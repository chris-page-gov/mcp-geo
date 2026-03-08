# VS Code MCP Setup (Copilot Chat + MCP-Apps)

This repo includes a VS Code workspace MCP configuration at `.vscode/mcp.json`.

## Requirements

- VS Code with MCP support enabled (MCP is GA in VS Code `>= 1.102`).
- GitHub Copilot + Copilot Chat installed and signed in.
- Use **Agent mode** in Copilot Chat (tools are only available in Agent mode).

## Servers Included (Workspace)

Defined in `.vscode/mcp.json`:

- `mcp-geo` (STDIO): runs `python3 scripts/vscode_mcp_stdio.py` from the workspace root, enables MCP-Apps UI, and defaults discovery to `starter` plus `features_layers` so boundary explorer can call `os_map.inventory`/`os_map.export`.
- `mcp-geo-trace` (STDIO + trace): wraps the same server with `scripts/mcp_stdio_trace_proxy.py` and the same default toolset filters.
- `mcp-geo-http` (HTTP): points to `http://127.0.0.1:8000/mcp` (you must run `uvicorn` yourself).
- `openaiDeveloperDocs` (HTTP): points to `https://developers.openai.com/mcp` so
  VS Code Agent mode can read current OpenAI developer docs without relying on
  the deprecated local `docs/vendor/openai/` copies.

Tool set file for VS Code Configure Tools:

- Repo copy: `.vscode/mcp-geo.toolsets.jsonc`
- Install location (macOS): `~/Library/Application Support/Code/User/prompts/mcp-geo.toolsets.jsonc`

Quick install:

```bash
mkdir -p "$HOME/Library/Application Support/Code/User/prompts"
cp .vscode/mcp-geo.toolsets.jsonc \
  "$HOME/Library/Application Support/Code/User/prompts/mcp-geo.toolsets.jsonc"
```

The workspace config reads both `OS_API_KEY` and `OS_API_KEY_FILE` from the
host environment (`${env:OS_API_KEY}` / `${env:OS_API_KEY_FILE}`).
Important: for MCP servers, VS Code uses the host app process environment.
Window reload does not re-read shell exports from a terminal you opened later.
Use one of:

- define `OS_API_KEY` before launching VS Code, or
- define `OS_API_KEY_FILE` to a readable local secret file path before
  launching VS Code, or
- keep `OS_API_KEY` in repo `.env` (loaded by `server/config.py`).

If you change `OS_API_KEY` or `OS_API_KEY_FILE`, restart the MCP server from
the VS Code MCP Servers panel so the new value is picked up.

Note: `scripts/vscode_mcp_stdio.py` exists because VS Code may launch MCP stdio
servers using the host Python. On macOS, it will automatically prefer the repo
venv at `.venv/` if present to avoid missing dependencies (for example `loguru`).

## Start and Verify

1. Open this repo folder in VS Code.
2. Command Palette: `MCP: List Servers` and confirm `mcp-geo` and
   `openaiDeveloperDocs` are present.
3. Start `mcp-geo` (or `mcp-geo-trace`) from the MCP Servers UI.
4. If it fails to start, check the VS Code **Output** panel for an MCP-related channel.

## Quick Smoke Tests (Agent Mode)

In Copilot Chat, switch to **Agent mode**, then try:

- "List available tools for mcp-geo."
- "Use `openaiDeveloperDocs` to find the latest OpenAI Documentation MCP guidance."
- "Call `os_mcp.route_query` with: Open a map so I can select wards in Westminster."
- "Open the geography selector UI (`os_apps.render_geography_selector`)."
- "Probe UI rendering support (`os_apps.render_ui_probe`)."

## Boundary Explorer Harness (Recommended)

To validate boundary rendering and fullscreen-handshake behavior without VS Code
host/runtime variance, run the deterministic Playwright host harness:

```bash
npm --prefix playground run test:boundary-harness
```

This simulates MCP host messaging (`ui/initialize`, `ui/request-display-mode`,
`tools/call`) and asserts:

- selected boundary is present in map source data,
- selected boundary is rendered in boundary line/outline layers,
- fullscreen fallback messaging appears when the host does not confirm mode
  transition.

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
