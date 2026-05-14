---
title: "MCP-Geo Public Conversation Wiki"
tags:
  - "index"
  - "mcp-geo"
  - "llm-wiki"
  - "conversation-record"
---

# MCP-Geo Public Conversation Wiki

This folder is a GitHub-safe LLM Wiki record for curated MCP-Geo conversations. It mirrors the conversation-postmortem shape used in the `ai-engineering-lab-hackathon-london-2026` repo: an index, a start-to-finish reader, standalone exchange notes, source notes, and machine-readable registers.

The first curated conversation covers the 2026-05-13 MCP-Geo session on server launch, Nottinghamshire geotechnical risk, LandIS/PostGIS recovery, ExtSSD archive inspection, and the LEACS download/access probe. The second curated conversation covers the CV1 3HB Claude client-interoperability examples, contrasting fragile generated map artifacts with constrained MCP postcode lookups. The third curated conversation covers the Leamington/Warwick statistics-routing examples, where provider choice and ward lookup worked better than dashboard/query execution. The fourth curated conversation covers the ONS UPRN shard-ingestion incident and the cache-refresh/rebuild boundary.

## Start Here

- [Conversation Summary](conversation-summary.md)
- [Publication Boundary](publication-boundary.md)
- [Decision Register](decisions.md)
- [Repository Evidence](repository-evidence.md)
- [Repeatable Workflow](repeatable-workflow.md)
- [Selected Capture Queue](capture-selection.md)
- [Start-to-Finish Conversation Readers](#start-to-finish-conversation-readers)

## Start-to-Finish Conversation Readers

| Source | Conversation | Exchanges | Reader | Source Note |
|---|---|---:|---|---|
| CONV-001 | LandIS, Nottinghamshire Coverage, and LEACS Access Probe | 10 | [read](readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) | [source](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) |
| CONV-002 | Claude CV1 Map Failure and Constrained Success Path | 5 | [read](readers/conv-002-claude-cv1-map-failure-success.md) | [source](sources/conv-002-claude-cv1-map-failure-success.md) |
| CONV-003 | Claude Opus Leamington/Warwick Stats-Routing Failures | 6 | [read](readers/conv-003-claude-leamington-warwick-stats-routing.md) | [source](sources/conv-003-claude-leamington-warwick-stats-routing.md) |
| CONV-004 | ONS UPRN Shard-Ingestion Incident | 4 | [read](readers/conv-004-ons-uprn-shard-ingestion-incident.md) | [source](sources/conv-004-ons-uprn-shard-ingestion-incident.md) |

## Redacted Prompt-Response Exchanges

| Sequence | Exchange | Source |
|---:|---|---|
| 1 | [Launch MCP-Geo Server for Demonstration](exchanges/0001-20260513-launch-mcp-geo-server-for-demonstration.md) | CONV-001 |
| 2 | [Assess Nottinghamshire Geotechnical Earthworks Collapse Risk](exchanges/0002-20260513-assess-nottinghamshire-geotechnical-earthworks-collapse-risk.md) | CONV-001 |
| 3 | [Explain LandIS Warehouse Unavailability](exchanges/0003-20260513-explain-landis-warehouse-unavailability.md) | CONV-001 |
| 4 | [Troubleshoot Missing Postgres](exchanges/0004-20260513-troubleshoot-missing-postgres.md) | CONV-001 |
| 5 | [Extend LandIS Coverage to Nottinghamshire](exchanges/0005-20260513-extend-landis-coverage-to-nottinghamshire.md) | CONV-001 |
| 6 | [Mount ExtSSD-Data and Recheck Archives](exchanges/0006-20260513-mount-extssd-data-and-recheck-archives.md) | CONV-001 |
| 7 | [Check LEACS Provenance](exchanges/0007-20260513-check-leacs-provenance.md) | CONV-001 |
| 8 | [Probe LEACS Download Routes](exchanges/0008-20260513-probe-leacs-download-routes.md) | CONV-001 |
| 9 | [Document LEACS Access and Future Conditions](exchanges/0009-20260513-document-leacs-access-and-future-conditions.md) | CONV-001 |
| 10 | [Create MCP-Geo Conversation LLM Wiki](exchanges/0010-20260513-create-mcp-geo-conversation-llm-wiki.md) | CONV-001 |
| 11 | [CV1 Map Request Produces Fragile HTML Output](exchanges/0011-20260213-cv1-map-request-fragile-html-output.md) | CONV-002 |
| 12 | [OS Mapping and API-Key Handling Drift](exchanges/0012-20260213-os-mapping-api-key-handling-drift.md) | CONV-002 |
| 13 | [Vector Tile Runtime and CSP Failures](exchanges/0013-20260213-vector-tile-runtime-csp-failures.md) | CONV-002 |
| 14 | [Constrained CV1 Postcode Tool Probes](exchanges/0014-20260214-constrained-cv1-postcode-tool-probes.md) | CONV-002 |
| 15 | [Surrounding Postcodes and Road Workbook Request](exchanges/0015-20260214-surrounding-postcodes-road-workbook-request.md) | CONV-002 |
| 16 | [Broad Leamington/Warwick Comparison Overloads Search](exchanges/0016-20260207-leamington-warwick-broad-comparison-overload.md) | CONV-003 |
| 17 | [Stats Routing Creates a Ward-Level Comparison Contract](exchanges/0017-20260210-stats-routing-ward-comparison-contract.md) | CONV-003 |
| 18 | [Dashboard Render Fallback to Direct Queries](exchanges/0018-20260210-dashboard-render-fallback-to-direct-queries.md) | CONV-003 |
| 19 | [NOMIS Dataset Discovery Drift](exchanges/0019-20260210-nomis-dataset-discovery-drift.md) | CONV-003 |
| 20 | [Census Query Parameter Failures](exchanges/0020-20260210-census-query-parameter-failures.md) | CONV-003 |
| 21 | [Comparison Output Contract Needed](exchanges/0021-20260210-comparison-output-contract-needed.md) | CONV-003 |
| 22 | [UPRN Lookup Returns False NOT_FOUND](exchanges/0022-20260415-uprn-lookup-false-not-found.md) | CONV-004 |
| 23 | [Cache Diagnosis Finds Single-Shard Ingestion](exchanges/0023-20260415-cache-diagnosis-single-shard-ingestion.md) | CONV-004 |
| 24 | [Refresh Logic Streams All Compatible UPRN Shards](exchanges/0024-20260415-refresh-logic-streams-all-uprn-shards.md) | CONV-004 |
| 25 | [Rebuild Requirement and Regression Boundary](exchanges/0025-20260415-rebuild-requirement-regression-boundary.md) | CONV-004 |

## Machine-Readable Registers

- [Session register](data/session-register-public.json)
- [Exchange register](data/exchange-register-public.json)
- [Artifact register](data/artifact-register-public.json)
- [Capture selection register](data/capture-selection-public.json)

## Related Existing Conversation Artifacts

These repository files have now been reviewed for the first selected capture
batch; see [Selected Capture Queue](capture-selection.md). The CV1 3HB pair is
curated as CONV-002, the Leamington/Warwick examples are curated as CONV-003,
and the ONS UPRN incident is curated as CONV-004.

- [Claude failed conversation](../../docs/Claude_failed_conversation.md)
- [Claude success conversation](../../docs/Claude_success_conversation.md)
- [Claude Opus failed conversation 1](../../docs/Claude_opus_4-6_failed_convo_1.md)
- [Claude Opus failed conversation 2](../../docs/claude_opus_4-6_failed_convo_2.md)

## Publication Counts

- Conversation summaries: 4
- Redacted/curated prompt-response exchanges: 25
- Machine-readable registers: 4
- Selected capture candidates: 7
- Repository evidence links: 28

## Scope Notes

- This is a curated derivative, not a raw transcript dump.
- Secret material, browser tokens, API keys, and local-only secret file paths are intentionally excluded.
- Local machine paths that are needed for operational memory are generalized in public pages.
