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
| `os_map.export` with ward `selectionSpec` succeeded, but Claude treated the run as blocked because the result stayed resource-backed | `T13`-`T18`, `T23` | `logs/claude-trace.jsonl:5136`-`5139` | Mixed: MCP-Geo startup profile plus client/runtime | `open_server_gap` | Closed in this follow-up. The trace already showed valid `resourceHandoff`, but `os_resources.get` was still deferred, so a host that failed to activate deferred tools could not follow the recovery path reliably. `os_resources.get` is now always loaded. | Keep the explicit `resourceHandoff` contract and force-load the resource bridge so `resource://` recovery does not depend on deferred-tool activation. |
| The reviewed trace slice contains no follow-on read for the export job URIs after the server returned them | `T15`-`T18`, `T22` | `logs/claude-trace.jsonl:5137`, `:5139` and no later matching URI read in the same slice | Client/runtime | `client/runtime limitation` | Open outside this repo. The missing step is resource consumption, not export generation. | Keep resource handoff metadata stable and push hosts toward protocol-native `resources/read` first. |
| `os_mcp.descriptor` exposed the right deferred tools but still returned an avoidable category error for singular `map` | `T19` | `logs/claude-trace.jsonl:5134`-`5135` | MCP-Geo server | `open_server_gap` | Closed in this change. `map` now aliases to `maps`, matching the existing `stats -> statistics` tolerance. | Keep singular/plural alias handling narrow and test-backed. |
| `os_mcp.select_toolsets` failed before producing a server result | `T21` | Transcript-only; the failure is reported as `No result received from client-side tool execution.` and there is no matching successful server result in the reviewed trace slice | Client/runtime | `client/runtime limitation` | Open outside this repo. The failure boundary sits in host-side tool execution or elicitation handling, not in the selection result payload. | When the host cannot complete `select_toolsets`, fall back to already-loaded direct tool calls instead of depending on a follow-on expansion step. |
| Claude could name `os_linked_ids.get` and `os_resources.get`, but those tools were still deferred in the descriptor, so exact-name recovery still depended on host-side deferred-tool activation | `T19`-`T23` | `logs/claude-trace.jsonl:5135` advertises both tools only under `deferred`; current repo-side `/tools/search` replay returns them for exact-name queries, which means the remaining practical gap sat in the deferred-loading path rather than raw indexing | MCP-Geo startup profile plus client/runtime | `open_server_gap` | Closed in this follow-up. `admin_lookup.area_geometry`, `os_linked_ids.get`, and `os_resources.get` are now always loaded starter tools, so Claude-like hosts do not need deferred-tool activation for the Harold Wood recovery path. | Treat these recovery tools as baseline tools, not deferred tools. Keep exact-name `/tools/search` regressions to prove the server still surfaces them. |

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
`os_mcp.select_toolsets`. In the reviewed repo state at the time of the run,
that recovery still depended on deferred tools being activated successfully.

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

### 2. Mixed server/host gap around resource-backed exports

The server-side export contract was explicit:

- `resourceUri`
- `resource_link`
- `resourceHandoff.resolverTool = os_resources.get`
- `resourceHandoff.protocolMethod = resources/read`

The trace slice reviewed here shows the handoff being returned at
`logs/claude-trace.jsonl:5137` and again at `:5139`, but no later matching read
for those export URIs. That means the blocking step was not export creation.

However, the repo also made that recovery harder than necessary: the handoff
named `os_resources.get`, but that tool was still classified as deferred. In a
host that did not reliably activate deferred tools from search or descriptor
metadata, the server-side "next step" existed but was not operational enough.

### 3. Repo-side startup profile gap around deferred-tool activation

The transcript criticism about tool search was not entirely wrong.

Current repo-side `/tools/search` replay does return the exact tools:

- query `os_linked_ids.get` -> top result `os_linked_ids_get`
- query `os_resources.get` -> top result `os_resources_get`

But the third Harold Wood trace still mattered because the descriptor exposed
those tools only as deferred. For Claude-like hosts, exact-name search was not
sufficient if the runtime then failed to materialize the deferred tool.

This change therefore treats the gap as partly repo-side and partly host-side:

- repo-side: the critical recovery tools were not force-loaded
- host-side: deferred-tool activation still failed even after the tools were
  named explicitly
The transcript also shows `os_mcp.select_toolsets` failing with
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
  - promoted `admin_lookup.area_geometry`, `os_linked_ids.get`, and
    `os_resources.get` into the always-loaded starter toolset
- `tools/admin_lookup.py`
  - clarified `admin_lookup.find_by_name` as discovery plus bbox summary
  - clarified `admin_lookup.area_geometry` as bbox plus optional full geometry

### Tests

- `tests/test_tool_search.py`
  - added `test_get_tool_search_config_map_alias`
  - added `test_starter_toolset_includes_harold_wood_recovery_tools`
- `tests/test_tools_search.py`
  - added exact-name search regressions for `os_linked_ids.get` and
    `os_resources.get`
  - added transcript-phrase search regressions for linked-id and resource
    recovery queries
- `tests/test_tools_describe.py`
  - added a starter-toolset regression proving startup `tools/list` now
    includes the Harold Wood recovery tools
- `tests/test_os_mcp_descriptor.py`
  - added `test_os_mcp_descriptor_accepts_map_category_alias`
  - added `test_os_mcp_descriptor_force_loads_harold_wood_recovery_tools`

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
  tests/test_tools_search.py \
  tests/test_tools_describe.py \
  tests/test_os_mcp_descriptor.py
```

Result:

- `43 passed in 0.16s`
- singular `map` now behaves like `maps`
- `os_linked_ids.get` and `os_resources.get` are always loaded in the
  descriptor/startup toolset
- exact-name `/tools/search` returns the expected sanitized tool entries with
  their dotted `annotations.originalName`

## Practical Guidance for Future Harold Wood-Like Runs

1. For a named administrative area, use:
- `admin_lookup.find_by_name` to discover the id
- `admin_lookup.area_geometry` to retrieve actual geometry

2. For selector-driven exports, assume async/resource-backed delivery is normal.
- If the result includes `resourceUri`, read that exact URI next.
- `os_resources.get` is now always loaded specifically so this step does not
  depend on deferred-tool activation.

3. Prefer protocol-native resource reading over more tool discovery.
- `resources/read` is enough if the host supports it.
- `os_resources.get` is the portable tool fallback.

4. Treat `os_mcp.select_toolsets` errors carefully.
- A client-side execution error there does not prove the server lacks the
  relevant tools.
- For Harold Wood-like flows, `os_linked_ids.get`, `os_resources.get`, and
  `admin_lookup.area_geometry` should now already be present without a
  toolset-expansion step.

## Bottom Line

The third Harold Wood follow-up was not just a host/runtime problem. The export
generation path worked, but the server still left the key recovery tools behind
deferred loading even after Claude named them explicitly. The repo-side fixes
therefore needed to do three things: clarify which admin lookup tool yields
full geometry, remove the `map`/`maps` descriptor mismatch, and force-load the
recovery tools (`admin_lookup.area_geometry`, `os_linked_ids.get`,
`os_resources.get`) so Claude-like hosts no longer depend on fragile deferred
activation for this workflow.
