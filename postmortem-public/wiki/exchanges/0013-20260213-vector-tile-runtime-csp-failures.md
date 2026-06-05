---
exchange_id: "EX-0013"
title: "Vector Tile Runtime and CSP Failures"
source_id: "CONV-002"
global_sequence: 13
session_sequence: 3
user_timestamp: "2026-02-13"
timestamp_precision: "date"
publication_status: "public-safe-curated-derivative"
tags:
  - "exchange"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
  - "maplibre"
  - "csp"
---

# 0013. Vector Tile Runtime and CSP Failures

Conversation reader: [start-to-finish](../readers/conv-002-claude-cv1-map-failure-success.md) | Previous: [EX-0012](0012-20260213-os-mapping-api-key-handling-drift.md) | Next: [EX-0014](0014-20260214-constrained-cv1-postcode-tool-probes.md)

## Publication Boundary

This is a curated public derivative. It preserves sequence and contribution
evidence, but it is not the raw Claude or Codex transcript.

## User Prompt

```text
No way, maybe not leaflet? Use vector tiles.

Yuk!! maplibregl is not defined.

Failed again.

This is costing me a lot.
```

## Curated Outcome

The client pivoted from Leaflet to MapLibre and OS vector tiles, but the host
environment still blocked the generated artifact. The error pattern moved from
missing globals to content-security-policy and worker-loading failures. Several
successive repair attempts changed CDN sources, worker settings, and API usage,
but the generated page remained unreliable.

## Why It Matters

This exchange is the clearest evidence that "use vector tiles" is necessary
but not sufficient. The map runtime must be designed for the target host:
script loading, worker policy, cross-origin behaviour, credentials, and
fallback display all need to be part of the MCP-Geo contract rather than an
after-the-fact model-generated repair loop.
