# MCP-Geo Stakeholder Capability Roadmap

Date: 2026-03-10
Branch context: `codex/mcp-geo-stakeholder-eval`

Companion inputs:

- [live run report](/Users/crpage/repos/mcp-geo/docs/reports/mcp_geo_stakeholder_live_run_2026-03-10.md)
- [gap analysis](/Users/crpage/repos/mcp-geo/docs/reports/mcp_geo_stakeholder_gap_analysis_2026-03-09.md)

## Current state

- Live benchmark status: `1 full`, `17 partial`, `2 blocked`
- `SG03` is now full when the benchmark route graph is seeded.
- `SG17` and `SG20` remain hard blocked.
- Most other gaps are product-surface gaps, not base-data lookup failures.

## Sequencing rule

Build the shared primitives first, then the domain connectors, then the operational decision workflows.
That gives the fastest path from "partial everywhere" to a usable stakeholder answer surface.

## Epic roadmap

### Epic A: Benchmark Runtime Gates

Goal:

- Make live evaluation deterministic and auditable.

Scenarios unlocked or hardened:

- all scenarios

Acceptance criteria:

- Benchmark runs fail fast when a scenario is marked live-required and `OS_API_KEY` is unavailable.
- Each scenario output records `live`, `cache`, `fixture`, or `synthetic` provenance.
- Route-graph readiness is reported before any route-dependent scenario runs.
- Benchmark score and product-capability status are always reported separately.

### Epic B: Batch Address and UPRN Matching

Goal:

- Add a first-class server-side batch matcher rather than looping single-record search calls externally.

Scenarios primarily unlocked:

- `SG01`, `SG02`, `SG06`, `SG07`, `SG09`, `SG10`

Scenarios materially strengthened:

- `SG12`, `SG13`, `SG15`, `SG16`

Acceptance criteria:

- New tool surface exists, for example `os_places.match_batch`.
- Inputs can be CSV or JSON rows with canonical address fields.
- Output includes per-row `uprn`, confidence band, duplicate/collision flags, and review reasons.
- Review queues can be exported as CSV and JSON.
- Regression coverage proves duplicate, unmatched, and low-confidence branches.

### Epic C: Generic Ingest, Join, and Overlay

Goal:

- Make MCP-Geo able to ingest stakeholder files and perform repeatable geospatial workflows without bespoke harness code.

Scenarios primarily unlocked:

- `SG01`, `SG06`, `SG07`, `SG08`, `SG10`

Scenarios materially strengthened:

- `SG18`, `SG19`

Acceptance criteria:

- File-ingest surface accepts CSV and GeoJSON.
- Column mapping supports address, postcode, UPRN, geometry, area code, and site/resource id.
- Native operations exist for point-in-polygon, polygon intersection, distance, aggregation, and export.
- Join outputs include unmatched diagnostics and provenance for every derived field.

### Epic D: Planning, Flood, and Public Dataset Connectors

Goal:

- Model the comparator datasets used by stakeholders as native MCP-Geo tool families.

Scenarios primarily unlocked:

- `SG05`, `SG06`, `SG07`, `SG08`, `SG09`

Acceptance criteria:

- First-class planning and flood connectors exist with freshness metadata.
- A BDUK adapter exists with status interpretation and absence reasoning.
- Spatial intersection against planning and flood layers can be executed natively.
- Returned outputs cite source dataset, version, release date, and licensing.

### Epic E: Route Graph Productization

Goal:

- Make routing work in default environments, not just seeded benchmark sessions.

Scenarios primarily unlocked:

- `SG03`

Scenarios materially strengthened:

- `SG04`, `SG12`

Acceptance criteria:

- Route graph bootstrap is automatic in supported local/dev environments.
- `os_route.descriptor` reports `ready=true` without manual seeding in standard setups.
- Restriction and hazard tables are loaded and versioned with the graph.
- Route outputs include geometry, distance, duration, and warnings from the real graph.

### Epic F: ONS Geography Allocation and Cache Coverage

Goal:

- Make exact and best-fit UPRN geography allocation reliable enough for direct stakeholder use.

Scenarios primarily unlocked:

- `SG11`, `SG15`

Scenarios materially strengthened:

- `SG09`

Acceptance criteria:

- Cache status reports freshness, coverage, and missingness clearly.
- Benchmark UPRNs are covered in exact and best-fit modes where public source data allows.
- Batch comparison output shows exact, best-fit, mismatch, and `NOT_FOUND` rows cleanly.

### Epic G: Operational Decision Workflows

Goal:

- Promote current lookup primitives into first-class decision tools.

Scenarios primarily unlocked:

- `SG12`, `SG13`, `SG16`, `SG18`, `SG19`

Acceptance criteria:

- Native dispatch-ranking output exists for resource-vs-incident comparisons.
- Native nearest-facility output exists for patient/site style use cases.
- Address-classification output can map UPRN-backed properties into an operational settings taxonomy.
- Service-coverage and inequity outputs can rank areas and nearest sites without bespoke external code.

### Epic H: Derived Built-Environment and Network Metrics

Goal:

- Expose the operational attributes that are still synthetic in the benchmark pack today.

Scenarios primarily unlocked:

- `SG04`, `SG14`, `SG17`

Acceptance criteria:

- Maintained-road totals by class can be produced from a native workflow.
- Building height and floor-count data can be queried or ingested through a documented first-class contract.
- Street width and gradient can be derived or ingested through a native workflow with provenance.

### Epic I: Patrol Optimisation and Demand Planning

Goal:

- Add a true operational planning surface for policing-style hotspot review.

Scenarios primarily unlocked:

- `SG20`

Acceptance criteria:

- Demand and vulnerability inputs can be ingested or derived natively.
- Hotspots can be ranked against live resource locations.
- Patrol allocation or nearest-resource optimisation is produced as a native output, not a heuristic in the harness.

## Suggested delivery order

1. Epic A
2. Epic B
3. Epic C
4. Epic D
5. Epic E
6. Epic F
7. Epic G
8. Epic H
9. Epic I

## Expected payoff by stage

- After `A+B+C`: most of the original Phase 2-style data-integration questions stop depending on bespoke harness logic.
- After `D+E+F`: the remaining public-data and routing questions become product-grade rather than benchmark-grade.
- After `G+H+I`: the more operational Phase 1 scenarios can move from grounded partial answers to genuine first-class stakeholder workflows.

## Definition of done

An epic only counts as complete when:

- the needed workflow exists as MCP-Geo product surface, not just harness code
- the benchmark scenario can run against that surface directly
- the output is reproducible and exportable
- provenance and freshness are explicit
- regression tests cover the new happy path and the main failure branches
