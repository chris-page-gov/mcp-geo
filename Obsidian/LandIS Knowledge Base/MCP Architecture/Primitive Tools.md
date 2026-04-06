---
aliases: [primitive tools, MCP tools, spatial tools, landis tools]
tags: [mcp, tools, api, spatial, landis]
---

# Primitive Tools

> [!info] Design Principle
> Primitive tools are **deterministic and low-level**. They return structured JSON with explicit provenance. They shield users from data formats, coordinate systems, and join complexity — but do not interpret the results. Interpretation is the role of [[Derived Semantic Tools]].

## Currently Active Tools

These tools are live on the connected MCP server:

### Dataset Discovery

| Tool | Returns |
|---|---|
| `landis_catalog_list_products()` | Available layers, coverage, spatial type, scale/resolution, last-updated, access tier |
| `landis_metadata_get(product_id)` | ISO metadata and provenance narrative for a specific dataset |

### Point Lookup

| Tool | Returns |
|---|---|
| `landis_soilscapes_point(lat, lon)` | Soilscape class + key attributes + uncertainty note |
| `landis_natmap_point(lat, lon)` | Soil association (MUSID) + association label + legend link |

**Note:** Also accepts OSGB easting/northing. Always returns a provenance block including dataset version and scale caveat.

### Area Summary

| Tool | Returns |
|---|---|
| `landis_soilscapes_area_summary(geometry)` | % area by soilscape class for a polygon/bbox |
| `landis_natmap_area_summary(geometry)` | % area by association; optionally dominant association |
| `landis_natmap_thematic_area_summary(geometry, theme)` | Thematic breakdown (HOST, wetness, carbon, CAW) for an area |

**Theme values:** `"host"`, `"wetness"`, `"carbon"`, `"caw"`

### NSI (Point Monitoring)

| Tool | Returns |
|---|---|
| `landis_nsi_nearest_sites(lat, lon, n)` | Nearest N NSI monitoring sites with distance and sampling year |
| `landis_nsi_profile_summary(site_id, year)` | Chemistry summary for a specific NSI site and year |
| `landis_nsi_within_area(geometry)` | All NSI points within a polygon, with aggregated stats + density caveat |

> [!important] NSI Density Caveat
> All NSI area queries must include a sampling density note. The 5km grid means that small areas may contain zero or very few points.

### Archive Access

| Tool | Returns |
|---|---|
| `landis_archive_list_items()` | List of available archive items |
| `landis_archive_get_item(item_id)` | Retrieve a specific archive item |

### Derived Risk Tool

| Tool | Returns |
|---|---|
| `landis_derive_pipe_risk(route_geometry)` | Corrosion and shrink-swell risk segments along a route |

*This is also documented under [[Derived Semantic Tools]] as it includes semantic interpretation.*

---

## Proposed Additional Primitive Tools

These are documented in the MCP strategy but not yet implemented:

### Classification and Code Lookup

```
landis.classification.soilscape(code)
→ name, description, typical texture/drainage/carbon/habitats

landis.classification.host(class_id)
→ HOST class definition, response model

landis.classification.wetness(class_id)
→ Wetness class definition and drainage interpretation
```

### Association-to-Series Expansion

```
landis.natmap.association_series(musid)
→ Component series + expected percentage (from NATMAPassociations)
```

*Enables deeper queries by exposing the series composition of a polygon.*

### Series and Horizon Profile

```
landis.series.get(series_code)
→ Modern definition, taxonomy, classification

landis.horizon.get(series_code, landuse_group, depth_range)
→ Horizon fundamentals/hydraulics summarised with QA flags
```

---

## Output Format

Every primitive tool response includes:

```json
{
  "result": { ... },
  "provenance": {
    "dataset": "NATMAPvector",
    "version": "...",
    "scale": "1:250,000",
    "accessed": "2026-04-06"
  },
  "caveats": [
    "This dataset is generalised at 1:250,000 scale.",
    "Not suitable for site-level decisions without field investigation.",
    "Licence: portal.landis.org.uk/licence"
  ]
}
```

---

## Geometry Input Formats

Tools accept:
- `lat, lon` (WGS84 decimal degrees)
- `easting, northing` (OSGB36)
- Postcode (resolved to centroid)
- GeoJSON polygon
- Bounding box `[minx, miny, maxx, maxy]`

---

## Related Notes
- [[Derived Semantic Tools]] — tools that interpret primitive outputs
- [[Resources and Prompts]] — static knowledge assets
- [[Data Structure and Joins]] — the underlying data model

---
*← [[00 - Home|Home]]  |  See also: [[MCP Overview]], [[Derived Semantic Tools]]*
