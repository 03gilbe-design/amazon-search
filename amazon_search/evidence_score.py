# -*- coding: utf-8 -*-
"""Position-weighted evidence scoring — generalized from the INCI eye-cream research.

The idea that worked there: an ordered ingredient list is EVIDENCE with decaying
weight — an active in the top-5 positions drives the product, the same active
after the preservative line is marketing dust. Scoring = sum of (active weight ×
positional multiplier), per category, normalized 0-100.

Generic here: "ingredients" can be INCI names, spec bullet keywords, feature
tokens — anything ordered by importance. NOT wired into the main pipeline
(standalone by design): import and call, or run this file for a self-check.

    from amazon_search.evidence_score import evidence_scores
    ACTIVES = {
        "caffeine":   {"weight": 30, "category": "vascular"},
        "retinol":    {"weight": 35, "category": "pigment"},
        "niacinamide":{"weight": 25, "category": "pigment"},
        "ceramide":   {"weight": 30, "category": "barrier"},
    }
    scores = evidence_scores(["water", "glycerin", "caffeine", ...], ACTIVES)
    # -> {"vascular": {"score": 27, "found": [("caffeine", 3, 1.0)]}, ...}
"""
from __future__ import annotations


def positional_multiplier(position: int) -> float:
    """1-based position in the ordered list -> evidence multiplier.
    Buckets from the eye-cream research: top5=1.0, top10=0.7, top20=0.4, else 0.2."""
    if position <= 5:
        return 1.0
    if position <= 10:
        return 0.7
    if position <= 20:
        return 0.4
    return 0.2


def _matches(name: str, key: str) -> bool:
    n, k = name.lower().strip(), key.lower().strip()
    return n == k or (len(k) >= 5 and k in n) or (len(n) >= 5 and n in k)


def evidence_scores(items: list[str], actives: dict[str, dict],
                    *, cap: float = 100.0) -> dict[str, dict]:
    """items: ordered list (most important first). actives: {key: {weight, category}}.
    Returns {category: {"score": 0-100, "found": [(key, position, multiplier), ...]}}.
    Each active counts once (best position wins)."""
    by_cat: dict[str, dict] = {}
    seen: set[str] = set()
    for pos, name in enumerate(items, 1):
        for key, spec in actives.items():
            if key in seen or not _matches(name, key):
                continue
            seen.add(key)
            mult = positional_multiplier(pos)
            cat = by_cat.setdefault(spec.get("category", "default"),
                                    {"score": 0.0, "found": []})
            cat["score"] += spec.get("weight", 10) * mult
            cat["found"].append((key, pos, mult))
    for cat in by_cat.values():
        cat["score"] = round(min(cat["score"], cap), 1)
    return by_cat


if __name__ == "__main__":  # self-check
    actives = {"caffeine": {"weight": 30, "category": "vascular"},
               "niacinamide": {"weight": 25, "category": "pigment"},
               "ceramide np": {"weight": 30, "category": "barrier"}}
    inci = ["Water", "Glycerin", "Caffeine", "Dimethicone", "Phenoxyethanol",
            "Niacinamide", "Carbomer"] + ["Filler"] * 15 + ["Ceramide NP"]
    s = evidence_scores(inci, actives)
    assert s["vascular"]["score"] == 30.0, s          # pos 3 -> x1.0
    assert s["pigment"]["score"] == 25 * 0.7, s        # pos 6 -> x0.7
    assert s["barrier"]["score"] == 30 * 0.2, s        # pos 23 -> x0.2
    assert evidence_scores([], actives) == {}
    print("evidence_score self-check: PASS", {k: v["score"] for k, v in s.items()})
