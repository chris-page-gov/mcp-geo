# OS Catalog Review and MCP Delivery Plan (2026-02-12)

## Scope

This report reviews `/Users/crpage/repos/mcp-geo/resources/os_catalog.json`, identifies what is currently used in the repository runtime, and proposes a practical delivery model for large datasets under MCP payload limits (around 1MB), including delayed download workflows, cache options, and QGIS linkage.

## Inputs Reviewed

- `/Users/crpage/repos/mcp-geo/resources/os_catalog.json`
- `/Users/crpage/repos/mcp-geo/scripts/os_catalog_refresh.py`
- `/Users/crpage/repos/mcp-geo/tools/os_common.py`
- `/Users/crpage/repos/mcp-geo/tools/os_places.py`
- `/Users/crpage/repos/mcp-geo/tools/os_places_extra.py`
- `/Users/crpage/repos/mcp-geo/tools/os_poi.py`
- `/Users/crpage/repos/mcp-geo/tools/os_names.py`
- `/Users/crpage/repos/mcp-geo/tools/os_linked_ids.py`
- `/Users/crpage/repos/mcp-geo/tools/os_features.py`
- `/Users/crpage/repos/mcp-geo/tools/os_vector_tiles.py`
- `/Users/crpage/repos/mcp-geo/server/maps_proxy.py`
- `/Users/crpage/repos/mcp-geo/tools/os_map.py`
- `/Users/crpage/repos/mcp-geo/tools/ons_data.py`
- `/Users/crpage/repos/mcp-geo/server/mcp/resource_catalog.py`

## Catalog Classification and Documentation Ordering

### Category order in `os_catalog.json`

The catalog items are presented in this order:

1. `search`
2. `features`
3. `maps`
4. `downloads`
5. `positioning`

### Category sizes

- `search`: 14 probes
- `features`: 94 probes
- `maps`: 9 probes
- `downloads`: 57 probes
- `positioning`: 4 probes
- Total: 178 probes

### Documentation ordering pattern

Each API family consistently links docs in this sequence:

1. `overview`
2. `gettingStarted`
3. `technicalSpecification`

Distinct docs families referenced:

- `places`
- `names`
- `linkedIdentifiers`
- `match`
- `wfs`
- `ofa` (NGD OGC API Features)
- `wmts`
- `vts`
- `ota` (NGD tiles)
- `downloads`

## What Is Used in Repo Runtime

This section is focused on runtime MCP server usage (tool handlers and proxy routes), not catalog refresh scripts.

### Coverage summary vs catalog

- Catalog probes matched by current runtime behavior: **103 / 178**
- Not currently wired via MCP runtime tools/proxy behavior: **75 / 178**

Matched by category:

- `features`: 92
- `search`: 8
- `maps`: 3

Unmatched by category:

- `downloads`: 57
- `search`: 6
- `maps`: 6
- `positioning`: 4
- `features`: 2

### Actively used OS endpoint families

- Places:
  - `/search/places/v1/find`
  - `/search/places/v1/postcode`
  - `/search/places/v1/uprn`
  - `/search/places/v1/nearest`
  - `/search/places/v1/bbox`
- Names:
  - `/search/names/v1/find`
  - `/search/names/v1/nearest`
- Linked IDs:
  - `/search/links/v1/identifierTypes/{type}/{id}`
- NGD Features:
  - `/features/ngd/ofa/v1/collections`
  - `/features/ngd/ofa/v1/collections/{collection}/items`
- Vector Tiles:
  - `/maps/vector/v1/vts`
  - `/maps/vector/v1/vts/resources/styles`
  - `/maps/vector/v1/vts/tile/{z}/{y}/{x}.pbf`

### Catalog gaps (implemented in code but absent from catalog)

- `/features/ngd/ofa/v1/collections/{collection}/queryables` is used by `os_features.query` (`includeQueryables=true`) but currently missing from `os_catalog.json`.

## High-value Catalog Areas Not Yet Wired to MCP Tools

- Search:
  - Places `radius`, `polygon`
  - Linked IDs `identifiers`, `featureTypes`, `productVersionInfo`
  - Match & Cleanse `match`
- Features:
  - WFS capabilities and WFS archive capabilities
- Maps:
  - Raster WMTS/ZXY
  - NGD OTA tiles endpoints
- Downloads:
  - Entire downloads surface (products, product metadata, product downloads, dataPackages, openapi)
- Positioning:
  - Entire OS Net probe set

## Commonality and Duplication: NGD vs Other Sources

The catalog naturally groups by transport/protocol, but user questions are usually domain-first. A domain view highlights overlap:

### Address and identifiers

- Live query APIs:
  - Places API (address lookup/search)
  - Linked IDs API (crosswalk between UPRN/USRN/TOID)
- Bulk/snapshot equivalents:
  - `OpenUPRN`, `OpenUSRN`, `OpenTOID`, `LIDS` via Downloads
- Recommendation:
  - Use live APIs for lookup and conversational QA.
  - Use bulk downloads for background enrichment/index builds.

### Named features

- Live query APIs:
  - Names API
  - NGD `gnm-*` collections (via OFA)
- Bulk/snapshot equivalent:
  - `OpenNames` via Downloads
- Recommendation:
  - Prefer Names API for lightweight name search.
  - Use NGD collections when geometry/attributes are needed.

### Transport network

- Live query APIs:
  - NGD `trn-*` collections via OFA
- Tile representation:
  - OTA/VTS for rendering
- Bulk/snapshot equivalent:
  - `OpenRoads` download product
- Recommendation:
  - OFA for analytics/filtering.
  - OTA/VTS for map display.
  - Downloads for offline joins and heavy batch workflows.

### Boundaries and admin geography

- Current repo uses ArcGIS-driven admin lookup and boundary cache pipeline.
- Catalog includes Boundary-Line downloads product.
- Recommendation:
  - Boundary-Line should become a first-class bulk source in the same cache/delivery model.

## Large Dataset and 1MB MCP Limit: Current State

Existing patterns already in repo:

- UI payload guardrail:
  - `tools/os_apps.py` enforces `~950KB` max tool response budget.
- Progressive disclosure:
  - `os_places.within` tiles/clamps over-large bboxes.
  - `os_features.query` supports `limit` + `nextPageToken`.
- Resource-backed output for large results:
  - `ons_data.get_filter_output` supports `delivery=resource|auto`.
  - Exports written to `data/ons_exports/` and read via `resource://mcp-geo/ons-exports/...`.

These patterns are the right base to apply to OS datasets.

## Recommended Delivery Model for OS Downloads and Large NGD Results

### 1) Add OS bulk export tools with async/resource delivery

Introduce tools aligned with current ONS export style:

- `os_downloads.list_products`
- `os_downloads.list_product_downloads`
- `os_downloads.prepare_export` (request definition + async job metadata)
- `os_downloads.get_export` (returns `resourceUri` + metadata)

Back these tools with OS Downloads API capabilities already in the catalog:

- `/downloads/v1/products`
- `/downloads/v1/products/{productId}`
- `/downloads/v1/products/{productId}/downloads`
- `/downloads/v1/dataPackages`

Suggested delayed-access control flow:

1. Validate request (product, area, format, entitlement).
2. Create/track a package request (`dataPackages` where supported).
3. Persist a local job record (status, requester, expiry).
4. Return small MCP payload (`jobId`, `state`, `pollAfterMs`).
5. On completion, return `resourceUri` and cache metadata (bytes, checksum, expiry).

Key behavior:

- Default `delivery=auto`.
- Inline only when payload is small.
- Large content always returned via resource URI.

### 2) Add a dedicated OS cache root (external storage friendly)

Add config such as:

- `OS_DATA_CACHE_DIR` (default `data/cache/os`)
- `OS_DATA_CACHE_TTL`
- `OS_DATA_CACHE_SIZE_GB` or file-count cap

If you mount external storage, point `OS_DATA_CACHE_DIR` to the mounted path.

### 3) Persist metadata + integrity

For each cached artifact store:

- source URL
- dataset/product identifiers
- retrieved timestamp
- content type/format
- byte size
- checksum (`sha256`)
- staleness status

Expose this via resources, similar to `ons-cache-index` and `ons-exports-index`.

### 4) Enforce payload-size controls uniformly

Apply the same size-guard idea across all high-volume tools:

- hard max response bytes
- downgrade to resource URI response when exceeded
- emit explicit `delivery`, `bytes`, and `contentTruncated` metadata

This is consistent with the pattern used by database-focused MCP servers: results are discoverable via metadata and fetched through controlled follow-up reads, not pushed inline as a single oversized payload.

## Format Suitability for Caching

### Recommended by use case

- Conversational + API round-trips:
  - JSON summaries + resource URI to full file
- QGIS-ready vector storage:
  - GeoPackage (`.gpkg`) as default
- Streaming web/map delivery:
  - Vector tiles (`.pbf` via VTS/OTA), optionally PMTiles if introduced later
- Large analytics pipelines:
  - Parquet/GeoParquet as an additional export option (if needed for Python/duckdb workloads)

### Practical default choices now

- For geospatial feature exports: **GeoPackage first**, GeoJSON optional for small extracts.
- For tabular extracts: CSV/JSON inline for small; file-backed for large.
- Avoid Shapefile as default due file fragmentation and schema limits.

## QGIS Linkage Strategy

There is already a strong starting point:

- Vector tile styles repo vendored at:
  - `/Users/crpage/repos/mcp-geo/submodules/os-vector-tile-api-stylesheets`
- QGIS `.qml` styles included:
  - `/Users/crpage/repos/mcp-geo/submodules/os-vector-tile-api-stylesheets/QGIS Stylesheets (QML)/`

Recommended integration paths:

1. VTS in QGIS (EPSG:3857) using existing `.qml` styles.
2. MCP-generated GeoPackage exports for analysis layers.
3. Optional: add tool outputs that include a QGIS-friendly connection descriptor (layer URL/resource URI, CRS, style hint).

## Discoverability Improvements (Catalog + Tool UX)

To make MCP question-answering more reliable, add catalog metadata fields:

- `surface`: `live_query`, `tiles`, `bulk_download`, `positioning`
- `domain`: `address`, `transport`, `names`, `water`, `land`, `boundaries`, `imagery`, `positioning`
- `preferredFor`: short list of user intents
- `overlapsWith`: explicit cross-links (for duplication awareness)
- `deliveryHint`: `inline_safe`, `paged`, `resource_required`

Then use these fields in:

- `/tools/search` ranking
- `os_mcp.route_query` guidance
- fallback recommendations when response-size limits are likely

## Concrete Next Actions

1. Add catalog probe(s) for NGD queryables:
   - `/features/ngd/ofa/v1/collections/{collection}/queryables`
2. Implement first OS downloads read-only tools:
   - list products
   - list product downloads
3. Add OS export cache path config and index resource:
   - mirror `ons-exports-index` pattern for OS
4. Add `delivery=resource|auto` semantics to any OS tool that can exceed safe payload size.
5. Add one QGIS-oriented export path:
   - GeoPackage output + metadata resource URI.
