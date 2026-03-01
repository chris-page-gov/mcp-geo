# Figma MCP Setup and Capture Runbook (Codex Desktop)

This runbook documents the exact setup and troubleshooting sequence used in this repository.

Date: 2026-03-01

## 1) Configure Figma MCP in Codex

Add this to `~/.codex/config.toml`:

```toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"

[features]
unified_exec = true
shell_snapshot = true
rmcp_client = true
```

Notes:

- `rmcp_client = true` is required for streamable HTTP OAuth flows.
- If this section already exists, verify there is no `enabled = false` for `figma`.

## 2) Restart and verify server registration

After editing config, restart Codex Desktop and open a new session.

Verification command:

```bash
codex mcp list --json
```

Expected:

- entry for `figma`
- `enabled: true`
- `transport.type: "streamable_http"`
- `auth_status: "o_auth"`

## 3) Authenticate (if required)

If tools are not available, run:

```bash
codex mcp login figma
```

Then verify identity via MCP:

- call `figma.whoami` from the agent
- expected: user email/handle and plan info

## 4) Confirm Figma MCP is loaded in this session

From the agent/tooling side:

- `list_mcp_resources(server="figma")` should return Figma docs/resources
- `list_mcp_resource_templates(server="figma")` should return templates

If these return unknown server, restart session/app again.

## 5) Local page capture workflow used here

For local HTML pages in this repo:

1. Add capture script tag to target page:

```html
<script src="https://mcp.figma.com/mcp/html-to-design/capture.js" async></script>
```

2. Serve local page (example):

```bash
cd docs/design/figma
python3 -m http.server 4173 --bind 127.0.0.1
```

3. Create capture ID via `generate_figma_design`:

- first capture: `outputMode="newFile"`
- additional captures: `outputMode="existingFile"` + `fileKey`

4. Open capture URL with hash params:

```bash
open "http://127.0.0.1:4173/<page>.html#figmacapture=<captureId>&figmaendpoint=<encoded-endpoint>&figmadelay=1200"
```

5. Poll until complete using `generate_figma_design(captureId=...)`.

## 6) Known fidelity issue and workaround

Observed issue:

- captures of pages that embed complex SVG text can produce broken glyphs/square boxes in Figma.

Workaround used:

- recapture using native HTML/CSS wireframe blocks (not SVG text).
- this produced cleaner editable text and structure in Figma.

## 7) Artifacts used in this repo

- Initial capture page: `docs/design/figma/compact_ui_proposals.html`
- Native recapture page: `docs/design/figma/compact_ui_proposals_native.html`
- SVG wireframes (reference): `docs/design/figma/mcp_apps_small_window_wireframes.svg`

## 8) Practical recommendation

Use Figma MCP for:

- quick stakeholder visibility
- collaborative annotation after capture

Do design decision-making in repo docs first when:

- host constraints are the main problem
- capture fidelity risks obscuring decisions
