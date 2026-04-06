---
aliases: [thematic layers, HOST, Wetness, Carbon, CAW, WRB, derived layers]
tags: [dataset, thematic, derived, HOST, wetness, carbon, landis]
layer: 4
type: Derived polygon layers
---

# Interpreted Layers

> [!info] Layer Identity
> **Type:** Derived thematic polygon layers (NATMAP-based)
> **Layer:** 4 — Interpreted / Actionable
> **Derivation:** Computed from series/horizon attributes and aggregated to NATMAP polygons
> **Output:** Class codes + percentage coverage per polygon

## Overview

The interpreted layers are LandIS's most decision-ready products. They take the raw taxonomy of [[NATMAP Vector]] and the physical/chemical properties of [[Horizon Data]] and synthesise them into **actionable thematic classifications** directly relevant to hydrology, agriculture, engineering, and environmental accounting.

Each layer provides, per polygon: one or more class codes plus the percentage of the polygon area in each class (since multiple series may be present).

---

## HOST — Hydrological Response to Soil Type

> **29 classes, 11 conceptual response models**

HOST classifies soils by their **dominant hydrological response** — how they behave in terms of water movement, routing, and storage. It is derived from combining soil series properties with hydrogeology.

| Field | Content |
|---|---|
| HOST class | 1–29 class code |
| % per polygon | Proportion of each class within the association |
| Baseflow index | Related field in SOILSERIES Hydrology |
| Standard % runoff | Related field |

**Primary uses:**
- Catchment hydrological modelling and calibration
- Flood response prediction
- [[Hydrology and Flood]] — essential for groundwater modelling

**MCP access:** `landis_natmap_thematic_area_summary(geometry, "host")`

---

## NATMAP Wetness

> **6 wetness classes**

Wetness class describes the degree of seasonal waterlogging, based on soil drainage properties. It is a direct input to:

- **Agricultural Land Classification (ALC)** — Defra's grading system for land capability
- Drainage design and land management planning
- Engineering constraint assessment (construction windows, dewatering)

| Wetness Class | Interpretation |
|---|---|
| 1 | Freely draining — rarely waterlogged |
| 2 | Moderately well drained |
| 3 | Imperfect drainage — seasonally wet |
| 4 | Poor drainage — wet for significant periods |
| 5 | Very poor drainage |
| 6 | Extremely poor — almost permanently wet |

**MCP access:** `landis_natmap_thematic_area_summary(geometry, "wetness")`

---

## NATMAP Carbon

> **Multi-depth carbon stock summaries**

NATMAP Carbon provides estimates of **organic carbon stocks** by depth layer:
- 0–30 cm
- 30–100 cm
- 100–150 cm
- Total stock summary

It is derived from horizon carbon data weighted by polygon series composition, and is **explicitly used in the UK Greenhouse Gas Inventory**.

> [!info] Policy Relevance
> NATMAP Carbon is a direct input to the GHG Inventory and underpins policy work on net zero, peatland restoration, and high-carbon soil protection.

**MCP access:** `landis_natmap_thematic_area_summary(geometry, "carbon")`

---

## NATMAP Crop Available Water (CAW)

> **Multiple crop rooting models**

CAW estimates the water available to crops between field capacity and wilting point, computed for different crop rooting depth models. It is a direct input to agricultural land capability assessment and irrigation planning.

**Primary uses:** [[Agriculture and Land Management]] — crop suitability, irrigation, yield modelling

---

## NATMAP WRB

Maps NATMAP soil associations to the international **World Reference Base for Soil Resources (WRB 2006)** classification. This enables comparison with European and global soil datasets.

---

## Summary Comparison

| Layer | Classes | Primary Policy Use | MCP Theme Key |
|---|---|---|---|
| HOST | 29 | Flood / hydrology modelling | `"host"` |
| Wetness | 6 | ALC, drainage, engineering | `"wetness"` |
| Carbon | Continuous | GHG inventory, net zero | `"carbon"` |
| CAW | Continuous | Crop suitability, ALC | `"caw"` |
| WRB | International | Cross-border comparison | — |

---

## MCP Pattern

All thematic layers share the same access pattern:

```
landis_natmap_thematic_area_summary(
  geometry = <polygon/bbox>,
  theme    = "host" | "wetness" | "carbon" | "caw"
)
→ Returns: class breakdown + % coverage + provenance + caveat block
```

The caveat block always includes the 1:250k scale limitation and a "not for site-level decisions" warning.

---

## Sources
- [HOST](https://www.landis.org.uk/data/nmhost.cfm)
- [Wetness](https://www.landis.org.uk/data/nmwetness.cfm)
- [Carbon](https://www.landis.org.uk/data/nmcarbon.cfm)
- [Crop Available Water](https://www.landis.org.uk/data/nmap.cfm)
- [WRB](https://www.landis.org.uk/data/nmwrb.cfm)

---
*← [[00 - Home|Home]]  |  See also: [[NATMAP Vector]], [[Hydrology and Flood]], [[Climate and Carbon]]*
