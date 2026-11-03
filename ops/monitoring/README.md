# Monitoring and Alerting

This directory contains undeployed monitoring configuration reviewed by the
OWASP MCP reference assessment. No live scraping or SIEM delivery is claimed.
The protected metrics route needs operator-supplied bearer credentials, and
external SIEM delivery needs verified egress and runtime credentials before use.

## Components

- `prometheus.yml`: scrapes the private `/metrics` endpoint from the internal
  Docker network.
- `prometheus-alert-rules.yml`: alert rules for authentication failures,
  session quota exhaustion, HTTP rate limiting, and tool execution errors.
- `vector.toml`: ships structured container logs plus runtime JSONL/audit files
  to an HTTP SIEM sink.

## Expected metrics

- `app_rate_limited_total`
- `mcp_http_auth_failures_total`
- `mcp_http_session_quota_rejections_total`
- `mcp_http_sessions_active`
- `mcp_tool_errors_total`

Keep `/metrics` private to the monitoring plane and route SIEM credentials via
runtime secret delivery rather than committed environment values.
