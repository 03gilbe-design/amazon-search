# -*- coding: utf-8 -*-
"""Orchestratore report Amazon: search -> specs -> immagini -> HTML(+PDF).

Deterministico e parametrico. Riusa searcher (SerpAPI), specs (Canopy),
imagecache (httpx) e render (presentazione). Una categoria = una funzione
che mappa i prodotti in Card; il motore fa il resto.

Uso libreria:
    from amazon_search.report import collect, to_pdf
    items = collect("subwoofer underseat", n=12, specs=True)   # lista dict arricchiti
    # ... costruisci sezioni/Card con render.py ...

Uso CLI (lista veloce):
    python -m amazon_search.report "subwoofer underseat" --specs
"""
from __future__ import annotations
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import amazon_search.config  # noqa: F401  carica le key in env
from amazon_search.searcher import AmazonSearcher
from amazon_search import imagecache

try:
    from amazon_search.specs import fetch_specs
except Exception:  # specs opzionale
    fetch_specs = None


def collect(query: str, *, n: int = 12, domain: str = "IT",
            specs: bool = False, specs_top: int = 6, images: bool = False,
            images_top: int = 0) -> list[dict]:
    """Cerca + (opz.) arricchisce con specs Canopy e immagini. Ritorna lista dict."""
    s = AmazonSearcher()
    prods = s.search(query, max_results=n, domain=domain)
    items = [asdict(p) for p in prods]

    if specs and fetch_specs:
        asins = [it["asin"] for it in items[:specs_top] if it.get("asin")]
        smap = fetch_specs(asins, domain=domain) if asins else {}
        for it in items:
            d = smap.get(it.get("asin"), {})
            it["specs"] = d.get("specs") or {}
            if d.get("bullets"):
                it["bullets"] = d["bullets"]

    if images:
        topN = images_top or len(items)
        dom = domain.lower()
        for it in items[:topN]:
            if it.get("asin"):
                it["img1"], it["img2"] = imagecache.two_images(
                    it["asin"], it.get("thumbnail", ""), domain=dom)
    return items


def to_pdf(html_path: str | Path, pdf_path: str | Path) -> bool:
    """Converte un HTML in PDF via Chrome headless. True se ok."""
    chrome = _find_chrome()
    if not chrome:
        return False
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    try:
        subprocess.run([chrome, "--headless=new", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        html_path.as_uri()], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return pdf_path.exists()
    except Exception:
        return False


def _find_chrome() -> str | None:
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"):
        if Path(c).exists():
            return c
    return shutil.which("chrome") or shutil.which("google-chrome")


def _cli() -> None:
    args = sys.argv[1:]
    if not args:
        print('uso: python -m amazon_search.report "query" [--specs] [--n 12] [--json out.json]')
        return
    query = args[0]
    specs = "--specs" in args
    n = 12
    if "--n" in args:
        n = int(args[args.index("--n") + 1])
    out = None
    if "--json" in args:
        out = args[args.index("--json") + 1]

    items = collect(query, n=n, specs=specs)
    print(f"\n=== {len(items)} prodotti per: {query} ===")
    for it in items:
        line = f"{it.get('asin')} | {str(it.get('price_str')):>9} | {it.get('stars')}*({it.get('reviews')}) | {(it.get('title') or '')[:48]}"
        print(line)
        if specs and it.get("specs"):
            wanted = [k for k in it["specs"] if any(
                w in k.lower() for w in ("watt", "potenz", "rms", "frequenz", "impedenz",
                                          "dimension", "materiale", "peso", "diametro"))]
            for k in wanted[:4]:
                print(f"       {k}: {it['specs'][k]}")
    if out:
        Path(out).write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nsalvato {out}")


if __name__ == "__main__":
    _cli()
