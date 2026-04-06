---
aliases: [policy use cases, Defra, ELMS, NCEA, ALC]
tags: [use-case, government, policy, defra, ELMS, landis]
confidence: high
---

# Government and Policy

> [!success] Directly Evidenced
> LandIS is explicitly described by Defra as used across "projects and policy areas" with named applications in land-use planning, environmental protection, agricultural policy, and climate adaptation.

## Core Policy Applications

### Environmental Land Management Schemes (ELMS)
The Defra procurement notice (Feb 2025) explicitly frames open access as strategically enabling ELMS. Soil type, drainage, and carbon data are essential evidence for:
- Qualifying areas for higher-tier payments
- Defining soil health improvement actions
- Monitoring baseline and change

**LandIS data used:** [[NATMAP Vector]], [[Interpreted Layers]] (Wetness, Carbon), [[Soilscapes]]

---

### Agricultural Land Classification (ALC)
NATMAP Wetness and crop available water are **directly connected to ALC methodology**. ALC grades land 1–5 based on soil and climate constraints, with soil wetness being a primary limiting factor.

**Questions LandIS can answer:**
- What is the ALC-relevant wetness class distribution for this proposed development site?
- Which areas of a holding are Grade 3b or better based on soil constraints?

**LandIS data used:** [[Interpreted Layers]] (Wetness, CAW), [[NATMAP Vector]]

---

### Nature Recovery Network and Local Nature Recovery Strategies (LNRS)
Open LandIS enables screening of land for nature recovery potential based on soil type — identifying where habitats can most readily be re-established.

**Questions LandIS can answer:**
- What soil types underpin Priority Habitat types in this area?
- Are soils in this LNRS area compatible with wet grassland or heathland restoration?

**LandIS data used:** [[Soilscapes]] (habitats sub-dataset), [[Interpreted Layers]] (Wetness, HOST)

---

### NCEA — Natural Capital and Ecosystem Assessment
The NCEA requires a national evidence base for quantifying soil ecosystem services. LandIS carbon, hydrology, and soil quality data are foundational inputs.

**LandIS data used:** [[Interpreted Layers]] (Carbon, HOST), [[NSI - National Soil Inventory]]

---

### Net Zero and Climate Commitments
The Greenhouse Gas Inventory explicitly uses **NATMAP Carbon** for soil carbon accounting in England and Wales. This makes LandIS a statutory input to national climate reporting.

**Questions LandIS can answer:**
- What is the total organic carbon stock in this proposed land-use change area?
- Where are the highest-risk soils for carbon loss under drainage or cultivation?

**LandIS data used:** [[Interpreted Layers]] (Carbon), [[Climate and Carbon]]

---

### Peat Mapping and Protection
Defra case study: Natural England uses LandIS soil association data to **guide surveyors to potential buried peat locations** — a direct operational use of NATMAP in field survey prioritisation.

---

## MCP Tools for Policy Use

| Question | Tool |
|---|---|
| What is the wetness class distribution for this area? | `landis_natmap_thematic_area_summary(geometry, "wetness")` |
| What is the carbon stock in this proposed ELMS area? | `landis_natmap_thematic_area_summary(geometry, "carbon")` |
| What HOST classes dominate this catchment? | `landis_natmap_thematic_area_summary(geometry, "host")` |
| What is the soil overview for a planning enquiry? | `landis_soilscapes_area_summary(geometry)` |

**Prompt template:** Local Planning Evidence Pack → see [[Resources and Prompts]]

---

## Key Stakeholders
→ [[Stakeholders#🏛️ Government and Policy Teams]]

---
*← [[00 - Home|Home]]  |  See also: [[Agriculture and Land Management]], [[Climate and Carbon]], [[Stakeholders]]*
