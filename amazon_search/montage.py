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


def build_color_scatter(items: list[dict], out_path: str | Path, *,
                         canvas_size: int = 900, thumb: int = 44) -> str:
    """items: [{"image": path, "color": (r,g,b), "label": str, "cluster": str}, ...]
    (color from scoring._dominant_color — pass it in, this function doesn't recompute it).
    Projects the actual RGB colors to 2D via PCA (the two directions of most variance in
    THIS batch's colors — not a fixed R-vs-G axis, so the plot uses whatever axis actually
    separates the images) and places each product's real thumbnail at its point, colored
    border by cluster. This is the "see it with your own eyes" tool for calibrating
    thresholds — a good separation should look like visually distinct patches on the
    plot; a bad one looks like a single smeared blob."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    valid = [it for it in items if it.get("color")]
    if len(valid) < 2:
        raise ValueError("build_color_scatter: need at least 2 items with a color")

    colors = np.array([it["color"] for it in valid], dtype=float)
    mean = colors.mean(axis=0)
    centered = colors - mean
    # 2 principal components via SVD — the data-driven "best" 2D axes for this batch
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T  # (n, 2)
    lo, hi = coords.min(axis=0), coords.max(axis=0)
    span = np.where(hi - lo == 0, 1, hi - lo)

    pad = thumb
    canvas = Image.new("RGB", (canvas_size, canvas_size), "#f4f2ee")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()

    # axes
    draw.line([(pad, canvas_size // 2), (canvas_size - pad, canvas_size // 2)], fill="#ccc")
    draw.line([(canvas_size // 2, pad), (canvas_size // 2, canvas_size - pad)], fill="#ccc")
    draw.text((canvas_size - pad - 10, canvas_size // 2 + 4), "PC1 +", fill="#999", font=font)
    draw.text((canvas_size // 2 + 4, pad - 14), "PC2 +", fill="#999", font=font)

    cluster_colors = {}
    palette = ["#16a34a", "#0066c0", "#c9781f", "#c0392b", "#8b5cf6", "#0891b2", "#db2777"]

    for it, (x, y) in zip(valid, coords):
        px = pad + (x - lo[0]) / span[0] * (canvas_size - 2 * pad)
        py = canvas_size - pad - (y - lo[1]) / span[1] * (canvas_size - 2 * pad)
        cluster = it.get("cluster") or "?"
        if cluster not in cluster_colors:
            cluster_colors[cluster] = palette[len(cluster_colors) % len(palette)]
        border = cluster_colors[cluster]
        try:
            im = Image.open(it["image"]).convert("RGB")
            im.thumbnail((thumb, thumb))
            box = (int(px - thumb / 2), int(py - thumb / 2))
            draw.rectangle([box[0] - 2, box[1] - 2, box[0] + im.width + 2, box[1] + im.height + 2],
                           outline=border, width=2)
            canvas.paste(im, box)
        except Exception:
            draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=border)

    out_path = str(out_path)
    canvas.save(out_path)
    return out_path


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
