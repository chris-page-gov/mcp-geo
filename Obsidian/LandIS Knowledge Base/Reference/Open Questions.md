---
aliases: [open questions, uncertainties, unknowns, portal questions]
tags: [reference, questions, uncertainties, portal, landis]
priority: high
---

# Open Questions

> [!important] These questions gate further development
> The following issues require validation against the open access portal's current operational reality before the MCP implementation can move beyond Phase 1. See [[Implementation Roadmap]].

---

## Portal and Dataset Availability

**Q1: What specific datasets are included in "open access" on the portal?**
- Is NATMAPvector included, or only Soilscapes?
- Are HORIZON Fundamentals and Hydraulics available?
- Is NSI available, or only NATMAP-derived layers?
- What about specialist series datasets (Leacs, Pesticides, Hydrology)?

**Impact:** Determines which MCP tools can be built without local data caching.

---

**Q2: What is the authoritative open-access licence / EULA text?**
- Does the licence permit redistribution of derived outputs?
- Does it permit commercial reuse?
- Does it permit derivative works (e.g. risk scores, classifications)?
- Has the "delete derived data at licence expiry" clause been removed?
- Are there still dataset-specific restrictions for some products?

**Impact:** Determines whether MCP tool outputs can be shared, stored, or embedded in third-party apps.

---

**Q3: Are there bulk download packages with stable version identifiers?**
- Can NATMAPvector be downloaded as a versioned shapefile/GeoPackage?
- Are NSI survey data tables downloadable?
- Is there a changelog documenting changes between dataset versions?

**Impact:** Determines whether a local spatial warehouse is needed for reliable MCP performance.

---

## Programmatic Access

**Q4: Are programmatic query endpoints available?**
- Is there an ArcGIS REST API alongside the WMS?
- Is there an OGC API – Features endpoint (the recommended modern standard)?
- Is there a WFS endpoint for vector feature queries?
- Are there query limits, rate limits, or authentication requirements?

**Impact:** Determines MCP implementation architecture — whether tools call live APIs or query local data.

---

**Q5: What does the WMS support beyond GetMap?**
- Does GetFeatureInfo work on the WMS endpoints?
- Can attributes (MUSID, class codes) be retrieved via WMS, or only map images?

---

## Data Model and Aggregation

**Q6: What are the recommended aggregation defaults?**
When computing weighted averages across a polygon's component series, what is the official guidance?
- Dominant series only (simplest, lowest precision)?
- Area-weighted average across all component series?
- What to do when no series dominates (e.g. three species at ~33% each)?
- How should uncertainty be represented in aggregated outputs?

**Impact:** MCP tools must apply consistent, defensible aggregation logic. Without official guidance, tools must document their chosen defaults explicitly.

---

**Q7: How should soil alerts be attached to mapped units programmatically?**
- What are the lookup keys connecting soil associations/series to soil alert flags?
- Are thresholds or conditional logic documented?
- Is there a machine-readable alerts dataset, or only the web-based Soils Guide?

---

## Provenance and Legal

**Q8: How will Ordnance Survey copyright be represented in open access outputs?**
NATMAP Vector was redigitised to an OS 1:50,000 base in 1999. OS data typically carries Crown Copyright. Will derived outputs from portal.landis.org.uk still require OS attribution?

---

**Q9: What safeguards will be required to prevent misuse?**
Particularly for:
- High-stakes planning decisions using 1:250k data
- Engineering designs based on generalised soil classes
- Regulatory compliance decisions (contamination, pollution prevention)

Will the portal impose any use restrictions or mandatory disclaimers?

---

## Versioning

**Q10: What are the update and versioning policies post-open-access?**
- How frequently will datasets be updated?
- Will there be deprecation notices?
- Will old versions remain accessible for reproducibility?
- Is there a stable dataset DOI for citation in published work?

---

## Status Tracking

| Question | Status | Last Checked |
|---|---|---|
| Q1: Dataset scope | ❓ Unknown | April 2026 |
| Q2: Licence text | ❓ Unknown | April 2026 |
| Q3: Bulk downloads | ❓ Unknown | April 2026 |
| Q4: Programmatic endpoints | ❓ Unknown | April 2026 |
| Q5: WMS GetFeatureInfo | ❓ Unknown | April 2026 |
| Q6: Aggregation defaults | ❓ Unknown | April 2026 |
| Q7: Soil alerts lookup | ❓ Unknown | April 2026 |
| Q8: OS attribution | ❓ Unknown | April 2026 |
| Q9: Misuse safeguards | ❓ Unknown | April 2026 |
| Q10: Versioning policy | ❓ Unknown | April 2026 |

*Update this table as answers are confirmed from portal.landis.org.uk.*

---
*← [[00 - Home|Home]]  |  See also: [[Implementation Roadmap]], [[Governance and Licensing]], [[Key Links and Sources]]*
