# Teignmouth wheelchair access map

Generated artefacts:

- HTML map: `docs/reports/teignmouth_wheelchair_access_map_2026-03-07.html`
- JSON export: `data/exports/teignmouth_wheelchair_access_map_2026-03-07.json`
- PNG render: `output/playwright/teignmouth-wheelchair-access-map-2026-03-07.png`

## Scope

This map is a conservative town-centre access aid for a powered wheelchair user in Teignmouth.
It uses live MCP-Geo extracts from `2026-03-07` and focuses on what the current data can validate:

- road links with recorded pavement width and pavement coverage
- path links with path type, surface, lighting coverage, and elevation gain
- pavement polygons for pedestrian-realm context
- rail and water geometry for orientation
- exact named anchors from search tools

The HTML report also includes an optional `OS Light` basemap toggle. That layer loads
browser-side from Ordnance Survey when the user supplies an OS Maps API key locally,
and the browser view supports wheel zoom, drag pan, and higher-detail tile refresh as
the user zooms in.

It does **not** claim to validate dropped kerbs, crossing design, tactile paving, camber,
temporary obstructions, parked cars, café furniture, or works on the day.

## Current MCP-Geo data used

Primary map layers:

- `trn-ntwk-roadlink-5`
- `trn-ntwk-pathlink-3`
- `trn-fts-roadtrackorpath-3` filtered to `Pavement`
- `trn-fts-cartographicraildetail-1`
- `wtr-fts-water-3`
- `os_places.search`
- OS `Light_3857` raster tiles in the HTML view only, when a browser key is supplied,
  with browser-side tile refresh on zoom for sharper street context

## Live findings from this extract

Area used: `[-3.5025, 50.5405, -3.4905, 50.5495]`

Counts:

- `422` road links
- `306` path links
- `145` pavement polygons
- `58` rail-detail features
- `10` water features

Accessible-network summary:

- Preferred route length: `2.84 km`
- Use-with-care route length: `4.17 km`
- Barrier length shown on the map: `1.25 km`

Named sections that read best in the current data:

- Preferred roads: `Den Crescent`, `Bitton Park Road`, `Promenade`, `Higher Brook Street`, `Powderham Terrace`
- Preferred paths: `OSMONDS LANE`, `BATH TERRACE`, `Regents Gardens`, `FRENCH STREET`, `CLAMPET LANE`
- Use-with-care roads: `Promenade`, `Brunswick Street`, `Powderham Terrace`, `Salisbury Terrace`, `Strand`
- Use-with-care paths: `Riverside Walk`, `The Mews`, `Sun Lane`, `Commercial Road`, `CLAY LANE`
- Recorded barrier paths: `Mulberry Street`, `WILLOW STREET`, `Riverside Walk`, `SPERANZA GROVE`

Anchor-point check:

- `Teignmouth station` is about `26 m` from the nearest cleared route segment.
- `Shopmobility` is about `27 m` from the nearest cleared route segment.

That means the current route filter is useful for planning within the core, but the final approach to
those anchor points still needs an on-the-ground crossing and kerb check.

## Filtering logic used

Road links:

- `Preferred`: recorded pavement, minimum width at least `1.2 m`, average pavement width at least
  `1.8 m`, pavement coverage at least `80%`, gentle grade under `3%`, and mostly or fully lit
- `Use with care`: minimum width at least `1.0 m`, average pavement width at least `1.4 m`,
  pavement coverage at least `60%`, and grade up to `5%`
- `Context only`: anything else, including steep or missing pavement evidence

Path links:

- `Preferred`: `Path`, `Made Sealed`, under `3%`, and mostly or fully lit
- `Use with care`: plain `Path` up to `5%`, including unlit or less certain surfaces
- `Barrier`: `Path With Steps`, `Footbridge`, `Subway`, or grade above `5%`

These thresholds are deliberately stricter than “can a chair physically squeeze through”.
`iLevel` is a seating system across multiple Quantum chair bases, so the map uses public-realm
guidance rather than assuming one exact chair width.

Reference guidance:

- GOV.UK, *Inclusive Mobility*: <https://www.gov.uk/government/publications/inclusive-mobility-making-transport-accessible-for-passengers-and-pedestrians>
- Active Travel England inclusive design guidance: <https://www.activetravelengland.gov.uk/>
- Quantum Rehab `iLevel` product family: <https://www.quantumrehab.com/>

## What MCP-Geo should consider adding

Highest-value additions for a real disabled-navigation product:

1. Dropped kerbs and crossing metadata:
   kerb height, flush status, tactile paving, crossing type, refuge islands, signal control.
2. Accessible parking:
   Blue Badge bays, step-free access from car parks, payment constraints, and surface type.
3. Public transport accessibility:
   bus stop locations, raised kerbs, shelter availability, route identifiers, and timetable / GTFS links.
4. Rest and support points:
   public toilets, benches, Changing Places toilets, pharmacies, charging points, and mobility support.
5. Temporary and environmental constraints:
   works, diversions, flood / overtopping risk, and tide-sensitive waterfront access.
6. Better amenity categorisation:
   category-coded tourist and daily-life destinations instead of broad text search alone.
