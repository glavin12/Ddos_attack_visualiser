# CLAUDE.md — Threat Observatory

Context and working rules for Claude Code sessions in this repo. Read this first, then the docs it points to, before changing anything.

---

## 1. What we are building

**Threat Observatory** (formerly DDoS Sentinel) is a defensive, real-time global threat **visualization** dashboard — a portfolio project demonstrating a full telemetry pipeline.

```
Cloudflare Radar (24h DDoS aggregates)      abuse.ch feeds (URLhaus / Feodo / ThreatFox)
        ↓                                            ↓
FastAPI backend (ingest → validate → normalize → store / enrich)
        ↓                                            ↓
PostgreSQL (Supabase) — normalized observations + real IOCs
        ↓                                            ↓
WebSocket: radar_pulse (aggregate heartbeat)   threat_indicator (real IOCs)
        ↓
Next.js frontend — 3D globe (globe.gl / Three.js) + analytics
```

- Backend: `src/ddos_attack_project/` — FastAPI, SQLAlchemy 2.x async + asyncpg, Pydantic v2, httpx. Tests in `tests/`.
- Frontend: `frontend/` — Next.js 16 (App Router), TypeScript, Tailwind CSS v4, Zustand, globe.gl/Three.js.
- Database: Supabase-hosted PostgreSQL. Migrations in `supabase/migrations/`.

### What we are NOT building

- NOT a DDoS attack tool, packet generator, or botnet.
- NOT an individual-IP attribution system for Radar data. Radar gives country-level aggregates; threat-intel dots are real public IOCs, not "confirmed DDoS attacks."
- NOT a synthetic-event simulator — **the synthetic simulator and demo-mode fallback were removed** (commits `729b7e3` + the `radar_pulse` follow-up). Everything rendered is real; an offline backend yields an empty globe + honest status.

See `Docs/IMPLEMENTATION.md` §1.1–1.3 (plus the SUPERSEDED MODEL NOTICE at its top) for the full statement.

---

## 2. Current state (transparency snapshot)

- **Backend: working, real-only pipeline.** Radar ingest loop (6h cadence) persists normalized observations; abuse.ch threat-intel ingest (URLhaus / Feodo Tracker / ThreatFox, GeoLite2 geolocation, optional GreyNoise enrichment) persists real IOCs with 7d retention; `RadarPulseBroadcaster` pushes the latest 24h aggregates over WS as `radar_pulse` (30s heartbeat, immediately after each Radar refresh, and once per client on connect). Test suite in `tests/` passes (153 passed, 3 skipped at last check).
- **Frontend: working.** Globe renders comet arcs from Radar aggregates (REST bootstrap + `radar_pulse` WS push — the backend, not the frontend, drives updates) and real IOC dots streamed as `threat_indicator`s. The demo/synthetic fallback (`useDemoData`, `DEMO_MODE`, `isSynthetic` plumbing) was **fully removed**; offline = empty globe + ConnectionStatus signal.
- **Integration:** REST + WebSocket contracts in `Docs/IMPLEMENTATION.md` §23–32 (§31–32 documents the current 4-message WS protocol: `threat_indicator | radar_pulse | stats | system`). Frontend consumes them via `frontend/src/lib/api.ts` and `frontend/src/hooks/useWebSocket.ts`.
- **No demo mode exists anymore.** The old `NEXT_PUBLIC_DEMO_MODE` env var and its hook are deleted; do not reintroduce synthetic data paths.

When starting work, check `git log --oneline -10` and `git status` to confirm nothing changed since this file was written.

---

## 3. The transparency rules (non-negotiable)

This project's identity is **honest data representation**. Never compromise these:

1. **Everything on the globe is real.** Arcs derive from Cloudflare Radar aggregates; dots are real public-feed IOCs. There is no synthetic layer anymore — never reintroduce one.
2. **Never invent measurements.** No fabricated Mbps/pps/absolute counts. If Radar gives percentages, show percentages. If it gives relative `MIN0_MAX` timeseries, label it "relative activity" — never volume.
3. **Threat-indicator dots are real IOCs from public feeds**, not confirmed DDoS attacks and not exact attack locations (GeoLite2 is city-level approximation). Tooltips/legend must keep saying so.
4. **Never persist visualization state.** PostgreSQL stores normalized observations + real IOCs only; no synthetic or derived event rows.
5. **Never expose secrets** (`SUPABASE_DATABASE_URL`, `CF_API_TOKEN`, `THREAT_FOX_AUTH`, `GREYNOISE_COMM_KEY`) to the frontend or into `NEXT_PUBLIC_*`.

Full rules: `Docs/AGENTS.md` §7, §12, §20, §29; `Docs/IMPLEMENTATION.md` §1, §16 (see the SUPERSEDED notice for sections describing the deleted simulator).

---

## 4. Backend — where things live

```
src/ddos_attack_project/
├── main.py            # app factory, lifespan (Radar ingestor + threat-intel ingestor + pulse broadcaster)
├── config.py          # pydantic-settings (reads .env)
├── database.py        # async engine/session factory
├── dependencies.py    # DI (session, repos)
├── api/               # router.py (REST), schemas.py (Pydantic), service.py
├── db/                # models.py (SQLAlchemy), repositories.py, mappers.py
├── domain/            # canonical domain models + enums (internal language)
├── radar/             # client.py (httpx), external.py, adapters/, ingestor.py (on_refresh callback)
├── threatintel/       # ingestor.py, geoip.py, enrichment.py, sources/ (urlhaus, feodo, threatfox)
├── websocket/         # manager.py, envelopes.py, pulse.py (RadarPulseBroadcaster), router.py
└── data/              # GeoLite2-City.mmdb (downloaded manually)
```

### REST surface (implemented, contract in `Docs/IMPLEMENTATION.md` §23–30)

```
GET /api/v1/radar/overview
GET /api/v1/radar/attacks?layer=L3|L7
GET /api/v1/radar/countries?layer=&role=origin|target
GET /api/v1/radar/characteristics?layer=&type=protocol|vector|http_method
GET /api/v1/radar/history?layer=L3|L7
GET /api/v1/radar/status
GET /api/v1/health
WS  /api/v1/ws/radar     # threat_indicator | radar_pulse | stats | system
```

### Commands (PowerShell, from repo root)

```powershell
.venv\Scripts\activate                 # Python 3.11+, uv-managed venv
uv run uvicorn ddos_attack_project.main:app --reload --port 8000
uv run pytest                          # full test suite
uv run pytest tests/test_radar_pulse_broadcaster.py -v  # single module
```

Docs: `http://localhost:8000/docs`. WebSocket: `ws://localhost:8000/api/v1/ws/radar`.

### Backend rules (summarized from `Docs/AGENTS.md`)

- Domain models are the internal language; adapters are the only layer that sees Cloudflare field names (`originCountryAlpha2` etc.).
- Shares are parsed with `Decimal`, divided by 100 → canonical `0 <= share <= 1`. Timeseries `MIN0_MAX` values are NOT divided by 100. WS `radar_pulse` carries `share` as a JSON **number** (float) — `model_dump(mode="json")` stringifies Decimal, which would break the frontend contract.
- Radar failure → log, keep last known good dataset, continue. Never wipe valid data because one poll failed.
- SQLAlchemy 2.x async only (AsyncEngine/AsyncSession/async_sessionmaker). No sync DB calls in async endpoints.
- Schema changes must be migrations (Supabase migrations), then tests, then app update.
- No premature infrastructure (no Redis/Kafka/Celery unless a real need appears).
- Breaking changes (schema / REST / WS / env vars / event format) update backend + WS docs + frontend types + tests **in the same change**.
- WS envelope models are defined in `websocket/envelopes.py` only; `radar_pulse` route shape must keep mirroring REST `AttackRoute` (parity test in `tests/test_radar_pulse_envelope.py`).

---

## 5. Frontend — where things live

```
frontend/src/
├── app/                    # page.tsx (landing), dashboard/page.tsx, layout, error/loading/not-found
├── components/             # Globe.tsx, GlobeCanvas.tsx, MetricsBar, ThreatFeed,
│   │                       # AttackIntensity, AttackTypes, TopCountries, TopTargets,
│   │                       # TargetDistribution, HistoryChart, AnalyticsPanel/Drawer,
│   │                       # Topbar, Legend, ConnectionStatus, BarList, PanelStates
│   │                       # + landing/ (Hero, Nav, BentoShowcase, HowItWorks, ...)
├── store/useRadarStore.ts  # Zustand state (topRoutes + routesByLayer, per-slice status flags)
├── hooks/                  # useWebSocket.ts (threat_indicator | radar_pulse | stats | system)
└── lib/                    # api.ts, types.ts (API contract), constants.ts, format.ts, countries.ts
```

### Commands (PowerShell)

```powershell
cd frontend            # use workdir instead of cd in this tool
npm run dev            # http://localhost:3000  (dashboard at /dashboard)
npm run lint
npm run build          # must pass — Vercel-compliant repo
```

Env: `frontend/.env.local` — `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL` only.

### Frontend rules

- **Next.js 16 has breaking changes vs training data.** Before writing Next.js code, read `frontend/AGENTS.md` and the guide in `frontend/node_modules/next/dist/docs/` relevant to what you're touching.
- Frontend consumes only normalized backend contracts — never parse Cloudflare JSON.
- Bounded state everywhere: rolling window for events, no unbounded arrays, no React component per arc (globe is imperative globe.gl/Three.js).
- Visual direction is locked in `Docs/Frontend-Design-Plan.md`: deep space black (`#000308`), signal cyan (`#2FD1E0`, never `#00F0FF`), dark-only, 70% professional dataviz / 30% cyber aesthetic. No neon, Matrix rain, or hacker clichés.
- A11y/perf requirements from the Vercel audit are already applied (reduced-motion gates, aria-live, focus traps, `Intl.*` formatting via `lib/format.ts`, `content-visibility` virtualization). Don't regress them.
- The globe must stay the visual centerpiece and remain readable — the arc budget (`MAX_ARCS`, 30, matches the backend's `RADAR_PULSE_MAX_ROUTES`) controls density.
- **No demo/synthetic code paths.** If the WS is offline the globe is empty and `ConnectionStatus` shows Offline — that is the intended honest behavior. Do not add fabricated fallbacks (the removed `AttackTypes.FALLBACK` shares were the last of them).
- The store keeps both layers' routes (`routesByLayer`) so the backend's always-both-layers `radar_pulse` serves an instant L3/L7 toggle; `topRoutes` is the selected layer's view.

---

## 6. Known issues / open work

1. **Docs lag in places.** `Docs/IMPLEMENTATION.md` carries a SUPERSEDED MODEL NOTICE at the top; simulator-era sections are historical. `Docs/AGENTS.md` has a STATUS UPDATE banner. When touching contracts, keep §31–32 current.
2. **Transparency scope.** All future UI/backend work must keep aggregate-vs-IOC distinctions visible (legend, methodology copy). See `Docs/IMPLEMENTATION.md` §29-adjacent notice and `frontend/src/components/Legend.tsx`.
3. **Landing-page rename residue.** Dashboard is fully "Threat Observatory"; landing metadata updated, but any residual "DDoS Sentinel" strings in copy/screenshots should be fixed opportunistically.
4. **Known Radar data quirks** (by design, not bugs): L3 pair responses lack `rank` (L7 has it); `T1` = Cloudflare's Tor identifier; top-N shares don't sum to 1 and must NOT be renormalized; L3 = bytes, L7 = requests — never mix layers.
5. **GeoLite2 database is a manual download** — without `./data/GeoLite2-City.mmdb`, IOCs lack lat/lng and are never placed on the globe (by design; they still appear in the ThreatFeed list).

---

## 7. Workflow

1. Read this file, then `Docs/AGENTS.md` (rules), and the relevant spec in `Docs/`.
2. Inspect existing code before creating files; follow existing patterns (Pydantic v2 + DI on backend; `'use client'` islands + Zustand slices on frontend).
3. Smallest correct change; run tests / lint / build after.
4. Backend-first contract: define Pydantic + TS types together; don't invent API responses on the frontend.
5. Commits: small and meaningful (`feat:`, `fix:`, `test:` — see `Docs/AGENTS.md` §38). Never `stuff`/`final2`.
6. Ask before: replacing stack pieces, introducing infra (Redis/Kafka/etc.), changing WS protocol, changing the real/synthetic model, adding auth, or any major architectural decision.
7. Update this file (state snapshot / known issues) whenever project reality changes — that is the point of this document.

## 8. Doc index

| Doc | Purpose |
|---|---|
| `README.md` | Setup, architecture tree, env vars |
| `Docs/AGENTS.md` | Full engineering rules (43 sections) |
| `Docs/IMPLEMENTATION.md` | Frozen implementation spec — 11 Radar endpoints, contracts, sampling, simulator |
| `Docs/Database.md` | Schema, constraints, indexes, RLS, migrations |
| `Docs/Frontend-Design-Plan.md` | Visual direction + Vercel-compliance plan |
| `Docs/Radar-Sample-Outputs.md` | Real Cloudflare sample payloads |
| `frontend/AGENTS.md` | Next.js 16 agent rules (auto-generated, keep committed) |
