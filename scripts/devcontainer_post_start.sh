#!/usr/bin/env bash
set -euo pipefail

# Best-effort workspace ownership repair.
# On Docker Desktop (macOS/Windows) the workspace mount can produce root-owned files.
# Avoid touching .git (some mounts make objects immutable).

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspaces/mcp-geo}"
CODEX_HOME_DIR="${CODEX_HOME:-/home/vscode/.codex}"
RUNTIME_DATA_ROOT="${MCP_GEO_RUNTIME_DATA_ROOT:-/var/lib/mcp-geo}"

if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  sudo find "$WORKSPACE_ROOT" -xdev \
    \( -path "$WORKSPACE_ROOT/.git" -o -path "$WORKSPACE_ROOT/.git/*" \) -prune -o \
    \( -user root -o -group root \) -print0 \
    | sudo xargs -0r chown vscode:vscode >/dev/null 2>&1 || true

  if [[ -n "$CODEX_HOME_DIR" ]]; then
    sudo mkdir -p "$CODEX_HOME_DIR" >/dev/null 2>&1 || true
    sudo chown -R vscode:vscode "$CODEX_HOME_DIR" >/dev/null 2>&1 || true
  fi

  if [[ -n "$RUNTIME_DATA_ROOT" ]]; then
    sudo mkdir -p "$RUNTIME_DATA_ROOT" >/dev/null 2>&1 || true
    sudo chown -R vscode:vscode "$RUNTIME_DATA_ROOT" >/dev/null 2>&1 || true
  fi
fi

if ! python3 - <<'PY' >/dev/null 2>&1
try:
    import loguru
except Exception:
    raise SystemExit(1)
PY
then
  if ! python3 -m pip install -e . >/dev/null 2>&1; then
    echo "mcp-geo: runtime dependency auto-install failed; run: python3 -m pip install -e ." >&2
  elif ! python3 -m pip install -e ".[dev,test]" >/dev/null 2>&1; then
    echo "mcp-geo: optional dev/test extras install failed; run: python3 -m pip install -e \".[dev,test]\"" >&2
  fi
fi

# Auto-create boundary cache tables for fresh PostGIS named volumes.
if ! python3 - <<'PY' >/dev/null 2>&1
from __future__ import annotations

from pathlib import Path

try:
    import psycopg
except Exception:
    raise SystemExit(0)

from server.config import settings

if not (settings.BOUNDARY_CACHE_ENABLED and settings.BOUNDARY_CACHE_DSN):
    raise SystemExit(0)

schema_name = settings.BOUNDARY_CACHE_SCHEMA
table_name = settings.BOUNDARY_CACHE_TABLE
dataset_table_name = settings.BOUNDARY_DATASET_TABLE

with psycopg.connect(settings.BOUNDARY_CACHE_DSN) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s), to_regclass(%s)", (
            f"{schema_name}.{table_name}",
            f"{schema_name}.{dataset_table_name}",
        ))
        boundary_table, dataset_table = cur.fetchone()
if boundary_table and dataset_table:
    raise SystemExit(0)
raise SystemExit(1)
PY
then
  if ! python3 - <<'PY' >/dev/null 2>&1
from __future__ import annotations

from pathlib import Path

import psycopg

from server.config import settings

schema_sql = Path("scripts/boundary_cache_schema.sql")
if not schema_sql.exists():
    raise SystemExit(1)

sql_text = schema_sql.read_text(encoding="utf-8")
with psycopg.connect(settings.BOUNDARY_CACHE_DSN, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(sql_text)
PY
  then
    echo "mcp-geo: boundary cache schema bootstrap failed; run: psql \"\$BOUNDARY_CACHE_DSN\" -f scripts/boundary_cache_schema.sql" >&2
  fi
fi

# Auto-seed ons_geo cache with bundled bootstrap files when cache DB is empty.
if ! python3 - <<'PY' >/dev/null 2>&1
from __future__ import annotations

import sqlite3
from pathlib import Path

from server.config import settings

db_path = Path(settings.ONS_GEO_CACHE_DIR) / settings.ONS_GEO_CACHE_DB
if not db_path.exists():
    raise SystemExit(1)
try:
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM geo_lookup")
        row_count = int(cur.fetchone()[0])
except Exception:
    raise SystemExit(1)
if row_count > 0:
    raise SystemExit(0)
raise SystemExit(1)
PY
then
  bootstrap_dir="data/cache/ons_geo/bootstrap"
  if [[ -f "$bootstrap_dir/onspd_bootstrap.csv" \
     && -f "$bootstrap_dir/nspl_bootstrap.csv" \
     && -f "$bootstrap_dir/onsud_bootstrap.csv" \
     && -f "$bootstrap_dir/nsul_bootstrap.csv" ]]; then
    if ! python3 scripts/ons_geo_cache_refresh.py \
      --sources resources/ons_geo_sources.json \
      --cache-dir "${ONS_GEO_CACHE_DIR:-data/cache/ons_geo}" \
      --index-path "${ONS_GEO_CACHE_INDEX_PATH:-resources/ons_geo_cache_index.json}" \
      --db-name "${ONS_GEO_CACHE_DB:-ons_geo_cache.sqlite}" \
      --product-file "ONSPD=$bootstrap_dir/onspd_bootstrap.csv" \
      --product-file "NSPL=$bootstrap_dir/nspl_bootstrap.csv" \
      --product-file "ONSUD=$bootstrap_dir/onsud_bootstrap.csv" \
      --product-file "NSUL=$bootstrap_dir/nsul_bootstrap.csv" \
      >/dev/null 2>&1; then
      echo "mcp-geo: ons_geo cache bootstrap failed; run scripts/ons_geo_cache_refresh.py manually." >&2
    fi
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
