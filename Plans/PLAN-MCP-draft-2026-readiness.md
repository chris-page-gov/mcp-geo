# MCP Draft 2026 Readiness Assessment

Date: 2026-04-28
Status: preparation only; do not adopt `DRAFT-2026-v1` yet.

## Sources Checked

- Official stable/current docs: `https://modelcontextprotocol.io/specification/2025-11-25`
- Official versioning docs: `https://modelcontextprotocol.io/docs/learn/versioning`
- Official draft docs: `https://modelcontextprotocol.io/specification/draft`
- Upstream draft schema source:
  `https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/schema/draft/schema.ts`
- Upstream draft changelog:
  `https://modelcontextprotocol.io/specification/draft/changelog`

The current stable MCP protocol remains `2025-11-25`. The upstream draft schema now
declares `LATEST_PROTOCOL_VERSION = "DRAFT-2026-v1"`. This repo should continue to
negotiate stable protocol versions until the draft is released or the team explicitly
opts into draft interop testing.

## Impact Summary

### Protocol Negotiation

MCP-Geo currently supports `2025-11-25`, `2025-06-18`, `2025-03-26`, and
`2024-11-05` in `server/protocol.py`. A client requesting `DRAFT-2026-v1` will
currently negotiate back to `2025-11-25`, which is correct for stable support but will
not satisfy a draft-only client.

Preparation work should add a feature-gated draft compatibility mode rather than adding
the draft version to the default supported tuple.

### Capabilities and Extensions

The draft formalizes an `extensions` field in `ClientCapabilities` and
`ServerCapabilities`. MCP-Geo already advertises an `extensions` capability for
`io.modelcontextprotocol/ui` and already reads client extension data to detect MCP-Apps
UI support. This is a low-impact alignment area, but the extension declarations should be
centralized and tested against the draft schema before any draft protocol opt-in.

### Streamable HTTP Headers

The draft requires Streamable HTTP clients to send standard request headers:

- `Mcp-Method` for all POST requests and notifications.
- `Mcp-Name` for `tools/call`, `resources/read`, and `prompts/get`.

MCP-Geo's `/mcp` endpoint currently parses the JSON-RPC body and does not require those
headers. Moving straight to strict rejection would break existing clients. The safe path
is an observe-first mode that logs and metrics missing or mismatched headers, followed by
an opt-in strict mode, and only later default strict behavior if the requirement lands in
a stable spec and clients have caught up.

### Custom `x-mcp-header` Tool Parameters

The draft lets tool schemas mark primitive input parameters with `x-mcp-header`, causing
clients to mirror those values into `Mcp-Param-*` HTTP headers. MCP-Geo does not need this
for current tools. Adding these annotations would alter tool schemas and should be
treated as a tool contract change, including OWASP MCP manifest/risk-inventory refresh.

Preparation should add validation helpers and tests so future annotations cannot violate
the draft constraints.

### OpenTelemetry Trace Context in `_meta`

The draft documents trace context conventions for `_meta.traceparent`,
`_meta.tracestate`, and `_meta.baggage`. MCP-Geo currently has correlation IDs and
Prometheus metrics, and it passes some result `_meta` through to clients, but it does not
parse inbound MCP request `_meta` for W3C trace context or propagate it to logs, audit
events, or outbound OS/ONS requests.

This is useful preparation independent of the draft protocol bump, but it needs privacy
and redaction review before propagation, especially for `baggage`.

### Deterministic `tools/list`

The draft says servers should return `tools/list` in a deterministic order. MCP-Geo is
already close: `tools.registry.list_tools()` and `all_tools()` sort registry keys, and
the stdio and `/mcp` list paths build from those sorted tools unless a query rank is
requested. This should be locked with explicit regression tests across:

- stdio `tools/list`
- Streamable HTTP `/mcp` `tools/list`
- direct `GET /tools/list`
- compact startup catalog mode
- toolset-filtered listings
- sanitized tool-name listings

## Backlog

| ID | Priority | Work | Notes |
| --- | --- | --- | --- |
| MCP-DRAFT-1 | High | Track draft spec drift explicitly | Add draft docs/schema paths to spec drift checks and review upstream draft changelog monthly and before releases. |
| MCP-DRAFT-2 | High | Add feature-gated draft negotiation path | Support `DRAFT-2026-v1` only behind an explicit environment flag or test harness option; default remains stable `2025-11-25`. |
| MCP-DRAFT-3 | High | Add Streamable HTTP standard-header observe mode | Validate `Mcp-Method` and `Mcp-Name` when present, log/metric missing or mismatched values, and add an opt-in strict mode. |
| MCP-DRAFT-4 | Medium | Lock deterministic tool listing | Add regressions proving deterministic list ordering across stdio, `/mcp`, direct HTTP, compact startup, toolset-filtered, and sanitized-name paths. |
| MCP-DRAFT-5 | Medium | Centralize extension capability declarations | Create one registry/source for supported MCP extensions and validate initialize capability output against stable and draft expectations. |
| MCP-DRAFT-6 | Medium | Add `_meta` trace context handling design | Parse and validate `traceparent`, `tracestate`, and `baggage`; decide propagation/redaction policy before wiring to logs or upstream calls. |
| MCP-DRAFT-7 | Medium | Add `x-mcp-header` schema guardrails | Add validators for future tool-schema annotations; do not annotate current tools until there is a concrete routing or gateway need. |
| MCP-DRAFT-8 | Medium | Add draft conformance test harness | Run current stable tests plus draft-focused probes against stdio and Streamable HTTP without making draft behavior the default. |
| MCP-DRAFT-9 | Low | Client compatibility sweep | Re-run Claude, Codex, Gemini, VS Code, and Inspector interop after observe-mode headers and extension capability changes land. |

## Recommended Sequence

1. Update spec drift tracking and documentation only.
2. Add deterministic `tools/list` tests and extension capability tests.
3. Add HTTP header observe mode and metrics, with strict mode disabled by default.
4. Design trace context handling and redaction.
5. Only after upstream stabilizes the draft, decide whether to promote
   `DRAFT-2026-v1` or its final dated successor into `SUPPORTED_PROTOCOL_VERSIONS`.
