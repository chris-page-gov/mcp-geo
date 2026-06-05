---
source_id: "CONV-002"
title: "Claude CV1 Map Failure and Constrained Success Path"
source_type: "curated_conversation_summary"
publication_status: "public-safe-curated-derivative"
conversation_date: "2026-02-13/2026-02-14"
exchange_count: 5
raw_transcript_status: "not-exported"
capture_ids:
  - "CAP-002"
  - "CAP-003"
  - "CAP-004"
tags:
  - "source"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "cv1-3hb"
---

# Claude CV1 Map Failure and Constrained Success Path

This source note summarizes the first selected Stage 2 client-interoperability
capture. It uses existing public repository example documents, not raw Codex
JSONL paths.

- Conversation source ID: `CONV-002`
- Date range: `2026-02-13` to `2026-02-14`
- Start-to-finish reader: [conversation reader](../readers/conv-002-claude-cv1-map-failure-success.md)
- User-visible exchange groups: 5
- Raw Codex transcript: not exported into this repository
- Evidence basis: [Claude failed conversation](../../../docs/Claude_failed_conversation.md), [Claude success conversation](../../../docs/Claude_success_conversation.md), and the selected capture register

## Public Exchange Notes

- [EX-0011: CV1 Map Request Produces Fragile HTML Output](../exchanges/0011-20260213-cv1-map-request-fragile-html-output.md)
- [EX-0012: OS Mapping and API-Key Handling Drift](../exchanges/0012-20260213-os-mapping-api-key-handling-drift.md)
- [EX-0013: Vector Tile Runtime and CSP Failures](../exchanges/0013-20260213-vector-tile-runtime-csp-failures.md)
- [EX-0014: Constrained CV1 Postcode Tool Probes](../exchanges/0014-20260214-constrained-cv1-postcode-tool-probes.md)
- [EX-0015: Surrounding Postcodes and Road Workbook Request](../exchanges/0015-20260214-surrounding-postcodes-road-workbook-request.md)

## Durable Findings

- A general "show this postcode on a map" request led the client toward
  ad hoc HTML generation, browser-library loading errors, and repeated
  map-runtime repair attempts.
- Asking for OS mapping increased the operational constraints: credentials had
  to remain outside the transcript, and the client needed a host-compatible
  rendering route rather than an exposed key or brittle script include.
- Switching from Leaflet to MapLibre did not solve the host problem by itself;
  the hosted artifact environment also constrained library globals, web
  workers, and cross-origin script behaviour.
- Narrow, explicit MCP tool calls against `os_places.by_postcode` for `CV1 3HB`
  produced stable, auditable data and made the success path easier to verify.
- The right design lesson is not "never show maps"; it is to separate data
  retrieval, map descriptor/resource handoff, credential handling, and
  host-specific rendering capability.
