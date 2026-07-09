from pathlib import Path
import urllib.request
import json
import time
import os
import re

print("Iniziando Ricerca ad Albero Dinamica su GitHub...")
print("L'algoritmo non usa query predefinite. Esplora i 'topics' dei repository, scarta il rumore (framework pesanti) e segue i nodi più promettenti (lightweight/vanilla).")

visited_queries = set()
# Seed iniziale
queue = [{"query": "lightweight animation", "score": 100}]
collected_repos = {}

# Parole per il negative sampling (rumore da evitare)
noise_words = ['react', 'angular', 'vue', 'heavy', 'framework', 'fullstack', 'django', 'laravel', 'nextjs', 'flutter']
# Parole per il positive sampling (gap da seguire)
boost_words = ['vanilla', 'css', 'micro', 'lightweight', 'tiny', 'zero-dependency', 'svg', 'canvas', 'transition', 'interaction', 'ui', 'dashboard']

iterations = 0
max_iterations = 40

while queue and iterations < max_iterations:
    # Ordina la coda per score decrescente
    queue.sort(key=lambda x: x['score'], reverse=True)
    
    # Prendi il nodo migliore non visitato
    current = queue.pop(0)
    q = current["query"]
    
    if q in visited_queries:
        continue
        
    visited_queries.add(q)
    iterations += 1
    
    print(f"\n[{iterations}/{max_iterations}] Esplorazione nodo: '{q}' (Score: {current['score']})")
    
    # Query verso Github (cerchiamo repository)
    # Aggiungiamo in:description,readme per allargare il match
    safe_q = urllib.parse.quote(f"{q} in:topics,description,readme sort:stars-desc")
    url = f"https://api.github.com/search/repositories?q={safe_q}&per_page=5"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/vnd.github.mercy-preview+json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            items = data.get("items", [])
            
            new_topics_found = {}
            
            for item in items:
                repo_name = item["full_name"]
                # Filtro rumore hard: se pesa più di 30MB, probabilmente non è lightweight
                if item.get("size", 0) > 30000:
                    continue
                    
                if repo_name not in collected_repos:
                    collected_repos[repo_name] = {
                        "description": item.get("description", ""),
                        "stars": item["stargazers_count"],
                        "url": item["html_url"],
                        "topics": item.get("topics", [])
                    }
                
                # Estrai nuovi nodi (topics) per l'albero
                for topic in item.get("topics", []):
                    topic_lower = topic.lower()
                    if topic_lower not in visited_queries:
                        new_topics_found[topic_lower] = new_topics_found.get(topic_lower, 0) + 1
                        
            # Calcola lo score per i nuovi rami trovati
            for topic, freq in new_topics_found.items():
                score = freq * 10 # Base score basato su popolarità nel nodo corrente
                
                # Negative sampling
                if any(noise in topic for noise in noise_words):
                    score -= 50 # Penalità pesante
                
                # Positive sampling
                if any(boost in topic for boost in boost_words):
                    score += 20 # Boost
                    
                if score > 0:
                    # Inserisci il nuovo ramo nella coda
                    queue.append({"query": topic, "score": score})
                    
    except Exception as e:
        print(f"Errore API per '{q}': {e}")
        if "403" in str(e):
            print("Rate limit raggiunto. Pausa di 30 secondi...")
            time.sleep(30)
            
    # Pausa di 6.5s per evitare rate limit (10 req/minuto)
    time.sleep(6.5)

# Salvataggio finale
output_file = rstr(Path.home() / "amazon_search", "github_dynamic_tree_search.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "visited_queries": list(visited_queries),
        "total_repos_found": len(collected_repos),
        "repos": collected_repos
    }, f, indent=4, ensure_ascii=False)

print(f"\nRicerca ad albero completata! Esplorati {iterations} nodi unici.")
print(f"Librerie candidate salvate in: {output_file}")
