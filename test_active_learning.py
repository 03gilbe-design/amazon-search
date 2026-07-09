import json
import requests
import urllib.parse
from bs4 import BeautifulSoup
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import random
import time

dataset_file = Path.home() / ".amazon_search_offline.json"

# Mappa delle query online per le categorie manuali
CATEGORY_QUERIES = {
    "Soft collar": "collare cervicale morbido",
    "cuscini U viaggio": "cuscino da viaggio memory foam",
    "100% rigidi": "collare cervicale ortopedico rigido",
    "cuscini gonfiabili": "cuscino collo gonfiabile aereo"
}

def fetch_amazon_products_text(query, limit=20):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'it-IT,it;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    url = f"https://www.amazon.it/s?k={urllib.parse.quote(query)}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        results = []
        for item in items:
            img = item.find('img', class_='s-image')
            if not img: continue
            title = img.get('alt', '')
            if title:
                results.append(title)
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"Errore scraping '{query}': {e}")
        return []

def main():
    print("Avvio Test Machine Learning (Zero-Shot via Web Scraping)...")
    if not dataset_file.exists():
        print("Dataset non trovato.")
        return
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    products = data.get("products", [])
    
    # Costruisco Ground Truth (Test Set)
    test_X = []
    test_y = []
    for p in products:
        cat = p.get("category", "")
        if cat in CATEGORY_QUERIES:
            test_X.append(p.get("title", ""))
            test_y.append(cat)
            
    print(f"\n--- Ground Truth (Prodotti Manuali) ---")
    print(f"Totale prodotti per le {len(CATEGORY_QUERIES)} classi principali: {len(test_X)}")
    
    # Costruisco Training Set (Scraping Online)
    train_X = []
    train_y = []
    print(f"\n--- Raccolta dati da Amazon (Training Set) ---")
    for cat, query in CATEGORY_QUERIES.items():
        print(f"Cerco online: '{query}' per la classe '{cat}'...")
        titles = fetch_amazon_products_text(query, limit=30)
        time.sleep(2) # delay anti-ban
        for t in titles:
            train_X.append(t)
            train_y.append(cat)
        print(f" -> Trovati {len(titles)} titoli.")
        
    if len(train_X) == 0:
        print("Nessun dato raccolto online. Probabile blocco da parte di Amazon.")
        return
        
    print("\n--- Addestramento Modello (Random Forest su TF-IDF) ---")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
    X_train_vec = vectorizer.fit_transform(train_X)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train_vec, train_y)
    print("Addestramento completato con successo.")
    
    print("\n--- Valutazione Modello sui Prodotti Manuali ---")
    X_test_vec = vectorizer.transform(test_X)
    preds = clf.predict(X_test_vec)
    
    report = classification_report(test_y, preds, zero_division=0)
    print(report)
    
    print("\n--- Esempi di Errore ---")
    errors = 0
    for i in range(len(test_y)):
        if preds[i] != test_y[i]:
            if errors < 10:
                print(f"VERO: {test_y[i]:<18} | PREDETTO: {preds[i]:<18} | {test_X[i][:60]}...")
            errors += 1
    print(f"Totale errori: {errors} su {len(test_y)}")

if __name__ == "__main__":
    main()
