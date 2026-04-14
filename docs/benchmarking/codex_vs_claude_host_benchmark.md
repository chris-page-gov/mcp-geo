# Codex vs Claude MCP Host Benchmark

This runbook adds Codex as a first-class MCP host benchmark target for
`mcp-geo` alongside Claude Desktop.

## Benchmark Cache Topology

The default host benchmark topology is isolated per-client PostGIS sidecars:

- Claude: `mcp-geo-postgis-claude` on `mcp-geo-claude`
- Codex: `mcp-geo-postgis-codex` on `mcp-geo-codex`
- Gemini: `mcp-geo-postgis-gemini` on `mcp-geo-gemini`

This is the anti-corruption default and should be assumed unless you have
explicitly switched to shared mode.

Benchmark parity is enforced in one of two ways:

1. `isolated` mode, the default:
   - each client keeps its own PostGIS sidecar
   - `./scripts/check_shared_benchmark_cache.sh` verifies that all wrappers
     target their dedicated sidecars, that host-port publishing is disabled,
     that mounted data roots match, and that the key cache counts match
2. `shared` mode, explicit opt-in:
   - every wrapper reuses the same PostGIS container, typically the repo
     devcontainer PostGIS service
   - enable it by setting `MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=1` and
     `MCP_GEO_BENCHMARK_CACHE_MODE=shared`

## Exact Startup Procedure

Use this order every time before benchmarking multiple clients in the default
isolated mode:

1. Start Docker Desktop.
2. Start each wrapper once, or run the startup-scope probes, so the dedicated
   sidecars exist and have completed any first-start bootstrap:
   - `./scripts/check_claude_startup_scope.sh`
   - `./scripts/check_codex_startup_scope.sh`
   - `./scripts/check_gemini_startup_scope.sh`
3. Run the benchmark-cache preflight:

   ```bash
   ./scripts/check_shared_benchmark_cache.sh
   ```

4. Only proceed if the script prints `PASS: benchmark cache is ready`.
5. Then start or benchmark clients through the standard wrappers:
   - Codex host runs: `scripts/codex-mcp-local`
   - Claude Desktop: `scripts/claude-mcp-local`
   - Gemini CLI: `scripts/gemini-mcp-local`

The default preflight verifies that:

- the dedicated PostGIS containers are running
- `postgis` and `pgrouting` are installed in each
- no wrapper-owned sidecar is still publishing a host port
- the mounted host data roots match across Claude, Codex, and Gemini
- the key cache counts match across the dedicated sidecars

If you explicitly want shared mode instead, use this order:

1. Start the repo devcontainer PostGIS service from the repo root:

   ```bash
   docker compose -f .devcontainer/docker-compose.yml up -d postgis
   ```

2. Export:

   ```bash
   export MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=1
   export MCP_GEO_BENCHMARK_CACHE_MODE=shared
   export MCP_GEO_BENCHMARK_POSTGIS_CONTAINER=mcp-geo_devcontainer-postgis-1
   ```

3. Run `./scripts/check_shared_benchmark_cache.sh`.
4. Only proceed if the script prints `PASS: benchmark cache is ready`.

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

## Unattended Four-Client Run

Run the unattended comparison harness across Codex CLI, Gemini CLI, Claude Code
CLI, and VS Code Agent:

```bash
./.venv/bin/python scripts/unattended_client_eval.py \
  --session-root logs/sessions/client_interop_unattended_eval_$(date +%Y%m%d) \
  --out-prefix docs/reports/client_interop_unattended/client_interop_unattended_eval_$(date +%F)
```

Important behavior:

- Codex CLI reuses the existing `host_benchmark` runner and produces the most
  complete unattended baseline today.
- Gemini CLI uses a temporary project-scoped MCP registration outside the repo
  so unattended runs do not create or modify a repo-local `.gemini/` folder.
- Claude Code CLI uses a temporary strict MCP config per scenario. If the local
  Claude CLI auth/session is broken, the unattended report will record
  `claude_cli_failed` rather than hanging.
- VS Code Agent now creates a clean ignored benchmark workspace per attempt,
  writes a traced `.vscode/mcp.json` into that workspace, opens it on the live
  authenticated VS Code profile, raises the new benchmark window, and only
  then issues `code chat --reuse-window`. Without that window-steering step,
  the headless chat command may attach to a different live Code window with no
  benchmark MCP context and therefore no `mcp-geo` tools/resources exposed.
- Blocked runs keep their rubric score only as `diagnosticScore`; they do not
  count as scored attempts in the aggregate average.
- Benchmark temp-server runs now resolve `OS_API_KEY` / `OS_API_KEY_FILE`
  from the same practical local sources used by real client sessions:
  process env first, then `launchctl`, repo `.env`, Claude Desktop `mcp-geo`
  config, and Codex `mcp-geo` config. If a higher-priority
  `OS_API_KEY_FILE` is found, it takes precedence over a lower-priority raw
  `OS_API_KEY` fallback.

Current evidence snapshot:

- `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12.md`
- `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12.json`
- `docs/reports/client_interop_unattended/client_interop_unattended_eval_2026-04-12_analysis.md`

Current interpreted state:

- Codex CLI is the strongest unattended host today and provides the best
  baseline for actual tool-quality comparisons.
- Gemini CLI is currently blocked before first MCP traffic by its own
  workspace/settings behavior on the current headless path.
- Claude Code CLI currently reaches MCP startup but then fails the headless run
  path on local Anthropic CLI authentication before task execution.
- VS Code Agent becomes partially usable when the workspace is force-opened,
  but the unattended `code chat` path remains nondeterministic and still needs
  a readiness probe before the full scenario pack is trustworthy.

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
  `scripts/claude-mcp-local`; Gemini uses `scripts/gemini-mcp-local`. The
  Codex wrapper prefers Docker on host surfaces and falls back to
  `scripts/os-mcp` when Docker is unavailable or the session is already inside
  a container.
- Docker-backed wrappers now default to
  `MCP_GEO_POSTGIS_REUSE_DEVCONTAINER=0`, so isolated per-client PostGIS is the
  normal host behavior. Shared devcontainer reuse remains available, but only
  when you enable it explicitly for a comparison run.
- The VS Code CLI path is still less deterministic than Codex CLI. Even with
  the forced workspace-open step, some unattended `code chat` sessions only
  complete startup discovery and never translate the prompt into tool calls.
