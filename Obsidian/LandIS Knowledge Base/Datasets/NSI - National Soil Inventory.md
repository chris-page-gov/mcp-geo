---
aliases: [NSI, National Soil Inventory, Topsoil83, Topsoil95]
tags: [dataset, point, monitoring, NSI, chemistry, landis]
layer: 1
type: Point monitoring grid
spacing: 5km
coverage: "England and Wales"
sampling_periods: ["~1980", "mid-1990s"]
---

# NSI — National Soil Inventory

> [!info] Dataset Identity
> **Type:** Systematic point monitoring — 5km grid
> **Coverage:** England and Wales
> **Sampling:** Initial ~1980 (Topsoil83), partial resample mid-1990s (Topsoil95)
> **Content:** Site + profile data, topsoil chemistry (20+ elements + pH), textures, features
> **Standard:** INSPIRE Annex III Soil exemplary case study

## What It Is

The NSI is a **statistically representative** national monitoring dataset providing point observations of topsoil conditions across England and Wales. Sampled on a systematic 5km grid, it enables geostatistical analysis and trend mapping across the country. It is the principal source for national-scale soil carbon trend monitoring and is used by academic researchers and government bodies alike.

Each point records:
- Site information (location, land use, parent material indicators)
- Profile description
- Topsoil chemistry: >20 elements including carbon, nitrogen, phosphorus, pH, heavy metals
- Texture classes
- Features including a **flood-risk indicator**

## Sampling Periods

| Name | Period | Notes |
|---|---|---|
| Topsoil83 | ~1980 | Initial national survey |
| Topsoil95 | mid-1990s | Partial resample — not all sites revisited |

The time gap between samples makes NSI the primary evidence base for detecting national-scale soil change — most famously the landmark *Nature* paper documenting carbon losses across England and Wales (1978–2003).

## Key Capabilities

- Geostatistical trend mapping of soil chemistry
- National benchmarking of topsoil carbon, pH, heavy metals
- Flood risk indicator at point locations
- Input to national carbon accounting and the Greenhouse Gas Inventory

## Critical Structural Note

> [!important] NSI is self-standing
> NSI is **not designed to be joined** to NATMAP or other Cranfield tabular datasets. It uses its own identifier scheme and is queried independently. See [[Data Structure and Joins]].

## MCP Access

**Nearest sites:** `landis_nsi_nearest_sites(lat, lon, n)` → nearest N NSI monitoring points with distance
**Profile summary:** `landis_nsi_profile_summary(site_id, year)` → chemistry summary for a site
**Area query:** `landis_nsi_within_area(geometry)` → all NSI sites within a polygon, with aggregated statistics and sampling density caveat

> [!warning] Density Caveat
> NSI points are spaced 5km apart. Any area smaller than ~25km² may contain zero or very few points, making area statistics unreliable. Always include a sampling density note in outputs.

## Use Cases

- [[Climate and Carbon]] — carbon trend analysis, GHG inventory inputs
- [[Government and Policy]] — monitoring for NCEA, nature recovery
- [[Academic Research]] — peer-reviewed geostatistical studies
- [[Agriculture and Land Management]] — regional soil chemistry benchmarking

## Academic Record

NSI data underpins numerous peer-reviewed studies including:
- The widely-cited *Nature* (2005) paper on England and Wales carbon losses
- National-scale geostatistical monitoring studies across multiple chemistry parameters

It has been adopted by INSPIRE Annex III Soil technical working groups as an exemplary case study for soil monitoring deployment.

## Sources
- [LandIS NSI page](https://www.landis.org.uk/data/nsi.cfm)
- INSPIRE Annex III Soil documentation

---
*← [[00 - Home|Home]]  |  See also: [[Climate and Carbon]], [[Data Structure and Joins]]*
