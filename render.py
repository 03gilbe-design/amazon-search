# -*- coding: utf-8 -*-
"""Libreria di rendering generica per report prodotti: tag, icone SVG, card, HTML.

Riusabile per QUALSIASI categoria. La logica specifica (quali tag, quali colonne)
sta nel chiamante: qui ci sono solo i mattoni di presentazione, deterministici.

Concetti:
- Tag = (label, color, icon_svg). Costruiscili con tag().
- Card = immagini + titolo + prezzo + voti + lista di tag + righe metriche + bottone.
- render_html(meta, sections) produce un HTML self-contained (immagini base64 inline).
"""
from __future__ import annotations
import html
from dataclasses import dataclass, field

# ---------- icone SVG (no emoji) ----------
def svg(inner: str, w: int = 12, h: int = 12, extra: str = "") -> str:
    return (f'<svg viewBox="0 0 16 16" width="{w}" height="{h}" style="vertical-align:-2px;{extra}" '
            f'fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" '
            f'stroke-linejoin="round">{inner}</svg>')

ICONS = {
    "check2":  svg('<path d="M2 8l3 3 5-6"/><path d="M8 11l3 3 5-6"/>'),   # doppia spunta
    "check":   svg('<path d="M3 8.5l3.5 3.5L13 4.5"/>'),                   # spunta
    "info":    svg('<path d="M8 3v7"/><circle cx="8" cy="13" r="0.6" fill="#fff" stroke="none"/>'),
    "warning": svg('<path d="M8 2L1.5 14h13z"/><path d="M8 7v3.5"/>'),
    "cross":   svg('<path d="M4 4l8 8M12 4l-8 8"/>'),
    "question":svg('<path d="M5.5 6a2.5 2.5 0 113.5 2.3c-.7.3-1 .8-1 1.7"/><circle cx="8" cy="13" r="0.6" fill="#fff" stroke="none"/>'),
    "glass":   svg('<path d="M6 2h4M6.6 2v3.5L4 12.5A1.4 1.4 0 005.3 14.5h5.4A1.4 1.4 0 0012 12.5L9.4 5.5V2"/>'),
    "up":      svg('<path d="M8 13V4M4.5 7.5L8 4l3.5 3.5"/>'),
    "down":    svg('<path d="M8 3v9M4.5 8.5L8 12l3.5-3.5"/>'),
    "bolt":    svg('<path d="M9 2L3.5 9H8l-1 5 5.5-7H8z"/>'),              # potenza
    "ruler":   svg('<path d="M2 6h12v4H2zM5 6v2M8 6v2M11 6v2"/>'),        # dimensioni
    "star":    svg('<path d="M8 2l1.8 3.9 4.2.5-3.1 2.9.9 4.2L8 11.8 4.3 13.6l.9-4.2L2 6.4l4.2-.5z"/>'),
}

def resin_triangle(code: str) -> str:
    """Triangolo riciclo con numero = codice resina plastica."""
    return (f'<svg viewBox="0 0 18 18" width="13" height="13" style="vertical-align:-2px">'
            f'<path d="M9 2.5L15.5 14.5H2.5Z" fill="none" stroke="#fff" stroke-width="1.4"/>'
            f'<text x="9" y="13" font-size="8" fill="#fff" text-anchor="middle" '
            f'font-family="Arial" font-weight="700">{html.escape(code)}</text></svg>')

# scala materiale riusabile (vs solventi/alcol)
MATERIAL_TIERS = {
    "perfetto": ("#15803d", "TOP"), "ottimo": ("#16a34a", "BUONA"),
    "buono": ("#65a30d", "discreta"), "discreto": ("#ca8a04", "cosi-cosi"),
    "scarso": ("#ea580c", "scarsa"), "pessimo": ("#dc2626", "NO"),
    "inadatto": ("#991b1b", "NO"), "ignoto": ("#b45309", "DA VERIFICARE"),
}


@dataclass
class Tag:
    label: str
    color: str = "#64748b"
    icon: str = ""          # chiave in ICONS, o SVG gia' pronto, o ""
    bold_suffix: str = ""   # parte sottolineata/grassetto in coda (es. verdetto)

    def html(self) -> str:
        ico = ICONS.get(self.icon, self.icon)
        suf = f' &middot; <b>{html.escape(self.bold_suffix)}</b>' if self.bold_suffix else ""
        return (f'<span class="chip" style="background:{self.color}">'
                f'{ico}&nbsp;{html.escape(self.label)}{suf}</span>')


@dataclass
class Metric:
    label: str
    value: str
    accent: str = "#d6d3d1"   # colore barra laterale

    def html(self) -> str:
        return (f'<div class="metric" style="border-left-color:{self.accent}">'
                f'<b>{html.escape(self.label)}:</b> {html.escape(self.value)}</div>')


@dataclass
class Card:
    asin: str
    title: str
    price: str = ""
    rating: str = ""        # es. "4.6 (1472)"
    img1: str = ""          # data URI
    img2: str = ""
    tags: list = field(default_factory=list)      # list[Tag]
    metrics: list = field(default_factory=list)   # list[Metric]
    note: str = ""          # descrizione/perche'
    badge: str = ""         # etichetta evidenza (es. "CONSIGLIATO")
    domain: str = "it"

    def html(self) -> str:
        badge = f'<span class="badge">{html.escape(self.badge)}</span>' if self.badge else ""
        rate = f'&#9733; {html.escape(self.rating)}' if self.rating else ""
        tags = "".join(t.html() for t in self.tags)
        mets = "".join(m.html() for m in self.metrics)
        link = f"https://www.amazon.{self.domain}/dp/{self.asin}"
        return (f'<div class="card"><div class="imgcol">'
                f'<div class="imgwrap"><img src="{self.img1}"></div>'
                f'<div class="imgwrap"><img src="{self.img2}"></div></div>'
                f'<div class="body">'
                f'<div class="ttop">{badge}<span class="price">{html.escape(self.price)}</span>'
                f'<span class="rate">{rate}</span></div>'
                f'<div class="chips">{tags}</div>'
                f'<div class="title">{html.escape(self.title)}</div>'
                f'<div class="why">{html.escape(self.note)}</div>{mets}'
                f'<a class="btn" href="{link}" target="_blank" rel="noopener">'
                f'Apri su Amazon (nuova scheda) &rarr; {self.asin}</a></div></div>')


@dataclass
class Section:
    title: str
    subtitle: str = ""
    cards: list = field(default_factory=list)  # list[Card]
    note: str = ""

    def html(self) -> str:
        cards = "".join(c.html() for c in self.cards)
        note = f'<p class="nota">{html.escape(self.note)}</p>' if self.note else ""
        return (f'<section><h3>{self.title}</h3>'
                f'<p class="sub">{html.escape(self.subtitle)}</p>{cards}{note}</section>')


_CSS = """
@page{size:A4;margin:12mm;}*{box-sizing:border-box;}
body{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:#2b2118;margin:0;}
@media screen{body{max-width:820px;margin:0 auto;padding:22px 26px;}html{background:#f4f1ec;}}
h1{font-size:23px;margin:0 0 6px;color:#c2410c;}
.lead{font-size:11.5px;color:#5c554c;margin:0 0 14px;line-height:1.5;}
.htmlonly{background:#ecfdf5;border:1px solid #6ee7b7;border-radius:8px;padding:7px 11px;font-size:10px;color:#065f46;margin:0 0 10px;}
@media print{.htmlonly{display:none;}}
.part{color:#fff;border-radius:10px;padding:9px 14px;margin:14px 0 6px;font-size:16px;font-weight:800;}
.part small{font-weight:500;font-size:11px;opacity:.92;display:block;margin-top:2px;}
h3{font-size:13.5px;margin:14px 0 2px;color:#9a3412;border-bottom:2px solid #fed7aa;padding-bottom:3px;}
.sub{font-size:10.5px;color:#7c6f61;margin:3px 0 9px;line-height:1.45;}
.legend{font-size:9.5px;color:#444;margin:0 0 12px;line-height:1.95;}
.legend b{display:block;color:#9a3412;font-size:10.5px;margin-bottom:3px;}
.legend .chip{margin:0 4px 3px 0;}
.card{display:flex;gap:12px;border:1px solid #f0e3d4;border-radius:12px;padding:10px;margin:8px 0;background:#fffdfb;page-break-inside:avoid;}
.imgcol{flex:0 0 96px;display:flex;flex-direction:column;gap:6px;}
.imgwrap{width:96px;height:80px;display:flex;align-items:center;justify-content:center;background:#fff;border-radius:8px;border:1px solid #f3ece3;}
.imgwrap img{max-width:92px;max-height:76px;object-fit:contain;}
.body{flex:1;min-width:0;}
.ttop{display:flex;align-items:center;gap:7px;margin-bottom:4px;flex-wrap:wrap;}
.badge{background:#0e7490;color:#fff;font-size:8.5px;font-weight:700;padding:2px 8px;border-radius:20px;}
.price{font-weight:700;color:#57534e;font-size:13px;}.rate{color:#78716c;font-size:10.5px;}
.chips{display:flex;gap:6px;margin-bottom:4px;flex-wrap:wrap;}
.chip{color:#fff;font-size:9.5px;font-weight:700;padding:2px 9px;border-radius:20px;display:inline-flex;align-items:center;}
.chip b{font-weight:800;text-decoration:underline;}
.title{font-size:11.5px;font-weight:600;line-height:1.3;margin-bottom:4px;color:#33302b;}
.why{font-size:10.5px;color:#4a463f;line-height:1.45;margin-bottom:5px;}
.metric{font-size:10px;color:#4a463f;line-height:1.4;margin-bottom:3px;padding:3px 0 3px 9px;border-left:2px solid #d6d3d1;}
.metric b{color:#33302b;font-weight:700;}
.nota{font-size:10px;color:#15803d;background:#f0fdf4;border-left:3px solid #16a34a;padding:6px 10px;border-radius:0 6px 6px 0;margin:4px 0 0;line-height:1.45;}
.btn{display:inline-block;background:#ea580c;color:#fff !important;text-decoration:none;font-size:10px;font-weight:600;padding:5px 10px;border-radius:8px;margin-top:5px;}
.foot{margin-top:16px;font-size:9px;color:#9a8d7e;border-top:1px solid #f0e3d4;padding-top:7px;}
"""


def render_html(title: str, lead: str, sections: list, *, legend: str = "", foot: str = "") -> str:
    body = "".join(s.html() for s in sections)
    leg = f'<div class="legend">{legend}</div>' if legend else ""
    return (f'<!doctype html><html lang="it"><head><meta charset="utf-8"><style>{_CSS}</style></head><body>'
            f'<div class="htmlonly">Versione HTML: i bottoni &laquo;Apri su Amazon&raquo; aprono in '
            f'<b>nuova scheda</b>. (Nel PDF il link apre nello stesso visualizzatore: limite dei PDF.)</div>'
            f'<h1>{title}</h1><p class="lead">{lead}</p>{leg}{body}'
            f'<p class="foot">{foot}</p></body></html>')
