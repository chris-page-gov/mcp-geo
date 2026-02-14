# Troubleshooting & Error Codes

This guide lists common error codes emitted by the MCP Geo server and suggested remediation steps.

| Code | Meaning | Typical Cause | Remediation |
|------|---------|---------------|-------------|
| INVALID_INPUT | Input validation failed | Missing or malformed parameters (e.g. postcode format) | Re-check required fields, normalize postcode (strip spaces, uppercase) |
| UNKNOWN_TOOL | Tool name not registered | Typo in `tool` field or outdated client cache | Call `/tools/list` or `/tools/describe` to confirm names |
| NO_API_KEY | OS API key absent | `OS_API_KEY` env not set | Export `OS_API_KEY` or add to `.env` then restart server |
| OS_API_KEY_INVALID | OS API key invalid or unauthorized | Wrong key, not enabled for API, or revoked | Verify key in OS Data Hub; ensure APIs are enabled |
| OS_API_KEY_EXPIRED | OS API key expired | Key has expired or is no longer active | Rotate the key in OS Data Hub and update `OS_API_KEY` |
| LIVE_DISABLED | Live data disabled | `ONS_LIVE_ENABLED` or `ADMIN_LOOKUP_LIVE_ENABLED` set to false | Enable live mode and retry |
| OS_API_ERROR | Upstream OS API non-200 response | External API returned error (quota, bad request) | Inspect message snippet; adjust parameters or check quota |
| ONS_API_ERROR | Upstream ONS API non-200 response | External API returned error (quota, bad request) | Inspect message snippet; adjust dataset/edition/version |
| NOMIS_API_ERROR | Upstream NOMIS error | NOMIS API returned error or blocked request | Inspect message snippet; adjust parameters or check API availability |
| NOMIS_QUERY_ERROR | NOMIS rejected query | Invalid or unsupported query parameters | Simplify params, verify dataset/codelists, retry with known-good examples |
| ADMIN_LOOKUP_API_ERROR | Upstream ArcGIS error | ONS Open Geography returned error | Retry; verify service availability |
| UPSTREAM_TLS_ERROR | TLS handshake failure | Network / certificate issue | Retry later; verify container trust store and target host availability |
| UPSTREAM_CONNECT_ERROR | Connection or timeout exhaustion | Network instability or endpoint downtime | Reduce concurrency, add backoff, confirm endpoint status |
| UPSTREAM_INVALID_RESPONSE | Upstream returned invalid JSON | Non-JSON or truncated upstream response | Retry; check upstream service status and authentication |
| INTEGRATION_ERROR | Unexpected exception during call | Unhandled edge case or library error | Capture logs with correlationId; file issue with stack trace (if DEBUG_ERRORS enabled) |
| RATE_LIMITED | In-memory rate limit exceeded | High request volume to same path | Slow down; implement client-side rate limiting/backoff; raise limit if safe |
| UNKNOWN_FILTER | Referenced filter id not found | Expired or incorrect filter identifier | Recreate filter via `ons_data.create_filter` and use returned `filterId` |
| NO_OBSERVATION | Observation not found | Invalid combination (geography / measure / time) | List dimensions (`ons_data.dimensions`), verify codes before querying |
| NOT_FOUND | Resource or area id missing | Invalid admin boundary id | Use `admin_lookup.find_by_name` or `reverse_hierarchy` to locate valid ids |
| ELICITATION_CANCELLED | User declined/cancelled elicitation prompt | Comparison routing prompt was dismissed | Re-run stats routing with explicit `comparisonLevel`/`providerPreference` or accept prompt |
| ELICITATION_INVALID_RESULT | Client returned malformed elicitation result | Client bug or unsupported elicitation response shape | Update client MCP support or disable elicitation (`MCP_STDIO_ELICITATION_ENABLED=0` / `MCP_HTTP_ELICITATION_ENABLED=0`) |
| ELICITATION_UNAVAILABLE | No elicitation response arrived | Client announced support but did not answer prompt | Retry, verify client capability handling, or disable elicitation for deterministic flow |

## `os_features.query` returns an XML `ExceptionReport`
If `os_features.query` returns an `OS_API_ERROR` whose message starts with XML (for example `<?xml ... <ExceptionReport ...>`),
it usually means the upstream OS endpoint rejected the request (wrong endpoint, unknown collection id, or missing entitlement).

Remediation:
- Ensure you are running a build that targets OS NGD OGC API Features (`features/ngd/ofa/v1/collections/{collection}/items`).
  If using `scripts/claude-mcp-local`, set `MCP_GEO_DOCKER_BUILD=always` at least once so the Docker image is rebuilt.
- Confirm the `collection` id is valid and enabled for your OS Data Hub key.

## MCP-Apps UI "unsupported format"
If the client reports an unsupported format error after calling an `os_apps.render_*`
tool, it is usually rejecting the `resource_link` content block.

Remediation:
- Set `MCP_APPS_CONTENT_MODE=embedded` to embed UI HTML as a `resource` content block.
- Or set `MCP_APPS_CONTENT_MODE=text` to emit text-only tool content.
- Keep `MCP_APPS_RESOURCE_LINK=0` for Claude Desktop unless trace evidence shows
  `resource_link` rendering works in your current Claude build.
- Use `os_apps.render_ui_probe` to test which modes the client renders.
- Use `python3 scripts/mcp_ui_mode_probe.py --save logs/ui-probe.json -- ./scripts/claude-mcp-local`
  to verify STDIO payload shapes for `resource_link`, `embedded`, and `text`.

Notes:
- `scripts/claude-mcp-local` now defaults to `MCP_APPS_RESOURCE_LINK=0` and
  `MCP_APPS_CONTENT_MODE=embedded`.
- JSON trace lines with `direction=server->stderr` are diagnostics; they are not
  MCP JSON-RPC payloads.

## Widget rendering unavailable in a host
If the host does not advertise `io.modelcontextprotocol/ui` (or renders no
widget output), use compatibility mode instead of retrying widget calls.

Remediation:
- Start with `os_maps.render` and treat it as the canonical baseline.
- Consume fallback skeleton contracts (`map_card`, `overlay_bundle`,
  `export_handoff`) from tool outputs.
- Keep startup discovery lean with `MCP_TOOLS_DEFAULT_TOOLSET=starter`.
- Use targeted post-init discovery (`toolset` / `includeToolsets`) only when
  you need additional tools.

Reference docs:
- `docs/spec_package/06_api_contracts.md`
- `docs/spec_package/06a_map_delivery_fallback_contracts.md`
- `docs/map_delivery_support_matrix.md`

## Mixed UI / no-UI host fleet drift
If one host renders widgets and another does not, enforce deterministic
degradation instead of host-specific ad hoc payloads.

Remediation:
- Keep one fallback contract set (`map_card`, `overlay_bundle`, `export_handoff`).
- Log and inspect `degradationMode` and `widgetUnsupportedReason`.
- Use style profiles from
  `resource://mcp-geo/map-embedding-style-profiles` for constrained hosts.
- Validate both UI-supported and UI-unsupported replay fixtures in map trials.

Reference bundle:
- `docs/map_embedding_best_practices.md`

## OS VTS labels missing for custom symbol layers
If custom label layers render without text on OS Vector Tile Service basemaps,
the style is usually referencing glyph assets that are not available for
arbitrary custom symbol layers.

Remediation:
- Prefer HTML markers / DOM overlays for custom labels and highlighted points.
- Keep OS VTS for the basemap itself; render your interactive annotations in a
  separate overlay layer (for example, `new maplibregl.Marker(...)`).
- If you need style-only map output, use icon/circle/fill/line layers that do
  not rely on custom glyph text rendering.

## VS Code MCP server start fails: "cannot find script" / path context
If VS Code fails to start `mcp-geo` / `mcp-geo-trace` and reports it cannot find a script,
it’s usually a **launch context** issue (working directory / variable substitution), not a missing file.

What to do:
- Prefer repo-root relative paths and set `cwd` to the repo root.
  - This repo’s known-good configuration is in `.vscode/mcp.json`.
- Avoid relying on `${workspaceFolder}` substitution unless you have confirmed your MCP launcher expands it.
  - Some launchers treat it literally, producing non-existent paths like `${workspaceFolder}/scripts/os-mcp`.

Notes:
- For repo-local dev, `scripts/os-mcp` is supported.
- `scripts/os_mcp.py` defensively adds the repo root to `sys.path` so `python3 scripts/os-mcp` works reliably.

## STDIO server start fails: `ModuleNotFoundError` (for example `loguru`)
If an MCP client starts the STDIO server with a Python interpreter that does not have the
repo dependencies installed, you may see errors like:

- `ModuleNotFoundError: No module named 'loguru'`

Remediation:
- VS Code: use the repo’s `.vscode/mcp.json` which runs `scripts/vscode_mcp_stdio.py` to select the
  appropriate Python environment.
- Local dev (macOS): ensure the repo venv exists and deps are installed (example: `python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'`),
  then run `./scripts/os-mcp` from that activated venv.
- Devcontainer: rebuild/reopen the devcontainer so `postCreateCommand` installs dependencies inside the container.

## Client context/window is exhausted after initialization
If the client fails early with "context too long" style errors, it is usually
because it requests `tools/list` with empty params and receives all tool schemas.

Remediation:
- Set `MCP_TOOLS_DEFAULT_TOOLSET=starter` for lean startup discovery.
- Or set `MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS=<csv>` to scope startup tools to your workflow
  (for example `core_router,places_names,maps_tiles`).
- Keep explicit request filters available: clients can still pass `toolset`,
  `includeToolsets`, or `excludeToolsets` on `tools/list` / `tools/describe`.
- Avoid loading full trace logs into model context; inspect with `rg`, `head`, or `tail`
  when diagnosing large traces.

## Claude error: `parent_message_uuid` must be a UUID
If Claude shows an error like:

`parent_message_uuid: Input should be a valid UUID ... found 'n' at 1`

this is a Claude host/session metadata error, not an `mcp-geo` tool payload
validation error.

How to confirm:
- Check MCP trace logs (`logs/claude-trace.jsonl`) for `parent_message_uuid`.
- If it does not appear in `client->server`/`server->client` JSON-RPC payloads,
  the failure is outside MCP tool exchange.

Remediation:
- Start a new Claude chat (do not reuse the failing thread).
- Restart Claude Desktop.
- Retry with `MCP_APPS_CONTENT_MODE=embedded` and `MCP_APPS_RESOURCE_LINK=0`.
- If reproducible, report to Anthropic with timestamp and screenshot.

## General Debug Steps
1. Capture correlationId from response headers/logs for traceability.
2. Reproduce with minimal payload and add parameters progressively.
3. Use `/tools/describe?name=<tool>` to confirm required fields and types.
4. If the tool list is large, use `/tools/search` to locate the right tool quickly.
5. Validate network connectivity (e.g., container DNS) if upstream errors persist.
6. Monitor rate limiting metrics (if enabled) to tune client request pacing.

## ArcGIS Geometry Notes
Some ArcGIS services omit `extent` when returning geometry. The server now computes
bboxes from geometry when needed; if you see `ADMIN_LOOKUP_API_ERROR` for
`admin_lookup.area_geometry` with `includeGeometry=true`, upgrade to a build that
includes this fix.

## Conditional Requests & Caching
If receiving repeated full payloads for static resources, ensure you supply the prior `etag` via `ifNoneMatch` (HTTP) or `ifNoneMatch` param (STDIO) for efficient `304`/`notModified` responses.

## When to Enable DEBUG_ERRORS
Set `DEBUG_ERRORS=true` only in development; it exposes stack traces that aid debugging but may leak implementation details in production.
