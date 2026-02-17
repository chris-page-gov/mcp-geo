# MCP Geo Examples

## Canonical map delivery flow (widget optional)

Start map workflows with `os_maps.render`; do not require widgets for baseline
success.

```json
POST /tools/call
{
  "tool": "os_maps.render",
  "bbox": [-0.18, 51.49, -0.05, 51.54],
  "size": 640,
  "zoom": 13
}
```

Typical fallback skeletons for non-UI hosts:

```json
{
  "type": "map_card",
  "title": "Westminster map",
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

```json
{
  "type": "overlay_bundle",
  "layers": [
    {"id": "input_points", "kind": "point", "featureCollection": {"type": "FeatureCollection", "features": []}}
  ]
}
```

```json
{
  "type": "export_handoff",
  "resourceUri": "resource://mcp-geo/os-exports/example.json",
  "format": "json",
  "generatedAt": "2026-02-14T00:00:00Z",
  "hash": "sha256:..."
}
```

References:
- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

## Progressive fallback examples (official pattern)

Full UI host:

```json
POST /tools/call
{ "tool": "os_apps.render_geography_selector", "level": "ward" }
```

Partial UI host:

```json
POST /tools/call
{
  "tool": "os_maps.render",
  "bbox": [-0.18, 51.49, -0.05, 51.54],
  "overlays": { "points": [{ "lat": 51.5034, "lon": -0.1276, "properties": { "label": "A" } }] }
}
```

No UI host:

```json
POST /tools/call
{ "tool": "os_offline.get", "packId": "gb_basemap_light_pmtiles" }
```

Style profile reference:

```http
GET /resources/read?uri=resource://mcp-geo/map-embedding-style-profiles
```

## Tool Invocation Payloads

```
POST /tools/call
{ "tool": "os_places.by_postcode", "postcode": "SW1A1AA" }

# Enriched UPRN output now includes classificationDescription & localCustodianName
# Example response excerpt:
# {
#   "uprns": [
#     {
#       "uprn": "100023336959",
#       "address": "10 Downing Street, London",
#       "classification": "RD",
#       "classificationDescription": "Residential Detached",
#       "local_custodian_code": 5990,
#       "localCustodianName": "Westminster City Council"
#     }
#   ]
# }

POST /tools/call
{ "tool": "os_places.search", "text": "10 Downing Street" }

POST /tools/call
{ "tool": "os_names.find", "text": "Downing" }

POST /tools/call
{ "tool": "os_maps.render", "bbox": [-0.18, 51.49, -0.05, 51.54], "size": 640, "zoom": 13 }

POST /tools/call
{ "tool": "os_offline.descriptor" }

POST /tools/call
{ "tool": "os_offline.get", "packId": "gb_basemap_light_pmtiles", "bbox": [-0.18, 51.49, -0.05, 51.54] }

POST /tools/call
{ "tool": "os_names.nearest", "lat": 51.5034, "lon": -0.1276 }

POST /tools/call
{ "tool": "os_places.nearest", "lat": 51.5034, "lon": -0.1276 }

POST /tools/call
{ "tool": "os_places.within", "bbox": [-0.14, 51.50, -0.12, 51.51] }

POST /tools/call
{ "tool": "os_features.query", "collection": "buildings", "bbox": [-0.14,51.50,-0.12,51.51] }

POST /tools/call
{ "tool": "os_linked_ids.get", "identifier": "100021892956" }

POST /tools/call
{ "tool": "ons_data.query", "geography": "K02000001", "limit": 2 }

POST /tools/call
{ "tool": "ons_data.dimensions" }

POST /tools/call
# Live dataset search (beta API)
{ "tool": "ons_search.query", "term": "population" }

POST /tools/call
{ "tool": "ons_codes.list" }

POST /tools/call
{ "tool": "ons_codes.options", "dimension": "geography" }

POST /tools/call
{ "tool": "ons_data.create_filter", "geography": ["K02000001"], "measure": ["GDPV"], "timeRange": "2024 Q1-2024 Q2" }

POST /tools/call
{ "tool": "ons_data.get_filter_output", "filterId": "FILT123" }
```

## Tool Search and MCP-Apps

Lean startup discovery (recommended for initialization):

```
POST /tools/list
{ "toolset": "starter" }
```

Defer broad discovery until after initialization:

```
POST /tools/list
{ "includeToolsets": ["maps_tiles", "apps_ui", "admin_boundaries"] }
```

```
POST /tools/search
{ "query": "postcode" }

POST /tools/search
{ "query": "^os_places\\.", "mode": "regex" }

POST /tools/call
{ "tool": "os_mcp.route_query", "query": "Find Westminster ward boundaries" }

POST /tools/call
{ "tool": "os_mcp.descriptor" }

POST /tools/call
{ "tool": "os_apps.render_geography_selector", "level": "ward" }

GET /resources/read?uri=skills://mcp-geo/getting-started
GET /resources/read?uri=ui://mcp-geo/geography-selector
```

## Error Examples

```
{ "tool": "os_places.by_postcode" }
-> 400 INVALID_INPUT (missing postcode)

{ "tool": "os_names.nearest", "lat": "abc", "lon": 1 }
-> 400 INVALID_INPUT (lat/lon must be numeric)

{ "tool": "os_places.by_postcode", "postcode": "ZZ99ZZ" }
-> 400 INVALID_INPUT (invalid postcode format)
```

## Conversation Snippets

### 1. UPRNs for a Postcode
User: List addresses for SW1A 1AA.
Assistant (internal): call os_places.by_postcode { postcode: "SW1A1AA" }
Assistant: Returns N UPRNs with addresses + classificationDescription + localCustodianName.

### 2. Nearest Named Feature then Addresses
User: What named features and addresses are near 51.5034,-0.1276?
Assistant (internal sequence):
1. os_names.nearest { lat: 51.5034, lon: -0.1276 }
2. os_places.nearest { lat: 51.5034, lon: -0.1276 }
Assistant: Summarize top names + count of addresses.

### 3. Features by BBox
User: Show building feature IDs in small Westminster box.
Assistant (internal): os_features.query { collection: "buildings", bbox: [...] }
Assistant: Lists feature IDs and geometry types.

### 5. ONS Dimensions & Query
User: What observation dimensions are available?
Assistant (internal): ons_data.dimensions {}
Assistant: Returns dimension list and codes.

User: Get two observations for UK GDPV.
Assistant (internal): ons_data.query { geography: "K02000001", measure: "GDPV", limit: 2 }
Assistant: Provides first two observations, includes count and pagination token if more.

### 6. ONS Filter Workflow (Sample)
User: Prepare a bulk GDPV filter for UK 2024 Q1-Q2.
Assistant (internal sequence):
1. ons_data.create_filter { geography: ["K02000001"], measure: ["GDPV"], timeRange: "2024 Q1-2024 Q2" }
2. ons_data.get_filter_output { filterId: "<returned id>" }
Assistant: Returns JSON results (future: CSV/XLSX).

Example create filter response:
```
{
	"filterId": "FILT123",
	"status": "created",
	"requested": {
		"geography": ["K02000001"],
		"measure": ["GDPV"],
		"timeRange": "2024 Q1-2024 Q2"
	}
}
```

Example get filter output response:
```
{
	"filterId": "FILT123",
	"results": [
		{"geography": "K02000001", "measure": "GDPV", "time": "2024 Q1", "value": 100.2},
		{"geography": "K02000001", "measure": "GDPV", "time": "2024 Q2", "value": 101.0}
	],
	"count": 2,
	"provenance": {"source": "ons_data", "mode": "sample"}
}
```

Future enhancement: CSV/XLSX output with `format` parameter (planned) and streaming for large result sets.

### 4. Linked Identifiers
User: Given this UPRN 100021892956 what other IDs exist?
Assistant (internal): os_linked_ids.get { identifier: "100021892956" }
Assistant: Presents related USRNs / TOIDs if present.

## Pattern Guidance
- Normalize postcode (strip spaces, uppercase) before calling.
- Use nearest tools only when both lat & lon present.
- Summaries: list top 5 results; mention total count when >5.
- Chain: find geometry (features / coordinates) first, then overlay other data.
- For ONS queries, enumerate dimensions first (ons_data.dimensions) to guide valid filters and reduce errors.

## Golden Test Philosophy
Golden tests provide deterministic inputs + mocked upstream responses verifying schema stability and transformation logic. They SHOULD NOT hit live OS APIs.
