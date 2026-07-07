# -*- coding: utf-8 -*-
"""Web UI for amazon-search — wraps pipeline.run() behind the user-designed
Flask templates (search form, live log, report page, sunflower/kanban
categorizer, settings). The classic CLI + standalone HTML report stay as-is;
this is an additional way in, not a replacement.

Run:  python -m webui.app   (from the repo root)  ->  http://127.0.0.1:5000
"""
from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True  # edit a template, refresh, done — no restart

JOBS: dict[str, dict] = {}  # job_id -> {status, log, error, result}
SETTINGS_PATH = Path.home() / ".amazon_search_ui_settings.json"


def _settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.context_processor
def _inject():
    return {"settings": _settings(), "environ": os.environ}

# user category picks survive restarts and feed future runs: {query: {asin: category}}
LEARNED_PATH = Path.home() / ".amazon_search_learned_categories.json"


def _load_learned() -> dict:
    try:
        return json.loads(LEARNED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_learned(data: dict) -> None:
    LEARNED_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                            encoding="utf-8")


def _run_job(job_id: str, payload: dict) -> None:
    job = JOBS[job_id]
    try:
        from amazon_search import pipeline
        job["log"].append(f"searching '{payload['query']}' ...")
        result = pipeline.run(
            payload["query"],
            max_price=payload.get("max_price") or None,
            min_stars=payload.get("min_stars") or None,
            n=int(payload.get("results") or 15),
            domain=payload.get("domain") or "IT",
            specs=bool(payload.get("specs")),
            dedup=True,
            rank=not payload.get("no_llm"),
            budget=payload.get("budget") or None,
            criteria={c.strip(): [c.strip()] for c in (payload.get("criteria") or "").split(",") if c.strip()} or None,
            junk_patterns={j.strip(): [j.strip()] for j in (payload.get("junk") or "").split(",") if j.strip()} or None,
        )
        # apply learned category picks from previous sunflower sessions
        _l = _load_learned()
        learned = {**_l.get("_global", {}), **_l.get(payload["query"].lower().strip(), {})}
        for p in result.products:
            if p.asin in learned:
                p.category = learned[p.asin]
        job["log"].append(f"{len(result.products)} products, "
                          f"{len(result.families)} duplicate families, "
                          f"{len(result.excluded)} excluded")
        job["result"] = result
        job["status"] = "done"
    except Exception as e:
        job["error"] = str(e)
        job["status"] = "error"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["POST"])
def search():
    payload = request.get_json()
    if not (payload.get("query") or "").strip():
        return jsonify({"error": "query is required"})
    job_id = uuid.uuid4().hex[:10]
    JOBS[job_id] = {"status": "running", "log": [], "error": None, "result": None,
                    "params": payload}
    threading.Thread(target=_run_job, args=(job_id, payload), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"status": "error", "error": "unknown job"})
    return jsonify({"status": job["status"], "log": job["log"], "error": job["error"]})


@app.route("/report/<job_id>")
def report(job_id):
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return render_template("loading.html", job_id=job_id)
    return render_template("report.html", result=job["result"], job_id=job_id,
                           params=job.get("params", {}))


class _DatasetResult:
    """Job sintetico: l'intero archivio prodotti come pool da etichettare."""
    def __init__(self, products):
        self.query = "dataset"
        self.products = products
        self.families, self.excluded, self.filters = [], [], {"domain": "IT"}


class _P:
    def __init__(self, d, cat):
        self.asin = d.get("asin", "")
        self.title = d.get("title", "")
        self.thumbnail = d.get("thumbnail")
        self.price = d.get("price")
        self.price_str = d.get("price_str")
        self.brand = d.get("brand")
        self.link = d.get("link") or (f"https://www.amazon.it/dp/{self.asin}" if self.asin else "#")
        self.category = cat
        self.family_id = None


# dataset = solo prodotti sonno-correlati: la cache su disco è condivisa con
# progetti non-sonno (subwoofer auto, occhiaie, smart ring generico...) — quel
# rumore va escluso esplicitamente, un match debole non basta.
_SLEEP_INCLUDE = ("sonno", "dormire", "notte", "sleep", "cervical", "collare",
                  "neck", "russamento", "snor", "cpap", "apnea", "mascherina",
                  "eye mask", "cuscino", "pillow", "guanciale", "materasso",
                  "trazione", "anti-russ")
_SLEEP_EXCLUDE = ("subwoofer", "altoparlante", "cassa acustica", "bluetooth speaker",
                  "minoxidil", "occhiaie", "eye cream", "crema",
                  "tongue", "lingua", "bite", "paradenti", "mouthpiece", "bocchino",
                  "smart ring", "anello", "smartring", "oura")


def _is_sleep_related(title: str) -> bool:
    t = (title or "").lower()
    if any(kw in t for kw in _SLEEP_EXCLUDE):
        return False
    return any(kw in t for kw in _SLEEP_INCLUDE)


def _build_dataset_job() -> None:
    import glob
    learned = _load_learned()
    lookup = learned.get("_global", {})
    seen: dict[str, dict] = {}
    for f in glob.glob(str(Path.home() / ".amazon_search_cache" / "*.json")):
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data.get("products") if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        for it in items:
            if (isinstance(it, dict) and it.get("asin") and it.get("thumbnail")
                    and _is_sleep_related(it.get("title", ""))):
                seen.setdefault(it["asin"], it)
    # dedup: stesso URL foto tra ASIN diversi = stesso listing rivenduto,
    # tienine uno solo (il primo visto) per non etichettare copie identiche
    seen_thumbs: set[str] = set()
    seen_titles: set[str] = set()
    deduped = {}
    for asin, d in seen.items():
        th = d.get("thumbnail")
        tkey = " ".join((d.get("title") or "").lower().split())[:90]
        if th in seen_thumbs or (tkey and tkey in seen_titles):
            continue
        seen_thumbs.add(th)
        seen_titles.add(tkey)
        deduped[asin] = d
    products = [_P(d, lookup.get(a)) for a, d in deduped.items()]
    JOBS["dataset"] = {"status": "done", "log": [], "error": None,
                       "result": _DatasetResult(products), "params": {}}


@app.route("/categorize/<job_id>")
def categorize(job_id):
    if job_id == "dataset":
        _build_dataset_job()
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return render_template("loading.html", job_id=job_id)
    result = job["result"]
    # full pool: every product is a labelable dataset row (family members included —
    # confirming a duplicate's category is one click and improves the dataset)
    items = [{"asin": p.asin, "title": p.title, "thumbnail": p.thumbnail,
              "price": p.price, "price_str": p.price_str, "brand": p.brand,
              "family_id": getattr(p, "family_id", None),
              "link": p.link, "category": getattr(p, "category", None)}
             for p in result.products]
    existing = sorted(({getattr(p, "category", None) for p in result.products}
                       | set(_load_learned().get("_categories", []))) - {None, ""})
    return render_template("categorize.html", job_id=job_id,
                           query=result.query, existing_cats=existing,
                           products=items)


@app.route("/api/set_category", methods=["POST"])
def set_category():
    d = request.get_json()
    job = JOBS.get(d.get("job_id") or "")
    if job and job.get("result"):
        query_key = job["result"].query.lower().strip()
        learned = _load_learned()
        learned.setdefault(query_key, {})[d["asin"]] = d["category"]
        learned.setdefault("_global", {})[d["asin"]] = d["category"]
        if d.get("category"):
            cats = learned.setdefault("_categories", [])
            if d["category"] not in cats:
                cats.append(d["category"])
        _save_learned(learned)
        for p in job["result"].products:
            if p.asin == d["asin"]:
                p.category = d["category"]
    return jsonify({"ok": True})


@app.route("/export/<job_id>.<fmt>")
def export(job_id, fmt):
    import csv
    import io
    job = JOBS.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "unknown job"}), 404
    result = job["result"]
    rows = [{"asin": p.asin, "title": p.title, "brand": p.brand, "price": p.price,
             "stars": getattr(p, "stars", None), "reviews": getattr(p, "reviews", None),
             "prime": getattr(p, "prime", None),
             "category": getattr(p, "category", None),
             "family_id": getattr(p, "family_id", None),
             "dedup_note": getattr(p, "dedup_note", None),
             "link": p.link, "thumbnail": p.thumbnail}
            for p in result.products]
    if fmt == "json":
        payload = {"query": result.query, "products": rows,
                   "families": result.families, "excluded": result.excluded}
        data = json.dumps(payload, ensure_ascii=False, indent=1)
        mime = "application/json"
    elif fmt == "csv":
        def _safe(v):
            # CSV formula injection: Excel esegue celle che iniziano con =+-@
            if isinstance(v, str) and v[:1] in "=+-@":
                return "'" + v
            return v
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=rows[0].keys() if rows else ["asin"])
        w.writeheader()
        w.writerows([{k: _safe(v) for k, v in r.items()} for r in rows])
        data, mime = buf.getvalue(), "text/csv"
    else:
        return jsonify({"error": "fmt must be csv or json"}), 400
    from flask import Response
    return Response(data, mimetype=mime, headers={
        "Content-Disposition": f"attachment; filename=amazon_{_slugify(result.query)}.{fmt}"})


def _slugify(t: str) -> str:
    import re as _r
    return _r.sub(r"[^a-z0-9]+", "_", t.lower())[:30].strip("_")


@app.route("/settings", methods=["GET", "POST"])
def settings():
    env_path = Path.home() / ".env"
    if request.method == "POST":
        d = request.get_json()
        keys = {k: v for k, v in d.items() if k.isupper()}     # API keys -> ~/.env
        prefs = {k: v for k, v in d.items() if not k.isupper()}  # form defaults -> json
        if keys:
            lines = []
            if env_path.exists():
                lines = [l for l in env_path.read_text(encoding="utf-8").splitlines()
                         if not any(l.startswith(k + "=") for k in keys)]
            for k, v in keys.items():
                if v:
                    lines.append(f"{k}={v}")
                    os.environ[k] = v
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if prefs:
            merged = _settings() | prefs
            SETTINGS_PATH.write_text(json.dumps(merged, indent=1), encoding="utf-8")
        return jsonify({"ok": True})
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=False, port=5000)
