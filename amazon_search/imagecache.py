# -*- coding: utf-8 -*-
"""Scraping immagini prodotto Amazon (httpx) con cache su disco.

Deterministico + veloce: una volta scaricate le URL di un ASIN, restano in cache.
NON usa SerpAPI/Canopy (zero quota). Le immagini DISTINTE si ricavano dal campo
"large" della pagina /dp/ASIN (un'occorrenza per scatto -> niente doppioni hiRes/large).
"""
from __future__ import annotations
import base64
import json
import re
from pathlib import Path

import httpx

_UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36"),
    "Accept-Language": "it-IT,it;q=0.9",
}
_CACHE = Path.home() / ".amazon_report_cache"
_IMG_JSON = _CACHE / "image_urls.json"
_LARGE_RE = re.compile(r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+?\.jpg)"')
_ID_RE = re.compile(r"/I/([^.]+)\.")


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(path: Path, data: dict) -> None:
    _CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def image_urls(asin: str, domain: str = "it", n: int = 3,
               *, retries: int = 3, timeout: float = 30.0) -> list[str]:
    """URL di n scatti DISTINTI per ASIN. Cache su disco. Lista vuota se fallisce."""
    cache = _load(_IMG_JSON)
    if asin in cache and cache[asin]:
        return cache[asin][:n]
    url = f"https://www.amazon.{domain}/dp/{asin}"
    for _ in range(retries):
        try:
            r = httpx.get(url, timeout=timeout, follow_redirects=True, headers=_UA)
            if r.status_code != 200:
                continue
            seen, uniq = set(), []
            for u in _LARGE_RE.findall(r.text):
                m = _ID_RE.search(u)
                key = m.group(1) if m else u
                if key not in seen:
                    seen.add(key)
                    uniq.append(u)
            if uniq:
                cache[asin] = uniq
                _save(_IMG_JSON, cache)
                return uniq[:n]
        except Exception:
            continue
    return []


def local_path(asin: str, domain: str = "it", *, timeout: float = 20.0) -> str:
    """Download the primary product photo to a real file on disk and return its
    path (empty string on failure). For dedup.py's pHash comparison, which
    needs a local file, not a data: URI."""
    import hashlib
    urls = image_urls(asin, domain=domain, n=1)
    if not urls:
        return ""
    fp = _CACHE / f"{hashlib.md5(urls[0].encode()).hexdigest()[:16]}.jpg"
    if fp.exists() and fp.stat().st_size > 0:
        return str(fp)
    try:
        r = httpx.get(urls[0], timeout=timeout, follow_redirects=True, headers=_UA)
        if r.status_code == 200 and len(r.content) > 200:
            _CACHE.mkdir(exist_ok=True)
            fp.write_bytes(r.content)
            return str(fp)
    except Exception:
        pass
    return ""


def data_uri(url: str, *, timeout: float = 20.0) -> str:
    """Scarica un'immagine e la restituisce come data: URI base64 (per HTML/PDF self-contained)."""
    if not url:
        return ""
    try:
        r = httpx.get(url, timeout=timeout, follow_redirects=True)
        if r.status_code == 200:
            ct = r.headers.get("content-type", "image/jpeg")
            return f"data:{ct};base64,{base64.b64encode(r.content).decode()}"
    except Exception:
        pass
    return ""


def two_images(asin: str, fallback_thumb: str = "", *, domain: str = "it") -> tuple[str, str]:
    """Due data-URI distinti per ASIN; usa il thumbnail SerpAPI come fallback."""
    urls = image_urls(asin, domain=domain, n=3)
    if len(urls) >= 2:
        return data_uri(urls[0]), data_uri(urls[1])
    if len(urls) == 1:
        return data_uri(urls[0]), data_uri(fallback_thumb or urls[0])
    th = (fallback_thumb or "").replace("_AC_UL320_", "_AC_SL400_")
    d = data_uri(th)
    return d, d
