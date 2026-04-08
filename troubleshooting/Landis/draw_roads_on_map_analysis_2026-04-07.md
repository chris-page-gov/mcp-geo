# Draw Roads On Map Analysis (2026-04-07)

## Question

What is the best way to stop AI clients from struggling with `mcp-geo` when the
real task is "draw the roads on the map" rather than "manually orchestrate
paged feature export, byte-chunk reads, JSON reassembly, Python ETL, and HTML
replacement"?

Primary evidence: `troubleshooting/Landis/draw_roads_on_map.md`

## Bottom line

The best fix is not more prompt guidance. The best fix is to change the server
contract so the AI no longer acts as a transport-layer ETL engine.

For this class of task, `mcp-geo` should provide a task-shaped export tool that
does the following server-side:

1. resolves the requested road network/features
2. fetches all upstream pages
3. assembles the full geometry set
4. optionally filters/simplifies it
5. returns one ready artifact:
   - GeoJSON
   - JS overlay block
   - map package / HTML fragment
   - durable `resource://` bundle with semantic parts

The model should orchestrate which roads to draw and where to place the output.
It should not be responsible for byte-offset chunk stitching or reconstructing
mid-string JSON documents.

## What went wrong in the transcript

### 1. The AI was pushed into byte-level resource recovery

The run quickly devolved into manual chunk management:

- expired resources forced the model to restart the whole fetch flow
  (`draw_roads_on_map.md:51`)
- the model then tracked page/chunk bookkeeping by hand
  (`draw_roads_on_map.md:43-50`, `draw_roads_on_map.md:53-60`)
- later it had to reason explicitly about concatenating chunk text back into
  valid JSON (`draw_roads_on_map.md:146`, `draw_roads_on_map.md:241-251`,
  `draw_roads_on_map.md:393-397`)

That is a bad use of model cognition. It is high-effort, low-signal, and easy
to derail.

### 2. The model had to compensate for missing task-level tooling

The actual user goal was map output. The available contract was raw
`os_features.query` + `os_resources.get`, so the model invented its own ETL
pipeline:

- write a Python geometry extractor (`draw_roads_on_map.md:81-123`)
- manually save concatenated page JSON (`draw_roads_on_map.md:146-147`,
  `draw_roads_on_map.md:175-182`)
- generate JS arrays and splice them into HTML via regex
  (`draw_roads_on_map.md:255-358`)

This is exactly the kind of work the server should own when the task is
"produce a map-ready road overlay."

### 3. Partial-success outputs looked superficially correct

The first attempt produced an HTML file that looked structurally plausible:

- expected sections existed (`draw_roads_on_map.md:62-78`)
- but the output only contained a tiny sample of road segments
  (`draw_roads_on_map.md:78-80`)

This is especially dangerous. A host or user sees a plausible map artifact,
while the underlying data is incomplete because the model ran out of transport
patience before completing the geometry assembly.

### 4. The workflow mixed two separate responsibilities

The transcript forced one conversation to handle both:

- geospatial data acquisition
- host-side file editing for a specific external HTML map

Those are different jobs. `mcp-geo` currently helps with the first only at a
low level, so the model had to improvise the second as well.

## Root cause

The AI/server boundary is in the wrong place for high-volume map assembly.

Current boundary:

- server returns paged feature results or chunked resources
- AI performs assembly, filtering, transformation, and embedding

Recommended boundary:

- AI specifies intent, roads, AOI, and desired output format
- server performs assembly/export and returns one usable artifact

In short:

- AI should choose
- server should compile

## Best-practice recommendation

### Preferred design

Add a map-overlay export tool for road/network geometry, for example:

`os_map.export_roads`

Suggested input:

```json
{
  "roads": [
    {"label": "A444", "roadClassificationNumber": "A444"},
    {"label": "A5", "roadClassificationNumber": "A5"},
    {"label": "B4089", "roadClassificationNumber": "B4089"},
    {"label": "B4101", "roadClassificationNumber": "B4101"},
    {"label": "Harbury", "roadClassificationNumber": null}
  ],
  "bbox": [-1.56, 52.14, -1.37, 52.58],
  "collection": "trn-ntwk-roadlink-5",
  "includeGeometry": true,
  "outputFormat": "geojson_bundle",
  "simplifyToleranceMeters": 2.0
}
```

Suggested output:

```json
{
  "delivery": "resource",
  "resourceUri": "resource://mcp-geo/os-exports/roads-overlay-<hash>.json",
  "featureCounts": {
    "A444": 284,
    "A5": 66,
    "B4089": 91,
    "B4101": 231,
    "Harbury": 143
  },
  "format": "geojson_bundle",
  "parts": [
    {"name": "A444.geojson", "uri": "resource://.../A444.geojson"},
    {"name": "A5.geojson", "uri": "resource://.../A5.geojson"}
  ]
}
```

Optional output formats:

- `geojson_bundle`
- `javascript_overlay`
- `leaflet_snippet`
- `html_map_package`

### Why this is the best approach

- It removes page/chunk orchestration from the model.
- It eliminates repeated upstream refetches when resources expire.
- It makes completeness testable server-side.
- It returns a domain object the user actually wants.
- It keeps hosts with weak tool/runtime behavior usable because the hard work is
  done before the result reaches the model.

## Secondary improvements

### 1. Replace byte-offset chunking with semantic part manifests for large exports

`os_resources.get` is useful as a generic bridge, but byte-offset chunking is a
poor fit for LLM-driven assembly of large JSON payloads.

For export-sized data, prefer:

- part indexes instead of raw byte offsets
- named files (`A444.geojson`, `B4101.geojson`)
- explicit `partCount`
- stable export manifests

This avoids situations like the transcript’s manual reasoning about chunk
boundaries and broken JSON joins (`draw_roads_on_map.md:146`,
`draw_roads_on_map.md:241-251`).

### 2. Make export resources durable enough to survive a normal conversation

The transcript lost progress because the previous session's resources expired
(`draw_roads_on_map.md:51`).

For server-generated exports:

- keep them alive longer
- key them by deterministic content hash
- allow regeneration by id/hash without re-running the whole reasoning flow

### 3. Add route-query guidance for map-editing/export tasks

`os_mcp.route_query` should recognize prompts like:

- "draw these roads on a map"
- "replace broken Overpass fetch with OS geometry"
- "generate a Leaflet overlay for these roads"

and recommend the export tool directly, not low-level `os_features.query`.

### 4. Return completeness metadata by default

Every assembled export should state:

- source pages fetched
- upstream page count
- feature counts per requested road
- filters applied
- whether the output is complete or sampled

That would have caught the transcript’s false-success case immediately
(`draw_roads_on_map.md:78-80`).

### 5. Keep tolerant low-level tools, but stop making them the primary UX

The existing `os_features.query` improvements are still useful:

- queryable normalization
- unsupported-collection suggestions
- warning metadata

But those are resilience features for power users and fallback paths. They are
not the right primary interface for "build me a roads overlay."

## Recommended implementation order

### Phase 1: highest-value change

Add `os_map.export_roads` or equivalent domain export tool that:

- accepts multiple road specs
- fetches all pages server-side
- emits one complete artifact
- reports per-road counts

This is the main fix.

### Phase 2: improve export delivery

Add durable manifest-backed export resources with named semantic parts instead
of byte-chunk-only recovery.

### Phase 3: route-query and descriptor guidance

Teach `os_mcp.route_query` and descriptor docs to steer map-overlay tasks toward
the export tool first.

### Phase 4: optional host-facing helpers

If this workflow is common, add one of:

- `outputFormat="javascript_overlay"` for direct HTML embedding
- `outputFormat="html_map_package"` for a full ready-to-open map export

## What not to do

Do not try to solve this mainly by:

- adding more prompt instructions about chunk handling
- asking the AI to write more Python scripts
- relying on the model to manually stitch `resource://` chunk text
- expecting hosts to behave perfectly around deferred tools and resource reads

Those help around the edges, but they do not move the boundary to the right
place.

## Conclusion

The transcript demonstrates a general rule:

When the output is a compiled spatial artifact, the MCP server should own the
compilation.

The best way to address the current AI angst is therefore:

1. introduce a task-shaped road overlay export tool
2. make large exports durable and semantically chunked
3. route map-building prompts to that tool first

That changes `mcp-geo` from "a box of low-level geospatial primitives" into "a
reliable map-production backend that an AI can orchestrate without drowning in
transport details."
