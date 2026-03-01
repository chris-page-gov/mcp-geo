# Map Lab Help Resources and Tutorial Blueprint (2026-02-28)

## Purpose

This document curates high-quality reference material to design a novice-first
"Map Lab" help experience for learning UK geospatial mapping with Ordnance
Survey and ONS data.

Goals:
- explain web mapping fundamentals clearly
- explain OS/ONS data products and how they connect
- explain operational modes (server-proxy vs direct API)
- support experimentation with styling, overlays, hierarchy-based highlighting
- define Help tab UX expectations (state persistence across tab switches)

## 1) Best Existing Beginner Material (UK-focused)

### Ordnance Survey and ONS first

- OS Docs welcome: https://docs.os.uk/welcome
- OS Vector Tile API getting started: https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api/getting-started
- OS Vector Tile API technical spec: https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api/technical-specification
- OS Vector Tile styles endpoint: https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api/technical-specification/stylesheet
- OS Vector Tile tile endpoint: https://docs.os.uk/os-apis/accessing-os-apis/os-vector-tile-api/technical-specification/tile-request
- OS Places API overview: https://docs.os.uk/os-apis/accessing-os-apis/os-places-api
- OS Places API postcode endpoint (filters, datasets): https://docs.os.uk/os-apis/accessing-os-apis/os-places-api/technical-specification/postcode
- OS Places API UPRN endpoint: https://docs.os.uk/os-apis/accessing-os-apis/os-places-api/technical-specification/uprn
- OS Linked Identifiers API overview: https://docs.os.uk/os-apis/accessing-os-apis/os-linked-identifiers-api
- OS Linked Identifiers available data: https://docs.os.uk/os-apis/accessing-os-apis/os-linked-identifiers-api/what-data-is-available
- OS Features API filtering (attribute + spatial): https://docs.os.uk/os-apis/accessing-os-apis/os-features-api/technical-specification/filtering
- OS Product Archive (historical MasterMap/ITN/UPRN): https://docs.os.uk/os-apis/accessing-os-apis/os-features-api/os-product-archive
- OS NGD unique identifiers (OSID, UPRN, USRN, TOID context): https://docs.os.uk/osngd/getting-started/os-ngd-fundamentals/unique-identifiers
- OS NGD coordinate reference systems: https://docs.os.uk/osngd/getting-started/os-ngd-fundamentals/coordinate-reference-systems
- OS NGD Buildings theme: https://docs.os.uk/osngd/data-structure/buildings
- OS NGD Path Link feature: https://docs.os.uk/osngd/data-structure/transport/transport-network/path-link
- OS NGD Road Link feature: https://docs.os.uk/osngd/data-structure/transport/transport-network/road-link
- OS Open Roads documentation: https://docs.os.uk/os-downloads/products/transport-network-portfolio/os-open-roads
- OS Open Roads feature types (RoadLink/RoadNode/MotorwayJunction): https://docs.os.uk/os-downloads/products/transport-network-portfolio/os-open-roads/os-open-roads-overview/feature-types
- OS Open UPRN overview: https://docs.os.uk/os-downloads/products/addresses-and-names-portfolio/os-open-uprn/os-open-uprn-overview
- OS Open UPRN technical spec: https://docs.os.uk/os-downloads/identifiers/os-open-uprn/os-open-uprn-technical-specification
- Code-Point Open documentation: https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/code-point-open
- Code-Point Open product details: https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/code-point-open/code-point-open-overview/product-details
- Boundary-Line data overview (admin/electoral boundaries): https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/boundary-line/boundary-line-overview/data-overview
- Boundary-Line principles and feature coverage: https://docs.os.uk/os-downloads/addressing-and-location/boundary-line/boundary-line-product-information/boundary-line-principles-and-features

- ONS Geography landing page: https://www.ons.gov.uk/methodology/geography
- ONS Open geography framework: https://www.ons.gov.uk/methodology/geography/geographicalproducts/opengeography
- ONS Geographical products catalogue: https://www.ons.gov.uk/methodology/geography/geographicalproducts
- ONS Statistical geographies (OA/LSOA/MSOA): https://www.ons.gov.uk/methodology/geography/ukgeographies/statisticalgeographies
- ONS Other geographies (includes built-up areas): https://www.ons.gov.uk/methodology/geography/ukgeographies/othergeographies
- ONS Electoral geographies: https://www.ons.gov.uk/methodology/geography/ukgeographies/ukelectoralgeography
- ONS England administrative geography details: https://www.ons.gov.uk/methodology/geography/ukgeographies/administrativegeography/england
- ONS names/codes administrative geographies: https://www.ons.gov.uk/methodology/geography/geographicalproducts/namescodesandlookups/namesandcodeslistings/namesandcodesforadministrativegeography?lang=english
- ONS names/codes electoral geographies: https://www.ons.gov.uk/methodology/geography/geographicalproducts/namescodesandlookups/namesandcodeslistings/namesandcodesforelectoralgeography
- ONS names/codes OAs/LSOAs/MSOAs: https://www.ons.gov.uk/methodology/geography/geographicalproducts/namescodesandlookups/namesandcodeslistings/namesandcodesforsuperoutputareassoa
- ONS lookups overview: https://www.ons.gov.uk/methodology/geography/geographicalproducts/namescodesandlookups/lookups
- ONS postcode products (ONSPD/NSPL): https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts
- ONS UK parliamentary constituencies guidance: https://www.ons.gov.uk/methodology/methodologicalpublications/generalmethodology/ukparliamentaryconstituencies
- ONS built-up areas methodology context: https://www.ons.gov.uk/peoplepopulationandcommunity/housing/articles/townsandcitiescharacteristicsofbuiltupareasenglandandwales/census2021
- ONS Beginner's Guide dataset listing: https://www.data.gov.uk/dataset/9d00e352-e578-414a-8f94-ebf7ff983acb/a-beginners-guide-to-uk-geography-20231

## 2) Core Web Mapping Fundamentals (platform-agnostic)

- MapLibre GL JS introduction: https://maplibre.org/maplibre-gl-js/docs
- MapLibre examples index: https://maplibre.org/maplibre-gl-js/docs/examples/
- MapLibre style specification: https://maplibre.org/maplibre-style-spec/
- MapLibre expressions (zoom-driven styling): https://maplibre.org/maplibre-style-spec/expressions/
- MapLibre layers spec: https://maplibre.org/maplibre-style-spec/layers/
- MapLibre 3D buildings example: https://maplibre.org/maplibre-gl-js/docs/examples/display-buildings-in-3d/
- MapLibre hover/feature-state example: https://maplibre.org/maplibre-gl-js/docs/examples/hover-styles/
- MapLibre polygon draw example: https://maplibre.org/maplibre-gl-js/docs/examples/draw-polygon-with-mapbox-gl-draw/
- OSM slippy map tile naming (z/x/y): https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
- RFC 7946 GeoJSON standard: https://datatracker.ietf.org/doc/html/rfc7946
- Mapbox Vector Tile spec (MVT): https://mapbox.github.io/vector-tile-spec/
- OGC API Tiles standard: https://www.ogc.org/standards/ogcapi-tiles

## 3) Data Engineering and Querying Fundamentals (for advanced lab tracks)

- PostGIS ST_Intersects (point-in-polygon and intersection workflows): https://www.postgis.net/docs/manual-3.0/ST_Intersects.html
- PostGIS ST_AsMVT (serve vector tiles from DB): https://postgis.net/docs/ST_AsMVT.html
- OGC GeoPackage standard overview: https://www.geopackage.org/spec140/
- QGIS training manual (structured GIS learning): https://docs.qgis.org/3.40/en/docs/training_manual/
- QGIS export/save layers guidance: https://documentation.qgis.org/latest/en/docs/user_manual/managing_data_source/create_layers.html

## 4) Accessibility and State-Preserving Help UI Patterns

For the Help tab and collapsible tutorial sections:

- W3C ARIA Tabs pattern: https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
- MDN ARIA tab role: https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Reference/Roles/tab_role
- W3C Disclosure pattern: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/
- MDN details element: https://developer.mozilla.org/ms/docs/Web/HTML/Element/details
- MDN HTMLDetailsElement API: https://developer.mozilla.org/en-US/docs/Web/API/HTMLDetailsElement
- MDN Web Storage API (persist fold/tab state): https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API
- MDN History scrollRestoration: https://developer.mozilla.org/en-US/docs/Web/API/History/scrollRestoration
- web.dev tabs component architecture: https://web.dev/articles/building/a-tabs-component

## 5) Statistical Data APIs for Geography + Indicators

- ONS developer observations guide: https://developer.ons.gov.uk/observations/
- Nomis API documentation: https://www.nomisweb.co.uk/api

## 6) Tutorial Information Architecture for "Welcome to Map Lab"

Recommended top-level help sections (novice-first):

1. Welcome to Map Lab
- What this lab is for
- What you can build in 15 minutes
- Two modes of operation (server-proxy mode vs direct API mode)

2. How Web Maps Work
- Basemap, source, layer, style
- Raster vs vector tiles
- Why zoom changes what you should draw
- CRS basics (EPSG:27700, EPSG:3857, EPSG:4326)

3. UK Geography Primer
- OA, LSOA, MSOA
- Wards, parishes, LADs, constituencies
- Built-up areas
- Why boundaries do not always nest cleanly

4. Identifier Primer
- UPRN, USRN, TOID, OSID
- Linking identifiers across products
- Why identifiers are better than names for joins

5. Primary Hierarchy Display Strategy
- At high zoom: UPRN points, building polygons, local detail
- Mid zoom: building emphasis + selected links
- Low zoom: RoadLink/PathLink/USRN-oriented emphasis + area summaries
- Explain this as cartographic generalisation, not "losing" data

6. Postcode Parallel Stream
- Postcode to area/statistical linkage via ONSPD/NSPL
- UPRN-centred postcode highlighting approaches
- Address filtering options and caveats

7. Styling and Cartography Lab
- Opacity/fade controls
- Contrast and legibility
- Symbology choices by geometry type
- Hover/selection semantics
- 2D and 3D buildings

8. Build Your Own Collections
- Add/remove features
- Group into collections
- Save/load/export (GeoJSON/GeoPackage where relevant)
- Reproducible state snapshots

9. Troubleshooting
- No map tiles (proxy/API key/mode mismatch)
- Missing layer data
- CRS mismatch symptoms
- 401/403/429 quick fixes

10. Glossary
- Novice-friendly definitions with one-line examples

## 7) Help Tab Behavior Requirements (stateful learning UX)

To meet your requirement that users can leave Help and return exactly where they were:

Persist at minimum:
- active help tab id
- scroll position per tab
- open/closed state per disclosure section
- expanded/collapsed table of contents state
- last viewed tutorial step

Suggested persistence keys:
- `maplab.help.activeTab`
- `maplab.help.scroll.<tabId>`
- `maplab.help.section.<sectionId>.open`
- `maplab.help.lastStep`

Behavior contract:
- when map rendering auto-switches to Map tab, keep Help tab state untouched
- when switching back to Help tab, restore tab + scroll + fold states before paint
- do not reset state on soft refresh unless explicitly requested
- provide "Reset tutorial state" button for support/debugging

## 8) Mode Explanation Block (must appear near top of Help)

This should be explicit for novices:

- Server-proxy mode (recommended):
  - browser talks to local MCP server (`/maps/...`)
  - server injects credentials
  - key is not shown in UI payloads

- Direct API mode (advanced):
  - browser talks directly to external API
  - credentials are handled client-side
  - higher exposure risk and stricter browser/CORS constraints

- How to verify current mode:
  - check tile/style request host in network panel
  - local host implies proxy mode

## 9) Gaps to Fill in Map Lab Help Content

High-priority authored content needed (repo-specific, not solved by external links):
- "What this app is doing" architecture diagram tied to your current endpoints
- explicit examples of your primary hierarchy transitions by zoom band
- postcode highlighting strategy options with pros/cons
- practical recipes ("highlight all UPRNs in this postcode", "fade basemap to 35%", "switch to road-link emphasis")
- "save collections" UX guide tied to actual project behavior

## 10) Recommended Next Build Step

Create a first in-app Help draft with:
- a fixed left Table of Contents
- sectioned content using native disclosure elements
- persistent state via localStorage
- automatic map-tab switch that does not disturb Help state
- one complete beginner walkthrough end-to-end (15-minute path)

