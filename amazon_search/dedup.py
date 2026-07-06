# -*- coding: utf-8 -*-
"""Rebrand/same-mold detection via perceptual image hashing.

Products get relisted under different brands/titles with the *same* stock
photo (identical or resized) at different prices. Text/title similarity
misses this entirely; the product photo doesn't lie. Group by pHash
(Hamming distance <= threshold) to surface these families and their price
spread, so "same mold, pick the cheapest" becomes a checkable fact instead
of a guess.

Needs the `imagehash` package (pip install imagehash). Requires local image
files (see imagecache.py to fetch them first).
"""
from __future__ import annotations
from pathlib import Path


def phash_families(images: dict[str, str], *, threshold: int = 8) -> list[dict]:
    """Group items whose product photo is near-identical.

    Handles mirrored listings — a horizontally-flipped product shot has a plain pHash
    distance of ~30 from the original (measured), way above any sane threshold, so a
    naive single-hash compare misses it entirely. Each image gets hashed BOTH as-is and
    mirrored; two images match if the best (minimum) distance across those combinations
    clears the threshold — mirrored duplicates that would otherwise be invisible now
    match at distance ~0-8 like a normal duplicate.

    images: {item_id: local_image_path}. Returns a list of families, each
    `{"items": [item_id, ...], "diff_image": bool, "min_distance": int}` — diff_image is
    True when the family was found despite the source images not being byte-identical
    (resized/re-encoded/cropped copies of the same shot, not just literal dupes).
    `min_distance` is the closest pairwise Hamming distance found inside the family (0 =
    byte-identical hash, higher = more different but still under threshold) — sort
    families by this to put the most-confident matches first. Singletons (no match) are
    omitted.
    """
    import imagehash
    from PIL import Image, ImageOps

    hashes: dict[str, "imagehash.ImageHash"] = {}
    hashes_mirrored: dict[str, "imagehash.ImageHash"] = {}
    for item_id, path in images.items():
        try:
            im = Image.open(path)
            hashes[item_id] = imagehash.phash(im)
            hashes_mirrored[item_id] = imagehash.phash(ImageOps.mirror(im))
        except Exception:
            continue

    def _best_distance(a: str, b: str) -> int:
        return min(
            hashes[a] - hashes[b],
            hashes[a] - hashes_mirrored[b],
            hashes_mirrored[a] - hashes[b],
        )

    ids = list(hashes)
    seen: set[str] = set()
    families: list[dict] = []
    for i, a in enumerate(ids):
        if a in seen:
            continue
        group = [a]
        group_min_dist = 999
        seen.add(a)
        for b in ids[i + 1:]:
            if b in seen:
                continue
            d = _best_distance(a, b)
            if d <= threshold:
                group.append(b)
                seen.add(b)
                group_min_dist = min(group_min_dist, d)
        if len(group) > 1:
            paths = {images[x] for x in group}
            families.append({"items": group, "diff_image": len(paths) > 1,
                              "min_distance": group_min_dist})
    families.sort(key=lambda f: f["min_distance"])
    return families


def price_spread(family_items: list[str], prices: dict[str, float]) -> float | None:
    """Max-min price within a family, ignoring items with no known price."""
    vals = [prices[i] for i in family_items if prices.get(i) is not None]
    if len(vals) < 2:
        return None
    return max(vals) - min(vals)


# --- numeric spec fingerprint: rebrand detection when the photo is DIFFERENT ---
# pHash only catches relistings that reuse the same stock photo. Rebrands that shot
# their own photo are invisible to it — but same-mold products quote the same exact
# measurements in the title ("20.3x7.6 cm", "150kg", "72dB"). Numbers with units are
# hard to fake accidentally: two listings sharing several of them are the same mold.

import re as _re

_NUM_UNIT_RX = _re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(x\s*\d+(?:[.,]\d+)?(?:\s*x\s*\d+(?:[.,]\d+)?)?)?\s*"
    r"(cm|mm|m|kg|g|w|watt|db|v|volt|ah|mah|hz|khz|ohm|Ω|pollici|inch|\"|'')(?![a-zà-ù])",
    _re.IGNORECASE)


def numeric_fingerprint(title: str) -> frozenset[str]:
    """Normalized number+unit tokens from a title. '20,3 cm' and '20.3cm' -> same token.
    Dimension chains (20x30x5 cm) are kept whole — they're the most identifying."""
    toks = set()
    for m in _NUM_UNIT_RX.finditer(title or ""):
        num, dims, unit = m.group(1), m.group(2) or "", m.group(3)
        tok = (num + dims).replace(",", ".").replace(" ", "").lower()
        unit = {"watt": "w", "volt": "v", "ω": "ohm", "''": '"', "pollici": "inch"}.get(unit.lower(), unit.lower())
        toks.add(f"{tok}{unit}")
    return frozenset(toks)


def spec_families(titles: dict[str, str], *, min_shared: int = 2,
                  max_pool_ratio: float = 0.5) -> list[dict]:
    """Group items whose titles share >= min_shared rare numeric tokens.

    titles: {item_id: title}. Tokens present in more than max_pool_ratio of the pool
    are generic for the query ("12v" on a car-audio search) and are ignored — only
    discriminative numbers count. Returns [{"items": [...], "shared": [tokens]}],
    singletons omitted. Greedy like phash_families; meant as a complementary,
    lower-confidence tier (match="specs") after the photo-based one.
    """
    fps = {i: numeric_fingerprint(t) for i, t in titles.items()}
    n = len(fps)
    if n < 2:
        return []
    # drop tokens too common in this pool to identify anything
    counts: dict[str, int] = {}
    for fp in fps.values():
        for t in fp:
            counts[t] = counts.get(t, 0) + 1
    cutoff = max(2, int(n * max_pool_ratio))
    fps = {i: frozenset(t for t in fp if counts[t] <= cutoff) for i, fp in fps.items()}

    ids = list(fps)
    seen: set[str] = set()
    families: list[dict] = []
    for i, a in enumerate(ids):
        if a in seen:
            continue
        group, shared = [a], set()
        for b in ids[i + 1:]:
            if b in seen:
                continue
            common = fps[a] & fps[b]
            if len(common) >= min_shared:
                group.append(b)
                seen.add(b)
                shared |= common
        if len(group) > 1:
            seen.add(a)
            families.append({"items": group, "shared": sorted(shared)})
    families.sort(key=lambda f: -len(f["shared"]))
    return families


# --- pseudo-brand signal (idea da AmazonBrandFilter, ★54: filtrare per brand noti) ---
# I rebrand cinesi usano nomi generati per il registro marchi USA: consonanti a caso,
# tutto maiuscolo ("XKJIYU", "BZDZMQM"). Un nome così + stesso stampo = rebrand quasi certo.

_VOWELS = set("aeiou")


def pseudo_brand_score(brand: str) -> float:
    """0 = brand plausibile, 1 = quasi certamente nome-registro-marchi generato.
    Euristica pura, niente liste esterne: rapporto vocali, digrammi impronunciabili,
    tutto-maiuscolo. Da usare come segnale, mai come esclusione automatica."""
    b = (brand or "").strip()
    if not b or len(b) < 4:
        return 0.0
    letters = [c for c in b.lower() if c.isalpha()]
    if not letters:
        return 0.0
    score = 0.0
    vowel_ratio = sum(1 for c in letters if c in _VOWELS) / len(letters)
    if vowel_ratio < 0.2:
        score += 0.5
    elif vowel_ratio < 0.3:
        score += 0.25
    # lettere rare in inglese/italiano ma comunissime nei nomi generati
    rare_ratio = sum(1 for c in letters if c in "xkjqz") / len(letters)
    if rare_ratio >= 0.4:
        score += 0.4
    elif rare_ratio >= 0.25:
        score += 0.2
    # 3+ consonanti consecutive rare in parole vere (y conta da vocale)
    run = mx = 0
    for c in letters:
        run = run + 1 if c not in _VOWELS and c != "y" else 0
        mx = max(mx, run)
    if mx >= 4:
        score += 0.35
    elif mx == 3:
        score += 0.15
    if b.isupper() and len(b) >= 5:
        score += 0.15
    return min(score, 1.0)


def rebrand_confidence(shared_tokens: list[str], brands: list[str]) -> float:
    """Combina i segnali: token numerici condivisi (spec_families) + pseudo-brand.
    >= 0.7 = mostralo come 'stesso stampo, brand diversi' con fiducia alta."""
    base = min(len(shared_tokens) / 4.0, 0.7)  # 4+ token condivisi = tetto
    pseudo = max((pseudo_brand_score(b) for b in brands), default=0.0)
    return min(base + 0.3 * pseudo, 1.0)


if __name__ == "__main__":  # self-check, no deps needed
    titles = {
        "A": "BRANDX Subwoofer Auto Slim 20.3x7.6x33 cm 150W attivo",
        "B": "NoName Sub sottile per auto 20,3 x 7,6 x 33cm 150 W bass",
        "C": "JBL BassPro SL2 125W subwoofer compatto",
        "D": "Collare cervicale regolabile taglia unica",
    }
    fams = spec_families(titles)
    assert len(fams) == 1 and set(fams[0]["items"]) == {"A", "B"}, fams
    assert numeric_fingerprint("20,3 cm") == numeric_fingerprint("20.3cm")
    assert spec_families({"A": titles["A"]}) == []
    print("dedup spec_families self-check: PASS", fams)
