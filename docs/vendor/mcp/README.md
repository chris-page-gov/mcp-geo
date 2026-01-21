# Vendor snapshot: MCP (spec + dev tools)

This folder is intended to hold **offline** copies of the MCP specification and key dev-tool docs.

## Canonical source pages (online)
- [MCP specification (latest, 2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP transports (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP Inspector docs](https://modelcontextprotocol.io/docs/tools/inspector)
- [MCP architecture (docs)](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP Apps blog post (SEP-1865 intro)](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/)
- [ext-apps SDK repo (SEP-1865)](https://github.com/modelcontextprotocol/ext-apps)
- [spec+docs repo](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [inspector repo](https://github.com/modelcontextprotocol/inspector)
- [OpenAI Apps SDK examples](https://github.com/openai/openai-apps-sdk-examples)

## Recommended workflow
- Use `../../../../scripts/vendor_submodules.sh` to pin GitHub repos as submodules (best for code + specs that already live in repos).
- Use `../../../../scripts/vendor_fetch.sh` to snapshot key *web* docs pages (e.g., spec HTML, Inspector docs page).
- Snapshots are intentionally excluded from git; see `docs/vendor/README.md` for storage policy.

## Offline viewing (no-JS)
If a snapshot relies on JavaScript and fails offline, create script-free copies and serve them:

```bash
python scripts/vendor_html_nojs.py docs/vendor/mcp/_snapshot
python -m http.server 8000 --directory docs/vendor/mcp/_snapshot_noscript
```
