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
        learned = _load_learned().get(payload["query"].lower().strip(), {})
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


@app.route("/categorize/<job_id>")
def categorize(job_id):
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return render_template("loading.html", job_id=job_id)
    result = job["result"]
    # skip items already certain: inside a photo-identical family the category of
    # one member answers for all — the sunflower must stay fast, not exhaustive
    fam_seen: set[int] = set()
    items = []
    for p in result.products:
        fid = getattr(p, "family_id", None)
        if fid is not None:
            if fid in fam_seen:
                continue
            fam_seen.add(fid)
        items.append({"asin": p.asin, "title": p.title, "thumbnail": p.thumbnail,
                      "price": p.price, "category": getattr(p, "category", None)})
    existing = sorted({getattr(p, "category", None) for p in result.products}
                      - {None, ""})
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
             "stars": p.stars, "reviews": p.reviews, "prime": p.prime,
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
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=rows[0].keys() if rows else ["asin"])
        w.writeheader()
        w.writerows(rows)
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
