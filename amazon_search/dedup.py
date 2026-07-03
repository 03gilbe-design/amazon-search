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
