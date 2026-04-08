---
aliases: [Lincolnshire case study, BGS road resilience, Harrison 2023, GeoSure validation]
tags: [reference, bgs, case-study, validation, lincolnshire, road, compressible-ground, peat, climate]
source: "Harrison, M., Heaton, C. & Entwisle, D. (2023). Increasing road network resilience to the impacts of ground movement due to climate change: a case study from Lincolnshire, UK. Quarterly Journal of Engineering Geology and Hydrogeology, 56(2)."
doi: https://doi.org/10.1144/qjegh2022-131
---

# BGS Lincolnshire Case Study — Road Resilience to Ground Movement

> [!abstract] Why This Matters
> This paper directly validates the approach used in [[Ground Resilience Skill Design]] and [[Infrastructure Resilience]]. It is the most important empirical evidence base for using BGS GeoSure + UKCP18 + LiDAR to screen road network resilience — and it contains critical findings about **compressible ground** that substantially expand the risk picture beyond shrink-swell.

---

## Reference

**Full citation:**
Harrison, M., Heaton, C. & Entwisle, D. (2023). *Increasing road network resilience to the impacts of ground movement due to climate change: a case study from Lincolnshire, UK.* Quarterly Journal of Engineering Geology and Hydrogeology, **56**(2). https://doi.org/10.1144/qjegh2022-131

**Organisations:** British Geological Survey (BGS) + Lincolnshire County Council (LCC)

---

## Core Approach

The study used BGS **GeoSure** hazard layers combined with **UKCP18** climate projections to screen the Lincolnshire road network for ground movement risk — exactly the approach documented in [[UK Ground Risk Strategy]].

**Data stack used:**
- BGS GeoSure: shrink-swell, landslide, compressible ground, collapsible deposits, dissolution, running sand (all 6 layers)
- BGS GeoClimate: GeoSure shrink-swell + UKCP18 combined into a single future-risk layer
- EA LiDAR: ground surface change over time — used to validate modelled compressible ground risk
- UKCP18 climate projections: summer moisture deficit, winter rainfall intensity (RCP8.5 2050 and 2080)
- LCC road condition and maintenance records: used to correlate modelled risk with observed damage

**Key output:** Priority road sections for investigation, ranked by composite geohazard + climate sensitivity score.

---

## Key Findings

### 1. Compressible Ground Dominates in Low-Lying Areas

> [!important] Critical Finding for Skill Design
> Compressible ground (peat, alluvium, tidal flat deposits) correlated **more strongly** with observed road damage in Lincolnshire than shrink-swell — challenging the assumption that shrink-swell is always the primary mode.

In low-lying fenland and coastal plain areas, the dominant failure mechanism is **progressive compression of soft deposits** under road loading, accelerated by climate-driven changes to the water table and soil moisture.

**Implication for skill scoring:** Do not automatically weight shrink-swell above compressible ground. Always check BGS `GeoSure_Compressible_Ground` and `natmap-carbon` alongside clay content.

### 2. "Evolved Roads" — The Highest-Risk Asset Class

Roads that were historically widened from trackways or field paths, with **no engineered foundation**, built directly on susceptible soils. These roads exist throughout the Lincolnshire Fens and similar low-lying agricultural areas.

**Characteristics:**
- Typically unclassified or C-class rural roads
- Surface consists of successive layers of patching applied over decades
- Each patch adds load → compresses underlying soft deposits further
- Damage is progressive and accelerating
- No sub-base to distribute load

**Why patching accelerates failure:** Patching repairs surface irregularity but adds 40–80mm of dense tarmac weight. On compressible deposits, this load increase exceeds the bearing capacity increment from the repair, net accelerating the compression cycle.

### 3. Local Amplifiers — Critical for Site-Level Assessment

The study identified several local factors that significantly amplify ground movement risk beyond what regional soil and geohazard data can predict:

| Factor | Mechanism | Infrastructure Impact |
|---|---|---|
| **Drainage ditch management** | Alters local water table; deep drains lower peat moisture → compression | Differential settlement across road; width-direction cracking |
| **Agricultural irrigation** | Lowers soil moisture in summer; increases depth of desiccation | Longitudinal cracking; differential settlement adjacent to irrigated fields |
| **Roadside trees (one-sided)** | Differential drying of soil beneath canopy vs open side | Longitudinal cracking; asymmetric road deformation |
| **Roddons** | Buried silty ridges of former river courses — higher, better-drained, stiffer than surrounding peat | Highly localised differential settlement at sub-metre scale; not visible in 1:250k data |

### 4. Roddons — Hidden Heterogeneity in Fenland

Roddons (also spelled "rodhams") are the silty ridges of former river channels now buried under peat. They are:
- Composed of silty/clayey alluvium — drier and stiffer than surrounding peat
- Typically 0.5–2m above the surrounding land surface (now reduced by peat wastage)
- Visible on EA LiDAR as subtle linear or sinuous ridges
- Invisible at 1:250k scale — not distinguishable from surrounding associations

Where a road crosses multiple roddons at oblique angles, differential settlement occurs at each crossing point. Only field investigation or LiDAR analysis can identify these.

### 5. EA LiDAR Validation

EA LiDAR (1m DEM, composite product) was used to:
- Measure surface level change between survey epochs (peat compression validation)
- Identify roddons and palaeo-drainage features invisible in soil maps
- Map road surface longitudinal and transverse profile irregularity

**Finding:** LiDAR-derived surface change correlated well with modelled high compressible ground risk zones, confirming GeoSure_Compressible_Ground as a reliable screening proxy.

**Implication:** EA LiDAR should always be recommended in the verification checklist for roads on BGS GeoSure_Compressible_Ground class D or E.

### 6. Vegetation Effects Under Climate Change

Trees on the roadside cause significant asymmetric soil drying in summer on both clay and peat soils. Under UKCP18 2050 scenarios, longer and more intense summer droughts will intensify this effect.

**Observed damage pattern:** Longitudinal cracking running along the road, with more severe cracking on the vegetated side. In Witham Bank (Site 3), west-side tree cover caused differential moisture → pronounced longitudinal crack running the full length of the assessed section.

---

## Four Study Sites

### Site 1 — Fodderdyke Bank (Grade C road, Lincolnshire Fens)
- **Ground:** 5–10m deep peat (amorphous, low bearing capacity)
- **Road type:** Evolved road — no engineered foundation
- **Failure mode:** Progressive peat compression; surface splitting and undulations; slope movement at road edges
- **Climate context:** Future drying → peat desiccation (irreversible) → accelerated surface irregularity
- **Fatality:** 2015 road accident linked to surface condition
- **EA LiDAR:** Shows differential peat compression along road length; roddons visible as subtle ridges
- **Key risk factor:** No foundation + peat depth + no remediation path except full road reconstruction

### Site 2 — Brandy Wharf (B1205, ~400m section)
- **Ground:** Peat 1–3m over glaciolacustrine clay; old river course (roddon) creates stratigraphy variability
- **Road type:** B-road with engineered sub-base (better than Site 1 but still on compressible ground)
- **Failure mode:** Differential settlement; longitudinal cracking; variable surface roughness
- **Stratigraphy (windowless samples):** Complex — fibrous peat, amorphous peat, organic clay, minerogenic clay layers alternating at depth
- **Key risk factor:** Roddon creates variability over very short distances — patches fail differentially

### Site 3 — Witham Bank (rural road, Witham valley)
- **Ground:** Alluvium to 6m depth (fibrous peat at depth); former river floodplain
- **Failure mode:** Differential soil moisture → longitudinal cracking; asymmetric settlement
- **Local amplifier:** Trees on west side only → differential drying → crack runs full section length
- **Climate projection:** Further intensification of crack under 2050 summer drought scenarios
- **Key risk factor:** Vegetation management (tree removal or irrigation) would reduce differential drying

### Site 4 — Amber Hill (rural road, coastal plain)
- **Ground:** Tidal flat deposits ~5m depth over thick fluvial gravels
- **Failure mode:** Soil drying (not primary wetness → compressible, but secondary desiccation cracking)
- **Local amplifiers:**
  - Drainage ditch management (lowered water table)
  - Adjacent field irrigation (further lowers summer soil moisture)
  - Roadside trees (differential drying)
- **Key risk factor:** Multiple converging factors from land management — invisible from regional data alone

---

## Implications for the Ground Resilience Skill

1. **Always query `GeoSure_Compressible_Ground`** — not just shrink-swell — in any assessment
2. **In low-lying areas** (fens, river valleys, coastal plains, Somerset Levels): assume compressible ground is the primary mode until proven otherwise
3. **Flag evolved roads explicitly** — unclassified/C-class roads in low-lying areas on compressible deposits
4. **Add vegetation survey to verification checklist** — especially trees causing one-sided drying
5. **Add drainage management audit to verification checklist** — especially where deep ditches or irrigation present
6. **Always recommend LiDAR** where GeoSure_Compressible_Ground ≥ class C
7. **Note roddon risk** in any assessment of Fenland, Lincolnshire, Norfolk Broads, Humber Levels, or similar areas
8. **Short-term patching is not a solution** on evolved roads on compressible ground — advise ground investigation before further maintenance expenditure
9. **BGS GeoClimate** (GeoSure + UKCP18 combined) is the preferred future-risk product where available

---

## Quantified Deterioration Data

From the companion visual documents, the following hard numbers are available for the Lincolnshire network:

| BGS GeoSure Compressibility Class | Annual Residual Life Loss (evolved roads) |
|---|---|
| A — Low | 0.80 years/year |
| B | 0.07 years/year |
| C | 0.00 years/year |
| D — Significant | 3.10 years/year |
| E — Very Significant | **3–17 years/year** |

Source: [[Subsurface Road Resilience Blueprint]] Slide 7. When engineered A-Roads are excluded, GeoSure E roads spike to 3–17 years of structural life lost per year. **This is the single most important quantitative output for maintenance prioritisation.**

---

## See Also
- [[Infrastructure Resilience]] — the primary use case note
- [[Ground Resilience Skill Design]] — the skill this study validates
- [[MCP-Geo Validation Suite]] — ⭐ 8 live queries against all four study sites, 8/8 pass
- [[Subsurface Road Resilience Blueprint]] — ⭐ full 10-slide visual strategic document
- [[Assets/Building Climate-Resilient Roads|Building Climate-Resilient Roads]] — single-page infographic summary
- [[UK Ground Risk Strategy]] — national roll-out context
- [[Open Questions]] — Q13 (BGS GeoSure MCP tool) and Q15 (tile pre-computation)
- [[Assets/LandIS_MCP_Strategy.pdf|MCP Strategy Slides]]

---

*Source PDF: `Assets/BGS_Lincolnshire_Road_Resilience_2023.pdf`*

---
*← [[00 - Home|Home]]  |  See also: [[Infrastructure Resilience]], [[Ground Resilience Skill Design]]*
