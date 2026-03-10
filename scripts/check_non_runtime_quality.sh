#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF_BIN="${ROOT_DIR}/scripts/ruff-local"
MYPY_BIN="${ROOT_DIR}/scripts/mypy-local"
cd "${ROOT_DIR}"

RUFF_TARGETS=(
  "server/mcp/tools.py"
  "tools/os_mcp.py"
  "tools/os_peat.py"
  "tests/test_os_peat.py"
  "tests/test_psr_peat_e2e.py"
  "tests/test_evaluation_harness_full.py"
  "tests/test_os_mcp_route_query.py"
)

MYPY_TARGETS=(
  "server/mcp/tools.py"
  "server/mcp/resource_catalog.py"
  "tools/os_mcp.py"
  "tools/os_peat.py"
  "tests/test_os_peat.py"
  "tests/test_psr_peat_e2e.py"
  "tests/test_evaluation_harness_full.py"
  "tests/test_os_mcp_route_query.py"
)

echo "[quality] ruff (non-runtime reliability surfaces)"
"${RUFF_BIN}" check "${RUFF_TARGETS[@]}"

echo "[quality] mypy (non-runtime reliability surfaces)"
"${MYPY_BIN}" --follow-imports=skip "${MYPY_TARGETS[@]}"

echo "[quality] non-runtime static gates passed"
