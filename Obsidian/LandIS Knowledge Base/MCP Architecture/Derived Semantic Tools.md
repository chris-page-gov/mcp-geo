---
aliases: [semantic tools, derived tools, interpretation tools]
tags: [mcp, tools, semantic, interpretation, landis]
---

# Derived Semantic Tools

> [!info] Design Principle
> Derived semantic tools convert raw data into **decision-relevant outputs** in plain language. They compose multiple primitive lookups internally and always return:
> 1. The underlying raw classes/values
> 2. A plain-English explanation
> 3. A caveat block
> 4. Provenance and dataset version

These are the tools end users actually interact with. They abstract the relational complexity of [[Data Structure and Joins|LandIS's join model]] into meaningful answers.

---

## Active Derived Tool

### `landis_derive_pipe_risk(route_geometry)`

**Purpose:** Estimate corrosion and shrink-swell risk for buried pipe assets along a route.

**Inputs:** Route geometry (polyline — GeoJSON or WKT)

**Internal process:**
1. Intersects route with [[NATMAP Vector]] polygons
2. Resolves series via NATMAPassociations
3. Looks up SOILSERIES Leacs (corrosivity to Fe/Zn, shrink-swell class)
4. Aggregates to chainage segments

**Output:**
- Chainage-by-class risk segments
- Per-segment: corrosion class (Fe and Zn), shrink-swell class
- Hotspot list (highest risk segments)
- Plain-English explanation of drivers
- Mandatory caveat: field verification required for asset design

**Primary use case:** [[Utilities and Engineering]] — water utilities, telecoms, gas networks

**Evidence basis:** SOILSERIES Leacs is explicitly described as used by "most major water companies" for predicting corrosion rates on underground pipe assets.

---

## Proposed Derived Tools

### Trenching Difficulty Estimation

**Purpose:** Estimate construction difficulty and risk for linear excavations.

**Inputs:** Route/area, wetness, drainage, depth to rock, shrink-swell class

**Output:**
- Categorical difficulty (Easy / Moderate / Difficult / Very Difficult)
- Drivers (e.g. "Wetness Class 4 — likely dewatering required; Shrink-swell Class 3 — ground movement risk")
- "Where to verify on site" checklist
- Construction window estimate (workable days/season)

**Evidence basis:** Wetness/drainage and soil engineering applications are explicitly documented in LandIS. [[Agriculture and Land Management]] workdays data is relevant.

---

### Drainage and Flood-Response Narrative

**Inputs:** HOST class + Soilscapes drainage + wetness for an area

**Output:**
- Likely hydrological behaviour patterns
- "Respond fast to rain?" / "Baseflow dominated?" assessment
- "Do not infer" caveats (e.g. "this does not predict specific flood events")

**Evidence basis:** HOST conceptual response modelling; Soilscapes drainage describes flood response times.

**Primary use case:** [[Hydrology and Flood]]

---

### High-Carbon Soil Screening

**Inputs:** Area polygon → NATMAP Carbon stock layers

**Output:**
- High/medium/low carbon stock classification
- Depth-layer breakdown (0–30, 30–100, 100–150 cm)
- Policy flags (e.g. "potential peatland — verify with peat depth survey")

**Evidence basis:** NATMAP Carbon fields explicitly used in GHG Inventory.

**Primary use case:** [[Climate and Carbon]], [[Government and Policy]]

---

### Pesticide Leaching and Runoff Vulnerability Screening

**Inputs:** Area → SOILSERIES Pesticides classes via NATMAPassociations

**Output:**
- Vulnerability class (leaching / runoff / both / low risk)
- Plain-English explanation of pathway
- Groundwater/surface water risk flag

**Evidence basis:** Pesticide leaching/runoff fields and groundwater monitoring relevance.

**Primary use case:** [[Government and Policy]], [[Hydrology and Flood]]

---

### Soil Alerts Explainer

**Inputs:** Location/area → soil associations → matched alerts

**Output:**
- Alert list (e.g. acid sulphate peat, groundwater-affected soils, problem horizons)
- Plain-language implications for the project type
- Recommended verification steps
- Links to specialist guidance

**Evidence basis:** Soil Alerts explicitly aimed at non-specialist practitioners (ecology, forestry, hydrology, engineering) to prevent project failure.

**Caveat:** Soil Alerts are screening flags, not diagnoses. Always verify with a soil specialist.

---

### Catchment Vulnerability Summary

**Inputs:** Catchment polygon

**Output:**
- HOST breakdown (dominant hydrological response classes)
- Wetness class distribution
- Drainage characterisation
- Pesticide leaching/runoff vulnerability
- NSI monitoring context (if points available)

**Primary use case:** [[Hydrology and Flood]], [[Government and Policy]]

---

### Route Constraint Screening

**Inputs:** Route polyline + project type (telecoms / pipeline / road / cable)

**Output:**
- Soil constraint summary by chainage
- Wetness/drainage constraints (construction window)
- Corrosion/shrink-swell classes (asset longevity)
- Depth/rock indicators (excavation difficulty)
- Verification checklist

**Primary use case:** [[Utilities and Engineering]]

---

## Guardrail Requirements

All derived semantic tools must:

> [!warning] Mandatory Guardrails
> - Never imply site-level certainty from 1:250k data
> - Always return raw class codes alongside plain-English
> - Always include a caveat block
> - Always include provenance (dataset, version, date accessed)
> - Never omit the "field investigation required" statement
> - For engineering uses: explicitly state the scale limitation and recommend specialist site investigation

---
*← [[00 - Home|Home]]  |  See also: [[Primitive Tools]], [[MCP Overview]], [[Utilities and Engineering]]*
