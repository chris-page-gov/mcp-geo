---
title: "MCP-Geo Conversation Summary"
tags:
  - "summary"
  - "mcp-geo"
  - "llm-wiki"
---

# Conversation Summary

## CONV-001: LandIS, Nottinghamshire Coverage, and LEACS Access Probe

- Date: 2026-05-13
- Type: curated public-safe conversation record
- Reader: [CONV-001 reader](readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- Source note: [CONV-001 source](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- Exchange count: 10
- Raw transcript status: not exported into this repository

This conversation began as a live MCP-Geo demonstration check, then moved into a practical geospatial investigation: identify collapse-risk geotechnical earthworks in Nottinghamshire, explain why LandIS-backed pipe-risk coverage was unavailable, recover the local PostGIS/LandIS workflow, inspect the mounted external data archive, and test whether missing LEACS data could be downloaded from public or authenticated LandIS routes.

The operational conclusion was that the MCP-Geo server and PostGIS/LandIS phase-2 archive path were recoverable, and Nottinghamshire can be served for NATMAP/Soilscapes/NSI-style soil context. LEACS-derived pipe-risk expansion is blocked because the public metadata and authenticated portal scan exposed LEACS descriptions but no downloadable LEACS payload.

## Key Outcomes

- MCP-Geo could be launched locally for demonstration once the secure OS API key source and server process were set up.
- OS NGD/admin tooling could identify Nottinghamshire and return geotechnical landform features relevant to collapse-risk screening.
- The LandIS warehouse issue was caused by local runtime/data availability, not by the MCP protocol surface itself.
- A working PostGIS sidecar could load the phase-2 LandIS archive tables needed for NATMAP, Soilscapes, and NSI queries.
- The external `ExtSSD-Data` archive was necessary for broader historical LandIS evidence, but it did not contain a LEACS data table.
- A fresh authenticated portal probe found no LEACS item, table, service, or relevant fields such as corrosion/shrink-swell indicators.
- The resulting LEACS access report is now the durable reference for future requests.

## CONV-002: Claude CV1 Map Failure and Constrained Success Path

- Date: 2026-02-13 to 2026-02-14
- Type: curated public-safe conversation record
- Reader: [CONV-002 reader](readers/conv-002-claude-cv1-map-failure-success.md)
- Source note: [CONV-002 source](sources/conv-002-claude-cv1-map-failure-success.md)
- Exchange count: 5
- Raw transcript status: not exported into this repository

This conversation captures the CV1 3HB client-interoperability examples from
the selected Stage 2 batch. A broad "show this postcode on a map" request led
to generated HTML, OS map-runtime repair attempts, and MapLibre/CSP/worker
failures. Narrow, explicit MCP calls against `os_places.by_postcode` then
provided a control case showing that the OS Places data path was stable.

The operational conclusion is that map delivery should be a server-owned
descriptor/resource handoff with explicit host fallbacks and runtime credential
handling. Chat-generated standalone HTML is too brittle for repeatable
user-facing OS map delivery, while constrained MCP tool calls produce auditable
diagnostic evidence.

## CONV-002 Key Outcomes

- The CV1 3HB postcode lookup was not the core failure; the generated map
  artifact and dependency chain were.
- OS API credentials must stay in runtime/server configuration, not pasted into
  chat or public artifacts.
- Vector tiles were technically appropriate, but the client still needed a
  host-aware rendering contract.
- Exact MCP tool calls produced stable postcode/address evidence and exposed
  the earlier map failures as presentation/runtime failures.
- Structured road/postcode/workbook-style outputs are a better fallback than
  repeated ad hoc browser artifact repair.

## CONV-003: Claude Opus Leamington/Warwick Stats-Routing Failures

- Date: 2026-02-07 to 2026-02-10
- Type: curated public-safe conversation record
- Reader: [CONV-003 reader](readers/conv-003-claude-leamington-warwick-stats-routing.md)
- Source note: [CONV-003 source](sources/conv-003-claude-leamington-warwick-stats-routing.md)
- Exchange count: 6
- Raw transcript status: not exported into this repository

This conversation captures the Leamington Spa and Warwick statistics-routing
examples from the selected Stage 2 batch. The client successfully found useful
ward sets and the stats-routing tool correctly recommended NOMIS for
labour/census indicators, but the workflow broke down when the dashboard did
not render and direct NOMIS queries had to be assembled from incomplete
parameter knowledge.

The operational conclusion is that routing is not enough by itself. MCP-Geo
needs to provide executable comparison plans: disambiguated current areas,
selected indicators, ready query templates or validation hints, and a compact
tabular fallback when a dashboard resource cannot be rendered.

## CONV-003 Key Outcomes

- Broad place-name search can flood the client before the comparison unit is
  selected.
- Ward-level geography was the right comparison level for the two towns, but
  generic or legacy ward matches had to be excluded.
- Stats routing correctly selected NOMIS and ward-level comparison, but did
  not hand off a complete query plan.
- Broad NOMIS dataset searches missed or obscured the relevant Census 2021
  topic-summary datasets.
- Direct NOMIS calls repeatedly failed with incomplete-query and upstream
  response errors once the client tried to infer parameters itself.
- Dashboard tools need public fallback state so comparison work can continue
  when the host cannot render the widget.

## CONV-004: ONS UPRN Shard-Ingestion Incident

- Date: 2026-04-15
- Type: curated public-safe conversation record
- Reader: [CONV-004 reader](readers/conv-004-ons-uprn-shard-ingestion-incident.md)
- Source note: [CONV-004 source](sources/conv-004-ons-uprn-shard-ingestion-incident.md)
- Exchange count: 4
- Raw transcript status: not exported into this repository

This conversation captures the ONS UPRN lookup incident selected as CAP-007.
Claude-side `ons_geo.by_uprn` calls returned `NOT_FOUND` for Welsh and
non-Yorkshire English UPRNs, even though ONSUD/NSUL were marked as ingested.
The diagnosis found that the source ZIP archives were region-sharded and that
the refresh process had loaded only one best-scoring data member.

The operational conclusion is that the lookup contract was not the root cause.
The refresh path needed to stream all compatible UPRN archive members, and
existing pre-fix cache files need a rebuild before client lookups become
healthy.

## CONV-004 Key Outcomes

- Product-level `ingested` status was insufficient evidence of national UPRN
  coverage.
- ONSUD/NSUL source archives can contain regional data shards under `Data/`.
- The pre-fix refresh process selected one best-scoring member, causing false
  `NOT_FOUND` responses outside that shard.
- The fixed refresh path streams every compatible best-schema UPRN member.
- Regression coverage now proves that `LN`, `WA`, and `YH` fixture shards are
  ingested together.
- Caches built before the fix remain incomplete until refreshed.

## Future Curation Candidates

Existing Claude conversation records in `docs/` have been reviewed as example
source material. The first selected Stage 2 capture batch is recorded in
[Selected Capture Queue](capture-selection.md): seven candidate Codex sessions
covering CV1 3HB map failure/success, Leamington/Warwick stats-routing
failures, and the ONS UPRN shard-ingestion incident. CONV-002, CONV-003, and
CONV-004 are now curated. The selected Stage 2 batch is complete.
