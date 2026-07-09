# 🤖 HANDOVER CLAUDE CODE - PROGETTO AMAZON SEARCH

Benvenuto Claude! Questo è il documento di passaggio consegne da Gemini a te. 
Il progetto è una WebUI per clustering, classificazione e detection di immagini basata su Python (Flask backend) e Vanilla JS (Frontend).
Leggi attentamente tutto per non ripetere errori dolorosi.

## 📁 Struttura e Path Importanti
- **Root**: `C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements`
- **Backend App**: `webui/app.py` (Flask server, rotte API, clustering PHash, SIFT Scene Matching)
- **Frontend SPA**: `webui/templates/categorize.html` (Tutto il codice UI/UX, logica drag&drop, canvas, rendering SVG)
- **Dati Offline (Dataset base)**: `C:\Users\Gilberto Bizzo\.amazon_search_offline.json` (Dataset pesantissimo, ATTENZIONE a deduplicare per ASIN!)
- **Cache Dati**: `C:\Users\Gilberto Bizzo\.amazon_search_cache\*.json`

## 🧠 L'Obiettivo del Tool
Il tool carica prodotti Amazon e permette a Gilberto di raggrupparli e confrontarli. Le tre funzionalità principali sono:
1. **🌻 Girasole (Sunflower)**: Dispone le categorie a cerchio attorno a una foto. L'utente smista le foto tramite Drag&Drop o click. Aggiunto split screen per creare categorie al volo (sinistra "scartati", destra "promossi").
2. **📋 Kanban**: Dispone le foto a pile (stack). Lo script raggruppa foto dello stesso ASIN sotto una singola card con badge (xN ASIN) e hover pop-up.
3. **🔍 Image Detector (Scene Match)**: Usa OpenCV SIFT (RANSAC) in background per cercare prodotti all'interno di scene/foto ambientali. I match sono suddivisi in bucket base ai Punti in Comune (Identici >100, Varianti >35, Simili <35).
4. **🕸️ Distribuzione Parole**: Mostra un grafico o diagramma di Venn (appena aggiunto) delle parole più comuni raggruppate per categoria.

## 💣 Errori Dolorosi / Lezioni Imparate (Non Ripeterli!)
1. **Dataset Pesantissimi**: L'app si blocca se ricarichi tutto il file o esegui pesanti cicli RANSAC nel main thread di Javascript. Sposta tutto in background in Python (usando `threading.Thread`) o scrivi Javascript ottimizzato (No innerHTML continui).
2. **OpenCV (SIFT)**: Non puoi fare `import cv2.SIFT`. Si rompe. Devi usare `cv2.SIFT_create()`. Il path di PYTHONPATH potrebbe essere spaccato nei sub-scripts, ricordati di fare `sys.path.append()`.
3. **Immagini Amazon e 403 Forbidden**: Molte immagini Amazon restituiscono 403 se fai Fetch/XHR standard dal browser. Aggiungi `<meta name="referrer" content="no-referrer">` nell'head del file HTML, altrimenti Gilberto si incazza perché le immagini scompaiono.
4. **Layout CSS Grid/Flexbox**: Attenzione alle dipendenze di grandezza. Le UI di "Sunflower" e "Kanban" convivono nella stessa pagina. `switchView(view)` le nasconde impostando `display:none`. Non fare confusione con i container.
5. **Deduplicazione**: Se trovi "KMINA Collare Cervicale" 2 volte in Kanban o Sunflower, è perché lo script originario non filtra i duplicati! Lo abbiamo appena patchato in `app.py` ma tieni a mente che l'Offline Cache ha dentro mondezza.

## 📝 Richieste di Gilberto (Completate stanotte)
- [x] Aggiunto bottone globale 🛒 "Carrello" e pulsante inline cart sulle immagini. Lo stato è salvato in `localStorage`.
- [x] Sunflower diviso a metà (Sfondo Tick verde e Croce rossa). Drag&Drop sul background crea una nuova categoria.
- [x] Image Detector adesso separa i risultati in 3 "Bucket" basati sui Punti Inliers RANSAC per facilitare la revisione (Identiche vs Simili).
- [x] Aggiunti i Diagrammi di Venn (approssimati tramite sovrapposizione mix-blend e top keywords).
- [x] C'è uno script Python in esecuzione pianificata asincrona: `scripts/sift_exhaustive_combinations.py`. È dormiente per 2 ore e poi proverà incroci pazzi di SIFT.

## 🚀 Prossimi Passi Consigliati
- Trova e implementa loading GIF iconografiche moderne (la ricerca online suggerisce di **EVITARE le GIF e usare CSS Spinner/SVG** per performance e fluidità. Implementali al posto delle stringhe di caricamento).
- Testa a fondo la UI della barra delle Ricerche nel Girasole. Ho inserito la struttura ma il click necessita l'implementazione del ricaricamento del JSON corretto.
- Gilberto ha categorie "manuali" tipo "Altro" che andrebbero controllate automaticamente per valutare l'accuratezza visiva delle immagini che ci butta dentro.

Buon Lavoro Claude! Non fermarti mai.
-- Gemini
