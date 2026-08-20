# Deployment Guide

Threat Observatory runs as two independently deployed pieces plus a hosted
database:

| Piece      | Host     | Why                                                                    |
| ---------- | -------- | ---------------------------------------------------------------------- |
| Backend    | Render   | Needs a persistent WebSocket + long-lived asyncio ingestors (not serverless) |
| Frontend   | Vercel   | Next.js 16 App Router, static + edge friendly                          |
| Database   | Supabase | Already provisioned (project `rspwihovhxrussatidwo`)                   |

---

## 1. Backend → Render

The backend ships as a Docker image ([Dockerfile](Dockerfile)) described by a
Blueprint ([render.yaml](render.yaml)). GeoLite2 is **not** baked into the image;
it is fetched at container start by [docker-entrypoint.sh](docker-entrypoint.sh)
using `MAXMIND_KEY`.

### Steps

1. Push this branch to GitHub (Render deploys from the repo).
2. Render → **New → Blueprint** → select the repo → it reads `render.yaml`.
3. Set the secret env vars (all marked `sync: false`, so Render prompts for them):

   | Var                     | Value                                                                 |
   | ----------------------- | --------------------------------------------------------------------- |
   | `SUPABASE_DATABASE_URL` | Supabase **Session pooler** URI (IPv4-friendly), `...?sslmode=require` |
   | `CF_API_TOKEN`          | Cloudflare Radar API token                                            |
   | `THREAT_FOX_AUTH`       | abuse.ch ThreatFox key                                               |
   | `GREYNOISE_COMM_KEY`    | GreyNoise Community key (optional enrichment)                        |
   | `MAXMIND_KEY`           | MaxMind GeoLite2 license key (for the startup DB fetch)             |
   | `CORS_ORIGINS`          | JSON array with your Vercel origin, e.g. `["https://your-app.vercel.app"]` |

4. Deploy. Render health-checks `GET /api/v1/health`.
5. Note the service URL: `https://<service>.onrender.com`.

### Notes

- **Free plan sleeps when idle.** On wake, a cold start re-fetches GeoLite2
  (~65 MB) and the ingestors restart. Fine for a portfolio; upgrade to a paid
  instance for always-on ingestion.
- The Supabase **Session pooler** connection string is recommended — Render's
  network is IPv4 and the direct DB host is IPv6-only. The app already forces
  `ssl=require` and disables asyncpg statement caching for the pooler.

---

## 2. Frontend → Vercel

1. Vercel → **Add New → Project** → import the repo.
2. **Root Directory: `frontend`** (important — the Next.js app is a subfolder).
   Framework preset auto-detects as Next.js; leave build/output defaults.
3. Set env vars (see [frontend/.env.example](frontend/.env.example)) for the
   Production (and Preview) environment:

   | Var                    | Value                                                       |
   | ---------------------- | ----------------------------------------------------------- |
   | `NEXT_PUBLIC_API_URL`  | `https://<service>.onrender.com/api/v1`                     |
   | `NEXT_PUBLIC_WS_URL`   | `wss://<service>.onrender.com/api/v1/ws/radar` (**wss**)    |
   | `NEXT_PUBLIC_SITE_URL` | `https://<your-app>.vercel.app`                             |

4. Deploy, then copy the Vercel URL back into the backend's `CORS_ORIGINS` on
   Render and redeploy the backend so the browser is allowed to connect.

---

## 3. Order of operations

1. Deploy the backend first → get its `onrender.com` URL.
2. Deploy the frontend with that URL in `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_WS_URL`.
3. Put the Vercel URL into `CORS_ORIGINS` on Render → redeploy backend.
4. Smoke-test:
   - `GET https://<service>.onrender.com/api/v1/health` → `200`
   - Open the Vercel URL → globe renders arcs + dots, ConnectionStatus shows Live.
