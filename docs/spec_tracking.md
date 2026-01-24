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
| MCP specification | https://modelcontextprotocol.io/specification/2025-11-25 | Preview | maintainers | 2026-01-21 (local logs only) | Each release | External verification required; track changes before release. |
| MCP-Apps UI (`text/html;profile=mcp-app`) | https://modelcontextprotocol.io/specification/2025-11-25 | Preview | maintainers | 2026-01-21 (Claude logs) | Each release | Claude client did not fetch `resources/read` or render UI in current logs. |
| MCP Streamable HTTP transport (OpenAI docs) | docs/vendor/openai/mcp_transport_streamable_http.md | Preview | maintainers | 2026-01-21 (pending vendor drop) | Monthly | Local copy pending; source URL needed for verification. |
| ChatGPT Developer Mode Connectors | docs/vendor/openai/chatgpt_connectors_developer_mode.md | Preview | maintainers | 2026-01-21 (pending vendor drop) | Monthly | Local copy pending; source URL needed for verification. |
| OpenAI Apps SDK (MCP-Apps UI) | https://developers.openai.com/apps-sdk/build/mcp-server/ | Preview | maintainers | 2026-01-24 (local snapshot) | Monthly | Local snapshot at `docs/vendor/openai/_snapshot/apps-sdk/build/mcp-server.html`. |
| MCP Inspector CLI | docs/vendor/openai/mcp_inspector.md | Preview | maintainers | 2026-01-21 (pending vendor drop) | Monthly | Local copy pending; source URL needed for verification. |
| OpenAI MCP docs (platform) | https://platform.openai.com/docs/mcp | Preview | maintainers | 2026-01-24 (link added) | Monthly | Local stub at `docs/vendor/openai/mcp_platform_docs.md`; snapshot pending. |
