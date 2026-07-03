"""Query cache. Dedup ricerche <1h vecchie."""
import hashlib
import json
import time
from pathlib import Path

CACHE_DIR = Path.home() / ".amazon_search_cache"
CACHE_TTL = 3600  # 1 hour


def _hash_query(query: str, domain: str, max_price: float | None, min_stars: float | None) -> str:
    key = f"{query}|{domain}|{max_price}|{min_stars}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def _ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get(query: str, domain: str, max_price: float | None, min_stars: float | None) -> list | None:
    """Return cached products if valid, None if miss/expired."""
    _ensure_cache_dir()
    qid = _hash_query(query, domain, max_price, min_stars)
    cache_file = CACHE_DIR / f"{qid}.json"

    if not cache_file.exists():
        return None

    try:
        mtime = cache_file.stat().st_mtime
        age = time.time() - mtime
        if age > CACHE_TTL:
            return None  # Expired

        data = json.loads(cache_file.read_text())
        return data.get("products", [])
    except Exception:
        return None


def set(query: str, domain: str, max_price: float | None, min_stars: float | None, products: list) -> None:
    """Cache products."""
    _ensure_cache_dir()
    qid = _hash_query(query, domain, max_price, min_stars)
    cache_file = CACHE_DIR / f"{qid}.json"

    try:
        cache_file.write_text(json.dumps({
            "query": query,
            "domain": domain,
            "max_price": max_price,
            "min_stars": min_stars,
            "timestamp": time.time(),
            "products": [
                {
                    "title": p.title,
                    "asin": p.asin,
                    "brand": p.brand,
                    "price": p.price,
                    "price_str": p.price_str,
                    "stars": p.stars,
                    "reviews": p.reviews,
                    "thumbnail": p.thumbnail,
                    "link": p.link,
                    "prime": p.prime,
                    "in_stock": p.in_stock,
                    "source": p.source,
                }
                for p in products
            ],
        }, indent=2))
    except Exception as e:
        print(f"⚠ Cache write failed: {e}")


def clear_all() -> None:
    """Delete all cache."""
    _ensure_cache_dir()
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()


def status() -> str:
    """Cache size/age."""
    _ensure_cache_dir()
    files = list(CACHE_DIR.glob("*.json"))
    if not files:
        return "Cache: vuoto"
    total_size = sum(f.stat().st_size for f in files) / 1024  # KB
    oldest = min(f.stat().st_mtime for f in files)
    age_min = int((time.time() - oldest) / 60)
    return f"Cache: {len(files)} query, {total_size:.1f}KB, più vecchio {age_min}m fa"
