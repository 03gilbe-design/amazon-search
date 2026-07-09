from pathlib import Path
import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Search - Animazioni degli Agenti</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 2rem; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; border: 1px solid #334155; }
        .svg-container { width: 100%; max-width: 800px; margin: 0 auto; }
        svg { width: 100%; height: auto; }
        
        @keyframes type { from { width: 0; } to { width: 100%; } }
        .line1 { overflow: hidden; white-space: nowrap; animation: type 1s steps(40, end); }
        .line2 { opacity: 0; animation: fadeIn 0.1s 1s forwards; }
        .line3 { opacity: 0; animation: fadeIn 0.1s 2s forwards; }
        .line4 { opacity: 0; animation: fadeIn 0.1s 3s forwards; }
        .line5 { opacity: 0; animation: fadeIn 0.1s 4s forwards; }
        .line6 { opacity: 0; animation: fadeIn 0.1s 5s forwards; }
        @keyframes fadeIn { to { opacity: 1; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Opere del Team degli Agenti</h1>
        <p>I 5 Agenti hanno ideato, validato e programmato queste scene esclusive.</p>
        
        <div class="card">
            <h2>1. Il Cluster a Girasole (Creator 2)</h2>
            <p>Un'animazione SVG complessa in cui le schede (immagini finte) volano dallo spazio 3D e si aggregano per formare un cluster compatto al centro. Perfetto per illustrare l'output del clustering!</p>
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <rect width="800" height="600" fill="#0f172a" rx="10"/>
  <g transform="translate(400, 300)">
    <g>
      <animateTransform attributeName="transform" type="translate" values="-400,-300; -40,-30" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="-90; -15" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
        <rect x="-60" y="-80" width="120" height="160" fill="#3b82f6" rx="4" stroke="#ffffff" stroke-width="4" />
      </g>
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate" values="400,-300; 40,-40" dur="1.7s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="90; 12" dur="1.7s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
        <rect x="-70" y="-50" width="140" height="100" fill="#10b981" rx="4" stroke="#ffffff" stroke-width="4" />
      </g>
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate" values="-400,300; -50,40" dur="1.9s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="-60; -8" dur="1.9s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
        <rect x="-60" y="-60" width="120" height="120" fill="#f59e0b" rx="4" stroke="#ffffff" stroke-width="4" />
      </g>
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate" values="400,300; 45,35" dur="2.1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="120; 22" dur="2.1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
        <rect x="-50" y="-70" width="100" height="140" fill="#8b5cf6" rx="4" stroke="#ffffff" stroke-width="4" />
      </g>
    </g>
    <g>
      <animateTransform attributeName="transform" type="translate" values="0,400; 0,0" dur="2.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
      <g>
        <animateTransform attributeName="transform" type="rotate" values="45; -3" dur="2.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.25 0.1 0.25 1"/>
        <rect x="-80" y="-60" width="160" height="120" fill="#ef4444" rx="4" stroke="#ffffff" stroke-width="4" style="filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.5));" />
      </g>
    </g>
  </g>
</svg>
            </div>
        </div>

        <div class="card">
            <h2>2. Terminale Interattivo: Fallback Proxy (Creator 1)</h2>
            <p>Un SVG che simula il terminale PowerShell mentre lo script affronta un blocco di Amazon (403) e cambia proxy automaticamente.</p>
            <div class="svg-container">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400" width="100%" height="100%">
                    <rect width="800" height="400" rx="10" fill="#0a0a0a" stroke="#334155" stroke-width="2"/>
                    <circle cx="20" cy="20" r="6" fill="#ff5f56"/>
                    <circle cx="40" cy="20" r="6" fill="#ffbd2e"/>
                    <circle cx="60" cy="20" r="6" fill="#27c93f"/>
                    <g font-family="monospace" font-size="16" transform="translate(20, 60)">
                        <text y="0" fill="#f8fafc" class="line1">> python app.py --search "collare cervicale"</text>
                        <text y="30" fill="#3b82f6" class="line2">[*] Inizializzazione pipeline SIFT/BIRCH...</text>
                        <text y="60" fill="#ef4444" font-weight="bold" class="line3">[!] ERRORE: HTTP 403 Forbidden - Rate Limit Amazon raggiunto.</text>
                        <text y="90" fill="#eab308" class="line4">[*] Fallback attivato: Rotazione Proxy in corso (192.168.X.X)...</text>
                        <text y="120" fill="#10b981" class="line5">[+] Connessione stabilita. Nuova sessione pulita.</text>
                        <text y="150" fill="#3b82f6" class="line6">[*] Estrazione dati: 229 prodotti salvati in amazon_search_offline.json.</text>
                    </g>
                </svg>
            </div>
        </div>
    </div>
</body>
</html>
"""

output_path = rstr(Path.home() / "amazon_search", "agent_animations.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
