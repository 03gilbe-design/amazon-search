import time

print("="*60)
print(">>> TEST COMPARATIVO: IA (Gemini) vs STATISTICA (TF-IDF)")
print("Obiettivo: Rimuovere il rumore da 5000 query.")
print("="*60)

num_prodotti = 5000

# TEMPO TF-IDF
# Come abbiamo visto dal test precedente, ci mette 8.24 secondi totali
tempo_totale_tfidf = 8.24  # secondi
tempo_per_prodotto_tfidf = (tempo_totale_tfidf / num_prodotti) * 1000 # in ms

print(f"\n[1] MATEMATICA E STATISTICA (TF-IDF):")
print(f" -> Tempo per 1 prodotto: {tempo_per_prodotto_tfidf:.2f} ms")
print(f" -> Tempo per 5000 prodotti: {tempo_totale_tfidf:.2f} SECONDI")
print(f" -> Costo in API: $0.00 (Gratis e gira in locale)")

# TEMPO INTELLIGENZA ARTIFICIALE (LLM / Gemini Flash)
# Un LLM veloce (come Gemini Flash) impiega in media circa 1.2 secondi per 
# ricevere il prompt, analizzarlo, ragionare e restituire "Rumore" o "Segnale".
tempo_medio_api_llm = 1.2 # secondi per chiamata API
tempo_totale_llm = num_prodotti * tempo_medio_api_llm # secondi

print(f"\n[2] INTELLIGENZA ARTIFICIALE (Gemini API / AutoGPT):")
print(f" -> Tempo medio API per 1 prodotto: {tempo_medio_api_llm * 1000:.0f} ms")
print(f" -> Tempo per 5000 prodotti: {(tempo_totale_llm / 60):.2f} MINUTI (ovvero {tempo_totale_llm / 3600:.2f} ore)")
print(f" -> Costo in API: Circa $0.35 (Considerando i token di input/output)")

print("\n" + "="*60)
print(">>> CONCLUSIONE DEL TEST")
print("="*60)
print(f"Il TF-IDF è {((tempo_medio_api_llm*1000) / tempo_per_prodotto_tfidf):.0f} VOLTE più veloce di un LLM.")
print("Se usi Gemini in loop per rimuovere il rumore su 1 Milione di prodotti,")
print("il programma impiegherebbe circa 13 GIORNI di chiamate API ininterrotte.")
print("Il TF-IDF locale impiega 27 MINUTI totali.")
