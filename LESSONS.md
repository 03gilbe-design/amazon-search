# LESSONS — Top 12 errori ricorrenti & principi

**Repo:** amazon_search  
**Ultimo commit:** `8023347` (2026-07-03)  
**Scope:** errori osservati da PROGRESS + DESIGN_PLAN + STATO_NIGHT + web_benchmark (RESULTS, INTEGRATION_SCOUTING) + minoxidil audit + neck collar audit

## 1. rich.py rogue in home dir — path ordering

**Errore:** File `rich.py` (custom) in home dir shadowa libreria `rich` vera. Crash silenziosi finché non si gira da dir pulita. Successo 2 volte (night_runner, minoxidil session).

**Lezione:** `sys.path` ordering importa. Home in HEAD = shadowing garantito. Home in CODA = lasciapassare alle librerie installate.

**Applica:** Audit tutto home dir per nomi che shadoano stdlib. Se devi tenere file locale, rinominalo `_rich.py` o `myrich.py`. PYTHONPATH esplicito se critico.

---

## 2. "mean relevance ↑" fuorviante — ranking naive regredisce

**Errore:** Ranking per token-match REGREDIVA top1: `finstral.com` (produttore, giusto) → YouTube short (irrilevante ma keyword-matchy). Metrica "mean relevance" era **gameable**.

**Lezione:** Non lasciare feature deboli (keyword match) sovrascrivere segnali di autorità del motore sottostante. Affina, non sostituire. La posizione del motore = prior, non guess.

**Applica:** `W_POSITION` (bonus decrescente per engine_rank) > token-relevance bruto. Fidati ranking engine, raffinalo on edge cases, non ri-ordinare.

---

## 3. pass_rate ≠ metrica giusta da sola — due metriche in tensione

**Errore:** ZenRows migliora extraction (7→9 testo pieno) ma FA CROLLARE pass_rate (12/12→8/12) per sforare SLA latenza. Lezione di ZenRows: 16-22s JS+proxy = killer SLA.

**Lezione:** Metriche in tensione vanno lette INSIEME. Tavily solve: 2s fast + testo pieno = 12/12 pass. ZenRows last-resort.

**Applica:** Ogni provider spike = leggi (latenza, testo pieno, pass_rate) insieme. OFF default provider che ammazza pass_rate per marginal gain.

---

## 4. Latenza inline sincrona vs enrichment async

**Errore:** ZenRows (16-22s), Firecrawl (2.8-8.4s) finiti nel hot-path real-time → SLA sforata. Provider lenti SEMPRE opzionali fallback, mai path critico.

**Lezione:** Sincrono ha SLA. Asincrono non ha SLA → usalo offline/batch. Ordine catena: trafilatura (1-3s) → Tavily (1.75s) → [ZenRows/Firecrawl off-default].

**Applica:** `--use-zenrows` / `--use-firecrawl` sempre OFF default. Flag esplicito per deep enrichment.

---

## 5. PDF ≠ HTML per scraper — false positives da content-type

**Errore:** ZenRows ritorna "200 OK, 1.3M char" ma è binario PDF grezzo. Falso positivo se non controlli content-type/parsing. Testo "estratto" = garbage.

**Lezione:** HTTP 200 ≠ success. Verifica SEMPRE testo effettivo (non solo char count) e content-type. PDF serve parser separato (pypdf).

**Applica:** `extracted_text.strip() and len(text) > 500` sempre, post-fetch. PDF → `extract_pdf()` separato, non generico scraper.

---

## 6. Titoli Amazon mentono — verifica visiva obbligatoria

**Errore:** POFET venduto "rullo palla" ma foto mostra **pettine a denti**. Titolo != realtà. Trust titolo alone = sbagliato 10% dei prodotti.

**Lezione:** Vision verifica obbligatoria (Read immagine) PRIMA di fidarsi di title/categoria. Specialmente prodotti con nomi generici.

**Applica:** Per ogni ASIN top-3, scarica thumbnail via httpx → Read immagine, visual check. Flag discrepanze.

---

## 7. Materiale dichiarato Amazon contraddittorio

**Errore:** Campo "Acrilico/PS" vs bullet "PE" sullo stesso prodotto. Contraddizione ovvia = nessun source è gold.

**Lezione:** Material-first sourcing: cerca marche che DICHIARANO esplicitamente (lab-grade, industriali = sempre pulito). Cross-reference B2B (Alibaba/made-in-china) per OEM cinesi.

**Applica:** Se material=unknown, cross-ref B2B o scarica foto fondo per resin code (♳–♹ numero 2-7).

---

## 8. SearchAPI fragile — disabled hardcoded

**Errore:** SearchAPI ritorna 400 errors su engine amazon. Hardcoded OFF come fallback-only, SerpAPI = vero motore. Dead weight nel path critico.

**Lezione:** Se provider è fragile per il tuo use case, toglilo dal hot-path. Not "maybe later", disabilitalo subito. Codex altrimenti aspetta il crash.

**Applica:** `SEARCHAPI_FALLBACK_ONLY = True` permanente, oppure rimuovilo dal repo se morto.

---

## 9. Test "reporting" ≠ test regressione — assertion esplicite richieste

**Errore:** `test_real_offline.py` produce report utile ma SENZA assertion forti. Si può peggiorare il classificatore senza far fallire il test.

**Lezione:** Report = diagnostica. Test = guardrail. Se serve proteggere, aggiungi assert 3-5 fixture stabili.

**Applica:** Accoppia ogni report con 1-2 assertion piccoli su fixture stabili. Assertion prima di merge.

---

## 10. Quota API = risorsa scarsa da tracciare sempre

**Errore:** Ricerche senza logging → sorpresa fine mese quota esaurita. Nessuna visibilità sui consumi.

**Lezione:** Ogni call API log `before/after quota`. JSONL track timestamp, query, source, delta quota. Non è complesso, è obbligatorio per API pagate.

**Applica:** Vedi `logger.py` + log in runner. Replicare per ogni nuovo provider.

---

## 11. Handoff GPT arresta troppo presto su problemi locali

**Errore:** Handoff neck collar: GPT si arrende a "cache miss Amazon" senza sfruttare HTML locale già estratto. Verdetto prudente ("dubbio") ma povero.

**Lezione:** Se file locale/parziale esiste, usalo come INPUT non scusa. "Non posso accedere" ≠ "non ho niente". Raffinare dati locali > ricominciare.

**Applica:** Lettura COORD/ / evidenze locali PRIMA di dichiarare impossibile. "Incrementale non perfetto" > "perfectionist stuck".

---

## 12. GET diretto Amazon senza browser = HTML enorme ma bullet spesso 0

**Errore:** GET via httpx → 1MB+ HTML ma bullet=0 su 3/5 ASIN (neck audit). Fallback automatico su snippet quando bullet vuoto.

**Lezione:** GET grezzo non basta. JavaScript rendering o browser real utili. Fallback Canopy specs o vision immagine quando bullet=0.

**Applica:** If `bullets.count == 0` → fallback specs Canopy (ASIN batch fetch) o vision immagine per materiale.

---

## Uso

Leggi PRIMA di toccare `amazon_search/*`, specialmente:
- Prima di aggiungere provider → check latenza + fallback chain ordine
- Prima di usare materiale dichiarato → cross-ref B2B o visual check
- Prima di fidare ranking top1 → verifica autorità motore non è stato overfit

Handoff interrotto? Leggi file STATO locale PRIMA di ricominciare.
