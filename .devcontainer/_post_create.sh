#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m pip install -e '.[dev,test]'
python3 -m pip install -e '.[boundaries]' || echo 'mcp-geo: optional boundaries extras failed; continuing with core runtime'

if [ -d "playground" ]; then
  (cd playground && npm install --no-audit --no-fund) || true
  (cd playground && npx playwright install --with-deps) || true
fi
