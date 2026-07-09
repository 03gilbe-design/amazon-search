# STATO LAVORO: Test Deep Learning e Analisi

## Obiettivi
1. **Analisi Active Learning**: Quanti feedback (click) servono all'utente per istruire l'algoritmo a riconoscere la differenza tra "morbidi", "rigidi" e "rumore"?
2. **Analisi Clustering (Gruppi/Sottogruppi)**: Qual è la soglia ideale (slider) per evitare mega-gruppi o gruppi singoli, misurando la distanza dalla categorizzazione manuale (Ground Truth).
3. **Analisi Scraping**: Confronto di parità tra scraping Online (esteso) e dataset Offline attuale.

## Piano di Test
1. Creazione script `ml_evaluation.py` per simulare l'utente (N click di feedback) e misurare l'F1-score.
2. Sweep delle soglie Birch (Macro e Micro) e calcolo Adjusted Rand Index (ARI) rispetto ai gruppi manuali.
3. Chiamata API amazon-scraping in background per 100 prodotti e confronto intersezione ASIN.

## Limitazioni Dichiarate
- Il dataset manuale potrebbe non essere perfetto, ma lo usiamo come Ground Truth.
- Le ricerche online variano di giorno in giorno per colpa dell'algoritmo Amazon A9.
