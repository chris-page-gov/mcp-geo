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

The first curated conversation covers the 2026-05-13 MCP-Geo session on server launch, Nottinghamshire geotechnical risk, LandIS/PostGIS recovery, ExtSSD archive inspection, and the LEACS download/access probe.

## Start Here

- [Conversation Summary](conversation-summary.md)
- [Publication Boundary](publication-boundary.md)
- [Decision Register](decisions.md)
- [Repository Evidence](repository-evidence.md)
- [Start-to-Finish Conversation Readers](#start-to-finish-conversation-readers)

## Start-to-Finish Conversation Readers

| Source | Conversation | Exchanges | Reader | Source Note |
|---|---|---:|---|---|
| CONV-001 | LandIS, Nottinghamshire Coverage, and LEACS Access Probe | 10 | [read](readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) | [source](sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md) |

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

## Machine-Readable Registers

- [Session register](data/session-register-public.json)
- [Exchange register](data/exchange-register-public.json)
- [Artifact register](data/artifact-register-public.json)

## Related Existing Conversation Artifacts

These repository files are source candidates for future curation. They are not yet split into the reader/exchange/source pattern used by this wiki:

- [Claude failed conversation](../../docs/Claude_failed_conversation.md)
- [Claude success conversation](../../docs/Claude_success_conversation.md)
- [Claude Opus failed conversation 1](../../docs/Claude_opus_4-6_failed_convo_1.md)
- [Claude Opus failed conversation 2](../../docs/claude_opus_4-6_failed_convo_2.md)

## Publication Counts

- Conversation summaries: 1
- Redacted/curated prompt-response exchanges: 10
- Machine-readable registers: 3
- Repository evidence links: 10

## Scope Notes

- This is a curated derivative, not a raw transcript dump.
- Secret material, browser tokens, API keys, and local-only secret file paths are intentionally excluded.
- Local machine paths that are needed for operational memory are generalized in public pages.
