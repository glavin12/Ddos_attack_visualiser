#!/usr/bin/env bash
# fetch-radar-samples.sh
# Pulls real sample responses from every Cloudflare Radar endpoint this
# project uses, and saves each as its own JSON file under ./radar-samples/.
#
# Usage:
#   CF_API_TOKEN=your_token ./fetch-radar-samples.sh

set -euo pipefail

if [ -z "${CF_API_TOKEN:-}" ]; then
  echo "Error: set CF_API_TOKEN first, e.g. CF_API_TOKEN=xxxx ./fetch-radar-samples.sh"
  exit 1
fi

BASE="https://api.cloudflare.com/client/v4/radar"
OUT="./radar-samples"
mkdir -p "$OUT"

PYTHON_BIN=""
if command -v python3 &> /dev/null && python3 --version &> /dev/null; then
  PYTHON_BIN="python3"
elif command -v python &> /dev/null && python --version &> /dev/null; then
  PYTHON_BIN="python"
fi

fetch() {
  local name="$1"
  local url="$2"
  echo "Fetching $name..."
  curl -s "$url" -H "Authorization: Bearer $CF_API_TOKEN" -o "$OUT/$name.json"
  if [ -n "$PYTHON_BIN" ]; then
    "$PYTHON_BIN" -c "
import json, sys
data = json.load(open('$OUT/$name.json'))
if not data.get('success'):
    errs = [(e.get('code'), e.get('message')) for e in data.get('errors', [])]
    print(f'  WARNING: $name returned an error: {errs}', file=sys.stderr)
"
  fi
}

# Real attack pairs — the main data source for your arcs
fetch "layer3-top-attacks"        "$BASE/attacks/layer3/top/attacks?limit=100&dateRange=1d"
fetch "layer7-top-attacks"        "$BASE/attacks/layer7/top/attacks?limit=100&dateRange=1d"

# Broader single-side country coverage
fetch "layer3-top-origin"         "$BASE/attacks/layer3/top/locations/origin?limit=50&dateRange=1d"
fetch "layer3-top-target"         "$BASE/attacks/layer3/top/locations/target?limit=50&dateRange=1d"
fetch "layer7-top-origin"         "$BASE/attacks/layer7/top/locations/origin?limit=50&dateRange=1d"
fetch "layer7-top-target"         "$BASE/attacks/layer7/top/locations/target?limit=50&dateRange=1d"

# Real attack-type breakdown — could replace the simulated attackType field
fetch "layer3-summary-protocol"   "$BASE/attacks/layer3/summary/protocol?dateRange=1d"
fetch "layer3-summary-vector"     "$BASE/attacks/layer3/summary/vector?dateRange=1d"
fetch "layer7-summary-http-method" "$BASE/attacks/layer7/summary/http_method?dateRange=1d"

# Historical data, for a stats/chart panel later
fetch "layer3-timeseries"         "$BASE/attacks/layer3/timeseries?dateRange=7d&aggInterval=1h"
fetch "layer7-timeseries"         "$BASE/attacks/layer7/timeseries?dateRange=7d&aggInterval=1h"

echo ""
echo "Done. Sample responses saved in $OUT/"
echo "Pretty-print any of them with: cat $OUT/layer3-top-attacks.json | python3 -m json.tool"
