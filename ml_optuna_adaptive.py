import sys
import json
import time
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import optuna
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, Birch, DBSCAN, AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler

sys.path.append(r"C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements\webui")
from app import JOBS, _build_dataset_job, _load_learned

# --- Inizializzazione Globale ---
_build_dataset_job()
job = JOBS["dataset"]
products = job["result"].products

learned = _load_learned().get("_global", {})
valid_products = []
labels = []
for p in products:
    cat = learned.get(p.asin)
    if cat:
        valid_products.append(p)
        labels.append(cat)

titles = [p.title for p in valid_products]
prices = [p.price or 0.0 for p in valid_products]
price_scaler = MinMaxScaler()
norm_prices = price_scaler.fit_transform(np.array(prices).reshape(-1, 1))

scenes_path = Path.home() / ".amazon_search_offline_scenes.json"
sift_matches = []
if scenes_path.exists():
    sift_matches = json.loads(scenes_path.read_text(encoding="utf-8"))

TOTAL_TRIALS = 2000
START_TIME = time.time()
STATUS_FILE = Path("optuna_status.json")

def objective(trial):
    # 1. Variabili di Rappresentazione Dati
    max_features = trial.suggest_int("max_features", 10, 1000)
    use_price = trial.suggest_categorical("use_price", [True, False])
    price_weight = trial.suggest_float("price_weight", 0.1, 5.0) if use_price else 0.0
    
    # Text Vettorizzazione
    vec = TfidfVectorizer(max_features=max_features)
    X = vec.fit_transform(titles).toarray()
    
    if use_price:
        scaled_p = norm_prices * price_weight
        X = np.hstack([X, scaled_p])
        
    # 2. Scelta Algoritmo
    algo_name = trial.suggest_categorical("algo", ["kmeans", "birch", "dbscan"])
    
    try:
        if algo_name == "kmeans":
            k = trial.suggest_int("kmeans_k", 2, 50)
            algo = KMeans(n_clusters=k, random_state=42, n_init=1)
            preds = algo.fit_predict(X)
        elif algo_name == "birch":
            th = trial.suggest_float("birch_th", 0.1, 0.99)
            algo = Birch(threshold=th, n_clusters=None)
            preds = algo.fit_predict(X)
        elif algo_name == "dbscan":
            eps = trial.suggest_float("dbscan_eps", 0.1, 1.5)
            ms = trial.suggest_int("dbscan_ms", 2, 5)
            algo = DBSCAN(eps=eps, min_samples=ms)
            preds = algo.fit_predict(X)
            
        n_clusters = len(set(preds))
        if n_clusters <= 1 or n_clusters >= len(valid_products) - 1:
            return 0.0 # Puniamo aggregazioni estreme (tutti insieme o tutti separati)
            
        # 3. Ri-aggregazione SIFT
        use_sift = trial.suggest_categorical("use_sift", [True, False])
        if use_sift and sift_matches:
            sift_th = trial.suggest_int("sift_threshold", 10, 150)
            
            asin_to_pred = {p.asin: pred for p, pred in zip(valid_products, preds)}
            group_merges = {}
            for match in sift_matches:
                if match.get("inliers", 0) >= sift_th:
                    asin1 = match.get("prod_1", "")
                    asin2 = match.get("prod_2", "")
                    if asin1 in asin_to_pred and asin2 in asin_to_pred:
                        g1 = asin_to_pred[asin1]
                        g2 = asin_to_pred[asin2]
                        if g1 != g2:
                            group_merges[max(g1, g2)] = min(g1, g2)
                            
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
        
        # Aggiornamento File di Status Live ogni 10 trial
        current_trial = trial.number
        if current_trial % 10 == 0:
            elapsed = time.time() - START_TIME
            eta = (elapsed / max(1, current_trial)) * (TOTAL_TRIALS - current_trial)
            status_data = {
                "current_trial": current_trial,
                "total_trials": TOTAL_TRIALS,
                "best_ari": trial.study.best_value if len(trial.study.trials) > 0 else 0,
                "elapsed_sec": int(elapsed),
                "eta_sec": int(eta),
                "completion_pct": round((current_trial/TOTAL_TRIALS)*100, 1)
            }
            STATUS_FILE.write_text(json.dumps(status_data), encoding="utf-8")
            
        return ari
        
    except Exception as e:
        return 0.0 # In caso di errori matematici penalizziamo la pipeline

def main():
    print("Avvio Mente Adattiva (Optuna). Database: sqlite:///optuna_amazon.db")
    
    # Creazione study persistente per salvare lo storico
    study = optuna.create_study(
        study_name="amazon_adaptive_clustering_v1", 
        storage="sqlite:///optuna_amazon.db", 
        load_if_exists=True,
        direction="maximize"
    )
    
    # Quanti trial mancanti eseguire?
    trials_to_run = TOTAL_TRIALS
    print(f"Eseguo {trials_to_run} trial. Lo stato live sarà su optuna_status.json")
    
    study.optimize(objective, n_trials=trials_to_run, n_jobs=1) # 1 job per evitare memory leak
    
    print("\n\nOTTIMIZZAZIONE COMPLETATA!")
    best = study.best_trial
    print(f"Miglior ARI Trovato: {best.value:.4f}")
    print("Migliori Parametri:")
    for k, v in best.params.items():
        print(f"  {k}: {v}")
        
    # Generazione Report HTML Storico
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8"><title>Report Adattivo</title>
    <style>
        body {{ font-family: sans-serif; padding: 20px; }}
        h1 {{ color: #2c3e50; }}
        .param-box {{ background: #e8f4f8; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 1.1rem; }}
        .score {{ font-size: 2rem; color: #27ae60; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Report: Modello Adattivo Bayesiano</h1>
    <p>Il sistema ha imparato dagli errori ed è arrivato a una precisione massima di: <span class="score">{best.value:.4f}</span></p>
    <h2>La Formula Perfetta Trovata dall'AI:</h2>
    <div class="param-box">
"""
    for k, v in best.params.items():
        html += f"<b>{k}</b>: {v}<br>"
        
    html += """
    </div>
    <p>Tutto lo storico matematico dei fallimenti e dei successi è salvato per sempre nel database: <code>optuna_amazon.db</code>.</p>
</body>
</html>
"""
    Path("report_optuna.html").write_text(html, encoding="utf-8")
    
if __name__ == "__main__":
    main()
