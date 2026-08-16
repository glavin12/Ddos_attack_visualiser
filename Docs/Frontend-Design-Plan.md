# Frontend Design Plan — DDoS Atlas

> Status: IN PROGRESS — Phase A underway
> Last updated: Phase A execution

## Visual Direction (locked)
- **Background**: Deep space black — `#000308` page, `#070D18` panels, `#0A1320` raised, `#14253C` hairline
- **Globe**: Textureless deep sphere + glowing cyan country borders (no earth-night texture)
- **Accent**: Signal cyan (`--color-signal-cyan: #2FD1E0`) kept and reconciled across all hardcoded `#00F0FF` instances

## Decisions Confirmed
| Decision | Pick |
|---|---|
| Routing | A: `/` = landing, `/dashboard` = radar |
| New deps (landing) | Approve: `@phosphor-icons/react` + `motion` |
| Landing theme | Dark-only |
| Hero/bento imagery | I capture from running dashboard |
| Toast notifications | Yes (no new dep) |
| Deep-linking | Native `useSearchParams` (no new dep) |
| LiveFeed virtualization | `content-visibility: auto` (no new dep) |

---

## Phase A — Dashboard (Vercel-compliant, no new deps)

### A.1 — Design tokens + background family
- `globals.css`: Update `@theme` color tokens to deep space black family; add `color-scheme: dark`; lift text-muted/faint values for contrast on pure black
- `constants.ts COLORS`: Mirror new token values; canonical `--color-signal-cyan: #2FD1E0` everywhere (no more `#00F0FF`)
- `page.tsx`: Inline `style` bg values updated; `h-screen` → `min-h-[100dvh]`

### A.2 — Globe restyle
- `GlobeCanvas.tsx`: Drop `globeImageUrl`/`bumpImageUrl`; globe material `#040810`/`#020408`; polygons: transparent cap/side, stroke=cyan glowing; atmosphere=cyan@0.22
- Vendored GeoJSON + textures to `frontend/public/globe/` (local-first, CDN fallback)
- Globe asset error UI
- `touch-action: none` + `inert`+`user-select:none` during drag
- Guard arc/ring/sweep under `prefers-reduced-motion`
- `role="img"`+`aria-label` on globe container

### A.3 — HistoryChart fixes
- `NORMALIZED MIN0_MAX` → `MIN_MAX`
- `duration-400` → `duration-300`
- `.toFixed(2)` → `Intl.NumberFormat` via new `lib/format.ts`

### A.4 — Layout / semantics (Vercel)
- Skip-to-main link + `<main>` landmark
- Heading hierarchy: `h1` brand, `h2`/`h3` for panel titles (not `<span>`)
- `scroll-margin-top` on heading anchors
- Abstract desktop+mobile rail tabs into `<RailTabs>`
- Replace inline-style layer-toggle with `.layer-toggle--active` CSS class

### A.5 — Dark mode (Vercel)
- `color-scheme: dark` on `<html>`
- `<meta name="theme-color" content="#000308">`

### A.6 — Focus / hover / popover (Vercel)
- `:hover` states on page.tsx rail tabs + Topbar layer toggle
- `role="group"` + `aria-label` on layer toggle container; `aria-pressed` on buttons
- **Legend popover overhaul**: overlay `div onClick`→`button`; Escape handler; `role="dialog"`+`aria-modal`; focus trap; `aria-expanded` on toggle; `aria-label` on ✕ button; `overscroll-behavior: contain`

### A.7 — Animation discipline (Vercel)
- Replace `transition-all` in Topbar:170, AnalyticsPanel:50, BarList:81 with explicit properties
- `.bar-fill`: `width` → `transform: scaleX()` with `transform-origin: left`
- `prefers-reduced-motion`: gate feed-enter/exit keyframes + all Tailwind `animate-spin/ping/pulse`

### A.8 — Aria-live + aria-hidden (Vercel)
- `aria-hidden="true"` on all decorative animated indicators (Topbar ×3, Legend ×1, LiveFeed ×3)
- `aria-live="polite"` on: Topbar active-event count, DATA DEGRADED badge, LiveFeed `{n} CAPTURED`

### A.9 — lib/format.ts + typography (Vercel)
- `formatTime` / `formatNumber` / `formatPercent` / `formatDate` using `Intl.*`, locale from `navigator.languages` (SSR-safe)
- `.tabular-nums` utility; apply to ranks/percentages/counters/clocks
- `text-wrap: balance` on headings
- `translate="no"` on brand `DDoS ATLAS`
- Copy: Title Case in source, CSS `text-transform: uppercase` via `.type-label`

### A.10 — Errors / loading / demo (Vercel parity)
- Per-slice Zustand status flags `idle|loading|loaded|error`
- Skeleton shimmer for REST panels; inline retry with fix/next-step copy
- Globe: shaped skeleton loader; asset-error fallback
- Wire `useDemoData` behind `NEXT_PUBLIC_DEMO_MODE`; `real: false` events
- Wire or delete `fetchAttacks` / `fetchHealth`
- `AbortController` + timeout on `lib/api.ts` fetches

### A.11 — Navigation / state (Vercel)
- Active tab + selected layer → URL query params via `useSearchParams`
- `<Link>` for in-app navigation

### A.12 — LiveFeed virtualization
- `content-visibility: auto` + `contain-intrinsic-size` on feed rows

### A.13 — Route segments
- `app/loading.tsx` (skeleton), `app/error.tsx`, `app/not-found.tsx`

### A.14 — Verify
- `npm run lint`
- `npm run build`

---

## Phase B — Landing page (after Phase A)

### B.1 — Routing
- `/` = landing page; `/dashboard` = live radar (301 redirect from old `/`)
- `/methodology` = methodology deep-dive

### B.2 — Stack
- `@phosphor-icons/react` (one icon family, strokeWidth standardized)
- `motion/react` (isolated `'use client'` leaves for scroll-reveal + magnetic CTA)

### B.3 — Structure (8 sections)
1. Nav — wordmark + `Methodology` · `Source` · `Open dashboard`
2. Hero — asymmetric split: text left (≤2 lines headline, ≤20 words subtext, 1 primary CTA) / globe visual right
3. Trust strip — Simple Icons SVGs: Cloudflare, FastAPI, Next.js, Three.js, PostgreSQL, TypeScript
4. Bento "What it shows" — 3 cells with real screenshots
5. "How it works" — 3 verb-noun steps vertical stack
6. Pull-quote — ≤3 lines on honest data principle
7. Methodology summary — paragraph + link
8. Final CTA + footer

### B.4 — Pre-flight (taste-skill §14)
Zero em-dashes · one accent (cyan) · one radius system · CTA contrast WCAG AA · no CTA wrap · no serif · hero fits viewport · no scroll cues · no decorative dots · real images only · motion motivated · reduced-motion gate · mobile collapse explicit · `min-h-[100dvh]` · `useEffect` cleanups · Vercel-compliant

---

## Vercel Web Interface Guidelines — Coverage Map

| Category | Status |
|---|---|
| Accessibility (aria-label/aria-hidden/aria-live/semantics/headings/skip-link/scroll-margin) | ✓ |
| Focus (focus-visible kept, hover added, :focus-within where needed) | ✓ |
| Forms | N/A (no forms in dashboard; landing CTAs only) |
| Animation (reduced-motion full, transform/opacity-only, no `transition: all`) | ✓ |
| Typography (`…`, tabular-nums, text-wrap: balance, `Intl.*`) | ✓ |
| Content (truncate, min-w-0, empty states, Title Case) | ✓ |
| Images (next/image on landing, lazy/priority) | ✓ |
| Performance (AbortController, vendored assets, content-visibility, next/font preload) | ✓ |
| Navigation (deep-link tabs+layer via useSearchParams, `<Link>`) | ✓ |
| Touch (touch-action: manipulation/none, overscroll-behavior on popover, inert on drag) | ✓ |
| Safe Areas (env(safe-area-inset-*), overflow-x-hidden) | ✓ |
| Dark Mode (`color-scheme: dark`, meta theme-color) | ✓ |
| Locale (`Intl.*`, translate="no" on brand) | ✓ |
| Hydration (clock uses placeholder+useEffect) | ✓ |
| Hover (tabs/toggles hover states added) | ✓ |
| Content & Copy (active voice, numerals, specific labels, `&` over "and") | ✓ |
| Anti-patterns (no user-scalable=no, no paste-blocking, no outline-none, no div-onClick nav, no img-without-dims, no icon-button-without-aria-label, no hardcoded formats, no unjustified autoFocus) | ✓ |

---

## Anti-patterns resolved (from Vercel audit)

| File | Issue | Fix |
|---|---|---|
| layout.tsx | Missing `color-scheme: dark`, no `<meta name="theme-color">`, no skip link | Added |
| page.tsx | `<div>` wrapper not `<main>`, tab state not deep-linked | Fixed |
| globals.css | `transition: all` in `.bar-fill`, incomplete reduced-motion | Fixed |
| Topbar | `aria-hidden` missing on pulse/ping spans, `transition: all`, hardcoded locale, no `aria-live` on counts | Fixed |
| Legend | `div onClick` overlay, missing focus trap, icon button no aria-label, no aria-expanded | Fixed |
| LiveFeed | Hardcoded locale, `aria-hidden` missing on decorative glyphs, 100-row map without virtualization | Fixed |
| HistoryChart | `MIN0_MAX` typo, `duration-400`, `.toFixed()` hardcoded | Fixed |
| AnalyticsPanel | `transition: all`, `.toFixed()` hardcoded | Fixed |
| BarList | `transition: all`, `.toFixed()` hardcoded, no tabular-nums | Fixed |
| GlobeCanvas | No reduced-motion on arcs/rings, no aria-label on globe | Fixed |
| api.ts | No timeout/AbortController | Fixed |
