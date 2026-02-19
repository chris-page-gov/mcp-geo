# Deep Analysis: "Do a peatland site survey on the forrest of Bowland"

Date: 2026-02-19
Analyst: Codex

## 1) Scope and Evidence

This report reconstructs and analyzes the floor question event centered on:
- `troubleshooting/claude-stopped-after-ngd-features.md`
- `logs/claude-trace.jsonl`
- `troubleshooting/claude-floor-questions-harness-report-2026-02-18.md`

Question under review (transcript line 41):
- `Do a peatland site survey on the forrest of Bowland`

Constraint introduced by user (transcript line 84):
- `Don't use the web, use mcp-geo`

## 2) Executive Findings

1. Claude did not stop because mcp-geo crashed.
- The trace shows valid `tools/call` request/response pairs through `id=31`, including final `status=200`.

2. One real upstream failure occurred mid-workflow.
- `id=25` returned `501` with `UPSTREAM_CONNECT_ERROR` after an NGD CQL call over a broad bbox.

3. The workflow then produced large payloads and a long-latency call.
- `id=30`: response frame size `555,546` bytes.
- `id=31`: response frame size `271,223` bytes, latency `317.381s`.

4. The "stop" was most likely host/runtime pressure after heavy tool output.
- Transcript contains adapter truncation marker and then `Claude's response could not be fully generated`.

5. The current tool behavior can produce misleading survey conclusions.
- Local post-filtering is applied only to the fetched page, not the full result set.
- A string-valued `polygon` can be silently ignored when `bbox` is present.
- Some returned counters (`numberReturned`) can reflect upstream page size, not filtered output.

## 3) Forensic Timeline (14:34-14:55 UTC)

Trace run segment: `logs/claude-trace.jsonl` lines `3025-3060`.

| id | Tool | Request line | Response line | Latency (s) | Status | Response bytes | Notes |
|---:|---|---:|---:|---:|---:|---:|---|
| 15 | `os_names_find` | 3025 | 3026 | 0.510 | 200 | 12,003 | Name search for "Forest of Bowland" |
| 16 | `admin_lookup_find_by_name` | 3027 | 3028 | 3.776 | 200 | 439 | No match for exact phrase |
| 17 | `os_places_search` | 3029 | 3030 | 0.643 | 200 | 14,311 | Address-like matches |
| 18 | `os_poi_search` | 3031 | 3032 | 0.440 | 200 | 14,556 | Address/POI-like matches |
| 19 | `admin_lookup_find_by_name` | 3033 | 3034 | 6.372 | 200 | 601 | Found ward "Bowland" |
| 20 | `admin_lookup_area_geometry` | 3035 | 3037 | 2.240 | 200 | 46,919 | Ward geometry payload |
| 21 | `os_features_collections` | 3038 | 3039 | 0.640 | 200 | 26,668 | Collection discovery |
| 22 | `os_features_query` | 3040 | 3041 | 11.468 | 200 | 41,518 | Queryables fetch on `lnd-fts-land-3` |
| 23 | `os_features_query` | 3042 | 3043 | 1.305 | 200 | 1,852 | `filter.description=Peat`, zero filtered |
| 24 | `os_features_query` | 3044 | 3045 | 1.184 | 200 | 1,970 | `resultType=hits`, `Heath Or Rough Grassland` -> `count=3` |
| 25 | `os_features_query` | 3046 | 3047 | 15.624 | 501 | 578 | CQL broad filter timed out upstream |
| 26 | `os_features_query` | 3049 | 3050 | 1.361 | 200 | 1,913 | `Heath` hits -> 0 |
| 27 | `os_features_query` | 3051 | 3052 | 1.363 | 200 | 1,913 | `Marsh` hits -> 0 |
| 28 | `os_features_query` | 3053 | 3054 | 1.759 | 200 | 66,813 | 20 land features, `nextPageToken=20` |
| 29 | `os_features_query` | 3055 | 3056 | 13.989 | 200 | 2,296 | Filtered query returned zero filtered |
| 30 | `os_features_query` | 3057 | 3058 | 2.495 | 200 | 555,546 | Large land payload with geometry |
| 31 | `os_features_query` | 3059 | 3060 | 317.381 | 200 | 271,223 | Long-running water payload, `nextPageToken=50` |

Session payload footprint for ids `15-31`:
- Request bytes: `4,156`
- Response bytes: `1,061,119`
- Total: `1,065,275`

## 4) Concrete Log Examples

### A) CQL timeout event (real upstream failure)

From call `id=25`:

```json
{
  "collection": "lnd-fts-land-3",
  "bbox": [-2.85, 53.85, -2.1, 54.2],
  "cql": "description IN ('Heath','Marsh','Heath Or Rough Grassland And Marsh','Heath Or Rough Grassland','Boulders Or Rock And Heath Or Rough Grassland And Marsh','Marsh And Heath Or Rough Grassland')",
  "resultType": "hits"
}
```

Response payload:

```json
{
  "isError": true,
  "code": "UPSTREAM_CONNECT_ERROR",
  "message": "HTTPSConnectionPool(host='api.os.uk', port=443): Read timed out. (read timeout=5)"
}
```

### B) Adapter truncation marker before final stop

Transcript markers:
- Line 450: `...[content truncated by stdio adapter; omitted 229125 bytes. Use result.data for complete payload.]`
- Line 490: `Claude's response could not be fully generated`

### C) High-latency final call completed successfully

`id=31` request:

```json
{
  "collection": "wtr-fts-water-3",
  "bbox": [-2.85, 53.88, -2.1, 54.2],
  "includeFields": ["description", "geometry_area_m2"],
  "includeGeometry": true,
  "limit": 50
}
```

`id=31` response summary:

```json
{
  "status": 200,
  "count": 50,
  "numberReturned": 50,
  "nextPageToken": "50",
  "latency_s": 317.381
}
```

## 5) What Claude Did Well

- Switched to mcp-only when asked.
- Used `os_features_collections` and `includeQueryables=true` to discover available land-cover dimensions.
- Identified peat-relevant enum values in `lnd-fts-land-3` queryables (including `Peat`, `Heath`, `Marsh`, `Rough Grassland`).
- Added water context with `wtr-fts-water-3`.

## 6) What Failed (and Why)

### 6.1 Area resolution quality was weak

Observed behavior:
- Place/address and POI tools returned many irrelevant address matches for "Forest"/"Bowland".
- Admin lookup found a ward (`E05012002`) rather than the Forest of Bowland AONB boundary.

Why this happened:
- `admin_lookup` is scoped to OA/LSOA/MSOA/WARD/DISTRICT/COUNTY/REGION/NATION (`tools/admin_lookup.py:44-109`), not protected landscape boundaries (AONB).
- `os_poi` currently uses `DPA,LPI` datasets (`tools/os_poi.py:10-11`), so it is address-centric, not a nature-designation index.

### 6.2 Filtering semantics can undercount or mislead

Key implementation behavior in `os_features.query`:
- `cql/filterText` is pushed upstream as `params["filter"]` (`tools/os_features.py:321-352`).
- `filter` object is local post-filtering over the fetched page (`tools/os_features.py:370-378`).

Risk:
- For broad areas, `filter` can produce false negatives or undercounts because it only inspects returned page features, not the full result universe.

Counter inconsistency:
- With local `filter` and `resultType=results`, `numberReturned` can remain upstream value even when filtered `features` are empty (`tools/os_features.py:431-439`).
- This occurred in trace (`id=23`, `id=29`): `count=0` while `numberReturned` reflected upstream page size.

### 6.3 `polygon` was provided as a JSON string and silently ignored

Trace `id=30` sent:

```json
"polygon": "{\"type\":\"Polygon\",\"coordinates\":[...]}"
```

Implementation details:
- Polygon parser accepts dict/list, not string (`tools/os_features.py:267-271`).
- If `bbox` is valid, the query proceeds without polygon and no explicit warning (`tools/os_features.py:269-281`).

Impact:
- Query likely ran over full bbox instead of intended polygon constraint.

### 6.4 Query and payload pressure accumulated

- `id=25` CQL over large bbox timed out (5s timeout, 3 retries in OS client: `tools/os_common.py:25-26`, `tools/os_common.py:184-202`).
- `id=30` and `id=31` emitted very large tool result envelopes.
- STDIO adapter truncates text content above threshold (`server/stdio_adapter.py:432-466`) but still includes full `structuredContent` by default (`server/stdio_adapter.py:848-852`), so host context pressure can remain high.

## 7) Effectiveness of mcp-geo API Usage in This Run

Good usage:
- Collection discovery and queryables introspection (`id=21`, `id=22`).
- Progressive hypothesis testing across land/water collections.

Ineffective usage:
- Over-reliance on address-centric tools for named landscape boundary resolution.
- Broad CQL + broad bbox before narrowing geometry.
- Heavy `includeGeometry=true` and rich fields too early.
- Local post-filters used as if they were global analytical counts.
- No robust pagination strategy before interpreting absence/presence.

## 8) What a Correct Peatland Survey Workflow Should Look Like (with current APIs)

This is the best-practical workflow using the currently available toolset.

### Phase A: Define survey extent explicitly and defensibly

1. Resolve area geometry.
- Preferred: exact polygon from authoritative boundary source.
- Current fallback: use admin geometry and explicitly state it is a proxy if AONB boundary unavailable.

2. Validate area in output.
- Always report bbox, source, and whether boundary is proxy/approximate.

### Phase B: Fast indicator scan (low payload)

Use `lnd-fts-land-3` with low-cost requests first.

- `resultType="hits"`
- `includeGeometry=false`
- minimal fields
- tile large extents if needed (for reliability and to avoid single-call timeout)

For peat-indicator classes, prioritize:
- `description`: `Peat`, `Heath`, `Heath Or Rough Grassland`, `Heath Or Rough Grassland And Marsh`, `Marsh`, and mixed variants.
- `oslandcovertierb` contains `Peat`, `Heath`, `Marsh`, `Rough Grassland`.

### Phase C: Hydrology context

Use `wtr-fts-water-3`:
- first with low `limit` and no geometry for counts/type mix
- then fetch geometry for selected subsets only

### Phase D: Evidence extraction for report

Fetch representative geometry samples only after narrowing.
- Use `includeFields` to minimize payload.
- Use `pageToken` when present.
- If pagination metadata is missing/uncertain, record uncertainty and avoid global claims.

### Phase E: Survey output structure

A robust model answer should include:
- Area definition and confidence.
- Land-cover indicator counts and classes.
- Hydrology summary.
- Candidate peatland zones (ranked, with rationale).
- Access/logistics notes.
- Data limitations and next field verification steps.

## 9) What Result Should Look Like (example skeleton)

```
Survey area: Forest of Bowland (proxy boundary: <type>, bbox: [...])
Data sources: os_features.query (lnd-fts-land-3, wtr-fts-water-3), admin_lookup.*

1) Peatland indicator summary
- Direct peat class hits: <n>
- Heath / rough grassland / marsh mixed classes: <n by class>
- Confidence note: <high|medium|low> based on boundary fidelity and pagination completeness

2) Hydrological context
- Watercourse features: <n>
- Still water features: <n>
- Reservoir/canal/drain features: <n>

3) Candidate priority zones
- Zone A: <why>
- Zone B: <why>

4) Field plan
- Suggested transects / access windows / ground-truth checks

5) Limitations
- Boundary proxy caveat
- Any timed-out or partial queries
- Any pagination uncertainty
```

## 10) Immediate Engineering Recommendations for mcp-geo

1. Tighten polygon validation behavior in `os_features.query`.
- If `polygon` is provided but invalid type/shape, return `INVALID_INPUT` instead of silently ignoring when `bbox` exists.

2. Clarify and correct count semantics for local filtering.
- When local `filter` is applied, set `numberReturned` consistently to filtered output semantics.
- Optionally label counts as `pageFilteredCount` vs `globalMatchedCount`.

3. Add delivery mode to `os_features.query` for large outputs.
- Match existing `delivery=inline|resource|auto` pattern used in other tools.
- Reduce host context pressure for large geometry responses.

4. Add a protected-landscape boundary capability.
- Without AONB/SSSI-style boundary lookup, peatland surveys will keep starting with proxy extents.

5. Improve routing for environmental survey prompts.
- Current route classifier extracts poor place names for imperative queries (example: returns `Do`/`Survey` for the Bowland prompt).
- Extend `os_mcp.route_query` intent patterns and place extraction for "survey"/"habitat"/"peatland" style tasks.

## 11) Copy-Paste Prompt for ChatGPT Deep Research

Use the following prompt verbatim with Deep Research:

```text
You are conducting a forensic and methodological deep research study for an MCP geospatial server.

Task context:
- Investigate the question: "Do a peatland site survey on the forrest of Bowland" (original spelling retained).
- Analyze the observed tool behavior from these artifacts:
  1) troubleshooting/claude-stopped-after-ngd-features.md
  2) logs/claude-trace.jsonl
  3) troubleshooting/claude-floor-questions-harness-report-2026-02-18.md
- Treat these artifacts as primary evidence.

Deliverables:
1) Forensic reconstruction
- Build a precise timeline of tool calls (id, timestamp, args, status, latency, payload size).
- Identify turning points: discovery, failure, degradation, stop.
- Distinguish confirmed facts from inferred causes.

2) Technical diagnosis
- Evaluate how effectively the workflow used available APIs/tools.
- Identify where calls were semantically weak (e.g., area definition, filtering method, pagination assumptions, payload management).
- Explain why the session likely stopped despite successful final tool responses.

3) "Correct approach" method design
- Propose a robust, low-risk peatland survey workflow using the currently available mcp-geo tool families.
- Include stepwise call strategy with parameter guidance, fallback strategy, and uncertainty handling.
- Explicitly specify which outputs are suitable for claiming "survey complete" and which are not.

4) Model answer specification
- Produce a target answer blueprint for the user query:
  - area definition
  - peat indicators
  - hydrology context
  - candidate zones
  - fieldwork recommendations
  - caveats/confidence
- Provide an example answer skeleton populated with plausible placeholders.

5) Engineering recommendations
- Prioritize server-side improvements by impact and implementation effort.
- Include concrete changes for:
  - filtering/count semantics
  - polygon validation
  - large-payload delivery mode
  - protected-landscape boundary support
  - routing improvements for environmental surveys

Constraints:
- Do not use speculative claims when evidence is available.
- Mark all inferences explicitly as inference.
- Prefer concise tables for timelines and failure mode matrices.
- Produce output suitable for an engineering post-mortem document.

Output format:
- Section A: Executive summary (<= 10 bullets)
- Section B: Timeline table
- Section C: Evidence-backed failure analysis
- Section D: Proposed end-to-end survey workflow
- Section E: "Model answer" blueprint
- Section F: Prioritized implementation roadmap
```

## 12) Bottom Line

The Bowland peatland question exposed a real and useful stress case for mcp-geo.
- The server handled many calls correctly and returned valid data.
- The analytical workflow quality degraded due area-definition gaps, mixed filtering semantics, and payload/latency pressure.
- With targeted query strategy and a few server-level guardrails, this class of question can become reliably answerable.
