import urllib.request
import json
import time
import os

queries = [
    "lightweight css animation library",
    "vanilla js animation engine",
    "micro-interactions library",
    "FLIP animation vanilla js",
    "layout transition library js",
    "drag and drop animation js",
    "svg animation lightweight",
    "canvas animation lightweight",
    "pure css transitions",
    "js physics animation lightweight",
    "spring animation javascript",
    "ui transitions css",
    "lightweight scroll animation",
    "reveal on scroll css library",
    "hover effects css lightweight",
    "card flip animation css",
    "masonry layout animation js",
    "grid transition animation",
    "javascript tweening engine",
    "tiny animation library",
    "minimal css animations",
    "zero dependency animation js",
    "dom animation library",
    "web animations api wrapper",
    "smooth scroll vanilla js",
    "parallax lightweight js",
    "text animation css",
    "loading spinner css minimalist",
    "toast notification animation css",
    "modal transition css",
    "css keyframes library",
    "javascript requestanimationframe library",
    "gpu accelerated css animations",
    "hardware accelerated transitions",
    "staggered animations js",
    "list reorder animation js",
    "swipe animation vanilla js",
    "page transition library lightweight",
    "60fps css animations",
    "lightweight particle animation js"
]

results = {}

print("Iniziando la ricerca ad albero su GitHub (40 query)...")
print("Uso l'API pubblica di GitHub. Inserisco un piccolo ritardo per non superare il rate limit (10 req/min).")

for i, q in enumerate(queries):
    # Rimuoviamo spazi e creiamo query valide per GitHub
    safe_q = urllib.parse.quote(f"{q} in:readme,description sort:stars-desc")
    url = f"https://api.github.com/search/repositories?q={safe_q}&per_page=3"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get("items", [])
            repos = []
            for item in items:
                # Evitiamo roba troppo pesante (selezioniamo solo < 5000 KB se possibile, o ignoriamo la size se ottimi)
                if item.get("size", 0) < 50000: # < 50 MB
                    repos.append({
                        "name": item["full_name"],
                        "description": item["description"],
                        "stars": item["stargazers_count"],
                        "url": item["html_url"]
                    })
            results[q] = repos
            print(f"[{i+1}/40] Trovati {len(repos)} repo per '{q}'")
    except Exception as e:
        print(f"[{i+1}/40] Errore API per '{q}': {e}")
        # Gestione rate limit manuale
        if "403" in str(e):
            print("Rate limit raggiunto. Pausa di 30 secondi...")
            time.sleep(30)
            
    # Pausa di 6.5 secondi per restare sotto le 10 chiamate al minuto
    time.sleep(6.5)

output_file = r"C:\Users\Gilberto Bizzo\amazon_search\github_animations_report.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"\nRicerca completata. Risultati salvati in {output_file}")
