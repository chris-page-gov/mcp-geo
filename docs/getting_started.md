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
- `ONS_LIVE_ENABLED=true` for live ONS datasets

## 2) Use MCP Inspector (recommended)

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
Set `ONS_LIVE_ENABLED=true` and `OS_API_KEY` on the server process
before starting `uvicorn`.

If you prefer STDIO instead, use the repo wrapper:

1) Set `Transport Type` to `STDIO`.
2) Set `Command` to `./scripts/os-mcp`.
3) In `Environment Variables`, add:
   - `OS_API_KEY` (required for OS tools)
   - `ONS_LIVE_ENABLED=true` (optional, enables live ONS tools)
4) Click `Connect`.

Note: STDIO mode runs the server process via the Inspector proxy, so it is best
used on the host (not inside the devcontainer) unless you also forward port 6274
for the Inspector UI.

In Inspector you can:
- Run `tools/list` and `tools/describe` to see tool schemas
- Run `resources/list` and `resources/describe`
- Call tools and inspect structured outputs
- Validate MCP-Apps UI resources (if supported)

## 3) Use the Playground (web UI)

The playground is a lightweight MCP client built with Svelte + Vite. It uses
the MCP TypeScript SDK to connect over HTTP and records tool calls and prompt
events to the server's `/playground/*` endpoints.

From the repo root:

```bash
cd playground
npm install
npm run dev
```

Then open:

- `http://localhost:5173`

Defaults:
- MCP server URL: `http://localhost:8000/mcp`
- Playground API: `http://localhost:8000/playground`

Note: `playground/app.py` is a legacy stub and does not serve the Svelte UI.

If you see CORS/preflight errors, ensure `CORS_ALLOWED_ORIGINS` includes the
playground URL (default includes `http://localhost:5173`).

The playground can:
- Connect and list tools/resources/templates
- Call tools with raw JSON arguments
- Log prompts to help correlate with tool usage
- Read evaluation results from the server (`/playground/evaluation/latest`)

For playground tests, install Playwright system deps once:

```bash
cd playground
npx playwright install --with-deps
```

## 4) What data is available

### Ordnance Survey (OS)

- Addresses and UPRNs: `os_places.*`
- Gazetteer place names: `os_names.*`
- Linked identifiers (UPRN/USRN/TOID): `os_linked_ids.get`
- NGD features (bbox query): `os_features.query`
- Maps metadata and vector tiles: `os_maps.render`, `os_vector_tiles.descriptor`

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

Reference: OS-Vector-Tile-API-Stylesheets (GitHub). This repo is also available as
`submodules/os-vector-tile-api-stylesheets`.

### ONS statistics

- Dataset search: `ons_search.query`
- Dimensions and codes: `ons_data.dimensions`, `ons_codes.*`
- Observations and filters: `ons_data.query`, `ons_data.get_observation`,
  `ons_data.create_filter`, `ons_data.get_filter_output`

Note: ONS tools are live-only and require `dataset`, `edition`, and `version`
parameters in tool payloads.

### Administrative geography

- Containment lookup: `admin_lookup.containing_areas`
- Hierarchy and geometry: `admin_lookup.reverse_hierarchy`,
  `admin_lookup.area_geometry`, `admin_lookup.find_by_name`

### UI widgets (MCP-Apps)

- Geography selector: `os_apps.render_geography_selector`
- Statistics dashboard: `os_apps.render_statistics_dashboard`
- Feature inspector: `os_apps.render_feature_inspector`
- Route planner: `os_apps.render_route_planner`

## 5) Quick inspection examples

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

## 6) Where to go next

- Detailed walkthrough: `docs/tutorial.md`
- Tool catalog: `docs/tool_catalog.md`
- Evaluation suite and questions: `docs/evaluation.md`
- MCP-Apps alignment notes: `docs/mcp_apps_alignment.md`

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
  -e ONS_LIVE_ENABLED=true \
  mcp-geo-server
```
