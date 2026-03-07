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
- `resources/list`, `resources/read` traffic

## 1b) Capture MCP JSON-RPC traffic (HTTP proxy)

For ChatGPT or any HTTP client, run the HTTP trace proxy in front of `/mcp`:

```bash
python scripts/mcp_http_trace_proxy.py \
  --upstream http://127.0.0.1:8000/mcp \
  --log logs/mcp-http-trace.jsonl \
  --host 127.0.0.1 \
  --port 8899
```

Point your HTTP client at `http://127.0.0.1:8899/mcp` (or tunnel that URL).

What you get in `logs/mcp-http-trace.jsonl`:
- Request/response headers (authorization redacted)
- JSON-RPC payloads for initialize, tools/list, tools/call, and resources/read
- Streamed SSE chunks (if any)

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

## 4b) VS Code quick setup example

This repo includes a workspace MCP config at `.vscode/mcp.json` with a traced
server entry `mcp-geo-trace`. Start that server in VS Code, then reproduce the
workflow in Copilot Chat (Agent mode). Artifacts:

- MCP JSON-RPC: `logs/vscode-mcp-trace.jsonl`
- UI events: `logs/ui-events.vscode-trace.jsonl`

To snapshot these into a per-run session directory (and generate a report):

```bash
python scripts/vscode_trace_snapshot.py
```

## 5) What to look for

- `tools/search` calls in `logs/mcp-trace.jsonl` confirm tool search usage.
- `os_apps.log_event` entries in `logs/ui-events.jsonl` confirm UI actions.
- Use timestamps to correlate MCP tool calls with UI events.

## 6) One-command trace sessions (recommended)

If you want a single workflow that captures artifacts and generates a report:

STDIO (Claude Desktop / Claude Code):
```bash
python scripts/trace_session.py stdio
```

HTTP (Inspector / web clients):
```bash
python scripts/trace_session.py http
```

Each run creates a session directory under `logs/sessions/<timestamp>/` containing:
- `mcp-stdio-trace.jsonl` or `mcp-http-trace.jsonl`
- `ui-events.jsonl`
- `upstream.log`
- `session.json`
- `summary.json`
- `report.md`
- `bundle.zip`

To regenerate the report from an existing session:
```bash
python scripts/trace_report.py logs/sessions/<session-id>
```

To make STDIO capture automatic in Claude Desktop, set your MCP server command
to the trace session wrapper:

```json
{
  "mcpServers": {
    "mcp-geo": {
      "command": "python",
      "args": [
        "/path/to/mcp-geo/scripts/trace_session.py",
        "stdio",
        "--",
        "mcp-geo-stdio"
      ]
    }
  }
}
```

`session.json` can now carry host benchmark metadata:

- `source`: `codex`, `claude`, `vscode`
- `surface`: `cli`, `ide`, `desktop`
- `hostProfile`: for example `codex_cli_stdio`, `codex_ide_ui`
- `clientVersion`
- `model`
- `scenarioPack`
- `scenarioId`

For scored Codex vs Claude comparisons, use the dedicated benchmark runner and
runbook:

```bash
./.venv/bin/python scripts/host_benchmark.py scenario-pack
```

- Runbook: `docs/benchmarking/codex_vs_claude_host_benchmark.md`
