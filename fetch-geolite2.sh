#!/usr/bin/env bash
# fetch-geolite2.sh
# Downloads the MaxMind GeoLite2 City database used to geolocate threat
# indicators (src/ddos_attack_project/threatintel/geoip.py), and places it
# at the path GeoIPService expects by default: ./data/GeoLite2-City.mmdb
# (override with MAXMIND_CITY_DB_PATH if you keep it elsewhere).
#
# Requires a free MaxMind GeoLite2 account + license key:
#   https://www.maxmind.com/en/geolite2/signup
# Generate the key under Account -> Manage License Keys, then:
#
# Usage:
#   MAXMIND_KEY=your_license_key ./fetch-geolite2.sh
#
# Re-run this periodically (MaxMind refreshes GeoLite2 roughly weekly) —
# it always overwrites the existing file with the latest snapshot.

set -euo pipefail

if [ -z "${MAXMIND_KEY:-}" ]; then
  echo "Error: set MAXMIND_KEY first, e.g. MAXMIND_KEY=xxxx ./fetch-geolite2.sh" >&2
  echo "(Same value as MAXMIND_KEY in .env — this script does not read .env for you.)" >&2
  exit 1
fi

DEST_DIR="${MAXMIND_CITY_DB_DIR:-./data}"
DEST_FILE="$DEST_DIR/GeoLite2-City.mmdb"
URL="https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=${MAXMIND_KEY}&suffix=tar.gz"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

echo "Downloading GeoLite2-City..."
HTTP_STATUS="$(curl -sSL -w '%{http_code}' -o "$TMP_DIR/geolite2-city.tar.gz" "$URL")"
if [ "$HTTP_STATUS" != "200" ]; then
  echo "Error: download failed with HTTP $HTTP_STATUS — check that MAXMIND_KEY is a valid, active license key." >&2
  exit 1
fi

echo "Extracting..."
tar -xzf "$TMP_DIR/geolite2-city.tar.gz" -C "$TMP_DIR"

MMDB_PATH="$(find "$TMP_DIR" -name 'GeoLite2-City.mmdb' -print -quit)"
if [ -z "$MMDB_PATH" ]; then
  echo "Error: GeoLite2-City.mmdb not found inside the downloaded archive." >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
mv "$MMDB_PATH" "$DEST_FILE"

echo ""
echo "Done. GeoLite2 City DB installed at $DEST_FILE"
echo "Restart the backend so GeoIPService picks it up."
