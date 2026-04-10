---
aliases: [utilities, engineering, pipe corrosion, shrink-swell, Leacs, trenching]
tags: [use-case, utilities, engineering, corrosion, infrastructure, landis]
confidence: high
key_dataset: SOILSERIES Leacs
---

# Utilities and Engineering

> [!success] Strongly Evidenced
> LandIS has a long-documented relationship with the utilities and engineering sectors. SOILSERIES Leacs is explicitly described as used by **"most major water companies"** in the UK for predicting corrosion rates on underground pipe assets.

## Core Engineering Applications

### Pipe Corrosion Risk (SOILSERIES Leacs)
The primary engineering use case. Leacs provides:
- **Corrosivity to iron (Fe)** — risk of corrosion on cast/ductile iron pipes
- **Corrosivity to zinc (Zn)** — risk on galvanised or zinc-coated assets
- **Shrink-swell class** — risk of ground movement affecting pipe integrity and joints

Used by water utilities, gas network operators, and highway authorities to:
- Prioritise pipe replacement programmes
- Specify pipe materials for new installations
- Assess asset longevity on route alignments

**MCP tool:** `landis_derive_pipe_risk(route_geometry)` → chainage-by-class segments + hotspot list

---

### Shrink-Swell Risk
Shrink-swell soils (typically clay-rich) expand when wet and contract when dry, causing ground movement that damages:
- Building foundations
- Underground pipes and cable ducts
- Road surfaces and pavements

LandIS shrink-swell data is a direct input to site suitability assessment for development and infrastructure.

> [!warning] Planning Caveat
> Shrink-swell class from LandIS is at 1:250k scale and must not be used as a substitute for a site-specific ground investigation. It provides screening-level awareness only.

---

### Trenching Difficulty and Construction Windows
Soil wetness and drainage class directly affect:
- **Construction windows** — when excavation is practical without excessive dewatering
- **Dewatering requirements** — costs and programme risk
- **Reinstatement quality** — ability to compact backfill in wet soils

**Relevant data:** [[Interpreted Layers]] (Wetness), SOILSERIES Agronomy (workdays), Soilscapes drainage class

**Proposed MCP tool:** Trenching Difficulty Estimation → see [[Derived Semantic Tools]]

---

### Excavation Depth and Rock Indicators
Series hydrology data includes depth indicators relevant to:
- Depth to rock (excavation difficulty for deep trenches)
- Depth to seasonal waterlogging
- Soil depth for foundations

**Relevant data:** SOILSERIES Hydrology (depth parameters)

---

### Subsidence and Foundation Risk
National case study framing from Cranfield explicitly includes:
- Subsidence risk
- Road condition deterioration
- Pollutant leaching from development sites

---

### Auger Bore Data
The auger bore dataset (>150,000 bores, >450,000 horizons) is the most site-relevant LandIS data because it represents **measured observations at specific locations** rather than modelled associations. Particularly valuable for:
- Engineering and land development ground truth
- Identifying anomalous soil conditions within an association

---

## The Route Screening Workflow

A complete route constraint screen for a linear infrastructure project:

```
Input: Route polyline (GeoJSON)
          │
          ▼
1. landis_natmap_area_summary(route_buffer)
   → soil associations along route
          │
          ▼
2. landis_derive_pipe_risk(route)
   → corrosion/shrink-swell by chainage
          │
          ▼
3. landis_natmap_thematic_area_summary(route_buffer, "wetness")
   → construction window constraints
          │
          ▼
4. Soil Alerts check (proposed tool)
   → acid sulphate peats, groundwater soils
          │
          ▼
Output: Route constraint report with hotspot map
        + verification checklist for ground investigation
```

**Prompt template:** Route Constraint Screening → see [[Resources and Prompts]]

---

## Key Questions (Stakeholder Perspective)

| Question | LandIS Dataset | MCP Tool |
|---|---|---|
| What is the corrosion risk to iron pipes on this route? | SOILSERIES Leacs | `landis_derive_pipe_risk` |
| Where are the shrink-swell hotspots? | SOILSERIES Leacs | `landis_derive_pipe_risk` |
| What wetness constraints affect our construction window? | NATMAP Wetness | `landis_natmap_thematic_area_summary(…, "wetness")` |
| How difficult is excavation on this alignment? | Leacs + Hydrology | Derived tool (proposed) |
| Are there any soil alerts on this route? | Soil Alerts | Proposed tool |

---

## Key Stakeholders
→ [[Stakeholders#🔧 Utilities and Infrastructure Planners]]

---
*← [[00 - Home|Home]]  |  See also: [[Horizon Data]], [[Derived Semantic Tools]], [[Hydrology and Flood]]*
