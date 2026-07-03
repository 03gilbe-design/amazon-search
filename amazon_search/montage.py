# -*- coding: utf-8 -*-
"""Numbered thumbnail grid for free vision classification.

One montage image lets a human (or an LLM's vision tier) classify dozens of
products in a single look instead of one request per product — the
token-cheap way to do vision. Titles lie about category far more often than
photos do (measured: text-only recall 69%, precision 53% on a mislabeled
product set) so this is the fallback that actually resolves ambiguous cases.
"""
from __future__ import annotations
from pathlib import Path


def build_montage(items: list[dict], out_path: str | Path, *,
                   cols: int = 7, cell: int = 150, pad: int = 22,
                   label_fn=None) -> str:
    """items: [{"image": local_path, "label": str}, ...] (or pass label_fn to
    derive the label from an arbitrary item dict, e.g. lambda it: f"{it['price']}e").
    Writes a numbered grid PNG and returns its path as a string."""
    from PIL import Image, ImageDraw, ImageFont

    if not items:
        raise ValueError("build_montage: no items")

    rows = (len(items) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * cell, rows * (cell + pad)), "white")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except Exception:
        font = ImageFont.load_default()

    for i, it in enumerate(items):
        cx, cy = (i % cols) * cell, (i // cols) * (cell + pad)
        try:
            im = Image.open(it["image"]).convert("RGB")
            im.thumbnail((cell - 8, cell - 8))
            canvas.paste(im, (cx + 4, cy + pad - 2))
        except Exception:
            pass
        label = label_fn(it) if label_fn else it.get("label", "")
        draw.text((cx + 3, cy + 3), f"{i}: {label}", fill="black", font=font)

    out_path = str(out_path)
    canvas.save(out_path)
    return out_path


def _pca_scatter(items: list[dict], vectors, out_path: str | Path, *,
                  canvas_size: int = 900, thumb: int = 44, axis_label: str = "PC",
                  title: str = "") -> str:
    """Shared renderer: projects arbitrary N-dim `vectors` (one per item, same order) to
    2D via PCA (the two directions of most variance in THIS batch — data-driven axes, not
    fixed), places each product's real thumbnail at its point, border-colored by cluster."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    if len(items) < 2:
        raise ValueError("_pca_scatter: need at least 2 items")

    vecs = np.array(vectors, dtype=float)
    centered = vecs - vecs.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    k = min(2, vt.shape[0])
    coords = centered @ vt[:k].T
    if k < 2:
        coords = np.hstack([coords, np.zeros((len(items), 1))])

    # Standard boxplot rule (1.5*IQR beyond Q1/Q3) — flags only genuinely extreme points,
    # not an arbitrary top/bottom slice. A percentile cutoff like 10/90 always flags ~20%
    # of normally-spread data by construction; IQR only flags points actually far from the
    # bulk. Outliers are still drawn — clamped to the edge with a red border and flagged in
    # the return value — never silently dropped, just no longer distorting everyone else's scale.
    q1, q3 = np.percentile(coords, 25, axis=0), np.percentile(coords, 75, axis=0)
    iqr = q3 - q1
    dmin, dmax = coords.min(axis=0), coords.max(axis=0)
    # if an axis has ~zero spread in the middle 50% (IQR≈0), fall back to the real
    # min/max on that axis so a degenerate batch doesn't get flagged as "all outliers"
    lo = np.where(iqr > 1e-9, q1 - 1.5 * iqr, dmin)
    hi = np.where(iqr > 1e-9, q3 + 1.5 * iqr, dmax)
    span = np.where(hi - lo == 0, 1, hi - lo)
    outliers: list[dict] = []

    top_margin = 56  # room for title
    pad = thumb
    canvas = Image.new("RGB", (canvas_size, canvas_size + top_margin), "#f4f2ee")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
        font_title = ImageFont.truetype("arialbd.ttf", 16)
    except Exception:
        font = font_title = ImageFont.load_default()

    if title:
        draw.text((pad, 16), title, fill="#1c1a17", font=font_title)

    # shift all chart drawing down by top_margin
    draw.line([(pad, top_margin + canvas_size // 2), (canvas_size - pad, top_margin + canvas_size // 2)], fill="#ccc")
    draw.line([(canvas_size // 2, top_margin + pad), (canvas_size // 2, top_margin + canvas_size - pad)], fill="#ccc")
    draw.text((canvas_size - pad - 10, top_margin + canvas_size // 2 + 4), f"{axis_label}1 +", fill="#999", font=font)
    draw.text((canvas_size // 2 + 4, top_margin + pad - 14), f"{axis_label}2 +", fill="#999", font=font)

    cluster_colors = {}
    palette = ["#16a34a", "#0066c0", "#c9781f", "#c0392b", "#8b5cf6", "#0891b2", "#db2777"]

    for it, (x, y) in zip(items, coords):
        is_outlier = x < lo[0] or x > hi[0] or y < lo[1] or y > hi[1]
        cx = min(max(x, lo[0]), hi[0])
        cy = min(max(y, lo[1]), hi[1])
        px = pad + (cx - lo[0]) / span[0] * (canvas_size - 2 * pad)
        py = top_margin + canvas_size - pad - (cy - lo[1]) / span[1] * (canvas_size - 2 * pad)
        cluster = it.get("cluster") or "?"
        if cluster not in cluster_colors:
            cluster_colors[cluster] = palette[len(cluster_colors) % len(palette)]
        border = "#d32f2f" if is_outlier else cluster_colors[cluster]
        width = 3 if is_outlier else 2
        if is_outlier:
            outliers.append({"label": it.get("label"), "cluster": cluster})
        try:
            im = Image.open(it["image"]).convert("RGB")
            im.thumbnail((thumb, thumb))
            box = (int(px - thumb / 2), int(py - thumb / 2))
            draw.rectangle([box[0] - 2, box[1] - 2, box[0] + im.width + 2, box[1] + im.height + 2],
                           outline=border, width=width)
            canvas.paste(im, box)
            if is_outlier:
                draw.text((box[0], box[1] + im.height + 4), "outlier", fill=border, font=font)
        except Exception:
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=border)

    # legend: one swatch per cluster, top-right, plus the outlier marker if any exist
    lx, ly = canvas_size - 220, 8
    draw.text((lx, ly), "Legenda", fill="#1c1a17", font=font)
    ly += 16
    for cluster, color in cluster_colors.items():
        draw.rectangle([lx, ly, lx + 10, ly + 10], outline=color, width=2)
        draw.text((lx + 16, ly - 1), str(cluster)[:28], fill="#555", font=font)
        ly += 15
    if outliers:
        draw.rectangle([lx, ly, lx + 10, ly + 10], outline="#d32f2f", width=2)
        draw.text((lx + 16, ly - 1), "outlier (fuori scala)", fill="#555", font=font)

    out_path = str(out_path)
    canvas.save(out_path)
    if outliers:
        print(f"[build_scatter] {len(outliers)} outlier(s) clamped to edge (not dropped): "
              + ", ".join(f"{o['label']}({o['cluster']})" for o in outliers))
    return out_path


def build_color_scatter(items: list[dict], out_path: str | Path, *,
                         canvas_size: int = 900, thumb: int = 44) -> str:
    """items: [{"image": path, "color": (r,g,b), "label": str, "cluster": str}, ...]
    (color from scoring._dominant_color — pass it in, this function doesn't recompute it).
    See _pca_scatter — this is the color-space version. A good separation should look
    like visually distinct patches on the plot; a bad one looks like a smeared blob."""
    valid = [it for it in items if it.get("color")]
    if len(valid) < 2:
        raise ValueError("build_color_scatter: need at least 2 items with a color")
    return _pca_scatter(valid, [it["color"] for it in valid], out_path,
                         canvas_size=canvas_size, thumb=thumb, axis_label="PC",
                         title="Colore medio (sfondo escluso)")


def build_word_scatter(items: list[dict], out_path: str | Path, *,
                        canvas_size: int = 900, thumb: int = 44) -> str:
    """items: [{"image": path, "vector": [0/1,...], "label": str, "cluster": str}, ...]
    (vector from scoring.word_vectors() — a bag-of-discriminative-words per product, same
    dimension/order for every item). Same rendering as the color scatter, different space:
    proximity here means "shares distinctive title words", not "looks the same color"."""
    valid = [it for it in items if it.get("vector") is not None]
    if len(valid) < 2:
        raise ValueError("build_word_scatter: need at least 2 items with a vector")
    return _pca_scatter(valid, [it["vector"] for it in valid], out_path,
                         canvas_size=canvas_size, thumb=thumb, axis_label="WordPC",
                         title="Parole discriminanti del titolo")


def build_palette_scatter(items: list[dict], out_path: str | Path, *,
                           canvas_size: int = 900, thumb: int = 44) -> str:
    """items: [{"image": path, "palette": [...], "label": str, "cluster": str}, ...]
    (palette from scoring.color_palette_vector() — a full color histogram, not a single
    averaged RGB). Distinguishes "half black half white" from "uniform gray" the way
    build_color_scatter's single average can't."""
    valid = [it for it in items if it.get("palette") is not None]
    if len(valid) < 2:
        raise ValueError("build_palette_scatter: need at least 2 items with a palette")
    return _pca_scatter(valid, [it["palette"] for it in valid], out_path,
                         canvas_size=canvas_size, thumb=thumb, axis_label="PalettePC",
                         title="Palette colore (istogramma per immagine, non media)")


def build_cluster_graph(clusters: dict[str, list[dict]], out_path: str | Path, *,
                         cell: int = 90, pad: int = 14, cols_per_row: int = 8) -> str:
    """clusters: {label: [{"image": path, "label": str}, ...]} (e.g. from
    scoring.visual_cluster()'s assignment, grouped by label). Draws each cluster as its
    own bordered box of thumbnails with the cluster name as a header — a visual audit of
    what the algorithm actually grouped, side by side, so a human can eyeball the margins
    (are these boxes clean, or is one box actually two different things stuck together?)."""
    from PIL import Image, ImageDraw, ImageFont

    if not clusters:
        raise ValueError("build_cluster_graph: no clusters")
    try:
        font = ImageFont.truetype("arial.ttf", 13)
        font_small = ImageFont.truetype("arial.ttf", 10)
    except Exception:
        font = font_small = ImageFont.load_default()

    header_h = 24
    box_gap = 20
    boxes = []
    for label, items in clusters.items():
        cols = min(cols_per_row, len(items))
        rows = (len(items) + cols - 1) // cols
        box_w = cols * cell + pad * 2
        box_h = header_h + rows * (cell + 16) + pad
        boxes.append((label, items, box_w, box_h, cols))

    canvas_w = max(b[2] for b in boxes) + pad * 2
    canvas_h = sum(b[3] for b in boxes) + box_gap * (len(boxes) - 1) + pad * 2
    canvas = Image.new("RGB", (canvas_w, canvas_h), "#f4f2ee")
    draw = ImageDraw.Draw(canvas)

    y = pad
    for label, items, box_w, box_h, cols in boxes:
        draw.rounded_rectangle([pad, y, pad + box_w, y + box_h], radius=10,
                                outline="#16a34a", width=2, fill="#ffffff")
        draw.text((pad + 10, y + 6), f"{label} ({len(items)})", fill="#1c1a17", font=font)
        for i, it in enumerate(items):
            cx = pad + 10 + (i % cols) * cell
            cy = y + header_h + (i // cols) * (cell + 16)
            try:
                im = Image.open(it["image"]).convert("RGB")
                im.thumbnail((cell - 10, cell - 10))
                canvas.paste(im, (cx, cy))
            except Exception:
                pass
            if it.get("label"):
                draw.text((cx, cy + cell - 8), str(it["label"])[:12], fill="#c0392b", font=font_small)
        y += box_h + box_gap

    out_path = str(out_path)
    canvas.save(out_path)
    return out_path
