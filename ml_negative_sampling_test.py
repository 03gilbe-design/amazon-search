import requests
from bs4 import BeautifulSoup
import json
import random
import cv2
import numpy as np
import urllib.request
import time
from pathlib import Path
from itertools import combinations

# Setup
home = Path.home()
dataset_file = home / ".amazon_search_offline.json"
OUTPUT_FILE = home / "negative_sampling_results.json"
NUM_POSITIVES = 10
NUM_NEGATIVES_PER_CAT = 10
NEGATIVE_QUERIES = ["cappello invernale", "sciarpa di lana", "cuscino da viaggio"]

def fetch_amazon_products(query, limit=10):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept-Language': 'it-IT,it;q=0.9',
    }
    url = f"https://www.amazon.it/s?k={urllib.parse.quote(query)}"
    print(f"Scraping Amazon per '{query}'...")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        results = []
        for item in items:
            asin = item.get('data-asin')
            img = item.find('img', class_='s-image')
            if not asin or not img: continue
            title = img.get('alt', '')
            src = img.get('src', '')
            if src:
                results.append({
                    "asin": asin,
                    "title": title,
                    "thumbnail": src,
                    "category": query,
                    "is_negative": True
                })
            if len(results) >= limit:
                break
        return results
    except Exception as e:
        print(f"Errore scraping {query}: {e}")
        return []

def download_image_cv2(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            # Ridimensiona per velocizzare SIFT
            if img is not None:
                img = cv2.resize(img, (300, 300))
            return img
    except Exception as e:
        return None

def compute_sift_match(img1, img2):
    if img1 is None or img2 is None: return 0
    sift = cv2.SIFT_create(nfeatures=500)
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    if des1 is None or des2 is None or len(des1) < 5 or len(des2) < 5:
        return 0
    
    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)
    
    good = []
    for m_n in matches:
        if len(m_n) == 2:
            m, n = m_n
            if m.distance < 0.75 * n.distance:
                good.append(m)
    return len(good)

def main():
    print("Avvio Negative Sampling Test...")
    # 1. Carica dataset positivo
    if not dataset_file.exists():
        print(f"File {dataset_file} non trovato.")
        return
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    all_positives = data.get("products", [])
    if len(all_positives) > NUM_POSITIVES:
        positives = random.sample(all_positives, NUM_POSITIVES)
    else:
        positives = all_positives
        
    for p in positives:
        p["category"] = "collare cervicale (POSITIVO)"
        p["is_negative"] = False
        
    print(f"Selezionati {len(positives)} campioni positivi.")
    
    # 2. Scarica campioni negativi
    negatives = []
    import urllib.parse
    for query in NEGATIVE_QUERIES:
        negatives.extend(fetch_amazon_products(query, NUM_NEGATIVES_PER_CAT))
        time.sleep(2)
        
    print(f"Scaricati {len(negatives)} campioni negativi.")
    
    dataset = positives + negatives
    print(f"Dataset totale: {len(dataset)} prodotti. Scarico immagini...")
    
    # 3. Scarica immagini e calcola SIFT
    images = {}
    for p in dataset:
        img = download_image_cv2(p["thumbnail"])
        if img is not None:
            images[p["asin"]] = img
            
    print(f"Immagini scaricate con successo: {len(images)}")
    
    # 4. Esegui match a coppie
    print("Calcolo similarità visiva (SIFT)...")
    results_matrix = []
    
    pairs = list(combinations(dataset, 2))
    matched_pairs = 0
    
    for p1, p2 in pairs:
        asin1, asin2 = p1["asin"], p2["asin"]
        if asin1 not in images or asin2 not in images: continue
        
        score = compute_sift_match(images[asin1], images[asin2])
        if score >= 8: # Soglia empirica per un buon match
            matched_pairs += 1
            results_matrix.append({
                "p1_asin": asin1,
                "p1_cat": p1["category"],
                "p2_asin": asin2,
                "p2_cat": p2["category"],
                "score": score,
                "is_false_positive": p1["is_negative"] != p2["is_negative"]
            })
            
    print(f"\n--- RISULTATI TEST ---")
    print(f"Coppie totali analizzate: {len(pairs)}")
    print(f"Match validi trovati (score >= 8): {matched_pairs}")
    
    false_positives = [m for m in results_matrix if m["is_false_positive"]]
    true_positives = [m for m in results_matrix if not m["is_false_positive"]]
    
    print(f"Match CORRETTI (Stessa classe): {len(true_positives)}")
    print(f"Match ERRATI (Falsi Positivi / Classi Diverse): {len(false_positives)}")
    
    if len(false_positives) == 0:
        print("\nSUCCESSO! L'algoritmo visivo ha diviso perfettamente i prodotti, senza confondere le categorie negative!")
    else:
        print("\nATTENZIONE: Trovati falsi positivi tra categorie diverse.")
        for fp in false_positives[:5]:
            print(f"  - FP: {fp['p1_cat']} <-> {fp['p2_cat']} (Score: {fp['score']})")

    # Salva report
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_samples": len(dataset),
            "true_positives_count": len(true_positives),
            "false_positives_count": len(false_positives),
            "false_positives_examples": false_positives
        }, f, indent=2)

if __name__ == "__main__":
    main()
