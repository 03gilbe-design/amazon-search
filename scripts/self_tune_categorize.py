# -*- coding: utf-8 -*-
"""Zero-LLM-token category classifier tuner.

Takes the user's hand-labeled dataset (~/.amazon_search_learned_categories.json
+ titles from the on-disk search cache) as ground truth, then tries several
deterministic methods against it with leave-one-out cross-validation, sweeping
parameters for each — no API calls, no LLM tokens, just local string/vector math.
Slow-by-design is fine here (the user said so): it grid-searches everything and
reports the best method+params found, plus per-category weak spots.

Run:  python scripts/self_tune_categorize.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from amazon_search.scoring import _tfidf_vectors, _cosine_sim, _unique_title_words, categorize


def load_ground_truth() -> list[dict]:
    gt_path = Path.home() / "amazon_search_reports" / "ground_truth_dataset.json"
    return json.loads(gt_path.read_text(encoding="utf-8"))


class _P:
    """Shim so scoring.categorize() (expects a Product) works on plain dicts."""
    def __init__(self, d):
        self.title, self.bullets, self.specs = d["title"], [], {}


def accuracy(preds: list[str | None], truth: list[str]) -> float:
    correct = sum(1 for p, t in zip(preds, truth) if p == t)
    return correct / len(truth)


def macro_f1(preds: list[str | None], truth: list[str]) -> float:
    cats = set(truth)
    scores = []
    for c in cats:
        tp = sum(1 for p, t in zip(preds, truth) if p == c and t == c)
        fp = sum(1 for p, t in zip(preds, truth) if p == c and t != c)
        fn = sum(1 for p, t in zip(preds, truth) if p != c and t == c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        scores.append(f1)
    return sum(scores) / len(scores)


# ---------- Method A: keyword categorize, keywords auto-derived from category names ----------
def method_keyword_baseline(rows: list[dict]) -> list[str | None]:
    cats = list(dict.fromkeys(r["category"] for r in rows))
    keywords = {c: [w for w in c.lower().replace("/", " ").split() if len(w) > 3] or [c.lower()]
                for c in cats}
    return [categorize(_P(r), keywords, default=None) for r in rows]


# ---------- Method B: TF-IDF nearest-centroid, LOO ----------
def method_tfidf_centroid(rows: list[dict], max_vocab: int) -> list[str | None]:
    texts = {i: r["title"] for i, r in enumerate(rows)}
    vecs, vocab = _tfidf_vectors(texts, max_vocab=max_vocab)
    truth = [r["category"] for r in rows]
    preds = []
    for i in range(len(rows)):
        # centroids over every OTHER row (leave current one out)
        by_cat: dict[str, list[list[float]]] = defaultdict(list)
        for j in range(len(rows)):
            if j != i:
                by_cat[truth[j]].append(vecs[j])
        centroids = {c: [sum(col) / len(vs) for col in zip(*vs)] for c, vs in by_cat.items()}
        best_c, best_s = None, -1.0
        for c, cen in centroids.items():
            s = _cosine_sim(vecs[i], cen)
            if s > best_s:
                best_c, best_s = c, s
        preds.append(best_c)
    return preds


# ---------- Method C: TF-IDF k-NN, LOO ----------
def method_tfidf_knn(rows: list[dict], max_vocab: int, k: int) -> list[str | None]:
    texts = {i: r["title"] for i, r in enumerate(rows)}
    vecs, vocab = _tfidf_vectors(texts, max_vocab=max_vocab)
    truth = [r["category"] for r in rows]
    preds = []
    for i in range(len(rows)):
        sims = sorted(((j, _cosine_sim(vecs[i], vecs[j])) for j in range(len(rows)) if j != i),
                      key=lambda t: -t[1])[:k]
        votes = Counter(truth[j] for j, _ in sims if _ > 0)
        preds.append(votes.most_common(1)[0][0] if votes else None)
    return preds


# ---------- Method D: raw word-overlap (Jaccard) k-NN, LOO ----------
def method_jaccard_knn(rows: list[dict], k: int) -> list[str | None]:
    words = [_unique_title_words(r["title"]) for r in rows]
    truth = [r["category"] for r in rows]
    preds = []
    for i in range(len(rows)):
        def jac(a, b):
            u = a | b
            return len(a & b) / len(u) if u else 0.0
        sims = sorted(((j, jac(words[i], words[j])) for j in range(len(rows)) if j != i),
                      key=lambda t: -t[1])[:k]
        votes = Counter(truth[j] for j, s in sims if s > 0)
        preds.append(votes.most_common(1)[0][0] if votes else None)
    return preds


def main():
    rows = load_ground_truth()
    truth = [r["category"] for r in rows]
    print(f"ground truth: {len(rows)} labeled products, {len(set(truth))} categories")
    print(f"class sizes: {dict(Counter(truth).most_common())}\n")

    results = []

    p = method_keyword_baseline(rows)
    results.append(("keyword baseline (auto keywords from category name)",
                    accuracy(p, truth), macro_f1(p, truth), p))

    # saturates around ~1200 for this dataset size (264 rows) — measured 50->3000,
    # gains flatten past 1200 (78-79% acc plateau), so that's the practical ceiling
    for mv in (50, 100, 200, 400, 600, 800, 1200, 2000):
        p = method_tfidf_centroid(rows, max_vocab=mv)
        results.append((f"tfidf nearest-centroid (max_vocab={mv})",
                        accuracy(p, truth), macro_f1(p, truth), p))

    for mv in (100, 300):
        for k in (1, 3, 5):
            p = method_tfidf_knn(rows, max_vocab=mv, k=k)
            results.append((f"tfidf k-NN (max_vocab={mv}, k={k})",
                            accuracy(p, truth), macro_f1(p, truth), p))

    for k in (1, 3, 5):
        p = method_jaccard_knn(rows, k=k)
        results.append((f"jaccard word-overlap k-NN (k={k})",
                        accuracy(p, truth), macro_f1(p, truth), p))

    results.sort(key=lambda r: -r[2])  # rank by macro-F1 (robust to class imbalance)

    print(f"{'method':50s} {'accuracy':>9s} {'macro-F1':>9s}")
    print("-" * 70)
    for name, acc, f1, _ in results:
        print(f"{name:50s} {acc*100:8.1f}% {f1*100:8.1f}%")

    best_name, best_acc, best_f1, best_preds = results[0]
    print(f"\nBEST: {best_name}  (accuracy {best_acc*100:.1f}%, macro-F1 {best_f1*100:.1f}%)")

    print("\nworst categories for the best method (recall):")
    cats = set(truth)
    recalls = []
    for c in cats:
        idx = [i for i, t in enumerate(truth) if t == c]
        correct = sum(1 for i in idx if best_preds[i] == c)
        recalls.append((c, correct / len(idx), len(idx)))
    for c, r, n in sorted(recalls, key=lambda t: t[1])[:6]:
        print(f"  {c:45s} recall {r*100:5.1f}%  (n={n})")

    out = Path.home() / "amazon_search_reports" / "self_tune_results.json"
    out.write_text(json.dumps(
        {"n": len(rows), "results": [{"method": n, "accuracy": a, "macro_f1": f}
                                     for n, a, f, _ in results]},
        indent=1), encoding="utf-8")
    print(f"\nfull results: {out}")
    print(f"ground truth dataset (for other AIs to try): "
          f"{Path.home() / 'amazon_search_reports' / 'ground_truth_dataset.json'}")


if __name__ == "__main__":
    main()
