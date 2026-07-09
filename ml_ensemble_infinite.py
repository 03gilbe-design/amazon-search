import time
import json
import random
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, Birch, DBSCAN
from sklearn.metrics import silhouette_score
import sys

# Per caricare il nuovo dataset
sys.path.append(r"C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements\webui")
from app import JOBS, _build_dataset_job, _load_learned

print("Inizializzazione Ensemble Infinito...")
_build_dataset_job()
# Usiamo l'ultimo job, che ora dovrebbe essere il nuovo dataset "collare cervicale morbido"
job = list(JOBS.values())[-1] 
products = job.get("result").products

if not products:
    print("Nessun prodotto trovato.")
    sys.exit()

titles = [p.title for p in products]
prices = [p.price or 0.0 for p in products]

print(f"Dataset caricato: {len(products)} prodotti.")

STATUS_FILE = Path("ensemble_infinite_status.json")

def normalize(arr):
    arr = np.array(arr)
    if arr.max() == arr.min(): return arr
    return (arr - arr.min()) / (arr.max() - arr.min())

norm_prices = normalize(prices).reshape(-1, 1)

best_score = -1.0
best_params = {}

iteration = 0

# Loop Infinito di Miglioramento (Ricerca Random-Adattiva)
while True:
    iteration += 1
    try:
        # 1. Mutazione Parametri (Genetica)
        max_feat = random.randint(50, 500)
        k_kmeans = random.randint(2, min(30, len(products)-1))
        birch_th = random.uniform(0.3, 0.95)
        eps_dbscan = random.uniform(0.1, 1.0)
        
        weight_text = random.uniform(0.1, 1.0)
        weight_price = random.uniform(0.0, 0.5)
        
        # 2. Vettorizzazione Mista (Testo + Prezzo)
        vec = TfidfVectorizer(max_features=max_feat)
        X_text = vec.fit_transform(titles).toarray()
        X_mixed = np.hstack([X_text * weight_text, norm_prices * weight_price])
        
        # 3. Ensemble (I 3 Modelli votano)
        km = KMeans(n_clusters=k_kmeans, random_state=42, n_init=1).fit_predict(X_mixed)
        br = Birch(threshold=birch_th, n_clusters=None).fit_predict(X_mixed)
        db = DBSCAN(eps=eps_dbscan, min_samples=2).fit_predict(X_mixed)
        
        # Co-occorrenza (Costruzione matrice di consenso)
        n = len(products)
        consensus = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if km[i] == km[j]: consensus[i, j] += 0.4
                if br[i] == br[j]: consensus[i, j] += 0.4
                if db[i] == db[j]: consensus[i, j] += 0.2
        
        # Trasformiamo il consenso in distanze (1 - consenso)
        distances = 1.0 - consensus
        # Usiamo Agglomerative per il verdetto finale
        from sklearn.cluster import AgglomerativeClustering
        final_labels = AgglomerativeClustering(
            n_clusters=None, distance_threshold=1.0, metric='precomputed', linkage='average'
        ).fit_predict(distances)
        
        # Valutazione non supervisionata (Silhouette Score: quanto sono compatti i gruppi)
        n_clusters = len(set(final_labels))
        if 2 <= n_clusters <= n - 1:
            score = silhouette_score(distances, final_labels, metric='precomputed')
        else:
            score = -1.0
            
        # Se è il migliore, salva
        if score > best_score:
            best_score = score
            best_params = {
                "max_features": max_feat,
                "k_kmeans": k_kmeans,
                "birch_th": round(birch_th, 4),
                "weight_text": round(weight_text, 4),
                "weight_price": round(weight_price, 4),
                "n_clusters_found": n_clusters
            }
            
        # Log su file ogni secondo per evitare I/O blocking
        if iteration % 5 == 0:
            STATUS_FILE.write_text(json.dumps({
                "status": "RUNNING_INFINITE",
                "iteration": iteration,
                "best_silhouette_score": round(best_score, 4),
                "best_ensemble_params": best_params
            }), encoding="utf-8")
            
    except Exception as e:
        pass
        
    time.sleep(0.01) # Evita surriscaldamento CPU 100%
