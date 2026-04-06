---
aliases: [agriculture, farming, agronomy, land management, crop]
tags: [use-case, agriculture, agronomy, farming, landis]
confidence: high
---

# Agriculture and Land Management

> [!success] Directly Evidenced
> LandIS's own applications list includes agriculture-adjacent functional planning: direct drilling, drainage design, trafficability, machinery workdays, and suitability for specific crops.

## Core Agricultural Applications

### Soil Type and Drainage Suitability
The foundational agricultural question: what can I grow here, and under what constraints?

- **Soilscapes** provides a plain-language soil class for farm awareness purposes
- **NATMAP Wetness** provides the drainage class used in ALC and planning
- **SOILSERIES Agronomy** provides crop-specific suitability indicators

**MCP access:**
- `landis_soilscapes_point(lat, lon)` — quick farm field soil class
- `landis_soilscapes_area_summary(holding_polygon)` — holding-level soil breakdown
- `landis_natmap_thematic_area_summary(field_polygon, "wetness")` — drainage constraints

---

### Machinery Workdays and Trafficability
How many days per year is the soil workable — i.e. suitable for machinery without structural damage?

**SOILSERIES Agronomy** provides workday estimates by crop operation type. Critical for:
- Harvest window planning
- Drilling date decisions (direct drilling vs ploughing)
- Slurry spreading compliance planning

---

### Crop Available Water (CAW)
[[Interpreted Layers#NATMAP Crop Available Water (CAW)|NATMAP CAW]] estimates water available to crops between field capacity and wilting point, for different rooting depth models. Directly relevant to:
- Irrigation planning and water licence decisions
- Drought risk assessment for specific crops
- Crop selection on light, sandy soils

---

### Drainage Design
Soil drainage class and wetness category inform the specification of:
- Field drainage systems (mole drains, pipe drains)
- Headland design
- Ditch management priorities

**Soilscapes drainage** data has been used by local governments, engineers, agronomists, and environmental consultants for drainage design support.

---

### Diffuse Pollution Prevention
Soilscapes drainage is framed as supporting **pollution prevention policies** and **river basin management planning** — specifically identifying where soils are at risk of:
- Phosphorus runoff (poorly drained soils near watercourses)
- Pesticide leaching (freely draining soils over shallow aquifers)
- Sediment mobilisation (structurally unstable soils)

**LandIS data:** SOILSERIES Pesticides (leaching/runoff vulnerability classes)

---

### Direct Drilling and Soil Structure
Soil texture and structure affect the viability of direct drilling (no-tillage) approaches. Sandy or loamy soils with good drainage are generally more suitable than heavy clays with poor structure.

---

## Farm Advisory Workflow

```
Input: Farm holding boundary polygon
          │
          ▼
1. landis_soilscapes_area_summary(holding)
   → Soilscapes class breakdown with drainage descriptions
          │
          ▼
2. landis_natmap_thematic_area_summary(holding, "wetness")
   → Wetness class distribution
          │
          ▼
3. landis_natmap_thematic_area_summary(holding, "caw")
   → Crop available water by area
          │
          ▼
Output: Farm soil advisory note
        → "50% of your holding is on Soilscapes class 3b
           (slowly permeable seasonally wet soils)..."
        → Drainage recommendations + crop suitability flags
        + "This is based on 1:250k mapping — local conditions
           may vary significantly. Field survey recommended."
```

**Prompt template:** Farm Advisory Summary → see [[Resources and Prompts]]

---

## Key Questions (Stakeholder Perspective)

| Question | Dataset | Tool |
|---|---|---|
| What soils does my farm have? | Soilscapes | `landis_soilscapes_area_summary` |
| What are the drainage constraints for this field? | NATMAP Wetness | `landis_natmap_thematic_area_summary(…, "wetness")` |
| How many workable machinery days can I expect? | SOILSERIES Agronomy | Proposed series lookup |
| What crop available water does this area provide? | NATMAP CAW | `landis_natmap_thematic_area_summary(…, "caw")` |
| What is the pesticide leaching risk? | SOILSERIES Pesticides | Proposed derived tool |

---

## Key Stakeholders
→ [[Stakeholders#🌾 Agricultural Advisors and Land Managers]]

---
*← [[00 - Home|Home]]  |  See also: [[Government and Policy]], [[Interpreted Layers]], [[Soilscapes]]*
