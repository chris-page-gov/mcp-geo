# MCP-Geo Stakeholder Benchmark Gap Analysis

Date: 2026-03-09
Branch context: `codex/mcp-geo-stakeholder-eval`

## Executive finding

Yes. The current stakeholder benchmark pack scores the **reference answers** at
`100/100`, but that does **not** mean MCP-Geo can fully answer the 10 benchmark
questions today.

- The generated pack currently marks `9` scenarios as `partial` and `1` as
  `blocked`.
- The score measures whether the benchmark's expected output is complete,
  evidence-backed, caveated, and exportable.
- The score does **not** measure current repo capability completeness.

## Environment finding

The local runtime used for the benchmark build did **not** have an OS API key
available to MCP-Geo at execution time.

Observed checks in this workspace:

```text
printenv OS_API_KEY | wc -c  -> 0
server.config.settings.OS_API_KEY -> ""
```

So your second reading is also correct for this run: live OS-backed tool paths
that require `OS_API_KEY` were not exercised by the benchmark generation
process.

This does not prove the key does not exist elsewhere on the machine. It only
proves the key was not visible to the current Codex/pytest/process environment.
For MCP-Geo specifically, the runtime currently hydrates the key from:

- process environment `OS_API_KEY`
- file-based secret `OS_API_KEY_FILE`
- repo `.env`

If the expectation is that benchmark runs must use live OS services, the
benchmark harness should fail fast when `settings.OS_API_KEY` is empty.

## Scenario status snapshot

| Scenario | Current status | Why it is not fully answered today |
| --- | --- | --- |
| SG01 incident + vulnerable households | partial | No first-class protected household join workflow, no bulk address-to-UPRN matcher, no built-in incident polygon to premises resolver. |
| SG02 batch free-text address matching | partial | No dedicated batch matcher with confidence bands, collision handling, or manual-review queue output. |
| SG03 shortest route between premises | blocked | UI exists, but no actual routing engine or routable network backend is exposed. |
| SG04 maintainable road lengths by class | partial | No live maintained-road rollup flow for statutory-quality totals from segment-level data. |
| SG05 planning constraints summary | partial | Planning layers used in the example are not first-class MCP-Geo tools. |
| SG06 asset register + flood overlay | partial | No generic CSV-to-UPRN-to-overlay workflow; current answer depends on pre-curated fixtures. |
| SG07 flood appraisal + verification plan | partial | No full premises/building inventory resolver and no authoritative building-footprint flood overlay workflow. |
| SG08 fragmented housing development normalization | partial | No canonical multi-file reconciliation workflow for planning/allocation/promoter records. |
| SG09 BDUK premise status lookup | partial | BDUK is not modeled as a native dataset/tool family and absence reasoning is still inferential. |
| SG10 council-tax-like vs price-paid linking | partial | No hierarchy-aware cross-dataset property linker with persistent UPRN resolution and unmatched diagnostics. |

## Cross-cutting gaps

### 1. Runtime and credential gating

Required:

- Fail fast when a benchmark scenario is marked `live_os_required` and
  `settings.OS_API_KEY` is empty.
- Record whether each scenario ran in `live`, `cached`, `fixture`, or
  `synthetic` mode.
- Capture the exact MCP-Geo tool calls and upstream status codes used during the
  evaluation.

Why it matters:

- Without this, a benchmark can look authoritative while silently falling back
  to fixture-only reasoning.

Repo impact:

- `server/config.py`
- `scripts/stakeholder_benchmark_pack.py`
- likely a new scenario runner, separate from the pack generator

### 2. Bulk address and UPRN resolution

Required:

- A batch address-matching tool or workflow over OS Places / AddressBase-style
  data.
- Confidence scoring for exact, plausible, unmatched, and duplicate/collision
  cases.
- Explicit PAON/SAON parsing, postcode validation, and hierarchy handling.
- Review-queue export as CSV/JSON.

Needed for:

- SG01
- SG02
- SG06
- SG07
- SG09
- SG10

Minimum implementation target:

- new `os_places.match_batch` or equivalent server-side batch matcher
- reusable normalization module instead of ad hoc prompt logic

### 3. Generic file-ingest and join pipeline

Required:

- Accept CSV/GeoJSON inputs as evaluation fixtures or uploaded datasets.
- Map columns to canonical fields: address, postcode, UPRN, geometry, area code,
  asset id, site id.
- Support deterministic joins, dedupe, anomaly reporting, and export.

Needed for:

- SG01
- SG02
- SG06
- SG08
- SG09
- SG10

Current gap:

- The repo has strong point tools, but not a general “ingest tabular file and
  run a reproducible geospatial workflow” surface.

### 4. First-class overlay and spatial-analysis tools

Required:

- Point-in-polygon
- polygon intersection
- distance-to-boundary / near-risk checks
- area/boundary aggregation
- reproducible geometry provenance

Needed for:

- SG01
- SG05
- SG06
- SG07
- SG08

Current gap:

- MCP-Geo has lookup and NGD feature tooling, but not a high-level overlay
  workflow that directly answers stakeholder questions from uploaded or curated
  input files.

### 5. Planning/open-data connectors

Required:

- native tool family for `planning.data.gov.uk` layers used in stakeholder work:
  flood-risk zones, conservation areas, listed buildings, TPOs, article 4,
  brownfield/local-plan compatible layers where licensing allows
- explicit source freshness/provenance in responses

Needed for:

- SG05
- SG06
- SG07

Current gap:

- The benchmark examples use planning.data as a public comparator, but MCP-Geo
  does not currently expose those layers as first-class tools.

### 6. Road network and routing backend

Required:

- a real routing engine exposed through MCP-Geo, not just the route planner UI
- prebuilt routable graph based on OS Highways Network
- turn restrictions, access constraints, and optional hazard exclusions
- route geometry, distance, warnings, and export

Needed for:

- SG03 directly
- SG04 indirectly for credible network-derived road reporting

Current gap:

- `os_apps.render_route_planner` is a UI launcher.
- `os_mcp.route_query` is an intent router, not a route solver.

### 7. Domain adapters for benchmark-specific public datasets

Required:

- BDUK lookup adapter with status interpretation and epoch caveats
- HM Land Registry / Price Paid helper logic for curated examples
- council-tax-like to land-registry-like linking workflow
- housing-development reconciliation workflow with canonical site ids

Needed for:

- SG08
- SG09
- SG10

Current gap:

- These are represented as supplied fixtures, not native MCP-Geo capability.

## Scenario-by-scenario implementation requirements

### SG01

Needed to answer fully:

- live incident geometry ingestion
- bulk UPRN resolution
- protected dataset join contract
- dedupe/anomaly table generation
- boundary aggregation

Primary blocker:

- no reusable bulk premises-resolution and protected-data join workflow

### SG02

Needed to answer fully:

- batch matcher tool
- confidence classification
- review queue export
- collision diagnostics

Primary blocker:

- no server-side batch matching product surface

### SG03

Needed to answer fully:

- routable network backend
- restriction-aware routing
- route geometry + distance output
- operational map/export output

Primary blocker:

- no route solver in MCP-Geo today

### SG04

Needed to answer fully:

- maintained-road segment connector
- class rollup from live segment data
- anomaly reporting for conflicting class/maintainability
- comparator reconciliation against authority publication

Primary blocker:

- no end-to-end maintained-road reporting workflow

### SG05

Needed to answer fully:

- planning layer discovery
- site polygon resolution
- intersect / nearby checks over planning layers
- explicit local-policy gap reporting

Primary blocker:

- planning layers are external comparator inputs, not MCP-Geo tools

### SG06

Needed to answer fully:

- CSV asset ingest
- UPRN matching and verification
- flood overlay engine
- near-risk distance calculation

Primary blocker:

- no generic asset-register join and overlay workflow

### SG07

Needed to answer fully:

- authoritative premises/building inventory
- building-footprint flood overlay
- classification by risk band
- prioritized field-verification exports

Primary blocker:

- current logic is sample-based and partly postcode-proxy based

### SG08

Needed to answer fully:

- multi-source site normalization
- canonical site family logic
- geometry assignment to wards/polling districts
- confirmed vs uncertain supply split

Primary blocker:

- no native fragmented-planning-source reconciliation toolchain

### SG09

Needed to answer fully:

- BDUK dataset adapter
- AddressBase / OS classification check
- ranked absence reasoning from live/current records

Primary blocker:

- premise-status reasoning is still driven by fixture + comparator logic

### SG10

Needed to answer fully:

- hierarchy-aware property linker
- persistent UPRN enrichment
- unmatched diagnostics
- exact/plausible/unmatched join outputs

Primary blocker:

- no reusable property-record linking engine

## Recommended implementation order

### Phase A: make live OS evaluation real

1. Enforce `OS_API_KEY` visibility checks in benchmark runs.
2. Add live/fixture provenance flags to scenario execution outputs.
3. Separate “benchmark pack generation” from “benchmark execution against live MCP-Geo”.

### Phase B: unlock 6 of the 10 scenarios

1. Build batch address-to-UPRN matching.
2. Build generic CSV/GeoJSON ingest + join pipeline.
3. Add overlay helpers for point/polygon/distance/aggregation.

This is the shortest path to materially improving:

- SG01
- SG02
- SG06
- SG07
- SG09
- SG10

### Phase C: add missing domain connectors

1. Add planning.data tool family.
2. Add BDUK dataset adapter.
3. Add fragmented housing-development reconciliation workflow.

This unlocks:

- SG05
- SG08
- stronger SG09

### Phase D: solve the blocked routing case

1. Expose a true routing backend over OS Highways Network.
2. Add restriction-aware route computation and export.
3. Feed routing output into route-planner UI instead of using UI-only launch.

This unlocks:

- SG03
- strengthens SG04 if road-network reporting is implemented from the same graph

## Definition of done for these 10 questions

MCP-Geo should only be described as able to answer these benchmark questions
fully when all of the following are true:

- each scenario can run against MCP-Geo, not just a curated fixture explanation
- each run records whether live OS/open-data services were used
- scenarios that require OS data fail loudly when `OS_API_KEY` is absent
- uploaded or supplied input files can be ingested without hand-built fixtures
- exports are machine-readable and reproducible
- the benchmark score and the product capability level are reported separately

## Immediate next actions

1. Add a hard benchmark-run preflight that checks `settings.OS_API_KEY`.
2. Implement batch UPRN matching and reusable address normalization.
3. Add a generic ingest-and-overlay workflow for CSV/GeoJSON inputs.
4. Model planning.data and BDUK as first-class dataset/tool families.
5. Implement a real routing backend before claiming route-answer capability.
