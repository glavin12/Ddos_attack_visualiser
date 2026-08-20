# Threat Observatory — backend container (FastAPI + asyncio ingestors + WS).
# Built for Render (or any Docker host). Uses uv for reproducible installs from
# the committed uv.lock. GeoLite2 is fetched at container start (never baked in),
# so the licensed .mmdb is never committed or redistributed.

FROM python:3.11-slim

# curl + ca-certificates + tar are needed by fetch-geolite2.sh at startup.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates tar \
    && rm -rf /var/lib/apt/lists/*

# uv (pinned image) provides the resolver/installer used locally.
COPY --from=ghcr.io/astral-sh/uv:0.12.2 /uv /uvx /bin/

WORKDIR /app

# Reproducible dependency + project install from the committed lockfile.
# README.md is required because pyproject references it.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

# Startup helpers.
COPY fetch-geolite2.sh docker-entrypoint.sh ./
RUN chmod +x fetch-geolite2.sh docker-entrypoint.sh

# uvicorn binds to $PORT (Render injects it); default for local `docker run`.
ENV PORT=8000 \
    MAXMIND_CITY_DB_PATH=./data/GeoLite2-City.mmdb
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
