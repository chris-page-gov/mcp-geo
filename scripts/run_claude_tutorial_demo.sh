#!/usr/bin/env bash
set -euo pipefail

# Text-first demo runner for the Claude tutorial flow.
# Requires a running mcp-geo HTTP server (default: http://127.0.0.1:8000).

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-logs/claude_tutorial_demo}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${OUT_DIR}/${STAMP}"

mkdir -p "${RUN_DIR}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

say() {
  printf '\n%s\n' "$1"
}

call_tool() {
  local name="$1"
  local payload="$2"
  local out_file="$3"
  curl -sS "${BASE_URL}/tools/call" \
    -H 'content-type: application/json' \
    -d "{\"tool\":\"${name}\",${payload}}" >"${out_file}"
}

print_title() {
  local title="$1"
  printf '\n============================================================\n'
  printf '%s\n' "${title}"
  printf '============================================================\n'
}

print_title "MCP Geo Claude Tutorial Demo (Text Mode)"
echo "BASE_URL: ${BASE_URL}"
echo "Output:   ${RUN_DIR}"

say "0) Health check"
HEALTH_CODE="$(curl -s -o /dev/null -w '%{http_code}' "${BASE_URL}/health" || true)"
if [[ -z "${HEALTH_CODE}" || "${HEALTH_CODE}" == "000" ]]; then
  echo "Could not connect to ${BASE_URL}." >&2
  echo "Start the server first:" >&2
  echo "  uvicorn server.main:app --reload" >&2
  exit 1
fi
echo "Health status: ${HEALTH_CODE}"
if [[ "${HEALTH_CODE}" != "200" ]]; then
  echo "Server is not healthy at ${BASE_URL}. Start it first:" >&2
  echo "  uvicorn server.main:app --reload" >&2
  exit 1
fi

say "1) Prompt: Find tools related to postcode search."
curl -sS "${BASE_URL}/tools/search" \
  -H 'content-type: application/json' \
  -d '{"query":"postcode search","limit":8}' \
  > "${RUN_DIR}/01_tools_search.json"
python3 - "${RUN_DIR}/01_tools_search.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
tools=data.get("tools",[])
print("Top tools:")
for t in tools[:8]:
    print(f"- {t.get('name')} (score={t.get('score')})")
PY

say "2) Prompt: Open a map so I can select wards in Westminster."
call_tool \
  "os_apps.render_geography_selector" \
  '"level":"WARD","focusName":"Westminster","focusLevel":"local_auth"' \
  "${RUN_DIR}/02_geography_selector.json"
python3 - "${RUN_DIR}/02_geography_selector.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
print("Selector status:", data.get("status"))
print("Instructions:", data.get("instructions"))
print("UI URI:", data.get("resourceUri"))
PY

say "3) Simulate selected ward for follow-up (St James's in Westminster)."
call_tool \
  "admin_lookup.find_by_name" \
  '"text":"St James'"'"'s","levels":["WARD"],"limit":1' \
  "${RUN_DIR}/03_find_ward.json"

WARD_ID="$(python3 - "${RUN_DIR}/03_find_ward.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
results=data.get("results",[])
if results and isinstance(results[0], dict):
    print(results[0].get("id",""))
else:
    print("")
PY
)"

if [[ -z "${WARD_ID}" ]]; then
  echo "Could not resolve ward id from admin_lookup.find_by_name output." >&2
  echo "Inspect: ${RUN_DIR}/03_find_ward.json" >&2
  exit 1
fi
echo "Selected ward id: ${WARD_ID}"

say "4) Prompt: Fetch the boundary bbox for the selected ward."
call_tool \
  "admin_lookup.area_geometry" \
  "\"id\":\"${WARD_ID}\"" \
  "${RUN_DIR}/04_area_geometry.json"

python3 - "${RUN_DIR}/04_area_geometry.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
bbox=data.get("bbox")
print("Boundary bbox:", bbox)
print("Live source:", data.get("live"))
PY

say "5) Optional static map baseline for slide screenshots."
python3 - "${RUN_DIR}/04_area_geometry.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
bbox=data.get("bbox") or [-0.15198,51.49336,-0.11098,51.51662]
print(",".join(str(x) for x in bbox))
PY
read -r BBOX_CSV < <(python3 - "${RUN_DIR}/04_area_geometry.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
bbox=data.get("bbox") or [-0.15198,51.49336,-0.11098,51.51662]
print(",".join(str(x) for x in bbox))
PY
)

call_tool \
  "os_maps.render" \
  "\"bbox\":[${BBOX_CSV}],\"size\":1024,\"zoom\":13" \
  "${RUN_DIR}/05_os_maps_render.json"

python3 - "${RUN_DIR}/05_os_maps_render.json" <<'PY'
import json,sys
p=sys.argv[1]
data=json.load(open(p))
render=data.get("render",{})
print("Map URL:", render.get("urlTemplate") or render.get("url") or "n/a")
print("Note: If OS_API_KEY is missing, this call may return NO_API_KEY.")
PY

print_title "Demo Complete"
echo "Artifacts written to:"
echo "  ${RUN_DIR}/01_tools_search.json"
echo "  ${RUN_DIR}/02_geography_selector.json"
echo "  ${RUN_DIR}/03_find_ward.json"
echo "  ${RUN_DIR}/04_area_geometry.json"
echo "  ${RUN_DIR}/05_os_maps_render.json"
