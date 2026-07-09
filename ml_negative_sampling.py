import json
import time
import random
import re
import urllib.request
import urllib.parse
from pathlib import Path

def search_duckduckgo_lite(query):
    encoded_query = urllib.parse.quote(query)
    url = f"https://lite.duckduckgo.com/lite/"
    data = urllib.parse.urlencode({'q': query}).encode('utf-8')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    time.sleep(random.uniform(1.5, 3.0))
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Estrai tutti i link
            links = re.findall(r'href="([^"]+)"', html)
            asins = set()
            for link in links:
                if 'uddg=' in link:
                    actual_url = urllib.parse.unquote(link.split('uddg=')[1].split('&')[0])
                    match = re.search(r'/(?:dp|product)/([A-Z0-9]{10})', actual_url)
                    if match:
                        asins.add(match.group(1))
            return list(asins)
    except Exception as e:
        print(f"Errore query {query}: {e}")
        return []

def main():
    home = Path.home()
    dataset_file = home / ".amazon_search_offline.json"
    if not dataset_file.exists():
        print("Dataset non trovato.")
        return

    with open(dataset_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    products = data.get("products", [])
    print(f"Trovati {len(products)} prodotti nel dataset.")
    
    # 1. Definisci le categorie / query da cercare (Positive & Negative Sampling)
    # Vogliamo dividere tra collare cervicale, cuscino viaggio, e cuscino letto
    categories = {
        "Collare Cervicale": [
            'site:amazon.it/dp "collare cervicale"',
            'site:amazon.it/dp "collare ortopedico collo"',
            'site:amazon.it/dp "tutore collo"'
        ],
        "Cuscino Viaggio": [
            'site:amazon.it/dp "cuscino da viaggio"',
            'site:amazon.it/dp "cuscino aereo memory"',
            'site:amazon.it/dp "poggiatesta viaggio"'
        ],
        "Cuscino Letto Cervicale": [
            'site:amazon.it/dp "cuscino cervicale letto"',
            'site:amazon.it/dp "cuscino ortopedico memory foam dormire"'
        ]
    }
    
    # Raccogli ASIN per ogni categoria tramite scraping web
    category_asins = {cat: set() for cat in categories}
    
    for cat, queries in categories.items():
        print(f"--- Cercando ASIN per categoria: {cat} ---")
        for q in queries:
            print(f"Eseguo query web: {q}")
            found_asins = search_duckduckgo_lite(q)
            category_asins[cat].update(found_asins)
            print(f" -> Trovati {len(found_asins)} ASINs")
            
    # Usa le informazioni trovate online per dividere i prodotti del dataset
    results = {"Collare Cervicale": [], "Cuscino Viaggio": [], "Cuscino Letto Cervicale": [], "Ignoto/Altro": []}
    
    for p in products:
        asin = p.get("asin")
        assigned = False
        for cat, asins_set in category_asins.items():
            if asin in asins_set:
                results[cat].append(p)
                assigned = True
                break
        if not assigned:
            # Fallback testuale o ignoto
            title = p.get("title", "").lower()
            if "collare" in title and "cervicale" in title:
                results["Collare Cervicale"].append(p)
            elif "viaggio" in title or "aereo" in title:
                results["Cuscino Viaggio"].append(p)
            elif "letto" in title or "dormire" in title:
                results["Cuscino Letto Cervicale"].append(p)
            else:
                results["Ignoto/Altro"].append(p)
                
    # Stampo statistiche finali
    print("\n=== RISULTATI DIVISIONE TRAMITE NEGATIVE SAMPLING / RICERCA WEB ===")
    for cat, items in results.items():
        print(f"{cat}: {len(items)} prodotti")
        
    # Salvo il risultato in un file per reference
    out_file = home / "divisione_categorie_ml.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRisultati salvati in {out_file}")

if __name__ == "__main__":
    main()
