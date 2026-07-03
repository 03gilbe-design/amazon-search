# amazon-search

**Deterministic Amazon product search + report engine.** Searches (SerpAPI), fetches technical
specs, ranks by fit-for-budget, and renders a self-contained HTML report — no manual curation,
same query in → same shape out.

```bash
amazon-search "subwoofer 200W" --max-price 120 --min-stars 4 --specs
```

## What it does

1. **Search** (`searcher.py`) — SerpAPI Amazon search, mobile HTML parsing, price/star filters.
2. **Specs** (`spec_parser.py`, `specs.py`) — fetches technical specifications for the top
   candidates (optional, costs API credits).
3. **Enrich** (`enrich.py`, `llm.py`) — optional AI ranking/comparison pass against a budget or
   free-text criteria.
4. **Render** (`render.py`, `html_gen.py`) — a single self-contained HTML report: image cache
   inlined, comparison table, per-product breakdown.
5. **Cache + quota** (`cache.py`, `quota.py`) — repeated queries don't re-spend API credits;
   `--quota` / `--cache-status` show what's left before you run.

## Quick start

```bash
pip install -r requirements.txt   # click, rich, requests, Pillow
export SERPAPI_KEY="..."          # search
export CANOPY_KEY="..."           # optional, for --specs
python -m amazon_search "wireless earbuds" --max-price 40 --min-stars 4
```

Runs fine outside Termux too — `termux-open` (auto browser launch) is best-effort and silently
skipped if unavailable.

## Project layout

```
main.py / __main__.py    CLI entry point (click)
searcher.py               SerpAPI search + mobile HTML parsing
spec_parser.py specs.py   technical spec extraction
enrich.py llm.py          optional AI ranking/comparison pass
render.py html_gen.py     HTML report generation
imagecache.py             product image caching (inlined into the report)
cache.py quota.py         API cache + quota tracking
config.py config_search.py  configuration
logger.py                 run logging
report.py                 report assembly glue
```

## Status

Functional, used for real product research (see `PROGRESS.md`, `DESIGN_PLAN.md`,
`HTML_DETAILED_QA.md` for design history and QA notes). Born on Termux/Android, runs anywhere
Python does.

## License

MIT.
