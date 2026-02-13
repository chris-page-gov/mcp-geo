#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_LOG_DIR="$REPO_ROOT/research/map_delivery_research_2026-02/evidence/logs"
mkdir -p "$EVIDENCE_LOG_DIR"
RUN_LOG="$EVIDENCE_LOG_DIR/map_delivery_trials_run_$(date -u +%Y%m%dT%H%M%SZ).log"

echo "[map-trials] ensuring devcontainer is running..."
devcontainer up --workspace-folder "$REPO_ROOT" >/dev/null

echo "[map-trials] resetting trial observation log..."
devcontainer exec --workspace-folder "$REPO_ROOT" bash -lc \
  "cd /workspaces/mcp-geo && : > research/map_delivery_research_2026-02/evidence/logs/playwright_trials_observations.jsonl"

echo "[map-trials] executing Playwright trial matrix inside devcontainer..."
devcontainer exec --workspace-folder "$REPO_ROOT" \
  bash -lc "cd /workspaces/mcp-geo && npm --prefix playground run test:trials" \
  | tee "$RUN_LOG"

echo "[map-trials] verifying map panel screenshots contain visible detail..."
devcontainer exec --workspace-folder "$REPO_ROOT" \
  bash -lc "cd /workspaces/mcp-geo && python scripts/map_trials/verify_map_screenshots.py" \
  | tee -a "$RUN_LOG"

echo "[map-trials] generating markdown summary from this run..."
devcontainer exec --workspace-folder "$REPO_ROOT" \
  bash -lc "cd /workspaces/mcp-geo && python scripts/map_trials/summarize_playwright_trials.py" \
  | tee -a "$RUN_LOG"

echo "[map-trials] run log: $RUN_LOG"
