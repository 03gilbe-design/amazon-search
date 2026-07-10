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
import re
import sys
import threading
import uuid
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.template_filter("regex_price")
def _regex_price(note: str) -> str:
    """Estrae '-€4.49' da 'Same item also seen for €4.49 less' (badge compatto)."""
    import re as _r
    m = _r.search(r"€\s?([\d.,]+)", note or "")
    return ("-€" + m.group(1)) if m else "↓"  # edit a template, refresh, done — no restart

@app.template_filter("hq_img")
def _hq_img(url: str) -> str:
    """Amazon image URL -> high-res: swap ANY size modifier (_AC_SX148_...,
    _AC_UL320_, ...) with _AC_SL500_. Non-Amazon/odd URLs pass through."""
    if not url or "media-amazon" not in url:
        return url or ""
    return re.sub(r"\._[^./]+\.(jpg|jpeg|png|webp)$", r"._AC_SL500_.\1", url)


JOBS: dict[str, dict] = {}  # job_id -> {status, log, error, result}
SETTINGS_PATH = Path.home() / ".amazon_search_ui_settings.json"


def _settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.context_processor
def _inject():
    last = next((jid for jid in reversed(list(JOBS)) if JOBS[jid].get("status") == "done"), None)
    return {"settings": _settings(), "environ": os.environ, "last_job_id": last}

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
    if job_id == "dataset":
        _build_dataset_job()   # il dataset completo è visibile anche come report
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return render_template("loading.html", job_id=job_id)
    result = job["result"]
    # duplicati stesso-thumbnail + stesso-prezzo: inutili da mostrare (direttiva),
    # tieni il primo — vale per OGNI report, non solo per il dataset unificato
    seen_tp = set()
    kept = []
    for prod in result.products:
        key = (prod.thumbnail, prod.price)
        if prod.thumbnail and prod.price is not None and key in seen_tp:
            continue
        seen_tp.add(key)
        kept.append(prod)
    result.products = kept
    # il template raggruppa per categoria: cat_list/single_cat/families vanno
    # costruiti qui (il template li ha sempre pretesi, nessuno li passava — report vuoto)
    colors = ["#e47911", "#4a9eff", "#3dba6a", "#9b6dff", "#c8a84b", "#ff66aa", "#00ccbb", "#c0392b"]
    groups: dict[str, list] = {}
    for i, prod in enumerate(result.products, 1):
        groups.setdefault(getattr(prod, "category", None) or "All results", []).append((i, prod))
    cat_list = [{"name": name, "color": colors[ix % len(colors)], "prods": prods}
                for ix, (name, prods) in enumerate(sorted(groups.items(), key=lambda kv: -len(kv[1])))]
    rank_of = {}
    for c in cat_list:
        for r, prod in c["prods"]:
            if prod.asin:
                rank_of[prod.asin] = (r, prod)
    families = []
    for fam in (result.families or []):
        if not isinstance(fam, dict):
            continue
        members = []
        for it in (fam.get("items") or []):
            asin = it.get("asin") if isinstance(it, dict) else it
            if asin in rank_of:
                members.append(rank_of[asin])
        if len(members) > 1:
            families.append({"members": members, "get": fam.get,
                             "diff_image": fam.get("diff_image", True),
                             "min_distance": fam.get("min_distance", "?")})
    # dict.get non è esposto come attributo in Jinja sui dict custom: uso dict veri
    families = [{"members": f["members"], "diff_image": f["diff_image"],
                 "min_distance": f["min_distance"]} for f in families]
    # dati per il compare drawer (client-side): specs reali + stimate + materiali
    cmp_data = {p.asin: {
        "asin": p.asin, "title": (p.title or "")[:80], "thumbnail": p.thumbnail,
        "price": p.price, "stars": getattr(p, "stars", None),
        "reviews": getattr(p, "reviews", None), "brand": getattr(p, "brand", None),
        "specs": getattr(p, "specs", None) or {},
        "estimated_specs": getattr(p, "estimated_specs", None) or {},
        "materials": getattr(p, "materials", None) or [],
        "attrs": getattr(p, "attrs", None) or [],
    } for p in result.products if p.asin}
    return render_template("report.html", result=result, job_id=job_id,
                           params=job.get("params", {}),
                           cat_list=cat_list, single_cat=len(cat_list) <= 1,
                           families=families, cmp_data=cmp_data,
                           verdicts=_family_verdicts())


# ---- niche knowledge (distilled from 1.2M ESCI products on Colab) ----
_NICHE_STOP = set("the a an for with and or of to in on new set pack pcs pieces "
                  "mens womens kids de la el para con y los las un una per il lo "
                  "i gli le di da "
                  # parole generiche che in ESCI risultano nicchie ma sono aggettivi
                  "anti memory auto design mini plus premium smart pro max ultra "
                  "super extra multi portable wireless bluetooth digital "
                  "adjustable universal comfort unisex wonder made play tape".split())
# titoli italiani -> tipo prodotto inglese della knowledge base
_NICHE_IT2EN = {"collare": "collar", "cervicale": "cervical", "cuscino": "pillow",
    "cuscini": "pillow", "lampada": "lamp", "auricolari": "earbuds",
    "cuffie": "headphones", "cerotti": "strips", "fascia": "strap",
    "anello": "ring", "mascherina": "mask", "maschera": "mask",
    "torcia": "flashlight", "sveglia": "clock", "tastiera": "keyboard",
    "caricatore": "charger", "supporto": "support", "materasso": "mattress",
    "tutore": "brace", "massaggiatore": "massager", "orologio": "watch"}
_NICHE_KB: dict | None = None


def _niche_kb() -> dict:
    global _NICHE_KB
    if _NICHE_KB is None:
        try:
            pth = Path(__file__).resolve().parent.parent / "private" / "esci_niche_knowledge.json"
            _NICHE_KB = json.loads(pth.read_text(encoding="utf-8"))
        except Exception:
            _NICHE_KB = {}
    return _NICHE_KB


def _niche_info(title: str):
    """First title keyword that exists in the knowledge base -> (niche, entry)."""
    kb = _niche_kb()
    if not kb:
        return None, None
    import re as _re
    fallback = None
    for w in _re.findall(r"[a-zà-ù]{4,}", (title or "").lower()):
        w = _NICHE_IT2EN.get(w, w)
        if w in _NICHE_STOP or w not in kb:
            continue
        entry = kb[w]
        # a word that is also a top brand of its own niche is a BRAND, not a
        # product type ("xiaomi") — its specs mix unrelated products, skip it
        if w in {b.lower() for b in (entry.get("brands") or {})}:
            continue
        if entry.get("specs"):
            return w, entry
        if fallback is None and entry.get("materials"):
            fallback = (w, entry)
    return fallback or (None, None)


_SPEC_LABELS = {"battery_mah": ("Batteria", "mAh"), "power_w": ("Potenza", "W"),
                "bluetooth": ("Bluetooth", ""), "screen_in": ("Schermo", "\""),
                "weight_g": ("Peso", "g"), "weight_kg": ("Peso", "kg"),
                "hours_h": ("Autonomia", "h"), "hours": ("Autonomia", "h"),
                "storage_gb": ("Memoria", "GB"), "capacity_l": ("Capacità", "L")}


@app.route("/product/<job_id>/<asin>")
def product_page(job_id, asin):
    if job_id == "dataset":
        _build_dataset_job()
    job = JOBS.get(job_id)
    if not job or job["status"] != "done":
        return render_template("loading.html", job_id=job_id)
    result = job["result"]
    prod = next((p for p in result.products if p.asin == asin), None)
    if not prod:
        return "prodotto non trovato in questo job", 404
    specs = dict(getattr(prod, "specs", {}) or {})
    est = dict(getattr(prod, "estimated_specs", {}) or {})
    materials = list(getattr(prod, "materials", []) or [])
    # spec rows: real first, then twin-estimated, then niche typical range for the rest
    niche, kb = _niche_info(prod.title)
    rows = []
    for k, v in specs.items():
        lab, unit = _SPEC_LABELS.get(k, (k, ""))
        rows.append({"label": lab, "value": f"{v:g} {unit}".strip(), "kind": "real"})
    for k, v in est.items():
        if k in specs:
            continue
        lab, unit = _SPEC_LABELS.get(k, (k, ""))
        rows.append({"label": lab, "value": f"~{v:g} {unit}".strip(), "kind": "twin"})
    niche_rows = []
    if kb:
        for k, s in (kb.get("specs") or {}).items():
            if k in specs or k in est:
                continue
            lab, unit = _SPEC_LABELS.get(k, (k, ""))
            niche_rows.append({"label": lab,
                               "value": f"{s['min']:g}–{s['max']:g} {unit}".strip(),
                               "median": f"{s['median']:g}"})
        if not materials:
            materials = [m for m, _ in sorted((kb.get("materials") or {}).items(),
                                              key=lambda x: -x[1])[:4]]
            mats_estimated = bool(materials)
        else:
            mats_estimated = False
    else:
        mats_estimated = False
    # same family = similar products
    similar = []
    fam_id = getattr(prod, "family_id", None)
    if fam_id:
        similar = [p for p in result.products
                   if getattr(p, "family_id", None) == fam_id and p.asin != asin][:8]
    attrs = list(getattr(prod, "attrs", []) or [])
    return render_template("product.html", p=prod, job_id=job_id, rows=rows,
                           niche=niche, niche_n=(kb or {}).get("n"),
                           niche_rows=niche_rows, materials=materials,
                           mats_estimated=mats_estimated, similar=similar, attrs=attrs)


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
        self.stars = d.get("stars")
        self.reviews = d.get("reviews")
        self.prime = d.get("prime", False)
        self.in_stock = d.get("in_stock", False)
        self.dedup_note = d.get("dedup_note") or (
            f"visto a €{abs(d['saving_vs_duplicate']):.2f} in meno"
            if d.get("saving_vs_duplicate") else None)
        self.link = d.get("link") or (f"https://www.amazon.it/dp/{self.asin}" if self.asin else "#")
        self.category = cat
        self.family_id = d.get("family_id")


# topic filter for the "dataset" labeling pool: keyword lists live in a local
# gitignored file (private/topic_keywords.json) — repo stays generic; without
# the file no include-filtering happens.
def _topic_keywords() -> dict:
    try:
        pth = Path(__file__).resolve().parent.parent / "private" / "topic_keywords.json"
        return json.loads(pth.read_text(encoding="utf-8"))
    except Exception:
        return {"include": [], "exclude": []}


_TOPIC = _topic_keywords()
_SLEEP_INCLUDE = tuple(_TOPIC.get("include", []))
_SLEEP_EXCLUDE = tuple(_TOPIC.get("exclude", []))


def _is_sleep_related(title: str) -> bool:
    t = (title or "").lower()
    if any(kw in t for kw in _SLEEP_EXCLUDE):
        return False
    return not _SLEEP_INCLUDE or any(kw in t for kw in _SLEEP_INCLUDE)


def _async_calculate_phash_families(products):
    if any(p.family_id for p in products):
        return
    try:
        from amazon_search.dedup import phash_families
        from amazon_search import imagecache
        import json
        import os
        from pathlib import Path
        
        print("Calcolo famiglie pHash in background...")
        paths = {}
        for p in products:
            if p.asin:
                fp = imagecache.local_path(p.asin, domain="it")
                if fp and os.path.exists(fp):
                    paths[p.asin] = fp
        if len(paths) > 1:
            raw_families = phash_families(paths, threshold=8)
            family_map = {}
            for fam_idx, fam in enumerate(raw_families):
                for asin in fam["items"]:
                    family_map[asin] = f"fam_{fam_idx}"
            
            # Assegna in memoria
            for p in products:
                p.family_id = family_map.get(p.asin)
                
            # Salva su disco nel file prodotti per renderlo persistente e caricabile all'istante
            OFFLINE_PATH = Path.home() / ".amazon_search_offline.json"
            if OFFLINE_PATH.exists():
                try:
                    data = json.loads(OFFLINE_PATH.read_text(encoding="utf-8"))
                    for prod_dict in data.get("products", []):
                        prod_dict["family_id"] = family_map.get(prod_dict.get("asin"))
                    OFFLINE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
                    print("Famiglie pHash salvate con successo in offline cache!")
                except Exception as e:
                    print("Errore nel salvataggio offline delle famiglie pHash:", e)
    except Exception as e:
        print("Errore nel calcolo background delle famiglie pHash:", e)


def _build_dataset_job() -> None:
    # dataset unificato (build_local_dataset.py): pulito, dedup stesso-prezzo,
    # specs/materiali estratti — se c'è, è LA fonte (basta fusioni al volo doppie)
    uni = Path(__file__).resolve().parent.parent / "private" / "unified_dataset.json"
    if uni.exists():
        try:
            data = json.loads(uni.read_text(encoding="utf-8"))
            prods = [d for d in (data.get("products") or []) if d.get("thumbnail")]
            lookup = _load_learned().get("_global", {})
            products = [_P(d, d.get("category") or lookup.get(d.get("asin"))) for d in prods]
            for pr, d in zip(products, prods):
                pr.specs = d.get("specs") or {}
                pr.materials = d.get("materials") or d.get("estimated_materials") or []
                pr.attrs = d.get("attrs") or []
                pr.estimated_specs = d.get("estimated_specs") or {}
                pr.duplicate_of = d.get("duplicate_of")
            # famiglie pHash in background anche qui (il detector le mostra)
            threading.Thread(target=_async_calculate_phash_families,
                             args=(products,), daemon=True).start()
            JOBS["dataset"] = {"status": "done", "log": [], "error": None,
                               "result": _DatasetResult(products), "params": {}}
            return
        except Exception:
            import traceback
            print("unified dataset load FAILED, fallback offline:")
            traceback.print_exc()
    if "dataset" in JOBS and JOBS["dataset"].get("status") == "done":
        return
        
    import glob
    import os
    
    OFFLINE_PATH = Path.home() / ".amazon_search_offline.json"
    cache_files = glob.glob(str(Path.home() / ".amazon_search_cache" / "*.json"))
    
    # Controllo se l'offline cache è aggiornata rispetto ai dati sorgente
    needs_rebuild = True
    if OFFLINE_PATH.exists():
        offline_mtime = OFFLINE_PATH.stat().st_mtime
        newest_cache = max([os.path.getmtime(f) for f in cache_files] + [0])
        if offline_mtime > newest_cache:
            needs_rebuild = False
            
    if not needs_rebuild:
        print("Caricamento Dataset OFFLINE pre-calcolato (Lazy Load RANSAC)...")
        try:
            data = json.loads(OFFLINE_PATH.read_text(encoding="utf-8"))
            
            # Migrazione automatica se l'utente ha il vecchio file unico da 44MB
            query_key = "dataset" # non lo sappiamo, usa default
            SCENES_PATH = Path.home() / f".amazon_search_offline_scenes_{query_key}.json"
            if "scene_matches" in data:
                print("Esecuzione migrazione: scorporo RANSAC dal file prodotti...")
                unique_matches = data.get("scene_matches", [])
                SCENES_PATH.write_text(json.dumps(unique_matches, ensure_ascii=False, indent=1), encoding="utf-8")
                # Sovrascrivi il file prodotti rimuovendo le scene per renderlo leggerissimo
                products_data = {"products": data.get("products", [])}
                OFFLINE_PATH.write_text(json.dumps(products_data, ensure_ascii=False, indent=1), encoding="utf-8")
                data = products_data
                
            seen_asins = set()
            products = []
            for p in data.get("products", []):
                asin = p.get("asin")
                if asin and asin not in seen_asins:
                    seen_asins.add(asin)
                    products.append(_P(p, p.get("category")))
            # Calcola le famiglie in background se non sono già presenti
            threading.Thread(target=_async_calculate_phash_families, args=(products,), daemon=True).start()
                
            JOBS["dataset"] = {
                "status": "done", "log": [], "error": None,
                "result": _DatasetResult(products), "params": {},
                "scene_matches": [] # Caricato on-demand per non appesantire l'avvio
            }
            return
        except Exception as e:
            print("Errore lettura dataset offline, rigenerazione in corso...", e)
            needs_rebuild = True

    print("Costruzione nuovo Dataset da zero e rigenerazione OFFLINE...")
    learned = _load_learned()
    lookup = learned.get("_global", {})
    seen: dict[str, dict] = {}
    for f in cache_files:
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data.get("products") if isinstance(data, dict) else data
        if not isinstance(items, list):
            continue
        for it in items:
            if (isinstance(it, dict) and it.get("asin") and it.get("thumbnail")):
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
    
    # Calcola famiglie pHash in background per non bloccare il caricamento della pagina (scarica prima le foto a bassa qualità)
    threading.Thread(target=_async_calculate_phash_families, args=(products,), daemon=True).start()
    
    # Salva offline per i successivi riavvii veloci — MAI rimpicciolire il file
    # esistente (un fallback degradato una volta ha sovrascritto 61 prodotti con 14)
    try:
        old_n = 0
        if OFFLINE_PATH.exists():
            try:
                old_n = len(json.loads(OFFLINE_PATH.read_text(encoding="utf-8")).get("products", []))
            except Exception:
                pass
        products_data = {"products": [p.__dict__ for p in products]}
        if len(products) < old_n:
            raise RuntimeError(f"refusing to shrink offline cache {old_n} -> {len(products)}")
        OFFLINE_PATH.write_text(json.dumps(products_data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as e:
        print("Errore salvataggio offline cache dataset:", e)
        
    JOBS["dataset"] = {"status": "done", "log": [], "error": None,
                       "result": _DatasetResult(products), "params": {}}
    
    # Avvia precalcolo RANSAC offline in background
    threading.Thread(target=_precalculate_offline, args=(JOBS["dataset"],), daemon=True).start()


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
    # SOLO le categorie presenti in QUESTO job: la lista globale inquinava ogni
    # nuovo dataset con le categorie di tutte le ricerche precedenti
    existing = sorted({getattr(p, "category", None) for p in result.products}
                      - {None, ""})
    return render_template("categorize.html", job_id=job_id,
                           query=result.query, existing_cats=existing,
                           products=items)
@app.route("/api/export_duplicates", methods=["POST"])
def export_duplicates_api():
    data = request.json
    job_id = data.get("job_id")
    if not job_id or job_id not in JOBS:
        return jsonify({"error": "Job non trovato"})
    job = JOBS[job_id]
    result = job.get("result")
    if not result:
        return jsonify({"error": "Nessun risultato"})
    
    import subprocess
    from pathlib import Path
    
    # Run the export script
    script_path = Path(__file__).parent.parent.parent / "export_duplicates.py"
    if not script_path.exists():
        script_path = Path(__file__).resolve().parent.parent / "export_duplicates.py"
        
    if script_path.exists():
        try:
            # Popen in background
            subprocess.Popen(["python", str(script_path)])
            return jsonify({"status": "success", "message": "Esportazione avviata in background nella cartella duplicates_export/"})
        except Exception as e:
            return jsonify({"error": str(e)})
    return jsonify({"error": "Script export_duplicates.py non trovato nel root."})


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


@app.route("/api/run_clustering", methods=["POST"])
def run_clustering():
    d = request.get_json() or {}
    job_id = d.get("job_id")
    threshold = float(d.get("threshold", 0.65))
    method = d.get("method", "birch")
    
    job = JOBS.get(job_id)
    if not job or not job.get("result"):
        return jsonify({"error": "Job non trovato"}), 404
        
    products = job["result"].products
    if not products:
        return jsonify({"clusters": []})
        
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    
    titles = [p.title for p in products]

    # Il vocabolario viene calcolato dinamicamente in base all'algoritmo scelto (scoperta ML)
    max_feat = 100 if method == "kmeans" else 227
    vectorizer = TfidfVectorizer(stop_words=None, min_df=1, max_features=max_feat)
    X = vectorizer.fit_transform(titles)
    feature_names = vectorizer.get_feature_names_out()
    
    labels = []
    
    if method == "kmeans":
        from sklearn.cluster import KMeans
        # Scoperta: K-Means batte Birch. Mappiamo lo slider 0.1-1.5 a un K dinamico
        # Threshold alto = K basso (grupponi), Threshold basso = K alto (frammentati)
        k = max(2, min(len(products) - 1, int(len(products) / (threshold * 15))))
        km = KMeans(n_clusters=k, random_state=42, n_init=3)
        km.fit(X)
        labels = km.labels_
        
    elif method == "birch":
        from sklearn.cluster import Birch
        # Scoperta: Birch collassa in un mega-gruppo se threshold >= 1.0.
        safe_threshold = min(threshold, 0.95) # Aumentato limite a 0.95 dato che optimum è 0.86
        brc = Birch(threshold=safe_threshold, n_clusters=None)
        labels = brc.fit_predict(X)
        
    elif method == "hybrid":
        from amazon_search import imagecache
        from amazon_search import scoring
        
        # Risolvi i percorsi delle immagini locali
        images = {}
        domain = job["result"].filters.get("domain", "it").lower()
        for p in products:
            if p.asin:
                # Disabilitiamo lo scaricamento bloccante sincrono, usa solo se GIA' in cache
                import os
                cached = str(Path.home() / ".amazon_report_cache" / f"{p.asin}.jpg")
                if os.path.exists(cached):
                    images[p.asin] = cached
                    
        # Esegui la clusterizzazione ibrida (testo + colore)
        # tfidf_threshold = threshold (mappe della somiglianza testo)
        # color_threshold = 40.0 (calibrata per i canali RGB)
        assignment = scoring.visual_cluster(
            products, images,
            color_threshold=40.0,
            tfidf_threshold=threshold,
            use_tfidf=True
        )
        
        # Gli elementi non raggruppati ricevono l'etichetta del loro ASIN singolo (cluster di 1)
        labels = []
        cluster_map = {}
        current_cluster_id = 0
        for p in products:
            lbl = assignment.get(p.asin)
            if lbl:
                if lbl not in cluster_map:
                    cluster_map[lbl] = current_cluster_id
                    current_cluster_id += 1
                labels.append(cluster_map[lbl])
            else:
                # Singolo
                labels.append(current_cluster_id)
                current_cluster_id += 1
        labels = np.array(labels)
        
    else: # Default: birch
        from sklearn.cluster import Birch
        brc = Birch(threshold=threshold, n_clusters=None)
        brc.fit(X)
        labels = brc.labels_
    
    # POST-PROCESSING: Forza prodotti visivamente identici nello stesso cluster (Color/Hash)
    import re
    import concurrent.futures
    import urllib.request
    import hashlib
    import io
    from PIL import Image
    from amazon_search.scoring import _color_distance
    
    # Cache globale per non riscaricare le thumbnail ad ogni ricalcolo
    if not hasattr(app, '_img_hash_cache'):
        app._img_hash_cache = {}
        app._img_color_cache = {}
    
    def fetch_hash_and_color(p):
        thumb = getattr(p, "thumbnail", None)
        if thumb is None and isinstance(p, dict):
            thumb = p.get("thumbnail", "")
        if not thumb: return p, "", None
        
        m = re.search(r'/images/I/([^._\s]+)', thumb)
        img_id = m.group(1) if m else thumb
        return p, img_id, None

    hashed_results = [fetch_hash_and_color(p) for p in products]
        
    # Raggruppa gli hash in macro-gruppi se il colore dominante è praticamente identico (< 6.0)
    # Questo fonde le immagini "stessa foto ma compressione/watermark diversi"
    unique_hashes = list({h for p, h, c in hashed_results if h})
    hash_to_macro = {h: h for h in unique_hashes}
    for i in range(len(unique_hashes)):
        h1 = unique_hashes[i]
        c1 = next((c for p, h, c in hashed_results if h == h1), None)
        if not c1: continue
        for j in range(i+1, len(unique_hashes)):
            h2 = unique_hashes[j]
            c2 = next((c for p, h, c in hashed_results if h == h2), None)
            if not c2: continue
            if _color_distance(c1, c2) < 15.0:
                # Fonde h2 in h1
                hash_to_macro[h2] = hash_to_macro[h1]
                
    img_to_label = {}
    for i, (p, h, c) in enumerate(hashed_results):
        if h:
            macro_h = hash_to_macro[h]
            if macro_h in img_to_label:
                labels[i] = img_to_label[macro_h]
            else:
                img_to_label[macro_h] = labels[i]
                
    # Salva i macro hash per la deduplicazione interna
    global_hashes = {getattr(p, "asin", p.get("asin") if isinstance(p, dict) else ""): hash_to_macro[h] for p, h, c in hashed_results if h}
    
    import re
    def _get_val(obj, key):
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _get_img_id(url: str) -> str:
        if not url: return ""
        m = re.search(r'/images/I/([^._\s]+)', url)
        return m.group(1) if m else url

    from amazon_search import imagecache
    from amazon_search.scoring import _dominant_color, _color_distance
    domain = job["result"].filters.get("domain", "it").lower()

    clusters = {}
    for idx, label in enumerate(labels):
        p = products[idx]
        p_thumb = _get_val(p, "thumbnail")
        p_asin = _get_val(p, "asin")
        p_title = _get_val(p, "title")
        p_price_str = _get_val(p, "price_str")
        p_cat = _get_val(p, "category")
        
        img_id = _get_img_id(p_thumb)
        
        # Risolvi colore dominante locale
        p_color = None
        # Disabilitato per evitare blocchi asincroni di scraping sulla rete
        # if p_asin:
        #     fp = imagecache.local_path(p_asin, domain=domain)
        #     if fp and os.path.exists(fp):
        #         p_color = _dominant_color(fp)

        clusters.setdefault(int(label), []).append({
            "asin": p_asin,
            "title": p_title,
            "thumbnail": p_thumb,
            "img_id": img_id,
            "color": p_color,
            "price_str": p_price_str,
            "category": p_cat
        })
        
    result_clusters = []
    global_mean = np.asarray(X.mean(axis=0)).flatten()
    for label, items in clusters.items():
        cluster_indices = [i for i, l in enumerate(labels) if l == label]
        cluster_vectors = X[cluster_indices]
        mean_vector = np.asarray(cluster_vectors.mean(axis=0)).flatten()
        
        # Sottrai la media globale per trovare i termini SPECIFICI di questo cluster
        specific_vector = mean_vector - (global_mean * 0.8) 
        top_term_indices = specific_vector.argsort()[-5:][::-1]
        top_terms = [feature_names[i] for i in top_term_indices if specific_vector[i] > 0]
        
        # Deduplica usando gli hash calcolati a livello globale
        unique_items = []
        img_counts = {}
        for item in items:
            h = global_hashes.get(item["asin"])
            if h:
                img_counts[h] = img_counts.get(h, 0) + 1
                
        seen_hashes = set()
        for item in items:
            h = global_hashes.get(item["asin"])
            if h:
                if h in seen_hashes:
                    continue
                seen_hashes.add(h)
                item["dup_count"] = img_counts[h]
            else:
                item["dup_count"] = 1
            unique_items.append(item)
            
        # Raggruppa gli elementi visivamente simili (distanza colore ristretta < 20)
        # Assegna un sub_color_group_id
        color_groups = {}
        group_counter = 0
        for i, item in enumerate(unique_items):
            if "color_group" in item:
                continue
            if not item["color"]:
                continue
            # Trova altri simili non ancora assegnati
            has_matches = False
            for j in range(i + 1, len(unique_items)):
                other = unique_items[j]
                if "color_group" in other or not other["color"]:
                    continue
                dist = _color_distance(item["color"], other["color"])
                if dist <= 22.0: # Soglia di somiglianza colore stretta
                    if not has_matches:
                        item["color_group"] = group_counter
                        has_matches = True
                    other["color_group"] = group_counter
            if has_matches:
                group_counter += 1
                
        # Calcola sottogruppi se richiesto
        subs = []
        if d.get("subgroups", False) and len(unique_items) > 1:
            from sklearn.cluster import Birch
            sub_threshold = float(d.get("sub_threshold", 0.40))
            # Se è K-Means o ibrido con K-Means, Birch potrebbe non essere l'ideale, 
            # ma usiamo Birch sui vettori globali per coerenza di distanze col parametro
            if cluster_vectors.shape[0] > 1:
                sub_brc = Birch(threshold=sub_threshold, n_clusters=None)
                sub_brc.fit(cluster_vectors)
                item_to_sub = {item["asin"]: sub_lbl for item, sub_lbl in zip(items, sub_brc.labels_)}
                
                sub_dict = {}
                for u in unique_items:
                    lbl = item_to_sub.get(u["asin"], 0)
                    sub_dict.setdefault(int(lbl), []).append(u)
                    
                # keywords del sottogruppo: parole frequenti QUI ma non in tutto il cluster
                _sub_stop = {"della", "delle", "dello", "degli", "with", "para",
                             "anti", "this", "that", "from", "your", "sono"}
                cluster_wc = Counter()
                for u in unique_items:
                    cluster_wc.update(set(re.findall(r"[a-zà-ù]{4,}", (u.get("title") or "").lower())))
                for s_id, s_items in sub_dict.items():
                    wc = Counter()
                    for u in s_items:
                        wc.update(set(re.findall(r"[a-zà-ù]{4,}", (u.get("title") or "").lower())))
                    distinctive = sorted(
                        (w for w, c in wc.items()
                         if c >= max(2, len(s_items) // 2) and w not in _sub_stop),
                        key=lambda w: (cluster_wc[w] / max(len(unique_items), 1), -wc[w]))
                    subs.append({
                        "id": f"{label}_{s_id}",
                        "terms": distinctive[:3],
                        "unique_products": s_items
                    })
            else:
                subs.append({"id": f"{label}_0", "unique_products": unique_items})
        else:
            subs.append({"id": f"{label}_0", "unique_products": unique_items})
                
        result_clusters.append({
            "id": label,
            "terms": top_terms,
            "products": items,
            "unique_products": unique_items,
            "subgroups": subs
        })
        
    return jsonify({"clusters": result_clusters})

@app.route("/api/scene_match", methods=["POST"])
def api_scene_match():
    data = request.json
    url1 = data.get("template_url")
    url2 = data.get("scene_url")
    if not url1 or not url2:
        return jsonify({"error": "Mancano URL"})
        
    try:
        import cv2
        import numpy as np
        import urllib.request
        import base64
        
        def download_cv2(url):
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                return cv2.imdecode(arr, -1)
                
        img1 = download_cv2(url1)
        img2 = download_cv2(url2)
        if img1 is None or img2 is None:
            return jsonify({"error": "Impossibile scaricare le immagini"})
            
        # Scala l'immagine 2 se troppo grande
        sh2 = 500 / max(img2.shape[:2])
        if sh2 < 1.0: img2 = cv2.resize(img2, None, fx=sh2, fy=sh2)
        sh1 = 500 / max(img1.shape[:2])
        if sh1 < 1.0: img1 = cv2.resize(img1, None, fx=sh1, fy=sh1)
        
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        sift = cv2.SIFT_create(400)
        k1, d1 = sift.detectAndCompute(gray1, None)
        k2, d2 = sift.detectAndCompute(gray2, None)
        
        if d1 is None or d2 is None or len(k1) < 4:
            return jsonify({"error": "Pochi dettagli per il tracciamento SIFT"})
            
        pairs = cv2.BFMatcher(cv2.NORM_L2).knnMatch(d1, d2, k=2)
        good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.75 * n.distance]
        
        if len(good) < 8:
            return jsonify({"error": "Nessuna corrispondenza visiva trovata"})
            
        src_pts = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
        dst_pts = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
        
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        
        success = False
        if H is not None and mask.sum() >= 8:
            h, w = gray1.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, H)
            
            # Controlli geometrici per evitare "strisce" o match sballati
            area = cv2.contourArea(np.int32(dst))
            h2, w2 = gray2.shape
            x, y, bw, bh = cv2.boundingRect(np.int32(dst))
            
            if cv2.isContourConvex(np.int32(dst)) and area >= (h2 * w2 * 0.03) and area <= (h2 * w2 * 0.95) and bw > 0 and bh > 0 and max(bw/bh, bh/bw) <= 4.0:
                # Disegna il rettangolo verde acceso spesso
                img2 = cv2.polylines(img2, [np.int32(dst)], True, (0, 255, 0), 4, cv2.LINE_AA)
                success = True
            
        _, buffer = cv2.imencode('.jpg', img2)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            "success": success,
            "inliers": int(mask.sum()) if mask is not None else 0,
            "result_image": f"data:image/jpeg;base64,{img_b64}"
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# --- PRECALCOLO OFFLINE BACKGROUND ---
SIFT_PROGRESS = {"total": 1, "done": 0, "status": "idle"}

@app.route("/api/sift_progress")
def api_sift_progress():
    global SIFT_PROGRESS
    return jsonify(SIFT_PROGRESS)

def _precalculate_offline(job):
    global SIFT_PROGRESS
    SIFT_PROGRESS["status"] = "running"
    print("Inizio precalcolo offline dei dati pesanti (SIFT RANSAC)...")
    products = getattr(job.get("result"), "products", [])
    if not products: 
        SIFT_PROGRESS["status"] = "done"
        return
    
    import cv2
    import numpy as np
    import urllib.request
    import concurrent.futures
    import base64
    
    def download_cv2(p):
        thumb = getattr(p, "thumbnail", None) or (p if isinstance(p, dict) else "")
        if isinstance(thumb, dict): thumb = thumb.get("thumbnail", "")
        if not thumb: return None, None
        try:
            req = urllib.request.Request(thumb, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                arr = np.asarray(bytearray(resp.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1)
                if img is None: return None, None
                sh = 500 / max(img.shape[:2])
                if sh < 1.0: img = cv2.resize(img, None, fx=sh, fy=sh)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                return img, gray
        except:
            return None, None

    SIFT_PROGRESS["status"] = "downloading"
    SIFT_PROGRESS["total"] = len(products)
    SIFT_PROGRESS["done"] = 0
    imgs = [None] * len(products)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_idx = {executor.submit(download_cv2, products[i]): i for i in range(len(products))}
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                imgs[idx] = future.result()
            except Exception:
                imgs[idx] = (None, None)
            SIFT_PROGRESS["done"] += 1
        
    import imagehash
    from PIL import Image
    
    # 1. Calcola i pHash in memoria sui download paralleli effettuati
    hashes = {}
    for i, (img, gray) in enumerate(imgs):
        if img is not None:
            try:
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                hashes[i] = imagehash.phash(pil_img)
            except:
                pass
                
    # 2. Raggruppa i prodotti simili in famiglie pHash (Hamming distance <= 8)
    family_map = {}
    family_counter = 0
    visited = set()
    for i in hashes:
        if i in visited: continue
        fam = [i]
        visited.add(i)
        for j in hashes:
            if j in visited: continue
            if hashes[i] - hashes[j] <= 8:
                fam.append(j)
                visited.add(j)
        if len(fam) > 1:
            family_id = f"fam_{family_counter}"
            family_counter += 1
            for idx in fam:
                family_map[products[idx].asin] = family_id
                products[idx].family_id = family_id

    sift = cv2.SIFT_create(400)
    features = []
    for i, (img, gray) in enumerate(imgs):
        if gray is not None:
            k, d = sift.detectAndCompute(gray, None)
            features.append((i, img, gray, k, d))
            
    matches_found = []
    bf = cv2.BFMatcher(cv2.NORM_L2)
    SIFT_PROGRESS["total"] = len(features)
    for i in range(len(features)):
        SIFT_PROGRESS["done"] = i
        i_idx, img1, gray1, k1, d1 = features[i]
        asin1 = products[i_idx].asin
        if d1 is None or len(k1) < 4: continue
        for j in range(len(features)):
            if i == j: continue
            j_idx, img2, gray2, k2, d2 = features[j]
            asin2 = products[j_idx].asin
            
            # Escludi a monte il confronto geometrico tra duplicati/immagini simili!
            if asin1 in family_map and asin2 in family_map and family_map[asin1] == family_map[asin2]:
                continue
                
            if d2 is None or len(k2) < 4: continue
            
            pairs = bf.knnMatch(d1, d2, k=2)
            # Stricter Lowe's ratio to avoid false positives (volti modelle, duplicati spuri)
            good = [m for m, n in (p for p in pairs if len(p) == 2) if m.distance < 0.70 * n.distance]
            
            if len(good) >= 12: # Minimo 12 inliers per evitare falsi positivi
                src_pts = np.float32([k1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst_pts = np.float32([k2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
                H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                
                if H is not None and mask.sum() >= 12:
                    h, w = gray1.shape
                    pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, H)
                    
                    # Filtra rettangoli sballati, troppo sottili o non convessi (evita "strisce" false)
                    if not cv2.isContourConvex(np.int32(dst)):
                        continue
                    area = cv2.contourArea(np.int32(dst))
                    h2, w2 = gray2.shape
                    
                    if area < (h2 * w2 * 0.03): # Area deve essere almeno 3%
                        continue
                    if area > (h2 * w2 * 0.65): # Se copre più del 65%, NON è una scena, è un duplicato del prodotto isolato!
                        continue
                        
                    x, y, bw, bh = cv2.boundingRect(np.int32(dst))
                    if bw == 0 or bh == 0 or max(bw/bh, bh/bw) > 2.5: # Scarta forme troppo allungate (rettangoli sminchiati)
                        continue
                    if bw == 0 or bh == 0 or max(bw/bh, bh/bw) > 4.0: # No strisce lunghe
                        continue
                        
                    out_img = img2.copy()
                    cv2.polylines(out_img, [np.int32(dst)], True, (0, 255, 0), 4, cv2.LINE_AA)
                    _, buffer = cv2.imencode('.jpg', out_img)
                    img_b64 = base64.b64encode(buffer).decode('utf-8')
                    matches_found.append({
                        "prod_1": (getattr(products[i_idx], "title", None) or products[i_idx].get("title", ""))[:40],
                        "prod_2": (getattr(products[j_idx], "title", None) or products[j_idx].get("title", ""))[:40],
                        "inliers": int(mask.sum()),
                        "image": f"data:image/jpeg;base64,{img_b64}"
                    })
                    SIFT_PROGRESS["current_matches"] = list(matches_found)

    unique_matches = []
    seen = set()
    matches_found.sort(key=lambda x: -x["inliers"])
    for m in matches_found:
        pair = frozenset([m["prod_1"], m["prod_2"]])
        if pair not in seen:
            seen.add(pair)
            unique_matches.append(m)
            
    job["scene_matches"] = unique_matches
    
    # Salva offline separatamente per ottimizzare i tempi di caricamento all'avvio
    import json
    from pathlib import Path
    try:
        products_data = {
            "products": [
                {
                    "asin": p.asin, "title": p.title, "thumbnail": getattr(p, "thumbnail", None),
                    "price_str": getattr(p, "price_str", None), "brand": getattr(p, "brand", None),
                    "category": getattr(p, "category", None),
                    "family_id": getattr(p, "family_id", None)
                } for p in products
            ]
        }
        OFFLINE_PATH = Path.home() / ".amazon_search_offline.json"
        query_key = getattr(job.get("result"), "query", "dataset").lower().strip().replace(" ", "_")
        SCENES_PATH = Path.home() / f".amazon_search_offline_scenes_{query_key}.json"
        
        OFFLINE_PATH.write_text(json.dumps(products_data, ensure_ascii=False, indent=1), encoding="utf-8")
        SCENES_PATH.write_text(json.dumps(unique_matches, ensure_ascii=False, indent=1), encoding="utf-8")
        
        print(f"Precalcolo SIFT terminato e SALVATO SU DISCO IN OFFLINE: trovati {len(unique_matches)} incroci (salvati separatamente).")
    except Exception as e:
        print(f"Errore salvataggio offline: {e}")
    finally:
        SIFT_PROGRESS["status"] = "done"

@app.route("/api/run_all_scenes", methods=["POST"])
def api_run_all_scenes():
    data = request.json
    job_id = data.get("job_id")
    if not job_id or job_id not in JOBS:
        return jsonify({"error": "Job non trovato"})
        
    job = JOBS[job_id]
        
    query_key = getattr(job.get("result"), "query", "dataset").lower().strip().replace(" ", "_")
    # Lazy load: se scene_matches è vuoto, lo carichiamo dal file separato
    if not job.get("scene_matches"):
        from pathlib import Path
        SCENES_PATH = Path.home() / f".amazon_search_offline_scenes_{query_key}.json"
        if SCENES_PATH.exists():
            try:
                print("Caricamento on-demand delle scene SIFT RANSAC...")
                job["scene_matches"] = json.loads(SCENES_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                print("Errore caricamento pigro scene:", e)
                
    if "scene_matches" in job and job["scene_matches"]:
        return jsonify({"matches": job["scene_matches"], "status": "ready"})
    else:
        if SIFT_PROGRESS["status"] not in ("running", "processing"):
            # Il thread non sta girando, avvialo ORA
            import threading
            threading.Thread(target=_precalculate_offline, args=(job,), daemon=True).start()
            
        return jsonify({"status": "processing", "message": "Precalcolo offline appena riavviato... attendi."})

@app.route("/api/terms_distribution", methods=["POST"])
def api_terms_distribution():
    data = request.json
    job_id = data.get("job_id")
    if not job_id or job_id not in JOBS:
        return jsonify({"error": "Job non trovato"})
        
    job = JOBS[job_id]
    products = getattr(job.get("result"), "products", [])
    if not products:
        return jsonify({"error": "Nessun prodotto nel dataset"})
        
    import re
    from collections import defaultdict
    
    threshold = float(data.get("threshold", 0.35))
    max_niche = int(data.get("max_niche", 30))
    
    # Raggruppa i prodotti per categoria (o 'Non Assegnati')
    categories_groups = defaultdict(list)
    for p in products:
        cat = getattr(p, "category", None) or "Generico"
        categories_groups[cat].append(p)
        
    stop_words = {"il","lo","la","i","gli","le","un","uno","una","di","a","da","in","con","su","per","tra","fra","e","o","ma","se","che","non","del","della","degli","delle","al","alla","agli","alle","dal","dalla","dagli","dalle","nel","nella","negli","nelle","col","coi","sul","sulla","sugli","sulle","cm","mm","kg","g","ml","l"}
    
    response_data = []
    
    for cat_name, items in categories_groups.items():
        doc_count = len(items)
        if doc_count < 2: continue # Ignora categorie con 1 solo item
        
        word_doc_map = defaultdict(list)
        for p in items:
            title = (getattr(p, "title", None) or "").lower()
            words = set(re.findall(r'\b[a-z]{2,}\b', title))
            thumb = getattr(p, "thumbnail", None)
            for w in words:
                if w not in stop_words and len(w) > 2:
                    if thumb and thumb not in word_doc_map[w]:
                        word_doc_map[w].append(thumb)
                    
        # Separiamo in "Parole Forti della Categoria" (Macro) e "Nicchie della Categoria" (Brand)
        macro_terms = []
        niche_terms = []
        
        for w, thumbs in word_doc_map.items():
            count = len(thumbs)
            if count < 2: continue
            pct = count / doc_count
            item = {"word": w, "count": count, "pct": round(pct * 100, 1), "thumbs": thumbs[:5]}
            
            if pct > threshold:
                macro_terms.append(item)
            else:
                niche_terms.append(item)
                
        macro_terms.sort(key=lambda x: -x["count"])
        niche_terms.sort(key=lambda x: -x["count"])
        
        response_data.append({
            "category": cat_name,
            "size": doc_count,
            "macro": macro_terms[:15],
            "niche": niche_terms[:max_niche]
        })
        
    response_data.sort(key=lambda x: -x["size"])
    return jsonify({"bubbles": response_data})

@app.route("/api/upload_image", methods=["POST"])
def upload_image():
    if "file" not in request.files:
        return jsonify({"error": "Nessun file caricato"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Nome file vuoto"}), 400
        
    temp_path = Path(__file__).resolve().parent / "static" / "uploads"
    temp_path.mkdir(parents=True, exist_ok=True)
    file_path = temp_path / f.filename
    f.save(str(file_path))
    
    from amazon_search.scoring import _dominant_color, _color_distance
    import concurrent.futures
    from amazon_search import imagecache
    
    color = _dominant_color(str(file_path))
    job_id = request.form.get("job_id")
    matches = []
    
    if job_id and color:
        job = JOBS.get(job_id)
        if job and job.get("result"):
            domain = job["result"].filters.get("domain", "it").lower()
            
            def check_product(p):
                if not getattr(p, "asin", None): return None
                fp = imagecache.local_path(p.asin, domain=domain, timeout=5.0)
                if fp and os.path.exists(fp):
                    p_color = _dominant_color(fp)
                    if p_color:
                        dist = _color_distance(color, p_color)
                        sim = max(0, 100 - (dist / 3))
                        if sim > 50:
                            return {
                                "asin": p.asin,
                                "title": p.title,
                                "thumbnail": getattr(p, "thumbnail", None),
                                "similarity": round(sim, 2)
                            }
                return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                results = list(executor.map(check_product, job["result"].products))
                matches = [r for r in results if r is not None]
                
            matches = sorted(matches, key=lambda x: x["similarity"], reverse=True)[:5]
            
    return jsonify({
        "url": f"/static/uploads/{f.filename}",
        "color": color,
        "matches": matches
    })


@app.route("/api/image/<asin>")
def api_image(asin):
    """Proxy locale per servire le immagini dei prodotti eludendo blocchi CORS/Referer del browser."""
    from amazon_search import imagecache
    from flask import send_file, redirect
    # Prova a prendere dal db/cache locale (o scaricare on-the-fly con timeout breve)
    fp = imagecache.local_path(asin, timeout=5.0)
    if fp and os.path.exists(fp):
        return send_file(fp, mimetype='image/jpeg')
    # Se fallisce, tenta il redirect all'URL originale come ultima spiaggia
    urls = imagecache.image_urls(asin, n=1)
    if urls:
        return redirect(urls[0])
    return "Not found", 404


VERDICTS_PATH = Path.home() / ".amazon_search_family_verdicts.json"


@app.route("/api/family_verdict", methods=["POST"])
def family_verdict():
    """User's call on a duplicate family: same product / different / different
    generations (the JBL Beam vs Beam 2 case). Persisted across restarts."""
    data = request.get_json() or {}
    asins = sorted(a for a in (data.get("asins") or []) if isinstance(a, str))
    verdict = data.get("verdict")
    if not asins or verdict not in ("same", "different", "generations"):
        return jsonify({"error": "asins + verdict (same|different|generations) required"}), 400
    try:
        store = json.loads(VERDICTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        store = {}
    store["|".join(asins)] = {"verdict": verdict, "job": data.get("job_id"),
                              "at": __import__("time").strftime("%Y-%m-%d %H:%M")}
    VERDICTS_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    return jsonify({"ok": True, "stored": len(store)})


def _family_verdicts() -> dict:
    try:
        return json.loads(VERDICTS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


@app.route("/api/dataset_info")
def dataset_info():
    try:
        uni = Path(__file__).resolve().parent.parent / "private" / "unified_dataset.json"
        data = json.loads(uni.read_text(encoding="utf-8"))
        prods = [d for d in (data.get("products") or []) if d.get("thumbnail")]
        labeled = sum(1 for d in prods if d.get("category"))
        return jsonify({"count": len(prods), "labeled": labeled,
                        "built_at": data.get("built_at")})
    except Exception:
        return jsonify({"count": 0})


@app.route("/api/searches")
def api_searches():
    """Ricerche in cache su disco (query + file), per la lista nella UI."""
    import glob
    out = []
    for f in glob.glob(str(Path.home() / ".amazon_search_cache" / "*.json")):
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("query"):
            out.append({"query": data["query"], "file": Path(f).name,
                        "count": len(data.get("products") or [])})
    return jsonify(out)


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
