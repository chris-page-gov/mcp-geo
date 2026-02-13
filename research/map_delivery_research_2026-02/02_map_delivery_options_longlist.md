# Map Delivery Options Longlist

## Delivery channels considered

1. Static image URL (`/maps/static/osm`) from tool response.
2. Tool-generated static descriptor + client-side map rendering.
3. Interactive MCP-App widget (`ui://` resources).
4. Resource-backed GeoJSON layers with client rendering.
5. Vector tile style + tile template descriptors (`os_vector_tiles.descriptor`).
6. WMTS capability + tile access (`os_maps.wmts_capabilities`, `os_maps.raster_tile`).
7. WFS/OGC API Features discovery + filtered retrieval.
8. QGIS profile/descriptor outputs (`os_qgis.*`).
9. Export-oriented handoff (GeoPackage descriptor + resource URI).
10. Notebook-native map exploration (Jupyter + ipyleaflet/folium style pattern).
11. Hosted map-server composition (GeoServer/MapServer/QGIS Server/TiTiler/Martin/Tegola/pg_tileserv).
12. Offline-first packaging (MBTiles/PMTiles + lightweight local viewer).

## Longlist matrix

| Option | Industry standards | Strengths | Risks/constraints | Persona fit |
| --- | --- | --- | --- | --- |
| Static image URL from MCP tool | HTTP + PNG/JPEG | Works in most AI clients and browsers; low payload complexity | Limited interactivity; annotation complexity | A, C, E, F |
| MCP-App widget (MapLibre) | MCP Apps + vector/raster tiles | Rich interaction and overlays | Host UI support varies across clients | B, D, E |
| GeoJSON resource delivery | RFC 7946 | Portable and inspectable; GIS-friendly | Large payload risk without paging/resource mode | B, D, E |
| Vector tile descriptor | Mapbox style spec + MVT | Scalable cartography and smooth pan/zoom | Requires style/worker/glyph compatibility | B, D, E |
| WMTS/ZXY raster path | WMTS, XYZ | Mature, broad compatibility | Less semantic interactivity than vector features | A, C, D |
| WFS/OFA capabilities path | OGC API Features / WFS | Query precision and enterprise interop | Schema and pagination complexity | B, D, E |
| QGIS descriptor outputs | OGR/GPKG + style hints | Direct analyst workflow handoff | Requires desktop GIS familiarity | D, B |
| Notebook map workflow | Jupyter ecosystem | Transparent analysis + reproducibility | Not ideal for casual public users | B, D, E |
| Hosted map server sidecar | OGC APIs / tile services | Enterprise deployment and caching control | Operational overhead and infra skills | D, E |
| PMTiles/MBTiles distribution | PMTiles/MBTiles | Great offline and edge distribution | Build pipeline and update process required | C, D, E |

## Skeletal map response systems for MCP clients

These are lightweight contracts for clients with weak or no map UI support.

### Skeleton A: `map_card`

- fields: `title`, `bbox`, `center`, `imageUrl`, `summaryText`, `nextActions`
- purpose: immediate visual + textual context for public users

### Skeleton B: `geography_selector_stub`

- fields: `availableLevels`, `selectedAreaIds`, `queryHints`, `fallbackTools`
- purpose: minimal selection workflow even when embedded widgets are unsupported

### Skeleton C: `overlay_bundle`

- fields: `baseMap`, `overlayCollections`, `resourceUris`, `bytes`, `provenance`
- purpose: robust app integration path for developers and GIS users

### Skeleton D: `export_handoff`

- fields: `descriptorType`, `resourceUri`, `targetCRS`, `importSteps`
- purpose: bridge from conversational output to desktop GIS execution

## Candidate delivery stack patterns

### Pattern 1: Public-safe default

- `os_maps.render` for immediate image output
- optional overlay summary and area list
- escalation path to interactive widget only when supported

### Pattern 2: Analyst mode

- `os_features.query` / `admin_lookup.*` for boundary semantics
- resource-backed GeoJSON + tabular outputs
- notebook + GIS export path

### Pattern 3: GIS mode

- `os_qgis.vector_tile_profile`
- `os_qgis.export_geopackage_descriptor`
- optional sidecar map server for enterprise scale

### Pattern 4: AI-client compatibility-first

- startup with `starter` toolset and static map skeleton
- defer heavy discovery and UI payloads
- always include text fallback and resource URI references

## Containerized server architecture variants considered

### Variant A: In-process map server module inside `mcp-geo`

- Description: expand FastAPI app to include richer tile/feature-serving endpoints.
- Benefit: single deployment unit and simpler local startup.
- Tradeoff: larger blast radius, tighter coupling, and harder independent scaling.

### Variant B: Sidecar map server in same container stack

- Description: keep MCP orchestration in `mcp-geo`, delegate heavy map serving to sidecars.
- Candidate sidecars: GeoServer, QGIS Server, Martin, pg_tileserv, Tegola, TiTiler.
- Benefit: clearer scaling boundaries and specialist-optimized serving paths.
- Tradeoff: extra operational complexity and service coordination.

### Variant C: QGIS fork as service core

- Description: fork QGIS codebase to expose MCP-specific map behaviors directly.
- Benefit: deep GIS feature control.
- Tradeoff: unsustainable maintenance burden versus using stable upstream QGIS/QGIS Server interfaces.
- Decision: not selected for implementation; descriptor-first QGIS integration is preferred.
