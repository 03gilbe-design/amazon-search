import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import time
import random

def search_ddg_amazon(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    encoded_query = urllib.parse.quote(f"site:amazon.it {query}")
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    
    # Optional delay to avoid bans
    time.sleep(random.uniform(1.0, 3.0))
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', class_='result__url')
        
        asins = set()
        for link in links:
            href = link.get('href', '')
            # Decode DuckDuckGo redirect URL
            if 'uddg=' in href:
                href = urllib.parse.unquote(href.split('uddg=')[1].split('&')[0])
                
            match = re.search(r'/(?:dp|product)/([A-Z0-9]{10})', href)
            if match:
                asins.add(match.group(1))
                
        return list(asins)
    except Exception as e:
        print(f"Error: {e}")
        return []

print(search_ddg_amazon("cuffie bluetooth"))
