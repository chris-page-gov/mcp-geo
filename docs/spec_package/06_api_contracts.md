# API Contracts and Protocol

## MCP endpoints

- `/mcp` (streamable HTTP JSON-RPC)
- `/tools/list`, `/tools/describe`, `/tools/call`, `/tools/search`
- `/resources/list`, `/resources/describe`, `/resources/read`
- `/prompts/list`, `/prompts/get`

## STDIO JSON-RPC framing

- Content-Length framing (default)
- Optional line framing (`MCP_STDIO_FRAMING=line`)

## Tool call schema (STDIO)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {"name": "os_places.by_postcode", "arguments": {"postcode": "SW1A 1AA"}}
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"status": 200, "ok": true, "data": {"uprns": []}}
}
```

## Error envelope

```json
{ "isError": true, "code": "INVALID_INPUT", "message": "..." }
```

## MCP-Apps UI resources

- `ui://mcp-geo/geography-selector`
- `ui://mcp-geo/route-planner`
- `ui://mcp-geo/feature-inspector`
- `ui://mcp-geo/statistics-dashboard`

Returned via `resources/read` with `text/html;profile=mcp-app`.

