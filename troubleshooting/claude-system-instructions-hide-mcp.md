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
