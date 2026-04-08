---
aliases: [infrastructure resilience, ground failure, earthworks, climate adaptation, buried assets]
tags: [use-case, infrastructure, resilience, ground-movement, climate, engineering, landslide, shrink-swell]
confidence: high
priority: PRIMARY
status: validated-in-test
test_area: "Warwickshire M40/rail corridor (52.25–52.35°N, 1.45–1.65°W)"
---

# Infrastructure Resilience — Ground Failure and Climate Risk

> [!abstract] The Core Use Case
> **Climate change is increasing the frequency and severity of ground failure events that damage or destroy roads, railways, buried pipes, cables, pylons and their foundations.** The four primary failure modes — shrink-swell, slope instability, settlement, and scour — are all driven or amplified by soil type, moisture regime, and the geometry of engineered earthworks. LandIS + OS NGD + BGS GeoSure + UKCP18 form the combined evidence base to screen, prioritise and investigate risk systematically across UK infrastructure.

---

## The Four Failure Modes

### 1. Shrink-Swell Ground Movement
**Mechanism:** Clay-rich soils expand when wet and contract when dry. Magnitude of movement is proportional to clay plasticity and the severity of moisture change.

**Infrastructure impact:**
- Foundation movement → cracking and differential settlement of structures
- Pipe joint failure → leakage and asset deterioration
- Road surface deformation → pothole clustering, pavement failure
- Cable duct distortion → service interruption and joint failure

**Climate driver:** Hotter, longer summer droughts increase soil moisture deficit → greater shrinkage. Wetter winters increase swelling. The amplitude of the seasonal cycle increases under most UKCP18 scenarios.

**Soil indicator in LandIS:** `natmap-subsoil-texture` (clay fraction in subsoil) — the primary available proxy. Heavy clay subsoil (>50% clay) = high shrink-swell potential. BGS GeoSure provides a dedicated shrink-swell hazard layer with 5 risk classes.

**Key soil types:** London Clay, Lias Clay, Oxford Clay, Gault Clay, Mercia Mudstone, Kimmeridge Clay — widespread across central/southern England and the main rail/road corridors.

---

### 2. Slope Instability and Earthworks Failure
**Mechanism:** Railway embankments and road cuttings are engineered earthworks that rely on soil shear strength remaining above a critical threshold. Prolonged rainfall, rapid snowmelt, or toe erosion can trigger slips.

**Infrastructure impact:**
- Embankment slips → track misalignment, speed restrictions, line closures
- Cutting failures → debris on track or road, access blocked
- Landslides on natural slopes adjacent to infrastructure → overtopping/burial

**Climate driver:** More intense winter rainfall events → faster pore pressure build-up → lower effective stress → failure. The number of high-intensity rainfall events is increasing under all UKCP18 scenarios.

**Critical OS NGD finding (validated in Warwickshire test):**
> [!success] Live Test Result
> `lnd-fts-landform-1` with description = **"Artificial Slope For Transport"** directly identifies embankments and cuttings of road and rail infrastructure. In the Warwickshire test bbox, **multiple features were returned immediately**, confirming this is the correct entry point for identifying high-risk earthwork assets.

**BGS data:** National Landslide Database (OGC API: `ogcapi.bgs.ac.uk/collections/landslideindex`) — 18,000+ landslide records, many adjacent to infrastructure.

---

### 3. Settlement of Embankments on Soft Ground
**Mechanism:** Roads and railways cross river valleys on embankments built over compressible alluvium, peat, or made ground. Long-term consolidation and seasonal shrinkage cause differential settlement.

**Infrastructure impact:**
- Track geometry deterioration → speed restrictions and increased maintenance
- Road surface undulation → driver safety and surfacing costs
- Bridge approach problems → bump at end of bridge (soil settles, structure doesn't)

**Climate driver:** Changes to groundwater table and soil moisture → altered consolidation behaviour. Peat desiccation under drought → irreversible volume loss.

**Soil indicator in LandIS:** `natmap-carbon` (high carbon = peat/organic soil candidate) + `natmap-subsoil-texture` (silty/sandy subsoil over compressible alluvium) + `NSIfeatures` (flood-risk indicator at monitoring points).

---

### 4. Scour and Erosion at Hydraulic Structures
**Mechanism:** Bridge piers, culverts, and outfalls are vulnerable to scour when peak flow velocities exceed the erosion threshold of foundation soils. Culverts can collapse when flows exceed design capacity.

**Infrastructure impact:**
- Bridge pier undermining → structural failure risk
- Culvert blockage/collapse → road or track closure
- Erosion of embankment toes adjacent to watercourses

**Climate driver:** More intense, shorter-duration rainfall events → higher peak flows → increased scour energy. Design return periods need revision.

**Data needed:** EA Flood Zones + OS Water Network (`wtr-ntwk-waterlink-2`) + OS Routing Structures (`trn-rami-routingstructure-1` — bridges and tunnels) + UKCP18 peak flow projections.

---

## Live Test Results — Warwickshire Corridor

**Test area:** [-1.65, 52.25, -1.45, 52.35] covering Leamington Spa / Rugby corridor (M40, A46, WCML, Chiltern Line).

| Tool | Result | Significance |
|---|---|---|
| `landis_catalog_list_products` | ✅ 16 products catalogued, 178 archive Feature Services | Full LandIS estate confirmed |
| `landis_natmap_point` | ✅ **LIVE** — routed via archive ArcGIS REST (Apr 6, 2026) | Warehouse issue resolved; direct archive routing |
| `landis_natmap_thematic_area_summary` | ✅ **LIVE** — subsoil texture, carbon, available water all returned | Wetness/HOST still absent from productId enum (Q11) |
| `landis_nsi_nearest_sites` | ✅ **LIVE** — NSI site locations returned | 5 NSI sites within 10km of Warwickshire test point |
| `landis_archive_list_items` | ✅ **178 Feature Services** — NATMAP2000 (39k polys), AUGERsite (141k pts+421k profile pts), NATMAPsubstratetexture (19k), NATMAPsubsoiltexture (19k), NATMAPassociations, HORIZONfundamentals, SOILSERIES, NATMAPcarbon (166k polys) | Rich archive fully accessible |
| `os_features_collections (road)` | ✅ `trn-ntwk-roadlink-5` (latest), `trn-fts-roadtrackorpath-3`, maintenance + reinstatement layers | Complete strategic road network queryable |
| `os_features_collections (rail)` | ✅ `trn-fts-rail-3` (latest), `trn-ntwk-railwaylink-1`, `trn-ntwk-railwaylinkset-1`, railway nodes | Full rail network queryable |
| `os_features_collections (water)` | ✅ `wtr-ntwk-waterlink-2`, `wtr-fts-water-3`, water nodes/link sets | Complete watercourse network for scour analysis |
| `os_peat_layers` | ✅ England Peat Map (extent+depth), Peat Condition Register; NGD hydrology + land cover proxies live | Peat/compressible ground screening available |
| BGS GeoSure (external) | ✅ `ogcapi.bgs.ac.uk` — 6 hazard layers (shrink-swell, landslide, compressible, collapsible, dissolution, running sand), 1:50k, OGL | **Most important external layer for this use case** |

### Warwickshire Corridor — Actual LandIS Data (April 6, 2026)

Bbox: [-1.65, 52.25, -1.45, 52.35] (Leamington/Rugby, ~152 km²)

**Subsoil texture breakdown:**
| Texture | % of area | Shrink-Swell Implication |
|---|---|---|
| Clay (C metric 55–100%) | ~33% | **Very High** — Lias/Mercia Mudstone country |
| Clay loam (CL metric 35–45%) | ~28% | **High** |
| Medium sandy loam | ~39% | Low — but note: some classes have 15–20% C component |
| Silty clay | 0.4% | Medium |

**Combined clayey subsoil (clay + clay loam + silty clay): ~61% of the area.** This confirms the Warwickshire corridor is high shrink-swell risk terrain. The sandy loam fraction likely represents Triassic sandstone outcrops (e.g. Keuper Sandstone inliers) and river gravel terraces.

**Topsoil organic carbon:**
- Predominantly mineral soils: 1.6–3.0% OC (typical agricultural mineral soil) covering ~50% of area
- Higher OC patches (3.1–6.0%): ~7% of area — likely river floodplain alluvial soils (Avon, Learn valleys)
- Elevated (6.1–12%): 1.2% of area — localised organic enrichment near watercourses
- Unclassified: 19.5%

**Conclusion:** This is primarily **mineral clay country** — shrink-swell is the dominant risk mode. No significant peat/compressible ground risk (low OC across most of the area). Risk priority: shrink-swell (score 4–5/5) > slope instability > scour > settlement.

### Key Gap Identified
> [!warning] Wetness and HOST not in current thematic API
> The valid thematic `productId` values are: `natmap-available-water`, `natmap-carbon`, `natmap-soilscapes`, `natmap-subsoil-texture`, `natmap-substrate-texture`, `natmap-topsoil-texture`, `natmap-wrb2006`. **Wetness class and HOST are absent.** These are the most critical layers for drainage and slope instability assessment. They must be added from the LandIS archive ArcGIS Feature Services or from BGS GeoSure.

---

## The Complete Data Stack

### Available Now (mcp-geo)
| Dataset | Relevance | Access Status |
|---|---|---|
| `natmap-subsoil-texture` | Clay content → shrink-swell proxy | ⚠️ Warehouse (offline now) |
| `natmap-carbon` | Peat/organic soil → settlement risk | ⚠️ Warehouse (offline now) |
| `natmap-available-water` | Moisture dynamics | ⚠️ Warehouse (offline now) |
| LandIS Archive (178 services) | Full NATMAP, NSI, AUGER — direct ArcGIS Feature Service REST URLs | ✅ ArcGIS REST endpoints live (confirmed April 2026) |
| `lnd-fts-landform-1` | Embankments, cuttings, slopes | ✅ OS NGD live |
| `trn-ntwk-roadlink-5` | Strategic road network | ✅ OS NGD live |
| `trn-ntwk-railwaylink-1` | Rail network | ✅ OS NGD live |
| `trn-rami-routingstructure-1` | Bridges and tunnels | ✅ OS NGD live |
| `wtr-ntwk-waterlink-2` | Watercourse network | ✅ OS NGD live |
| `str-fts-compoundstructure-3` | Bridges, dams, aqueducts | ✅ OS NGD live |

### Needs Adding (External APIs — confirmed available)
| Dataset | Relevance | API Endpoint |
|---|---|---|
| **BGS GeoSure** — Shrink-swell | 5-class susceptibility (A–E). Clay soils across central/SE England rated C–E | `ogcapi.bgs.ac.uk` + WMS at `data.gov.uk` (OGL) |
| **BGS GeoSure** — Landslide | Slope instability susceptibility. Links to 18k+ National Landslide DB records | Same OGC API |
| **BGS GeoSure** — Compressible Ground | Settlement risk on peat, alluvium, soft clay | Same OGC API |
| **BGS GeoSure** — Collapsible Deposits | Loess, brickearth; collapse on wetting | Same OGC API |
| **BGS GeoSure** — Dissolution | Chalk, limestone, gypsum; sinkhole risk | Same OGC API |
| **BGS GeoSure** — Running Sand | Saturated granular soils; liquefaction risk | Same OGC API |
| **BGS National Landslide DB** | 18,000+ historical landslide records, many adjacent to infrastructure | `ogcapi.bgs.ac.uk/collections/landslideindex` |
| **BGS DiGMapGB-50** | 1:50k superficial + bedrock geology; clay type confirmation | BGS WMS (INSPIRE compliant) |
| **EA Flood Zones 1–3** | Waterlogging, scour, embankment toe | `environment.data.gov.uk/spatialdata/flood-map-for-planning-rivers-and-sea-flood-zone-2/wms` |
| **UKCP18 Climate Projections** | Future rainfall/temperature changes | `ukclimateprojections-ui.metoffice.gov.uk` (WPS + CEDA) |
| **EGMS InSAR** | Observed ground movement (mm accuracy) | `egms.land.copernicus.eu` |
| **NATMAP Wetness** | Drainage class (missing from thematic API) | LandIS archive ArcGIS REST |
| **NATMAP HOST** | Hydrological response | LandIS archive ArcGIS REST |

---

## MCP Tool Workflow (Proposed)

For a given corridor or area:

```
Input: Route/area geometry + infrastructure type + risk modes + time horizon
           │
           ▼
Step 1: OS NGD — identify assets and earthworks
  trn-ntwk-roadlink-5 + trn-ntwk-railwaylink-1
  → strategic asset inventory
  lnd-fts-landform-1 (Artificial Slope For Transport)
  → embankment/cutting locations
  trn-rami-routingstructure-1
  → bridges and tunnels
  wtr-ntwk-waterlink-2
  → watercourse crossings (scour risk)
           │
           ▼
Step 2: LandIS — soil characterisation
  natmap-subsoil-texture → clay content (shrink-swell proxy)
  natmap-carbon → organic soil (settlement risk)
  LandIS archive: NATMAP wetness (via ArcGIS REST)
  LandIS archive: NATMAP HOST (via ArcGIS REST)
  AUGERsite → site-specific observations near assets
           │
           ▼
Step 3: BGS GeoSure — hazard classification
  Shrink-swell class per polygon
  Landslide susceptibility class
  Compressible ground class
  BGS Landslide DB — historical events near corridor
           │
           ▼
Step 4: Hydrological context
  EA Flood Zones → waterlogging and scour exposure
  HOST + Wetness → drainage characterisation
           │
           ▼
Step 5: Climate sensitivity
  UKCP18 projections → future moisture deficit change
  Translate to hazard amplification factors per soil type
           │
           ▼
Step 6: EGMS InSAR (where available)
  Observed ground movement at asset locations
  → validation of modelled risk
           │
           ▼
Output: Structured risk report per asset/earthwork
  → Risk scores per failure mode (1–5)
  → Hotspot map of priority locations
  → Verification checklist (ground investigation targets)
  → Data provenance block
  → Confidence rating
```

---

## Key Stakeholders
- [[Stakeholders#🔧 Utilities and Infrastructure Planners]] — pipes, cables
- Network Rail — earthworks, bridges
- National Highways — motorways, A-roads
- NGET / DNOs — pylons, substations
- Water companies — mains and sewers on slopes
- Local highway authorities — county roads

---

## See Also
- [[UK Ground Risk Strategy]] — how to scale this nationally
- [[Ground Resilience Skill Design]] — the skill specification
- [[Utilities and Engineering]] — current pipe corrosion use case
- [[Hydrology and Flood]] — hydrological context
- [[Open Questions]] — warehouse availability issue

---
*← [[00 - Home|Home]]  |  Primary contact datasets: [[NATMAP Vector]], [[Interpreted Layers]], [[Horizon Data]]*
