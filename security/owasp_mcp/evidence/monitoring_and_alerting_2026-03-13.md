# Monitoring and Alerting

Verified on 2026-03-13 for the strict OWASP MCP profile.

- `server/main.py` exports application, tool, and MCP HTTP auth/session metrics on `/metrics`.
- `ops/monitoring/prometheus.yml` scrapes the internal metrics endpoint only from the private monitoring plane.
- `ops/monitoring/prometheus-alert-rules.yml` alerts on auth failures, session quota exhaustion, rate-limit spikes, and elevated tool errors.
- `ops/monitoring/vector.toml` forwards structured container logs plus runtime audit/event files to an HTTP SIEM sink.
- `ops/monitoring/README.md` documents the expected metrics and routing constraints.
