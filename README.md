# MCP Geo Server

Production-focused Model Context Protocol (MCP) server for geospatial (Ordnance Survey) tooling built with FastAPI & Python 3.11+. Provides a uniform tool abstraction, typed schemas, structured error model, correlation IDs, and high test coverage (≥90%).

## Key Features
- MCP endpoints: `/tools/list`, `/tools/call`, `/tools/describe`, `/resources/list`, `/resources/get`
- Uniform error envelope and pagination (`nextPageToken`)
- Dynamic tool registration with schema introspection
- Structured logging & correlation IDs
- OS API client with retries and explicit upstream error codes
- High coverage test suite exercising success + failure paths

## Quickstart
```bash
git clone <repo-url>
cd mcp-geo
pip install -e .[test]
uvicorn server.main:app --reload
```
Then visit:
- `GET /healthz`
- `GET /tools/list`
- `GET /tools/describe`
- `POST /tools/call` with `{ "tool": "os_places.by_postcode", "postcode": "SW1A1AA" }`

Set `OS_API_KEY` in environment (or `.env`) for live Ordnance Survey calls; otherwise tools return graceful `501 NO_API_KEY` responses.

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
| os_maps.render | Static map render metadata (stub/descriptor) |
| os_vector_tiles.descriptor | Vector tiles style/source descriptor |
| admin_lookup.containing_areas | Administrative area containment for a point |
| admin_lookup.reverse_hierarchy | Ancestor chain for an administrative area |
| admin_lookup.area_geometry | Bounding box geometry for an area |
| admin_lookup.find_by_name | Case-insensitive substring name search |
| ons_data.query | Query sample or live ONS observations (geography / measure / time) |
| ons_data.dimensions | List available ONS observation dimensions (sample or live) |
| ons_data.get_observation | Retrieve a single observation (sample/live) |
| ons_data.create_filter | Create an ONS bulk filter (sample scaffold) |
| ons_data.get_filter_output | Retrieve filter output in JSON (sample) |
| ons_search.query | Search ONS datasets/dimensions (sample) |
| ons_codes.list | List dimension IDs (sample/live) |
| ons_codes.options | List codes/options for a dimension (sample/live) |

## Resources, Filtering & Provenance
The server exposes static / reference datasets under the resources API surface:

- `GET /resources/list` returns an array of resource descriptors (now including provenance: version, source, license).
- `GET /resources/get?name=admin_boundaries` returns the administrative boundaries sample dataset with optional parameters:
	- `limit` (default 100, max 500)
	- `page` (1-based)
	- `level` (e.g. `OA`, `LSOA`, `MSOA`, `WARD`, `DISTRICT`, `COUNTY`, `REGION`, `NATION`)
	- `nameContains` (case-insensitive substring filter)
	Response includes:
	- `etag`: Weak ETag for conditional caching (SHA-256 of file + version)
	- `provenance`: Embedded metadata (version, source, license, retrievedAt)
	- `count`: Total filtered feature count (across all pages)
	- `data.features`: Current page of features
	- `data.total`: Same as `count` (filtered total)
	- `data.limit`, `data.page`, `data.nextPageToken`
	- `data.features[*].bbox` retains original CRS (EPSG:4326)

### Conditional Requests (ETag)
Clients should cache responses and revalidate:
```
GET /resources/get?name=admin_boundaries
If-None-Match: W/"f337e5733a4b7f50"
```
If unchanged, the server returns `304 Not Modified` with the same `ETag` header and an empty body.

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
Current `admin_boundaries` is a minimal illustrative chain (OA→LSOA→MSOA→Ward→District→County→Region→Nation) using real English geography codes (sample Westminster lineage). Not a complete authoritative dataset—replace or extend before production use.

### ONS Observations & Discovery (Epic D)
An initial statistical dataset (`resources/ons_observations.json`) is bundled to prototype ONS integration.

Dimensions:
- `geography`: e.g. `K02000001` (UK), `E92000001` (England)
- `measure`: `GDPV` (illustrative)
- `seasonalAdjustment`: `SA` (seasonally adjusted)
- `time`: Quarterly periods (e.g. `2024 Q1`)

Tool `ons_data.query` supports filters:
- `geography` (single code)
- `measure` (single code)
- `timeRange` — either single period (`2024 Q2`) or inclusive range (`2024 Q1-2024 Q4`)
- Pagination: `limit` (1–500, default 100) and `page` (1-based)

Response shape:
```json
{
	"results": [ { "geography": "K02000001", "measure": "GDPV", "time": "2024 Q1", "value": 100.2 } ],
	"count": 5,
	"data": { "limit": 2, "page": 1, "nextPageToken": "2" }
}
```
`count` is total after filtering (before pagination). `nextPageToken` absent on final page. This mock illustrates future integration with real ONS APIs (observations, dimensions catalogue, metadata endpoints) that will replace or augment the static file.

### ONS Observations Resource
The underlying sample dataset is also exposed via the resources API:
```
GET /resources/list            # includes ons_observations
GET /resources/get?name=ons_observations&limit=2&page=1
```
Response includes `observations`, `dimensions`, pagination metadata, provenance, and ETag for conditional requests.

### ONS Client & Discovery Scaffold
`tools/ons_common.py` introduces `ONSClient` with:
- Simple `get_json` wrapper (retry + error mapping)
- In-memory TTL cache (configurable via `ONS_CACHE_TTL`, `ONS_CACHE_SIZE`)
- Pagination helper `build_paged_params(limit, page, extra)`
This prepares the codebase for swapping the static dataset with live ONS endpoints while keeping test determinism (cache can be tuned in tests).

### Live ONS Mode & Codes
Enable live mode by setting `ONS_LIVE_ENABLED=true` and supplying `dataset`, `edition`, and `version` in tool payloads.

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
Provide an optional `dimension` field to retrieve only a single dimension's codes (optimization avoids extra network calls).

If live mode is disabled (or parameters missing) both tools fall back to the bundled sample dataset.

### ons_observations Resource & Filters
The resource endpoint now supports:
```
GET /resources/get?name=ons_observations&geography=K02000001&measure=chained_volume_measure
```
Filters influence pagination and ETag variant generation (`geography`, `measure`).

## Error Model
All errors conform to:
```json
{ "isError": true, "code": "<CODE>", "message": "..." }
```
Primary codes: `INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`, `OS_API_ERROR`, `UPSTREAM_TLS_ERROR`, `UPSTREAM_CONNECT_ERROR`, `INTEGRATION_ERROR`, `RATE_LIMITED`, `UNKNOWN_FILTER`, `NO_OBSERVATION`.

## Project Structure
```text
server/        FastAPI app & routers
tools/         Tool implementations (one module per domain)
resources/     Static datasets (future expansion)
playground/    Transcript / UI stubs
tests/         Pytest suite (≥90% coverage)
docs/          Backlog & design notes
.devcontainer/ Dev environment setup
```

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
`os_places.by_postcode` now enriches each UPRN record with:
- `classificationDescription` — human-readable description looked up from `address_classification_codes.json`.
- `localCustodianName` — local authority name from `custodian_codes.json`.
These static code lists are exposed via `/resources/get?name=address_classification_codes` and `/resources/get?name=custodian_codes`.
Other `os_places.*` endpoints will adopt the same enrichment (roadmap).

## Examples & Golden Tests
See `docs/examples.md` for sample payloads, conversation flows, and guidance on chaining tools. Golden scenario tests (`test_golden_scenarios.py`) ensure transformation stability with deterministic mocked upstream responses.

## Resource Caching & Provenance
All `/resources/get` responses include:
- `etag` (weak) for conditional requests
- `provenance.retrievedAt` timestamp
- `Cache-Control` header (currently 300s for dynamic admin boundaries sample; 86400s for static code lists)
Clients should respect TTL and still perform ETag revalidation for freshness.

## Troubleshooting
See `docs/troubleshooting.md` for a table of common error codes (`INVALID_INPUT`, `UNKNOWN_TOOL`, `NO_API_KEY`, etc.) and remediation steps.

## Configuration
Copy `.env.example` → `.env` and set `OS_API_KEY`. Optional flags:
- `DEBUG_ERRORS` (if present / truthy) enables traceback in error responses; otherwise stack traces are suppressed.

## SSL & Certificates
Container and dev setup ensure current CA bundle (certifi) for stable TLS to OS APIs.

## License
MIT

## MCP STDIO Adapter (Local Dev)
The JSON-RPC 2.0 STDIO adapter lives in `server/stdio_adapter.py` (refactored from the prior `scripts/os_mcp.py`). Legacy entry points remain:
- Console script: `mcp-geo-stdio`
- Wrapper script: `scripts/os-mcp` (delegates to `server/stdio_adapter.py`)

This adapter is referenced by `mcp.json` (`os-mcp-stdio`).

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
| resources/list  | Lists basic resource names |
| resources/describe | Returns resource metadata (name, description, license) |
| resources/get   | Fetch resource data (supports filters, ETag varianting) |
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
- `resources/get` now emits a weak ETag (`etag`) and supports conditional retrieval via `ifNoneMatch` param. If matched, response shape: `{ "jsonrpc":"2.0", "id": <n>, "result": { "notModified": true, "etag": "W/\"...\"" } }`.
- Use the same pagination/filter parameters when revalidating or the variant key changes and a full payload is returned.
- `resources/describe` returns the static metadata list (extend as resources grow).
- Errors follow JSON-RPC error envelope with custom positive codes (1001-1003) for validation and -32603 for internal errors.

### Helper Client Script
For quick one-shot invocations without crafting frames manually, use the helper script added in `scripts/mcp_client.py` (it spawns the adapter, performs `initialize`, your requested method, then `shutdown`/`exit`).

Examples:
```bash
# List tools
python scripts/mcp_client.py tools/list

# Describe available ONS dimensions (sample mode)
python scripts/mcp_client.py tools/call ons_data.dimensions '{}'

# Live mode (requires env vars); pass dataset/edition/version via params
ONS_LIVE_ENABLED=true python scripts/mcp_client.py tools/call ons_data.dimensions '{"params":{"dataset":"gdp","edition":"time-series","version":"1"}}'

# Query observations (sample)
python scripts/mcp_client.py tools/call ons_data.query '{"params":{"geography":"K02000001","limit":2}}'

# Fetch resource with ETag then conditional request (two approaches)
R1=$(python scripts/mcp_client.py resources/get '{"name":"admin_boundaries","limit":1}' | jq -r '.response.result.etag')
python scripts/mcp_client.py resources/get '{"name":"admin_boundaries","limit":1,"ifNoneMatch":"'$R1'"}'

# Or using the convenience flag (no JSON escaping needed):
python scripts/mcp_client.py resources/get --if-none-match "$R1" '{"name":"admin_boundaries","limit":1}'
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
mcp> resources/get {"name":"ons_observations","geography":"K02000001","limit":2}
mcp> resources/get {"name":"ons_observations","geography":"K02000001","limit":2,"ifNoneMatch":"W/\"abc123deadbeef00\""}
mcp> exit
```
`notModified` responses are compacted by the client for readability.
