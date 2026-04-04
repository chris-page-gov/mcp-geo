# LandIS as AI-accessible soil data infrastructure: evidence, use cases, and an MCP access strategy

## Executive summary

### High-confidence findings grounded in direct evidence

LandIS is presented by its operators as a large, national-scale soil and land information system for England and Wales, operated by entity["organization","Cranfield University","postgraduate university uk"], and described as the definitive national soils source recognised by UK Government. citeturn38view0turn24view0turn41view0

LandIS’ public-facing product landscape is explicitly “family-structured”: a national polygon map family (NATMAP products), point monitoring data (NSI), soil-series and horizon attribute tables, and interpreted thematic layers (e.g., wetness, carbon stock, HOST, crop available water). citeturn12view0turn13view0turn14view0turn19view0turn18view0turn18view2

NATMAP Vector is described as the principal national soil map dataset: a 1:250,000-scale vector dataset derived from decades of soil survey work, with about 300 mapped soil associations; it is described as redigitised (1999) with improved registration to an entity["organization","Ordnance Survey","uk national mapping agency"] 1:50,000 base. citeturn13view0turn12view0

Soilscapes is a simplified 1:250,000 classification (27 classes) derived from NATMAPvector, explicitly framed as a generalised dataset and not suitable for detailed site assessments (e.g., planning applications or site investigations). citeturn10view0turn43view0

NSI is explicitly described as point data on a 5 km grid across England and Wales, with initial sampling around 1980 and partial resampling in the mid‑1990s; it includes site, profile, topsoil chemistry (including >20 elements plus pH), textures, and “features” including a flood-risk indicator. citeturn14view0turn24view0

LandIS’ soil-series and horizon attribute datasets are explicitly tabular and intended to be joined to NATMAP mapping via linking tables; the “NATMAPassociations” table and “MUSID” key are explicitly described as the join mechanism from association polygons to series attributes. citeturn41view2turn15view0turn16view1

Specific interpreted thematic products are documented with clear derivation logic and data fields, including:
- NATMAP Carbon (0–30, 30–100, 100–150 cm summaries/stock) derived from horizon fundamentals and hydraulics, and used as part of the Greenhouse Gas Inventory. citeturn18view2turn36view0  
- NATMAP Wetness (6 wetness classes) used in Agricultural Land Classification and other constraint-related definitions. citeturn18view1  
- NATMAP HOST (29 classes; based on conceptual hydrological response models; class proportions within polygons). citeturn18view0turn41view7  
- NATMAP Crop Available Water for different crop rooting models. citeturn19view0  
- NATMAP WRB mapping to international WRB 2006 classes. citeturn19view1

There is strong evidence of a major policy/operational shift towards open access. A Defra procurement notice describes historic constraints (royalty-free access for Crown bodies; barriers for non‑Crown public bodies and private users; licensing constraints on Defra policy use) and states a decision between entity["organization","Department for Environment, Food & Rural Affairs","uk government department"] and Cranfield to make “the majority” of key datasets openly available. citeturn6view0

By April 2026, the LandIS home page itself states “LandIS Soils have become Open Access!” and links to a new portal at `portal.landis.org.uk`, implying at least a user-facing open-access mechanism is now live or in late-stage rollout. citeturn38view0

LandIS already participates in service-based geospatial distribution via OGC WMS endpoints hosted under LandIS’ ArcGIS services path, evidenced via published WMS links referenced by the entity["organization","UK Soil Observatory","uk research soil portal"] ecosystem and metadata catalogues. citeturn27view0turn30search5turn28view0

MCP is now supported by a mature documentation/specification ecosystem and is positioned as a standard means of exposing “tools”, “resources”, and “prompts” through an interoperable JSON‑RPC protocol between hosts/clients/servers; it is supported in practice by multiple major platform ecosystems, including entity["company","OpenAI","ai company"]’s developer guidance for building MCP servers for ChatGPT Apps and API integrations. citeturn44search3turn44search19turn44search0turn44search32turn44search17

### Medium-confidence findings expressed as reasoned inferences

Because LandIS data products are already exposed through (at least) WMS endpoints and multiple web applications (Soilscapes viewer, UKSO integration, Mapshop), a composable “tool layer” is likely to deliver substantial near-term value even if bulk downloads remain available, by reducing friction for non-GIS users and enabling deterministic spatial queries on demand. This inference is supported by the plurality of existing interfaces and the explicit historic friction caused by licensing/access asymmetries. citeturn10view0turn27view0turn36view0turn6view0

The dataset family design (associations → series → horizons) makes LandIS particularly suitable for “semantic tooling” that turns specialist data structures into decision-relevant explanations (e.g., “why is this location seasonally waterlogged?”), because the data model already encodes both classification systems and derived functional indicators (wetness, HOST, pesticides, corrosivity/shrink-swell). citeturn41view2turn17view3turn18view1turn18view0turn17view2

Given that LandIS (a) is explicitly used across government policy areas and (b) is structurally compatible with spatial joins, it is likely to become more valuable when composably combined with national addressing, boundaries, infrastructure networks, planning constraints, catchments, and land cover datasets (for example via OGC API – Features style APIs that enable fine-grained feature-level access). citeturn24view0turn13view0turn44search2turn44search6

### Speculative but promising findings (explicitly forward-looking)

An MCP server, implemented as a policy-safe “thin semantic sheath” over LandIS (provenance-aware, uncertainty-aware, spatially deterministic), could become a practical early demonstration and value-discovery mechanism for the open access transition, because it can expose a small number of high-value spatial tools without forcing full-scale API productisation. This is speculative but consistent with MCP’s design goals and the kinds of “tool” and “resource” primitives it standardises. citeturn44search3turn44search33turn38view0

LandIS-derived “ground constraint” tools (wetness, drainage, shrink‑swell, corrosion potential, carbon stock, pesticide leaching) could materially improve agentic workflows for infrastructure planning (including telecoms deployment and excavation/trenching risk triage), particularly when combined with route geometry and asset datasets; this is plausible given that these same soil properties are already framed for engineering and utilities contexts. citeturn11view2turn17view3turn36view0turn39view0

The open access shift creates a plausible opportunity to establish LandIS as a UK “reference benchmark” for grounded environmental reasoning tasks (spatial QA, uncertainty-aware classification, multi-layer provenance), but doing so responsibly would require careful evaluation design, clear disclaimers, and strict provenance/version controls. This remains speculative and depends on the final open-access licensing terms and programmatic access affordances. citeturn38view0turn6view0turn43view0


## What LandIS is

### Dataset and ecosystem overview

LandIS is described by its operators as a national soil and soil-related environmental information system for England and Wales, operated by Cranfield University, with multiple modes of access (web tools, services, and data products). citeturn38view0turn13view0turn12view0

LandIS is explicitly framed as having begun in the 1970s as a “trusted basis and repository” for digital soil representations collected over 60–70+ years, and as supporting a range of application areas (environmental, agricultural, engineering). citeturn38view0turn13view0turn11view2

A government-facing narrative also positions LandIS as a foundational resource: Defra’s digital blog describes a multi-year agreement for maintenance and licensing and states that Defra and Cranfield “jointly own” the IPR in LandIS. citeturn24view0

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["LandIS Soilscapes viewer England and Wales screenshot","Cranfield Mapshop soil data selector screenshot","UK Soil Observatory soil map viewer screenshot","LandIS downloads soil data structures and relationships PDF cover"],"num_per_query":1}

### Governance, provenance, and the open-access transition

A 2024 “Soil Information and Data Policy” document states that Cranfield holds soil information/data for England and Wales across published maps/reports, unpublished field records, and digital soil data in LandIS; it describes a legal agreement between Cranfield and the Crown under which Cranfield has an exclusive right to grant licences for use of the digital data, with special conditions for Crown departments and bona fide research users (administrative fee, no royalties). citeturn41view0turn41view1

A Defra procurement pipeline notice (published February 2025) provides unusually specific context: it names the platform and datasets in scope (including NATMAP and NSI/soil attributes), describes a historic access asymmetry (royalty-free access for Crown bodies; non‑Crown public bodies and most other users lacked such access), and states a decision taken between Defra and Cranfield for Cranfield to make “the majority” of those datasets openly available, explicitly to support major policy initiatives (ELMS, Nature Recovery Network, Local Nature Recovery Strategies, Agricultural Land Classification, and NCEA) and net zero work. citeturn6view0

Cranfield’s January 2026 press release documents the agreement to develop an open access portal (including NATMAP) and states that a new system would launch during 2026, derived from LandIS, giving free access to extensive data. citeturn21search0

As of the current date anchor, LandIS’ own home page states “LandIS Soils have become Open Access!” and links to a new portal at `portal.landis.org.uk`. The contents, licensing terms, and programmatic affordances of that portal could not be fully extracted from the portal site using the tools available (the portal pages do not render as readable HTML in this research environment), but the existence and prominence of the link is directly evidenced. citeturn38view0turn39view4

### Coverage and thematic scope

LandIS’ core spatial coverage is consistently stated as England and Wales for its national mapping and monitoring datasets (NATMAP family; NSI). citeturn13view0turn14view0turn43view0turn7view0

LandIS’ thematic scope spans:
- soil classification and mapping (associations, series, horizons); citeturn41view4turn12view0  
- soil physical/chemical properties (texture, carbon, bulk density, pH, water retention); citeturn16view1turn16view2turn18view2  
- hydrology and drainage response (HOST, wetness, series hydrology); citeturn18view0turn18view1turn17view0turn43view1  
- agronomy and crop-related functional measures (available water, crop rooting models); citeturn19view0turn17view1  
- environmental risk indicators (pesticide leaching/runoff classes; corrosion/shrink‑swell); citeturn17view2turn17view3turn39view0  
- soil alerts intended for environmental/engineering project awareness (acid sulphate peats, groundwater-affected soils, etc.). citeturn39view0


## Data inventory and technical characterisation

### Data families, structures, and key relationships

**NATMAP family (polygon and gridded vector products).** LandIS describes NATMAPvector as the core 1:250k polygon soil association map (about 300 associations), with derived products including Soilscapes (27 classes), and gridded vector versions (1 km, 2 km, 5 km) that attribute grid cells with proportions of soil series. citeturn13view0turn12view0turn41view2

A data.gov.uk metadata record positions NATMAP Vector as the “most detailed” of four versions of the National Soil Map, derived from 60 years of survey work, with British National Grid as SRS and a licensing regime described as variable by user status. citeturn7view0

A separate data.gov.uk record describes NATMAP v3 1K as a “series based, 1km² grid vector” dataset covering England and Wales, designed for “easy database querying” via a flattened table representation. citeturn21search19

**Soil series and horizon properties (tabular).** LandIS describes soil series as taxonomic soil types recognised within England and Wales and explicitly frames the combination of series/horizon properties with national mapping as enabling “complex thematic maps and modelled outputs” and a national three-dimensional representation of soils. citeturn15view0

SOILSERIES Info is documented as basic series description data (including a 4‑digit series code and modern definition) and is stated to be provided “at no charge” when leased with NATMAP products (historically, at least). citeturn16view0

HORIZON Fundamentals and HORIZON Hydraulics are documented as tabular, horizon-level data keyed by a unique horizon identifier and series code, including detailed particle size fractions, organic carbon, pH, bulk density, porosity, and water retention parameters. citeturn16view1turn16view2

HORIZON Hydraulics explicitly documents a version update (v2.0, November 2014) based on expanded measured data across the UK and references updated predictive equations for water retention. citeturn16view2turn17view0

**Association ↔ series join model.** A LandIS “soil data structures and relationships” paper explicitly states:
- NATMAPvector polygons are keyed by a mapping unit code (MUSID),
- NATMAPlegend links to NATMAPvector by MUSID,
- NATMAPassociations is the linking table connecting soil associations to their component soil series and expected percentages,
- SOILSERIES and HORIZON tabular datasets join via SERIES codes, but NSI is self-standing and “not designed to be joined” to other tabular Cranfield data. citeturn41view2turn41view3

This join model is central to MCP suitability: it creates a clear boundary between low-level spatial operations (polygon selection, grid extraction) and higher-level semantic aggregation (dominant series; weighted averages; confidence caveats).

### Point monitoring data: NSI

NSI is explicitly framed as a systematic national monitoring dataset, statistically representative for England and Wales, suitable for geostatistical methods and trend mapping of soil chemistry, with documented historic sampling/resampling periods. citeturn14view0

The NSI page states it has been adopted by INSPIRE “Annex III Soil” technical working groups as an exemplary case study for soil monitoring deployment. citeturn14view0

### Interpreted thematic layers and derived indicators

LandIS documents multiple interpreted NATMAP-derived layers with explicit **field-level attribute descriptions** for polygons, including:
- HOST classifications and per-class coverage percentages per polygon; citeturn18view0  
- Wetness class and per-class polygon percentages; citeturn18view1  
- Carbon stocks and organic carbon summaries by depth layer; citeturn18view2  
- Crop-available water for multiple crop rooting models. citeturn19view0  

Separately, LandIS documents SOILSERIES datasets supporting pesticide leaching/runoff classes and utility/engineering risk (shrink‑swell and corrosivity). citeturn17view2turn17view3

A Soilscapes “use and applications” brochure describes Soilscapes as a shapefile dataset at 1:250,000 scale (created 2003; updated 2010) and explicitly highlights limitations due to within-polygon variability and generalisation; it also asserts ISO19115/19139 metadata availability. citeturn43view0turn43view2

### Access modes and technical surfacing already evidenced

LandIS presently exposes content through:
- Web applications and pages (Soilscapes viewer; Soils Guide; Soil Alerts). citeturn10view0turn39view0  
- Downloads of supporting documentation and some reports, including data structure papers and classification documents. citeturn39view1turn41view2turn41view4  
- Paid or licence-based commercial distribution (historically) through Mapshop. citeturn35view0turn36view0  
- OGC WMS services embedded in the UK Soil Observatory ecosystem, with discoverable WMS endpoints. citeturn27view0turn30search5turn28view0  
- Metadata records on data.gov.uk (with ISO metadata links) and third-party catalogues such as EJPSoil. citeturn7view0turn30search5turn32view0  

A key technical constraint repeatedly stated across Soilscapes materials is that **mapped polygons are generalisations**; for many uses, field validation remains required and local variation can be significant even within a soil association or series. citeturn39view0turn43view0turn26view2

### Licensing, constraints, and auditability considerations

Historically, multiple sources document a licensing regime based on user status:
- Data.gov.uk entries describe LandIS information as copyrighted and subject to specific licensing agreements, with costs varying from commercial charge to royalty-free with extraction fees depending on user status. citeturn7view0turn9view0  
- A Mapshop FAQ states licences are time-limited (one year) and require deletion of both the original and derived data at licence end (a significant reproducibility barrier for downstream analytics). citeturn35view0  
- A Natural Resources Wales metadata record states the dataset is wholly owned by Cranfield University; NRW may not publish or disseminate it, and third parties must approach the owner directly. citeturn32view0  

These constraints may be changing rapidly due to the open-access transition, but they remain relevant to the governance design of any MCP server: responses must include licence and version information and avoid encouraging prohibited reuse where restrictions remain.


## Established uses

### Government, public agencies, and policy delivery

Defra explicitly describes LandIS as used across “projects and policy areas” and lists: land-use planning, environmental protection, agricultural policy, and climate adaptation. It also provides a peat mapping case study where entity["organization","Natural England","nature conservation body england"] uses LandIS soil association data to guide surveyors to potential buried peat locations. citeturn24view0

The Defra procurement notice frames open access as strategically enabling ELMS, nature recovery initiatives, land classification, NCEA, and net zero work, implying a broad public-sector dependency on soil data as an enabling evidence layer. citeturn6view0

### Agriculture, land management, and agronomy

LandIS’ own applications list includes agriculture-adjacent functional planning such as direct drilling, drainage design, trafficability, machinery workdays, and suitability for specific crops. citeturn11view2

NATMAP wetness and crop available water are explicitly connected to Agricultural Land Classification methodology and to constraints-based land assessment, anchoring use in land capability and planning. citeturn18view1turn19view0

The Soilscapes drainage dataset is framed as supporting farm operations (ease of cultivation), pollution prevention policies, and river basin management planning, again signalling direct relevance to agronomy and diffuse pollution management. citeturn43view1

### Hydrology, catchment management, and flood-related work

HOST is documented as a hydrologically-based classification intended to describe catchment hydrological response and soil‑subtrate processes, with 29 classes and 11 response models, derived by combining soil series properties and hydrogeology and then aggregating to polygons. citeturn18view0turn41view7turn36view0

SOILSERIES Hydrology is explicitly described as “essential” for groundwater modelling and flow prediction and includes (under commercial licence in the documented configuration) HOST class, bypass flow, baseflow index, and standard percentage runoff. citeturn17view0

Within LandIS’ case studies, soils data is referenced in work linking soil drainage characteristics to risk pathways (e.g., leachate reaching water bodies beneath historic landfills by identifying freely draining or groundwater-connected soils). citeturn11view1

### Utilities, engineering risk, and built environment

The SOILSERIES Leacs dataset is explicitly described as widely used in the UK water utility sector, including “most major water companies”, for prediction of corrosion rates on underground pipe assets; it also includes shrink‑swell classes relevant to ground movement. citeturn17view3turn36view0

Cranfield’s case study framing for the National Soil Map explicitly includes risks such as subsidence, flooding, pipe management, road condition, and pollutant leaching, signalling a consistent engineering-risk use narrative. citeturn34view0turn11view2

The Soilscapes brochure documents that drainage data has been used by local governments, engineers, agronomists, and environmental consultants. citeturn43view1

Auger bore data is described as >150,000 auger bores (>450,000 horizons) and framed as particularly useful for engineering and land development projects because it represents surveyed information at specific locations. citeturn36view0

### Biodiversity planning and habitat restoration

The Soilscapes habitats dataset is framed as supporting habitat project decision-making and biodiversity issues; it provides example usage in conservation planning and land purchase decisions, including use by the Bedfordshire and Luton Biodiversity Recording and Monitoring Centre (BRMC) and by Wildlife Trust actors for land purchase and linkage/buffering analysis. citeturn43view3

Soil Alerts are explicitly framed as aimed at practitioners in ecology, forestry, hydrology, geology and engineering who may not be soil specialists, to prevent project failure due to soil misinterpretation (e.g., soil translocation failure when pans are misidentified). citeturn39view0

### Academic research and monitoring

The NSI page lists multiple peer-reviewed publications that use NSI data for national-scale soil monitoring, including the widely cited Nature paper on carbon losses across England and Wales (1978–2003) and other geostatistical monitoring studies. citeturn14view0

### Observed limitations and pain points explicitly documented

Multiple sources explicitly caution that generalised soil maps, particularly Soilscapes, should not be used for detailed assessments without field investigation; local variability can be significant even within series/associations. citeturn43view0turn39view0turn26view2

Licensing terms historically required deletion of derived data after a year for Mapshop-acquired datasets, which can undermine reproducibility and longitudinal model auditing unless renewed or migrated to open terms. citeturn35view0

Government documentation highlights that restricted access for non‑Crown public bodies and others “significantly hampers” wider use and can limit Defra’s ability to use the datasets to further policy objectives. citeturn6view0


## Speculative and emerging uses

This section distinguishes: **Reasonable inference** (grounded but not explicitly documented as current practice) vs **Speculative opportunity** (promising but requires validation and/or new capability).

### Composable spatial reasoning across UK public-sector datasets

**Reasonable inference.** LandIS is structurally suited to “composable constraint reasoning” when combined with other spatial feature datasets (boundaries, infrastructure networks, land cover, flood zones, protected sites) because:
- it already encodes soil‑driven constraints (wetness, drainage, corrosion/shrink‑swell, pesticide leaching), citeturn18view1turn43view1turn17view3turn17view2  
- and it has established GIS-join patterns (association/series/horizon) that can be operationalised into tools. citeturn41view2turn15view0  

**Dependencies.** Boundary datasets, authoritative addressing/UPRN and administrative geographies, network assets, and a standard feature API pattern such as OGC API – Features for cross-provider interoperability. citeturn44search2turn44search6  

**Access pattern fit.** MCP tools for spatial queries + MCP resources for schema/ontology + API/OGC services for heavy geometries.

### Infrastructure deployment difficulty scoring and excavation/trenching risk estimation

**Reasonable inference with speculative extensions.** LandIS already frames shrink‑swell, corrosivity, wetness, drainage, and groundwater susceptibility as engineering-relevant; it explicitly lists “routes for roads and pipelines” and “corrosion risk to buried pipes” among LandIS applications. citeturn11view2turn17view3turn18view1turn43view1

**Speculative opportunity.** A “route feasibility and difficulty scoring” toolchain for telecoms rollout and other linear infrastructure could combine:
- soil wetness/drainage (construction window constraints; dewatering needs), citeturn18view1turn43view1  
- shrink‑swell and corrosion classes (asset longevity and reinstatement risk), citeturn17view3turn36view0  
- and soil depth/rock indicators from series hydrology (excavation difficulty). citeturn17view0  

**Dependencies.** Route geometry, road/footway network, land ownership and constraints, watercourse crossings, highway authority assets.

**Confidence level.** Medium: the soil variables’ relevance is well established in LandIS material, but the specific deployment scoring workflow would require domain calibration and validation.

**Access pattern fit.** MCP derived semantic tool (score + explanation) composed atop primitive “route intersect” and “area summary” tools.

### Climate adaptation, carbon accounting, and peat/organic soil targeting

**Directly evidenced foundation.** NATMAP Carbon is explicitly used for the Greenhouse Gas Inventory and provides multi-depth carbon stock summaries; NSI supports carbon trend studies. citeturn18view2turn14view0turn36view0

**Reasonable inference.** With open access, LandIS carbon and wetness layers could underpin:
- screening of high-carbon soils for protection/restoration prioritisation, citeturn18view2turn39view0  
- and scenario planning for land-use change impacts (provided provenance and uncertainty are clearly represented).

**Dependencies.** Land use/land cover time series, peat depth maps (e.g., those under development by Natural England), emissions factor methodologies.

**Confidence level.** Medium-high for screening; lower for quantified accounting without additional local measurements.

**Access pattern fit.** Hybrid: MCP tools for rapid screening + notebook/workflow for modelling.

### Contamination and remediation triage

**Reasonable inference.** Soilscapes drainage and pesticide leaching/runoff classes can inform vulnerability of groundwater/surface waters to contaminant transport, and LandIS already frames pollutant transfer mechanisms and land contamination as application areas. citeturn43view1turn17view2turn11view2turn11view1

**Speculative opportunity.** A “triage assistant” could:
- flag where soils are likely to facilitate rapid leaching/runoff,  
- recommend where specialist investigation is more urgent,  
- and generate an audit trail linking to source datasets and soil alerts.

**Dependencies.** Contaminant sources/landfill registries, hydrogeology, abstraction zones, regulatory thresholds.

**Confidence level.** Medium (value is plausible, but risk of misinterpretation is high without careful guardrails).

**Access pattern fit.** MCP derived tool with strict disclaimers + links to “Soil Alerts” resources.

### Educational and public-facing explanation tools

**Directly evidenced need.** Soilscapes is explicitly designed to communicate soil variation to non‑soil scientists and is used via a free viewer; Soil Alerts are aimed at non-specialist practitioners. citeturn10view0turn13view0turn39view0

**Speculative opportunity.** MCP-enabled “explain my soil” apps could generate:
- plain-language explanations (with appropriate uncertainty warnings),
- curated learning paths via resources (classification guides, glossaries),
- and locality-based examples for schools, NGOs, and citizens.

**Dependencies.** High-quality prompt templates, carefully curated explanatory content, and consistent provenance.

**Confidence level.** High for usability; medium for scientific safety unless carefully governed.

### AI research benchmarks for grounded environmental reasoning

**Speculative opportunity.** LandIS could support benchmark tasks such as:
- spatial QA (“What soil wetness class dominates this polygon?”),
- multi-source reasoning (“Given soil wetness + HOST class, what drainage behaviours are plausible?”),
- and uncertainty-aware responses (“What should you not infer at site scale from Soilscapes?”).

**Dependencies.** Stable open licensing, release notes, dataset versioning, and benchmark governance.

**Confidence level.** Medium-low until the open portal’s licensing and programmatic access are validated.


## Surfacing options and recommended MCP design

### Surfacing options evidenced today

**Interactive portals and viewers.** LandIS provides a Soilscapes viewer and other web tools; Soilscapes viewer includes location search by postcode, place name, OS grid reference, and coordinates. citeturn10view0turn26view2

**Downloads for documentation and selected resources.** LandIS publishes downloadable documents including:
- soil data structure and join guidance, citeturn39view1turn41view2  
- soil classification guide, citeturn41view4  
- Soilscapes applications and metadata brochure. citeturn41view5turn43view0  

**OGC Web Map Services (WMS).** LandIS-hosted WMS endpoints exist for Soilscapes and other layers via an ArcGIS MapServer WMSServer path, linked through UKSO and catalogues. citeturn30search5turn28view0turn28view2

**Commercial and semi-commercial distribution paths.** The Cranfield Mapshop documents multiple soil products (National Soil Map, HOST, Carbon Stock, Shrink Swell, Auger Bores) and provides formats (ESRI shapefile, MapInfo TAB). It also documents augmentation of risk products (Natural Perils Directory) by third-party tree data. citeturn36view0

**Metadata and discovery.** Data.gov.uk lists LandIS datasets with ISO metadata records and licensing notes; UKSO pages provide additional contextual metadata and WMS links. citeturn7view0turn27view0

**Open-access portal.** LandIS now links to a new portal under `portal.landis.org.uk`, but the portal’s internal structure, API availability, and licence text could not be reliably extracted for analysis here. citeturn38view0turn39view4

### Plausible near-term API pathways

This section separates **evidenced** from **inferred** feasibility.

**Evidenced.** WMS endpoints provide map-image access and, depending on configuration, can support GetFeatureInfo-style attribute interrogation; they also provide a standard integration path for GIS clients. citeturn30search5turn28view0turn27view0

**Reasonable inference.** Because WMS endpoints are served from ArcGIS MapServer WMSServer paths, it is plausible (but not verified here) that related ArcGIS REST endpoints exist that could support feature and metadata queries. This must not be assumed without direct testing.

**Strategically recommended modern pathway.** Where LandIS intends broad composability, consider OGC API – Features for feature-level access using REST/OpenAPI patterns. OGC explicitly positions OGC API – Features as modular building blocks for discovery/query/retrieval of geospatial features, offering fine-grained access rather than bulk datasets. citeturn44search2turn44search14

### Is MCP a strong fit for LandIS?

**Fit factors in favour (evidenced + inference).**
- LandIS has many high-value, deterministic query types (point lookup, polygon summary, class decoding, “show me the dominant wetness class”) that align well with MCP tools. citeturn18view1turn43view0turn41view2  
- LandIS has rich “static knowledge” assets (classification documents, schema explanations, glossaries) that align with MCP resources and prompts. citeturn39view1turn41view4turn41view2turn44search0  
- MCP is explicitly designed to standardise exposure of tools/resources/prompts via a host/client/server architecture and JSON‑RPC messaging, enabling composable integrations. citeturn44search3turn44search19turn44search9  

**Caution factors.**
- Soil map generalisation and within-polygon variability create a strong risk of misinterpretation if tools imply site-level certainty; Soilscapes explicitly warns against detailed assessment use. citeturn43view0turn10view0turn39view0  
- Licensing and versioning transitions (open access shift) demand careful governance: an MCP server must attach licence text/links and dataset version IDs to outputs. citeturn6view0turn38view0turn35view0  

### Core composable MCP design for LandIS

#### Design intent

**Primary role:** a combined **access + semantic + assurance** layer.
- **Access layer:** deterministic spatial queries that shield users from file formats and joins.
- **Semantic layer:** derived interpretations that turn classes into plain-language constraints with explicit caveats.
- **Assurance layer:** attaches provenance, versioning, and scale/limitation warnings to every response.

#### Proposed primitive tools

These are deterministic and low-level; they should return structured JSON with explicit provenance.

- **Dataset discovery**
  - `landis.catalog.list_products()` → lists available layers, coverage, spatial type, scale/resolution, last-updated, access tier.
  - `landis.metadata.get(product_id)` → returns ISO metadata (where available) and provenance narrative.

  Evidence basis: LandIS publishes product families and references ISO metadata availability. citeturn12view0turn43view0turn7view0  

- **Point lookup**
  - `landis.soilscapes.point(lat, lon | osgb_easting, osgb_northing)` → soilscape class + key attributes + uncertainty note.
  - `landis.natmap.point(...)` → soil association (MUSID) + association label + link to legend text.

  Evidence basis: Soilscapes viewer supports coordinate/grid reference lookup; NATMAP has association mapping units. citeturn10view0turn13view0turn41view2  

- **Area summary**
  - `landis.soilscapes.area_summary(geometry)` → percent area by soilscape class.
  - `landis.natmap.area_summary(geometry)` → percent area by association; optionally dominant association.

  Evidence basis: NATMAP and Soilscapes are polygon datasets; Soilscapes is used for regional overviews. citeturn12view0turn43view0  

- **Route intersection**
  - `landis.route.intersect(polyline, layers=[wetness, host, shrink_swell])` → chainage-by-class segments and hotspot list.

  Evidence basis: LandIS explicitly lists “routes for roads and pipelines” as an application area and provides multiple constraint layers. citeturn11view2turn18view0turn18view1turn17view3  

- **Classification and code retrieval**
  - `landis.classification.soilscape(code)` → name, description, typical texture/drainage/carbon/habitats (if available).
  - `landis.classification.host(class_id)` and `landis.classification.wetness(class_id)` → definitions.

  Evidence basis: Soilscapes viewer and NATMAP pages define class systems and attribute fields. citeturn10view0turn18view0turn18view1  

- **Association-to-series expansion**
  - `landis.natmap.association_series(musid)` → list of component series + expected percentage from NATMAPassociations.

  Evidence basis: NATMAPassociations as explicit linking table. citeturn41view2turn41view3  

- **Series and horizon profile retrieval**
  - `landis.series.get(series_code)` → modern definition and taxonomy.
  - `landis.horizon.get(series_code, landuse_group, depth_range)` → horizon fundamentals/hydraulics summarised with QA flags.

  Evidence basis: SOILSERIES Info and HORIZON datasets are described with keys and QA fields. citeturn16view0turn16view1turn16view2  

- **NSI access**
  - `landis.nsi.nearest_point(lat, lon, year=1983|1995)` → NSI chemistry summaries with distance and sampling year.
  - `landis.nsi.area_stats(geometry)` → aggregated stats with explicit sampling density caveats.

  Evidence basis: NSI includes Topsoil83/Topsoil95 and is point grid data. citeturn14view0  

#### Proposed derived semantic tools

These convert raw data into decision-relevant outputs and must always return:
- the underlying raw classes/values,
- an explanation,
- a caveat block,
- provenance/version.

- **Trenching difficulty estimation**
  - Inputs: route/area, wetness, drainage, depth to rock, shrink‑swell.
  - Output: categorical difficulty + drivers + “where to verify on site”.

  Evidence basis for drivers: wetness/drainage and soil engineering applications are explicitly documented. citeturn18view1turn43view1turn11view2turn17view3  

- **Corrosion and ground movement risk indicator**
  - Inputs: SOILSERIES Leacs (corrosivity to Fe/Zn; shrink‑swell class) aggregated to an area/route.
  - Output: risk band + explanation for buried pipes/assets.

  Evidence basis: Leacs dataset description and its use by water utilities. citeturn17view3turn36view0  

- **Drainage and flood-response narrative**
  - Inputs: HOST + Soilscapes drainage + wetness.
  - Output: likely hydrological behaviour patterns, with “do not infer” caveats.

  Evidence basis: HOST conceptual response modelling; Soilscapes drainage describes flood response times. citeturn18view0turn43view1turn18view1  

- **High-carbon soil screening**
  - Inputs: NATMAP Carbon stock layers.
  - Output: high/medium/low carbon stock areas + depth-layer breakdown.

  Evidence basis: NATMAP Carbon fields and stated use in GHG inventory. citeturn18view2turn36view0  

- **Pesticide leaching/runoff vulnerability screening**
  - Inputs: SOILSERIES Pesticides classes aggregated through NATMAPassociations.
  - Output: vulnerability class + explanation.

  Evidence basis: pesticide leaching/runoff fields and stated groundwater monitoring relevance. citeturn17view2turn41view2  

- **Soil Alerts explainer**
  - Inputs: location/area → soil associations/series → matched alerts.
  - Output: alert list + plain-language implications + recommended verification steps.

  Evidence basis: Soil Alerts purpose and intended audience. citeturn39view0turn41view7  

#### Resources to expose via MCP

MCP resources are well suited to static but essential context: schema, glossaries, provenance, licensing. MCP explicitly supports exposing data as resources that can be retrieved without side effects. citeturn44search4turn44search3

Core LandIS resources:
- `landis://catalog/products` (product list and coverage)
- `landis://docs/soil-data-structures` (join guidance) citeturn41view2  
- `landis://docs/soil-classification` (classification guide) citeturn41view4  
- `landis://docs/soil-information-policy` (licensing/governance context) citeturn41view0  
- `landis://docs/soilscapes-applications` (use cases + metadata) citeturn41view5turn43view0  
- `landis://schemas/natmapvector` (field definitions: MUSID etc; where available) citeturn41view2  
- `landis://schemas/horizon-fundamentals` and `landis://schemas/horizon-hydraulics` (field dictionaries and QA semantics) citeturn16view1turn16view2  
- `landis://licence/current` (pointer to the open access licence/EULA for the portal; must be validated)

#### Prompts to provide via MCP

MCP defines prompts as discoverable prompt templates exposed by servers. citeturn44search0turn44search3

Proposed LandIS prompt templates:
- **Route constraint screening prompt**: “Given a polyline, summarise soil-related construction constraints and generate a verification checklist.”
- **Local planning evidence pack prompt**: “Given an administrative area, produce a soil constraints briefing with map-layer summaries and caveats.”
- **Farm advisory prompt**: “Given a holding boundary, summarise soilscape types, drainage/wetness risks, and crop-available-water implications.”
- **Catchment vulnerability prompt**: “Given a catchment polygon, summarise HOST, drainage, wetness, and pesticide leaching indicators.”
- **Education prompt**: “Explain local soils for a non-specialist audience, highlighting uncertainty and what field checks are needed.”

Each prompt should automatically embed the Soilscapes limitation wording and a “not a substitute for field investigation” warning where applicable. citeturn43view0turn39view0  

#### Apps and app patterns

While MCP does not mandate a specific UI, the combination of tools/resources/prompts supports app patterns such as:
- map-based exploration with a geography selector,
- route analysis workbench,
- “soil knowledge card” views (soilscape / association / series),
- dashboard summaries for a selected area,
- report generator with explicit provenance fields.

These align with MCP’s goal of composable integrations across host applications. citeturn44search3turn44search32  

### Appendix 1: Candidate MCP tool catalogue

| tool/resource/prompt/app name | purpose | inputs | outputs | dependencies | stakeholder users | priority | confidence | notes |
|---|---|---|---|---|---|---|---|---|
| `landis.catalog.list_products` (tool) | discover what exists | none | product list + coverage + access tier | internal catalogue + portal metadata | all | Essential | High | Start here for UX and safety |
| `landis.metadata.get` (tool) | provenance & ISO metadata retrieval | product_id | metadata bundle + citations | ISO metadata where available | all | Essential | High | Attach to every derived output |
| `landis.soilscapes.point` (tool) | soilscape class at location | coordinate/grid ref | class + summary attrs + caveats | Soilscapes polygons citeturn43view0 | public, planners | Essential | High | Must include “generalised” warning |
| `landis.soilscapes.area_summary` (tool) | composition by soilscape | polygon | % by soilscape | Soilscapes polygons | government, NGOs | Useful | High | Supports evidence packs |
| `landis.natmap.point` (tool) | association at location | coordinate | MUSID + association | NATMAPvector + legend join citeturn41view2 | GIS pros | Useful | Medium | Depends on open portal access |
| `landis.natmap.association_series` (tool) | expand association into series mix | MUSID | series list + % | NATMAPassociations citeturn41view2 | modellers | Essential | High | Core to semantic layer |
| `landis.series.get` (tool) | series definition lookup | series_code | definition + taxonomy | SOILSERIES Info citeturn16view0 | researchers | Useful | High | Underpins explanations |
| `landis.horizon.get` (tool) | horizon properties retrieval | series_code, landuse, depth | horizon table + QA | HORIZON datasets citeturn16view1turn16view2 | modellers | Useful | Medium | Needs careful aggregation defaults |
| `landis.nsi.nearest_point` (tool) | NSI nearest values | coordinate, year | chemistry + distance + date | NSI datasets citeturn14view0 | researchers | Useful | Medium | Must emphasise sampling era |
| `landis.route.intersect` (tool) | route segmentation by soil classes | polyline, layers | segments + hotspots | spatial engine | utilities, telecoms | Useful | Medium | High-value demo tool |
| `landis.derive.trenching_difficulty` (derived tool) | decision-relevant construction constraint summary | route/area | score + causes + checklist | wetness/drainage/leacs | utilities, telecoms | Useful | Medium | Needs calibration; avoid overclaiming |
| `landis.derive.pipe_corrosion_risk` (derived tool) | corrosion + shrink-swell risk band | route/area | risk band + evidence | Leacs citeturn17view3 | water utilities | Useful | High | Strong precedent evidence |
| `landis.derive.high_carbon_screen` (derived tool) | identify high carbon soils | area | carbon depth summaries | NATMAP carbon citeturn18view2 | climate teams | Useful | High | Must include uncertainty |
| `landis.derive.hydrology_narrative` (derived tool) | translate HOST/wetness/drainage into behaviour summary | area | narrative + caveats | HOST, drainage citeturn18view0turn43view1 | EA, planners | Useful | Medium | Risk of misinterpretation |
| `landis://docs/soil-data-structures` (resource) | teach joins & keys | none | PDF/text | LandIS downloads citeturn41view2 | developers | Essential | High | Enables correct downstream use |
| `landis://docs/soil-classification` (resource) | classification glossary | none | PDF/text | LandIS downloads citeturn41view4 | all | Useful | High | Prompt and UI embedding |
| `prompt.route_constraint_screen` (prompt) | guided route assessment | route + context | structured analysis request | above tools | infra planners | Useful | Medium | Bundles caveats consistently |
| `app.route_workbench` (app pattern) | GIS-light route exploration | route + toggles | maps + report | tools + basemap | telecoms, utilities | Optional | Medium | High demonstration value |


## Stakeholder landscape and proposition evaluation

### Stakeholder landscape

Stakeholders are defined here as *groups with distinct goals, questions, and interface needs*. Awareness and barriers are assessed as **likely** (inference) unless directly evidenced.

**Stakeholder groups (summary table).**

| stakeholder group | objectives with soil/land data | likely awareness of LandIS | key barriers today | impact if access improves | best-fit interfaces |
|---|---|---|---|---|---|
| Defra policy and delivery teams | soil health indicators; land use frameworks; ELMS support; evidence for programmes | High (directly evidenced) citeturn24view0turn6view0 | historic licensing constraints; tooling fragmentation | faster policy iteration; better consistent evidence packs | semantic tools + dashboards + MCP integration |
| Non‑Crown environmental bodies (e.g., entity["organization","Environment Agency","environment regulator england"]) | flood/catchment management; pollution control | Medium (explicitly cited as impacted by licensing) citeturn6view0turn24view0 | restricted access historically; need for operable APIs | improved modelling inputs; faster screening | tools + GIS services + MCP |
| Local authorities | planning; highways; drainage; climate resilience | Medium-low | skills gap; GIS capacity; uncertainty management | improved constraint screening; fewer late-stage surprises | apps + dashboards + prompts |
| Farmers and land managers | crop planning; soil constraints; scheme eligibility | Medium (open-access target group) citeturn6view0turn21search0 | usability; interpretation risk; trust | better decision support, lower consultancy cost | map apps + conversational |
| Agronomists and advisers | drought/wetness; nutrient and pesticide risk | Medium | need for reliable, queryable access | faster advice and field prioritisation | tools + prompts + API |
| Water utilities | pipe corrosion; ground movement; risk modelling | High (explicitly referenced) citeturn17view3turn36view0 | licensing costs; integration effort | improved asset risk analytics | tools + API + MCP |
| Civil engineering & geoenvironmental consultants | ground risk screening; site appraisal | Medium | need for evidence-grade provenance; avoiding misuse | faster early-phase screening | tools + resources + dashboards |
| Insurers and risk analytics | subsidence and perils modelling | Medium (NPD referenced) citeturn36view0 | licensing; explainability | stronger underwriting insight | semantic tools + API |
| Conservation NGOs & habitat planners | restoration targeting; habitat suitability | Medium (Soilscapes habitats use evidenced) citeturn43view3 | map literacy; uncertainty | better targeting & linkage planning | apps + dashboards |
| Researchers & soil scientists | monitoring; model parameterisation | High | reproducibility under licence constraints | easier replication and innovation | downloads + API + MCP |
| GIS professionals | authoritative layers; interoperable services | High | inconsistent formats; service limitations | improved interoperability | WMS/OGC API + resources |
| AI product/agent developers | grounded environmental tools | Medium | unclear schemas; licensing; evaluation | rapid prototyping; safer agents | MCP tools + resources |

### Top 20 questions per stakeholder group

To keep the report implementable, the top‑20 questions are provided as an appendix matrix (Appendix 2). The questions are intentionally phrased as realistic tasks/decisions rather than generic “what is soil”.

### Evaluation of the MCP proposition

Proposition: “Creating an MCP server is a strong way to begin exploring and demonstrating the utility of the LandIS dataset.”

#### Technical perspective

**Strengths (evidence + inference).**
- LandIS has many deterministic spatial query primitives (lookup, summarise, intersect) and structured classification outputs, which map well to MCP “tools”. citeturn41view2turn18view1turn44search19  
- LandIS has rich schema/provenance documentation suited to MCP “resources” and “prompts”. citeturn41view2turn41view4turn44search0  
- MCP’s host/client/server model is explicitly designed for composable integrations and can reduce repeated bespoke connector work. citeturn44search3turn44search17  

**Weaknesses and risks.**
- Many LandIS layers are generalised (e.g., Soilscapes) and MCP-powered conversational use may inadvertently encourage site-scale overconfidence unless outputs embed scale and uncertainty controls. citeturn43view0turn39view0  
- If open-access portal access is not yet stable or lacks programmatic endpoints, an MCP server may require local caching/warehouse replication for performance and reliability—raising governance complexity. This is a reasonable inference rather than directly evidenced.

**Prerequisites.**
- A stable machine-readable catalogue of datasets, versions, and licences.
- A spatial execution layer (PostGIS-like or tiled vector index) and disciplined aggregation defaults matching LandIS join guidance. citeturn41view2  

#### Product and user experience perspective

**Strengths.**
- MCP can lower the “GIS barrier” by enabling natural-language tool invocation while still returning structured outputs. citeturn44search32turn44search3  
- Prompt templates can encode best practice (“don’t use Soilscapes for planning applications”) so users do not need to learn limitations the hard way. citeturn43view0turn44search0  

**Weaknesses.**
- Soil science nuance may be flattened; the system must explicitly present caveats and encourage field validation where required. citeturn39view0turn43view0  

#### Governance and assurance perspective

**Strengths.**
- Tools can embed provenance, dataset versions, and licence references by default, supporting auditability and reproducibility.

**Risks.**
- Rapid licensing transitions (open access rollout) can create ambiguity; confusion between historic licence models (time‑limited, delete derived data) and new open terms could cause compliance failures if not handled explicitly. citeturn35view0turn6view0turn38view0  

#### Strategic and innovation value perspective

A focused MCP server can act as a “value discovery harness” during the open access transition by:
- rapidly surfacing which questions users actually ask,
- enabling cross-dataset composition experiments,
- and informing subsequent formal API and portal design.

This is consistent with the policy intent to widen access and unlock innovation, and with MCP’s stated goal of composable integrations. citeturn6view0turn44search3turn44search17  

#### Alternatives and complements

- **Direct APIs (REST/OGC API – Features).** Best for high-volume programmatic integration and enterprise-grade performance; recommended as a medium-term target, especially for feature-level access. citeturn44search2turn44search14  
- **OGC WMS/WFS-style services.** Strong for GIS clients and visualisation; already evidenced. citeturn30search5turn27view0  
- **Download-only models.** Good for research reproducibility, but high barrier for non-experts and weak for composability.
- **Portals/viewers.** Good for exploration but often poor for integration and automation.
- **MCP.** Best when the aim is rapid composable tool exposure across multiple host environments, especially for mixed technical/non-technical audiences, and when you want to standardise prompts/resources alongside tools. citeturn44search3turn44search32  

**Conclusion (disciplined).** MCP is a strong *first* move if it is implemented as a provenance-aware semantic access layer and paired with a roadmap towards formal APIs/OGC services. It is not a substitute for proper geospatial API productisation, but it is strategically useful for early value discovery and demonstrator development.


## Prioritised roadmap, evidence register, bibliography, and appendices

### Prioritised roadmap

**Immediate discovery work**
- Validate what the open access portal exposes (dataset list, licences, any API endpoints, bulk downloads, query limits). citeturn38view0turn6view0  
- Build an internal “LandIS product registry” derived from documented dataset families and ISO metadata, including version labels and provenance notes. citeturn12view0turn43view0turn7view0  
- Identify 3–5 high-value pilot workflows aligned to evidenced demand: flood/catchment screening, wetness/carbon screening, utilities corrosion/shrink‑swell screening, planning evidence packs. citeturn24view0turn17view3turn18view2turn18view1  

**MVP MCP server**
- Implement `catalog`, `metadata`, `soilscapes.point`, `soilscapes.area_summary`, and `soil_alerts_for_area` first.
- Add one “hero” derived tool (pipe corrosion/shrink-swell risk summary) because it has strong documented precedent in utilities. citeturn17view3turn36view0  
- Ship prompt templates for 3 pilot personas (local authority planner; water utility analyst; catchment manager).

**Ingestion and modelling priorities**
- If bulk data is available: build a spatial warehouse with:
  - Soilscapes polygons and attributes,
  - NATMAPvector polygons + NATMAPlegend + NATMAPassociations,
  - selected derived layers (wetness, HOST, carbon),
  - NSI points as self-standing dataset. citeturn41view2turn14view0turn18view0turn18view1turn18view2  

**Pilot stakeholders**
- Defra cross-policy data users; Environment Agency flood teams; at least one local authority planning team; one water utility asset risk team; one conservation/habitat planning partner. citeturn6view0turn24view0turn43view3turn17view3  

**Evaluation questions**
- Does access time for “basic soil constraints for an area” drop from days/weeks to minutes?
- Do users correctly interpret limitations (measured by prompt‑embedded “caveat recall”)?
- Which tools get used most; what follow-up data do users demand?

**Success metrics**
- Adoption: number of active users/clients and repeat usage.
- Quality: proportion of outputs including provenance/limitations; user-reported trust.
- Efficiency: time saved in evidence pack creation; reduction in duplicate bespoke GIS work.

**Future API/app evolution**
- Promote stable feature-level APIs (OGC API – Features or equivalent) for key layers where demand and governance justify it. citeturn44search2turn44search14  
- Keep MCP as the orchestration and semantic layer that composes across multiple datasets and servers.

### Evidence register

URLs are provided in code formatting.

| source title | organisation/author | date | URL | type of evidence | key claims supported |
|---|---:|---:|---|---|---|
| LandIS homepage (“Soils have become Open Access!”) | Cranfield University | accessed 2026‑04‑04 | `https://www.landis.org.uk/` | official portal page | open access claim; portal link; system description citeturn38view0 |
| Open Access LandIS Portal (pipeline notice) | Defra Group Commercial | 2025‑02‑18 | `https://www.find-tender.service.gov.uk/Notice/005506-2025` | UK Government procurement notice | historic access constraints; decision to open majority data; policy initiatives citeturn6view0 |
| World Soil Day blog: improving access | Defra digital blog | 2023‑12‑05 | `https://defradigital.blog.gov.uk/2023/12/05/world-soil-day-how-were-improving-access-to-soils-data-and-information-for-england-and-wales/` | official government blog | govt recognition; IPR joint ownership; dataset contents; use examples citeturn24view0 |
| Soil data repository to become open access | Cranfield University | 2026‑01‑29 | `https://www.cranfield.ac.uk/press/news-2026/soil-data-repository-to-become-open-access` | official press release | open portal agreement; launch during 2026; NATMAP included citeturn21search0 |
| Digital Soil Dataset Families | LandIS | accessed 2026‑04‑04 | `https://www.landis.org.uk/data/datafamilies.cfm` | official technical overview | dataset families; class counts; grid products; NSI description citeturn12view0 |
| NATMAP overview | LandIS | accessed 2026‑04‑04 | `https://www.landis.org.uk/data/natmap.cfm` | official technical overview | NATMAP provenance; redigitisation; derived products citeturn13view0 |
| NSI overview | LandIS | accessed 2026‑04‑04 | `https://www.landis.org.uk/data/nsi.cfm` | official technical overview | NSI grid, sampling era, variables, INSPIRE case study citeturn14view0 |
| Soil data structures and relationships | LandIS (CEC) | 2024‑04 | `https://www.landis.org.uk/downloads/downloads/Soil%20Data%20Structures.pdf` | official information paper | NATMAPassociations join model; NSI self-standing citeturn41view2turn41view3 |
| National Soil Map and Soil Classification | LandIS (CEC) | 2024‑04 | `https://www.landis.org.uk/downloads/downloads/Soil%20Classification.pdf` | official classification paper | association/series taxonomy; map basis citeturn41view4 |
| Soilscapes use and applications brochure | LandIS (CEC) | 2024‑04 | `https://www.landis.org.uk/downloads/downloads/Soilscapes_Brochure.pdf` | official brochure | Soilscapes metadata; limitations; drainage/habitat uses citeturn43view0turn43view1turn43view3 |
| Cranfield Mapshop FAQ | Cranfield Mapshop | accessed 2026‑04‑04 | `https://cranfield.blueskymapshop.com/about/faqs` | commercial terms | time-limited licence; delete derived data; map redigitisation note citeturn35view0 |
| Cranfield Mapshop – Soil Data products | Cranfield Mapshop | accessed 2026‑04‑04 | `https://cranfield.blueskymapshop.com/products/soil-data` | product catalogue | formats; HOST/carbon/auger bores numbers; NPD relation citeturn36view0 |
| UKSO soils of England and Wales | UK Soil Observatory | accessed 2026‑04‑04 | `https://www.ukso.org/static-maps/soils-of-england-and-wales.html` | third-party portal | WMS link references; thematic map descriptions citeturn27view0 |
| EJPSoil catalogue entry with WMS link | EJPSoil catalogue | updated 2019‑01‑01 | `https://catalogue.ejpsoil.eu/collections/metadata%3Amain/items/Soil-map-for-England-and-Wales` | metadata catalogue | explicit LandIS WMS endpoint citeturn30search5 |
| Model Context Protocol specification (overview) | Model Context Protocol project | 2025‑11‑25 | `https://modelcontextprotocol.io/specification/2025-11-25` | protocol specification | MCP host/client/server model; JSON‑RPC; goals citeturn44search3 |
| MCP tools and prompts documentation | Model Context Protocol project | 2025‑11‑25 / 2025‑06‑18 | `https://modelcontextprotocol.io/specification/2025-11-25/server/tools` `https://modelcontextprotocol.io/specification/2025-06-18/server/prompts` | protocol documentation | definitions of tools/prompts and usage citeturn44search19turn44search0 |
| OpenAI MCP server guidance | OpenAI | accessed 2026‑04‑04 | `https://developers.openai.com/api/docs/mcp/` | platform documentation | MCP server positioning for ChatGPT and API integrations citeturn44search32 |
| OGC API – Features standard overview | Open Geospatial Consortium | accessed 2026‑04‑04 | `https://www.ogc.org/standards/ogcapi-features/` | standards documentation | feature-level API building blocks; fine-grained access citeturn44search2 |

### Bibliography

- Cranfield University. “Mapping and understanding soil types across England and Wales.” `https://www.cranfield.ac.uk/case-studies/national-soil-map` citeturn34view0  
- LandIS. “LandIS data applications.” `https://www.landis.org.uk/overview/applications.cfm` citeturn11view2  
- LandIS. “NATMAP HOST.” `https://www.landis.org.uk/data/nmhost.cfm` citeturn18view0  
- LandIS. “NATMAP Wetness.” `https://www.landis.org.uk/data/nmwetness.cfm` citeturn18view1  
- LandIS. “NATMAP Carbon.” `https://www.landis.org.uk/data/nmcarbon.cfm` citeturn18view2  
- LandIS. “NATMAP Crop Available Water.” `https://www.landis.org.uk/data/nmap.cfm` citeturn19view0  
- LandIS. “Soil Series: Leacs / Pesticides / Hydrology / Agronomy.” `https://www.landis.org.uk/data/ssleacs.cfm` etc. citeturn17view3turn17view2turn17view0turn17view1  
- LandIS. “Soil Alerts.” `https://www.landis.org.uk/soilsguide/soil_alerts.cfm` citeturn39view0  
- Data.gov.uk. “NATMAP – National Soil Map.” `https://www.data.gov.uk/dataset/ea1442bf-ba77-42cc-80e7-2ea339ccb28a/natmap-national-soil-map1` citeturn7view0  
- Data.gov.uk. “Soilscapes.” `https://www.data.gov.uk/dataset/26d61739-e05b-420d-8fd0-d11edffa8b27/soilscapes1` citeturn9view0  
- Natural Resources Wales metadata record (LandIS soil data in Wales). `https://test.metadata.naturalresources.wales/geonetwork/srv/api/records/EXT_DS119264` citeturn32view0  

### Appendix 2: Stakeholder-question matrix

The table below lists the *top 20* realistic questions/tasks per stakeholder group. These are written as user questions that a LandIS‑exposed tool ecosystem could answer.

| stakeholder group | top 20 questions/tasks |
|---|---|
| Defra policy and delivery teams | 1) Which soil constraints dominate each Local Nature Recovery Strategy area? 2) Where are high-carbon soils (by depth layer) and what land uses overlap them? 3) Which areas have soils most vulnerable to drought (low crop-available water) under current rooting models? 4) Where are soils most prone to seasonal wetness that could constrain scheme options? 5) What is the uncertainty/scale caveat for each soil constraint map we cite in policy? 6) Which soil types are likely to have hidden peat layers requiring survey attention? 7) For a proposed land-use change scenario, what soil risks should we explicitly assess? 8) How do soils vary across administrative boundaries for a given programme footprint? 9) Which soil layers are used in the GHG inventory assumptions and what map products feed them? 10) What change-monitoring evidence exists in NSI (1983 vs 1995) for target indicators? 11) Where are soils likely to leach pesticides/runoff into water bodies for WFD‑related policies? 12) Which soil alerts are most common in areas targeted for habitat creation? 13) For a ministerial brief, what are the top soil constraints nationally and regionally? 14) Which datasets are open access vs restricted and what licence terms apply? 15) What are the join rules between associations, series, and horizons for analytical modelling? 16) For a new metric proposal, what stable soil classifications exist and how do they map to international schemes? 17) What is the “do not infer” list for each dataset (planning/site scale limitations)? 18) Which complementary datasets are needed to interpret soils for land-use trade-off analysis? 19) What is the version/date lineage for the datasets used in a published analysis? 20) Can we generate consistent soil evidence packs automatically for programme teams? |
| Environment Agency and catchment managers | 1) What HOST classes dominate this catchment and what runoff/baseflow behaviours do they imply? 2) Which subcatchments have the wettest soils likely to respond rapidly to storms? 3) Where are soils likely to transmit pollutants to groundwater (leaching classes)? 4) Where does Soilscapes drainage indicate high runoff vs infiltration pathways? 5) How should we caveat soils data when used for operational flood risk decisions? 6) Which river reaches have surrounding soils prone to waterlogging and overland flow? 7) Where might soil structure degradation increase runoff risk (proxy indicators)? 8) How do soil constraints vary along a proposed natural flood management corridor? 9) For a pollution incident, what soil types could accelerate contaminant transport? 10) What are the likely groundwater-connected soils in a Source Protection Zone? 11) Can we prioritise field inspections using soil risk screening? 12) Which soils are susceptible to erosion and what mitigation should be considered? 13) What soil properties should be fed into our catchment models, and at what resolution? 14) Which data products are appropriate for strategic vs local modelling? 15) How can we retrieve soil constraints programmatically per catchment? 16) What is the best way to combine HOST, wetness, and land cover for vulnerability mapping? 17) Where are engineered interventions likely to trigger acid sulphate soil risks? 18) What soil alerts apply to riparian restoration projects? 19) What is the provenance and update status of each soil layer we use? 20) Can we generate a reproducible soil-layer package for each modelling run? |
| Local authority planners and highways/drainage teams | 1) What soil wetness constraints should we reference in planning decisions for this site? 2) Is Soilscapes appropriate evidence for this planning application, and if not what should we do? 3) Which wards/LSOAs have the highest shrink‑swell ground movement risks? 4) Which road segments coincide with soils likely to suffer subgrade instability or heave? 5) Where are soakaways likely to be unsuitable due to wetness/drainage? 6) For SuDS planning, what soils are likely to infiltrate vs run off? 7) Where are corrosion risks to buried assets highest? 8) What soil alerts apply to proposed earthworks and soil translocation projects? 9) How does soil type vary across a development allocation area? 10) What are the “must verify on site” flags for soil-derived screening? 11) Can we create a standard “soil constraints briefing” for planning committees? 12) Where might buried peat or soft soils create foundation issues? 13) How do soil constraints interact with flood zones and groundwater vulnerability areas? 14) What are the dominant soils in our authority area for a local plan evidence base? 15) How can we integrate soil layers into our GIS with standard services? 16) What version of soil data did we cite last year, and has it changed? 17) Which land parcels have soils suitable for habitat creation targets? 18) How do we procure/use higher-resolution soils evidence if needed? 19) Can we automatically attach soil caveats to every map we publish? 20) What training do non-soil specialists need to interpret soil outputs safely? |
| Farmers and land managers | 1) What soilscape type is my field and what does it imply for drainage and workability? 2) Am I likely to have a peaty topsoil or hidden peat layer? 3) Which parts of my holding are most drought-prone (available water)? 4) Which parts are most likely to waterlog in winter? 5) What crop rooting depth assumptions drive the available-water estimate? 6) What soils on my holding are most sensitive to compaction? 7) Where should I prioritise field pits/auger checks to validate map expectations? 8) Are there soil alerts (e.g., ironpans, acid sulphate risk) relevant to planned works? 9) What does my soil imply for nitrate leaching or pesticide runoff risk? 10) Which fields are likely to be harder to cultivate after rainfall events? 11) How should I interpret Soilscapes limitations for field-level decisions? 12) Can I get a printable soil summary pack for my farm? 13) How do soils vary across the boundary of my holding? 14) What are the likely soil textures of my topsoil/subsoil? 15) What is the best season window for field works given wetness class? 16) Where might drainage investment pay off most? 17) Which soils are likely to have low natural fertility? 18) How do soil properties differ under arable vs grass assumptions in the dataset? 19) What parts of my land are suitable for scheme options that require particular soil conditions? 20) If I need higher confidence, what dataset or survey should I commission? |
| Water utilities asset risk teams | 1) Which pipe segments run through high-corrosivity soils (Fe/Zn)? 2) Where is shrink‑swell risk highest along our network? 3) Which assets are in seasonally wet soils likely to complicate repairs? 4) What is the likely failure risk uplift from soil-driven corrosion factors? 5) How do we explain soil risk drivers to non-soil stakeholders? 6) Which soil risks cluster near historic bursts? 7) What soil drainage patterns correlate with ground movement or washout? 8) Where should we prioritise proactive replacement based on soil risk? 9) What are the caveats about using soil maps at street scale? 10) Can we generate a reproducible soil risk layer package per asset cohort? 11) What is the versioning/provenance of the soils layers feeding our models? 12) Can we query soil risk at a point quickly for field teams? 13) Which soil characteristics suggest difficult excavation conditions? 14) Where are shallow rock or hard substrates likely? 15) How do soil risks vary by operational region? 16) Can we automate soil intersection for new capital programmes? 17) How can we integrate soils data into our GIS and asset platforms? 18) Which soils are likely to facilitate pollutant transport from sewer failures? 19) How can we audit that we used licensed/open data correctly? 20) What additional datasets do we need to calibrate soil risk to observed failures? |
| AI platform and agent developers | 1) What are the authoritative LandIS datasets available and their access tiers? 2) How do I safely interpret soil polygons without implying site certainty? 3) What is the join model from NATMAP associations to soil series/horizons? 4) What schema/code lists exist for soil classes? 5) How do I attach provenance and version fields to every tool output? 6) Which tools should be low-level deterministic vs derived semantic? 7) What are the “do not infer” caveats for each dataset type? 8) How can I build route intersection tools efficiently? 9) How should coordinate input be validated (WGS84 vs BNG)? 10) What are safe defaults for aggregation (dominant series vs weighted mean)? 11) How do I expose docs and glossaries as resources? 12) Which stakeholder prompts are highest value? 13) How do I prevent hallucinated soil claims in LLM output? 14) What evaluation suite can test soil reasoning correctness? 15) How do we handle licensing constraints in an agentic workflow? 16) What does “open access” mean in practice for redistribution? 17) How do we integrate LandIS with OGC API – Features services from other providers? 18) What caching strategy is required for scalability? 19) What security model is needed for hosted MCP servers? 20) What monitoring is needed to detect misuse or misinterpretation? |

### Appendix 3: Capability map

| need / task type | downloads | viewer | API (OGC/REST) | MCP resource | MCP tool | MCP app | prompt template | dashboard |
|---|---|---|---|---|---|---|---|---|
| Locality “what soils are here?” | Medium | High | High | Medium | High | High | High | Medium |
| Evidence-grade reproducible modelling | High | Low | High | Medium | Medium | Low | Low | Medium |
| Route/asset intersection at scale | Low | Medium | High | Low | High | High | High | Medium |
| Non-specialist guidance and caveats | Low | Medium | Medium | High | High | High | High | High |
| Cross-dataset composable reasoning | Low | Low | High | Medium | High | High | High | Medium |
| Governance/provenance inspection | Medium | Low | High | High | High | Medium | Medium | Medium |

### Appendix 4: Open questions and uncertainties

The following issues require validation against the open access portal’s current operational reality.

What specific datasets are included in “open access” on the new portal, and which remain commercial/specialist?

What is the authoritative open-access licence/EULA text for `portal.landis.org.uk`, and does it permit redistribution, derivative works, and commercial reuse?

Are there bulk download packages for key datasets (NATMAPvector, Soilscapes, HOST, wetness, carbon, NSI), and are they versioned with stable identifiers?

Are programmatic query endpoints available (ArcGIS REST, OGC API – Features, WFS), or only WMS and viewers?

What are the update/versioning policies post-open-access (frequency, changelogs, deprecation)?

What are the recommended aggregation defaults when mapping series/horizon attributes through association polygons (dominant series vs weighted average), and how should uncertainty be represented?

How should soil alerts be attached to mapped units programmatically (lookup keys and thresholds)?

What safeguards will be required to prevent misuse of generalised datasets in high-stakes planning and engineering decisions?

How will provenance of historic OS data usage be represented in open access outputs (e.g., crown copyright notices embedded in derived outputs)? citeturn43view2