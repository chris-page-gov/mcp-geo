---
exchange_id: "EX-0015"
title: "Surrounding Postcodes and Road Workbook Request"
source_id: "CONV-002"
global_sequence: 15
session_sequence: 5
user_timestamp: "2026-02-14"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "os-places"
  - "structured-output"
---

# 0015. Surrounding Postcodes and Road Workbook Request

Conversation reader: [start-to-finish](../readers/conv-002-claude-cv1-map-failure-success.md) | Previous: [EX-0014](0014-20260214-constrained-cv1-postcode-tool-probes.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
Can you list road names and UPRN counts with types please?

Can you give the size of the bounding box and then produce an excel workbook
keyed on road names that accurately gives a breakdown of UPRNs on each road by
type. Classify roads as within the bbox or crossing the bbox boundary so we can
see which are partial reports of premises count.
```

## Curated Outcome

After the bounded postcode and bounding-box lookups, the user moved from map
display toward structured analysis: road names, UPRN counts, property-type
breakdowns, bounding-box dimensions, and boundary-crossing classification. The
client was able to describe a more useful tabular/workbook output, which is a
better fit for repeatable evidence than a brittle generated map.

## Why It Matters

This exchange shows the productive path after the map failure: keep the OS
Places data path explicit, summarize spatial scope, and move complex outputs
into structured artifacts that can be validated. It also records a caveat: a
bounding-box sample is not automatically an exhaustive road inventory unless
the query strategy is designed for complete coverage.
