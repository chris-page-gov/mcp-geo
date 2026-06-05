---
title: "MCP-Geo Conversation Decision Register"
tags:
  - "decision-register"
  - "mcp-geo"
  - "llm-wiki"
---

# Decision Register

| ID | Date | Decision | Evidence | Status |
|---|---|---|---|---|
| D-001 | 2026-05-13 | Keep OS API credentials out of chat and source; load them from secure local configuration for live demos. | [EX-0001](exchanges/0001-20260513-launch-mcp-geo-server-for-demonstration.md) | Active |
| D-002 | 2026-05-13 | Treat the Nottinghamshire geotechnical answer as a screening/ranking output, not as an engineering collapse determination. | [EX-0002](exchanges/0002-20260513-assess-nottinghamshire-geotechnical-earthworks-collapse-risk.md) | Active |
| D-003 | 2026-05-13 | Diagnose LandIS warehouse failures through runtime topology first: environment DSNs, Docker/PostGIS availability, and loaded tables. | [EX-0003](exchanges/0003-20260513-explain-landis-warehouse-unavailability.md) | Active |
| D-004 | 2026-05-13 | Use the local phase-2 LandIS archive and PostGIS sidecar for NATMAP, Soilscapes, and NSI coverage where available. | [EX-0004](exchanges/0004-20260513-troubleshoot-missing-postgres.md) | Active |
| D-005 | 2026-05-13 | Do not represent Nottinghamshire pipe-risk outputs as LEACS-derived until a licensed/downloadable LEACS payload is available. | [EX-0005](exchanges/0005-20260513-extend-landis-coverage-to-nottinghamshire.md), [EX-0008](exchanges/0008-20260513-probe-leacs-download-routes.md) | Active |
| D-006 | 2026-05-13 | Keep the original ExtSSD Postgres data directory read-only during recovery-style inspection; use scratch copies for destructive database repair attempts. | [EX-0006](exchanges/0006-20260513-mount-extssd-data-and-recheck-archives.md) | Active |
| D-007 | 2026-05-13 | Preserve the LEACS access probe as the durable future-request reference, including negative findings and conditions that would change the answer. | [EX-0009](exchanges/0009-20260513-document-leacs-access-and-future-conditions.md) | Active |
| D-008 | 2026-05-13 | Represent the conversation in the same reader/source/exchange LLM Wiki pattern used by the hackathon postmortem, but mark it as curated rather than raw. | [EX-0010](exchanges/0010-20260513-create-mcp-geo-conversation-llm-wiki.md) | Active |
| D-009 | 2026-02-13 | For user-facing maps, prefer MCP-Geo server-owned descriptors/resources and host-compatible fallbacks over chat-generated standalone HTML. | [EX-0011](exchanges/0011-20260213-cv1-map-request-fragile-html-output.md), [EX-0013](exchanges/0013-20260213-vector-tile-runtime-csp-failures.md) | Active |
| D-010 | 2026-02-13 | Keep OS API key handling in runtime/server configuration; public map artifacts must not require pasted OS credentials or expose keys. | [EX-0012](exchanges/0012-20260213-os-mapping-api-key-handling-drift.md) | Active |
| D-011 | 2026-02-14 | Use constrained MCP calls as control probes before broad presentation tasks when diagnosing client/tool failures. | [EX-0014](exchanges/0014-20260214-constrained-cv1-postcode-tool-probes.md), [EX-0015](exchanges/0015-20260214-surrounding-postcodes-road-workbook-request.md) | Active |
| D-012 | 2026-02-10 | Treat stats routing output as an executable comparison contract, not just a provider recommendation. | [EX-0017](exchanges/0017-20260210-stats-routing-ward-comparison-contract.md) | Active |
| D-013 | 2026-02-10 | Bound town comparisons to explicit current-area sets and record excluded ambiguous matches before querying indicators. | [EX-0016](exchanges/0016-20260207-leamington-warwick-broad-comparison-overload.md), [EX-0017](exchanges/0017-20260210-stats-routing-ward-comparison-contract.md) | Active |
| D-014 | 2026-02-10 | Dashboard resources must expose selected areas, indicators, and fallback query state when the host cannot render the widget. | [EX-0018](exchanges/0018-20260210-dashboard-render-fallback-to-direct-queries.md), [EX-0021](exchanges/0021-20260210-comparison-output-contract-needed.md) | Active |
| D-015 | 2026-02-10 | NOMIS/Census tools should provide query templates or actionable dimension validation for common Census 2021 comparison datasets. | [EX-0019](exchanges/0019-20260210-nomis-dataset-discovery-drift.md), [EX-0020](exchanges/0020-20260210-census-query-parameter-failures.md) | Active |
| D-016 | 2026-04-15 | Treat sharded ONS UPRN product coverage separately from product-level ingestion status. | [EX-0022](exchanges/0022-20260415-uprn-lookup-false-not-found.md), [EX-0023](exchanges/0023-20260415-cache-diagnosis-single-shard-ingestion.md) | Active |
| D-017 | 2026-04-15 | Stream all compatible best-schema UPRN archive members for ONSUD/NSUL instead of selecting one member from a region-sharded ZIP. | [EX-0024](exchanges/0024-20260415-refresh-logic-streams-all-uprn-shards.md) | Active |
| D-018 | 2026-04-15 | Treat cache rebuild as part of closure for pre-fix ONS geo caches; code changes alone do not repair already-populated SQLite caches. | [EX-0025](exchanges/0025-20260415-rebuild-requirement-regression-boundary.md) | Active |
