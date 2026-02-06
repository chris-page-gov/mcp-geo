# MCP Geo Server

Production-focused Model Context Protocol (MCP) server for geospatial (Ordnance Survey) tooling built with FastAPI & Python 3.11+. Provides a uniform tool abstraction, typed schemas, structured error model, correlation IDs, and high test coverage (≥90%).

## MCP Specification

See [Latest Specification which this MUST conform to](https://modelcontextprotocol.io/specification/2025-11-25).
This is a preview spec; tracking and review cadence live in `docs/spec_tracking.md`.
OpenAI's MCP documentation is at https://platform.openai.com/docs/mcp (preview; tracked in `docs/spec_tracking.md`).

## Key Features
- MCP endpoints: `/mcp` (streamable HTTP JSON-RPC), `/tools/list`, `/tools/call`, `/tools/describe`, `/tools/search`, `/resources/list`, `/resources/describe`, `/resources/read`
- Uniform error envelope and pagination (`nextPageToken`)
- Dynamic tool registration with schema introspection
- Tool annotations + defer-loading metadata for tool search integrations
- Agent skills resource (`skills://mcp-geo/getting-started`)
- MCP-Apps UI resources (`ui://mcp-geo/...`) with helper `os_apps.*` tools
- Svelte playground UI for MCP tool calls, prompt capture, and auditing
- Routing tool `os_mcp.route_query` for intent classification and workflow guidance
- Structured logging & correlation IDs
- OS API client with retries and explicit upstream error codes
- High coverage test suite exercising success + failure paths
- Evaluation harness with question suite and scoring rubric

## Quickstart
```bash
git clone <repo-url>
cd mcp-geo
pip install -e .[test]
uvicorn server.main:app --reload
```
Then visit:
- `GET /health`
- `GET /tools/list`
- `GET /tools/describe`
- `POST /tools/call` with `{ "tool": "os_places.by_postcode", "postcode": "SW1A1AA" }`
- `POST /mcp` with `{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}`

Set `OS_API_KEY` in the environment (or `.env`) for all Ordnance Survey calls. The server assumes it is present; missing or invalid keys return `NO_API_KEY`, `OS_API_KEY_INVALID`, or `OS_API_KEY_EXPIRED`.

## Getting Started (User Guide)

See `docs/getting_started.md` for a quick way to discover available data, run
MCP Inspector or the playground UI, and explore tools/resources.

## Full Specification Package

For a complete design specification (aims, personas, architecture, scenarios,
diagrams, backlog), see `docs/spec_package/README.md`.

## Codex Context (Mac App)

- Use `CONTEXT.md` as the durable project context for Codex across environments.
- If you use the Codex Mac app, open this repo as a project and read `CONTEXT.md`
  at session start.
- Codex app documentation: https://developers.openai.com/codex/app/
- Codex app features: https://developers.openai.com/codex/app/features

## Docker (STDIO / Claude Desktop)
Build the image:
```bash
docker build -t mcp-geo-server .
```

Claude Desktop config example (STDIO transport):
```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "/absolute/path/to/mcp-geo/scripts/claude-mcp-local",
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "MCP_STDIO_UI_SUPPORTED": "1",
        "MCP_STDIO_FRAMING": "line",
        "MCP_STDIO_ELICITATION_ENABLED": "1"
      }
    }
  }
}
```

The wrapper script starts PostGIS locally (Docker), builds the image if needed,
and runs STDIO with the boundary cache enabled.
Use `MCP_GEO_DOCKER_BUILD=always|missing|never` to control rebuild behavior.

If Docker isn't on the GUI PATH (common on macOS), set `MCP_GEO_DOCKER_BIN` in
Claude Desktop to the absolute Docker path (for example `/opt/homebrew/bin/docker`).

Optional HTTP transport:
```bash
docker run --rm -p 8000:8000 \
  -e OS_API_KEY=your-api-key-here \
  mcp-geo-server \
  uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## Tutorial

See [docs/tutorial.md](docs/tutorial.md) for an evaluation-style walkthrough covering tool discovery, admin lookup, OS tools, ONS tools, resources/ETags, and STDIO.

## Evaluation

See [docs/evaluation.md](docs/evaluation.md) for the question suite, rubric, and harness usage.

## Client Tracing

See [docs/client_trace_strategy.md](docs/client_trace_strategy.md) for MCP traffic
and MCP-Apps UI interaction capture using the stdio and HTTP trace proxies.

## Tool Catalog (Epics B–D)
Tools are discoverable via `/tools/list` and rich metadata via `/tools/describe`.

| Tool | Purpose |
|------|---------|
| os_places.search | Free text address search |
| os_places.by_postcode | UPRNs + addresses for a postcode |
| os_places.by_uprn | Single address lookup |
| os_places.nearest | Nearest addresses to a coordinate |
| os_places.within | Addresses within bbox |
| os_names.find | Gazetteer name search |
| os_names.nearest | Nearest named features |
| os_features.query | NGD features by bbox & collection |
| os_linked_ids.get | Relationship lookup between UPRN/USRN/TOID |
| os_maps.render | Static map render metadata (proxy URL) |
| os_vector_tiles.descriptor | Vector tiles style/source descriptor |
| admin_lookup.containing_areas | Administrative area containment for a point |
| admin_lookup.reverse_hierarchy | Ancestor chain for an administrative area |
| admin_lookup.area_geometry | Bounding box geometry for an area |
| admin_lookup.find_by_name | Case-insensitive substring name search |
| ons_data.query | Query live ONS observations (dataset/edition/version or term) |
| ons_data.dimensions | List ONS observation dimensions for a live dataset |
| ons_data.get_observation | Retrieve a single live observation |
| ons_data.create_filter | Create a live ONS filter |
| ons_data.get_filter_output | Retrieve filter output in JSON/CSV/XLSX |
| ons_search.query | Search live ONS datasets (beta API) |
| ons_codes.list | List live dimension IDs |
| ons_codes.options | List live dimension options |
| nomis.datasets | List NOMIS datasets or dataset definitions |
| nomis.concepts | List NOMIS concepts |
| nomis.codelists | List NOMIS code lists |
| nomis.query | Query NOMIS datasets (JSON-stat/SDMX) |
| os_mcp.descriptor | Server capabilities and tool search configuration |
| os_mcp.route_query | Intent classification and tool/workflow recommendation |
| os_apps.render_geography_selector | Open the MCP-Apps geography selector widget |
| os_apps.render_statistics_dashboard | Open the MCP-Apps statistics dashboard widget |
| os_apps.render_feature_inspector | Open the MCP-Apps feature inspector widget |
| os_apps.render_route_planner | Open the MCP-Apps route planner widget |
| os_apps.render_ui_probe | Probe MCP-Apps UI rendering support |

## Resources, Filtering & Provenance
The resources API exposes skills, UI widgets, and data resources (boundary
manifest, cache status, and local ONS code cache entries).

- `GET /resources/list` returns skill, UI, and data resource descriptors (with provenance metadata).
- `GET /resources/read?uri=skills://mcp-geo/getting-started` returns skills guidance.
- `GET /resources/read?uri=ui://mcp-geo/geography-selector` returns MCP-Apps UI HTML.
- `GET /resources/read?uri=resource://mcp-geo/boundary-manifest` returns the boundary manifest.

### Skills and MCP-Apps Resources
In addition to data resources, MCP Geo exposes:

- `skills://mcp-geo/getting-started` (Agent Skills guidance)
- `ui://mcp-geo/geography-selector`
- `ui://mcp-geo/statistics-dashboard`
- `ui://mcp-geo/feature-inspector`
- `ui://mcp-geo/route-planner`

Use `GET /resources/read?uri=...` to fetch these resources. MCP-Apps widgets are
HTML documents with `text/html;profile=mcp-app` MIME types.

MCP-Apps support varies by client. If the client does not advertise UI support,
the stdio adapter injects a `fallback` static map payload for
`os_apps.render_geography_selector` (computed via `os_maps.render`).
Set `MCP_STDIO_UI_SUPPORTED=1` to force UI mode, or
`MCP_STDIO_FALLBACK_BBOX_DEG` to control the fallback map span.
Set `MCP_APPS_CONTENT_MODE=embedded` to embed UI HTML as a `resource` content
block, or `MCP_APPS_CONTENT_MODE=resource_link` to emit a `resource_link`
content block. Use `MCP_APPS_CONTENT_MODE=text` to suppress UI content blocks.
Set `MCP_STDIO_ELICITATION_ENABLED=0` to disable comparison elicitation in
`os_mcp.stats_routing`.

### Conditional Requests (ETag)
Clients should cache UI/skills responses and revalidate using `If-None-Match`.
If unchanged, the server returns `304 Not Modified` with the same `ETag` header.

### Dataset Notes
## Compression (GZip)
GZip compression is enabled (minimum payload size 512 bytes). Send:
```
Accept-Encoding: gzip
```
to receive a compressed response (check `Content-Encoding: gzip`).

## Rate Limiting
Basic per-minute in-memory rate limiting is enabled by default:
- Environment variable: `RATE_LIMIT_PER_MIN` (default 120 per IP per top-level path segment)
- Bypass (tests/dev): `RATE_LIMIT_BYPASS=true` (set to `false` to enforce)
Responses over the limit return:
```json
{ "isError": true, "code": "RATE_LIMITED", "message": "Rate limit exceeded" }
```
Note: In-memory approach is not multi-process safe; replace with Redis or a shared store for production.

## Metrics
Prometheus-style metrics exposed at `GET /metrics` (if `METRICS_ENABLED=true`):
- `app_requests_total` counter
- `app_rate_limited_total` counter
- `app_request_latency_ms_bucket` / `_count` histogram (client-observed wall time per request)

Example scrape output snippet:
```
# HELP app_requests_total Total HTTP requests
# TYPE app_requests_total counter
app_requests_total 42
# HELP app_request_latency_ms Request latency histogram (ms)
# TYPE app_request_latency_ms histogram
app_request_latency_ms_bucket{le="50"} 40
app_request_latency_ms_bucket{le="100"} 41
app_request_latency_ms_bucket{le="+Inf"} 42
app_request_latency_ms_count 42
```
Admin lookup tools call the live ONS Open Geography services by default. Static
boundary resources are not advertised in the resources API.

### ONS Observations & Discovery (Epic D)
ONS data tools require live mode (`ONS_LIVE_ENABLED=true`). You can supply
`dataset`, `edition`, and `version` directly, or provide a `term` and let
`ons_data.query` auto-resolve the latest version.
`ons_codes.*` supports an optional on-disk cache via `ONS_DATASET_CACHE_ENABLED`.

Tool `ons_data.query` supports:
- `geography` (single code)
- `measure` (single code)
- `timeRange` — either single period (`2024 Q2`) or inclusive range (`2024 Q1-2024 Q4`)
- Pagination: `limit` (1–500, default 100) and `page` (1-based)

### ONS Client & Dataset Caching
`tools/ons_common.py` provides:
- Retry + error mapping
- In-memory TTL cache (short-lived request cache)
- `get_all_pages` helper for full dataset paging

Full dataset cache snapshots are stored on disk when enabled via
`ONS_DATASET_CACHE_ENABLED=true` and `ONS_DATASET_CACHE_DIR`.

### Live ONS Mode & Codes
Enable live mode by setting `ONS_LIVE_ENABLED=true`. If you do not supply
dataset metadata, `ons_data.query` will attempt to resolve the latest edition
and version using `term`.

`ons_data.query` (live):
```
GET https://api.ons.gov.uk/dataset/{dataset}/edition/{edition}/version/{version}/observations?limit=...&page=...
```

`ons_data.dimensions` (live):
1. Fetch version metadata:
```
GET https://api.ons.gov.uk/dataset/{dataset}/edition/{edition}/version/{version}
```
2. For each dimension id returned, fetch its codes (paged, currently requesting up to 1000):
```
GET https://api.ons.gov.uk/dataset/{dataset}/edition/{edition}/version/{version}/dimensions/{dimensionId}/options?limit=1000&page=1
```
Provide an optional `dimension` field to retrieve only a single dimension's codes.

`ons_search.query` (live dataset search):
```
GET https://api.beta.ons.gov.uk/v1/datasets?search=<term>&limit=...&offset=...
```
You can override the base with `ONS_DATASET_API_BASE` or disable live search with `ONS_SEARCH_LIVE_ENABLED=false`.

### NOMIS Labour & Census Statistics
Enable live mode with `NOMIS_LIVE_ENABLED=true` (default). Optional credentials
may be provided via `NOMIS_UID` and `NOMIS_SIGNATURE` if you need higher limits.

Use:
- `nomis.datasets` for dataset discovery
- `nomis.concepts` / `nomis.codelists` for metadata
- `nomis.query` for JSON-stat or SDMX JSON observations

## Error Model
All errors conform to:
```json
{ "isError": true, "code": "<CODE>", "message": "..." }
```
Primary codes: `INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`, `OS_API_KEY_INVALID`, `OS_API_KEY_EXPIRED`, `LIVE_DISABLED`, `OS_API_ERROR`, `ONS_API_ERROR`, `NOMIS_API_ERROR`, `ADMIN_LOOKUP_API_ERROR`, `UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`, `INTEGRATION_ERROR`, `RATE_LIMITED`, `UNKNOWN_FILTER`, `NO_OBSERVATION`.

## Project Structure
```text
server/        FastAPI app & routers
tools/         Tool implementations (one module per domain)
resources/     Static datasets (future expansion)
playground/    Svelte + Vite playground UI
tests/         Pytest suite (≥90% coverage)
docs/          Backlog & design notes
.devcontainer/ Dev environment setup
```
Note: The Svelte playground is served by Vite (`npm run dev`). The legacy
`playground/app.py` stub does not serve the UI.

## Dynamic Tool Registration
`server/mcp/tools.py` explicitly imports each `tools.*` module at startup to guarantee registration in environments where implicit side-effect imports are skipped (e.g. selective packaging or lazy loaders). This ensures `/tools/describe` always reflects the full catalog without relying on import order.

## Testing & Coverage
Run tests with:
```bash
pytest -q
```
Coverage gate (configured) requires ≥90%. Add tests for both success and error branches (retry paths, validation failures, upstream errors). Avoid broad mocks that skip normalization logic.

## Contributing
- Use Conventional Commits (e.g. `feat(tools): add os_places.within pagination`).
- Every PR: update `CHANGELOG.md`, add/adjust tests, keep coverage ≥90%.
- Include JSON schemas (input/output) when adding a tool.
- Prefer incremental refactors; avoid unrelated changes in feature PRs.

## Enriched Address Data
`os_places.*` currently return raw OS Places fields only. Enrichment via local
code lists is not implemented yet.

## Examples & Golden Tests
See `docs/examples.md` for sample payloads, conversation flows, and guidance on chaining tools. Golden scenario tests (`test_golden_scenarios.py`) ensure transformation stability with deterministic mocked upstream responses.

## Resource Caching & Provenance
All `/resources/read` responses include:
- `etag` (weak) for conditional requests
- `provenance.retrievedAt` timestamp
- `Cache-Control` header
Clients should respect TTL and still perform ETag revalidation for freshness.

## Troubleshooting
See `docs/troubleshooting.md` for a table of common error codes (`INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`, `OS_API_KEY_INVALID`, etc.) and remediation steps.

## Configuration
Copy `.env.example` → `.env` and set `OS_API_KEY`. Optional flags:
- `DEBUG_ERRORS` (if present / truthy) enables traceback in error responses; otherwise stack traces are suppressed.
- `CIRCUIT_BREAKER_ENABLED`, `CIRCUIT_BREAKER_FAILURE_THRESHOLD`,
  `CIRCUIT_BREAKER_RESET_SECONDS` to control upstream circuit breaker behavior.

## SSL & Certificates
Container and dev setup ensure current CA bundle (certifi) for stable TLS to OS APIs.

## License
MIT

## MCP STDIO Adapter (Local Dev)
The JSON-RPC 2.0 STDIO adapter lives in `server/stdio_adapter.py` (refactored from the prior `scripts/os_mcp.py`). Legacy entry points remain:
- Console script: `mcp-geo-stdio`
- Wrapper script: `scripts/os-mcp` (delegates to `server/stdio_adapter.py`)

This adapter is referenced by `mcp.json` (`mcp-geo-stdio`).

### Framing
Each request/response:
```
Content-Length: <bytes>\r\n
\r\n
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}
```

### Methods
| Method          | Description |
|-----------------|-------------|
| initialize      | Returns server metadata & capabilities |
| tools/list      | Lists tools (name, description, schemas) |
| tools/call      | Invoke a tool (`params.tool`, optional `params.args`) |
| resources/list  | Lists resource descriptors (skills + UI resources) |
| resources/describe | Returns resource metadata (name, description, license) |
| resources/read   | Fetch resource content (ETag supported) |
| shutdown        | Graceful shutdown (result null) |
| exit (notify)   | Process terminates (no response) |

Tool call result shape:
```json
{
	"jsonrpc": "2.0",
	"id": 3,
	"result": { "status": 200, "ok": true, "data": { ...tool output... } }
}
```

### Manual Test
```bash
python scripts/os-mcp & PID=$!
printf 'Content-Length: 60\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | nc -U /dev/fd/0 # or use a small Python helper
kill $PID
```
Simpler: write a tiny Python snippet to send framed messages (see `tests/test_stdio_adapter.py`).

### VS Code
Opening the workspace lets compatible MCP extensions discover `mcp.json` and spawn the STDIO adapter. Environment variables (`OS_API_KEY`, `ONS_LIVE_ENABLED`) are injected via the `env` block.

### Notes
- `resources/read` now emits a weak ETag (`etag`) and supports conditional retrieval via `ifNoneMatch` param. If matched, response shape: `{ "jsonrpc":"2.0", "id": <n>, "result": { "notModified": true, "etag": "W/\"...\"" } }`.
- Use the same pagination/filter parameters when revalidating or the variant key changes and a full payload is returned.
- `resources/describe` returns the static metadata list (extend as resources grow).
- Errors follow JSON-RPC error envelope with custom positive codes (1001-1003) for validation and -32603 for internal errors.

### Helper Client Script
For quick one-shot invocations without crafting frames manually, use the helper script added in `scripts/mcp_client.py` (it spawns the adapter, performs `initialize`, your requested method, then `shutdown`/`exit`).

Examples:
```bash
# List tools
python scripts/mcp_client.py tools/list

# Describe available ONS dimensions (live mode)
ONS_LIVE_ENABLED=true python scripts/mcp_client.py tools/call ons_data.dimensions '{"params":{"dataset":"gdp","edition":"time-series","version":"1"}}'

# Query observations (live)
ONS_LIVE_ENABLED=true python scripts/mcp_client.py tools/call ons_data.query '{"params":{"dataset":"gdp","edition":"time-series","version":"1","geography":"K02000001","limit":2}}'

# Fetch resource with ETag then conditional request
R1=$(python scripts/mcp_client.py resources/read '{"uri":"skills://mcp-geo/getting-started"}' | jq -r '.response.result.etag')
python scripts/mcp_client.py resources/read '{"uri":"skills://mcp-geo/getting-started","ifNoneMatch":"'$R1'"}'

# Or using the convenience flag (no JSON escaping needed):
python scripts/mcp_client.py resources/read --if-none-match "$R1" '{"uri":"skills://mcp-geo/getting-started"}'
```

The JSON argument after the tool name is merged into the request `params` object. Include nested objects as required by each tool schema.

### Correct Inline Heredoc Helper (Advanced)
If you prefer piping multiple framed requests to a persistently running adapter instance:
```bash
python scripts/os-mcp & APP_PID=$!
python - <<'PY'
import sys, json
def send(mid, method, params=None):
	msg = {"jsonrpc":"2.0","id":mid,"method":method,"params":params or {}}
	body = json.dumps(msg).encode()
	sys.stdout.buffer.write(b"Content-Length: "+str(len(body)).encode()+b"\r\n\r\n"+body)
	sys.stdout.flush()

# Emit two requests (initialize then list tools)
send(1, "initialize")
send(2, "tools/list")
PY | ./scripts/os-mcp
kill $APP_PID
```
Be careful to avoid duplicating or truncating function definitions when editing inline; each framed JSON-RPC message must be complete and preceded by a correct `Content-Length` header.

### REPL Mode
Interactive session:
```bash
python scripts/mcp_client.py --repl
mcp> resources/describe
mcp> resources/read {"uri":"skills://mcp-geo/getting-started"}
mcp> resources/read {"uri":"skills://mcp-geo/getting-started","ifNoneMatch":"W/\"abc123deadbeef00\""}
mcp> exit
```
`notModified` responses are compacted by the client for readability.
