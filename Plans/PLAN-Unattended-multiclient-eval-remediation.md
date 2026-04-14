# Unattended Multi-Client Evaluation Remediation Plan

## Summary

Rework the unattended evaluation into a two-stage system: `readiness` first, `capability` second. The immediate goal is to eliminate false benchmark failures caused by client launch/auth/workspace issues, starting with Gemini, while keeping the comparison meaningful across Codex, Claude, Gemini, and VS Code.

Chosen defaults:
- Optimize for deterministic runs, not strict single-shot purity.
- Move to one shared local secret source for benchmark-critical config.
- Keep one automatic recovery attempt only where the failure is a known host-side flake, and report it explicitly.

## Key Changes

### 1. Gemini unblock and stable client workspaces
- Replace the current Gemini temp-project pattern with a stable ignored benchmark workspace root, for example `logs/benchmark-workspaces/gemini/<scenario-id>/`, recreated per scenario.
- Keep Gemini MCP registration project-scoped within that workspace so runs stay isolated and do not dirty the repo or user-global MCP state.
- Launch Gemini with `--include-directories ~/.gemini` so its read of `~/.gemini/settings.json` is inside the allowed workspace set.
- Keep stderr parsing for the existing workspace-restriction signature, but reclassify it as a readiness failure, not a scenario failure.
- Add a Gemini-specific warmup step before the pack:
  - register the traced MCP server
  - run a minimal headless prompt that must reach one MCP request and one tool call
  - only proceed to scenarios if that succeeds

### 2. Shared readiness framework for all tracks
- Add a preflight phase ahead of the scenario pack for every client:
  - `secret/config visibility`: benchmark env resolves OS/API credentials and startup toolset defaults
  - `client launch`: CLI/app command runs without immediate auth/session failure
  - `MCP discovery`: at least one MCP startup request is observed
  - `useful tool call`: one compact preflight prompt reaches a known safe tool such as `os_mcp.descriptor`
- Persist one readiness artifact per track plus an aggregate readiness section in the final JSON/Markdown report.
- If a track fails readiness, mark the track `not_ready` and skip capability scenarios instead of generating misleading runner-error scenario rows.
- Allow one labelled recovery attempt only for host-side nondeterminism:
  - Gemini: rebuild workspace and rerun readiness once
  - VS Code: reopen workspace and rerun readiness once
  - Claude/Codex: no retry for auth or secret failures

### 3. Canonical shared secret/config source
- Make local unattended evaluation use one canonical shared source for benchmark-critical secrets:
  - primary local source: `launchctl`-visible `OS_API_KEY_FILE`
  - secondary explicit override: repo/local env for CI or non-mac shells
- Update local client setup guidance so Claude, Codex, Gemini, and VS Code all point at the same shared secret source instead of carrying divergent per-client literals.
- Keep the current client-config fallback in `benchmark_env.py` only as a compatibility bridge during migration; document it as temporary and remove it after the shared-source migration is complete.
- Extend wrapper plan/preflight output to show non-sensitive readiness facts only:
  - `os_api_key_present`
  - `os_api_key_file_present`
  - chosen toolset/include settings
  - readiness pass/fail by client

### 4. Scenario-pack and scoring redesign
- Add explicit metadata to the scenario pack:
  - `requiresLiveOsApi`
  - `requiresUiRuntime`
  - `toolFamily` or `expectedCapability`
- Split capability execution into groups:
  - `offline_safe`
  - `live_os`
  - `ui`
- Only run `live_os` scenarios for tracks that pass secret/live-readiness.
- Keep resource-only scenarios, but score them under a separate “resource consumption” capability so they do not get conflated with tool-selection failures.
- Update aggregate scoring and report schema to separate:
  - `readiness outcome`
  - `capability outcome`
  - `first attempt`
  - `recovery attempt` if used
- Add blocker taxonomy in reports, using stable classes such as:
  - `client_auth_failure`
  - `client_workspace_restriction`
  - `client_no_mcp_traffic`
  - `server_no_live_key`
  - `scenario_tool_failure`

### 5. Client-specific reliability improvements after Gemini
- Claude:
  - keep the new auth-ready path
  - add a fast auth/readiness probe before scenario execution
  - treat auth failure as track-level `not_ready`
- VS Code:
  - keep forced workspace-open
  - add a mandatory readiness prompt before the real pack
  - if readiness produces no MCP traffic, perform one restart/retry and then stop
- Codex:
  - keep as the control baseline
  - add the same readiness artifact so its runs can be compared structurally with the other clients
- All tracks:
  - preserve traced startup discovery, tool calls, resources, and UI events as today
  - add explicit timing for readiness latency and first useful capability call

## Public Interfaces / Output Changes

- `scripts/unattended_client_eval.py`
  - add a built-in readiness stage before capability execution
  - add `--readiness-only`
  - add deterministic recovery behavior with a fixed max of one recovery attempt for eligible tracks
- Aggregate JSON/Markdown outputs
  - add top-level readiness summary by track
  - add per-attempt fields for `attemptKind` (`readiness`, `capability`, `recovery`)
  - separate `not_ready` from scenario-level blocked states
- Scenario pack schema
  - add `requiresLiveOsApi`, `requiresUiRuntime`, and `toolFamily`

## Test Plan

- Unit tests
  - Gemini workspace strategy includes `~/.gemini` and no longer produces the previous settings-path blockage
  - readiness classification maps client failures to the correct blocker taxonomy
  - secret-source precedence prefers shared `OS_API_KEY_FILE` over lower-priority raw keys
  - live-scenario gating skips `live_os` scenarios when readiness lacks a usable OS key
  - recovery attempts are emitted once, labelled, and excluded from first-attempt metrics
- Harness integration tests
  - Gemini readiness passes on a mocked success path and fails cleanly on the old workspace-restriction stderr
  - Claude readiness fails fast on auth and passes on the current fixed path
  - VS Code readiness retry path produces one retry only
  - aggregate report includes readiness/capability separation and blocker taxonomy
- Acceptance scenarios
  - Gemini `address_lookup_postcode` reaches at least one MCP request and one tool call
  - Claude `address_lookup_postcode` no longer returns `NO_API_KEY`
  - VS Code produces either a scored run or an explicit `not_ready` track result, not silent `no_mcp_traffic` scenario noise
  - full four-client run produces one aggregate report with readiness, capability, and tool-family summaries

## Assumptions and Defaults

- Local benchmark target is the current macOS workstation environment.
- `launchctl`-visible `OS_API_KEY_FILE` is the canonical local shared secret source.
- Client-config fallback support remains temporarily for migration safety, but is not the desired end state.
- Deterministic evidence is more important than preserving pure single-shot semantics, so one labelled recovery attempt is acceptable for Gemini and VS Code only.
- The benchmark should measure tool behavior only after a client is proven ready; readiness failures are first-class outputs, not scenario failures.
