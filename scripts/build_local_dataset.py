# -*- coding: utf-8 -*-
"""Build the unified local dataset the app loads — clean, deduped, enriched.

Sources (read-only): ~/.amazon_search_cache/*.json, ~/.amazon_search_offline.json,
~/.amazon_search_learned_categories.json, ~/amazon_search_reports/ground_truth_dataset.json

Rules:
- one record per ASIN, best-known fields win (latest cache file wins on conflict)
- duplicates with SAME thumbnail AND SAME price -> keep one (not interesting);
  same thumbnail but DIFFERENT price -> keep both, mark duplicate_of + saving
- local enrichment (zero ML, from the Colab findings):
  * numeric specs regex (mah/w/gb/inch/g/kg/hours/l/p/bluetooth)
  * materials keywords (memory foam, gel, cotone, ...)
  * same-mold transfer: if a twin (>=2 shared number+unit tokens in title)
    has a spec this product lacks -> copy it as estimated_specs

Output: <repo>/private/unified_dataset.json + unified_dataset_stats.md
Run:  python scripts/build_local_dataset.py
"""
from __future__ import annotations

import glob
import itertools
import json
import re
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"

# unita' scelte DAI DATI (scan titoli reali 2026-07-11): cm=30, V=25,
# modalita'/livelli/posizioni=26, pezzi=20, giorni=8, mm, lm, gradi C
SPEC_RX = {
    "battery_mah": r"(\d{3,6})\s*mah",
    "power_w": r"(\d{1,4}(?:[.,]\d)?)\s*w(?:att)?s?\b",
    "voltage_v": r"(\d{1,3}(?:[.,]\d)?)\s*v(?:olt)?s?\b",
    "bluetooth": r"bluetooth\s*(\d\.\d)",
    "screen_in": r"(\d{1,2}(?:[.,]\d)?)\s*(?:inch|pollici)\b",
    "size_cm": r"(\d{1,3}(?:[.,]\d)?)\s*cm\b",
    "size_mm": r"(\d{1,3}(?:[.,]\d)?)\s*mm\b",
    "weight_g": r"(\d{2,5})\s*g(?:rammi|rams?)?\b",
    "weight_kg": r"(\d{1,3}(?:[.,]\d{1,2})?)\s*kg\b",
    "hours_h": r"(\d{1,3})\s*(?:hours|ore|hrs|h)\b",
    "days_d": r"(\d{1,3})\s*giorni\b",
    "storage_gb": r"(\d{2,4})\s*gb\b",
    "modes_n": r"(\d{1,2})\s*(?:modalità|livelli|posizioni|strati|velocità|modes|levels|speeds)\b",
    "pieces_n": r"(\d{1,3})\s*(?:pezzi|pcs|pz|pieces|pack|count|ct)\b",
    "lumen_lm": r"(\d{2,5})\s*lm\b",
    "temp_c": r"(\d{1,3})\s*°\s*c\b",
}
MATERIALS = ("memory foam", "gel", "cotone", "cotton", "poliestere", "polyester",
             "silicone", "lattice", "latex", "schiuma", "foam", "velluto", "velvet",
             "pelle", "leather", "bamboo", "bambù", "lana", "wool", "seta", "silk",
             "microfibra", "microfiber", "eva", "abs", "acciaio", "steel", "alluminio")

FP_RX = re.compile(r"\d+(?:[.,]\d+)?\s*(?:mah|w|gb|kg|g|inch|pollici|ore|hours|h|l|cm|mm|p)\b")


# attributi QUALITATIVI (dai prodotti veri: nei titoli non-tech i numeri quasi
# non esistono - contano rigidita', gonfiabile, regolabile, lavabile, taglia)
ATTR_RX = {
    "rigido": r"\brigid[oa]|semirigid[oa]|semi-rigid|\brigid\b|stiff",
    "morbido": r"\bmorbid[oa]|\bsoft\b|plush",
    "gonfiabile": r"gonfiabile|inflatable|\bad aria\b",
    "regolabile": r"regolabile|adjustable",
    "lavabile": r"lavabile|washable|machine wash",
    "portatile": r"portatile|da viaggio|portable|travel|foldable|pieghevole",
    "ricaricabile": r"ricaricabile|rechargeable|usb-?c?\b",
    "impermeabile": r"impermeabile|waterproof|water resistant",
    "wireless": r"wireless|senza fili|bluetooth",
    "taglia": r"\btaglia [smlx]{1,3}\b|\bsize [smlx]{1,3}\b|cod\.art|\d{2}-\d{2} ?cm",
}
ATTR_RX = {k: re.compile(v) for k, v in ATTR_RX.items()}


def extract_attrs(text):
    t = (text or "").lower()
    return [a for a, rx in ATTR_RX.items() if rx.search(t)]


# ── scoperta unita' AUTOMATICA: niente liste hardcoded ──────────────────
# A: scan generico "numero + token"; B: un token e' un'unita' se quando appare
# e' quasi sempre attaccato a un numero (num_ratio) e ricorre nel pool;
# B x C: la lista risultante e' specifica di QUESTO pool di prodotti.
_NUM_TOKEN_RX = re.compile(r"(\d+(?:[.,]\d+)?)\s*([a-zà-ù%°\"]{1,12})\b")
_TOKEN_RX = re.compile(r"[a-zà-ù%°\"]{1,12}")


def discover_units(texts, min_count=3, num_ratio=0.65):
    """Token che nel pool compaiono quasi solo preceduti da un numero = unita'.
    'cm' passa (30/30 volte dopo numero), 'collare' no (4/100)."""
    with_num = Counter()
    total = Counter()
    for t in texts:
        tl = (t or "").lower()
        for m in _NUM_TOKEN_RX.finditer(tl):
            with_num[m.group(2)] += 1
        for tok in _TOKEN_RX.findall(tl):
            total[tok] += 1
    return {u for u, c in with_num.items()
            if c >= min_count and c / max(total[u], 1) >= num_ratio}


def extract_specs_auto(text, units):
    t = (text or "").lower()
    out = {}
    for m in _NUM_TOKEN_RX.finditer(t):
        num, unit = m.group(1), m.group(2)
        if unit in units and unit not in out:
            try:
                out[unit] = float(num.replace(",", "."))
            except ValueError:
                pass
    return out


def extract_specs(text: str) -> dict:
    t = (text or "").lower()
    out = {}
    for k, rx in SPEC_RX.items():
        m = re.search(rx, t)
        if m:
            try:
                out[k] = float(m.group(1).replace(",", "."))
            except ValueError:
                pass
    return out


def extract_materials(text: str) -> list[str]:
    t = (text or "").lower()
    return [m for m in MATERIALS if m in t]


def fingerprint(title: str) -> frozenset:
    return frozenset(m.group(0).replace(" ", "").replace(",", ".")
                     for m in FP_RX.finditer((title or "").lower()))


def main():
    t0 = time.time()
    records: dict[str, dict] = {}
    src_count = Counter()

    def merge(item: dict, source: str, query: str | None = None):
        asin = item.get("asin")
        if not asin or not item.get("title"):
            return
        r = records.setdefault(asin, {"asin": asin, "source_queries": []})
        for k in ("title", "price", "price_str", "stars", "reviews", "thumbnail",
                  "link", "brand", "family_id"):
            v = item.get(k)
            if v is not None and v != "":
                r[k] = v
        if query and query not in r["source_queries"]:
            r["source_queries"].append(query)
        src_count[source] += 1

    for f in sorted(glob.glob(str(Path.home() / ".amazon_search_cache" / "*.json"))):
        try:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
        except Exception:
            continue
        items = data.get("products") if isinstance(data, dict) else data
        q = data.get("query") if isinstance(data, dict) else None
        if isinstance(items, list):
            for it in items:
                if isinstance(it, dict):
                    merge(it, "cache", q)

    off = Path.home() / ".amazon_search_offline.json"
    if off.exists():
        try:
            data = json.loads(off.read_text(encoding="utf-8"))
            for it in (data.get("products") or []):
                merge(it, "offline")
        except Exception:
            pass

    # ground truth (264 righe etichettate con titolo+thumb) come sorgente prodotti
    gt = Path.home() / "amazon_search_reports" / "ground_truth_dataset.json"
    if gt.exists():
        try:
            for it in json.loads(gt.read_text(encoding="utf-8")):
                merge({"asin": it.get("asin"), "title": it.get("title"),
                       "thumbnail": it.get("thumbnail")}, "ground_truth")
        except Exception:
            pass

    # labels
    learned = {}
    lp = Path.home() / ".amazon_search_learned_categories.json"
    if lp.exists():
        try:
            learned = json.loads(lp.read_text(encoding="utf-8")).get("_global", {})
        except Exception:
            pass
    for asin, cat in learned.items():
        if asin in records:
            records[asin]["category"] = cat

    # dedup: same thumbnail
    by_thumb: dict[str, list[str]] = {}
    for a, r in records.items():
        th = r.get("thumbnail")
        if th:
            by_thumb.setdefault(th, []).append(a)
    dropped_same_price = 0
    marked_savings = 0
    for th, asins in by_thumb.items():
        if len(asins) < 2:
            continue
        asins.sort(key=lambda a: records[a].get("price") if records[a].get("price") is not None else 9e9)
        keeper = asins[0]
        kp = records[keeper].get("price")
        for a in asins[1:]:
            p = records[a].get("price")
            if p is not None and kp is not None and abs(p - kp) < 0.01:
                # stesso prodotto, stesso prezzo: non interessante a schermo — ma
                # PRIMA di buttarlo fondi i suoi dati nel keeper (un listing puo'
                # mostrare cio' che l'altro nasconde: l'obiettivo e' la scheda completa)
                ku = records[keeper]
                for fld in ("stars", "reviews", "brand"):
                    if not ku.get(fld) and records[a].get(fld):
                        ku[fld] = records[a][fld]
                ku.setdefault("merged_listings", []).append(a)
                del records[a]
                dropped_same_price += 1
            else:
                records[a]["duplicate_of"] = keeper
                if p is not None and kp is not None:
                    records[a]["saving_vs_duplicate"] = round(p - kp, 2)
                    marked_savings += 1

    # enrichment — unita' scoperte automaticamente da QUESTO pool
    pool_units = discover_units(r.get("title", "") for r in records.values())
    # prior da ESCI (1.2M prodotti, scoperto su Colab): unita' note che nel nostro
    # pool sono troppo rare per superare la soglia locale, ma valide comunque
    try:
        esci_units = json.loads((PRIV / "esci_discovered_units.json").read_text(encoding="utf-8"))
        prior = {u for loc in esci_units.values() for u in loc}
        pool_units |= prior
    except Exception:
        pass
    print(f"unita' scoperte dal pool: {sorted(pool_units)}")
    for r in records.values():
        r["specs"] = extract_specs_auto(r.get("title", ""), pool_units)
        mats = extract_materials(r.get("title", ""))
        if mats:
            r["materials"] = mats
        attrs = extract_attrs(r.get("title", ""))
        if attrs:
            r["attrs"] = attrs

    # same-mold transfer (estimated specs dal gemello)
    fps = {a: fingerprint(r.get("title", "")) for a, r in records.items()}
    transferred = 0
    asins = [a for a in records if len(fps[a]) >= 2]
    for a, b in itertools.combinations(asins, 2):
        if len(fps[a] & fps[b]) >= 2:
            ra, rb = records[a], records[b]
            for src, dst in ((ra, rb), (rb, ra)):
                for k, v in src.get("specs", {}).items():
                    if k not in dst.get("specs", {}) and k not in dst.get("estimated_specs", {}):
                        dst.setdefault("estimated_specs", {})[k] = v
                        transferred += 1
                if src.get("materials") and not dst.get("materials"):
                    dst["estimated_materials"] = src["materials"]

        # fusione dati nelle famiglie confermate dall'utente come STESSO prodotto
    # (verdetti Same dal report): specs/materiali/attrs passano tra i membri
    verd_path = Path.home() / ".amazon_search_family_verdicts.json"
    merged_from_verdicts = 0
    try:
        verd = json.loads(verd_path.read_text(encoding="utf-8"))
    except Exception:
        verd = {}
    for key, v in verd.items():
        if (v or {}).get("verdict") != "same":
            continue
        members = [records[x] for x in key.split("|") if x in records]
        if len(members) < 2:
            continue
        for fld in ("specs", "materials", "attrs"):
            pool = {}
            for m in members:
                vals = m.get(fld)
                if isinstance(vals, dict):
                    pool.update(vals)
                elif isinstance(vals, list):
                    pool = {x: True for x in list(pool) + vals}
            for m in members:
                cur = m.get(fld)
                if isinstance(pool, dict) and not isinstance(cur, list):
                    extra = {k2: v2 for k2, v2 in pool.items()
                             if v2 is not True and k2 not in (cur or {})}
                    if extra:
                        m.setdefault("estimated_specs", {}).update(extra)
                        merged_from_verdicts += len(extra)
                elif pool:
                    lst = sorted(set((cur or []) + [k2 for k2, v2 in pool.items() if v2 is True]))
                    if lst != (cur or []):
                        m[fld] = lst
                        merged_from_verdicts += 1

    PRIV.mkdir(exist_ok=True)
    out = PRIV / "unified_dataset.json"
    out.write_text(json.dumps({"built_at": time.strftime("%Y-%m-%d %H:%M"),
                               "products": list(records.values())},
                              ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(records)
    labeled = sum(1 for r in records.values() if r.get("category"))
    with_specs = sum(1 for r in records.values() if r.get("specs"))
    with_mats = sum(1 for r in records.values() if r.get("materials"))
    with_attrs = sum(1 for r in records.values() if r.get("attrs"))
    with_est = sum(1 for r in records.values() if r.get("estimated_specs") or r.get("estimated_materials"))
    stats = [
        f"# Unified dataset — {time.strftime('%Y-%m-%d %H:%M')} ({time.time()-t0:.1f}s)",
        f"- prodotti unici: **{n}** (da {dict(src_count)})",
        f"- scartati duplicati stesso-thumb+stesso-prezzo: {dropped_same_price}",
        f"- duplicati con risparmio marcato: {marked_savings}",
        f"- etichettati (categoria utente): {labeled} ({labeled/max(n,1):.0%})",
        f"- con specs estratte: {with_specs} ({with_specs/max(n,1):.0%})",
        f"- con materiali: {with_mats} ({with_mats/max(n,1):.0%})",
        f"- con attributi qualitativi: {with_attrs} ({with_attrs/max(n,1):.0%})",
        f"- con specs/materiali STIMATI dal gemello stesso-stampo: {with_est} (trasferimenti: {transferred})",
        f"- fusioni da verdetti-Same dell'utente: {merged_from_verdicts}",
        f"- output: {out}",
    ]
    (PRIV / "unified_dataset_stats.md").write_text("\n".join(stats), encoding="utf-8")
    print("\n".join(stats))


if __name__ == "__main__":
    main()
