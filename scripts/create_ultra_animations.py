import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Search - Ultra Premium Flat Design</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }
        .header { text-align: center; margin-bottom: 3rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 3rem; max-width: 1400px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 20px; padding: 3rem; border: 1px solid #334155; display: flex; flex-direction: column; align-items: center; text-align: center; box-shadow: 0 20px 40px -10px rgba(0,0,0,0.5); }
        .svg-container { width: 100%; max-width: 350px; height: 350px; margin-bottom: 2rem; background: #0f172a; border-radius: 50%; display: flex; justify-content: center; align-items: center; box-shadow: inset 0 10px 20px rgba(0,0,0,0.5); }
        svg { width: 100%; height: 100%; overflow: visible; }
        h2 { font-size: 1.5rem; margin-bottom: 1rem; color: #f8fafc; }
        p { font-size: 1rem; color: #94a3b8; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Nuovo Set: Ultra Premium Flat Design</h1>
        <p>Niente terminali. Forme morbidissime, linee smussate (round caps), dissolvenze e transizioni di opacità avanzate.</p>
    </div>
    <div class="grid" id="grid"></div>

    <script>
        const animations = [
            {
                t: "1. The Fluid Sort (Grid Alignment)",
                d: "Una griglia disordinata di forme arrotondate (rounded rectangles) che scivola con transizioni dolcissime. I blocchi errati sfumano via (opacità a 0), mentre gli altri si riordinano perfettamente.",
                c: `<svg viewBox="0 0 400 400">
                    <defs>
                        <!-- Forme con bordi estremamente smussati -->
                        <style>
                            .block { rx: 20; ry: 20; stroke-width: 0; }
                            .anim-fade { animation: fadeOut 4s infinite ease-in-out; }
                            @keyframes fadeOut { 0%, 10% { opacity: 1; } 40%, 60% { opacity: 0; transform: scale(0.8); } 90%, 100% { opacity: 1; transform: scale(1); } }
                            @keyframes slideX { 0%, 20% { transform: translateX(0); } 40%, 60% { transform: translateX(110px); } 80%, 100% { transform: translateX(0); } }
                            @keyframes slideY { 0%, 20% { transform: translateY(0); } 40%, 60% { transform: translateY(-110px); } 80%, 100% { transform: translateY(0); } }
                            @keyframes slideBoth { 0%, 20% { transform: translate(0, 0); } 40%, 60% { transform: translate(-110px, 110px); } 80%, 100% { transform: translate(0, 0); } }
                        </style>
                    </defs>
                    <g transform="translate(45, 45)">
                        <!-- Row 1 -->
                        <rect x="0" y="0" width="90" height="90" fill="#3b82f6" class="block" style="animation: slideX 4s infinite ease-in-out;"/>
                        <rect x="110" y="0" width="90" height="90" fill="#ef4444" class="block anim-fade" style="transform-origin: 155px 45px;"/>
                        <rect x="220" y="0" width="90" height="90" fill="#3b82f6" class="block" style="animation: slideBoth 4s infinite ease-in-out;"/>
                        
                        <!-- Row 2 -->
                        <rect x="0" y="110" width="90" height="90" fill="#10b981" class="block" style="animation: slideY 4s infinite ease-in-out;"/>
                        <rect x="110" y="110" width="90" height="90" fill="#10b981" class="block"/>
                        <rect x="220" y="110" width="90" height="90" fill="#ef4444" class="block anim-fade" style="transform-origin: 265px 155px;"/>
                        
                        <!-- Row 3 -->
                        <rect x="0" y="220" width="90" height="90" fill="#ef4444" class="block anim-fade" style="transform-origin: 45px 265px;"/>
                        <rect x="110" y="220" width="90" height="90" fill="#f59e0b" class="block"/>
                        <rect x="220" y="220" width="90" height="90" fill="#f59e0b" class="block"/>
                    </g>
                </svg>`
            },
            {
                t: "2. The Neural Purge (Smooth Lines)",
                d: "Una rete di linee morbidissime (stroke-linecap='round'). Quando il segnale di 'Active Learning' passa, i nodi di rumore svaniscono dolcemente (transizione di opacità).",
                c: `<svg viewBox="0 0 400 400">
                    <style>
                        .line { stroke: #334155; stroke-width: 12; stroke-linecap: round; stroke-linejoin: round; fill: none; }
                        .signal { stroke: #10b981; stroke-width: 12; stroke-linecap: round; stroke-linejoin: round; fill: none; }
                        @keyframes pulseOp { 0%, 20% { opacity: 1; transform: scale(1); } 40%, 70% { opacity: 0; transform: scale(0.5); } 90%, 100% { opacity: 1; transform: scale(1); } }
                    </style>
                    <g transform="translate(50, 50)">
                        <!-- Background Smooth Paths -->
                        <path class="line" d="M 0 150 Q 150 150 150 0"/>
                        <path class="line" d="M 150 0 Q 150 150 300 150"/>
                        <path class="line" d="M 150 150 Q 150 300 0 300"/>
                        <path class="line" d="M 150 150 Q 150 300 300 300"/>

                        <!-- Signal Animation -->
                        <path class="signal" d="M 0 150 Q 150 150 300 150" stroke-dasharray="400" stroke-dashoffset="400">
                            <animate attributeName="stroke-dashoffset" values="400;-400" dur="3s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        </path>
                        <path class="signal" d="M 150 0 Q 150 150 150 300" stroke-dasharray="400" stroke-dashoffset="400">
                            <animate attributeName="stroke-dashoffset" values="400;-400" dur="3s" repeatCount="indefinite" calcMode="ease-in-out" begin="1s"/>
                        </path>

                        <!-- Nodes (Fading Noise) -->
                        <circle cx="150" cy="150" r="25" fill="#3b82f6"/>
                        <circle cx="0" cy="150" r="20" fill="#3b82f6"/>
                        <circle cx="300" cy="150" r="20" fill="#3b82f6"/>
                        
                        <!-- Noise Nodes Fading -->
                        <circle cx="150" cy="0" r="20" fill="#ef4444" style="transform-origin: 150px 0px; animation: pulseOp 3s infinite ease-in-out 0.5s;"/>
                        <circle cx="150" cy="300" r="20" fill="#ef4444" style="transform-origin: 150px 300px; animation: pulseOp 3s infinite ease-in-out 1.5s;"/>
                    </g>
                </svg>`
            },
            {
                t: "3. Morphing Silhouette (Clustering)",
                d: "Rappresentazione del clustering tramite morphing puro. Forme caotiche e distorte si fondono fluidamente in un unico, levigato cerchio centrale, svanendo dai bordi.",
                c: `<svg viewBox="0 0 400 400">
                    <style>
                        @keyframes morphBlob { 
                            0%   { d: path('M 100 200 C 100 100, 250 50, 300 150 C 350 250, 250 350, 150 300 C 50 250, 100 300, 100 200'); opacity: 0.5; }
                            50%  { d: path('M 200 100 C 255 100, 300 145, 300 200 C 300 255, 255 300, 200 300 C 145 300, 100 255, 100 200 C 100 145, 145 100, 200 100'); opacity: 1; fill: #10b981; }
                            100% { d: path('M 100 200 C 100 100, 250 50, 300 150 C 350 250, 250 350, 150 300 C 50 250, 100 300, 100 200'); opacity: 0.5; }
                        }
                        .blob { fill: #3b82f6; animation: morphBlob 4s infinite ease-in-out; }
                    </style>
                    <!-- Animated Morphing Blob -->
                    <path class="blob" d="M 100 200 C 100 100, 250 50, 300 150 C 350 250, 250 350, 150 300 C 50 250, 100 300, 100 200"/>
                    
                    <!-- Fading Orbiters -->
                    <circle cx="80" cy="80" r="15" fill="#f59e0b">
                        <animate attributeName="opacity" values="1;0;1" dur="4s" repeatCount="indefinite"/>
                        <animate attributeName="cx" values="80;200;80" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        <animate attributeName="cy" values="80;200;80" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                    </circle>
                    <circle cx="320" cy="320" r="20" fill="#f59e0b">
                        <animate attributeName="opacity" values="1;0;1" dur="4s" repeatCount="indefinite"/>
                        <animate attributeName="cx" values="320;200;320" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        <animate attributeName="cy" values="320;200;320" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                    </circle>
                </svg>`
            },
            {
                t: "4. The Overlap (Data Intersection)",
                d: "Tre morbidi cerchi semi-trasparenti si sovrappongono. L'area di intersezione pura brilla (opacity sale), mentre le parti non comuni svaniscono dolcemente nel vuoto.",
                c: `<svg viewBox="0 0 400 400">
                    <style>
                        .circle-overlap { mix-blend-mode: screen; }
                        @keyframes breatheOverlap {
                            0%, 100% { transform: translate(0, 0); opacity: 0.4; }
                            50% { opacity: 0.8; }
                        }
                    </style>
                    <g transform="translate(200, 200)">
                        <circle cx="0" cy="-40" r="90" fill="#ef4444" class="circle-overlap">
                            <animate attributeName="cy" values="-40; -10; -40" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="opacity" values="0.3; 0.8; 0.3" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        </circle>
                        <circle cx="-40" cy="40" r="90" fill="#3b82f6" class="circle-overlap">
                            <animate attributeName="cx" values="-40; -10; -40" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="cy" values="40; 10; 40" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="opacity" values="0.3; 0.8; 0.3" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        </circle>
                        <circle cx="40" cy="40" r="90" fill="#10b981" class="circle-overlap">
                            <animate attributeName="cx" values="40; 10; 40" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="cy" values="40; 10; 40" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="opacity" values="0.3; 0.8; 0.3" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        </circle>
                        <!-- Purity Center -->
                        <circle cx="0" cy="0" r="10" fill="#ffffff" opacity="0">
                            <animate attributeName="opacity" values="0; 1; 0" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                            <animate attributeName="r" values="0; 30; 0" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        </circle>
                    </g>
                </svg>`
            },
            {
                t: "5. Gentle Wave (Data Smoothing)",
                d: "Una linea spessa e arrotondata. Inizia con picchi caotici che, sfumando con transizioni di opacità e bezier curves, si distendono in una rassicurante e perfetta sinusoide.",
                c: `<svg viewBox="0 0 400 400">
                    <style>
                        .wave { fill: none; stroke-width: 16; stroke-linecap: round; stroke-linejoin: round; }
                        @keyframes waveSmooth {
                            0%, 100% { d: path('M 50 200 L 100 100 L 150 300 L 200 50 L 250 350 L 300 150 L 350 200'); stroke: #ef4444; }
                            50% { d: path('M 50 200 C 100 150, 150 150, 200 200 C 250 250, 300 250, 350 200'); stroke: #10b981; }
                        }
                    </style>
                    <path class="wave" d="M 50 200 L 100 100 L 150 300 L 200 50 L 250 350 L 300 150 L 350 200" style="animation: waveSmooth 4s infinite ease-in-out;"/>
                    
                    <!-- Fading Noise Particles -->
                    <circle cx="100" cy="80" r="8" fill="#ef4444">
                        <animate attributeName="opacity" values="1;0;1" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        <animate attributeName="cy" values="80;150;80" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                    </circle>
                    <circle cx="200" cy="30" r="8" fill="#ef4444">
                        <animate attributeName="opacity" values="1;0;1" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        <animate attributeName="cy" values="30;200;30" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                    </circle>
                    <circle cx="250" cy="370" r="8" fill="#ef4444">
                        <animate attributeName="opacity" values="1;0;1" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                        <animate attributeName="cy" values="370;250;370" dur="4s" repeatCount="indefinite" calcMode="ease-in-out"/>
                    </circle>
                </svg>`
            }
        ];

        const grid = document.getElementById('grid');
        animations.forEach(s => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = '<div class="svg-container">' + s.c + '</div><h2>' + s.t + '</h2><p>' + s.d + '</p>';
            grid.appendChild(card);
        });
    </script>
</body>
</html>
"""

output_path = r"C:\Users\Gilberto Bizzo\amazon_search\agent_animations_v3.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
