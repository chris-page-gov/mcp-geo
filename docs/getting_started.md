# Getting Started: Discovering MCP Geo Data

This guide is for users who want to explore what data is available and how to
interact with it using MCP clients or the Inspector.

## 1) Start the server

Local dev:

```bash
pip install -e .[test]
uvicorn server.main:app --reload
```

If you cloned without submodules, initialize them (needed for vector tile
styles):

```bash
git submodule update --init --recursive
```

Set env vars for live data when you have keys:
- `OS_API_KEY` (required) for Ordnance Survey tools
- `OS_API_KEY_FILE` (optional) path to a local secret file (used when `OS_API_KEY` is unset)
- `NOMIS_UID` and `NOMIS_SIGNATURE` (optional) for higher-rate NOMIS access
- `ONS_LIVE_ENABLED=true` only if you have explicitly disabled live ONS mode elsewhere
- `LOG_JSON=true` to force JSON logs (now default)
- `MCP_TOOLS_DEFAULT_TOOLSET=starter` to reduce startup `tools/list` payloads for STDIO clients

Host-side verification wrappers:
- `./scripts/pytest-local -q`
- `./scripts/ruff-local check <paths...>`
- `./scripts/mypy-local <paths...>`
- These wrappers prefer the running repo devcontainer app container, then the
  repo `.venv`, then `uv run`. Override with
  `MCP_GEO_LOCAL_TOOL_MODE=devcontainer|venv|uv|path`.

Host shell best-practice:
- Keep non-secret runtime vars in your shell profile (or sourced env file).
- Keep secrets (API keys/tokens) in a separate `chmod 600` file and source it
  from `.zshrc`/`.bashrc`.
- This is a good pattern and is recommended for this repo.

Need OS credentials or trial access?
- OS API authentication overview:
  <https://docs.os.uk/os-apis/core-concepts/authentication>
- OAuth2 token flow quick start:
  <https://docs.os.uk/os-apis/accessing-os-apis/oauth-2-api/getting-started>
- Create an OS Data Hub account and API project (API key/secret):
  <https://docs.os.uk/os-apis/core-concepts/getting-started-with-an-api-project>
- OS Data Hub login/signup entry:
  <https://osdatahub.os.uk/b2c/unified.html>

Optional: enable the PostGIS boundary cache for full admin boundaries:
- `BOUNDARY_CACHE_ENABLED=true`
- `BOUNDARY_CACHE_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo`
- `ROUTE_GRAPH_ENABLED=true`
- `ROUTE_GRAPH_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo`

Devcontainer note:
- The devcontainer starts PostGIS as the `postgis` service; use
  `postgresql://mcp_geo:mcp_geo@postgis:5432/mcp_geo` inside the container.
- The `postgis` service now builds the repo-local
  `.devcontainer/postgis.Dockerfile` image so pgRouting is installed in the
  same sidecar the app uses, and the post-start hook bootstraps both
  `scripts/boundary_cache_schema.sql` and `scripts/route_graph_schema.sql` on
  fresh named volumes.
- The upstream `postgis/postgis:16-3.4` base is currently `linux/amd64` only,
  so `MCP_GEO_POSTGIS_PLATFORM` defaults to `linux/amd64` on Apple Silicon.
- PostGIS data now uses a Docker named volume by default (not a repo bind
  mount), so corruption/isolation issues do not spill across git worktrees.
  Override the volume names if needed:
  - `MCP_GEO_POSTGIS_VOLUME` (default `mcp-geo-postgis`)
  - `MCP_GEO_RUNTIME_DATA_VOLUME` (default `mcp-geo-runtime-data`)
  Set distinct values per worktree if you want fully isolated local state.
  For CLI compose runs, copy `.devcontainer/.env.example` to
  `.devcontainer/.env` and pass `--env-file .devcontainer/.env`.
  For VS Code Dev Containers, export the same vars in the host shell before
  launching VS Code.
- On Windows checkouts, LF is enforced repo-wide via `.gitattributes` and
  `.editorconfig` so `bash` entrypoints keep working inside the Linux
  devcontainer.
- On proxied or TLS-inspected networks, add `HTTP_PROXY` / `HTTPS_PROXY` /
  `NO_PROXY` to `.devcontainer/.env` and place any required corporate root CA
  `.crt` files in `.devcontainer/certs/` before rebuilding.
- `INSTALL_NGROK` defaults to `false` so inspected networks do not fail the
  devcontainer build on the optional tunnel binary fetch. Enable it explicitly
  in `.devcontainer/.env` only when you need `ngrok` inside the container.
- The PostGIS *host* port is random by default; set `MCP_GEO_POSTGIS_HOST_PORT=5433`
  before starting the devcontainer if you want it pinned.
- Default devcontainer-forwarded ports:
  - `8000` (MCP Geo HTTP API),
  - `5173` (Playground dev server),
  - `8899` (boundary cache debug service),
  - `5432` (PostGIS).
- Optional workflow ports can be forwarded manually from the VS Code Ports panel:
  - `4173` (Playwright/Vite map trial server),
  - `6274`/`6277` (MCP Inspector UI/proxy),
  - `8888` (Jupyter Lab for notebook-based map analysis).

Devcontainer startup modes (HTTP vs STDIO):
- STDIO requires the repo dependencies to be installed in the same Python used by VS Code
  inside the devcontainer. If you see `ModuleNotFoundError: loguru`, run:
  `python3 -m pip install -e ".[dev,boundaries,test]"`
  and reload the MCP server.
- HTTP auto-start: set `MCP_GEO_DEVCONTAINER_START_HTTP=1` before starting the devcontainer.
  This runs `python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload`
  in the background and logs to `logs/devcontainer-http.log`.
- STDIO registration (Codex): enabled by default when the `codex` CLI is available.
  Disable it with `MCP_GEO_DEVCONTAINER_REGISTER_STDIO=0`.
- Run both: set `MCP_GEO_DEVCONTAINER_START_HTTP=1` and leave STDIO registration enabled.

```bash
export BOUNDARY_CACHE_ENABLED=true
export BOUNDARY_CACHE_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo
export ROUTE_GRAPH_ENABLED=true
export ROUTE_GRAPH_DSN=postgresql://mcp_geo:mcp_geo@localhost:5432/mcp_geo

echo BOUNDARY_CACHE_ENABLED
echo BOUNDARY_CACHE_DSN
echo ROUTE_GRAPH_ENABLED
echo ROUTE_GRAPH_DSN
```

Storage best-practice for host runs (outside devcontainer):
- Keep PostGIS `PGDATA` out of repo trees (use Docker named volumes).
- Keep cache/log paths out of repo trees, for example:
  - `ONS_DATASET_CACHE_DIR="$HOME/Library/Application Support/mcp-geo/cache/ons"`
  - `ONS_GEO_CACHE_DIR="$HOME/Library/Application Support/mcp-geo/cache/ons_geo"`
  - `OS_DATA_CACHE_DIR="$HOME/Library/Application Support/mcp-geo/cache/os"`
  - `UI_EVENT_LOG_PATH="$HOME/Library/Application Support/mcp-geo/logs/ui-events.jsonl"`
  - `PLAYGROUND_EVENT_LOG_PATH="$HOME/Library/Application Support/mcp-geo/logs/playground-events.jsonl"`

See `docs/boundary_cache.md` for ingest + validation steps.

## 2) Validate canonical map delivery baseline

Before testing widgets, verify the compatibility-first map path:

1. Call `os_maps.render` with a bbox.
2. Render the returned image URL in any browser/client.
3. Layer optional overlay payloads separately.
4. Use `os_apps.render_*` only after host UI support is confirmed.

Example MCP tool call:

```json
{"jsonrpc":"2.0","id":"map-1","method":"tools/call","params":{"name":"os_maps.render","arguments":{"bbox":[-0.18,51.49,-0.05,51.54],"size":640,"zoom":13}}}
```

Contract and host references:
- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

## 3) Use MCP Inspector (recommended)

MCP Inspector is the fastest way to browse tools and try calls without writing
code. Point it at the HTTP MCP endpoint:

- URL: `http://127.0.0.1:8000/mcp`

### Start the Inspector

Requirements: Node.js 18+.

Run the Inspector (starts a local UI on port 6274 and a proxy on 6277):

```bash
npx @modelcontextprotocol/inspector
```

Then open:

- `http://localhost:6274`

In the Inspector UI, connect directly to:

- `http://127.0.0.1:8000/mcp`

If you are running the server on a different host/port, update the URL.

### Inspector UI setup (recommended for this repo)

For a devcontainer workflow, use the HTTP MCP endpoint. This avoids STDIO
process spawning from the Inspector and keeps everything on the forwarded port.

1) In the Inspector UI, set `Transport Type` to `Streamable HTTP` (or `HTTP/SSE`,
depending on the Inspector version).
2) Set the `URL` field to `http://127.0.0.1:8000/mcp`.
3) Leave `Authentication` empty unless you have added auth.
4) Click `Connect`.

Note: for HTTP connections, Inspector does not pass environment variables.
Set `OS_API_KEY` on the server process before starting `uvicorn`.
`ONS_LIVE_ENABLED` defaults to `true` unless you have disabled it.

If you prefer STDIO instead, use the repo wrapper:

1) Set `Transport Type` to `STDIO`.
2) Set `Command` to `./scripts/os-mcp`.
3) In `Environment Variables`, add:
   - `OS_API_KEY` (required for OS tools), or
   - `OS_API_KEY_FILE` (path to a file containing the OS key)
   - `ONS_LIVE_ENABLED=true` only if you have explicitly disabled live ONS tools elsewhere
4) Click `Connect`.

Note: STDIO mode runs the server process via the Inspector proxy, so it is best
used on the host (not inside the devcontainer) unless you also forward port 6274
for the Inspector UI.

In Inspector you can:
- Run `tools/list` and `tools/describe` to see tool schemas
- Run `resources/list` and `resources/describe`
- Call tools and inspect structured outputs
- Validate MCP-Apps UI resources (if supported)

## 4) Use the Playground (web UI)

The playground is a lightweight MCP client built with Svelte + Vite. It uses
the MCP TypeScript SDK to connect over HTTP and records tool calls and prompt
events to the server's `/playground/*` endpoints.

If `MCP_HTTP_AUTH_MODE` is enabled, only `GET /health` stays public. The
playground API routes, raw `/tools/*`, raw `/resources/*`, and `/metrics` then
require the same bearer auth as `/mcp`.

From the repo root:

```bash
./scripts/run-playground-demo.sh
```

This checks for running services on ports 8000/5173, starts the HTTP server and
playground UI if needed, and writes logs under `logs/`.

Manual alternative:

```bash
cd playground
npm install
npm run dev
```

Then open:

- `http://localhost:5173`
- Playwright UI tests run Vite on `http://localhost:4173` to avoid local `5173` collisions.

Defaults:
- MCP server URL: `http://localhost:8000/mcp`
- Playground API: `http://localhost:8000/playground`

Note: `playground/app.py` is a legacy stub and does not serve the Svelte UI.

If you see CORS/preflight errors, ensure `CORS_ALLOWED_ORIGINS` includes the
playground URL (default includes `http://localhost:5173`).
For Playwright runs, include `http://localhost:4173` as well.

The playground can:
- Connect and list tools/resources/templates
- Call tools with raw JSON arguments
- Log prompts to help correlate with tool usage
- Read evaluation results from the server (`/playground/evaluation/latest`)

## Latest report helper

Use the helper script to find the latest boundary pipeline run report and emit
the current boundary cache status:

```bash
python scripts/latest_reports.py
```

Pass `--boundary` or `--cache` to limit output. Cache status is written to
`data/cache_reports/<timestamp>/cache_status.json`.

For playground tests, install Playwright system deps once:

```bash
cd playground
npx playwright install --with-deps
```

### VS Code Playwright extension in a devcontainer

If you install the Playwright VS Code extension, use these container-specific
checks:

- Install the extension in the **Dev Container** context (not only on host
  macOS), so test discovery/debugging runs against container paths and Node.
- Re-run `npx playwright install --with-deps` inside the container if browser
  launches fail. The devcontainer post-create step is tolerant (`|| true`) and
  can hide install errors.
- Keep `OS_API_KEY` available in container env for OS-backed map demos; without
  it, basemap and OS-backed layer steps will degrade.
- Trials default to `http://127.0.0.1:8000`; if that port is occupied, set
  `MCP_GEO_TRIAL_BASE_URL` to the active server base URL.
- Prefer headless execution for reliable demo rehearsals. Use traces,
  screenshots, and videos for evidence when headed debug sessions are unstable.
- If Chromium crashes under load, increase container shared memory (`/dev/shm`)
  in your compose runtime.

Quick smoke command for presentation readiness:

```bash
npm --prefix playground run test:trials -- --project=chromium-desktop playground/trials/tests/map_story_gallery.spec.js
```

For automated map delivery validation (containerized trial matrix + evidence capture):

```bash
./scripts/run_map_delivery_trials.sh
python3 scripts/map_trials/summarize_playwright_trials.py
python3 scripts/map_trials/summarize_story_gallery.py
```

Presentation-ready story gallery output is written to
`research/map_delivery_research_2026-02/reports/story_gallery_report.md`,
using screenshots under `research/map_delivery_research_2026-02/evidence/screenshots/`.
If local port `8000` is occupied, set `MCP_GEO_TRIAL_BASE_URL` (for example
`http://127.0.0.1:8010`) when running targeted story-gallery trials.

## 5) What data is available

### Ordnance Survey (OS)

- Addresses and UPRNs: `os_places.*`
- Gazetteer place names: `os_names.*`
- Linked identifiers (UPRN/USRN/TOID): `os_linked_ids.get`
- NGD features (bbox query): `os_features.query`
- Maps metadata and vector tiles: `os_maps.render`, `os_vector_tiles.descriptor`
- Offline map packs and handoff contracts: `os_offline.descriptor`, `os_offline.get`

#### Vector tile styles (OS VTS)

Use EPSG:3857 styles for MapLibre/Mapbox clients. For live OS styles, call
`/maps/vector/vts/resources/styles?style=<STYLE_NAME>&srs=3857` (or via
`os_vector_tiles.descriptor`). For local styles from the submodule, use
`/maps/vector/styles?style=<STYLE_NAME>`.

Standard styles (EPSG:3857):
- `OS_VTS_3857_Light.json`
- `OS_VTS_3857_Dark.json`
- `OS_VTS_3857_Road.json`
- `OS_VTS_3857_Outdoor.json`
- `OS_VTS_3857_Greyscale.json`
- `OS_VTS_3857_No_Labels.json`
- `OS_VTS_3857_Black_and_White.json`
- `OS_VTS_3857_ESRI.json`
- `OS_VTS_3857_3D.json`

OpenData overzoom variants (EPSG:3857):
- `OS_VTS_3857_Open_Light.json`
- `OS_VTS_3857_Open_Dark.json`
- `OS_VTS_3857_Open_Road.json`
- `OS_VTS_3857_Open_Outdoor.json`
- `OS_VTS_3857_Open_Greyscale.json`
- `OS_VTS_3857_Open_Black_and_White.json`

Known limitation (validated in Claude/Desktop map tests on 2026-02-13):
- OS VTS does not expose glyph assets for arbitrary custom symbol layers.
- For custom labels/markers on top of OS VTS basemaps, prefer HTML markers or
  DOM overlays instead of glyph-backed symbol text layers.

Reference: OS-Vector-Tile-API-Stylesheets (GitHub). This repo is also available as
`submodules/os-vector-tile-api-stylesheets`.

### ONS statistics

- Ranked dataset selection: `ons_select.search`
- Dataset search: `ons_search.query`
- Dimensions and codes: `ons_data.dimensions`, `ons_codes.*`
- Observations and filters: `ons_data.query`, `ons_data.get_observation`,
  `ons_data.create_filter`, `ons_data.get_filter_output`

Note: ONS tools require live mode (`ONS_LIVE_ENABLED=true`) and `dataset`,
`edition`, and `version` parameters for observation/dimension calls.
`ons_codes.*` supports optional on-disk caching via
`ONS_DATASET_CACHE_ENABLED=true`.

### Administrative geography

- Containment lookup: `admin_lookup.containing_areas`
- Hierarchy and geometry: `admin_lookup.reverse_hierarchy`,
  `admin_lookup.area_geometry`, `admin_lookup.find_by_name`

### UI widgets (MCP-Apps)

- Geography selector: `os_apps.render_geography_selector`
- Statistics dashboard: `os_apps.render_statistics_dashboard`
- Feature inspector: `os_apps.render_feature_inspector`
- Route planner: `os_apps.render_route_planner`
- UI probe: `os_apps.render_ui_probe`

Set `MCP_APPS_CONTENT_MODE` to control how UI tools emit content blocks:
- `resource_link`: emit a `resource_link` block pointing at `ui://` resources.
- `embedded`: embed UI HTML as a `resource` content block.
- `text`: emit text only (no UI content blocks).

Note: `os_names.nearest` accepts WGS84 lat/lon (`EPSG:4326`) and converts to
British National Grid automatically. Use `coordSystem: "EPSG:27700"` if you
already have BNG eastings/northings.

## 6) Quick inspection examples

List tools:

```json
{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}
```

Describe a tool:

```json
{"jsonrpc":"2.0","id":"2","method":"tools/describe","params":{"name":"os_places.by_postcode"}}
```

Call a tool:

```json
{"jsonrpc":"2.0","id":"3","method":"tools/call","params":{"name":"os_places.by_postcode","arguments":{"postcode":"SW1A 1AA"}}}
```

List resources:

```json
{"jsonrpc":"2.0","id":"4","method":"resources/list","params":{}}
```

Read the boundary manifest resource:

```json
{"jsonrpc":"2.0","id":"5","method":"resources/read","params":{"uri":"resource://mcp-geo/boundary-manifest"}}
```

## 7) Where to go next

- Detailed walkthrough: `docs/tutorial.md`
- Tool catalog: `docs/tool_catalog.md`
- Evaluation suite and questions: `docs/evaluation.md`
- MCP-Apps alignment notes: `docs/mcp_apps_alignment.md`
- Browser/widget support matrix: `docs/map_delivery_support_matrix.md`
- Notebook scenario packs: `docs/map_scenario_packs.md`
- MCP/AI host embedding bundle: `docs/map_embedding_best_practices.md`

## Appendix: STDIO Docker (when to use it)

Use the STDIO Docker image when connecting from desktop MCP clients that only
support STDIO (e.g., Claude Desktop / Claude Code). Use HTTP for Inspector and
web clients.

Rebuild the STDIO image (include the training dot):

```bash
docker build -t mcp-geo-server .
```

Run STDIO:

```bash
docker run --rm -i \
  -e OS_API_KEY=your-api-key-here \
  mcp-geo-server
```

## Appendix: Claude Desktop local wrapper (PostGIS + cache)

For Claude Desktop, use the local wrapper script so PostGIS starts automatically
and the STDIO server runs with the cache enabled:

```bash
./scripts/claude-mcp-local
```

Claude Desktop config example:

```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "/absolute/path/to/mcp-geo/scripts/claude-mcp-local",
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "OS_API_KEY_FILE": "${env:OS_API_KEY_FILE}",
        "MCP_STDIO_UI_SUPPORTED": "1",
        "MCP_STDIO_FRAMING": "line",
        "MCP_STDIO_ELICITATION_ENABLED": "1"
      }
    }
  }
}
```

The wrapper starts PostGIS in Docker, builds the image if needed, and uses
`postgresql://mcp_geo:mcp_geo@postgis:5432/mcp_geo` for the cache.
Set either `OS_API_KEY` or `OS_API_KEY_FILE` in the host environment (if both
are set, `OS_API_KEY` wins).
By default it stores PostGIS data in a Docker named volume
(`mcp-geo-postgis-claude`) rather than a repo bind mount.

Control rebuilds with `MCP_GEO_DOCKER_BUILD`:
- `missing` (default): build only when the image is absent.
- `always`: run `docker build` each time (still uses cache).
- `never`: skip building even if the image is missing.

If Claude Desktop can't find Docker on macOS (GUI apps sometimes have a minimal
PATH), set the Docker binary explicitly:

```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "/absolute/path/to/mcp-geo/scripts/claude-mcp-local",
      "env": {
        "MCP_GEO_DOCKER_BIN": "/opt/homebrew/bin/docker"
      }
    }
  }
}
```

If port `5432` is already in use, set `MCP_GEO_POSTGIS_PUBLISH_PORT` to another
port or `0` to disable host publishing.

Storage controls for the wrapper:
- `MCP_GEO_POSTGIS_STORAGE_MODE=volume` (default) uses Docker volume
  `MCP_GEO_POSTGIS_VOLUME` (default `mcp-geo-postgis-claude`).
- `MCP_GEO_POSTGIS_STORAGE_MODE=bind` uses
  `MCP_GEO_POSTGIS_DATA_DIR` (legacy bind-mount mode).
- `MCP_GEO_POSTGIS_IMAGE` defaults to `mcp-geo-postgis-pgrouting:16-3.4`.
- `MCP_GEO_POSTGIS_PLATFORM` defaults to `linux/amd64`.
- `MCP_GEO_POSTGIS_REUSE_DEVCONTAINER` defaults to `auto` for Docker-backed
  wrappers, so host-side clients reuse the running repo devcontainer PostGIS
  container by default.
- `scripts/claude-mcp-local` now prefers the running repo devcontainer PostGIS
  container (`mcp-geo_devcontainer-postgis-1`) when available; otherwise it
  falls back to its own Docker sidecar.
- The wrapper now sets `PGDATA=/var/lib/postgresql/data/pgdata` to match the
  devcontainer layout and bootstraps the boundary-cache/route-graph schema
  files after the PostGIS sidecar becomes ready.

Benchmarking note:
- Before comparing Codex, Claude, or other Docker-backed clients, run
  `./scripts/check_shared_benchmark_cache.sh` and only continue if it reports
  `PASS`. This ensures every client is pointed at the same PostGIS cache.

If you need deterministic non-interactive routing, set
`MCP_STDIO_ELICITATION_ENABLED=0` to disable STDIO form elicitation prompts
(`os_mcp.stats_routing`, `ons_select.search`). For Streamable HTTP (`/mcp`), set
`MCP_HTTP_ELICITATION_ENABLED=0`.

## Appendix: Codex local wrapper (PostGIS + cache)

For Codex CLI and Codex IDE, use the Codex-specific launcher so Codex does not
inherit Claude-only startup defaults:

```bash
./scripts/codex-mcp-local
```

The devcontainer setup script now registers Codex against
`scripts/codex-mcp-local`. Shared Docker/bootstrap logic lives in
`scripts/mcp-docker-local`, while `scripts/claude-mcp-local` remains
Claude-only. The Codex wrapper prefers the Docker-backed launcher on host
surfaces and falls back to `scripts/os-mcp` when Docker is unavailable or the
session is already running inside a devcontainer/container.

To verify scoped startup discovery with the Codex launcher:

```bash
./scripts/check_codex_startup_scope.sh
```

For host benchmarking and scored Codex vs Claude runs, use the runbook in
`docs/benchmarking/codex_vs_claude_host_benchmark.md`.

## Appendix: ChatGPT local dev (HTTPS tunnel)

ChatGPT requires the MCP server to be reachable over HTTPS. For local
development, use a tunnel and set `OPENAI_WIDGET_DOMAIN` to the public domain.

Example with `cloudflared`:

```bash
cloudflared tunnel --url http://localhost:8000
export OPENAI_WIDGET_DOMAIN="<your-tunnel-domain>"
uvicorn server.main:app --reload
```

Alternatively, `ngrok` works similarly:

```bash
ngrok http 8000
export OPENAI_WIDGET_DOMAIN="<your-ngrok-domain>"
```
