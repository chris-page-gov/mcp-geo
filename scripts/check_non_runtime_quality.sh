#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUFF_BIN="${ROOT_DIR}/scripts/ruff-local"
MYPY_BIN="${ROOT_DIR}/scripts/mypy-local"
cd "${ROOT_DIR}"

echo "[quality] ruff (non-runtime reliability surfaces)"
"${RUFF_BIN}"

echo "[quality] mypy (non-runtime reliability surfaces)"
"${MYPY_BIN}"

echo "[quality] non-runtime static gates passed"
