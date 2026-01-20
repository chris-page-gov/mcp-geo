#!/usr/bin/env bash
set -euo pipefail

# Best-effort workspace ownership repair.
# On Docker Desktop (macOS/Windows) the workspace mount can produce root-owned files.
# Avoid touching .git (some mounts make objects immutable).

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/workspaces/mcp-geo}"

if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
  sudo find "$WORKSPACE_ROOT" -xdev \
    \( -path "$WORKSPACE_ROOT/.git" -o -path "$WORKSPACE_ROOT/.git/*" \) -prune -o \
    \( -user root -o -group root \) -print0 \
    | sudo xargs -0r chown vscode:vscode >/dev/null 2>&1 || true
fi

python -m pip install --user -e ".[test]" >/dev/null 2>&1 || true

if [[ -x "./scripts/devcontainer_mcp_setup.sh" ]]; then
  ./scripts/devcontainer_mcp_setup.sh >/dev/null 2>&1 || true
fi
