---
aliases: [infographic, soil data engine, LandIS overview visual, AI soil infographic]
tags: [overview, infographic, mcp, open-access, natmap, nsi, soilscapes]
source: "UK Soil Data Engine Infographic.png — generated via NotebookLM, April 2026"
---

# UK Soil Data Engine Infographic

![[UK Soil Data Engine Infographic.png]]

**Full title:** *LandIS: Powering UK Soil Intelligence through Open Access & AI*

> [!info] This infographic is the single-page overview of the entire LandIS strategy. It maps directly to the five-slide deck ([[LandIS MCP Strategy Slides]]) and provides the quickest entry point to understanding what LandIS is and why it matters.

---

## Left Panel — The National Soil Data Engine

### The Definitive National Record
Covers England and Wales using 60+ years of digital soil representations.

### Three Core Datasets

**NATMAP Vector** (1:250,000 — 300+ Mapped Soil Associations)
Principal national soil map for England and Wales. 300+ mapped soil associations at 1:250,000 scale for national planning and modelling.
→ See: [[NATMAP Vector]]

**Soilscapes** (1:250,000 — 27 classes)
Simplified, generalised dataset for non-specialist awareness. Collapses the 300 NATMAP associations into 27 meaningful landscape classes.
→ See: [[Soilscapes]]

**NSI** (5km Grid Point)
National Soil Inventory — systematic monitoring of topsoil chemistry and pH since 1980. The observational foundation for the entire system.
→ See: [[NSI - National Soil Inventory]]

### NSI Strategic Monitoring
Systematic 5km grid point data covering topsoil chemistry and pH since 1980. Provides time-series evidence for change detection — soil carbon trends, contamination, acidification.

---

## Right Panel — Unlocking Innovation via MCP & Open Access

### The Open Access Pivot
2026 transition to make the majority of datasets openly available for policy. Defra & Cranfield agreement removes historic royalty and licensing barriers. `portal.landis.org.uk` becomes the central distribution hub.
→ See: [[Open Access Transition]], [[Governance and Licensing]]

### AI-Ready via MCP
Uses Model Context Protocol to expose soil tools to AI platforms like ChatGPT [and Claude]. The MCP layer translates raw spatial queries, encodes semantic meaning, and enforces provenance on every output.
→ See: [[MCP Overview]], [[LandIS MCP Strategy Slides]]

### Composable Spatial Tools
Automated screening for pipe corrosion, carbon stocks, and trenching difficulty — the first generation of derived tools built on the MCP foundation.
→ See: [[Derived Semantic Tools]], [[Utilities and Engineering]]

---

## Reading the Infographic as a System Diagram

The infographic presents LandIS as a **pipeline**, not just a database:

```
FIELD OBSERVATIONS (NSI grid, Auger bores)
         ↓
MAPPED POLYGONS (NATMAP 1:250k, Soilscapes 27 classes)
         ↓
ATTRIBUTE TABLES (SOILSERIES, HORIZON fundamentals/hydraulics)
         ↓
INTERPRETED LAYERS (HOST, Wetness, Carbon Stock)
         ↓
MCP ACCESS LAYER (Access → Semantic → Assurance)
         ↓
AI APPLICATIONS  |  DEFRA POLICY  |  ENGINEERING SCREENING
```

Each layer is queryable independently or as a join chain. The MCP exposes all layers to AI agents without requiring GIS expertise or knowledge of the join model.

---

## Key Numbers Visible in the Infographic

| Fact | Source |
|---|---|
| 60+ years of digital soil data | NATMAP mapping programme started 1960s |
| 300+ mapped soil associations | NATMAP Vector polygon count |
| 27 Soilscapes classes | Simplified national classification |
| 5km grid spacing | NSI monitoring design |
| Since ~1980 | NSI systematic monitoring start date |
| >20 topsoil chemical elements + pH | NSI analytical suite |

---

## Use as a Communication Tool

This infographic is designed to communicate the LandIS value proposition to non-specialists — decision-makers, policy analysts, engineers, and AI system designers who need to understand what's available and why MCP access matters.

When briefing stakeholders on LandIS and the MCP strategy, this image conveys:
1. **What it is** — England & Wales' definitive 60-year soil record, three main products
2. **Why it's changing** — 2026 open access removes access barriers
3. **How AI can use it** — MCP tools expose it to any AI platform without GIS complexity
4. **What you can do with it** — pipe screening, carbon stocks, trenching difficulty (and much more — see [[Use Cases]])

---

## See Also

- [[LandIS MCP Strategy Slides]] — the five-slide deck this infographic summarises
- [[MCP Overview]] — full MCP architecture note
- [[NATMAP Vector]] — detail on the 1:250k polygon map
- [[Soilscapes]] — the 27-class simplified product
- [[NSI - National Soil Inventory]] — the 5km monitoring grid
- [[Derived Semantic Tools]] — the composable screening tools
- [[Open Access Transition]] — the 2026 policy shift in detail

---

*← [[00 - Home|Home]]  |  Related: [[LandIS MCP Strategy Slides]], [[MCP Overview]]*
