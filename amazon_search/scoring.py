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
    # Title-only products (no bullets/specs fetched) can't prove a criterion ABSENT:
    # a miss there means "unknown", not "no" — showing it as a confident ✗ misled
    # real searches (--specs not used -> everything looked like a bad fit). None
    # marks the unknowns; score counts them as 0 but the report can render "?".
    thin_data = not (product.bullets or product.specs)
    hits: dict[str, bool | None] = {}
    for name, keywords in criteria.items():
        found = any(kw.lower() in text for kw in keywords)
        hits[name] = True if found else (None if thin_data else False)
    score = sum(1 for v in hits.values() if v) / len(criteria)
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


def color_palette_vector(image_path: str, *, bins_per_channel: int = 4) -> list[float] | None:
    """A real palette fingerprint — what fraction of foreground pixels fall in each small
    RGB range — instead of collapsing the whole image to one averaged color. Two products
    that are half-black/half-white would average to the same gray as one that's uniformly
    gray; a histogram tells them apart because it captures WHICH colors are present and
    how much of each, not just their blend. Same background exclusion as _dominant_color.
    Returns a normalized vector of length bins_per_channel**3 (default 4^3=64 bins)."""
    try:
        from PIL import Image
        im = Image.open(image_path).convert("RGB").resize((48, 48))
        pixels = list(im.getdata())
        fg = [(r, g, b) for r, g, b in pixels
              if not (r > 235 and g > 235 and b > 235)
              and max(r, g, b) - min(r, g, b) > 8]
        if len(fg) < 10:
            fg = pixels
        n_bins = bins_per_channel
        hist = [0.0] * (n_bins ** 3)
        step = 256 // n_bins
        for r, g, b in fg:
            idx = (min(r // step, n_bins - 1) * n_bins * n_bins
                   + min(g // step, n_bins - 1) * n_bins
                   + min(b // step, n_bins - 1))
            hist[idx] += 1
        total = sum(hist) or 1
        return [h / total for h in hist]
    except Exception:
        return None


def _color_distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def _unique_title_words(text: str) -> set[str]:
    """Single words AND adjacent word-pairs/triplets (bigrams/trigrams) — a shared
    phrase like "anti bruxismo" is a much stronger category signal than either word
    alone, since generic words that pass the stopword/frequency filter individually
    can still combine into something specific.

    Despite the name (kept for compatibility), callers should pass the FULL text —
    title + bullets + specs via _haystack(product) — not just the bare title, whenever
    that richer text is available (it usually isn't unless --specs ran, since that costs
    Canopy credits; falls back gracefully to title-only text either way)."""
    import re
    toks = [w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if len(w) >= 4 and w not in _STOPWORDS]
    out = set(toks)
    for n in (2, 3):
        for i in range(len(toks) - n + 1):
            out.add(" ".join(toks[i:i + n]))
    return out


def _tfidf_vectors(texts: dict[str, str], *, max_vocab: int = 300) -> tuple[dict[str, list[float]], list[str]]:
    """Real TF-IDF, not a hard include/exclude cutoff: every word gets a continuous
    weight (rare-in-corpus words score high, common ones score low), so richer/longer
    text (e.g. marketing bullets) doesn't just inject noise at a fixed threshold — common
    filler phrases get automatically down-weighted instead of needing a tuned cutoff.
    Returns (vectors, vocab) so callers know which dimension is which word."""
    import math
    from collections import Counter

    tokenized = {pid: sorted(_unique_title_words(t)) for pid, t in texts.items()}
    doc_freq: Counter = Counter()
    for toks in tokenized.values():
        doc_freq.update(set(toks))
    n_docs = len(texts)
    vocab = [w for w, _ in doc_freq.most_common(max_vocab)]
    vocab_ix = {w: i for i, w in enumerate(vocab)}
    idf = {w: math.log(n_docs / (1 + doc_freq[w])) for w in vocab}

    vectors = {}
    for pid, toks in tokenized.items():
        tf = Counter(toks)
        vec = [0.0] * len(vocab)
        for w, c in tf.items():
            if w in vocab_ix:
                vec[vocab_ix[w]] = c * idf[w]
        vectors[pid] = vec
    return vectors, vocab


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def word_vectors(products: list, *, max_word_ratio: float = 0.3, max_vocab: int = 60) -> dict[str, list[float]]:
    """One bag-of-discriminative-words vector per product, same dimension/order for all —
    for plotting products in "word space" (montage.build_word_scatter) the same way
    _dominant_color lets you plot them in "color space". Same discriminative-word filter
    as visual_cluster (words in more than max_word_ratio of the batch are dropped — too
    common to separate anything), capped to the `max_vocab` most frequent survivors so the
    vector stays a reasonable size."""
    from collections import Counter

    raw_words = {p.asin: _unique_title_words(p.title) for p in products}
    doc_freq: Counter = Counter()
    for ws in raw_words.values():
        doc_freq.update(ws)
    max_docs = max(1, int(max_word_ratio * len(products)))
    vocab_counter = Counter({w: c for w, c in doc_freq.items() if 1 < c <= max_docs})
    vocab = [w for w, _ in vocab_counter.most_common(max_vocab)]
    return {p.asin: [1.0 if w in raw_words[p.asin] else 0.0 for w in vocab] for p in products}


def visual_cluster(products: list, images: dict[str, str], *,
                    color_threshold: float = 40.0, min_shared_words: int = 2,
                    max_word_ratio: float = 0.1,
                    use_tfidf: bool = True, tfidf_threshold: float = 0.25,
                    text_fn=None) -> dict[str, str]:
    """Groups products that keyword categorize() left in the default bucket, using two
    signals together (neither alone is reliable): similar average image color AND a
    word-similarity signal (TF-IDF cosine by default, see below) above threshold. Both
    conditions required — color alone would lump "all black items" together regardless
    of what they are; word similarity alone is just categorize() again.

    Defaults calibrated against a real hand-labeled ground truth (59 products, 24 real
    categories, manually classified by eye from a montage — see project history), tested
    across several real configurations, not guessed:
      - binary shared-word count, max_word_ratio=0.3, min_shared_words=1 (first attempt):
        66% purity, 4/16 clean clusters
      - binary, max_word_ratio=0.1, min_shared_words=2 (tightened): 79% purity, 5/11 clean
      - TF-IDF cosine, title+bullets+specs (richer text): 30-55% purity depending on
        threshold — WORSE. Marketing bullet text is generically similar across genuinely
        different products; more text was more noise, not more signal, regardless of
        weighting scheme (confirmed: TF-IDF's automatic down-weighting of common words
        didn't fix it either — it's the text content itself, not a threshold problem).
      - TF-IDF cosine, TITLE ONLY, threshold=0.25 (current default): 83% purity, 6/11
        clean clusters — best result found, now the default. use_tfidf=False restores
        the binary method above (kept for comparison / cases where cosine similarity
        behaves worse, e.g. very short titles with little vocabulary overlap to weight).

    images: {product_id: local_image_path} (see imagecache.local_path). `text_fn`
    controls what text feeds the word signal (defaults to title only — see above for why
    bullets/specs measured worse despite intuition suggesting richer text should help).
    Returns {product_id: cluster_label} only for products that got grouped (2+ members) —
    products that match no one stay out, the caller keeps them in "Altro" rather than
    inventing a fake category of one."""
    from collections import Counter

    colors: dict[str, tuple] = {}
    for p in products:
        img = images.get(p.asin)
        if img:
            c = _dominant_color(img)
            if c:
                colors[p.asin] = c

    text_fn = text_fn or (lambda p: p.title)

    if use_tfidf:
        # continuous weighting instead of a hard include/exclude cutoff: safe to use
        # with richer text (title+bullets+specs) since common filler phrases get
        # down-weighted automatically rather than needing a re-tuned ratio threshold.
        texts = {p.asin: text_fn(p) for p in products}
        tfidf, _vocab = _tfidf_vectors(texts)

        def _pair_match(a: str, b: str) -> bool:
            return (_color_distance(colors[a], colors[b]) <= color_threshold
                    and _cosine_sim(tfidf[a], tfidf[b]) >= tfidf_threshold)
    else:
        raw_words = {p.asin: _unique_title_words(text_fn(p)) for p in products}
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

    if not use_tfidf:
        label_words = raw_words  # unfiltered, for nicer/longer label candidates
    else:
        label_words = {p.asin: _unique_title_words(text_fn(p)) for p in products}

    assignment: dict[str, str] = {}
    for i, group in enumerate(clusters):
        # label with the longest shared phrase (a bigram/trigram reads better than
        # a lone word, e.g. "anti bruxismo" over just "bruxismo")
        common = set.intersection(*(label_words[a] for a in group)) if len(group) > 1 else set()
        label = f"Simili: {max(common, key=len)}" if common else f"Gruppo visivo {i+1}"
        for a in group:
            assignment[a] = label
    return assignment


def refine_large_clusters(products: list, assignment: dict[str, str], images: dict[str, str], *,
                           min_size: int = 5, color_threshold: float = 25.0,
                           tfidf_threshold: float = 0.15) -> dict[str, str]:
    """Second pass: any cluster from visual_cluster() with `min_size`+ members gets
    re-clustered on its own, with looser thresholds (tighter color match, lower
    similarity bar) — verified live on real data: this correctly split a generic
    "Simili: schanz" (8 collars, mixed brands) into real brand-specific sub-groups
    (Moretti 3, TIELLE CAMP 2, 3 unmatched) instead of leaving them lumped together,
    while correctly leaving a genuinely single-product cluster (5 KMINA size variants)
    as one group since there was nothing real left to split.

    Sub-cluster labels REPLACE the parent label for members that get re-grouped;
    members the second pass can't place any further keep their ORIGINAL (parent)
    label — never dropped down to ungrouped just because a finer split didn't find
    them a smaller home."""
    by_label: dict[str, list] = {}
    for p in products:
        label = assignment.get(p.asin)
        if label:
            by_label.setdefault(label, []).append(p)

    refined = dict(assignment)
    for label, members in by_label.items():
        if len(members) < min_size:
            continue
        sub_images = {p.asin: images[p.asin] for p in members if p.asin in images}
        sub_assignment = visual_cluster(members, sub_images,
                                         color_threshold=color_threshold,
                                         tfidf_threshold=tfidf_threshold)
        for p in members:
            if p.asin in sub_assignment:
                refined[p.asin] = sub_assignment[p.asin]
            # else: keep the parent label already in `refined` — no regression to "ungrouped"
    return refined


def merge_similar_clusters(products: list, assignment: dict[str, str], images: dict[str, str], *,
                            color_threshold: float = 55.0, tfidf_threshold: float = 0.35) -> dict[str, str]:
    """The opposite direction of refine_large_clusters(): after splitting finds fine
    sub-groups (e.g. "Moretti schanz" vs "TIELLE CAMP schanz" vs a few unmatched Schanz
    collars), this asks whether those fine groups actually belong to the same broader
    family — by treating EACH CLUSTER as if it were a single representative product
    ("i singoli gruppi come delle specie di singole immagini") and re-clustering those
    representatives with a LOOSER threshold than the splitting pass. Two fine clusters
    that merge here become one parent label; clusters that don't match anyone stay as
    their own fine label — nothing is forced together.

    Ungrouped singletons (assignment doesn't cover them) are left untouched; this only
    operates on products that already got a label from an earlier pass."""
    from amazon_search.searcher import AmazonProduct

    by_label: dict[str, list] = {}
    for p in products:
        label = assignment.get(p.asin)
        if label:
            by_label.setdefault(label, []).append(p)
    if len(by_label) < 2:
        return dict(assignment)

    # one pseudo-product per cluster: representative image = first member with an
    # image, representative "title" = the cluster's members' titles concatenated (so
    # word-overlap between REPRESENTATIVES reflects word-overlap between the real
    # clusters, not just one arbitrarily-picked member)
    reps: list = []
    rep_images: dict[str, str] = {}
    for label, members in by_label.items():
        combined_title = " ".join(m.title for m in members)
        reps.append(AmazonProduct(
            title=combined_title, asin=label, brand=None, price=None, price_str="",
            stars=None, reviews=None, thumbnail=None, link="", prime=False,
            in_stock=True, source="cluster_rep",
        ))
        for m in members:
            if m.asin in images:
                rep_images[label] = images[m.asin]
                break

    rep_assignment = visual_cluster(reps, rep_images,
                                     color_threshold=color_threshold, tfidf_threshold=tfidf_threshold)

    merged = dict(assignment)
    for label, members in by_label.items():
        parent_label = rep_assignment.get(label)
        if parent_label:
            for m in members:
                merged[m.asin] = parent_label
    return merged


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
