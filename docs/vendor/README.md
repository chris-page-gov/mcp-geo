# Vendor snapshots (storage policy)

We keep large HTML snapshots **out of git** to avoid bloating repo history. Use the fetch and
post-process scripts to regenerate locally, then attach a tarball to a GitHub Release if needed.

OpenAI developer docs are now expected to be read through the shared
`openaiDeveloperDocs` MCP server (`https://developers.openai.com/mcp`). The
legacy `docs/vendor/openai/` snapshot path is deprecated and is no longer part
of the supported refresh/package workflow.

## Regenerate locally
```bash
scripts/vendor_fetch.sh
python scripts/vendor_html_nojs.py docs/vendor/mcp/_snapshot
python scripts/vendor_html_nojs.py docs/vendor/os/_snapshot
```

To refresh a single vendor set (for example OS only), set `VENDOR_TARGETS`:

```bash
VENDOR_TARGETS=os scripts/vendor_fetch.sh
python scripts/vendor_html_nojs.py docs/vendor/os/_snapshot
```

## Package for release
```bash
scripts/vendor_package.sh
```

This writes a tarball under `build/` for manual upload to a GitHub Release.
The package script now covers the supported MCP/OS snapshot sets only.
