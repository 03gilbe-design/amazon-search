# -*- coding: utf-8 -*-
"""Dump the dataset into one folder per category (photos), for a visual checkup.

Unlabeled products land in "_unassigned". Filenames carry price+title so a
mis-sorted photo is traceable back to the product without opening anything else.

Run:  python scripts/export_category_folders.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from webui.app import _build_dataset_job, JOBS

OUT_DIR = Path.home() / "amazon_search_reports" / "checkup_categorie"


def _slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower())[:n].strip("_") or "x"


def main():
    _build_dataset_job()
    products = JOBS["dataset"]["result"].products
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    by_cat: dict[str, list] = {}
    for p in products:
        by_cat.setdefault(p.category or "_unassigned", []).append(p)

    with httpx.Client(timeout=15, follow_redirects=True) as client:
        for cat, items in by_cat.items():
            folder = OUT_DIR / _slug(cat, 60)
            folder.mkdir(exist_ok=True)
            done, failed = 0, 0
            for p in items:
                if not p.thumbnail:
                    continue
                price = f"{p.price:.2f}" if p.price is not None else "na"
                fname = f"{price}e_{_slug(p.title)}_{p.asin}.jpg"
                fpath = folder / fname
                if fpath.exists():
                    done += 1
                    continue
                try:
                    r = client.get(p.thumbnail)
                    r.raise_for_status()
                    fpath.write_bytes(r.content)
                    done += 1
                except Exception:
                    failed += 1
            print(f"{cat:55s} {done:3d} foto" + (f"  ({failed} fallite)" if failed else ""))

    print(f"\ntotale prodotti: {len(products)}  |  categorie: {len(by_cat)}")
    print(f"cartella: {OUT_DIR}")


if __name__ == "__main__":
    main()
