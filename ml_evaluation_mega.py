import sys
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, Birch, DBSCAN, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score
from collections import defaultdict

sys.path.append(rstr(Path.home() / "amazon_search", ".claude", "worktrees", "amazon-improvements", "webui"))
from app import JOBS, _build_dataset_job, _load_learned

def run_mega_grid():
    print("Inizializzazione ambiente e caricamento dati (Dataset + Ground Truth + SIFT Offline)...")
    _build_dataset_job()
    job = JOBS["dataset"]
    products = job["result"].products
    
    learned = _load_learned().get("_global", {})
    labels = []
    valid_products = []
    
    for p in products:
        cat = learned.get(p.asin)
        if cat:
            valid_products.append(p)
            labels.append(cat)
            
    print(f"Trovati {len(valid_products)} prodotti etichettati manualmente.")
    titles = [p.title for p in valid_products]
    
    scenes_path = Path.home() / ".amazon_search_offline_scenes.json"
    sift_matches = {}
    if scenes_path.exists():
        sift_matches = json.loads(scenes_path.read_text(encoding="utf-8"))
        print(f"Caricati {len(sift_matches)} incroci SIFT per la ri-aggregazione geometrica.")
    else:
        print("Nessun match SIFT trovato. Il ricalcolo geometrico sarà inattivo.")
        
    results = []
    
    # 1. Variabili TF-IDF
    vec_options = [
        ("TFIDF-Top50", TfidfVectorizer(max_features=50)),
        ("TFIDF-Top100", TfidfVectorizer(max_features=100)),
        ("TFIDF-Top300", TfidfVectorizer(max_features=300)),
        ("TFIDF-Illimitato", TfidfVectorizer())
    ]
    
    # 2. Variabili Algoritmi
    algo_options = []
    for k in [2, 5, 10, 15, 20, 30]:
        algo_options.append((f"KMeans (K={k})", KMeans(n_clusters=k, random_state=42, n_init=1)))
    for th in [0.3, 0.4, 0.6, 0.8, 0.9]:
        algo_options.append((f"Birch (Soglia {th})", Birch(threshold=th, n_clusters=None)))
    for eps in [0.3, 0.5, 0.7, 0.9]:
        algo_options.append((f"DBSCAN (Eps {eps})", DBSCAN(eps=eps, min_samples=2)))
    for lnk in ["ward", "average", "complete"]:
        algo_options.append((f"Agglomerative ({lnk})", AgglomerativeClustering(n_clusters=10, linkage=lnk)))
        
    # 3. Variabili Ri-aggregazione
    sift_thresholds = [0, 20, 40, 60, 80] # 0 = inattivo
    
    total_tests = len(vec_options) * len(algo_options) * len(sift_thresholds)
    print(f"\n--- AVVIO BATCH: {total_tests} test totali stimati ---")
    
    start_global = time.time()
    
    for vec_name, vec in vec_options:
        X_text = vec.fit_transform(titles).toarray()
        
        for algo_name, algo in algo_options:
            for sift_th in sift_thresholds:
                test_start = time.time()
                
                try:
                    preds = algo.fit_predict(X_text)
                except Exception:
                    continue # DBSCAN sometimes fails if params are entirely incompatible
                
                # SIFT Re-aggregation logic
                if sift_th > 0 and sift_matches:
                    asin_to_pred = {p.asin: pred for p, pred in zip(valid_products, preds)}
                    group_merges = {}
                    
                    for match in sift_matches:
                        if match["inliers"] >= sift_th:
                            asin1 = match["prod_1"]
                            asin2 = match["prod_2"]
                            if asin1 in asin_to_pred and asin2 in asin_to_pred:
                                g1 = asin_to_pred[asin1]
                                g2 = asin_to_pred[asin2]
                                if g1 != g2:
                                    # Fonde il gruppo id maggiore nel minore
                                    group_merges[max(g1, g2)] = min(g1, g2)
                                    
                    # Resolve cascaded merges (e.g. 3->2, 2->1)
                    new_preds = []
                    for pr in preds:
                        cur = pr
                        iters = 0
                        while cur in group_merges and iters < 100:
                            cur = group_merges[cur]
                            iters += 1
                        new_preds.append(cur)
                    preds = new_preds
                
                ari = adjusted_rand_score(labels, preds)
                duration = time.time() - test_start
                
                unique, counts = np.unique(preds, return_counts=True)
                n_clust = len(unique)
                
                results.append({
                    "vec": vec_name,
                    "algo": algo_name,
                    "reagg": f"Colla SIFT > {sift_th} pt." if sift_th > 0 else "Nessuna",
                    "ari": float(ari),
                    "clusters": int(n_clust),
                    "max_group": int(np.max(counts)) if n_clust > 0 else 0,
                    "time_ms": int(duration * 1000)
                })
                
    total_time = time.time() - start_global
    print(f"Elaborazione completata in {total_time:.2f} secondi.")
    
    # Sort
    results.sort(key=lambda x: x["ari"], reverse=True)
    
    # HTML Report Generation
    html = f'''<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Mega Grid Search</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #1e293b; padding: 40px; margin: 0; }}
        h1 {{ color: #0f172a; margin-bottom: 10px; }}
        .summary {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 30px; border-left: 5px solid #3b82f6; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        th, td {{ text-align: left; padding: 15px 20px; border-bottom: 1px solid #e2e8f0; }}
        th {{ background-color: #f1f5f9; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover {{ background-color: #f8fafc; }}
        .top-rank {{ background-color: #ecfdf5; border-left: 4px solid #10b981; }}
        .badge {{ background: #e0e7ff; color: #4f46e5; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }}
        .ari-score {{ font-weight: 800; color: #059669; }}
    </style>
</head>
<body>
    <h1>🧪 Mega Grid Search (100+ Test)</h1>
    <div class="summary">
        <p><strong>Totale Combinazioni Generate ed Eseguite:</strong> {total_tests}</p>
        <p><strong>Tempo di Esecuzione Totale:</strong> {total_time:.2f} secondi (Circa {(total_time/total_tests)*1000:.1f} ms per iterazione)</p>
        <p>I test includono l'incrocio di: 4 vocabolari testuali X 18 algoritmi di base X 5 strategie di Colla Visiva post-clustering.</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Rank</th>
                <th>Base Dati (Testo)</th>
                <th>Algoritmo Macro</th>
                <th>Colla Visiva (Post-Aggregazione)</th>
                <th>Qualità (ARI Score)</th>
                <th>Gruppi Generati</th>
                <th>Tempo</th>
            </tr>
        </thead>
        <tbody>
'''
    for i, r in enumerate(results):
        row_class = "top-rank" if i < 15 else ""
        html += f'''
            <tr class="{row_class}">
                <td>#{i+1}</td>
                <td><span class="badge">{r["vec"]}</span></td>
                <td><strong>{r["algo"]}</strong></td>
                <td>{r["reagg"]}</td>
                <td class="ari-score">{(r["ari"] * 100):.1f}%</td>
                <td>{r["clusters"]}</td>
                <td style="color:#64748b; font-size:0.9rem;">{r["time_ms"]} ms</td>
            </tr>
'''
    html += '''
        </tbody>
    </table>
</body>
</html>
'''
    out_path = Path(rstr(Path.home() / "amazon_search", "report_mega_grid.html"))
    out_path.write_text(html, encoding="utf-8")
    print(f"Report salvato in: {out_path.resolve()}")

if __name__ == "__main__":
    run_mega_grid()
