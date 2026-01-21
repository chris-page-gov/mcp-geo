# Client Trace Strategy (MCP Geo)

This strategy captures enough signal to answer questions like:
- "Is the client using tool search or only the always-loaded list?"
- "Which tools were called in response to a conversation?"
- "What UI interactions happened inside MCP-Apps widgets?"

It combines:
1) A stdio proxy log (MCP JSON-RPC traffic)
2) Optional client transcript export (visible assistant text)
3) UI interaction event logs from MCP-Apps

## 1) Capture MCP JSON-RPC traffic (stdio proxy)

Use the stdio proxy to log every JSON-RPC request/response between the client
and the MCP server.

```bash
python scripts/mcp_stdio_trace_proxy.py --log logs/mcp-trace.jsonl -- mcp-geo-stdio
```

Then point your MCP client to this proxy command instead of calling `mcp-geo-stdio`
(or `./scripts/os-mcp`) directly.

What you get in `logs/mcp-trace.jsonl`:
- `initialize` payloads (client capabilities)
- `tools/list`, `tools/search`, `tools/call` traffic
- `resources/list`, `resources/get` traffic

## 2) Capture UI interactions (MCP-Apps)

MCP-Apps widgets in this repo emit UI interaction events via the
`os_apps.log_event` tool. Events are written to a JSONL log file.

Default location:
- `logs/ui-events.jsonl`

Override with environment variable:
- `UI_EVENT_LOG_PATH=/path/to/ui-events.jsonl`

Example event record:
```json
{"eventId":"...","eventType":"select_result","source":"geography-selector","timestamp":1737400000.0,"payload":{"id":"E09000033","name":"Westminster"},"context":{"mode":"area","level":"local_auth"}}
```

Notes:
- Sensitive keys are redacted (`api_key`, `token`, `authorization`, etc.).
- Events are best-effort; if the client does not support MCP-Apps, no UI events
  will be captured.

## 3) Capture client transcript (optional)

MCP traffic alone does not include user prompts or the assistant's visible
messages. Export the conversation transcript from the client when possible and
store it alongside the MCP trace log.

Note: MCP does not expose model chain-of-thought. If you need a rationale, ask
the assistant to include a brief, user-visible explanation in its responses.

## 4) Claude Code quick setup example

Use the proxy and UI event logging together:

```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "python",
      "args": [
        "scripts/mcp_stdio_trace_proxy.py",
        "--log", "logs/claude-code-trace.jsonl",
        "--", "mcp-geo-stdio"
      ],
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "ONS_LIVE_ENABLED": "true",
        "UI_EVENT_LOG_PATH": "logs/ui-events.jsonl"
      }
    }
  }
}
```

## 5) What to look for

- `tools/search` calls in `logs/mcp-trace.jsonl` confirm tool search usage.
- `os_apps.log_event` entries in `logs/ui-events.jsonl` confirm UI actions.
- Use timestamps to correlate MCP tool calls with UI events.
