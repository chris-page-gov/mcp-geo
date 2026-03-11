# MCP-Geo Stakeholder Evaluation Benchmark Pack

Generated: 2026-03-10

This pack turns the Phase 3 prompt bank into a run-ready benchmark for stakeholder evaluation.
Scenarios 1 to 10 are the existing Phase 2-derived top set; scenarios 11 to 20 add the next Phase 1-derived high-impact cases in the same format.
Each scenario now has populated inputs, expected outputs, source provenance, capability notes, and a scored reference answer.

## Reusable Header

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.
```

## SOTA Scoring Rubric

| Dimension | Points | What it tests |
| --- | ---: | --- |
| Answer Contract | 20 | All six reusable-header return items are present.; All scenario-specific return items are present.; Short answer and structured output do not contradict each other. |
| Geospatial Grounding | 20 | Incident/site/area inputs are resolved to explicit geometry, address, or identifier references.; Spatial operations are stated operationally: lookup, join, intersect, route, aggregate, verify.; Maps are recommended when the scenario materially benefits from spatial inspection. |
| Identifier Integrity | 15 | UPRN/address reasoning distinguishes confirmed identifiers from inferred matches.; Duplicates, collisions, and hierarchy issues are surfaced explicitly.; Missing-record explanations are ranked by evidence rather than guessed. |
| Evidence and Comparator Alignment | 15 | Public-source comparator findings are referenced when available.; Synthetic scenarios are labelled synthetic in the answer and output tables.; Published findings are compared cautiously rather than treated as generated output. |
| Uncertainty and Caveats | 10 | Tooling, dataset, licensing, and freshness gaps are named.; Blocked workflows return the furthest grounded partial result.; Caveats are concrete enough for an operational reviewer to act on them. |
| Verification and Export Readiness | 10 | Verification steps are explicit, ordered, and scenario-specific.; Export formats are suggested in a way that fits the evidence produced.; High-risk scenarios include a field-check or manual-review plan. |
| Dataset and Tool Traceability | 10 | Datasets, tools, and external layers are named precisely.; Known MCP-Geo gaps are made explicit when the scenario exceeds current capability.; The answer differentiates MCP-Geo outputs from supplied fixture data. |

Scoring thresholds:

- `excellent`: 90+
- `good`: 75+
- `acceptable`: 60+
- `poor`: 40+

## Validation Status

- Pack valid: `True`
- Machine-readable pack: `data/benchmarking/stakeholder_eval/benchmark_pack_v1.json`
- Workflow report: [mcp_geo_stakeholder_benchmark_workflow_2026-03-10.md](mcp_geo_stakeholder_benchmark_workflow_2026-03-10.md)
- Interpretation note: the `Reference score` grades the completeness and auditability of the benchmark's gold answer, not the current implementation completeness of MCP-Geo itself.
- Read `MCP-Geo support level` separately: `partial` and `blocked` mark product capability gaps even when the benchmark reference output scores `100/100`.

## Scenario Pack

## 1. Affected premises and vulnerable households in an incident area (SG01)

- Example mode: `mixed`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

Public benchmark base: Retford flood-risk-zone references 402042/2 and 167647/3 from planning.data.gov.uk plus real Retford residential addresses from HM Land Registry Price Paid Data. Synthetic component: vulnerability categories layered onto those real addresses because public vulnerable-household datasets are not openly published at household level.

**Sources**
- benchmark rationale: [Identifying and supporting persons who are vulnerable in an emergency](https://www.gov.uk/government/publications/identifying-people-who-are-vulnerable-in-a-crisis-guidance-for-emergency-planners-and-responders/identifying-and-supporting-persons-who-are-vulnerable-in-an-emergency-supporting-guidance-for-local-resilience-forums-in-england-html)
- real-address source: [HM Land Registry Price Paid Data downloads](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- incident-area source: [Planning Data flood-risk-zone dataset](https://www.planning.data.gov.uk/dataset/flood-risk-zone)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_01_incident_zone.wkt`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_01_vulnerable_households.csv`

**Comparator**

Comparator baseline is structural rather than numeric: Cabinet Office guidance states that multi-source conversion is time-consuming during emergencies, so this benchmark expects MCP-Geo to expose joins, dedupe, and caveats explicitly rather than pretending the supplied synthetic vulnerability file is authoritative.

**Known Gaps**
- This repo does not ship an open vulnerable-household dataset; the benchmark file is synthetic.
- OS Places requires a live OS key for direct UPRN resolution in a real run.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- incident geometry: POLYGON((-0.946200 53.321400,-0.946200 53.318800,-0.943000 53.318800,-0.943000 53.321400,-0.946200 53.321400))
- vulnerable-households dataset: data/benchmarking/stakeholder_eval/fixtures/scenario_01_vulnerable_households.csv
- optional critical-sites dataset: none

Use MCP-Geo to answer:
“Which premises and households are affected, and what support-relevant counts can we produce?”

Required steps:
- Resolve the incident geography precisely.
- Identify all affected premises/UPRNs within the incident area.
- Join to the vulnerable-households dataset using the safest available identifier strategy.
- Deduplicate records where multiple address forms point to the same premises.
- Summarise by:
  - total affected premises
  - total affected households/records
  - counts by vulnerability category
  - counts by area/boundary if available
- Flag any ambiguous, unmatched, or duplicate records.
- State what could be wrong because of missing UPRNs, stale address data, or join-quality issues.

Return:
- executive summary
- affected-premises table
- vulnerability summary table
- duplicates/anomalies table
- confidence and caveats
- suggested export format

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `executive_summary`
- `affected_premises_table`
- `vulnerability_summary_table`
- `duplicates_anomalies_table`
- `suggested_export_format`

**Reference Output Summary**

- `The benchmark incident area affects 4 unique premises and 5 vulnerable-household records after deduplication review. One duplicated address variant maps to the same Mill Bridge Close premises, so the operational answer must separate affected premises from raw records.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The benchmark incident area affects 4 unique premises and 5 vulnerable-household records after deduplication review. One duplicated address variant maps to the same Mill Bridge Close premises, so the operational answer must separate affected premises from raw records.",
  "method_used": [
    "Use the supplied incident polygon clipped from planning.data flood-risk-zone references 402042/2 and 167647/3.",
    "Resolve each supplied address to a candidate premises or UPRN using MCP-Geo address tools where available.",
    "Join the synthetic vulnerability file by normalized address, then deduplicate the two variants of 6 Mill Bridge Close.",
    "Assign affected premises to Bassetlaw using the postcode and area context already embedded in the example."
  ],
  "datasets_tools_used": [
    "planning.data.gov.uk flood-risk-zone references 402042/2 and 167647/3",
    "HM Land Registry Price Paid Data 2025 addresses used as the real-address base for the synthetic vulnerability file",
    "MCP-Geo tools: os_places.search, os_places.by_uprn, ons_geo.by_uprn, admin_lookup.containing_areas"
  ],
  "confidence_caveats": [
    "Public vulnerable-household data is synthetic in this benchmark, so counts test workflow quality rather than real emergency truth.",
    "Exact UPRN resolution depends on OS Places availability; without it, a high-quality answer must still report address-level matches and caveats.",
    "The incident polygon is a clipped operational exercise area derived from authoritative flood-zone geometry rather than the full published geometry."
  ],
  "verification_steps": [
    "Re-run the four affected addresses through OS Places or AddressBase-backed matching and confirm the UPRN mapping.",
    "Verify whether the duplicate 6 Mill Bridge Close records are two services for one household or two households at one premises.",
    "Cross-check the affected set against the latest flood-warning or incident perimeter before export."
  ],
  "structured_output": {
    "affectedPremises": [
      {
        "premisesLabel": "Navigation Lodge, Wharf Road, Retford DN22 6EN",
        "recordCount": 1,
        "joinQuality": "high",
        "status": "affected"
      },
      {
        "premisesLabel": "6 Mill Bridge Close, Retford DN22 6FE",
        "recordCount": 2,
        "joinQuality": "review_duplicate",
        "status": "affected"
      },
      {
        "premisesLabel": "18 Mill Bridge Close, Retford DN22 6FE",
        "recordCount": 1,
        "joinQuality": "high",
        "status": "affected"
      },
      {
        "premisesLabel": "115 Mill Bridge Close, Retford DN22 6FE",
        "recordCount": 1,
        "joinQuality": "high",
        "status": "affected"
      }
    ],
    "vulnerabilitySummary": [
      {
        "category": "mobility_support",
        "records": 1
      },
      {
        "category": "older_person",
        "records": 1
      },
      {
        "category": "medically_dependent",
        "records": 1
      },
      {
        "category": "young_children",
        "records": 1
      },
      {
        "category": "visual_impairment",
        "records": 1
      }
    ]
  },
  "executive_summary": "4 affected premises, 5 affected records, 1 duplicate-address anomaly, and 2 negative-control records outside the incident area.",
  "affected_premises_table": [
    {
      "premises": "Navigation Lodge, Wharf Road, Retford DN22 6EN",
      "affectedRecords": 1,
      "boundary": "Bassetlaw",
      "notes": "Inside clipped flood incident area"
    },
    {
      "premises": "6 Mill Bridge Close, Retford DN22 6FE",
      "affectedRecords": 2,
      "boundary": "Bassetlaw",
      "notes": "Duplicate address forms require review"
    },
    {
      "premises": "18 Mill Bridge Close, Retford DN22 6FE",
      "affectedRecords": 1,
      "boundary": "Bassetlaw",
      "notes": "Inside clipped flood incident area"
    },
    {
      "premises": "115 Mill Bridge Close, Retford DN22 6FE",
      "affectedRecords": 1,
      "boundary": "Bassetlaw",
      "notes": "Inside clipped flood incident area"
    }
  ],
  "vulnerability_summary_table": [
    {
      "category": "mobility_support",
      "affectedRecords": 1
    },
    {
      "category": "older_person",
      "affectedRecords": 1
    },
    {
      "category": "medically_dependent",
      "affectedRecords": 1
    },
    {
      "category": "young_children",
      "affectedRecords": 1
    },
    {
      "category": "visual_impairment",
      "affectedRecords": 1
    }
  ],
  "duplicates_anomalies_table": [
    {
      "issue": "Duplicate candidate",
      "records": [
        "VH-002",
        "VH-003"
      ],
      "premises": "6 Mill Bridge Close, Retford DN22 6FE",
      "action": "Manual dedupe before operational export"
    }
  ],
  "suggested_export_format": "CSV for the premises list plus GeoJSON if point coordinates are resolved during the live MCP-Geo run."
}
```

## 2. Batch match free-text addresses to UPRNs at scale (SG02)

- Example mode: `mixed`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

The input file is synthetic but derived from real HM Land Registry 2025 Bassetlaw transactions so the benchmark can test messy-address handling without inventing the underlying real-world addresses.

**Sources**
- real-address source: [HM Land Registry Price Paid Data downloads](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- identifier standard: [Use UPRNs to identify locations and use addresses](https://www.gov.uk/guidance/use-uprns-to-identify-locations-and-use-addresses)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_02_address_batch.csv`

**Comparator**

Comparator baseline is benchmark truth rather than a published percentage: 10 messy records derived from real addresses should yield 6 exact matches, 2 plausible review cases, 1 unmatched record, and 1 duplicate/collision pair.

**Known Gaps**
- Without an OS key, the live MCP-Geo run cannot complete authoritative address matching in this environment.
- The benchmark therefore scores join logic, confidence labelling, and failure explanations rather than raw lookup success alone.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given this address file: data/benchmarking/stakeholder_eval/fixtures/scenario_02_address_batch.csv
Answer:
“Match these addresses to authoritative UPRNs, quantify match quality, and explain failures.”

Required steps:
- Inspect the input fields and assess address quality.
- Standardise address strings where possible.
- Use MCP-Geo to match each record to a likely UPRN.
- Classify results into:
  - exact/high-confidence match
  - plausible match needing review
  - unmatched
  - duplicate/collision
- Produce:
  - overall match rate
  - unmatched count
  - duplicate count
  - top 10 failure reasons
  - records needing manual review
- Explain whether live API lookup, cached AddressBase-style data, or both seem to have been used.
- Do not overstate certainty.

Return:
- short summary
- quality metrics
- matched output schema
- review queue
- failure-reason analysis
- recommended remediation actions

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `short_summary`
- `quality_metrics`
- `matched_output_schema`
- `review_queue`
- `failure_reason_analysis`
- `recommended_remediation_actions`

**Reference Output Summary**

- `Reference scoring expects a 60% exact/high-confidence match rate, 2 plausible manual-review cases, 1 unmatched record, and 1 duplicate/collision pair from the 10-row batch.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Reference scoring expects a 60% exact/high-confidence match rate, 2 plausible manual-review cases, 1 unmatched record, and 1 duplicate/collision pair from the 10-row batch.",
  "method_used": [
    "Normalize punctuation, postcode spacing, street abbreviations, and PAON/SAON ordering before matching.",
    "Use OS Places or an AddressBase-backed service to resolve candidate UPRNs.",
    "Separate duplicate raw rows from ambiguous address-to-premises collisions."
  ],
  "datasets_tools_used": [
    "Synthetic benchmark batch derived from HM Land Registry Price Paid Data 2025 Bassetlaw rows",
    "MCP-Geo tools: os_places.search, os_places.by_postcode, os_places.by_uprn"
  ],
  "confidence_caveats": [
    "The dirty-address file is synthetic, but every underlying address came from a real public record.",
    "The unmatched case is driven by an intentional postcode typo and should not be forced into a likely match."
  ],
  "verification_steps": [
    "Check review-queue records manually against authoritative address lookup.",
    "Inspect the duplicate pair for 50 Canal Road to confirm whether it is a duplicate raw row rather than a second premises."
  ],
  "structured_output": {
    "qualityMetrics": {
      "totalRecords": 10,
      "exactHighConfidence": 6,
      "plausibleReview": 2,
      "unmatched": 1,
      "duplicateCollision": 1,
      "matchRatePercent": 60.0
    },
    "reviewQueue": [
      {
        "sourceId": "ADDR-003",
        "reason": "Millbridge/Mill Bridge normalization needs confirmation"
      },
      {
        "sourceId": "ADDR-006",
        "reason": "PAON/SAON order reversed for The Close / Church Lane"
      },
      {
        "sourceId": "ADDR-010",
        "reason": "Postcode typo NG22 ORU prevents safe match"
      }
    ],
    "suggestedExportFormat": "CSV matched results plus a separate CSV manual-review queue."
  },
  "short_summary": "The pack is calibrated so that the model must surface a 60% exact match rate, one unmatched typo, one duplicate raw-row pair, and two plausible manual-review address normalizations.",
  "quality_metrics": {
    "total_records": 10,
    "exact_high_confidence": 6,
    "plausible_review": 2,
    "unmatched": 1,
    "duplicate_collision": 1,
    "top_failure_reasons": [
      "postcode typo",
      "street-name normalization",
      "PAON/SAON order ambiguity",
      "duplicate raw row"
    ]
  },
  "matched_output_schema": [
    "source_id",
    "normalized_address",
    "candidate_uprn",
    "match_quality",
    "review_required",
    "failure_reason"
  ],
  "review_queue": [
    {
      "source_id": "ADDR-003",
      "priority": "medium",
      "reason": "street name normalization"
    },
    {
      "source_id": "ADDR-006",
      "priority": "medium",
      "reason": "sub-building ordering"
    },
    {
      "source_id": "ADDR-010",
      "priority": "high",
      "reason": "postcode typo / unmatched"
    }
  ],
  "failure_reason_analysis": [
    {
      "reason": "postcode typo",
      "count": 1
    },
    {
      "reason": "duplicate raw row",
      "count": 1
    },
    {
      "reason": "street-name normalization",
      "count": 1
    },
    {
      "reason": "PAON/SAON ordering",
      "count": 1
    }
  ],
  "recommended_remediation_actions": [
    "Enforce postcode validation before batch submission.",
    "Retain PAON and SAON in separate fields instead of concatenating them.",
    "Flag exact duplicate raw rows upstream before UPRN matching."
  ]
}
```

## 3. Shortest route between two premises using authoritative road network constraints (SG03)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `routing` via `os_apps.render_route_planner`

Real public sites in Retford are used for the route endpoints. The benchmark checks whether MCP-Geo uses the first-class routing surface (`os_route.get`) and either returns a grounded route or an explicit graph-readiness blocker without inventing distance or turn-by-turn details.

**Sources**
- benchmark rationale: [Northumberland County Council uses OS route optimisation](https://www.ordnancesurvey.co.uk/customers/case-studies/northumberland-county-council)
- published implementation reference: [OS Multi-modal Routing Network pgRouting getting started guide](https://docs.os.uk/os-downloads/networks/os-multi-modal-routing-network/os-mrn-getting-started-guide/pgrouting)

**Fixtures**
- No local fixture file required; the prompt uses direct public inputs.

**Comparator**

MCP-Geo passes this benchmark if it uses `os_route.get` as the authoritative path and then either returns a grounded route from a ready graph or an explicit graph blocker such as `ROUTE_GRAPH_NOT_READY`.

**Known Gaps**
- Default repo environments may not yet have a provisioned MRN routing graph, so SG03 can still block at graph readiness.
- Restriction richness depends on the loaded edge/turn/hazard tables; live closures are not yet guaranteed.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- origin: Retford Library, 17 Churchgate, Retford, DN22 6PE
- destination: Goodwin Hall, Chancery Lane, Retford, DN22 6DF
- route mode: EMERGENCY
- optional constraints: avoid known flood-risk-zone reference 167647/3 if the routing engine can represent hazards or closures

Use MCP-Geo to answer:
“What is the best route, distance, and major restrictions affecting it?”

Required steps:
- Resolve origin and destination to authoritative locations.
- Confirm the active road/network dataset and graph-readiness state.
- Compute the shortest valid route respecting known restrictions if available.
- Return:
  - route distance
  - estimated travel path
  - key turning/restriction notes
  - any uncertainty caused by unavailable live restrictions or incomplete network state
- If the network is prebuilt or cached, say so.
- If MCP-Geo cannot fully compute routing, provide the furthest grounded partial result and explain the blocker.

Return:
- concise operational answer
- structured route summary
- assumptions/limitations
- verification notes
- “Map recommended” output description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_operational_answer`
- `structured_route_summary`
- `assumptions_limitations`
- `verification_notes`
- `map_recommended_description`

**Reference Output Summary**

- `MCP-Geo now routes this prompt correctly and exposes a route solver, but the grounded answer still depends on graph readiness: return the computed emergency route when the graph is ready, otherwise return an explicit graph-state blocker instead of inventing distance or turn notes.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "MCP-Geo now routes this prompt correctly and exposes a route solver, but the grounded answer still depends on graph readiness: return the computed emergency route when the graph is ready, otherwise return an explicit graph-state blocker instead of inventing distance or turn notes.",
  "method_used": [
    "Resolve the origin and destination as named premises.",
    "Classify the request as a route-planning workflow with MCP-Geo routing guidance.",
    "Check graph readiness with os_route.descriptor, then call os_route.get with emergency profile and soft flood-zone avoidance."
  ],
  "datasets_tools_used": [
    "MCP-Geo tools: os_mcp.route_query, os_route.descriptor, os_route.get, os_places.search, os_apps.render_route_planner",
    "Routing source model: OS Multi-modal Routing Network loaded into PostGIS/pgRouting when provisioned"
  ],
  "confidence_caveats": [
    "Endpoint resolution is high confidence because the sites are public named premises.",
    "A definitive route answer depends on an active routing graph; if the graph is not ready, no distance or turn list should be invented."
  ],
  "verification_steps": [
    "Check os_route.descriptor for graph readiness and provenance before operational use.",
    "If the graph is ready, validate the returned route against temporary closures and emergency-access policy."
  ],
  "structured_output": {
    "status": "graph_not_ready",
    "origin": "Retford Library, 17 Churchgate, Retford, DN22 6PE",
    "destination": "Goodwin Hall, Chancery Lane, Retford, DN22 6DF",
    "profile": "emergency",
    "routeDistanceKm": null,
    "routePath": null,
    "blocker": "Route solver exists, but the active routing graph is not ready in this environment.",
    "suggestedExportFormat": "JSON blocker record plus GeoJSON route output once the graph is ready."
  },
  "concise_operational_answer": "Resolve the two premises, check os_route.descriptor, then either return the computed emergency route or stop with ROUTE_GRAPH_NOT_READY.",
  "structured_route_summary": {
    "route_status": "graph_not_ready",
    "recommended_tool": "os_route.get",
    "interactive_companion_tool": "os_apps.render_route_planner",
    "graph_readiness_step": "Call os_route.descriptor before relying on the route."
  },
  "assumptions_limitations": [
    "The default repo environment may not have a built MRN graph attached.",
    "Hazard and turn-restriction handling depends on the loaded graph and restriction tables."
  ],
  "verification_notes": [
    "Confirm endpoint coordinates in an authoritative address service before routing.",
    "When a route is returned, review key restrictions and any soft-avoid penalties before operational use."
  ],
  "map_recommended_description": "Map recommended: show both premises, the flood-risk-zone 167647/3 polygon, and the solved route if the graph is ready; otherwise show the endpoints plus the graph-readiness blocker."
}
```

## 4. Maintainable road segments and total length by class (SG04)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `admin_lookup.find_by_name`

Rutland County Council publishes a current road-length transparency page with class totals, and Phase 2 evidence shows GeoPlace positioning this workload as a replacement for manual returns.

**Sources**
- published comparator: [Highway authority road lengths](https://www.rutland.gov.uk/roads-transport-parking/roads-pavements/highway-maintenance/highway-authority-road-lengths)
- benchmark rationale: [GeoPlace explores replacing manual highway returns](https://www.geoplace.co.uk/addresses-streets/location-data/street-data)

**Fixtures**
- No local fixture file required; the prompt uses direct public inputs.

**Comparator**

Published comparator for Rutland’s current highways maintenance transparency report: A roads 77 km, B/C roads 221 km, U roads 222 km, total roads 520 km. The benchmark expects the answer to treat those as published control totals unless it has a live segment-level run.

**Known Gaps**
- Segment-level maintainability aggregation depends on NGD road-maintenance collections and an OS key.
- The published Rutland comparator aggregates B and C roads together, so separate B/C totals need a live segment run.
- This environment does not have a live OS key, so published comparator totals are the ground truth for validation.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given area: Rutland County Council
Answer:
“Which road segments in this area are publicly maintainable, and what is the total length by class?”

Required steps:
- Resolve the requested geography.
- Identify relevant road segments and their maintainability/classification attributes.
- Aggregate total length by class/category.
- Flag anomalies, gaps, or conflicting classifications.
- If applicable, identify which segments likely need custodian review.
- Make clear whether the answer is suitable for operational insight only or close to statutory reporting quality.

Return:
- short answer
- summary table by class
- anomaly table
- confidence/caveats
- suggested follow-up checks

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `short_answer`
- `summary_table_by_class`
- `anomaly_table`
- `suggested_follow_up_checks`

**Reference Output Summary**

- `Rutland is the benchmark area. The published comparator totals are 77 km of A roads, 221 km of B/C roads, 222 km of U roads, and 520 km of total maintained roads.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Rutland is the benchmark area. The published comparator totals are 77 km of A roads, 221 km of B/C roads, 222 km of U roads, and 520 km of total maintained roads.",
  "method_used": [
    "Resolve Rutland as the target authority.",
    "Use NGD road-maintenance collections for a live run if available.",
    "Compare any live total against Rutland\u2019s published comparator figures before treating it as statutory-quality output."
  ],
  "datasets_tools_used": [
    "Rutland County Council road-length transparency page",
    "MCP-Geo tools: admin_lookup.find_by_name, os_features.collections, os_features.query"
  ],
  "confidence_caveats": [
    "The published totals are authoritative comparators for this benchmark.",
    "Without a live NGD segment run, MCP-Geo should treat the result as comparator-led rather than generated."
  ],
  "verification_steps": [
    "Check live NGD collection availability for trn-rami-maintenance* and any road-class fields.",
    "Reconcile any discrepancy against the latest authority publication before using it operationally.",
    "If separate B and C totals are needed, derive them from segment-level data rather than the transparency-page aggregate."
  ],
  "structured_output": {
    "lengthByClassKm": [
      {
        "roadClass": "A",
        "lengthKm": 77.0
      },
      {
        "roadClass": "B/C",
        "lengthKm": 221.0
      },
      {
        "roadClass": "U",
        "lengthKm": 222.0
      },
      {
        "roadClass": "Total roads",
        "lengthKm": 520.0
      }
    ],
    "suggestedExportFormat": "CSV by published road class totals, plus segment GeoJSON if a live NGD roll-up is run."
  },
  "short_answer": "Rutland\u2019s published maintained-road comparator totals are ready-made benchmark control values.",
  "summary_table_by_class": [
    {
      "road_class": "A",
      "length_km": 77.0
    },
    {
      "road_class": "B/C",
      "length_km": 221.0
    },
    {
      "road_class": "U",
      "length_km": 222.0
    },
    {
      "road_class": "Total roads",
      "length_km": 520.0
    }
  ],
  "anomaly_table": [
    {
      "issue": "No live segment roll-up in benchmark environment",
      "impact": "Comparator-led only"
    },
    {
      "issue": "Published comparator merges B and C roads",
      "impact": "Separate B/C analysis needs live segment data"
    }
  ],
  "suggested_follow_up_checks": [
    "Confirm whether the authority publication date matches the benchmark year being tested.",
    "Sample-test a handful of segments for class and maintainability coding if a live NGD run becomes available."
  ]
}
```

## 5. Planning site constraints and evidence summary (SG05)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

Goodwin Hall is a real public site from the Bassetlaw asset register, and open planning.data layers show it intersects both flood-risk zones and the Retford conservation area.

**Sources**
- site source: [Bassetlaw open land and building assets register](https://data.bassetlaw.gov.uk/land-building-assets/)
- constraint layer: [Planning Data flood-risk-zone dataset](https://www.planning.data.gov.uk/dataset/flood-risk-zone)
- constraint layer: [Planning Data conservation-area dataset](https://www.planning.data.gov.uk/dataset/conservation-area)

**Fixtures**
- No local fixture file required; the prompt uses direct public inputs.

**Comparator**

Published comparator: the benchmark site intersects flood-risk-zone references 406550/2 (level 2), 167647/3 (level 3), and the Retford conservation area (reference 18 / entity 44014417) when checked against open planning.data layers.

**Known Gaps**
- The repo does not yet expose planning.data or local-plan policy layers as MCP-Geo tools.
- An answer should therefore name missing layers rather than pretending local policy evidence is complete.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given planning site geometry: Goodwin Hall, Chancery Lane, Retford, DN22 6DF
Answer:
“For this site, which spatial constraints and policy-relevant layers intersect it, and what is the evidence summary?”

Required steps:
- Resolve the site precisely.
- Discover the relevant authoritative spatial layers available through MCP-Geo.
- Run intersection / within-distance / adjacency checks as appropriate.
- Produce an evidence summary that distinguishes:
  - direct intersections
  - nearby but non-intersecting constraints
  - missing or unavailable datasets
- Avoid making planning judgements; provide geospatial evidence only.
- Where a layer is unavailable, name the gap rather than inferring the result.

Return:
- concise site summary
- intersecting constraints table
- nearby constraints table
- missing-data note
- confidence statement
- “Map recommended” description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_site_summary`
- `intersecting_constraints_table`
- `nearby_constraints_table`
- `missing_data_note`
- `confidence_statement`
- `map_recommended_description`

**Reference Output Summary**

- `Goodwin Hall should be treated as a constrained site: the benchmark evidence shows direct intersection with fluvial flood-risk zones 2 and 3 plus the Retford conservation area.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Goodwin Hall should be treated as a constrained site: the benchmark evidence shows direct intersection with fluvial flood-risk zones 2 and 3 plus the Retford conservation area.",
  "method_used": [
    "Resolve Goodwin Hall as the site reference.",
    "Check open planning.data constraint layers for direct point/geometry intersection.",
    "Name the planning layers that are not available through MCP-Geo today."
  ],
  "datasets_tools_used": [
    "Bassetlaw land and building assets register",
    "planning.data.gov.uk flood-risk-zone and conservation-area datasets",
    "MCP-Geo tools: os_places.search, admin_lookup.containing_areas, os_features.collections"
  ],
  "confidence_caveats": [
    "Constraint intersections are strong because they come from open planning.data geometries.",
    "Local policy, heritage-setting, and nearby-constraint analysis remains incomplete without additional layers."
  ],
  "verification_steps": [
    "Resolve the exact site polygon or building footprint before making any planning submission decision.",
    "Check the local plan, heritage setting, and local land charges systems for non-open constraints."
  ],
  "structured_output": {
    "intersections": [
      {
        "dataset": "flood-risk-zone",
        "reference": "406550/2",
        "level": "2"
      },
      {
        "dataset": "flood-risk-zone",
        "reference": "167647/3",
        "level": "3"
      },
      {
        "dataset": "conservation-area",
        "reference": "18",
        "name": "Retford"
      }
    ],
    "suggestedExportFormat": "CSV constraint register plus GeoJSON site and intersecting constraints."
  },
  "concise_site_summary": "Goodwin Hall is inside both level-2 and level-3 fluvial flood-risk zones and inside the Retford conservation area.",
  "intersecting_constraints_table": [
    {
      "dataset": "flood-risk-zone",
      "reference": "406550/2",
      "detail": "Fluvial Models, level 2"
    },
    {
      "dataset": "flood-risk-zone",
      "reference": "167647/3",
      "detail": "Fluvial Models, level 3"
    },
    {
      "dataset": "conservation-area",
      "reference": "18",
      "detail": "Retford conservation area"
    }
  ],
  "nearby_constraints_table": [
    {
      "dataset": "listed-building",
      "detail": "No direct site-centroid intersection in sampled open layers"
    },
    {
      "dataset": "tree-preservation-zone",
      "detail": "No direct site-centroid intersection in sampled open layers"
    }
  ],
  "missing_data_note": "Local plan policies, setting analysis, land-charges constraints, and any local flood-mitigation evidence are not in the supplied benchmark pack.",
  "confidence_statement": "Moderate to high: direct open-layer intersections are strong, but the site polygon is still a proxy from the asset register rather than a planning-application boundary.",
  "map_recommended_description": "Map recommended: show Goodwin Hall, both flood-risk-zone polygons, and the Retford conservation-area outline on the same view."
}
```

## 6. Council asset register linked to UPRNs and overlaid with flood risk (SG06)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.by_uprn`

This uses a real Bassetlaw asset-register subset with published UPRNs, coordinates, and tenure fields, overlaid against published planning.data flood-risk-zone geometry.

**Sources**
- asset source: [Bassetlaw open land and building assets register](https://data.bassetlaw.gov.uk/land-building-assets/)
- flood overlay source: [Planning Data flood-risk-zone dataset](https://www.planning.data.gov.uk/dataset/flood-risk-zone)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_06_bassetlaw_assets_subset.csv`

**Comparator**

Published comparator for the selected seven-asset subset: all seven assets already carry real UPRNs; four intersect the sampled flood-risk-zone point checks; three more sit in the same operational cluster and should remain a manual review queue unless a distance-based overlay is added.

**Known Gaps**
- The repo does not yet expose planning.data as a first-class MCP-Geo source.
- Near-risk status in this benchmark is an explicit review queue, not a confirmed distance calculation.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- asset register file: data/benchmarking/stakeholder_eval/fixtures/scenario_06_bassetlaw_assets_subset.csv
- flood extent / risk layer: planning.data flood-risk-zone references 402042/2, 406550/2, and 167647/3 around Retford

Use MCP-Geo to answer:
“Which assets can be linked to authoritative premises identifiers, and which of those are within or near flood-risk areas?”

Required steps:
- Inspect the asset register and identify address/location fields.
- Match each asset to a UPRN or authoritative location where possible.
- Report unmatched or ambiguous assets separately.
- Overlay matched assets with the flood-risk geometry.
- Summarise:
  - matched assets
  - unmatched assets
  - assets in-risk
  - assets near-risk
- State confidence per asset or per match group.

Return:
- executive summary
- matched asset table
- unmatched asset table
- flood-risk overlay summary
- confidence/caveats
- recommended exports

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `executive_summary`
- `matched_asset_table`
- `unmatched_asset_table`
- `flood_risk_overlay_summary`
- `recommended_exports`

**Reference Output Summary**

- `All 7 benchmark assets are already keyed by real UPRN. 4 assets are confirmed in-risk from point-on-zone checks, 0 are unmatched, and 3 remain review candidates rather than confirmed near-risk assets.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "All 7 benchmark assets are already keyed by real UPRN. 4 assets are confirmed in-risk from point-on-zone checks, 0 are unmatched, and 3 remain review candidates rather than confirmed near-risk assets.",
  "method_used": [
    "Read UPRN, address, and coordinate fields directly from the asset register.",
    "Use the supplied Retford flood-risk-zone references for overlay.",
    "Keep non-intersecting assets in a review queue unless a distance rule is supplied."
  ],
  "datasets_tools_used": [
    "Bassetlaw asset register subset",
    "planning.data.gov.uk flood-risk-zone references 402042/2, 406550/2, 167647/3",
    "MCP-Geo tools: os_places.by_uprn, admin_lookup.containing_areas"
  ],
  "confidence_caveats": [
    "UPRN linkage is high confidence because the published asset register supplies the UPRN directly.",
    "In-risk classification is strong for the four intersecting points.",
    "Near-risk is intentionally conservative: the benchmark expects review-candidate labelling, not guessed distance classes."
  ],
  "verification_steps": [
    "Confirm any export uses the latest flood-zone release before publication.",
    "If near-risk assets matter operationally, run a true distance-to-zone calculation instead of point-only checks."
  ],
  "structured_output": {
    "matchedAssets": 7,
    "unmatchedAssets": 0,
    "confirmedInRiskAssets": 4,
    "reviewQueueAssets": 3
  },
  "executive_summary": "Seven assets matched cleanly by UPRN; four sit inside sampled flood zones and three require proximity review rather than being labelled safe.",
  "matched_asset_table": [
    {
      "uprn": "100032031194",
      "asset": "Nottinghamshire County Council land",
      "postcode": "DN22 6DG",
      "risk_status": "in_risk"
    },
    {
      "uprn": "100032031210",
      "asset": "Retford Library 17",
      "postcode": "DN22 6PE",
      "risk_status": "review_candidate"
    },
    {
      "uprn": "100032031287",
      "asset": "Goodwin Hall",
      "postcode": "DN22 6DF",
      "risk_status": "in_risk"
    },
    {
      "uprn": "10023266359",
      "asset": "Retford Shopmobility",
      "postcode": "DN22 6EY",
      "risk_status": "review_candidate"
    },
    {
      "uprn": "10023266361",
      "asset": "Public Car Park",
      "postcode": "DN22 6EY",
      "risk_status": "in_risk"
    },
    {
      "uprn": "10023269092",
      "asset": "North Public Car Park",
      "postcode": "DN22 6EY",
      "risk_status": "review_candidate"
    },
    {
      "uprn": "10023270715",
      "asset": "Pavillion at Kings Park",
      "postcode": "DN22 6EY",
      "risk_status": "in_risk"
    }
  ],
  "unmatched_asset_table": [],
  "flood_risk_overlay_summary": {
    "confirmed_in_risk_assets": 4,
    "review_queue_assets": 3,
    "intersecting_zone_references": [
      "402042/2",
      "406550/2",
      "167647/3"
    ]
  },
  "recommended_exports": [
    "CSV asset risk register",
    "GeoJSON or map layer if coordinates are included in the live run"
  ]
}
```

## 7. Flood appraisal: count properties at risk and generate a verification plan (SG07)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

The flood extent is public and real; the property list is a curated sample of real Retford price-paid addresses plus explicit negative controls. This lets the benchmark score uncertainty handling and verification planning.

**Sources**
- property sample source: [HM Land Registry Price Paid Data downloads](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- flood extent source: [Planning Data flood-risk-zone dataset](https://www.planning.data.gov.uk/dataset/flood-risk-zone)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_07_property_sample.csv`

**Comparator**

Comparator baseline for the sample file: 5 properties are high-confidence affected from postcode/zone evidence, 2 are outside-zone negative controls, and the benchmark should prioritize duplicate/leasehold and wharf-side cases for site verification.

**Known Gaps**
- The property list is a sample, not a full dwelling count for Retford.
- Some records rely on postcode-centroid evidence rather than building footprints, so verification remains mandatory.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- flood extent or risk geometry: planning.data flood-risk-zone references 402042/2 and 167647/3 around Retford
- target area: data/benchmarking/stakeholder_eval/fixtures/scenario_07_property_sample.csv

Use MCP-Geo to answer:
“How many properties are likely at risk, what categories do they fall into, and which cases most need field verification?”

Required steps:
- Resolve the flood geometry and target geography.
- Identify affected premises/buildings/UPRNs.
- Count affected properties by available classification.
- Separate:
  - high-confidence affected properties
  - borderline/uncertain cases
  - records that likely need manual/site verification
- Explain the basis of uncertainty.
- Produce a prioritised verification list rather than pretending the model can replace field validation.

Return:
- headline counts
- classification summary
- verification-priority table
- uncertainty explanation
- “Map recommended” description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `headline_counts`
- `classification_summary`
- `verification_priority_table`
- `uncertainty_explanation`
- `map_recommended_description`

**Reference Output Summary**

- `Within the benchmark sample, 5 properties are high-confidence at-risk cases and 2 are negative-control records outside the zone. The answer should explicitly keep field verification in scope.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Within the benchmark sample, 5 properties are high-confidence at-risk cases and 2 are negative-control records outside the zone. The answer should explicitly keep field verification in scope.",
  "method_used": [
    "Use the supplied flood-zone references as the risk geometry.",
    "Treat DN22 6EN and DN22 6FE sample addresses as affected because their postcode centroids intersect the published zones in benchmark prep.",
    "Keep outside-zone controls separate and prioritize wharf-side and duplicate/leasehold properties for verification."
  ],
  "datasets_tools_used": [
    "HM Land Registry Price Paid sample properties",
    "planning.data.gov.uk flood-risk-zone references 402042/2 and 167647/3",
    "MCP-Geo tools: os_places.search, os_places.by_uprn, admin_lookup.containing_areas"
  ],
  "confidence_caveats": [
    "This is a sampled property list rather than a full property inventory.",
    "Several properties are classified from postcode-level evidence and should be verified on the ground or against building footprints."
  ],
  "verification_steps": [
    "Verify 6 Mill Bridge Close because duplicate leasehold/freehold transaction records can distort property counts.",
    "Check Navigation Lodge and other wharf-side premises first because zone-3 exposure is highest there.",
    "Use building footprints or authoritative address-to-UPRN resolution to confirm the exact number of premises at each postcode."
  ],
  "structured_output": {
    "headlineCounts": {
      "highConfidenceAffected": 5,
      "borderline": 0,
      "negativeControls": 2
    },
    "suggestedExportFormat": "CSV verification queue plus GeoJSON points for the sampled properties."
  },
  "headline_counts": {
    "high_confidence_affected": 5,
    "borderline_uncertain": 0,
    "manual_verification": 3
  },
  "classification_summary": [
    {
      "class": "zone_3_or_core_floodplain",
      "properties": 2
    },
    {
      "class": "zone_2_or_adjacent_floodplain",
      "properties": 3
    },
    {
      "class": "outside_sampled_zone",
      "properties": 2
    }
  ],
  "verification_priority_table": [
    {
      "property": "Navigation Lodge, Wharf Road, Retford DN22 6EN",
      "priority": "high",
      "reason": "wharf-side / zone-3 exposure"
    },
    {
      "property": "6 Mill Bridge Close, Retford DN22 6FE",
      "priority": "high",
      "reason": "duplicate transaction records / exact-premises confirmation"
    },
    {
      "property": "115 Mill Bridge Close, Retford DN22 6FE",
      "priority": "medium",
      "reason": "postcode-centroid rather than footprint evidence"
    }
  ],
  "uncertainty_explanation": "The benchmark uses a sampled property list and postcode-derived checks, so it is deliberately designed to reward honest uncertainty handling instead of false precision.",
  "map_recommended_description": "Map recommended: show the sampled addresses, flood-zone 2/3 polygons, and a symbol distinction between high-confidence properties and negative controls."
}
```

## 8. Normalise fragmented housing development sources and summarise by polling district or ward (SG08)

- Example mode: `synthetic`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `admin_lookup.find_by_name`

North Yorkshire’s 2024 Boundary Commission review explicitly states that there is no single source for housing development data and that the GIS team had to reconcile points, polygons, planning inputs, and local plan allocations. The benchmark pack uses a validated synthetic mini-pack modelled on that workflow.

**Sources**
- workflow rationale: [North Yorkshire Boundary Commission Review GIS Processes 2024](https://edemocracy.northyorks.gov.uk/documents/g9198/Public%20reports%20pack%2009th-Jul-2024%2011.00%20Executive.pdf?T=10)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_08_housing_allocations.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_08_planning_permissions.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_08_site_promoters.csv`

**Comparator**

Comparator baseline is synthetic but validated against the published North Yorkshire workflow: 1 duplicate development family (Abbey Quarter), 1 uncertain promoter-only record (Scarborough North Infill), and geography totals of Selby West 120 confirmed / 40 permission-linked, Cayton 73, Ripon South 30, Scarborough North 30 uncertain.

**Known Gaps**
- The mini-pack is synthetic because the former-district raw files are not published as a reusable benchmark bundle.
- Geometry assignment is therefore benchmark logic, not a live authoritative planning register.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given these fragmented housing-development inputs:
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_housing_allocations.csv
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_planning_permissions.csv
- data/benchmarking/stakeholder_eval/fixtures/scenario_08_site_promoters.csv

Use MCP-Geo to answer:
“What is the best consolidated view of future housing development by polling district, ward, or other requested geography?”

Required steps:
- Inspect all inputs and identify overlaps, duplicates, and inconsistent formats.
- Normalise site/address/location references.
- Resolve each development to a mappable geometry or best-available point.
- Assign each development to the requested boundaries.
- Summarise counts and expected impact by geography.
- Clearly separate confirmed records from uncertain or duplicate candidate records.
- Describe the reconciliation logic.

Return:
- consolidated summary
- geography-level totals table
- duplicate/uncertain records table
- method note
- confidence statement
- suggested export schema

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `consolidated_summary`
- `geography_level_totals_table`
- `duplicate_uncertain_records_table`
- `method_note`
- `confidence_statement`
- `suggested_export_schema`

**Reference Output Summary**

- `The benchmark pack is designed so the model must consolidate three fragmented sources into 3 confirmed ward totals plus 1 uncertain promoter-only ward total.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The benchmark pack is designed so the model must consolidate three fragmented sources into 3 confirmed ward totals plus 1 uncertain promoter-only ward total.",
  "method_used": [
    "Normalize site names across the three files.",
    "Collapse Abbey Quarter duplicates into one development family with linked allocation and permission records.",
    "Keep Scarborough North Infill as uncertain because it appears only in the promoter file."
  ],
  "datasets_tools_used": [
    "Synthetic North Yorkshire-style housing-fragmentation fixtures",
    "Published benchmark rationale from North Yorkshire Boundary Commission GIS methodology",
    "MCP-Geo tools: admin_lookup.find_by_name, admin_lookup.containing_areas, ons_geo.by_postcode"
  ],
  "confidence_caveats": [
    "All three input files are synthetic representations of a published workflow, not the raw North Yorkshire operational files.",
    "Geography assignment is therefore a benchmark truth table rather than a live planning system result."
  ],
  "verification_steps": [
    "Cross-check duplicate development families with planning-policy officers before publication.",
    "Require a fresh geometry or planning reference for promoter-only records before they are counted as confirmed supply."
  ],
  "structured_output": {
    "wardTotals": [
      {
        "ward": "Selby West",
        "confirmedUnits": 120,
        "linkedPermissionUnits": 40,
        "uncertainUnits": 0
      },
      {
        "ward": "Cayton",
        "confirmedUnits": 48,
        "linkedPermissionUnits": 25,
        "uncertainUnits": 0
      },
      {
        "ward": "Ripon South",
        "confirmedUnits": 30,
        "linkedPermissionUnits": 25,
        "uncertainUnits": 0
      },
      {
        "ward": "Scarborough North",
        "confirmedUnits": 0,
        "linkedPermissionUnits": 0,
        "uncertainUnits": 30
      }
    ]
  },
  "consolidated_summary": "Abbey Quarter and Cayton East Extension appear in multiple files and need family-level consolidation; Scarborough North Infill remains promoter-only and uncertain.",
  "geography_level_totals_table": [
    {
      "geography": "Selby West",
      "confirmed_units": 120,
      "linked_permission_units": 40,
      "uncertain_units": 0
    },
    {
      "geography": "Cayton",
      "confirmed_units": 48,
      "linked_permission_units": 25,
      "uncertain_units": 0
    },
    {
      "geography": "Ripon South",
      "confirmed_units": 30,
      "linked_permission_units": 25,
      "uncertain_units": 0
    },
    {
      "geography": "Scarborough North",
      "confirmed_units": 0,
      "linked_permission_units": 0,
      "uncertain_units": 30
    }
  ],
  "duplicate_uncertain_records_table": [
    {
      "site_name": "Abbey Quarter",
      "issue": "duplicate family across allocation, permission, and promoter sources"
    },
    {
      "site_name": "Scarborough North Infill",
      "issue": "promoter-only / uncertain geometry"
    }
  ],
  "method_note": "This benchmark follows the published North Yorkshire workflow: points and polygons are harmonized, then counted by polling district or ward using GIS logic.",
  "confidence_statement": "Moderate: the reconciliation logic is realistic and source-backed, but the actual mini-pack is synthetic.",
  "suggested_export_schema": [
    "canonical_site_id",
    "source_refs",
    "ward",
    "polling_district",
    "confirmed_units",
    "uncertain_units",
    "confidence"
  ]
}
```

## 9. BDUK-style premises status lookup with explanation of missing/new-build/epoch issues (SG09)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.by_uprn`

The benchmark premise is a real UPRN from the Bassetlaw asset register that is absent from the September 2024 East Midlands BDUK release. That makes it a strong test of evidence-ranked missing-premise reasoning.

**Sources**
- dataset source: [Premises in BDUK plans (March 2025, England and Wales)](https://www.gov.uk/government/publications/premises-in-bduk-plans-england-and-wales)
- missing-premise reasoning: [User guide and technical note for premises in BDUK plans](https://www.gov.uk/government/publications/premises-in-bduk-plans-england-and-wales/user-guide-and-technical-note-for-premises-in-bduk-plans)
- premise source: [Bassetlaw open land and building assets register](https://data.bassetlaw.gov.uk/land-building-assets/)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_09_bduk_subset.csv`

**Comparator**

Comparator outcome: UPRN 10023266361 is absent from the East Midlands BDUK release, and the strongest evidence-backed explanation is non-target classification because the same public register labels it as a car park. The benchmark should still mention the BDUK guide’s epoch/new-build caveat, but rank it below the classification explanation.

**Known Gaps**
- BDUK is a supplied dataset, not a native MCP-Geo tool family.
- The benchmark expects evidence-ranked reasoning about absence, not fabricated status values.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- premise reference: UPRN 10023266361
- premises-status dataset: data/benchmarking/stakeholder_eval/fixtures/scenario_09_bduk_subset.csv with the full East Midlands September 2024 BDUK release as the authoritative backing dataset

Use MCP-Geo to answer:
“What is this premises’ current status in the dataset, and if it is missing or unclear, why?”

Required steps:
- Resolve the supplied premise reference to the best authoritative identifier.
- Look up the premise in the supplied status dataset.
- If missing, test grounded explanations such as:
  - new build not yet present in the source epoch
  - demolished / non-target classification
  - unmatched identifier
  - dataset coverage gap
- Do not guess; rank explanations by evidence.
- State what additional data refresh or validation step would confirm the answer.

Return:
- short user-facing answer
- structured premise status
- explanation of missing/uncertain cases
- confidence/caveats
- next verification step

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `short_user_facing_answer`
- `structured_premise_status`
- `explanation_of_missing_uncertain_cases`
- `next_verification_step`

**Reference Output Summary**

- `UPRN 10023266361 is missing from the supplied BDUK release. The strongest explanation is that it is a non-target public car park rather than a dwelling or business premises in BDUK’s recognised premises base.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "UPRN 10023266361 is missing from the supplied BDUK release. The strongest explanation is that it is a non-target public car park rather than a dwelling or business premises in BDUK\u2019s recognised premises base.",
  "method_used": [
    "Resolve the UPRN against the supplied benchmark sources.",
    "Check whether the UPRN appears in the East Midlands BDUK release.",
    "Rank missing-case explanations using the BDUK guide and the public asset-register classification."
  ],
  "datasets_tools_used": [
    "Bassetlaw asset register",
    "BDUK East Midlands September 2024 release",
    "BDUK user guide and technical note",
    "MCP-Geo tools: os_places.by_uprn, ons_geo.by_uprn"
  ],
  "confidence_caveats": [
    "The UPRN is real and the absence is real.",
    "The reason is still inferential until the UPRN is checked against AddressBase class or a newer BDUK release."
  ],
  "verification_steps": [
    "Confirm the UPRN\u2019s current AddressBase class or OS Places record.",
    "Check the next BDUK release in case the premise treatment has changed."
  ],
  "structured_output": {
    "premiseStatus": "missing",
    "rankedExplanations": [
      {
        "reason": "non_target_or_non_postal_premises",
        "confidence": "high"
      },
      {
        "reason": "dataset_coverage_gap",
        "confidence": "medium"
      },
      {
        "reason": "new_build_epoch_lag",
        "confidence": "low"
      },
      {
        "reason": "demolished_or_derelict",
        "confidence": "low"
      }
    ],
    "suggestedExportFormat": "JSON status record for the premise plus CSV ranked-explanations table."
  },
  "short_user_facing_answer": "This UPRN is not in the supplied BDUK file. Treat it as a likely non-target premises until AddressBase classification proves otherwise.",
  "structured_premise_status": {
    "uprn": "10023266361",
    "dataset_status": "not_found",
    "best_supported_reason": "non_target_or_non_postal_premises"
  },
  "explanation_of_missing_uncertain_cases": [
    "The public source labels the UPRN as a public car park, which is stronger evidence than a generic epoch-lag explanation.",
    "The BDUK guide still requires the answer to mention other grounded possibilities such as new-build lag or demolished/derelict classifications."
  ],
  "next_verification_step": "Resolve the UPRN against the latest OS-backed premises classification and compare it with the next BDUK release."
}
```

## 10. Link council-tax-like and land-registry-like property datasets via UPRN and quantify unmatched records (SG10)

- Example mode: `mixed`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

The council-tax-like file is synthetic but derived from real Bassetlaw address strings, and the land-registry-like file is a direct Price Paid extract. This mirrors the public sector property-platform problem without inventing the underlying land-registry rows.

**Sources**
- dataset B source: [HM Land Registry Price Paid Data downloads](https://www.gov.uk/government/statistical-data-sets/price-paid-data-downloads)
- property-platform rationale: [Welsh Revenue Authority annual report 2021 to 2022](https://www.gov.wales/welsh-revenue-authority-annual-report-and-accounts-2021-2022-html)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_10_council_tax_like.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_10_price_paid_subset.csv`

**Comparator**

Reference benchmark outcome: 5 exact matches, 2 plausible review matches, and 1 unmatched council-tax-like row. The most important mismatch reason is address-hierarchy handling for Canalside Wharf, 6 Wharf Road.

**Known Gaps**
- The council-tax-like file is synthetic because there is no reusable open council-tax benchmark file with equivalent address detail.
- Exact UPRN alignment needs live address tooling; without it, the benchmark rewards cautious hierarchy handling rather than overclaiming match rates.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- dataset A: data/benchmarking/stakeholder_eval/fixtures/scenario_10_council_tax_like.csv
- dataset B: data/benchmarking/stakeholder_eval/fixtures/scenario_10_price_paid_subset.csv

Use MCP-Geo to answer:
“How well can these datasets be aligned through authoritative property identifiers, and what remains unmatched?”

Required steps:
- Inspect both datasets and identify candidate join fields.
- Resolve addresses/locations to authoritative UPRNs where possible.
- Join the datasets through UPRN or best grounded fallback logic.
- Quantify:
  - exact matches
  - plausible matches needing review
  - unmatched records
  - likely causes of mismatch
- Where hierarchy matters, note parent/child premises issues.
- Avoid overstating completeness.

Return:
- summary of join success
- matched/unmatched metrics
- mismatch-reason table
- recommended remediation actions
- structured output schema

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `summary_of_join_success`
- `matched_unmatched_metrics`
- `mismatch_reason_table`
- `recommended_remediation_actions`
- `structured_output_schema`

**Reference Output Summary**

- `The benchmark is calibrated for 5 exact matches, 2 plausible review matches, and 1 unmatched council-tax-like record after identifier reconciliation.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The benchmark is calibrated for 5 exact matches, 2 plausible review matches, and 1 unmatched council-tax-like record after identifier reconciliation.",
  "method_used": [
    "Normalize both datasets to comparable address tokens.",
    "Use UPRN lookup where possible; otherwise fall back to grounded address matching with hierarchy checks.",
    "Separate exact joins from plausible but reviewable sub-building or legacy-address cases."
  ],
  "datasets_tools_used": [
    "Synthetic council-tax-like Bassetlaw address file",
    "HM Land Registry Price Paid subset",
    "MCP-Geo tools: os_places.search, os_places.by_postcode, os_places.by_uprn"
  ],
  "confidence_caveats": [
    "Dataset A is synthetic; dataset B is real.",
    "Canalside Wharf needs hierarchy-aware handling because PAON/SAON order differs across systems."
  ],
  "verification_steps": [
    "Resolve each review-queue record to a UPRN before loading it into a production join table.",
    "Split PAON and SAON explicitly in both datasets to reduce future mismatch rates."
  ],
  "structured_output": {
    "matchMetrics": {
      "exact": 5,
      "plausibleReview": 2,
      "unmatched": 1
    },
    "suggestedExportFormat": "CSV joined output plus CSV review queue for unresolved records."
  },
  "summary_of_join_success": "Most of the curated Bassetlaw records align cleanly, but one hierarchy case and one postcode-normalization problem still need review.",
  "matched_unmatched_metrics": {
    "exact_matches": 5,
    "plausible_matches_needing_review": 2,
    "unmatched_records": 1
  },
  "mismatch_reason_table": [
    {
      "reason": "PAON/SAON ordering mismatch",
      "records": 1
    },
    {
      "reason": "postcode normalization or typo",
      "records": 1
    },
    {
      "reason": "dataset coverage gap",
      "records": 1
    }
  ],
  "recommended_remediation_actions": [
    "Keep sub-building names in dedicated fields in both systems.",
    "Validate postcodes before attempting UPRN alignment.",
    "Store authoritative UPRNs once resolved to prevent repeated fuzzy matching."
  ],
  "structured_output_schema": [
    "record_id",
    "normalized_address",
    "candidate_uprn",
    "match_quality",
    "review_reason",
    "source_dataset"
  ]
}
```

## 11. Authoritative postcode result set with cache-freshness guidance (SG11)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_mcp.route_query`

Phase 1 evidence showed GOV.UK's `locations-api` as a mature OS Places pattern: it answers postcode lookups with cached PostgreSQL records and explicit refresh rules. This benchmark turns that architecture into a concrete prompt using a public postcode.

**Sources**
- published architecture reference: [GOV.UK locations-api](https://docs.publishing.service.gov.uk/repos/locations-api.html)
- published comparator: [How postcodes are added, cached and updated](https://docs.publishing.service.gov.uk/repos/locations-api/postcodes.html)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_11_postcode_sample.csv`

**Comparator**

Published GOV.UK comparator: postcode records are cached when first requested and refreshed when they have not been updated in the previous 30 days. The benchmark expects MCP-Geo to separate the live postcode result from that service-layer cache policy.

**Known Gaps**
- MCP-Geo exposes the postcode lookup but not GOV.UK's internal PostgreSQL cache metadata or refresh workers.
- Any cache policy discussion is therefore comparator-led rather than observed live from MCP-Geo.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given postcode sample file: data/benchmarking/stakeholder_eval/fixtures/scenario_11_postcode_sample.csv

Use MCP-Geo to answer:
"For postcode DN22 6PE, what is the authoritative result set, and how should a cache-backed service keep it fresh?"

Required steps:
- Resolve the postcode to the authoritative OS-backed result set.
- State how many premises the postcode resolves to.
- Distinguish the authoritative address result from any service-layer caching plan.
- Explain how a cache-backed implementation should treat freshness, stale records, and refresh triggers.
- Do not invent internal service metrics that MCP-Geo cannot observe directly.

Return:
- concise operational answer
- postcode result table
- cache freshness plan
- stale-risk note
- verification note
- structured output schema

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_operational_answer`
- `postcode_result_table`
- `cache_freshness_plan`
- `stale_risk_note`
- `verification_note`
- `structured_output_schema`

**Reference Output Summary**

- `DN22 6PE resolves to a single authoritative premises record in the current OS Places result set: Nottinghamshire County Council, Retford Library, 17 Churchgate, Retford, DN22 6PE. MCP-Geo can return that live result, but the cache-freshness rule comes from GOV.UK's published service pattern rather than from MCP-Geo runtime telemetry.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "DN22 6PE resolves to a single authoritative premises record in the current OS Places result set: Nottinghamshire County Council, Retford Library, 17 Churchgate, Retford, DN22 6PE. MCP-Geo can return that live result, but the cache-freshness rule comes from GOV.UK's published service pattern rather than from MCP-Geo runtime telemetry.",
  "method_used": [
    "Call os_places.by_postcode for DN22 6PE to obtain the current authoritative result set.",
    "Treat cache freshness as a separate service-operations concern and compare against GOV.UK's published locations-api rule set.",
    "Do not claim MCP-Geo can inspect the downstream PostgreSQL cache unless such telemetry is explicitly exposed."
  ],
  "datasets_tools_used": [
    "MCP-Geo tools: os_mcp.route_query, os_places.by_postcode",
    "Published comparator: GOV.UK locations-api postcode cache and refresh documentation"
  ],
  "confidence_caveats": [
    "High confidence on the live postcode result because it comes directly from OS Places.",
    "Cache-freshness guidance is comparator-led: MCP-Geo does not expose live cache age, refresh-worker status, or cache hit ratios."
  ],
  "verification_steps": [
    "Re-run os_places.by_postcode for DN22 6PE and confirm the premises count remains one.",
    "If this pattern is implemented in a service, log cache age and last-refresh timestamps separately from the authoritative result payload.",
    "Compare any local refresh schedule against GOV.UK's published 30-day refresh rule before treating it as aligned."
  ],
  "structured_output": {
    "postcode": "DN22 6PE",
    "resultCount": 1,
    "addresses": [
      {
        "uprn": "100032031210",
        "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE",
        "classification": "Library"
      }
    ],
    "cachePolicyComparator": {
      "publishedRule": "refresh cached postcode records after 30 days if not updated sooner",
      "observedByMcpGeo": false
    },
    "suggestedExportFormat": "JSON response plus CSV postcode-address extract."
  },
  "concise_operational_answer": "DN22 6PE currently resolves to one authoritative record. A cache-backed service should keep the live result separate from the published 30-day refresh policy.",
  "postcode_result_table": [
    {
      "postcode": "DN22 6PE",
      "uprn": "100032031210",
      "address": "NOTTINGHAMSHIRE COUNTY COUNCIL, RETFORD LIBRARY, 17, CHURCHGATE, RETFORD, DN22 6PE",
      "classification": "Library"
    }
  ],
  "cache_freshness_plan": [
    "Cache the postcode result after first lookup.",
    "Record the cache timestamp separately from the authoritative OS payload.",
    "Refresh cached postcode records when they have not been updated in the previous 30 days."
  ],
  "stale_risk_note": "MCP-Geo can show the current authoritative result, but it cannot prove whether a downstream service cache is stale unless explicit cache telemetry is added.",
  "verification_note": "Confirm the postcode still resolves to one premises record and that any downstream cache refresh schedule matches the published GOV.UK rule.",
  "structured_output_schema": [
    "postcode",
    "uprn",
    "address",
    "classification",
    "cache_last_refreshed_at",
    "cache_policy_reference"
  ]
}
```

## 12. Coordinate-to-address incident resolution and quickest responder comparison (SG12)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `routing` via `os_places.nearest`

Phase 1 highlighted North West Fire Control using AddressBase Premium and the road network to turn coordinates into addresses and mobilise the quickest resource. This benchmark uses public responder sites and a public incident coordinate in Retford.

**Sources**
- benchmark rationale: [North West Fire Control case study](https://www.ordnancesurvey.co.uk/customers/case-studies/north-west-fire-control-ltd)
- tooling analogue: [OS Places API nearest lookup](https://www.ordnancesurvey.co.uk/documentation/product-details/places-api)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_12_dispatch_resources.csv`

**Comparator**

Published comparator: North West Fire Control used AddressBase Premium and the road network to identify an address from coordinates and mobilise the quickest resource. The benchmark answer is complete only when it resolves the coordinate and compares the responder routes without inventing unavailable timings.

**Known Gaps**
- Responder ranking depends on a ready route graph; otherwise MCP-Geo can only resolve the incident and responder locations.
- Dispatch logic, appliance availability, and control-room policy remain external to MCP-Geo.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- incident coordinates: latitude 53.3219807, longitude -0.9451639
- responder file: data/benchmarking/stakeholder_eval/fixtures/scenario_12_dispatch_resources.csv

Use MCP-Geo to answer:
"What is the incident address, and which responder reaches it fastest?"

Required steps:
- Resolve the incident coordinate to the nearest authoritative premises or address context.
- Resolve each responder site to an authoritative location.
- Compare route distance and duration from each responder if the routing graph is ready.
- If routing is unavailable, provide the furthest grounded partial result without inventing the fastest resource.
- Make the graph-readiness state explicit.

Return:
- concise dispatch answer
- incident resolution table
- responder comparison table
- blocker_or_limitations
- verification notes
- map recommended description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_dispatch_answer`
- `incident_resolution_table`
- `responder_comparison_table`
- `blocker_or_limitations`
- `verification_notes`
- `map_recommended_description`

**Reference Output Summary**

- `The incident coordinate resolves to Goodwin Hall, Chancery Lane, Retford, DN22 6DF. On the benchmark route graph, Retford Fire Station is the quickest responder and Tuxford Fire Station is slower by design.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The incident coordinate resolves to Goodwin Hall, Chancery Lane, Retford, DN22 6DF. On the benchmark route graph, Retford Fire Station is the quickest responder and Tuxford Fire Station is slower by design.",
  "method_used": [
    "Use os_places.nearest to resolve the incident coordinate to the closest authoritative address context.",
    "Resolve each responder site with os_places.search or os_places.by_uprn.",
    "Check os_route.descriptor before comparing responder journeys with os_route.get."
  ],
  "datasets_tools_used": [
    "MCP-Geo tools: os_places.nearest, os_places.search, os_route.descriptor, os_route.get",
    "Benchmark public responder sites for Retford and Tuxford fire stations"
  ],
  "confidence_caveats": [
    "Incident-to-address resolution is high confidence because the benchmark coordinate is anchored to a known public premises.",
    "Fastest-responder ranking depends on an active benchmark route graph rather than a full live dispatch system."
  ],
  "verification_steps": [
    "Confirm the coordinate still resolves nearest to Goodwin Hall.",
    "Check os_route.descriptor to ensure the benchmark graph is active before using route timings.",
    "Treat appliance availability and control-room dispatch policy as out of scope unless supplied separately."
  ],
  "structured_output": {
    "incidentAddress": "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF",
    "quickestResource": "Retford Fire Station",
    "graphReadyRequired": true,
    "suggestedExportFormat": "JSON dispatch comparison plus GeoJSON route layers."
  },
  "concise_dispatch_answer": "Resolve the coordinate first; if the route graph is ready, Retford Fire Station is the benchmark quickest responder.",
  "incident_resolution_table": [
    {
      "incident_label": "Benchmark incident",
      "lat": 53.3219807,
      "lon": -0.9451639,
      "resolved_address": "GOODWIN HALL, CHANCERY LANE, RETFORD, DN22 6DF",
      "uprn": "100032031287"
    }
  ],
  "responder_comparison_table": [
    {
      "resource_name": "Retford Fire Station",
      "route_status": "benchmark_fastest",
      "distance_m": 260.0,
      "duration_s": 120.0
    },
    {
      "resource_name": "Tuxford Fire Station",
      "route_status": "benchmark_slower",
      "distance_m": 11100.0,
      "duration_s": 900.0
    }
  ],
  "blocker_or_limitations": "If os_route.descriptor reports the graph as not ready, stop after grounded address resolution and return ROUTE_GRAPH_NOT_READY instead of inventing responder timings.",
  "verification_notes": [
    "Check the incident and responder points on a map before dispatch rehearsal.",
    "Review any loaded route warnings or restriction rows on the active benchmark graph."
  ],
  "map_recommended_description": "Map recommended: show the incident point at Goodwin Hall plus both responder sites and their compared routes."
}
```

## 13. UKHSA-style property-setting classification from authoritative address records (SG13)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

Phase 1 cited UKHSA using AddressBase with UPRN and BLPU to classify case records into settings such as care homes and prisons. This benchmark uses public addresses covering prison, care-home, residential, and civic cases.

**Sources**
- benchmark rationale: [UKHSA COVID-19 settings series technical summary](https://www.gov.uk/government/publications/covid-19-settings-series-metrics-methodology-and-usage/covid-19-settings-series-reporting-summary)
- tooling analogue: [OS Places API](https://www.ordnancesurvey.co.uk/documentation/product-details/places-api)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_13_case_addresses.csv`

**Comparator**

Published comparator: UKHSA derives property classifications from AddressBase, using UPRN and BLPU to support settings reporting. The benchmark rewards safe translation of authoritative premises classes into operational setting labels, not freehand inference.

**Known Gaps**
- MCP-Geo returns authoritative premises classes, but the UKHSA-specific settings taxonomy is still external to the tool surface.
- Batch classification remains an orchestrated workflow rather than a native MCP-Geo tool.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given case-address file: data/benchmarking/stakeholder_eval/fixtures/scenario_13_case_addresses.csv

Use MCP-Geo to answer:
"Which setting does each case belong to, using the safest authoritative identifier workflow available?"

Required steps:
- Resolve each case address to an authoritative premises record.
- Capture the authoritative identifier and classification returned by MCP-Geo.
- Translate the authoritative class into an operational setting label only where the mapping is safe.
- Separate uncertain or non-comparable records from high-confidence setting labels.
- Summarise counts by setting without inventing unsupported medical or public-health attributes.

Return:
- concise classification answer
- case classification table
- setting summary counts
- ambiguous_or_review_table
- caveats
- verification steps

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_classification_answer`
- `case_classification_table`
- `setting_summary_counts`
- `ambiguous_or_review_table`
- `caveats`
- `verification_steps_detail`

**Reference Output Summary**

- `The benchmark case list resolves cleanly enough to classify one prison, one care home, one residential dwelling, and one community facility. The safe workflow is identifier-first: resolve the UPRN, inspect the authoritative class, then translate only where the class is operationally clear.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The benchmark case list resolves cleanly enough to classify one prison, one care home, one residential dwelling, and one community facility. The safe workflow is identifier-first: resolve the UPRN, inspect the authoritative class, then translate only where the class is operationally clear.",
  "method_used": [
    "Resolve each address with os_places.search and capture the returned UPRN and classification description.",
    "Translate 'HM Prison Service' to the prison setting and 'Care / Nursing Home' to the care-home setting.",
    "Keep ambiguous civic or mixed-use records in explicit review or 'other setting' buckets instead of forcing them into UKHSA-style categories."
  ],
  "datasets_tools_used": [
    "MCP-Geo tools: os_places.search, os_places.by_uprn",
    "Published comparator: UKHSA AddressBase, UPRN, and BLPU settings workflow"
  ],
  "confidence_caveats": [
    "High confidence for prison and care-home rows because their authoritative classes are explicit.",
    "The benchmark setting labels are a controlled translation layer, not raw AddressBase outputs."
  ],
  "verification_steps": [
    "Confirm each resolved UPRN before loading the row into a public-health settings pipeline.",
    "Keep the raw classificationDescription alongside any operational setting label.",
    "Route non-standard or mixed-use premises to manual review rather than auto-classifying them."
  ],
  "structured_output": {
    "settingCounts": {
      "prison": 1,
      "care_home": 1,
      "residential": 1,
      "community_facility": 1
    },
    "suggestedExportFormat": "CSV case classification register with raw class and mapped setting columns."
  },
  "concise_classification_answer": "Resolve first, translate second: the benchmark sample contains one prison, one care home, one residential dwelling, and one community facility.",
  "case_classification_table": [
    {
      "case_id": "CASE-001",
      "uprn": "10013978351",
      "authoritative_class": "HM Prison Service",
      "setting_label": "prison"
    },
    {
      "case_id": "CASE-002",
      "uprn": "100031280110",
      "authoritative_class": "Care / Nursing Home",
      "setting_label": "care_home"
    },
    {
      "case_id": "CASE-003",
      "uprn": "100031272122",
      "authoritative_class": "Terraced",
      "setting_label": "residential"
    },
    {
      "case_id": "CASE-004",
      "uprn": "100032031210",
      "authoritative_class": "Library",
      "setting_label": "community_facility"
    }
  ],
  "setting_summary_counts": [
    {
      "setting_label": "prison",
      "cases": 1
    },
    {
      "setting_label": "care_home",
      "cases": 1
    },
    {
      "setting_label": "residential",
      "cases": 1
    },
    {
      "setting_label": "community_facility",
      "cases": 1
    }
  ],
  "ambiguous_or_review_table": [],
  "caveats": [
    "The UKHSA-specific settings taxonomy is richer than the MCP-Geo tool output alone.",
    "Keep raw premises classes and mapped settings side by side for auditability."
  ],
  "verification_steps_detail": [
    "Re-check the UPRN and premises class for any record whose address resolves to multiple candidates.",
    "Document the settings-translation rules used between raw classes and reporting categories."
  ]
}
```

## 14. North Yorkshire-style tall-building threshold review (SG14)

- Example mode: `synthetic`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

Phase 1 cited North Yorkshire Fire and Rescue using OS Select+Build and OS Building Features to identify buildings over 18 metres or seven floors. Public building-height lists are not open, so this benchmark uses a validated synthetic candidate pack tied to real public buildings.

**Sources**
- benchmark rationale: [North Yorkshire Fire and Rescue Service case study](https://www.ordnancesurvey.co.uk/customers/case-studies/north-yorkshire-fire-and-rescue-service)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_14_building_candidates.csv`

**Comparator**

Published comparator: North Yorkshire Fire and Rescue used OS Select+Build and Building Features to identify buildings over 18 metres or seven floors. This benchmark carries that threshold question into a synthetic but location-validated pack.

**Known Gaps**
- MCP-Geo lists building collections but does not yet expose a native building-height query workflow.
- The supplied height and floor values are synthetic benchmark data and must be labelled as such in every answer.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given building candidate file: data/benchmarking/stakeholder_eval/fixtures/scenario_14_building_candidates.csv

Use MCP-Geo to answer:
"Which buildings exceed 18 metres or seven floors, and which records need review?"

Required steps:
- Resolve each building to a public location where possible.
- Use the supplied height_m and floors values as synthetic benchmark attributes.
- Identify buildings that exceed either threshold.
- Flag borderline records near 18 metres or seven floors for manual review.
- Make it explicit that the height data in this benchmark is synthetic.

Return:
- concise threshold answer
- exceedance table
- review table
- synthetic_data_note
- caveats
- map recommended description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_threshold_answer`
- `exceedance_table`
- `review_table`
- `synthetic_data_note`
- `caveats`
- `map_recommended_description`

**Reference Output Summary**

- `Using the synthetic benchmark attributes, four of the six candidate buildings exceed the 18 metres or seven floors threshold and one borderline record should remain in review. The heights and floors are synthetic, even though the building anchors are real public sites and every row keeps a building site reference for audit.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Using the synthetic benchmark attributes, four of the six candidate buildings exceed the 18 metres or seven floors threshold and one borderline record should remain in review. The heights and floors are synthetic, even though the building anchors are real public sites and every row keeps a building site reference for audit.",
  "method_used": [
    "Resolve each building anchor to confirm the location exists.",
    "Use the supplied synthetic height_m and floors values because MCP-Geo does not yet expose native building-height filters.",
    "Flag records above either threshold as positive and keep near-threshold rows in review."
  ],
  "datasets_tools_used": [
    "Synthetic benchmark file with real public building anchors",
    "MCP-Geo tools: os_places.search, os_features.collections, os_features.query"
  ],
  "confidence_caveats": [
    "Confidence is high for the threshold logic inside the fixture.",
    "Confidence is limited for any claim about live building heights because the underlying height attributes are synthetic."
  ],
  "verification_steps": [
    "Confirm each building anchor resolves to the intended public site.",
    "If a live building-height source becomes available, replace the synthetic attributes before operational use."
  ],
  "structured_output": {
    "exceedanceCount": 4,
    "reviewCount": 1,
    "buildingSiteReferenceCount": 6,
    "synthetic": true,
    "suggestedExportFormat": "CSV exceedance list plus GeoJSON building points or polygons."
  },
  "concise_threshold_answer": "Four benchmark buildings exceed the 18 metres or seven floors question and one is a borderline review case.",
  "exceedance_table": [
    {
      "building_id": "BLD-001",
      "building_name": "York Minster",
      "height_m": 23.0,
      "floors": 5,
      "trigger": "height"
    },
    {
      "building_id": "BLD-002",
      "building_name": "Hudson House",
      "height_m": 22.0,
      "floors": 7,
      "trigger": "height_and_floors"
    },
    {
      "building_id": "BLD-004",
      "building_name": "The Grand Hotel York",
      "height_m": 18.5,
      "floors": 6,
      "trigger": "height"
    },
    {
      "building_id": "BLD-005",
      "building_name": "York Hospital South Block",
      "height_m": 21.0,
      "floors": 8,
      "trigger": "height_and_floors"
    }
  ],
  "review_table": [
    {
      "building_id": "BLD-006",
      "building_name": "Scarborough Town Hall",
      "height_m": 14.0,
      "floors": 3,
      "reason": "location resolves but synthetic attributes show no exceedance"
    },
    {
      "building_id": "BLD-003",
      "building_name": "County Hall",
      "height_m": 15.0,
      "floors": 4,
      "reason": "below threshold but keep as control row"
    }
  ],
  "synthetic_data_note": "Synthetic scenario: the building heights and floor counts are validated benchmark values attached to real public building anchors because no reusable open tall-building list was found, so each building keeps a site reference and review note instead of pretending the height is live.",
  "caveats": [
    "This benchmark tests threshold logic and location grounding, not a live OS building-height feed."
  ],
  "map_recommended_description": "Map recommended: show the resolved building locations and symbolise exceedances versus control rows."
}
```

## 15. ONS-style address-to-geography allocation by UPRN (SG15)

- Example mode: `public`
- MCP-Geo support level: `partial`
- Reference score: `93/100 (excellent)`
- Demo mode: `guided` via `os_places.by_uprn`

Phase 1 highlighted ONS using AddressBase-maintained UPRNs to allocate addresses to geographies. This benchmark probes exact and best-fit UPRN geography lookup using a mix of cache-covered and uncached public UPRNs.

**Sources**
- benchmark rationale: [Office for National Statistics COVID-19 Infection Survey methodology](https://www.ons.gov.uk/peoplepopulationandcommunity/healthandsocialcare/conditionsanddiseases/methodologies/covid19infectionsurveyqmi)
- tooling reference: [ONS geography cache and UPRN lookup tooling in MCP-Geo](https://github.com/chris-page-gov/mcp-geo)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_15_uprn_geography_sample.csv`

**Comparator**

Published Phase 1 finding: ONS uses AddressBase-maintained addresses as a sampling frame and separately publishes UPRN-based geography allocation products. The benchmark expects exact-versus-best-fit comparison plus explicit NOT_FOUND handling.

**Known Gaps**
- The current ONS geography cache is sparse and does not cover every public UPRN.
- Some rows return only LAD and country in the bootstrap cache, not the full OA/LSOA/MSOA chain.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given UPRN sample file: data/benchmarking/stakeholder_eval/fixtures/scenario_15_uprn_geography_sample.csv

Use MCP-Geo to answer:
"For each UPRN, what geographies are available in exact and best-fit mode, and what is missing?"

Required steps:
- Resolve each UPRN to its authoritative address where possible.
- Call the ONS geography lookup in both exact and best-fit mode.
- Compare exact and best-fit outputs explicitly.
- Separate covered rows from NOT_FOUND rows.
- Report cache provenance and any coverage limitations.

Return:
- concise geography answer
- geography comparison table
- missing_rows_table
- cache_provenance_note
- caveats
- verification notes

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_geography_answer`
- `geography_comparison_table`
- `missing_rows_table`
- `cache_provenance_note`
- `caveats`
- `verification_notes_detail`

**Reference Output Summary**

- `The benchmark pack shows three different UPRN outcomes: one row has the same LAD result in exact and best-fit mode, one row diverges between Westminster and City of London, and one row is missing entirely from the current cache.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "The benchmark pack shows three different UPRN outcomes: one row has the same LAD result in exact and best-fit mode, one row diverges between Westminster and City of London, and one row is missing entirely from the current cache.",
  "method_used": [
    "Resolve each UPRN to a public address with os_places.by_uprn.",
    "Query ons_geo.by_uprn in exact mode and best_fit mode for each UPRN.",
    "Keep missing rows explicit and report the cache provenance rather than guessing absent geographies."
  ],
  "datasets_tools_used": [
    "MCP-Geo tools: os_places.by_uprn, ons_geo.by_uprn, ons_geo.cache_status",
    "Published comparator: ONS AddressBase-backed geography allocation workflow"
  ],
  "confidence_caveats": [
    "High confidence on rows that are present in the current cache.",
    "Coverage is intentionally limited in the bootstrap cache, so NOT_FOUND is an expected benchmark outcome for some UPRNs."
  ],
  "verification_steps": [
    "Confirm the current cache status and generation timestamp before relying on any lookup.",
    "Rebuild the ONS geography cache if wider UPRN coverage is needed."
  ],
  "structured_output": {
    "coveredRows": 2,
    "missingRows": 1,
    "suggestedExportFormat": "CSV exact/best-fit comparison table plus JSON cache-status snapshot."
  },
  "concise_geography_answer": "Two of the three benchmark UPRNs resolve in the current cache, and one of those shows an exact-versus-best-fit LAD difference.",
  "geography_comparison_table": [
    {
      "uprn": "100023336959",
      "address": "FOREIGN COMMONWEALTH & DEVELOPMENT OFFICE, KING CHARLES STREET, LONDON, SW1A 2AH",
      "exact_lad": "Coventry",
      "best_fit_lad": "Coventry",
      "difference_flag": false
    },
    {
      "uprn": "100120786206",
      "address": "3, THE MAGNOLIAS, BICESTER, OX26 3YG",
      "exact_lad": "Westminster",
      "best_fit_lad": "City of London",
      "difference_flag": true
    }
  ],
  "missing_rows_table": [
    {
      "uprn": "100032031210",
      "label": "Retford Library",
      "exact_status": "NOT_FOUND",
      "best_fit_status": "NOT_FOUND"
    }
  ],
  "cache_provenance_note": "Cache provenance should be read from ons_geo.cache_status; the current benchmark cache is a small bootstrap rather than a full production UPRN directory.",
  "caveats": [
    "The bootstrap cache currently exposes only limited geography fields for the covered UPRNs."
  ],
  "verification_notes_detail": [
    "Always compare exact and best-fit results before aggregating public-sector metrics by geography.",
    "Treat unexpected LAD differences as a signal to inspect the underlying ONS reference product."
  ]
}
```

## 16. NHS SCW-style patient distance-to-pharmacy validation (SG16)

- Example mode: `synthetic`
- MCP-Geo support level: `partial`
- Reference score: `93/100 (excellent)`
- Demo mode: `guided` via `os_places.search`

Phase 1 cited NHS South, Central and West using AddressBase and Code-Point to identify people beyond 1.6 kilometres from a pharmacy. Patient-level addresses are not public, so this benchmark uses synthetic patient rows anchored to public addresses and real public pharmacy sites.

**Sources**
- benchmark rationale: [NHS South, Central and West case study](https://www.ordnancesurvey.co.uk/customers/case-studies/nhs-south-central-and-west-commissioning-support-unit)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_16_patient_sample.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_16_pharmacy_sites.csv`

**Comparator**

Published comparator: NHS SCW used AddressBase and Code-Point to identify dispensing-list patients more than 1.6 km from their nearest pharmacy. The benchmark rewards careful distance ranking plus explicit synthetic-data labelling.

**Known Gaps**
- MCP-Geo does not yet expose a native nearest-facility-by-category workflow for pharmacies.
- The patient rows are synthetic and must be labelled synthetic in every answer and export.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- patient file: data/benchmarking/stakeholder_eval/fixtures/scenario_16_patient_sample.csv
- pharmacy file: data/benchmarking/stakeholder_eval/fixtures/scenario_16_pharmacy_sites.csv
- distance threshold: 1.6 kilometres

Use MCP-Geo to answer:
"Which patients are beyond 1.6 kilometres from the nearest pharmacy, and which rows need review?"

Required steps:
- Resolve patient and pharmacy addresses to authoritative locations.
- Compare each patient to the nearest resolved pharmacy.
- Identify rows above the 1.6 km threshold.
- Separate high-confidence rows from unresolved or review rows.
- Keep the synthetic-patient status explicit in the answer and exports.

Return:
- concise distance answer
- patient_distance_table
- threshold_breach_table
- review_table
- synthetic_data_note
- verification notes

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_distance_answer`
- `patient_distance_table`
- `threshold_breach_table`
- `review_table`
- `synthetic_data_note`
- `verification_notes_detail`

**Reference Output Summary**

- `In the benchmark pack, three synthetic patient rows are beyond the 1.6 km threshold, one is within range, and one should stay in review until both the patient and nearest pharmacy resolution are confirmed.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "In the benchmark pack, three synthetic patient rows are beyond the 1.6 km threshold, one is within range, and one should stay in review until both the patient and nearest pharmacy resolution are confirmed.",
  "method_used": [
    "Resolve each synthetic patient row and each public pharmacy address to authoritative coordinates.",
    "Measure each patient against the nearest resolved pharmacy.",
    "Keep unresolved or low-confidence rows in a review queue instead of forcing a threshold decision."
  ],
  "datasets_tools_used": [
    "Synthetic patient benchmark file anchored to public addresses",
    "Public Worksop pharmacy addresses",
    "MCP-Geo tools: os_places.search, os_places.by_postcode"
  ],
  "confidence_caveats": [
    "Distance logic is strong once both patient and pharmacy sites resolve.",
    "This benchmark uses synthetic patient rows and an external nearest-facility calculation rather than a native MCP-Geo workflow."
  ],
  "verification_steps": [
    "Confirm every patient and pharmacy location resolves cleanly before applying the threshold.",
    "Re-run the nearest-site calculation if the pharmacy list changes."
  ],
  "structured_output": {
    "breachCount": 3,
    "reviewCount": 1,
    "synthetic": true,
    "suggestedExportFormat": "CSV patient-to-pharmacy distance table plus CSV review queue."
  },
  "concise_distance_answer": "Three synthetic benchmark patients are beyond 1.6 km from their nearest pharmacy, one is within range, and one remains in review.",
  "patient_distance_table": [
    {
      "patient_id": "PT-001",
      "nearest_pharmacy": "Worksop Pharmacy",
      "distance_km": 1.2,
      "threshold_status": "within"
    },
    {
      "patient_id": "PT-002",
      "nearest_pharmacy": "Manton Pharmacy",
      "distance_km": 2.1,
      "threshold_status": "beyond"
    },
    {
      "patient_id": "PT-003",
      "nearest_pharmacy": "Worksop Pharmacy",
      "distance_km": 7.6,
      "threshold_status": "beyond"
    },
    {
      "patient_id": "PT-004",
      "nearest_pharmacy": "Worksop Pharmacy",
      "distance_km": 15.4,
      "threshold_status": "beyond"
    },
    {
      "patient_id": "PT-005",
      "nearest_pharmacy": "Worksop Pharmacy",
      "distance_km": null,
      "threshold_status": "review"
    }
  ],
  "threshold_breach_table": [
    {
      "patient_id": "PT-002",
      "distance_km": 2.1
    },
    {
      "patient_id": "PT-003",
      "distance_km": 7.6
    },
    {
      "patient_id": "PT-004",
      "distance_km": 15.4
    }
  ],
  "review_table": [
    {
      "patient_id": "PT-005",
      "reason": "Retford row requires a broader pharmacy site list or confirmation of the nearest resolved site."
    }
  ],
  "synthetic_data_note": "Synthetic scenario: patient rows are benchmark-only records anchored to public addresses because real dispensing-list patient addresses are not public.",
  "verification_notes_detail": [
    "Confirm the nearest pharmacy list covers the operational area before using the threshold output.",
    "Keep the synthetic patient flag in any downstream export or scorecard."
  ]
}
```

## 17. Transport for West Midlands-style street width and gradient bottleneck review (SG17)

- Example mode: `synthetic`
- MCP-Geo support level: `blocked`
- Reference score: `93/100 (excellent)`
- Demo mode: `blocked` via `os_features.query`

Phase 1 described Transport for West Midlands deriving street width and gradient insights at fine spatial granularity. Public segment-level width and gradient outputs were not available, so this benchmark uses a synthetic segment pack tied to real public streets.

**Sources**
- benchmark rationale: [Transport for West Midlands case study](https://www.ordnancesurvey.co.uk/customers/case-studies/transport-for-west-midlands)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_17_street_segments.csv`

**Comparator**

Published comparator: TfWM described generating street widths at 1 m intervals and street-gradient insights from OS datasets. This benchmark is synthetic because that granular derived output is not openly published for reuse.

**Known Gaps**
- MCP-Geo has no native street-width or gradient derivation tool today.
- The width and gradient figures are synthetic benchmark values and must remain clearly labelled as such.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given street segment file: data/benchmarking/stakeholder_eval/fixtures/scenario_17_street_segments.csv

Use MCP-Geo to answer:
"Which street segments are the main accessibility bottlenecks if width under 3.2 m or gradient over 5% is a concern?"

Required steps:
- Resolve the named streets and confirm the place context.
- Use the supplied synthetic width_m and gradient_pct attributes.
- Flag segments breaching width, gradient, or both thresholds.
- Rank the worst bottlenecks.
- Make clear that the width and gradient figures are synthetic benchmark data.

Return:
- concise bottleneck answer
- bottleneck_table
- review_or_control_table
- synthetic_data_note
- caveats
- map recommended description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_bottleneck_answer`
- `bottleneck_table`
- `review_or_control_table`
- `synthetic_data_note`
- `caveats`
- `map_recommended_description`

**Reference Output Summary**

- `Using the synthetic benchmark attributes, three street segments are bottlenecks: Digbeth High Street breaches the width threshold, Summer Lane breaches both thresholds, and Hockley Hill breaches the gradient threshold. The numbers are synthetic even though the streets are real.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Using the synthetic benchmark attributes, three street segments are bottlenecks: Digbeth High Street breaches the width threshold, Summer Lane breaches both thresholds, and Hockley Hill breaches the gradient threshold. The numbers are synthetic even though the streets are real.",
  "method_used": [
    "Resolve the named streets as real public streets in Birmingham.",
    "Apply the width and gradient thresholds to the supplied synthetic segment attributes.",
    "Rank segments breaching both thresholds ahead of single-threshold breaches."
  ],
  "datasets_tools_used": [
    "Synthetic street segment benchmark file tied to real public streets",
    "MCP-Geo tools: os_names.find, os_features.collections, os_features.query"
  ],
  "confidence_caveats": [
    "Confidence is high for the thresholding inside the fixture.",
    "There is no live MCP-Geo derivation of street width or gradient yet, so the output remains benchmark-only."
  ],
  "verification_steps": [
    "Resolve every street name to the intended place context.",
    "Replace the synthetic width and gradient fields with a live derivation source before operational use."
  ],
  "structured_output": {
    "bottleneckCount": 3,
    "synthetic": true,
    "suggestedExportFormat": "CSV bottleneck ranking plus GeoJSON segment overlays when live geometry becomes available."
  },
  "concise_bottleneck_answer": "Three synthetic benchmark street segments are the main accessibility bottlenecks.",
  "bottleneck_table": [
    {
      "segment_id": "SEG-003",
      "street_name": "Summer Lane",
      "width_m": 3.1,
      "gradient_pct": 6.8,
      "breach_type": "width_and_gradient"
    },
    {
      "segment_id": "SEG-002",
      "street_name": "Digbeth High Street",
      "width_m": 2.9,
      "gradient_pct": 3.4,
      "breach_type": "width"
    },
    {
      "segment_id": "SEG-005",
      "street_name": "Hockley Hill",
      "width_m": 3.8,
      "gradient_pct": 7.4,
      "breach_type": "gradient"
    }
  ],
  "review_or_control_table": [
    {
      "segment_id": "SEG-001",
      "street_name": "Corporation Street",
      "status": "control"
    },
    {
      "segment_id": "SEG-004",
      "street_name": "Broad Street",
      "status": "control"
    }
  ],
  "synthetic_data_note": "Synthetic scenario: width and gradient values are benchmark-only derived attributes tied to real public streets.",
  "caveats": [
    "This is a blocked first-class workflow in MCP-Geo today because the derivation layer is not exposed."
  ],
  "map_recommended_description": "Map recommended: show Birmingham street segments coloured by width/gradient breach type."
}
```

## 18. Birmingham and Solihull referral inequity review by ward (SG18)

- Example mode: `synthetic`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`
- Demo mode: `guided` via `admin_lookup.find_by_name`

Phase 1 cited Birmingham and Solihull Mental Health NHS Foundation Trust using OS boundaries and basemaps to visualise referral patterns and inequities. The referral counts in this benchmark are synthetic, but the wards and service sites are real.

**Sources**
- benchmark rationale: [Birmingham and Solihull Mental Health NHS Foundation Trust case study](https://www.ordnancesurvey.co.uk/customers/case-studies/birmingham-and-solihull-mental-health-nhs-foundation-trust)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_18_referral_wards.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_18_service_sites.csv`

**Comparator**

Published comparator: the trust used OS boundaries and mapping to visualise referrals and inequities. The benchmark keeps the counts synthetic but expects the geography and service-site reasoning to stay grounded.

**Known Gaps**
- Referral and need counts are synthetic benchmark values, not live NHS data.
- MCP-Geo does not yet expose a native inequity-dashboard workflow; site prioritisation still requires external logic.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- ward file: data/benchmarking/stakeholder_eval/fixtures/scenario_18_referral_wards.csv
- service site file: data/benchmarking/stakeholder_eval/fixtures/scenario_18_service_sites.csv

Use MCP-Geo to answer:
"Which wards look under-referred relative to need, and which service sites should review them first?"

Required steps:
- Resolve the ward geography and service site locations.
- Use the supplied synthetic_referrals and synthetic_need_index values.
- Identify wards with high need but comparatively low referrals.
- Associate those wards with the nearest or most relevant resolved service site where possible.
- Keep the synthetic nature of the referral counts explicit.

Return:
- concise inequity answer
- ward_inequity_table
- priority_review_sites
- synthetic_data_note
- caveats
- map recommended description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_inequity_answer`
- `ward_inequity_table`
- `priority_review_sites`
- `synthetic_data_note`
- `caveats`
- `map_recommended_description`

**Reference Output Summary**

- `Small Heath and Sparkbrook are the clearest synthetic under-referral wards in the benchmark because they pair the highest need scores with the lowest referral counts. Small Heath Health Centre should review Small Heath first, and central Birmingham teams should review Sparkbrook next.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Small Heath and Sparkbrook are the clearest synthetic under-referral wards in the benchmark because they pair the highest need scores with the lowest referral counts. Small Heath Health Centre should review Small Heath first, and central Birmingham teams should review Sparkbrook next.",
  "method_used": [
    "Resolve the ward names and service site addresses.",
    "Compare synthetic_referrals against synthetic_need_index to identify high-need / low-referral wards.",
    "Assign review priority to the most relevant resolved service sites."
  ],
  "datasets_tools_used": [
    "Synthetic ward referral benchmark file",
    "Public BSMHFT service-site addresses",
    "MCP-Geo tools: admin_lookup.find_by_name, os_places.search"
  ],
  "confidence_caveats": [
    "Geography and service-site resolution are grounded.",
    "Referral counts and need scores are synthetic and should not be treated as live NHS performance data."
  ],
  "verification_steps": [
    "Confirm each ward resolves to the intended Birmingham context.",
    "Replace synthetic counts with approved referral and need data before operational use."
  ],
  "structured_output": {
    "priorityWardCount": 2,
    "synthetic": true,
    "suggestedExportFormat": "CSV ward inequity table plus map-ready service-site overlay."
  },
  "concise_inequity_answer": "Two synthetic benchmark wards stand out for review: Small Heath and Sparkbrook.",
  "ward_inequity_table": [
    {
      "ward_name": "Small Heath",
      "synthetic_referrals": 12,
      "synthetic_need_index": 92,
      "priority": "high"
    },
    {
      "ward_name": "Sparkbrook",
      "synthetic_referrals": 10,
      "synthetic_need_index": 95,
      "priority": "high"
    },
    {
      "ward_name": "Ladywood",
      "synthetic_referrals": 16,
      "synthetic_need_index": 85,
      "priority": "medium"
    }
  ],
  "priority_review_sites": [
    {
      "site_name": "Small Heath Health Centre",
      "focus_wards": [
        "Small Heath",
        "Sparkbrook"
      ]
    },
    {
      "site_name": "Northcroft Hospital",
      "focus_wards": [
        "Erdington"
      ]
    }
  ],
  "synthetic_data_note": "Synthetic scenario: referral counts and need indices are benchmark-only values attached to real wards and real service sites.",
  "caveats": [
    "Under-referral signals in this benchmark are illustrative rather than operational."
  ],
  "map_recommended_description": "Map recommended: show resolved wards shaded by synthetic need-versus-referral gap and overlay the trust service sites."
}
```

## 19. Cheshire and Wirral service-location coverage versus client distribution (SG19)

- Example mode: `synthetic`
- MCP-Geo support level: `partial`
- Reference score: `93/100 (excellent)`
- Demo mode: `guided` via `os_names.find`

Phase 1 cited Cheshire and Wirral Partnership NHS Foundation Trust using OS mapping to compare client distribution with service locations. The client counts here are synthetic, while the towns and trust sites are real public references.

**Sources**
- benchmark rationale: [Cheshire and Wirral Partnership NHS Foundation Trust case study](https://www.ordnancesurvey.co.uk/customers/case-studies/cheshire-and-wirral-partnership-nhs-foundation-trust)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_coverage_towns.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_sites.csv`

**Comparator**

Published comparator: Cheshire and Wirral Partnership used OS mapping to compare client distribution with service locations. The benchmark reproduces the service-coverage logic using synthetic client counts and real site anchors.

**Known Gaps**
- Client counts and need indices are synthetic benchmark values.
- MCP-Geo does not yet expose a native service-network optimisation workflow.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- client cluster file: data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_coverage_towns.csv
- service site file: data/benchmarking/stakeholder_eval/fixtures/scenario_19_service_sites.csv

Use MCP-Geo to answer:
"Which client clusters look least well served by the current site pattern?"

Required steps:
- Resolve the towns and service sites.
- Use the supplied synthetic_clients and synthetic_need_index values.
- Compare the client clusters with the current service-site distribution.
- Highlight the clusters that look least well served.
- Keep the synthetic client counts explicit in every summary and export.

Return:
- concise coverage answer
- underserved_cluster_table
- service_site_context_table
- synthetic_data_note
- caveats
- verification notes

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_coverage_answer`
- `underserved_cluster_table`
- `service_site_context_table`
- `synthetic_data_note`
- `caveats`
- `verification_notes_detail`

**Reference Output Summary**

- `In the benchmark client pattern, Ellesmere Port and Tarvin look least well served because they are not colocated with the named trust sites and carry meaningful synthetic demand. Chester and Macclesfield align more closely with the current site pattern.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "In the benchmark client pattern, Ellesmere Port and Tarvin look least well served because they are not colocated with the named trust sites and carry meaningful synthetic demand. Chester and Macclesfield align more closely with the current site pattern.",
  "method_used": [
    "Resolve the cluster towns and trust service sites.",
    "Compare synthetic client volume and need against the current service-site pattern.",
    "Flag clusters without a clearly colocated or nearby service site for review."
  ],
  "datasets_tools_used": [
    "Synthetic client-cluster benchmark file",
    "Public Cheshire and Wirral Partnership service-site addresses",
    "MCP-Geo tools: os_names.find, os_places.search"
  ],
  "confidence_caveats": [
    "Town and site locations are grounded.",
    "The client distribution is synthetic and should be treated as a planning benchmark only."
  ],
  "verification_steps": [
    "Confirm the town anchors resolve to the intended Cheshire context.",
    "Replace synthetic client counts with approved service-planning data before any operational decision."
  ],
  "structured_output": {
    "underservedClusterCount": 2,
    "synthetic": true,
    "suggestedExportFormat": "CSV underserved cluster table plus map-ready town/service-site overlay."
  },
  "concise_coverage_answer": "Ellesmere Port and Tarvin are the clearest synthetic underserved clusters in the benchmark.",
  "underserved_cluster_table": [
    {
      "town_name": "Ellesmere Port",
      "synthetic_clients": 73,
      "synthetic_need_index": 88,
      "coverage_status": "underserved_review"
    },
    {
      "town_name": "Tarvin",
      "synthetic_clients": 24,
      "synthetic_need_index": 55,
      "coverage_status": "underserved_review"
    }
  ],
  "service_site_context_table": [
    {
      "site_name": "Countess of Chester Health Park",
      "context": "closest major site for Chester and nearby clusters"
    },
    {
      "site_name": "Delamere Resource Centre",
      "context": "Crewe-aligned service site"
    },
    {
      "site_name": "York House",
      "context": "Macclesfield-aligned service site"
    }
  ],
  "synthetic_data_note": "Synthetic scenario: client counts and need indices are benchmark-only values attached to real towns and real trust sites.",
  "caveats": [
    "No live service-capacity or appointment data is included in this benchmark."
  ],
  "verification_notes_detail": [
    "Validate cluster-to-site travel times before acting on a service-coverage recommendation."
  ]
}
```

## 20. Policing patrol-planning hotspot review with live resource locations (SG20)

- Example mode: `synthetic`
- MCP-Geo support level: `blocked`
- Reference score: `93/100 (excellent)`
- Demo mode: `blocked` via `os_mcp.route_query`

Phase 1 included a policing procurement that described map-driven analysis, demand prediction, patrol planning, and live resource location using Ordnance Survey and AddressBase data. Incident demand is private, so this benchmark uses synthetic hotspots anchored to real public places and police resource sites.

**Sources**
- benchmark rationale: [Police GIS platform procurement notice](https://www.contractsfinder.service.gov.uk/Notice/6f72e900-e31d-4055-b1cc-bd6528bab4ef)

**Fixtures**
- `data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_demand_cells.csv`
- `data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_resources.csv`

**Comparator**

Published comparator: the procurement described a system supporting map-driven analysis, demand prediction, patrol planning, and live resource location using authoritative OS data. MCP-Geo does not yet provide that end-to-end policing workflow natively.

**Known Gaps**
- Patrol demand and vulnerability values are synthetic benchmark data.
- MCP-Geo does not yet expose live patrol optimisation, demand prediction, or resource-allocation logic as a first-class tool.

**Populated Prompt**

```text
You are GPT-5.4 using MCP-Geo as the authoritative geospatial tool layer.

Rules:
- Use MCP-Geo tools wherever possible rather than answering from memory.
- Prefer authoritative OS-backed data and identifiers.
- Never invent UPRNs, geometries, classifications, or road-network facts.
- If data is missing, stale, ambiguous, or unavailable, say so explicitly.
- Show the exact reasoning steps in operational form, not hidden chain-of-thought: dataset discovery, lookup, joins, filters, overlays, routing, aggregation, and verification.
- Distinguish confirmed results from assumptions or inferred limitations.
- Return:
  1) concise answer
  2) method used
  3) datasets/tools used
  4) confidence and caveats
  5) verification steps
  6) exportable structured output where relevant
- Where useful, produce both a short narrative answer and a machine-readable table/JSON block.
- Where a map would materially help, say “Map recommended” and describe what should be shown.

Task:
Given:
- patrol demand file: data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_demand_cells.csv
- patrol resource file: data/benchmarking/stakeholder_eval/fixtures/scenario_20_patrol_resources.csv

Use MCP-Geo to answer:
"Which hotspots appear least well covered by the current police resource pattern, and what should be reviewed first?"

Required steps:
- Resolve the synthetic hotspot place names and the public police resource sites.
- Use the supplied synthetic_incidents and synthetic_vulnerability_index values.
- Highlight hotspots that appear least well covered by the current resource pattern.
- Avoid pretending MCP-Geo can run full patrol optimisation or demand prediction when it cannot.
- Keep the synthetic status explicit in the answer and outputs.

Return:
- concise patrol answer
- hotspot_priority_table
- resource_context_table
- synthetic_data_note
- capability_gap_note
- map recommended description

```

**Expected Output Fields**
- `concise_answer`
- `method_used`
- `datasets_tools_used`
- `confidence_caveats`
- `verification_steps`
- `structured_output`
- `concise_patrol_answer`
- `hotspot_priority_table`
- `resource_context_table`
- `synthetic_data_note`
- `capability_gap_note`
- `map_recommended_description`

**Reference Output Summary**

- `Worksop and Retford are the highest-priority synthetic hotspots in the benchmark. Worksop is at least colocated with one resource anchor, but Retford and Tuxford still look coverage-sensitive when compared with the current resource pattern.`

**Reference Output (JSON)**

```json
{
  "concise_answer": "Worksop and Retford are the highest-priority synthetic hotspots in the benchmark. Worksop is at least colocated with one resource anchor, but Retford and Tuxford still look coverage-sensitive when compared with the current resource pattern.",
  "method_used": [
    "Resolve the named hotspots and public police resource sites.",
    "Use the supplied synthetic incident and vulnerability values to rank hotspots.",
    "Describe coverage sensitivity without claiming a full patrol-optimisation result."
  ],
  "datasets_tools_used": [
    "Synthetic policing hotspot benchmark file",
    "Public police resource-site addresses",
    "MCP-Geo tools: os_names.find, os_places.search, os_mcp.route_query"
  ],
  "confidence_caveats": [
    "Place and resource resolution are grounded.",
    "Patrol demand ranking is synthetic and MCP-Geo does not yet provide live patrol optimisation."
  ],
  "verification_steps": [
    "Confirm the hotspot anchors and resource sites resolve to the intended Nottinghamshire context.",
    "Use an operational policing platform for any real patrol-allocation decision."
  ],
  "structured_output": {
    "priorityHotspots": [
      "Worksop",
      "Retford",
      "Tuxford"
    ],
    "synthetic": true,
    "suggestedExportFormat": "CSV hotspot priority table plus map-ready hotspot/resource overlay."
  },
  "concise_patrol_answer": "Worksop and Retford are the highest-priority synthetic patrol hotspots in the benchmark, with Tuxford next.",
  "hotspot_priority_table": [
    {
      "place_name": "Worksop",
      "synthetic_incidents": 52,
      "synthetic_vulnerability_index": 73,
      "priority": "high"
    },
    {
      "place_name": "Retford",
      "synthetic_incidents": 38,
      "synthetic_vulnerability_index": 77,
      "priority": "high"
    },
    {
      "place_name": "Tuxford",
      "synthetic_incidents": 17,
      "synthetic_vulnerability_index": 64,
      "priority": "medium"
    }
  ],
  "resource_context_table": [
    {
      "resource_name": "Crown House",
      "context": "Worksop-aligned public resource anchor"
    },
    {
      "resource_name": "Newark Police Station",
      "context": "Newark-aligned public resource anchor"
    }
  ],
  "synthetic_data_note": "Synthetic scenario: hotspot demand and vulnerability values are benchmark-only values attached to real public places and resource sites.",
  "capability_gap_note": "Blocked first-class workflow: MCP-Geo can ground places and resource sites, but it does not yet provide patrol optimisation, demand prediction, or live resource-allocation tooling.",
  "map_recommended_description": "Map recommended: show hotspot places sized by synthetic demand and overlay the resolved police resource sites."
}
```
