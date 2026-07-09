import requests
from bs4 import BeautifulSoup
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
r = requests.get('https://html.duckduckgo.com/html/?q=site:amazon.it+collare+cervicale', headers=headers)
soup = BeautifulSoup(r.text, 'html.parser')
results = soup.find_all('a', class_='result__url')
for res in results:
    print(res.get('href'))
