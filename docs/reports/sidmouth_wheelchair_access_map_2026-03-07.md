# Sidmouth wheelchair access map

Generated artefacts:

- HTML map: `docs/reports/sidmouth_wheelchair_access_map_2026-03-07.html`
- JSON export: `data/exports/sidmouth_wheelchair_access_map_2026-03-07.json`
- PNG render: `output/playwright/sidmouth-wheelchair-access-map-2026-03-07.png`

## Scope

This map is a conservative town-centre access aid for a powered wheelchair user in Sidmouth.
It uses live MCP-Geo extracts from `2026-03-07` and focuses on what the current data can validate:

- road links with recorded pavement width and pavement coverage
- path links with path type, surface, lighting coverage, and elevation gain
- pavement polygons for pedestrian-realm context
- rail and water geometry for orientation
- exact named anchors from search tools

The HTML report also includes an optional `OS Detailed` basemap toggle. That layer loads
browser-side from Ordnance Survey as the `OS_VTS_3857_Light.json` vector style when the
user supplies an OS Maps API key locally, and the browser view supports wheel zoom,
drag pan, and sharper building-level context as the user zooms in.

It does **not** claim to validate dropped kerbs, crossing design, tactile paving, camber,
temporary obstructions, parked cars, café furniture, or works on the day.

## Current MCP-Geo data used

Primary map layers:

- `trn-ntwk-roadlink-5`
- `trn-ntwk-pathlink-3`
- `trn-fts-roadtrackorpath-3` filtered to `Pavement`
- `trn-fts-cartographicraildetail-1`
- `wtr-fts-water-3`
- `os_poi.search`
- OS vector style `OS_VTS_3857_Light.json` in the HTML view only, when a browser key is
  supplied, with browser-side zoom and pan for sharper street and building context

## Live findings from this extract

Area used: `[-3.2445, 50.676, -3.233, 50.6826]`

Counts:

- `237` road links
- `140` path links
- `85` pavement polygons
- `0` rail-detail features
- `12` water features

Accessible-network summary:

- Preferred route length: `1.26 km`
- Use-with-care route length: `5.68 km`
- Barrier length shown on the map: `0.44 km`

Named sections that read best in the current data:

- Preferred roads: `The Esplanade`, `All Saints Road`, `Station Road`
- Preferred paths: `EAST STREET`
- Use-with-care roads: `Station Road`, `Peak Hill Road`, `The Esplanade`, `All Saints Road`, `Mill Street`
- Use-with-care paths: `Church Lane`, `Church Path`, `Heydon's Lane`, `RIVERSIDE`, `HEYDONS LANE`
- Recorded barrier paths: No stable named segments cleared this category in the current extract.

Anchor-point check:

- `Tourist Information Centre` is about `5 m` from the nearest cleared route segment.
- `Sidmouth Market` is about `12 m` from the nearest cleared route segment.

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
