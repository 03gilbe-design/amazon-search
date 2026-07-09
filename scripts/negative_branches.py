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

# 100 Query di Negative Sampling suddivise in rami logici
branches = {
    "Gonfiabili (Inflatables)": [
        "cuscino gonfiabile", "collare gonfiabile", "cuscino ad aria", 
        "cuscino aereo gonfiabile", "supporto collo gonfiabile", "trazione cervicale aria",
        "cuscino da viaggio aria", "gonfiabile collo", "collare aria", "trazione aria collo",
        "pompetta collare", "cuscino velluto gonfiabile", "cuscino mare gonfiabile", "collino gonfiabile"
    ],
    "Elettronica (Massagers/Heaters)": [
        "massaggiatore cervicale", "massaggiatore collo", "elettrostimolatore collo",
        "scaldacollo elettrico", "scaldacollo usb", "massaggio shiatsu collo",
        "fascia riscaldante collo", "cuscino massaggiante", "smartwatch", "cuffie bluetooth",
        "termocuscino", "cuscino termico elettrico", "massaggiatore spalle", "collare elettrico"
    ],
    "Abbigliamento / Inverno (Clothing)": [
        "scaldacollo pile", "sciarpa invernale", "scaldacollo lana", "fascia collo",
        "scaldacollo moto", "scaldacollo bambino", "scaldacollo running", "sciarpa termica",
        "scaldacollo sci", "scaldacollo uomo", "scaldacollo donna", "scaldacollo termico",
        "fascia testa lana", "cappello e scaldacollo", "sciarpa anello", "snood lana"
    ],
    "Animali domestici (Pets)": [
        "collare cane", "collare gatto", "collare antipulci", "collare elisabettiano",
        "collare addestramento", "collare luminoso cane", "collare cucciolo", "collare gps",
        "guinzaglio e collare", "collare zecche", "collare gatto antistrozzo", "pettorina cane"
    ],
    "Sonno generico (Sleep aids)": [
        "cerotti russare", "tappi orecchie dormire", "mascherina sonno", "dilatatore nasale",
        "bite notturno", "cuscino per dormire", "cuscino memory letto", "spray russare",
        "fascia mento russare", "sottogola russare", "bocchino russare", "bracciale russare"
    ],
    "Farmacia (Medical/Creams)": [
        "crema cervicale", "cerotti cervicale", "pomata antinfiammatoria", "gel dolori",
        "crema arnica", "artiglio del diavolo", "cerotti termici", "balsamo tigre",
        "integratori articolazioni", "tachipirina", "ibuprofene crema", "cerotti antidolorifici"
    ],
    "Accessori viaggio (Travel)": [
        "mascherina viaggio", "tappi viaggio", "poggiapiedi aereo", "valigia", 
        "cuscino bimbo viaggio", "organizer valigia", "copriocchi", "kit viaggio"
    ]
}

# Appiattimento delle query in una lista di 100 query e mappa (query -> branch)
query_to_branch = {}
for branch, q_list in branches.items():
    for q in q_list:
        query_to_branch[q] = branch

all_queries = list(query_to_branch.keys())
print(f"Preparate {len(all_queries)} query di Negative Sampling.")

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0'
]

# ASIN -> Set di (Branch, Query)
asin_to_noise = {}
successful_searches = 0
blocked_searches = 0

print("\n--- INIZIO MASSIVE NEGATIVE SCRAPING ---")
for i, query in enumerate(all_queries):
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept-Language': 'it-IT,it;q=0.9',
    }
    url = f'https://www.amazon.it/s?k={urllib.parse.quote(query)}'
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 503 or 'captcha' in r.text.lower() or 'robot check' in r.text.lower():
            blocked_searches += 1
            time.sleep(random.uniform(10, 15))
            continue
            
        soup = BeautifulSoup(r.text, 'html.parser')
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        branch = query_to_branch[query]
        for item in items:
            asin = item.get('data-asin')
            if asin:
                if asin not in asin_to_noise:
                    asin_to_noise[asin] = set()
                asin_to_noise[asin].add(branch)
                
        successful_searches += 1
        
        if (i+1) % 10 == 0:
            print(f"[{i+1}/{len(all_queries)}] OK: {successful_searches} | ASIN rumore raccolti: {len(asin_to_noise)}")
            
    except Exception as e:
        time.sleep(2)
        
    time.sleep(random.uniform(1.5, 3.5))

print("\n--- INCONTRO CON IL DATASET OFFLINE ---")
offline_asins = {p.get('asin'): p for p in products if p.get('asin')}
intersezione = set(offline_asins.keys()).intersection(asin_to_noise.keys())

print(f"ASIN Offline identificati come RUMORE: {len(intersezione)} su {len(offline_asins)}")

risultati_finali = {}
for asin in intersezione:
    p = offline_asins[asin]
    risultati_finali[asin] = {
        "title": p.get("title"),
        "branches": list(asin_to_noise[asin]),
        "manual_category": p.get("category", "Senza categoria")
    }

# Salvataggio
output_dir = Path("C:/Users/Gilberto Bizzo/amazon_search")
with open(output_dir / "negative_branches_results.json", "w", encoding="utf-8") as f:
    json.dump(risultati_finali, f, indent=4, ensure_ascii=False)

# Stampa sommario per branca
branch_counts = {b: 0 for b in branches.keys()}
for info in risultati_finali.values():
    for b in info["branches"]:
        branch_counts[b] += 1

print("\nProdotti rumore intercettati per Ramo (Branch):")
for b, count in branch_counts.items():
    if count > 0:
        print(f" - {b}: {count} prodotti")

print(f"\n[OK] Risultati completi salvati in {output_dir / 'negative_branches_results.json'}")
