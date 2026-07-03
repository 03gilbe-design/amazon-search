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


def _card(p, idx: int) -> str:
    """Card: image LEFT + info RIGHT. Minimal, no redundancy."""
    title_esc = html.escape(p.title[:70])
    price_esc = html.escape(p.price_str or "—")
    link_esc = html.escape(p.link)
    stars_str = _stars(p.stars)
    reviews_count = p.reviews if p.reviews else 0
    review_confidence = "●●●" if reviews_count > 100 else "●●" if reviews_count > 10 else "●"
    badge_html = _badge(p)
    dedup_badge_html = _dedup_badge(p)
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

    return f"""
    <div class="card" data-price="{price_data}" data-stars="{stars_data}" data-idx="{idx}">
        <div class="card-img">{thumb_html}</div>
        <div class="card-info">
            <div class="card-title">{title_esc}</div>
            <div class="card-rating">{stars_str} <span class="confidence">{review_confidence}</span> <span class="reviews">({reviews_count})</span></div>
            <div class="card-price">{price_esc}</div>
            {badge_html}
            {dedup_badge_html}
            {specs_html}
            <a href="{link_esc}" target="_blank" class="btn-cta">Vedi su Amazon</a>
        </div>
    </div>"""


def generate_html(
    products: list,
    query: str,
    *,
    summary: str = "",
    quota_info: str = "",
    output_dir: Path = OUTPUT_DIR,
) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"amazon_{_slug(query)}_{ts}.html"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename

    cards_html = "\n".join(_card(p, i) for i, p in enumerate(products))
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
html,body{{height:100%;background:#f5f5f5}}
body{{font-family:-apple-system,BlinkMacSystemFont,Roboto,sans-serif;color:#1a1a1a;line-height:1.5;-webkit-font-smoothing:antialiased}}

.header{{background:#232f3e;color:#fff;padding:10px 16px;position:sticky;top:0;z-index:100;display:flex;justify-content:space-between;align-items:center;gap:12px}}
.header h1{{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.header .sub{{font-size:11px;color:#aaa;margin-top:2px}}
.btn-filter{{background:#0066c0;color:#fff;border:none;padding:8px 12px;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0;transition:background 0.2s,transform 0.1s}}
.btn-filter:active{{background:#004494;transform:scale(0.95)}}

.filter-chips{{background:#fff;padding:8px 16px;border-bottom:1px solid #e0e0e0;display:flex;gap:8px;overflow-x:auto;-webkit-overflow-scrolling:touch}}
.chip{{background:#e3f2fd;color:#0066c0;padding:6px 10px;border-radius:16px;font-size:12px;display:inline-flex;align-items:center;gap:6px;white-space:nowrap;flex-shrink:0;cursor:pointer;border:1px solid #90caf9;transition:all 0.2s}}
.chip:active{{background:#bbdefb;transform:scale(0.95)}}
.chip.removing{{animation:fadeOut 0.2s ease forwards}}
@keyframes fadeOut{{to{{opacity:0;transform:scale(0.9)}}}}
.chip-close{{color:#0066c0;font-weight:bold;cursor:pointer}}

.controls{{background:#fff;padding:10px 16px;border-bottom:1px solid #e0e0e0;display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#666}}
.sort-ctrl{{background:#fff;border:1px solid #ccc;padding:6px 10px;border-radius:4px;font-size:13px;cursor:pointer;transition:border-color 0.2s}}
.sort-ctrl:active{{border-color:#0066c0}}

.summary{{background:#fffbe6;border-left:3px solid #ffc107;padding:12px 16px;margin:12px 16px 0;border-radius:4px;font-size:13px;line-height:1.5;color:#666}}

.grid{{display:flex;flex-direction:column;gap:12px;padding:12px 16px;padding-bottom:80px}}

.card{{background:#fff;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.1);overflow:hidden;transition:box-shadow 0.2s}}
.card:active{{box-shadow:0 2px 8px rgba(0,0,0,0.15);animation:cardPulse 0.3s ease}}
@keyframes cardPulse{{0%{{transform:scale(1)}}50%{{transform:scale(1.01)}}100%{{transform:scale(1)}}}}

.card-link{{display:flex;gap:12px;padding:12px;text-decoration:none;color:inherit;cursor:pointer;transition:background 0.2s}}
.card-link:active{{background:#f9f9f9}}

.card-img{{flex-shrink:0;width:100px;height:90px;background:#f8f8f8;border-radius:4px;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.card-img img{{max-width:100%;max-height:100%;object-fit:contain}}
.no-img{{font-size:2rem;color:#ccc}}

.card-info{{flex:1;display:flex;flex-direction:column;gap:6px;min-width:0}}

.card-title{{font-size:14px;font-weight:600;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}

.card-rating{{font-size:12px;color:#666;display:flex;gap:4px;align-items:center}}
.card-rating strong{{color:#f5a623;font-size:13px}}
.confidence{{color:#999;font-size:10px;letter-spacing:1px}}
.reviews{{color:#999;font-size:11px}}

.card-price{{font-size:18px;font-weight:700;color:#d32f2f}}

.badge-alert{{background:#d32f2f;color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600}}
.badge-prime{{background:#007bff;color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600}}
.badge-dedup{{display:inline-block;background:#16a34a;color:#fff;padding:3px 8px;border-radius:12px;font-size:11px;font-weight:600}}

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

@media (max-width:320px){{
.card-img{{width:80px;height:70px}}
.card-title{{font-size:13px}}
.card-price{{font-size:16px}}
}}
</style>
</head>
<body>

<div class="header">
  <h1>{html.escape(query[:40])}</h1>
  <button class="btn-filter" onclick="openDrawer()">Filtri</button>
</div>

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

<div class="grid" id="grid">
{cards_html}
</div>

<div class="no-results hidden" id="noResults">
Nessun prodotto trovato<br><small>Prova a rimuovere i filtri</small>
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
