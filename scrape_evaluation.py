import sys
import os
import json
from pathlib import Path

sys.path.append(rstr(Path.home() / "amazon_search", ".claude", "worktrees", "amazon-improvements", "webui"))
from app import JOBS, _build_dataset_job
sys.path.append(rstr(Path.home() / "amazon_search"))
from amazon_search.searcher import AmazonSearcher

def run_scraping_test():
    print("=== AVVIO TEST SCRAPING (Online vs Offline) ===")
    
    _build_dataset_job()
    job = JOBS["dataset"]
    offline_products = job["result"].products
    query = job["result"].query
    domain = job["result"].filters.get("domain", "it")
    
    offline_asins = {p.asin for p in offline_products}
    print(f"Dataset Offline: {len(offline_asins)} ASIN, Query: '{query}', Domain: {domain}")
    
    # Eseguiamo scraping online per molti prodotti (es. 150)
    print("Esecuzione scraping online in corso (SerpAPI / SearchAPI)...")
    searcher = AmazonSearcher()
    online_products = searcher.search(query=query, max_results=150, domain=domain)
    
    if not online_products:
        print("Scraping online fallito o zero risultati.")
        return
        
    online_asins = {p.asin for p in online_products}
    
    # Calcolo intersezione
    intersection = offline_asins.intersection(online_asins)
    print(f"Risultati Online ottenuti: {len(online_asins)}")
    print(f"Asin in comune (Parita'): {len(intersection)} su {len(online_asins)} ({(len(intersection)/len(online_asins))*100:.1f}%)")
    
    missed_by_offline = online_asins - offline_asins
    missed_by_online = offline_asins - online_asins
    
    print(f"Trovati online ma NON in offline: {len(missed_by_offline)}")
    print(f"Trovati offline ma NON in online: {len(missed_by_online)}")
    
if __name__ == "__main__":
    run_scraping_test()
