# -*- coding: utf-8 -*-
"""Scraping e caching immagini per prodotti Amazon.

Questa componente gestisce il download locale delle immagini e la loro conversione
in formato Base64 (data: URI) per rendere i report HTML completamente autonomi (offline).
"""
from __future__ import annotations
import base64
import json
import re
import os
import glob
from pathlib import Path
import httpx

_CACHE = Path.home() / ".amazon_report_cache"
_IMG_JSON = _CACHE / "image_urls.json"

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_HEADERS = {
    "User-Agent": _UA,
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

def _load_json(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _save_json(path: Path, data: dict) -> None:
    try:
        _CACHE.mkdir(exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass

_MEM_URL_MAP = None

def _find_url_in_search_cache(asin: str) -> str:
    """Cerca l'URL del thumbnail del prodotto nei cache file locali di SerpAPI/Amazon Search."""
    global _MEM_URL_MAP
    if _MEM_URL_MAP is None:
        _MEM_URL_MAP = {}
        # 1. Cerca nell'offline dataset
        offline_file = Path.home() / ".amazon_search_offline.json"
        if offline_file.exists():
            try:
                data = json.loads(offline_file.read_text(encoding="utf-8"))
                for p in data.get("products", []):
                    if p.get("asin") and p.get("thumbnail"):
                        _MEM_URL_MAP[p["asin"]] = p["thumbnail"]
            except Exception:
                pass
        
        # 2. Cerca in ~/.amazon_search_cache/*.json
        search_cache_dir = Path.home() / ".amazon_search_cache"
        if search_cache_dir.exists():
            for f in glob.glob(str(search_cache_dir / "*.json")):
                try:
                    data = json.loads(Path(f).read_text(encoding="utf-8"))
                    products = data.get("products") if isinstance(data, dict) else data
                    if isinstance(products, list):
                        for p in products:
                            if p.get("asin") and p.get("thumbnail"):
                                _MEM_URL_MAP[p["asin"]] = p["thumbnail"]
                except Exception:
                    continue

    return _MEM_URL_MAP.get(asin, "")

def image_urls(asin: str, domain: str = "it", n: int = 3,
               *, retries: int = 2, timeout: float = 8.0) -> list[str]:
    """Ottiene fino a n URL di immagini distinte per un dato ASIN.
    
    Tenta prima il caricamento da cache locale o dai file di ricerca per evitare
    chiamate di scraping bloccanti. Se non trova nulla, effettua lo scraping della pagina /dp/ASIN.
    """
    cache = _load_json(_IMG_JSON)
    if asin in cache and cache[asin]:
        return cache[asin][:n]
        
    # Cerca l'URL primario nella cache delle ricerche per evitare di scaricare la pagina di Amazon
    primary_url = _find_url_in_search_cache(asin)
    urls = []
    if primary_url:
        urls.append(primary_url)
        
    # Se non abbiamo trovato nulla o vogliamo più immagini di 1, proviamo lo scraping leggero
    if not urls or n > 1:
        url = f"https://www.amazon.{domain}/dp/{asin}"
        for _ in range(retries):
            try:
                # Usa client httpx standard con timeout ridotto per non bloccare
                with httpx.Client(headers=_HEADERS, timeout=timeout, follow_redirects=True) as client:
                    r = client.get(url)
                    if r.status_code == 200:
                        # Estrai le immagini ad alta risoluzione (large)
                        found = re.findall(r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+?\.jpg)"', r.text)
                        # Rendi unici gli ID delle immagini per non avere duplicati
                        seen_ids = set()
                        scraped_urls = []
                        for img_url in found:
                            m = re.search(r"/I/([^.]+)\.", img_url)
                            img_id = m.group(1) if m else img_url
                            if img_id not in seen_ids:
                                seen_ids.add(img_id)
                                scraped_urls.append(img_url)
                        
                        # Unisci e mantieni l'ordine
                        for u in scraped_urls:
                            if u not in urls:
                                urls.append(u)
                        break
            except Exception:
                continue
                
    if urls:
        cache[asin] = urls
        _save_json(_IMG_JSON, cache)
        return urls[:n]
        
    return []

def local_path(asin: str, domain: str = "it", *, timeout: float = 8.0) -> str:
    """Scarica la foto principale del prodotto su disco e ritorna il percorso assoluto.
    
    Usato principalmente per il confronto pHash/SIFT che richiede file locali.
    """
    urls = image_urls(asin, domain=domain, n=1)
    if not urls:
        return ""
        
    img_url = urls[0]
    _CACHE.mkdir(exist_ok=True)
    
    # Nome file deterministico basato su ASIN per semplicità e velocità
    fp = _CACHE / f"{asin}.jpg"
    if fp.exists() and fp.stat().st_size > 0:
        return str(fp)
        
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(img_url)
            if r.status_code == 200 and len(r.content) > 200:
                fp.write_bytes(r.content)
                return str(fp)
    except Exception:
        pass
        
    return ""

def data_uri(url: str, *, timeout: float = 8.0) -> str:
    """Scarica un'immagine e la restituisce codificata come base64 data URI."""
    if not url:
        return ""
        
    # Se è già un data URI, ritornalo
    if url.startswith("data:"):
        return url
        
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            r = client.get(url)
            if r.status_code == 200:
                ct = r.headers.get("content-type", "image/jpeg")
                b64 = base64.b64encode(r.content).decode("utf-8")
                return f"data:{ct};base64,{b64}"
    except Exception:
        pass
    return ""

def two_images(asin: str, fallback_thumb: str = "", *, domain: str = "it") -> tuple[str, str]:
    """Ottiene due data URI distinti per il prodotto.
    
    Usa la cache locale e le foto disponibili, ricadendo sul thumbnail se necessario.
    """
    urls = image_urls(asin, domain=domain, n=2)
    
    img1, img2 = "", ""
    if len(urls) >= 2:
        img1 = data_uri(urls[0])
        img2 = data_uri(urls[1])
    elif len(urls) == 1:
        img1 = data_uri(urls[0])
        img2 = img1
    
    # Se il caricamento o download ha fallito, usa il fallback
    if not img1 and fallback_thumb:
        img1 = data_uri(fallback_thumb)
        img2 = img1
        
    # Se tutto fallisce, usa un placeholder SVG
    placeholder = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'><rect width='100' height='100' fill='%23eee'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' font-family='sans-serif' font-size='12' fill='%23aaa'>No Img</text></svg>"
    
    return img1 or placeholder, img2 or placeholder
