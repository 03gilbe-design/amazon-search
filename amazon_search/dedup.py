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

    images: {item_id: local_image_path}. Returns a list of families, each
    `{"items": [item_id, ...], "diff_image": bool}` — diff_image is True
    when the family was found despite the source images not being byte-identical
    (resized/re-encoded/cropped copies of the same shot, not just literal dupes).
    Singletons (no match) are omitted.
    """
    import imagehash
    from PIL import Image

    hashes: dict[str, "imagehash.ImageHash"] = {}
    for item_id, path in images.items():
        try:
            hashes[item_id] = imagehash.phash(Image.open(path))
        except Exception:
            continue

    ids = list(hashes)
    seen: set[str] = set()
    families: list[dict] = []
    for i, a in enumerate(ids):
        if a in seen:
            continue
        group = [a]
        seen.add(a)
        for b in ids[i + 1:]:
            if b in seen:
                continue
            if hashes[a] - hashes[b] <= threshold:
                group.append(b)
                seen.add(b)
        if len(group) > 1:
            paths = {images[x] for x in group}
            families.append({"items": group, "diff_image": len(paths) > 1})
    return families


def price_spread(family_items: list[str], prices: dict[str, float]) -> float | None:
    """Max-min price within a family, ignoring items with no known price."""
    vals = [prices[i] for i in family_items if prices.get(i) is not None]
    if len(vals) < 2:
        return None
    return max(vals) - min(vals)
