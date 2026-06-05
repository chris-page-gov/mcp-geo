# Vendor snapshot: MCP (spec + dev tools)

This folder is intended to hold **offline** copies of the MCP specification and key dev-tool docs.

## Canonical source pages (online)
- [MCP specification (latest, 2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP transports (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCP 2026-07-28 release candidate blog](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)
- [MCP draft / 2026-07-28 RC changelog](https://modelcontextprotocol.io/specification/draft/changelog)
- [MCP stateless protocol SEP-2575](https://modelcontextprotocol.io/seps/2575-stateless-mcp)
- [MCP sessionless state handles SEP-2567](https://modelcontextprotocol.io/seps/2567-sessionless-mcp)
- [MCP HTTP header standardization SEP-2243](https://modelcontextprotocol.io/seps/2243-http-standardization)
- [MCP TTL metadata SEP-2549](https://modelcontextprotocol.io/seps/2549-TTL-for-list-results)
- [MCP MRTR SEP-2322](https://modelcontextprotocol.io/seps/2322-MRTR)
- [MCP Tasks extension SEP-2663](https://modelcontextprotocol.io/seps/2663-tasks-extension)
- [MCP deprecations SEP-2577](https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging)
- [MCP JSON Schema 2020-12 SEP-2106](https://modelcontextprotocol.io/seps/2106-json-schema-2020-12)
- [MCP Inspector docs](https://modelcontextprotocol.io/docs/tools/inspector)
- [MCP architecture (docs)](https://modelcontextprotocol.io/docs/learn/architecture)
- [MCP Apps blog post (SEP-1865 intro)](https://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/)
- [ext-apps SDK repo (SEP-1865)](https://github.com/modelcontextprotocol/ext-apps)
- [spec+docs repo](https://github.com/modelcontextprotocol/modelcontextprotocol)
- [inspector repo](https://github.com/modelcontextprotocol/inspector)
- [OpenAI Apps SDK examples](https://github.com/openai/openai-apps-sdk-examples)

## 2026-06-01 refresh state

The repo refreshed MCP-related submodules for the 2026-07-28 release candidate
in `Plans/PLAN-MCP-2026-07-28-RC-alignment.md`. Runtime defaults remain on
`2025-11-25`; RC behavior is opt-in via `MCP_2026_RC_ENABLED=1` or
`MCP_PROTOCOL_2026_07_28_ENABLED=1`.

Pinned supporting submodules after the refresh:

- `docs/vendor/mcp/repos/modelcontextprotocol`: `936a5c417fc54bf0580810aef5a71ce5a4a93c0f`
- `docs/vendor/mcp/repos/ext-apps`: `9a37ad71827d076af06978fa7f7f510449687061`
- `docs/vendor/mcp/repos/ext-auth`: `030b7382eada0ef7b3745c8d827b520bb97f6ed9`
- `docs/vendor/mcp/repos/inspector`: `10f429759f191349785c0ac1707e8ce1e9bceb83`
- `docs/vendor/agentskills`: `5d4c1fda3f786fff826c7f56b6cb3341e7f3a911`
- `docs/vendor/openai/repos/openai-apps-sdk-examples`: `18cc38e78a968712c357bacdc3c79fead5bfc6b4`

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
