# -*- coding: utf-8 -*-
"""Quick probe on the public Amazon ESCI dataset (local HF cache) to rank
noise-removal methods BEFORE the long night run. Zero LLM tokens.

Signal = products labeled E(xact) for the query; noise = S/C/I (or just I for
the lenient variant). Methods: the noise-lab trio + bm25s + RapidFuzz.

Output: private/ESCI_PROBE.md — ranked table that decides tonight's grids.
"""
from __future__ import annotations

import glob
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.night_noise_lab import sim_to_query, cluster_dominance, word_overlap_query, fbeta

HF_DATA = glob.glob(str(Path.home() / ".cache/huggingface/hub/datasets--tasksource--esci/snapshots/*/data"))[0]
PRIV = ROOT / "private"

N_QUERIES = 60


def load_queries():
    # i 4 shard test bastano e avanzano per un probe
    frames = []
    for f in sorted(glob.glob(HF_DATA + "/test-*.parquet")):
        frames.append(pd.read_parquet(f, columns=["query", "product_title",
                                                   "esci_label", "product_locale"]))
    df = pd.concat(frames)
    df = df[df["product_locale"] == "us"]
    picked = []
    for q, g in df.groupby("query"):
        vc = g["esci_label"].value_counts()
        # abbastanza grande, con segnale E e rumore vero I
        if len(g) >= 14 and vc.get("Exact", vc.get("E", 0)) >= 5 and vc.get("Irrelevant", vc.get("I", 0)) >= 3:
            picked.append((q, g))
            if len(picked) >= N_QUERIES:
                break
    return picked


def m_bm25(rows, query):
    import bm25s
    corpus = [r["title"] for r in rows]
    retriever = bm25s.BM25()
    retriever.index(bm25s.tokenize(corpus, show_progress=False), show_progress=False)
    qtok = bm25s.tokenize([query], show_progress=False)
    docs, scores = retriever.retrieve(qtok, k=len(corpus), show_progress=False)
    smap = {int(d): float(s) for d, s in zip(docs[0], scores[0])}
    mx = max(smap.values()) or 1.0
    return [smap.get(i, 0.0) / mx for i in range(len(corpus))]


def m_rapidfuzz(rows, query):
    from rapidfuzz import fuzz
    return [fuzz.token_set_ratio(query, r["title"]) / 100.0 for r in rows]


METHODS = {
    "sim_query mv800":        lambda rows, q: sim_to_query(rows, q, 800),
    "cluster_dom mv800 ct.25": lambda rows, q: cluster_dominance(rows, q, 800, 0.25),
    "word_overlap":           word_overlap_query,
    "bm25s (norm)":           m_bm25,
    "rapidfuzz token_set":    m_rapidfuzz,
}
THRESHOLDS = [0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7]


def main():
    t0 = time.time()
    picked = load_queries()
    print(f"{len(picked)} query campionate ({time.time()-t0:.0f}s load)")

    label_col = "esci_label"
    rows0 = picked[0][1]
    exact_val = "Exact" if "Exact" in set(rows0[label_col]) else "E"

    # per ogni metodo: F2 medio alla SUA soglia migliore (scelta sul campione)
    table = []
    for mname, fn in METHODS.items():
        per_thr = {t: [] for t in THRESHOLDS}
        tm = time.time()
        for q, g in picked:
            rows = [{"title": t} for t in g["product_title"].tolist()]
            truth = (g[label_col] == exact_val).tolist()
            try:
                scores = fn(rows, q)
            except Exception as e:
                print(f"  {mname} ERR {e}")
                break
            for t in THRESHOLDS:
                f, p, r = fbeta([s >= t for s in scores], truth)
                per_thr[t].append(f)
        best_t, best_f = max(((t, sum(v) / max(len(v), 1)) for t, v in per_thr.items()),
                             key=lambda x: x[1])
        table.append((mname, best_t, best_f, time.time() - tm))
        print(f"{mname:26s} best_thr={best_t:.2f} F2={best_f:.3f} ({time.time()-tm:.0f}s)")

    table.sort(key=lambda r: -r[2])
    lines = [f"# ESCI quick probe — {time.strftime('%Y-%m-%d %H:%M')}",
             f"{len(picked)} query US (shard test), segnale=Exact, F-beta2 medio alla soglia migliore",
             "", "| metodo | soglia | F2 | tempo |", "|---|---|---|---|"]
    lines += [f"| {m} | {t:.2f} | {f:.3f} | {s:.0f}s |" for m, t, f, s in table]
    lines += ["", "Indicazione per la notte: ampliare la griglia dei top-2 metodi, "
              "scartare quelli sotto 0.5."]
    PRIV.mkdir(exist_ok=True)
    (PRIV / "ESCI_PROBE.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport: {PRIV / 'ESCI_PROBE.md'} | tot {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
