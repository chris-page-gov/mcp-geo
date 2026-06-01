# Preview Specification & Feature Tracking

This file tracks preview or evolving specs/features that this repo depends on.

Process:
- Add an entry when a preview spec or preview feature is introduced or used.
- Record the spec URL, status, owner, last-checked date, and review cadence.
- Update entries on each release or when issues indicate a spec change.
- If the spec URL changes, update README + this table and note the reason.
- Run `python3 scripts/check_spec_drift.py` before release work or after
  refreshing vendored spec submodules so drift and broken local paths are
  detected explicitly rather than by ad hoc manual checks.

## Tracked Items

| Feature | Spec/Docs URL | Status | Owner | Last Checked | Review Cadence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| MCP specification | https://modelcontextprotocol.io/specification/2025-11-25 | Preview | maintainers | 2026-06-01 (vendored refresh plus RC impact review) | Each release | Stable runtime still defaults to `2025-11-25` and supports `2025-06-18`, `2025-03-26`, `2024-11-05`; HTTP validates `MCP-Protocol-Version` when provided. |
| MCP 2026-07-28 release candidate | https://modelcontextprotocol.io/specification/draft | Release candidate | maintainers | 2026-06-01 (submodules refreshed and feature-gated runtime tranche added) | Weekly until final; then each release | RC impact is tracked in `Plans/PLAN-MCP-2026-07-28-RC-alignment.md`. Runtime support is opt-in via `MCP_2026_RC_ENABLED=1` or `MCP_PROTOCOL_2026_07_28_ENABLED=1`; includes `server/discover`, stateless HTTP, per-request `_meta`, standard header strict mode, cache metadata, MRTR input-required results, RC resource-not-found mapping, and schema guardrails. |
| MCP draft core specification (`DRAFT-2026-v1`) | https://modelcontextprotocol.io/specification/draft | Superseded by 2026-07-28 RC tracking | maintainers | 2026-06-01 (rolled into RC alignment) | Kept for historical context | Stable runtime remains `2025-11-25`. The earlier readiness assessment remains in `Plans/PLAN-MCP-draft-2026-readiness.md`; active follow-up moved to `Plans/PLAN-MCP-2026-07-28-RC-alignment.md`. |
| MCP elicitation (form mode) | https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation | Preview | maintainers | 2026-02-06 (local trace + schema review) | Each release | Implemented for `os_mcp.stats_routing` in stdio when client advertises `elicitation.form`. |
| MCP-Apps UI (`text/html;profile=mcp-app`) | docs/vendor/mcp/repos/ext-apps/specification/2026-01-26/apps.mdx | Stable extension with active draft repo | maintainers | 2026-06-01 (submodule refreshed to `9a37ad7`) | Each release | Finalized MCP Apps spec (`2026-01-26`); refreshed repo includes server resource APIs, request teardown, pre-handshake guards, and current `_meta.ui.resourceUri` guidance. |
| MCP Auth extension (`ext-auth`) | docs/vendor/mcp/repos/ext-auth/specification/draft | Draft | maintainers | 2026-06-01 (submodule refreshed to `030b738`) | Each release | Draft auth extensions remain design/review only; refresh clarifies enterprise-managed authorization terminology without changing MCP Geo auth behavior. |
| MCP-Apps host window behavior (Claude + VS Code docs) | https://www.claude.com/docs/claude-code/mcp-app-design-guidelines and https://code.visualstudio.com/docs/copilot/chat/mcp-servers | Implementation docs | maintainers | 2026-03-01 (host capability review) | Monthly | Used for practical UI window budgets: Claude inline guidance (`max-height 500px`) and VS Code inline-only display mode support at present. |
| Agent Skills specification | https://agentskills.io/specification | Stable | maintainers | 2026-06-01 (submodule refreshed to `5d4c1fd`) | Monthly | Vendored as git submodule at `docs/vendor/agentskills`; refresh adds expanded best-practice/evaluation docs and clarifies skill name constraints. |
| MCP Streamable HTTP transport | https://modelcontextprotocol.io/specification/2025-11-25/basic/transports | Preview/stable baseline plus RC transition | maintainers | 2026-06-01 (RC transport impact reviewed) | Monthly | Stable transport remains `2025-11-25`; RC mode adds stateless requests plus strict `Mcp-Method` / `Mcp-Name` validation. |
| ChatGPT Developer Mode & Connectors | https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta | Preview | maintainers | 2026-03-08 (official help article re-linked) | Monthly | Canonical OpenAI help content; deprecated local placeholder removed from active tracking. |
| OpenAI Apps SDK (MCP-Apps UI) | https://developers.openai.com/apps-sdk/build/mcp-server/ | Preview | maintainers | 2026-06-01 (example submodule refreshed to `18cc38e`) | Monthly | Prefer current Apps SDK docs via `openaiDeveloperDocs`; local examples are supporting reference only and now reinforce non-legacy MCP Apps metadata. |
| MCP Inspector CLI | https://modelcontextprotocol.io/docs/tools/inspector | Preview | maintainers | 2026-06-01 (submodule refreshed to `10f4297`) | Monthly | Refreshed Inspector reference includes OAuth proxy/DCR, sanitized error responses, safer metadata rendering, and the latest package-lock audit refresh; use automated RC tests for release-gated behavior. |
| OpenAI Documentation MCP | https://developers.openai.com/resources/docs-mcp | Preview | maintainers | 2026-03-08 (guide reviewed; shared server URL verified) | Monthly | Shared read-only docs server is `https://developers.openai.com/mcp`; repo MCP configs now include `openaiDeveloperDocs`. |

## Drift Validation Workflow

1. Run `python3 scripts/check_spec_drift.py` and capture the local-vs-origin
   drift plus any missing vendored paths.
2. For every target reported as `behind_or_diverged`, review the upstream
   changelog or commit range before updating the submodule pointer.
3. After any submodule refresh, rerun the same script, then rerun the repo's
   targeted validation slices that depend on the changed spec surface.
4. Only then update the relevant `Last Checked` dates/notes in this file to
   show a completed refresh rather than an audit-only check.
