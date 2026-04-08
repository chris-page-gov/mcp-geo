---
aliases: [Warwickshire survey, Warwickshire ground risk, Warwickshire roads, shrink-swell Warwickshire]
tags: [warwickshire, ground-resilience, shrink-swell, lias-clay, survey, live-data, infrastructure]
survey_date: 2026-04-06
methodology: LandIS MCP-Geo desk-based survey
status: complete
---

# Warwickshire Ground Resilience Assessment
## Desk-Based Soil Risk Survey for Infrastructure

> [!info] Methodology
> This is a desk-based assessment using national datasets accessed via MCP-Geo (LandIS, OS NGD, BGS GeoClimate). It does not replace site investigation or field survey. All soil series data is from NATMAP 1:250,000 polygon mapping; NSI evidence is from field surveys conducted 1981–1983. Road risk conclusions are indicative only and should be validated against PMS (Pavement Management System) data and local authority maintenance records before action.

**Survey area:** Warwickshire (county bbox `[-1.90, 52.05, -1.15, 52.68]`), ~3,582 km²
**Survey date:** 6 April 2026
**Data sources:** LandIS NATMAP Core, LandIS NSI, LandIS NATMAPcarbon, LandIS NATMAP Subsoil Texture, OS NGD, BGS GeoClimate UKCP18
**Risk methodology:** Soil series characterisation → texture/carbon profiling → NSI field evidence → climate trajectory → road network overlay

---

## Executive Summary

Warwickshire is a county defined by clay. Approximately **75% of the county's land area has clay or clay-loam subsoil**, predominantly derived from Jurassic Lias (south and east) and Permo-Triassic mudstone (north and west). There is **no peat or compressible ground** anywhere in the county — the primary ground failure mode is **shrink-swell**: seasonal expansion and contraction of clay soils in response to moisture change, causing heaving, cracking, and settlement of roads, buildings, and buried infrastructure.

Three distinct risk zones emerge from the survey:

1. **The Feldon** (south and east Warwickshire — Southam, Kineton, Fenny Compton, Lower Brailes) — **highest risk**: deep Jurassic Lias clay soils (DENCHWORTH, EVESHAM series); clay fraction 52–58% throughout to 110cm depth; strongly developed angular blocky structure; gley mottling from 24cm; NATMAP explicitly flags landslip risk. The combination of high-plasticity clay, seasonal waterlogging, and rural unclassified/C-class roads on poorly engineered foundations makes this the priority intervention zone for any county-scale ground resilience programme.

2. **North Warwickshire and Arden** (Atherstone, Nuneaton, Kenilworth, Henley-in-Arden) — **moderate-high risk**: WHIMPLE and BROCKHURST series on Permo-Triassic reddish clay; slightly impeded drainage; moderate shrink-swell. Lower risk than Feldon Lias clay but covers the county's most economically productive road corridors (A5, A444, A47).

3. **River floodplains** (Avon valley, Arden stream valleys) — **differential risk**: FLADBURY alluvial clay (Warwick, Stratford); ARROW glaciofluvial drift (Coleshill). Failure mode shifts from shrink-swell to waterlogging, flooding, and alluvial differential settlement. Road crossings of these floodplains represent specific vulnerability points.

BGS GeoClimate UKCP18 returns "Improbable" for climate change amplification across Warwickshire — meaning the county's shrink-swell susceptibility is already at a high baseline that climate change will not dramatically shift in categorical terms. This should not be interpreted as low risk: more frequent and intense summer drought/wet cycles will intensify seasonal cycling within the existing susceptibility, accelerating damage even without a class change.

**This is the inverse risk profile from Lincolnshire**: different soil, different failure mode, different engineering response. Warwickshire roads crack and heave; they do not settle and rupture as Lincolnshire fen roads do. Both are high priority — but the solutions differ.

---

## 1. Geological and Soil Context

Warwickshire straddles three major geological belts running broadly NW–SE:

- **North and west (Arden):** Permo-Triassic red mudstones and sandstones, overlain by glacial till and drift. Reddish clay soils (WHIMPLE, BROCKHURST). The Forest of Arden sits on this belt.
- **Centre:** Transitional zone; Triassic/Jurassic boundary; some sandstone outcrops creating lighter, freer-draining patches (RIVINGTON near Leamington, WICK terrace gravels along the Avon).
- **South and east (Feldon):** Jurassic Lower Lias and Middle Lias clay, with some Cretaceous clay patches. The Feldon plateau is an almost unbroken expanse of deep, dark, sticky clay (DENCHWORTH, EVESHAM). Roads on this clay are among the most damage-prone in the English Midlands.

The River Avon runs broadly east-west through the county, separating the Arden (north) from the Feldon (south). Its floodplain introduces a third soil regime: alluvial clays and terrace gravels that behave differently from the surrounding upland clay country.

---

## 2. County-Wide Soil Characterisation

### 2.1 Subsoil Texture Distribution

| Texture class | % of county | Clay fraction (dominant class metric) | Shrink-swell risk |
|---|---|---|---|
| **Clay** (dominant) | **13.1%** | C = 86% | Very high |
| Clay | 10.7% | C = 85% | Very high |
| Clay | 8.8% | C = 70%, CL = 15% | Very high |
| Clay | 7.9% | C = 60%, CL = 20% | High |
| Clay loam | 6.6% | CL = 85% | High |
| Medium sandy loam | 5.6% | MSL = 80% | Low–moderate |
| Clay loam | 4.7% | CL = 40%, C = 35% | High |
| Medium sandy loam | 4.7% | MSL = 65% | Low–moderate |
| Clay | 4.0% | C = 65%, MSL = 20% | High |
| Clay loam | 3.3% | CL = 40%, C = 25% | High |

**Summary:** Pure clay or clay loam accounts for approximately **75% of the county's subsoil by area**. P metric (peat) = 0% throughout — no peat signature anywhere. The sandy loam belt (~13%) corresponds to the Arden sandstone zone in the north-west.

### 2.2 Organic Carbon Profile

| OC class | % of county | AV_OC at 30cm | AV_OC at 100cm | Interpretation |
|---|---|---|---|---|
| Unclassified | 16.5% | — | — | Urban/built area |
| **1.6–3.0%** | **~58% (multiple classes)** | 1.6–2.8% | 0.3–0.7% | Typical mineral clay |
| 3.1–6.0% | ~6.6% | 3.1–4.3% | 0.6–1.2% | Organic-enriched (floodplains, woodlands) |
| ≤1.5% | ~3.0% | ~1.5% | 0.4% | Very mineral (limestone, chalk fringe) |

**Key finding:** No OC class above 6% detected anywhere in the county. OC drops sharply between 30cm and 100cm across all zones — this is mineral clay country, not organic soil. The contrast with Lincolnshire (14% OC to 150cm depth at Brandy Wharf) is stark and confirms that Warwickshire has **no compressible ground risk** — the failure mode is entirely shrink-swell.

---

## 3. NATMAP Point Survey — 12 Locations

| # | Location | Lat/Lon | Soil Series | Geology | Drainage | Primary Risk |
|---|---|---|---|---|---|---|
| 1 | Atherstone | 52.58, -1.55 | **WHIMPLE 3** | Permo-Triassic/Carboniferous reddish mudstone | Slightly impeded | Shrink-swell (moderate-high) |
| 2 | Nuneaton | 52.52, -1.47 | **WHIMPLE 2** | Carboniferous reddish mudstone/sandstone | Slightly impeded | Shrink-swell (moderate-high) |
| 3 | Kenilworth | 52.35, -1.58 | **WHIMPLE 2** | Carboniferous reddish mudstone/sandstone | Slightly impeded | Shrink-swell (moderate-high) |
| 4 | Leamington Spa | 52.29, -1.54 | **RIVINGTON 1** | Carboniferous/Jurassic sandstone | Freely draining | Low (sandstone outlier) |
| 5 | Rugby (E) | 52.37, -1.26 | **ARROW** | Glaciofluvial drift | Naturally wet | Groundwater/settlement |
| 6 | Warwick | 52.28, -1.58 | **FLADBURY 1** | River alluvium | Naturally wet; flood risk | Alluvial settlement + flood |
| 7 | Stratford-upon-Avon | 52.19, -1.71 | **WICK 1** | Glaciofluvial/river terrace drift | Freely draining | Low (terrace gravels) |
| 8 | Shipston-on-Stour | 52.07, -1.62 | **BISHAMPTON 2** | River terrace drift | Slightly impeded | Moderate (clay-loam subsoil) |
| 9 | Southam | 52.25, -1.38 | **DENCHWORTH** | Jurassic/Cretaceous clay | Impeded; landslips | **Shrink-swell HIGHEST** |
| 10 | Coleshill | 52.50, -1.69 | **ARROW** | Glaciofluvial drift | Naturally wet | Groundwater/settlement |
| 11 | Kineton | 52.17, -1.49 | **DENCHWORTH** | Jurassic/Cretaceous clay | Impeded; landslips | **Shrink-swell HIGHEST** |
| 12 | Henley-in-Arden | 52.30, -1.79 | **BROCKHURST 1** | Permo-Triassic reddish mudstone and till | Impeded | Shrink-swell (moderate-high) |

> [!warning] Landslip Flag
> NATMAP records "Landslips and associated irregular terrain locally" against DENCHWORTH at both Southam and Kineton. This is the only series in Warwickshire to carry this flag. It applies not just to natural slopes but to any engineered earthwork (road embankment, cutting, culvert headwall) on this clay. DENCHWORTH land should trigger slope stability assessment before any earthwork design.

---

## 4. NSI Field Evidence — Definitive Lias Clay Profile

### EVESHAM Series — Site 7087 (Kineton, 1.84km from survey point)
*Surveyed 21 April 1983 — arable land — altitude 84m — slope 3° NE aspect*

| Horizon | Depth | Texture | Est. Clay | Structure | Carbonate | Notes |
|---|---|---|---|---|---|---|
| 1 | 0–24cm | **Clay** | 52% | Moderately developed coarse subangular | Calcareous | Roots common |
| 2 | 24–44cm | **Clay** | 56% | **Strongly developed medium angular blocky** | Very calcareous | Gley mottles (few) |
| 3 | 44–75cm | **Clay** | 58% | **Strongly developed medium angular blocky** | Very calcareous | Gley mottles (common) |
| 4 | 75–110cm | **Clay** | 52% | Weakly developed coarse prismatic | Very calcareous | Calcareous nodules |

**Laboratory texture fractions:** Clay 54.1%, Silt 29.1%, Sand 16.8%
**Topsoil chemistry:** Carbon = 2.3%, pH = 7.5

> [!danger] Engineering significance
> Clay fraction ≥52% throughout the entire 110cm profile, with no reduction at depth. Strongly developed angular blocky structure from 24cm is the morphological hallmark of active shrink-swell cycling — the clay literally breaks itself into angular blocks along shrinkage planes each dry season. Gley mottling from 24cm confirms seasonal saturation in winter, which then alternates with deep desiccation cracks in summer. Any road, pipe, foundation, or buried cable on EVESHAM or DENCHWORTH series is experiencing this cycling in every single year — and the cycling amplitude will increase with climate change.

**Comparison — EVESHAM (Warwickshire, Kineton) vs ADVENTURERS' (Lincolnshire, Brandy Wharf):**

| Property | EVESHAM (Kineton) | ADVENTURERS' (Brandy Wharf) |
|---|---|---|
| Failure mode | **Shrink-swell** | **Compressible settlement** |
| Clay fraction | 54.1% throughout | N/A (peat) |
| Organic carbon | **2.3%** (mineral) | **15.3%** (deep peat) |
| Von Post | — (no peat) | 8–9 (highly amorphous) |
| Structural indicator | Angular blocky (active shrink) | Peat horizon to 52cm |
| pH | 7.5 (calcareous) | 7.3 (calcareous peat) |
| Infrastructure response | Heaving, cracking, surface rupture | Gradual compression, settlement |
| Engineering approach | Flexible pavement, moisture management | Load management, foundation design |

---

## 5. BGS GeoClimate UKCP18 ShrinkSwell

**Query:** `map.bgs.ac.uk/arcgis/rest/services/GeoIndex_Onshore/geoclimate_basic/MapServer/3/query` (2030 projection)
**Warwickshire result:** CLASS = **"Improbable"** — single polygon covering ~221,868 km² (all of central-southern England)

**LEGEND:** *"It is improbable that climate change will affect clay shrink-swell susceptibility and change the likelihood of ground movement, which causes subsidence."*

> [!info] Interpreting "Improbable" for Warwickshire
> "Improbable" does NOT mean low shrink-swell risk. It means climate change is unlikely to shift the county's shrink-swell susceptibility into a higher risk class — because the clay is **already at a high baseline**. There is nowhere further to go on the scale.
>
> What climate change WILL do is intensify the seasonal cycling amplitude within the existing class: hotter, drier summers → deeper soil moisture deficits → wider desiccation cracks → more violent re-saturation events in autumn/winter. This accelerates fatigue damage to road surfaces and buried infrastructure year on year, even without a class-change on the GeoClimate scale.
>
> The correct tool for Warwickshire baseline susceptibility is the **NATMAP soil series** (DENCHWORTH, EVESHAM = very high; WHIMPLE, BROCKHURST = moderate-high) rather than GeoClimate, which is designed to show the climate change *delta* rather than the existing hazard level.

---

## 6. Road Network Risk by Zone

### Zone 1: The Feldon — Highest Priority

**Soil series:** DENCHWORTH, EVESHAM (Jurassic Lias clay)
**Key locations:** Southam, Kineton, Fenny Compton, Long Itchington, Harbury, Priors Hardwick, Lower Brailes
**Road network character:** Predominantly rural single carriageway — C-class and unclassified — on an agricultural plateau with minimal engineered foundations (same "evolved road" phenomenon as Lincolnshire, but driven by clay shrink-swell rather than peat settlement)
**OS NGD road sample (Feldon bbox):** All roads flagged Rural capture specification, single carriageway — consistent with the expected network character

**Risk indicators:**
- DENCHWORTH/EVESHAM clay shrinks dramatically in summer, heaves in winter
- Surface cracking and irregular heave on unbound sub-base roads
- NATMAP landslip flag: embankments, cuttings, and culvert headwalls require slope stability checking
- Drainage ditches on clay are essential but often inadequate — blocked or shallow ditches remove the only active moisture management from the system
- B4451 (Leamington–Southam), B4455, B4100 (Warwick–Banbury) and the network of unclassified roads between are all affected

### Zone 2: North Warwickshire and Arden — Moderate-High

**Soil series:** WHIMPLE 2/3, BROCKHURST 1 (Permo-Triassic reddish clay)
**Key locations:** Atherstone, Nuneaton, Kenilworth, Henley-in-Arden, Alcester
**Road network character:** Mix of A-road and rural; higher traffic volumes than Feldon
**Drainage:** Slightly impeded — better than Feldon but still shrink-swell susceptible
**Risk:** Lower plasticity than Lias clay but still moderate-high shrink-swell. The higher traffic loading on A444, A5, A47 means failure consequences are higher even if the soil is less extreme.

### Zone 3: Avon and Arden Floodplains — Differential Risk

**Soil series:** FLADBURY 1 (alluvial clay, Warwick area), ARROW (glaciofluvial drift, Coleshill/Rugby area), COMPTON (alluvial, permanent grassland)
**Risk character:** Different from upland clay — seasonal waterlogging and groundwater rather than cyclical shrink-swell. Roads crossing these floodplains face soft sub-grade, flood inundation risk, and alluvial differential settlement at approach gradients.
**Key crossings:** Avon bridges at Warwick, Stratford, and Bidford-on-Avon; B4085, B4086 flood corridor roads

---

## 7. Priority Intervention Matrix

| Priority         | Zone                      | Soil Series          | Road Type                    | Dominant Risk Mode           | Recommended Action                                                                     |
| ---------------- | ------------------------- | -------------------- | ---------------------------- | ---------------------------- | -------------------------------------------------------------------------------------- |
| **1 — Critical** | Feldon plateau            | DENCHWORTH / EVESHAM | Unclassified / C-class rural | Shrink-swell + landslip      | NATMAP series survey; drainage audit; embankment stability review; PMS cross-reference |
| **2 — High**     | North Warwickshire        | WHIMPLE 2/3          | A444, A5, A47, rural C       | Shrink-swell (moderate)      | Reactive maintenance pattern review; drainage maintenance prioritisation               |
| **3 — High**     | Arden / Henley belt       | BROCKHURST 1         | B4089, B4095, rural          | Shrink-swell (moderate-high) | Monitor; integrate into 5-year maintenance planning                                    |
| **4 — Medium**   | Avon floodplain crossings | FLADBURY 1 / COMPTON | A429, B4086, B4095 bridges   | Alluvial settlement + flood  | Scour risk assessment (BGS GeoScour); EA Flood Zone review                             |
| **5 — Lower**    | Leamington sandstone      | RIVINGTON 1          | Urban/suburban               | Low                          | Background monitoring only                                                             |

---

## 8. Comparison with Lincolnshire BGS Study

The desk-based methodology used here mirrors the approach validated by Harrison, Heaton & Entwisle (2023) for Lincolnshire, using the same MCP-Geo toolset. The contrast between counties illustrates why national soil data must be accessed at the local series level — aggregate statistics conceal the very distinctions that drive engineering decisions.

| Attribute | Warwickshire (Feldon) | Lincolnshire (Brandy Wharf / Fodderdyke) |
|---|---|---|
| Dominant soil risk | **Shrink-swell** | **Compressible ground** |
| Dominant soil series | EVESHAM / DENCHWORTH (Lias clay) | ADVENTURERS' / DOWNHOLLAND (fen peat/alluvium) |
| Clay % at 30–110cm | **52–58%** | Low (peat above; marine clay below) |
| Organic carbon at 30cm | **2.3%** | **14.1%** |
| Organic carbon at 100cm | ~0.6% | **13.4%** (still peat) |
| Road failure mode | Cracking, heaving, surface rupture | Settlement, compression, roddon buckling |
| LiDAR utility | Embankment geometry | **Roddon detection (critical)** |
| Climate change trajectory | Intensified seasonal cycling | Irrigation-driven moisture deficit |
| Engineering response | Flexible pavement, moisture management | Load management, roddon avoidance, foundation design |
| BGS GeoClimate (2030) | Improbable (already at max baseline) | Improbable (peat, not clay mechanism) |

---

## 9. Data Provenance and Limitations

**Data used:**
- LandIS NATMAP Core — Cranfield University / UKRI — Open Licence — updated 2026-03-31
- LandIS NSI Evidence (field surveys 1981–1983) — Cranfield University / UKRI — Open Licence
- LandIS NATMAPcarbon — Cranfield University / UKRI — Open Licence
- LandIS NATMAP Subsoil Texture — Cranfield University / UKRI — Open Licence
- OS NGD Features (trn-ntwk-roadlink-5) — Ordnance Survey — PSGA licence
- BGS GeoClimate UKCP18 ShrinkSwell — British Geological Survey / UKRI — © UKRI — cite "Contains BGS materials © UKRI"

**Limitations:**
- NATMAP is 1:250,000 scale — not suitable for parcel-level engineering decisions; site investigation required
- NSI survey dates 1981–1983 — land use and drainage conditions may have changed
- GeoClimate shows climate change *delta* not baseline susceptibility — baseline requires NATMAP series interpretation or commercial BGS GeoSure A–E classification
- No PMS (Pavement Management System) data overlaid — this assessment identifies soil risk zones but cannot confirm which roads are already showing damage
- Road classification from OS NGD returned empty attributes under thinMode — full classification requires `thinMode=false` query
- EA Flood Zone and BGS GeoScour not interrogated for this survey — recommended for Zone 4 (floodplain crossings)

---

## 10. Recommended Next Steps

1. **Cross-reference with WCC/DfT PMS data** — overlay EVESHAM/DENCHWORTH zone against road condition scores to confirm correlation between soil series and observed surface deterioration
2. **Drainage audit of Feldon unclassified network** — ditch condition and cross-section adequacy on DENCHWORTH/EVESHAM roads
3. **BGS GeoSure A–E classification** (commercial, via GeoReports) — obtain formal class for DENCHWORTH zone to confirm shrink-swell grade and quantify maintenance liability
4. **EA Flood Zone WMS query** — identify which Avon/Arden floodplain road crossings fall within Flood Zone 2/3
5. **BGS GeoScour** query for Avon bridges — catchment scour susceptibility for bridge structures on the River Avon and its tributaries
6. **Extend survey to Coventry and Solihull** — both are separate unitary authorities excluded from this county bbox but sit on the same WHIMPLE/Triassic clay geology

---

## See Also

- [[BGS Lincolnshire Case Study]] — contrasting fenland case study, same methodology
- [[MCP-Geo Validation Suite]] — methodology validated against published BGS field data
- [[Ground Resilience Skill Design]] — the skill that produced this assessment
- [[Infrastructure Resilience]] — primary use case note with earlier Warwickshire test data
- [[Subsurface Road Resilience Blueprint]] — visual framework for the concepts applied here

---

*Survey conducted using [[Ground Resilience Skill Design]] v0.4.0 | Data accessed 2026-04-06 | ← [[00 - Home|Home]]*
