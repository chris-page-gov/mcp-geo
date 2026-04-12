# MCP Geo Unattended Client Evaluation Analysis

Date: 2026-04-12
Primary evidence pack:
- `docs/reports/client_interop_unattended_eval_2026-04-12.md`
- `docs/reports/client_interop_unattended_eval_2026-04-12.json`
- `logs/sessions/client_interop_unattended_eval_20260412/`
- `logs/sessions/vscode_full_refresh_20260412/`

## Purpose

This report explains what the first unattended four-client comparison actually
proved, using the captured tool calls and raw session evidence rather than only
the aggregate scores. The goal is to separate MCP-Geo tool behavior from host
or client-launch failures, then turn those findings into a remediation plan
that improves the practical AI-client experience across the whole server.

## Scope and Method

- Scenario pack: `codex_vs_claude_host_v1`
- Tracks:
  - Codex CLI
  - Gemini CLI
  - Claude Code CLI
  - VS Code Agent
- Aggregate scoring rule:
  - only `scored` runs contribute to the track average
  - blocked runs retain a `diagnosticScore` only
- Evidence sources used here:
  - per-session `benchmark-evidence.json`
  - per-session `summary.json`
  - raw stderr / assistant-response artifacts where the client failed before
    useful MCP work

## Executive Summary

The unattended comparison did not show one universal MCP-Geo problem. It showed
four distinct host behaviors:

1. Codex CLI is currently the strongest unattended host and reached real tool
   use in `7/8` scenarios.
2. Gemini CLI never reached MCP traffic at all because the headless run path
   tripped over Gemini's own workspace restrictions before the scenario began.
3. Claude Code CLI completed MCP startup discovery but then failed on Anthropic
   CLI authentication before any task-level tool call.
4. VS Code Agent is partially viable after forcing the workspace open, but the
   `code chat` path is still nondeterministic and often stops before issuing any
   MCP request for the user prompt.

The most important conclusion is that the current benchmark already separates
server/tool quality from client-launch quality:

- MCP-Geo discovery and core compact workflows are working well enough for
  Codex and partially for VS Code.
- The biggest current blockers are client readiness, workspace attachment, and
  auth, not schema/transport failure inside the server.

## Aggregate Results

| Track | Attempts | Scored | Average | Main outcome |
| --- | ---: | ---: | ---: | --- |
| Codex CLI | 8 | 7 | 0.7016 | Best unattended baseline |
| Gemini CLI | 8 | 0 | n/a | Blocked before first MCP traffic |
| Claude Code CLI | 8 | 0 | n/a | Startup discovery okay, task execution blocked by CLI auth |
| VS Code Agent | 8 | 4 | 0.5361 | Partially usable, still nondeterministic |

## What Works

### 1. Compact discovery and summary workflows are viable

The strongest evidence is Codex, with partial confirmation from VS Code:

- `admin_lookup.find_by_name` was the most stable shared discovery tool.
  - Codex called it `8` times.
  - VS Code called it in successful postcode/tool-search flow.
- `ons_geo.area_summary` worked as the intended compact follow-up surface once
  a client had a usable geography anchor.
  - Codex used it in ambiguous geography and widget scenarios.
  - VS Code used it successfully in the postcode discovery scenario.
- `nomis.query` worked as a follow-on profile tool once the client had already
  resolved the target area. Codex used it three times in the Westminster
  scenario without transport or schema issues.

Interpretation:
- the new summary-oriented design direction is correct
- clients perform better when MCP-Geo exposes one compact answer surface rather
  than forcing the model to orchestrate a raw multi-step chain

### 2. Widget and UI-resource flows are viable

Two important UI surfaces showed real unattended success:

- `os_apps.render_geography_selector`
  - successful in Codex and VS Code
  - VS Code also completed paired `resources/read` calls against
    `ui://mcp-geo/geography-selector`
- `os_apps.render_boundary_explorer`
  - successful in Codex
  - boundary-widget scenario did not fully reach the same endpoint in VS Code,
    but it still routed through `os_mcp.route_query` and reached the geography
    selector UI resource successfully

Interpretation:
- MCP-Apps UI resources are not the main interop blocker
- when the client actually engages the tool chain, MCP-Geo can deliver widget
  tools plus UI resources in a usable form

### 3. Error normalization is helping rather than hurting

Observed errors were structured and did not collapse the session:

- `INVALID_INPUT` from `ons_geo.area_summary`
- `NOT_FOUND` from `admin_lookup.area_geometry`
- `NO_API_KEY` from `os_places.by_postcode`

In Codex and VS Code, those surfaced as normal tool outcomes rather than
transport failure. That is the right shape for AI-host compatibility.

## What Does Not Work

### 1. Gemini CLI unattended execution is blocked before MCP starts

Observed behavior:
- `8/8` runs ended `runner_error`
- blocker: `gemini_cli_timeout_after_45s`
- `requestCount=0` and `toolCalls=[]` on every scenario

Representative raw stderr:

`Error executing tool read_file: Path not in workspace: Attempted path "/Users/crpage/.gemini/settings.json" resolves outside the allowed workspace directories...`

Interpretation:
- this run path is not yet testing MCP-Geo tool quality
- Gemini CLI is failing inside its own local workspace/tooling contract before
  it can issue the first MCP request
- the temporary project-scope registration avoided dirtying the repo, but it
  also exposed that Gemini wants access to `~/.gemini/settings.json`

### 2. Claude Code CLI is blocked by auth after startup discovery

Observed behavior:
- `8/8` runs ended `runner_error`
- blocker: `claude_cli_failed`
- `requestCount=6` on every scenario
- startup pattern: initialize + list/discovery calls only
- `toolCalls=[]`

Representative raw assistant response:

`Failed to authenticate. API Error: 401 {"type":"error","error":{"type":"authentication_error","message":"Invalid authentication credentials"}}`

Interpretation:
- Claude CLI does reach the MCP server successfully
- startup registration, listing, and capability exposure are not the problem
- the benchmark is currently blocked by Anthropic CLI authentication, not by
  MCP-Geo runtime compatibility

### 3. VS Code Agent remains nondeterministic even after workspace correction

Observed behavior after the runner fix:
- `4/8` scored
- `4/8` no MCP traffic

What improved:
- forcing `code --reuse-window .` before each `code chat` session moved VS Code
  from mostly broken to partially usable

What still fails:
- some sessions still show `requestCount=0` and no MCP engagement at all
- this is now a session-execution reliability problem rather than a missing
  workspace-config problem

Interpretation:
- VS Code can use MCP-Geo correctly
- the unattended `code chat` host path is still not deterministic enough to be
  treated as a reliable benchmark executor

### 4. Resource-only prompts are weaker than tool-driven prompts

The clearest example is Codex on `skills_guide_resource`:
- it initialized cleanly
- listed tools and resources
- performed `resources/read` on `skills://mcp-geo/getting-started`
- then stopped without a task-level follow-through

This is important because it is the strongest current host. The failure mode is
not transport breakage; it is a resource-consumption behavior gap.

Interpretation:
- tool-oriented prompts are currently safer than pure resource-retrieval prompts
- the benchmark should continue to test resource-only scenarios, because they
  expose a real class of weak client behavior

### 5. Live OS-backed paths remain sensitive to credential visibility

Observed evidence:
- Codex address lookup called `os_places.by_postcode` and got `NO_API_KEY`
- VS Code postcode/tool-search flow also hit `NO_API_KEY` on `os_places.by_postcode`

The clients recovered partly by falling back to local/admin/ONS surfaces, but
this still reduces answer quality and benchmark comparability.

Interpretation:
- some benchmark scenarios currently mix live-API behavior with otherwise local
  reasoning paths
- the benchmark needs a clearer split between offline-safe evaluation and
  live-credential evaluation

## Tool-Call Analysis

### Codex CLI

Most-used tools:
- `admin_lookup.find_by_name`: `8`
- `os_mcp.route_query`: `3`
- `admin_lookup.area_geometry`: `3`
- `ons_geo.area_summary`: `3`
- `nomis.query`: `3`
- `os_apps.render_boundary_explorer`: `2`
- `os_mcp.descriptor`: `2`

What this shows:
- Codex prefers to get to a concrete geographic anchor early
- it can use the compact area-summary path correctly
- it can consume widget-style render tools
- it tolerates structured tool errors without derailing the session

Weak spots:
- resource-only scenario ended as startup/read-only behavior
- some scenarios still overuse general admin lookup before using the more
  compact specialized tools

### Gemini CLI

Tool traffic:
- none

What this shows:
- there is currently no meaningful server-side tool evaluation for Gemini from
  this unattended path
- all Gemini conclusions are about launcher/workspace readiness, not tool
  quality

### Claude Code CLI

Tool traffic:
- none

Startup discovery pattern:
- resource catalog startup completed repeatedly before failure

What this shows:
- strict-client MCP registration is good enough for Claude CLI startup
- the run path is blocked at the Anthropic account/session layer before prompt
  execution can begin

### VS Code Agent

Observed tool usage in scored sessions:
- `os_mcp.descriptor`: `2`
- `os_mcp.route_query`: `2`
- `os_apps.render_geography_selector`: `2`
- `os_places.by_postcode`: `1`
- `admin_lookup.find_by_name`: `1`
- `ons_geo.area_summary`: `1`
- `os_apps.log_event`: `1`

What this shows:
- once engaged, VS Code can use both discovery/routing and widget flows
- it can read UI resources and sustain simple tool chains
- the main weakness is not tool compatibility, but inconsistent transition from
  chat prompt to MCP activity

## Grouped Findings by Tool Family

### Strong today

- `admin_lookup.find_by_name`
- `ons_geo.area_summary`
- `nomis.query` after a resolved area
- `os_mcp.route_query`
- `os_apps.render_geography_selector`
- `ui://mcp-geo/geography-selector` resource reads

### Strong, but only once the host is healthy

- `os_apps.render_boundary_explorer`
- `os_resources.get`
- `admin_lookup.area_geometry`

### Technically sound, but benchmark-sensitive

- `os_places.by_postcode`
  - quality depends on `OS_API_KEY` visibility
- `skills://mcp-geo/getting-started`
  - readable, but not consistently acted upon by clients

### Not meaningfully exercised yet in unattended comparison

- most Gemini-targeted tool surfaces
- most Claude-targeted task execution paths

## Root-Cause Classes

### Class A: Client readiness blockers

- Gemini workspace-policy conflict
- Claude CLI auth failure

These are not MCP-Geo tool defects, but the benchmark needs to detect and
classify them before the full scenario pack starts.

### Class B: Session attachment / host execution nondeterminism

- VS Code sometimes opens a session that still produces no MCP traffic even
  after the workspace-open correction

### Class C: Resource-consumption weakness

- clients are more reliable when they can call a compact tool than when asked
  to interpret a retrieved guide/resource without another explicit next step

### Class D: Credential-sensitive live-path drift

- some scenarios silently degrade when live OS credentials are absent

## Remedial Plan

### Immediate

1. Add a strict client-readiness preflight before the full pack.
   - Gemini: verify that the chosen unattended launcher can read the settings it
     needs without leaving the allowed workspace.
   - Claude: verify CLI authentication before scenario execution.
   - VS Code: verify one real MCP request, not only that the workspace opens.

2. Split the benchmark into readiness and capability phases.
   - readiness: can the client authenticate, attach the workspace, and issue a
     first MCP request?
   - capability: can it complete the scenario once ready?

3. Keep blocked runs out of scored averages.
   - already implemented
   - preserve this rule as a hard requirement

4. Mark every scenario as either offline-safe or live-credential-dependent.
   - run the offline-safe pack unconditionally
   - run the live pack only when `OS_API_KEY` is confirmed visible

### Near-term

1. Improve Gemini unattended startup.
   - either allow the required Gemini settings path inside the effective
     workspace model
   - or mirror the minimal required config into the temp project so Gemini
     never needs to read outside the allowed roots

2. Improve Claude unattended startup.
   - add a harness-level auth probe and fail fast with a clear readiness report
   - do not burn scenario timeouts on a known-invalid CLI session

3. Stabilize VS Code unattended execution.
   - keep the forced workspace-open step
   - add a chat-session warm-up or a minimal probe scenario that confirms first
     MCP traffic before the real scenario begins
   - if the probe fails, restart the chat run instead of recording a false
     tool-quality failure

4. Strengthen resource-only evaluation.
   - add explicit resource-consumption examples in guide text and benchmark docs
   - consider pairing pure resource prompts with a required "summarize what you
     just read" instruction so the client has a clearer completion target

### Server and Tool Optimization

1. Continue moving prompt-heavy workflows toward compact summary tools.
   - `ons_geo.area_summary` is the right pattern
   - prefer one compact answer surface over multi-tool choreography where
     possible

2. Keep descriptor and routing output action-oriented.
   - clients should get a recommended next tool, not only a catalog overview
   - especially important for VS Code, which can stall on descriptor-style
     discovery without converting it into action

3. Keep widget tools self-sufficient.
   - when a widget tool can safely include the resource handoff or key resource
     metadata directly, do so
   - reduce the amount of extra inference the client must perform after the
     tool returns

4. Preserve strong error normalization.
   - the current `INVALID_INPUT`, `NOT_FOUND`, and `NO_API_KEY` behavior is
     helping clients recover instead of failing hard

### Benchmark and Evaluation Design

1. Treat client-environment failure as a first-class result, not noise.
   - Gemini and Claude produced useful evidence even without task tool calls
   - the benchmark should continue to record that separately from tool quality

2. Add per-tool-family success dashboards.
   - discovery/routing
   - compact profiling
   - widgets/resources
   - live OS-backed lookups
   - recovery/error handling

3. Add one deterministic smoke scenario per client before the full pack.
   - target: one route query or one compact summary tool call
   - if that fails, the track should be marked not ready immediately

## Recommended Priority Order

1. Gemini readiness fix
2. Claude auth preflight
3. VS Code session-stabilization preflight
4. Offline-vs-live scenario split
5. Resource-only benchmark strengthening
6. Tool-family scorecards and readiness/capability separation

## Final Assessment

The unattended benchmark is already valuable. It does not yet prove that all
four clients can execute MCP-Geo equally well, but it does prove something more
useful at this stage:

- which failures belong to the server
- which failures belong to the client launcher
- which workflows are already strong enough to be the default AI path

Right now MCP-Geo should optimize around the patterns that already work:
compact routing, compact geography summaries, structured widget tools, and
clear normalized errors. The next benchmark iteration should spend less effort
on rerunning known-bad client startup states and more effort on proving that a
ready client can use those strong tool families consistently.
