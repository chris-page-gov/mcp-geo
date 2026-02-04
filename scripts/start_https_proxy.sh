#!/usr/bin/env bash
set -euo pipefail

WORKDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UPSTREAM_HOST="127.0.0.1"
UPSTREAM_PORT="8000"
PROXY_HOST="127.0.0.1"
PROXY_PORT_START="8899"
PROXY_PORT_END="8909"
TRACE_LOG="${MCP_HTTP_TRACE_LOG:-logs/mcp-http-trace.jsonl}"
UPSTREAM_LOG="${MCP_UPSTREAM_LOG:-/tmp/mcp-geo-upstream.log}"
NGROK_START="${NGROK_START:-1}"
NGROK_DOMAIN="${NGROK_DOMAIN:-}"
NGROK_AUTHTOKEN="${NGROK_AUTHTOKEN:-}"

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    if command -v rg >/dev/null 2>&1; then
      ss -ltn "sport = :${port}" | rg -q ":${port}\\b"
    else
      ss -ltn "sport = :${port}" | grep -q ":${port}\\b"
    fi
  elif command -v lsof >/dev/null 2>&1; then
    lsof -i ":${port}" >/dev/null 2>&1
  else
    return 1
  fi
}

pick_free_port() {
  local port
  for port in $(seq "$PROXY_PORT_START" "$PROXY_PORT_END"); do
    if ! port_in_use "$port"; then
      echo "$port"
      return 0
    fi
  done
  return 1
}

if ! command -v python >/dev/null 2>&1; then
  echo "python not found in PATH" >&2
  exit 1
fi

if ! command -v uvicorn >/dev/null 2>&1; then
  echo "uvicorn not found in PATH. Run: pip install -e .[test]" >&2
  exit 1
fi

echo "Working dir: ${WORKDIR}"
cd "$WORKDIR"

mkdir -p "$(dirname "$TRACE_LOG")"
mkdir -p "$(dirname "$UPSTREAM_LOG")"

if port_in_use "$UPSTREAM_PORT"; then
  echo "Upstream already running on ${UPSTREAM_HOST}:${UPSTREAM_PORT}"
  upstream_pid=""
else
  echo "Starting upstream server on ${UPSTREAM_HOST}:${UPSTREAM_PORT}..."
  uvicorn server.main:app --host 0.0.0.0 --port "$UPSTREAM_PORT" --reload >"$UPSTREAM_LOG" 2>&1 &
  upstream_pid="$!"
  sleep 1
fi

proxy_port="$(pick_free_port)"
if [[ -z "${proxy_port}" ]]; then
  echo "No free proxy port found in ${PROXY_PORT_START}-${PROXY_PORT_END}" >&2
  if [[ -n "${upstream_pid}" ]]; then
    kill "${upstream_pid}" >/dev/null 2>&1 || true
  fi
  exit 1
fi

cleanup() {
  if [[ -n "${upstream_pid}" ]]; then
    kill "${upstream_pid}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${ngrok_pid:-}" ]]; then
    kill "${ngrok_pid}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "Starting HTTPS trace proxy on ${PROXY_HOST}:${proxy_port}..."
if [[ "${NGROK_START}" == "1" ]] && command -v ngrok >/dev/null 2>&1; then
  if [[ -n "${NGROK_AUTHTOKEN}" ]]; then
    ngrok config add-authtoken "${NGROK_AUTHTOKEN}" >/dev/null 2>&1 || true
  fi
  ngrok_args=("http" "${proxy_port}")
  if [[ -n "${NGROK_DOMAIN}" ]]; then
    ngrok_args+=("--domain=${NGROK_DOMAIN}")
  fi
  ngrok "${ngrok_args[@]}" >/tmp/mcp-geo-ngrok.log 2>&1 &
  ngrok_pid="$!"
  sleep 1
  if command -v curl >/dev/null 2>&1; then
    ngrok_url="$(curl -s http://127.0.0.1:4040/api/tunnels | python -c 'import json,sys; data=json.load(sys.stdin); print(data.get("tunnels",[{}])[0].get("public_url",""))' 2>/dev/null || true)"
  else
    ngrok_url=""
  fi
  if [[ -n "${ngrok_url}" ]]; then
    echo "Ngrok URL: ${ngrok_url}"
    echo "Health check: ${ngrok_url}/health"
    echo "MCP endpoint: ${ngrok_url}/mcp"
  else
    echo "Ngrok started. Check logs at /tmp/mcp-geo-ngrok.log for the URL."
  fi
else
  echo "Ngrok not started. To run it manually: ngrok http ${proxy_port}"
  echo "Health check via ngrok: https://<ngrok-id>.ngrok-free.app/health"
  echo "MCP endpoint via ngrok: https://<ngrok-id>.ngrok-free.app/mcp"
fi

python scripts/mcp_http_trace_proxy.py \
  --upstream "http://${UPSTREAM_HOST}:${UPSTREAM_PORT}/mcp" \
  --log "${TRACE_LOG}" \
  --host "${PROXY_HOST}" \
  --port "${proxy_port}"
