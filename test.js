
const JOB_ID = "";
const ALL_PRODUCTS = "";
const CAT_COLORS = ['#ff6600','#4a9eff','#3dba6a','#9b6dff','#ffcc44','#ff4466','#00ccbb','#ff88cc'];

let categories = "";
// le categorie create sopravvivono al reload (per job)
try {
  const saved = JSON.parse(localStorage.getItem('cats_' + JOB_ID) || '[]');
  saved.forEach(c => { if (!categories.includes(c)) categories.push(c); });
} catch (e) {}
function persistCats() { localStorage.setItem('cats_' + JOB_ID, JSON.stringify(categories)); }
if (categories.length === 0) categories = ['Other'];
let currentIdx  = 0;
let skipAssigned = false;
let currentView = 'playground';

// ── Helpers ──────────────────────────────────────────────────────────────
function catColor(i) { return CAT_COLORS[i % CAT_COLORS.length]; }

function autoSuggest(product) {
  const text = (product.title + ' ' + product.brand).toLowerCase();
  for (const cat of categories) {
    const words = cat.toLowerCase().split(/[\s,]+/);
    if (words.some(w => w.length > 3 && text.includes(w))) return cat;
  }
  return null;
}

async function assignCategory(asin, cat, skipHistory) {
  const p = ALL_PRODUCTS.find(x => x.asin === asin);
  if (!skipHistory) HISTORY.push({ asin, prevCat: p ? p.category : null });
  await fetch('/api/set_category', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ job_id: JOB_ID, asin, category: cat }),
  });
  if (p) p.category = cat;
}

// ── Sunflower ─────────────────────────────────────────────────────────────

const HISTORY = [];  // {asin, prevCat} per undo con freccia sinistra

function renameCategory(cat) {
  const name = prompt('Rename "' + cat + '" to:', cat);
  if (!name || name === cat) return;
  categories[categories.indexOf(cat)] = name;
  persistCats();
  ALL_PRODUCTS.filter(p => p.category === cat)
    .forEach(p => assignCategory(p.asin, name));
  renderSunflower();
}

let _undoDelete = null;
function deleteCategory(cat) {
  const affected = ALL_PRODUCTS.filter(p => p.category === cat).map(p => p.asin);
  categories.splice(categories.indexOf(cat), 1);
  persistCats();
  affected.forEach(a => assignCategory(a, null, true));
  renderCurrentProduct();
  // niente popup di conferma: toast con Undo per 5 secondi
  const toast = document.getElementById('sf-toast');
  document.getElementById('sf-toast-msg').textContent = 'Category "' + cat + '" deleted';
  toast.style.display = 'flex';
  _undoDelete = { cat, affected };
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { toast.style.display = 'none'; _undoDelete = null; }, 5000);
}
function undoDelete() {
  if (!_undoDelete) return;
  categories.push(_undoDelete.cat);
  persistCats();
  _undoDelete.affected.forEach(a => assignCategory(a, _undoDelete.cat, true));
  _undoDelete = null;
  document.getElementById('sf-toast').style.display = 'none';
  renderCurrentProduct();
}


function fitSunflower() {
  const wrap = document.getElementById('sunflower');
  const h = Math.max(420, window.innerHeight - wrap.getBoundingClientRect().top - 40);
  wrap.style.height = h + 'px';
  renderSunflower();
}
window.addEventListener('resize', fitSunflower);
fitSunflower();

document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT') return;
  if (e.key === 'ArrowRight') { skipCurrent(); }
  if (e.key === 'ArrowLeft') {
    currentIdx = Math.max(0, currentIdx - 1);
    renderCurrentProduct();
  }
  if (e.key === 'z' || e.key === 'Z') {
    const last = HISTORY.pop();
    if (last) assignCategory(last.asin, last.prevCat, true).then(renderCurrentProduct);
  }
});

function isGroupMode() { return document.getElementById('group-mode').checked; }
function groupSize() { return parseInt(document.getElementById('group-size').value, 10); }

// group = next N unassigned that the code considers together: same suggested
// category first, then sequential fill. Draggable singles; click circle = all.
function currentGroup() {
  const n = groupSize();
  const un = ALL_PRODUCTS.filter(p => !p.category);
  if (!un.length) return [];
  const seed = un[currentIdx % un.length];
  const key = autoSuggest(seed);
  const same = un.filter(p => autoSuggest(p) === key && p !== seed);
  return [seed, ...same, ...un.filter(p => p !== seed && !same.includes(p))].slice(0, n);
}

function renderGroupCenter(group) {
  const wrap = document.getElementById('sf-img-wrap');
  wrap.querySelectorAll('.sf-group-img').forEach(el => el.remove());
  document.getElementById('sf-img').style.display = 'none';
  document.getElementById('sf-ph').style.display = 'none';
  group.forEach((p, i) => {
    const img = document.createElement('img');
    img.className = 'sf-group-img';
    img.draggable = true;
    if (p.thumbnail && /^https?:\/\//.test(p.thumbnail)) img.src = p.thumbnail;
    img.title = p.title || '';
    const ang = (2 * Math.PI * i / group.length);
    img.style.cssText = 'position:absolute;width:80px;height:80px;object-fit:contain;'
      + 'border-radius:8px;cursor:grab;'
      + 'left:' + (60 + Math.cos(ang) * 48) + 'px;top:' + (60 + Math.sin(ang) * 48) + 'px;'
      + 'transform:rotate(' + ((i * 37) % 21 - 10) + 'deg);z-index:' + (5 + i);
    img.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', p.asin);
      img.style.opacity = '.4';
    });
    img.addEventListener('dragend', () => { img.style.opacity = '1'; });
    wrap.appendChild(img);
  });
}

// album stacks: pila ordinata a ventaglio, appesa FUORI dal cerchio lungo il suo
// raggio (mai sopra il cerchio: i click restano liberi). Trascinabili per spostarle.
function renderStacks(sf, cat, ccx, ccy, angle, color, CS) {
  const items = ALL_PRODUCTS.filter(p => p.category === cat && p.thumbnail
                                    && /^https?:\/\//.test(p.thumbnail));
  const thumbs = items.slice(-6);
  // nodi in alto/basso: ventaglio appiattito verso l'orizzontale, cosi' non buca
  // il bordo dello schermo; poi comunque clamp dentro il contenitore
  let dirx = Math.cos(angle), diry = Math.sin(angle) * 0.45;
  const L = Math.hypot(dirx, diry) || 1; dirx /= L; diry /= L;
  const perx = -diry, pery = dirx;
  const base = CS / 2 + 38;
  const W = sf.clientWidth || 900, H = sf.clientHeight || 640;
  thumbs.forEach((p, i) => {
    const im = document.createElement('img');
    im.className = 'sf-circle sf-stack-img';
    im.src = p.thumbnail;
    im.title = (p.title || '').slice(0, 60) + ' \u2014 drag to move';
    im.draggable = true;
    const along = base + i * 25;
    const side = (i % 2 ? 1 : -1) * 10;
    const jit = (h => (h % 9) - 4)([...p.asin].reduce((a, c) => a + c.charCodeAt(0), 0));
    const px = Math.min(Math.max(ccx + dirx * along + perx * side - 29, 4), W - 62);
    const py = Math.min(Math.max(ccy + diry * along + pery * side - 29, 4), H - 62);
    im.style.cssText = 'position:absolute;width:58px;height:58px;object-fit:contain;'
      + 'left:' + px + 'px;top:' + py + 'px;'
      + 'transform:rotate(' + jit + 'deg);z-index:' + (8 + i);
    im.addEventListener('dragstart', e => { e.dataTransfer.setData('text/plain', p.asin); im.style.opacity = '.4'; });
    im.addEventListener('dragend', () => { im.style.opacity = '1'; });
    sf.appendChild(im);
  });
  if (items.length > 6) {
    const more = document.createElement('div');
    more.className = 'sf-circle';
    more.style.cssText = 'position:absolute;width:auto;height:auto;border:none;background:none;'
      + 'font-size:.66rem;color:#7a746b;z-index:9;'
      + 'left:' + Math.min(Math.max(ccx + dirx * (base + 6 * 25) - 14, 4), W - 40) + 'px;'
      + 'top:'  + Math.min(Math.max(ccy + diry * (base + 6 * 25), 4), H - 30) + 'px;';
    more.textContent = '+' + (items.length - 6);
    sf.appendChild(more);
  }
}

function renderSunflower() {
  const sf = document.getElementById('sunflower');
  sf.querySelectorAll('.sf-circle, .sf-circle-holder').forEach(el => el.remove());

  const allCats = [...categories, '+'];
  const n = allCats.length;
  const W = sf.clientWidth || 900, H = sf.clientHeight || 640;
  const cx = W / 2, cy = H / 2;
  // ELLISSE: schermo rettangolare, i nodi usano la larghezza
  const rx = Math.max(W / 2 - 250, 230), ry = Math.max(H / 2 - 150, 170);
  const counts = Object.fromEntries(categories.map(c =>
    [c, ALL_PRODUCTS.filter(p => p.category === c).length]));
  const maxCount = Math.max(1, ...Object.values(counts));

  allCats.forEach((cat, i) => {
    const angle = (2 * Math.PI * i / n) - Math.PI / 2;
    // pochi elementi = cerchio piu' piccolo e piu' lontano (fa spazio ai grossi)
    const cnt = counts[cat] || 0;
    const ratio = cat === '+' ? 0.5 : cnt / maxCount;
    const CS = cat === '+' ? 72 : Math.round(72 + 40 * ratio);
    const push = cat === '+' ? 1 : (1 + 0.14 * (1 - ratio));
    const ccx = cx + Math.cos(angle) * rx * push;
    const ccy = cy + Math.sin(angle) * ry * push;

    const circle = document.createElement('div');
    circle.className = 'sf-circle' + (cat === '+' ? ' add-cat' : '');
    circle.style.cssText = 'left:0;top:0;width:' + CS + 'px;height:' + CS + 'px;'
      + 'transition:width .3s,height .3s';
    circle.style.borderColor = cat !== '+' ? catColor(i) + '88' : '';

    const holder = document.createElement('div');
    holder.className = 'sf-circle-holder';
    holder.style.cssText = 'position:absolute;left:' + (ccx - CS / 2) + 'px;top:'
      + (ccy - CS / 2) + 'px;width:' + CS + 'px;height:' + CS + 'px;z-index:25;cursor:pointer';

    if (cat === '+') {
      circle.textContent = '+';
      circle.title = 'Add new category';
      holder.onclick = () => {
        document.getElementById('sf-overlay').classList.remove('collapsed');
        document.getElementById('new-cat-input').focus();
      };
    } else {
      circle.textContent = cat;
      if (cat.length > 14) circle.style.fontSize = '0.66rem';
      circle.dataset.cat = cat;
      const group = isGroupMode() ? currentGroup() : null;
      const prod = ALL_PRODUCTS[currentIdx % ALL_PRODUCTS.length];
      const suggested = autoSuggest(group ? group[0] : prod);
      if (suggested === cat) circle.classList.add('suggested');
      holder.onclick = () => {
        const targets = group || [prod];
        Promise.all(targets.map(t => assignCategory(t.asin, cat)))
          .then(() => advanceSunflower());
      };
      holder.addEventListener('dragover', e => { e.preventDefault(); circle.classList.add('suggested'); });
      holder.addEventListener('dragleave', () => { if (suggested !== cat) circle.classList.remove('suggested'); });
      holder.addEventListener('drop', e => {
        e.preventDefault();
        const asin = e.dataTransfer.getData('text/plain');
        if (asin) assignCategory(asin, cat).then(() => renderCurrentProduct());
      });
      const tools = document.createElement('div');
      tools.className = 'sf-tools';
      tools.style.cssText += 'top:-10px;right:-6px;position:absolute';
      const bEdit = document.createElement('div');
      bEdit.className = 'sf-tool'; bEdit.textContent = '\u270E'; bEdit.title = 'Rename';
      bEdit.onclick = e => { e.stopPropagation(); renameCategory(cat); };
      const bDel = document.createElement('div');
      bDel.className = 'sf-tool del'; bDel.textContent = '\u2715'; bDel.title = 'Delete';
      bDel.onclick = e => { e.stopPropagation(); deleteCategory(cat); };
      tools.append(bEdit, bDel);
      holder.appendChild(tools);
      renderStacks(sf, cat, ccx, ccy, angle, catColor(i), CS);
    }
    holder.insertBefore(circle, holder.firstChild);
    sf.appendChild(holder);
  });
}

function advanceSunflower() {
  currentIdx++;
  if (skipAssigned) {
    while (currentIdx < ALL_PRODUCTS.length && ALL_PRODUCTS[currentIdx].category) {
      currentIdx++;
    }
  }
  renderCurrentProduct();
}

function renderCurrentProduct() {
  // Wrap around
  let idx = currentIdx % ALL_PRODUCTS.length;
  if (ALL_PRODUCTS.length === 0) return;

  document.getElementById('sf-img-wrap').querySelectorAll('.sf-group-img').forEach(el => el.remove());
  if (isGroupMode()) {
    const group = currentGroup();
    renderGroupCenter(group);
    const first = group[0] || ALL_PRODUCTS[idx];
    document.getElementById('sf-title').textContent = group.length + ' products — drag one, or click a circle for all';
    document.getElementById('sf-price').textContent = '';
    document.getElementById('sf-brand').textContent = first.title ? first.title.slice(0, 50) : '';
    document.getElementById('sf-current-cat').textContent = 'group';
    document.getElementById('sf-suggest').textContent = autoSuggest(first) || '—';
    const done = ALL_PRODUCTS.filter(x => x.category).length;
    document.getElementById('sf-progress').textContent = done + ' / ' + ALL_PRODUCTS.length;
    document.getElementById('sf-bar').style.width = (done / ALL_PRODUCTS.length * 100) + '%';
    renderSunflower();
    return;
  }

  const p = ALL_PRODUCTS[idx];
  const img = document.getElementById('sf-img');
  const ph  = document.getElementById('sf-ph');
  if (p.thumbnail) {
    img.src = p.thumbnail;
    img.style.display = 'block';
    ph.style.display  = 'none';
  } else {
    img.style.display = 'none';
    ph.style.display  = 'block';
  }

  document.getElementById('sf-amazon').href = p.link || '#';
  document.getElementById('sf-title').textContent = p.title || '—';
  document.getElementById('sf-price').textContent = p.price_str || '';
  document.getElementById('sf-brand').textContent = p.brand ? ('Brand: ' + p.brand) : '';
  document.getElementById('sf-current-cat').textContent = p.category || 'unassigned';

  const suggested = autoSuggest(p);
  document.getElementById('sf-suggest').textContent = suggested || '—';

  const done = ALL_PRODUCTS.filter(x => x.category).length;
  document.getElementById('sf-progress').textContent = done + ' / ' + ALL_PRODUCTS.length;
  document.getElementById('sf-bar').style.width = (done / ALL_PRODUCTS.length * 100) + '%';

  renderSunflower();
}

function skipCurrent() {
  currentIdx++;
  renderCurrentProduct();
}

function toggleSkipAssigned() {
  skipAssigned = !skipAssigned;
  document.getElementById('skip-assigned-label').textContent =
    skipAssigned ? '✓ Skip assigned' : 'Skip assigned';
  renderCurrentProduct();
}

function addCategory() {
  const input = document.getElementById('new-cat-input');
  const name  = input.value.trim();
  if (!name || categories.includes(name)) { input.value = ''; return; }
  categories.push(name);
  persistCats();
  input.value = '';
  renderCatList();
  renderSunflower();
}

function addPlaygroundCategory() {
  const input = document.getElementById('play-new-cat-input');
  const name = input.value.trim();
  if (!name || categories.includes(name)) { input.value = ''; return; }
  categories.push(name);
  persistCats();
  input.value = '';
  runClustering();
  renderCatList();
  renderSunflower();
}

function renderCatList() {
  const wrap = document.getElementById('cat-list-wrap');
  wrap.innerHTML = '';
  categories.forEach((cat, i) => {
    const span = document.createElement('span');
    span.className = 'chip';
    span.style.borderColor = catColor(i) + '66';
    span.style.color = catColor(i);
    span.style.cursor = 'pointer';
    span.textContent = cat;
    span.onclick = () => {
      const prod = ALL_PRODUCTS[currentIdx % ALL_PRODUCTS.length];
      assignCategory(prod.asin, cat).then(() => advanceSunflower());
    };
    wrap.appendChild(span);
  });
}

// ── Kanban ────────────────────────────────────────────────────────────────
function renderKanban() {
  const board = document.getElementById('kanban-board');
  board.innerHTML = '';

  const cols = ['Unassigned', ...categories];
  cols.forEach((col, ci) => {
    const colEl = document.createElement('div');
    colEl.className = 'kanban-col glass';
    colEl.innerHTML = `
      <div class="kanban-col-head" style="background:${catColor(ci-1)}22;color:${ci===0?'var(--dim)':catColor(ci-1)}">
        <span style="width:6px;height:6px;border-radius:50%;background:${ci===0?'var(--muted)':catColor(ci-1)};display:inline-block"></span>
      </div>
      <div class="kanban-items" id="kanban-col-${ci}"></div>`;
    // nome categoria e data-col via API DOM: è testo utente, non markup (XSS)
    colEl.querySelector('.kanban-col-head').append(document.createTextNode(' ' + col));
    colEl.querySelector('.kanban-items').dataset.col = col;
    board.appendChild(colEl);

    const items = colEl.querySelector('.kanban-items');
    items.addEventListener('dragover', e => { e.preventDefault(); items.classList.add('drag-over'); });
    items.addEventListener('dragleave', () => items.classList.remove('drag-over'));
    items.addEventListener('drop', e => {
      e.preventDefault();
      items.classList.remove('drag-over');
      const asin = e.dataTransfer.getData('text/plain');
      const newCat = col === 'Unassigned' ? '' : col;
      assignCategory(asin, newCat).then(() => renderKanban());
    });

    const prods = col === 'Unassigned'
      ? ALL_PRODUCTS.filter(p => !p.category)
      : ALL_PRODUCTS.filter(p => p.category === col);

    prods.forEach(p => {
      const item = document.createElement('div');
      item.className = 'kanban-item';
      item.draggable = true;
      item.dataset.asin = p.asin;
      // DOM APIs, non innerHTML: titolo/thumbnail sono dati Amazon non fidati (XSS)
      if (p.thumbnail && /^https?:\/\//.test(p.thumbnail)) {
        const img = document.createElement('img');
        img.className = 'kanban-img';
        img.loading = 'eager';
        img.onerror = () => { img.style.display = 'none'; };
        img.src = p.thumbnail;
        item.appendChild(img);
      } else {
        const ph = document.createElement('div');
        ph.className = 'kanban-img';
        ph.style.cssText = 'display:flex;align-items:center;justify-content:center;color:var(--muted)';
        ph.textContent = '▦';
        item.appendChild(ph);
      }
      const label = document.createElement('div');
      label.className = 'kanban-label';
      label.textContent = (p.title || '').slice(0, 40);
      item.appendChild(label);
      item.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', p.asin);
        item.classList.add('dragging');
      });
      item.addEventListener('dragend', () => item.classList.remove('dragging'));
      items.appendChild(item);
    });
  });
}

// ── View toggle & Switch Tab ───────────────────────────────────────────────────
// HTML per Scene Match
document.getElementById('view-kanban').insertAdjacentHTML('afterend', `
<!-- VIEW: SCENE MATCH -->
<div id="view-scene" style="display: none; max-width: 1000px; margin: 40px auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:15px;">
    <div>
      <h2 style="margin-top:0; font-size:1.5rem; color:var(--text);">Ricerca Automatica di Prodotti nelle Scene</h2>
      <p style="color:var(--dim); font-size:0.85rem; margin-bottom:0;">
        L'Intelligenza Artificiale (SIFT+RANSAC) rileva i prodotti inseriti nelle foto ambientali di altri prodotti.
      </p>
    </div>
    
    <!-- Pannello Controlli Grafo -->
    <div style="background:#f8f9fa; border:1px solid var(--border); border-radius:10px; padding:12px 18px; display:flex; gap:20px; align-items:center; flex-wrap:wrap;">
      <!-- Slider Inliers -->
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:0.75rem; font-weight:bold; color:var(--sub); white-space:nowrap;">Punti Geometrici (Soglia Inliers):</span>
        <input type="range" id="scene-inliers-threshold" min="6" max="30" step="1" value="12" style="width:100px;" oninput="document.getElementById('scene-inliers-val').textContent=this.value; applySceneFilters();">
        <span id="scene-inliers-val" style="font-size:0.75rem; font-weight:bold; color:var(--orange);">12</span>
      </div>
      
      <!-- Selettore Prodotto Singolo -->
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:0.75rem; font-weight:bold; color:var(--sub); white-space:nowrap;">Filtra Prodotto:</span>
        <select id="scene-product-filter" style="font-size:0.75rem; padding:4px 8px; border-radius:4px; border:1px solid var(--border); max-width:200px; cursor:pointer;" onchange="applySceneFilters()">
          <option value="all">Tutti i prodotti (Grafo Unico)</option>
        </select>
      </div>
      
      <button id="scene-run-btn" class="btn btn-outline btn-sm" onclick="runSceneMatch()" style="font-weight:bold;">Aggiorna</button>
    </div>
  </div>
  
  <div id="scene-match-result" style="margin-top: 20px;">
    <!-- Grafo Interattivo -->
    <div id="scene-graph-container" style="position:relative; width:100%; height:500px; background:#f8f9fa; border:2px solid var(--border); border-radius:16px; overflow:hidden; display:none; user-select:none;">
      <!-- SVG per le linee di collegamento -->
      <svg id="scene-graph-svg" style="position:absolute; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:1;"></svg>
      <!-- Nodi HTML fluttuanti -->
      <div id="scene-graph-nodes" style="position:absolute; top:0; left:0; width:100%; height:100%; z-index:2; pointer-events:none;"></div>
      
      <!-- Legenda -->
      <div style="position:absolute; bottom:15px; left:15px; background:rgba(255,255,255,0.9); padding:10px; border-radius:8px; border:1px solid var(--border); font-size:0.7rem; z-index:10; pointer-events:auto;">
        <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
          <span style="display:inline-block; width:10px; height:10px; background:#3498db; border-radius:50%;"></span> Prodotto Isolato (Origine)
        </div>
        <div style="display:flex; align-items:center; gap:8px;">
          <span style="display:inline-block; width:10px; height:10px; background:#e67e22; border-radius:50%;"></span> Scena Ambientale
        </div>
      </div>
    </div>
    
    <!-- Dettaglio SIFT all'occorrenza -->
    <div id="scene-detail-card" style="display:none; background:#fff; border:2px solid var(--orange); border-radius:12px; padding:20px; box-shadow:0 8px 25px rgba(0,0,0,0.06); margin-top:20px;">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; border-bottom:1px dashed var(--border); padding-bottom:10px;">
        <h4 style="margin:0; color:#2c3e50;">Dettaglio Incrocio Geometrico (SIFT)</h4>
        <button onclick="document.getElementById('scene-detail-card').style.display='none'" class="btn btn-outline btn-sm">Chiudi</button>
      </div>
      <div style="display:flex; gap:20px; flex-wrap:wrap;">
        <div style="flex:1; min-width:300px; text-align:center;">
          <img id="scene-detail-img" src="" style="max-width:100%; border-radius:8px; border:1px solid var(--border);" />
        </div>
        <div style="flex:1; min-width:200px; display:flex; flex-direction:column; justify-content:center;">
          <p style="margin:0 0 10px 0; font-size:0.9rem;"><b>Prodotto:</b> <span id="scene-detail-p1"></span></p>
          <p style="margin:0 0 10px 0; font-size:0.9rem;"><b>Trovato nella Scena di:</b> <span id="scene-detail-p2"></span></p>
          <p style="margin:0; font-size:0.9rem;"><b>Punti Geometrici Corrispondenti:</b> <b id="scene-detail-inliers" style="color:var(--orange);"></b></p>
        </div>
      </div>
    </div>
    
    <!-- Elenco Match Dettagliato (Prod1 + OpenCV SIFT + Prod2) -->
    <div id="scene-match-list-wrapper" style="margin-top: 40px; display:none;">
      <h3 style="color:#2c3e50; font-size:1.2rem; margin-bottom:15px; border-bottom:2px solid var(--orange); padding-bottom:8px;">Lista Incroci Fotografici nel Dataset</h3>
      <div id="scene-match-list" style="display:flex; flex-direction:column; gap:25px;"></div>
    </div>
  </div>
</div>
`);
document.getElementById('view-scene').insertAdjacentHTML('afterend', `
<!-- VIEW: TERMS DISTRIBUTION -->
<div id="view-terms" style="display: none; max-width: 1200px; margin: 40px auto; background: #fff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05);">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div>
      <h2 style="margin-top:0; font-size:1.5rem; color:#8e44ad;">Mappa Mentale delle Parole (Gerarchia)</h2>
      <p style="color:var(--dim); font-size:0.9rem; margin-bottom:0;">
        Come hai suggerito, le parole sono ora raggruppate <b>dentro le categorie</b>!
      </p>
    </div>
    
    <!-- Controlli Utente con Slider -->
    <div style="background:#f8f9fa; padding:15px; border-radius:10px; border:1px solid var(--border); display:flex; gap:25px; align-items:center; flex-wrap:wrap;">
      <!-- Slider Macro-raggruppamento (Threshold) -->
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:0.75rem; font-weight:bold; color:var(--sub); white-space:nowrap;">Macro-raggruppamento (Soglia %):</span>
        <input type="range" id="terms-threshold" min="10" max="90" step="5" value="35" style="width:120px;" oninput="document.getElementById('terms-threshold-val').textContent=this.value+'%'; renderTermsDistribution();">
        <span id="terms-threshold-val" style="font-size:0.75rem; font-weight:bold; color:#8e44ad; min-width:30px;">35%</span>
      </div>
      
      <!-- Slider Sotto-raggruppamenti (Nicchie) -->
      <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:0.75rem; font-weight:bold; color:var(--sub); white-space:nowrap;">Sotto-raggruppamenti (Nicchie):</span>
        <input type="range" id="terms-maxniche" min="5" max="100" step="5" value="30" style="width:120px;" oninput="document.getElementById('terms-maxniche-val').textContent=this.value; renderTermsDistribution();">
        <span id="terms-maxniche-val" style="font-size:0.75rem; font-weight:bold; color:#8e44ad; min-width:20px;">30</span>
      </div>
    </div>
  </div>
  
  <p style="color:var(--dim); font-size:0.8rem; margin-top:10px; margin-bottom:30px;">
    <i>Passa il mouse (o clicca) sopra ogni parola per vedere un'anteprima fotografica dei prodotti!</i>
  </p>
  
  <div id="terms-hierarchy-container" style="display:flex; flex-direction:column; gap:30px;"></div>
</div>
`);

function autoTuneTerms() {
  if (typeof ALL_PRODUCTS === 'undefined' || ALL_PRODUCTS.length === 0) return;
  
  const categoriesGroups = {};
  ALL_PRODUCTS.forEach(p => {
    const cat = p.category || "Generico";
    if(!categoriesGroups[cat]) categoriesGroups[cat] = [];
    categoriesGroups[cat].push(p);
  });
  
  let totalDocs = 0;
  let countCats = 0;
  Object.keys(categoriesGroups).forEach(c => {
    if (categoriesGroups[c].length >= 2) {
      totalDocs += categoriesGroups[c].length;
      countCats++;
    }
  });
  
  const avgDocSize = countCats > 0 ? totalDocs / countCats : ALL_PRODUCTS.length;
  
  // 1. Sotto-raggruppamenti (Nicchie): proporzionale alla dimensione media del pool
  const autoMaxNiche = Math.min(60, Math.max(15, Math.round(avgDocSize / 5)));
  
  // 2. Macro-raggruppamento (Threshold %): cerca il punto ottimale per ottenere tra 4 e 7 parole chiave
  let bestThreshold = 35;
  let bestScore = Infinity;
  
  const stop_words = new Set(["il","lo","la","i","gli","le","un","uno","una","di","a","da","in","con","su","per","tra","fra","e","o","ma","se","che","non","del","della","degli","delle","al","alla","agli","alle","dal","dalla","dagli","dalle","nel","nella","negli","nelle","col","coi","sul","sulla","sugli","sulle","cm","mm","kg","g","ml","l"]);
  
  for (let t = 10; t <= 80; t += 5) {
    const tVal = t / 100;
    let totalMacroWords = 0;
    
    Object.keys(categoriesGroups).forEach(catName => {
      const items = categoriesGroups[catName];
      const docCount = items.length;
      if (docCount < 2) return;
      
      const wordDocMap = {};
      items.forEach(p => {
        const title = (p.title || "").toLowerCase();
        const matches = title.match(/[a-z]{3,}/g) || [];
        const words = [...new Set(matches)];
        words.forEach(w => {
          if (!stop_words.has(w)) {
            if (!wordDocMap[w]) wordDocMap[w] = 0;
            wordDocMap[w]++;
          }
        });
      });
      
      let catMacroWords = 0;
      Object.keys(wordDocMap).forEach(w => {
        if (wordDocMap[w] / docCount > tVal) {
          catMacroWords++;
        }
      });
      totalMacroWords += catMacroWords;
    });
    
    const avgMacroWords = countCats > 0 ? totalMacroWords / countCats : 0;
    // Target ottimale: circa 5.5 macro parole descrittive per categoria
    const penalty = Math.abs(avgMacroWords - 5.5);
    if (penalty < bestScore) {
      bestScore = penalty;
      bestThreshold = t;
    }
  }
  
  // Applica i valori calcolati agli elementi HTML degli slider e aggiorna i relativi testi
  const thresholdEl = document.getElementById('terms-threshold');
  const thresholdValEl = document.getElementById('terms-threshold-val');
  if (thresholdEl && thresholdValEl) {
    thresholdEl.value = bestThreshold;
    thresholdValEl.textContent = bestThreshold + '%';
  }
  
  const maxNicheEl = document.getElementById('terms-maxniche');
  const maxNicheValEl = document.getElementById('terms-maxniche-val');
  if (maxNicheEl && maxNicheValEl) {
    maxNicheEl.value = autoMaxNiche;
    maxNicheValEl.textContent = autoMaxNiche;
  }
}

async function renderTermsDistribution() {
  const cont = document.getElementById('terms-hierarchy-container');
  
  if (!window.termsAutoTuned) {
    autoTuneTerms();
    window.termsAutoTuned = true;
  }
  
  const threshold = document.getElementById('terms-threshold') ? parseFloat(document.getElementById('terms-threshold').value) / 100 : 0.35;
  const maxNiche = document.getElementById('terms-maxniche') ? parseInt(document.getElementById('terms-maxniche').value) : 30;
  
  try {
  if (!window.cachedTermsBubbles || window.lastThreshold !== threshold || window.lastMaxNiche !== maxNiche) {
    cont.innerHTML = '<div style="text-align:center; padding:20px;"><div class="loading"></div><br/>Elaborazione istantanea nel browser...</div>';
    
    // Calcolo locale istantaneo in Javascript!
    await new Promise(r => setTimeout(r, 10)); // Piccolo yield per il DOM
    
    const stop_words = new Set(["il","lo","la","i","gli","le","un","uno","una","di","a","da","in","con","su","per","tra","fra","e","o","ma","se","che","non","del","della","degli","delle","al","alla","agli","alle","dal","dalla","dagli","dalle","nel","nella","negli","nelle","col","coi","sul","sulla","sugli","sulle","cm","mm","kg","g","ml","l"]);
    
    const categoriesGroups = {};
    ALL_PRODUCTS.forEach(p => {
      const cat = p.category || "Generico";
      if(!categoriesGroups[cat]) categoriesGroups[cat] = [];
      categoriesGroups[cat].push(p);
    });
    
    const responseData = [];
    
    Object.keys(categoriesGroups).forEach(catName => {
      const items = categoriesGroups[catName];
      const docCount = items.length;
      if (docCount < 2) return;
      
      const wordDocMap = {};
      
      items.forEach(p => {
        const title = (p.title || "").toLowerCase();
        // Regex word boundary equivalent
        const matches = title.match(/[a-z]{3,}/g) || [];
        const words = [...new Set(matches)]; // unique words in this doc
        const thumb = p.thumbnail;
        
        words.forEach(w => {
          if (!stop_words.has(w)) {
            if (!wordDocMap[w]) wordDocMap[w] = [];
            if (thumb && !wordDocMap[w].includes(thumb)) {
              wordDocMap[w].push(thumb);
            }
          }
        });
      });
      
      const macroTerms = [];
      const nicheTerms = [];
      
      Object.keys(wordDocMap).forEach(w => {
        const thumbs = wordDocMap[w];
        const count = thumbs.length;
        if (count < 2) return;
        
        const pct = count / docCount;
        const item = { word: w, count: count, pct: Math.round(pct * 1000)/10, thumbs: thumbs.slice(0, 5) };
        
        if (pct > threshold) {
          macroTerms.push(item);
        } else {
          nicheTerms.push(item);
        }
      });
      
      macroTerms.sort((a,b) => b.count - a.count);
      nicheTerms.sort((a,b) => b.count - a.count);
      
      responseData.push({
        id: 'cat_' + catName.replace(/[^a-zA-Z0-9]/g, ''),
        category: catName,
        size: docCount,
        macro: macroTerms.slice(0, 15),
        niche: nicheTerms.slice(0, maxNiche)
      });
    });
    
    responseData.sort((a,b) => b.size - a.size);
    window.cachedTermsBubbles = responseData;
    window.lastThreshold = threshold;
    window.lastMaxNiche = maxNiche;
  }
  
  const bubbles = window.cachedTermsBubbles;
  
  if (!bubbles || bubbles.length === 0) {
    cont.innerHTML = '<span style="color:var(--dim)">Nessun dato testuale sufficiente.</span>';
    return;
  }
  
  const createBubble = (item, baseColor, blockIdx) => {
    let size = 11 + (item.pct / 100) * 16; 
    if (size > 22) size = 22;
    
    // Serializza le thumbs come stringa JSON sicura per il click
    const thumbsStr = encodeURIComponent(JSON.stringify(item.thumbs || []));
    
    return `<div style="display:inline-block; margin:2px;" class="term-bubble-wrapper">
      <div style="background:${baseColor}; color:white; border-radius:20px; padding:6px 12px; font-size:${size}px; font-weight:bold; box-shadow:0 2px 5px rgba(0,0,0,0.1); display:flex; align-items:center; gap:6px; cursor:pointer;"
           onclick="showTermPreview('${item.word}', '${thumbsStr}', ${blockIdx}, this)">
        ${item.word}
        <span style="background:rgba(255,255,255,0.3); border-radius:10px; padding:2px 6px; font-size:0.7em;">${item.count}</span>
      </div>
    </div>`;
  };
  
  let html = '';
  bubbles.forEach((b, idx) => {
    html += `
    <div id="terms-block-${idx}" class="terms-category-block" style="background:rgba(142, 68, 173, 0.04); border:2px solid rgba(142, 68, 173, 0.2); border-radius:16px; padding:20px; position:relative; transition: transform 0.3s ease;">
      <div style="position:absolute; top:-15px; left:20px; background:#8e44ad; color:white; padding:4px 16px; border-radius:12px; font-weight:bold; font-size:1.1rem; box-shadow:0 3px 6px rgba(0,0,0,0.15); display:flex; align-items:center; gap:10px;">
        ${b.category} <span style="font-size:0.8rem; opacity:0.8; margin-left:8px;">(${b.size} prodotti)</span>
        <div style="margin-left: 15px; display:flex; gap:5px;">
          <button onclick="moveBlock(this, -1)" title="Sposta Su" style="background:rgba(255,255,255,0.2); border:none; color:white; border-radius:4px; cursor:pointer; padding:2px 8px; font-size:0.9rem;">▲</button>
          <button onclick="moveBlock(this, 1)" title="Sposta Giù" style="background:rgba(255,255,255,0.2); border:none; color:white; border-radius:4px; cursor:pointer; padding:2px 8px; font-size:0.9rem;">▼</button>
        </div>
      </div>
      
      <div style="display:flex; gap:20px; margin-top:15px;">
          <div style="flex:1;">
            <h4 style="color:#e67e22; margin-top:0; margin-bottom:10px; font-size:0.9rem;">Parole Macro della Categoria</h4>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
              ${b.macro.length ? b.macro.map(i => createBubble(i, '#e67e22', idx)).join('') : '<span style="color:var(--dim); font-size:0.8rem;">Nessuna parola dominante condivisa</span>'}
            </div>
          </div>
          <div style="flex:2; border-left:1px dashed rgba(0,0,0,0.1); padding-left:20px;">
            <h4 style="color:#2980b9; margin-top:0; margin-bottom:10px; font-size:0.9rem;">Mini-Cluster (Nicchie e Brand)</h4>
            <div style="display:flex; flex-wrap:wrap; gap:8px;">
              ${b.niche.length ? b.niche.map(i => createBubble(i, '#3498db', idx)).join('') : '<span style="color:var(--dim); font-size:0.8rem;">Nessuna parola di nicchia o brand</span>'}
            </div>
          </div>
        </div>
        
        <!-- Sezione Preview Foto -->
        <div id="terms-preview-${idx}" style="display:none; margin-top:20px; border-top:2px dashed rgba(142, 68, 173, 0.2); padding-top:15px; background:rgba(255,255,255,0.6); border-radius:8px; padding:15px;">
           <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
             <span style="font-size:0.85rem; font-weight:bold; color:#2c3e50;">Prodotti con la parola "<span id="terms-preview-word-${idx}" style="color:#e67e22;"></span>":</span>
             <button onclick="document.getElementById('terms-preview-${idx}').style.display='none'" class="btn btn-outline btn-sm" style="font-size:0.65rem; padding:2px 8px;">Nascondi</button>
           </div>
           <div id="terms-preview-images-${idx}" style="display:flex; gap:12px; flex-wrap:wrap;"></div>
        </div>
      </div>
      `;
    });
    
    cont.innerHTML = html;
    
  } catch(e) {
    cont.innerHTML = `<span style="color:red">Errore elaborazione parole.</span>`;
  }
}

window.showTermPreview = function(word, thumbsStr, blockIdx, bubbleEl) {
  const thumbs = JSON.parse(decodeURIComponent(thumbsStr));
  const previewDiv = document.getElementById(`terms-preview-${blockIdx}`);
  const previewWord = document.getElementById(`terms-preview-word-${blockIdx}`);
  const previewImages = document.getElementById(`terms-preview-images-${blockIdx}`);
  
  if (!previewDiv || !previewImages) return;
  
  // Rimuovi evidenziatura da altri bubble nello stesso blocco
  const block = document.getElementById(`terms-block-${blockIdx}`);
  block.querySelectorAll('.term-bubble-wrapper > div').forEach(el => {
    el.style.border = 'none';
    el.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
  });
  
  // Evidenzia bubble selezionato
  bubbleEl.style.border = '2px solid #2c3e50';
  bubbleEl.style.boxShadow = '0 0 10px rgba(44, 62, 80, 0.4)';
  
  // Popola la preview
  previewWord.textContent = word;
  previewImages.innerHTML = '';
  
  if (thumbs.length === 0) {
    previewImages.innerHTML = '<span style="color:var(--dim); font-size:0.8rem;">Nessuna immagine disponibile per questa parola.</span>';
  } else {
    thumbs.forEach(t => {
      const img = document.createElement('img');
      img.src = t;
      img.style.cssText = 'width:80px; height:80px; object-fit:cover; border-radius:8px; border:2px solid var(--border); box-shadow:0 3px 6px rgba(0,0,0,0.05); transition:transform 0.2s;';
      img.onmouseover = () => { img.style.transform = 'scale(1.15)'; };
      img.onmouseout = () => { img.style.transform = 'scale(1)'; };
      previewImages.appendChild(img);
    });
  }
  
  previewDiv.style.display = 'block';
};

function switchView(view) {
  currentView = view;
  
  // Aggiorna Status Line (Usage e Conteggio Prodotti)
  const productsCountEl = document.getElementById('status-products-count');
  if (productsCountEl && typeof ALL_PRODUCTS !== 'undefined') {
    productsCountEl.textContent = ALL_PRODUCTS.length;
  }
  
  const usageTips = {
    sunflower: "🌻 Sunflower: Trascina la foto del prodotto verso i cerchi esterni per assegnarlo a una categoria.",
    kanban: "📋 Kanban: Trascina le schede dei prodotti tra le colonne per aggiornare al volo le loro categorie.",
    playground: "🧪 Clustering: Regola la barra della sensibilità e ricalcola i cluster di affinità del testo e del colore.",
    scene: "🕸️ Rete SIFT: Visualizza gli incroci di foto riciclate. Trascina i nodi o clicca sulle linee arancioni per i dettagli.",
    terms: "🧮 Distribuzione Parole: Clicca su qualsiasi bolla per visualizzare all'istante le foto dei prodotti abbinati."
  };
  const usageTipEl = document.getElementById('status-usage-tip');
  if (usageTipEl) {
    usageTipEl.innerHTML = usageTips[view] || "Pronto.";
  }
  
  // Hide all view containers
  document.getElementById('view-sunflower').style.display = 'none';
  document.getElementById('view-kanban').style.display = 'none';
  document.getElementById('view-playground').style.display = 'none';
  document.getElementById('view-scene').style.display = 'none';
  document.getElementById('view-terms').style.display = 'none';
  
  // Reset active tab button styles
  const tabIds = ['sunflower', 'kanban', 'playground', 'scene', 'terms'];
  tabIds.forEach(id => {
    const btn = document.getElementById('btn-view-' + id);
    if (btn) {
      btn.className = 'btn btn-outline btn-sm';
    }
  });
  
  // Show active view & set class
  const activeBtn = document.getElementById('btn-view-' + view);
  if (activeBtn) {
    activeBtn.className = 'btn btn-orange btn-sm';
  }
if (view === 'sunflower') {
    document.getElementById('view-sunflower').style.display = 'block';
    renderCurrentProduct();
  } else if (view === 'kanban') {
    document.getElementById('view-kanban').style.display = 'block';
    renderKanban();
  } else if (view === 'playground') {
    document.getElementById('view-playground').style.display = 'block';
    runClustering();
  } else if (view === 'scene') {
    document.getElementById('view-scene').style.display = 'block';
    runSceneMatch();
  } else if (view === 'terms') {
    document.getElementById('view-terms').style.display = 'block';
    renderTermsDistribution();
  }
}

window.moveBlock = function(btn, direction) {
  const block = btn.closest('.terms-category-block');
  if (!block) return;
  const parent = block.parentElement;
  
  if (direction === -1) {
    const prev = block.previousElementSibling;
    if (prev) parent.insertBefore(block, prev);
  } else {
    const next = block.nextElementSibling;
    if (next) parent.insertBefore(block, next.nextElementSibling);
  }
};

// ── Scene Match Javascript ───────────────────────────────────────────
let graphSimInterval = null;
let graphNodes = [];
let graphLinks = [];
let draggedNode = null;

async function runSceneMatch() {
  const container = document.getElementById('scene-graph-container');
  const nodesDiv = document.getElementById('scene-graph-nodes');
  const detailCard = document.getElementById('scene-detail-card');
  const listWrapper = document.getElementById('scene-match-list-wrapper');
  
  if (graphSimInterval) {
    cancelAnimationFrame(graphSimInterval);
    graphSimInterval = null;
  }
  
  container.style.display = 'block';
  nodesDiv.innerHTML = '<div style="text-align:center; padding:100px; color:var(--orange); font-weight:bold; animation:pulse 1.5s infinite;">Caricamento della rete di incroci SIFT...</div>';
  detailCard.style.display = 'none';
  if (listWrapper) listWrapper.style.display = 'none';
  
  try {
    const res = await fetch('/api/run_all_scenes', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ job_id: JOB_ID })
    });
    const data = await res.json();
    
    if (data.error) {
      nodesDiv.innerHTML = `<div style="padding:20px; color:red; font-weight:bold;">Errore: ${data.error}</div>`;
      return;
    }
    
    if (data.status === 'processing') {
      nodesDiv.innerHTML = `<div style="text-align:center; padding:100px;">
        <h3 style="color:#e67e22; margin-top:0;">Precalcolo Offline in corso!</h3>
        <p style="color:var(--dim);">${data.message}</p>
        <button class="btn btn-outline" onclick="runSceneMatch()" style="margin-top:20px;">Aggiorna Stato</button>
      </div>`;
      return;
    }
    
    // Salva i dati grezzi a livello globale per poterli filtrare sul client al volo
    window.siftRawMatches = data.matches || [];
    
    // Popola dinamicamente il filtro dei prodotti
    const filterSelect = document.getElementById('scene-product-filter');
    if (filterSelect) {
      filterSelect.innerHTML = '<option value="all">Tutti i prodotti (Grafo Unico)</option>';
      
      const cleanString = (str) => (str || '').toLowerCase().replace(/[^a-z0-9]/g, '');
      const findProductByTitle = (titlePart) => {
        if (!titlePart) return null;
        const cleanPart = cleanString(titlePart).slice(0, 20);
        if (!cleanPart) return null;
        return ALL_PRODUCTS.find(x => cleanString(x.title).includes(cleanPart));
      };
      
      // Estrai tutti i prodotti unici coinvolti nei match
      const uniqueParticipants = new Set();
      window.siftRawMatches.forEach(m => {
        uniqueParticipants.add(m.prod_1);
        uniqueParticipants.add(m.prod_2);
      });
      
      uniqueParticipants.forEach(prodKey => {
        const p = findProductByTitle(prodKey);
        const title = p ? p.title : prodKey;
        const option = document.createElement('option');
        option.value = prodKey;
        option.textContent = (title.slice(0, 45) + (title.length > 45 ? '...' : ''));
        filterSelect.appendChild(option);
      });
    }
    
    // Applica i filtri e disegna il grafo
    applySceneFilters();
    
  } catch (e) {
    nodesDiv.innerHTML = `<div style="padding:20px; color:red; font-weight:bold;">Errore di connessione: ${e}</div>`;
  }
}

window.applySceneFilters = function() {
  const container = document.getElementById('scene-graph-container');
  const svg = document.getElementById('scene-graph-svg');
  const nodesDiv = document.getElementById('scene-graph-nodes');
  const detailCard = document.getElementById('scene-detail-card');
  const listWrapper = document.getElementById('scene-match-list-wrapper');
  const listDiv = document.getElementById('scene-match-list');
  
  if (graphSimInterval) {
    cancelAnimationFrame(graphSimInterval);
    graphSimInterval = null;
  }
  
  const inliersThreshold = parseInt(document.getElementById('scene-inliers-threshold').value);
  const selectedProduct = document.getElementById('scene-product-filter').value;
  
  // 1. Filtra per soglia inliers
  let filtered = (window.siftRawMatches || []).filter(m => m.inliers >= inliersThreshold);
  
  // Mappe helper per trovare i prodotti per titolo ed escludere i duplicati
  const cleanString = (str) => (str || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const findProductByTitle = (titlePart) => {
    if (!titlePart) return null;
    const cleanPart = cleanString(titlePart).slice(0, 20);
    if (!cleanPart) return null;
    return ALL_PRODUCTS.find(x => cleanString(x.title).includes(cleanPart));
  };
  
  // 2. Escludi i duplicati/foto simili che appartengono alla stessa famiglia pHash
  filtered = filtered.filter(m => {
    const p1 = findProductByTitle(m.prod_1);
    const p2 = findProductByTitle(m.prod_2);
    if (p1 && p2 && p1.family_id && p2.family_id && p1.family_id === p2.family_id) {
      return false; // Stessa famiglia pHash (foto duplicata/molto simile), escludi!
    }
    return true;
  });
  
  // 3. Filtra per prodotto selezionato (Isolamento Stella)
  if (selectedProduct !== 'all') {
    filtered = filtered.filter(m => m.prod_1 === selectedProduct || m.prod_2 === selectedProduct);
  }
  
  // 4. Togli Duplicati (Se due prodotti hanno più match, tieni solo quello col punteggio inliers massimo)
  const dedupedMatches = [];
  const seenPairs = new Set();
  // Ordina decrescente così il primo visto ha il massimo inliers
  filtered.sort((a,b) => b.inliers - a.inliers);
  filtered.forEach(m => {
    const pairKey = [m.prod_1, m.prod_2].sort().join('::');
    if (!seenPairs.has(pairKey)) {
      seenPairs.add(pairKey);
      dedupedMatches.push(m);
    }
  });
  
  const finalMatches = dedupedMatches;
  
  svg.innerHTML = '';
  nodesDiv.innerHTML = '';
  detailCard.style.display = 'none';
  if (listWrapper) listWrapper.style.display = 'none';
  
  // Mostra il grafo SOLO se è selezionato un prodotto specifico E ha più di 1 match!
  if (selectedProduct !== 'all' && finalMatches.length > 1) {
    container.style.display = 'block';
  } else {
    container.style.display = 'none';
    if (graphSimInterval) {
      cancelAnimationFrame(graphSimInterval);
      graphSimInterval = null;
    }
  }
  
  if (finalMatches.length === 0) {
    nodesDiv.innerHTML = `
      <div style="padding:40px; text-align:center; color:var(--dim); font-weight:bold;">
        Nessun incrocio visivo trovato con i parametri correnti.<br/>
        <span style="font-size:0.8rem; font-weight:normal;">Prova ad abbassare la soglia dei punti inliers o a selezionare \"Tutti i prodotti\".</span>
      </div>
    `;
    return;
  }
  
  // Helper functions already declared above
  const getThumb = (titlePart) => {
    const p = findProductByTitle(titlePart);
    return p && p.thumbnail ? p.thumbnail : '';
  };
  const getTitle = (titlePart) => {
    const p = findProductByTitle(titlePart);
    return p && p.title ? p.title : titlePart;
  };
  
  // Costruisci Nodi e Link per il Grafo
  const nodeMap = {};
  graphLinks = [];
  
  finalMatches.forEach(m => {
    if (!nodeMap[m.prod_1]) {
      nodeMap[m.prod_1] = { id: m.prod_1, isProduct: true, thumb: getThumb(m.prod_1), title: getTitle(m.prod_1) };
    }
    if (!nodeMap[m.prod_2]) {
      nodeMap[m.prod_2] = { id: m.prod_2, isProduct: false, thumb: getThumb(m.prod_2), title: getTitle(m.prod_2) };
    }
    graphLinks.push({ source: m.prod_1, target: m.prod_2, inliers: m.inliers, image: m.image });
  });
  
  const w = container.clientWidth || 900;
  const h = container.clientHeight || 500;
  
  graphNodes = Object.values(nodeMap);
  graphNodes.forEach((n, idx) => {
    // Posizioni iniziali
    if (selectedProduct !== 'all' && n.id === selectedProduct) {
      // Piazza l'elemento selezionato precisamente al centro
      n.x = w / 2;
      n.y = h / 2;
    } else {
      const angle = (idx / graphNodes.length) * 2 * Math.PI;
      n.x = w / 2 + Math.cos(angle) * (selectedProduct !== 'all' ? 150 : 120);
      n.y = h / 2 + Math.sin(angle) * (selectedProduct !== 'all' ? 150 : 120);
    }
    n.vx = 0;
    n.vy = 0;
    
    // Crea nodo DOM
    const el = document.createElement('div');
    el.className = 'graph-node';
    el.id = `node-${n.id}`;
    el.style.cssText = `
      position:absolute; width:55px; height:55px; border-radius:50%; 
      border:3px solid ${n.isProduct ? '#3498db' : '#e67e22'};
      background:#fff; background-image:url('${n.thumb}'); background-size:cover; background-position:center;
      box-shadow:0 4px 10px rgba(0,0,0,0.15); cursor:grab; pointer-events:auto; z-index:5;
      transition: transform 0.15s;
    `;
    el.title = `${n.isProduct ? 'Prodotto' : 'Scena'}: ${n.title}`;
    
    el.addEventListener('mousedown', (e) => {
      draggedNode = n;
      el.style.cursor = 'grabbing';
      e.preventDefault();
    });
    
    nodesDiv.appendChild(el);
  });
  
  // Linee SVG di collegamento
  graphLinks.forEach((l, idx) => {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('stroke', 'rgba(230, 126, 34, 0.4)');
    line.setAttribute('stroke-width', '4');
    line.setAttribute('cursor', 'pointer');
    line.style.pointerEvents = 'auto';
    line.id = `link-${idx}`;
    
    line.addEventListener('mouseover', () => {
      line.setAttribute('stroke', 'rgba(230, 126, 34, 0.9)');
      line.setAttribute('stroke-width', '6');
    });
    line.addEventListener('mouseout', () => {
      line.setAttribute('stroke', 'rgba(230, 126, 34, 0.4)');
      line.setAttribute('stroke-width', '4');
    });
    line.addEventListener('click', () => {
      showSiftDetails(l);
    });
    
    svg.appendChild(line);
  });
  
  // Renderizza la lista dettagliata dei match in basso
  if (listWrapper && listDiv) {
    listDiv.innerHTML = '';
    finalMatches.forEach((m, idx) => {
      const prod1Thumb = getThumb(m.prod_1);
      const prod2Thumb = getThumb(m.prod_2);
      const prod1Title = getTitle(m.prod_1);
      const prod2Title = getTitle(m.prod_2);
      
      const card = document.createElement('div');
      card.style.cssText = 'background:#fff; border:2px solid var(--border); border-radius:16px; padding:20px; box-shadow:0 4px 15px rgba(0,0,0,0.04); transition:border-color 0.2s;';
      card.onmouseover = () => { card.style.borderColor = 'var(--orange)'; };
      card.onmouseout = () => { card.style.borderColor = 'var(--border)'; };
      
      card.innerHTML = `
        <div style="text-align:center; font-size:0.75rem; color:var(--dim); font-weight:bold; margin-bottom:15px; border-bottom:1px dashed var(--border); padding-bottom:8px;">
          Rilevamento #${idx + 1} &bull; <span style="color:var(--orange)">${m.inliers} Punti in Comune (Inliers RANSAC)</span>
        </div>
        
        <div style="display:flex; justify-content:space-between; align-items:center; gap:20px; flex-wrap:wrap;">
          <!-- Foto Prodotto Singola (Origine) -->
          <div style="flex:1; min-width:180px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:10px;">
            <span style="font-size:0.75rem; font-weight:900; color:#3498db; text-transform:uppercase;">Prodotto Isolato</span>
            <img src="${prod1Thumb}" style="width:130px; height:130px; object-fit:cover; border-radius:8px; border:2px solid #3498db; box-shadow:0 4px 10px rgba(0,0,0,0.05);">
            <div style="font-size:0.7rem; font-weight:bold; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; width:180px;" title="${prod1Title}">${prod1Title}</div>
          </div>
          
          <!-- OpenCV SIFT Match Image -->
          <div style="flex:1.8; min-width:300px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:10px;">
            <span style="font-size:0.75rem; font-weight:900; color:var(--orange); text-transform:uppercase;">Incrocio Geometrico (SIFT)</span>
            <div style="position:relative; overflow:hidden; border-radius:8px; border:1.5px solid var(--border); width:100%; max-width:420px; box-shadow:0 4px 15px rgba(0,0,0,0.08);">
              <img src="${m.image}" style="width:100%; height:180px; object-fit:contain; background:#fafafa; cursor:zoom-in; transition:transform 0.2s;" onclick="openSIFTModal(this.src, '${encodeURIComponent(prod1Title)}', '${encodeURIComponent(prod2Title)}')">
            </div>
          </div>
          
          <!-- Foto Scena Ambientale -->
          <div style="flex:1; min-width:180px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:10px;">
            <span style="font-size:0.75rem; font-weight:900; color:#e67e22; text-transform:uppercase;">Foto della Scena</span>
            <img src="${prod2Thumb}" style="width:130px; height:130px; object-fit:cover; border-radius:8px; border:2px solid #e67e22; box-shadow:0 4px 10px rgba(0,0,0,0.05);">
            <div style="font-size:0.7rem; font-weight:bold; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; width:180px;" title="${prod2Title}">${prod2Title}</div>
          </div>
        </div>
      `;
      listDiv.appendChild(card);
    });
    listWrapper.style.display = 'block';
  }
  
  // Avvia simulazione fisica a 60fps
  function tick() {
    const width = container.clientWidth || 900;
    const height = container.clientHeight || 500;
    
    // 1. Repulsione
    for (let i = 0; i < graphNodes.length; i++) {
      for (let j = i + 1; j < graphNodes.length; j++) {
        let dx = graphNodes[j].x - graphNodes[i].x;
        let dy = graphNodes[j].y - graphNodes[i].y;
        if (dx === 0) dx = 0.1;
        let dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 1) dist = 1;
        if (dist < 160) {
          let force = 300 / (dist * dist);
          if (force > 4) force = 4;
          let fx = (dx / dist) * force;
          let fy = (dy / dist) * force;
          graphNodes[i].vx -= fx;
          graphNodes[i].vy -= fy;
          graphNodes[j].vx += fx;
          graphNodes[j].vy += fy;
        }
      }
    }
    
    // 2. Trazione molla
    graphLinks.forEach(link => {
      let s = graphNodes.find(n => n.id === link.source);
      let t = graphNodes.find(n => n.id === link.target);
      if (!s || !t) return;
      
      let dx = t.x - s.x;
      let dy = t.y - s.y;
      let dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 1) dist = 1;
      let desiredDist = 130;
      let force = (dist - desiredDist) * 0.03;
      let fx = (dx / dist) * force;
      let fy = (dy / dist) * force;
      s.vx += fx;
      s.vy += fy;
      t.vx -= fx;
      t.vy -= fy;
    });
    
    // 3. Attrito e centro di gravità
    const cx = width / 2;
    const cy = height / 2;
    graphNodes.forEach(n => {
      if (n === draggedNode) return;
      
      // Se il prodotto è in stella ed è isolato al centro, sforza la gravità
      if (selectedProduct !== 'all' && n.id === selectedProduct) {
        n.vx += (cx - n.x) * 0.05;
        n.vy += (cy - n.y) * 0.05;
      } else {
        n.vx += (cx - n.x) * 0.008;
        n.vy += (cy - n.y) * 0.008;
      }
      
      n.vx *= 0.80;
      n.vy *= 0.80;
      
      n.x += n.vx;
      n.y += n.vy;
      
      if (n.x < 30) n.x = 30;
      if (n.x > width - 30) n.x = width - 30;
      if (n.y < 30) n.y = 30;
      if (n.y > height - 30) n.y = height - 30;
    });
    
    // 4. Aggiorna elementi DOM nodi
    graphNodes.forEach(n => {
      const el = document.getElementById(`node-${n.id}`);
      if (el) {
        el.style.left = (n.x - 27.5) + 'px';
        el.style.top = (n.y - 27.5) + 'px';
      }
    });
    
    // Aggiorna SVG linee
    graphLinks.forEach((l, idx) => {
      const line = document.getElementById(`link-${idx}`);
      let s = graphNodes.find(n => n.id === l.source);
      let t = graphNodes.find(n => n.id === l.target);
      if (line && s && t) {
        line.setAttribute('x1', s.x);
        line.setAttribute('y1', s.y);
        line.setAttribute('x2', t.x);
        line.setAttribute('y2', t.y);
      }
    });
    
    graphSimInterval = requestAnimationFrame(tick);
    nodesDiv.innerHTML = `<div style="padding:20px; color:red; font-weight:bold;">Errore di connessione: ${e}</div>`;
  }
}

function showSiftDetails(link) {
  const detailCard = document.getElementById('scene-detail-card');
  const detailImg = document.getElementById('scene-detail-img');
  const detailP1 = document.getElementById('scene-detail-p1');
  const detailP2 = document.getElementById('scene-detail-p2');
  const detailInliers = document.getElementById('scene-detail-inliers');
  
  detailImg.src = link.image;
  detailP1.textContent = link.source;
  detailP2.textContent = link.target;
  detailInliers.textContent = `${link.inliers} punti geometrici validati SIFT`;
  
  detailCard.style.display = 'block';
  // Scroll automatico sui dettagli
  detailCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

window.openSIFTModal = function(src, p1Esc, p2Esc) {
  const p1 = decodeURIComponent(p1Esc);
  const p2 = decodeURIComponent(p2Esc);
  
  let modal = document.getElementById('sift-lightbox-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'sift-lightbox-modal';
    modal.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:10000; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:20px; box-sizing:border-box; color:white; font-family:sans-serif;';
    modal.innerHTML = `
      <div style="position:absolute; top:20px; right:20px; font-size:2rem; cursor:pointer;" onclick="this.parentElement.style.display='none'">&times;</div>
      <div style="text-align:center; max-width:90%; max-height:80%;">
        <img id="sift-lightbox-img" style="max-width:100%; max-height:100%; border:2px solid #fff; border-radius:8px; box-shadow:0 10px 30px rgba(0,0,0,0.5);" src="">
        <div id="sift-lightbox-info" style="margin-top:15px; font-size:0.9rem; font-weight:bold; background:rgba(0,0,0,0.6); padding:10px 20px; border-radius:20px; display:inline-block; max-width: 600px; text-overflow: ellipsis; overflow: hidden; white-space: nowrap;"></div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  document.getElementById('sift-lightbox-img').src = src;
  document.getElementById('sift-lightbox-info').textContent = `SIFT: ${p1} ➔ ${p2}`;
  modal.style.display = 'flex';
};

// ── Clustering Playground Javascript ───────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  if (JOB_ID) {
    runClustering();
  }
});

async function runClustering() {
  const container = document.getElementById('playground-clusters-container');
  // Evita il salto della pagina: non svuotare il contenitore ma rendilo semi-trasparente
  container.style.opacity = '0.5';
  container.style.pointerEvents = 'none';

  const threshold = document.getElementById('threshold-slider').value;
  const method = document.getElementById('method-select').value;
  
  // Aggiorna spiegazione del metodo
  const methodDescriptions = {
    birch: "🌳 BIRCH: Raggruppamento gerarchico ad albero. Regola la barra della soglia per fondere o dividere i gruppi in base alle parole nei titoli.",
    kmeans: "📊 K-Means: Divide i prodotti in gruppi bilanciati di pari dimensione analizzando la ricorrenza dei termini chiave nei titoli.",
    hybrid: "🎨 Ibrido: Combina i dati testuali (TF-IDF) e le informazioni visive (colore dominante delle foto) per raggruppare i prodotti simili."
  };
  document.getElementById('method-desc-box').textContent = methodDescriptions[method] || "";

  try {
    const res = await fetch('/api/run_clustering', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ job_id: JOB_ID, threshold: threshold, method: method })
    });
    const data = await res.json();
    
    if (data.error) {
      container.style.opacity = '1';
      container.style.pointerEvents = 'auto';
      container.innerHTML = `<div style="color:red;padding:20px;font-size:0.75rem">Errore: ${data.error}</div>`;
      return;
    }
    
    renderPlaygroundClusters(data.clusters);
    container.style.opacity = '1';
    container.style.pointerEvents = 'auto';
  } catch (e) {
    container.style.opacity = '1';
    container.style.pointerEvents = 'auto';
    container.innerHTML = `<div style="color:red;padding:20px;font-size:0.75rem">Errore di rete: ${e}</div>`;
  }
}

function renderPlaygroundClusters(clusters) {
  const container = document.getElementById('playground-clusters-container');
  container.innerHTML = '';
  
  if (!clusters || clusters.length === 0) {
    container.innerHTML = `<div style="padding:20px;text-align:center;font-size:0.7rem;color:var(--dim)">Nessun cluster generato.</div>`;
    return;
  }
  
  // Impostiamo il container come un unico flex-wrap globale fluido senza scatole interne
  container.style.display = 'flex';
  container.style.flexWrap = 'wrap';
  container.style.gap = '4px';
  container.style.alignItems = 'center';
  container.style.alignContent = 'flex-start';
  container.style.width = '100%';
  
  // Palette di colori accesi ma eleganti per distinguere i gruppi adiacenti
  const colors = ['#FF595E', '#FFCA3A', '#8AC926', '#1982C4', '#6A4C93', '#F15BB5', '#00BBF9', '#00F5D4', '#E07A5F', '#3D405B', '#81B29A', '#F2CC8F'];
  
  clusters.forEach((c, idx) => {
    const termsStr = c.terms && c.terms.length > 0 ? c.terms.slice(0, 5).join(', ') : 'Misto';
    const col = colors[idx % colors.length];
    
    // Etichetta (Pillola) Inline
    const pill = document.createElement('div');
    pill.style.display = 'inline-flex';
    pill.style.alignItems = 'center';
    pill.style.justifyContent = 'space-between';
    pill.style.height = '72px'; // Stessa altezza esatta delle foto grandi
    pill.style.padding = '0 12px 0 16px';
    pill.style.borderRadius = '36px';
    pill.style.backgroundColor = col + '55'; // colore pieno leggero
    pill.style.boxSizing = 'border-box';
    pill.style.margin = '2px';
    
    pill.innerHTML = `
      <div style="display:flex; flex-direction:column; justify-content:center; max-width:200px; margin-right:12px">
        <span style="font-size:0.6rem; font-weight:900; color:#333; text-transform:uppercase; line-height:1.2">Gruppo</span>
        <span style="font-size:0.75rem; font-weight:700; color:var(--text); line-height:1.2; white-space:normal; overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical" title="${termsStr}">${termsStr}</span>
      </div>
      <div style="position:relative; width:28px; height:28px">
        <select class="cluster-cat-select" style="position:absolute; top:0; left:0; width:100%; height:100%; opacity:0; cursor:pointer;" onchange="assignWholeCluster(${c.id}, ${JSON.stringify(c.products.map(p => p.asin))}, this.value)">
          <option value="">--</option>
          ${categories.map(cat => `<option value="${cat}">${cat}</option>`).join('')}
        </select>
      </div>
    `;
    container.appendChild(pill);
    
    // Foto del gruppo (inline)
    const itemsList = c.unique_products || [];
    itemsList.forEach(p => {
      const localProd = ALL_PRODUCTS.find(lp => lp.asin === p.asin) || p;
      const isAssigned = !!localProd.category;
      
      const card = document.createElement('div');
      card.className = 'cluster-prod-card' + (isAssigned ? ' assigned' : '');
      card.title = `${localProd.title} ${localProd.category ? '[' + localProd.category + ']' : ''}`;
      
      card.style.margin = '2px';
      card.style.backgroundColor = col + '55'; // Colore a riempimento come il pill
      card.style.border = 'none'; // Nessun contorno
      card.style.boxSizing = 'border-box';
      
      // Nessuna opacità o filtro per i prodotti assegnati: restano perfettamente visibili e intatti.
      
      card.innerHTML = `
        <img src="/api/image/${p.asin}" onerror="this.src='${p.thumbnail || ''}'" alt=""/>
      `;
      container.appendChild(card);
    });
  });
}

async function assignWholeCluster(clusterId, asins, cat) {
  if (!cat) return;
  
  for (const asin of asins) {
    await assignCategory(asin, cat, true);
  }
  
  runClustering();
  
  const toast = document.getElementById('sf-toast');
  document.getElementById('sf-toast-msg').textContent = `Assegnati ${asins.length} prodotti a "${cat}"!`;
  toast.style.display = 'flex';
  setTimeout(() => { toast.style.display = 'none'; }, 3000);
}

// ── Upload Immagine & Color Matching ─────────────────────────────────────────
async function uploadImage(file) {
  if (!file) return;
  
  const status = document.getElementById('upload-status');
  const previewContainer = document.getElementById('preview-container');
  const preview = document.getElementById('uploaded-preview');
  const indicator = document.getElementById('color-match-indicator');
  const matchesSection = document.getElementById('playground-upload-matches');
  const matchesContainer = document.getElementById('match-cards-container');
  
  status.textContent = "Caricamento in corso...";
  matchesSection.style.display = 'none';
  previewContainer.style.display = 'none';
  const formData = new FormData();
  formData.append('file', file);
  formData.append('job_id', JOB_ID);
  
  try {
    const res = await fetch('/api/upload_image', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    
    if (data.error) {
      status.textContent = "Errore: " + data.error;
      return;
    }
    
    status.textContent = "Caricato con successo!";
    preview.src = data.url;
    previewContainer.style.display = 'block';
    
    if (data.color) {
      indicator.innerHTML = `Colore Dominante: <span style="display:inline-block; width:12px; height:12px; background:rgb(${data.color.join(',')}); border:1px solid #000; vertical-align:middle"></span> RGB(${data.color.join(',')})`;
    }
    
    // Mostra corrispondenze visive
    if (data.matches && data.matches.length > 0) {
      matchesContainer.innerHTML = '';
      data.matches.forEach(m => {
        const card = document.createElement('div');
        card.className = 'cluster-prod-card';
        card.innerHTML = `
          <img src="/api/image/${m.asin}" onerror="this.src='${m.thumbnail || ''}'" alt=""/>
          <div style="font-weight:600; text-overflow:ellipsis; overflow:hidden; white-space:nowrap" title="${m.title}">${m.title.slice(0, 30)}...</div>
          <div style="color:var(--orange); font-weight:700; font-size:0.58rem">Match Visivo: ${m.similarity}%</div>
        `;
        matchesContainer.appendChild(card);
      });
      matchesSection.style.display = 'block';
    } else {
      matchesContainer.innerHTML = '<div style="padding:10px; font-size:0.62rem; color:var(--dim)">Nessun match visivo stretto con i prodotti del job corrente.</div>';
      matchesSection.style.display = 'block';
    }
  } catch (e) {
    status.textContent = "Errore di connessione: " + e;
  }
}

// ── Drag & Drop Event Listeners per Upload Zone ────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('drop-zone');
  if (dropZone) {
    dropZone.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--orange)';
      dropZone.style.background = 'rgba(255,102,0,0.05)';
    });
    
    dropZone.addEventListener('dragleave', () => {
      dropZone.style.borderColor = 'var(--muted)';
      dropZone.style.background = 'rgba(255,255,255,0.4)';
    });
    
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.style.borderColor = 'var(--muted)';
      dropZone.style.background = 'rgba(255,255,255,0.4)';
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        uploadImage(e.dataTransfer.files[0]);
      }
    });
  }
});

// Enter key in new-cat-input
document.getElementById('new-cat-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') addCategory();
});

// ── Init ──────────────────────────────────────────────────────────────────
renderCatList();
renderCurrentProduct();
switchView('playground');
