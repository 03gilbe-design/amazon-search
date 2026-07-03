"""Fetch detailed product specs from Canopy API.

Canopy = 100/mese. Used ONLY for --specs flag (detail per ASIN).
Path: data.amazonProductSearchResults.productResults.results (search)
Path: data.amazonProduct (product detail)
"""
from __future__ import annotations

import os

import httpx

from amazon_search import quota

CANOPY_BASE = "https://rest.canopyapi.co"
TIMEOUT = 30.0


def fetch_specs(asins: list[str], domain: str = "IT") -> dict[str, dict]:
    """Returns dict: asin → {bullets: [...], specs: {name: value}, in_stock: bool}

    Uses 1 Canopy credit per ASIN. Stops if quota exhausted.
    """
    key = os.environ.get("CANOPY_KEY", "")
    if not key:
        print("⚠ CANOPY_KEY non disponibile — specs saltate")
        return {}

    results: dict[str, dict] = {}

    with httpx.Client(timeout=TIMEOUT) as client:
        for asin in asins:
            if not quota.check_and_increment("canopy"):
                remaining = quota.remaining("canopy")
                print(f"⚠ Canopy quota esaurita ({remaining} rimasti) — specs saltate per {asin}+")
                break

            try:
                resp = client.get(
                    f"{CANOPY_BASE}/api/amazon/product",
                    params={"asin": asin, "domain": domain},
                    headers={"API-KEY": key},
                )
                resp.raise_for_status()
                data = resp.json()

                # Path: data.amazonProduct
                product = data.get("data", {}).get("amazonProduct") or data.get("amazonProduct") or {}

                raw_specs = product.get("technicalSpecifications") or []
                specs = {
                    s["name"]: s["value"]
                    for s in raw_specs
                    if isinstance(s, dict) and s.get("name") and s.get("value")
                }

                results[asin] = {
                    "bullets": product.get("featureBullets") or [],
                    "specs": specs,
                    "in_stock": bool(product.get("isInStock", True)),
                    "brand": product.get("brand"),
                }

            except Exception as e:
                quota.decrement("canopy")  # roll back — call failed
                print(f"⚠ Canopy product detail fallito per {asin}: {e}")
                results[asin] = {"bullets": [], "specs": {}, "in_stock": True, "brand": None}

    return results
