---
exchange_id: "EX-0024"
title: "Refresh Logic Streams All Compatible UPRN Shards"
source_id: "CONV-004"
global_sequence: 24
session_sequence: 3
user_timestamp: "2026-04-15"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "ons-geo"
  - "cache-refresh"
  - "regression"
---

# 0024. Refresh Logic Streams All Compatible UPRN Shards

Conversation reader: [start-to-finish](../readers/conv-004-ons-uprn-shard-ingestion-incident.md) | Previous: [EX-0023](0023-20260415-cache-diagnosis-single-shard-ingestion.md) | Next: [EX-0025](0025-20260415-rebuild-requirement-regression-boundary.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Fix the refresh path so ONSUD and NSUL ingest every applicable regional data shard.
```

## Curated Outcome

The refresh path now selects all compatible best-schema members for UPRN
products. `scripts/ons_geo_cache_refresh.py` treats UPRN-keyed archives as
multi-member sources by default, merges the member fieldnames, and streams each
chosen member into the cache and UPRN index.

## Why It Matters

The fix targets the ingestion root cause rather than special-casing individual
failed UPRNs. Any future ONSUD/NSUL archive with the same regional split should
be handled consistently.
