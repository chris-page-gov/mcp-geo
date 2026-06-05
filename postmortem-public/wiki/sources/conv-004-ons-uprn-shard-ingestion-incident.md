---
source_id: "CONV-004"
title: "ONS UPRN Shard-Ingestion Incident"
source_type: "curated_conversation_summary"
publication_status: "public-safe-curated-derivative"
conversation_date: "2026-04-15"
exchange_count: 4
raw_transcript_status: "not-exported"
capture_ids:
  - "CAP-007"
tags:
  - "source"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "ons-geo"
  - "uprn"
---

# ONS UPRN Shard-Ingestion Incident

This source note summarizes the final selected Stage 2
client-interoperability capture. It uses durable repository evidence, not raw
Codex JSONL paths.

- Conversation source ID: `CONV-004`
- Date: `2026-04-15`
- Start-to-finish reader: [conversation reader](../readers/conv-004-ons-uprn-shard-ingestion-incident.md)
- User-visible exchange groups: 4
- Raw Codex transcript: not exported into this repository
- Evidence basis: [CONTEXT.md](../../../CONTEXT.md), [CHANGELOG.md](../../../CHANGELOG.md), [ONS cache refresh script](../../../scripts/ons_geo_cache_refresh.py), and [ONS cache refresh regression tests](../../../tests/test_ons_geo_cache_refresh.py)

## Public Exchange Notes

- [EX-0022: UPRN Lookup Returns False NOT_FOUND](../exchanges/0022-20260415-uprn-lookup-false-not-found.md)
- [EX-0023: Cache Diagnosis Finds Single-Shard Ingestion](../exchanges/0023-20260415-cache-diagnosis-single-shard-ingestion.md)
- [EX-0024: Refresh Logic Streams All Compatible UPRN Shards](../exchanges/0024-20260415-refresh-logic-streams-all-uprn-shards.md)
- [EX-0025: Rebuild Requirement and Regression Boundary](../exchanges/0025-20260415-rebuild-requirement-regression-boundary.md)

## Durable Findings

- Claude-side `ons_geo.by_uprn` calls returned `NOT_FOUND` for Welsh and
  non-Yorkshire English UPRNs even though the ONS UPRN products were marked
  as ingested.
- The affected local cache had loaded only one region shard from ONSUD/NSUL ZIP
  archives. In the recorded diagnosis, the loaded shard was `YH`, so lookups
  outside that shard failed.
- The bug was in refresh ingestion, not in the public lookup API contract. The
  refresh path chose one best-scoring archive member instead of streaming every
  compatible best-schema UPRN data member.
- The code now treats UPRN archives as multi-member sources by default and
  streams every compatible member with the best schema.
- Regression coverage uses split ONSUD/NSUL ZIP fixtures with `LN`, `WA`, and
  `YH` data members, proving that the cache records all three UPRN rows.
- Existing caches built before the fix remain incomplete until the ONS geo
  cache refresh is rerun.
