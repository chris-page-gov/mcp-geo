# Exmouth wheelchair access map

Generated artefacts:

- HTML map: `docs/reports/exmouth_wheelchair_access_map_2026-03-07.html`
- JSON export: `data/exports/exmouth_wheelchair_access_map_2026-03-07.json`
- PNG render: `output/playwright/exmouth-wheelchair-access-map-2026-03-07.png`

## Scope

This map is a conservative town-centre access aid for a powered wheelchair user in Exmouth.
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

Area used: `[-3.4215, 50.6095, -3.396, 50.6238]`

Counts:

- `910` road links
- `532` path links
- `276` pavement polygons
- `3` rail-detail features
- `10` water features

Accessible-network summary:

- Preferred route length: `5.32 km`
- Use-with-care route length: `18.90 km`
- Barrier length shown on the map: `2.60 km`

Named sections that read best in the current data:

- Preferred roads: `Victoria Road`, `Cyprus Road`, `Esplanade`, `Queens Drive`, `Dagmar Road`
- Preferred paths: `BEACH GARDENS`, `MANOR GARDENS`, `CHAPEL STREET`, `Magnolia Walk`, `THE STRAND`
- Use-with-care roads: `Queens Drive`, `Marine Way`, `Salterton Road`, `Rosebery Road`, `Imperial Road`
- Use-with-care paths: `Madeira Walk`, `MANOR GARDENS`, `Lime Kiln Lane`, `PLANTATION WALK`, `BATH ROAD`
- Recorded barrier paths: `Fair View Terrace`, `Madeira Walk`, `Henrietta Place`, `PLANTATION WALK`, `ALBION TERRACE`

Anchor-point check:

- `Exmouth railway station` is about `22 m` from the nearest cleared route segment.
- `Exmouth indoor market` is about `28 m` from the nearest cleared route segment.

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
