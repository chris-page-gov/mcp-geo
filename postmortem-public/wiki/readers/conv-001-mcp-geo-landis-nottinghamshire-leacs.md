---
source_id: "CONV-001"
title: "LandIS, Nottinghamshire Coverage, and LEACS Access Probe Reader"
reader_type: "curated_start_to_finish_conversation"
publication_status: "public-safe-curated-derivative"
exchange_count: 10
tags:
  - "reader"
  - "conversation"
  - "mcp-geo"
  - "llm-wiki"
---

# CONV-001: LandIS, Nottinghamshire Coverage, and LEACS Access Probe

This public reader inlines the curated prompt-response exchanges for one MCP-Geo conversation in chronological order. It preserves sequence, decisions, and evidence, but it is not a raw Codex transcript.

## Navigation

- Index: [MCP-Geo Public Conversation Wiki](../index.md)
- Conversation source note: [CONV-001](../sources/conv-001-mcp-geo-landis-nottinghamshire-leacs.md)
- Raw transcript: not exported into this repository.

## Exchange Map

| Exchange | Prompt Theme | Standalone Note |
|---|---|---|
| [EX-0001](#ex-0001) | Launch MCP-Geo Server for Demonstration | [note](../exchanges/0001-20260513-launch-mcp-geo-server-for-demonstration.md) |
| [EX-0002](#ex-0002) | Assess Nottinghamshire Geotechnical Earthworks Collapse Risk | [note](../exchanges/0002-20260513-assess-nottinghamshire-geotechnical-earthworks-collapse-risk.md) |
| [EX-0003](#ex-0003) | Explain LandIS Warehouse Unavailability | [note](../exchanges/0003-20260513-explain-landis-warehouse-unavailability.md) |
| [EX-0004](#ex-0004) | Troubleshoot Missing Postgres | [note](../exchanges/0004-20260513-troubleshoot-missing-postgres.md) |
| [EX-0005](#ex-0005) | Extend LandIS Coverage to Nottinghamshire | [note](../exchanges/0005-20260513-extend-landis-coverage-to-nottinghamshire.md) |
| [EX-0006](#ex-0006) | Mount ExtSSD-Data and Recheck Archives | [note](../exchanges/0006-20260513-mount-extssd-data-and-recheck-archives.md) |
| [EX-0007](#ex-0007) | Check LEACS Provenance | [note](../exchanges/0007-20260513-check-leacs-provenance.md) |
| [EX-0008](#ex-0008) | Probe LEACS Download Routes | [note](../exchanges/0008-20260513-probe-leacs-download-routes.md) |
| [EX-0009](#ex-0009) | Document LEACS Access and Future Conditions | [note](../exchanges/0009-20260513-document-leacs-access-and-future-conditions.md) |
| [EX-0010](#ex-0010) | Create MCP-Geo Conversation LLM Wiki | [note](../exchanges/0010-20260513-create-mcp-geo-conversation-llm-wiki.md) |

## Conversation

<a id="ex-0001"></a>

### EX-0001: Launch MCP-Geo Server for Demonstration

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0001](../exchanges/0001-20260513-launch-mcp-geo-server-for-demonstration.md)

#### User Prompt

```text
Don't change anything, this is to test the functionality of mcp-geo. Is the server running and are you connected?

Can you launch the server so I can demonstrate
```

#### Curated Codex Response

```text
Checked the local MCP-Geo environment, treated the request as a no-code-change server/runtime task, loaded live OS access from secure local configuration, and launched the FastAPI MCP server for demonstration. The response avoided exposing the OS API key or secret file content.
```

<a id="ex-0002"></a>

### EX-0002: Assess Nottinghamshire Geotechnical Earthworks Collapse Risk

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0002](../exchanges/0002-20260513-assess-nottinghamshire-geotechnical-earthworks-collapse-risk.md)

#### User Prompt

```text
Use MCP-Geo: Which Geotechnical earthworks are most at risk from collapse in Nottinghamshire
```

#### Curated Codex Response

```text
Used MCP-Geo administrative lookup and OS NGD landform-style data to screen Nottinghamshire for collapse-relevant geotechnical earthwork features. The curated result treated collapsed shafts/adits and former mineral workings as the highest-risk feature classes, with caves/historic cave features and artificial extraction slopes as additional screening categories. The output was framed as a prioritization screen, not an engineering safety assessment.
```

<a id="ex-0003"></a>

### EX-0003: Explain LandIS Warehouse Unavailability

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0003](../exchanges/0003-20260513-explain-landis-warehouse-unavailability.md)

#### User Prompt

```text
Why was The LandIS warehouse unavailable
```

#### Curated Codex Response

```text
Explained that the LandIS warehouse failure was local runtime/data availability rather than a LandIS concept failure: the repository had LandIS tooling, but the effective DSN/table state was missing or incomplete for the requested pipe-risk path. The answer separated MCP server health from Docker/PostGIS availability and loaded LandIS table coverage.
```

<a id="ex-0004"></a>

### EX-0004: Troubleshoot Missing Postgres

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0004](../exchanges/0004-20260513-troubleshoot-missing-postgres.md)

#### User Prompt

```text
Troubleshoot the missing Postgress
```

#### Curated Codex Response

```text
Inspected the local Docker/PostGIS topology, recovered a working PostGIS sidecar path, and verified that the phase-2 LandIS archive tables could support NATMAP, Soilscapes, and NSI-style queries. This narrowed the remaining gap to LEACS-derived pipe-risk data rather than all LandIS data.
```

<a id="ex-0005"></a>

### EX-0005: Extend LandIS Coverage to Nottinghamshire

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0005](../exchanges/0005-20260513-extend-landis-coverage-to-nottinghamshire.md)

#### User Prompt

```text
Extend coverage to Nottinghamshire
```

#### Curated Codex Response

```text
Confirmed that Nottinghamshire soil-context coverage could be extended through loaded LandIS archive products, but pipe-risk coverage could not be extended honestly without the missing LEACS attributes. The response preserved the distinction between proxy screening and LEACS-derived pipe-risk classification.
```

<a id="ex-0006"></a>

### EX-0006: Mount ExtSSD-Data and Recheck Archives

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0006](../exchanges/0006-20260513-mount-extssd-data-and-recheck-archives.md)

#### User Prompt

```text
Do I need to mount ExtSSD-Data?

I've mounted the ExtSSD-Data drive which should have everything you need, can you take another look?
```

#### Curated Codex Response

```text
Confirmed that the external drive was needed for the broad LandIS archive. After it was mounted, inspected the archive and an external Postgres data directory using a no-touch posture for the original. The archive contained useful public/provenance material and phase-2 data, but no LEACS data table.
```

<a id="ex-0007"></a>

### EX-0007: Check LEACS Provenance

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0007](../exchanges/0007-20260513-check-leacs-provenance.md)

#### User Prompt

```text
Do we have the provenance, I think it was an agentic download?
```

#### Curated Codex Response

```text
Recovered provenance that earlier agentic collection captured public LandIS LEACS pages and data.gov.uk package pages in the full-release archive. That provenance showed public metadata and web pages, not a downloaded LEACS payload suitable for PostGIS loading.
```

<a id="ex-0008"></a>

### EX-0008: Probe LEACS Download Routes

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0008](../exchanges/0008-20260513-probe-leacs-download-routes.md)

#### User Prompt

```text
So can we go and download it?

yes

signed in with [PORTAL_ACCOUNT]

So can you download the missing data?
```

#### Curated Codex Response

```text
Checked public CKAN/data.gov.uk metadata and then used a fresh authenticated portal route for live probing without printing or persisting the token. Direct searches and a deeper portal item/service/table/field scan found no LEACS, corrosivity, shrink-swell, or equivalent fields. No missing LEACS dataset could be downloaded from the available routes.
```

<a id="ex-0009"></a>

### EX-0009: Document LEACS Access and Future Conditions

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0009](../exchanges/0009-20260513-document-leacs-access-and-future-conditions.md)

#### User Prompt

```text
Can you document this and capture useful metadata so we will know if this is a possibility for future requests?
```

#### Curated Codex Response

```text
Added a durable LEACS access probe report and machine-readable metadata record. The documentation states the negative result, the public and authenticated routes checked, the conditions that would make future download possible, and the rule that Nottinghamshire pipe-risk expansion must be labelled as proxy unless LEACS becomes available.
```

<a id="ex-0010"></a>

### EX-0010: Create MCP-Geo Conversation LLM Wiki

- User timestamp precision: date only (`2026-05-13`)
- Standalone note: [EX-0010](../exchanges/0010-20260513-create-mcp-geo-conversation-llm-wiki.md)

#### User Prompt

```text
Create an llm-wiki record of the conversations of mcp-geo in the same form as we did for the ai-engineering-lab-hackathon-london-2026 project/repo
```

#### Curated Codex Response

```text
Created this public-safe conversation wiki using the same navigational form as the hackathon postmortem: index, source note, start-to-finish reader, standalone exchange notes, and JSON registers. The record is marked as curated because no raw transcript export was available in the repository.
```
