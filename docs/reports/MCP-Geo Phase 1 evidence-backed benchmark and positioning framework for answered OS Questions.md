# Inventory of current UK public-sector questions answered using Ordnance Survey data

## Executive summary

This study compiled a high-confidence baseline inventory of **25 distinct, evidenced “question → answer/output → OS data/products → access mode → user/team” use cases** currently found in published public-sector and closely related materials (central government, local government, NHS, police/fire, and selected public authorities). The inventory is delivered as a master table (CSV/XLSX) with the exact column set requested.

[Download the master table (CSV)](sandbox:/mnt/data/os_public_sector_use_cases_inventory_2026-03-08.csv)
[Download the master table (XLSX)](sandbox:/mnt/data/os_public_sector_use_cases_inventory_2026-03-08.xlsx)

Across the evidence collected, the most consistently confirmed, operationally “real” public-sector questions answered using OS data fall into five dominant clusters:

Public-sector **addressing and identifier questions** (UPRN-centred) are repeatedly evidenced in both public health and emergency response. The **entity["organization","UK Health Security Agency","public health agency, uk"]** explicitly states that property classifications in its COVID-19 surveillance reporting are derived from **Ordnance Survey AddressBase**, with properties identified using **UPRN and BLPU**. citeturn28view0. A closely related emergency-services pattern is explicit in the **entity["organization","London Ambulance Service NHS Trust","ambulance trust, london, uk"]** case study: call handlers verify addresses and obtain grid references and UPRNs, using **OS Places API** specifically because it “requires no downloading or storage” for UK-wide addressing. citeturn44view0.

Public-sector **postcode/location lookup** appears as a mature “API + cache + refresh” pattern within **entity["organization","GOV.UK","uk government website"]** platform operations. Developer documentation for `locations-api` states that it caches OS Places API results in PostgreSQL and continuously refreshes cached postcode records. citeturn29view1.

Public-sector **planning and policy mapping** is anchored by an explicit statutory/standards driver: **entity["organization","Department for Levelling Up, Housing and Communities","uk central government department"]** guidance recommends OS basemaps (including **OS MasterMap Topography Layer**) via the **OS Maps API** for policies maps used to show how planning policies apply geographically. citeturn32view0.

Public-sector **network/routing questions** are evidenced in both local-government service delivery and emergency dispatch. A clear local-government operational example is **entity["organization","Northumberland County Council","local authority, england, uk"]** optimising waste collection routes using OS MasterMap road network data and road restrictions. citeturn45view0. A clear emergency dispatch analogue is **entity["organization","North West Fire Control","fire control centre, north west england, uk"]** using AddressBase Premium and OS MasterMap/ITN to pinpoint caller locations (including when callers cannot provide an address) and to mobilise the quickest resources. citeturn46view0.

Public-sector **“filter, count, and map buildings meeting a threshold”** questions are evidenced via OS NGD-era delivery. **entity["organization","North Yorkshire Fire and Rescue Service","fire and rescue service, england, uk"]** used **OS Select+Build** and **OS Building Features** to answer: how many buildings are over **18 metres or seven floors**. citeturn47view0.

These findings are descriptive of “what is confirmed in today’s evidence”, not a statement of sector-wide completeness (see Coverage and limits).

## Method and evidence rules

Evidence was collected and scored using a source-weighting approach aligned to the user’s rules:

Official primary evidence sources were prioritised: GOV.UK guidance/statistics/publications; official datasets and metadata pages published by public bodies; and official public code/configuration in repositories owned by public-sector organisations. Examples include the DLUHC policies-map guidance citeturn32view0, the Environment Agency dataset lineage explicitly naming AddressBase Premium and OS MasterMap Topography dependency citeturn48view0, and ONS methodology explicitly describing AddressBase as the sampling frame maintained by Ordnance Survey citeturn31view0.

Official secondary evidence was used extensively where it directly documents named organisations and workflows: Ordnance Survey case studies (“vendor case studies”) are treated as **official secondary**—useful, but sometimes incomplete on access model details. Examples include ambulance address verification via OS Places API citeturn44view0 and local authority waste route optimisation citeturn45view0.

Secondary/weak-signal evidence was used cautiously and labelled as such (in this phase, the strongest “secondary” items retained were procurement notices that directly confirm acquisition and intended capability, because they are official publications even when use-case detail is thin). Examples include procurement for “Ordnance Survey Point of Interest” by the **entity["organization","British Transport Police Authority","public authority, uk"]** citeturn15view0 and a policing GIS platform procurement describing consumption of Ordnance Survey and AddressBase datasets. citeturn15view1.

Question normalisation was done as follows: if the source states a literal question, it is captured verbatim; if it describes a workflow (dashboard, map, analysis), the underlying question is restated in natural language and labelled as **strongly implied** or **weakly inferred** (recorded in the table).

OS dependency classification was applied conservatively:
- **OS-essential** where the workflow/output explicitly depends on a named OS product or OS-derived identifiers in a way that is hard to replace (for example AddressBase-derived classifications for official surveillance outputs). citeturn28view0turn48view0
- **OS-primary** where OS data is a central analytic substrate (for example road-network optimisation). citeturn45view0
- **OS-supporting** where OS basemaps/boundaries primarily support visualisation or contextual mapping (common in NHS planning case studies). citeturn52view0turn53view0
- **OS-uncertain** where OS usage is evidenced (for example an API key is configured) but the specific downstream operational question is not yet confirmed in the collected sources. citeturn14view0

## Coverage and limits

Facts about coverage in this phase:

The master inventory includes use cases evidenced across central government departments and bodies (including **entity["organization","Home Office","uk central government department"]**, **entity["organization","Office for National Statistics","national statistics institute, uk"]**, **entity["organization","Department for Transport","uk central government department"]**, **entity["organization","HM Land Registry","land registry, uk"]**, and **entity["organization","HM Revenue & Customs","tax authority, uk"]**). citeturn51view0turn31view0turn18search8turn41view0turn43view0. It includes local authorities and regional bodies, plus emergency services and NHS organisations. citeturn45view0turn49view0turn46view0turn44view0turn54view0.

This is not claimed to be exhaustive across the UK public sector. It is an evidence-backed baseline constrained by what is explicitly published and discoverable within time and tool limits, and by what can be confirmed without private/internal documentation.

Key limits (as observed in the sources) that directly affect “exhaustiveness”:

Access-model detail is often omitted in public descriptions. Many credible case studies name OS products but do not specify whether access was via **bulk resupply downloads**, **Downloads API automation**, **locally hosted enterprise GIS copies**, or a vendor-managed embedded supply chain. This is especially visible in vendor case studies that focus on outcomes and programme narratives rather than architectures. citeturn45view0turn50view0turn51view0.

Devolved-administration coverage is partial in this phase. England-focused sources dominate for planning and some datasets (for example the DLUHC policies map guidance explicitly applies to England). citeturn32view0. The table includes UK-wide or Great Britain-wide uses (AddressBase/UPRN patterns in public health, ONS and emergency services), and one clearly Scotland-public-body-adjacent case study in the dataset (but the baseline still underrepresents devolved and local-body publishing outside England). citeturn28view0turn31view0.

## Inventory of confirmed OS-dependent questions

The master table is the primary deliverable for the inventory and is provided as downloadable CSV/XLSX (links in Executive summary). It contains one row per distinct use case plus fields for: organisation/team, question, outputs, OS products, OS data types/identifiers, access pattern, evidence quote/date, and confidence.

A short, human-readable index of the highest-confidence exemplars (each of these is fully expanded in the table):

The **entity["organization","Environment Agency","environment regulator, england, uk"]** publishes a “Flood risk: Postcode search tool” dataset whose lineage explicitly states that an internal receptor dataset is “based on Ordnance Survey data (AddressBase Premium and OS MasterMap Topography Layer)”. The operational question is explicitly postcode-based flood-risk summarisation for an embeddable tool. citeturn48view0.

The **UK Health Security Agency** explicitly uses “Ordnance Survey AddressBase” to derive property classifications for COVID-19 cases, using UPRN and BLPU. This is a direct “address matching → property type classification → surveillance output” pipeline. citeturn28view0.

The **entity["organization","Government Digital Service","government digital unit, uk"]** (via GOV.UK developer documentation) documents a concrete operational “postcode lookup” service (`locations-api`) that calls OS Places API and caches results in PostgreSQL with continual refresh workers—an explicit “live API + cached copy + update pattern” architecture. citeturn29view1turn29view0.

The **London Ambulance Service NHS Trust** explicitly implements OS Places API for “out of area address look ups” to obtain correct address + grid reference + UPRN without bulk-loading nationwide AddressBase; the evidence spells out why the API was chosen (no local storage). citeturn44view0.

The **entity["organization","North Yorkshire Fire and Rescue Service","fire and rescue service, england, uk"]** explicitly uses OS Select+Build and OS Building Features to answer a statutory/safety-driven building threshold question (buildings over 18m or 7 floors), producing a mapped output and spreadsheet. citeturn47view0.

The **Office for National Statistics** explicitly uses AddressBase as a sampling frame “maintained by Ordnance Survey” for the COVID-19 Infection Survey in Great Britain. citeturn31view0.

The **Department for Levelling Up, Housing and Communities** explicitly states that Land Use Statistics for England are derived from AddressBase Premium, OS MasterMap Sites Layer, OS MasterMap Topography Layer and OS Open Greenspace. citeturn31view1.

The **Department for Transport** explicitly states an intention to use OS MasterMap Highways Network as the sole source for road length estimates (and describes year-on-year changes reflecting methodological improvements in that dataset). citeturn18search8.

Local-government operational routing is documented in Northumberland’s garden waste route optimisation, with an explicit statement that OS MasterMap road network data (with turn restrictions) is central to creating efficient routes. citeturn45view0.

A policing operational platform procurement notice explicitly describes a system that consumes authoritative geospatial datasets including Ordnance Survey and AddressBase/gazetteers to support “map-driven analysis, demand prediction, patrol planning and live resource location”. citeturn15view1.

## Patterns across sectors, OS products, and access models

This section reports cross-cutting patterns observed in the collected evidence, separating what is explicit from what is inferred.

Addressing, UPRNs, and place lookup

Explicit evidence shows AddressBase and UPRN/BLPU being used to transform administrative or operational records into geospatially analysable units.

In public health surveillance, UKHSA’s report explicitly states that property classifications are derived from AddressBase and matched to laboratory address data, with properties identified by UPRN and BLPU. citeturn28view0. This is an archetypal “What type of property is this case associated with?” question, producing aggregate outputs suitable for national reporting.

In emergency response, London Ambulance explicitly uses AddressBase Premium for in-area response and OS Places API for out-of-area verification, obtaining grid references and UPRNs to reduce dispatch error. citeturn44view0. North West Fire Control similarly uses AddressBase Premium, with a workflow that can convert map coordinates into an address when the caller cannot provide one. citeturn46view0.

In national statistics, ONS explicitly positions AddressBase as a maintained list used as a sampling frame for the COVID-19 Infection Survey. citeturn31view0, and it separately publishes UPRN-based products to allocate addresses to Output Areas and other geographies through point-in-polygon methodology. citeturn16search1. These are direct public-sector answers to “Which geography does this address belong to?” questions.

Road links, routing constraints, and network analytics

Road network questions appear in both operational and statistical contexts.

Operational routing optimisation is explicit in Northumberland’s garden waste use case, where OS MasterMap road network data (including turn restrictions) informs where and when vehicles can travel. citeturn45view0. Emergency-service dispatch similarly frames a routing optimisation problem around “quickest resource to incident”, with OS road/topography context supporting accurate location and mobilisation. citeturn46view0.

National road network measurement is explicitly tied to OS MasterMap Highways Network in DfT statistical publications, with intent to use it as the sole source once quality is sufficient. citeturn18search8turn18search16.

Buildings and infrastructure features

A clear buildings threshold/filter question is explicitly documented in the North Yorkshire Fire & Rescue case study: identifying buildings over a height/floor threshold, using OS Select+Build and OS Building Features. citeturn47view0.

In transport scheme design, Transport for West Midlands describes methodologies for generating granular street-scene widths and street gradient insights, underpinned by OS datasets (MasterMap Topography, Highways, AddressBase, OS Open Roads). citeturn50view0. The “street width every 1 metre” claim is explicit, while the precise underlying “question” is a strongly implied planning/design question rather than a single published interrogative.

Boundaries, zones, and basemaps as operational backdrops

The DLUHC policies-map guidance is explicit that policy maps should use OS maps (and recommends OS Maps API delivery and OS MasterMap Topography for site-level policy understanding). citeturn32view0. This positions OS basemaps as legally and operationally central to planning-policy communication.

In health service planning case studies, OS boundaries and basemaps often play a “supporting” role: Birmingham and Solihull Mental Health NHS FT uses OS boundary/basemap products to visualise and analyse referral patterns and inequities. citeturn52view0. Cheshire and Wirral Partnership NHS FT uses OS VectorMap District and raster mapping to model client distribution versus service locations. citeturn53view0. In both, the OS products are explicit, but the more critical data may be internal patient/service records; hence OS is often “supporting” for the analytic question rather than the unique enabling identifier (unless AddressBase/UPRN linkage is also present, which is not explicit in those two case studies). citeturn52view0turn53view0.

Access models

Evidence in this phase confirms several distinct access patterns:

Live API + caching is explicitly documented for GOV.UK postcode lookups: `locations-api` calls OS Places API and caches responses in PostgreSQL with continual refresh. citeturn29view1.

Live API with explicit “no download/storage” motivation is explicitly described for emergency addressing in London Ambulance. citeturn44view0.

OS Maps API use is explicitly recommended for planning basemaps in DLUHC guidance. citeturn32view0.

Targeted data downloads through OS Data Hub Select+Build are explicitly documented in the North Yorkshire Fire & Rescue use case. citeturn47view0.

Enterprise/local cached datasets are strongly evidenced in local government via a published metadata page that includes internal layerfile paths for OS MasterMap Highways data used by **entity["organization","Hertfordshire County Council","local authority, england, uk"]** staff. citeturn33search3.

Finally, configuration evidence indicates GOV.UK frontend is provisioned with an OS Maps API key (OS_MAPS_API_KEY), but the exact user-facing journeys and question types are not confirmed within this phase, so this is recorded as OS-uncertain. citeturn14view0.

## Teams and workflows

Evidence in this phase shows two broad “user/team” patterns: specialist GIS/analytics intermediaries, and embedded operational users supported by integrated platforms.

GIS and analytics intermediaries frequently appear as the operational “question-answerers”. North Yorkshire Fire & Rescue explicitly describes a GIS team using OS Select+Build to rapidly answer a building-height threshold question and return a mapped output and spreadsheet. citeturn47view0. Cheshire and Wirral Partnership NHS FT explicitly names a Knowledge Manager and GIS analyst producing ~100 maps to inform service redesign decisions. citeturn53view0. Local authority planning workflows (for example Broxtowe’s SHLAA process) are described as GIS overlays and constraint calculations that reduce officer time and produce publishable site information. citeturn49view0.

Operational teams appear where OS data is embedded into workflow software. Emergency call handling and mobilisation is an exemplar: OS addressing and mapping are used in the control room context to identify caller location, resolve addresses from coordinates, and select the quickest available resources. citeturn46view0turn44view0. Likewise, the policing platform procurement describes an end-to-end operational system consuming OS and AddressBase/gazetteers to support map-driven analysis, demand prediction, and patrol planning. citeturn15view1.

Where the evidence is strongest, the “actual question” is either:
- asked in the moment (for example “What is the correct address/grid reference for this call?”), or
- asked as a repeated operational analysis query (for example “Which buildings exceed threshold?” “Which patients are eligible based on distance?” “How do policies apply to this site?”). citeturn44view0turn47view0turn54view0turn32view0.

## Candidate MCP-Geo question types already grounded in current public-sector OS usage

The list below is restricted to question types directly evidenced (explicitly or strongly implied) by the sources included in the master table. Each item maps to multiple real workflows already documented.

Address and identifier resolution:

“Given this postcode, what is its authoritative location/address result set (and how should it be cached/kept fresh)?” grounded in GOV.UK `locations-api` using OS Places API with PostgreSQL caching and background refresh. citeturn29view1.

“Given this (possibly partial) address, what is the correct address plus coordinates/grid reference and UPRN so responders can navigate correctly?” grounded in London Ambulance using OS Places API for out-of-area verification. citeturn44view0.

“Given coordinate X/Y, what is the nearest/true address (and what is its UPRN)?” grounded in North West Fire Control obtaining an address from AddressBase Premium using map coordinates. citeturn46view0.

Property-type and setting classification:

“Given a case record with an address, what property type/setting is it associated with (care home, prison, HMO, etc.)?” grounded in UKHSA deriving classifications from AddressBase with UPRN/BLPU. citeturn28view0.

Threshold and selection queries over buildings:

“How many (and which) buildings in this area exceed threshold T (height/floors), and where are they?” grounded in North Yorkshire Fire & Rescue using OS Select+Build and OS Building Features. citeturn47view0.

Routing and proximity analysis:

“Given a set of service addresses, what are the most efficient vehicle routes subject to turn restrictions and network constraints?” grounded in Northumberland’s waste route optimisation. citeturn45view0.

“Which population records are beyond distance D from facility type F (for example >1.6km from a pharmacy)?” grounded in NHS SCW’s dispensing-list validation using OS AddressBase and Code-Point. citeturn54view0.

Planning and policy applicability:

“For this site/location, which planning policies and constraints apply, and how do they intersect with the site boundary?” grounded in the legally driven OS-based policies map requirement and the SHLAA-style constraint overlay process. citeturn32view0turn49view0.

Initial implications for MCP-Geo test design (grounded in the above)

Test suites should include both “single-shot” and “pipeline” questions: for example, address-to-UPRN resolution followed by “within buffer/intersects polygon” queries and summarisation (mirroring the UKHSA and flood-risk patterns). citeturn28view0turn48view0.

Tests should separate access constraints from reasoning: some real workflows explicitly prefer API to avoid bulk storage (ambulance OS Places), while others demonstrably operate on locally cached enterprise datasets (county council MasterMap layerfiles). citeturn44view0turn33search3.

Derived-metric queries (street width/gradient, building thresholds) should be included as first-class tasks, reflecting transport and fire-building-review evidence. citeturn50view0turn47view0.

## Evidence gaps to investigate in Phase 2

The following are evidence gaps observed during collection, prioritised by how directly they block confident mapping of “question → OS product → access mode → team”.

Access-model confirmation gaps:

For multiple high-value case studies (transport planning, crime hotspot analytics, some NHS planning cases), OS products are named but whether access is via **OS NGD APIs**, **OS Maps API**, **bulk resupply downloads**, or **vendor-managed embedded datasets** is not stated. Phase 2 should target architecture docs, technical blogs, and platform runbooks inside public-sector repos and procurement appendices to pin this down. citeturn50view0turn51view0turn52view0turn53view0.

Downloads API automation evidence:

While the OS Downloads API is listed as a government API, this phase did not surface strong, public, named examples of UK public bodies that explicitly automate OS OpenData acquisition via the Downloads API in production. This is an important gap because it is likely common but poorly documented; Phase 2 should focus on: local authority GIS resupply automation notes; shared services (for example ESRI UK resupply patterns); and open-source pipelines in official repositories that include OS downloads endpoints. citeturn57search1.

Devolved-administration breadth:

England-specific planning guidance is well evidenced, but there is less direct, named evidence captured here for devolved governments and agencies in Scotland, Wales, and Northern Ireland beyond UK-wide bodies and a small number of cross-GB workflows. Phase 2 should explicitly target devolved portals, GIS strategies, and procurement notices for: flood/land management; transport; health boards; and resilience. citeturn32view0turn31view0.

Operational policing POI use:

Procurement confirms POI subscription by the British Transport Police Authority, but the operational questions and integration points are not described in that notice. Phase 2 should seek additional corroboration such as internal strategy documents, GIS platform documentation, or FOI disclosures that explain how POI is used (threat assessments, patrol planning, vulnerability mapping, etc.). citeturn15view0.

GOV.UK map journeys:

Configuration evidence shows GOV.UK frontend provisioned with an OS Maps API key, but this phase did not confirm which specific GOV.UK services/pages use OS maps and what user-driven questions they answer. Phase 2 should trace application code paths and content types to map components, and identify which operational questions are being answered (for example “show area boundary”, “locate place”, “render context basemap”). citeturn14view0