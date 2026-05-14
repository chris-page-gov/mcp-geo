---
exchange_id: "EX-0020"
title: "Census Query Parameter Failures"
source_id: "CONV-003"
global_sequence: 20
session_sequence: 5
user_timestamp: "2026-02-10"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "nomis"
  - "query-normalization"
---

# 0020. Census Query Parameter Failures

Conversation reader: [start-to-finish](../readers/conv-003-claude-leamington-warwick-stats-routing.md) | Previous: [EX-0019](0019-20260210-nomis-dataset-discovery-drift.md) | Next: [EX-0021](0021-20260210-comparison-output-contract-needed.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Continue the statistics-routing comparison for Leamington Spa and Warwick.
```

## Curated Outcome

Once the client had selected wards and candidate datasets, direct NOMIS query
attempts repeatedly failed. The examples include incomplete query errors,
invalid upstream JSON handling, and an SDMX conversion error when the client
varied geography, measure, time, frequency, codelist, and output-format
parameters.

## Why It Matters

This is the core implementation lesson for CONV-003. A model should not have to
infer full NOMIS parameter contracts from a dataset structure dump. The tool
surface should either validate missing dimensions with actionable messages or
offer ready-to-run query templates for the common Census 2021 comparison path.
