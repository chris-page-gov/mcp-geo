---
aliases: [users, stakeholder groups, personas]
tags: [strategy, stakeholders, users, personas, landis]
---

# Stakeholders

LandIS serves a broad and diverse set of stakeholder groups, each with distinct goals, questions, and interface needs. The open access transition and MCP layer are expected to significantly expand this user base.

## Primary Stakeholder Groups

### 🏛️ Government and Policy Teams
**Organisations:** Defra, Environment Agency, Natural England, DLUHC, Forestry Commission
**Core questions:**
- What is the baseline soil carbon across a proposed ELMS area?
- Which agricultural land classes are affected by this planning policy?
- What soil types intersect with a proposed nature recovery corridor?
- Where are the highest-carbon soils that should be protected from development?

**Interface needs:** Evidence packs, policy briefings, area summaries, provenance for auditable decisions
**Key use cases:** [[Government and Policy]], [[Climate and Carbon]]

---

### 🌾 Agricultural Advisors and Land Managers
**Organisations:** ADAS, farm consultancies, NFU, local farms
**Core questions:**
- What soil types are on this farm holding?
- What are the drainage constraints for this field?
- How many workable days can I expect for harvest machinery?
- What crop available water does this area provide?

**Interface needs:** Farm-scale summaries, plain-language drainage/suitability reports
**Key use cases:** [[Agriculture and Land Management]]

---

### 💧 Hydrology and Flood Teams
**Organisations:** Environment Agency, JBA Consulting, Mott MacDonald, catchment partnerships
**Core questions:**
- What HOST classes dominate this catchment?
- What is the baseflow index for these soils?
- Where are the soils most likely to generate rapid surface runoff?
- How do soil drainage characteristics interact with this flood zone?

**Interface needs:** Catchment summary reports, HOST breakdowns, drainage risk flags
**Key use cases:** [[Hydrology and Flood]]

---

### 🔧 Utilities and Infrastructure Planners
**Organisations:** Water companies, telecoms (Openreach, CTIL), National Grid, highway authorities
**Core questions:**
- What is the corrosion risk to buried iron/zinc pipes on this route?
- Where are the shrink-swell hotspots along this cable route?
- What wetness class constraints affect our construction window?
- How difficult is excavation likely to be on this alignment?

**Interface needs:** Route-based risk reports, chainage-by-class segments, asset risk bands
**Key use cases:** [[Utilities and Engineering]]
**MCP tool:** `landis_derive_pipe_risk(route)`

---

### 🌿 Biodiversity and Conservation Planners
**Organisations:** Wildlife Trusts, Natural England, RSPB, local nature partnerships
**Core questions:**
- What habitat types are associated with soils on this land parcel?
- Are there acid sulphate peats or other sensitive soil alerts here?
- Which soils link to target BAP habitats for this restoration project?
- What soil constraints should I consider before a land purchase?

**Interface needs:** Habitat overlays, soil alerts, conservation planning summaries
**Key use cases:** [[Biodiversity and Habitat]]

---

### 🏗️ Local Authority Planners and Engineers
**Organisations:** LPAs, county councils, combined authorities
**Core questions:**
- Are these soils suitable for this development site?
- What soil constraints affect the proposed housing allocation?
- Is there a shrink-swell or subsidence risk here?
- What is the drainage classification for this area?

**Interface needs:** Site constraint summaries with appropriate caveats
**Key use cases:** [[Utilities and Engineering]], [[Government and Policy]]

> [!warning] Critical Caveat for Planners
> Soilscapes and NATMAP are not suitable for site-level planning decisions. Any tool serving planners must prominently display the 1:250k scale limitation and recommend field investigation.

---

### 🎓 Academic Researchers
**Organisations:** Universities, UKCEH, BGS, Met Office
**Core questions:**
- What is the national distribution of HOST class 5?
- How do soil carbon stocks correlate with land use across England?
- Can I access NSI data for a geostatistical study?
- What is the uncertainty model for these soil classifications?

**Interface needs:** Bulk data access, versioned datasets, reproducible outputs, citable provenance
**Key use cases:** [[Emerging Opportunities]] — AI benchmarks, monitoring

---

### 🌍 Environmental Consultants
**Organisations:** WSP, Atkins, Arcadis, environmental SMEs
**Core questions:**
- What is the pesticide leaching vulnerability of soils in this catchment?
- Are there groundwater-sensitive soils beneath this proposed development?
- What corrosion class applies to these soils for a buried gas pipeline?
- Where should I focus site investigation resources?

**Interface needs:** Route/area risk reports with regulatory-grade provenance
**Key use cases:** [[Utilities and Engineering]], [[Hydrology and Flood]]

---

### 🏫 Education and Public
**Organisations:** Schools, NGOs, citizen science, public
**Core questions:**
- What kind of soil is under my feet?
- Why does my garden get waterlogged in winter?
- What is a soil association?
- What does the soil in my area tell us about nature and climate?

**Interface needs:** Plain-language explanations, locality-based, accessible visuals
**Key use cases:** [[Emerging Opportunities]] — "explain my soil" public tools

---

## Cross-Cutting Design Principles

All stakeholder tools must:
1. **Return appropriate caveats** for the group (planners and engineers need stronger warnings than researchers)
2. **Match the interface to the task** — farmers need plain language; researchers need raw data
3. **Embed provenance** — government and consultants need audit trails
4. **Offer verification paths** — always indicate when field investigation is needed

---
*← [[00 - Home|Home]]  |  See also: [[MCP Overview]], [[Implementation Roadmap]], [[Resources and Prompts]]*
