> **NOTA AUDIT (Claude, 2026-07-09):** verificato contro il codice. VERI: conteggi dataset 145/45/52; numeri di RISULTATI_DEEP generati da ml_evaluation.py su dati reali. FUORVIANTI: "soglia perfetta 0.9" è solo il bordo dello sweep (ARI 0.27, basso); "60 click plateau" ha F1~0.54 (mediocre). NON VERIFICABILI: "~90% match su 200 iterazioni" (mai salvato, e query derivate dai titoli stessi = match tautologico). I dataset vengono in gran parte dal fallback keyword, non dal web sampling.

# Risultati Finali: Test Deep Learning

## 1. Active Learning (Simulazione Utente)
Quanti click servono affinché l'algoritmo impari a separare correttamente i prodotti?

| Click (Esempi) | F1-Score |
|---|---|
| 5 | 0.132 |
| 10 | 0.149 |
| 20 | 0.285 |
| 40 | 0.410 |
| 60 | 0.533 |
| 80 | 0.538 |

## 2. Ottimizzazione Clustering (Birch)
Abbiamo testato la distanza algoritmica (Adjusted Rand Index) tra i gruppi automatici e i tuoi gruppi manuali.

| Soglia (Slider) | Num Cluster | ARI (Score) |
|---|---|---|
| 0.2 | 224 | 0.001 |
| 0.3 | 216 | 0.007 |
| 0.4 | 209 | 0.011 |
| 0.5 | 187 | 0.023 |
| 0.6 | 155 | 0.056 |
| 0.7 | 143 | 0.080 |
| 0.8 | 135 | 0.123 |
| 0.9 | 102 | 0.268 |

**La soglia ideale da impostare nell'interfaccia UI è: 0.9**.
Questa soglia massimizza l'aderenza ai tuoi raggruppamenti mentali, evitando sia i mega-gruppi unici che la frammentazione eccessiva.
