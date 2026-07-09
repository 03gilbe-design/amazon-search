import json
import time
from pathlib import Path
import difflib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Caricamento del dataset
dataset_file = Path(str(Path.home() / ".amazon_search_offline.json"))
try:
    with open(dataset_file, 'r', encoding='utf-8') as f:
        products = json.load(f).get('products', [])
except Exception as e:
    products = []
    print("Errore:", e)

# Testiamo questi due prodotti come esempio
campioni = [
    "Collare per Cani Antiparassitario Seresto", 
    "Collare Cervicale Ortopedico Morbido per Dormire",
    "Cuscino Gonfiabile da Viaggio a Forma di U"
]
# Se non li troviamo esatti, estraiamo 3 prodotti a caso dal DB
titoli = [p.get('title') for p in products[:10]] if len(products) > 0 else campioni

query_rumore = "collare per cane antipulci"
query_segnale = "collare cervicale ortopedico"

print("="*60)
print(">>> TEST 1: FUZZY STRING MATCHING (Leggerissimo, built-in Python)")
print("Nessun modello AI, calcola solo quante lettere bisogna cambiare.")
print("="*60)
start = time.time()

for titolo in titoli[:5]:
    # Ratio = quanto i due testi si assomigliano (da 0.0 a 1.0)
    sim_rumore = difflib.SequenceMatcher(None, query_rumore.lower(), titolo.lower()).ratio()
    sim_segnale = difflib.SequenceMatcher(None, query_segnale.lower(), titolo.lower()).ratio()
    
    print(f"-> Prodotto: {titolo[:50]}...")
    print(f"   Match con RUMORE ('{query_rumore}'): {sim_rumore:.2f}")
    print(f"   Match con SEGNALE ('{query_segnale}'): {sim_segnale:.2f}")
    if sim_rumore > sim_segnale:
        print("   [X] GIUDIZIO FUZZY: Questo è RUMORE (Scartare)")
    else:
        print("   [V] GIUDIZIO FUZZY: Questo è SEGNALE (Tenere)")
    print("-")

print(f"Tempo di esecuzione Fuzzy: {(time.time() - start)*1000:.2f} ms\n")

print("="*60)
print(">>> TEST 2: TF-IDF + Cosine Similarity (Scikit-Learn)")
print("Statistica pura: conta la frequenza delle parole pesando la loro rarità.")
print("="*60)
start = time.time()

# Creiamo il motore matematico
vectorizer = TfidfVectorizer(stop_words='english')
# Inseriamo le query e i titoli
corpus = [query_rumore, query_segnale] + titoli[:5]
tfidf_matrix = vectorizer.fit_transform(corpus)

# Calcoliamo la vicinanza (coseno) tra le query (indici 0 e 1) e i prodotti (indici 2+)
for i, titolo in enumerate(titoli[:5]):
    idx_prodotto = i + 2
    sim_rumore = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[idx_prodotto:idx_prodotto+1])[0][0]
    sim_segnale = cosine_similarity(tfidf_matrix[1:2], tfidf_matrix[idx_prodotto:idx_prodotto+1])[0][0]
    
    print(f"-> Prodotto: {titolo[:50]}...")
    print(f"   TF-IDF con RUMORE: {sim_rumore:.2f}")
    print(f"   TF-IDF con SEGNALE: {sim_segnale:.2f}")
    if sim_rumore > sim_segnale:
        print("   [X] GIUDIZIO TF-IDF: Questo è RUMORE (Scartare)")
    else:
        print("   [V] GIUDIZIO TF-IDF: Questo è SEGNALE (Tenere)")
    print("-")

print(f"Tempo di esecuzione TF-IDF: {(time.time() - start)*1000:.2f} ms")
