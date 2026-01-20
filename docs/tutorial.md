# MCP Geo tutorial

This tutorial is an evaluation-style walkthrough for the **mcp-geo** MCP server.
It is inspired by the question suite in `submodules/os-mcp/docs/evaluation.md`, but uses **mcp-geo** tool names and endpoints.

## Run the server

```bashpip install -e .[test]
uvicorn server.main:app --reload
```

Set a base URL for the examples:

```bashexport BASE_URL=${BASE_URL:-http://127.0.0.1:8000}
```

Check health:

```bashcurl -sS -o /dev/null -w 'healthz=%{http_code}\n' "$BASE_URL/healthz"
```

### Environment variables

- `OS_API_KEY`: enables Ordnance Survey-backed tools (Places, Names, NGD Features, Linked IDs, etc).
  If unset, OS-backed tools return `501` with `{ "code": "NO_API_KEY" }`.
- `ONS_LIVE_ENABLED=true`: enables live ONS API access for `ons_data.*` when you supply `dataset`, `edition`, `version`.
  If unset/false, mcp-geo uses bundled sample data.

## How to call tools

`POST /tools/call` expects JSON containing at least the tool name plus tool-specific fields.

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Birmingham"}'
```

Error responses use a consistent envelope:

```json
{ "isError": true, "code": "SOME_CODE", "message": "Human readable message", "correlationId": "...optional..." }
```

## Discover tools and resources

List tools (paged via `nextPageToken`):

```bashcurl -sS "$BASE_URL/tools/list"
```

Describe tools (schemas + descriptions):

```bashcurl -sS "$BASE_URL/tools/describe"
```

List resources (paged via `nextPageToken`):

```bashcurl -sS "$BASE_URL/resources/list?limit=50&page=1"
```

Fetch a resource:

```bashcurl -sS "$BASE_URL/resources/get?name=ons_observations"
```

## Basic evaluation-style questions

The upstream evaluation suite names tools like `search_geographic_areas` and `list_ons_datasets`.
In **mcp-geo**, closest equivalents are:

- admin areas: `admin_lookup.*` (bundled sample boundaries)
- datasets/resources: `/resources/*` and `ons_data.*`
- “open a map”: `os_maps.render` (descriptor) + `admin_lookup.containing_areas` (point containment)

### Find Birmingham

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Birmingham"}'
```

### Where is Manchester?

A practical answer is a bounding box.

1) Find an id:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.find_by_name","text":"Manchester"}'
```

2) Fetch bbox geometry:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.area_geometry","id":"<id-from-search>"}'
```

### Administrative hierarchy for an area

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"admin_lookup.reverse_hierarchy","id":"<area-id>"}'
```

### What datasets are available?

mcp-geo exposes bundled datasets via the Resources API:

```bashcurl -sS "$BASE_URL/resources/list?limit=50&page=1"
```

## Ordnance Survey tools (require OS_API_KEY)

If `OS_API_KEY` is not set, these tools return `501 NO_API_KEY`.

### OS Places

Postcode lookup:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_places.by_postcode","postcode":"SW1A1AA"}'
```

Free-text search:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_places.search","text":"10 Downing Street"}'
```

### OS Names

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_names.find","text":"Edinburgh"}'
```

### NGD features and linked IDs

Query a feature collection within a bounding box:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_features.query","collection":"buildings","bbox":[-0.15,51.49,-0.10,51.52]}'
```

Resolve linked IDs (e.g., UPRN/TOID/USRN relationships):

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_linked_ids.get","id":"<uprn-or-toid>"}'
```

### Vector tiles descriptor

Returns style/source metadata suitable for a tiles client:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"os_vector_tiles.descriptor"}'
```

## ONS data tools (sample + live modes)

List available dimensions (sample mode):

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.dimensions"}'
```

Query observations (sample mode):

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.query","geography":"K02000001"}'
```

In live mode, include `dataset`, `edition`, and `version`:

```bashcurl -sS "$BASE_URL/tools/call" \
  -H 'content-type: application/json' \
  -d '{"tool":"ons_data.query","dataset":"<dataset>","edition":"<edition>","version":"<version>","geography":"K02000001"}'
```

## Resources and conditional caching (ETag)

1) Fetch a resource and note the `ETag` response header:

```bashcurl -i "$BASE_URL/resources/get?name=admin_boundaries" | sed -n '1,20p'
```

2) Revalidate with `If-None-Match`:

```bashcurl -i "$BASE_URL/resources/get?name=admin_boundaries" \
  -H 'If-None-Match: W/"<etag-from-previous-response>"'
```

If unchanged, the server returns `304 Not Modified` with an empty body.

## Rate limiting, metrics, correlation IDs

- Rate limiting is enforced by middleware unless `RATE_LIMIT_BYPASS=true` (common in tests/dev).
- Metrics are available at `GET /metrics` when `METRICS_ENABLED=true`.
- Correlation IDs are created/propagated via the `x-correlation-id` header.

## STDIO (JSON-RPC 2.0)

There is a JSON-RPC 2.0 STDIO adapter.

- Console script: `mcp-geo-stdio`
- Legacy wrapper: `scripts/os-mcp`

See server implementation in `server/stdio_adapter.py`.
