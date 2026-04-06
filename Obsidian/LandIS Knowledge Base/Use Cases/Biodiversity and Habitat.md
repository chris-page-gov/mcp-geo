---
aliases: [biodiversity, habitat, conservation, wildlife, ecology]
tags: [use-case, biodiversity, habitat, conservation, ecology, landis]
confidence: medium-high
---

# Biodiversity and Habitat

> [!success] Evidenced via Soilscapes Habitats
> The Soilscapes habitats dataset is explicitly framed as supporting habitat project decision-making and biodiversity issues, with documented use by Wildlife Trusts and local biodiversity recording centres.

## Core Biodiversity Applications

### Habitat Suitability Mapping
Each of the 27 Soilscapes classes is associated with typical habitat types — from calcareous grasslands on chalk and limestone soils to wet woodland and fen peat soils.

**Use cases:**
- Identifying where Priority Habitats are most likely to have existed or can be restored
- Screening land for biodiversity net gain (BNG) opportunities
- Supporting Local Nature Recovery Strategy mapping

**MCP access:** `landis_soilscapes_area_summary(land_parcel)` → classes with habitat associations

---

### Land Purchase and Buffering Decisions
Documented use by **Bedfordshire and Luton Biodiversity Recording and Monitoring Centre (BRMC)** and **Wildlife Trust actors** for:
- Land purchase decisions based on soil suitability for target habitats
- Buffer zone and linkage analysis between existing reserves
- Connectivity assessment for habitat corridors

---

### Conservation Planning
Soil type determines the potential biodiversity of a site in the long term. Understanding baseline soils helps conservation planners:
- Set realistic restoration targets (calcareous grassland requires shallow chalk/limestone soils)
- Identify where intervention is likely to succeed vs fail
- Prioritise limited funding for land management

---

### Soil Alerts for Ecology Projects
**Soil Alerts** are explicitly framed as aimed at practitioners in:
- Ecology
- Forestry
- Hydrology
- Geology
- Engineering

...who may not be soil specialists. The alerts flag conditions that could cause **project failure due to soil misinterpretation**, including:
- Pans misidentified as bedrock (affecting translocation projects)
- Acid sulphate peats (releasing sulphuric acid when drained)
- Groundwater-affected soils (translocation failure risk)

**Proposed MCP tool:** Soil Alerts Explainer — flags relevant alerts for a location with plain-language implications. See [[Derived Semantic Tools]].

---

### Peat and Organic Soil Identification
Peat and organic soils are critical for:
- Biodiversity (mires, fens, wet heathland)
- Carbon storage
- Water regulation

LandIS wetness and carbon data, combined with Soil Alerts, provides a screening layer for targeting peatland surveys and protection.

See also: [[Climate and Carbon]]

---

### Habitat Restoration Feasibility
Before committing to habitat creation, practitioners need to know:
- Is the soil genuinely suitable for the target habitat?
- What drainage interventions are needed?
- Are there subsurface constraints (rock, hardpan, groundwater)?

LandIS provides the first screening layer; site investigation is always required to confirm.

---

## Key Questions (Stakeholder Perspective)

| Question | Dataset | Tool |
|---|---|---|
| What habitats are associated with soils on this parcel? | Soilscapes (habitats) | `landis_soilscapes_area_summary` |
| Are there any soil alerts we should know about? | Soil Alerts | Proposed Alerts Explainer |
| Are soils suitable for wet grassland restoration? | Soilscapes + Wetness | Combined query |
| Where should we focus survey effort for peat? | Soilscapes + Carbon + Alerts | Multi-layer screening |

---

## Confidence Assessment

> [!note] Confidence Level: Medium-High
> Soilscapes habitat data is evidenced for conservation use. However, using 1:250k mapping for biodiversity planning requires caution — habitat potential is highly local and within-class variability is significant. Soilscapes provides direction for survey prioritisation, not a substitute for habitat surveys.

---

## Key Stakeholders
→ [[Stakeholders#🌿 Biodiversity and Conservation Planners]]

---
*← [[00 - Home|Home]]  |  See also: [[Climate and Carbon]], [[Government and Policy]], [[Soilscapes]]*
