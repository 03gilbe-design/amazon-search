import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from pathlib import Path
import time
import random

dataset_file = Path("C:/Users/Gilberto Bizzo/.amazon_search_offline.json")
try:
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    products = data.get('products', [])
except Exception as e:
    products = []
    print("Errore caricamento:", e)

# 1. Definiamo le query di Negative Sampling (RUMORE) e Positive Sampling (VALIDI)
queries_rumore = [
    "cuscino da viaggio gonfiabile",
    "massaggiatore cervicale elettrico",
    "collare cane",
    "scaldacollo invernale pile",
    "fascia riscaldante collo",
    "smart watch",
    "cuffie bluetooth"
]

queries_valide = [
    "collare cervicale morbido",
    "collare cervicale rigido ortopedico",
    "cuscino viaggio memory foam",
    "supporto collo russare"
]

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15'
]

def scrape_queries(queries_list, limit_pages=2):
    asins = set()
    for query in queries_list:
        for page in range(1, limit_pages + 1):
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept-Language': 'it-IT,it;q=0.9',
            }
            url = f'https://www.amazon.it/s?k={urllib.parse.quote(query)}&page={page}'
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 503 or 'captcha' in r.text.lower():
                    time.sleep(10)
                    continue
                soup = BeautifulSoup(r.text, 'html.parser')
                items = soup.find_all('div', {'data-component-type': 's-search-result'})
                for item in items:
                    asin = item.get('data-asin')
                    if asin: asins.add(asin)
            except Exception as e:
                pass
            time.sleep(random.uniform(1.5, 3.0))
    return asins

print("Avvio classificazione automatica Rumore vs Non-Rumore...")
print("1. Raccolta Negative Sampling (Rumore)...")
asins_rumore = scrape_queries(queries_rumore, limit_pages=2)
print(f"   -> Raccolti {len(asins_rumore)} ASIN di RUMORE puro dal web.")

print("2. Raccolta Positive Sampling (Prodotti Validi)...")
asins_validi = scrape_queries(queries_valide, limit_pages=3)
print(f"   -> Raccolti {len(asins_validi)} ASIN di prodotti VALIDI dal web.")

# Algoritmo di Divisione Automatica
prodotti_rumore = []
prodotti_validi = []
prodotti_neutri = []

for p in products:
    asin = p.get('asin')
    title = p.get('title', '')
    
    is_rumore = asin in asins_rumore
    is_valido = asin in asins_validi
    
    if is_rumore and not is_valido:
        prodotti_rumore.append(p)
    elif is_valido and not is_rumore:
        prodotti_validi.append(p)
    elif is_rumore and is_valido:
        # Se cade in entrambi, Amazon è confuso. Trattiamolo come rumore ibrido
        prodotti_rumore.append(p)
    else:
        # Text fallback per quelli non trovati nelle prime pagine
        title_low = title.lower()
        if "gonfiabile" in title_low or "elettr" in title_low or "massagg" in title_low or "cane" in title_low or "scald" in title_low:
            prodotti_rumore.append(p)
        elif "collare" in title_low or "memory foam" in title_low:
            prodotti_validi.append(p)
        else:
            prodotti_neutri.append(p)

print("\n=== RISULTATO CLASSIFICAZIONE AUTOMATICA ===")
print(f"Totale prodotti offline: {len(products)}")
print(f"\n[!] PRODOTTI ETICHETTATI COME RUMORE (Da Scartare): {len(prodotti_rumore)}")
for p in prodotti_rumore[:5]:
    cat = p.get('category', 'Senza categoria')
    print(f" - {p.get('title')[:60]}... [Manual: {cat}]")

print(f"\n[V] PRODOTTI ETICHETTATI COME VALIDI (Segnale): {len(prodotti_validi)}")
for p in prodotti_validi[:5]:
    cat = p.get('category', 'Senza categoria')
    print(f" - {p.get('title')[:60]}... [Manual: {cat}]")
    
print(f"\n[?] PRODOTTI NON CLASSIFICATI: {len(prodotti_neutri)}")

# SALVATAGGIO DEI RISULTATI IN JSON
import os
output_dir = Path("C:/Users/Gilberto Bizzo/amazon_search")

# Salvataggio dataset pulito (solo validi)
with open(output_dir / "dataset_segnale.json", "w", encoding="utf-8") as f:
    json.dump({"products": prodotti_validi}, f, indent=4, ensure_ascii=False)

# Salvataggio dataset rumore (da scartare)
with open(output_dir / "dataset_rumore.json", "w", encoding="utf-8") as f:
    json.dump({"products": prodotti_rumore}, f, indent=4, ensure_ascii=False)

# Salvataggio dataset neutro (non classificati)
with open(output_dir / "dataset_neutro.json", "w", encoding="utf-8") as f:
    json.dump({"products": prodotti_neutri}, f, indent=4, ensure_ascii=False)

print(f"\n[OK] Risultati salvati fisicamente in: {output_dir}")
