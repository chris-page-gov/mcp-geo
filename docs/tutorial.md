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

- `OS_API_KEY`: enables Ordnance Survey-backed tools (Places, Names, NGD Features, Linked IDs, etc).
  If unset, OS-backed tools return `501` with `{ "code": "NO_API_KEY" }`.
- `ONS_LIVE_ENABLED=true`: enables live ONS API access for `ons_data.*` when you supply `dataset`, `edition`, `version`.
  If unset/false, mcp-geo uses bundled sample data.

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
        "ONS_LIVE_ENABLED": "true"
      }
    }
  }
}
```

Notes:
- If you installed the package, swap `command` to `mcp-geo-stdio`.
- If your client supports `cwd`, set it to the repo root when using `./scripts/os-mcp`.
- Remove `ONS_LIVE_ENABLED` or set it to `"false"` if you want sample ONS data only.
- `mcp.json` includes a ready-to-copy entry using the same settings.

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

MCP-Apps widgets require a client that supports UI resources (for example,
Claude Desktop). If your client does not render MCP-Apps, the server will still
return data-only responses.

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
- Microsoft/OpenAI/Google MCP-capable clients can still use tool search; if they
  do not render MCP-Apps, they will receive `uiResourceUris` and can fall back
  to data-only flows.

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
curl -sS "$BASE_URL/resources/get?name=ons_observations"
```

## Basic evaluation-style questions

The upstream evaluation suite names tools like `search_geographic_areas` and `list_ons_datasets`.
In **mcp-geo**, closest equivalents are:

- admin areas: `admin_lookup.*` (bundled sample boundaries)
- datasets/resources: `/resources/*` and `ons_data.*`
- “open a map”: `os_maps.render` (descriptor) + `admin_lookup.containing_areas` (point containment)

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

## Ordnance Survey tools (require OS_API_KEY)

If `OS_API_KEY` is not set, these tools return `501 NO_API_KEY`.

### OS Places

Postcode lookup:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_places.by_postcode","postcode":"SW1A1AA"}'
```

Free-text search:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_places.search","text":"10 Downing Street"}'
```

### OS Names

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_names.find","text":"Edinburgh"}'
```

### NGD features and linked IDs

Query a feature collection within a bounding box:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_features.query","collection":"buildings","bbox":[-0.15,51.49,-0.10,51.52]}'
```

Resolve linked IDs (e.g., UPRN/TOID/USRN relationships):

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_linked_ids.get","id":"<uprn-or-toid>"}'
```

### Vector tiles descriptor

Returns style/source metadata suitable for a tiles client:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_vector_tiles.descriptor"}'
```

## ONS data tools (sample + live modes)

List available dimensions (sample mode):

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.dimensions"}'
```

Query observations (sample mode):

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.query","geography":"K02000001"}'
```

In live mode, include `dataset`, `edition`, and `version`:

```bash
curl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.query","dataset":"<dataset>","edition":"<edition>","version":"<version>","geography":"K02000001"}'
```

## Resources and conditional caching (ETag)

1) Fetch a resource and note the `ETag` response header:

```bash
curl -i "$BASE_URL/resources/get?name=admin_boundaries" | sed -n '1,20p'
```

2) Revalidate with `If-None-Match`:

```bash
curl -i "$BASE_URL/resources/get?name=admin_boundaries" \
  -H 'If-None-Match: W/"<etag-from-previous-response>"'
```

If unchanged, the server returns `304 Not Modified` with an empty body.

## Rate limiting, metrics, correlation IDs

- Rate limiting is enforced by middleware unless `RATE_LIMIT_BYPASS=true` (common in tests/dev).
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
