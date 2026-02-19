#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"
HTTP_PORT="${MCP_GEO_HTTP_PORT:-8000}"
UI_PORT="${MCP_GEO_PLAYGROUND_PORT:-5173}"
HTTP_LOG="$LOG_DIR/playground-demo-http.log"
UI_LOG="$LOG_DIR/playground-demo-ui.log"
HTTP_PID="$LOG_DIR/playground-demo-http.pid"
UI_PID="$LOG_DIR/playground-demo-ui.pid"

log() {
  printf "[playground-demo] %s\n" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "missing required command: $1"
    exit 1
  fi
}

port_listening() {
  local port="$1"
  lsof -n -P -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
}

port_report() {
  local port="$1"
  if port_listening "$port"; then
    log "port $port is already in use:"
    lsof -n -P -iTCP:"$port" -sTCP:LISTEN || true
    return 0
  fi
  log "port $port is available"
  return 1
}

require_cmd lsof
require_cmd npm
require_cmd python3

mkdir -p "$LOG_DIR"

port_report "$HTTP_PORT" || true
port_report "$UI_PORT" || true

if ! port_listening "$HTTP_PORT"; then
  if ! python3 -c "import uvicorn" >/dev/null 2>&1; then
    log "python deps missing; run 'pip install -e .[test]' first."
    exit 1
  fi
  log "starting HTTP server on port $HTTP_PORT"
  nohup python3 -m uvicorn server.main:app --host 0.0.0.0 --port "$HTTP_PORT" \
    >"$HTTP_LOG" 2>&1 &
  echo $! > "$HTTP_PID"
fi

if ! port_listening "$UI_PORT"; then
  if [[ ! -d "$REPO_ROOT/playground/node_modules" ]]; then
    log "installing playground dependencies"
    npm --prefix "$REPO_ROOT/playground" install
  fi
  log "starting playground UI on port $UI_PORT"
  nohup npm --prefix "$REPO_ROOT/playground" run dev -- --host 0.0.0.0 --port "$UI_PORT" \
    >"$UI_LOG" 2>&1 &
  echo $! > "$UI_PID"
fi

log "ready: http://localhost:$UI_PORT (UI)"
log "server: http://localhost:$HTTP_PORT (MCP HTTP)"
log "logs: $HTTP_LOG, $UI_LOG"
