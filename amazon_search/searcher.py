"""Amazon product search with cache + parallel APIs.

Priority:
  1. Cache check (deterministic, no quota cost)
  2. SerpAPI + SearchAPI parallel (return first)
  3. Fallback if both fail
"""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

import httpx

import amazon_search.config  # noqa: F401 — loads keys into env
from amazon_search import cache, config_search, logger, quota

SERPAPI_BASE = "https://serpapi.com"
SEARCHAPI_BASE = "https://www.searchapi.io"
TIMEOUT = config_search.TIMEOUT_API


@dataclass
class AmazonProduct:
    title: str
    asin: str
    brand: str | None
    price: float | None
    price_str: str
    stars: float | None
    reviews: int | None
    thumbnail: str | None
    link: str
    prime: bool
    in_stock: bool
    source: str  # "serpapi" | "searchapi"
    bullets: list[str] = field(default_factory=list)
    specs: dict[str, str] = field(default_factory=dict)
    dedup_note: str | None = None  # set by --dedup: "same item also seen for €X less"


# first word of a listing title that is NOT a brand — generic product/marketing words.
# Deliberately conservative: a wrong brand is worse than no brand (grouping/filtering lie).
_NOT_BRAND = {
    "nuovo", "new", "set", "kit", "mini", "maxi", "smart", "auto", "per", "the",
    "collare", "cuscino", "supporto", "subwoofer", "custodia", "cover", "cavo",
    "caricatore", "caricabatterie", "batteria", "lampada", "luce", "led", "wireless",
    "bluetooth", "portatile", "universale", "professionale", "premium", "original",
    "originale", "upgrade", "confezione", "pezzi", "paia", "coppia", "adattatore",
}


def guess_brand(title: str) -> str | None:
    """Best-effort brand from the title's first token. Amazon brands sit first
    ("VELPEAU Collare...", "JBL BassPro..."); only fills the gap when the API gave
    none — never overwrites. Returns None unless the token looks brand-like."""
    tok = (title or "").split()[0] if (title or "").split() else ""
    tok = tok.strip("®™,.:;-—()[]")
    if not (2 <= len(tok) <= 20) or not tok[0].isalpha():
        return None
    if tok.lower() in _NOT_BRAND:
        return None
    if not (tok.isupper() or tok[0].isupper()):
        return None
    return tok


def _parse_price(item: dict) -> tuple[float | None, str]:
    raw = item.get("price", "")
    extracted = item.get("extracted_price")
    try:
        val = float(extracted) if extracted is not None else float(
            str(raw).replace("€", "").replace(",", ".").replace(".", "", str(raw).count(".") - 1).strip()
        )
        return val, str(raw)
    except (ValueError, TypeError):
        return None, str(raw)


def _serpapi_search(query: str, max_results: int, domain: str) -> list[AmazonProduct] | None:
    """Returns products or None on error."""
    key = os.environ.get("SERPAPI_KEY", "")
    if not key or not quota.check("serpapi"):
        return None

    amazon_domain = {
        "IT": "amazon.it", "DE": "amazon.de", "UK": "amazon.co.uk",
        "FR": "amazon.fr", "ES": "amazon.es", "US": "amazon.com",
    }.get(domain.upper(), f"amazon.{domain.lower()}")

    try:
        # una pagina SerpAPI = ~15-22 organici = 1 credito; per pool grandi (100+)
        # si pagina finché servono risultati. Stop a pagina vuota o quota esaurita.
        raw: list[dict] = []
        page = 1
        with httpx.Client(timeout=TIMEOUT) as client:
            while len(raw) < max_results and page <= 7:
                if not quota.check("serpapi"):
                    break
                quota.increment("serpapi")
                resp = client.get(
                    f"{SERPAPI_BASE}/search.json",
                    params={
                        "engine": "amazon",
                        "k": query,
                        "amazon_domain": amazon_domain,
                        "api_key": key,
                        "num": max_results,
                        "page": page,
                    },
                )
                resp.raise_for_status()
                batch = resp.json().get("organic_results") or []
                if not batch:
                    break
                raw.extend(batch)
                page += 1

        seen_asins: set[str] = set()
        products = []
        for item in raw[:max_results]:
            if item.get("asin"):
                if item["asin"] in seen_asins:
                    continue
                seen_asins.add(item["asin"])
            price_val, price_str = _parse_price(item)
            asin = item.get("asin", "")
            link = item.get("link") or (f"https://{amazon_domain}/dp/{asin}" if asin else "#")
            delivery = str(item.get("delivery", ""))

            products.append(AmazonProduct(
                title=item.get("title", ""),
                asin=asin,
                brand=item.get("brand") or guess_brand(item.get("title", "")),
                price=price_val,
                price_str=price_str,
                stars=item.get("rating"),
                reviews=item.get("ratings_total") or item.get("reviews"),
                thumbnail=item.get("thumbnail"),
                link=link,
                prime="Prime" in delivery or bool(item.get("prime")),
                in_stock=str(item.get("availability", "")).lower() not in ("out of stock", "non disponibile"),
                source="serpapi",
            ))
        return products if products else None
    except Exception as e:
        quota.decrement("serpapi")
        print(f"[SerpAPI error: {e}]")
        return None


def _searchapi_search(query: str, max_results: int, domain: str) -> list[AmazonProduct] | None:
    """Returns products or None on error."""
    key = os.environ.get("SEARCHAPI_KEY", "")
    if not key or not quota.check("searchapi"):
        return None

    amazon_domain = {
        "IT": "amazon.it", "DE": "amazon.de", "UK": "amazon.co.uk",
        "FR": "amazon.fr", "ES": "amazon.es", "US": "amazon.com",
    }.get(domain.upper(), f"amazon.{domain.lower()}")

    try:
        quota.increment("searchapi")
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.get(
                f"{SEARCHAPI_BASE}/api/v1/search",
                params={
                    "engine": "amazon",
                    "q": query,
                    "amazon_domain": amazon_domain,
                    "api_key": key,
                    "num": max_results,
                },
            )
            resp.raise_for_status()

        data = resp.json()
        raw = data.get("organic_results") or []

        products = []
        for item in raw[:max_results]:
            price_val, price_str = _parse_price(item)
            asin = item.get("asin", "")
            link = item.get("link") or (f"https://{amazon_domain}/dp/{asin}" if asin else "#")

            products.append(AmazonProduct(
                title=item.get("title", ""),
                asin=asin,
                brand=item.get("brand") or guess_brand(item.get("title", "")),
                price=price_val,
                price_str=price_str,
                stars=item.get("rating"),
                reviews=item.get("ratings_total") or item.get("reviews"),
                thumbnail=item.get("thumbnail"),
                link=link,
                prime=bool(item.get("prime", False)),
                in_stock=True,
                source="searchapi",
            ))
        return products if products else None
    except Exception as e:
        quota.decrement("searchapi")
        print(f"[SearchAPI error: {e}]")
        return None


class AmazonSearcher:
    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        max_price: float | None = None,
        min_stars: float | None = None,
        domain: str = "IT",
    ) -> list[AmazonProduct]:
        start_time = time.time()
        quota_before = {
            "serpapi": quota.used("serpapi"),
            "canopy": quota.used("canopy"),
            "searchapi": quota.used("searchapi"),
        }

        # 1. Check cache
        cached = cache.get(query, domain, max_price, min_stars)
        if cached:
            products = []
            for item in cached:
                p = AmazonProduct(**item)
                products.append(p)
            # Apply filters to cached products
            if max_price is not None:
                products = [p for p in products if p.price is None or p.price <= max_price]
            if min_stars is not None:
                products = [p for p in products if p.stars is None or p.stars >= min_stars]
            print(f"[cache hit] {len(products)} prodotti")

            duration = time.time() - start_time
            quota_after = {
                "serpapi": quota.used("serpapi"),
                "canopy": quota.used("canopy"),
                "searchapi": quota.used("searchapi"),
            }
            logger.log_search(
                query, domain, len(products), "cache",
                duration, quota_before, quota_after, cache_hit=True
            )
            return products

        # 2. Parallel search: SerpAPI + SearchAPI
        products: list[AmazonProduct] = []
        source_used = None
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(_serpapi_search, query, max_results, domain): "serpapi",
            }
            if config_search.SEARCHAPI_ENABLED:
                futures[executor.submit(_searchapi_search, query, max_results, domain)] = "searchapi"

            for future in as_completed(futures, timeout=config_search.PARALLEL_TIMEOUT_PER_API + 5):
                result = future.result()
                if result:
                    products = result
                    source_used = futures[future]
                    print(f"[{source_used} OK] {len(products)} prodotti")
                    break

        if not products:
            raise RuntimeError("Nessun risultato dalle API disponibili.")

        # 3. Apply filters
        if max_price is not None:
            products = [p for p in products if p.price is None or p.price <= max_price]
        if min_stars is not None:
            products = [p for p in products if p.stars is None or p.stars >= min_stars]

        # 4. Cache results
        cache.set(query, domain, max_price, min_stars, products)

        duration = time.time() - start_time
        quota_after = {
            "serpapi": quota.used("serpapi"),
            "canopy": quota.used("canopy"),
            "searchapi": quota.used("searchapi"),
        }
        logger.log_search(
            query, domain, len(products), source_used or "unknown",
            duration, quota_before, quota_after, cache_hit=False
        )

        return products
