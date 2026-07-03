# -*- coding: utf-8 -*-
"""Night-runner: batch resiliente per ricerche Amazon notturne.

Quello che il tool base NON aveva (verificato): retry+backoff, resume da
crash, cap budget notte, output HTML per query, log jsonl. NON usa Claude:
e' uno script Python autonomo, lo lanci e gira da solo (PC acceso + powercfg).

Robustezza:
- coda da queries.txt (1 query/riga, opz. `query | max_price`)
- resume: salta query gia' fatte (state.json) -> riavvio riprende da dove era
- retry 3x backoff su errore rete/API; ultimo tentativo senza immagini
- cap budget notte: stop dopo N ricerche SerpAPI REALI (cache non conta)
- ogni query -> 1 file HTML self-contained; log jsonl append-only

Uso:
    python "<repo-root>/night_runner.py"            # batch completo
    python ".../night_runner.py" --limit 2                                    # dry-run: prime 2
    python ".../night_runner.py" --budget 30 --domain IT --out C:/amz_out
    python ".../night_runner.py" --no-images
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

# --- entry robusto: home in fondo a sys.path (evita shadow rich.py) + utf-8 console ---
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
# _home E' il parent di amazon_search/ -> in FONDO rende il pacchetto importabile
# senza che home/rich.py (landmine) faccia ombra al vero rich di site-packages.
_home = str(Path.home())
while _home in sys.path:
    sys.path.remove(_home)
sys.path.append(_home)

import json  # noqa: E402
from amazon_search.report import collect  # noqa: E402
from amazon_search import quota, config_search  # noqa: E402
from amazon_search.render import Card, Section, Tag, render_html  # noqa: E402

# ---------------- config default (sovrascrivibili da CLI) ----------------
PKG = Path(__file__).resolve().parent
QUERIES_FILE = PKG / "queries.txt"
OUT_DIR = Path.home() / "amazon_search_out"
STATE_FILE = OUT_DIR / "state.json"
LOG_FILE = OUT_DIR / "runner_log.jsonl"
NIGHT_BUDGET = 30        # max ricerche SerpAPI REALI in una notte (cache esclusa)
RETRIES = 3
BACKOFF_BASE = 5         # secondi: 5, 10, 20
RESULTS = 12
DOMAIN = "IT"
IMAGES = True
SPECS = False            # specs = crediti Canopy; off di default in notturna


def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)  # scrittura atomica: niente state corrotto se crash a meta'


def _log(rec: dict) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _slug(s: str) -> str:
    keep = "".join(c if c.isalnum() or c in " -_" else "" for c in s)
    return "_".join(keep.split())[:60] or "query"


def read_queries(path: Path) -> list[tuple[str, float | None]]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            q, mp = line.split("|", 1)
            try:
                out.append((q.strip(), float(mp.strip())))
            except ValueError:
                out.append((q.strip(), None))
        else:
            out.append((line, None))
    return out


def build_html(query: str, items: list[dict], domain: str) -> str:
    cards = []
    for it in items:
        stars, revs = it.get("stars"), it.get("reviews")
        rating = f"{stars} ({revs})" if stars else (f"({revs})" if revs else "")
        tags = []
        if it.get("price_str"):
            tags.append(Tag(it["price_str"], "#57534e", "info"))
        if it.get("prime"):
            tags.append(Tag("Prime", "#0e7490", "bolt"))
        cards.append(Card(
            asin=it.get("asin", ""),
            title=it.get("title", "") or "",
            price=it.get("price_str", "") or "",
            rating=rating,
            img1=it.get("img1", "") or "",
            img2=it.get("img2", "") or "",
            tags=tags,
            domain=domain.lower(),
        ))
    sec = Section(f"{len(cards)} risultati", subtitle=query, cards=cards)
    return render_html(
        f"Ricerca Amazon: {query}",
        f"{len(cards)} prodotti su Amazon {domain}. Bottoni aprono in nuova scheda.",
        [sec],
        foot="Generato da night_runner (batch notturno autonomo).",
    )


def process_one(query: str, max_price: float | None, domain: str,
                images: bool, specs: bool, out_dir: Path) -> dict:
    """Una query con retry+backoff. Ritorna record esito."""
    last_err = ""
    for attempt in range(1, RETRIES + 1):
        use_images = images and attempt < RETRIES  # ultimo giro: niente immagini (meno fragile)
        try:
            items = collect(query, n=RESULTS, domain=domain, specs=specs,
                            images=use_images, images_top=0 if use_images else 0)
            if max_price is not None:
                items = [it for it in items
                         if it.get("price") is None or it["price"] <= max_price]
            html = build_html(query, items, domain)
            fname = out_dir / f"{_slug(query)}_{domain.lower()}.html"
            fname.write_text(html, encoding="utf-8")
            return {"query": query, "status": "done", "n": len(items),
                    "html": str(fname), "attempt": attempt}
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < RETRIES:
                wait = BACKOFF_BASE * (2 ** (attempt - 1))
                print(f"  [retry {attempt}/{RETRIES}] {last_err} -> attendo {wait}s")
                time.sleep(wait)
    return {"query": query, "status": "failed", "error": last_err}


def main(argv: list[str]) -> None:
    domain, budget, limit = DOMAIN, NIGHT_BUDGET, None
    images, specs = IMAGES, SPECS
    qfile, out_dir = QUERIES_FILE, OUT_DIR
    state_file, _ = STATE_FILE, LOG_FILE

    a = argv
    if "--domain" in a:    domain = a[a.index("--domain") + 1].upper()
    if "--budget" in a:    budget = int(a[a.index("--budget") + 1])
    if "--limit" in a:     limit = int(a[a.index("--limit") + 1])
    if "--queries" in a:   qfile = Path(a[a.index("--queries") + 1])
    if "--out" in a:       out_dir = Path(a[a.index("--out") + 1])
    if "--no-images" in a: images = False
    if "--specs" in a:     specs = True

    out_dir.mkdir(parents=True, exist_ok=True)
    state_file = out_dir / "state.json"
    globals()["LOG_FILE"] = out_dir / "runner_log.jsonl"

    queries = read_queries(qfile)
    if limit:
        queries = queries[:limit]
    if not queries:
        print(f"Nessuna query in {qfile}. Crea il file (1 query/riga).")
        return

    state = _load_json(state_file)
    spent_start = quota.used("serpapi")
    print(f"=== night_runner: {len(queries)} query | budget {budget} | "
          f"SerpAPI usate finora {spent_start}/{config_search.QUOTA_SAFE_LIMITS['serpapi']} ===")

    done = skipped = failed = 0
    for query, max_price in queries:
        key = f"{query}|{domain}"
        if state.get(key, {}).get("status") == "done":
            print(f"- SKIP (gia' fatto): {query}")
            skipped += 1
            continue

        spent_now = quota.used("serpapi") - spent_start
        if spent_now >= budget:
            print(f"! STOP budget notte ({budget} ricerche reali). "
                  f"Restano {len(queries) - done - skipped - failed} query -> prossimo run le riprende.")
            break
        if not quota.check("serpapi"):
            print("! STOP quota mensile SerpAPI esaurita.")
            break

        print(f"> {query}" + (f"  (<= {max_price} EUR)" if max_price else ""))
        rec = process_one(query, max_price, domain, images, specs, out_dir)
        rec["ts"] = int(time.time())
        rec["serpapi_used"] = quota.used("serpapi")
        state[key] = rec
        _save_json(state_file, state)
        _log(rec)

        if rec["status"] == "done":
            done += 1
            print(f"  OK {rec['n']} prodotti -> {rec['html']}")
        else:
            failed += 1
            print(f"  FAIL: {rec.get('error')}")

    print(f"=== fine: {done} fatte, {skipped} saltate, {failed} fallite. "
          f"SerpAPI usate stanotte: {quota.used('serpapi') - spent_start}. Output in {out_dir} ===")


if __name__ == "__main__":
    main(sys.argv[1:])
