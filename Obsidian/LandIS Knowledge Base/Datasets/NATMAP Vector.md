---
aliases: [NATMAPvector, National Soil Map, NATMAP]
tags: [dataset, polygon, natmap, landis]
layer: 2
scale: "1:250,000"
coverage: "England and Wales"
format: Vector polygon
---

# NATMAP Vector

> [!info] Dataset Identity
> **Type:** National polygon soil map
> **Scale:** 1:250,000
> **Units:** ~300 soil associations
> **SRS:** British National Grid
> **Redigitised:** 1999, registered to OS 1:50,000 base

## What It Is

NATMAP Vector is the core national soil map for England and Wales. It is the "most detailed" of four versions of the National Soil Map, derived from 60+ years of soil survey fieldwork. Each polygon represents a **soil association** — a named mapping unit containing a mixture of soil series occurring in a characteristic pattern.

The dataset is the principal entry point into the LandIS data hierarchy. Without NATMAP, the attribute tables ([[Horizon Data]], interpreted layers, series properties) have no spatial anchor.

## Data Structure

The key identifier is the **MUSID** (Mapping Unit ID), which links polygons outward to all attribute tables.

```
NATMAPvector polygon
    └─ MUSID
        └─ NATMAPlegend  (association names, descriptions)
            └─ NATMAPassociations  (lists component series + percentages)
                └─ SOILSERIES  (taxonomy, series definition)
                    └─ HORIZON Fundamentals / Hydraulics
```

See [[Data Structure and Joins]] for the full join model.

## Derived Products

| Product | Description |
|---|---|
| Soilscapes | Simplified 27-class generalisation for awareness purposes → [[Soilscapes]] |
| NATMAP 1K | 1km² grid vector — series-based, flat table, for easy querying |
| NATMAP 2K / 5K | Coarser grid versions with series proportions per cell |
| NATMAP Carbon | Carbon stocks by depth layer → [[Interpreted Layers]] |
| NATMAP Wetness | 6 wetness classes for ALC and constraint mapping → [[Interpreted Layers]] |
| NATMAP HOST | 29 hydrological response classes → [[Interpreted Layers]] |
| NATMAP CAW | Crop available water for rooting models → [[Interpreted Layers]] |
| NATMAP WRB | Mapping to international WRB 2006 classes |

## Scale and Generalisation Constraints

> [!warning] Critical Limitation
> NATMAP polygons are **sweeping generalisations**. Each association typically contains multiple soil series, and within-polygon variability can be high. The 1:250,000 scale means it is **not suitable for site-level decisions** (planning applications, site investigations, engineering design). Field validation is always required for fine-grained use.

## MCP Access

**Primary tool:** `landis_natmap_point(lat, lon)` → returns MUSID, association label, and provenance
**Area summary:** `landis_natmap_area_summary(geometry)` → percent area by association
**Thematic summary:** `landis_natmap_thematic_area_summary(geometry, theme)` → e.g. wetness, HOST, carbon
**Series lookup:** `landis_natmap_point` → then use MUSID to call series tools

## Key Use Cases
- [[Government and Policy]] — ALC, NCEA, land-use planning
- [[Agriculture and Land Management]] — soil suitability, drainage design
- [[Utilities and Engineering]] — corrosion/shrink-swell screening on routes
- [[Climate and Carbon]] — carbon stock screening via NATMAP Carbon

## Sources
- [LandIS NATMAP page](https://www.landis.org.uk/data/natmap.cfm)
- [data.gov.uk NATMAP record](https://www.data.gov.uk/dataset/ea1442bf-ba77-42cc-80e7-2ea339ccb28a/natmap-national-soil-map1)
- [[Data Structure and Joins]] — Soil Data Structures PDF

---
*← [[00 - Home|Home]]*
