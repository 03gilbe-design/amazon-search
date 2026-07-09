import sys
import json
import warnings
from pathlib import Path
from collections import defaultdict
import numpy as np

# Silenziamo warning verbosi di scikit-learn
warnings.filterwarnings("ignore")

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.cluster import Birch, MiniBatchKMeans, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

sys.path.append(r"C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements\webui")
from app import JOBS, _build_dataset_job, _load_learned

def build_data():
    _build_dataset_job()
    job = JOBS["dataset"]
    products = job["result"].products
    learned = _load_learned().get("_global", {})
    
    data = []
    for p in products:
        cat = learned.get(p.asin)
        if cat:
            data.append({"title": p.title, "cat": cat})
    return data

def extended_active_learning_sweep(data):
    titles = [d["title"] for d in data]
    labels = [d["cat"] for d in data]
    valid_cats = ["Soft collar", "100% rigidi", "rigidi+ morbidi"]
    y_valid = np.array([1 if l in valid_cats else 0 for l in labels])
    
    vectorizers = {
        "TFIDF-50": TfidfVectorizer(max_features=50),
        "TFIDF-300": TfidfVectorizer(max_features=300),
        "TFIDF-All": TfidfVectorizer()
    }
    
    models = {
        "SVM-Linear": SVC(kernel='linear', class_weight='balanced'),
        "SVM-RBF": SVC(kernel='rbf', class_weight='balanced'),
        "RandomForest": RandomForestClassifier(class_weight='balanced', random_state=42)
    }
    
    results = []
    for vec_name, vec in vectorizers.items():
        X = vec.fit_transform(titles)
        for mod_name, clf in models.items():
            # Simuliamo click 4, 8, 12, 16
            for n_clicks in [4, 8, 12, 16, 20]:
                scores = []
                for _ in range(10): # 10 retry per stabilita
                    try:
                        from sklearn.model_selection import train_test_split
                        from sklearn.metrics import f1_score
                        X_train, X_test, y_train, y_test = train_test_split(X, y_valid, train_size=n_clicks, stratify=y_valid)
                        clf.fit(X_train, y_train)
                        preds = clf.predict(X_test)
                        scores.append(f1_score(y_test, preds, zero_division=0))
                    except ValueError:
                        pass
                
                avg_f1 = np.mean(scores) if scores else 0
                results.append({
                    "vectorizer": vec_name,
                    "model": mod_name,
                    "clicks": n_clicks,
                    "f1": avg_f1
                })
    return results, titles, labels

def extended_clustering_sweep(titles, labels):
    vec = TfidfVectorizer(max_features=300)
    X = vec.fit_transform(titles)
    
    results = []
    # KMeans Sweep
    for k in [2, 5, 10, 20, 30, 50]:
        km = KMeans(n_clusters=k, random_state=42, n_init=5)
        preds = km.fit_predict(X)
        ari = adjusted_rand_score(labels, preds)
        # sil = silhouette_score(X, preds)
        unique, counts = np.unique(preds, return_counts=True)
        results.append({
            "algo": "KMeans", "param": f"K={k}", "clusters": int(k),
            "ari": float(ari), "max_group": int(np.max(counts)), "singletons": int(np.sum(counts==1))
        })
        
    # Birch Sweep
    for thresh in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        brc = Birch(threshold=thresh, n_clusters=None)
        preds = brc.fit_predict(X)
        n_clusters = len(set(preds))
        ari = adjusted_rand_score(labels, preds)
        if n_clusters > 1:
            # sil = silhouette_score(X, preds)
            unique, counts = np.unique(preds, return_counts=True)
            results.append({
                "algo": "Birch", "param": f"Thresh={thresh}", "clusters": int(n_clusters),
                "ari": float(ari), "max_group": int(np.max(counts)), "singletons": int(np.sum(counts==1))
            })
        else:
            results.append({
                "algo": "Birch", "param": f"Thresh={thresh}", "clusters": 1,
                "ari": 0.0, "max_group": int(len(preds)), "singletons": 0
            })
            
    return results

def run_all():
    print("Inizio estrazione dataset...")
    data = build_data()
    print("Dataset pronto. Avvio Sweep Active Learning...")
    al_res, titles, labels = extended_active_learning_sweep(data)
    print("Active Learning completato. Avvio Sweep Clustering...")
    cl_res = extended_clustering_sweep(titles, labels)
    print("Clustering completato. Salvataggio in JSON...")
    
    output = {
        "active_learning": al_res,
        "clustering": cl_res
    }
    with open("ml_sweep_results.json", "w") as f:
        json.dump(output, f, indent=2)
        
    print("Tutto completato! ml_sweep_results.json generato.")

if __name__ == "__main__":
    run_all()
