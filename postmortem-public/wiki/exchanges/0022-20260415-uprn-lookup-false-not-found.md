---
exchange_id: "EX-0022"
title: "UPRN Lookup Returns False NOT_FOUND"
source_id: "CONV-004"
global_sequence: 22
session_sequence: 1
user_timestamp: "2026-04-15"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "ons-geo"
  - "uprn"
---

# 0022. UPRN Lookup Returns False NOT_FOUND

Conversation reader: [start-to-finish](../readers/conv-004-ons-uprn-shard-ingestion-incident.md) | Previous: [EX-0021](0021-20260210-comparison-output-contract-needed.md) | Next: [EX-0023](0023-20260415-cache-diagnosis-single-shard-ingestion.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Investigate why Claude-side ONS geography UPRN lookups return NOT_FOUND for known UPRNs.
```

## Curated Outcome

The observed client symptom was a false negative from `ons_geo.by_uprn`.
Welsh and non-Yorkshire English UPRNs returned `NOT_FOUND` even though the
source products were recorded as ingested.

## Why It Matters

This is different from a genuinely unknown UPRN. The client had a healthy tool
surface but an incomplete local cache, so the response misled downstream users
about data absence.
