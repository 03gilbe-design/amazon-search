import json
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, adjusted_rand_score
from sklearn.cluster import Birch
import random

dataset_file = Path.home() / ".amazon_search_offline.json"

def evaluate_active_learning(X, y):
    print("--- 1. Analisi Active Learning (Simulazione User Feedback) ---")
    results = []
    vectorizer = TfidfVectorizer(max_features=1000)
    X_vec = vectorizer.fit_transform(X)
    
    # Simula N click dell'utente (N campioni annotati)
    feedback_sizes = [5, 10, 20, 40, 60, 80]
    
    for n in feedback_sizes:
        if n >= len(X): break
        f1_scores = []
        # Ripeti 10 volte per mediare
        for _ in range(10):
            indices = list(range(len(X)))
            random.shuffle(indices)
            train_idx = indices[:n]
            test_idx = indices[n:]
            
            X_train = X_vec[train_idx]
            y_train = [y[i] for i in train_idx]
            X_test = X_vec[test_idx]
            y_test = [y[i] for i in test_idx]
            
            # Assicuriamoci che ci sia almeno più di una classe, sennò RF crasha
            if len(set(y_train)) < 2:
                continue
                
            clf = RandomForestClassifier(n_estimators=50, random_state=None)
            clf.fit(X_train, y_train)
            preds = clf.predict(X_test)
            
            f1 = f1_score(y_test, preds, average='weighted', zero_division=0)
            f1_scores.append(f1)
            
        avg_f1 = np.mean(f1_scores) if f1_scores else 0
        print(f"Feedback = {n:2d} click  --> F1-Score: {avg_f1:.3f}")
        results.append((n, avg_f1))
    return results

def evaluate_clustering(X, y_true):
    print("\n--- 2. Analisi Clustering Sweep (Alla ricerca della Soglia Perfetta) ---")
    vectorizer = TfidfVectorizer(max_features=1000)
    X_vec = vectorizer.fit_transform(X).toarray()
    
    thresholds = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    results = []
    
    best_ari = -1
    best_t = None
    
    for t in thresholds:
        # Usiamo Birch come nell'interfaccia
        # branching_factor piccolo per dati sparsi
        birch = Birch(threshold=t, branching_factor=50, n_clusters=None)
        birch.fit(X_vec)
        labels = birch.labels_
        
        n_clusters = len(set(labels))
        # Calcoliamo la distanza dai cluster manuali dell'utente
        ari = adjusted_rand_score(y_true, labels)
        
        print(f"Soglia (Threshold) = {t:.1f} --> Gruppi creati: {n_clusters:3d} | Adjusted Rand Index (ARI): {ari:.3f}")
        results.append((t, n_clusters, ari))
        
        if ari > best_ari:
            best_ari = ari
            best_t = t
            
    print(f"\n=> SOGLIA IDEALE TROVATA: {best_t} (ARI Massimo = {best_ari:.3f})")
    return results, best_t

def main():
    if not dataset_file.exists():
        print("Errore: Dataset non trovato.")
        return
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    products = data.get("products", [])
    
    # Filtriamo i prodotti che hanno una categoria manuale
    valid_products = [p for p in products if p.get("category")]
    if not valid_products:
        print("Errore: Nessun prodotto con categoria manuale per fare test.")
        return
        
    print(f"Prodotti con Ground Truth manuale: {len(valid_products)}")
    
    X = [p.get("title", "") for p in valid_products]
    y = [p.get("category", "") for p in valid_products]
    
    # Raggruppiamo le minoranze per evitare troppo rumore nell'ARI
    from collections import Counter
    counts = Counter(y)
    y_clean = [label if counts[label] >= 5 else "Altro" for label in y]
    
    al_results = evaluate_active_learning(X, y_clean)
    cl_results, best_threshold = evaluate_clustering(X, y_clean)
    
    # Salvo Report Finale in Markdown
    report_file = Path.home() / "amazon_search" / "RISULTATI_DEEP.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Risultati Finali: Test Deep Learning\n\n")
        f.write("## 1. Active Learning (Simulazione Utente)\n")
        f.write("Quanti click servono affinché l'algoritmo impari a separare correttamente i prodotti?\n\n")
        f.write("| Click (Esempi) | F1-Score |\n|---|---|\n")
        for n, f1 in al_results:
            f.write(f"| {n} | {f1:.3f} |\n")
            
        f.write("\n## 2. Ottimizzazione Clustering (Birch)\n")
        f.write("Abbiamo testato la distanza algoritmica (Adjusted Rand Index) tra i gruppi automatici e i tuoi gruppi manuali.\n\n")
        f.write("| Soglia (Slider) | Num Cluster | ARI (Score) |\n|---|---|---|\n")
        for t, n_clus, ari in cl_results:
            f.write(f"| {t:.1f} | {n_clus} | {ari:.3f} |\n")
            
        f.write(f"\n**La soglia ideale da impostare nell'interfaccia UI è: {best_threshold}**.\n")
        f.write("Questa soglia massimizza l'aderenza ai tuoi raggruppamenti mentali, evitando sia i mega-gruppi unici che la frammentazione eccessiva.\n")
        
    print(f"\nOperazioni notturne completate. Report salvato in {report_file}")

if __name__ == "__main__":
    main()
