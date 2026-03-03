# Troubleshooting Report: Claude says MCP is hidden/not connected despite `mcp.json`

Date: 2026-03-03  
Scope: Claude MCP interop behavior with `mcp-geo` in this repository

## Summary

Claude reported that `mcp-geo` tools were visible as "deferred tools" but also
claimed the MCP server was not connected for Artifact-style usage. Immediately
after being asked to run a concrete smoke test (`CV1 3HB`), the response failed
with "Claude's response could not be fully generated."

This points to a host/model capability-reporting failure, not a confirmed `mcp-geo` server outage.

## Evidence

- User transcript captured in this file showed a claimed state of
  "`mcp-geo` available as deferred tools."
- The same transcript also claimed "`mcp-geo` not connected in server list."
- Follow-up prompt caused generation interruption before tool execution result.
- Repo configuration confirms server entries exist in
  [`mcp.json`](/Users/crpage/repos/mcp-geo/mcp.json):
- `mcp-geo-stdio`
- `mcp-geo`
- `mcp-geo-docker`
- `mcp-geo-http`
- Local deterministic smoke call succeeds on current workspace (2026-03-03):
  - `./.venv/bin/python` invoking `stdio_adapter.handle_call_tool(...)` with
    `name="os_places_by_postcode"` and `postcode="CV1 3HB"`.
  - Returns `status=200` with valid UPRN results for `CV1 3HB`.

## Diagnosis

Most likely failure mode:

- Claude produced a capability narration that mixed internal tool inventory
  language with external MCP connection status assumptions.
- The follow-up interruption occurred at host response generation time, before
  a reliable positive/negative tool execution result was surfaced to the user.

This is consistent with existing repo guidance that some Claude failures are
host/runtime or post-transport handling issues rather than MCP server failures.

## Reproduction Pattern

1. Ask Claude if `mcp-geo` is accessible.
2. Claude replies with contradictory statements about availability/connectivity.
3. Ask for a concrete tool smoke call (for example `os_places_by_postcode`
   with `CV1 3HB`).
4. Claude may stop with "response could not be fully generated."

## Deterministic Workaround

Use this sequence in a fresh chat/session:

1. Ask Claude to verify access by executing a real call, not by describing server lists:
   - `mcp-geo:os_mcp_descriptor`
2. If Claude suggests a namespaced tool (for example
   `mcp-geo:os_places_by_postcode`), use that exact namespaced form.
3. Run smoke test:
   - `mcp-geo:os_places_by_postcode` with `{"postcode":"CV1 3HB"}`
4. Treat successful tool output as ground truth; ignore contradictory narration
   about connected server lists in the same message.
5. If generation still interrupts:
   - start a new Claude thread
   - restart Claude Desktop/web session
   - retry the same deterministic two-call sequence above.

## Prompt Guardrail (practical)

When this issue appears, prepend:

`Do not infer MCP availability from memory or UI lists. First execute`
`mcp-geo:os_mcp_descriptor`, then run
`mcp-geo:os_places_by_postcode` with `CV1 3HB`, and report only
execution results.

## Conclusion

For this incident, available evidence supports "host/model reporting
instability" over "mcp-geo server unavailable." The fastest mitigation is to
force concrete tool-call verification first and treat those results as
authoritative.

---

## Follow-up Incident (2026-03-03): Claude tool-search gate fails before tool visibility

### User-visible symptom

- Claude stated tools were not visible until it had completed a tool-search step.
- The displayed request shape was:
  - `{"query":"geographic location mapping Leamington High Street","limit":10}`
- Claude then stopped with "Claude's response could not be fully generated."

### Local reproduction and findings

- `tools/search` with that exact payload succeeds in this repo (stdio and HTTP):
  - `count=10`, no handler error, deterministic ranked results.
- Prior to the interop patch below, if a client sent search-style params on
  `tools/list` (for example `query`, `limit`), `mcp-geo` ignored them and
  returned the full catalog (`81` tools in this workspace), which can create
  unnecessary context pressure in constrained clients.

### Standards validation (MCP spec)

Validated against local vendored MCP standard docs/schemas:

- Standard `2025-11-25` defines `tools/list` and `tools/call` for tool
  discovery/invocation.
- Standard `tools/list` supports pagination (`nextCursor`) but does **not**
  define a standard `tools/search` method.
- Server `tools` capability is standard `listChanged`; custom behavior belongs
  under extensions/experimental contract.

Evidence paths:

- `docs/vendor/mcp/repos/modelcontextprotocol/docs/specification/2025-11-25/server/tools.mdx`
- `docs/vendor/mcp/repos/modelcontextprotocol/schema/2025-11-25/schema.json`
  - `ListToolsRequest`
  - `ListToolsResult`
  - `ServerCapabilities.tools`

### Fix applied in repo

- Updated `server/stdio_adapter.py` `handle_list_tools(...)`:
  - If `query`/`q` is present, it now performs ranked filtering (honoring
    `mode`, `limit`, `category`, and toolset filters) and returns a **filtered**
    `tools/list` result instead of the full catalog.
  - If `query` is absent, behavior remains unchanged (full/filtered-by-toolset
    list as before).

### Verification

- Focused tests:
  - `tests/test_stdio_adapter_direct.py::test_tools_list_query_filters_and_limits_results`
  - `tests/test_mcp_http.py::test_mcp_http_list_tools_query_filters_and_limits`
- Command:
  - `uv run --with pytest --with pytest-cov pytest -q --no-cov tests/test_stdio_adapter_direct.py tests/test_mcp_http.py`
  - Result: `61 passed`

### Practical mitigation for Claude sessions

1. Prefer `tools/list` query-limited discovery first (`query` + small `limit`).
2. If still interrupted, retry in a fresh Claude thread/session.
3. Use `os_mcp_descriptor` as a deterministic first call to confirm live tool
   access before deeper planning flows.
