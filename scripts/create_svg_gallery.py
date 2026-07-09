import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>30 Animazioni SVG - Amazon UI</title>
    <style>
        :root {
            --primary: #4BB543; /* Colore modificabile dal Color Picker */
            --bg: #1e1e1e;
            --card-bg: #2d2d2d;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: #fff;
            margin: 0;
            padding: 2rem;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #444;
        }
        .color-picker {
            display: flex;
            align-items: center;
            gap: 10px;
            background: var(--card-bg);
            padding: 10px 20px;
            border-radius: 8px;
        }
        input[type="color"] {
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            background: transparent;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 1.5rem;
        }
        .card {
            background: var(--card-bg);
            border-radius: 12px;
            padding: 2rem 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 1.5rem;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        }
        .card-name {
            font-size: 0.9rem;
            color: #aaa;
            text-align: center;
        }
        
        /* MAGIC COLOR CLASS - all SVGs will use this */
        .svg-container {
            width: 60px;
            height: 60px;
            color: var(--primary); /* L'SVG userà currentColor per ereditare questo */
        }
        svg {
            width: 100%;
            height: 100%;
        }

        /* --- GLOBAL KEYFRAMES FOR SVGS --- */
        @keyframes spin { 100% { transform: rotate(360deg); } }
        @keyframes pulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(0.6); opacity: 0.5; } }
        @keyframes ping { 0% { transform: scale(0.8); opacity: 1; } 100% { transform: scale(2); opacity: 0; } }
        @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-25%); } }
        @keyframes wave { 0%, 100% { height: 10px; } 50% { height: 40px; } }
        @keyframes dash { to { stroke-dashoffset: 0; } }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
        @keyframes cluster-node { 0%, 100% { cx: 25; cy: 25; } 50% { cx: 75; cy: 75; } }
        @keyframes magic-sparkle { 0%, 100% { transform: scale(0) rotate(0deg); opacity: 0; } 50% { transform: scale(1) rotate(180deg); opacity: 1; } }
    </style>
</head>
<body>

    <div class="header">
        <div>
            <h1>30 Animazioni SVG Professionali</h1>
            <p>100% Lightweight, Vanilla CSS. Nessun JS pesante. Adatte per Clustering, AI, UI e Loader.</p>
        </div>
        <div class="color-picker">
            <label for="color">Cambia Colore Globale:</label>
            <input type="color" id="color" value="#4BB543">
        </div>
    </div>

    <div class="grid" id="svg-grid">
        <!-- SVG injected by JS for cleanliness in HTML -->
    </div>

    <script>
        // Array of 30 distinct SVGs using 'currentColor' to be 100% modifiable
        const svgs = [
            {
                name: "1. Match Check",
                code: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="8" stroke-dasharray="251" stroke-dashoffset="251" style="animation: dash 0.6s ease forwards;"/><path d="M30 50 L45 65 L70 35" fill="none" stroke="currentColor" stroke-width="8" stroke-dasharray="100" stroke-dashoffset="100" style="animation: dash 0.4s ease 0.5s forwards;"/></svg>`
            },
            {
                name: "2. Magic Noise Purge",
                code: `<svg viewBox="0 0 100 100" style="overflow: visible"><path d="M20 80 L80 20" stroke="currentColor" stroke-width="8" stroke-linecap="round"/><path d="M70 10 L80 0 M90 20 L100 30 M70 30 L60 40" stroke="currentColor" stroke-width="4" stroke-linecap="round" style="transform-origin: 80px 20px; animation: magic-sparkle 1.5s infinite;"/></svg>`
            },
            {
                name: "3. AI Clustering Nodes",
                code: `<svg viewBox="0 0 100 100"><circle cx="30" cy="30" r="10" fill="currentColor" style="animation: pulse 2s infinite;"/><circle cx="70" cy="70" r="10" fill="currentColor" style="animation: pulse 2s infinite 1s;"/><line x1="30" y1="30" x2="70" y2="70" stroke="currentColor" stroke-width="4" stroke-dasharray="10" style="animation: dash 2s linear infinite;"/></svg>`
            },
            {
                name: "4. Neural Network",
                code: `<svg viewBox="0 0 100 100"><polygon points="50,10 90,50 50,90 10,50" fill="none" stroke="currentColor" stroke-width="4" style="transform-origin: center; animation: spin 4s linear infinite;"/><circle cx="50" cy="50" r="15" fill="currentColor" style="animation: pulse 1s infinite;"/></svg>`
            },
            {
                name: "5. Active Learning",
                code: `<svg viewBox="0 0 100 100"><path d="M20 50 Q50 10 80 50 T20 50" fill="none" stroke="currentColor" stroke-width="6" style="stroke-dasharray: 200; animation: dash 2s infinite linear;"/><circle cx="50" cy="50" r="10" fill="currentColor"/></svg>`
            },
            {
                name: "6. Searching / Radar",
                code: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="4"/><circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="4" style="animation: ping 2s infinite ease-out;"/></svg>`
            },
            {
                name: "7. Processing Equalizer",
                code: `<svg viewBox="0 0 100 100"><rect x="20" y="30" width="12" height="40" fill="currentColor" style="animation: wave 1s infinite ease-in-out;"/><rect x="44" y="30" width="12" height="40" fill="currentColor" style="animation: wave 1s infinite ease-in-out 0.2s;"/><rect x="68" y="30" width="12" height="40" fill="currentColor" style="animation: wave 1s infinite ease-in-out 0.4s;"/></svg>`
            },
            {
                name: "8. Data Merge (Drag&Drop)",
                code: `<svg viewBox="0 0 100 100"><path d="M30 20 L30 80 L70 80 L70 20 Z" fill="none" stroke="currentColor" stroke-width="6"/><path d="M50 40 L50 60 M40 50 L60 50" stroke="currentColor" stroke-width="6" style="transform-origin: center; animation: spin 2s ease infinite;"/></svg>`
            },
            {
                name: "9. SIFT Feature Match",
                code: `<svg viewBox="0 0 100 100"><circle cx="20" cy="50" r="10" fill="currentColor"/><circle cx="80" cy="50" r="10" fill="currentColor"/><line x1="30" y1="50" x2="70" y2="50" stroke="currentColor" stroke-width="4" stroke-dasharray="80" stroke-dashoffset="80" style="animation: dash 1s infinite alternate;"/></svg>`
            },
            {
                name: "10. Eye Scanner (Vision)",
                code: `<svg viewBox="0 0 100 100"><path d="M10 50 Q50 10 90 50 Q50 90 10 50" fill="none" stroke="currentColor" stroke-width="6"/><circle cx="50" cy="50" r="15" fill="currentColor" style="animation: pulse 1.5s infinite;"/></svg>`
            },
            { name: "11. Orbit Loader", code: `<svg viewBox="0 0 100 100" style="animation: spin 2s linear infinite;"><circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="8" stroke-dasharray="180" stroke-linecap="round"/></svg>` },
            { name: "12. Double Ring", code: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="120" style="transform-origin: center; animation: spin 2s linear infinite;"/><circle cx="50" cy="50" r="25" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="60" style="transform-origin: center; animation: spin 1.5s linear infinite reverse;"/></svg>` },
            { name: "13. Floating Card", code: `<svg viewBox="0 0 100 100"><rect x="25" y="20" width="50" height="60" rx="8" fill="none" stroke="currentColor" stroke-width="6" style="animation: float 3s ease-in-out infinite;"/><line x1="40" y1="40" x2="60" y2="40" stroke="currentColor" stroke-width="4" style="animation: float 3s ease-in-out infinite;"/></svg>` },
            { name: "14. Database Sync", code: `<svg viewBox="0 0 100 100"><ellipse cx="50" cy="30" rx="30" ry="10" fill="none" stroke="currentColor" stroke-width="6"/><path d="M20 30 L20 70 A30 10 0 0 0 80 70 L80 30" fill="none" stroke="currentColor" stroke-width="6"/><path d="M20 50 A30 10 0 0 0 80 50" fill="none" stroke="currentColor" stroke-width="6" style="animation: blink 1s infinite;"/></svg>` },
            { name: "15. Pulse Dots", code: `<svg viewBox="0 0 100 100"><circle cx="20" cy="50" r="10" fill="currentColor" style="animation: pulse 1s infinite;"/><circle cx="50" cy="50" r="10" fill="currentColor" style="animation: pulse 1s infinite 0.2s;"/><circle cx="80" cy="50" r="10" fill="currentColor" style="animation: pulse 1s infinite 0.4s;"/></svg>` },
            { name: "16. Bouncing Ball", code: `<svg viewBox="0 0 100 100"><circle cx="50" cy="80" r="15" fill="currentColor" style="animation: bounce 0.5s infinite alternate cubic-bezier(0.5, 0, 1, 0.5);"/></svg>` },
            { name: "17. Expanding Hexagon", code: `<svg viewBox="0 0 100 100"><polygon points="50,10 85,30 85,70 50,90 15,70 15,30" fill="none" stroke="currentColor" stroke-width="6" style="transform-origin: center; animation: pulse 2s infinite;"/></svg>` },
            { name: "18. Sifting Filter", code: `<svg viewBox="0 0 100 100"><path d="M10 20 L90 20 L60 50 L60 80 L40 90 L40 50 Z" fill="none" stroke="currentColor" stroke-width="6"/><circle cx="50" cy="35" r="5" fill="currentColor" style="animation: float 1s infinite;"/></svg>` },
            { name: "19. Trash Noise", code: `<svg viewBox="0 0 100 100"><path d="M30 30 L70 30 M40 30 L40 20 L60 20 L60 30 M35 30 L40 80 L60 80 L65 30" fill="none" stroke="currentColor" stroke-width="6"/><line x1="45" y1="45" x2="45" y2="65" stroke="currentColor" stroke-width="4" style="animation: blink 1s infinite;"/><line x1="55" y1="45" x2="55" y2="65" stroke="currentColor" stroke-width="4" style="animation: blink 1s infinite 0.5s;"/></svg>` },
            { name: "20. Hourglass", code: `<svg viewBox="0 0 100 100" style="animation: spin 3s infinite steps(1);"><path d="M30 20 L70 20 L50 50 L70 80 L30 80 L50 50 Z" fill="none" stroke="currentColor" stroke-width="6"/></svg>` },
            { name: "21. Signal Bars", code: `<svg viewBox="0 0 100 100"><rect x="20" y="60" width="10" height="20" fill="currentColor" style="animation: blink 1s infinite;"/><rect x="45" y="40" width="10" height="40" fill="currentColor" style="animation: blink 1s infinite 0.2s;"/><rect x="70" y="20" width="10" height="60" fill="currentColor" style="animation: blink 1s infinite 0.4s;"/></svg>` },
            { name: "22. Heartbeat", code: `<svg viewBox="0 0 100 100"><path d="M10 50 L30 50 L40 20 L60 80 L70 50 L90 50" fill="none" stroke="currentColor" stroke-width="6" stroke-linejoin="round" stroke-dasharray="300" stroke-dashoffset="300" style="animation: dash 1.5s linear infinite;"/></svg>` },
            { name: "23. Refresh Arrows", code: `<svg viewBox="0 0 100 100" style="transform-origin: center; animation: spin 2s linear infinite;"><path d="M30 30 A 30 30 0 0 1 80 50 L95 40 M70 70 A 30 30 0 0 1 20 50 L5 60" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/></svg>` },
            { name: "24. Document Scan", code: `<svg viewBox="0 0 100 100"><rect x="20" y="10" width="60" height="80" rx="5" fill="none" stroke="currentColor" stroke-width="6"/><line x1="10" y1="50" x2="90" y2="50" stroke="currentColor" stroke-width="4" style="animation: float 2s linear infinite;"/></svg>` },
            { name: "25. Cloud Upload", code: `<svg viewBox="0 0 100 100"><path d="M30 60 A20 20 0 0 1 30 20 A30 30 0 0 1 80 30 A20 20 0 0 1 80 70 L30 70" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/><line x1="55" y1="70" x2="55" y2="40" stroke="currentColor" stroke-width="6"/><path d="M40 55 L55 40 L70 55" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" style="animation: float 1s infinite;"/></svg>` },
            { name: "26. Shield Security", code: `<svg viewBox="0 0 100 100"><path d="M50 10 L20 25 L20 50 Q20 80 50 90 Q80 80 80 50 L80 25 Z" fill="none" stroke="currentColor" stroke-width="6"/><path d="M40 50 L50 60 L65 40" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-dasharray="50" stroke-dashoffset="50" style="animation: dash 1s infinite alternate;"/></svg>` },
            { name: "27. Infinity Loop", code: `<svg viewBox="0 0 100 100"><path d="M25 50 A 15 15 0 1 1 50 50 A 15 15 0 1 0 75 50 A 15 15 0 1 1 50 50 A 15 15 0 1 0 25 50" fill="none" stroke="currentColor" stroke-width="6" stroke-dasharray="250" stroke-dashoffset="250" style="animation: dash 2s linear infinite;"/></svg>` },
            { name: "28. Magnifying Glass", code: `<svg viewBox="0 0 100 100"><circle cx="40" cy="40" r="25" fill="none" stroke="currentColor" stroke-width="8"/><line x1="60" y1="60" x2="85" y2="85" stroke="currentColor" stroke-width="12" stroke-linecap="round"/><circle cx="40" cy="40" r="10" fill="currentColor" style="animation: ping 1.5s infinite;"/></svg>` },
            { name: "29. Speedometer", code: `<svg viewBox="0 0 100 100"><path d="M20 70 A 40 40 0 1 1 80 70" fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round"/><line x1="50" y1="70" x2="80" y2="40" stroke="currentColor" stroke-width="6" stroke-linecap="round" style="transform-origin: 50px 70px; animation: spin 2s infinite alternate ease-in-out;"/></svg>` },
            { name: "30. Particle Burst", code: `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="5" fill="currentColor"/><circle cx="50" cy="20" r="6" fill="currentColor" style="transform-origin:50px 50px; animation: spin 2s infinite;"/><circle cx="80" cy="50" r="4" fill="currentColor" style="transform-origin:50px 50px; animation: spin 1.5s infinite reverse;"/><circle cx="20" cy="50" r="8" fill="currentColor" style="transform-origin:50px 50px; animation: spin 3s infinite;"/></svg>` }
        ];

        const grid = document.getElementById('svg-grid');
        
        svgs.forEach(svg => {
            const card = document.createElement('div');
            card.className = 'card';
            card.title = "Clicca per copiare il codice SVG";
            
            const container = document.createElement('div');
            container.className = 'svg-container';
            container.innerHTML = svg.code;
            
            const name = document.createElement('div');
            name.className = 'card-name';
            name.textContent = svg.name;
            
            card.appendChild(container);
            card.appendChild(name);
            
            // Click to copy code
            card.onclick = () => {
                navigator.clipboard.writeText(svg.code).then(() => {
                    const oldText = name.textContent;
                    name.textContent = "COPIATO!";
                    name.style.color = "var(--primary)";
                    setTimeout(() => {
                        name.textContent = oldText;
                        name.style.color = "#aaa";
                    }, 1500);
                });
            };
            
            grid.appendChild(card);
        });

        // Color Picker Logic
        document.getElementById('color').addEventListener('input', (e) => {
            document.documentElement.style.setProperty('--primary', e.target.value);
        });
    </script>
</body>
</html>
"""

output_path = r"C:\Users\Gilberto Bizzo\amazon_search\svg_gallery.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
