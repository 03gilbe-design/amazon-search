# Amazon Search Tool — Progresso

## ✅ FATTO

### v1 — Baseline
- [x] SerpAPI search (250/mese)
- [x] HTML output mobile-friendly
- [x] Quota tracking (multi-API)
- [x] Canopy specs (optional, --specs)

### v2 — Cache + Parallel
- [x] Cache layer (1h TTL, dedup)
- [x] Parallel SerpAPI + SearchAPI (return first)
- [x] ThreadPoolExecutor (no asyncio, Termux safe)
- [x] Quota tracking on both APIs
- [x] CLI flags: --cache-status, --clear-cache

### v3 — Config + Logging + Testing
- [x] config_search.py — parametri facili da modificare
- [x] logger.py — record ricerche (JSONL format)
- [x] --test flag — test suite 3 query predefinite
- [x] --log-summary flag — statistiche ricerche
- [x] --clear-log flag — svuota log
- [x] Timing + quota tracking in log

### v3.1 — Real Testing + Spec Parser
- [x] spec_parser.py — parsing specs da titolo (robusto)
- [x] test_subwoofer_mock.py — mock test con 15 prodotti fake
- [x] Real SerpAPI test con subwoofer query
- [x] HTML generation con risultati reali
- [x] Log tracking verificato (9 SerpAPI su 250, cache hit funzionante)

### v4 — Mobile-First UI/UX Redesign
- [x] DESIGN_PLAN.md — wireframe, user journey, gerarchia info
- [x] heatmap_eyetrack.html — eye-tracking visualization
- [x] html_gen.py complete rewrite (350+ lines CSS/JS)
  - Sticky header con query + filter button
  - Card layout: image LEFT (100px) + info RIGHT (flex)
  - Price: 18px bold RED (#d32f2f)
  - Rating: accanto titolo con review count
  - Filter drawer: bottom-sheet, slide-up 0.3s
  - Active filter chips: removable, horizontal scroll
  - Sort dropdown: separato dai filtri
  - Result counter: dinamico
  - No results recovery con suggerimenti
- [x] Accessibility: 44px+ buttons, WCAG AA color contrast
- [x] Tested: 9 prodotti reali, responsive 375px+

### v5 — Redundancy Removal + Interactivity (NEW)
- [x] Rimosso: emoji header, duplicate query, CTA text, "In Stock" badge, brand field
- [x] Aggiunto: confidence indicator (reviews), "Non disp." alert, real-time price display
- [x] Fixed mobile: single price slider, no overflow, better scrollbar
- [x] Animazioni: 
  - Card tap: scale pulse (200ms)
  - Chip remove: fade-out (200ms)
  - Button tap: scale 0.95 feedback
  - Filter apply: pulse animation
  - Drawer: cubic-bezier easing
  - Sort/slider: real-time updates
  - Swipe/click-outside drawer close
- [x] Tested: 9 prodotti, all interactions working, 320px+ responsive

## 📊 Test Results

```
v3 test suite: 3 ricerche
  Total quota cost: 3 SerpAPI
  Cache hits: 0 (first time)
  Avg durata: 2.55s per ricerca
  SearchAPI: fragile (400 errors, disabled in fallback)

v3.1 real test: subwoofer auto sottile amplificato
  Query: "subwoofer auto sottile amplificato"
  Filtri: max_price=120€, min_stars=3.5⭐, results=20
  Risultati: 9 prodotti match (1 cache hit)
  Quota usato: 9 SerpAPI (rimangono 241/250)
  Avg durata: 2.27s
  Status: HTML generated + log tracked ✅

v4 UI redesign test:
  HTML: /storage/emulated/0/Download/amazon_subwoofer_..._20260519_0518.html
  Components: sticky header, card layout, filter drawer, sort, chips
  Accessibility: 44px+ buttons, WCAG AA color contrast
  Responsive: 375px+ (single column, image LEFT)
  Rendering: ✅ CSS/JS working, drawer slide animation smooth
  Status: Production-ready design ✅
```

## 🎯 Facile da modificare

```python
# config_search.py
TIMEOUT_API = 30  # Cambiar timeout
CACHE_TTL_SECONDS = 3600  # Cambiar cache duration
QUOTA_SAFE_LIMITS = {"serpapi": 240, ...}  # Cambiar limiti quota
TEST_QUERIES = [...]  # Aggiungere test query
```

```bash
amazon-search --test  # Esegui test suite
amazon-search --log-summary  # Vedi statistiche
amazon-search --clear-log  # Svuota log
amazon-search --cache-status  # Cache info
```

## 📝 Log Format

File: `~/.amazon_search_log.jsonl`

Esempio entry:
```json
{
  "timestamp": 1234567890,
  "query": "subwoofer",
  "results": 10,
  "source": "serpapi",
  "duration_s": 2.5,
  "cache_hit": false,
  "quota": {"before": {...}, "after": {...}, "delta": {...}}
}
```

## 🚀 Prossimi step (Opzionali)

- [ ] Desktop layout (2-3 col grid, left sidebar filters)
- [ ] Keepa integration (price history)
- [ ] HTML "Confronta prodotti" (2-3 side-by-side)
- [ ] Dedup prodotti (se risultati duplicati)
- [ ] Multi-query helper (100+ prodotti con parallelizzazione)
- [ ] Scraping fallback (ZenRows, last resort)
- [ ] Brand extraction da titolo (parsing migliorato)
- [ ] spec_parser.py integrazione opzionale in searcher (--smart-parse flag)
- [ ] Dark mode toggle
- [ ] Share filters (URL state)
- [ ] Export CSV

## 🔍 Problemi Noti

- SearchAPI fragile (400 errors, hardcoded in SEARCHAPI_FALLBACK_ONLY=True) → SerpAPI è il vero fallback
- Max 20 prodotti per API call → 250/mese SerpAPI ÷ 20 = ~12 ricerche max
- Canopy non usata per search (100 credits riservati per specs via --specs flag)
- Brand non sempre estratto da SerpAPI (campi mancanti)
- Parsing specs techniche da titolo: 53-100% accuracy (vedi spec_parser test_cases)

## 💾 File Creati

```
~/amazon_search/
├── config.py              # Key loader
├── config_search.py       # Parametri modifiable
├── quota.py               # Quota tracker
├── cache.py               # Cache layer (1h TTL)
├── logger.py              # JSONL logging
├── searcher.py            # SerpAPI + SearchAPI parallel
├── specs.py               # Canopy specs fetcher
├── llm.py                 # Groq summary (opzionale)
├── html_gen.py            # 👈 HTML output (REDESIGNED v4)
├── spec_parser.py         # 👈 Spec parsing tool
├── main.py                # CLI entry point
├── test_subwoofer_mock.py # 👈 Mock test (15 prodotti)
├── DESIGN_PLAN.md         # 👈 Design spec completo
├── heatmap_eyetrack.html  # 👈 Eye-tracking visualization
├── PROGRESS.md            # Questo file
└── __init__.py
```
