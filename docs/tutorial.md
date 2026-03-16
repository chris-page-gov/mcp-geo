# MCP Geo tutorial

This tutorial is an evaluation-style walkthrough for the **mcp-geo** MCP server.
It is inspired by the legacy evaluation suite from the earlier OS/ONS MCP prototype, but uses **mcp-geo** tool names and endpoints.

## Run the server

```bash
pip install -e .[test]
uvicorn server.main:app --reload
```

Set a base URL for the examples:

```bash
export BASE_URL=${BASE_URL:-http://127.0.0.1:8000}
```

Check health:

```bash
curl -sS -o /dev/null -w 'health=%{http_code}\n' "$BASE_URL/health"
```

### Environment variables

- `OS_API_KEY`: required for Ordnance Survey-backed tools (Places, Names, NGD Features, Linked IDs, etc).
  Missing or invalid keys return `NO_API_KEY`, `OS_API_KEY_INVALID`, or `OS_API_KEY_EXPIRED`.
- `ONS_LIVE_ENABLED=true`: enables live ONS API access for `ons_data.*` when you supply `dataset`, `edition`, `version`.
  If unset/false, mcp-geo uses bundled sample data.
- `UI_EVENT_LOG_PATH`: path to the MCP-Apps UI interaction log (default: `logs/ui-events.jsonl`).

### Cache population quick runbook

All cache artifacts are written under `data/` (gitignored).

1. Refresh hybrid pack caches:

```bash
./.venv/bin/python scripts/pack_cache_refresh.py --kind all
```

2. Populate `ons_geo` cache (exact + best-fit products):

```bash
./.venv/bin/python scripts/ons_geo_cache_refresh.py \
  --sources resources/ons_geo_sources.json \
  --cache-dir data/cache/ons_geo \
  --index-path resources/ons_geo_cache_index.json \
  --db-name ons_geo_cache.sqlite \
  --product-file ONSPD=/path/to/onspd.csv \
  --product-file NSPL=/path/to/nspl.csv \
  --product-file ONSUD=/path/to/onsud.csv \
  --product-file NSUL=/path/to/nsul.csv
```

3. Populate PostGIS boundary cache (requires PostGIS + geospatial source):

```bash
./.venv/bin/python scripts/boundary_cache_ingest.py \
  --dsn "$BOUNDARY_CACHE_DSN" \
  --dataset-id <dataset_id> \
  --source ONS \
  --title "<dataset title>" \
  --input /path/to/boundaries.gpkg \
  --layer <layer_name> \
  --level <LEVEL> \
  --id-field <CODE_FIELD> \
  --name-field <NAME_FIELD> \
  --resolution BGC \
  --apply-schema
```

4. Verify status/degradation flags:

```bash
curl -sS "$BASE_URL/tools/call" -H 'content-type: application/json' \
  -d '{"tool":"ons_geo.cache_status"}'

curl -sS "$BASE_URL/tools/call" -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.get_cache_status"}'
```

Both status payloads expose `performance.degraded` with `reason`/`impact`.

## Client setup (MCP-capable clients)

Most MCP clients connect over STDIO. This repo ships a JSON-RPC 2.0 STDIO adapter
via `mcp-geo-stdio` (installed) or `scripts/os-mcp` (repo-local wrapper).

### STDIO config (works for most clients)

```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "./scripts/os-mcp",
      "args": [],
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "ONS_LIVE_ENABLED": "true",
        "MCP_TOOLS_DEFAULT_TOOLSET": "starter"
      }
    }
  }
}
```

Notes:
- If you installed the package, swap `command` to `mcp-geo-stdio`.
- If your client supports `cwd`, set it to the repo root when using `./scripts/os-mcp`.
- Remove `ONS_LIVE_ENABLED` or set it to `"false"` if you want sample ONS data only.
- Keep `MCP_TOOLS_DEFAULT_TOOLSET=starter` for lean startup discovery.
- `mcp.json` includes a ready-to-copy entry using the same settings.
- Claude Desktop enforces tool name patterns; the stdio adapter normalizes dotted names to underscores in list/search results. Use the names shown in your client (the server still accepts original names).

### HTTP /mcp (Streamable HTTP)

The server exposes a native `/mcp` JSON-RPC endpoint for remote MCP clients (ChatGPT,
Inspector, web apps, etc.).

Initialize:
```bash
curl -sS "$BASE_URL/mcp" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":"1","method":"initialize","params":{}}'
```

Then call tools (reuse the `mcp-session-id` response header if you want a stable session):
```bash
curl -sS "$BASE_URL/mcp" \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"ons_data_dimensions","arguments":{}}}'
```

### Docker STDIO config (Claude Desktop / Claude Code)

Build the image from the repo root:
```bash
docker build -t mcp-geo-server .
```

Then use this client config:
```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OS_API_KEY=your-api-key-here",
        "-e",
        "ONS_LIVE_ENABLED=true",
        "mcp-geo-server"
      ]
    }
  }
}
```

### Anthropic (Claude Desktop / Claude Code)

- Claude Desktop config paths:
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Windows: `%APPDATA%\\Claude\\claude_desktop_config.json`
  - Linux: `~/.config/Claude/claude_desktop_config.json`
- Claude Code config path: `~/.config/claude-code/config.json`
- Paste the `mcpServers` entry above and restart the client.

### OpenAI

If you're using an MCP-capable OpenAI client (desktop app, Agents SDK, or other
integrations), register the same STDIO server entry. Use `mcp-geo-stdio` for
installed deployments, or `./scripts/os-mcp` for repo-local dev. Refer to the
client's docs for the exact config location.

### Microsoft

For MCP-capable Microsoft clients (Copilot Studio / Azure AI Studio / VS Code
Copilot Chat), register the STDIO server entry above, or point the client to a
remote server you run locally. Consult Microsoft docs for the specific MCP
configuration UI or file path.

### Other MCP clients

Common MCP-capable tools (Cursor, Windsurf, Continue, Cline, Zed, Neovim MCP
plugins) typically accept the same `mcpServers` JSON. Paste the STDIO entry
above and adjust `command`/`cwd` as needed.

MCP-Apps widgets require a client that advertises the MCP Apps extension
(`io.modelcontextprotocol/ui`) and supports `text/html;profile=mcp-app`. If your
client does not render MCP Apps, the server will still return data-only
responses.

## MCP-Apps + tool search tutorial (best support: Anthropic Claude Desktop)

Claude Desktop currently provides the strongest MCP-Apps UI rendering and tool
search experience, so this walkthrough uses it as the reference client.

### 1) Connect the server

Use the STDIO config from the client setup section, then restart Claude Desktop.

### 2) Verify tool search

Ask:
```
Find tools related to postcode search.
```

Expected: the client uses `/tools/search` (or `tools/search` over stdio) and
lists `os_places.by_postcode`, `os_places.search`, and related tools with scores.

### 3) Open the MCP-Apps geography selector

Ask:
```
Open a map so I can select wards in Westminster.
```

Expected: the client calls `os_apps.render_geography_selector` and opens the
MCP-Apps UI at `ui://mcp-geo/geography-selector`.

### 4) Use the selection in a follow-up tool call

After selecting a ward in the UI, ask:
```
Fetch the boundary bbox for the selected ward.
```

Expected: the client uses the selection context and calls
`admin_lookup.area_geometry`.

Notes for other clients:
- MCP-capable clients can still use tool search; if they do not render MCP Apps,
  they should ignore UI metadata and fall back to data-only flows.

## Client tracing (tools + UI)

For end-to-end tracing (tool search, tool calls, and MCP-Apps UI events), see
`docs/client_trace_strategy.md`.

## How to call tools

`POST /tools/call` expects JSON containing at least the tool name plus tool-specific fields.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Birmingham"}'
```

Error responses use a consistent envelope:

```json
{ "isError": true, "code": "SOME_CODE", "message": "Human readable message", "correlationId": "...optional..." }
```

## Start with os_mcp.route_query

For free-form questions, call `os_mcp.route_query` first. It returns intent,
the recommended tool, and workflow steps.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_mcp.route_query","query":"Find Westminster ward boundaries"}'
```

## Discover tools and resources

List tools (paged via `nextPageToken`):

```bash
curl -sS "$BASE_URL/tools/list"
```

Describe tools (schemas + descriptions):

```bash
curl -sS "$BASE_URL/tools/describe"
```

List resources (paged via `nextPageToken`):

```bash
curl -sS "$BASE_URL/resources/list?limit=50&page=1"
```

Fetch a resource:

```bash
curl -sS "$BASE_URL/resources/read?name=ons_observations"
```

## Map baseline first (works without widgets)

Use this sequence before attempting MCP-Apps rendering:

1. Call `os_maps.render`.
2. Display the static image URL.
3. Add overlay payloads (`overlay_bundle`) if needed.
4. Only then call `os_apps.render_*` when UI support is confirmed.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_maps.render","bbox":[-0.18,51.49,-0.05,51.54],"size":640,"zoom":13}'
```

Fallback contract references:
- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

## Progressive fallback walkthrough (full UI -> no UI)

1. Try full UI:
   `os_apps.render_geography_selector`.
2. If host UI is partial/unsupported, keep `os_maps.render` + overlays.
3. For constrained/offline hosts, use `os_offline.get` to deliver
   `map_card`/`overlay_bundle`/`export_handoff`.
4. Select a constrained profile from:
   `resource://mcp-geo/map-embedding-style-profiles`.

Mixed-fleet reference: `docs/map_embedding_best_practices.md`.

## Basic evaluation-style questions

The upstream evaluation suite names tools like `search_geographic_areas` and `list_ons_datasets`.
In **mcp-geo**, closest equivalents are:

- admin areas: `admin_lookup.*` (bundled sample boundaries)
- datasets/resources: `/resources/*` and `ons_data.*`
- “open a map”: `os_maps.render` (static map proxy URL) + `admin_lookup.containing_areas` (point containment)

### Find Westminster

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Westminster"}'
```

### Where is London?

A practical answer is a bounding box.

1) Find an id:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"London"}'
```

2) Fetch bbox geometry:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.area_geometry","id":"<id-from-search>"}'
```

### Administrative hierarchy for an area

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.reverse_hierarchy","id":"<area-id>"}'
```

### What datasets are available?

mcp-geo exposes bundled datasets via the Resources API:

```bash
curl -sS "$BASE_URL/resources/list?limit=50&page=1"
```

## Tool coverage map (all current families)

As of 2026-02-22, this server exposes 81 tools. Use these grouped families to
cover the full surface area.

### Core routing and discovery (`os_mcp.*`)

- `os_mcp.descriptor`
- `os_mcp.route_query`
- `os_mcp.select_toolsets`
- `os_mcp.stats_routing`

Route first, then narrow discovery:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_mcp.route_query","query":"Find geographies for postcode SW1A 1AA"}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_mcp.select_toolsets","query":"Find geographies for postcode SW1A 1AA"}'
```

### ONS geography cache (`ons_geo.*`)

- `ons_geo.by_postcode`
- `ons_geo.by_uprn`
- `ons_geo.cache_status`

Exact mode uses ONSPD/ONSUD; best-fit mode uses NSPL/NSUL.
Use `ons_geo.cache_status` to check `performance.degraded` before running
postcode/UPRN lookups.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_geo.by_postcode","postcode":"SW1A 1AA","derivationMode":"exact"}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_geo.by_postcode","postcode":"SW1A 1AA","derivationMode":"best_fit"}'
```

### ONS datasets and code lists

- `ons_select.search`
- `ons_search.query`
- `ons_data.create_filter`
- `ons_data.dimensions`
- `ons_data.editions`
- `ons_data.get_filter_output`
- `ons_data.get_observation`
- `ons_data.query`
- `ons_data.versions`
- `ons_codes.list`
- `ons_codes.options`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_select.search","question":"population growth in regions"}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.dimensions","dataset":"cpih01","edition":"time-series","version":"1"}'
```

### NOMIS tools (`nomis.*`)

- `nomis.datasets`
- `nomis.query`
- `nomis.concepts`
- `nomis.codelists`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"nomis.datasets","q":"employment","limit":5}'
```

### Administrative geography (`admin_lookup.*`)

- `admin_lookup.find_by_name`
- `admin_lookup.area_geometry`
- `admin_lookup.reverse_hierarchy`
- `admin_lookup.containing_areas`
- `admin_lookup.search_cache`
- `admin_lookup.get_cache_status`

Check `admin_lookup.get_cache_status` and inspect `performance.degraded` to
confirm whether PostGIS cache-backed responses are available.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Westminster"}'
```

## Ordnance Survey tools (require `OS_API_KEY`)

If `OS_API_KEY` is missing/invalid, OS-backed tools return `NO_API_KEY`,
`OS_API_KEY_INVALID`, or `OS_API_KEY_EXPIRED`.

### Places, POI, Names, and Linked IDs

- `os_places.by_postcode`, `os_places.by_uprn`, `os_places.search`,
  `os_places.nearest`, `os_places.radius`, `os_places.polygon`,
  `os_places.within`
- `os_poi.search`, `os_poi.nearest`, `os_poi.within`
- `os_names.find`, `os_names.nearest`
- `os_linked_ids.get`, `os_linked_ids.identifiers`,
  `os_linked_ids.feature_types`, `os_linked_ids.product_version_info`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_places.by_postcode","postcode":"SW1A1AA"}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_linked_ids.get","id":"100023336959"}'
```

### NGD features, peat evidence, and protected landscapes

- `os_features.collections`
- `os_features.query`
- `os_features.wfs_capabilities`
- `os_features.wfs_archive_capabilities`
- `os_peat.layers`
- `os_peat.evidence_paths`
- `os_landscape.find`
- `os_landscape.get`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_landscape.find","text":"Forest of Bowland"}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_peat.evidence_paths","landscapeId":"E12000007","limit":10}'
```

### Map delivery, inventories, and tiles

- `os_maps.render`, `os_maps.raster_tile`, `os_maps.wmts_capabilities`
- `os_vector_tiles.descriptor`
- `os_map.inventory`, `os_map.export`
- `os_offline.descriptor`, `os_offline.get`
- `os_qgis.vector_tile_profile`, `os_qgis.export_geopackage_descriptor`
- `os_tiles_ota.collections`, `os_tiles_ota.conformance`,
  `os_tiles_ota.tilematrixsets`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_maps.render","bbox":[-0.18,51.49,-0.05,51.54],"size":640,"zoom":13}'

curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_offline.descriptor","packId":"uk-demo"}'
```

### OS Downloads and OS Net

- `os_downloads.list_products`
- `os_downloads.get_product`
- `os_downloads.list_product_downloads`
- `os_downloads.list_data_packages`
- `os_downloads.prepare_export`
- `os_downloads.get_export`
- `os_net.station_get`
- `os_net.station_log`
- `os_net.rinex_years`

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_downloads.list_products","limit":5}'
```

### MCP-Apps UI tools (`os_apps.*`)

- `os_apps.render_geography_selector`
- `os_apps.render_boundary_explorer`
- `os_apps.render_statistics_dashboard`
- `os_apps.render_feature_inspector`
- `os_apps.render_route_planner`
- `os_apps.render_ui_probe`
- `os_apps.log_event`

Notes:
- `render_geography_selector`, `render_boundary_explorer`, and
  `render_statistics_dashboard` are the main operational widget paths.
- `render_feature_inspector` and `render_route_planner` are currently static UI
  shells; treat them as placeholders pending full runtime integration.

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_apps.render_ui_probe"}'
```

For full schemas, use:

```bash
curl -sS "$BASE_URL/tools/describe"
```

## Initialization footprint and Claude context impact

Claude clients do not currently rely on progressive/deferred MCP tool loading,
so startup tool payload size directly consumes model context.

Repeatable measurement (stdio adapter in-process):

```bash
./.venv/bin/python - <<'PY'
import json
import os
from contextlib import contextmanager
from server import stdio_adapter
from server.mcp import tools as _  # noqa: F401

def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)

@contextmanager
def env_overrides(**kwargs):
    old = {}
    for k, v in kwargs.items():
        old[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

with env_overrides(MCP_TOOLS_DEFAULT_TOOLSET=None):
    all_resp = stdio_adapter.handle_list_tools({})
with env_overrides(MCP_TOOLS_DEFAULT_TOOLSET='starter'):
    starter_resp = stdio_adapter.handle_list_tools({})

all_json = json.dumps(all_resp, ensure_ascii=True, separators=(',', ':'))
starter_json = json.dumps(starter_resp, ensure_ascii=True, separators=(',', ':'))
print('all_tools', len(all_resp['tools']), len(all_json.encode('utf-8')), approx_tokens(all_json))
print('starter', len(starter_resp['tools']), len(starter_json.encode('utf-8')), approx_tokens(starter_json))
PY
```

Latest measurement on 2026-03-15:

- Full `tools/list` (85 tools): `95,527` bytes (~`23,881` tokens approximate).
- Starter `tools/list` (20 tools): `28,722` bytes (~`7,180` tokens approximate).
- Startup reduction with `MCP_TOOLS_DEFAULT_TOOLSET=starter`: about `70%` fewer
  bytes/tokens.

Claude-safe mitigation workflow (no deferred loading dependency):

1. Keep startup lean with `MCP_TOOLS_DEFAULT_TOOLSET=starter`.
2. Call `os_mcp.select_toolsets` (included in starter) using the user query.
3. Re-run `tools/list` with returned `includeToolsets`.
4. Call target tool(s), using sanitized names shown by Claude (for example
   `ons_geo_by_postcode`).

The starter toolset now also force-loads `admin_lookup.area_geometry`,
`os_linked_ids.get`, and `os_resources.get` so common Harold Wood-style
recovery paths do not depend on deferred-tool activation.

This keeps startup context small while preserving deterministic expansion paths.

## Resources and conditional caching (ETag)

1) Fetch a resource and note the `ETag` response header:

```bash
curl -i "$BASE_URL/resources/read?name=admin_boundaries" | sed -n '1,20p'
```

2) Revalidate with `If-None-Match`:

```bash
curl -i "$BASE_URL/resources/read?name=admin_boundaries" \
  -H 'If-None-Match: W/"<etag-from-previous-response>"'
```

If unchanged, the server returns `304 Not Modified` with an empty body.

## Rate limiting, metrics, correlation IDs

- Rate limiting is enforced by middleware by default; set `RATE_LIMIT_BYPASS=true` only for explicit tests/dev bypass.
- Metrics are available at `GET /metrics` when `METRICS_ENABLED=true`.
- Correlation IDs are created/propagated via the `x-correlation-id` header.

## Evaluation harness

The evaluation harness runs a question suite and scores results with the rubric:

```bash
python -m tests.evaluation.harness --difficulty=basic
```

Include OS-backed questions (requires `OS_API_KEY`):

```bash
python -m tests.evaluation.harness --include-os-api
```

## STDIO (JSON-RPC 2.0)

There is a JSON-RPC 2.0 STDIO adapter.

- Console script: `mcp-geo-stdio`
- Legacy wrapper: `scripts/os-mcp` (use `mcp-geo-stdio` when installed)

See server implementation in `server/stdio_adapter.py`.
