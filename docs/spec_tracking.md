# Preview Specification & Feature Tracking

This file tracks preview or evolving specs/features that this repo depends on.

Process:
- Add an entry when a preview spec or preview feature is introduced or used.
- Record the spec URL, status, owner, last-checked date, and review cadence.
- Update entries on each release or when issues indicate a spec change.
- If the spec URL changes, update README + this table and note the reason.

## Tracked Items

| Feature | Spec/Docs URL | Status | Owner | Last Checked | Review Cadence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| MCP specification | https://modelcontextprotocol.io/specification/2025-11-25 | Preview | maintainers | 2026-03-01 (vendored submodule refresh + path verification) | Each release | Initialize negotiation now prefers `2025-11-25` and supports `2025-06-18`, `2025-03-26`, `2024-11-05`; HTTP validates `MCP-Protocol-Version` when provided. |
| MCP elicitation (form mode) | https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation | Preview | maintainers | 2026-02-06 (local trace + schema review) | Each release | Implemented for `os_mcp.stats_routing` in stdio when client advertises `elicitation.form`. |
| MCP-Apps UI (`text/html;profile=mcp-app`) | docs/vendor/mcp/repos/ext-apps/specification/2026-01-26/apps.mdx | Stable | maintainers | 2026-03-01 (vendored submodule refresh + spec path verification) | Each release | Finalized MCP Apps spec (`2026-01-26`); UI uses JSON-RPC `ui/initialize` and no skybridge fallback. |
| MCP Auth extension (`ext-auth`) | docs/vendor/mcp/repos/ext-auth/specification/draft | Draft | maintainers | 2026-03-01 (new submodule vendored + path verification) | Each release | Draft auth extensions now available locally for design/review (`enterprise-managed-authorization`, `oauth-client-credentials`). |
| MCP-Apps host window behavior (Claude + VS Code docs) | https://www.claude.com/docs/claude-code/mcp-app-design-guidelines and https://code.visualstudio.com/docs/copilot/chat/mcp-servers | Implementation docs | maintainers | 2026-03-01 (host capability review) | Monthly | Used for practical UI window budgets: Claude inline guidance (`max-height 500px`) and VS Code inline-only display mode support at present. |
| Agent Skills specification | https://agentskills.io/specification | Stable | maintainers | 2026-03-01 (vendored submodule refresh) | Monthly | Vendored as git submodule at `docs/vendor/agentskills`. |
| MCP Streamable HTTP transport | https://modelcontextprotocol.io/specification/2025-11-25/basic/transports | Preview | maintainers | 2026-03-08 (normative transport path re-verified) | Monthly | Normative transport reference; no maintained local OpenAI copy. |
| ChatGPT Developer Mode & Connectors | https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta | Preview | maintainers | 2026-03-08 (official help article re-linked) | Monthly | Canonical OpenAI help content; deprecated local placeholder removed from active tracking. |
| OpenAI Apps SDK (MCP-Apps UI) | https://developers.openai.com/apps-sdk/build/mcp-server/ | Preview | maintainers | 2026-03-08 (Documentation MCP adoption) | Monthly | Prefer accessing current Apps SDK docs via `openaiDeveloperDocs`; local vendor copies are deprecated. |
| MCP Inspector CLI | https://modelcontextprotocol.io/docs/tools/inspector | Preview | maintainers | 2026-03-08 (canonical upstream docs re-linked) | Monthly | Canonical upstream docs replace the old local placeholder. |
| OpenAI Documentation MCP | https://developers.openai.com/resources/docs-mcp | Preview | maintainers | 2026-03-08 (guide reviewed; shared server URL verified) | Monthly | Shared read-only docs server is `https://developers.openai.com/mcp`; repo MCP configs now include `openaiDeveloperDocs`. |
