# -*- coding: utf-8 -*-
"""The one search pipeline. Both the CLI (main.py) and library callers (report.py, night_runner)
go through here — nothing else independently re-implements search+enrich.

Execution order matters and is deliberate, not arbitrary:
  1. organic search
  2. negative-sampling exclusion (BEFORE spending quota on items we already know are junk)
  3. manual ASIN pulls merged in — these bypass step 2 on purpose: a candidate a human chose
     deliberately shouldn't be auto-excluded by a keyword false positive
  4. specs (Canopy) — only on survivors + pulls
  5. dedup (pHash) — needs images, downloaded after specs so we don't fetch images for
     items that just got excluded
  6. video claims (opt-in, slow/costly — never run unless explicitly requested)
  7. feature-fit scoring (benefits from specs bullets if step 4 ran; works on title alone
     otherwise, with a flag so the report can say so)
  8. AI budget-rank — a SEPARATE ordering signal from feature-fit, never blended into one score
"""
from __future__ import annotations
from dataclasses import dataclass, field

from amazon_search.searcher import AmazonProduct, AmazonSearcher


@dataclass
class SearchResult:
    query: str
    filters: dict
    products: list  # list[AmazonProduct], survivors + pulls, in final (possibly AI-ranked) order
    families: list[dict] = field(default_factory=list)          # dedup.phash_families() output
    video_claims: list[dict] = field(default_factory=list)      # video_review claims, [] if not run
    video_coverage: dict = field(default_factory=dict)          # video_review.coverage() output
    excluded: list[dict] = field(default_factory=list)          # negative-sampling audit trail
    external_benchmarks: list[dict] = field(default_factory=list)
    feature_fit_ready: bool = False   # True only if criteria AND specs both ran (stronger match)
    quota_info: str = ""
    ai_summary: str = ""
    query_variants: list[str] = field(default_factory=list)  # deterministic + AI, free to generate


def run(query: str, *,
        max_price: float | None = None,
        min_stars: float | None = None,
        n: int = 15,
        domain: str = "IT",
        specs: bool = False,
        dedup: bool = False,
        videos: bool = False,
        video_out_dir: str = "",
        rank: bool = True,
        budget: float | None = None,
        criteria: dict[str, list[str]] | None = None,
        junk_patterns: dict[str, list[str]] | None = None,
        pull_asins: list[str] | None = None,
        external_benchmarks: list[dict] | None = None,
        suggest_queries: bool = False,
        deep_image_match: bool = False,
        price_bands: list[tuple[float, float]] | None = None,
        categories: dict[str, list[str]] | None = None) -> SearchResult:
    """Run the full pipeline once, returning everything computed — the report renders
    from this single object, nothing is a side file."""
    from amazon_search import scoring

    searcher = AmazonSearcher()
    if price_bands:
        # una ricerca (1+ crediti) PER FASCIA: i primi organici Amazon sono quasi
        # tutti cheap, così ogni fascia di prezzo porta i suoi candidati veri
        products, seen = [], set()
        for lo, hi in price_bands:
            for p in searcher.search(query, max_results=n, max_price=max_price,
                                      min_stars=min_stars, domain=domain,
                                      price_range=(lo, hi)):
                if p.asin and p.asin in seen:
                    continue
                seen.add(p.asin)
                products.append(p)
    else:
        products = searcher.search(query, max_results=n, max_price=max_price,
                                    min_stars=min_stars, domain=domain)

    # 2. negative sampling — before any paid enrichment
    excluded: list[dict] = []
    if junk_patterns:
        survivors = []
        for p in products:
            reason = scoring.exclusion_reason(p, junk_patterns)
            if reason:
                excluded.append({"asin": p.asin, "title": p.title, "reason": reason})
            else:
                survivors.append(p)
        products = survivors

    # 3. manual pulls — bypass exclusion by design, tagged source
    for p in products:
        if not hasattr(p, "source_kind"):
            p.source_kind = "organic"
    if pull_asins:
        from amazon_search.specs import fetch_specs as _fs
        pulled_specs = _fs(pull_asins, domain=domain) if specs else {}
        known = {p.asin for p in products}
        for asin in pull_asins:
            if asin in known:
                continue
            d = pulled_specs.get(asin, {})
            products.append(AmazonProduct(
                title=d.get("title", asin), asin=asin, brand=None, price=None,
                price_str="?", stars=None, reviews=None, thumbnail=None,
                link=f"https://www.amazon.{domain.lower()}/dp/{asin}", prime=False,
                in_stock=d.get("in_stock", True), source="manual",
                bullets=d.get("bullets", []), specs=d.get("specs", {}),
            ))
            products[-1].source_kind = "manual_pull"

    # 4. specs
    feature_fit_ready = False
    if specs:
        top_asins = [p.asin for p in products[:6] if p.asin]
        if top_asins:
            from amazon_search.specs import fetch_specs
            specs_data = fetch_specs(top_asins, domain=domain)
            for p in products:
                if p.asin in specs_data:
                    d = specs_data[p.asin]
                    p.bullets = d.get("bullets", [])
                    p.specs = d.get("specs", {})
                    p.in_stock = d.get("in_stock", p.in_stock)
        feature_fit_ready = True

    # 5. dedup
    families: list[dict] = []
    if dedup and len(products) > 1:
        from amazon_search import imagecache
        from amazon_search import dedup as dedup_mod

        paths = {}
        for p in products:
            if p.asin:
                fp = imagecache.local_path(p.asin, domain=domain.lower())
                if fp:
                    paths[p.asin] = fp
        price_by_asin = {p.asin: p.price for p in products}
        title_by_asin = {p.asin: p.title for p in products}
        thumb_by_asin = {p.asin: p.thumbnail for p in products}
        raw_families = []
        if len(paths) > 1:
            raw_families = dedup_mod.phash_families(paths, threshold=8)
        # second tier: same-mold rebrands that shot a DIFFERENT photo — invisible to
        # pHash, caught by identical measurements in the title (numeric fingerprint).
        # Only over items not already grouped by photo; lower confidence -> match="specs".
        in_photo_fam = {a for fam in raw_families for a in fam["items"]}
        # titolo + bullet (se --specs li ha portati): più numeri-con-unità nel testo
        # = fingerprint più discriminante, i rebrand copiano le misure anche lì
        spec_titles = {p.asin: " ".join([p.title] + (p.bullets or []))
                       for p in products if p.asin and p.asin not in in_photo_fam}
        brand_by_asin = {p.asin: p.brand for p in products}
        for fam in dedup_mod.spec_families(spec_titles):
            fam["match"] = "specs"
            # segnali che collaborano: misure condivise + brand pseudo-generato
            # (nome da registro marchi tipo "XKJIYU") = fiducia rebrand più alta
            fam["confidence"] = dedup_mod.rebrand_confidence(
                fam.get("shared", []),
                [brand_by_asin.get(a) or "" for a in fam["items"]])
            raw_families.append(fam)
        # third tier (opt-in, lento ~1s/coppia): stesso prodotto RIFOTOGRAFATO in una
        # scena (3 copie, persona, sfondo) — invisibile a pHash e spesso ai numeri.
        # Solo su item non già raggruppati, dentro la stessa categoria (meno coppie).
        if deep_image_match:
            grouped = {a for fam in raw_families for a in fam["items"]}
            cat_of = {p.asin: getattr(p, "category", None) for p in products}
            from collections import defaultdict
            by_cat: dict = defaultdict(dict)
            for asin, path in paths.items():
                if asin not in grouped:
                    by_cat[cat_of.get(asin)][asin] = path
            for cat_imgs in by_cat.values():
                if len(cat_imgs) > 1:
                    raw_families.extend(dedup_mod.scene_families(cat_imgs))

        for fam_ix, fam in enumerate(raw_families):
            by_specs = fam.get("match") == "specs"
            spread = dedup_mod.price_spread(fam["items"], price_by_asin)
            cheapest = min(fam["items"], key=lambda a: price_by_asin.get(a) or 9e9)
            if spread is not None and spread > 2:
                note = (f"Possibile stesso stampo (misure identiche), visto per €{spread:.2f} meno"
                        if by_specs else f"Same item also seen for €{spread:.2f} less")
                for p in products:
                    if p.asin in fam["items"] and p.asin != cheapest:
                        p.dedup_note = note
            for p in products:
                if p.asin in fam["items"]:
                    p.family_id = fam_ix  # so the report can cluster same-family cards together
            families.append({
                "spread": spread,
                "diff_image": fam.get("diff_image", False),
                "match": fam.get("match", "photo"),
                "confidence": fam.get("confidence"),
                "shared_specs": fam.get("shared", []),
                "items": [{"asin": a, "price": price_by_asin.get(a),
                           "title": title_by_asin.get(a) or "",
                           "thumbnail": thumb_by_asin.get(a) or ""}
                          for a in fam["items"]],
            })

    # 6. video claims — opt-in, slow, never automatic
    video_claims: list[dict] = []
    video_coverage: dict = {}
    if videos and video_out_dir:
        from amazon_search import video_review as vr
        video_claims = vr.load_claims(video_out_dir)
        video_coverage = vr.coverage(video_claims)

    # 7. feature-fit scoring
    if criteria:
        for p in products:
            score, hits = scoring.feature_fit_score(p, criteria)
            p.feature_fit_score = score
            p.feature_fit_hits = hits

    # sub-category bucketing (deterministic half of "sub-categories by eye")
    if categories:
        # visual_cluster (color + TF-IDF title similarity) runs on the WHOLE product
        # set FIRST, not just on categorize()'s leftovers — measured on real hand-labeled
        # data (59 products, 24 real categories): running it on everything together
        # matches the same 83% purity as running it on leftovers alone, but finds more
        # clean clusters (7/12 vs 6/11) because it has more context to match against, and
        # correctly isolates unrelated items (e.g. a stray dog-collar result) into their
        # own group instead of leaving keyword categorize()'s coarse buckets to absorb
        # them. Keyword categorize() becomes the FALLBACK label, only for items
        # visual_cluster didn't group with anyone.
        from amazon_search import imagecache
        images = {p.asin: imagecache.local_path(p.asin, domain=domain.lower())
                  for p in products if p.asin}
        images = {a: fp for a, fp in images.items() if fp}
        assignment = scoring.visual_cluster(products, images)
        # second pass: split any large cluster further if real sub-groups exist inside
        # it (verified live: correctly separates mixed-brand clusters by brand, leaves
        # genuinely single-product clusters — e.g. same item in different sizes — alone)
        assignment = scoring.refine_large_clusters(products, assignment, images)
        # third pass: fine sub-groups that actually belong to the same broader family
        # merge back together (verified live: 5 separate "pressure relief" sub-groups
        # correctly reunited into one umbrella label, purity unchanged at 83%)
        assignment = scoring.merge_similar_clusters(products, assignment, images)
        for p in products:
            p.category = assignment.get(p.asin) or scoring.categorize(p, categories)

    # 8. AI budget-rank (separate signal, own field, never overwrites feature-fit)
    ai_summary = ""
    if rank and len(products) > 1:
        from amazon_search.llm import ai_rank, compare_products
        products = ai_rank(products, query, budget=budget or max_price)
        ai_summary = compare_products(products, query)

    # query variants — deterministic is free, always try it; AI only on request (costs a call)
    query_variants: list[str] = []
    if suggest_queries and products:
        from amazon_search import query_suggest as qs
        query_variants = qs.deterministic_variants(query, products)
        if rank:  # only bother with the paid call if AI is enabled at all this run
            query_variants += qs.ai_variants(query, products)

    from amazon_search import quota as q
    quota_info = f"serpapi {q.remaining('serpapi')} | canopy {q.remaining('canopy')} | searchapi {q.remaining('searchapi')}"

    return SearchResult(
        query=query,
        filters={"max_price": max_price, "min_stars": min_stars, "domain": domain, "n": n},
        products=products,
        families=families,
        video_claims=video_claims,
        video_coverage=video_coverage,
        excluded=excluded,
        external_benchmarks=external_benchmarks or [],
        feature_fit_ready=feature_fit_ready,
        quota_info=quota_info,
        ai_summary=ai_summary,
        query_variants=query_variants,
    )
