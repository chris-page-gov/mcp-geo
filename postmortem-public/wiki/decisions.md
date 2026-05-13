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
