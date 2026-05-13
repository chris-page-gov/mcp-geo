---
source_id: "CONV-001"
title: "LandIS, Nottinghamshire Coverage, and LEACS Access Probe"
source_type: "curated_conversation_source_summary"
conversation_date: "2026-05-13"
publication_status: "public-safe-source-summary"
raw_transcript_status: "not-exported"
tags:
  - "source"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
---

# CONV-001: LandIS, Nottinghamshire Coverage, and LEACS Access Probe

This is the source summary for the public MCP-Geo conversation wiki entry. It records the conversation sequence and evidence basis without embedding a raw transcript.

## Source Status

- Raw transcript export: not available in this repository at time of creation.
- Curated public wiki: `postmortem-public/wiki/`
- Public reader: `postmortem-public/wiki/readers/conv-001-mcp-geo-landis-nottinghamshire-leacs.md`
- Public source note: `postmortem-public/wiki/sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md`

## Conversation Sequence

1. Launch MCP-Geo locally for demonstration without changing source code.
2. Use MCP-Geo to screen Nottinghamshire geotechnical earthworks for collapse-relevant feature classes.
3. Explain why the LandIS warehouse path was unavailable for the requested pipe-risk workflow.
4. Troubleshoot local Docker/PostGIS availability and LandIS archive loading.
5. Extend Nottinghamshire coverage where supported by loaded LandIS phase-2 products.
6. Mount and inspect the external `ExtSSD-Data` archive as a source of historical LandIS evidence.
7. Check whether LEACS provenance came from an earlier agentic download.
8. Probe public and authenticated routes for a downloadable LEACS payload.
9. Document the LEACS negative finding and future conditions.
10. Create the MCP-Geo conversation LLM Wiki in the same reader/source/exchange form used by the hackathon repo.

## Evidence Basis

- Current Codex thread context on 2026-05-13.
- Repository context in `CONTEXT.md`.
- LEACS report at `docs/reports/landis_leacs_access_probe_2026-05-13.md`.
- LEACS metadata at `research/landis-data-source/landis_leacs_access_probe_2026-05-13.json`.
- Prior LandIS reports and plans linked from `postmortem-public/wiki/repository-evidence.md`.

## Notes For Future Curators

- If a raw transcript is later exported, preserve it under a private/local evidence archive and update the source note with a hash rather than publishing the raw file by default.
- Existing Claude conversation markdown files in `docs/` are future curation candidates but are not part of CONV-001.
- Keep credential and token material out of this wiki.
