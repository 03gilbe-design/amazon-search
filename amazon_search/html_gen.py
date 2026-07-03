"""Generate standalone mobile-first HTML from Amazon product results."""
from __future__ import annotations

import html
import os
import re
from datetime import datetime
from pathlib import Path


def _default_output_dir() -> Path:
    """Termux's Download dir on real Termux, a home subfolder everywhere else.

    Checked via a Termux-specific marker (not just path existence — on
    Windows, Path("/storage/...").mkdir() silently creates a *drive-relative*
    directory, so an existence check alone can be fooled by a stray leftover
    folder from a previous run).
    """
    if os.name != "nt" and Path("/data/data/com.termux").exists():
        return Path("/storage/emulated/0/Download")
    return Path.home() / "amazon_search_reports"


OUTPUT_DIR = _default_output_dir()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower())[:30].strip("_")


def _stars(rating: float | None) -> str:
    if rating is None:
        return "N/D"
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty


def _badge(product) -> str:
    """Only show if NOT in stock (red alert)"""
    if not product.in_stock:
        return '<span class="badge-alert">Non disponibile</span>'
    if product.prime:
        return '<span class="badge-prime">Prime</span>'
    return ""


def _dedup_badge(product) -> str:
    note = getattr(product, "dedup_note", None)
    if not note:
        return ""
    return f'<span class="badge-dedup">{html.escape(note)}</span>'


def _fit_chips(p) -> str:
    hits = getattr(p, "feature_fit_hits", None)
    if not hits:
        return ""
    chips = "".join(
        f'<span class="fit-chip {"fit-yes" if ok else "fit-no"}">{"✓" if ok else "✗"} {html.escape(name)}</span>'
        for name, ok in hits.items()
    )
    return f'<div class="fit-chips">{chips}</div>'


def _video_line(p, video_coverage: dict) -> str:
    if not video_coverage:
        return ""
    cov = video_coverage.get(p.title) or next(
        (v for k, v in video_coverage.items() if k.lower() in p.title.lower()
         or p.title.lower() in k.lower()), None)
    if not cov:
        return ""
    n = cov["video_count"]
    if n >= 2:
        return f'<div class="video-line video-ok">Confermato da {n} recensioni indipendenti</div>'
    return '<div class="video-line video-warn">Solo 1 video, verifica sponsorizzazione</div>'


def _card(p, idx: int, *, video_coverage: dict | None = None) -> str:
    """Card: image LEFT + info RIGHT. Minimal, no redundancy."""
    title_esc = html.escape(p.title[:70])
    price_esc = html.escape(p.price_str or "—")
    link_esc = html.escape(p.link)
    stars_str = _stars(p.stars)
    reviews_count = p.reviews if p.reviews else 0
    review_confidence = "●●●" if reviews_count > 100 else "●●" if reviews_count > 10 else "●"
    badge_html = _badge(p)
    dedup_badge_html = _dedup_badge(p)
    fit_html = _fit_chips(p)
    video_html = _video_line(p, video_coverage or {})
    thumb = html.escape(p.thumbnail or "")
    price_data = str(p.price or 9999)
    stars_data = str(p.stars or 0)

    thumb_html = (
        f'<img src="{thumb}" alt="" loading="lazy">'
        if thumb else '<div class="no-img">■</div>'
    )

    specs_html = ""
    if p.specs:
        rows = "".join(
            f"<tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>"
            for k, v in list(p.specs.items())[:8]
        )
        specs_html = f'<details class="specs"><summary>Specifiche</summary><table>{rows}</table></details>'

    fam_ring = ' card-grouped' if getattr(p, "family_id", None) is not None else ''
    return f"""
    <div class="card{fam_ring}" data-price="{price_data}" data-stars="{stars_data}" data-idx="{idx}">
        <div class="card-img">{thumb_html}</div>
        <div class="card-info">
            <div class="card-title">{title_esc}</div>
            <div class="card-rating">{stars_str} <span class="confidence">{review_confidence}</span> <span class="reviews">({reviews_count})</span></div>
            <div class="card-price">{price_esc}</div>
            {badge_html}
            {dedup_badge_html}
            {fit_html}
            {video_html}
            {specs_html}
            <a href="{link_esc}" target="_blank" class="btn-cta">Vedi su Amazon</a>
        </div>
    </div>"""


def _family_card(fam: dict) -> str:
    spread = fam.get("spread")
    spread_txt = f"€{spread:.2f} di differenza" if spread is not None else "differenza non nota"
    items = sorted(fam["items"], key=lambda it: it["price"] if it["price"] is not None else 9e9)
    identical = not fam.get("diff_image", False)

    if identical:
        # exact same photo file: one true overlapping stack + a vertical price list
        stack_imgs = "".join(
            f'<img src="{html.escape(items[i]["thumbnail"] or "")}" alt="" loading="lazy" style="--i:{i}">'
            for i in range(min(3, len(items)))
        )
        more_badge = f'<div class="fam-more">+{len(items)-3}</div>' if len(items) > 3 else ""
        price_list = "".join(
            f'<li>€{it["price"]:.2f}</li>' if it["price"] is not None else "<li>?</li>"
            for it in items
        )
        body = f"""
        <div class="fam-stack">{stack_imgs}{more_badge}</div>
        <ul class="fam-pricelist">{price_list}</ul>"""
    else:
        # similar but not byte-identical photos: distinct thumbnails, tightly clustered
        thumbs = "".join(
            f'<div class="fam-sim-item"><img src="{html.escape(it["thumbnail"] or "")}" alt="" loading="lazy">'
            f'<div class="fam-sim-price">{("€" + format(it["price"], ".2f")) if it["price"] is not None else "?"}</div></div>'
            for it in items
        )
        body = f'<div class="fam-sim-cluster">{thumbs}</div>'

    return f"""
    <div class="fam-card {'fam-identical' if identical else 'fam-similar'}">
        <div class="fam-spread">{spread_txt}</div>
        {body}
        <div class="fam-count">{len(items)} listati{' — foto identica' if identical else ' — foto simili'}</div>
    </div>"""


def _families_section(families: list[dict]) -> str:
    """Only families with a REAL price gap (>€2) — this is the section that answers
    "same item, pick the cheaper one". Near-zero-spread families aren't shown here:
    zero savings isn't a finding, and it's exactly the case where a false-positive
    photo match (pHash says "same" but it's actually two different products that
    happen to look alike, e.g. a dog vs. a cat photo) would go unnoticed if presented
    with the same confidence as a genuine result."""
    real_gap = [f for f in families if f.get("spread") is not None and f["spread"] > 2]
    if not real_gap:
        return ""
    cards = "".join(_family_card(f) for f in real_gap)
    return f"""
    <div class="section">
        <h2>Stesso prodotto, prezzi diversi</h2>
        <p class="section-sub">Foto quasi identiche con un vero risparmio in {len(real_gap)} gruppi — spesso è lo stesso oggetto rietichettato. Foto identica = stesso file, impilate; foto simile = stesso oggetto ma scatti diversi, affiancate.</p>
        <div class="fam-grid">{cards}</div>
    </div>"""


def _possible_duplicates_section(families: list[dict]) -> str:
    """Zero/near-zero spread families: same photo, ~same price, no arbitrage value —
    but ALSO no independent confirmation these are truly the same product (could be a
    genuine duplicate listing, or a pHash false-positive). Shown separately, collapsed,
    with an explicit "verify before trusting" framing rather than presented as fact."""
    flat = [f for f in families if f.get("spread") is None or f["spread"] <= 2]
    if not flat:
        return ""
    cards = "".join(_family_card(f) for f in flat)
    return f"""
    <details class="section dup-section">
        <summary>{len(flat)} possibili doppioni (stesso prezzo — verifica a occhio)</summary>
        <p class="section-sub">Nessuna differenza di prezzo rilevante, quindi nessun vantaggio a saperlo — ma occhio: un pHash può anche
        raggruppare due prodotti DIVERSI che sembrano solo simili nella foto (es. un cane scambiato per un gatto). Non dare per scontato che sia lo stesso oggetto senza guardare.</p>
        <div class="fam-grid">{cards}</div>
    </details>"""


def _price_chart(products: list) -> str:
    pts = [(p.price, p.stars, p.title) for p in products if p.price is not None and p.stars is not None]
    if len(pts) < 2:
        return ""
    prices = [p for p, _, _ in pts]
    pmin, pmax = min(prices), max(prices)
    prange = (pmax - pmin) or 1
    w, h, pad = 600, 160, 24
    dots = []
    for price, stars, title in pts:
        x = pad + (price - pmin) / prange * (w - 2 * pad)
        y = h - pad - (stars / 5) * (h - 2 * pad)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#0066c0" fill-opacity="0.65">'
                     f'<title>{html.escape(title[:40])} — €{price:.2f}, {stars}★</title></circle>')
    return f"""
    <div class="section">
        <h2>Prezzo vs valutazione</h2>
        <p class="section-sub">Ogni punto è un prodotto — outlier isolati sono spesso rumore (poche recensioni, prezzo anomalo).</p>
        <svg viewBox="0 0 {w} {h}" class="price-chart">
            <line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#ddd"/>
            <line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#ddd"/>
            <text x="{pad}" y="{h-6}" font-size="10" fill="#999">€{pmin:.0f}</text>
            <text x="{w-pad-24}" y="{h-6}" font-size="10" fill="#999">€{pmax:.0f}</text>
            <text x="2" y="{pad+4}" font-size="10" fill="#999">5★</text>
            <text x="2" y="{h-pad}" font-size="10" fill="#999">0★</text>
            {"".join(dots)}
        </svg>
    </div>"""


def _video_section(video_claims: list[dict]) -> str:
    if not video_claims:
        return ""
    by_product: dict[str, list] = {}
    for c in video_claims:
        by_product.setdefault(c.get("product", "?"), []).append(c)
    blocks = []
    for product, claims in by_product.items():
        items = "".join(
            f'<li class="claim claim-{html.escape(c.get("sentiment","neutral"))}">'
            f'{html.escape(c.get("claim",""))} — '
            f'<a href="https://www.youtube.com/watch?v={html.escape(c.get("video",""))}" target="_blank">{html.escape(c.get("title","video")[:40])}</a></li>'
            for c in claims[:6]
        )
        blocks.append(f'<details class="video-block"><summary>{html.escape(product)} ({len(claims)} claim)</summary><ul>{items}</ul></details>')
    return f"""
    <div class="section">
        <h2>Cosa dicono le recensioni video</h2>
        {"".join(blocks)}
    </div>"""


def _excluded_section(excluded: list[dict]) -> str:
    if not excluded:
        return ""
    rows = "".join(
        f'<tr><td>{html.escape(e["title"][:60])}</td><td>{html.escape(e["reason"])}</td></tr>'
        for e in excluded
    )
    return f"""
    <details class="section excluded-section">
        <summary>{len(excluded)} esclusi (negative sampling) — motivo</summary>
        <table class="excluded-table">{rows}</table>
    </details>"""


def _query_variants_section(variants: list[str], current_query: str) -> str:
    if not variants:
        return ""
    chips = "".join(
        f'<a class="qv-chip" href="?" onclick="return false" title="riesegui la ricerca con questa query">{html.escape(v)}</a>'
        for v in variants[:10]
    )
    return f"""
    <div class="section">
        <h2>Query alternative</h2>
        <p class="section-sub">Termini trovati nei titoli reali (o suggeriti da AI) che "{html.escape(current_query)}" non copre — prova a rilanciare la ricerca con una di queste.</p>
        <div class="qv-chips">{chips}</div>
    </div>"""


def _benchmarks_section(benchmarks: list[dict]) -> str:
    if not benchmarks:
        return ""
    cards = "".join(
        f'<div class="bench-card"><div class="bench-title">{html.escape(b.get("title",""))}</div>'
        f'<div class="bench-note">{html.escape(b.get("note",""))}</div>'
        f'<div class="bench-flag">non acquistabile su questo marketplace</div></div>'
        for b in benchmarks
    )
    return f"""
    <div class="section">
        <h2>Benchmark esterni</h2>
        <p class="section-sub">Prodotti seri di riferimento, non in vendita qui — solo confronto.</p>
        <div class="bench-grid">{cards}</div>
    </div>"""


def _cluster_by_family(products: list) -> list:
    """Reorder so pHash-family siblings sit next to each other in the main grid,
    instead of scattered across the page — same idea as the dedicated families
    section, applied to the catalog itself. Products with no family_id keep their
    original relative order; the first product of each family determines where
    that cluster is inserted."""
    seen_families: dict[int, list] = {}
    order: list = []
    for p in products:
        fid = getattr(p, "family_id", None)
        if fid is None:
            order.append(p)
        elif fid not in seen_families:
            seen_families[fid] = [p]
            order.append(seen_families[fid])  # placeholder for the whole cluster
        else:
            seen_families[fid].append(p)
    flat: list = []
    for item in order:
        flat.extend(item) if isinstance(item, list) else flat.append(item)
    return flat


def generate_html(
    products: list,
    query: str,
    *,
    summary: str = "",
    quota_info: str = "",
    output_dir: Path = OUTPUT_DIR,
    sections_before_grid: str = "",
    sections_after_grid: str = "",
    footer_html: str = "",
    video_coverage: dict | None = None,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"amazon_{_slug(query)}_{ts}.html"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename

    products = _cluster_by_family(products)
    categories = [getattr(p, "category", None) for p in products]
    if any(categories):
        seen_order: list[str] = []
        for c in categories:
            c = c or "Altro"
            if c not in seen_order:
                seen_order.append(c)
        blocks = []
        idx = 0
        for cat in seen_order:
            cat_products = [p for p in products if (getattr(p, "category", None) or "Altro") == cat]
            cat_cards = "\n".join(_card(p, idx + i, video_coverage=video_coverage) for i, p in enumerate(cat_products))
            idx += len(cat_products)
            blocks.append(f'<h3 class="cat-title">{html.escape(cat)} <span class="cat-count">({len(cat_products)})</span></h3><div class="grid">{cat_cards}</div>')
        cards_html = "\n".join(blocks)
        grid_wrap_class = ""  # each category already has its own .grid
    else:
        cards_html = "\n".join(_card(p, i, video_coverage=video_coverage) for i, p in enumerate(products))
        grid_wrap_class = "grid"
    n = len(products)

    summary_html = ""
    if summary:
        summary_html = f'<div class="summary">{html.escape(summary)}</div>'

    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<title>{html.escape(query)}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:#f4f2ee}}
body{{font-family:'Segoe UI',-apple-system,BlinkMacSystemFont,Roboto,sans-serif;color:#1c1a17;line-height:1.55;-webkit-font-smoothing:antialiased}}
.page{{max-width:1180px;margin:0 auto}}

.header{{background:linear-gradient(135deg,#1a2436,#232f3e);color:#fff;padding:16px 20px;position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:flex-start;gap:16px;box-shadow:0 2px 10px rgba(0,0,0,.15)}}
.header .eyebrow{{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7dd3fc;font-weight:700;margin-bottom:4px}}
.header h1{{font-size:16px;font-weight:700;line-height:1.35;max-width:70ch}}
.header .sub{{font-size:11.5px;color:#9fb0c0;margin-top:4px}}
.btn-filter{{background:#e47911;color:#fff;border:none;padding:9px 14px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;white-space:nowrap;flex-shrink:0;transition:background 0.2s,transform 0.1s;box-shadow:0 2px 6px rgba(228,121,17,.35)}}
.btn-filter:active{{background:#c96b00;transform:scale(0.95)}}

.filter-chips{{background:#fff;padding:8px 16px;border-bottom:1px solid #e0e0e0;display:flex;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch}}
.chip{{background:#e3f2fd;color:#0066c0;padding:6px 10px;border-radius:16px;font-size:12px;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;flex-shrink:0;cursor:pointer;border:1px solid #90caf9;transition:all 0.2s}}
.chip:active{{background:#bbdefb;transform:scale(0.95)}}
.chip.removing{{animation:fadeOut 0.2s ease forwards}}
@keyframes fadeOut{{to{{opacity:0;transform:scale(0.9)}}}}
.chip-close{{color:#0066c0;font-weight:bold;cursor:pointer}}

.controls{{background:#fff;padding:10px 16px;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#666}}
.sort-ctrl{{background:#fff;border:1px solid #ccc;padding:6px 10px;border-radius:4px;font-size:13px;cursor:pointer;transition:border-color 0.2s}}
.sort-ctrl:active{{border-color:#0066c0}}

.summary{{background:#fff7e0;border-left:4px solid #f5a623;padding:14px 18px;margin:16px 16px 0;border-radius:6px;font-size:13.5px;line-height:1.55;color:#5c4b1e}}

.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;padding:16px;padding-bottom:80px}}
.cat-title{{font-size:15px;font-weight:800;color:#1c1a17;margin:22px 16px 4px;letter-spacing:-.01em}}
.cat-title:first-of-type{{margin-top:16px}}
.cat-count{{font-weight:500;color:#a39d8f;font-size:12.5px}}

.card{{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(20,20,10,.08),0 1px 2px rgba(20,20,10,.04);overflow:hidden;transition:box-shadow .2s,transform .2s;display:flex;flex-direction:column}}
.card-grouped{{box-shadow:0 0 0 2px rgba(22,163,74,.35),0 1px 3px rgba(20,20,10,.08)}}
.card:hover{{box-shadow:0 6px 18px rgba(20,20,10,.12);transform:translateY(-1px)}}
.card:active{{animation:cardPulse 0.3s ease}}
@keyframes cardPulse{{0%{{transform:scale(1)}}50%{{transform:scale(1.01)}}100%{{transform:scale(1)}}}}

.card-link{{display:flex;flex-direction:column;gap:0;text-decoration:none;color:inherit;cursor:pointer;height:100%}}

.card-img{{flex-shrink:0;width:100%;height:150px;background:linear-gradient(135deg,#faf8f5,#f0ede7);display:flex;align-items:center;justify-content:center;overflow:hidden}}
.card-img img{{max-width:88%;max-height:88%;object-fit:contain}}
.no-img{{font-size:2rem;color:#ccc}}

.card-info{{flex:1;display:flex;flex-direction:column;gap:7px;min-width:0;padding:14px}}

.card-title{{font-size:14px;font-weight:600;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:2.7em}}

.card-rating{{font-size:12px;color:#666;display:flex;gap:4px;align-items:center}}
.card-rating strong{{color:#e08a2e;font-size:13px}}
.confidence{{color:#b8b2a5;font-size:10px;letter-spacing:1px}}
.reviews{{color:#999;font-size:11px}}

.card-price{{font-size:19px;font-weight:800;color:#c0392b;letter-spacing:-.01em}}

.badge-alert{{background:#d32f2f;color:#fff;padding:3px 9px;border-radius:20px;font-size:10.5px;font-weight:700}}
.badge-prime{{background:#0066c0;color:#fff;padding:3px 9px;border-radius:20px;font-size:10.5px;font-weight:700}}
.badge-dedup{{display:inline-block;background:#16a34a;color:#fff;padding:3px 9px;border-radius:20px;font-size:10.5px;font-weight:700}}

.fit-chips{{display:flex;flex-wrap:wrap;gap:4px}}
.fit-chip{{font-size:10px;font-weight:700;padding:3px 8px;border-radius:20px}}
.fit-yes{{background:rgba(22,163,74,.12);color:#16a34a}}
.fit-no{{background:rgba(0,0,0,.04);color:#aaa}}

.video-line{{font-size:11px;font-weight:600;padding:2px 0}}
.video-ok{{color:#16a34a}}
.video-warn{{color:#c9781f}}

.section{{
  background:rgba(255,255,255,.72); backdrop-filter:blur(14px) saturate(160%); -webkit-backdrop-filter:blur(14px) saturate(160%);
  margin:14px 16px; padding:18px 20px; border-radius:14px;
  border:1px solid rgba(255,255,255,.6); box-shadow:0 4px 20px rgba(30,20,5,.06);
}}
.section h2{{font-size:16px;font-weight:800;margin-bottom:4px;letter-spacing:-.01em}}
.section-sub{{font-size:12px;color:#8a8577;margin-bottom:12px;line-height:1.5}}

.fam-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}
.fam-card{{text-align:center}}
.fam-stack{{position:relative;height:84px;margin-bottom:10px}}
.fam-stack img{{
  position:absolute; top:0; left:50%; width:74px;height:74px;object-fit:contain;
  background:#faf8f5;border-radius:10px;border:1px solid rgba(0,0,0,.06);
  box-shadow:0 4px 10px rgba(20,15,5,.14);
  transform:translateX(calc(-50% + var(--i)*14px)) rotate(calc(var(--i)*4deg - 4deg));
}}
.fam-more{{
  position:absolute; right:4px; bottom:0; background:#1c1a17; color:#fff; font-size:10.5px;
  font-weight:700; padding:2px 7px; border-radius:10px; box-shadow:0 2px 6px rgba(0,0,0,.2);
}}
.fam-spread{{font-size:12px;font-weight:800;color:#16a34a;display:inline-block;background:rgba(22,163,74,.1);padding:3px 10px;border-radius:20px;margin-bottom:10px}}
.fam-count{{font-size:11px;color:#8a8577;margin-top:8px}}

.fam-identical .fam-stack{{margin-bottom:6px}}
.fam-pricelist{{list-style:none;font-size:12.5px;font-weight:700;color:#c0392b;display:flex;flex-direction:column;gap:2px}}

.fam-sim-cluster{{display:flex;justify-content:center;gap:4px;flex-wrap:wrap}}
.fam-sim-item{{width:60px;text-align:center}}
.fam-sim-item img{{width:56px;height:56px;object-fit:contain;background:#faf8f5;border-radius:8px;border:1px solid rgba(0,0,0,.06)}}
.fam-sim-price{{font-size:10.5px;font-weight:700;color:#c0392b;margin-top:3px}}

.price-chart{{width:100%;height:auto}}

.video-block{{border-top:1px solid rgba(0,0,0,.06);padding:10px 0}}
.video-block:first-of-type{{border-top:none}}
.video-block summary{{cursor:pointer;font-size:13.5px;font-weight:700;color:#0066c0}}
.video-block ul{{margin:8px 0 0 16px;font-size:12px;line-height:1.65}}
.claim-pos{{color:#16a34a}}
.claim-neg{{color:#d32f2f}}
.claim-neutral{{color:#555}}

.dup-section{{background:rgba(255,255,255,.45);cursor:pointer}}
.dup-section summary{{font-size:13.5px;font-weight:700;color:#8a8577}}
.dup-section .fam-grid{{margin-top:12px}}

.excluded-section{{cursor:pointer}}
.excluded-section summary{{font-size:13.5px;font-weight:700;color:#8a8577}}
.excluded-table{{width:100%;margin-top:10px;font-size:12px;border-collapse:collapse}}
.excluded-table td{{padding:6px 8px;border-bottom:1px solid rgba(0,0,0,.06)}}

.bench-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}
.bench-card{{border:1.5px dashed rgba(0,0,0,.15);border-radius:10px;padding:12px;background:rgba(0,0,0,.015)}}
.bench-title{{font-size:13.5px;font-weight:700}}
.bench-note{{font-size:12px;color:#666;margin-top:3px}}
.bench-flag{{font-size:10.5px;color:#c9781f;font-weight:700;margin-top:6px}}

.footer-disclosure{{padding:20px 16px 28px;text-align:center;font-size:11.5px;color:#a39d8f;line-height:1.6;max-width:60ch;margin:0 auto}}

.qv-chips{{display:flex;flex-wrap:wrap;gap:7px}}
.qv-chip{{background:rgba(0,102,192,.08);color:#0066c0;padding:6px 12px;border-radius:20px;font-size:12px;font-weight:600;text-decoration:none;border:1px solid rgba(0,102,192,.15);transition:background .15s}}
.qv-chip:hover{{background:rgba(0,102,192,.15)}}

.specs{{font-size:11px;margin-top:4px}}
.specs summary{{color:#0066c0;cursor:pointer;padding:4px 0;font-weight:500;user-select:none}}
.specs table{{width:100%;margin-top:4px;border-collapse:collapse}}
.specs td{{padding:3px 6px;border-bottom:1px solid #f0f0f0}}
.specs td:first-child{{color:#666;width:45%;font-weight:500}}

.btn-cta{{display:block;text-align:center;background:#e47911;color:#fff;text-decoration:none;padding:10px 12px;min-height:44px;border-radius:4px;font-size:13px;font-weight:600;margin-top:auto;border:none;cursor:pointer;transition:background 0.2s,transform 0.1s}}
.btn-cta:active{{background:#c96b00;transform:scale(0.95)}}

.no-results{{text-align:center;padding:40px 20px;color:#999;font-size:14px}}

.hidden{{display:none!important}}

.drawer-overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:200;display:none;opacity:0;transition:opacity 0.3s ease}}
.drawer-overlay.active{{display:block;opacity:1}}

.drawer{{position:fixed;bottom:0;left:0;right:0;background:#fff;border-radius:12px 12px 0 0;max-height:85vh;z-index:201;transform:translateY(100%);transition:transform 0.3s cubic-bezier(0.25,0.46,0.45,0.94);display:flex;flex-direction:column;overflow:hidden;box-shadow:0 -2px 16px rgba(0,0,0,0.2)}}
.drawer.active{{transform:translateY(0)}}

.drawer-header{{padding:16px;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:center;font-weight:600}}
.drawer-close{{background:none;border:none;font-size:24px;cursor:pointer;color:#666;padding:0;width:32px;height:32px;transition:transform 0.2s}}
.drawer-close:active{{transform:scale(0.9)}}

.drawer-body{{flex:1;overflow-y:auto;padding:16px;-webkit-overflow-scrolling:touch}}
.drawer-body::-webkit-scrollbar{{width:4px}}
.drawer-body::-webkit-scrollbar-track{{background:#f1f1f1}}
.drawer-body::-webkit-scrollbar-thumb{{background:#ccc;border-radius:2px}}

.filter-group{{margin-bottom:20px}}
.filter-group h3{{font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:10px;text-transform:uppercase;letter-spacing:0.5px}}

.filter-option{{display:flex;align-items:center;gap:10px;padding:10px 0;font-size:13px;cursor:pointer;transition:background 0.2s}}
.filter-option:active{{background:#f5f5f5}}
.filter-option input[type="radio"]{{width:18px;height:18px;cursor:pointer}}
.filter-option label{{flex:1;cursor:pointer;user-select:none}}

.price-slider{{width:100%;margin:12px 0;cursor:pointer;accent-color:#0066c0}}
.price-display{{font-size:14px;font-weight:600;color:#d32f2f;margin:8px 0}}

.drawer-footer{{padding:12px 16px;border-top:1px solid #e0e0e0;display:flex;gap:10px}}
.btn-reset,.btn-apply{{flex:1;padding:12px;border:none;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer;min-height:44px;transition:all 0.2s}}
.btn-reset{{background:#f0f0f0;color:#1a1a1a;border:1px solid #ccc}}
.btn-reset:active{{background:#e0e0e0;transform:scale(0.95)}}
.btn-apply{{background:#0066c0;color:#fff;animation:pulse 0.4s ease}}
.btn-apply:active{{background:#004494;transform:scale(0.95)}}
@keyframes pulse{{0%,100%{{box-shadow:0 0 0 0 rgba(0,102,192,0.5)}}70%{{box-shadow:0 0 0 8px rgba(0,102,192,0)}}}}

.result-count{{font-size:12px;color:#999;padding:0 16px;margin-bottom:8px}}

@media (max-width:420px){{
.grid{{grid-template-columns:1fr;padding:12px}}
.section{{margin:10px 12px;padding:14px 16px}}
.header{{padding:12px 14px}}
.header h1{{font-size:14px}}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <div class="eyebrow">amazon-search report</div>
    <h1>{html.escape(query)}</h1>
  </div>
  <button class="btn-filter" onclick="openDrawer()">Filtri</button>
</div>

<div class="page">

<div class="filter-chips" id="activeChips"></div>

<div class="controls">
  <span id="resultCount"></span>
  <select class="sort-ctrl" id="sortSel" onchange="sortCards()">
    <option value="idx">Rilevanza</option>
    <option value="price_asc">Prezzo ↑</option>
    <option value="price_desc">Prezzo ↓</option>
    <option value="stars">Stelle ↓</option>
  </select>
</div>

{summary_html}

{sections_before_grid}

<div class="{grid_wrap_class}" id="grid">
{cards_html}
</div>

<div class="no-results hidden" id="noResults">
Nessun prodotto trovato<br><small>Prova a rimuovere i filtri</small>
</div>

{sections_after_grid}

{footer_html}

</div>

<div class="drawer-overlay" id="overlay" onclick="closeDrawer()"></div>
<div class="drawer" id="drawer">
  <div class="drawer-header">
    Filtri
    <button class="drawer-close" onclick="closeDrawer()">✕</button>
  </div>

  <div class="drawer-body">
    <div class="filter-group">
      <h3>Prezzo</h3>
      <div class="price-display">Max: <span id="priceDisplay">—</span></div>
      <input type="range" id="priceSlider" min="0" max="2000" value="2000" class="price-slider" oninput="updatePrice()">
    </div>

    <div class="filter-group">
      <h3>Valutazione minima</h3>
      <div class="filter-option" onclick="setMinStars(0)">
        <input type="radio" name="stars" value="0" checked> <label>Tutte</label>
      </div>
      <div class="filter-option" onclick="setMinStars(3.5)">
        <input type="radio" name="stars" value="3.5"> <label>3.5★+</label>
      </div>
      <div class="filter-option" onclick="setMinStars(4)">
        <input type="radio" name="stars" value="4"> <label>4.0★+</label>
      </div>
      <div class="filter-option" onclick="setMinStars(4.5)">
        <input type="radio" name="stars" value="4.5"> <label>4.5★+</label>
      </div>
    </div>
  </div>

  <div class="result-count" id="resultPreview">—</div>
  <div class="drawer-footer">
    <button class="btn-reset" onclick="resetFilters()">Reset</button>
    <button class="btn-apply" onclick="applyFilters()">Applica</button>
  </div>
</div>

<script>
const cards=Array.from(document.querySelectorAll('.card'));
let filterState={{maxPrice:2000,minStars:0}};

function openDrawer(){{
  document.getElementById('overlay').classList.add('active');
  document.getElementById('drawer').classList.add('active');
}}

function closeDrawer(){{
  document.getElementById('overlay').classList.remove('active');
  document.getElementById('drawer').classList.remove('active');
}}

function updatePrice(){{
  const val=parseFloat(document.getElementById('priceSlider').value);
  document.getElementById('priceDisplay').textContent=val===2000?'—':'€'+val;
  updatePreview();
}}

function setMinStars(val){{
  document.querySelector('input[name="stars"][value="'+val+'"]').checked=true;
  updatePreview();
}}

function updatePreview(){{
  const maxPrice=parseFloat(document.getElementById('priceSlider').value);
  const minStars=parseFloat(document.querySelector('input[name="stars"]:checked').value);
  let visible=0;
  cards.forEach(c=>{{
    const p=parseFloat(c.dataset.price);
    const s=parseFloat(c.dataset.stars);
    const show=(maxPrice>=2000||p===9999||p<=maxPrice)&&(minStars===0||s>=minStars);
    if(show)visible++;
  }});
  document.getElementById('resultPreview').textContent=visible+' risultati';
}}

function resetFilters(){{
  filterState.maxPrice=2000;
  filterState.minStars=0;
  document.getElementById('priceSlider').value=2000;
  document.querySelector('input[name="stars"][value="0"]').checked=true;
  updatePreview();
}}

function applyFilters(){{
  filterState.maxPrice=parseFloat(document.getElementById('priceSlider').value);
  filterState.minStars=parseFloat(document.querySelector('input[name="stars"]:checked').value);
  filterCards();
  updateActiveChips();
  closeDrawer();
}}

function filterCards(){{
  let visible=0;
  cards.forEach(c=>{{
    const p=parseFloat(c.dataset.price);
    const s=parseFloat(c.dataset.stars);
    const show=(filterState.maxPrice>=2000||p===9999||p<=filterState.maxPrice)&&(filterState.minStars===0||s>=filterState.minStars);
    c.classList.toggle('hidden',!show);
    if(show)visible++;
  }});
  document.getElementById('resultCount').textContent=visible+' risultati';
  document.getElementById('noResults').classList.toggle('hidden',visible>0);
}}

function updateActiveChips(){{
  const chips=[];
  if(filterState.maxPrice<2000){{
    chips.push('<div class="chip">€ ≤'+filterState.maxPrice+'<span class="chip-close" onclick="removeFilter(\'price\')">×</span></div>');
  }}
  if(filterState.minStars>0){{
    chips.push('<div class="chip">★ '+filterState.minStars+'+<span class="chip-close" onclick="removeFilter(\'stars\')">×</span></div>');
  }}
  document.getElementById('activeChips').innerHTML=chips.length?chips.join(''):''
}}

function removeFilter(type){{
  const chip=event.target.parentElement;
  chip.classList.add('removing');
  setTimeout(()=>{{
    if(type==='price'){{filterState.maxPrice=2000;document.getElementById('priceSlider').value=2000;document.getElementById('priceDisplay').textContent='—'}}
    if(type==='stars'){{filterState.minStars=0;document.querySelector('input[name="stars"][value="0"]').checked=true}}
    filterCards();
    updateActiveChips();
  }},200);
}}

function sortCards(){{
  const mode=document.getElementById('sortSel').value;
  const grid=document.getElementById('grid');
  const sorted=[...cards].filter(c=>!c.classList.contains('hidden')).sort((a,b)=>{{
    if(mode==='price_asc')return parseFloat(a.dataset.price)-parseFloat(b.dataset.price);
    if(mode==='price_desc')return parseFloat(b.dataset.price)-parseFloat(a.dataset.price);
    if(mode==='stars')return parseFloat(b.dataset.stars)-parseFloat(a.dataset.stars);
    return parseInt(a.dataset.idx)-parseInt(b.dataset.idx);
  }});
  sorted.forEach(c=>grid.appendChild(c));
}}

updatePreview();
document.getElementById('resultCount').textContent={n}+' risultati';
document.getElementById('priceSlider').addEventListener('input',updatePrice);
document.querySelectorAll('input[name="stars"]').forEach(r=>r.addEventListener('change',updatePreview));
document.getElementById('overlay').addEventListener('click',e=>{{if(e.target===document.getElementById('overlay'))closeDrawer()}});
</script>
</body>
</html>"""

    out_path.write_text(html_content, encoding="utf-8")
    return out_path


def generate_report(result, *, output_dir: Path = OUTPUT_DIR) -> Path:
    """Single entry point for a pipeline.SearchResult -> one HTML report with every
    section the pipeline computed (families, price chart, video claims, exclusions,
    benchmarks). This is what the CLI calls; generate_html() stays as the lower-level
    card-list builder other code can still use directly."""
    n = len(result.products)
    n_pulled = sum(1 for p in result.products if getattr(p, "source_kind", "organic") == "manual_pull")
    domain = result.filters.get("domain", "IT")

    sections_before = "".join([
        _families_section(result.families),
        _price_chart(result.products),
    ])
    sections_after = "".join([
        _video_section(result.video_claims),
        _query_variants_section(result.query_variants, result.query),
        _possible_duplicates_section(result.families),
        _excluded_section(result.excluded),
        _benchmarks_section(result.external_benchmarks),
    ])
    footer = (
        f'<div class="footer-disclosure">Questo report copre {n} risultati dalla ricerca '
        f'Amazon.{html.escape(str(domain))}'
        + (f" + {n_pulled} pull manuali" if n_pulled else "")
        + '. Il prodotto migliore in assoluto potrebbe non essere in questo pool.</div>'
    )

    return generate_html(
        result.products,
        result.query,
        summary=result.ai_summary,
        quota_info=result.quota_info,
        output_dir=output_dir,
        sections_before_grid=sections_before,
        sections_after_grid=sections_after,
        footer_html=footer,
        video_coverage=result.video_coverage,
    )
