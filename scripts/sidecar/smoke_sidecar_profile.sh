#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/scripts/sidecar/docker-compose.map-sidecar.yml"

echo "[sidecar-smoke] starting optional sidecar profile..."
docker compose -f "$COMPOSE_FILE" up -d --wait

cleanup() {
  echo "[sidecar-smoke] stopping optional sidecar profile..."
  docker compose -f "$COMPOSE_FILE" down -v
}
trap cleanup EXIT

echo "[sidecar-smoke] probing Martin and pg_tileserv..."
curl -fsS "http://127.0.0.1:3000/catalog" >/dev/null
curl -fsS "http://127.0.0.1:7800/index.json" >/dev/null

echo "[sidecar-smoke] sidecar profile is healthy."
