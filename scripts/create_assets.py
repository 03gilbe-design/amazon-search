import os

out_dir = r'C:\Users\Gilberto Bizzo\Downloads\App_Assets_Github'
os.makedirs(out_dir, exist_ok=True)

# 1. GitHub Header Hero Animation (Wide banner)
header_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" width="100%" height="100%">
  <defs>
    <style>
      .bg { fill: #0f172a; }
      .path { stroke: #3b82f6; stroke-width: 4; fill: none; stroke-linecap: round; stroke-linejoin: round; }
      .node { fill: #10b981; }
      @keyframes flow {
        0% { stroke-dashoffset: 1000; }
        100% { stroke-dashoffset: 0; }
      }
      .anim-path { stroke-dasharray: 1000; animation: flow 5s linear infinite; }
      @keyframes pulse {
        0%, 100% { r: 6; opacity: 0.5; }
        50% { r: 10; opacity: 1; }
      }
      .anim-node { animation: pulse 2s ease-in-out infinite; }
    </style>
  </defs>
  <rect width="800" height="200" class="bg" rx="15"/>
  
  <path d="M 0 100 C 200 150, 400 50, 600 100 S 800 150, 900 100" class="path anim-path"/>
  <path d="M 0 150 C 300 50, 500 180, 800 50" class="path anim-path" style="stroke: #8b5cf6; animation-duration: 7s;"/>
  
  <circle cx="200" cy="120" class="node anim-node" style="animation-delay: 0s;"/>
  <circle cx="400" cy="80" class="node anim-node" style="animation-delay: 1s; fill: #f59e0b;"/>
  <circle cx="600" cy="100" class="node anim-node" style="animation-delay: 0.5s; fill: #ef4444;"/>
  
  <text x="400" y="105" font-family="Inter, sans-serif" font-size="24" font-weight="bold" fill="#f8fafc" text-anchor="middle" letter-spacing="2">AMAZON AI SEARCH</text>
  <text x="400" y="130" font-family="Inter, sans-serif" font-size="12" fill="#94a3b8" text-anchor="middle" letter-spacing="4">CLUSTERING &amp; NOISE REMOVAL</text>
</svg>'''
with open(os.path.join(out_dir, 'github_header_animation.svg'), 'w') as f: f.write(header_svg)

# 2. App Loading Spinner (Resonance Wave)
loading_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <defs>
    <style>
      .ring { fill: none; stroke: #3b82f6; stroke-linecap: round; }
      @keyframes ripple {
        0% { r: 10; opacity: 1; stroke-width: 6; }
        100% { r: 40; opacity: 0; stroke-width: 1; }
      }
      .r1 { animation: ripple 2s cubic-bezier(0.4, 0, 0.2, 1) infinite; }
      .r2 { animation: ripple 2s cubic-bezier(0.4, 0, 0.2, 1) infinite 0.6s; }
      .r3 { animation: ripple 2s cubic-bezier(0.4, 0, 0.2, 1) infinite 1.2s; }
    </style>
  </defs>
  <rect width="100" height="100" fill="#0f172a" rx="15"/>
  <circle cx="50" cy="50" class="ring r1"/>
  <circle cx="50" cy="50" class="ring r2"/>
  <circle cx="50" cy="50" class="ring r3"/>
  <circle cx="50" cy="50" r="8" fill="#10b981"/>
</svg>'''
with open(os.path.join(out_dir, 'loading_spinner.svg'), 'w') as f: f.write(loading_svg)

# 3. Sunflower UI Icon (from the notes)
sunflower_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <defs>
    <style>
      @keyframes orbit {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      .group { animation: orbit 10s linear infinite; transform-origin: 50px 50px; }
      .center-blob { fill: #3b82f6; }
      .satellite { fill: #1e293b; stroke: #3b82f6; stroke-width: 2; }
      .plus { stroke: #f8fafc; stroke-width: 2; stroke-linecap: round; }
    </style>
  </defs>
  <rect width="100" height="100" fill="#0f172a" rx="15"/>
  <g class="group">
    <circle cx="50" cy="20" r="10" class="satellite"/>
    <path d="M 50 15 L 50 25 M 45 20 L 55 20" class="plus"/>
    
    <circle cx="80" cy="50" r="10" class="satellite"/>
    <path d="M 80 45 L 80 55 M 75 50 L 85 50" class="plus"/>
    
    <circle cx="50" cy="80" r="10" class="satellite"/>
    <path d="M 50 75 L 50 85 M 45 80 L 55 80" class="plus"/>
    
    <circle cx="20" cy="50" r="10" class="satellite"/>
    <path d="M 20 45 L 20 55 M 15 50 L 25 50" class="plus"/>
  </g>
  <circle cx="50" cy="50" r="16" class="center-blob"/>
</svg>'''
with open(os.path.join(out_dir, 'icon_sunflower_ui.svg'), 'w') as f: f.write(sunflower_svg)

# 4. Duplicate Remover Icon (from notes)
duplicate_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <defs>
    <style>
      @keyframes pop {
        0%, 100% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(0); opacity: 0; }
      }
      .dup { animation: pop 3s ease-in-out infinite; transform-origin: 65px 35px; fill: #ef4444; }
      .main { fill: #10b981; }
    </style>
  </defs>
  <rect width="100" height="100" fill="#0f172a" rx="15"/>
  <rect x="45" y="15" width="40" height="40" rx="8" class="dup"/>
  <rect x="15" y="45" width="40" height="40" rx="8" class="main"/>
  <path d="M 35 65 L 45 65" stroke="#f8fafc" stroke-width="4" stroke-linecap="round"/>
</svg>'''
with open(os.path.join(out_dir, 'icon_duplicate_remover.svg'), 'w') as f: f.write(duplicate_svg)

print(f"Creati {len(os.listdir(out_dir))} file in {out_dir}")
