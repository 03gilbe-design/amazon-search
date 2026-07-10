# Data pipeline — where data lives, how it flows, how the app loads it

One page. If a file isn't listed here, the app doesn't need it.

## 1. Where data lives (disk)

| Store | Path | What | Written by |
|---|---|---|---|
| Search cache | `~/.amazon_search_cache/*.json` | one file per (query+filters): products with title/price/stars/thumbnail/asin. TTL 1h for reuse as "fresh", kept on disk forever for the dataset pool | `amazon_search/cache.py` after every search |
| Image cache | `~/.amazon_report_cache/*.jpg` | product thumbnails by ASIN (for pHash/SIFT) | `amazon_search/imagecache.py` on demand |
| Offline DB | `~/.amazon_search_offline.json` | frozen snapshot (242 products) used by ML scripts | manual export (Gemini session) |
| Your labels | `~/.amazon_search_learned_categories.json` | `{query: {asin: category}}` + `_global` merge + `_categories` list. Every click in the categorizer writes here immediately | `webui/app.py /api/set_category` |
| Ground truth | `~/amazon_search_reports/ground_truth_dataset.json` | 264 labeled rows (asin,title,thumbnail,category) — THE dataset for method testing | `scripts/` export |
| ESCI (public) | `~/.cache/huggingface/hub/datasets--tasksource--esci` | 15 parquet shards, real Amazon queries with E/S/C/I relevance labels | HuggingFace download |
| Lab outputs | `amazon_search/private/*.md|json` | probe/night reports, gitignored | `scripts/night_*`, `scripts/esci_*` |

## 2. How data flows (processing)

```
query ──> searcher.py (SerpAPI paginated / price bands / free-scrape fallback)
            └─> cache.py write ──> pipeline.run()
                  ├─ dedup.py: pHash families (photo) + numeric fingerprint (title)
                  ├─ scoring.py: categories (keyword/learned), feature-fit, exclusions
                  └─> SearchResult ──> webui report / categorize / CLI HTML report
labels (your clicks) ──> learned_categories.json ──> re-applied on every future run
method testing ──> ground_truth + ESCI ──> scripts/night_noise_lab.py / esci_quick_probe.py
```

## 3. How the app loads it (webui)

- `/` home: `GET /api/searches` lists the cache files (query + count).
- `POST /search`: runs `pipeline.run()` in a thread; `GET /status/<job>` polls log lines; when done → `/report/<job>`.
- `/report/<job>`: groups the job's products by category → `cat_list` (chips + sections).
- `/categorize/<job>`: the job's products + labels for THIS job only. `/categorize/dataset` = whole disk cache merged (sleep-filtered via `private/topic_keywords.json`, thumbnail+title dedup).
- Every categorize click → `POST /api/set_category` → written to disk before the response returns. Nothing is lost on refresh/crash.
- Export any time: `/export/<job>.csv|json`.

## 4. Findings that shape the pipeline (measured, 2026-07-10)

- ESCI 600 real queries: keep-all baseline F2=0.766 beats every title-only filter (best bm25s 0.53). → title-only HARD noise filtering is out; scores are used for grouping/ranking, removal stays a user click (category chip X).
- Local 264 labels: cluster-dominance best generalist but weak (min F2 0.49). Broad 2-3 class splits work (94-96%), fine 17-class don't (79%).
- Heavy experiments (embeddings, vision models) → Google Colab notebook: `~/Downloads/amazon_noise_lab_colab.ipynb`.
