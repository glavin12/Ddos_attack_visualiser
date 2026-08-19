# Threat Observatory — Global DDoS & Threat-Intel Visualizer

A dark, high-end cybersecurity operations center (SOC) dashboard visualizing real global threat telemetry: Cloudflare Radar's 24-hour DDoS attack aggregates plus live indicators from public threat feeds (URLhaus, Feodo Tracker, ThreatFox). Built with **FastAPI**, **SQLAlchemy/asyncpg**, **Cloudflare Radar Telemetry**, **Next.js 16**, **Three.js / globe.gl**, and **Zustand**. Nothing on the globe is simulated — an offline backend means an empty globe and an honest connection status, never fake data.

---

## 🚀 Quick Start

### 1. Backend (FastAPI + Uvicorn)

#### Prerequisites
- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (recommended) or standard `pip` / `venv`

#### Installation & Setup

1. **Clone and navigate to the project root:**
   ```bash
   cd ddos_attack_project
   ```

2. **Set up Python environment:**
   ```bash
   # Using uv (fastest)
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate

   # Install dependencies
   uv pip install -e ".[dev]"
   # Or using standard pip:
   # pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   ```bash
   # Copy sample configuration
   cp .env.example .env
   ```
   *Edit `.env` to supply your `SUPABASE_DATABASE_URL` and optionally `CF_API_TOKEN`.*

4. **Start the Uvicorn Backend Server:**

   ```bash
   # Standard uvicorn command (with hot-reload):
   uvicorn ddos_attack_project.main:app --reload --host 0.0.0.0 --port 8000
   ```

   *Alternative invocation options:*
   ```bash
   # Using factory mode:
   uvicorn ddos_attack_project.main:create_app --factory --reload --port 8000

   # Or via uv directly:
   uv run uvicorn ddos_attack_project.main:app --reload --port 8000
   ```

   The backend will be available at:
   - **REST API:** `http://localhost:8000/api/v1`
   - **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
   - **WebSocket Stream:** `ws://localhost:8000/api/v1/ws/radar`

---

### 2. Frontend (Next.js 16 + React + Tailwind CSS v4)

#### Prerequisites
- Node.js >= 18.18
- npm / pnpm / yarn

#### Installation & Run

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Run Development Server:**
   ```bash
   npm run dev
   ```

   The frontend will be running at:
   - **Landing Page:** `http://localhost:3000`
   - **Operations Dashboard:** `http://localhost:3000/dashboard`

4. **Production Build:**
   ```bash
   npm run build
   npm start
   ```

---

## 🧭 Project Architecture

```
Ddos_Attack_project/
├── src/ddos_attack_project/        # FastAPI Python Backend
│   ├── main.py                     # FastAPI application factory & entrypoint
│   ├── config.py                   # Pydantic v2 settings management
│   ├── database.py                 # Async SQLAlchemy engine & session factory
│   ├── api/                        # REST API routers & query services
│   │   ├── router.py               # /radar/overview, /countries, /history, /status
│   │   └── service.py              # Telemetry aggregation query service
│   ├── db/                         # Database schema, models & repositories
│   ├── radar/                      # Cloudflare Radar API client & ingestor
│   ├── threatintel/                # abuse.ch feeds + GeoIP + GreyNoise enrichment
│   └── websocket/                  # Connection manager, pulse broadcaster & router
│
├── frontend/                       # Next.js 16 Frontend App
│   ├── src/app/
│   │   ├── page.tsx                # Marketing landing page (SSR + client islands)
│   │   ├── dashboard/page.tsx      # Main SOC Operations Dashboard
│   │   └── globals.css             # Design tokens & dark theme
│   ├── src/components/
│   │   ├── Globe.tsx               # Dynamic client-only WebGL wrapper
│   │   ├── GlobeCanvas.tsx         # globe.gl / Three.js 3D visualization
│   │   ├── AttackIntensity.tsx     # Top-5 routes panel (24h Radar aggregates)
│   │   ├── ThreatFeed.tsx          # Live real-IOC feed from public feeds
│   │   ├── AttackTypes.tsx         # Protocol & vector proportions
│   │   ├── TopCountries.tsx        # Attacking country rankings
│   │   ├── TargetDistribution.tsx  # Continental target SVG donut chart
│   │   ├── MetricsBar.tsx          # Live metrics bar with UTC clock
│   │   ├── Topbar.tsx              # Operations header with LIVE indicator
│   │   └── landing/                # Modular landing page components
│   ├── src/store/useRadarStore.ts  # Zustand global telemetry state
│   └── src/hooks/useWebSocket.ts   # WS stream: threat_indicator / radar_pulse
```

---

## ⚙️ Environment Variables

### Backend (`.env`)

| Variable | Description | Default |
|---|---|---|
| `SUPABASE_DATABASE_URL` | PostgreSQL connection URI (`asyncpg` driver) | Required |
| `CF_API_TOKEN` | Cloudflare Radar API token (server-side only) | Required |
| `RADAR_REFRESH_SECONDS` | Radar ingestion poll interval in seconds | `21600` |
| `RADAR_PULSE_INTERVAL_SECONDS` | `radar_pulse` WS heartbeat interval in seconds | `30` |
| `RADAR_PULSE_MAX_ROUTES` | Max routes per layer in each pulse | `30` |
| `THREAT_FOX_AUTH` | ThreatFox (abuse.ch) API key — feed skipped if unset | — |
| `GREYNOISE_COMM_KEY` | GreyNoise Community key for IOC enrichment | — |
| `MAXMIND_CITY_DB_PATH` | GeoLite2 City `.mmdb` path for IOC geolocation | `./data/GeoLite2-City.mmdb` |
| `CORS_ORIGINS` | Allowed frontend origins (JSON array) | `["http://localhost:3000"]` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base HTTP endpoint of the backend | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_WS_URL` | WebSocket stream endpoint | `ws://localhost:8000/api/v1/ws/radar` |

---

## 🛡️ Key Features

- **High-Precision 3D Globe:** Traveling comet arcs render Cloudflare Radar's 24-hour aggregate attack routes — brighter arcs carry a larger share of attack traffic — refreshed by a backend-driven WebSocket pulse.
- **Real Threat Indicators:** Live IOCs from URLhaus, Feodo Tracker, and ThreatFox, geolocated via MaxMind GeoLite2 and optionally enriched with GreyNoise, stream onto the globe as they are ingested.
- **Honest Data Model:** Everything on screen comes from real sources; the legend distinguishes aggregate routes from live indicators, and an offline backend shows an empty globe instead of fabricated data.
- **Zero-Dependency Vector Visualizations:** Lightweight, SVG-driven sparklines, donut charts, and proportion bars with zero heavy charting overhead.
