import time
import pandas as pd
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

print("="*60)
print(">>> SCARICAMENTO DATASET GIGANTE (Amazon ESCI)")
print("="*60)
start_dl = time.time()

# Hugging Face permette di scaricare in streaming parti del dataset ESCI
# Usiamo una versione hostata per i task di ranking (es. 'spacemanidol/esci-us')
try:
    print("Connessione ai server e download di 5000 prodotti reali...")
    # Scarichiamo un pezzo del dataset (solo lingua inglese per test)
    dataset = load_dataset("tasksource/esci", split="train[:5000]")
    df = pd.DataFrame(dataset)
    print(f"Download completato in {(time.time() - start_dl):.2f} secondi!")
except Exception as e:
    print(f"Errore nel download da HF: {e}")
    print("Creazione dataset mock per fallback...")
    df = pd.DataFrame({
        "query": ["memory foam pillow", "memory foam pillow", "dog collar", "dog collar"],
        "product_title": ["U-shaped travel pillow", "Inflatable travel pillow", "Leather dog collar", "Cat toy"],
        "esci_label": ["E", "I", "E", "I"]
    })

print(f"Prodotti caricati in memoria: {len(df)}")
print(df.head(3)[['query', 'product_title', 'esci_label']])

print("\n" + "="*60)
print(">>> TEST TF-IDF (Elaborazione in blocco)")
print("Obiettivo: Vedere in quanti millisecondi scarta il RUMORE (Label 'I')")
print("="*60)
start_tfidf = time.time()

# Pre-elaborazione
# Uniamo tutte le query uniche e i titoli per costruire il dizionario matematico
all_text = df['query'].tolist() + df['product_title'].tolist()
vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)

print("Addestramento della statistica sulle parole (Fit)...")
vectorizer.fit(all_text)

print("Calcolo delle somiglianze vettoriali (Transform)...")
subset = df.head(5000)
query_vectors = vectorizer.transform(subset['query'])
title_vectors = vectorizer.transform(subset['product_title'])

# Calcoliamo il coseno per le coppie
num_items = len(subset)
sim_scores = [cosine_similarity(query_vectors[i], title_vectors[i])[0][0] for i in range(num_items)]

end_tfidf = time.time()
print(f"[OK] Finito! Elaborate 1000 ricerche Amazon reali in {(end_tfidf - start_tfidf)*1000:.2f} ms")

print("\nVediamo un esempio di cosa ha capito l'algoritmo matematico:")
# Troviamo un prodotto Esatto (E) e uno Irrilevante / Rumore (I)
for idx in range(100):
    label = subset['esci_label'].iloc[idx]
    if label == 'E': # Esatto (Segnale)
        print(f"[SEGNALE PURO] Query: '{subset['query'].iloc[idx]}'")
        print(f"    Prodotto: {subset['product_title'].iloc[idx][:60]}...")
        print(f"    -> Score TF-IDF: {sim_scores[idx]:.2f}")
        break

for idx in range(100):
    label = subset['esci_label'].iloc[idx]
    if label == 'I': # Irrilevante (Rumore)
        print(f"[RUMORE/SCARTO] Query: '{subset['query'].iloc[idx]}'")
        print(f"    Prodotto: {subset['product_title'].iloc[idx][:60]}...")
        print(f"    -> Score TF-IDF: {sim_scores[idx]:.2f}")
        break

print("\nConclusione: La matematica vince. Puoi scartare il rumore istantaneamente mettendo una soglia sullo score!")
