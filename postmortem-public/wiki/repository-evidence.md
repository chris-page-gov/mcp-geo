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
- [CONV-001 public source note](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- [CONV-001 source summary](../../postmortem/sources/conversations/conv-001-20260513-mcp-geo-landis-nottinghamshire-leacs.md)

## External Data Roots

The conversation referred to an external archive mounted as `ExtSSD-Data`. Public wiki pages generalize that mount as `[EXTSSD_DATA_ROOT]`. The important durable facts are:

- The phase-2 LandIS archive can support NATMAP, Soilscapes, and NSI coverage after loading into PostGIS.
- The full-release archive preserved public LEACS pages and metadata pages, but not a downloadable LEACS data table.
- The inspected external Postgres data directory was not modified in place during recovery-style checks.
