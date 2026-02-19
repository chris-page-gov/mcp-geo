# API Contracts and Protocol

## MCP endpoints

- `/mcp` (streamable HTTP JSON-RPC)
- `/tools/list`, `/tools/describe`, `/tools/call`, `/tools/search`
- `/resources/list`, `/resources/describe`, `/resources/read`
- `/prompts/list`, `/prompts/get`

## STDIO JSON-RPC framing

- Content-Length framing (default)
- Optional line framing (`MCP_STDIO_FRAMING=line`)

## Tool call schema (STDIO)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {"name": "os_places.by_postcode", "arguments": {"postcode": "SW1A 1AA"}}
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"status": 200, "ok": true, "data": {"uprns": []}}
}
```

## Error envelope

```json
{ "isError": true, "code": "INVALID_INPUT", "message": "..." }
```

## `os_features.query` reliability contract

`os_features.query` now follows a bounded-response contract designed for
stdio-host reliability:

1. `numberReturned` always equals `len(features)`.
2. `count` is the returned feature count (same as `numberReturned`).
3. `numberMatched` is included only when reliable (`null` otherwise).
4. `limit` is clamped to NGD-safe max (`<=100`) with warning metadata.
5. `delivery=inline|resource|auto` is supported for large payload handoff.

Representative response envelope:

```json
{
  "collection": "lnd-fts-land-3",
  "features": [],
  "count": 0,
  "numberMatched": null,
  "numberReturned": 0,
  "nextPageToken": "100",
  "delivery": "inline",
  "hints": {
    "warnings": ["RESULT_LIMIT_CLAMPED", "LOCAL_FILTER_PARTIAL_SCAN"],
    "filterApplied": "local",
    "scan": {
      "mode": "local",
      "pagesScanned": 1,
      "pageBudget": 1,
      "partial": true
    }
  }
}
```

## Canonical map delivery contract order

All host profiles should use this order:

1. `os_maps.render` static map contract (baseline, always available).
2. `overlay_bundle` data overlays.
3. MCP-Apps widget content (`os_apps.render_*`) when UI support is advertised.
4. Explicit fallback skeletons for non-UI/partial-UI hosts.

Detailed fallback schema guidance lives in
`docs/spec_package/06a_map_delivery_fallback_contracts.md`.

## Fallback skeleton snippets

Offline workflows can request these contracts via `os_offline.get`.

### `map_card`

```json
{
  "type": "map_card",
  "title": "Westminster ward map",
  "bbox": [-0.18, 51.49, -0.05, 51.54],
  "render": {"imageUrl": "/maps/static/osm?bbox=-0.18,51.49,-0.05,51.54&size=640&zoom=13"},
  "guidance": {
    "widgetUnsupported": true,
    "widgetUnsupportedReason": "ui_extension_not_advertised",
    "degradationMode": "no_ui",
    "preferredNextTools": ["os_maps.render", "admin_lookup.area_geometry"]
  }
}
```

### `overlay_bundle`

```json
{
  "type": "overlay_bundle",
  "layers": [
    {
      "id": "input_points",
      "name": "Input points",
      "kind": "point",
      "featureCollection": {"type": "FeatureCollection", "features": []}
    }
  ],
  "source": {"tool": "os_maps.render", "generatedAt": "2026-02-14T00:00:00Z"}
}
```

### `export_handoff`

```json
{
  "type": "export_handoff",
  "resourceUri": "resource://mcp-geo/os-exports/example.json",
  "format": "json",
  "generatedAt": "2026-02-14T00:00:00Z",
  "hash": "sha256:..."
}
```

## Host compatibility modes

- `full_ui`: widgets + data contracts.
- `partial_ui`: host accepts some UI content blocks but still requires fallback
  skeletons.
- `no_ui`: host does not advertise `io.modelcontextprotocol/ui`; return fallback
  skeletons directly.

The same fallback key names must remain stable across STDIO and HTTP transports.

## MCP-Apps UI resources

- `ui://mcp-geo/geography-selector`
- `ui://mcp-geo/boundary-explorer`
- `ui://mcp-geo/route-planner`
- `ui://mcp-geo/feature-inspector`
- `ui://mcp-geo/statistics-dashboard`

Returned via `resources/read` with `text/html;profile=mcp-app`.
