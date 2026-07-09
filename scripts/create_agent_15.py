import os

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Amazon Search - 15 Premium Agent Animations</title>
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }
        .header { text-align: center; margin-bottom: 3rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 2rem; max-width: 1400px; margin: 0 auto; }
        .card { background: #1e293b; border-radius: 12px; padding: 2rem; border: 1px solid #334155; display: flex; flex-direction: column; align-items: center; text-align: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); transition: transform 0.3s ease; }
        .card:hover { transform: translateY(-5px); border-color: #3b82f6; }
        .svg-container { width: 100%; max-width: 300px; height: 300px; margin-bottom: 1.5rem; display: flex; justify-content: center; align-items: center; }
        svg { width: 100%; height: 100%; border-radius: 12px; }
        h2 { font-size: 1.25rem; margin-bottom: 0.5rem; color: #e2e8f0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>15 Premium Agent Animations</h1>
        <p>Realizzate dal Team Agenti (Alpha, Beta, Gamma). Zero spigoli, zero console, pura morbidezza e transizioni Flat.</p>
    </div>
    <div class="grid">

        <!-- 1 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <style>
    .dot { animation: cluster 4s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate; fill: #4F46E5; }
    .dot2 { animation: cluster2 4s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate; fill: #10B981; }
    .dot3 { animation: cluster3 4s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate; fill: #F43F5E; }
    .bg-layer { opacity: 0; animation: fadeBg 4s ease-in-out infinite alternate; fill: #EEF2FF; }
    @keyframes cluster { 0% { transform: translate(0, 0); opacity: 0.3; } 100% { transform: translate(100px, 50px); opacity: 1; } }
    @keyframes cluster2 { 0% { transform: translate(0, 0); opacity: 0.3; } 100% { transform: translate(-80px, 60px); opacity: 1; } }
    @keyframes cluster3 { 0% { transform: translate(0, 0); opacity: 0.3; } 100% { transform: translate(60px, -70px); opacity: 1; } }
    @keyframes fadeBg { 0% { opacity: 0; transform: scale(0.9); } 100% { opacity: 1; transform: scale(1.1); } }
  </style>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <rect x="100" y="75" width="200" height="150" rx="40" class="bg-layer" style="transform-origin: center; fill: #1e293b;"/>
  <g transform="translate(100, 100)">
    <circle cx="50" cy="50" r="15" class="dot"/>
    <circle cx="150" cy="20" r="12" class="dot2"/>
    <circle cx="20" cy="120" r="18" class="dot3"/>
  </g>
</svg>
            </div>
            <h2>1. AI Data Clustering</h2>
        </div>

        <!-- 2 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <style>
    .noise { animation: filterOut 3s ease-in-out infinite alternate; }
    .signal { animation: signalStrong 3s ease-in-out infinite alternate; fill: #3B82F6; }
    .path { stroke-dasharray: 400; stroke-dashoffset: 400; animation: draw 3s ease-in-out infinite alternate; }
    @keyframes filterOut { 0% { opacity: 0.8; transform: scale(1); } 100% { opacity: 0; transform: scale(0.5); } }
    @keyframes signalStrong { 0% { opacity: 0.2; r: 5; } 100% { opacity: 1; r: 12; } }
    @keyframes draw { 0% { stroke-dashoffset: 400; opacity: 0; } 100% { stroke-dashoffset: 0; opacity: 1; } }
  </style>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g class="noise" fill="#94A3B8" style="transform-origin: center;">
    <circle cx="80" cy="60" r="6"/>
    <circle cx="300" cy="90" r="8"/>
    <circle cx="120" cy="240" r="5"/>
    <circle cx="280" cy="220" r="7"/>
  </g>
  <path d="M 50 150 Q 150 50 200 150 T 350 150" fill="none" stroke="#3B82F6" stroke-width="8" stroke-linecap="round" stroke-linejoin="round" class="path"/>
  <circle cx="50" cy="150" class="signal"/>
  <circle cx="200" cy="150" class="signal" style="animation-delay: 1s"/>
  <circle cx="350" cy="150" class="signal" style="animation-delay: 2s"/>
</svg>
            </div>
            <h2>2. Noise Filtering Process</h2>
        </div>

        <!-- 3 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <style>
    .node { animation: pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite alternate; fill: #8B5CF6; }
    .link { animation: glow 3s ease-in-out infinite alternate; stroke: #C4B5FD; stroke-width: 6; stroke-linecap: round; stroke-linejoin: round; }
    @keyframes pulse { 0% { opacity: 0.4; transform: scale(0.85); } 100% { opacity: 1; transform: scale(1.15); } }
    @keyframes glow { 0% { opacity: 0.2; stroke-width: 4; } 100% { opacity: 0.8; stroke-width: 8; } }
  </style>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g transform="translate(50, 50)">
    <path d="M 50 100 L 150 40 L 250 100 L 150 160 Z" fill="none" class="link"/>
    <path d="M 150 40 L 150 160" fill="none" class="link"/>
    <circle cx="50" cy="100" r="14" class="node" style="animation-delay: 0s; transform-origin: 50px 100px;"/>
    <circle cx="150" cy="40" r="18" class="node" style="animation-delay: 0.5s; transform-origin: 150px 40px;"/>
    <circle cx="250" cy="100" r="14" class="node" style="animation-delay: 1s; transform-origin: 250px 100px;"/>
    <circle cx="150" cy="160" r="18" class="node" style="animation-delay: 1.5s; transform-origin: 150px 160px;"/>
  </g>
</svg>
            </div>
            <h2>3. Fluid Neural Pathways</h2>
        </div>

        <!-- 4 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <style>
    .track { stroke: #334155; stroke-width: 20; fill: none; stroke-linecap: round; stroke-linejoin: round; }
    .flow { stroke: #F59E0B; stroke-width: 12; fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 100 600; animation: slide 3s cubic-bezier(0.4, 0, 0.2, 1) infinite; }
    @keyframes slide { 0% { stroke-dashoffset: 600; opacity: 0; } 20% { opacity: 1; } 80% { opacity: 1; } 100% { stroke-dashoffset: 0; opacity: 0; } }
  </style>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <path d="M 60 150 C 150 50, 250 250, 340 150" class="track"/>
  <path d="M 60 150 C 150 50, 250 250, 340 150" class="flow"/>
  <path d="M 60 150 C 150 50, 250 250, 340 150" class="flow" style="animation-delay: -1.5s; stroke: #D97706;"/>
</svg>
            </div>
            <h2>4. Continuous Data Sync</h2>
        </div>

        <!-- 5 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <style>
    .layer { fill: none; stroke-linecap: round; stroke-linejoin: round; transform-origin: center; animation: expandFade 4s cubic-bezier(0.25, 1, 0.5, 1) infinite; }
    .core { animation: corePulse 2s ease-in-out infinite alternate; transform-origin: center; }
    @keyframes expandFade { 0% { transform: scale(0.4); opacity: 1; stroke-width: 14; } 100% { transform: scale(1.6); opacity: 0; stroke-width: 2; } }
    @keyframes corePulse { 0% { opacity: 0.3; transform: scale(0.8); } 100% { opacity: 1; transform: scale(1.2); } }
  </style>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g transform="translate(200, 150)">
    <rect x="-40" y="-30" width="80" height="60" rx="25" class="layer" stroke="#06B6D4" style="animation-delay: 0s;"/>
    <rect x="-60" y="-45" width="120" height="90" rx="35" class="layer" stroke="#0891B2" style="animation-delay: 1.3s;"/>
    <rect x="-80" y="-60" width="160" height="120" rx="45" class="layer" stroke="#164E63" style="animation-delay: 2.6s;"/>
    <circle cx="0" cy="0" r="12" fill="#06B6D4" class="core"/>
  </g>
</svg>
            </div>
            <h2>5. GenAI Model Optimization</h2>
        </div>

        <!-- 6 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <style>
      .node-beta { fill: #4a90e2; }
      .node-alt { fill: #50e3c2; }
      @keyframes cluster-move-1 { 0%, 100% { transform: translate(0, 0); opacity: 0.9; } 50% { transform: translate(45px, 25px); opacity: 0.2; } }
      @keyframes cluster-move-2 { 0%, 100% { transform: translate(0, 0); opacity: 0.8; } 50% { transform: translate(-35px, -15px); opacity: 0.3; } }
      .c1-beta { animation: cluster-move-1 4s ease-in-out infinite; }
      .c2-beta { animation: cluster-move-2 4.5s ease-in-out infinite; }
      .c3-beta { animation: cluster-move-1 5s ease-in-out infinite reverse; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g transform="translate(140, 120)">
    <circle class="node-beta c1-beta" cx="0" cy="0" r="18"/>
    <circle class="node-beta c2-beta" cx="35" cy="20" r="14"/>
    <circle class="node-beta c3-beta" cx="-25" cy="40" r="22"/>
  </g>
  <g transform="translate(260, 170)">
    <circle class="node-alt c2-beta" cx="0" cy="0" r="16"/>
    <circle class="node-alt c3-beta" cx="-30" cy="-25" r="18"/>
    <circle class="node-alt c1-beta" cx="20" cy="-45" r="12"/>
  </g>
</svg>
            </div>
            <h2>6. Clustering Dynamics</h2>
        </div>

        <!-- 7 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <style>
      .path-base { stroke: #9b51e0; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; fill: none; opacity: 0.15; }
      .path-flow { stroke: #f2994a; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; fill: none; stroke-dasharray: 80 150; }
      @keyframes dash-flow { 0% { stroke-dashoffset: 230; opacity: 0; } 50% { opacity: 0.9; } 100% { stroke-dashoffset: 0; opacity: 0; } }
      .flow-anim { animation: dash-flow 3.5s ease-in-out infinite; }
      @keyframes soft-pulse { 0%, 100% { r: 7; opacity: 0.4; } 50% { r: 12; opacity: 1; } }
      .synapse { fill: #bb6bd9; animation: soft-pulse 2.5s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <path class="path-base" d="M 80 150 Q 150 80 200 150 T 320 150" />
  <path class="path-flow flow-anim" d="M 80 150 Q 150 80 200 150 T 320 150" />
  <circle class="synapse" cx="80" cy="150" r="7" style="animation-delay: 0s;"/>
  <circle class="synapse" cx="200" cy="150" r="7" style="animation-delay: 1.2s;"/>
  <circle class="synapse" cx="320" cy="150" r="7" style="animation-delay: 2.4s;"/>
</svg>
            </div>
            <h2>7. AI Neural Synapses</h2>
        </div>

        <!-- 8 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <style>
      .blob-scan { fill: #2d9cdb; transition: all 0.5s; }
      .scanner-bar { stroke: #56ccf2; stroke-width: 8; stroke-linecap: round; }
      @keyframes soft-scan { 0%, 100% { transform: translateY(0); opacity: 0; } 15% { opacity: 0.7; } 85% { opacity: 0.7; } 50% { transform: translateY(140px); opacity: 0.3; } }
      .scanner-group { animation: soft-scan 4s ease-in-out infinite; }
      @keyframes pattern-match { 0%, 100% { opacity: 0.15; transform: scale(1); fill: #2d9cdb; } 50% { opacity: 0.9; transform: scale(1.08); fill: #f2c94c; } }
      .target-blob { animation: pattern-match 4s ease-in-out infinite; animation-delay: 2s; }
      .idle-blob { opacity: 0.15; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <rect class="blob-scan idle-blob" x="90" y="70" width="60" height="60" rx="20" ry="20"/>
  <rect class="blob-scan target-blob" x="170" y="70" width="60" height="60" rx="20" ry="20"/>
  <rect class="blob-scan idle-blob" x="250" y="70" width="60" height="60" rx="20" ry="20"/>
  <rect class="blob-scan idle-blob" x="90" y="150" width="60" height="60" rx="20" ry="20"/>
  <rect class="blob-scan idle-blob" x="170" y="150" width="60" height="60" rx="20" ry="20"/>
  <rect class="blob-scan idle-blob" x="250" y="150" width="60" height="60" rx="20" ry="20"/>
  <g class="scanner-group">
    <line class="scanner-bar" x1="70" y1="50" x2="330" y2="50"/>
    <path d="M 70 50 Q 200 80 330 50" fill="none" stroke="#56ccf2" stroke-width="3" opacity="0.4" stroke-linecap="round"/>
  </g>
</svg>
            </div>
            <h2>8. Pattern Recognition</h2>
        </div>

        <!-- 9 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <style>
      .layer-rect { fill: none; stroke-width: 10; stroke-linecap: round; stroke-linejoin: round; }
      @keyframes layer-breathe { 0% { transform: translateY(0) scale(0.95); opacity: 0.9; } 50% { transform: translateY(-25px) scale(1.02); opacity: 0.2; } 100% { transform: translateY(0) scale(0.95); opacity: 0.9; } }
      .l-back { stroke: #eb5757; animation: layer-breathe 4s ease-in-out infinite; }
      .l-mid { stroke: #f2994a; animation: layer-breathe 4s ease-in-out infinite 0.8s; }
      .l-front { stroke: #f2c94c; animation: layer-breathe 4s ease-in-out infinite 1.6s; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g transform="translate(100, 160) rotate(-18) skewX(25)">
    <rect class="layer-rect l-front" x="0" y="60" width="160" height="90" rx="25" ry="25" />
    <rect class="layer-rect l-mid" x="0" y="30" width="160" height="90" rx="25" ry="25" />
    <rect class="layer-rect l-back" x="0" y="0" width="160" height="90" rx="25" ry="25" />
  </g>
</svg>
            </div>
            <h2>9. Deep Learning Layers</h2>
        </div>

        <!-- 10 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="100%" height="100%">
  <defs>
    <style>
      .resonance-ring { fill: none; stroke-linecap: round; }
      @keyframes cognitive-ripple { 0% { r: 15; opacity: 0.9; stroke-width: 10; } 100% { r: 110; opacity: 0; stroke-width: 2; } }
      .ring-1 { stroke: #27ae60; animation: cognitive-ripple 4.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; }
      .ring-2 { stroke: #2ecc71; animation: cognitive-ripple 4.5s cubic-bezier(0.4, 0, 0.2, 1) infinite 1.5s; }
      .ring-3 { stroke: #6fcf97; animation: cognitive-ripple 4.5s cubic-bezier(0.4, 0, 0.2, 1) infinite 3s; }
      .cognitive-core { fill: #27ae60; animation: core-glow 2.25s ease-in-out infinite; }
      @keyframes core-glow { 0%, 100% { r: 14; opacity: 1; } 50% { r: 20; opacity: 0.4; } }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g transform="translate(200, 150)">
    <circle class="resonance-ring ring-1" cx="0" cy="0" />
    <circle class="resonance-ring ring-2" cx="0" cy="0" />
    <circle class="resonance-ring ring-3" cx="0" cy="0" />
    <circle class="cognitive-core" cx="0" cy="0" />
  </g>
</svg>
            </div>
            <h2>10. Cognitive Resonance</h2>
        </div>

        <!-- 11 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <style>
      .pill { fill: #4A90E2; opacity: 0; }
      @keyframes alignA { 0%, 100% { transform: translateX(50px); opacity: 0.2; } 50% { transform: translateX(300px); opacity: 1; } }
      @keyframes alignB { 0%, 100% { transform: translateX(150px); opacity: 0.2; } 50% { transform: translateX(300px); opacity: 1; } }
      @keyframes alignC { 0%, 100% { transform: translateX(500px); opacity: 0.2; } 50% { transform: translateX(300px); opacity: 1; } }
      .p1 { animation: alignA 4s ease-in-out infinite; }
      .p2 { animation: alignB 4s ease-in-out infinite; }
      .p3 { animation: alignC 4s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <rect class="pill p1" x="0" y="200" width="200" height="40" rx="20" ry="20" />
  <rect class="pill p2" x="0" y="280" width="200" height="40" rx="20" ry="20" />
  <rect class="pill p3" x="0" y="360" width="200" height="40" rx="20" ry="20" />
</svg>
            </div>
            <h2>11. Data Alignment</h2>
        </div>

        <!-- 12 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <style>
      .dot-pca { fill: #50E3C2; opacity: 0.4; }
      .axis { stroke: #F5A623; stroke-width: 16; stroke-linecap: round; opacity: 0; }
      @keyframes pcaLine { 0%, 100% { opacity: 0; transform: rotate(-20deg) scale(0.8); } 40%, 60% { opacity: 1; transform: rotate(15deg) scale(1); } }
      @keyframes projectA { 0%, 100% { transform: translate(0, 0); opacity: 0.4; } 40%, 60% { transform: translate(20px, 40px); opacity: 0.9; } }
      @keyframes projectB { 0%, 100% { transform: translate(0, 0); opacity: 0.4; } 40%, 60% { transform: translate(-30px, -50px); opacity: 0.9; } }
      .line-anim { animation: pcaLine 6s ease-in-out infinite; transform-origin: 400px 300px; }
      .pa { animation: projectA 6s ease-in-out infinite; }
      .pb { animation: projectB 6s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <g class="pa">
    <circle class="dot-pca" cx="300" cy="250" r="24" />
    <circle class="dot-pca" cx="350" cy="200" r="24" />
  </g>
  <g class="pb">
    <circle class="dot-pca" cx="450" cy="350" r="24" />
    <circle class="dot-pca" cx="500" cy="400" r="24" />
  </g>
  <line class="axis line-anim" x1="200" y1="350" x2="600" y2="250" />
</svg>
            </div>
            <h2>12. Principal Component Analysis</h2>
        </div>

        <!-- 13 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <style>
      .norm { fill: #9B9B9B; opacity: 0.6; }
      .outlier { fill: #9B9B9B; }
      .halo { fill: none; stroke: #D0021B; stroke-width: 8; stroke-linecap: round; opacity: 0; }
      @keyframes drift { 0%, 100% { transform: translate(0, 0); fill: #9B9B9B; opacity: 0.6; } 40%, 60% { transform: translate(250px, -150px); fill: #D0021B; opacity: 1; } }
      @keyframes pulseOut { 0%, 30%, 100% { r: 20; opacity: 0; } 45% { r: 50; opacity: 0.8; } 60% { r: 80; opacity: 0; } }
      .out-anim { animation: drift 7s ease-in-out infinite; }
      .halo-anim { animation: pulseOut 7s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <circle class="norm" cx="380" cy="300" r="20" />
  <circle class="norm" cx="420" cy="280" r="24" />
  <circle class="norm" cx="360" cy="340" r="22" />
  <circle class="norm" cx="400" cy="330" r="18" />
  <circle class="norm" cx="440" cy="320" r="20" />
  <g class="out-anim">
    <circle class="outlier" cx="390" cy="290" r="24" />
    <circle class="halo halo-anim" cx="390" cy="290" r="20" />
  </g>
</svg>
            </div>
            <h2>13. Outlier Detection</h2>
        </div>

        <!-- 14 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <style>
      .blob-clust { opacity: 0.5; }
      @keyframes clusterX1 { 0%, 100% { transform: translate(0, 0); fill: #C4C4C4; opacity: 0.4; } 40%, 60% { transform: translate(-100px, -80px); fill: #F8E71C; opacity: 0.9; } }
      @keyframes clusterX2 { 0%, 100% { transform: translate(0, 0); fill: #C4C4C4; opacity: 0.4; } 40%, 60% { transform: translate(120px, 90px); fill: #BD10E0; opacity: 0.9; } }
      .cx1 { animation: clusterX1 6s ease-in-out infinite; }
      .cx2 { animation: clusterX2 6s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <circle class="blob-clust cx1" cx="380" cy="280" r="28" />
  <circle class="blob-clust cx2" cx="410" cy="310" r="32" />
  <circle class="blob-clust cx1" cx="360" cy="320" r="24" />
  <circle class="blob-clust cx2" cx="430" cy="290" r="30" />
  <circle class="blob-clust cx1" cx="400" cy="270" r="26" />
  <circle class="blob-clust cx2" cx="390" cy="330" r="28" />
</svg>
            </div>
            <h2>14. Data Clustering Evolution</h2>
        </div>

        <!-- 15 -->
        <div class="card">
            <div class="svg-container">
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="100%" height="100%">
  <defs>
    <style>
      .stream { fill: none; stroke-width: 24; stroke-linecap: round; stroke-linejoin: round; }
      @keyframes flowUp { 0%, 100% { stroke-dashoffset: 800; opacity: 0.1; } 50% { stroke-dashoffset: 0; opacity: 0.9; } }
      @keyframes flowDown { 0%, 100% { stroke-dashoffset: -800; opacity: 0.1; } 50% { stroke-dashoffset: 0; opacity: 0.9; } }
      .s1 { stroke: #7ED321; stroke-dasharray: 800; animation: flowUp 5s ease-in-out infinite; }
      .s2 { stroke: #4A90E2; stroke-dasharray: 800; animation: flowDown 6s ease-in-out infinite; }
      .s3 { stroke: #F5A623; stroke-dasharray: 800; animation: flowUp 7s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#0f172a" rx="20"/>
  <path class="stream s1" d="M 100 200 Q 300 100 400 200 T 700 200" />
  <path class="stream s2" d="M 100 300 Q 300 400 400 300 T 700 300" />
  <path class="stream s3" d="M 100 400 Q 300 300 400 400 T 700 400" />
</svg>
            </div>
            <h2>15. Smooth Data Flow</h2>
        </div>

    </div>
</body>
</html>
"""

output_path = r"C:\Users\Gilberto Bizzo\amazon_search\agent_animations_premium_team.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)
