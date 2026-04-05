# Codex vs Claude MCP Host Benchmark

This runbook adds Codex as a first-class MCP host benchmark target for
`mcp-geo` alongside Claude Desktop.

## Shared Cache Requirement

For any cross-client benchmark or comparison, all clients must hit the same
PostGIS-backed cache and route-graph store. In this repo, the canonical shared
cache is the repo devcontainer PostGIS service:

- container: `mcp-geo_devcontainer-postgis-1`
- Docker network: `mcp-geo_devcontainer_default`
- service hostname inside that network: `postgis`

Do not benchmark one client against `mcp-geo_devcontainer-postgis-1` and
another against a fallback sidecar such as `mcp-geo-postgis-claude`,
`mcp-geo-postgis-codex`, or `mcp-geo-postgis-sidecar`. That invalidates
cache-comparison claims.

## Exact Startup Procedure

Use this order every time before benchmarking multiple clients:

1. Start Docker Desktop.
2. Start the repo devcontainer, or bring up its PostGIS service from the repo root:

   ```bash
   docker compose -f .devcontainer/docker-compose.yml up -d postgis
   ```

3. Wait until `mcp-geo_devcontainer-postgis-1` is running.
4. Run the shared-cache preflight:

   ```bash
   ./scripts/check_shared_benchmark_cache.sh
   ```

5. Only proceed if the script prints `PASS: shared benchmark cache is ready`.
6. Then start or benchmark clients through the standard wrappers:
   - Codex host runs: `scripts/codex-mcp-local`
   - Claude Desktop: `scripts/claude-mcp-local`

The preflight verifies that:

- the shared PostGIS container is running
- `postgis` and `pgrouting` are installed
- Claude and Codex wrappers both target the same devcontainer PostGIS container
- neither wrapper would start a separate fallback PostGIS sidecar

If the preflight fails, do not benchmark until the Docker state is corrected.

## Outputs

Each scored session writes these artifacts into the session directory:

- `mcp-stdio-trace.jsonl` or `mcp-http-trace.jsonl`
- `ui-events.jsonl` when UI runtime is available
- `session.json` with standardized host metadata
- `summary.json` and `report.md` from `scripts/trace_report.py`
- `benchmark-evidence.json`
- `benchmark-score.json`

Aggregate reports are generated under `docs/reports/` as:

- `codex_vs_claude_host_benchmark_<date>.json`
- `codex_vs_claude_host_benchmark_<date>.md`

## Scenario Pack

Default pack:

- `docs/benchmarking/codex_vs_claude_host_scenarios_v1.json`

Inspect or export it:

```bash
./.venv/bin/python scripts/host_benchmark.py scenario-pack
```

## Codex Registration

Devcontainer onboarding now registers `mcp-geo` against:

- `scripts/codex-mcp-local`

Validate Codex startup scoping:

```bash
./scripts/check_codex_startup_scope.sh
```

Validate Claude startup scoping:

```bash
./scripts/check_claude_startup_scope.sh
```

## Codex CLI Scripted Run

Run one scripted benchmark scenario with `codex exec` and GPT-5.4:

```bash
./.venv/bin/python scripts/host_benchmark.py run-codex-cli tool_search_postcode
```

Options:

- `--model gpt-5.4`
- `--server-name mcp-geo`
- `--session-root logs/sessions`
- `--wrapper scripts/codex-mcp-local`

The runner temporarily swaps the Codex MCP registry entry for `mcp-geo` to a
traced stdio proxy, runs the scenario, restores the prior config, generates the
trace report, and writes benchmark evidence/score artifacts.

## Codex IDE Manual UI Capture

Use one session per scenario. Point the Codex IDE MCP server command at
`trace_session.py` so the server launch itself is traced and annotated.

Example command:

```bash
./.venv/bin/python scripts/trace_session.py stdio \
  --source codex \
  --surface ide \
  --host-profile codex_ide_ui \
  --scenario-pack codex_vs_claude_host_v1 \
  --scenario-id geography_selector_widget \
  -- \
  /Users/crpage/repos/mcp-geo/scripts/codex-mcp-local
```

After reproducing the scenario in Codex IDE, score the captured session:

```bash
./.venv/bin/python scripts/host_benchmark.py score-session \
  logs/sessions/<session-id>
```

## Claude Desktop Manual Capture

Use the same trace-session wrapper pattern, but keep the Claude launcher:

```bash
./.venv/bin/python scripts/trace_session.py stdio \
  --source claude \
  --surface desktop \
  --host-profile claude_desktop_ui_partial \
  --scenario-pack codex_vs_claude_host_v1 \
  --scenario-id geography_selector_widget \
  -- \
  /Users/crpage/repos/mcp-geo/scripts/claude-mcp-local
```

Score the captured session after the manual run:

```bash
./.venv/bin/python scripts/host_benchmark.py score-session \
  logs/sessions/<session-id>
```

## Regenerate the Comparison Report

Once you have scored session directories for the Codex CLI, Codex IDE, and
Claude Desktop tracks, generate the aggregate report without rerunning the
hosts:

```bash
./.venv/bin/python scripts/host_benchmark.py summarize \
  logs/sessions/<codex-cli-session> \
  logs/sessions/<codex-ide-session> \
  logs/sessions/<claude-session> \
  --out-prefix docs/reports/codex_vs_claude_host_benchmark_$(date +%F)
```

The markdown report includes:

- per-track coverage and average score
- scenario matrix for Codex CLI / Codex IDE / Claude Desktop
- category averages for protocol, discovery, tool search, resources, UI runtime,
  fallback behavior, and latency

## Notes

- `trace_session.py` now records `source`, `surface`, `hostProfile`,
  `clientVersion`, `model`, `scenarioPack`, and `scenarioId` in `session.json`.
- `trace_report.py` writes both `report.md` and `summary.json`.
- Codex uses `scripts/codex-mcp-local`; Claude remains on
  `scripts/claude-mcp-local` and retains Claude-only defaults. The Codex
  wrapper prefers Docker on host surfaces and falls back to `scripts/os-mcp`
  when Docker is unavailable or the session is already inside a container.
- Docker-backed wrappers now default to
  `MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=auto`, so when the repo devcontainer DB is
  running both Codex and Claude reuse that shared cache by default.
