# Amazon Search UI/UX — Design Plan

## Contesto

- **Platform**: Termux Android (mobile only)
- **User**: Persona ricerca budget (subwoofer auto, LED auto, charger) — criterio: prezzo max, stelle minime
- **API**: SerpAPI (20 prodotti max per call, 250/mese quota)
- **Dati**: title, price, stars, reviews, brand (spesso mancante), image URL, link
- **HTML**: Standalone (no server, JS client-only, offline-ready)

---

## GERARCHIA INFORMAZIONI

**Ordine visualizzazione su mobile (top-to-bottom):**

1. **Ricerca + Filtri attivi** (sticky header)
   - Query ("subwoofer auto...")
   - Chip dei filtri attivi con X (price, stars, brand)
   - Tap "More filters" → drawer
   - Alto-prioritario: user vede sempre cosa ha cercato

2. **Risultati counter + sort**
   - "9 risultati trovati"
   - Sort dropdown (Relevance, Price, Rating)
   - Info importante: quanti match user ha

3. **Product card** (repeating)
   - **Immagine** (aspect ratio 4:3, thumbnail CDN)
   - **Titolo** (1-2 linee, truncate con "...")
   - **Rating** (★★★★☆ 4.3) + review count (312 reviews)
   - **Prezzo** (grande, contrasto alto, rosso)
   - **Badge Info** (Prime, In Stock, NEW)
   - **Tasto "Vedi su Amazon"** (accessibile, 48px height)

4. **Footer** (dopo ultimi card)
   - Link back to search
   - Quota info (serpapi 241/250)
   - Timestamp ricerca

---

## USER JOURNEY

**User enters:**
1. Click "amazon-search 'subwoofer auto'" → HTML opens in browser
2. Vede risultati subito, 9 card visibili
3. Scroll → vede più prodotti
4. Vuole filtrare per marca? Tap "Filter" → drawer opens
5. Select "Pioneer" checkbox + click "Apply" → drawer chiude, card ricalcolate
6. Tap price slider → range €50-€100 → apply → risultati aggiornati
7. Trova prodotto interessante → tap "Vedi su Amazon" → apre link

**Friction points to avoid:**
- Non mostrare filtri come select-dropdown (Android: 3-tap per option)
- Non infinito scroll (quota SerpAPI limitato)
- Non "loading spinner" per filtri (JS istantaneo, client-side)
- Non sidebar (waste 50% screen on mobile)

---

## LAYOUT WIREFRAME (Mobile 375px width)

```
╔═══════════════════════════════╗
║ Search bar                    ║  ← Sticky, with back button
║ [Filtri attivi: $50-120 ▌ ★4+]║  ← Chip row, horizontal scroll
╚═══════════════════════════════╝

┌───────────────────────────────┐
│ ✓ 9 risultati | Sort: Price ▼ │  ← Info + control
└───────────────────────────────┘

┌───────────────────────────────┐
│ [IMG] ┌─────────────────────┐  │
│       │ Subwoofer Pioneer   │  │  ← Card: image LEFT, info RIGHT
│       │ TS-WX310A          │  │    (vertical stack on very small phones)
│       │ ★★★★☆ 4.5          │  │
│       │ 234 reviews         │  │
│       │ €89,99              │  │  ← Price: large, red, obvious
│       │ ✓ Prime   □ In Stock│  │
│       │ [Vedi su Amazon →]  │  │
└───────────────────────────────┘

┌───────────────────────────────┐
│ [IMG] ┌─────────────────────┐  │
│       │ JBL BassPro SL2     │  │
│       │ ...                 │  │
└───────────────────────────────┘
... (repeat card)
```

---

## VISUAL HIERARCHY & CONTRAST

**Font sizes (relative):**
- Titolo: 16px (bold, #1a1a1a)
- Prezzo: 20px (bold, #d32f2f rosso)
- Rating: 14px (#666 grigio)
- Reviews count: 12px (#999 grigio)
- Badge: 12px (white text, colored background)

**Colors:**
- Price: #d32f2f (red, attention)
- Rating: #ffc107 (yellow star)
- Prime/badge: #007bff (blue)
- In Stock: #28a745 (green)
- Link: #0077b6 (blue, accessible)

**Spacing:**
- Card padding: 12px
- Image height: 120-150px (aspect ratio 4:3)
- Gap between cards: 12px
- Sticky header height: 60px

---

## FILTRI - Placement & Logic

**Location: Bottom-sheet drawer (mobile pattern)**
- Trigger: "Filtri" button in header (or "Filter" hamburger)
- Animation: slide-up 300ms ease
- Full-screen or half-screen (user choice? No — half-screen saves context)
- Dismiss: tap outside, swipe down, or "Back" button

**Filter types:**

| Filter | Type | UI | Default |
|--------|------|-----|---------|
| **Prezzo** | Range | Slider + input min/max | 0-200€ |
| **Stelle** | Range | Slider 0-5 or 5 buttons | All |
| **Marca** | Multi-select | Checkboxes (scrollable list) | All |
| **Disponibilità** | Toggle | Switch: In Stock Only | Off |
| **Prime** | Toggle | Switch: Prime Only | Off |

**Drawer UI:**
```
┌─────────────────────────────┐
│ Filter          X           │  ← Header, close button
├─────────────────────────────┤
│ PRICE RANGE                 │
│ [Min input] - [Max input]   │
│ ◄─────●────────► (slider)   │
├─────────────────────────────┤
│ MINIMUM RATING              │
│ ☆☆☆☆☆  ★★★★☆  ★★★★★      │
│ (All 3.5+ 4+ 4.5+)          │
├─────────────────────────────┤
│ BRAND (scroll if >5)        │
│ ☐ Pioneer      (4)          │  ← count di items disponibili
│ ☐ JBL          (2)          │
│ ☐ Alpine       (1)          │
│ ☐ Blaupunkt    (0) [disabled]
│ [Show 7 more ▼]             │
├─────────────────────────────┤
│ ☐ In Stock Only             │
│ ☐ Prime Only                │
├─────────────────────────────┤
│ [RESET]  [APPLY & SHOW 12]  │  ← Sticky, always visible
└─────────────────────────────┘
```

**Logic:**
- Counts dinamici: reale, no fake numbers
- Disabled options (grayed out) se count = 0
- URL state: `?price=50-100&stars=4&brand=pioneer`
- Reset button: clear all, default all filters
- "Apply" button shows: "APPLY & SHOW 12" (real-time count)

---

## PRODUCT CARD - Design Details

**Desktop (future scope):** 2-col grid, larger card
**Mobile (NOW):** 1-col, image-left layout

```
┌──────────────────────────────────┐
│ ┌────────┐ ┌──────────────────┐  │
│ │        │ │ Title 1-2 lines  │  │
│ │ Image  │ │                  │  │
│ │ 120x90 │ │ ★★★★☆ 4.5       │  │
│ │        │ │ 234 reviews      │  │
│ │        │ │ €89,99           │  │
│ │        │ │ ✓Prime ▫In Stock │  │
│ │        │ └──────────────────┘  │
│ │        │ [Vedi su Amazon →]     │
│ └────────┘ └──────────────────┘  │
└──────────────────────────────────┘
```

**Info da mostrare:**
- Title (max 60 chars)
- Image (CDN thumbnail, lazy load)
- Price (€XX,XX format)
- Stars + count (★★★★☆ 234)
- Badges (Prime, In Stock)
- Link (CTA)

**Info da nascondere (per ora):**
- Brand (spesso mancante da SerpAPI)
- Description/bullets
- Shipping info
- Seller rating

**On tap:**
- Tap image or "Vedi su Amazon" → opens amazon.it link
- Tap rating → scroll to see reviews count
- No modal (per mantener semplice)

---

## FILTRI - User Story

**User: "Voglio subwoofer sotto 100€ di marca Pioneer"**

1. Tap "Filtri" button
2. Drawer slide-up
3. Set PRICE: input "100" in max field (or drag slider to 100)
4. Set BRAND: tap "Pioneer" checkbox
5. Count update: "APPLY & SHOW 3"
6. Tap "APPLY"
7. Drawer slide-down
8. Only 3 cards visible, filtered
9. Tap "Filtri" again → drawer shows checkmarks on selections
10. Can tweak further or close

**Zero results case:**
- Mostri: "0 risultati per Pioneer + €50-100"
- Suggerisci: "Remove 'Pioneer'" o "Increase budget to €150"
- Mostra: "Top 5 bestseller senza filtri" (reset suggestion)

---

## INFORMATION DENSITY

**What user sees without scroll (above-the-fold):**
- Search query
- Active filter chips (1-2 visible)
- Result count + sort control
- 2-3 product card (parziali, può vedere di più con scroll)

**Cosa NON mettere above-the-fold:**
- Ads / promotional banners
- Disclaimer sulla API
- "Read more" collapsed sections
- Pagination controls (use load-more, not numbered)

---

## SORT OPTIONS

**Default: Relevance** (match query, no arbitrary)

**Options:**
1. Relevance (query match + rating weighted)
2. Price: Low to High
3. Price: High to Low
4. Rating: Highest First
5. Newest First (if available)

**UI:** Dropdown select with current value shown

---

## FOOTER / Additional Info

**After last product card:**
```
┌─────────────────────────────┐
│ Ricerca: 2026-05-19 14:40  │
│ Quota SerpAPI: 241/250     │
│ Cache: Hit (0s)            │
│ [New Search]  [Export CSV] │
└─────────────────────────────┘
```

**Purpose:** Transparency (quota), quick re-search, debug info

---

## INTERACTIVE ELEMENTS - Accessibility

**Touch targets:**
- Buttons: min 44x44px (WCAG 2.1 AA)
- Filter chips: min 40px height
- Card: entire card tappable (not just link)

**Color contrast:**
- Text on white: 4.5:1 minimum
- Price red (#d32f2f) on white: 5.5:1 ✓
- Gray text (#999) on white: 4.5:1 edge case (fix: #666)

**Keyboard support:**
- Tab through filters (mobile: native keyboard)
- Enter to apply (mobile: native)
- Esc to close drawer

---

## RESPONSIVE BREAKPOINTS

**Current: Mobile-first (≤375px)**
- Single column
- Bottom-sheet filters
- Sticky header

**Future (if desktop scope):**
- 768px+: Left sidebar filters + 2-col grid
- 1200px+: 3-col grid + wider sidebar

---

## IMPLEMENTATION PHASES

### Phase 1: MVP (core)
- ✓ Product card layout
- ✓ Sticky header + filters chips
- ✓ Filter drawer (price slider + star buttons + brand checkboxes)
- ✓ Sort dropdown
- ✓ Result counter
- ✓ Mobile responsive (375-600px)

### Phase 2: Polish
- Lazy-load images
- Animations (drawer slide, button hover)
- Error states (zero results)
- Loading skeleton
- Accessibility (aria labels, color contrast)

### Phase 3: Enhancement
- Export to CSV
- Share filters (URL state)
- Dark mode toggle
- Comparison mode (2-3 cards side-by-side)

---

## SUCCESS METRICS

- **Time to first filter**: < 2 taps
- **Filter clarity**: User sees immediately which filters are active
- **Zero-result recovery**: User knows how to clear filters
- **Mobile scroll smoothness**: No jank, 60fps
- **Accessibility**: All interactive elements keyboard-accessible
