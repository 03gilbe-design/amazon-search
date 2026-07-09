# -*- coding: utf-8 -*-
"""Night orchestrator: full noise-lab grid on the local ground truth, then
external validation on the public Amazon ESCI dataset (query relevance labels)
— all zero-AI, resumable, everything logged to private/.

Phases (each skipped if its output already exists — safe to re-run):
  1. full grid on local labels     -> private/NOISE_LAB_REPORT.md
  2. download ESCI parquet files   -> private/esci/ (examples ~80MB, products ~2GB)
  3. evaluate the same methods on ESCI queries (signal=E[xact], noise=I[rrelevant])
     -> private/ESCI_REPORT.md
  4. combined verdict              -> private/NIGHT_REPORT.md

Run:  python scripts/night_run_all.py   (designed for an overnight scheduled run)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PRIV = ROOT / "private"
ESCI_DIR = PRIV / "esci"
LOG = PRIV / "night_log.txt"

ESCI_BASE = "https://github.com/amazon-science/esci-data/raw/main/shopping_queries_dataset/"
ESCI_FILES = ["shopping_queries_dataset_examples.parquet",
              "shopping_queries_dataset_products.parquet"]


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def phase1_local_full():
    if (PRIV / "NOISE_LAB_REPORT.md").exists() and "full" in (PRIV / "NOISE_LAB_REPORT.md").read_text(encoding="utf-8")[:80]:
        log("fase 1 già fatta, skip")
        return
    log("fase 1: full grid locale...")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "night_noise_lab.py")],
                       capture_output=True, text=True)
    log(f"fase 1 exit={r.returncode}")
    if r.returncode:
        log("stderr: " + r.stderr[-500:])


def phase2_download_esci():
    ESCI_DIR.mkdir(parents=True, exist_ok=True)
    import httpx
    for fn in ESCI_FILES:
        dst = ESCI_DIR / fn
        if dst.exists() and dst.stat().st_size > 1_000_000:
            log(f"fase 2: {fn} già presente ({dst.stat().st_size//1_000_000}MB), skip")
            continue
        log(f"fase 2: scarico {fn} ...")
        try:
            with httpx.stream("GET", ESCI_BASE + fn, follow_redirects=True, timeout=None) as r:
                r.raise_for_status()
                with dst.open("wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)
            log(f"fase 2: {fn} ok ({dst.stat().st_size//1_000_000}MB)")
        except Exception as e:
            log(f"fase 2: {fn} FALLITO: {e}")


def phase3_esci_eval(max_queries=300):
    out = PRIV / "ESCI_REPORT.md"
    if out.exists():
        log("fase 3 già fatta, skip")
        return
    try:
        import pandas as pd  # noqa
    except ImportError:
        log("fase 3: installo pandas+pyarrow...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pandas", "pyarrow"])
        import pandas as pd  # noqa
    import pandas as pd

    ex_p = ESCI_DIR / ESCI_FILES[0]
    pr_p = ESCI_DIR / ESCI_FILES[1]
    if not (ex_p.exists() and pr_p.exists()):
        log("fase 3: parquet mancanti, skip")
        return
    log("fase 3: carico ESCI (small_version, locale us)...")
    ex = pd.read_parquet(ex_p)
    ex = ex[(ex["small_version"] == 1) & (ex["product_locale"] == "us")]
    pr = pd.read_parquet(pr_p, columns=["product_id", "product_title", "product_locale"])
    pr = pr[pr["product_locale"] == "us"]
    df = ex.merge(pr, on="product_id")
    log(f"fase 3: {len(df)} righe esempio unite")

    sys.path.insert(0, str(ROOT))
    from scripts.night_noise_lab import sim_to_query, cluster_dominance, word_overlap_query, fbeta

    # query con abbastanza prodotti e almeno un po' di noise vero
    grp = df.groupby("query")
    picked = []
    for q, g in grp:
        lab = g["esci_label"].value_counts()
        if len(g) >= 12 and lab.get("E", 0) >= 4 and lab.get("I", 0) >= 2:
            picked.append((q, g))
        if len(picked) >= max_queries:
            break
    log(f"fase 3: {len(picked)} query valutabili")

    METHODS = {
        "sim_query mv800 kt.05":  lambda rows, q: [s >= 0.05 for s in sim_to_query(rows, q, 800)],
        "sim_query mv800 kt.02":  lambda rows, q: [s >= 0.02 for s in sim_to_query(rows, q, 800)],
        "sim_query mv1200 kt.05": lambda rows, q: [s >= 0.05 for s in sim_to_query(rows, q, 1200)],
        "cluster_dom mv800 ct.25 kt.05": lambda rows, q: [s >= 0.05 for s in cluster_dominance(rows, q, 800, 0.25)],
        "word_overlap kt.34":     lambda rows, q: [s >= 0.34 for s in word_overlap_query(rows, q)],
    }
    agg = {m: [] for m in METHODS}
    t0 = time.time()
    for qi, (q, g) in enumerate(picked):
        rows = [{"title": t} for t in g["product_title"].tolist()]
        truth = (g["esci_label"] == "E").tolist()  # segnale=Exact; noise=S/C/I
        for m, fn in METHODS.items():
            try:
                f, p, r = fbeta(fn(rows, q), truth)
                agg[m].append(f)
            except Exception:
                agg[m].append(0.0)
        if qi % 50 == 0:
            log(f"fase 3: {qi}/{len(picked)} query, {time.time()-t0:.0f}s")

    lines = [f"# ESCI external validation — {time.strftime('%Y-%m-%d %H:%M')}",
             f"{len(picked)} query US (small version), segnale=E, F-beta2 medio:", ""]
    for m, fs in sorted(agg.items(), key=lambda kv: -sum(kv[1]) / max(len(kv[1]), 1)):
        mean = sum(fs) / max(len(fs), 1)
        lines.append(f"- {m}: F2={mean:.3f} (min {min(fs):.2f}, max {max(fs):.2f})")
    out.write_text("\n".join(lines), encoding="utf-8")
    log("fase 3: report scritto")


def phase4_verdict():
    parts = []
    for f in ["NOISE_LAB_REPORT.md", "ESCI_REPORT.md"]:
        p = PRIV / f
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
    (PRIV / "NIGHT_REPORT.md").write_text(
        f"# NIGHT REPORT — {time.strftime('%Y-%m-%d %H:%M')}\n\n" + "\n\n---\n\n".join(parts),
        encoding="utf-8")
    log("fase 4: NIGHT_REPORT.md pronto")


if __name__ == "__main__":
    PRIV.mkdir(exist_ok=True)
    log("=== night run start ===")
    phase1_local_full()
    phase2_download_esci()
    phase3_esci_eval()
    phase4_verdict()
    log("=== night run done ===")
