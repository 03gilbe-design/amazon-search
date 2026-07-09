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


# --- Preset categorie (deterministiche, keyword su titolo+bullet) ---
# Esempio: 13 sotto-categorie per la nicchia supporti cervicali.
# ORDINE = priorità: le categorie più specifiche stanno PRIMA (un "massaggiatore
# cervicale gonfiabile" deve finire in Massaggiatore, non in Trazione gonfiabile).
# Uso: --categorize-preset neck  (oppure copiare/adattare per altre ricerche)
CATEGORY_PRESETS: dict[str, dict[str, list[str]]] = {
    "neck": {
        "Per cane / animale": ["cane", "gatto", "pet ", "animale", "dog", "cat "],
        "Massaggiatore elettronico": ["massaggiat", "elettro", "riscaldat", "heating",
                                       "massager", "ems ", "impulsi", "vibrazione", "display"],
        "Bite / mouthpiece": ["bite", "paradenti", "bocchino", "mouthpiece", "mouth guard",
                               "bruxismo", "denti"],
        "Tongue trainer": ["lingua", "tongue"],
        # Trazione PRIMA di Banda: i device di trazione citano spesso "supporto mento"
        # ma una fascia mento non dice mai "gonfiabile/trazione" (ordine = priorità).
        # Gonfiabile SOLO con keyword d'aria: un "dispositivo di trazione" a molla/stecca
        # NON è gonfiabile (feedback utente su caso reale NEWFUN) — categoria separata.
        "Trazione gonfiabile": ["gonfiabile", "inflatable", "pompa", "pump", " aria"],
        "Trazione (altro tipo)": ["trazione", "traction", "estensore", "stretcher"],
        # " mento" con spazio: "Poggiamento"/"trattamento" contengono "mento" (bug reale
        # visto sul pool collare cervicale); "strap" da solo matcha troppo
        "Banda mandibola": [" mento", "mentoniera", "mandibol", "chin strap", "chinstrap",
                             " chin"],
        "Cuscino a U da viaggio": ["viaggio", "travel", "aereo", "u-shape", "a u ",
                                    "forma di u", "memory foam viaggio"],
        "Gel pad notturno": ["gel "],
        "Cuscino forma strana": ["cuscino", "pillow", "guanciale"],
        "Scaldacollo / fascia collo": ["scaldacollo", "sciarpa", "neck warmer", "pile",
                                        "termico", "warmer"],
        "Neck rigido": ["rigido", "semirigido", "semi-rigido", "philadelphia", "stecca",
                         "immobilizz", "frattura"],
        "Neck medicale": ["ortopedic", "medicale", "medico", "cervicale morbido schiuma",
                           "vertebr", "postura", "dolore"],
        "Neck morbido": ["morbido", "soffice", "soft", "riposo", "notte", "dormire",
                          "schiuma", "foam", "spugna"],
    },
}
