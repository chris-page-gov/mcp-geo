---
aliases: [hydrology, flood, HOST, catchment, drainage, baseflow]
tags: [use-case, hydrology, flood, HOST, catchment, landis]
confidence: high
key_dataset: NATMAP HOST
---

# Hydrology and Flood

> [!success] Directly Evidenced
> HOST is documented as a hydrologically-based classification intended to describe **catchment hydrological response and soil-substrate processes**, with 29 classes and 11 conceptual response models. It is widely used in catchment hydrology modelling across the UK.

## Core Hydrological Applications

### HOST — Hydrological Response to Soil Type
HOST classifies soils by dominant hydrological response — how water moves through soil and substrate under rainfall. Derived from:
- Soil series properties (drainage, texture, porosity)
- Hydrogeology (aquifer presence, depth)

**29 classes, 11 conceptual response models** — ranging from rapid surface/near-surface routing to deep groundwater recharge.

**Uses:**
- Catchment model parameterisation (e.g. PDM, TOPMODEL)
- Baseflow index (BFI) prediction
- Standard percentage runoff estimation
- Low-flow frequency analysis

**MCP access:** `landis_natmap_thematic_area_summary(catchment_polygon, "host")`

---

### Baseflow Index and % Runoff
SOILSERIES Hydrology explicitly includes:
- **HOST class** at series level
- **Bypass flow** indicators
- **Baseflow index (BFI)** — proportion of river flow from groundwater
- **Standard percentage runoff (SPR)** — key input to design flood estimation

These parameters are **"essential" for groundwater modelling and flow prediction** (LandIS documentation).

---

### NATMAP Wetness and Seasonal Flooding
Wetness class describes seasonal waterlogging — directly relevant to:
- Floodplain identification and management
- Agricultural drain design
- Surface runoff generation in wet periods
- Flood response time prediction

**Soilscapes drainage** data describes how quickly an area responds to rainfall — useful for qualitative flood response characterisation in non-specialist contexts.

---

### NSI Flood-Risk Indicator
The NSI includes a flood-risk indicator at each monitoring point. While point-based and not a hydrological model, it provides monitored evidence of flood exposure at grid locations.

**MCP access:** `landis_nsi_within_area(catchment_polygon)` → includes flood-risk flag

---

### Landfill and Contamination Leachate Risk
LandIS case studies reference identifying freely draining or groundwater-connected soils beneath historic landfills to assess **leachate risk pathways to water bodies**. HOST and drainage data provide the hydrological connectivity evidence.

**See also:** [[Emerging Opportunities#Contamination and Remediation Triage]]

---

## The Catchment Screening Workflow

```
Input: Catchment polygon
          │
          ▼
1. landis_natmap_thematic_area_summary(catchment, "host")
   → HOST class distribution + % coverage
          │
          ▼
2. landis_natmap_thematic_area_summary(catchment, "wetness")
   → Wetness class distribution
          │
          ▼
3. landis_soilscapes_area_summary(catchment)
   → Drainage class characterisation
          │
          ▼
4. landis_nsi_within_area(catchment)
   → Point monitoring context + sampling density note
          │
          ▼
Output: Catchment vulnerability summary
        with HOST response model, BFI inference,
        wetness constraints, and uncertainty flags
```

**Prompt template:** Catchment Vulnerability Assessment → see [[Resources and Prompts]]

---

## Proposed Derived Tool: Drainage and Flood-Response Narrative

**Input:** HOST + Soilscapes drainage + wetness for an area
**Output:**
- Likely hydrological behaviour: "This catchment is dominated by HOST class 5 (slowly permeable soils with surface saturation) — expect rapid runoff response to rainfall, limited baseflow, and extended wet periods."
- "Do not infer" caveats: "This does not predict specific flood events or water levels."

See [[Derived Semantic Tools]] for specification.

---

## Key Questions (Stakeholder Perspective)

| Question | Dataset | Tool |
|---|---|---|
| What HOST classes dominate this catchment? | NATMAP HOST | `landis_natmap_thematic_area_summary(…, "host")` |
| What is the baseflow index for these soils? | SOILSERIES Hydrology | Proposed series lookup tool |
| Where are soils likely to generate rapid surface runoff? | HOST + Wetness | Derived drainage narrative |
| How does drainage interact with this flood zone? | Wetness + HOST | Catchment Vulnerability prompt |

---

## Key Stakeholders
→ [[Stakeholders#💧 Hydrology and Flood Teams]]

---
*← [[00 - Home|Home]]  |  See also: [[Interpreted Layers]], [[Horizon Data]], [[Government and Policy]]*
