# Analysis: Fourth Harold Wood Follow-up Trace

Date: 2026-03-15  
Scope: Exhaustive review of the fourth Harold Wood validation follow-up using
only the transcript working copy, `logs/claude-trace.jsonl`, and the current
server/test surface.

## Artifacts Reviewed

- Transcript working copy:
  `troubleshooting/Fourth Harold Wood, after updates.md`
- Source transcript:
  `troubleshooting/Fourth Harold Wood, after updates.docx`
- Historical transport trace:
  `logs/claude-trace.jsonl`
- Relevant implementation:
  `tools/os_places_extra.py`
  `tools/os_map.py`
  `tools/os_features.py`
  `tools/os_names.py`
  `tools/nomis_data.py`
- Relevant regressions:
  `tests/test_os_places_extra_more_success.py`
  `tests/test_os_map_tools.py`
  `tests/test_tool_search.py`
  `tests/test_tools_search.py`
  `tests/test_tools_describe.py`
  `tests/test_os_mcp_descriptor.py`

## Issue Matrix

| Symptom | Transcript evidence | Trace evidence | Likely owner | Status tag | Current repo status | Mitigation |
| --- | --- | --- | --- | --- | --- | --- |
| `os_map.inventory` still failed on the `uprns` layer for Harold Wood, but this time because the fallback OS Places bbox was just over the strict `< 1 km²` vendor limit | `T10`-`T11` | `logs/claude-trace.jsonl:5161`-`5164` | MCP-Geo shared Places helper | `open_server_gap` | Closed in this change. `os_places.within` now targets a safety margin below the published 1 km² ceiling, and new regressions prove the Harold Wood clamp stays strictly under the limit. | Keep the safety margin in the shared helper and treat any future OS Places size-limit bug as a shared-helper regression, not a one-off inventory bug. |
| `os_map.inventory` returned a mixed-success payload, but Claude's final prose summarized it as if the whole inventory had succeeded | `T11`, `T20` | `logs/claude-trace.jsonl:5164` | Mixed: client/model summarization plus upstream pressure | `client/runtime limitation` | Still open outside this repo. The server already preserved the `uprns` error and the building-layer warning flags in the structured response. | Hosts should treat mixed layer results as partial success, not as a fully successful inventory. The server-side response contract is already explicit enough to support that. |
| The `buildings` layer only succeeded after timeout degradation and bbox reduction | `T11` | `logs/claude-trace.jsonl:5164` | Upstream OS availability plus repo-side degrade policy | `upstream instability` | Open externally. The repo normalized the condition correctly, but it cannot prevent upstream latency pressure. | Keep the current normalized warning surface (`TIMEOUT_DEGRADE_APPLIED`, `TIMEOUT_BBOX_REDUCED`, `TIMEOUT_GEOMETRY_DISABLED`) and treat these as partial, sampled outputs. |
| Claude asked for an unsupported collection id, `gnm-fts-namedplace-1` | `T13` | `logs/claude-trace.jsonl:5165`-`5167` | Client/model tool selection | `client/runtime limitation` | Closed on the server side already. The error payload included `requestedCollection`, `suggestedCollections`, and a repair hint. | Use the returned `suggestedCollections` or call `os_features.collections` before retrying. This is not a missing-server-capability failure. |
| `gnm-fts-namedpoint-1` technically succeeded, but default thin projection stripped away the most useful human-readable fields | `T14` | `logs/claude-trace.jsonl:5168`-`5169` | MCP-Geo feature projection defaults | `open_server_gap` | Still open. The current generic thin-mode rule trims alphabetically, which is safe for payload size but not collection-aware enough for named-point exploration. | For named collections, callers should use `thinMode=false` or explicit `includeFields`. Longer term, collection-aware thin defaults would be safer for `gnm-*` exploration. |
| `os_places.search("Harold Wood")` returned useful local premises, but the tail of the result set drifted into unrelated Cardiff `Harold Street` matches | `T15` | `logs/claude-trace.jsonl:5170`-`5171` | Upstream OS Places free-text matching | `upstream instability` | Open externally. The repo passed through the free-text query as designed. | Prefer bbox-/polygon-scoped lookups or post-filtering when the user needs only in-area premises, not broad free-text address matches. |

## What This Run Proves

This fourth run is materially different from the first three Harold Wood traces.

1. It is not a repeat of the old bbox-axis-order bug.
The `uprns` failure is now a strict-size bug, not a coordinate-order bug. The
OS Places error text in `logs/claude-trace.jsonl:5164` is explicit: the
requested bbox must be less than 1 km².

2. It is not a repeat of the second-run MCP-Apps mount failure.
No widget or `ui://` handoff was involved. Every important action stayed in the
core data-tool path:
`os_names.find`, `admin_lookup.find_by_name`, `admin_lookup.area_geometry`,
`os_map.inventory`, `os_features.query`, `os_places.search`, and `nomis.query`.

3. It is not a repeat of the third-run deferred-tool discovery failure.
Claude found and used `admin_lookup.area_geometry` directly in `T07`-`T08`,
never stalled on loading `os_resources.get`, and never repeated the earlier
`os_mcp.select_toolsets` / exact-name recovery loop.

4. The admin and NOMIS fixes now hold in a realistic Claude flow.
Harold Wood resolved directly to current ward code `E05013973` in `T05`, full
geometry came back from `admin_lookup.area_geometry` in `T08`, and Census 2021
population data resolved cleanly through `nomis.query` in `T19`.

5. The remaining hard server-side failure in this run was narrow and
reproducible.
The `uprns` branch failed because the helper-generated fallback bbox was
slightly above the vendor's strict limit. Replaying the current helper against
the same bbox reproduced the exact failing sub-bbox from the trace and measured
it at `1000000.0000004031 m²`.

## Closed and Confirmed Improvements

### 1. Harold Wood now resolves at source to the current ward code

The run started with the right current ward code:

- transcript `T05`: `E05013973`
- trace `logs/claude-trace.jsonl:5154`-`5157`

That means the older stale-code Harold Wood NOMIS failure is no longer present
in the main discovery path. The earlier source refresh in `tools/admin_lookup.py`
is holding.

### 2. Full ward geometry is now practically discoverable

The fourth run also proves the geometry-discoverability fix is working in
practice, not just in theory:

- transcript `T07` shows the search phrase `administrative area geometry bbox`
  surfacing `admin_lookup.area_geometry`
- transcript `T08` shows Claude actually calling it and receiving the polygon
- trace `logs/claude-trace.jsonl:5158`-`5160` confirms the successful response

This closes the earlier operational gap where Harold Wood analysis got stuck on
`find_by_name(includeGeometry=true)` returning only bbox summaries.

### 3. NOMIS is now healthy in the Harold Wood path

`nomis.query` succeeded directly in `T19`, and the trace at
`logs/claude-trace.jsonl:5172`-`5173` confirms:

- `originalGeography = "E05013973"`
- `resolvedGeography = "641734965"`
- `resolution = "dataset_geography_code_search"`
- returned population `13807`

That is exactly the corrected path the earlier NOMIS fix was meant to enforce.

## Root-Cause Analysis

### 1. Shared-helper server bug: strict vendor limit not respected

The `uprns` layer failure is a real repo-side defect.

Current code in `tools/os_places_extra.py` used:

- `MAX_BBOX_AREA_M2 = 1_000_000.0`
- direct `<= 1_000_000` acceptance for single bboxes
- `sqrt(1_000_000)` as the target edge for tile sizing
- `sqrt(1_000_000 / area)` for clamp scaling

That is subtly wrong for OS Places because the vendor requires the bbox to be
strictly less than 1 km², not less than or equal to 1 km².

Replaying the fourth-run ward bbox against `_tile_or_clamp_bbox()` before this
fix produced:

- `bboxMode = "clamped"`
- `tileCount = 1`
- `originalTileCount = 30`
- clamped bbox
  `(0.24189359941841485, 51.586773162422915, 0.2580694005815851, 51.594790837577094)`
- measured area
  `1000000.0000004031 m²`

That clamped bbox exactly matches the vendor error embedded in the transcript
and trace. This is the clearest server-side defect in the fourth run.

### 2. Upstream pressure: building inventory degraded but remained usable

The building branch did not hard-fail, but it only succeeded after the server
reduced the workload under latency pressure:

- `TIMEOUT_DEGRADE_APPLIED`
- `TIMEOUT_BBOX_REDUCED`
- `TIMEOUT_GEOMETRY_DISABLED`
- `THIN_PROPERTIES_APPLIED`

That is upstream pressure plus repo-side resilience, not a clean success. The
server behaved reasonably here by returning a sampled, bounded result rather
than failing the entire inventory call.

### 3. Open server usability gap: thin-mode defaults are not collection-aware

The `gnm-fts-namedpoint-1` retry succeeded, but the output was not very useful
for human exploration because thin-mode kept fields such as bounding extents
and country language metadata while omitting obvious display-name fields.

The current implementation in `tools/os_features.py` trims to the first
alphabetically sorted keys when `thinMode` is on and the caller has not set
`includeFields`. That keeps payloads small, but it is not semantically safe for
all collections.

This is still an open repo-side gap. It did not break the server contract, but
it degraded the usefulness of the returned data.

### 4. Client/model interpretation gap: Claude overclaimed completeness

The final answer in `T20` read like a comprehensive ward summary, but the
underlying evidence was more mixed:

- the `uprns` layer failed
- the `buildings` layer was degraded and sampled
- the named-point retry was technically valid but not very readable
- the OS Places search result set drifted out of area at the tail

That overclaim sits outside the server, because the structured payloads still
carried the error and warning evidence.

## Secondary Observations

### 1. `os_names.find` still returned null coordinates

In `T04` and trace line `5153`, `os_names.find("Harold Wood")` returned useful
name/type classification but no coordinates. Based on the evidence reviewed for
this task, the exact cause is not yet provable:

- the reviewed trace only contains the normalized MCP response, not the raw OS
  Names upstream body
- the current tool code will surface `coordinates = null` if the upstream body
  omits `GEOMETRY`

So this run shows a real data-quality limitation, but not enough evidence to
assign it confidently to either upstream content or a repo-side parse bug.

### 2. There was a non-fatal upstream warning around `admin_lookup.area_geometry`

Trace line `5159` logged `server.logging:log_upstream_error:81 - Upstream error`
immediately before the successful `admin_lookup.area_geometry` response at
`5160`. Because the response still returned `partial = false` and full geometry,
this looks like a successfully normalized fallback or redundant-source failure,
not a user-visible defect in this run.

## Changes Implemented

### Code

- `tools/os_places_extra.py`
  - added `SAFE_BBOX_AREA_M2 = MAX_BBOX_AREA_M2 * 0.99`
  - changed single-bbox acceptance from `<= 1_000_000` to the safer sub-limit
  - changed tiling/clamp target sizing to use the same sub-limit

### Tests

- `tests/test_os_places_extra_more_success.py`
  - added
    `test_os_places_within_harold_wood_clamp_stays_below_strict_vendor_limit`
- `tests/test_os_map_tools.py`
  - added
    `test_os_map_inventory_keeps_harold_wood_places_clamp_below_strict_vendor_limit`

### Troubleshooting package and trackers

- Added:
  - `troubleshooting/Fourth Harold Wood, after updates.md`
  - `troubleshooting/fourth-harold-wood-after-updates-analysis-2026-03-15.md`
- Updated:
  - `docs/troubleshooting.md`
  - `PROGRESS.MD`
  - `CHANGELOG.md`
  - `CONTEXT.md`

## Verification

Command run:

```bash
./scripts/pytest-local -q --no-cov \
  tests/test_os_places_extra_more_success.py \
  tests/test_os_map_tools.py \
  tests/test_tool_search.py \
  tests/test_tools_search.py \
  tests/test_tools_describe.py \
  tests/test_os_mcp_descriptor.py
```

Verification goals:

- the new Places clamp stays strictly under `1_000_000 m²`
- the Harold Wood `os_map.inventory` UPRN path now succeeds through the shared
  helper instead of reproducing the vendor error
- the previously prepared third-run starter-tool and exact-name search
  regressions still pass in the same commit

## Bottom Line

The fourth Harold Wood follow-up shows a much healthier server than the first
three runs. Ward lookup, full geometry retrieval, and NOMIS all worked in a
normal Claude flow, and the third-run deferred-tool discovery problem did not
recur. The one clear remaining server-side defect was the OS Places strict
`< 1 km²` clamp bug in `os_places.within`, and that is closed in this change.

What remains open after this fix is mostly about analysis quality rather than
transport correctness:

- upstream latency can still force degraded building inventories
- `os_features.query` thin defaults are still not collection-aware enough for
  `gnm-*` exploration
- Claude can still overstate completeness when mixed-success layer payloads are
  summarized as if they were complete inventories
