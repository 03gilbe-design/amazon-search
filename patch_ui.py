import sys
import re

path = r'C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements\webui\templates\categorize.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add D3 and Venn.js to block scripts
head_patch = '''
<script src="https://d3js.org/d3.v7.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/venn.js@0.2.20/venn.min.js"></script>
<style>
.venn-circle path { fill-opacity: 0.5; }
.venn-circle text { font-size: 14px; font-weight: bold; fill: #333; }
.venn-intersection text { 
    font-size: 11px; 
    font-weight: 800; 
    fill: white !important; 
    filter: drop-shadow(0px 1px 2px rgba(0,0,0,0.8));
}
.palette-btn { display:inline-block; width:24px; height:24px; border-radius:12px; cursor:pointer; border:2px solid transparent; margin-right:8px; box-shadow:0 2px 4px rgba(0,0,0,0.2); }
.palette-btn:hover { border-color:#fff; box-shadow:0 0 8px rgba(0,0,0,0.6); }

/* Migliore divisione Sunflower */
#sf-left-pane {
    background: linear-gradient(135deg, rgba(231,76,60,0.05) 0%, rgba(231,76,60,0.2) 100%);
    border-right: 2px dashed rgba(231,76,60,0.4);
}
#sf-right-pane {
    background: linear-gradient(135deg, rgba(46,204,113,0.05) 0%, rgba(46,204,113,0.2) 100%);
    border-left: 2px dashed rgba(46,204,113,0.4);
}
</style>
'''
if 'd3.v7.min.js' not in text:
    text = text.replace('{% block scripts %}', '{% block scripts %}' + head_patch)

# 2. Move Venn Diagram to the top
venn_container = '''<div id="playground-venn" style="display:none; margin-top:20px; margin-bottom: 20px;">
      <h2 style="color:var(--text); font-size:1.1rem; margin-bottom:15px">Diagrammi di Venn (Incroci Ricerche)</h2>
      <div id="venn-diagram-target" style="background:#fff; border-radius:12px; padding:20px; box-shadow:0 4px 15px rgba(0,0,0,0.05); text-align:center; min-height:400px; position:relative;">
      </div>
    </div>'''

if 'id="playground-venn"' in text:
    text = re.sub(r'<div id="playground-venn".*?</div>\s*</div>', '', text, flags=re.DOTALL)
text = text.replace('<!-- SIFT Lightbox -->', venn_container + '\n\n      <!-- SIFT Lightbox -->')

# 3. Add Palette Picker and '+' to Sunflower Lanes
sunflower_patch = '''
        <!-- Sunflower Split View -->
        <div id="sunflower-split" style="display:none; width:100%; height:calc(100vh - 180px); min-height:600px; flex-direction:row; position:relative; overflow:hidden;">
          
          <div style="position:absolute; top:10px; left:50%; transform:translateX(-50%); z-index:100; background:rgba(255,255,255,0.9); padding:5px 15px; border-radius:20px; box-shadow:0 4px 10px rgba(0,0,0,0.1); display:flex; align-items:center;">
             <span style="font-size:0.75rem; font-weight:bold; margin-right:10px;">Palette:</span>
             <div class="palette-btn" style="background:#3498db" onclick="changePalette('#3498db')"></div>
             <div class="palette-btn" style="background:#9b59b6" onclick="changePalette('#9b59b6')"></div>
             <div class="palette-btn" style="background:#e67e22" onclick="changePalette('#e67e22')"></div>
             <div class="palette-btn" style="background:#34495e" onclick="changePalette('#34495e')"></div>
          </div>

          <div id="sf-left-pane" style="flex:1; position:relative; overflow:hidden;" ondragover="event.preventDefault(); this.style.opacity=0.8" ondragleave="this.style.opacity=1" ondrop="dropOnLane(event, 'Scartato')">
            <h3 style="position:absolute; top:20px; left:20px; color:#c0392b; font-size:1.5rem; text-shadow:0 2px 4px rgba(255,255,255,0.8); z-index:10;">Scartati ❌
               <button onclick="addCustomLaneCategory('Scartato')" style="font-size:1rem; border:none; background:#c0392b; color:#fff; width:24px; height:24px; border-radius:12px; cursor:pointer; margin-left:10px;">+</button>
            </h3>
            <div id="sf-left-content" style="width:100%; height:100%;"></div>
          </div>
          
          <div id="sf-right-pane" style="flex:1; position:relative; overflow:hidden;" ondragover="event.preventDefault(); this.style.opacity=0.8" ondragleave="this.style.opacity=1" ondrop="dropOnLane(event, 'Promosso')">
            <h3 style="position:absolute; top:20px; right:20px; color:#27ae60; font-size:1.5rem; text-shadow:0 2px 4px rgba(255,255,255,0.8); z-index:10; text-align:right;">
               <button onclick="addCustomLaneCategory('Promosso')" style="font-size:1rem; border:none; background:#27ae60; color:#fff; width:24px; height:24px; border-radius:12px; cursor:pointer; margin-right:10px;">+</button>
               Promossi ✅
            </h3>
            <div id="sf-right-content" style="width:100%; height:100%;"></div>
          </div>
'''
text = re.sub(r'<!-- Sunflower Split View -->.*?<div id="sf-right-content"[^>]*></div>\s*</div>', sunflower_patch, text, flags=re.DOTALL)


# 4. Modify venn drawing logic to use venn.js
js_venn_logic = '''
function renderVennDiagram(data) {
  const c = document.getElementById('venn-diagram-target');
  if(!c) return;
  c.innerHTML = '';
  
  if(!data || data.length === 0) {
    c.innerHTML = '<div style="padding:40px; color:var(--dim)">Nessun dato Venn disponibile.</div>';
    return;
  }
  
  // Mappa la struttura esistente per venn.js
  // I nostri data sono: [{ sets: ["A"], size: 10 }, { sets: ["A","B"], size: 2 }]
  const chart = venn.VennDiagram()
    .width(c.clientWidth || 800)
    .height(400);

  const div = d3.select("#venn-diagram-target");
  div.datum(data).call(chart);
  
  // Aggiungi tooltip (etichette con background colorato)
  div.selectAll("text")
    .style("fill", "white")
    .style("font-size", "11px")
    .style("font-weight", "bold");
    
  // Colora le intersezioni con background
  div.selectAll(".venn-intersection text")
    .each(function(d) {
        // Puoi aggiungere tspan per rendere più carino, 
        // oppure aggiungere un rettangolo dietro
        const bbox = this.getBBox();
        d3.select(this.parentNode).insert("rect", "text")
          .attr("x", bbox.x - 4)
          .attr("y", bbox.y - 2)
          .attr("width", bbox.width + 8)
          .attr("height", bbox.height + 4)
          .attr("fill", "rgba(0,0,0,0.6)")
          .attr("rx", "4");
    });
}
'''
if 'venn.VennDiagram' not in text:
    text = text.replace('function renderTermsDistribution() {', js_venn_logic + '\nasync function renderTermsDistribution() {')


# 5. Modify JS to handle drag and drop of groups and palette
js_additions = '''
window.currentPaletteColor = '#3498db';
function changePalette(color) {
    window.currentPaletteColor = color;
    document.querySelectorAll('.cluster-bubble, .sf-node').forEach(el => {
        el.style.backgroundColor = color;
    });
}

function addCustomLaneCategory(side) {
    const catName = prompt("Nome nuova categoria per " + side + ":");
    if (catName) {
        addCategoryAPI(catName); // Supponendo che aggiorni existing_cats globali
        alert("Categoria aggiunta! Riassegna i prodotti.");
    }
}

function dropOnLane(event, side) {
    event.preventDefault();
    event.currentTarget.style.opacity = 1;
    const data = event.dataTransfer.getData("text/plain");
    
    // Possiamo supportare sia singoli ASIN che interi gruppi (cluster ID)
    if (data.startsWith('cluster_')) {
        const clusterId = parseInt(data.split('_')[1]);
        const cluster = window.lastClusters.find(c => c.id === clusterId);
        if (cluster) {
            cluster.products.forEach(p => {
                p.category = side;
                fetch('/api/set_category', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({job_id: window.JOB_ID, asin: p.asin, category: side})
                });
            });
            alert("Gruppo assegnato a " + side);
            renderCatList(); // Forza ricaricamento
        }
    } else {
        const pObj = ALL_PRODUCTS.find(x => x.asin === data);
        if(pObj) {
            pObj.category = side;
            fetch('/api/set_category', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({job_id: window.JOB_ID, asin: pObj.asin, category: side})
            });
            renderCatList();
        }
    }
}
'''
if 'function dropOnLane' not in text:
    text = text.replace('// 📌 Init 📌', js_additions + '\n// 📌 Init 📌')


with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('SUCCESS')
