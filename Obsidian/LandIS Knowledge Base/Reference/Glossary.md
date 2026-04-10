---
aliases: [glossary, terms, definitions, abbreviations]
tags: [reference, glossary, terms, landis]
---

# Glossary

A reference for key terms, codes, and classifications used across the LandIS knowledge base.

---

## Data Terms

**ALC — Agricultural Land Classification**
Defra's system for grading agricultural land 1–5 based on soil and climate constraints. Grade 1 is the best quality; Grade 5 is limited. Soil wetness class is a primary determining factor.

**Association** (soil association)
A named mapping unit in [[NATMAP Vector]] representing a characteristic pattern of soil series occurring together. Each polygon on NATMAP maps an association, not a single soil type. One association typically contains 2–6 component soil series.

**Auger bore**
A soil observation made by pushing a hand auger into the ground and recording soil characteristics at depth. LandIS holds >150,000 auger bore observations at >450,000 horizons.

**Baseflow Index (BFI)**
The proportion of total river flow derived from groundwater (baseflow) rather than surface/near-surface runoff. Derived from [[Horizon Data|SOILSERIES Hydrology]]; linked to HOST class.

**BFI — see Baseflow Index**

**CAW — Crop Available Water**
The water available to crops in soil between field capacity and wilting point. Estimated per soil type for different crop rooting depth models. See [[Interpreted Layers]].

**CLASS / Code**
Many LandIS datasets use integer codes. For example, Wetness Class 4, HOST Class 17. Always decode codes using classification guides rather than assuming numeric order implies quality.

---

## Datasets

**HOST — Hydrological Response to Soil Type**
A 29-class classification of soils by their dominant hydrological response to rainfall. 11 conceptual response models underpin the classification. Used in catchment hydrology modelling. See [[Interpreted Layers]].

**HORIZON Fundamentals**
Tabular dataset of physical and chemical soil properties at horizon level: particle size fractions, organic carbon, pH, bulk density, porosity. See [[Horizon Data]].

**HORIZON Hydraulics (v2.0)**
Tabular dataset of water retention and hydraulic conductivity parameters at horizon level. Updated November 2014. See [[Horizon Data]].

**LandIS**
Land Information System — Cranfield University's national soil and land information system for England and Wales. See [[00 - Home]].

**Leacs** (SOILSERIES Leacs)
Soil Series dataset providing corrosivity to iron and zinc buried assets, plus shrink-swell class. Used by water utilities for pipe asset risk assessment. See [[Utilities and Engineering]].

**MUSID — Mapping Unit ID**
The primary key field in [[NATMAP Vector]]. Each polygon has a MUSID; all attribute lookups begin with resolving a polygon to its MUSID.

**NATMAP / NATMAPvector**
The National Soil Map — a 1:250,000-scale polygon dataset of ~300 soil associations covering England and Wales. See [[NATMAP Vector]].

**NSI — National Soil Inventory**
A 5km-grid systematic point monitoring dataset of topsoil chemistry across England and Wales, with sampling in ~1980 and mid-1990s. See [[NSI - National Soil Inventory]].

**NATMAPassociations**
The linking table connecting polygon associations (via MUSID) to their component soil series (with expected percentages). Central to the [[Data Structure and Joins|join model]].

---

## Institutions and Policy

**Cranfield University**
Operator of LandIS; holds and licences the soil data under agreement with Defra/Crown.

**Defra**
Department for Environment, Food and Rural Affairs. Joint owner (with Cranfield) of LandIS IPR. The primary government funder of LandIS and driver of the open access transition.

**ELMS — Environmental Land Management Schemes**
The post-Brexit agri-environment scheme framework replacing CAP payments. Soil data is foundational evidence for ELMS payment design and monitoring.

**Environment Agency (EA)**
UK regulatory body for water, waste, and environmental protection. A major LandIS user for flood, groundwater, and contamination work.

**INSPIRE**
EU/UK directive on infrastructure for spatial information. NSI has been adopted as an INSPIRE Annex III Soil exemplary case study.

**NCEA — Natural Capital and Ecosystem Assessment**
UK programme to quantify the state of natural capital and ecosystem services. LandIS is a key input.

**Natural England (NE)**
UK body for nature conservation. Uses LandIS for peat targeting, habitat planning, and nature recovery strategy support.

---

## MCP and Technical Terms

**MCP — Model Context Protocol**
Open standard for exposing tools, resources, and prompts via JSON-RPC between AI hosts/clients/servers. See [[MCP Overview]].

**OGC API – Features**
An open geospatial standard for feature-level REST/OpenAPI access to spatial data. The recommended future API pathway for LandIS programmatic access.

**Provenance**
The documented origin of a data value — which dataset, which version, which date accessed. LandIS MCP tools embed provenance in every output.

**Semantic sheath**
The MCP layer's role: translating raw data codes into plain-English explanations with context and caveats, without altering the underlying deterministic data. See [[MCP Overview]].

**WMS — Web Map Service**
OGC standard for serving map images. LandIS already exposes Soilscapes and other layers via WMS. Not suitable for data queries or AI agent use; useful for GIS visualisation.

---

## Soil Science Terms

**Horizon** (soil horizon)
A layer in a soil profile with distinct physical and chemical characteristics. Horizons are named (O, A, B, C) and described by depth range. [[Horizon Data]] provides properties for each horizon of each soil series.

**Series** (soil series)
A taxonomic soil type recognised within England and Wales, characterised by a specific profile of horizons with defined properties. NATMAP associations are made up of component series.

**Shrink-swell**
The expansion and contraction of clay-rich soils with changes in moisture content. High shrink-swell soils cause ground movement affecting buildings, pipes, and roads. See [[Utilities and Engineering]].

**Soilscapes**
LandIS's simplified 27-class national soil map for non-specialist use. See [[Soilscapes]].

**SPR — Standard Percentage Runoff**
The proportion of rainfall that becomes direct runoff (not absorbed by soil). A key input to design flood estimation. Linked to HOST and soil drainage class.

**Wetness class**
A 6-class drainage classification (1=freely draining to 6=almost permanently wet) used in Agricultural Land Classification and soil constraint mapping. See [[Interpreted Layers]].

**WRB — World Reference Base for Soil Resources**
The international soil classification standard. LandIS provides WRB 2006 mapping for NATMAP associations.

---
*← [[00 - Home|Home]]*
