# Claude Demo Follow-Up: Floor Questions + Stop Analysis

Date: 2026-02-18
Analyst: Codex

## Scope

This report analyzes the demo behavior described in:

- `troubleshooting/claude-stopped-after-ngd-features.md`
- `logs/claude-trace.jsonl`

Goals:

1. Explain what we learned from the floor questions.
2. Explain why the hard query appeared to stop.
3. Provide detailed harness log examples showing what the trace captured.
4. Give mitigation steps, including intermittent train connectivity.

## Executive Summary

1. Forcing `mcp-geo` worked. The trace shows valid MCP tool calls and valid `200` responses.
2. One true upstream network failure occurred during the session: `UPSTREAM_CONNECT_ERROR` with `read timeout=5` from `api.os.uk`.
3. The final stop was not a server-side MCP error. The last hard call (`id=31`) returned `200` after a long runtime (~317s) with a very large payload.
4. The likely failure mode is host-side interruption after long, heavy tool-output accumulation (inference from logs and transcript markers).

## What The Floor Questions Taught Us

### Q1: "Can you force mcp-geo instead of web search?"

Yes, and this is validated in both transcript and trace:

- Transcript explicitly switches to MCP-only (`troubleshooting/claude-stopped-after-ngd-features.md:84`).
- Trace then shows direct MCP `tools/call` requests/responses (`logs/claude-trace.jsonl:3025` onward).

Key point: There was one UI-facing message `"No result received from client-side tool execution."` (`troubleshooting/claude-stopped-after-ngd-features.md:70`), but the MCP trace still shows a successful server response for that tool call (`status=200`).

### Q2: "Why did the hard question get far then stop?"

The session did progress far into NGD analysis. It then hit two stressors:

- A real upstream timeout on one call (`id=25`, `UPSTREAM_CONNECT_ERROR`).
- Very large and expensive NGD responses (`id=30`, `id=31`), with the final call taking ~317 seconds.

Transcript ends with `"Claude's response could not be fully generated"` (`troubleshooting/claude-stopped-after-ngd-features.md:490`) after the large water-features call.

## Key Timeline (from `logs/claude-trace.jsonl`)

| id | tool | latency_s | status | raw_bytes | notes |
|---:|---|---:|---:|---:|---|
| 15 | `os_names_find` | 0.510 | 200 | 12,003 | MCP worked despite UI confusion earlier |
| 16 | `admin_lookup_find_by_name` | 3.776 | 200 | 439 | Empty result set |
| 22 | `os_features_query` | 11.468 | 200 | 41,518 | Queryables + large schema payload |
| 25 | `os_features_query` | 15.624 | 501 | 578 | `UPSTREAM_CONNECT_ERROR` (`read timeout=5`) |
| 28 | `os_features_query` | 1.759 | 200 | 66,813 | Land features with rich fields |
| 30 | `os_features_query` | 2.495 | 200 | 555,546 | Very large inline response (100 features) |
| 31 | `os_features_query` | 317.381 | 200 | 271,223 | Long-running water query, 50 features, `nextPageToken=50` |

## Detailed Harness Log Examples

### Example A: UI said "no result", server still returned 200

Sources:

- UI text: `troubleshooting/claude-stopped-after-ngd-features.md:70`
- MCP trace: `logs/claude-trace.jsonl:3025`, `logs/claude-trace.jsonl:3026`

```json
{"ts":1771425277.634447,"direction":"client->server","method":"tools/call","id":15,"tool":"os_names_find","raw_bytes":145}
{"ts":1771425278.1448162,"direction":"server->client","id":15,"status":200,"raw_bytes":12003}
```

Interpretation: host/UI rendering can fail independently of MCP server success.

### Example B: True upstream timeout surfaced cleanly

Source: `logs/claude-trace.jsonl:3047`

```json
{
  "id":25,
  "status":501,
  "code":"UPSTREAM_CONNECT_ERROR",
  "message":"HTTPSConnectionPool(host='api.os.uk', port=443): Read timed out. (read timeout=5)"
}
```

Interpretation: this is a real upstream/network issue, not a hallucinated model failure.

### Example C: Payload pressure immediately before stop

Sources: `logs/claude-trace.jsonl:3057`, `logs/claude-trace.jsonl:3058`, `logs/claude-trace.jsonl:3059`, `logs/claude-trace.jsonl:3060`

```json
{"id":30,"direction":"client->server","tool":"os_features_query","args":{"includeGeometry":true,"limit":500}}
{"id":30,"direction":"server->client","status":200,"raw_bytes":555546}
{"id":31,"direction":"client->server","tool":"os_features_query","args":{"collection":"wtr-fts-water-3","includeGeometry":true,"limit":50}}
{"id":31,"direction":"server->client","status":200,"raw_bytes":271223,"count":50,"nextPageToken":"50"}
```

Interpretation: server remained healthy, but response size + latency became demo-hostile.

### Example D: Transcript-level stop marker

Sources:

- `troubleshooting/claude-stopped-after-ngd-features.md:450`
- `troubleshooting/claude-stopped-after-ngd-features.md:490`

Markers:

- `...[content truncated by stdio adapter; omitted ...]`
- `Claude's response could not be fully generated`

Interpretation: end-user break happened after high-volume data exchange.

## Harness Capabilities Demonstrated

This trace harness is giving high-value forensic visibility:

1. Directional capture (`client->server`, `server->client`, `server->stderr`).
2. Full JSON-RPC envelopes (`method`, `id`, params/result).
3. Precise timings for each step (epoch timestamps).
4. Payload size observability (`raw` length can be computed reliably).
5. Transport + startup diagnostics (container build/start lines on stderr).

This is enough to separate:

- host/UI failure,
- upstream API failure,
- and server implementation failure.

## Mitigation: Immediate (Travel / Intermittent Connectivity)

Use this during train/mobile demos:

1. Run "thin" first calls:
   - `includeGeometry=false`
   - `resultType="hits"`
   - low `limit` (10-25)
2. Only fetch geometry after narrowing candidates.
3. Page results (`nextPageToken`) instead of large single pulls.
4. Avoid broad bbox + rich fields + geometry in one call.
5. If a timeout appears, retry with smaller bbox and reduced fields.

Practical fallback pattern for NGD demos:

1. `resultType="hits"` for quick count.
2. `limit=10`, minimal `includeFields`.
3. One geometry call on selected subset.

## Mitigation: Harness/Server Enhancements (Recommended)

1. Add a "demo-safe mode" preset in tools docs/scripts with conservative defaults.
2. Add size guardrails for `os_features_query` (warn or auto-clamp when response risk is high).
3. Add optional response delivery mode (resource link/export) for large feature sets.
4. Make upstream timeout and retry policy user-tunable for unstable networks.
5. Add automatic tool-call fallback policy in demo prompts:
   - on timeout -> smaller bbox + no geometry + lower limit.

## Final Diagnosis

- `mcp-geo` did not crash in the hard-question sequence.
- There was one genuine upstream timeout.
- The final perceived stop most likely came from host-side generation/handling limits after long-latency, high-volume tool outputs.

This conclusion is strongly supported by the MCP trace and transcript markers, but host-internal Claude runtime logs are not present here, so host-specific root cause is inferred rather than directly logged.
