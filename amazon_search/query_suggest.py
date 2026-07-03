# -*- coding: utf-8 -*-
"""Query variant suggestions — both deterministic (free) and AI-generated (costs a call).

Recovered and generalized from the neck-collar research (`build_query_gap_probe.py`): that
version scored candidate queries against a manually-labeled "good vs junk" set — a real,
useful technique, but it needs pre-existing labels this generic version doesn't have. What's
kept here is the two *generation* strategies (deterministic token-mining, AI free-text) minus
the labeled-precision scoring step, which only makes sense once you already know which results
were good (that's what `scoring.exclusion_reason()` + a human's own judgment give you, not
something this module can know on its own).
"""
from __future__ import annotations
import re
from collections import Counter

_STOPWORDS = {
    "the", "for", "and", "with", "a", "an", "of", "to", "in", "on",
    "il", "la", "lo", "un", "una", "per", "con", "da", "di", "del",
    "della", "delle", "degli", "e",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(t) >= 4 and t not in _STOPWORDS]


def deterministic_variants(query: str, products: list, *, top_k: int = 6) -> list[str]:
    """Free, no API call. Mines the most frequent title tokens (excluding words already
    in the query) across the KEPT products — words the real listings actually use that
    the original query didn't — and proposes "query + token" variants. Callers should
    pass only survivors (post negative-sampling), not raw results, so junk titles don't
    pollute the token frequency."""
    query_words = set(_tokens(query))
    freq = Counter()
    for p in products:
        for tok in _tokens(p.title):
            if tok not in query_words:
                freq[tok] += 1
    variants = [f"{query} {tok}" for tok, _ in freq.most_common(top_k)]
    return variants


def ai_variants(query: str, products: list, *, n: int = 8) -> list[str]:
    """Costs one LLM call (reuses llm.py's provider rotation). Asks for query variants
    that would surface more of what the current good results look like. Returns []
    on any failure — never blocks the pipeline."""
    from amazon_search.llm import _llm  # reuse existing provider rotation

    titles = [p.title for p in products[:15] if p.title]
    if not titles:
        return []
    prompt = (
        f"Query di ricerca Amazon attuale: \"{query}\".\n"
        f"Prodotti trovati (buoni, tenerne conto):\n- " + "\n- ".join(titles[:10]) + "\n\n"
        f"Genera {n} query di ricerca alternative (italiano o inglese) che troverebbero "
        f"prodotti simili a questi, con termini/sinonimi diversi dalla query originale. "
        f"Rispondi solo con le query, una per riga, senza numerazione."
    )
    try:
        text = _llm(prompt)
    except Exception:
        return []
    if not text:
        return []
    lines = [ln.strip("-• \t") for ln in text.splitlines() if ln.strip()]
    return [ln for ln in lines if ln.lower() != query.lower()][:n]
