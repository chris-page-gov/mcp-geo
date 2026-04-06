---
aliases: [HORIZON Fundamentals, HORIZON Hydraulics, SOILSERIES, soil series, horizon attributes]
tags: [dataset, tabular, series, horizon, attributes, landis]
layer: 3
type: Tabular
key_field: series_code
---

# Horizon Data

> [!info] Dataset Identity
> **Type:** Tabular attribute datasets (soil series + horizon level)
> **Key field:** Series code (4-digit) / Horizon identifier
> **Layer:** 3 — Attributes
> **Linked to:** [[NATMAP Vector]] via NATMAPassociations → SOILSERIES join

## Overview

LandIS holds a rich set of tabular datasets describing soil properties at the **series** and **horizon** level. These tables are the scientific backbone of the system — they encode the physical, chemical, and hydraulic properties that make LandIS useful for engineering, agronomy, hydrology, and environmental modelling.

They are joined to spatial data through [[Data Structure and Joins|the MUSID → NATMAPassociations → SOILSERIES chain]].

---

## SOILSERIES Info

The foundational taxonomy table.

| Field | Content |
|---|---|
| Series code | 4-digit unique identifier |
| Modern definition | Current taxonomic description |
| Typical profile | Horizon sequence and characteristics |
| Classification | National and international (WRB) class |

SOILSERIES Info is described as provided "at no charge" when leased with NATMAP products (historically). It enables any polygon to be "expanded" into its component series for richer attribution.

---

## HORIZON Fundamentals

Detailed physical and chemical properties at horizon level.

| Property Group | Fields |
|---|---|
| Particle size | Clay, silt, sand fractions |
| Organic matter | Organic carbon % |
| Reaction | pH |
| Bulk properties | Bulk density, porosity |
| Taxonomy | Horizon name, depth range |

---

## HORIZON Hydraulics (v2.0, November 2014)

Water retention and hydraulic conductivity at horizon level. Version 2.0 was based on an expanded measured dataset across the UK, using updated predictive equations.

| Property Group | Fields |
|---|---|
| Water retention | Field capacity, wilting point, saturation |
| Hydraulic conductivity | Ksat estimates |
| QA flags | Data quality indicators |

> [!note] Version Note
> HORIZON Hydraulics v2.0 (November 2014) represents a significant update to water retention parameters. Always check version provenance when using for hydrological modelling.

---

## Specialist Series Datasets

Beyond fundamentals and hydraulics, LandIS publishes several specialist series-level datasets:

| Dataset | Content | Primary Use |
|---|---|---|
| SOILSERIES Leacs | Corrosivity to Fe/Zn, shrink-swell class | [[Utilities and Engineering]] — pipe assets |
| SOILSERIES Pesticides | Leaching and runoff vulnerability classes | [[Government and Policy]] — pollution prevention |
| SOILSERIES Hydrology | HOST class, bypass flow, baseflow index, standard % runoff | [[Hydrology and Flood]] — groundwater modelling |
| SOILSERIES Agronomy | Crop suitability, workdays, trafficability | [[Agriculture and Land Management]] |
| Soil Alerts | Flags for acid sulphate peats, groundwater soils, problem horizons | All engineering/ecology uses |
| Auger Bores | >150,000 auger bore observations (>450,000 horizons) | Engineering, land development |

> [!info] Auger Bores
> The auger bore dataset is particularly valuable for engineering and land development because it represents **surveyed information at specific locations** rather than generalised associations. It is the most site-relevant data in LandIS.

---

## MCP Access

Horizon and series data is accessed through derived semantic tools rather than raw table queries:

- `landis_derive_pipe_risk(route)` — uses Leacs data for corrosion/shrink-swell risk
- `landis_natmap_thematic_area_summary(geometry, "carbon")` — draws on carbon horizon fields
- Future: `landis.series.get(series_code)`, `landis.horizon.get(series_code, depth_range)`

---

## Join Chain (Summary)

```
Polygon MUSID
  → NATMAPassociations (series + percentage)
    → SOILSERIES (taxonomy)
      → HORIZON Fundamentals (physical/chemical per layer)
      → HORIZON Hydraulics (water retention per layer)
      → SOILSERIES Leacs (engineering risk)
      → SOILSERIES Pesticides (leaching risk)
      → SOILSERIES Hydrology (flow/drainage)
```

See [[Data Structure and Joins]] for full detail.

---

## Sources
- [LandIS Soil Series: Leacs](https://www.landis.org.uk/data/ssleacs.cfm)
- [LandIS Soil Data Structures PDF](https://www.landis.org.uk/downloads/downloads/Soil%20Data%20Structures.pdf)

---
*← [[00 - Home|Home]]  |  See also: [[Data Structure and Joins]], [[NATMAP Vector]], [[Utilities and Engineering]]*
