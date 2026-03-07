# Teignmouth Peninsula Building Profile Brief (2026-03-06)

## Objective

Define a reproducible south-of-railway area of interest for the Teignmouth
peninsula, identify the MCP-Geo data that can support a detailed building
profile, and specify a practical infographic set that can be produced from the
available layers.

## Evidence Used

- User-provided screenshot showing the peninsula width and the intended
  "south of the railway line" scope.
- Prior session output in
  `/Users/crpage/Library/CloudStorage/OneDrive-Personal/!NotebookLM Sources/MCP and Context Engineering/Example use of MCP-Geo.docx`,
  which captured live Clampet Lane and Orchard Gardens road/building context
  around Stanley House.
- Live MCP-Geo queries on 2026-03-06 against rail, tidal boundary, building,
  building-part, road-link, path-link, and administrative-area tools.

## Study Area

The area below is an operational extraction polygon for the peninsula south of
the railway. It is not an official cadastral or administrative boundary.

- The north edge follows OS rail detail.
- The east, south, and west edges are approximated from tidal boundary
  geometry and then manually closed back to the rail line.
- It is suitable for repeatable profiling and infographic production.

```json
{
  "type": "Polygon",
  "coordinates": [[
    [-3.50072, 50.54703],
    [-3.49992, 50.54720],
    [-3.49888, 50.54736],
    [-3.49732, 50.54764],
    [-3.49572, 50.54804],
    [-3.49423, 50.54830],
    [-3.49241, 50.54864],
    [-3.49101, 50.54899],
    [-3.49057, 50.54836],
    [-3.49166, 50.54725],
    [-3.49223, 50.54667],
    [-3.49244, 50.54593],
    [-3.49304, 50.54536],
    [-3.49430, 50.54456],
    [-3.49500, 50.54377],
    [-3.49555, 50.54310],
    [-3.49649, 50.54254],
    [-3.49759, 50.54190],
    [-3.49821, 50.54165],
    [-3.49906, 50.54202],
    [-3.49991, 50.54065],
    [-3.50072, 50.54079],
    [-3.50095, 50.54180],
    [-3.50060, 50.54320],
    [-3.49986, 50.54502],
    [-3.50030, 50.54610],
    [-3.50072, 50.54703]
  ]]
}
```

## Exact Layer Counts

| Layer | Collection / tool | Exact count | Interpretation |
| --- | --- | ---: | --- |
| Buildings | `bld-fts-building-4` | 743 | Whole building footprints |
| Building parts | `bld-fts-buildingpart-2` | 915 | Finer-grained massing and use units |
| Road links | `trn-ntwk-roadlink-5` | 297 | Carriageway network segments |
| Path links | `trn-ntwk-pathlink-3` | 254 | Pedestrian permeability network |

Derived metrics:

- Building parts per building: `915 / 743 = 1.23`
- Additional parts beyond the whole-building count: `172`
- Practical implication: most peninsula buildings are still readable at whole
  footprint level, but there are enough split or compound structures to justify
  separate part-level massing and use graphics.

## Geographic Context Caveat

Sampled points across the peninsula fall within:

- `OA E00102658`, `E00102659`, `E00102660`, and `E00102662`
- `Ward Teignmouth West` and `Ward Teignmouth East`
- `LSOA Teignbridge 010B`
- `MSOA Teignbridge 010`

Implication:

- ONS or NOMIS data can provide neighbourhood context.
- ONS or NOMIS outputs should not be presented as exact peninsula values.
- Any census panel should be clearly labelled as surrounding small-area context.

## What MCP-Geo Can Contribute

| Data source | What it is good for | High-value fields or outputs | Notes |
| --- | --- | --- | --- |
| `bld-fts-building-4` | Whole-footprint inventory | footprint area, part count, roof shape/material, construction material, basement presence, address counts, some age and height fields | Best denominator for "how many buildings" |
| `bld-fts-buildingpart-2` | Fine-grained massing and use | `height_relativemax_m`, `height_absolutemax_m`, `height_roofbase_m`, footprint area, `address_primarydescription`, `address_secondarydescription`, associated structure, containing site count | Best layer for skyline, complexity, mixed-use, and frontage narratives |
| `trn-ntwk-roadlink-5` | Street character | hierarchy, classification, length, average/minimum width, pavement extent/width, lighting, directionality, bus/cycle lane presence, gradient | Strongest layer for street-form infographics |
| `trn-ntwk-pathlink-3` | Permeability | paths, steps, subways, footbridges, route connectivity, elevation change | Useful for walkability and shortcuts |
| `os_map.inventory` | Addresses grouped to buildings in a bounded area | road-fronting UPRNs, grouped building summaries, road adjacency | Better fallback than relying on a single polygon address query |
| `os_places.within` or tiled postcode/address extraction | Address intensity | UPRNs, classification codes, residential/commercial mix | Polygon path returned zero in this session, so use tiled extraction |
| `admin_lookup`, `ons_*`, `nomis_*` | Context only | OA/LSOA/ward lookup and census variables | Use in a separate contextual panel |

## Notable Live Signals

These are useful anchor examples for annotations or callouts.

### Road-width contrasts

- `Exeter Road` roundabout segment: about `16.3 m` average width
- `South View`: about `15.3 m`
- `Brunswick Street`: about `12.1 m`
- `Clampet Lane`: about `3.1 m`
- `Ivy Lane`: about `3.6 m`

These extremes are good evidence for a "tight lanes versus broad approach
streets" story.

### Taller building-part examples

- `osgb1000012331727`: residential, footprint `139.753 m2`,
  relative max height `16.7 m`, absolute max height `21.2 m`
- `osgb1000012352403`: mixed / unknown artificial, footprint `513.977 m2`,
  relative max height `14.7 m`
- `osgb1000012331534`: mixed use, footprint `82.347 m2`,
  relative max height `11.6 m`

These examples show that the peninsula has enough height variation to justify a
dedicated built-form panel rather than a flat footprint-only map.

### Clampet Lane / Orchard Gardens precedent

The prior live session showed that MCP-Geo can already resolve:

- narrow lane geometry (`Clampet Lane` around `3.4 m` average width)
- broader nearby street context (`Orchard Gardens` around `7.5 m`)
- building-part heights and footprints
- address ambiguity / dual-road context around Stanley House

That precedent is directly relevant to peninsula-wide work because it shows that
MCP-Geo is strong at frontage, road-context, and block-level building analysis.

## Recommended Infographic Set

### 1. Peninsula at a glance

Purpose:
- Establish the AOI and the scale of the profiling pack.

Use:
- AOI polygon
- rail line
- `743` buildings
- `915` building parts
- `297` road links
- `254` path links

Recommended visuals:
- one locator map with the railway clearly marked as the north boundary
- four KPI tiles
- one small comparison bar showing buildings versus building parts

### 2. Built form and skyline

Purpose:
- Show where the peninsula is flat, where it steps up, and where complex
  building groups sit.

Primary layer:
- `bld-fts-buildingpart-2`

Recommended visuals:
- footprint map shaded by height band
- histogram of relative maximum height
- scatter plot of footprint area versus relative maximum height

Why this matters:
- Part-level heights are much richer than footprint-only counts.
- This panel is the best way to communicate form rather than just density.

### 3. Street character

Purpose:
- Compare narrow historic lanes, commercial core streets, and wider approach
  roads.

Primary layer:
- `trn-ntwk-roadlink-5`

Recommended visuals:
- ranked bar chart of street segments by average width
- map of road links symbolised by width band
- callouts for lighting, pavement provision, and two-way or constrained links

Anchor contrasts:
- `Clampet Lane` and `Ivy Lane` versus `Exeter Road`, `South View`, and
  `Brunswick Street`

### 4. Frontage and address intensity

Purpose:
- Show how strongly buildings front onto streets and where address density
  concentrates.

Primary layers:
- `os_map.inventory`
- tiled `os_places.within`
- optionally `bld-fts-building-4`

Recommended visuals:
- frontage-density bars by street
- grouped building summaries for selected blocks
- highlighted case studies where one building cluster relates to multiple roads

Caveat:
- This is spatial frontage context, not proof of legal access rights.

### 5. Use mix and active edges

Purpose:
- Show where the peninsula is mainly residential and where mixed, retail,
  leisure, community, or transport activity clusters.

Primary layer:
- `bld-fts-buildingpart-2`

Recommended visuals:
- stacked bars by broad use group
- footprint map highlighting mixed or non-residential parts
- zone comparison chart for west harbour, central core, east seafront, and
  south tip

Important handling:
- Keep an explicit `Unknown / Unclassified` bucket.
- Exclude or separately mark shelters, archways, piers, and lighthouse-like
  structures when the narrative is about occupied buildings.

### 6. Movement and permeability

Purpose:
- Explain how easy it is to cross or move through the peninsula on foot.

Primary layers:
- `trn-ntwk-roadlink-5`
- `trn-ntwk-pathlink-3`

Recommended visuals:
- simplified network diagram
- map of path links over the road skeleton
- small chart for steps, subways, or path-heavy connectors if they prove dense

### 7. Edge conditions

Purpose:
- Compare the harbour edge, central town fabric, beach edge, and southern tip.

Suggested zones:
- west harbour / port edge
- central commercial core
- east seafront edge
- south peninsula tip

Recommended visuals:
- four small multiples using the same scale
- one comparison table for median height, typical road width, part density, and
  address intensity

Reason to use zones:
- The peninsula is narrow and elongated, so zonal comparison will read more
  clearly than one overloaded whole-area map.

### 8. Census context panel

Purpose:
- Add social or housing context without pretending that boundary data is exact
  to the peninsula footprint.

Use:
- `admin_lookup`
- `ons_*`
- `nomis_*`

Recommended visuals:
- one compact contextual panel only
- dwelling type, tenure, occupancy, or room-count context for the sampled OAs
  or `LSOA Teignbridge 010B`

Labelling rule:
- Must be presented as surrounding-area context, not peninsula extract.

## Visual Design Rules

- Keep whole-building and part-level graphics separate.
- Keep the railway line and AOI outline visible on every map page.
- Use small multiples instead of stacking too many variables on one map.
- Avoid pie charts for use mix; sorted bars and banded footprint maps will read
  better.
- Use annotation callouts for the strongest contrasts rather than overlabelling
  every feature.
- Use one consistent palette family for built form, another for movement, and a
  neutral palette for contextual panels.

## What To Avoid Overclaiming

- `buildingpart` is not the same denominator as `building`.
- Address or road context does not prove legal access.
- ONS and NOMIS data do not map exactly to the peninsula footprint.
- Entrance-point or building-access layers should not be made central until a
  tighter extract shows they are complete enough to trust.

## Suggested Production Workflow

1. Freeze the operational polygon and use it consistently.
2. Extract whole buildings, building parts, road links, and path links first.
3. Run a separate tiled address workflow for UPRNs and frontage density.
4. Create a small number of derived metrics:
   - parts per building
   - height bands
   - footprint-size bands
   - road-width bands
   - frontage density per street
5. Design as a sequence of separate infographics, not one dashboard.

## Recommended First Deliverable

The best first infographic pair is:

1. `Peninsula at a glance`
2. `Built form and skyline`

That pair uses the strongest exact counts, the cleanest polygon, and the most
distinctive MCP-Geo data without depending on boundary-based census proxies or
address-query edge cases.
