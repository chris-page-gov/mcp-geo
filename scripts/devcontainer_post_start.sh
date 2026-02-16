#!/usr/bin/env bash
set -euo pipefail

# Best-effort workspace ownership repair.
# On Docker Desktop (macOS/Windows) the workspace mount can produce root-owned files.
# Avoid touching .git (some mounts make objects immutable).

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspaces/mcp-geo}"
CODEX_HOME_DIR="${CODEX_HOME:-/home/vscode/.codex}"

if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  sudo find "$WORKSPACE_ROOT" -xdev \
    \( -path "$WORKSPACE_ROOT/.git" -o -path "$WORKSPACE_ROOT/.git/*" \) -prune -o \
    \( -user root -o -group root \) -print0 \
    | sudo xargs -0r chown vscode:vscode >/dev/null 2>&1 || true

  if [[ -n "$CODEX_HOME_DIR" ]]; then
    sudo mkdir -p "$CODEX_HOME_DIR" >/dev/null 2>&1 || true
    sudo chown -R vscode:vscode "$CODEX_HOME_DIR" >/dev/null 2>&1 || true
  fi
fi

if ! python3 - <<'PY' >/dev/null 2>&1
try:
    import loguru
except Exception:
    raise SystemExit(1)
PY
then
  if ! python3 -m pip install -e ".[dev,boundaries,test]" >/dev/null 2>&1; then
    echo "mcp-geo: dependency auto-install failed; run: python3 -m pip install -e \".[dev,boundaries,test]\"" >&2
  fi
fi

if [[ -x "./scripts/devcontainer_mcp_setup.sh" ]]; then
  ./scripts/devcontainer_mcp_setup.sh >/dev/null 2>&1 || true
fi

start_http="${MCP_GEO_DEVCONTAINER_START_HTTP:-}"
if [[ "${start_http}" =~ ^(1|true|yes)$ ]]; then
  mkdir -p logs
  http_running="0"

  if [[ -f logs/devcontainer-http.pid ]]; then
    pid=$(cat logs/devcontainer-http.pid 2>/dev/null || true)
    if [[ -n "${pid}" ]] && ps -p "${pid}" >/dev/null 2>&1; then
      http_running="1"
    fi
  fi

  if [[ "${http_running}" == "0" ]] && command -v lsof >/dev/null 2>&1; then
    if lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
      http_running="1"
    fi
  fi

  if [[ "${http_running}" == "0" ]]; then
    if command -v setsid >/dev/null 2>&1; then
      setsid python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload \
        > logs/devcontainer-http.log 2>&1 < /dev/null &
    else
      nohup python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload \
        > logs/devcontainer-http.log 2>&1 < /dev/null &
    fi
    echo $! > logs/devcontainer-http.pid
  fi
fi
