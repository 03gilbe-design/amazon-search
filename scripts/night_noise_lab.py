# -*- coding: utf-8 -*-
"""Noise-removal lab — find a GENERAL, zero-AI, zero-questions method.

Given a user query, decide automatically which products in the result pool are
noise (wrong product type) without asking the user anything and without any
LLM. Candidate methods are evaluated against the hand-labeled ground truth and
must hold up on MULTIPLE niches (config-driven) to avoid overfitting one.

Everything personal (label->signal mappings, queries, niche names) lives in
private/noise_lab_config.json (gitignored). Without it the script exits.

Usage:
  python scripts/night_noise_lab.py --quick    # coarse grid, minutes
  python scripts/night_noise_lab.py            # full grid, hours (night run)

Output: private/NOISE_LAB_REPORT.md + private/noise_lab_results.json
Metric: F-beta with beta=2 on the SIGNAL class (recall-heavy: never throw away
good products), reported per niche + worst-niche score (generality).
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from amazon_search.scoring import _tfidf_vectors, _cosine_sim, _unique_title_words

PRIV = Path(__file__).resolve().parent.parent / "private"
CONFIG_PATH = PRIV / "noise_lab_config.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f"config mancante: {CONFIG_PATH} — vedi docstring")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_ground_truth() -> list[dict]:
    p = Path.home() / "amazon_search_reports" / "ground_truth_dataset.json"
    return json.loads(p.read_text(encoding="utf-8"))


# ---------------- candidate scoring methods (all pure math) ----------------

def sim_to_query(rows, query, max_vocab):
    """Cosine similarity of each title to the query string in TF-IDF space."""
    texts = {i: r["title"] for i, r in enumerate(rows)}
    texts["__q__"] = query
    vecs, _ = _tfidf_vectors(texts, max_vocab=max_vocab)
    q = vecs["__q__"]
    return [_cosine_sim(vecs[i], q) for i in range(len(rows))]


def cluster_dominance(rows, query, max_vocab, cluster_thr):
    """Greedy clustering; score of a product = similarity of ITS CLUSTER's
    centroid to the query (noise clusters score low as a block)."""
    texts = {i: r["title"] for i, r in enumerate(rows)}
    texts["__q__"] = query
    vecs, _ = _tfidf_vectors(texts, max_vocab=max_vocab)
    q = vecs.pop("__q__")
    ids = list(range(len(rows)))
    seen, clusters = set(), []
    for i in ids:
        if i in seen:
            continue
        grp = [i]
        seen.add(i)
        for j in ids:
            if j not in seen and _cosine_sim(vecs[i], vecs[j]) >= cluster_thr:
                grp.append(j)
                seen.add(j)
        clusters.append(grp)
    score = [0.0] * len(rows)
    for grp in clusters:
        cen = [sum(col) / len(grp) for col in zip(*(vecs[i] for i in grp))]
        s = _cosine_sim(cen, q)
        for i in grp:
            score[i] = s
    return score


def word_overlap_query(rows, query):
    """Jaccard-style overlap between title words and query words (cheapest)."""
    qw = _unique_title_words(query)
    out = []
    for r in rows:
        tw = _unique_title_words(r["title"])
        out.append(len(qw & tw) / len(qw) if qw else 0.0)
    return out


def price_inlier(rows):
    """1 if price inside IQR fence of the pool, else 0 (noise often prices apart)."""
    prices = [r.get("price") for r in rows if isinstance(r.get("price"), (int, float))]
    if len(prices) < 8:
        return [1.0] * len(rows)
    prices.sort()
    q1 = prices[len(prices) // 4]
    q3 = prices[3 * len(prices) // 4]
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    out = []
    for r in rows:
        p = r.get("price")
        out.append(1.0 if not isinstance(p, (int, float)) or lo <= p <= hi else 0.0)
    return out


# ---------------- evaluation ----------------

def fbeta(preds, truth, beta=2.0):
    tp = sum(1 for p, t in zip(preds, truth) if p and t)
    fp = sum(1 for p, t in zip(preds, truth) if p and not t)
    fn = sum(1 for p, t in zip(preds, truth) if not p and t)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    if not prec and not rec:
        return 0.0, prec, rec
    b2 = beta * beta
    return (1 + b2) * prec * rec / (b2 * prec + rec) if (prec or rec) else 0.0, prec, rec


def run(quick: bool):
    cfg = load_config()
    rows_all = load_ground_truth()
    t0 = time.time()
    results = []

    grids = {
        "sim_query":    {"max_vocab": [300, 800, 1200] if quick else [100, 300, 600, 800, 1200, 2000],
                         "keep_thr": [0.02, 0.05, 0.1, 0.15] if quick else [0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.15, 0.2]},
        "cluster_dom":  {"max_vocab": [800] if quick else [400, 800, 1200],
                         "cluster_thr": [0.2, 0.3] if quick else [0.15, 0.2, 0.25, 0.3, 0.4],
                         "keep_thr": [0.02, 0.05, 0.1] if quick else [0.01, 0.02, 0.05, 0.08, 0.12]},
        "word_overlap": {"keep_thr": [0.34, 0.5, 0.67] if quick else [0.2, 0.34, 0.5, 0.67, 0.99]},
    }

    for niche in cfg["niches"]:
        name, query = niche["name"], niche["query"]
        signal_sets = {k: set(v) for k, v in niche["signal_labels"].items()}
        rows = [r for r in rows_all if r["category"] in niche.get("universe", [])] \
            if niche.get("universe") else rows_all
        for sig_name, sig_labels in signal_sets.items():
            truth = [r["category"] in sig_labels for r in rows]
            n_sig = sum(truth)
            if n_sig < 5:
                continue

            def evaluate(method, params, scores):
                for kt in (params.pop("keep_thr_list") if "keep_thr_list" in params else [params["keep_thr"]]):
                    preds = [s >= kt for s in scores]
                    f, prec, rec = fbeta(preds, truth)
                    results.append({"niche": name, "signal": sig_name, "method": method,
                                    "params": {**params, "keep_thr": kt},
                                    "fbeta2": round(f, 4), "precision": round(prec, 4),
                                    "recall": round(rec, 4), "n": len(rows), "n_signal": n_sig})

            g = grids["sim_query"]
            for mv in g["max_vocab"]:
                scores = sim_to_query(rows, query, mv)
                evaluate("sim_query", {"max_vocab": mv, "keep_thr_list": g["keep_thr"]}, scores)

            g = grids["cluster_dom"]
            for mv, ct in itertools.product(g["max_vocab"], g["cluster_thr"]):
                scores = cluster_dominance(rows, query, mv, ct)
                evaluate("cluster_dom", {"max_vocab": mv, "cluster_thr": ct,
                                          "keep_thr_list": g["keep_thr"]}, scores)

            scores = word_overlap_query(rows, query)
            evaluate("word_overlap", {"keep_thr_list": grids["word_overlap"]["keep_thr"]}, scores)

            # price come segnale aggiuntivo combinato con sim_query migliore
            pr = price_inlier(rows)
            base = sim_to_query(rows, query, 800)
            for kt in ([0.02, 0.05] if quick else [0.01, 0.02, 0.05, 0.08]):
                preds = [s >= kt and p > 0 for s, p in zip(base, pr)]
                f, prec, rec = fbeta(preds, truth)
                results.append({"niche": name, "signal": sig_name, "method": "sim+price",
                                "params": {"max_vocab": 800, "keep_thr": kt},
                                "fbeta2": round(f, 4), "precision": round(prec, 4),
                                "recall": round(rec, 4), "n": len(rows), "n_signal": n_sig})

    # GENERALITÀ: per ogni (method, params) presenti in TUTTE le nicchie/segnali,
    # punteggio = minimo tra le nicchie (il metodo vince solo se regge ovunque)
    by_key: dict[str, list] = {}
    for r in results:
        # generalità su metodo+parametri: i nomi dei segnali variano per nicchia
        key = r["method"] + "|" + json.dumps(r["params"], sort_keys=True)
        by_key.setdefault(key, []).append(r)
    general = []
    n_niches = len({r["niche"] for r in results})
    for key, rs in by_key.items():
        if len({r["niche"] for r in rs}) == n_niches:
            general.append({"key": key, "min_fbeta2": min(r["fbeta2"] for r in rs),
                            "mean_fbeta2": round(sum(r["fbeta2"] for r in rs) / len(rs), 4),
                            "detail": rs})
    general.sort(key=lambda g: -g["min_fbeta2"])

    PRIV.mkdir(exist_ok=True)
    (PRIV / "noise_lab_results.json").write_text(
        json.dumps({"quick": quick, "elapsed_s": round(time.time() - t0, 1),
                    "results": results, "general_top": general[:40]}, indent=1),
        encoding="utf-8")

    lines = [f"# Noise Lab report ({'quick' if quick else 'full'}) — {time.strftime('%Y-%m-%d %H:%M')}",
             f"combos: {len(results)} | tempo: {time.time()-t0:.0f}s | metrica: F-beta2 sul SEGNALE (recall pesa doppio)",
             "", "## Top metodi GENERALI (score = peggiore tra le nicchie)"]
    for g in general[:12]:
        head = g["detail"][0]
        lines.append(f"- min={g['min_fbeta2']:.3f} mean={g['mean_fbeta2']:.3f} | {head['method']} "
                     f"{head['params']} | signal={head['signal']}")
        for d in g["detail"]:
            lines.append(f"    {d['niche']}: F={d['fbeta2']:.3f} P={d['precision']:.2f} R={d['recall']:.2f}")
    (PRIV / "NOISE_LAB_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:30]))
    print(f"\nreport completo: {PRIV / 'NOISE_LAB_REPORT.md'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    run(ap.parse_args().quick)
