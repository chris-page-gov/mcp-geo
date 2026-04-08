---
aliases: [Home, Index, LandIS Hub]
tags: [landis, index, hub]
created: 2026-04-06
---

# LandIS Knowledge Base

> [!abstract] What is LandIS?
> **LandIS** (Land Information System) is the UK's definitive national soil and land information system, operated by **Cranfield University** for England and Wales. It holds 60+ years of digital soil survey data and is jointly owned by Cranfield and the Crown (Defra). As of 2026, LandIS has become **Open Access**, transforming from a restricted specialist resource into national open data infrastructure.

![[UK Soil Data Engine Infographic.png]]
*→ [[Assets/UK Soil Data Engine Infographic|Full annotated breakdown of this infographic]]*

---

## Quick Navigation

### 🗄️ Datasets
The four-layer data architecture that powers LandIS.

| Note | Summary |
|---|---|
| [[NATMAP Vector]] | Core 1:250k national soil polygon map — ~300 soil associations |
| [[Soilscapes]] | Simplified 27-class generalisation, free viewer, broad awareness use |
| [[NSI - National Soil Inventory]] | 5km grid point monitoring of topsoil chemistry since ~1980 |
| [[Horizon Data]] | Tabular series/horizon properties (fundamentals + hydraulics) |
| [[Interpreted Layers]] | Derived thematic layers: HOST, Wetness, Carbon, CAW, WRB |
| [[Data Structure and Joins]] | How polygons, series, horizons and NSI connect |

### 📋 Strategy & Policy
The governance context and open-access transition.

| Note | Summary |
|---|---|
| [[Open Access Transition]] | The 2026 shift from restricted to open infrastructure |
| [[Governance and Licensing]] | IPR, Defra/Cranfield agreement, historic constraints |
| [[Stakeholders]] | Who uses LandIS and for what |
| [[UK Ground Risk Strategy]] | National roll-out strategy for infrastructure resilience |

### 🔌 MCP Architecture
Exposing LandIS to AI agents via the Model Context Protocol.

| Note | Summary |
|---|---|
| [[MCP Overview]] | Why MCP is a strong fit — access, semantic, assurance layers |
| [[LandIS MCP Strategy Slides]] | ⭐ Full 5-slide deck: strategic case, four-layer architecture, usability gap, semantic sheath |
| [[Primitive Tools]] | Deterministic spatial query tools |
| [[Derived Semantic Tools]] | Higher-order interpretation tools with guardrails |
| [[Resources and Prompts]] | Static schema, docs and prompt templates |
| [[Implementation Roadmap]] | MVP → pilot → full API evolution |
| [[Ground Resilience Skill Design]] | ⭐ Full skill spec for infrastructure resilience assessment |

### 🎯 Use Cases
Documented and emerging applications of LandIS data.

| Note | Summary |
|---|---|
| [[Infrastructure Resilience]] | ⭐ **PRIMARY** — Roads, rail, pipes, cables, pylons vs climate-driven ground failure |
| [[Warwickshire Ground Resilience Assessment]] | ⭐ **NEW** — Full county desk-based survey (2026-04-06): 12-point NATMAP grid, NSI EVESHAM profile, BGS GeoClimate, 3 risk zones — shrink-swell dominant |
| [[Feldon Priority Zone — Detailed Assessment]] | ⭐ **NEW** — Priority 1 deep-dive: NATMAP series survey, NSI dual profiles (EVESHAM + DRAYTON), 50+ embankments inventoried, drainage audit, PMS cross-reference method |
| [[North Warwickshire — Priority 2 Assessment]] | ⭐ **NEW** — Priority 2: WHIMPLE 2/3 on Triassic Mercia Mudstone; A444/A5/A47 corridor; 6 BGS records (3 railway); reactive maintenance pattern review method |
| [[Arden — Priority 3 Assessment]] | ⭐ **NEW** — Priority 3: BROCKHURST 1+2 + OAK 1 on glacial/Triassic till; 87% clay-loam subsoil; chronic waterlogging; 5-year monitoring framework |
| [[Government and Policy]] | ELMS, Nature Recovery, ALC, NCEA, net zero |
| [[Agriculture and Land Management]] | Drainage, trafficability, crop suitability |
| [[Hydrology and Flood]] | HOST, catchment response, flood risk |
| [[Utilities and Engineering]] | Pipe corrosion, shrink-swell, trenching difficulty |
| [[Biodiversity and Habitat]] | Habitat planning, conservation, wildlife trusts |
| [[Climate and Carbon]] | Carbon stocks, GHG inventory, peat targeting |
| [[Emerging Opportunities]] | AI benchmarks, public tools, contamination triage |

### 📚 Reference
| Note | Summary |
|---|---|
| [[Glossary]] | Key terms, codes and classifications explained |
| [[Key Links and Sources]] | URLs to LandIS pages, data.gov.uk, policy documents |
| [[Open Questions]] | Unresolved issues about the portal and open access |
| [[BGS Lincolnshire Case Study]] | BGS/LCC paper (Harrison et al. 2023) validating GeoSure + UKCP18 for road resilience — compressible ground, evolved roads, peat |
| [[MCP-Geo Validation Suite]] | ⭐ 12 queries run (Q1–Q15): 10 passed, 1 partial, 2 invalidated (GeoSure endpoint corrected) |
| [[Subsurface Road Resilience Blueprint]] | ⭐ 10-slide strategic blueprint — three input nodes, stratigraphic analysis, compressibility data, Roddon Effect, Edge Effect |
| [[Assets/Building Climate-Resilient Roads\|Building Climate-Resilient Roads]] | Infographic — GeoSure deterioration rates, patching vs recycling, Fodderdyke reinforcement, GeoClimate prioritisation |

---

## System at a Glance

```
LandIS Data Architecture
─────────────────────────────────────────────
Layer 4  │ Interpreted Layers    │ HOST · Wetness · Carbon · CAW
Layer 3  │ Attribute Tables      │ SOILSERIES · HORIZON Fundamentals/Hydraulics
Layer 2  │ NATMAP Polygons       │ ~300 associations · 1:250k · OS-registered
Layer 1  │ NSI Point Monitoring  │ 5km grid · ~1980 onwards · 20+ elements
─────────────────────────────────────────────
```

## Live MCP Tools (Active)

These tools are queryable right now via the connected MCP server:

- `landis_natmap_point` — soil association at a coordinate
- `landis_natmap_area_summary` — association breakdown for a polygon
- `landis_soilscapes_point` — Soilscapes class at a coordinate
- `landis_soilscapes_area_summary` — Soilscapes breakdown for an area
- `landis_nsi_nearest_sites` — nearest NSI monitoring points
- `landis_nsi_profile_summary` — chemistry profile for NSI sites
- `landis_nsi_within_area` — NSI sites within a geometry
- `landis_natmap_thematic_area_summary` — thematic layer summaries
- `landis_archive_list_items` / `landis_archive_get_item` — archive access
- `landis_derive_pipe_risk` — corrosion/shrink-swell risk for routes
- `landis_metadata_get` — dataset metadata and provenance
- `landis_catalog_list_products` — list all available LandIS products

> [!tip] Using This Vault with AI
> This knowledge base is structured so that AI agents can navigate it via wikilinks. Start with a specific use-case note (e.g. [[Utilities and Engineering]]) to discover which tools and datasets apply, then follow links to [[Primitive Tools]] for exact query syntax.

---

## Source Documents
- [[LandIS MCP Strategy Slides]] — annotated note with full content from all 5 slides
- [[Assets/LandIS_MCP_Strategy.pdf|MCP Strategy Slides (PDF)]] — original slide deck
- [[Assets/UK Soil Data Engine Infographic|UK Soil Data Engine Infographic]] — annotated breakdown of the overview visual
- [[BGS Lincolnshire Case Study]] — Harrison et al. 2023 (QJEGH) — real-world validation
- Full report: *LandIS as AI-accessible soil data infrastructure: evidence, use cases, and an MCP access strategy*
