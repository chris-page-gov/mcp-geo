---
aliases: [join model, MUSID, NATMAPassociations, data structure, LandIS joins]
tags: [dataset, structure, joins, schema, landis]
---

# Data Structure and Joins

> [!abstract] The Central Challenge
> LandIS data is organised as a **relational hierarchy** connecting spatial polygons to tabular series and horizon attributes via linking tables. Understanding the join model is essential for correct data use — and it is the primary source of "technical friction" for non-GIS users. The MCP semantic layer exists specifically to abstract this complexity.

## The Four-Layer Architecture

![[UK Soil Data Engine Infographic.png]]

```
─────────────────────────────────────────────────────────
Layer 4  │  Interpreted Layers  │  HOST · Wetness · Carbon · CAW
         │  (thematic, derived)  │  ← aggregated from series via polygon
─────────────────────────────────────────────────────────
Layer 3  │  Attributes           │  SOILSERIES · HORIZON Fundamentals
         │  (tabular, keyed)     │  HORIZON Hydraulics · Leacs · Pesticides
─────────────────────────────────────────────────────────
Layer 2  │  NATMAP Polygons      │  ~300 associations · 1:250k scale
         │  (spatial)            │  keyed by MUSID
─────────────────────────────────────────────────────────
Layer 1  │  NSI Points           │  5km grid · chemistry · self-standing
         │  (independent)        │  NOT designed to join to above tables
─────────────────────────────────────────────────────────
```

---

## The Polygon → Series → Horizon Join Chain

This is the core relational model. All attribute queries start from a spatial polygon.

```
NATMAPvector polygon
    MUSID (mapping unit code)
        │
        ▼
    NATMAPlegend          ← association name, description, MUSID
        │
        ▼
    NATMAPassociations    ← links MUSID to component SERIES_CODEs + percentage
        │
        ▼
    SOILSERIES            ← series definition, taxonomy (keyed by SERIES_CODE)
        │
        ├─▶ HORIZON Fundamentals   (particle size, OC, pH, bulk density, porosity)
        ├─▶ HORIZON Hydraulics     (water retention, Ksat — v2.0 Nov 2014)
        ├─▶ SOILSERIES Leacs       (corrosivity to Fe/Zn, shrink-swell)
        ├─▶ SOILSERIES Pesticides  (leaching/runoff vulnerability)
        ├─▶ SOILSERIES Hydrology   (HOST, bypass flow, BFI, % runoff)
        └─▶ SOILSERIES Agronomy    (workdays, trafficability, crop suitability)
```

## Key Tables and Their Roles

| Table | Key Field | Role |
|---|---|---|
| NATMAPvector | MUSID | Spatial polygon anchor |
| NATMAPlegend | MUSID | Association names and descriptions |
| NATMAPassociations | MUSID + SERIES_CODE | Bridge: polygon to series, with % |
| SOILSERIES | SERIES_CODE | Taxonomy and series definition |
| HORIZON Fundamentals | SERIES_CODE + horizon ID | Physical/chemical per layer |
| HORIZON Hydraulics | SERIES_CODE + horizon ID | Water retention per layer |
| SOILSERIES Leacs | SERIES_CODE | Corrosion/shrink-swell |
| SOILSERIES Pesticides | SERIES_CODE | Leaching vulnerability |
| SOILSERIES Hydrology | SERIES_CODE | HOST, flow parameters |

---

## NSI: The Exception

> [!important] NSI Does Not Join
> The National Soil Inventory ([[NSI - National Soil Inventory|NSI]]) is explicitly documented as **self-standing** — it is not designed to be joined to the NATMAP polygon system or the series/horizon tables. NSI uses its own point identifiers and is accessed independently.

---

## The Aggregation Problem

When computing weighted averages across a polygon (e.g. mean organic carbon), you must:

1. Retrieve all component series from NATMAPassociations (with their percentages)
2. Look up the relevant horizon properties for each series
3. Weight each value by the series percentage

This is non-trivial and introduces uncertainty because:
- Series percentages are typical, not measured at the specific location
- Within-series variability is not captured
- Missing data for some series may skew results

> [!question] Open Question
> What are the recommended aggregation defaults (dominant series vs weighted average), and how should uncertainty be represented? See [[Open Questions]].

---

## Why This Matters for MCP

The join complexity is the primary barrier for non-GIS users. An MCP server can:

1. **Hide the joins** — tools accept coordinates/polygons and return semantically meaningful outputs
2. **Encode aggregation logic** — apply weighted averages internally with documented defaults
3. **Surface uncertainty** — return confidence notes alongside values
4. **Attach provenance** — every output includes dataset version, MUSID, series codes used

See [[MCP Overview]] and [[Primitive Tools]] for how this is implemented.

---

## Technical Friction: The Usability Gap

The Soilscapes brochure and multiple other sources document the challenge: raw series joins are "highly complex for non-GIS developers, requiring relational mastery of mapping unit keys." This is the core problem the MCP server solves.

> [!quote] From the report
> "The dataset family design (associations → series → horizons) makes LandIS particularly suitable for 'semantic tooling' that turns specialist data structures into decision-relevant explanations."

---

## Sources
- [LandIS Soil Data Structures PDF](https://www.landis.org.uk/downloads/downloads/Soil%20Data%20Structures.pdf)
- [LandIS Data Families page](https://www.landis.org.uk/data/datafamilies.cfm)

---
*← [[00 - Home|Home]]  |  See also: [[NATMAP Vector]], [[Horizon Data]], [[MCP Overview]]*
