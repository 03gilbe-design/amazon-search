from pathlib import Path
import re

path = rstr(Path.home() / "amazon_search", ".claude", "worktrees", "amazon-improvements", "webui", "templates", "categorize.html")
text = open(path, 'r', encoding='utf-8').read()

start_idx = text.find('async function renderVennDiagram(bubbles)')
end_idx = text.find('async function renderTermsDistribution()')

replacement = """async function renderVennDiagram(bubbles) {
  const container = document.getElementById('venn-diagram-target');
  if (!container) return;
  container.innerHTML = '';

  // Raccogli tutte le parole e i set
  let allWords = {};
  bubbles.forEach(b => {
    b.macro.forEach(m => {
      const w = m.word;
      if(!allWords[w]) allWords[w] = { count: 0, asins: new Set() };
      allWords[w].count += m.count;
      (m.thumbs || []).forEach(thumb => {
          const p = ALL_PRODUCTS.find(x => x.thumbnail === thumb);
          if (p) allWords[w].asins.add(p.asin);
      });
    });
  });

  const topWords = Object.keys(allWords).sort((a,b) => allWords[b].count - allWords[a].count).slice(0, 5);
  if(topWords.length === 0) {
     container.innerHTML = '<div style="padding:40px; color:var(--dim)">Nessun dato Venn disponibile.</div>';
     return;
  }

  // Costruisci l'array data per venn.js
  let data = [];
  // I nodi singoli
  topWords.forEach(w => {
    data.push({sets: [w], size: allWords[w].asins.size || 1});
  });
  // Le intersezioni (solo coppie per non appesantire)
  for(let i=0; i<topWords.length; i++){
     for(let j=i+1; j<topWords.length; j++){
         const w1 = topWords[i];
         const w2 = topWords[j];
         let intersectionSize = 0;
         allWords[w1].asins.forEach(asin => {
             if(allWords[w2].asins.has(asin)) intersectionSize++;
         });
         if(intersectionSize > 0) {
             data.push({sets: [w1, w2], size: intersectionSize});
         }
     }
  }

  const chart = venn.VennDiagram().width(container.clientWidth || 800).height(400);
  const div = d3.select("#venn-diagram-target");
  div.datum(data).call(chart);
  
  div.selectAll("text").style("fill", "white").style("font-size", "11px").style("font-weight", "bold");
  div.selectAll(".venn-intersection text").each(function(d) {
        const bbox = this.getBBox();
        d3.select(this.parentNode).insert("rect", "text")
          .attr("x", bbox.x - 4).attr("y", bbox.y - 2).attr("width", bbox.width + 8)
          .attr("height", bbox.height + 4).attr("fill", "rgba(0,0,0,0.6)").attr("rx", "4");
  });
}

"""

if start_idx != -1 and end_idx != -1:
    text = text[:start_idx] + replacement + text[end_idx:]
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print('Replaced')
else:
    print('Indices not found!')
