import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from pathlib import Path
import time

dataset_file = Path("C:/Users/Gilberto Bizzo/.amazon_search_offline.json")
try:
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    products = data.get('products', [])
except:
    products = []

query = 'collare cervicale russare'
online_asins = set()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

url = f'https://www.amazon.it/s?k={urllib.parse.quote(query)}'
try:
    r = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')
    for item in soup.find_all('div', {'data-component-type': 's-search-result'}):
        asin = item.get('data-asin')
        if asin: online_asins.add(asin)
except Exception as e:
    print(e)

match = [p for p in products if p.get('asin') in online_asins]

print(f'Trovati {len(online_asins)} risultati su Amazon per "{query}".')
print(f'Trovati {len(match)} match nel dataset Offline.')
for m in match:
    cat = m.get('category', 'Senza categoria')
    print(f' - {m.get("title")[:60]}... [{cat}]')
