#!/bin/bash
# ── Meeth 3D Buildings Viewer ──────────────────────────────────────
# Double-click this file on macOS to launch the map in your browser.
# Requires Python 3 (pre-installed on macOS 10.15+).
# ──────────────────────────────────────────────────────────────────
cd "$(dirname "$0")"
PORT=8765

# Kill anything already on the port
lsof -ti:$PORT | xargs kill -9 2>/dev/null
sleep 0.3

echo "Starting local server on http://localhost:$PORT …"
python3 -m http.server $PORT &
SERVER_PID=$!
sleep 1

open "http://localhost:$PORT/meeth_3d_buildings.html"
echo "Map open. Close this window to stop the server."
wait $SERVER_PID
