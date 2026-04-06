---
aliases: [roadmap, MVP, implementation plan, LandIS roadmap]
tags: [mcp, roadmap, implementation, strategy, landis]
---

# Implementation Roadmap

> [!abstract] Strategic Logic
> MCP is the right **first move** for the open access transition — a rapid value-discovery harness that surfaces user needs and informs the design of future formal APIs. It is not a substitute for geospatial API productisation, but it is strategically useful as a demonstrator and orchestration layer.

## Phase 1 — Immediate Discovery

**Goal:** Validate what exists and what is possible before building.

- [ ] Validate what the open access portal exposes: dataset list, licences, API endpoints, bulk downloads, query limits → [[Open Questions]]
- [ ] Build an internal **LandIS product registry**: documented dataset families + ISO metadata + version labels + provenance notes
- [ ] Identify 3–5 high-value pilot workflows aligned to evidenced demand:
  - Flood/catchment screening
  - Wetness/carbon screening for ELMS
  - Utilities corrosion/shrink-swell screening
  - Planning evidence packs for local authorities

**Output:** Product registry document + confirmed access method for each dataset.

---

## Phase 2 — MVP MCP Server

**Goal:** A working server with highest-value tools that demonstrate the proposition.

### Implement First
1. `landis_catalog_list_products()` — entry point for all users
2. `landis_metadata_get(product_id)` — provenance foundation
3. `landis_soilscapes_point()` + `landis_soilscapes_area_summary()` — highest accessibility
4. `landis_natmap_point()` + `landis_natmap_area_summary()` — core spatial access
5. `landis_natmap_thematic_area_summary()` — HOST, wetness, carbon
6. `landis_nsi_nearest_sites()` + `landis_nsi_profile_summary()` — monitoring data
7. **Hero derived tool:** `landis_derive_pipe_risk()` — strongest documented use case (utilities)

### Ship With
- Prompt templates for 3 pilot personas:
  - Local authority planner
  - Water utility analyst
  - Catchment manager

### Success Criteria (MVP)
- All outputs include provenance + caveat block
- No output implies site-level certainty
- Demonstration to at least one stakeholder group

---

## Phase 3 — Spatial Data Ingestion

**Goal:** Build a reliable spatial execution layer for production queries.

If bulk data is available from the portal:

```
Spatial warehouse (PostGIS or equivalent):
  ├── Soilscapes polygons + attributes
  ├── NATMAPvector polygons + NATMAPlegend + NATMAPassociations
  ├── Selected derived layers:
  │     ├── Wetness
  │     ├── HOST
  │     └── Carbon
  └── NSI points (self-standing dataset)
```

**Aggregation defaults** must be documented and consistent:
- Dominant series (by %) for single-value outputs
- Weighted average for continuous properties
- Uncertainty flag when no dominant series exists (e.g. >3 species each ~33%)

---

## Phase 4 — Pilot Stakeholder Evaluation

**Goal:** Test with real users from target groups.

**Target pilot organisations:**
- Defra cross-policy data team
- Environment Agency flood risk team
- At least one local planning authority
- One water utility asset risk team
- One conservation/habitat planning partner

**Evaluation questions:**
1. Does access time for "basic soil constraints for an area" drop from days/weeks to minutes?
2. Do users correctly interpret limitations (measured by caveat recall)?
3. Which tools get used most? What follow-up data do users demand?

**Success metrics:**
- Adoption: active users, repeat usage
- Quality: % of outputs including provenance/limitations; user trust score
- Efficiency: time saved in evidence pack creation; reduction in duplicate GIS work

---

## Phase 5 — API and Service Evolution

**Goal:** Promote stable feature-level APIs for high-demand use cases.

- Promote **OGC API – Features** (or equivalent) for key layers where demand and governance justify it
- Keep MCP as the **orchestration and semantic layer** composing across multiple datasets and servers
- MCP tools evolve to call formal APIs rather than local data stores where possible

**Long-term target architecture:**

```
User / AI Agent
      │
      ▼
MCP Semantic Layer  ←──── Schema/prompt resources
      │
      ├── LandIS OGC API (feature-level)
      ├── OS APIs (addresses, network, boundaries)
      ├── Environment Agency APIs (flood zones)
      └── Planning data APIs
```

---

## Open Questions That Gate Progress

The following must be resolved before moving to Phase 3. See [[Open Questions]] for detail.

1. What datasets are included in "open access" on the portal?
2. What is the licence text — does it permit redistribution and derivatives?
3. Are there bulk download packages with stable version identifiers?
4. Are programmatic endpoints available (REST, OGC API, WFS)?
5. What are the recommended aggregation defaults for series/horizon joins?

---
*← [[00 - Home|Home]]  |  See also: [[MCP Overview]], [[Open Questions]], [[Stakeholders]]*
