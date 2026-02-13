# External Scan: OS Documentation, Ecosystem, and Mapping MCP Servers

## Ordnance Survey official materials reviewed

### API and onboarding docs

- [OS APIs getting started](https://docs.os.uk/getting-started/apis)
- [OS Maps API getting started](https://docs.os.uk/os-apis/accessing-os-apis/os-maps-api/getting-started)
- [OS Features API](https://docs.os.uk/os-apis/accessing-os-apis/os-features-api)
- [OS Vector Tile API](https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api)
- [OS Vector Tile API technical specification](https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api/technical-specification)
- [OS Downloads](https://docs.os.uk/os-downloads)

### OS GitHub assets and examples

- [OS vector tile stylesheets repo](https://github.com/OrdnanceSurvey/os-vector-tile-api-stylesheets)
- [OS Data Hub API demos](https://github.com/OrdnanceSurvey/OS-Data-Hub-API-Demos)
- [OrdnanceSurvey GitHub organization](https://github.com/OrdnanceSurvey)

### Key findings from OS sources

1. OS documentation already supports multiple map access patterns (vector, raster, features, downloads), which aligns with a layered MCP delivery strategy.
2. OS vector tile stylesheet assets provide a practical bridge for QGIS and web clients when used via descriptors.
3. Technical references emphasize API-key-backed runtime access, reinforcing the need for server-side key handling and client-safe placeholders.

## Broader mapping library landscape reviewed

- [MapLibre GL JS docs](https://maplibre.org/maplibre-gl-js/docs/)
- [MapLibre CSP guidance](https://maplibre.org/maplibre-gl-js/docs/guides/csp/)
- [OpenLayers docs](https://openlayers.org/doc/)
- [Leaflet docs](https://leafletjs.com/)
- [deck.gl docs](https://deck.gl/docs)
- [CesiumJS docs](https://cesium.com/learn/cesiumjs/)
- [Mapbox vector tile specification](https://github.com/mapbox/vector-tile-spec)
- [GeoJSON RFC 7946](https://www.rfc-editor.org/rfc/rfc7946)

### Key findings for client compatibility

1. MapLibre remains a strong default for vector tile rendering in browser-based widgets.
2. OpenLayers is attractive where strict standards interoperability is prioritized.
3. Leaflet remains useful for lightweight raster and marker-centric scenarios.
4. Deck.gl and Cesium are better treated as advanced/optional layers due to complexity and runtime overhead.

## Map server and GIS deployment options reviewed

- [GeoServer user manual](https://docs.geoserver.org/latest/en/user/)
- [MapServer docs](https://mapserver.org/documentation.html)
- [QGIS documentation](https://qgis.org/resources/documentation/)
- [QGIS Server docs](https://docs.qgis.org/latest/en/docs/server_manual/)
- [TileServer GL](https://github.com/maptiler/tileserver-gl)
- [Martin tile server](https://maplibre.org/martin/)
- [pg_tileserv](https://github.com/CrunchyData/pg_tileserv)
- [Tegola docs](https://tegola.io/documentation/)
- [TiTiler docs](https://developmentseed.org/titiler/)
- [PMTiles docs](https://docs.protomaps.com/pmtiles/)

### Key findings for containerized MCP integration

1. Sidecar tile/feature servers are feasible as optional profile-based services for high-scale deployments.
2. `pg_tileserv`/`Martin`/`Tegola` are strong candidates for PostGIS-native vector tile serving.
3. GeoServer and QGIS Server are stronger for enterprise OGC compliance and existing GIS admin teams.
4. PMTiles is strong for offline/edge delivery where bandwidth is constrained.

## OGC and interoperability standards reviewed

- [OGC API Features](https://www.ogc.org/standards/ogcapi-features/)
- [OGC WMTS](https://www.ogc.org/standards/wmts/)

These standards support a resilient MCP strategy where tool outputs can degrade from interactive widgets to standards-based service descriptors and static assets.

## Open-source mapping MCP servers reviewed

- [Model Context Protocol servers index](https://github.com/modelcontextprotocol/servers)
- [Official server catalog (includes Google Maps remote MCP endpoint)](https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md)
- [MCP Mapbox server (official repo path)](https://github.com/modelcontextprotocol/servers/tree/main/src/mapbox)
- [Community Google Maps MCP server](https://github.com/LouieR3d/mcp-google-map)
- [Community mapbox MCP server](https://github.com/haasonsaas/mcp-server-mapbox)
- [Community OpenStreetMap MCP server](https://github.com/bingal/mcp-server-openstreetmap)
- [MCP Apps map server example](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/map-server)

### MCP server ecosystem findings

1. Existing map MCP servers typically expose geocoding/search and rendering-adjacent tools rather than full GIS orchestration.
2. UI-host variability is common, so robust fallbacks are essential (text + static image + resource links).
3. `mcp-geo` is already ahead in combining map display, administrative geography, and statistical integration in one server.

## Operational policy references

- [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/)

This reinforces the importance of cache, user-agent identification, and respectful tile-request behavior for fallback map routes.
