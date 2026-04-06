---
aliases: [Home, Index, LandIS Hub]
tags: [landis, index, hub]
created: 2026-04-06
---

# LandIS Knowledge Base

> [!abstract] What is LandIS?
> **LandIS** (Land Information System) is the UK's definitive national soil and land information system, operated by **Cranfield University** for England and Wales. It holds 60+ years of digital soil survey data and is jointly owned by Cranfield and the Crown (Defra). As of 2026, LandIS has become **Open Access**, transforming from a restricted specialist resource into national open data infrastructure.

![[UK Soil Data Engine Infographic.png]]

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

### 🔌 MCP Architecture
Exposing LandIS to AI agents via the Model Context Protocol.

| Note | Summary |
|---|---|
| [[MCP Overview]] | Why MCP is a strong fit — access, semantic, assurance layers |
| [[Primitive Tools]] | Deterministic spatial query tools |
| [[Derived Semantic Tools]] | Higher-order interpretation tools with guardrails |
| [[Resources and Prompts]] | Static schema, docs and prompt templates |
| [[Implementation Roadmap]] | MVP → pilot → full API evolution |

### 🎯 Use Cases
Documented and emerging applications of LandIS data.

| Note | Summary |
|---|---|
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
- [[Assets/LandIS_MCP_Strategy.pdf|MCP Strategy Slides (PDF)]]
- Full report: *LandIS as AI-accessible soil data infrastructure: evidence, use cases, and an MCP access strategy*
