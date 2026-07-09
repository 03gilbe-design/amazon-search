import time
import urllib.request
import concurrent.futures
from pathlib import Path
import pandas as pd
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from PIL import Image
import io

print("="*60)
print(">>> STRESS TEST LOCALE: DATI MASSIVI + IMMAGINI")
print("="*60)

# 1. TEST TESTUALE (50.000 RIGHE)
print("\n[FASE 1] Caricamento di 50.000 righe dal dataset ESCI testuale...")
start_txt_load = time.time()
try:
    # Usiamo il dataset già scaricato in cache!
    dataset = load_dataset("tasksource/esci", split="train[:50000]")
    df = pd.DataFrame(dataset)
except Exception as e:
    print("Errore nel caricamento:", e)
    df = pd.DataFrame({"query": ["test"]*50000, "product_title": ["test title"]*50000})

print(f"Caricamento completato in {time.time()-start_txt_load:.2f} secondi.")

print("\n[FASE 2] Avvio Elaborazione Matematica Locale (TF-IDF) su 50.000 prodotti...")
start_tfidf = time.time()
all_text = df['query'].tolist() + df['product_title'].tolist()
vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
vectorizer.fit(all_text)
query_vectors = vectorizer.transform(df['query'])
title_vectors = vectorizer.transform(df['product_title'])
end_tfidf = time.time()
print(f"-> TEMPO TF-IDF (50.000 prodotti): {end_tfidf - start_tfidf:.2f} Secondi.")


# 3. TEST IMMAGINI (DOWNLOAD E PROCESSO LOCALE)
print("\n[FASE 3] Test di Download + Elaborazione Immagini in Locale")
print("Scaricheremo 100 immagini reali dal web e le elaboreremo (Resize + Analisi base)")

# Usiamo un placeholder veloce o un URL reale per simulare le foto dei prodotti Amazon
url_img = "https://picsum.photos/400/400"  # Immagine casuale 400x400

def scarica_e_processa(i):
    try:
        # Download (I/O)
        req = urllib.request.Request(url_img, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            image_data = response.read()
        
        # Elaborazione puramente locale (Senza AI)
        # Apriamo l'immagine in RAM e facciamo un'operazione pesante (ridimensionamento)
        image = Image.open(io.BytesIO(image_data))
        # Simuliamo estrazione feature (es. per SIFT o hashing visivo)
        image_resized = image.resize((224, 224)).convert('L') # Convert to grayscale
        return True
    except Exception as e:
        return False

start_img = time.time()
successi = 0
num_immagini = 100

# Usiamo il multithreading per scaricare e processare le immagini in parallelo
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    risultati = list(executor.map(scarica_e_processa, range(num_immagini)))
    successi = sum(risultati)

end_img = time.time()
print(f"-> TEMPO IMMAGINI ({successi}/{num_immagini} elaborate): {end_img - start_img:.2f} Secondi.")
print(f"-> Media per Immagine (Download + Processo): {((end_img - start_img) / num_immagini) * 1000:.2f} ms")

print("\n" + "="*60)
print(">>> CONCLUSIONI TEMPISTICHE")
print("="*60)
print(f"Testo (50.000) = {end_tfidf - start_tfidf:.2f} s")
print(f"Immagini ({num_immagini}) = {end_img - start_img:.2f} s")
print("I colli di bottiglia sono la banda internet per le immagini, ma l'elaborazione locale su CPU è fulminea!")
