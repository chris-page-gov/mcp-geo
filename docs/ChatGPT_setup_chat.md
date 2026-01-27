# ChatGPT Apps (Deprecated)

This repository no longer supports the OpenAI Apps SDK (“skybridge”) format
(`text/html+skybridge` and `openai/*` metadata). The MCP Apps integration now
targets the finalized MCP Apps spec (`text/html;profile=mcp-app`) only.

If you need UI rendering, use an MCP client that advertises the
`io.modelcontextprotocol/ui` extension and supports MCP Apps resources. For
general server connectivity, refer to `docs/getting_started.md` and
`docs/tutorial.md`.
