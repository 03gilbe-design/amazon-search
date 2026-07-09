from pathlib import Path
import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>30 Animazioni SVG Complesse - Tailored for Amazon Search AI</title>
    <style>
        :root {
            --primary: #3b82f6;
            --secondary: #10b981;
            --danger: #ef4444;
            --bg: #0f172a;
            --card-bg: #1e293b;
        }
        body {
            font-family: 'Inter', system-ui, sans-serif;
            background-color: var(--bg);
            color: #f8fafc;
            margin: 0;
            padding: 2rem;
        }
        .header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 2rem;
        }
        .card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
            border: 1px solid #334155;
            transition: all 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2);
        }
        .svg-container {
            width: 120px;
            height: 120px;
        }
        svg { width: 100%; height: 100%; overflow: visible; }
        
        .desc { font-size: 0.85rem; color: #94a3b8; text-align: center; line-height: 1.4; }
        .title { font-weight: bold; color: #e2e8f0; font-size: 1.1rem; }

        /* Complex Keyframes */
        @keyframes draw-path { 0% { stroke-dashoffset: 1000; } 100% { stroke-dashoffset: 0; } }
        @keyframes ransac-break { 0%, 40% { opacity: 1; stroke: var(--primary); } 50%, 90% { opacity: 0; stroke: var(--danger); } 100% { opacity: 1; stroke: var(--primary); } }
        @keyframes ransac-keep { 0%, 40% { stroke: var(--primary); } 50%, 100% { stroke: var(--secondary); stroke-width: 4; } }
        @keyframes birch-expand { 0% { transform: scale(0); opacity: 0; } 50% { transform: scale(1.1); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
        @keyframes scan-line { 0% { transform: translateY(-40px); opacity: 0; } 50% { opacity: 1; } 100% { transform: translateY(40px); opacity: 0; } }
        @keyframes data-flow { 0% { stroke-dashoffset: 20; } 100% { stroke-dashoffset: 0; } }
        @keyframes pulse-node { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.5); fill: var(--secondary); } }
        @keyframes spin-slow { 100% { transform: rotate(360deg); } }
        @keyframes float-complex { 0%, 100% { transform: translate(0, 0); } 33% { transform: translate(5px, -10px); } 66% { transform: translate(-5px, 5px); } }
        @keyframes active-learn-reject { 0% { transform: translateX(0); opacity:1; } 100% { transform: translateX(50px) rotate(45deg); opacity:0; } }
        @keyframes binary-stream { 0% { transform: translateY(0); } 100% { transform: translateY(-50px); } }
        @keyframes radar-ping { 0% { r: 0; opacity: 1; } 100% { r: 50; opacity: 0; } }
        @keyframes centroid-move { 0%, 100% { cx: 50; cy: 50; } 50% { cx: 70; cy: 30; } }
        @keyframes proxy-deflect { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(-15px); } }
        @keyframes hash-compare { 0% { fill: #334155; } 50% { fill: var(--secondary); } 100% { fill: #334155; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>30 Animazioni SVG Complesse (Amazon Search AI)</h1>
        <p>Progettate specificamente per spiegare la logica del tuo codice (SIFT, RANSAC, BIRCH, Active Learning, ecc.)</p>
    </div>
    <div class="grid" id="grid"></div>

    <script>
        const complexSvgs = [
            {
                t: "1. SIFT RANSAC Filter",
                d: "Mostra le linee di feature matching: le false corrispondenze (rosse) vengono spezzate, quelle inlier (verdi) rimangono.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="10" y="20" width="30" height="60" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
                    <rect x="60" y="20" width="30" height="60" rx="4" fill="none" stroke="currentColor" stroke-width="2"/>
                    <circle cx="25" cy="30" r="3" fill="currentColor"/><circle cx="75" cy="30" r="3" fill="currentColor"/>
                    <circle cx="25" cy="70" r="3" fill="currentColor"/><circle cx="75" cy="50" r="3" fill="currentColor"/>
                    <circle cx="25" cy="50" r="3" fill="currentColor"/><circle cx="75" cy="70" r="3" fill="currentColor"/>
                    <line x1="25" y1="30" x2="75" y2="30" stroke="currentColor" stroke-width="2" style="animation: ransac-keep 3s infinite"/>
                    <line x1="25" y1="50" x2="75" y2="70" stroke="currentColor" stroke-width="2" style="animation: ransac-break 3s infinite"/>
                    <line x1="25" y1="70" x2="75" y2="50" stroke="currentColor" stroke-width="2" style="animation: ransac-break 3s infinite"/>
                </svg>`
            },
            {
                t: "2. BIRCH Clustering Hierarchy",
                d: "Costruzione gerarchica dei cluster di testo (CF Tree). I nodi figli si espandono dal nodo padre.",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="50" cy="20" r="8" fill="var(--primary)"/>
                    <line x1="50" y1="28" x2="30" y2="45" stroke="currentColor" stroke-width="2" style="transform-origin: 50px 20px; animation: birch-expand 2s infinite ease-out"/>
                    <line x1="50" y1="28" x2="70" y2="45" stroke="currentColor" stroke-width="2" style="transform-origin: 50px 20px; animation: birch-expand 2s infinite ease-out 0.2s"/>
                    <circle cx="30" cy="50" r="6" fill="currentColor" style="animation: birch-expand 2s infinite 0.1s"/>
                    <circle cx="70" cy="50" r="6" fill="currentColor" style="animation: birch-expand 2s infinite 0.3s"/>
                    <line x1="30" y1="56" x2="20" y2="75" stroke="currentColor" stroke-width="2" style="animation: birch-expand 2s infinite 0.4s"/>
                    <line x1="30" y1="56" x2="40" y2="75" stroke="currentColor" stroke-width="2" style="animation: birch-expand 2s infinite 0.5s"/>
                    <circle cx="20" cy="80" r="4" fill="var(--secondary)" style="animation: birch-expand 2s infinite 0.6s"/>
                    <circle cx="40" cy="80" r="4" fill="var(--secondary)" style="animation: birch-expand 2s infinite 0.7s"/>
                </svg>`
            },
            {
                t: "3. Active Learning (Noise Purge)",
                d: "Filtro ad imbuto: il Tasto Magico identifica il prodotto rumore e lo espelle fuori dall'app.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 20 L80 20 L60 50 L60 80 L40 80 L40 50 Z" fill="none" stroke="currentColor" stroke-width="4"/>
                    <circle cx="50" cy="10" r="5" fill="var(--secondary)" style="animation: data-flow 2s infinite; transform: translateY(30px)"/>
                    <rect x="45" y="5" width="10" height="10" fill="var(--danger)" style="animation: active-learn-reject 2s infinite 0.5s; transform-origin: center"/>
                </svg>`
            },
            {
                t: "4. SIFT Keypoint Grid Scan",
                d: "L'algoritmo SIFT scansiona l'immagine alla ricerca di gradienti e angoli (keypoints).",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="20" y="20" width="60" height="60" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="5"/>
                    <line x1="20" y1="50" x2="80" y2="50" stroke="var(--primary)" stroke-width="3" style="animation: scan-line 2s infinite alternate ease-in-out"/>
                    <circle cx="35" cy="40" r="3" fill="var(--secondary)" style="animation: birch-expand 2s infinite 0.5s"/>
                    <circle cx="65" cy="70" r="3" fill="var(--secondary)" style="animation: birch-expand 2s infinite 1.2s"/>
                </svg>`
            },
            {
                t: "5. Multi-Thread Scraping",
                d: "Rappresenta l'estrazione dati concorrente da Amazon, con flussi paralleli indipendenti.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 10 L20 90" stroke="currentColor" stroke-width="4" stroke-dasharray="20 10" style="animation: data-flow 1s infinite linear"/>
                    <path d="M50 10 L50 90" stroke="var(--primary)" stroke-width="4" stroke-dasharray="15 15" style="animation: data-flow 0.8s infinite linear reverse"/>
                    <path d="M80 10 L80 90" stroke="var(--secondary)" stroke-width="4" stroke-dasharray="25 5" style="animation: data-flow 1.2s infinite linear"/>
                </svg>`
            },
            {
                t: "6. JSON Dataset Merge",
                d: "Due file JSON offline che vengono uniti in un unico database centrale.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M10 20 L30 20 L30 40 L10 40 Z" fill="none" stroke="currentColor" stroke-width="3" style="animation: float-complex 3s infinite"/>
                    <path d="M70 20 L90 20 L90 40 L70 40 Z" fill="none" stroke="currentColor" stroke-width="3" style="animation: float-complex 3s infinite 1s reverse"/>
                    <path d="M30 30 Q50 50 50 60" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4" style="animation: data-flow 1s infinite linear"/>
                    <path d="M70 30 Q50 50 50 60" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="4" style="animation: data-flow 1s infinite linear"/>
                    <ellipse cx="50" cy="70" rx="20" ry="8" fill="none" stroke="var(--secondary)" stroke-width="3"/>
                    <path d="M30 70 L30 90 A20 8 0 0 0 70 90 L70 70" fill="none" stroke="var(--secondary)" stroke-width="3"/>
                </svg>`
            },
            {
                t: "7. Centroid Update (K-Means/BIRCH)",
                d: "Il centroide del cluster si aggiorna dinamicamente avvicinandosi ai dati più densi.",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="20" cy="20" r="3" fill="currentColor" class="data"/><circle cx="25" cy="30" r="3" fill="currentColor"/><circle cx="35" cy="25" r="3" fill="currentColor"/>
                    <circle cx="80" cy="80" r="3" fill="currentColor"/><circle cx="75" cy="70" r="3" fill="currentColor"/><circle cx="65" cy="75" r="3" fill="currentColor"/>
                    <polygon points="50,45 55,55 45,55" fill="var(--danger)" style="animation: centroid-move 4s infinite ease-in-out"/>
                    <line x1="25" y1="25" x2="50" y2="50" stroke="currentColor" stroke-dasharray="4" style="animation: centroid-move 4s infinite ease-in-out"/>
                </svg>`
            },
            {
                t: "8. Sunflower Drag&Drop Layout",
                d: "Simula l'UI 'Girasole' dove le card vengono organizzate circolarmente attorno al centroide.",
                c: `<svg viewBox="0 0 100 100" style="animation: spin-slow 15s linear infinite">
                    <circle cx="50" cy="50" r="15" fill="var(--primary)"/>
                    <g style="animation: pulse-node 2s infinite">
                        <circle cx="20" cy="50" r="8" fill="currentColor"/>
                        <line x1="35" y1="50" x2="28" y2="50" stroke="currentColor" stroke-width="2"/>
                    </g>
                    <g style="animation: pulse-node 2s infinite 0.5s">
                        <circle cx="80" cy="50" r="8" fill="currentColor"/>
                        <line x1="65" y1="50" x2="72" y2="50" stroke="currentColor" stroke-width="2"/>
                    </g>
                    <g style="animation: pulse-node 2s infinite 1s">
                        <circle cx="50" cy="20" r="8" fill="currentColor"/>
                        <line x1="50" y1="35" x2="50" y2="28" stroke="currentColor" stroke-width="2"/>
                    </g>
                    <g style="animation: pulse-node 2s infinite 1.5s">
                        <circle cx="50" cy="80" r="8" fill="currentColor"/>
                        <line x1="50" y1="65" x2="50" y2="72" stroke="currentColor" stroke-width="2"/>
                    </g>
                </svg>`
            },
            {
                t: "9. Cervical Collar Shape Match",
                d: "Riconoscimento della sagoma di un collare cervicale tramite contorni vettoriali.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 50 Q50 20 80 50 Q80 80 50 70 Q20 80 20 50 Z" fill="none" stroke="#334155" stroke-width="6"/>
                    <path d="M20 50 Q50 20 80 50 Q80 80 50 70 Q20 80 20 50 Z" fill="none" stroke="var(--primary)" stroke-width="3" stroke-dasharray="200" style="animation: draw-path 3s infinite ease-out"/>
                    <circle cx="50" cy="50" r="4" fill="var(--secondary)" style="animation: birch-expand 1.5s infinite"/>
                </svg>`
            },
            {
                t: "10. Image Hash Compare",
                d: "Confronto tra Hash MD5/Color per trovare duplicati esatti. Bit stream.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="10" y="20" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.1s"/>
                    <rect x="25" y="20" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.2s"/>
                    <rect x="40" y="20" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.3s"/>
                    <rect x="10" y="70" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.1s"/>
                    <rect x="25" y="70" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.2s"/>
                    <rect x="40" y="70" width="10" height="10" rx="2" style="animation: hash-compare 1s infinite 0.3s"/>
                    <path d="M60 45 L90 45 M75 30 L90 45 L75 60" fill="none" stroke="var(--secondary)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" style="animation: birch-expand 1s infinite 0.5s"/>
                </svg>`
            },
            {
                t: "11. Rate Limit Proxy Deflector",
                d: "Il bot evita i blocchi 403 di Amazon (o GitHub) rimbalzandoli con proxy.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M70 20 Q50 50 70 80" fill="none" stroke="var(--primary)" stroke-width="4" style="animation: proxy-deflect 2s infinite ease-in-out"/>
                    <circle cx="90" cy="50" r="10" fill="var(--secondary)"/>
                    <line x1="10" y1="50" x2="60" y2="50" stroke="var(--danger)" stroke-width="4" stroke-dasharray="10 10" style="animation: data-flow 1s infinite linear"/>
                </svg>`
            },
            {
                t: "12. False Positive Radar",
                d: "Radar che scansiona lo spazio vettoriale in cerca di anomalie (cuscini mascherati da collari).",
                c: `<svg viewBox="0 0 100 100" style="overflow:hidden">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="#334155" stroke-width="2"/>
                    <circle cx="50" cy="50" r="20" fill="none" stroke="#334155" stroke-width="2"/>
                    <line x1="50" y1="50" x2="50" y2="10" stroke="var(--primary)" stroke-width="2" style="transform-origin: 50px 50px; animation: spin-slow 3s linear infinite"/>
                    <circle cx="70" cy="30" r="5" fill="var(--danger)" style="animation: radar-ping 3s infinite"/>
                    <circle cx="30" cy="70" r="4" fill="var(--secondary)"/>
                </svg>`
            },
            {
                t: "13. Parallel Pipeline Execution",
                d: "pipeline.run() che lancia moduli NLP, Vision e Clustering simultaneamente.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="20" y="20" width="60" height="10" rx="5" fill="#334155"/>
                    <rect x="20" y="20" width="60" height="10" rx="5" fill="var(--primary)" style="animation: draw-path 2s infinite ease-out; stroke-dasharray: 60; stroke-dashoffset: 60;"/>
                    <rect x="20" y="45" width="60" height="10" rx="5" fill="#334155"/>
                    <rect x="20" y="45" width="60" height="10" rx="5" fill="var(--secondary)" style="animation: draw-path 2s infinite ease-out 0.5s; stroke-dasharray: 60; stroke-dashoffset: 60;"/>
                    <rect x="20" y="70" width="60" height="10" rx="5" fill="#334155"/>
                    <rect x="20" y="70" width="60" height="10" rx="5" fill="var(--danger)" style="animation: draw-path 2s infinite ease-out 1s; stroke-dasharray: 60; stroke-dashoffset: 60;"/>
                </svg>`
            },
            {
                t: "14. Memory Optimizer",
                d: "De-allocazione dei tensori non usati per non intasare la RAM (come dicevi per le img).",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="20" y="20" width="20" height="20" rx="4" fill="var(--danger)" style="animation: birch-expand 2s infinite alternate"/>
                    <rect x="50" y="20" width="20" height="20" rx="4" fill="var(--secondary)"/>
                    <rect x="20" y="50" width="20" height="20" rx="4" fill="var(--secondary)"/>
                    <rect x="50" y="50" width="20" height="20" rx="4" fill="currentColor"/>
                    <path d="M30 30 L40 40 M30 40 L40 30" stroke="var(--bg)" stroke-width="3" style="animation: birch-expand 2s infinite alternate"/>
                </svg>`
            },
            {
                t: "15. Graph Neural Network",
                d: "I nodi si scambiano embeddings (vettori colorati lungo gli spigoli).",
                c: `<svg viewBox="0 0 100 100">
                    <line x1="20" y1="50" x2="80" y2="50" stroke="#334155" stroke-width="3"/>
                    <circle cx="50" cy="50" r="4" fill="var(--primary)" style="animation: data-flow 2s infinite; stroke-dasharray: 60; stroke-dashoffset: 60; transform: translateX(-30px)"/>
                    <circle cx="20" cy="50" r="10" fill="currentColor"/>
                    <circle cx="80" cy="50" r="10" fill="currentColor"/>
                    <circle cx="50" cy="20" r="10" fill="currentColor"/>
                    <line x1="20" y1="50" x2="50" y2="20" stroke="#334155" stroke-width="3"/>
                </svg>`
            },
            // Genero altre 15 varianti specifiche riusando primitive e CSS avanzato
            {
                t: "16. Text Feature Extraction (NLP)",
                d: "Trasforma stringhe di testo (Keyword) in vettori numerici (Array).",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M10 30 L40 30 M10 50 L30 50 M10 70 L45 70" stroke="currentColor" stroke-width="4" stroke-linecap="round"/>
                    <path d="M60 20 L90 20 L90 80 L60 80 Z" fill="none" stroke="var(--primary)" stroke-width="3"/>
                    <circle cx="75" cy="35" r="3" fill="var(--secondary)" style="animation: pulse-node 1s infinite"/>
                    <circle cx="75" cy="50" r="3" fill="var(--secondary)" style="animation: pulse-node 1s infinite 0.2s"/>
                    <circle cx="75" cy="65" r="3" fill="var(--secondary)" style="animation: pulse-node 1s infinite 0.4s"/>
                    <path d="M45 50 L55 50" stroke="currentColor" stroke-width="3" stroke-dasharray="2" style="animation: data-flow 1s infinite linear"/>
                </svg>`
            },
            {
                t: "17. Vector Space Scatter",
                d: "Visualizzazione a 3 dimensioni dei prodotti raggruppati.",
                c: `<svg viewBox="0 0 100 100">
                    <line x1="20" y1="80" x2="80" y2="80" stroke="#475569" stroke-width="2"/>
                    <line x1="20" y1="80" x2="20" y2="20" stroke="#475569" stroke-width="2"/>
                    <circle cx="70" cy="40" r="4" fill="var(--primary)" style="animation: float-complex 4s infinite"/>
                    <circle cx="75" cy="35" r="3" fill="var(--primary)" style="animation: float-complex 4s infinite 0.5s"/>
                    <circle cx="35" cy="65" r="4" fill="var(--danger)" style="animation: float-complex 3s infinite 1s"/>
                    <circle cx="40" cy="70" r="3" fill="var(--danger)" style="animation: float-complex 3s infinite 1.5s"/>
                </svg>`
            },
            {
                t: "18. Thumbnail Async Fetcher",
                d: "Simula il fix che abbiamo fatto per caricare le immagini asincronamente senza bloccare l'UI.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="20" y="20" width="60" height="60" rx="5" fill="none" stroke="currentColor" stroke-width="4"/>
                    <circle cx="50" cy="50" r="15" fill="none" stroke="var(--primary)" stroke-width="4" stroke-dasharray="70" style="animation: spin-slow 1s linear infinite"/>
                    <path d="M30 80 L50 50 L80 80" fill="none" stroke="currentColor" stroke-width="4" style="opacity: 0.5"/>
                </svg>`
            },
            {
                t: "19. Background Cron Job",
                d: "Task ricorrente che gira ogni tot minuti per scansionare nuovi dati (Amazon Scheduler).",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="6"/>
                    <line x1="50" y1="50" x2="50" y2="25" stroke="var(--primary)" stroke-width="4" stroke-linecap="round" style="transform-origin: 50px 50px; animation: spin-slow 4s steps(60) infinite"/>
                    <line x1="50" y1="50" x2="70" y2="50" stroke="var(--secondary)" stroke-width="4" stroke-linecap="round" style="transform-origin: 50px 50px; animation: spin-slow 48s linear infinite"/>
                    <circle cx="50" cy="50" r="6" fill="currentColor"/>
                </svg>`
            },
            {
                t: "20. Model Checkpoint Save",
                d: "Il cervello dell'AI che salva lo stato dell'apprendimento su disco (.pkl o JSON).",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M25 45 Q25 20 50 20 Q75 20 75 45 Q85 45 85 60 Q85 80 65 80 L35 80 Q15 80 15 60 Q15 45 25 45 Z" fill="none" stroke="currentColor" stroke-width="4"/>
                    <path d="M50 40 L50 70 M40 60 L50 70 L60 60" fill="none" stroke="var(--secondary)" stroke-width="4" stroke-linecap="round" style="animation: float-complex 2s infinite"/>
                </svg>`
            },
            {
                t: "21. API Webhook Signal",
                d: "Comunicazione tra Flask backend e Frontend (segnali WebSocket/SSE).",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="20" cy="50" r="10" fill="currentColor"/>
                    <circle cx="80" cy="50" r="10" fill="var(--primary)"/>
                    <path d="M35 50 Q50 30 65 50" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="10" style="animation: data-flow 1s infinite linear"/>
                    <path d="M65 50 Q50 70 35 50" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="10" style="animation: data-flow 1s infinite linear"/>
                </svg>`
            },
            {
                t: "22. HTML Parser (BeautifulSoup)",
                d: "Estrazione del DOM di Amazon (albero HTML) in nodi utili.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 20 L40 50 L20 80" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>
                    <path d="M80 20 L60 50 L80 80" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>
                    <line x1="50" y1="10" x2="50" y2="90" stroke="var(--primary)" stroke-width="4" style="animation: scan-line 2s infinite"/>
                </svg>`
            },
            {
                t: "23. Confidence Score Meter",
                d: "Strumento di gauge che indica il 98% di confidenza del matching.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 70 A 40 40 0 1 1 80 70" fill="none" stroke="#334155" stroke-width="10" stroke-linecap="round"/>
                    <path d="M20 70 A 40 40 0 0 1 70 35" fill="none" stroke="var(--secondary)" stroke-width="10" stroke-linecap="round" style="animation: draw-path 2s ease-out forwards"/>
                    <line x1="50" y1="70" x2="65" y2="40" stroke="currentColor" stroke-width="4" stroke-linecap="round" style="transform-origin: 50px 70px; animation: magic-sparkle 1s ease-out forwards"/>
                    <circle cx="50" cy="70" r="6" fill="currentColor"/>
                </svg>`
            },
            {
                t: "24. Error Boundary Catch",
                d: "Modulo che intercetta un'eccezione (es. Timeout) e la isola in sicurezza.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="20" y="20" width="60" height="60" rx="10" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="10 5" style="animation: spin-slow 10s linear infinite"/>
                    <path d="M40 40 L60 60 M60 40 L40 60" stroke="var(--danger)" stroke-width="6" stroke-linecap="round" style="animation: pulse-node 1.5s infinite"/>
                </svg>`
            },
            {
                t: "25. Semantic Tokenizer",
                d: "Divide una frase 'Collare cervicale morbido' nei suoi token base.",
                c: `<svg viewBox="0 0 100 100">
                    <rect x="10" y="40" width="80" height="20" rx="5" fill="none" stroke="currentColor" stroke-width="4"/>
                    <line x1="35" y1="30" x2="35" y2="70" stroke="var(--primary)" stroke-width="4" style="animation: birch-expand 1s infinite alternate"/>
                    <line x1="65" y1="30" x2="65" y2="70" stroke="var(--primary)" stroke-width="4" style="animation: birch-expand 1s infinite alternate 0.5s"/>
                </svg>`
            },
            {
                t: "26. High-D Vector Compression",
                d: "Riduzione della dimensionalità (PCA / t-SNE) dei vettori SIFT.",
                c: `<svg viewBox="0 0 100 100">
                    <polygon points="50,10 90,30 90,70 50,90 10,70 10,30" fill="none" stroke="currentColor" stroke-width="2"/>
                    <polygon points="50,30 70,45 70,75 50,90 30,75 30,45" fill="none" stroke="var(--primary)" stroke-width="3" style="animation: pulse-node 2s infinite alternate"/>
                    <line x1="10" y1="30" x2="50" y2="50" stroke="currentColor" stroke-width="1"/><line x1="90" y1="30" x2="50" y2="50" stroke="currentColor" stroke-width="1"/>
                </svg>`
            },
            {
                t: "27. Live Report Writer",
                d: "Generazione statica del report HTML (report.html e categorize.html).",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M25 15 L55 15 L75 35 L75 85 L25 85 Z" fill="none" stroke="currentColor" stroke-width="4"/>
                    <path d="M55 15 L55 35 L75 35" fill="none" stroke="currentColor" stroke-width="4"/>
                    <line x1="35" y1="50" x2="65" y2="50" stroke="var(--primary)" stroke-width="4" stroke-linecap="round" style="animation: draw-path 1.5s infinite"/>
                    <line x1="35" y1="65" x2="55" y2="65" stroke="var(--primary)" stroke-width="4" stroke-linecap="round" style="animation: draw-path 1.5s infinite 0.5s"/>
                </svg>`
            },
            {
                t: "28. SIFT Orientation Histogram",
                d: "Calcolo della rotazione e scala dei keypoints visivi per invarianza.",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="4"/>
                    <path d="M50 50 L50 20 M50 20 L45 30 M50 20 L55 30" stroke="var(--primary)" stroke-width="4" style="transform-origin: 50px 50px; animation: spin-slow 3s infinite cubic-bezier(0.68, -0.55, 0.27, 1.55)"/>
                    <line x1="50" y1="50" x2="80" y2="50" stroke="var(--secondary)" stroke-width="4" style="transform-origin: 50px 50px; animation: spin-slow 5s infinite linear"/>
                </svg>`
            },
            {
                t: "29. Distributed Nodes",
                d: "Rappresentazione di un'architettura a micro-moduli (Vision + NLP + Scraper).",
                c: `<svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="8" fill="var(--primary)" style="animation: pulse-node 1.5s infinite"/>
                    <circle cx="20" cy="20" r="5" fill="currentColor"/><circle cx="80" cy="20" r="5" fill="currentColor"/>
                    <circle cx="20" cy="80" r="5" fill="currentColor"/><circle cx="80" cy="80" r="5" fill="currentColor"/>
                    <line x1="25" y1="25" x2="45" y2="45" stroke="currentColor" stroke-width="2" style="animation: dash 1s infinite alternate"/><line x1="75" y1="25" x2="55" y2="45" stroke="currentColor" stroke-width="2" style="animation: dash 1s infinite alternate"/>
                    <line x1="25" y1="75" x2="45" y2="55" stroke="currentColor" stroke-width="2" style="animation: dash 1s infinite alternate"/><line x1="75" y1="75" x2="55" y2="55" stroke="currentColor" stroke-width="2" style="animation: dash 1s infinite alternate"/>
                </svg>`
            },
            {
                t: "30. Amazon Smile Optimizer",
                d: "Ricerca e ottimizzazione sull'inventario Amazon.",
                c: `<svg viewBox="0 0 100 100">
                    <path d="M20 60 Q50 90 80 60" fill="none" stroke="#f59e0b" stroke-width="8" stroke-linecap="round"/>
                    <path d="M75 75 L85 60 L90 80 Z" fill="#f59e0b" style="animation: float-complex 2s infinite"/>
                    <circle cx="35" cy="40" r="12" fill="none" stroke="currentColor" stroke-width="4" style="animation: pulse-node 2s infinite"/>
                    <circle cx="65" cy="40" r="12" fill="none" stroke="currentColor" stroke-width="4" style="animation: pulse-node 2s infinite 1s"/>
                </svg>`
            }
        ];

        const grid = document.getElementById('grid');
        complexSvgs.forEach(s => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = \`
                <div class="svg-container">\${s.c}</div>
                <div class="title">\${s.t}</div>
                <div class="desc">\${s.d}</div>
            \`;
            grid.appendChild(card);
        });
    </script>
</body>
</html>
"""

output_path = rstr(Path.home() / "amazon_search", "svg_gallery_complex.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
