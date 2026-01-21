# Vendor snapshot: OpenAI / ChatGPT (Docs pointers + offline fetch)

This folder is intended to hold **offline** copies of the specific OpenAI/ChatGPT docs pages needed by a code-writing assistant without web access.

## Canonical source pages (online)
- [ChatGPT developer mode (platform docs)](https://platform.openai.com/docs/guides/developer-mode)
- [Developer mode and MCP apps in ChatGPT (Help Centre)](https://help.openai.com/en/articles/12584461-developer-mode-and-mcp-apps-in-chatgpt-beta)
- [Apps in ChatGPT / Connectors overview (Help Centre)](https://help.openai.com/en/articles/11487775-connectors-in-chatgpt)
- [Apps SDK home](https://developers.openai.com/apps-sdk/)
- [Apps SDK Quickstart](https://developers.openai.com/apps-sdk/quickstart/)
- [Apps SDK: Connect from ChatGPT](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/)
- [Apps SDK: Build your MCP server](https://developers.openai.com/apps-sdk/build/mcp-server/)
- [Apps SDK: Build your ChatGPT UI](https://developers.openai.com/apps-sdk/build/chatgpt-ui/)
- [Apps SDK Reference](https://developers.openai.com/apps-sdk/reference/)
- [Help: Build with the Apps SDK](https://help.openai.com/en/articles/12515353-build-with-the-apps-sdk)

## Recommended workflow
Use the script: `../../../../scripts/vendor_fetch.sh` to fetch and store these pages as static HTML under this folder.

Notes:
- The fetch script uses `wget` with `--convert-links` and conservative crawling.
- If you prefer a cleaner offline format, you can post-process HTML → Markdown/PDF using tools like `pandoc`.
- Snapshots are intentionally excluded from git; see `docs/vendor/README.md` for storage policy.

## Offline viewing (no-JS)
Some Help Center pages are rendered by JavaScript and show an error when opened offline. Use the
no-JS helper to strip scripts, then serve the static copies.

```bash
python scripts/vendor_html_nojs.py docs/vendor/openai/_snapshot
python -m http.server 8000 --directory docs/vendor/openai/_snapshot_noscript
```

Then open (example):
`http://127.0.0.1:8000/en/articles/6783457-what-is-chatgpt.html`
