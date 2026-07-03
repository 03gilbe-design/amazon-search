# -*- coding: utf-8 -*-
"""Feature-fit scoring and negative-sampling exclusion — both generic, both caller-supplied.

Neither function hardcodes any product category. The caller passes the real criteria/junk
patterns for the category being searched (a snoring collar and a smart ring have nothing in
common, but the matching logic is identical): keyword presence in title/bullets/specs.

Deliberately separate from `llm.py`'s AI budget-rank: this is rule-based and auditable (you can
see exactly which keyword matched), the AI rank is not. Never blend the two into one score —
they answer different questions ("does it match what I actually need" vs "is it cheap and
decent") and silently merging them would hide which one drove the final order.
"""
from __future__ import annotations


def _haystack(product) -> str:
    parts = [product.title or ""]
    parts.extend(product.bullets or [])
    parts.extend(f"{k} {v}" for k, v in (product.specs or {}).items())
    return " ".join(parts).lower()


def feature_fit_score(product, criteria: dict[str, list[str]]) -> tuple[float, dict[str, bool]]:
    """criteria: {"regolabile": ["regolabile", "adjustable"], "traspirante": [...], ...}
    Returns (score 0-1, {criterion: hit}) — the per-criterion breakdown matters more than
    the single number, so the report can show WHICH real-need signals were found, not just
    a score that could mean anything."""
    if not criteria:
        return 0.0, {}
    text = _haystack(product)
    hits = {name: any(kw.lower() in text for kw in keywords)
            for name, keywords in criteria.items()}
    score = sum(hits.values()) / len(criteria)
    return score, hits


def exclusion_reason(product, junk_patterns: dict[str, list[str]]) -> str | None:
    """junk_patterns: {"categoria_sbagliata": ["cuscino", "pillow"], ...} — caller-supplied,
    generic. Returns the matched category name, or None if nothing matched (product stays in).
    Callers must keep excluded items in an audit list, not silently drop them — an exclusion
    that can't be reviewed is just another hidden filter, the opposite of the point."""
    if not junk_patterns:
        return None
    text = _haystack(product)
    for reason, keywords in junk_patterns.items():
        if any(kw.lower() in text for kw in keywords):
            return reason
    return None
