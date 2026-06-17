# Claude Code Guidance

This repository is `mcp-geo`, not a generic hackathon workspace.

Use `AGENTS.md` as the source of truth for build, validation, coding, review,
and security rules. Read `CONTEXT.md` for the current handoff before making
changes.

Claude-specific notes:

- Do not commit API keys, `.env` secrets, or local Claude settings.
- Use the repo wrappers and docs for MCP startup rather than assuming a shared
  local server or shared PostGIS volume.
- Preserve STDIO compatibility: sanitized tool names, JSON-RPC notifications
  without responses, and `resources/read` accepting both `uri` and `name`.
- For current operational learnings, see `docs/agent_context/agent-operations.md`.
