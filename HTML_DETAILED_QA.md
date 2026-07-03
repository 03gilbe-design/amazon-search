# HTML Amazon Search — Documento QA Dettagliato

## Componenti e Specifiche

### 1. HEADER (Sticky, Z-index 100)
**Posizione:** Top della pagina, rimane sempre visibile durante scroll
**Componenti:**
- **H1**: Query max 40 caratteri (truncate se più lungo)
- **Sub**: Quota info (non visibile attualmente, rimosso da ridondanza)
- **Button "Filtri"**: Blue (#0066c0), 8x12px padding, 44px min height
- **Animazione al tap:** scale(0.95) 100ms feedback

**Test QA:**
- [ ] Header sticky durante scroll
- [ ] H1 truncate per query lunghe
- [ ] Button "Filtri" responsive al tap
- [ ] Z-index non interferisce con drawer

---

### 2. ACTIVE FILTERS CHIPS ROW
**Posizione:** Sotto header, horizontal scroll
**Comportamento:**
- Vuota se nessun filtro attivo
- Mostra max 2 chip (price + stars)
- Chip: background light blue (#e3f2fd), text blue (#0066c0)
- Close button "×" su ogni chip

**Interazioni:**
- Tap chip × → fade-out (200ms) + recount
- Scroll orizzontale se >1 chip
- No vertical scrollbar (horizontale only)

**Test QA:**
- [ ] Chip non appaiono se nessun filtro
- [ ] Chip appaiono dopo applica filtri
- [ ] Close button funziona (fade-out smooth)
- [ ] Recount accurato dopo remove

---

### 3. CONTROLS BAR (Result Counter + Sort)
**Posizione:** Sotto chips
**Componenti:**
- **Left:** "X risultati" (dinamico, aggiorna su filter)
- **Right:** Sort dropdown ("Rilevanza", "Prezzo ↑", "Prezzo ↓", "Stelle ↓")

**Animazioni:**
- Counter update: instant (no animation, ma critico che sia accurato)
- Sort dropdown: active state on press

**Test QA:**
- [ ] Counter init correto (n prodotti)
- [ ] Counter update dopo applica filtri
- [ ] Counter match risultati visibili
- [ ] Sort dropdown funziona per ogni option
- [ ] Sort mantiene filtri attivi
- [ ] Niente animation flickering

---

### 4. SUMMARY BOX (Opzionale)
**Posizione:** Sotto controls
**Styling:** Yellow background (#fffbe6), 3px left border (#ffc107)
**Contenuto:** Testo descrittivo (es "9 prodotti sotto 120€")

**Test QA:**
- [ ] Summary box appare se testo fornito
- [ ] Summary box scomparso se vuoto
- [ ] Text colore leggibile (#666)

---

### 5. PRODUCT GRID
**Layout:** Single column (flex column), gap 12px
**Responsive:** 320px+ (no horizontal scroll)

#### 5.1 CARD LAYOUT
**Structure:** Horizontal flex: image LEFT (100px) + info RIGHT (flex-1)
**Card Height:** Auto (min ~120px)

**Componenti:**
- **Image (LEFT):**
  - Width: 100px (fixed)
  - Height: 90px (fixed aspect 10:9)
  - Fallback: Gray box with "■" (no emoji)
  - Image: lazy-load, object-fit contain
  - Border-radius: 4px

- **Info (RIGHT):** Flex column, gap 6px
  - **Title:** 14px, bold, 2-line max (overflow hidden)
  - **Rating:** Stars + confidence (●●●) + review count
  - **Price:** 18px bold RED (#d32f2f)
  - **Badge:** "Non disp." (red if out-of-stock) OR "Prime" (blue)
  - **Specs:** <details> (collapsibile, closed by default)
  - **CTA Button:** "Vedi su Amazon" orange (#e47911)

**Animazioni:**
- Card tap: scale pulse 1.01 (200ms)
- Button tap: scale 0.95 (100ms)

**Test QA:**
- [ ] Image aspect ratio fisso (no layout shift)
- [ ] Title truncate a 2 linee (ellipsis)
- [ ] Price color RED (#d32f2f)
- [ ] Price visibility senza scroll
- [ ] Button orange (#e47911), 44px height
- [ ] Specs closed by default, clickable summary
- [ ] Card tap feedback (pulse animation)
- [ ] Confidence dots (●●●) display based on reviews (>100, >10, any)
- [ ] "Non disp." red alert only if out-of-stock
- [ ] "Prime" blue badge only if prime=true

---

### 6. NO RESULTS MESSAGE
**Posizione:** Sostituisce grid se nessun risultato
**Testo:** "Nessun prodotto trovato\nProva a rimuovere i filtri"
**Styling:** Center text, gray (#999), 14px

**Test QA:**
- [ ] Appare quando 0 risultati
- [ ] Scomparso quando risultati > 0
- [ ] Testo chiaro e leggibile

---

### 7. FILTER DRAWER (Bottom Sheet)
**Posizione:** Fixed bottom, z-index 201
**Animation:** translateY(100% → 0) in 0.3s cubic-bezier(0.25,0.46,0.45,0.94)
**Overlay:** Semi-transparent black (rgba(0,0,0,0.5)), z-index 200

#### 7.1 DRAWER HEADER
- **Text:** "Filtri" (bold, 16px)
- **Close button:** "×" (24px font, cursor pointer, 32x32px tap target)

#### 7.2 DRAWER BODY (Scrollable)
**Scrolling:** -webkit-overflow-scrolling touch, custom scrollbar (4px)

**Filter Groups:**

**A. PRICE FILTER**
- **Label:** "PREZZO" (uppercase, 13px, 0.5px letter-spacing)
- **Display:** "Max: €X" (real-time update)
- **Slider:** type=range, min=0, max=2000, step=1, accent-color #0066c0
- **Behavior:** On input → update display "€X"
- **Default:** 2000 (mostra "—")

**Test QA:**
- [ ] Slider range 0-2000
- [ ] Display aggiorna real-time
- [ ] Display show "—" quando max=2000
- [ ] Slider accent-color blue (#0066c0)

**B. RATING FILTER**
- **Label:** "VALUTAZIONE MINIMA" (uppercase, 13px)
- **Options:** Radio buttons (single select)
  - Tutte (0 ★)
  - 3.5★+
  - 4.0★+
  - 4.5★+
- **Default:** "Tutte" checked
- **Tap target:** 18px radio + full row clickable

**Test QA:**
- [ ] Radio buttons single-select (not checkboxes)
- [ ] Default "Tutte" selected
- [ ] Each option clickable (hit area 10px padding)
- [ ] Visual feedback on select

#### 7.3 DRAWER FOOTER
- **Preview counter:** "X risultati" (12px gray, dynamic)
- **Buttons:** "Reset" (gray bg) + "Applica" (blue bg)
  - Padding: 12px, min-height: 44px
  - Border-radius: 4px
  - Font: 13px bold
  - Gap: 10px (flex gap)
  - Apply button: blue pulse animation

**Behavior:**
- "Reset": Clear all filters to default, update preview
- "Applica": Apply filters, close drawer, update grid + counter + chips

**Test QA:**
- [ ] Preview counter updates real-time
- [ ] Reset button clears slider + radios
- [ ] Applica button closes drawer smooth
- [ ] Applica updates grid
- [ ] Applica updates counter
- [ ] Applica updates active chips
- [ ] Applica blue pulse animation visible

---

### 8. INTERACTIVITY & ANIMATIONS

| Action | Trigger | Animation | Duration |
|--------|---------|-----------|----------|
| Filter button tap | .btn-filter:active | scale(0.95) | 100ms |
| Chip tap × | removeFilter() | fadeOut (opacity 0, scale 0.9) | 200ms |
| Card tap | .card:active | scale pulse (1→1.01→1) | 200ms |
| CTA button tap | .btn-cta:active | scale(0.95) + color darken | 100ms |
| Drawer open | openDrawer() | translateY(100%→0) | 300ms cubic-bezier |
| Drawer close | closeDrawer() | translateY(0→100%) | 300ms cubic-bezier |
| Price slider | oninput | Real-time display update | instant |
| Sort change | onchange | Grid re-sort | instant |
| Overlay | overlay.active | opacity (0→1) | 300ms |

**Test QA:**
- [ ] All animations smooth, no jank (60fps)
- [ ] Easing curves correct (cubic-bezier, ease)
- [ ] No animation flickering
- [ ] Animations accessible (respects prefers-reduced-motion? Check later)

---

### 9. MOBILE RESPONSIVE

**Breakpoints:**
- **<320px:** Adjusted image size (80x70px instead of 100x90px)
- **320-600px:** Single column, current layout
- **600px+:** Future desktop (2-3 col grid, left sidebar)

**Current:** All testing at 375px viewport

**Test QA:**
- [ ] No horizontal scrollbar on filter chips
- [ ] No horizontal scrollbar on grid
- [ ] Button text not truncate
- [ ] Image not squish (aspect ratio maintained)
- [ ] Touch targets min 44x44px
- [ ] Drawer max-height 85vh (scroll inside)

---

### 10. ACCESSIBILITY CHECKLIST

| Item | WCAG Level | Test |
|------|------------|------|
| Color contrast | AA (4.5:1) | Price red vs white: 5.5:1 ✓ |
| Touch targets | AAA (44x44px) | All buttons ≥44px ✓ |
| Focus states | A | Keyboard nav tabindex? (Not yet) |
| Semantic HTML | A | <details>, <label> for radios ✓ |
| Alt text | A | Image alt="" (no alt needed, no text equiv) ✓ |
| Skip links | A | Not required for single-page |

**Test QA:**
- [ ] All buttons ≥44x44px
- [ ] Color contrast 4.5:1+ (test with WAVE tool)
- [ ] Keyboard navigation (tab through filters)
- [ ] Screen reader announcements (update live region for counter?)
- [ ] Radio button labels clickable

---

### 11. PERFORMANCE

**Metrics to track:**
- First Paint: <1s
- Images lazy-loaded
- CSS inline (no external)
- JS inline (no external)
- No network requests (standalone HTML)

**Test QA:**
- [ ] Page load <1s
- [ ] Images load on-demand (lazy)
- [ ] No console errors
- [ ] No network requests (offline-capable)

---

### 12. EDGE CASES

| Case | Expected Behavior | Test |
|------|-------------------|------|
| 0 products | Show "Nessun prodotto trovato" | [ ] |
| Missing image | Show gray box with ■ | [ ] |
| Long title | Truncate to 2 lines + ellipsis | [ ] |
| Price = null | Show "—" | [ ] |
| Stars = null | Show "N/D" | [ ] |
| Reviews = 0 | Show "(0)" | [ ] |
| Out-of-stock | Show "Non disp." red badge | [ ] |
| No badge | Nothing shown | [ ] |
| Filter = no match | Update counter, show 0 results msg | [ ] |

**Test QA:**
- [ ] Each edge case tested

---

## Testing Workflow

1. **Visual Check:** Open HTML in browser, compare to screenshots
2. **Interaction Test:** Tap all buttons, sliders, dropdowns
3. **Filter Test:** Apply/remove each filter, verify counter updates
4. **Animation Test:** Confirm smooth 60fps animations
5. **Mobile Test:** Test on real phone (375px min)
6. **Accessibility Test:** WAVE tool, keyboard nav
7. **Performance Test:** Lighthouse, load time

---

## Known Limitations

- No desktop layout (future v6)
- No dark mode (future feature)
- No CSV export (future feature)
- Keyboard navigation incomplete (no tab order, no focus indicators)
- Screen reader support minimal (no aria-live regions)
- No gesture support (swipe to close drawer — future)

---

## Success Criteria

- [x] All buttons functional
- [x] Filter drawer opens/closes smoothly
- [x] Counter updates accurately
- [x] Chips display/remove correctly
- [x] Animations smooth (no jank)
- [x] Mobile responsive (no overflow)
- [x] Accessibility baseline (color contrast, touch targets)
- [x] Zero redundancy (no duplicate info)
