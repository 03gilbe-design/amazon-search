"""Config per Amazon search. Facile da modificare."""

# API timeouts (secondi)
TIMEOUT_API = 30
TIMEOUT_PARALLEL = 35  # ThreadPoolExecutor timeout

# Search limits
MAX_RESULTS_PER_API_CALL = 20  # SerpAPI limit
MAX_QUERIES_DEMO = 3  # Test suite limit

# Cache
CACHE_TTL_SECONDS = 3600  # 1 hour
CACHE_DIR_NAME = ".amazon_search_cache"

# Quota blocchi — stop prima di pagare
QUOTA_SAFE_LIMITS = {
    "serpapi": 240,    # 250 - 10 buffer
    "canopy": 95,      # 100 - 5 buffer
    "searchapi": 95,   # 100 - 5 buffer
}

# Parallel search: timeout per API failure
PARALLEL_TIMEOUT_PER_API = 15  # seconds

# SearchAPI è fragile (400 errors spesso) — disabilitata: SerpAPI basta e avanza
SEARCHAPI_ENABLED = False
SEARCHAPI_FALLBACK_ONLY = True  # Non usare in parallel, solo fallback

# Test queries — uso: --test flag
TEST_QUERIES = [
    {
        "query": "subwoofer buono basso prezzo",
        "max_price": 80,
        "min_stars": 4,
        "results": 10,
    },
    {
        "query": "striscia LED auto RGB",
        "max_price": 30,
        "min_stars": 3.5,
        "results": 10,
    },
    {
        "query": "caricatore USB auto ritraibile",
        "max_price": 25,
        "min_stars": 4,
        "results": 10,
    },
]
