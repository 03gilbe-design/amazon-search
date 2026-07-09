import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from pathlib import Path
import time
import random
import re

dataset_file = Path("C:/Users/Gilberto Bizzo/.amazon_search_offline.json")
try:
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    products = data.get('products', [])
except Exception as e:
    products = []
    print(e)

# Estraiamo query dai titoli dei prodotti, prendendo solo le prime 4-5 parole per non far fallire la ricerca
queries = set()
for p in products:
    title = p.get('title', '')
    if title:
        # Prendi le prime 5 parole pulite
        clean_title = re.sub(r'[^\w\s]', '', title)
        words = clean_title.split()[:5]
        if len(words) >= 2:
            queries.add(" ".join(words))

queries = list(queries)[:200]
print(f"Preparate {len(queries)} query uniche derivate dai prodotti.")

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0'
]

# Database ASIN estratti (Negative/Positive Sampling Graph)
# asin_to_queries = { ASIN: [lista_di_query_in_cui_compare] }
asin_to_queries = {}

successful_searches = 0
blocked_searches = 0

print("\n--- INIZIO MASSIVE SCRAPING (ANTI-BOT) ---")
for i, query in enumerate(queries):
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.it/'
    }
    url = f'https://www.amazon.it/s?k={urllib.parse.quote(query)}'
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 503 or 'captcha' in r.text.lower() or 'robot check' in r.text.lower():
            print(f"[{i+1}/200] BLOCCATO (Captcha) per: {query}")
            blocked_searches += 1
            time.sleep(random.uniform(10, 15)) # Pausa lunga se becca captcha
            continue
            
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        found = 0
        for item in items:
            asin = item.get('data-asin')
            if asin:
                found += 1
                if asin not in asin_to_queries:
                    asin_to_queries[asin] = set()
                asin_to_queries[asin].add(query)
                
        successful_searches += 1
        
        if (i+1) % 10 == 0:
            print(f"[{i+1}/200] Progress: {successful_searches} OK, {blocked_searches} Blocked. ASIN univoci raccolti: {len(asin_to_queries)}")
            
    except Exception as e:
        print(f"[{i+1}/200] ERRORE di rete: {e}")
        time.sleep(5)
        
    # Pausa random per evitare bot
    time.sleep(random.uniform(2.0, 4.5))

print("\n--- RISULTATI FINALI MASSIVE SCRAPING ---")
print(f"Ricerche Effettuate: {len(queries)}")
print(f"Ricerche Successo (No-Bot): {successful_searches}")
print(f"Ricerche Bloccate (Captcha): {blocked_searches}")
print(f"Totale ASIN univoci estratti dall'intero ecosistema: {len(asin_to_queries)}")

# Verifica intersezione con offline
offline_asins = {p.get('asin') for p in products if p.get('asin')}
intersezione = offline_asins.intersection(asin_to_queries.keys())

print(f"\nASIN Offline trovati durante la navigazione ombra: {len(intersezione)} su {len(offline_asins)}")

# Calcola quali query sono state più utili
query_hits = {}
for asin in intersezione:
    for q in asin_to_queries[asin]:
        query_hits[q] = query_hits.get(q, 0) + 1

print("\nLe 10 Query (ricavate dai titoli) che hanno fatto emergere più prodotti del tuo dataset:")
for q, hits in sorted(query_hits.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f" - '{q}': {hits} match")

print("\nTest completato interamente in memoria senza creare file esterni al sistema.")
