from pathlib import Path
import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Search - 15 Premium Animations</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }
        .header { text-align: center; margin-bottom: 3rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; max-width: 1400px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 12px; padding: 2rem; border: 1px solid #334155; display: flex; flex-direction: column; align-items: center; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); border-color: #3b82f6; }
        .svg-container { width: 100%; max-width: 300px; height: 300px; margin-bottom: 1.5rem; }
        svg { width: 100%; height: 100%; }
        h2 { font-size: 1.25rem; margin-bottom: 0.5rem; color: #e2e8f0; }
        p { font-size: 0.9rem; color: #94a3b8; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>15 Premium Agent Animations</h1>
        <p>Qualità altissima, design Flat e animazioni vettoriali complesse (ispirate alla perfezione del Cluster a Girasole).</p>
    </div>
    <div class="grid" id="grid"></div>

    <script>
        const splines = "0.25 0.1 0.25 1"; // Smooth easing
        const animations = [
            {
                t: "1. BIRCH Tree Expansion (Depth Sync)",
                d: "Un nodo centrale genera dinamicamente rami figli che si espandono con fluidità nello spazio.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <g transform="translate(200, 50)">
                        <!-- Branch 1 -->
                        <line x1="0" y1="0" x2="-100" y2="100" stroke="#3b82f6" stroke-width="4" stroke-dasharray="150" stroke-dashoffset="150">
                            <animate attributeName="stroke-dashoffset" values="150;0" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" />
                        </line>
                        <!-- Branch 2 -->
                        <line x1="0" y1="0" x2="100" y2="100" stroke="#10b981" stroke-width="4" stroke-dasharray="150" stroke-dashoffset="150">
                            <animate attributeName="stroke-dashoffset" values="150;0" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" begin="0.2s"/>
                        </line>
                        
                        <!-- Sub-branches Left -->
                        <g transform="translate(-100, 100)">
                            <line x1="0" y1="0" x2="-50" y2="80" stroke="#3b82f6" stroke-width="3" stroke-dasharray="100" stroke-dashoffset="100">
                                <animate attributeName="stroke-dashoffset" values="100;0" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" begin="1s"/>
                            </line>
                            <line x1="0" y1="0" x2="50" y2="80" stroke="#3b82f6" stroke-width="3" stroke-dasharray="100" stroke-dashoffset="100">
                                <animate attributeName="stroke-dashoffset" values="100;0" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" begin="1.2s"/>
                            </line>
                            <circle cx="-50" cy="80" r="15" fill="#3b82f6"><animate attributeName="r" values="0;15" dur="0.5s" begin="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                            <circle cx="50" cy="80" r="15" fill="#3b82f6"><animate attributeName="r" values="0;15" dur="0.5s" begin="2.2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        </g>

                        <!-- Sub-branches Right -->
                        <g transform="translate(100, 100)">
                            <line x1="0" y1="0" x2="-50" y2="80" stroke="#10b981" stroke-width="3" stroke-dasharray="100" stroke-dashoffset="100">
                                <animate attributeName="stroke-dashoffset" values="100;0" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" begin="1.4s"/>
                            </line>
                            <line x1="0" y1="0" x2="50" y2="80" stroke="#10b981" stroke-width="3" stroke-dasharray="100" stroke-dashoffset="100">
                                <animate attributeName="stroke-dashoffset" values="100;0" dur="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}" begin="1.6s"/>
                            </line>
                            <circle cx="-50" cy="80" r="15" fill="#10b981"><animate attributeName="r" values="0;15" dur="0.5s" begin="2.4s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                            <circle cx="50" cy="80" r="15" fill="#10b981"><animate attributeName="r" values="0;15" dur="0.5s" begin="2.6s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        </g>

                        <circle cx="0" cy="0" r="25" fill="#f8fafc"><animate attributeName="r" values="0;25;20" dur="1s" fill="freeze" calcMode="spline" keyTimes="0;0.7;1" keySplines="\${splines};\${splines}"/></circle>
                        <circle cx="-100" cy="100" r="20" fill="#3b82f6"><animate attributeName="r" values="0;20" dur="0.5s" begin="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="100" cy="100" r="20" fill="#10b981"><animate attributeName="r" values="0;20" dur="0.5s" begin="1.7s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                    </g>
                </svg>`
            },
            {
                t: "2. Vector Space Compression (PCA)",
                d: "50 particelle caotiche subiscono una riduzione dimensionale collassando in 3 densi cluster 3D flat.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Simuliamo particelle con delay diversi che collassano verso centri -->
                    <g fill="#3b82f6">
                        <circle cx="100" cy="50" r="6"><animate attributeName="cx" values="100;120" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="50;200" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="300" cy="80" r="6"><animate attributeName="cx" values="300;120" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="80;200" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="50" cy="300" r="6"><animate attributeName="cx" values="50;120" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="300;200" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="120" cy="200" r="30" fill-opacity="0"><animate attributeName="fill-opacity" values="0;0.5" dur="1s" begin="1.5s" fill="freeze"/></circle>
                    </g>
                    <g fill="#f59e0b">
                        <circle cx="350" cy="350" r="6"><animate attributeName="cx" values="350;280" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="350;150" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="200" cy="100" r="6"><animate attributeName="cx" values="200;280" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="100;150" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="280" cy="150" r="25" fill-opacity="0"><animate attributeName="fill-opacity" values="0;0.5" dur="1s" begin="1.5s" fill="freeze"/></circle>
                    </g>
                    <g fill="#10b981">
                        <circle cx="150" cy="380" r="6"><animate attributeName="cx" values="150;250" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="380;300" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="380" cy="250" r="6"><animate attributeName="cx" values="380;250" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/><animate attributeName="cy" values="250;300" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/></circle>
                        <circle cx="250" cy="300" r="20" fill-opacity="0"><animate attributeName="fill-opacity" values="0;0.5" dur="1s" begin="1.5s" fill="freeze"/></circle>
                    </g>
                    <!-- Scansione Radiale Finale -->
                    <circle cx="200" cy="200" r="10" fill="none" stroke="#f8fafc" stroke-width="2" opacity="0">
                        <animate attributeName="r" values="10;400" dur="1s" begin="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                        <animate attributeName="opacity" values="0;0.8;0" dur="1s" begin="2s" fill="freeze"/>
                    </circle>
                </svg>`
            },
            {
                t: "3. SIFT Keypoint Laser Match",
                d: "Un laser scansiona due pattern. Le linee di connessione esatte si accendono, quelle false (outliers) cadono.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <rect x="40" y="50" width="100" height="300" fill="#1e293b" rx="5" stroke="#334155" stroke-width="2"/>
                    <rect x="260" y="50" width="100" height="300" fill="#1e293b" rx="5" stroke="#334155" stroke-width="2"/>
                    
                    <!-- Scanner -->
                    <line x1="20" y1="40" x2="380" y2="40" stroke="#3b82f6" stroke-width="4" opacity="0.8">
                        <animate attributeName="y1" values="40;360;40" dur="4s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                        <animate attributeName="y2" values="40;360;40" dur="4s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                    </line>
                    <rect x="20" y="40" width="360" height="30" fill="url(#laser-glow)" opacity="0.3">
                        <animate attributeName="y" values="40;360;40" dur="4s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                    </rect>

                    <!-- Keypoints -->
                    <circle cx="90" cy="100" r="5" fill="#10b981"/>
                    <circle cx="310" cy="100" r="5" fill="#10b981"/>
                    <line x1="90" y1="100" x2="310" y2="100" stroke="#10b981" stroke-width="3" stroke-dasharray="220" stroke-dashoffset="220">
                        <animate attributeName="stroke-dashoffset" values="220;0" dur="1s" begin="0.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                    </line>

                    <circle cx="90" cy="200" r="5" fill="#ef4444"/>
                    <circle cx="310" cy="280" r="5" fill="#ef4444"/>
                    <line x1="90" y1="200" x2="310" y2="280" stroke="#ef4444" stroke-width="3" stroke-dasharray="250" stroke-dashoffset="250">
                        <animate attributeName="stroke-dashoffset" values="250;0" dur="1s" begin="1.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                        <!-- Spezzatura RANSAC -->
                        <animate attributeName="opacity" values="1;0" dur="0.2s" begin="3s" fill="freeze"/>
                    </line>

                    <circle cx="90" cy="300" r="5" fill="#10b981"/>
                    <circle cx="310" cy="300" r="5" fill="#10b981"/>
                    <line x1="90" y1="300" x2="310" y2="300" stroke="#10b981" stroke-width="3" stroke-dasharray="220" stroke-dashoffset="220">
                        <animate attributeName="stroke-dashoffset" values="220;0" dur="1s" begin="2.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                    </line>
                </svg>`
            },
            {
                t: "4. Optuna Radar Optimizer",
                d: "Una rete radar (grafico a ragnatela) si deforma alla ricerca dell'iperparametro perfetto.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <g transform="translate(200, 200)">
                        <!-- Griglie Base -->
                        <polygon points="0,-120 104,-60 104,60 0,120 -104,60 -104,-60" fill="none" stroke="#334155" stroke-width="2"/>
                        <polygon points="0,-80 69,-40 69,40 0,80 -69,40 -69,-40" fill="none" stroke="#334155" stroke-width="2"/>
                        <polygon points="0,-40 34,-20 34,20 0,40 -34,20 -34,-20" fill="none" stroke="#334155" stroke-width="2"/>
                        
                        <line x1="0" y1="0" x2="0" y2="-120" stroke="#334155" stroke-width="2"/>
                        <line x1="0" y1="0" x2="104" y2="-60" stroke="#334155" stroke-width="2"/>
                        <line x1="0" y1="0" x2="104" y2="60" stroke="#334155" stroke-width="2"/>
                        <line x1="0" y1="0" x2="0" y2="120" stroke="#334155" stroke-width="2"/>
                        <line x1="0" y1="0" x2="-104" y2="60" stroke="#334155" stroke-width="2"/>
                        <line x1="0" y1="0" x2="-104" y2="-60" stroke="#334155" stroke-width="2"/>

                        <!-- Morphing Polygon -->
                        <polygon fill="#3b82f6" opacity="0.5" stroke="#60a5fa" stroke-width="3">
                            <animate attributeName="points" 
                                values="
                                0,-40 34,-20 34,20 0,40 -34,20 -34,-20;
                                0,-100 80,-40 40,50 0,80 -90,30 -50,-50;
                                0,-60 104,-30 80,60 0,100 -40,40 -104,-20;
                                0,-120 104,-60 104,60 0,120 -104,60 -104,-60
                                " 
                                dur="4s" repeatCount="indefinite" calcMode="spline" 
                                keyTimes="0;0.33;0.66;1" 
                                keySplines="\${splines};\${splines};\${splines}"/>
                        </polygon>
                        <circle cx="0" cy="0" r="10" fill="#f8fafc"/>
                    </g>
                </svg>`
            },
            {
                t: "5. Active Learning Funnel",
                d: "I dati cadono. Quelli rossi vengono scartati con violenza, i verdi assorbiti nell'AI.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Imbuto -->
                    <path d="M100 100 L300 100 L230 250 L230 350 L170 350 L170 250 Z" fill="none" stroke="#475569" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
                    
                    <!-- Dati Buoni -->
                    <rect x="180" y="-50" width="40" height="40" rx="8" fill="#10b981">
                        <animate attributeName="y" values="-50;300;400" dur="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.7;1" keySplines="\${splines};\${splines}"/>
                        <animate attributeName="width" values="40;40;10" dur="2s" repeatCount="indefinite"/>
                        <animate attributeName="height" values="40;40;10" dur="2s" repeatCount="indefinite"/>
                    </rect>

                    <!-- Dati Rumorosi -->
                    <rect x="220" y="-80" width="40" height="40" rx="4" fill="#ef4444" transform="rotate(45 240 -60)">
                        <animate attributeName="y" values="-80;150;100" dur="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                        <animate attributeName="x" values="220;220;400" dur="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                    </rect>

                    <rect x="140" y="-150" width="30" height="30" rx="4" fill="#ef4444">
                        <animate attributeName="y" values="-150;180;100" dur="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                        <animate attributeName="x" values="140;140;-50" dur="2s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                    </rect>

                    <!-- Processing Core -->
                    <circle cx="200" cy="300" r="15" fill="#3b82f6">
                        <animate attributeName="r" values="15;25;15" dur="1s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="\${splines};\${splines}"/>
                    </circle>
                </svg>`
            },
            {
                t: "6. Data Pagination Crawler",
                d: "Raccoglitore di pagine: inghiotte dati sequenziali e deposita batch nel database (JSON).",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Track -->
                    <line x1="50" y1="200" x2="350" y2="200" stroke="#334155" stroke-width="8" stroke-linecap="round"/>
                    
                    <!-- Data Dots -->
                    <circle cx="100" cy="200" r="8" fill="#f8fafc"><animate attributeName="opacity" values="1;0;0" dur="3s" repeatCount="indefinite" keyTimes="0;0.33;1"/></circle>
                    <circle cx="200" cy="200" r="8" fill="#f8fafc"><animate attributeName="opacity" values="1;0;0" dur="3s" repeatCount="indefinite" keyTimes="0;0.66;1"/></circle>
                    <circle cx="300" cy="200" r="8" fill="#f8fafc"><animate attributeName="opacity" values="1;0;0" dur="3s" repeatCount="indefinite" keyTimes="0;0.99;1"/></circle>

                    <!-- Crawler (Pacman-like Box) -->
                    <rect x="30" y="175" width="50" height="50" rx="10" fill="#3b82f6">
                        <animate attributeName="x" values="30;320" dur="3s" repeatCount="indefinite" calcMode="linear"/>
                        <animate attributeName="width" values="50;60;50;70;50;80" dur="3s" repeatCount="indefinite"/>
                    </rect>

                    <!-- DB Cylinder -->
                    <ellipse cx="330" cy="300" rx="40" ry="15" fill="#10b981"/>
                    <path d="M290 300 L290 350 A40 15 0 0 0 370 350 L370 300 Z" fill="#059669"/>
                    
                    <!-- Drop Payload -->
                    <rect x="315" y="200" width="30" height="30" rx="5" fill="#3b82f6" opacity="0">
                        <animate attributeName="opacity" values="0;1;0" dur="3s" repeatCount="indefinite" keyTimes="0;0.95;1"/>
                        <animate attributeName="y" values="200;300;300" dur="3s" repeatCount="indefinite" keyTimes="0;0.95;1"/>
                    </rect>
                </svg>`
            },
            {
                t: "7. Async Lazy Loading",
                d: "Simulazione del fetching asincrono: sei placeholder si illuminano in parallelo, non in sequenza.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <g transform="translate(50, 50)">
                        <!-- Griglia Immagini -->
                        <rect x="0" y="0" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#3b82f6" dur="0.5s" begin="0.5s" fill="freeze"/></rect>
                        <rect x="110" y="0" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#10b981" dur="0.5s" begin="0.7s" fill="freeze"/></rect>
                        <rect x="220" y="0" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#f59e0b" dur="0.5s" begin="0.6s" fill="freeze"/></rect>
                        <rect x="0" y="110" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#8b5cf6" dur="0.5s" begin="0.9s" fill="freeze"/></rect>
                        <rect x="110" y="110" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#ec4899" dur="0.5s" begin="0.8s" fill="freeze"/></rect>
                        <rect x="220" y="110" width="80" height="80" rx="8" fill="#1e293b"><animate attributeName="fill" values="#1e293b;#14b8a6" dur="0.5s" begin="1.0s" fill="freeze"/></rect>

                        <!-- Skeleton Loaders -->
                        <rect x="-10" y="-10" width="10" height="200" fill="#f8fafc" opacity="0.1" transform="skewX(-20)">
                            <animate attributeName="x" values="-50;400" dur="1.5s" repeatCount="indefinite"/>
                        </rect>
                    </g>
                </svg>`
            },
            {
                t: "8. K-Means Centroid Gravity",
                d: "3 stelle (centroidi) si spostano e attraggono i nodi grigi, che cambiano colore allineandosi.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Nodi -->
                    <circle cx="100" cy="150" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#3b82f6" dur="0.2s" begin="1s" fill="freeze"/><animate attributeName="cx" values="100;120" dur="1s" begin="1s" fill="freeze"/></circle>
                    <circle cx="120" cy="120" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#3b82f6" dur="0.2s" begin="1.1s" fill="freeze"/><animate attributeName="cx" values="120;140" dur="1s" begin="1s" fill="freeze"/></circle>
                    <circle cx="80" cy="180" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#3b82f6" dur="0.2s" begin="1.2s" fill="freeze"/><animate attributeName="cx" values="80;100" dur="1s" begin="1s" fill="freeze"/></circle>

                    <circle cx="300" cy="120" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#10b981" dur="0.2s" begin="1.3s" fill="freeze"/><animate attributeName="cy" values="120;150" dur="1s" begin="1s" fill="freeze"/></circle>
                    <circle cx="320" cy="150" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#10b981" dur="0.2s" begin="1.4s" fill="freeze"/><animate attributeName="cx" values="320;290" dur="1s" begin="1s" fill="freeze"/></circle>

                    <circle cx="200" cy="300" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#f59e0b" dur="0.2s" begin="1.5s" fill="freeze"/><animate attributeName="cy" values="300;280" dur="1s" begin="1s" fill="freeze"/></circle>
                    <circle cx="220" cy="320" r="8" fill="#64748b"><animate attributeName="fill" values="#64748b;#f59e0b" dur="0.2s" begin="1.6s" fill="freeze"/><animate attributeName="cx" values="220;200" dur="1s" begin="1s" fill="freeze"/></circle>

                    <!-- Centroidi (Stelle/Poligoni) -->
                    <polygon points="150,150 160,130 170,150 190,160 170,170 160,190 150,170 130,160" fill="#3b82f6" opacity="0">
                        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.5s" fill="freeze"/>
                        <animateTransform attributeName="transform" type="rotate" values="0 160 160; 360 160 160" dur="4s" repeatCount="indefinite"/>
                    </polygon>
                    <polygon points="270,180 280,160 290,180 310,190 290,200 280,220 270,200 250,190" fill="#10b981" opacity="0">
                        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.7s" fill="freeze"/>
                        <animateTransform attributeName="transform" type="rotate" values="0 280 190; 360 280 190" dur="4s" repeatCount="indefinite"/>
                    </polygon>
                    <polygon points="180,250 190,230 200,250 220,260 200,270 190,290 180,270 160,260" fill="#f59e0b" opacity="0">
                        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="0.9s" fill="freeze"/>
                        <animateTransform attributeName="transform" type="rotate" values="0 190 260; 360 190 260" dur="4s" repeatCount="indefinite"/>
                    </polygon>
                </svg>`
            },
            {
                t: "9. Silhouette Score Meter",
                d: "Tachimetro moderno. L'ago oscilla, scansiona i punteggi e si blocca sul verdissimo 0.94.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Track di sfondo -->
                    <path d="M100 250 A 100 100 0 1 1 300 250" fill="none" stroke="#334155" stroke-width="20" stroke-linecap="round"/>
                    
                    <!-- Track Punteggio -->
                    <path d="M100 250 A 100 100 0 0 1 290 190" fill="none" stroke="#10b981" stroke-width="20" stroke-linecap="round" stroke-dasharray="314" stroke-dashoffset="314">
                        <animate attributeName="stroke-dashoffset" values="314;200;250;100;40" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;0.4;0.6;0.8;1" keySplines="\${splines};\${splines};\${splines};\${splines}"/>
                    </path>
                    
                    <!-- Needle -->
                    <g transform="translate(200, 250)">
                        <line x1="0" y1="0" x2="-80" y2="0" stroke="#f8fafc" stroke-width="6" stroke-linecap="round">
                            <animateTransform attributeName="transform" type="rotate" values="0; 60; 30; 110; 150" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;0.4;0.6;0.8;1" keySplines="\${splines};\${splines};\${splines};\${splines}"/>
                        </line>
                        <circle cx="0" cy="0" r="15" fill="#f8fafc"/>
                    </g>
                    <!-- Testo Finale -->
                    <text x="200" y="320" font-size="32" font-weight="bold" fill="#10b981" text-anchor="middle" opacity="0">0.94
                        <animate attributeName="opacity" values="0;1" dur="0.2s" begin="2s" fill="freeze"/>
                    </text>
                </svg>`
            },
            {
                t: "10. Text TF-IDF Vectorization",
                d: "Righe di testo grezzo (sinistra) vengono scansionate e convertite in grafici a barre densi (destra).",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Testo Grizzo -->
                    <g stroke="#64748b" stroke-width="6" stroke-linecap="round">
                        <line x1="50" y1="100" x2="150" y2="100"/>
                        <line x1="50" y1="130" x2="180" y2="130"/>
                        <line x1="50" y1="160" x2="120" y2="160"/>
                        <line x1="50" y1="190" x2="160" y2="190"/>
                    </g>

                    <!-- Scanner Line -->
                    <line x1="200" y1="50" x2="200" y2="250" stroke="#3b82f6" stroke-width="4">
                        <animate attributeName="x1" values="50;350" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                        <animate attributeName="x2" values="50;350" dur="2s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                        <animate attributeName="opacity" values="1;0" dur="0.2s" begin="2s" fill="freeze"/>
                    </line>

                    <!-- Bar Chart (Output Vettoriale) -->
                    <g fill="#10b981">
                        <rect x="250" y="200" width="10" height="0"><animate attributeName="height" values="0;80" dur="0.5s" begin="1s" fill="freeze"/><animate attributeName="y" values="200;120" dur="0.5s" begin="1s" fill="freeze"/></rect>
                        <rect x="270" y="200" width="10" height="0"><animate attributeName="height" values="0;40" dur="0.5s" begin="1.2s" fill="freeze"/><animate attributeName="y" values="200;160" dur="0.5s" begin="1.2s" fill="freeze"/></rect>
                        <rect x="290" y="200" width="10" height="0"><animate attributeName="height" values="0;120" dur="0.5s" begin="1.4s" fill="freeze"/><animate attributeName="y" values="200;80" dur="0.5s" begin="1.4s" fill="freeze"/></rect>
                        <rect x="310" y="200" width="10" height="0"><animate attributeName="height" values="0;60" dur="0.5s" begin="1.6s" fill="freeze"/><animate attributeName="y" values="200;140" dur="0.5s" begin="1.6s" fill="freeze"/></rect>
                        <rect x="330" y="200" width="10" height="0"><animate attributeName="height" values="0;30" dur="0.5s" begin="1.8s" fill="freeze"/><animate attributeName="y" values="200;170" dur="0.5s" begin="1.8s" fill="freeze"/></rect>
                    </g>
                </svg>`
            },
            {
                t: "11. Proxy Waterfall (Block & Bypass)",
                d: "Pacchetti dati blocchi da scudo rosso (403), rimbalzano su scudo blu (Proxy) in corsia sicura verde.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <!-- Data Pipes -->
                    <rect x="100" y="0" width="40" height="150" fill="#1e293b"/>
                    <rect x="200" y="180" width="40" height="220" fill="#1e293b"/>
                    
                    <!-- FireWall (403) -->
                    <rect x="90" y="150" width="60" height="15" fill="#ef4444" rx="4"/>
                    <!-- Proxy Deflector -->
                    <path d="M140 100 L180 140 L220 180" fill="none" stroke="#3b82f6" stroke-width="8" stroke-linecap="round"/>

                    <!-- Data Packets -->
                    <rect x="110" y="-30" width="20" height="20" rx="4" fill="#f8fafc">
                        <animate attributeName="y" values="-30;120;120" dur="1.5s" repeatCount="indefinite" calcMode="linear"/>
                        <animate attributeName="x" values="110;110;210" dur="1.5s" repeatCount="indefinite" calcMode="linear"/>
                    </rect>
                    
                    <rect x="210" y="180" width="20" height="20" rx="4" fill="#10b981" opacity="0">
                        <animate attributeName="opacity" values="0;1;1" dur="1.5s" repeatCount="indefinite" keyTimes="0;0.5;1"/>
                        <animate attributeName="y" values="180;420;420" dur="1.5s" repeatCount="indefinite" calcMode="linear"/>
                    </rect>
                </svg>`
            },
            {
                t: "12. Ensemble Majority Voting",
                d: "Tre algoritmi votano: due fasci di luce verde vincono sul raggio rosso. Il master si tinge di verde.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    
                    <rect x="50" y="80" width="60" height="60" rx="10" fill="#334155" stroke="#10b981" stroke-width="4"/>
                    <rect x="50" y="170" width="60" height="60" rx="10" fill="#334155" stroke="#ef4444" stroke-width="4"/>
                    <rect x="50" y="260" width="60" height="60" rx="10" fill="#334155" stroke="#10b981" stroke-width="4"/>

                    <rect x="250" y="150" width="100" height="100" rx="20" fill="#1e293b" stroke="#64748b" stroke-width="4">
                        <animate attributeName="stroke" values="#64748b;#10b981" dur="0.5s" begin="1.5s" fill="freeze"/>
                        <animate attributeName="fill" values="#1e293b;#064e3b" dur="0.5s" begin="1.5s" fill="freeze"/>
                    </rect>

                    <!-- Voting Beams -->
                    <line x1="120" y1="110" x2="240" y2="180" stroke="#10b981" stroke-width="8" stroke-dasharray="150" stroke-dashoffset="150">
                        <animate attributeName="stroke-dashoffset" values="150;0" dur="1s" begin="0.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                    </line>
                    <line x1="120" y1="200" x2="240" y2="200" stroke="#ef4444" stroke-width="8" stroke-dasharray="150" stroke-dashoffset="150">
                        <animate attributeName="stroke-dashoffset" values="150;0" dur="1s" begin="0.7s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                    </line>
                    <line x1="120" y1="290" x2="240" y2="220" stroke="#10b981" stroke-width="8" stroke-dasharray="150" stroke-dashoffset="150">
                        <animate attributeName="stroke-dashoffset" values="150;0" dur="1s" begin="0.9s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                    </line>
                </svg>`
            },
            {
                t: "13. JSON Serialization Cube",
                d: "Forme geometriche destrutturate entrano in una scatola ed escono come testo formattato (codice puro).",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <circle cx="100" cy="100" r="15" fill="#3b82f6"><animate attributeName="cy" values="100;180" dur="1s" fill="freeze"/><animate attributeName="cx" values="100;200" dur="1s" fill="freeze"/></circle>
                    <polygon points="100,280 120,320 80,320" fill="#10b981"><animate attributeName="points" values="100,280 120,320 80,320; 200,200 200,200 200,200" dur="1s" fill="freeze"/></polygon>
                    <rect x="80" y="180" width="30" height="30" fill="#f59e0b"><animate attributeName="x" values="80;185" dur="1s" fill="freeze"/></rect>

                    <rect x="150" y="150" width="100" height="100" rx="10" fill="none" stroke="#64748b" stroke-width="6"/>
                    <path d="M150 150 L200 200 L250 150" fill="none" stroke="#64748b" stroke-width="6"/>

                    <!-- JSON Text Output -->
                    <g font-family="monospace" font-size="14" fill="#10b981" font-weight="bold" opacity="0">
                        <animate attributeName="opacity" values="0;1" dur="0.5s" begin="1.5s" fill="freeze"/>
                        <text x="280" y="160">{</text>
                        <text x="300" y="180">"id": 1,</text>
                        <text x="300" y="200">"vec": []</text>
                        <text x="280" y="220">}</text>
                    </g>
                    <!-- Ejection line -->
                    <line x1="250" y1="200" x2="270" y2="200" stroke="#f8fafc" stroke-width="4" opacity="0">
                        <animate attributeName="opacity" values="0;1" dur="0.2s" begin="1.2s" fill="freeze"/>
                    </line>
                </svg>`
            },
            {
                t: "14. Database Table Syncing",
                d: "Sincronizzazione in tempo reale di due tabelle distinte tramite bridge vettoriale.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <g transform="translate(50, 100)">
                        <!-- Table 1 -->
                        <rect x="0" y="0" width="100" height="20" fill="#334155" rx="4"/>
                        <rect x="0" y="30" width="100" height="20" fill="#334155" rx="4"/>
                        <rect x="0" y="60" width="100" height="20" fill="#334155" rx="4"/>
                        <!-- Update Ping -->
                        <rect x="80" y="30" width="20" height="20" fill="#3b82f6" rx="4"><animate attributeName="opacity" values="1;0" dur="2s" repeatCount="indefinite"/></rect>
                    </g>
                    <g transform="translate(250, 100)">
                        <!-- Table 2 -->
                        <rect x="0" y="0" width="100" height="20" fill="#334155" rx="4"/>
                        <rect x="0" y="30" width="100" height="20" fill="#334155" rx="4"/>
                        <rect x="0" y="60" width="100" height="20" fill="#334155" rx="4"/>
                        <!-- Update Receive -->
                        <rect x="0" y="30" width="20" height="20" fill="#10b981" rx="4" opacity="0"><animate attributeName="opacity" values="0;1" dur="2s" repeatCount="indefinite" begin="0.5s"/></rect>
                    </g>
                    <!-- Sync Line -->
                    <path d="M160 140 Q200 100 240 140" fill="none" stroke="#3b82f6" stroke-width="4" stroke-dasharray="10 10">
                        <animate attributeName="stroke-dashoffset" values="40;0" dur="1s" repeatCount="indefinite" calcMode="linear"/>
                    </path>
                </svg>`
            },
            {
                t: "15. The Final Output (Report Dispatch)",
                d: "Righe di codice volano in un foglio che si trasforma in una busta e scatta via.",
                c: `<svg viewBox="0 0 400 400">
                    <rect width="400" height="400" fill="#0f172a" rx="10"/>
                    <g transform="translate(150, 100)">
                        <rect x="0" y="0" width="100" height="140" fill="#1e293b" stroke="#f8fafc" stroke-width="4" rx="4"/>
                        <!-- Lines flying in -->
                        <line x1="-100" y1="30" x2="80" y2="30" stroke="#10b981" stroke-width="6" stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="180">
                            <animate attributeName="stroke-dashoffset" values="180;0" dur="1s" fill="freeze"/>
                        </line>
                        <line x1="-150" y1="60" x2="60" y2="60" stroke="#3b82f6" stroke-width="6" stroke-linecap="round" stroke-dasharray="60" stroke-dashoffset="210">
                            <animate attributeName="stroke-dashoffset" values="210;0" dur="1s" begin="0.3s" fill="freeze"/>
                        </line>
                        <line x1="-50" y1="90" x2="70" y2="90" stroke="#f59e0b" stroke-width="6" stroke-linecap="round" stroke-dasharray="70" stroke-dashoffset="120">
                            <animate attributeName="stroke-dashoffset" values="120;0" dur="1s" begin="0.6s" fill="freeze"/>
                        </line>

                        <!-- Envelope Fold (Cover up lines) -->
                        <polygon points="0,0 50,60 100,0" fill="#f8fafc" opacity="0">
                            <animate attributeName="opacity" values="0;1" dur="0.2s" begin="1.8s" fill="freeze"/>
                        </polygon>
                        <polygon points="0,0 50,60 100,0" fill="#1e293b" opacity="0" transform="scale(0.9) translate(5, 5)">
                            <animate attributeName="opacity" values="0;1" dur="0.2s" begin="1.8s" fill="freeze"/>
                        </polygon>
                        
                        <animateTransform attributeName="transform" type="translate" values="150, 100; 500, -100" dur="0.8s" begin="2.5s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="\${splines}"/>
                        <animateTransform attributeName="transform" type="scale" values="1; 0.5" dur="0.8s" begin="2.5s" fill="freeze" additive="sum"/>
                    </g>
                </svg>`
            }
        ];

        const grid = document.getElementById('grid');
        animations.forEach(s => {
            const card = document.createElement('div');
            card.className = 'card';
            card.innerHTML = \`
                <div class="svg-container">\${s.c}</div>
                <h2>\${s.t}</h2>
                <p>\${s.d}</p>
            \`;
            grid.appendChild(card);
        });
    </script>
</body>
</html>
"""

output_path = rstr(Path.home() / "amazon_search", "agent_animations_premium.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
