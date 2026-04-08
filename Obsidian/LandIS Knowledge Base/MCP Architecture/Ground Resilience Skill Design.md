---
aliases: [resilience skill, ground failure skill, infrastructure skill, skill design]
tags: [mcp, skill, design, infrastructure, resilience, ground-failure, climate]
status: draft-validated
test_area: Warwickshire corridor
---

# Ground Resilience Skill Design

> [!info] Skill Purpose
> A composable MCP skill that screens any UK road, rail, or utility corridor for climate-driven ground failure risk — combining LandIS soil data, OS infrastructure geometry, BGS geohazards, and UKCP18 climate projections into a structured, auditable risk output that any AI agent or analyst can query.

---

## Skill Identity

```yaml
name: ground-resilience
version: 0.1.0-draft
author: Landis/OS/BGS composite
trigger_phrases:
  - "ground failure risk"
  - "infrastructure resilience"
  - "shrink-swell risk"
  - "embankment stability"
  - "climate risk to buried assets"
  - "soil risk for [road/rail/pipeline/cable/pylon]"
  - "earthworks assessment"
  - "climate adaptation [infrastructure type]"
toolsets_required:
  - landis_soils
  - features_layers
  - admin_boundaries
external_apis:
  - BGS GeoSure (ogcapi.bgs.ac.uk)
  - EA Flood Zones (environment.data.gov.uk)
  - UKCP18 (ukclimateprojections-ui.metoffice.gov.uk)
  - EGMS InSAR (egms.land.copernicus.eu) [optional]
```

---

## Inputs

| Parameter | Type | Description | Required |
|---|---|---|---|
| `geometry` | GeoJSON / postcode / place name / bbox | The area, corridor, or route to assess | Yes |
| `infrastructure_type` | enum | `road`, `rail`, `pipeline`, `cable`, `pylon`, `all` | No (default: all) |
| `risk_modes` | enum[] | `shrink_swell`, `slope`, `settlement`, `scour`, `all` | No (default: all) |
| `time_horizon` | enum | `current`, `2050`, `2080` | No (default: current + 2050) |
| `output_format` | enum | `summary`, `detailed`, `json`, `checklist` | No (default: summary) |

---

## Step-by-Step Execution

### Step 1 — Resolve Geometry
```
If input is a place name or postcode:
  → os_places.search() or os_places.by_postcode()
  → admin_lookup.find_by_name() if administrative area
  → resolve to bbox or polygon

If input is a corridor description (e.g. "M40 between Warwick and Banbury"):
  → os_names.find() to locate endpoints
  → os_route.get() for route geometry
  → buffer route by [50m / 250m / 500m] depending on infrastructure type
```

### Step 2 — Asset Inventory (OS NGD)
```
Query in parallel:

trn-ntwk-roadlink-5 (bbox)
  → filter: roadClassification IN [Motorway, A Road, B Road]
  → count and classify strategic road assets

trn-ntwk-railwaylink-1 (bbox)
  → count rail links and link sets

lnd-fts-landform-1 (bbox)
  → filter: description = "Artificial Slope For Transport"
  → *** HIGHEST PRIORITY FEATURES — embankments and cuttings ***
  → count and flag locations

trn-rami-routingstructure-1 (bbox)
  → filter: type IN [Bridge, Tunnel]
  → inventory of hydraulic structures (scour risk)

wtr-ntwk-waterlink-2 (bbox)
  → identify watercourse crossings
  → flag proximity of embankments to watercourses
```

> [!important] The Earthwork Intersection
> The most valuable analysis step is crossing `lnd-fts-landform-1` ("Artificial Slope For Transport") with the LandIS soil data. An embankment sitting on high-plasticity clay = high shrink-swell risk. An embankment with high wetness class soil = high slip risk. This intersection is the primary risk signal.

### Step 3 — Soil Characterisation (LandIS)
```
Primary (warehouse, if available):
  landis_natmap_thematic_area_summary(geometry, "natmap-subsoil-texture")
  landis_natmap_thematic_area_summary(geometry, "natmap-carbon")
  landis_natmap_thematic_area_summary(geometry, "natmap-available-water")

Fallback (if warehouse offline — use archive ArcGIS REST, CONFIRMED LIVE April 2026):
  Base: https://services-eu1.arcgis.com/BsCa1SurMySYByZ3/arcgis/rest/services/
  GET /NATMAPsubsoiltexture/FeatureServer/0/query?geometry=...    [19,973 polygons]
  GET /NATMAPsubstratetexture/FeatureServer/0/query?geometry=...  [19,751 polygons]
  GET /NATMAPavailablewater/FeatureServer/0/query?geometry=...    [38,097 polygons]
  GET /NATMAPtopsoiltexture/FeatureServer/0/query?geometry=...   [38,102 polygons]
  GET /NATMAPassociations/FeatureServer/0/query?...               [join table]
  GET /AUGERsite/FeatureServer/0/query?geometry=...              [140,902 pts]
  Total archive: 178 Feature Services confirmed (April 2026)

Wetness and HOST (always from archive — not in thematic API):
  GET /NATMAP2000/FeatureServer/0/query?geometry=...
  → join to NATMAPassociations → SOILSERIES for wetness/HOST

Site observations (AUGERsite — where available):
  GET /AUGERsite/FeatureServer/0/query?geometry=...&distance=500
  → ground-truth soil type at specific locations
```

**Soil Risk Scoring (subsoil texture → shrink-swell proxy):**

| Subsoil Texture | Shrink-Swell Proxy Score | Notes |
|---|---|---|
| Heavy clay (>50% clay) | 5 / Very High | London Clay, Lias, Oxford Clay |
| Clay (35–50%) | 4 / High | Mercia Mudstone, Gault Clay |
| Clay loam (27–35%) | 3 / Medium | Mixed geology |
| Silty clay loam | 2 / Low-Medium | Variable |
| Sand / gravel / peat | 1 / Low (but settlement risk for peat) | Check carbon layer |

### Step 4 — BGS Geohazard Classification
```
BGS OGC API (CONFIRMED: ogcapi.bgs.ac.uk, OGL licence, © UKRI):
  Swagger: https://ogcapi.bgs.ac.uk/openapi
  WMS fallback: data.gov.uk/dataset/4997fbf6-e3f8-4bbd-bdf9-7c582addbf94
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Shrink_Swell/items?bbox=...&f=json
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Landslide/items?bbox=...&f=json
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Compressible_Ground/items?bbox=...&f=json
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Collapsible_Deposits/items?bbox=...&f=json
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Dissolution/items?bbox=...&f=json
  GET https://ogcapi.bgs.ac.uk/collections/GeoSure_Running_Sand/items?bbox=...&f=json
  Resolution: 1:50,000 — significantly better than LandIS 1:250,000
  Susceptibility: A (very low) → E (very high)

BGS National Landslide Database:
  GET ogcapi.bgs.ac.uk/collections/landslideindex/items?bbox=...
  → count historical events within 1km of corridor
  → flag any events within 100m of known assets
```

**GeoSure Shrink-Swell Classes:**
| Class | Description | Infrastructure Risk |
|---|---|---|
| 5 — Very High | Very high volume change | Highest priority investigation |
| 4 — High | High volume change | Field verification required |
| 3 — Moderate | Moderate volume change | Monitor |
| 2 — Low | Low volume change | Low concern |
| 1 — Very Low | Negligible change | Background |

### Step 5 — Hydrological Context (EA + LandIS)
```
EA Flood Zones:
  GET environment.data.gov.uk/spatialdata/flood-map-for-planning-rivers-and-sea-flood-zone-2/wms
  GET environment.data.gov.uk/spatialdata/flood-map-for-planning-rivers-and-sea-flood-zone-3/wms
  → overlay with embankment locations
  → flag: embankments within Flood Zone 2 or 3 (toe erosion risk)

HOST class from LandIS archive:
  → Classify catchment drainage behaviour
  → Classes 1-5: rapid surface response (high slope instability risk)
  → Classes 24-29: deep drainage (lower slope risk, higher settlement potential on alluvium)
```

### Step 6 — Climate Sensitivity Score (UKCP18)
```
For each risk mode, apply UKCP18 amplification factors:

Summer precipitation deficit change (2050 RCP8.5):
  → Central England: ~-20% summer rainfall, +2°C
  → Amplifies shrink-swell cycle by estimated 1.3–1.6×
  → Drier summers → deeper desiccation cracks → more rapid rewetting

Winter/autumn rainfall intensity change (2050 RCP8.5):
  → +10–20% increase in high-intensity events
  → Amplifies slope instability risk by estimated 1.2–1.4×
  → Higher peak pore pressures in embankments and cuttings

Output: per-risk-mode "climate amplification factor" for 2050 and 2080
```

### Step 7 — (Optional) EGMS InSAR Validation
```
If ground movement data requested:
  → Fetch EGMS L3 vertical velocity product for bbox
  → Report: mean movement rate (mm/year), max subsidence, max heave
  → Flag locations with |movement| > 2mm/year as "observed anomaly"
  → Cross-reference with high-risk soil/geohazard zones
  → High movement + high shrink-swell class = confirmed problem area
```

### Step 8 — Composite Risk Scoring
```
Per earthwork / asset segment:

SHRINK_SWELL_SCORE = (soil_clay_score × 0.4) + (BGS_geosure_class × 0.4) + (climate_factor × 0.2)

SLOPE_SCORE = (wetness_class × 0.3) + (BGS_landslide_class × 0.3) + (historical_events_nearby × 0.2) + (climate_precip_factor × 0.2)

SETTLEMENT_SCORE = (carbon_content × 0.5) + (HOST_class_deep_drainage_penalty × 0.3) + (floodzone_proximity × 0.2)

SCOUR_SCORE = (watercourse_proximity × 0.4) + (HOST_rapid_response × 0.3) + (structure_age_proxy × 0.3)

COMPOSITE_SCORE = MAX(individual scores) with flag if multiple scores > 3
```

---

## Output Structure

```json
{
  "area": "Leamington Spa - Rugby corridor, Warwickshire",
  "bbox": [-1.65, 52.25, -1.45, 52.35],
  "assessment_date": "2026-04-06",
  "time_horizons": ["current", "2050-RCP8.5"],

  "asset_inventory": {
    "strategic_road_links": 12,
    "rail_links": 8,
    "transport_earthworks": 47,
    "bridges_tunnels": 6,
    "watercourse_crossings": 9
  },

  "soil_context": {
    "dominant_subsoil_texture": "Clay loam to Clay",
    "clay_fraction_range": "30-55%",
    "shrink_swell_proxy": "High (score 4/5)",
    "organic_carbon": "Low (mineral soils dominant)",
    "settlement_risk": "Low-Medium",
    "data_source": "LandIS NATMAPsubsoiltexture v2026-03-31",
    "scale_caveat": "1:250,000 — screening only"
  },

  "bgs_geohazard": {
    "shrink_swell_class": "High (class 4)",
    "landslide_susceptibility": "Low-Medium",
    "historical_landslides_within_2km": 2,
    "compressible_ground": "Low"
  },

  "hydrological": {
    "dominant_host_class": "CLASS_5_6 (slowly permeable — moderate runoff)",
    "wetness_class_majority": "Class 3-4 (imperfect to poor drainage)",
    "flood_zone_2_exposure_pct": 12,
    "flood_zone_3_exposure_pct": 4
  },

  "climate_sensitivity": {
    "horizon": "2050 RCP8.5",
    "shrink_swell_amplification": 1.4,
    "slope_instability_amplification": 1.25,
    "basis": "UKCP18 Central England region projections"
  },

  "risk_scores": {
    "shrink_swell": {"current": 4, "2050": 5, "rating": "Very High"},
    "slope_instability": {"current": 3, "2050": 3, "rating": "Medium"},
    "settlement": {"current": 2, "2050": 2, "rating": "Low"},
    "scour": {"current": 3, "2050": 3, "rating": "Medium"}
  },

  "priority_locations": [
    {
      "description": "Embankment cluster — 3 transport slopes on high-clay soil near watercourse",
      "risk_mode": "shrink_swell + scour",
      "composite_score": 5,
      "recommended_action": "Targeted ground investigation; InSAR time-series review"
    }
  ],

  "verification_checklist": [
    "Commission geotechnical site investigation on top-3 priority embankments",
    "Review EGMS InSAR time series for movement anomalies on high-clay segments",
    "Inspect watercourse crossings for evidence of scour at 3 flagged culverts",
    "Check historical maintenance records for repeat slope failures on WCML",
    "Validate LandIS soil class against available borehole logs"
  ],

  "provenance": {
    "landis_version": "2026-03-31-portal",
    "os_ngd_version": "live-2026-04-06",
    "bgs_geosure": "GeoSure v7",
    "ukcp18_scenario": "RCP8.5",
    "egms": "not_queried"
  },

  "caveats": [
    "All LandIS data at 1:250,000 scale — not suitable for site design.",
    "BGS GeoSure provides area-based hazard classes, not site-specific assessment.",
    "Climate factors are regional projections — local conditions may vary significantly.",
    "FIELD INVESTIGATION IS REQUIRED before any design or mitigation decision.",
    "This output is a screening tool only."
  ]
}
```

---

## Failure Handling

| Condition | Behaviour |
|---|---|
| LandIS warehouse offline | Log warning; fall back to archive ArcGIS REST endpoints; flag in provenance |
| BGS GeoSure API unavailable | Return LandIS-only soil risk with "BGS data unavailable" flag; reduce confidence rating |
| UKCP18 unavailable | Return current risk only with "climate projection unavailable" note |
| EGMS not queried | Omit from output silently; available on request |
| Geometry too large (>50km corridor) | Tile into 10km segments; process and aggregate |
| No OS landform features found | Flag: "No transport earthworks mapped — assess road/rail geometry directly" |

---

## Confidence Rating System

| Rating | Criteria |
|---|---|
| ⭐⭐⭐⭐⭐ High | LandIS + BGS + EA + OS all returned data; EGMS available |
| ⭐⭐⭐⭐ Good | LandIS + BGS + OS available; EA or EGMS missing |
| ⭐⭐⭐ Moderate | LandIS archive fallback; BGS available |
| ⭐⭐ Low | Warehouse offline; only OS and archive data |
| ⭐ Minimal | Major data gaps; screening value only |

---

## Prompt Template

```
Ground Resilience Assessment Prompt:
"Given [corridor/area], assess climate-driven ground failure risk
to [infrastructure type] for [time horizon].
Return: risk scores per failure mode, priority earthwork locations,
verification checklist, and data provenance.
Always include: scale limitations, field investigation requirement,
and confidence rating."
```

---

## Next Steps to Build This Skill

1. [ ] Fix LandIS thematic API to include `natmap-wetness` and `natmap-host` productIds
2. [ ] Build BGS GeoSure MCP wrapper tool (`bgs_geosure_area_summary`)
3. [ ] Build EA Flood Zone MCP wrapper tool (`ea_flood_zone_summary`)
4. [ ] Build UKCP18 delta tool (`climate_sensitivity_score`)
5. [ ] Test composite scoring on Warwickshire corridor with a geotechnical expert
6. [ ] Package as a Cowork skill with SKILL.md trigger phrases
7. [ ] Validate output against known failure locations (Network Rail incident database)

See [[Implementation Roadmap]] and [[UK Ground Risk Strategy]].

---
*← [[00 - Home|Home]]  |  See also: [[Infrastructure Resilience]], [[UK Ground Risk Strategy]], [[Primitive Tools]]*
