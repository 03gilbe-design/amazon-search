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


def categorize(product, categories: dict[str, list[str]], *, default: str = "Altro") -> str:
    """categories: {"Gonfiabile": ["gonfiabile","inflatable"], "Rigido": ["rigido","semirigido"], ...}
    ORDER MATTERS — first matching category wins (a title can match several keyword sets;
    the caller decides priority by list order, same principle as feature-fit: auditable,
    not a black box). Every product lands in exactly one bucket, `default` catches the rest.
    This is the deterministic half of "sub-categories by eye" — the photo/vision half still
    needs a human or montage.py, keyword matching alone can't see what a photo shows."""
    if not categories:
        return default
    text = _haystack(product)
    for name, keywords in categories.items():
        if any(kw.lower() in text for kw in keywords):
            return name
    return default


_STOPWORDS = {
    "collare", "cervicale", "supporto", "collo", "neck", "support", "per", "il", "la", "lo",
    "con", "da", "di", "del", "della", "delle", "degli", "the", "for", "and", "un", "una",
}


def _dominant_color(image_path: str) -> tuple[int, int, int] | None:
    """Average RGB of the FOREGROUND only — Amazon product photos are almost always shot
    on a near-white background, so a plain full-image average is mostly measuring "how
    much white border does this photo have", not the product's actual color. That's the
    real cause of false-positive clusters (two unrelated products both photographed on
    white look "similar" by color alone). Fix: drop near-white/near-gray pixels (low
    saturation, high brightness) before averaging, so only the actual product color counts."""
    try:
        from PIL import Image
        im = Image.open(image_path).convert("RGB").resize((32, 32))
        pixels = list(im.getdata())
        fg = [(r, g, b) for r, g, b in pixels
              if not (r > 235 and g > 235 and b > 235)  # near-white background
              and max(r, g, b) - min(r, g, b) > 8]        # near-gray/washed-out
        if len(fg) < 10:  # too little foreground survived, fall back to full average
            fg = pixels
        n = len(fg)
        return (sum(p[0] for p in fg) // n, sum(p[1] for p in fg) // n, sum(p[2] for p in fg) // n)
    except Exception:
        return None


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _unique_title_words(title: str) -> set[str]:
    """Single words AND adjacent word-pairs/triplets (bigrams/trigrams) — a shared
    phrase like "anti bruxismo" is a much stronger category signal than either word
    alone, since generic words that pass the stopword/frequency filter individually
    can still combine into something specific."""
    import re
    toks = [w for w in re.findall(r"[a-z0-9]+", (title or "").lower())
            if len(w) >= 4 and w not in _STOPWORDS]
    out = set(toks)
    for n in (2, 3):
        for i in range(len(toks) - n + 1):
            out.add(" ".join(toks[i:i + n]))
    return out


def visual_cluster(products: list, images: dict[str, str], *,
                    color_threshold: float = 40.0, min_shared_words: int = 1,
                    max_word_ratio: float = 0.3) -> dict[str, str]:
    """Groups products that keyword categorize() left in the default bucket, using two
    signals together (neither alone is reliable): similar average image color AND at least
    one DISCRIMINATIVE word shared between titles. Both conditions required — color alone
    would lump "all black items" together regardless of what they are; any-shared-word
    alone over-merges on words that are common across the whole leftover set (a word
    appearing in 40% of "Altro" isn't distinctive of a sub-group, it's just common).

    A word only counts as discriminative if it appears in at most `max_word_ratio` of the
    leftover set — this is what keeps clusters from bleeding into each other ("buoni
    margini, non merged"): common-but-not-generic words get filtered out the same way
    stopwords are, just based on measured frequency in THIS batch instead of a fixed list.

    images: {product_id: local_image_path} (see imagecache.local_path).
    Returns {product_id: cluster_label} only for products that got grouped (2+ members) —
    products that match no one stay out, the caller keeps them in "Altro" rather than
    inventing a fake category of one."""
    from collections import Counter

    colors: dict[str, tuple] = {}
    raw_words: dict[str, set] = {}
    for p in products:
        img = images.get(p.asin)
        if img:
            c = _dominant_color(img)
            if c:
                colors[p.asin] = c
        raw_words[p.asin] = _unique_title_words(p.title)

    # document frequency: how many products (not occurrences) each word appears in
    doc_freq: Counter = Counter()
    for ws in raw_words.values():
        doc_freq.update(ws)
    max_docs = max(1, int(max_word_ratio * len(products)))
    words = {a: {w for w in ws if doc_freq[w] <= max_docs} for a, ws in raw_words.items()}

    def _pair_match(a: str, b: str) -> bool:
        return (_color_distance(colors[a], colors[b]) <= color_threshold
                and len(words[a] & words[b]) >= min_shared_words)

    # complete-linkage: a candidate joins a group only if it matches EVERY member
    # already in it, not just the seed. Single-linkage (match-the-seed-only) chains
    # A-B-C together when A-C don't actually belong together, which is exactly the
    # kind of noise a "buoni margini, non merged" grouping is supposed to avoid.
    ids = [p.asin for p in products if p.asin in colors]
    seen: set[str] = set()
    clusters: list[list[str]] = []
    for i, a in enumerate(ids):
        if a in seen:
            continue
        group = [a]
        seen.add(a)
        for b in ids[i + 1:]:
            if b in seen:
                continue
            if all(_pair_match(b, g) for g in group):
                group.append(b)
                seen.add(b)
        if len(group) > 1:
            clusters.append(group)

    assignment: dict[str, str] = {}
    for i, group in enumerate(clusters):
        # label with the longest shared phrase (a bigram/trigram reads better than
        # a lone word, e.g. "anti bruxismo" over just "bruxismo")
        common = set.intersection(*(words[a] for a in group)) if len(group) > 1 else set()
        label = f"Simili: {max(common, key=len)}" if common else f"Gruppo visivo {i+1}"
        for a in group:
            assignment[a] = label
    return assignment


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
