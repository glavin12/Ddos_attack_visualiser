#!/usr/bin/env bash
# Container startup: optionally fetch the GeoLite2 City database, then launch
# the API. GeoLite2 is licensed and never committed — it is downloaded here at
# runtime when MAXMIND_KEY is present. Without it, IOCs still stream to the
# ThreatFeed list but are not placed on the globe (by design).
set -euo pipefail

DB_PATH="${MAXMIND_CITY_DB_PATH:-./data/GeoLite2-City.mmdb}"

if [ -f "$DB_PATH" ]; then
  echo "GeoLite2 DB already present at $DB_PATH — skipping fetch."
elif [ -n "${MAXMIND_KEY:-}" ]; then
  echo "Fetching GeoLite2-City database..."
  # Never fatal: a failed geo fetch degrades gracefully (dots absent, list intact).
  ./fetch-geolite2.sh || echo "WARN: GeoLite2 fetch failed; IOCs will not be geolocated onto the globe."
else
  echo "WARN: MAXMIND_KEY unset — skipping GeoLite2 fetch; IOCs will not be geolocated onto the globe."
fi

exec uv run --no-dev uvicorn ddos_attack_project.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
