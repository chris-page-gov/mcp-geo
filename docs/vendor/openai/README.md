# Deprecated vendor snapshot: OpenAI developer docs

Deprecated as of 2026-03-08.

For current OpenAI/Codex/API/App SDK documentation, use the shared
`openaiDeveloperDocs` MCP server:

- Endpoint: <https://developers.openai.com/mcp>
- Setup guide: <https://developers.openai.com/resources/docs-mcp>

Repo policy:

- Prefer the Documentation MCP for current OpenAI developer docs.
- Do not refresh `developers.openai.com` snapshots via `scripts/vendor_fetch.sh`;
  that workflow is deprecated.
- Keep this folder only for legacy offline context or historical artifacts that
  pre-date the Documentation MCP adoption.

If an air-gapped workflow needs local OpenAI docs again, document the exception
in `docs/spec_tracking.md` before reintroducing any supported refresh flow.
