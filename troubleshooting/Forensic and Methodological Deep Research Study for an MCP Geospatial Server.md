# Forensic and Methodological Deep Research Study for an MCP Geospatial Server

## Section A: Executive summary

- The relevant peatland-survey session (Europe/London time) executed **17 MCP tool calls** (IDs **15-31**) between **2026-02-18 14:34:37** and **14:55:42**, and received **16x HTTP 200** tool responses plus **1x HTTP 501** response caused by an upstream timeout to `api.os.uk`.
- The first "correct" discovery action, `os_names_find` for *Forest of Bowland*, **did return successfully**, but the user-visible client/UI reported **"No result received from client-side tool execution."** This created an early divergence between **MCP server reality** and **host/UI perception**.
- The workflow then attempted to locate the area using **address/POI search** (`os_places_search`, `os_poi_search`), yielding many irrelevant results because **OS Places is not intended to locate general areas such as "forest"** (the OS documentation explicitly warns this and recommends using OS Names for such needs) [1].
- The boundary strategy pivoted to an electoral ward named "Bowland" (ID **E05012002**) rather than the protected-landscape boundary for the Forest of Bowland AONB/National Landscape, which materially reduced precision and increased the risk of surveying the wrong area-of-interest [5][13].
- NGD querying escalated into **high-risk payload mode** (queryables/schema + geometry + high limits + broad bboxes), generating a very large response (e.g., **~555 kB** raw payload) and a very long-running call (**~317 s**) immediately before the visible stop; this pattern is known to be expensive under OS NGD Features paging/limits [3][6].
- The session ended with a user-visible failure: **"Claude's response could not be fully generated"**, and the transcript also shows **stdio adapter truncation** of a large tool payload.
- **Inference:** the most likely proximate cause of the observed "stop" is **host-side interruption** (latency + accumulated large tool outputs and/or truncation/limits in the host tool-output handling), rather than an MCP server crash, because the last "hard" call is recorded as successful in the trace and the floor report explicitly distinguishes host/UI failure from MCP server failure.
- The session reveals at least one **server-side contract/semantics bug**: in "no matches" responses, `numberReturned` appears to equal the **requested limit** despite `features=[]` (e.g., `numberReturned=100` with zero returned). This undermines tooling that relies on counts and is a key fix target.

## Section B: Timeline reconstruction

The sequence below is a mechanical reconstruction from the captured JSONL trace:
request timestamp (`ts`), parsed tool arguments, response status, latency
(response `ts` - request `ts`), and raw JSON-RPC payload sizes (bytes). Selected
cross-check points (IDs 15, 25, 30, 31) are also summarised in the floor report.

| id | start (UTC) | tool | status | latency (s) |
|---:|---|---|---:|---:|
| 15 | 2026-02-18 14:34:37 | os_names_find | 200 | 0.510 |
| 16 | 2026-02-18 14:35:11 | admin_lookup_find_by_name | 200 | 3.776 |
| 17 | 2026-02-18 14:45:16 | os_places_search | 200 | 0.643 |
| 18 | 2026-02-18 14:45:20 | os_poi_search | 200 | 0.440 |
| 19 | 2026-02-18 14:45:26 | admin_lookup_find_by_name | 200 | 6.372 |
| 20 | 2026-02-18 14:45:35 | admin_lookup_area_geometry | 200 | 2.240 |
| 21 | 2026-02-18 14:45:47 | os_features_collections | 200 | 0.640 |
| 22 | 2026-02-18 14:46:40 | os_features_query | 200 | 11.468 |
| 23 | 2026-02-18 14:47:12 | os_features_query | 200 | 1.305 |
| 24 | 2026-02-18 14:47:20 | os_features_query | 200 | 1.184 |
| 25 | 2026-02-18 14:47:40 | os_features_query | 501 | 15.624 |
| 26 | 2026-02-18 14:47:58 | os_features_query | 200 | 1.361 |
| 27 | 2026-02-18 14:48:16 | os_features_query | 200 | 1.363 |
| 28 | 2026-02-18 14:48:33 | os_features_query | 200 | 1.759 |
| 29 | 2026-02-18 14:49:12 | os_features_query | 200 | 13.989 |
| 30 | 2026-02-18 14:49:40 | os_features_query | 200 | 2.495 |
| 31 | 2026-02-18 14:50:24 | os_features_query | 200 | 317.381 |

Detailed row notes (args, payload size, and key observations):

1. `id=15`: req `145`, resp `12,003`; args `text='Forest of Bowland'`; notes `count=25`.
2. `id=16`: req `169`, resp `439`; args `text='Forest of Bowland'`; notes `count=0`.
3. `id=17`: req `151`, resp `14,311`; args `text='Forest of Bowland'`; notes `count=25`.
4. `id=18`: req `150`, resp `14,556`; args `text='Forest of Bowland AONB'`; notes `count=20`.
5. `id=19`: req `159`, resp `601`; args `text='Bowland'`; notes `count=1`.
6. `id=20`: req `184`, resp `46,919`; args `id=E05012002`, `includeGeometry=True`; notes `-`.
7. `id=21`: req `149`, resp `26,668`; args `q='land'`; notes `count=20`.
8. `id=22`: req `220`, resp `41,518`; args `collection=lnd-fts-land-3`, `bbox=[-2.80,53.90,-2.10,54.20]`, `includeQueryables=True`, `limit=1`; notes `count=1`, `nextPageToken=1`.
9. `id=23`: req `254`, resp `1,852`; args `collection=lnd-fts-land-3`, `bbox=[-2.85,53.85,-2.10,54.20]`, `filter.description='Peat'`, `includeGeometry=True`, `limit=100`; notes `count=0`, `numberReturned=100 != returned=0`.
10. `id=24`: req `259`, resp `1,970`; args `collection=lnd-fts-land-3`, `bbox=[-2.85,53.85,-2.10,54.20]`, `filter.description='Heath Or Rough Grassland'`, `resultType=hits`; notes `count=3`.
11. `id=25`: req `407`, resp `578`; args `collection=lnd-fts-land-3`, `bbox=[-2.85,53.85,-2.10,54.20]`, `cql='description IN (...)'`, `resultType=hits`; notes `UPSTREAM_CONNECT_ERROR (read timeout=5)`.
12. `id=26`: req `240`, resp `1,913`; args `collection=lnd-fts-land-3`, `bbox=[-2.85,53.85,-2.10,54.20]`, `filter.description='Heath'`, `resultType=hits`; notes `count=0`.
13. `id=27`: req `240`, resp `1,913`; args `collection=lnd-fts-land-3`, `bbox=[-2.85,53.85,-2.10,54.20]`, `filter.description='Marsh'`, `resultType=hits`; notes `count=0`.
14. `id=28`: req `311`, resp `66,813`; args `collection=lnd-fts-land-3`, `bbox=[-2.70,53.95,-2.40,54.10]`, `includeFields=5`, `limit=20`; notes `count=20`, `nextPageToken=20`.
15. `id=29`: req `399`, resp `2,296`; args `collection=lnd-fts-land-3`, `bbox=[-2.75,53.95,-2.35,54.12]`, `filter.description='Heath Or Rough Grassland And Marsh'`, `includeGeometry=True`, `includeFields=5`, `limit=50`; notes `count=0`, `numberReturned=50 != returned=0`.
16. `id=30`: req `446`, resp `555,546`; args `collection=lnd-fts-land-3`, `bbox=[-2.75,53.95,-2.35,54.12]`, `polygon=Y`, `includeGeometry=True`, `includeFields=4`, `limit=500`; notes `count=100`.
17. `id=31`: req `273`, resp `271,223`; args `collection=wtr-fts-water-3`, `bbox=[-2.85,53.88,-2.10,54.20]`, `includeGeometry=True`, `includeFields=2`, `limit=50`; notes `count=50`, `nextPageToken=50`.

## Section C: Evidence-backed failure analysis

### Confirmed turning points

The user's "peatland site survey" prompt appears in the transcript as the initiating question for this session.

The workflow exhibits four clear turning points:

**Discovery (but user-visible failure):** `os_names_find` was issued for "Forest of Bowland", and the trace shows a normal successful response. However the transcript records a UI-level error ("No result received..."), after which the workflow immediately pivoted to other methods.

**Boundary failure:** `admin_lookup_find_by_name` for "Forest of Bowland" returned an empty set (`count=0`). This is consistent with "admin lookup" being limited to administrative geographies rather than designated/protected landscapes.

**Degradation:** the workflow moved into expansive NGD queries (queryables/schema and geometry, higher limits, larger bboxes) and produced very large responses (e.g., ~555 kB raw JSON-RPC payload in one call).

**Stop (user-visible):** after requesting water features with geometry, the transcript shows "response could not be fully generated", and also shows truncation by the stdio adapter (large payload omitted).

### Failure modes

1. **Using address/POI tools to locate a landscape**
Evidence: address/POI searches returned many address matches unrelated to the landscape name.
Impact: wasted calls and incorrect geographic anchors.
Likely cause: not an API failure; this is a tool-semantic mismatch. OS Places does not target general areas such as forests [1].
Practical mitigation: route named-landscape queries to names/gazetteer or named-area features first, and enforce tool guidance in server hints/prompts.

2. **Missing protected-landscape boundary layer**
Evidence: admin lookup for "Forest of Bowland" produced no results, and the workflow fell back to a ward named "Bowland".
Impact: incorrect AOI polygon and high risk of surveying the wrong area.
Likely cause (inference): no designated landscape boundary source (AONB/National Landscape) in the active flow, so "best available" became an electoral ward.
Practical mitigation: add AONB boundary support via Natural England/Planning Data and/or provide NGD named-area lookup [12][13].

3. **Semantically weak peat detection strategy**
Evidence: filter on `description='Peat'` in a land-cover collection returned zero.
Impact: false negatives and potentially misleading "no peat" conclusions.
Likely cause: the dataset attribute does not directly encode peat presence; peat is a soil/condition class and land cover is proxy-only.
Practical mitigation: prefer peat-specific datasets (England Peat Map) and/or structured habitat datasets (Priority Habitat Inventory) for peat relevance [2][7][8][9][10][11].

4. **Server contract bug: counts/returned mismatch**
Evidence: responses with `features=[]` showed `numberReturned` equal to requested limit (for example 100 or 50).
Impact: broken pagination logic, broken QA checks, and misleading returned metrics.
Likely cause (inference): `numberReturned` appears to be set to `limit` instead of `len(features)` on empty result sets.
Practical mitigation: set `numberReturned` to actual returned feature count and add automated empty-result/pagination tests.

5. **Upstream timeout surfaced as 501**
Evidence: one call returned `status=501` with `UPSTREAM_CONNECT_ERROR` and message `read timeout=5`.
Impact: break in analytical flow and forced fallback.
Likely cause: network instability and/or timeout policy too short for the query profile.
Practical mitigation: retries with backoff, configurable timeouts, and thin-mode defaults (no geometry, low limit, reduced bbox).

6. **Payload/latency pressure leading to end-user stop**
Evidence: large response sizes and long latency immediately before transcript stop, while trace indicates response still returned.
Impact: perceived agent failure despite successful tool call.
Likely cause (inference): host-side generation/tool-output handling limits (context bloat, timeouts, truncation).
Practical mitigation: resource-based delivery for large result sets, size guardrails, progressive paging, and summary-first responses.

### Why the session likely stopped despite a successful final tool response

- The floor report explicitly states that the final "hard" call returned **200** after **~317 seconds**, and that the stop was **not** a server-side MCP error.
- The transcript shows **tool-output truncation** ("content truncated by stdio adapter; omitted 229125 bytes") immediately before the final request, and then ends with "response could not be fully generated".
- The OS NGD API - Features endpoint is explicitly limited to **max 100** items per request and uses offset/limit paging; large-geometry payloads and repeated paging are expected to be expensive [3][6].

**Inference (explicit):** given (a) the long-running final call, (b) large structured outputs, and (c) transcript truncation plus the "could not be fully generated" marker, the most parsimonious explanation is **host-side interruption** (runtime/tool-output handling constraints) rather than server failure, consistent with the floor report's diagnosis.

## Section D: Proposed end-to-end survey workflow

This section proposes a **robust, low-risk** workflow for answering: "Do a peatland site survey on the forrest of Bowland" using the currently observed *mcp-geo* tool families (names search, admin lookup, NGD features querying, maps), while explicitly handling uncertainty.

### Design principles for a "demo-safe" peatland workflow

1. **AOI before analytics**: do not query NGD collections until the area-of-interest is pinned down to a defensible polygon (or a clearly stated approximation).
2. **Progressive disclosure**: start with **counts** and **small attribution-only samples**, then fetch geometry only for the minimal subset needed. This aligns with OGC guidance on pagination and with OS NGD paging constraints [3][4][6].
3. **Hard caps**: clamp `limit` to **<=100** for OS NGD API - Features requests, because max=100 [3][6].
4. **Page results deliberately**: if `nextPageToken` is present, either page to completion (when feasible) or explicitly state "partial sample".
5. **Separate "peat evidence" sources from "proxies"**: land cover and hydrology are proxies; for peat extent/depth/condition you want peat-specific datasets (see "engineering recommendations" for adding them) [2].

### Stepwise call strategy using current tool families

**Step 1: Define the AOI (three-tier fallback)**

- **Preferred (if available in-tool): NGD Named Area polygon**
  Use NGD "named area" features (e.g., a named-area collection) to retrieve a polygon for "Forest of Bowland" (requires queryables inspection once to find the correct name property). This avoids overloading OS Places with non-address queries [1][3][6][15].
  - First, discover the "named area" collection using `os_features_collections` with a query term like "named area" or "gnm".
  - Then, call `os_features_query` with `includeQueryables=true` once (tiny bbox, limit=1) to learn the name field to filter on.
  - Then, query the named-area collection with a name filter to retrieve the polygon, with `includeGeometry=true` and `limit=1`.

- **Fallback: Protected landscape boundary (AONB/National Landscape)**
  If/when a designated-landscape layer exists in the server (recommended in Section F), use the AONB boundary for Forest of Bowland rather than an electoral ward. The planning dataset provides a stable reference for Forest Of Bowland [5][12][13].

- **Last-resort (explicit approximation): point + buffered bbox/polygon**
  Use a known representative point for the area (e.g., the Planning Data point geometry) and create a bbox/polygon buffer explicitly labelled as an approximation [5].

**Outputs required to proceed:** AOI polygon + citation to its source + explicit statement of whether it is authoritative or an approximation.

**Step 2: Build a "thin" hydrology context (water presence and density)**

- Query relevant water collections with `resultType='hits'` first, *no geometry*, `limit=1`, to get *counts only*.
- Then sample small pages of water features with minimal fields (`includeFields` limited to identifiers and type/description) and `includeGeometry=false` unless you need geometry.
- Only once candidate zones are identified, fetch geometry for a subset (or fetch geometry page-by-page with strict limits).

This aligns with OS NGD API - Features paging and max-limit constraints [3][6].

**Stop condition for this step ("hydrology context complete"):**
- You have counts for water bodies/links/points in the AOI, and at least one representative sample page for each key water collection, with paging either completed or explicitly bounded.

**Step 3: Build land-cover / habitat proxies for peat likelihood**

- Use land polygons (`lnd-fts-land-*`) with **CQL-capable filters** (server-side where possible) rather than local post-filtering; OS NGD supports CQL filtering (`filter` + `filter-lang`) [3][6].
- Queryables: inspect once, then cache; do not repeat per call.
- Start with `resultType='hits'` per class (e.g., marsh, heath, rough grassland variants), then fetch only small samples of features (limit 10-25) for mapping.

**Stop condition ("land proxy layer complete"):**
- Counts by land-cover/habitat proxy class + sampled polygons/centroids sufficient to delineate candidate zones for fieldwork.

**Step 4: Candidate zone synthesis (desk-based)**

Construct candidate peatland zones using **rules**, not single attributes:

- **High-likelihood**: wetness indicators (dense small water features, frequent water links/nodes, ponding) + "marsh/fen/swamp" style proxies + topographic settings (if terrain available).
- **Moderate-likelihood**: upland heath/rough grassland + headwater density + known peatland management indicators (if added later).
- **Low-likelihood**: urban/residential garden, intensive arable, built-up.

**Stop condition ("desk-based survey complete"):**
- AOI + candidate zones (polygons/bboxes) + the evidence layers used to derive them + explicit confidence ratings.

**Step 5: Fieldwork plan (ground-truthing)**

Produce a targeted plan: transects, access points, sampling density, and safety constraints.

### Which outputs justify "survey complete" vs "not complete"

**Suitable to claim "desk-based peatland survey complete":**
- AOI boundary is authoritative or clearly described approximation (with source).
- Hydrology and land/habitat proxy layers extracted with paging control (or documented sampling).
- Candidate zones identified, mapped, and prioritised with explicit confidence.
- A fieldwork plan is produced that targets uncertainties.

**Not suitable to claim "peatland survey complete" (in the strong/field sense):**
- Any conclusion asserting peat **extent**, **depth**, or **condition** as fact without peat-specific datasets and/or field verification. England's peat map products exist precisely because peat extent/depth/condition require dedicated modelling and validation [2][7][8][9][10][11].

## Section E: "Model answer" blueprint

### Target answer blueprint for: "Do a peatland site survey on the forrest of Bowland"

A target response should be structured to distinguish: **(a) authoritative boundaries; (b) peat evidence; (c) proxies; (d) uncertainty**.

**Area definition**
- Name the AOI and the authority for its geometry (AONB boundary, named-area polygon, or explicit approximation).
- Provide the centroid/representative point, bbox, and polygon provenance (licence/copyright terms if relevant).
- Provide the operational AOI used for queries (possibly an AOI buffer for hydrology catchments).

**Peat indicators**
- Primary evidence (where available): peat extent probability, peat depth, peat condition, erosion/drainage features (grips, gullies, haggs, bare peat), vegetation on peaty soil. England Peat Map explicitly models these layers [2][7][8][9][10][11].
- Secondary evidence: Priority Habitat Inventory classes relevant to peat such as blanket bog, lowland raised bog, fens, upland flushes/fens/swamps (as corroboration or targeting).
- Proxies: land-cover categories (heath/rough grassland, marsh), topographic wetness, headwater density, mapped water bodies.

**Hydrology context**
- Summarise surface water abundance and pattern (water bodies, water links/nodes, springs/ponds).
- Identify likely wet basins and headwater zones; note drainage risks.

**Candidate zones**
- Provide a small set of prioritised zones (e.g., 3-8) with bounding geometry references.
- For each: what evidence supports peat likelihood, what is uncertain, and what field checks address it.

**Fieldwork recommendations**
- Access and safety: route planning, permissions, biosecurity.
- Survey design: transects and stratified sampling; peat depth probing/coring where permitted; water table indicators; vegetation indicators (e.g., Sphagnum presence as peat-forming indicator-only as an indicator, not a guarantee).
- Data capture: GNSS points/photos, standardised condition scoring, timestamping, and repeatability.

**Caveats/confidence**
- Make confidence explicit per zone.
- State what is desk-based vs field-verified.

### Example answer skeleton with plausible placeholders

**Area of interest (AOI)**
- AOI: Forest Of Bowland (protected landscape boundary). Source: Planning Data "area-of-outstanding-natural-beauty:13". Representative point: `POINT (-2.520193 53.978219)` [5][13].
- Operational AOI used for desk-based queries: `<AOI_POLYGON_FROM_AONB_DATASET_OR_SERVER>` plus optional buffer `<BUFFER_DISTANCE_KM>` to capture hydrological connectivity.

**Peat evidence layers (desk-based)**
- Primary peat layers (to be ingested/queried if available):
  - Peaty soil extent probability: `<EPM_EXTENT_LAYER>` [2][8]
  - Peaty soil depth: `<EPM_DEPTH_LAYER>` [2][7]
  - Upland erosion and drainage features (e.g., bare peat / haggs): `<EPM_BAREPEAT_LAYER>`, `<EPM_HAGGS_LAYER>` [2][9][10]
  - Vegetation and land cover on peaty soil: `<EPM_VEGETATION_LAYER>` [2][11]

**Hydrology context (from NGD water features)**
- Water bodies (polygons): `<COUNT_WATER_BODIES>`; sample includes `<EXAMPLE_FEATURE_IDS>`.
- Water network (links/nodes): `<COUNT_WATER_LINKS>`, `<COUNT_WATER_NODES>`.
- Key hydrological observations: `<HEADWATER_DENSITY_SUMMARY>`, `<PONDING_OR_WET_BASINS>`.

**Candidate peatland survey zones (prioritised)**
- Zone A (high-likelihood): `<ZONE_A_POLYGON/BBOX>`
  - Evidence: high peaty-soil probability + shallow basin hydrology + peat erosion/drainage features present.
  - Confidence: `<HIGH/MEDIUM/LOW>`
- Zone B (medium-likelihood): `<ZONE_B_POLYGON/BBOX>`
  - Evidence: upland habitat proxies + headwater density; peat layers uncertain.
  - Confidence: `<MEDIUM>`
- Zone C (targeted uncertainty reduction): `<ZONE_C_POLYGON/BBOX>`
  - Evidence conflicting or sparse; fieldwork designed to resolve.

**Fieldwork recommendations**
- Permissions/constraints: `<LANDOWNERSHIP_CONTACTS_OR_ACCESS_NOTES>`
- Sampling:
  - Stratified transects across zones A-C, targeting transitions from wet hollows to drier ridges.
  - At each waypoint: depth probe/coring where permitted, water table indicators, vegetation indicators, photo log, GNSS coordinate.
- Deliverables from fieldwork: ground-truth points, peat depth samples, condition observations, and revised zone boundaries.

**Caveats**
- Desk-based layers indicate probability and proxies; final statements about peat depth/condition require field verification and/or authoritative peat map layers integrated and cited [2][7][8][9][10][11].

## Section F: Prioritised implementation roadmap

This is a server-side roadmap framed for an engineering post-mortem. Items are prioritised by **impact** and **implementation effort**.

### Highest-impact, lower-effort changes

**Fix count/return semantics (contract correctness)**
- Problem: `numberReturned` can equal the requested `limit` when `features=[]`, which is contract-breaking for pagination and QA.
- Change: set `numberReturned = len(features)` always; ensure `count` is either `len(features)` (returned count) or clearly documented as such; if "total matched" is known, provide it as `numberMatched` (or `totalMatched`) consistent with OGC guidance [4].
- Tests: empty results; partial-page results; paging completion.

**Clamp and validate paging parameters**
- Enforce `limit <= 100` for OS NGD API - Features. The official technical specification sets max=100 [3][6].
- If a user requests higher, clamp and add a warning in a small `hints/warnings` field (do not silently accept).

**Default to thin mode for large-area queries**
- Default `includeGeometry=false` unless explicitly requested.
- Default `includeFields` minimal; require explicit opt-in for rich attributive payloads.

**Improve upstream timeout and retry handling**
- Evidence: upstream timeout surfaced as a 501 with `read timeout=5`.
- Change: configurable upstream timeouts (separate connect/read), automatic retry with backoff for idempotent GET requests, and a "degrade plan": halve bbox, reduce limit, and disable geometry on retry.

### Medium-effort, high-impact changes

**Large-payload delivery mode (resource-backed, not inline)**
- Evidence: stdio adapter truncation and "could not be fully generated" after large outputs.
- Change: when payload exceeds a threshold (e.g., 200 kB), store the full feature collection as a server resource (file/blob) and return:
  - a lightweight summary (counts, bbox, first N IDs), and
  - a `resource://...` handle for retrieval/paging/export.
- This aligns with progressive disclosure and avoids host context bloat (also consistent with general OGC pagination patterns) [4].

**Polygon validation and normalisation**
- Validate GeoJSON polygon inputs: closure, coordinate ranges, self-intersections (as feasible), orientation normalisation.
- Accept polygons as structured objects (not only JSON strings) and normalise internally.
- Reject polygons exceeding complexity limits unless "export mode" is used.

**Better filter semantics: distinguish server-side CQL vs local filtering**
- OS NGD supports CQL via `filter`/`filter-lang` [3][6].
- Change:
  - Represent CQL explicitly in tool schemas.
  - Indicate whether filtering occurred upstream or locally (e.g., `filterApplied: upstream|local`).
  - If local filtering requires scanning multiple pages, expose the scan budget and report "partial scan" explicitly.

### Higher-effort strategic changes

**Protected-landscape boundary support (AONB and beyond)**
- Add first-class boundary tools for: AONB/National Landscapes, National Parks, SSSI, SAC, SPA, etc.
- Candidate authoritative sources:
  - Natural England "Areas of Outstanding Natural Beauty (England)" dataset (WMS/WFS/OGC API Features and downloadable GeoJSON/GPKG) [12].
  - Planning Data "area-of-outstanding-natural-beauty" dataset (entity pages with downloadable GeoJSON) [5][13].
  - Defra Data Services Platform direction towards OGC API Features as an authoritative publishing approach [14].
- Result: the server can resolve "Forest of Bowland" to an authoritative protected-landscape polygon quickly, avoiding the "ward fallback".

**Environmental survey "routing" improvements**
- Implement a server-side "survey router" that maps intents (peatland survey, flood risk scoping, habitat assessment) to:
  - recommended boundary sources,
  - recommended NGD collections, and
  - safe default parameters (thin mode + counts first).
- Use OS guidance that the Features API is for interrogating small areas and uses paging; embed these constraints in routing to avoid GB-scale pulls [3][6][15].

**Add peat-specific layers as MCP-accessible sources**
- Peatland surveys are best anchored on peat-specific evidence layers. England Peat Map provides extent, depth, condition and erosion/drainage features [2][7][8][9][10][11].
- Implement as:
  - an OGC API Features/WMS/WCS adapter (where published), or
  - a pre-indexed vector/raster package accessible as MCP resources (AOI clip + summary statistics).

### Implementation checklist mapped to the requested categories

- **Filtering/count semantics**: fix `numberReturned`; clarify `count` vs `numberMatched`; expose `filterApplied` and scan budgets [4].
- **Polygon validation**: strict GeoJSON parsing; complexity caps; closure and CRS checks; explicit errors.
- **Large-payload delivery mode**: thresholds -> resource handle; summary-only inline; paging-first.
- **Protected-landscape boundary support**: integrate AONB/National Landscape boundaries from Natural England / Planning Data; add discovery by name + geometry fetch [5][12][13].
- **Routing improvements for environmental surveys**: intent->tool routing, safe defaults, and explicit "survey completeness" gates tied to evidence layers; align with OS NGD API constraints [3][6][15].

## Section G: Sources and citations (restored)

The list below restores the external citations that were referenced by the
original deep-research output.

1. OS Places API: <https://docs.os.uk/os-apis/accessing-os-apis/os-places-api>
2. England Peat Map (data.gov.uk):
   <https://www.data.gov.uk/dataset/5a2047b0-b1a4-4f5e-b0aa-1dae85c4c2eb/england-peat-map>
3. OS NGD API Features technical specification:
   <https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-features/technical-specification/features>
4. OGC Web API Guidelines:
   <https://github.com/opengeospatial/OGC-Web-API-Guidelines>
5. Planning Data entity (Forest of Bowland AONB):
   <https://www.planning.data.gov.uk/curie/area-of-outstanding-natural-beauty%3A13>
6. OS NGD API Features technical specification (overview):
   <https://docs.os.uk/osngd/getting-started/access-the-os-ngd-api/os-ngd-api-features/technical-specification>
7. Environment Data Services dataset:
   <https://environment.data.gov.uk/dataset/92b43165-0dd0-4e69-a712-1e49bb5aa0d0>
8. Environment Data Services dataset:
   <https://environment.data.gov.uk/dataset/ab92bc06-bd99-47c4-89a3-b93aa9c0db4d>
9. Environment Data Services dataset:
   <https://environment.data.gov.uk/dataset/fc9e34eb-6119-47fb-a1ab-9508e82eef22>
10. Environment Data Services dataset:
    <https://environment.data.gov.uk/dataset/0212a29b-9e17-48c1-8eac-c27d48919f13>
11. Environment Data Services dataset:
    <https://environment.data.gov.uk/dataset/8e7c6f34-cc47-462e-b2c8-a152811a8f83>
12. Areas of Outstanding Natural Beauty (England) (data.gov.uk):
    <https://www.data.gov.uk/dataset/8e3ae3b9-a827-47f1-b025-f08527a4e84e/areas-of-outstanding-natural-beauty-england1>
13. Planning Data AONB dataset:
    <https://www.planning.data.gov.uk/dataset/area-of-outstanding-natural-beauty>
14. Environment Data Services announcement:
    <https://environment.data.gov.uk/support/announcements/275811286/275811339>
15. OS MasterMap demonstrator, using the OS Features API:
    <https://docs.os.uk/more-than-maps/demonstrators/os-mastermap-generation-apis/using-the-os-features-api>
