# Fourth Harold Wood, after updates

Source: `troubleshooting/Fourth Harold Wood, after updates.docx`  
Prepared: 2026-03-15  
Scope: Markdown working copy of the fourth Harold Wood validation follow-up.
This copy keeps the visible Claude reasoning, tool searches, tool calls, and
the final answer because the fourth run mixed genuine server results with a
partially misleading end summary.

## Turn 1: "What can MCP-Geo tell me about Harold Wood, Essex"

### T01
- User prompt:
  `Test4: What can MCP-Geo tell me about Harold Wood, Essex`
- Timestamp in transcript: `07:59`

### T02
- Visible Claude reasoning:
  - start by searching for tools relevant to Harold Wood
  - search for the place first, then pull in relevant geographic data

### T03
- Tool-search request:
  `{"query": "find place names"}`
- Tool-search response summary:
  - `os_names.find`
  - `os_places.by_postcode`
  - `os_places.search`
  - `os_landscape.find`
  - `admin_lookup.find_by_name`

### T04
- Tool request: `os_names.find`
- Arguments:
  `{"text": "Harold Wood", "limit": 10}`
- Response highlights:
  - `Harold Wood` as `populatedPlace` / `Suburban Area`
  - `Harold Wood` as `transportNetwork` / `Railway Station`
  - `Harold Wood Primary School`
  - `Harold Court Woods`
  - `Harold's Wood`
  - every returned item had `coordinates: null`, `lat: null`, `lon: null`
- Visible Claude takeaway:
  `Harold Wood` is visible as both a populated place and a railway station

### T05
- Tool request: `admin_lookup.find_by_name`
- Arguments:
  `{"text": "Harold Wood", "limit": 20}`
- Response:
  `{"results":[{"id":"E05013973","level":"WARD","name":"Harold Wood"}],`
  `"count":1,"live":true,...}`
- Visible Claude takeaway:
  Harold Wood ward is now resolved to the current ward code `E05013973`

### T06
- Tool request: `admin_lookup.find_by_name`
- Arguments:
  `{"text":"Harold Wood","levels":["LSOA","MSOA","WARD","LAD","PCON"],`
  `"limit":20,"includeGeometry":true}`
- Response:
  `{"results":[{"id":"E05013973","level":"WARD","name":"Harold Wood",`
  `"bbox":[0.212839833440574,51.5723721073295,0.287123868086035,`
  `51.6091919944458]}],...}`
- Visible Claude takeaway:
  only the ward matched, with bbox summary included

### T07
- Tool-search request:
  `{"query": "administrative area geometry bbox"}`
- Tool-search response summary:
  - `admin_lookup.area_geometry`
  - `admin_lookup.find_by_name`
  - `os_features.query`
  - `os_map.inventory`
  - `os_landscape.get`
- Visible Claude reasoning:
  get full ward geometry and then inspect what sits inside the ward

### T08
- Tool request: `admin_lookup.area_geometry`
- Arguments:
  `{"id": "E05013973", "includeGeometry": true}`
- Response highlights:
  - bbox repeated for `E05013973`
  - `meta.level = "WARD"`
  - `meta.source = "arcgis"`
  - `meta.partial = false`
  - full polygon geometry returned as `geometry.rings`
- Visible Claude takeaway:
  full ward boundary geometry is now available, not just bbox

### T09
- Visible Claude reasoning:
  with the ward geometry in hand, get an inventory for the Harold Wood ward

### T10
- Tool request: `os_map.inventory`
- Arguments:
  `{"bbox":[0.212839,51.572372,0.287124,51.609192],`
  `"layers":["uprns","buildings","road_links"],`
  `"limits":{"uprns":20,"buildings":20,"road_links":20}}`

### T11
- `os_map.inventory` response highlights:
  - `uprns` branch failed:
    `{"isError":true,"code":"OS_API_ERROR","message":"OS API error: ...`
    `"Requested bbox must be less than 1km2. Requested BBox was`
    `51.586773162422915,0.24189359941841485,51.594790837577094,`
    `0.2580694005815851."}`
  - `buildings` branch succeeded:
    - collection `bld-fts-buildingpart-2`
    - `count = 20`
    - warning flags:
      `TIMEOUT_DEGRADE_APPLIED`,
      `TIMEOUT_BBOX_REDUCED`,
      `TIMEOUT_GEOMETRY_DISABLED`,
      `THIN_PROPERTIES_APPLIED`
    - sample properties mostly show residential dwellings plus one commercial /
      medical premises
  - `road_links` branch succeeded:
    - collection `trn-ntwk-roadlink-5`
    - `count = 20`
    - warning flag:
      `THIN_PROPERTIES_APPLIED`
    - sample properties include `description` and `directionality`
- Visible Claude takeaway:
  the inventory is treated as broadly successful, despite the failed `uprns`
  layer

### T12
- Visible Claude reasoning:
  search for named features and ONS data next

### T13
- Tool request: `os_features.query`
- Arguments:
  `{"collection":"gnm-fts-namedplace-1","bbox":[0.22,51.58,0.27,51.6],`
  `"limit":20,"includeGeometry":false}`
- Error payload:
  - `code = "OS_API_ERROR"`
  - `requestedCollection = "gnm-fts-namedplace-1"`
  - `suggestedCollections` included:
    `gnm-fts-crowdsourcednamepoint-1`,
    `gnm-fts-namedarea-1`,
    `gnm-fts-namedpoint-1`,
    `gnm-fts-namedroadjunction-1`
  - `hint` explicitly said to call `os_features.collections`
- Visible Claude takeaway:
  the collection id was wrong and needs a valid substitute

### T14
- Tool request: `os_features.query`
- Arguments:
  `{"bbox":[0.22,51.58,0.27,51.6],"collection":"gnm-fts-namedpoint-1",`
  `"includeGeometry":false,"limit":20}`
- Response highlights:
  - `count = 10`
  - warning flag:
    `THIN_PROPERTIES_APPLIED`
  - projected properties only included fields such as:
    `boundedbymaxx`, `boundedbymaxy`, `boundedbyminx`, `boundedbyminy`,
    `changetype`, `country_name1_language`, `country_name1_text`,
    `country_name2_language`
- Visible Claude takeaway:
  the named-point query technically worked, but the thin properties were not
  useful for human-readable names

### T15
- Tool request: `os_places.search`
- Arguments:
  `{"text": "Harold Wood", "limit": 10}`
- Response highlights:
  - locally relevant Harold Wood matches:
    - Harold Wood Polyclinic
    - Harold Wood Methodist Church
    - Harold Wood Primary School
    - Harold Court School
    - The Harold pub
  - noisy out-of-area matches also surfaced:
    - `1, HAROLD STREET, CAERDYDD, CF24 1NZ`
    - `2, HAROLD STREET, CAERDYDD, CF24 1PA`
    - `3, HAROLD STREET, CAERDYDD, CF24 1NZ`
    - `4, HAROLD STREET, CAERDYDD, CF24 1PA`
    - `5, HAROLD STREET, CAERDYDD, CF24 1NZ`
- Visible Claude takeaway:
  OS Places search gives useful named premises, but the tail of the result set
  is noisy

### T16
- Visible Claude reasoning:
  check ONS / NOMIS data for ward-level statistics

### T17
- Tool-search request:
  `{"query": "ONS statistics search census"}`
- Tool-search response summary:
  - `ons_search.query`
  - `ons_data.query`
  - `ons_select.search`
  - `os_mcp.stats_routing`
  - `os_places.search`

### T18
- Tool-search request:
  `{"query": "NOMIS census population ward data"}`
- Tool-search response summary:
  - `os_mcp.stats_routing`
  - `nomis.query`
  - `ons_data.query`

### T19
- Tool request: `nomis.query`
- Arguments:
  `{"dataset":"NM_2021_1","params":{"geography":"E05013973","measures":"20100"}}`
- Response highlights:
  - dataset label:
    `TS001 - Number of usual residents in households and communal establishments`
  - `queryAdjusted.geographyResolvedFromGss = true`
  - `queryAdjusted.resolvedGeography = 641734965`
  - `queryAdjusted.mapping[0].currentGss = "E05013973"`
  - returned values:
    - total usual residents: `13807`
    - lives in a household: `13704`
    - lives in a communal establishment: `103`
- Visible Claude takeaway:
  the NOMIS path now works directly for Harold Wood ward

### T20
- Final Claude summary to user:
  - Harold Wood described as a suburban area in Havering
  - ward code `E05013973` quoted with bbox range
  - full ward geometry described as available and ready for MapLibre
  - OS Names summary repeated
  - OS Places premises and NGD buildings / roads samples summarized
  - Census 2021 population quoted as `13,807`
  - follow-up suggestions:
    age structure, ethnicity, tenure, economic activity, qualifications,
    fuller inventories, and more detailed feature queries
- Important omission in the final summary:
  the `uprns` branch of `os_map.inventory` had actually failed with a strict
  OS Places bbox-size error, but that partial failure was not carried through
  clearly into the final answer
