---
source_id: "CONV-002"
title: "Claude CV1 Map Failure and Constrained Success Path Reader"
reader_type: "curated_start_to_finish_conversation"
publication_status: "public-safe-curated-derivative"
exchange_count: 5
tags:
  - "reader"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
  - "client-interop"
---

# CONV-002: Claude CV1 Map Failure and Constrained Success Path

This public reader inlines the curated prompt-response exchanges for the CV1
3HB client-interoperability capture. It contrasts a fragile generated-map path
with a constrained MCP tool-call success path.

## Navigation

- Index: [MCP-Geo Public Conversation Wiki](../index.md)
- Conversation source note: [CONV-002](../sources/conv-002-claude-cv1-map-failure-success.md)
- Raw Codex transcript: not exported into this repository.
- Public example sources: [failed map conversation](../../../docs/Claude_failed_conversation.md), [success/control conversation](../../../docs/Claude_success_conversation.md)

## Exchange Map

| Exchange | Prompt Theme | Standalone Note |
|---|---|---|
| [EX-0011](#ex-0011) | CV1 Map Request Produces Fragile HTML Output | [note](../exchanges/0011-20260213-cv1-map-request-fragile-html-output.md) |
| [EX-0012](#ex-0012) | OS Mapping and API-Key Handling Drift | [note](../exchanges/0012-20260213-os-mapping-api-key-handling-drift.md) |
| [EX-0013](#ex-0013) | Vector Tile Runtime and CSP Failures | [note](../exchanges/0013-20260213-vector-tile-runtime-csp-failures.md) |
| [EX-0014](#ex-0014) | Constrained CV1 Postcode Tool Probes | [note](../exchanges/0014-20260214-constrained-cv1-postcode-tool-probes.md) |
| [EX-0015](#ex-0015) | Surrounding Postcodes and Road Workbook Request | [note](../exchanges/0015-20260214-surrounding-postcodes-road-workbook-request.md) |

## Conversation

<a id="ex-0011"></a>

### EX-0011: CV1 Map Request Produces Fragile HTML Output

- User timestamp precision: date only (`2026-02-13`)
- Standalone note: [EX-0011](../exchanges/0011-20260213-cv1-map-request-fragile-html-output.md)

#### User Prompt

```text
show me cv1 3hb on a map
```

#### Curated Outcome

```text
The client found plausible CV1 3HB address/location data, but delivered it through brittle standalone HTML. The failure was not the postcode lookup; it was the map rendering surface and the model-generated dependency chain.
```

<a id="ex-0012"></a>

### EX-0012: OS Mapping and API-Key Handling Drift

- User timestamp precision: date only (`2026-02-13`)
- Standalone note: [EX-0012](../exchanges/0012-20260213-os-mapping-api-key-handling-drift.md)

#### User Prompt

```text
Use OS Mapping, fix the repeated browser-library error, and keep the OS API key out of conversation logs.
```

#### Curated Outcome

```text
The client recognized the need for secure key handling and attempted browser-side entry, but still relied on a generated page that did not reliably load the required map runtime. The useful lesson is that credentials belong in server/runtime configuration and map delivery needs a host-compatible contract.
```

<a id="ex-0013"></a>

### EX-0013: Vector Tile Runtime and CSP Failures

- User timestamp precision: date only (`2026-02-13`)
- Standalone note: [EX-0013](../exchanges/0013-20260213-vector-tile-runtime-csp-failures.md)

#### User Prompt

```text
Use vector tiles; the generated MapLibre page is still failing.
```

#### Curated Outcome

```text
The client pivoted to MapLibre and OS vector tiles, but the host environment blocked successive generated artifacts through missing globals, worker restrictions, and cross-origin/CSP limits. Vector tiles were the right technical direction, but the delivery pattern still lacked host awareness.
```

<a id="ex-0014"></a>

### EX-0014: Constrained CV1 Postcode Tool Probes

- User timestamp precision: date only (`2026-02-14`)
- Standalone note: [EX-0014](../exchanges/0014-20260214-constrained-cv1-postcode-tool-probes.md)

#### User Prompt

```text
Make exactly one MCP tool call for CV1 3HB and return only the first address string.
```

#### Curated Outcome

```text
The narrow tool-call probes succeeded because they reduced the task to a verifiable OS Places lookup. They showed that the data path for CV1 3HB was stable and that the earlier failures were caused by broad presentation/runtime behaviour.
```

<a id="ex-0015"></a>

### EX-0015: Surrounding Postcodes and Road Workbook Request

- User timestamp precision: date only (`2026-02-14`)
- Standalone note: [EX-0015](../exchanges/0015-20260214-surrounding-postcodes-road-workbook-request.md)

#### User Prompt

```text
List road names and UPRN counts with types, then produce a workbook keyed on roads with bounding-box classification.
```

#### Curated Outcome

```text
The conversation moved toward structured data products: postcode grouping, road-level counts, property-type breakdowns, bounding-box size, and boundary-crossing classification. That is a more auditable MCP-Geo output shape than repeated ad hoc map repair.
```

## Summary

CONV-002 preserves the main client-design lesson from the CV1 examples: a broad
map request can push the model into fragile generated artifacts, while a narrow
tool call produces stable evidence. For user-facing maps, MCP-Geo should prefer
server-owned map descriptors/resources and explicit fallback metadata over
chat-generated HTML that must guess the host runtime.
