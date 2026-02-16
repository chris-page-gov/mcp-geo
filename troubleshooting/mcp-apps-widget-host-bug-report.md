# Bug Report: MCP-Apps UI Widget Host Runtime Not Starting After Successful `resources/read`

Sumbitted as https://github.com/modelcontextprotocol/modelcontextprotocol/issues/2247 
20250214-16:50

**Component:** Claude client (claude.ai / Claude in Chrome extension)
**Severity:** Functional gap — MCP-Apps interactive widgets are non-functional
**Date:** 2026-02-14
**Reporter:** Chris (Warwickshire County Council) — mcp-geo MCP server developer

---

## Summary

Claude's client successfully completes MCP-Apps resource discovery and fetch (`tools/call` → `resources/read` of `ui://` URIs), but never mounts the returned HTML widget in an iframe/webview or starts the postMessage bridge. Interactive MCP-Apps widgets are therefore completely non-functional despite the protocol's discovery and fetch phases working correctly.

This is a **runtime interoperability bug**, not a feature request. The client already participates in the MCP-Apps flow up to resource fetch — it simply does not complete the last mile.

---

## Environment

- **MCP Server:** mcp-geo (custom server providing UK geographic data via OS/ONS APIs)
- **Transport:** STDIO adapter
- **Client fingerprint in trace:** `clientInfo.name=claude-ai`, `clientInfo.version=0.1.0`
- **Client surfaces tested by operator:** claude.ai web interface, Claude in Chrome extension
- **Widgets affected:** All `os_apps_render_*` tools (boundary explorer, geography selector, statistics dashboard, route planner, feature inspector)

---

## Expected Behaviour

1. `tools/call` → `os_apps_render_*` → server returns `ui://mcp-geo/{widget}` in `_meta.ui.resourceUri` (and optionally `resource_link` content) ✅
2. Client calls `resources/read` on the `ui://` URI → server returns `text/html;profile=mcp-app` content ✅
3. Client mounts the returned HTML in an iframe/webview ❌
4. Client starts the postMessage bridge:
   - Widget sends `ui/initialize` with `appCapabilities`
   - Client relays `tools/call` JSON-RPC requests from the widget to the MCP server
   - Client forwards `ui/notifications/*` events
   - Widget becomes interactive ❌

## Actual Behaviour

Steps 1 and 2 succeed. After `resources/read` completes, nothing further happens:

- The HTML content is never rendered to the user
- The `ui://` URI string is passed back to the LLM as opaque text
- No widget-runtime activity reaches the server
- `os_apps_log_event` is never called
- The widget's `ui/initialize` handshake never occurs

---

## Trace Evidence

From `claude-trace.jsonl`, four independent sessions show the same pattern:
both `tools/call os_apps_render_*` and `resources/read ui://...` occur, then no
widget-runtime activity follows. (Ordering between the two calls can vary.)

| Session window (Unix) | Event sequence | Result |
|---|---|---|
| 1771085229.* | `tools/call` `1771085229.544111` + `resources/read` `1771085229.659928` | URI + HTML returned |
| 1771081739.* | `resources/read` `1771081739.394575` + `tools/call` `1771081739.837377` | URI + HTML returned |
| 1771075574.* | `tools/call` `1771075574.657804` + `resources/read` `1771075574.771148` | URI + HTML returned |
| 1771068355.* | `tools/call` `1771068355.396543` + `resources/read` `1771068355.423197` | URI + HTML returned |
| After each pair | *(no `ui/*` or widget bridge activity)* | session goes silent for MCP-Apps runtime |

The gap is consistent: `resources/read` succeeds → no iframe mount → no `ui/initialize` → no `tools/call` relay → no `os_apps_log_event`.

Concrete trace excerpt (same session):

- `1771085229.544111` `client->server` `tools/call` `os_apps_render_boundary_explorer`
- `1771085229.548673` `server->client` tool result includes:
  - `content[1].type = "resource_link"`
  - `content[1].uri = "ui://mcp-geo/boundary-explorer"`
  - `content[1].mimeType = "text/html;profile=mcp-app"`
- `1771085229.659928` `client->server` `resources/read` `ui://mcp-geo/boundary-explorer`
- `1771085229.66x` `server->client` `resources/read` result includes:
  - `contents[0].mimeType = "text/html;profile=mcp-app"`
  - `contents[0].text` contains full HTML document (`<!DOCTYPE html>...`)
- No subsequent `client->server` calls to `os_apps_log_event` or any `ui/*` methods.

---

## Server-Side Architecture (Confirmed Working)

The mcp-geo server correctly implements the MCP-Apps protocol:

- **Resource publishing:** `resources/list` + `resources/read` via `resource_catalog.py` — serves HTML content with `text/html;profile=mcp-app` media type
- **Tool metadata:** `os_apps_render_*` tools return `ui://` URIs in `_meta.ui.resourceUri` and optional `resource_link` content via `os_apps.py`
- **STDIO adapter:** Defaults Claude app calls to `contentMode=resource_link` via `stdio_adapter.py`
- **Widget protocol:** All widgets implement the MCP-Apps postMessage bridge contract:
  - `window.parent.postMessage({jsonrpc: "2.0", ...})` for RPC
  - `ui/initialize` handshake on load
  - `tools/call` requests for data fetching
  - `ui/notifications/size-changed` for responsive layout
  - `ResizeObserver`-based height reporting

**Verification:** The `os_apps_render_ui_probe` tool with `contentMode=embedded` successfully returns the full widget HTML, confirming the server serves valid content. A standalone reference host (Svelte + Playwright) in the dev repo successfully completes the full widget lifecycle including the postMessage bridge.

---

## Diagnosis

The break point is between `resources/read` (step 2) and iframe mount (step 3). The client:

1. **Does** recognise `ui://` URIs as resources requiring `resources/read` — this is implemented
2. **Does** successfully fetch the HTML content from the server
3. **Does not** mount the returned HTML in an iframe/webview
4. **Does not** wire up the postMessage bridge to relay JSON-RPC between the iframe and the MCP server

The `profile=mcp-app` media type hint should signal that this resource requires
interactive mounting rather than text-only consumption.

Important transport detail:
- This reproduction is over STDIO JSON-RPC, so there is no HTTP `Content-Type`
  header at this step.
- The media-type signal is present in MCP payload fields:
  - tool result `resource_link.mimeType`
  - `resources/read` result `contents[*].mimeType`

---

## Impact

All MCP-Apps interactive widgets are non-functional in Claude's client surfaces. This affects any MCP server that implements the MCP-Apps UI protocol for interactive data exploration, including:

- Geographic boundary selection and exploration
- Statistical data dashboards with interactive filtering
- Route planning with map visualisation
- Any widget requiring bidirectional communication between UI and MCP server tools

---

## Suggested Fix

The Claude client needs to:

1. **Detect `text/html;profile=mcp-app` content** from `resources/read` responses (or detect `_meta.ui.resourceUri` in tool call results)
2. **Mount the HTML in a sandboxed iframe** within the chat interface
3. **Implement the postMessage bridge:**
   - Listen for `window.postMessage` events from the iframe
   - Relay `tools/call` requests to the MCP server via the existing transport
   - Forward responses back to the iframe via `postMessage`
   - Handle `ui/notifications/*` events (e.g., `size-changed` for responsive layout)
4. **Complete the handshake:** Respond to the widget's `ui/initialize` call to signal host readiness

Optional diagnostics that would accelerate triage:
- Client-side log line when a `ui://` resource is resolved but iframe mount is skipped.
- Client-side log line when iframe mounts but bridge registration fails.
- Surface-level indication in chat when MCP-Apps runtime is unavailable for a specific message.

This is architecturally similar to how first-party tools like `places_map_display_v0` render interactive map widgets — the difference is that MCP-Apps widgets are served by third-party MCP servers rather than built into the client.

---

## Workarounds (Current)

- **Manual data retrieval:** Claude can call the underlying MCP tools directly (e.g., `admin_lookup_containing_areas`, `os_features_query`) and present results as text/tables, bypassing the interactive widget
- **Static HTML export:** Widget HTML can be saved as a file for the user to open in a browser, though without the postMessage bridge it shows "Awaiting host"
- **Local reference host:** Developers can use the standalone dev/test host shell for full widget lifecycle testing

---

## References

- MCP-Apps protocol specification: postMessage-based JSON-RPC bridge between iframe widgets and MCP servers
- mcp-geo server: UK geographic data MCP server implementing OS NGD + ONS statistical APIs with interactive UI widgets
- Trace file: `claude-trace.jsonl` (available on request)
