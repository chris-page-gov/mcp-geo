# Harold Wood Trace Evidence (2026-03-14)

- Source conversation:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md`
- Source transport trace:
  `logs/claude-trace.jsonl`
- Scope:
  Harold Wood, Essex validation run where Claude found the ward, hit a failed
  `os_map.inventory` call, received a large `resource://` handoff for the road
  network, and then failed to consume that handoff correctly.

## Conversation Evidence (Markdown Trace)

1. Claude correctly started with place lookup and found Harold Wood as a
   populated place plus railway station.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T02`-`T04`)

2. Claude then found the Harold Wood ward and requested geometry, which exposed
   a valid ward bbox for follow-on queries.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T05`-`T08`)

3. Claude also queried OS Places for address-level context inside Harold Wood.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T09`)

4. `os_map.inventory` failed inside the Harold Wood ward bbox and surfaced a
   specific OS Places bbox error:
- `uprns`:
  `OS_API_ERROR` with message beginning
  `BBox has SouthWest Coordinate Greater than NorthEast Coordinate`
- `buildings`:
  `UPSTREAM_CONNECT_ERROR`
- `road_links` and `path_links`:
  `CIRCUIT_OPEN`
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T10`-`T11`)

5. Claude then requested the Harold Wood road network. The first call asked for
   a `hits` count; the second call asked for the actual features.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T14`-`T17`)

6. The full road-network result was not returned inline. MCP-Geo returned a
   `resource://` URI and a resource-sized delivery contract instead.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T17`)

7. Claude then misinterpreted the `resource://` handoff as a likely local file
   path, searched `/tmp`, `/home`, and `/mnt`, and only afterwards reasoned
   that it probably needed an MCP resource read path.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T18`-`T20`)

8. Claude recovered by forcing the same large road-network request back to
   inline mode, and the transcript records that the stdio adapter truncated the
   payload.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T21`-`T22`)

9. The user then challenged Claude on using the ward bbox rather than the
   actual ward boundary polygon.
- Transcript evidence:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md` (`T23`-`T24`)

## Transport Evidence (JSONL)

### Request/response timeline

- `id=4` `os_names_find` for `Harold Wood` succeeded.
  Trace lines: `logs/claude-trace.jsonl:4973`-`4974`
- `id=5` `admin_lookup_find_by_name` for `Harold Wood` succeeded.
  Trace lines: `logs/claude-trace.jsonl:4975`-`4976`
- `id=6` `admin_lookup_find_by_name` with `includeGeometry=true` succeeded.
  Trace lines: `logs/claude-trace.jsonl:4977`-`4978`
- `id=7` `os_places_search` for `Harold Wood, Havering` succeeded.
  Trace lines: `logs/claude-trace.jsonl:4979`-`4980`
- `id=8` `os_map_inventory` used the Harold Wood ward bbox and returned a
  mixed-failure payload.
  Trace lines: `logs/claude-trace.jsonl:4981`, `:4985`
- `id=9` `os_features_query` for named areas failed with `CIRCUIT_OPEN`.
  Trace lines: `logs/claude-trace.jsonl:4986`-`4987`
- `id=10` `os_features_query` road-network `hits` request returned:
  `count=50`, `numberMatched=null`, `numberReturned=0`, `delivery=inline`.
  Trace lines: `logs/claude-trace.jsonl:4988`-`4989`
- `id=11` `os_features_query` road-network results request returned:
  `count=100`, `delivery=resource`,
  `resourceUri=resource://mcp-geo/os-exports/os-features-query-1773431292836-8b898abd.json`,
  `bytes=325469`.
  Trace lines: `logs/claude-trace.jsonl:4990`-`4991`
- `id=12` forced-inline road-network retry returned `delivery=inline`.
  Trace lines: `logs/claude-trace.jsonl:4992`-`4993`

### `os_map.inventory` failure details

The raw `id=8` payload in `logs/claude-trace.jsonl:4985` shows the historical
failure was not just a generic timeout:

- `uprns`:
  `OS_API_ERROR` with OS Places message beginning
  `BBox has SouthWest Coordinate Greater than NorthEast Coordinate`
- `buildings`:
  `UPSTREAM_CONNECT_ERROR` with a read timeout
- `road_links`:
  `CIRCUIT_OPEN`
- `path_links`:
  `CIRCUIT_OPEN`

That ties the `uprns` branch to a server-side bbox formatting problem, while
the other branches reflect upstream instability and circuit-breaker behavior.

## Current Server/Test Surface

1. Current `os_places.within` explicitly documents and enforces the OS Places
   WGS84 axis order `lat,lon,lat,lon`.
- Code evidence:
  `tools/os_places_extra.py:263`-`269`

2. Current resource-backed large outputs advertise a portable handoff contract
   with both resolver options:
- `resolverTool = os_resources.get`
- `protocolMethod = resources/read`
- user-facing hint:
  `Large resource output is available via os_resources.get or resources/read`
- Code evidence:
  `server/mcp/resource_handoff.py:85`-`145`

3. `os_mcp.route_query` now classifies resource-URI questions as a dedicated
   resource-bridge intent.
- Code evidence:
  `tools/os_mcp.py:652`-`669`

4. `os_mcp.route_query` now recommends `os_resources.get` plus
   `resources/read` for those prompts and explicitly tells callers not to
   search the filesystem.
- Code evidence:
  `tools/os_mcp.py:1225`-`1232`
  and `tools/os_mcp.py:1637`-`1646`

5. `os_mcp.route_query` now also ignores conversational/question opener words
   when extracting place names, so the Harold Wood prompt no longer collapses
   to `What` or `Geo`.
- Code evidence:
  `tools/os_mcp.py:228`-`293`

6. Focused regressions now lock both Harold Wood fixes in place:
- `tests/test_os_mcp_route_query.py:28`-`32`
  verifies the Harold Wood prompt routes with `text == "Harold Wood"`
- `tests/test_os_mcp_route_query.py:259`-`264`
  verifies resource-URI prompts route to `os_resources.get` with
  `resources/read` in the workflow
- `tests/test_os_map_tools.py:150`-`184`
  verifies Harold Wood ward bbox traffic through `os_map.inventory` preserves
  valid OS Places axis ordering

7. Current stdio tool-search replay already returns the historically relevant
   tools at the top of the ranking:
- query `administrative boundary lookup containing areas`
  -> `admin_lookup_containing_areas`
- query `vector tiles descriptor style URL key`
  -> `os_vector_tiles_descriptor`
- query `resource read resource uri large output`
  -> `os_resources_get`

## Evidence Appendix: Transcript to Trace Mapping

| Transcript moment | Transcript ids | Trace lines | Notes |
| --- | --- | --- | --- |
| Place lookup and ward discovery | `T04`, `T07`, `T08` | `4973`-`4978` | Claude found Harold Wood, then resolved the ward and bbox. |
| Address-level place search | `T09` | `4979`-`4980` | OS Places search succeeded before inventory failed. |
| Harold Wood ward inventory failure | `T10`, `T11` | `4981`, `4985` | `uprns` branch carried the invalid OS Places bbox error. |
| Named-area follow-up failure | `T12` | `4986`-`4987` | Independent `CIRCUIT_OPEN` evidence. |
| Road-network count and full export handoff | `T16`, `T17` | `4988`-`4991` | Full details moved to `delivery=resource`. |
| Claude recovery after resource handoff | `T18`-`T22` | `4992`-`4993` plus transcript-only reasoning | Trace shows forced inline retry; transcript shows the failed filesystem assumption. |
| User bbox challenge | `T23`, `T24` | transcript only | The trace slice does not carry Claude's visible prose, only tool traffic. |

## Evidence Summary

- The Harold Wood trace includes one historical server bug
  (`os_map.inventory` -> `os_places.within` bbox ordering for the `uprns`
  branch), one clear client/runtime limitation (Claude did not follow the
  `resource://` handoff), and one later-opened server router gap
  (`os_mcp.route_query` did not previously steer resource-URI questions toward
  `os_resources.get` / `resources/read`).
- Current repo behavior already shows the resource-handoff contract, the bbox
  regression, and the search-surface improvements needed to explain which parts
  of the original failure chain were historical and which were still open.
