# VS Code MCP Setup (Copilot Chat + MCP-Apps)

This repo includes a VS Code workspace MCP configuration at `.vscode/mcp.json`.

## Requirements

- VS Code with MCP support enabled (MCP is GA in VS Code `>= 1.102`).
- GitHub Copilot + Copilot Chat installed and signed in.
- Use **Agent mode** in Copilot Chat (tools are only available in Agent mode).

## Servers Included (Workspace)

Defined in `.vscode/mcp.json`:

- `mcp-geo` (STDIO): runs `python3 scripts/vscode_mcp_stdio.py` from the workspace root and enables MCP-Apps UI.
- `mcp-geo-trace` (STDIO + trace): wraps the same server with `scripts/mcp_stdio_trace_proxy.py`.
- `mcp-geo-http` (HTTP): points to `http://127.0.0.1:8000/mcp` (you must run `uvicorn` yourself).

The config uses a VS Code `inputs` prompt for `OS_API_KEY` and stores it in VS Code
secure storage (it is not written to the repo).

If you prefer environment variables instead, replace `${input:osApiKey}` with
`${env:OS_API_KEY}` in `.vscode/mcp.json` and ensure `OS_API_KEY` is set in the
environment where VS Code runs (or in the devcontainer `containerEnv`).

Note: `scripts/vscode_mcp_stdio.py` exists because VS Code may launch MCP stdio
servers using the host Python. On macOS, it will automatically prefer the repo
venv at `.venv/` if present to avoid missing dependencies (for example `loguru`).

## Start and Verify

1. Open this repo folder in VS Code.
2. Command Palette: `MCP: List Servers` and confirm `mcp-geo` is present.
3. Start `mcp-geo` (or `mcp-geo-trace`) from the MCP Servers UI.
4. If it fails to start, check the VS Code **Output** panel for an MCP-related channel.

## Quick Smoke Tests (Agent Mode)

In Copilot Chat, switch to **Agent mode**, then try:

- "List available tools for mcp-geo."
- "Call `os_mcp.route_query` with: Open a map so I can select wards in Westminster."
- "Open the geography selector UI (`os_apps.render_geography_selector`)."
- "Probe UI rendering support (`os_apps.render_ui_probe`)."

## Tracing (Recommended for Client Interop Debugging)

Use `mcp-geo-trace` and reproduce the issue in Agent mode. It writes:

- `logs/vscode-mcp-trace.jsonl` (all MCP JSON-RPC requests/responses)
- `logs/ui-events.vscode-trace.jsonl` (MCP-Apps UI events via `os_apps.log_event`)

To snapshot these into a per-run session directory (and generate a report):

```bash
python scripts/vscode_trace_snapshot.py
```

These logs are the fastest way to confirm what VS Code advertised in
`initialize` (capabilities) and what the server returned for UI tools.
