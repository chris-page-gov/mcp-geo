# MCP-Geo View of Harold Wood Essex

Source: `troubleshooting/MCP-Geo view of Harold Wood Essex.docx`  
Prepared: 2026-03-14  
Scope: Markdown working copy of the Harold Wood validation segment used for the
trace analysis below. Unrelated later turns were omitted once the conversation
left the MCP-Geo failure chain.

## Turn 1: "What can MCP-Geo tell me about Harold Wood, Essex?"

### T01
- User prompt: `What can MCP-Geo tell me about Harold Wood, Essex`
- Timestamp in transcript: `19:42`

### T02
- Visible Claude reasoning:
  `The user is asking about Harold Wood, Essex using MCP-Geo tools. Let me use`
  `the available MCP-Geo tools to find information about this place. I should`
  `start with a place name search.`

### T03
- Tool-search request: `{"query": "find place names"}`
- Tool-search response summary:
  `os_names_find`, `os_landscape_find`, `os_places_by_postcode`,
  `os_places_search`, `os_landscape_get`

### T04
- Tool request: `os_names_find`
- Arguments: `{"text": "Harold Wood"}`
- Response highlights:
  - `Harold Wood` as `populatedPlace` / `Suburban Area`
  - `Harold Wood` as `transportNetwork` / `Railway Station`
  - `Harold Wood Primary School`
  - multiple nearby woodland and named-road matches

### T05
- Visible Claude reasoning:
  `I found Harold Wood as a "Suburban Area" (populated place) and also Harold`
  `Wood Railway Station. Let me now search for administrative boundary`
  `information and also try OS Places to get more detail.`

### T06
- Tool-search request:
  `{"query": "administrative boundary lookup containing areas"}`
- Tool-search response summary:
  `admin_lookup_find_by_name`, `os_places_by_postcode`, `os_landscape_get`

### T07
- Tool request: `admin_lookup_find_by_name`
- Arguments: `{"text": "Harold Wood", "limit": 20}`
- Response:
  `{"results":[{"id":"E05000312","level":"WARD","name":"Harold Wood"}],`
  `"count":1}`

### T08
- Tool request: `admin_lookup_find_by_name`
- Arguments:
  `{"text": "Harold Wood", "level": "WARD", "includeGeometry": true}`
- Response highlight:
  `Harold Wood` ward `E05000312` with bbox
  `[0.212767901572177, 51.5770138134869, 0.270927815822217, 51.6091919953636]`

### T09
- Tool request: `os_places_search`
- Arguments: `{"text": "Harold Wood, Havering", "limit": 10}`
- Response highlights:
  - Harold Wood Polyclinic
  - Harold Wood Methodist Church
  - Station Road shops
  - Harold Wood Primary School
  - Harold Court School
  - Harold Wood Sports Association

### T10
- Visible Claude reasoning:
  `Let me run a few queries in parallel: inventory of the Harold Wood ward`
  `bbox, and named areas within that bbox.`

### T11
- Tool request: `os_map_inventory`
- Arguments:
  `{"bbox":[0.212767901572177,51.5770138134869,0.270927815822217,`
  `51.6091919953636],"limits":{"uprns":10,"buildings":10,"road_links":10}}`
- Response highlights:
  - `uprns` returned `OS_API_ERROR`
  - message begins `BBox has SouthWest Coordinate Greater than NorthEast`
  - `buildings` returned `UPSTREAM_CONNECT_ERROR`
  - `road_links` and `path_links` returned `CIRCUIT_OPEN`

### T12
- Tool request: `os_features_query`
- Arguments:
  `{"collection":"gnm-fts-namedarea-1","bbox":[0.22,51.58,0.25,51.6],`
  `"limit":10}`
- Response:
  `{"isError":true,"code":"CIRCUIT_OPEN","message":"OS upstream circuit`
  `breaker is open."}`

### T13
- Visible Claude summary to user:
  - Harold Wood identified as a suburban area and station
  - ward `E05000312`
  - ward bbox quoted from the admin lookup response
  - address-level landmarks summarised from OS Places
  - future work suggested: `os_map_inventory`, `os_features_query`,
    NOMIS census queries, boundary explorer widget

## Turn 2: "Give me full details of the whole road network"

### T14
- User prompt: `Give me full details of the whole road network`
- Timestamp in transcript: `19:48`

### T15
- Visible Claude reasoning:
  `Let me pull the road network for the Harold Wood ward area. I'll start with`
  `a count, then page through the full dataset.`

### T16
- Tool request: `os_features_query`
- Arguments:
  `{"collection":"trn-ntwk-roadlink-5","bbox":[0.212767901572177,`
  `51.5770138134869,0.270927815822217,51.6091919953636],`
  `"resultType":"hits"}`
- Response highlights:
  - `count: 50`
  - `numberMatched: null`
  - warnings:
    `HITS_COUNT_LOWER_BOUND`, `HITS_NUMBER_MATCHED_UNAVAILABLE`
  - `delivery: "inline"`

### T17
- Tool request: `os_features_query`
- Arguments:
  `{"bbox":[0.212767901572177,51.5770138134869,0.270927815822217,`
  `51.6091919953636],"collection":"trn-ntwk-roadlink-5","limit":100,`
  `"thinMode":false,"includeGeometry":false}`
- Response highlights:
  - `count: 100`
  - `delivery: "resource"`
  - `resourceUri:`
    `resource://mcp-geo/os-exports/os-features-query-1773431292836-8b898abd.json`
  - `bytes: 325469`

### T18
- Visible Claude reasoning after the resource handoff:
  `The data was delivered as a resource file (325KB). Let me read it from the`
  `resource URI path. The resource path suggests it's at a local file. Let me`
  `check.`

### T19
- Bash command issued by Claude:
  `find /tmp -name "os-features-query-1773431292836*" 2>/dev/null;`
  `find /home -name "os-features-query-1773431292836*" 2>/dev/null;`
  `find /mnt -name "os-features-query*" 2>/dev/null | head -5`
- Transcript output: `exit code 0`

### T20
- Visible Claude recovery reasoning:
  `The resource file isn't on the filesystem directly. It's delivered via an`
  `MCP resource URI. Let me try fetching it through the tool system.`
  `Actually, looking at the delivery mode, it says "resource" ... I need to use`
  `the web_fetch tool or try to access it as an MCP resource.`

### T21
- Tool request: `os_features_query`
- Arguments:
  `{"bbox":[0.212767901572177,51.5770138134869,0.270927815822217,`
  `51.6091919953636],"collection":"trn-ntwk-roadlink-5","delivery":"inline",`
  `"includeGeometry":false,"inlineMaxBytes":500000,"limit":100,`
  `"thinMode":false}`
- Response highlights:
  - `delivery: "inline"`
  - `100` road-link features returned
  - transcript explicitly marks the payload as truncated:
    `...[content truncated by stdio adapter; omitted 293729 bytes. Use`
    `result.data for complete payload.]`

### T22
- Visible Claude reasoning after the inline truncation:
  - acknowledges the dataset is large
  - decides to keep paging manually
  - later moves into ad-hoc spreadsheet generation from partial data

## Immediate Follow-up from User

### T23
- User challenge:
  `Why the bbox rather than the actual border, which is available, possibly`
  `from ONS or OS but definately from the MCP-Geo.`

### T24
- Claude acknowledgement:
  `Good point on the bbox — you're right, the actual ward polygon is available`
  `and would give much tighter results.`
