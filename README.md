# DDoS Sentinel — Global Real-Time Attack Visualizer

A dark, high-end cybersecurity operations center (SOC) dashboard and simulation engine for real-time global DDoS attack monitoring. Built with **FastAPI**, **SQLAlchemy/asyncpg**, **Cloudflare Radar Telemetry**, **Next.js 16**, **Three.js / globe.gl**, and **Zustand**.

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
│   ├── radar/                      # Cloudflare Radar API client & sync worker
│   ├── simulator/                  # Probabilistic attack event generator
│   └── websocket/                  # Real-time WebSocket connection manager & router
│
├── frontend/                       # Next.js 16 Frontend App
│   ├── src/app/
│   │   ├── page.tsx                # Marketing landing page (SSR + client islands)
│   │   ├── dashboard/page.tsx      # Main 3-column SOC Operations Dashboard
│   │   └── globals.css             # Design tokens & Sentinel dark theme
│   ├── src/components/
│   │   ├── Globe.tsx               # Dynamic client-only WebGL wrapper
│   │   ├── GlobeCanvas.tsx         # globe.gl / Three.js 3D visualization
│   │   ├── AttackIntensity.tsx     # Severity distribution tracker
│   │   ├── LiveAttacks.tsx         # Real-time streaming attack feed
│   │   ├── AttackTypes.tsx         # Protocol & vector proportions
│   │   ├── TopCountries.tsx        # Attacking country rankings
│   │   ├── TargetDistribution.tsx  # Continental target SVG donut chart
│   │   ├── MetricsBar.tsx          # 6-card live metrics bar with SVG sparklines
│   │   ├── Topbar.tsx              # Operations header with LIVE indicator
│   │   └── landing/                # Modular landing page components
│   ├── src/store/useRadarStore.ts  # Zustand global telemetry state
│   └── src/hooks/useDemoData.ts    # Synthetic fallback simulation
```

---

## ⚙️ Environment Variables

### Backend (`.env`)

| Variable | Description | Default |
|---|---|---|
| `SUPABASE_DATABASE_URL` | PostgreSQL connection URI (`asyncpg` driver) | Required for DB storage |
| `CF_API_TOKEN` | Cloudflare Radar API token (server-side only) | Optional (simulation fallback) |
| `RADAR_REFRESH_SECONDS` | Ingestion poll interval in seconds | `300` |
| `WS_EVENT_INTERVAL_MS` | WebSocket event emission tick | `250` |
| `MAX_ACTIVE_EVENTS` | Maximum concurrent active attack paths | `50` |
| `CORS_ORIGINS` | Allowed frontend origins (JSON array) | `["http://localhost:3000"]` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Base HTTP endpoint of the backend | `http://localhost:8000/api/v1` |
| `NEXT_PUBLIC_WS_URL` | WebSocket stream endpoint | `ws://localhost:8000/api/v1/ws/radar` |
| `NEXT_PUBLIC_DEMO_MODE`| Enable synthetic telemetry if backend is offline | `true` |

---

## 🛡️ Key Features

- **High-Precision 3D Globe:** Renders directional, severity-coded attack arcs (Critical `#FF3B4E`, High `#FF7A18`, Medium `#FFB52E`, Low `#12C8B0`) with distinct source vs. target node markers.
- **Autonomous Simulation Engine:** Reconstructs continuous real-time attack flows from discrete 24-hour Cloudflare Radar statistical distributions.
- **Resilient Fallback Mode:** Seamless client-side demo generation automatically engages when the server is offline or reconnecting.
- **Zero-Dependency Vector Visualizations:** Lightweight, SVG-driven sparklines, donut charts, and proportion bars with zero heavy charting overhead.
