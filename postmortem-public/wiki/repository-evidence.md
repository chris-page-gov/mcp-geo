---
title: "MCP-Geo Conversation Repository Evidence"
tags:
  - "repository-evidence"
  - "mcp-geo"
  - "llm-wiki"
---

# Repository Evidence

This page links the curated conversation record to durable repository artifacts.

## LandIS And LEACS Evidence

- [LandIS LEACS access probe report](../../docs/reports/landis_leacs_access_probe_2026-05-13.md)
- [LEACS access probe machine-readable metadata](../../research/landis-data-source/landis_leacs_access_probe_2026-05-13.json)
- [LandIS release surface reconciliation](../../docs/reports/landis_release_surface_reconciliation_2026-04-05.md)
- [LandIS portal inventory](../../docs/reports/landis_portal_inventory_2026-04-04.md)
- [LandIS phase 2 surfacing plan](../../docs/reports/landis_phase_2_surfacing_plan_2026-04-04.md)
- [LandIS MVP implementation plan](../../research/landis-data-source/LandIS%20MVP%20Implementation%20PLAN.md)

## Conversation And Project Memory

- [Durable MCP-Geo context](../../CONTEXT.md)
- [LLM Wiki vs RAG research note](../../research/llm_wiki_vs_rag/LLM%20Wiki,%20Enhanced%20RAG%20and%20the%20Right%20Knowledge%20Architecture%20for%20MCP-Geo.md)
- [Selected capture queue](capture-selection.md)
- [CONV-001 public source note](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- [CONV-001 start-to-finish reader](readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- [CONV-002 public source note](sources/conv-002-claude-cv1-map-failure-success.md)
- [CONV-002 start-to-finish reader](readers/conv-002-claude-cv1-map-failure-success.md)
- [CONV-003 public source note](sources/conv-003-claude-leamington-warwick-stats-routing.md)
- [CONV-003 start-to-finish reader](readers/conv-003-claude-leamington-warwick-stats-routing.md)
- [CONV-004 public source note](sources/conv-004-ons-uprn-shard-ingestion-incident.md)
- [CONV-004 start-to-finish reader](readers/conv-004-ons-uprn-shard-ingestion-incident.md)
- [Repeatable workflow](repeatable-workflow.md)
- [Repository workflow note](../../docs/llm_wiki_postmortem_workflow.md)
- [Codex session inventory script](../../scripts/llm_wiki_postmortem_inventory.py)

## ONS UPRN Evidence

- [ONS geo source resolution note](../../docs/ons_geo_source_resolution.md)
- [ONS cache refresh script](../../scripts/ons_geo_cache_refresh.py)
- [ONS cache refresh regression tests](../../tests/test_ons_geo_cache_refresh.py)
- [Release changelog](../../CHANGELOG.md)

## Selected Client-Interop Source Examples

- [Claude failed conversation](../../docs/Claude_failed_conversation.md)
- [Claude success conversation](../../docs/Claude_success_conversation.md)
- [Claude Opus failed conversation 1](../../docs/Claude_opus_4-6_failed_convo_1.md)
- [Claude Opus failed conversation 2](../../docs/claude_opus_4-6_failed_convo_2.md)

## External Data Roots

The conversation referred to an external archive mounted as `ExtSSD-Data`. Public wiki pages generalize that mount as `[EXTSSD_DATA_ROOT]`. The important durable facts are:

- The phase-2 LandIS archive can support NATMAP, Soilscapes, and NSI coverage after loading into PostGIS.
- The full-release archive preserved public LEACS pages and metadata pages, but not a downloadable LEACS data table.
- The inspected external Postgres data directory was not modified in place during recovery-style checks.
