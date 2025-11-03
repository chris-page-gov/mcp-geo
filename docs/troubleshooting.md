# Troubleshooting & Error Codes

This guide lists common error codes emitted by the MCP Geo server and suggested remediation steps.

| Code | Meaning | Typical Cause | Remediation |
|------|---------|---------------|-------------|
| INVALID_INPUT | Input validation failed | Missing or malformed parameters (e.g. postcode format) | Re-check required fields, normalize postcode (strip spaces, uppercase) |
| UNKNOWN_TOOL | Tool name not registered | Typo in `tool` field or outdated client cache | Call `/tools/list` or `/tools/describe` to confirm names |
| NO_API_KEY | OS API key absent | `OS_API_KEY` env not set | Export `OS_API_KEY` or add to `.env` then restart server |
| OS_API_ERROR | Upstream OS API non-200 response | External API returned error (quota, bad request) | Inspect message snippet; adjust parameters or check quota |
| UPSTREAM_TLS_ERROR | TLS handshake failure | Network / certificate issue | Retry later; verify container trust store and target host availability |
| UPSTREAM_CONNECT_ERROR | Connection or timeout exhaustion | Network instability or endpoint downtime | Reduce concurrency, add backoff, confirm endpoint status |
| INTEGRATION_ERROR | Unexpected exception during call | Unhandled edge case or library error | Capture logs with correlationId; file issue with stack trace (if DEBUG_ERRORS enabled) |
| RATE_LIMITED | In-memory rate limit exceeded | High request volume to same path | Slow down; implement client-side rate limiting/backoff; raise limit if safe |
| UNKNOWN_FILTER | Referenced filter id not found | Expired or incorrect filter identifier | Recreate filter via `ons_data.create_filter` and use returned `filterId` |
| NO_OBSERVATION | Observation not found | Invalid combination (geography / measure / time) | List dimensions (`ons_data.dimensions`), verify codes before querying |
| NOT_FOUND | Resource or area id missing | Invalid admin boundary id | Use `admin_lookup.find_by_name` or `reverse_hierarchy` to locate valid ids |

## General Debug Steps
1. Capture correlationId from response headers/logs for traceability.
2. Reproduce with minimal payload and add parameters progressively.
3. Use `/tools/describe?name=<tool>` to confirm required fields and types.
4. Validate network connectivity (e.g., container DNS) if upstream errors persist.
5. Monitor rate limiting metrics (if enabled) to tune client request pacing.

## Conditional Requests & Caching
If receiving repeated full payloads for static resources, ensure you supply the prior `etag` via `ifNoneMatch` (HTTP) or `ifNoneMatch` param (STDIO) for efficient `304`/`notModified` responses.

## When to Enable DEBUG_ERRORS
Set `DEBUG_ERRORS=true` only in development; it exposes stack traces that aid debugging but may leak implementation details in production.
