# MCP-Geo Stakeholder Evaluation Benchmark Pack

Generated: 2026-03-09

This pack turns the Phase 3 prompt bank into a run-ready benchmark for stakeholder evaluation.
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
- Workflow report: [mcp_geo_stakeholder_benchmark_workflow_2026-03-09.md](mcp_geo_stakeholder_benchmark_workflow_2026-03-09.md)
- Interpretation note: the `Reference score` grades the completeness and auditability of the benchmark's gold answer, not the current implementation completeness of MCP-Geo itself.
- Read `MCP-Geo support level` separately: `partial` and `blocked` mark product capability gaps even when the benchmark reference output scores `100/100`.

## Scenario Pack

## 1. Affected premises and vulnerable households in an incident area (SG01)

- Example mode: `mixed`
- MCP-Geo support level: `partial`
- Reference score: `100/100 (excellent)`

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
