# Third Harold Wood, after updates

Source: `troubleshooting/Third Harold Wood, after updates.docx`  
Prepared: 2026-03-15  
Scope: Markdown working copy of the third Harold Wood validation follow-up.
Repeated boilerplate and unrelated late-turn chatter were omitted once the
failure mode was clear.

## Turn 1: Updated Harold Wood overview

### T01
- Claude summary to user:
  - Harold Wood identified as ward `E05013973`
  - Census 2021 population quoted as `13,807`
  - ethnicity, built environment, and woodland context summarised
  - follow-up options suggested:
    housing, age structure, economic activity, water features, building
    counts, or a premises inventory

## Turn 2: "Premises inventory but make sure you use the Ward boundary not a bbox"

### T02
- User prompt:
  `Premises inventory but make sure you use the Ward boundary not a bbox`
- Timestamp in transcript: `22:12`

### T03
- Visible Claude reasoning:
  - the request needs the actual ward polygon, not bbox approximation
  - planned sequence:
    get the Harold Wood ward geometry, then run an inventory against that
    boundary

### T04
- Tool-search request:
  `{"query": "map inventory premises buildings"}`
- Tool-search response summary:
  `os_map_inventory`, `os_map_export`, `os_features_collections`,
  `os_peat_evidence_paths`

### T05
- Visible Claude reasoning:
  - `os_map_inventory` only accepts `bbox`
  - `os_features_query` accepts `polygon`
  - Claude decides it first needs the ward polygon geometry

### T06
- Tool request: `admin_lookup_find_by_name`
- Arguments:
  `{"text": "Harold Wood", "level": "WARD", "match": "exact",`
  `"includeGeometry": true}`

### T07
- Response:
  `{"results":[{"id":"E05013973","level":"WARD","name":"Harold Wood",`
  `"bbox":[0.212839833440574,51.5723721073295,0.287123868086035,`
  `51.6091919944458]}],"count":1,...}`
- Visible Claude takeaway:
  `includeGeometry=true` still returned only a bbox summary, not polygon
  coordinates

### T08
- Tool-search request:
  `{"query": "boundary polygon ward geometry GeoJSON"}`
- Tool-search response summary:
  `os_features_query`, `os_landscape_get`, `os_mcp_stats_routing`,
  `os_route_get`

### T09
- Tool request: `os_features_collections`
- Arguments: `{"q": "boundary"}`
- Response highlights:
  - `str-fts-fieldboundary-1`
  - `trn-ntwk-path-1`
  - `trn-ntwk-road-1`
  - `wtr-fts-tidalboundary-1`
- Visible Claude takeaway:
  no administrative ward polygon collection surfaced through NGD collections

### T10
- Tool request: `os_features_collections`
- Arguments: `{"q": "admin"}`
- Response:
  `{"count":0,"collections":[],"latestByBaseId":{},"live":true,...}`

### T11
- Visible Claude reasoning:
  - the boundary explorer widget had displayed the ward before
  - `admin_lookup.find_by_name` exposed only bbox
  - Claude considers whether `selectionSpec` on `os_map_export` can do
    ward-level selection without first extracting polygon coordinates

### T12
- Tool-search request:
  `{"query": "geography selector ward polygon selection UPRN"}`
- Tool-search response summary:
  `os_map_export`, `os_features_query`, `os_mcp_stats_routing`,
  `os_route_get`, `os_mcp_select_toolsets`

### T13
- Tool request: `os_map_export`
- Arguments:
  `{"exportType":"selection_uprn","selectionSpec":{"level":"WARD",`
  `"gss":"E05013973","name":"Harold Wood"},"layers":["uprns"],`
  `"format":"json","delivery":"inline"}`

### T14
- Response highlights:
  - `Large resource output is available via os_resources.get or resources/read`
  - `resource://mcp-geo/os-exports/jobs/0c50ff10-3393-410d-9c7b-`
    `ac4bffb3ee62.json`
- Visible Claude takeaway:
  the selection export worked, but the result arrived as a resource handoff

### T15
- Tool-search request:
  `{"query": "resources read get export job"}`
- Tool-search response summary:
  - returned `os_map_export`
  - did not surface `os_resources.get`
  - also mixed in unrelated Chrome-side tools

### T16
- Visible Claude reasoning:
  - the export job exists
  - the blocker is reading the `resource://` output back
  - Claude starts looking for alternate ways to force a smaller inline result

### T17
- Tool request: `os_map_export`
- Arguments:
  `{"delivery":"inline","exportType":"selection_uprn","format":"json",`
  `"layers":["uprns"],"limits":{"uprns":10},"selectionSpec":{"level":"WARD",`
  `"gss":"E05013973","name":"Harold Wood"}}`

### T18
- Response highlights:
  - still returned `Large resource output is available via os_resources.get`
    `or resources/read`
  - later repeated again for multi-layer and smaller-limit attempts
- Visible Claude takeaway:
  `delivery: "inline"` did not prevent resource-backed export delivery

### T19
- Tool request: `os_mcp_descriptor`
- Arguments: `{"category": "map", "includeTools": true}`
- Response highlights:
  - deferred tools listed included:
    `admin_lookup.area_geometry`, `os_linked_ids.get`,
    `os_linked_ids.feature_types`, `os_linked_ids.identifiers`,
    `os_resources.get`, `os_map.get_export`
  - response also carried:
    `Invalid category 'map'. Valid: ['core', 'places', 'names', 'features',`
    `'linked', 'maps', 'routing', 'vector', 'admin', 'statistics', 'codes',`
    `'apps', 'utility']`

### T20
- Tool-search request:
  `{"query": "linked identifiers get feature types"}`
- Tool-search response summary:
  - returned only already-loaded tools such as `os_map_inventory`,
    `os_features_wfs_capabilities`, and `os_map_export`
  - did not load `os_linked_ids.*`

### T21
- Tool request: `os_mcp_select_toolsets`
- Arguments: `{"includeToolsets": ["places_names"]}`
- Transcript result:
  `No result received from client-side tool execution.`

### T22
- Further tool-search requests:
  - `{"query": "os_linked_ids os_resources"}`
  - `{"query": "identifiers UPRN TOID building product version"}`
  - `{"query": "os_resources get export job read"}`
  - `{"query": "os_resources"}`
  - `{"query": "get export download retrieve stored"}`
- Visible Claude takeaway:
  tool search kept returning the same already-loaded tools instead of
  `os_resources.get` or `os_linked_ids.*`

### T23
- Final Claude summary to user:
  - `os_map_export` with ward `selectionSpec` succeeded multiple times
  - the correct architecture is still:
    ward/UPRN selection -> linked identifiers -> NGD features
  - the blocking problem was framed as deferred-tool loading and the inability
    to read the resource-backed export output
  - Claude asks whether this is a known tool-search indexing gap
