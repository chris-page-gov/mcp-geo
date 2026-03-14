# Deep Analysis Report: Harold Wood, Essex Trace

Date: 2026-03-14  
Scope: Failure modes and misunderstandings in the Harold Wood validation run,
with explicit separation between historical server bugs, client/runtime
limitations, and upstream instability.

## Artifacts Reviewed

- Transcript working copy:
  `troubleshooting/MCP-Geo view of Harold Wood Essex.md`
- Historical transport trace:
  `logs/claude-trace.jsonl`
- Evidence extraction:
  `troubleshooting/harold-wood-essex-trace-evidence-2026-03-14.md`
- Relevant implementation:
  `tools/os_mcp.py`
  `tools/os_places_extra.py`
  `server/mcp/resource_handoff.py`
- Relevant regressions:
  `tests/test_os_mcp_route_query.py`
  `tests/test_os_map_tools.py`
- Post-change same-route validation:
  `logs/sessions/20260314T203104Z-harold-wood-wrapper-validation/`

## Issue Matrix

| Symptom | Transcript evidence | Trace evidence | Likely owner | Status tag | Current repo status | Mitigation |
| --- | --- | --- | --- | --- | --- | --- |
| `os_map.inventory` failed on the Harold Wood ward bbox because the OS Places `uprns` branch sent an invalid bbox ordering | `T10`-`T11` | `logs/claude-trace.jsonl:4981`, `:4985` | MCP-Geo server | `historical_server_bug` | Closed. Current `os_places.within` uses WGS84 `lat,lon,lat,lon`, and a Harold Wood regression now covers the ward bbox path. | Keep the new regression in place and treat any similar bbox-order bug as a shared-helper issue, not a one-off handler bug. |
| Claude received a valid `resource://` handoff for the full road network but tried to search the filesystem instead of using MCP resource retrieval | `T17`-`T20` | `logs/claude-trace.jsonl:4990`-`4991` | Client/runtime | `client/runtime limitation` | Open outside this repo. Current server already emits `resourceHandoff`, `resolverTool=os_resources.get`, `protocolMethod=resources/read`, and a direct text hint. | Keep the portable handoff contract. For hosts that do not auto-follow `resource://` URIs, route users toward `os_resources.get` / `resources/read` instead of local-path assumptions. |
| Natural-language questions about reading `resource://` URIs were not previously steered to the MCP resource bridge | Not directly in the historical transcript, but it is the missing recovery step after `T20` | Historical trace shows the need after `logs/claude-trace.jsonl:4991` | MCP-Geo server | `open_server_gap` | Closed in this change. `os_mcp.route_query` now recognizes resource-bridge prompts and recommends `os_resources.get` with `resources/read`. | Keep the narrow router branch and avoid broad search/ranking churn unless future traces show a new miss. |
| The Harold Wood natural-language prompt could previously be misparsed as `What` or `Geo` instead of `Harold Wood` | Implicit in `T01` because the prompt is conversational, not noun-only | Reproduced before the fix via same-route wrapper replay; not present in the historical Claude trace because Claude manually chose tools | MCP-Geo server | `open_server_gap` | Closed in this change. Stop-word hardening now ignores conversational openers and `MCP-Geo` tokens during place extraction. | Keep prompt-extraction regressions for conversational place requests. |
| Tool discovery in the old Claude run looked weak around administrative boundaries, vector tiles, and resource reading | `T06` only surfaced a limited subset during the original session | Historical trace captures the limited search sequence indirectly around `4975`-`4980`; current replay now differs | MCP-Geo server metadata/search surface | `historical_server_bug` | Already improved before this task. Current replay now returns `admin_lookup_containing_areas`, `os_vector_tiles_descriptor`, and `os_resources_get` as top hits for the traced phrases. | Do not retune ranking further unless a fresh trace regresses; document the old behavior as historical. |
| `buildings` timed out and `road_links` / `path_links` hit `CIRCUIT_OPEN` during the same inventory call | `T11`, `T12` | `logs/claude-trace.jsonl:4985`, `:4987` | Upstream OS service plus repo circuit-breaker policy | `upstream instability` | Still possible. The repo correctly normalizes these failures, but normalization does not eliminate upstream read timeouts or open circuits. | Keep normalized error envelopes and troubleshooting guidance. For analyses, separate upstream outage evidence from server formatting bugs. |

## Cause Allocation

The Harold Wood run surfaced faults in three different layers:

1. Historical MCP-Geo server behavior:
- The `uprns` inventory branch used an invalid bbox ordering for OS Places in
  this historical trace.
- The natural-language router did not previously help with resource-URI
  recovery prompts.
- Place-name extraction was too willing to keep conversational tokens.

2. Client/runtime behavior:
- Claude received a standards-compliant resource handoff and still treated the
  URI as a likely filesystem path.
- That misunderstanding is not fixed by changing the transport or the
  collection query itself.

3. Upstream OS instability:
- Read timeouts and `CIRCUIT_OPEN` results appeared in adjacent branches of the
  same inventory request.
- Those failures should be treated as external availability pressure, not as
  evidence that all Harold Wood failures came from one server bug.

## Mitigation and Optimization Plan

### 1. Keep the portable resource-handoff contract

Current server behavior is the right design:

- `delivery="resource"`
- `resourceUri`
- `resourceHandoff.resolverTool = os_resources.get`
- `resourceHandoff.protocolMethod = resources/read`
- explicit text hint for non-auto-resolving hosts

No transport expansion is needed. The mitigation is to keep this pattern stable
and make route guidance point to it sooner.

### 2. Route resource-URI questions to the bridge, not back to place search

This task closes the open server gap by teaching `os_mcp.route_query` that
questions like:

- `How do I read a resource:// URI from MCP-Geo?`
- `How do I open large resource output from MCP-Geo?`

should recommend:

- `os_resources.get`
- `resources/read`

with explicit guidance not to inspect the filesystem.

### 3. Prefer actual area geometry over bbox when area geometry is available

The user's `T23` challenge was correct. A bbox is acceptable for coarse
inventory and discovery, but it is not the tightest or most faithful analysis
window when the actual ward polygon is already available.

Mitigation:

- Use `admin_lookup.area_geometry` or geometry-bearing admin lookup results when
  the question is boundary-sensitive.
- Prefer `polygon` queries for `os_features.query` where the feature collection
  and request size allow it.
- Treat bbox-only routing as an approximation, not the ideal endpoint.

### 4. Do not re-fix already-remediated search ranking

Current replay already returns:

- `admin_lookup_containing_areas`
- `os_vector_tiles_descriptor`
- `os_resources_get`

as the leading hits for the traced discovery phrases. That means this task
should document those improvements as historical remediation, not reopen
ranking churn without fresh evidence.

### 5. Preserve the operational lesson from the Claude wrapper route

The Docker-backed Claude wrapper can serve stale code if the image is not
rebuilt. A same-route validation run is only trustworthy if the wrapper image
reflects the current checkout.

Mitigation:

- rebuild once with `MCP_GEO_DOCKER_BUILD=always` before concluding that a same
  wrapper replay still exhibits old behavior
- treat stale-image replays as invalid validation, not as product regressions

## Changes Implemented

### Code

- `tools/os_mcp.py`
  - added resource-URI detection via `RESOURCE_URI_REGEX`
  - added `_looks_like_resource_bridge_query()`
  - routes resource-bridge questions to `os_resources.get` with
    `resources/read` in the workflow
  - adds explicit guidance not to search the filesystem
  - hardens place-name extraction stop words so conversational Harold Wood
    prompts resolve to `Harold Wood`

### Tests

- `tests/test_os_mcp_route_query.py`
  - `test_route_query_harold_wood_prompt_ignores_question_openers`
  - `test_route_query_resource_uri_bridge_phrase`
- `tests/test_os_map_tools.py`
  - `test_os_map_inventory_preserves_harold_wood_places_bbox_axis_order`

### Documentation

- Added:
  - `troubleshooting/MCP-Geo view of Harold Wood Essex.md`
  - `troubleshooting/harold-wood-essex-trace-evidence-2026-03-14.md`
  - `troubleshooting/harold-wood-essex-deep-analysis-2026-03-14.md`
- Updated:
  - `docs/troubleshooting.md`
  - `PROGRESS.MD`
  - `CONTEXT.md`
  - `CHANGELOG.md`

## Verification

### Focused regressions

Command run:

```bash
./scripts/pytest-local -q --no-cov \
  tests/test_os_mcp_route_query.py \
  tests/test_os_map_tools.py \
  tests/test_os_places_extra_more_success.py \
  tests/test_resource_fallback.py
```

Result:
- `93 passed in 0.61s`

### Same-route Codex validation through the Claude wrapper

Preflight:

- `./scripts/check_shared_benchmark_cache.sh`
- Result:
  blocked because `mcp-geo_devcontainer-postgis-1` was not running

Initial traced wrapper sessions:

- `logs/sessions/20260314T202148Z/`
- `logs/sessions/20260314T202444Z/`

These runs were useful operationally but noisy:

- the first wrapper replay still reflected stale image behavior
- a rebuilt replay proved the Harold Wood route fix on stdout
- the original `trace_session.py` route was only partially captured under the
  interactive wrapper path

Clean manual-proxy wrapper validation:

- `logs/sessions/20260314T203104Z-harold-wood-wrapper-validation/`

What it proved:

1. `os_mcp.route_query` now routes
   `What can MCP-Geo tell me about Harold Wood, Essex?`
   to `admin_lookup.find_by_name` with
   `recommended_parameters.text == "Harold Wood"`.
2. `os_mcp.route_query` now routes
   `How do I read a resource:// URI from MCP-Geo?`
   to `os_resources.get` with workflow
   `["os_resources.get", "resources/read"]`.
3. A same-route `os_features.query` road-network request still returns
   `delivery="resource"` plus `resourceHandoff`.
4. Both `os_resources.get` and protocol `resources/read` succeeded when called
   against the returned `resource://` URI.

This is the key validation outcome: the remaining resource-handoff failure in
the original Claude conversation was client/runtime behavior, not a missing
server-side recovery path.

## Residual Risks

- Upstream OS timeouts and open-circuit states can still interrupt adjacent
  inventory branches even when bbox formatting is correct.
- Hosts may still ignore or mishandle `resource://` URIs even when the server
  advertises both `resourceHandoff` metadata and a bridge tool.
- Bbox-based feature analysis remains broader than polygon-based analysis unless
  callers explicitly move to geometry-constrained queries.
