---
aliases: [UK strategy, national ground risk, infrastructure resilience strategy, scale-up]
tags: [strategy, UK, ground-risk, infrastructure, national, AI, scalable]
---

# UK Ground Risk Strategy

> [!abstract] Strategic Goal
> Create a **queryable, AI-accessible national ground risk intelligence system** that any asset manager, planner, or AI agent can interrogate to understand climate-driven ground failure risk to UK infrastructure — without needing GIS expertise, BGS data science skills, or weeks of manual analysis.

---

## The Scale of the Problem

UK infrastructure at risk from climate-driven ground failure:

| Asset Class | Approximate Extent | Primary Risk Modes |
|---|---|---|
| Strategic road network (motorways + A-roads) | ~50,000 km | Shrink-swell, slope failure, scour |
| Rail network | ~32,000 km of track | Embankment failure, cutting slips, scour |
| Water mains | ~340,000 km | Shrink-swell bursts, ground movement |
| Gas distribution mains | ~270,000 km | Shrink-swell, settlement |
| High-voltage transmission lines | ~25,000 km of lines, ~7,000 towers | Foundation movement |
| Distribution cables (electricity) | ~800,000 km | Shrink-swell, ground heave |
| Local highway network | ~320,000 km | Shrink-swell, slope failure |

No organisation currently has a unified, spatially consistent, AI-queryable view across all of these. Each asset owner holds their own records, usually in GIS systems that do not talk to each other and require specialist skills to query.

---

## The Data Foundation

Three confirmed open data estates form the backbone:

### 1. LandIS (Cranfield / Defra) — Soil Evidence
Now open access via portal.landis.org.uk. Provides the fundamental soil characterisation layer — clay content, drainage class, hydrological response, carbon, auger observations — that determines how ground behaves.

**Key datasets for ground risk:**
- NATMAP subsoil texture (clay fraction → shrink-swell proxy)
- NATMAP wetness class (drainage → slope stability, waterlogging)
- NATMAP HOST (hydrological response → flood/drainage timing)
- NATMAP carbon (organic soil → settlement)
- AUGERsite (140k+ field observations → local calibration)

### 2. OS NGD — Infrastructure and Terrain
94 live feature collections covering the full built and transport environment.

**Key collections for ground risk (all confirmed live April 2026):**
- `trn-ntwk-roadlink-5` — road network v5 (latest), full strategic network with classification
- `trn-fts-rail-3` — railway features v3 (latest), permanent way features
- `trn-ntwk-railwaylink-1` — rail network links and nodes
- `trn-ntwk-railwaylinkset-1` — named railway lines (full extent)
- `wtr-ntwk-waterlink-2` — watercourse network v2, rivers + canals (scour exposure)
- `wtr-fts-water-3` — water area polygons v3
- `lnd-fts-land-3` — land features v3 (includes slope, embankment context)
- `lnd-fts-landform-1` — **Artificial Slope For Transport** = embankments/cuttings
- `trn-rami-routingstructure-1` — bridges and tunnels (scour/maintenance)

### 3. BGS — Geohazard Classification (confirmed April 2026)
Open OGC API providing six dedicated hazard layers at 1:50,000:
- GeoSure: shrink-swell (A–E), landslide, compressible ground, collapsible deposits, dissolution, running sand
- National Landslide Database: 18,000+ historical events
- **Primary endpoint:** `https://ogcapi.bgs.ac.uk` (OGC API Features, JSON)
- **WMS fallback:** data.gov.uk dataset `4997fbf6-e3f8-4bbd-bdf9-7c582addbf94`
- **Licence:** Open Government Licence (OGL) — attribute "Contains BGS materials © UKRI"
- Also: BGS DiGMapGB-50 (superficial + bedrock geology, INSPIRE WMS)

### 4. EA, Met Office, Copernicus — Climate and Hydrology
- EA Flood Zones: `environment.data.gov.uk`
- UKCP18 projections: `ukclimateprojections-ui.metoffice.gov.uk`
- EGMS InSAR: `egms.land.copernicus.eu`

---

## Tiling Strategy for National Coverage

The UK cannot be processed as a single query — the geometry is too large and the data volumes are significant. The recommended approach is a **hierarchical tile system** matching existing infrastructure management frameworks.

### Tier 1 — Management Zones (Strategic)
Align with existing asset management frameworks:

| Zone Type | Rationale | Count |
|---|---|---|
| Network Rail Routes (14 routes) | Matches existing maintenance regions | 14 |
| National Highways regions (4 + network) | Matches HA maintenance contracts | 5 |
| Water company areas (17) | Asset management units | 17 |
| Distribution Network Operator areas (6 + 1 transmission) | Grid management units | 7 |

### Tier 2 — Processing Tiles (Operational)
10km × 10km tiles (British National Grid), approximately 2,500 tiles covering England and Wales (4,500 including Scotland).

Each tile is processed with:
1. LandIS soil characterisation (via archive ArcGIS REST)
2. OS NGD asset inventory (roads, rail, earthworks, structures)
3. BGS GeoSure hazard classes
4. EA Flood Zone overlay
5. UKCP18 climate sensitivity scores (2050 and 2080 horizons)
6. EGMS InSAR ground movement (where data available)

Output per tile: a structured JSON document representing the risk landscape, indexable by AI agents.

### Tier 3 — Asset-Level Detail (Tactical)
For priority tiles (high risk score × high asset density):
- AUGERsite observations within 500m of assets
- NSI monitoring points within 5km
- BGS Landslide Database events within 2km
- OS routing structures (bridges, tunnels) inventory

---

## Priority Zones for Phase 1

Not all UK ground is equal. Phase 1 should focus on tiles with the highest combination of:
- **Clay soil extent** (shrink-swell exposure)
- **Infrastructure density** (asset value at risk)
- **UKCP18 moisture deficit change** (climate amplification)
- **Existing earthwork density** (embankments/cuttings)

Based on known soil and geology, the highest priority regions are:

| Region | Soil Reason | Infrastructure at Risk |
|---|---|---|
| London Basin | London Clay (very high plasticity) | TfL, Southern, SE Rail, NRAIL, all utilities |
| SE England (Kent/Surrey) | Gault Clay, Weald Clay, London Clay | HS1, Southeastern, M2/M20/M25 |
| East Midlands | Lias Clay, Mercia Mudstone | WCML, Midland Main Line, M1 |
| Yorkshire (Vale of York) | Lias Clay, alluvium | ECML, TransPennine, A1(M) |
| Somerset Levels | Peat (very compressible) | South West Main Line, A303 |
| Pennines / Welsh Marches | Slope instability, Coal Measures | TransPennine, Welsh routes |

---

## The MCP Architecture at National Scale

```
National Ground Risk MCP Server
            │
     ┌──────┴──────────────────────────────┐
     │                                      │
  Tile Index Layer                    Tool Layer
  ─────────────                       ──────────
  10km grid with pre-computed          Query tools:
  risk summaries per tile              - screen_corridor()
  Indexable by:                        - assess_asset()
  - TOID                               - hotspot_ranking()
  - Grid reference                     - climate_delta()
  - Local authority                    - validate_with_insar()
  - Route/corridor
     │                                      │
     └──────────────┬──────────────────────┘
                    │
         Live API calls (on demand):
         ├── LandIS Archive (ArcGIS REST)
         ├── OS NGD (94 collections)
         ├── BGS GeoSure (OGC API)
         ├── BGS Landslide DB (OGC API)
         ├── EA Flood Zones (OGC API)
         ├── UKCP18 (WPS / CEDA)
         └── EGMS InSAR (Copernicus)
```

### Pre-computation vs On-Demand
**Pre-compute (tile index):**
- Soil texture class per tile (from LandIS archive)
- BGS GeoSure hazard class per tile
- EA Flood Zone exposure per tile
- Earthwork count per tile (from OS NGD landform)
- Composite risk score per tile

**On-demand (live query):**
- Asset-specific details for priority tiles
- UKCP18 climate delta for specific coordinates
- EGMS InSAR movement time series
- AUGERsite observations near a specific asset

---

## Data Gaps and Enablers Needed

### Gap 1 — LandIS Wetness and HOST in Thematic API
The current MCP thematic productIds do not include wetness or HOST — the two most critical layers for drainage and slope stability. These must be added from:
- LandIS archive ArcGIS REST endpoints (confirmed available)
- Or via a dedicated warehouse query once the warehouse is back online

→ **Action:** Add `natmap-wetness` and `natmap-host` as thematic productIds in the MCP server configuration. See [[Open Questions]].

### Gap 2 — BGS GeoSure MCP Tool
No current MCP tool wraps the BGS GeoSure API. A new `bgs_geosure_area_summary(geometry)` tool is needed that:
- Calls `ogcapi.bgs.ac.uk` for each hazard layer
- Returns class distribution per area
- Caches results by tile for performance

### Gap 3 — UKCP18 Climate Delta Tool
A `climate_sensitivity_score(geometry, scenario, horizon)` tool that:
- Queries UKCP18 for summer precipitation deficit and winter rainfall changes at the tile centroid
- Translates to hazard amplification factors (e.g. "shrink-swell hazard × 1.4 by 2050")

### Gap 4 — EGMS InSAR Integration
A `observed_ground_movement(geometry)` tool that:
- Fetches EGMS L3 velocity products for the area
- Returns mean and range of vertical movement (mm/year)
- Flags locations with anomalous movement (>±2mm/year)

### Gap 5 — LandIS Warehouse Resilience (CRITICAL — confirmed April 2026)
The warehouse was confirmed offline during live validation testing (April 2026). The skill MUST:
- Detect `UPSTREAM_CONNECT_ERROR` and fall back to ArcGIS archive endpoints immediately
- **Archive confirmed live:** 178 ArcGIS Feature Services at `services-eu1.arcgis.com/BsCa1SurMySYByZ3/arcgis/rest/services/`
- Cache tile-level results to reduce warehouse dependency
- Flag data freshness in all outputs — "archive fallback used" provenance flag
- See [[Open Questions]] Q12 for warehouse SLA status

---

## Governance and Liability

> [!warning] Critical Governance Requirement
> Ground failure risk assessment for infrastructure has significant liability implications. The system must:
> - Never imply site-level certainty from 1:250k soil data
> - Always attach data provenance and scale limitations to outputs
> - Always recommend professional ground investigation for design decisions
> - Distinguish clearly between **screening** (this system) and **assessment** (requires site investigation)
> - Track dataset versions and dates in all outputs

The system is a **screening and prioritisation tool**, not a substitute for geotechnical investigation. Every output must say so explicitly.

---

## Implementation Phasing

### Phase 1 — Proof of Concept (1 corridor)
Build and validate the skill on one defined test corridor (e.g. Leamington–Rugby: M40/WCML/A46).
- Validate all data sources live
- Build composite risk score algorithm
- Test with a domain expert (geotechnical engineer)
- Document confidence and calibration notes

### Phase 2 — Priority Zone Roll-out (6 regions)
Process the six highest-priority regions (see above) with pre-computed tile index.

### Phase 3 — National Coverage
Tile the full GB grid. Automate via scheduled tasks. See [[schedule skill]].

### Phase 4 — Asset Owner Integration
Work with Network Rail, National Highways, and utility asset owners to:
- Cross-reference with their asset registries
- Add proprietary inspection data layers
- Enable role-based query scoping

---

## See Also
- [[Infrastructure Resilience]] — the use case note
- [[Ground Resilience Skill Design]] — the skill specification
- [[Implementation Roadmap]] — LandIS MCP roadmap
- [[Open Questions]] — data access gaps

---
*← [[00 - Home|Home]]*
