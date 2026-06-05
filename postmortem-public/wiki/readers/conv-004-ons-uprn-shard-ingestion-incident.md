---
source_id: "CONV-004"
title: "ONS UPRN Shard-Ingestion Incident Reader"
reader_type: "curated_start_to_finish_conversation"
publication_status: "public-safe-curated-derivative"
exchange_count: 4
tags:
  - "reader"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "ons-geo"
---

# CONV-004: ONS UPRN Shard-Ingestion Incident

This public reader inlines the curated prompt-response exchanges for the ONS
UPRN shard-ingestion incident. It captures why `ons_geo.by_uprn` looked broken
to a client even though the root cause was an incomplete local cache refresh.

## Navigation

- Index: [MCP-Geo Public Conversation Wiki](../index.md)
- Conversation source note: [CONV-004](../sources/conv-004-ons-uprn-shard-ingestion-incident.md)
- Raw Codex transcript: not exported into this repository.
- Durable repo evidence: [CONTEXT.md](../../../CONTEXT.md), [CHANGELOG.md](../../../CHANGELOG.md), [cache refresh code](../../../scripts/ons_geo_cache_refresh.py), [regression tests](../../../tests/test_ons_geo_cache_refresh.py)

## Exchange Map

| Exchange | Prompt Theme | Standalone Note |
|---|---|---|
| [EX-0022](#ex-0022) | UPRN Lookup Returns False NOT_FOUND | [note](../exchanges/0022-20260415-uprn-lookup-false-not-found.md) |
| [EX-0023](#ex-0023) | Cache Diagnosis Finds Single-Shard Ingestion | [note](../exchanges/0023-20260415-cache-diagnosis-single-shard-ingestion.md) |
| [EX-0024](#ex-0024) | Refresh Logic Streams All Compatible UPRN Shards | [note](../exchanges/0024-20260415-refresh-logic-streams-all-uprn-shards.md) |
| [EX-0025](#ex-0025) | Rebuild Requirement and Regression Boundary | [note](../exchanges/0025-20260415-rebuild-requirement-regression-boundary.md) |

## Conversation

<a id="ex-0022"></a>

### EX-0022: UPRN Lookup Returns False NOT_FOUND

- User timestamp precision: date only (`2026-04-15`)
- Standalone note: [EX-0022](../exchanges/0022-20260415-uprn-lookup-false-not-found.md)

#### User Prompt

```text
Investigate why Claude-side ONS geography UPRN lookups return NOT_FOUND for known UPRNs.
```

#### Curated Outcome

```text
The symptom was a false negative: Welsh and non-Yorkshire English UPRNs returned NOT_FOUND even though ONSUD/NSUL were reported as ingested.
```

<a id="ex-0023"></a>

### EX-0023: Cache Diagnosis Finds Single-Shard Ingestion

- User timestamp precision: date only (`2026-04-15`)
- Standalone note: [EX-0023](../exchanges/0023-20260415-cache-diagnosis-single-shard-ingestion.md)

#### User Prompt

```text
Check whether the ONS geography cache contents match the advertised ingested products.
```

#### Curated Outcome

```text
The local cache held only one regional UPRN shard from ONSUD/NSUL. The product looked ingested, but most regional UPRNs were absent from the SQLite rows and UPRN index.
```

<a id="ex-0024"></a>

### EX-0024: Refresh Logic Streams All Compatible UPRN Shards

- User timestamp precision: date only (`2026-04-15`)
- Standalone note: [EX-0024](../exchanges/0024-20260415-refresh-logic-streams-all-uprn-shards.md)

#### User Prompt

```text
Fix the refresh path so ONSUD and NSUL ingest every applicable regional data shard.
```

#### Curated Outcome

```text
The refresh logic now treats UPRN products as multi-member archives by default and streams every compatible best-schema member instead of one tie-broken CSV.
```

<a id="ex-0025"></a>

### EX-0025: Rebuild Requirement and Regression Boundary

- User timestamp precision: date only (`2026-04-15`)
- Standalone note: [EX-0025](../exchanges/0025-20260415-rebuild-requirement-regression-boundary.md)

#### User Prompt

```text
Record what remains required after the refresh-code fix.
```

#### Curated Outcome

```text
The code fix is not enough for existing local caches. Any cache built before the fix must be refreshed, and regression coverage must prove that multiple ONSUD/NSUL regional shards are ingested together.
```

## Summary

CONV-004 preserves the cache-health lesson from the ONS UPRN incident: product
status must not be treated as sufficient evidence of coverage. For sharded
source archives, MCP-Geo needs ingestion logic and cache-status reporting that
distinguish "a product was ingested" from "all expected regional shards were
loaded."
