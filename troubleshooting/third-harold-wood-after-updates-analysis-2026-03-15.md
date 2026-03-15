# Analysis: Third Harold Wood Follow-up Trace

Date: 2026-03-15  
Scope: The third Harold Wood validation follow-up where Claude was asked to
produce a premises inventory using the ward boundary rather than a bbox. This
analysis is limited to the transcript working copy, `logs/claude-trace.jsonl`,
and the current server/test surface.

## Artifacts Reviewed

- Transcript working copy:
  `troubleshooting/Third Harold Wood, after updates.md`
- Source transcript:
  `troubleshooting/Third Harold Wood, after updates.docx`
- Historical trace:
  `logs/claude-trace.jsonl`
- Relevant implementation:
  `server/mcp/tool_search.py`
  `tools/admin_lookup.py`
  `server/mcp/resource_handoff.py`
- Relevant tests:
  `tests/test_tool_search.py`
  `tests/test_os_mcp_descriptor.py`

## Issue Matrix

| Symptom | Transcript evidence | Trace evidence | Likely owner | Status tag | Current repo status | Mitigation |
| --- | --- | --- | --- | --- | --- | --- |
| Claude requested ward geometry through `admin_lookup.find_by_name(includeGeometry=true)` and still only saw a bbox summary, not full polygon coordinates | `T03`-`T11` | `logs/claude-trace.jsonl:5110`-`5111` | MCP-Geo tool surface | `open_server_gap` | Open as a discoverability/documentation gap, not a broken query. `admin_lookup.area_geometry` already exists for full geometry. This change makes that distinction explicit in tool metadata. | After `find_by_name`, call `admin_lookup.area_geometry` when the workflow requires the actual boundary polygon. Treat `find_by_name` as discovery plus bbox summary. |
| `os_map.export` with ward `selectionSpec` succeeded, but Claude treated the run as blocked because the result stayed resource-backed | `T13`-`T18`, `T23` | `logs/claude-trace.jsonl:5136`-`5139` | Client/runtime | `client/runtime limitation` | Open outside this repo. The server already returns `resourceHandoff`, `resolverTool=os_resources.get`, `protocolMethod=resources/read`, and `resource_link` blocks. | Hosts should read the returned `resource://` URI directly with `resources/read` or `os_resources.get` instead of treating `delivery="inline"` as a guarantee for async export jobs. |
| The reviewed trace slice contains no follow-on read for the export job URIs after the server returned them | `T15`-`T18`, `T22` | `logs/claude-trace.jsonl:5137`, `:5139` and no later matching URI read in the same slice | Client/runtime | `client/runtime limitation` | Open outside this repo. The missing step is resource consumption, not export generation. | Keep resource handoff metadata stable and push hosts toward protocol-native `resources/read` first. |
| `os_mcp.descriptor` exposed the right deferred tools but still returned an avoidable category error for singular `map` | `T19` | `logs/claude-trace.jsonl:5134`-`5135` | MCP-Geo server | `open_server_gap` | Closed in this change. `map` now aliases to `maps`, matching the existing `stats -> statistics` tolerance. | Keep singular/plural alias handling narrow and test-backed. |
| `os_mcp.select_toolsets` failed before producing a server result | `T21` | Transcript-only; the failure is reported as `No result received from client-side tool execution.` and there is no matching successful server result in the reviewed trace slice | Client/runtime | `client/runtime limitation` | Open outside this repo. The failure boundary sits in host-side tool execution or elicitation handling, not in the selection result payload. | When the host cannot complete `select_toolsets`, fall back to `os_mcp.descriptor`, direct tool calls, or protocol `resources/read` instead of assuming the server lacks a route. |
| Claude framed the blockage as tool-search indexing even though the descriptor already advertised `admin_lookup.area_geometry`, `os_resources.get`, and `os_linked_ids.get` | `T19`-`T23` | `logs/claude-trace.jsonl:5135` | Mixed, but primarily client/runtime interpretation | `client/runtime limitation` | Partly mitigated in this change by clarifying admin-geometry tool descriptions and the `map` alias. The larger host-side deferred-tool loading issue remains external. | Distinguish descriptor visibility from host tool-loading success. If a tool is already listed in the descriptor, the next question is host/tool bridge behavior, not search indexing alone. |

## What This Run Proves

This third run is not the same failure mode as the earlier Harold Wood traces.

1. It is not the historical bbox-order bug.
The ward code was current (`E05013973`), and the server accepted ward-based
selection exports.

2. It is not the second-run MCP-Apps mount failure.
The main loop here happens after data selection and export handoff, not during
widget bootstrap.

3. The export path itself worked.
`os_map.export` queued selection-based jobs and returned explicit
resource-retrieval instructions.

4. The visible stall happened at resource consumption and deferred-tool access.
Claude did not move from the returned export URIs to `resources/read` or
`os_resources.get`, and the transcript records a client-side failure on
`os_mcp.select_toolsets`.

## Cause Allocation

### 1. Repo-side discoverability gap

The server already had the right geometry tool:

- `admin_lookup.find_by_name` for discovery
- `admin_lookup.area_geometry` for boundary geometry

But the third run shows that this distinction was not obvious enough from the
tool surface alone. Calling `find_by_name(includeGeometry=true)` and receiving
only a bbox summary was enough to send Claude into a long detour.

This change therefore clarifies the tool descriptions:

- `admin_lookup.find_by_name` now says it returns ids and bbox summaries
- `admin_lookup.area_geometry` now says it returns bbox plus optional full
  boundary geometry

### 2. Host/runtime limitation around resource-backed exports

The server-side export contract was explicit:

- `resourceUri`
- `resource_link`
- `resourceHandoff.resolverTool = os_resources.get`
- `resourceHandoff.protocolMethod = resources/read`

The trace slice reviewed here shows the handoff being returned at
`logs/claude-trace.jsonl:5137` and again at `:5139`, but no later matching read
for those export URIs. That means the blocking step was not export creation.

### 3. Host/runtime limitation around deferred-tool activation

The transcript shows `os_mcp.select_toolsets` failing with
`No result received from client-side tool execution.` That is not a normal
server-side payload from this repo. It points to a host or bridge execution
failure before a usable selection result was delivered back into the chat.

### 4. Small repo-side category alias friction

Claude asked the descriptor for `category="map"` and received the right
descriptor data plus an avoidable category error. That did not create the whole
failure chain, but it added friction in the middle of an already confused
recovery path.

This change closes that gap by accepting `map` as an alias for `maps`.

## Changes Implemented

### Code and metadata

- `server/mcp/tool_search.py`
  - added `map -> maps` category alias
- `tools/admin_lookup.py`
  - clarified `admin_lookup.find_by_name` as discovery plus bbox summary
  - clarified `admin_lookup.area_geometry` as bbox plus optional full geometry

### Tests

- `tests/test_tool_search.py`
  - added `test_get_tool_search_config_map_alias`
- `tests/test_os_mcp_descriptor.py`
  - added `test_os_mcp_descriptor_accepts_map_category_alias`

### Documentation

- Added:
  - `troubleshooting/Third Harold Wood, after updates.md`
  - `troubleshooting/third-harold-wood-after-updates-analysis-2026-03-15.md`
- Updated:
  - `docs/troubleshooting.md`
  - `PROGRESS.MD`
  - `CHANGELOG.md`
  - `CONTEXT.md`

## Verification

Command run:

```bash
./scripts/pytest-local -q --no-cov \
  tests/test_tool_search.py \
  tests/test_os_mcp_descriptor.py
```

Result:

- `15 passed in 0.06s`
- singular `map` now behaves like `maps`
- descriptor responses no longer carry an error for `category="map"`

## Practical Guidance for Future Harold Wood-Like Runs

1. For a named administrative area, use:
- `admin_lookup.find_by_name` to discover the id
- `admin_lookup.area_geometry` to retrieve actual geometry

2. For selector-driven exports, assume async/resource-backed delivery is normal.
- If the result includes `resourceUri`, read that exact URI next.

3. Prefer protocol-native resource reading over more tool discovery.
- `resources/read` is enough if the host supports it.
- `os_resources.get` is the portable tool fallback.

4. Treat `os_mcp.select_toolsets` errors carefully.
- A client-side execution error there does not prove the server lacks the
  relevant tools.

## Bottom Line

The third Harold Wood follow-up was mainly a host/runtime recovery failure, not
an export-generation failure. The server already had the right ward-selection
path and already returned the correct resource-handoff contract. The repo-side
improvements worth making were narrower: clarify which admin lookup tool yields
full geometry, and remove the unnecessary `map`/`maps` category mismatch that
showed up in the descriptor call.
