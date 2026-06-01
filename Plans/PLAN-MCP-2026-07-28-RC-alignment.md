# MCP 2026-07-28 RC Submodule Refresh And Alignment

Last updated: 2026-06-01
Owner: maintainers
Branch/worktree: `codex/mcp-2026-rc-alignment` at `/Users/crpage/tmp/mcp-geo-rc-align`

## Summary

The upstream MCP release-candidate blog URL includes `2026-07-28`, but the post
was published on 2026-05-21. It says the release candidate is available now and
the final specification is planned for 2026-07-28. MCP Geo keeps
`2025-11-25` as the default runtime protocol until the RC becomes final or an
operator explicitly enables the RC feature flag.

This work was done from a clean worktree because the original checkout had
unrelated uncommitted edits. Those edits were not touched.

## Source Set

- MCP RC blog: <https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/>
- Draft changelog: <https://modelcontextprotocol.io/specification/draft/changelog>
- Stateless protocol: <https://modelcontextprotocol.io/seps/2575-stateless-mcp>
- Sessionless state handles: <https://modelcontextprotocol.io/seps/2567-sessionless-mcp>
- HTTP standard headers: <https://modelcontextprotocol.io/seps/2243-http-standardization>
- Cache TTL metadata: <https://modelcontextprotocol.io/seps/2549-TTL-for-list-results>
- MRTR: <https://modelcontextprotocol.io/seps/2322-MRTR>
- Tasks extension: <https://modelcontextprotocol.io/seps/2663-tasks-extension>
- Deprecations: <https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging>
- JSON Schema 2020-12: <https://modelcontextprotocol.io/seps/2106-json-schema-2020-12>
- Resource-not-found code: <https://modelcontextprotocol.io/seps/2164-resource-not-found-error>
- Migration signal, TypeScript SDK sessions:
  <https://github.com/modelcontextprotocol/typescript-sdk/issues/1658>
- Migration signal, Python SDK list caching:
  <https://github.com/modelcontextprotocol/python-sdk/issues/2108>
- Migration signal, Python SDK session/auth binding:
  <https://github.com/modelcontextprotocol/python-sdk/issues/2100>
- Migration signal, Go SDK SEP-2567 task:
  <https://github.com/modelcontextprotocol/go-sdk/issues/951>

## Refresh Ledger

| Stage | Submodule | Before | After | Commit count | Status | Evidence |
| --- | --- | --- | --- | ---: | --- | --- |
| 1 | `docs/vendor/mcp/repos/modelcontextprotocol` | `967e8db7` | `936a5c417fc54bf0580810aef5a71ce5a4a93c0f` | 866 | done | `git diff --submodule=log`; `git diff --stat 967e8db7..936a5c4` reports 375 files. |
| 2 | `docs/vendor/mcp/repos/ext-apps` | `30f79b9e` | `9a37ad71827d076af06978fa7f7f510449687061` | 88 | done | `git diff --submodule=log`; `git diff --stat 30f79b9e..9a37ad7` reports 139 files. |
| 3 | `docs/vendor/mcp/repos/ext-auth` | `f29c419` | `030b7382eada0ef7b3745c8d827b520bb97f6ed9` | 5 | done | `git diff --stat f29c419..030b738` reports one auth documentation file. |
| 4 | `docs/vendor/mcp/repos/inspector` | `db0827b` | `10f429759f191349785c0ac1707e8ce1e9bceb83` | 47 | done | `git diff --stat db0827b..10f4297` reports 29 files. The final extra commit after the planned pin was a package-lock-only npm audit refresh. |
| 5 | `docs/vendor/agentskills` | `fbb6c82` | `5d4c1fda3f786fff826c7f56b6cb3341e7f3a911` | 81 | done | `git diff --stat fbb6c82..5d4c1fd` reports 38 files. |
| 6 | `docs/vendor/openai/repos/openai-apps-sdk-examples` | `ac8a7f6` | `18cc38e78a968712c357bacdc3c79fead5bfc6b4` | 30 | done | `git diff --stat ac8a7f6..18cc38e` reports 74 files. |
| 7a | `submodules/os-mcp` | `584cb6d0c2ded52b7e5f27b89be5c7a4eb1f2365` | unchanged | 0 | verified no-op | Configured branch `geo-mcpi` remote ref equals local HEAD. `origin/HEAD` points elsewhere and is not the configured submodule branch. |
| 7b | `submodules/os-vector-tile-api-stylesheets` | `618729210e8bbe3f75e7d2c4db3076c093d9f316` | unchanged | 0 | verified no-op | Remote `origin/HEAD` equals local HEAD. |

Current `git submodule status` after the refresh:

```text
+5d4c1fda3f786fff826c7f56b6cb3341e7f3a911 docs/vendor/agentskills (heads/main)
+9a37ad71827d076af06978fa7f7f510449687061 docs/vendor/mcp/repos/ext-apps (v1.7.2)
+030b7382eada0ef7b3745c8d827b520bb97f6ed9 docs/vendor/mcp/repos/ext-auth (heads/main)
+10f429759f191349785c0ac1707e8ce1e9bceb83 docs/vendor/mcp/repos/inspector (0.21.2-hotfix-3-4-g10f42975)
+936a5c417fc54bf0580810aef5a71ce5a4a93c0f docs/vendor/mcp/repos/modelcontextprotocol (2024-11-05-3936-g936a5c41)
+18cc38e78a968712c357bacdc3c79fead5bfc6b4 docs/vendor/openai/repos/openai-apps-sdk-examples (heads/main)
 584cb6d0c2ded52b7e5f27b89be5c7a4eb1f2365 submodules/os-mcp (v0.1.11-48-g584cb6d)
 618729210e8bbe3f75e7d2c4db3076c093d9f316 submodules/os-vector-tile-api-stylesheets (heads/main)
```

The leading `+` markers are expected while the parent repository records the
new submodule pointers in the working tree.

## Stage Notes

### Stage 1: MCP Core RC

Changed file classes include the RC blog, draft specification and schema,
rendered SEP pages, raw SEP files, release/governance workflow files, and docs
site navigation. The runtime-relevant changes for MCP Geo are:

- protocol-level sessions and `Mcp-Session-Id` are removed for `2026-07-28`
- `server/discover` replaces initialize-first capability discovery
- protocol version, client info, capabilities, log level, and trace context move
  to per-request `_meta`
- Streamable HTTP uses `Mcp-Method` and `Mcp-Name` for routing and body/header
  consistency checks
- cacheable list/read results carry `ttlMs` and `cacheScope`
- MRTR returns `InputRequiredResult` instead of requiring long-lived SSE for
  every server-to-client prompt
- Tasks moves to an extension lifecycle
- roots, sampling, and logging are deprecated but not removed
- tool schemas move to JSON Schema 2020-12, with input roots still constrained
  to objects and external `$ref` dereferencing explicitly out of scope
- missing resources move from the previous custom code to JSON-RPC `-32602`
  in RC mode

Migration issues found:

- The TypeScript SDK issue on multi-node Streamable HTTP sessions shows the
  current session model is operationally brittle behind round-robin routing.
- The Python SDK caching issue shows SDK authors are actively designing list
  caching semantics for a world without persistent list-change streams.
- The Python SDK session/auth issue confirms that session identifiers and
  authenticated identity need careful binding until sessionless transports are
  adopted.
- The Go SDK task for SEP-2567 shows official SDK work is still in progress
  during the RC window.

MCP Geo impact:

- Keep stable clients on `2025-11-25`.
- Add feature-gated RC support so clients can test the future protocol without
  changing default behavior.
- Favor explicit state handles in future long workflows instead of hidden
  transport session state.

### Stage 2: MCP Apps

Changed file classes include the Apps draft specification, bridge/runtime
types, React helpers, examples, docs, tests, and package metadata. Notable
changes include server resource APIs, request teardown notification support,
guarding requests before the app handshake completes, progress-aware timeout
reset behavior, modern `_meta.ui.resourceUri` semantics, stricter metadata
typing, and `v1.7.2` package state.

Migration issues found:

- The OpenAI examples refresh removes old `openai/outputTemplate` references,
  reinforcing the existing MCP Geo decision to use standard MCP Apps metadata.
- Apps hosts are tightening request lifecycle and pre-handshake behavior, so
  widgets should tolerate teardown, reconnect, and capability discovery.

MCP Geo impact:

- Existing `ui://mcp-geo/...` resources and `_meta.ui.resourceUri` remain the
  right direction.
- Future widget work should add request-teardown handling and avoid assuming a
  bridge request can be sent before `ui/initialize` completes.

### Stage 3: Auth Extension

Changed file classes are limited to enterprise-managed authorization wording.
The update clarifies MCP client/server and authorization server terminology.

Migration issues found:

- No runtime-breaking change was found for MCP Geo's current bearer/JWT HTTP
  boundary.
- The Python SDK session/auth issue remains relevant to the old session model.

MCP Geo impact:

- No immediate runtime change beyond continuing to keep bearer auth separate
  from MCP protocol version negotiation.

### Stage 4: MCP Inspector

Changed file classes include Inspector client/server code, OAuth proxy support,
tests, CI, package metadata, and release metadata. Notable changes include an
OAuth proxy path, Dynamic Client Registration handling, proxy fetch behavior,
sanitized server errors, validation for `serverInfo.websiteUrl`, and the
0.21.2-era release update. A follow-up drift audit found one newer upstream
commit, `10f42975`, which changes only `package-lock.json` for transitive
security advisories; the submodule was advanced to that commit so
`scripts/check_spec_drift.py --fail-on-drift` remains clean.

Migration issues found:

- Inspector is becoming stricter around auth/OAuth and safer rendering of
  server-provided metadata.

MCP Geo impact:

- Keep Inspector as the primary manual interop tool, but include RC tests in
  automation instead of relying on manual Inspector behavior during the RC
  window.

### Stage 5: Agent Skills

Changed file classes include the Agent Skills specification, skill-creation
guides, best-practice/evaluation docs, client showcase data, and README content.
The spec now clarifies name constraints and expands guidance for concise,
progressively disclosed skills.

Migration issues found:

- No direct MCP runtime issue was found. Skill docs are still a maintained
  companion standard and should remain tracked for repo skill resources.

MCP Geo impact:

- Existing `skills://mcp-geo/getting-started` remains valid.
- Future repo skills should keep YAML frontmatter and concise triggerable
  descriptions aligned with the refreshed spec.

### Stage 6: OpenAI Apps SDK Examples

Changed file classes include new MCP Basics examples, Cards Against AI example
server/widgets, package/workspace files, app SDK example widgets, and pinned
workflow/pre-commit references. This remains supporting material only; the
canonical OpenAI docs source for this repo is still the OpenAI Documentation MCP
server, not the local vendor tree.

Migration issues found:

- Removal of `openai/outputTemplate` examples confirms the move away from
  legacy OpenAI-specific template metadata toward MCP Apps conventions.

MCP Geo impact:

- No runtime dependency on the examples.
- Keep local examples as reference material and cite current OpenAI docs through
  the Documentation MCP when OpenAI-specific behavior is needed.

### Stage 7: OS Submodule No-op Checks

`submodules/os-mcp` is pinned to its configured `geo-mcpi` branch head. The
repository's generic `origin/HEAD` points at a different branch and is not the
submodule's configured update target.

`submodules/os-vector-tile-api-stylesheets` matches remote `origin/HEAD`.

MCP Geo impact:

- No OS runtime or vector basemap change is introduced by this workstream.

## Repo Alignment Implemented In This Tranche

- Added feature-gated `2026-07-28` protocol support. Enable with
  `MCP_2026_RC_ENABLED=1` or `MCP_PROTOCOL_2026_07_28_ENABLED=1`.
- Kept `2025-11-25` as the default stable runtime protocol.
- Added shared RC helpers in `server/mcp/rc2026.py`.
- Added HTTP and STDIO `server/discover`.
- Added per-request `_meta` extraction for protocol version, client info,
  capabilities, log level, and W3C trace context keys.
- Added stateless HTTP RC path that does not issue or require
  `Mcp-Session-Id` when a request explicitly opts into `2026-07-28`.
- Added observe-mode metrics for `Mcp-Method` and `Mcp-Name`; RC mode is
  strict and rejects missing or mismatched standard headers.
- Added `ttlMs` and `cacheScope` metadata to RC list/read result objects.
- Added RC-mode MRTR `input_required` results for toolset selection and
  ONS selection disambiguation while retaining existing SSE/session elicitation
  for stable clients.
- Added RC-mode `resources/read` not-found mapping to JSON-RPC `-32602`.
- Added JSON Schema 2020-12 guardrail checks for registered tool schemas:
  object root for inputs, no external `$ref`, bounded depth, and bounded node
  count.
- Added `scripts/mcp-http-demo-local` so HTTP MCP connectors can be launched
  with the same OS API key hydration and ONS/OS cache mounts as the Docker
  STDIO wrappers. This closes the demo gap where the protocol endpoint was
  healthy but postcode/geography examples lacked mounted host data.

Tasks remains a future extension target. No task runtime was added because MCP
Geo does not yet have a selected long-running workflow that needs the new Tasks
extension lifecycle.

## Runtime Validation Results

Completed validation:

- `python3 scripts/check_spec_drift.py --fail-on-drift`
- `git diff --check`
- `python3 -m py_compile server/protocol.py server/mcp/rc2026.py server/stdio_adapter.py server/mcp/http_transport.py tests/test_mcp_2026_rc.py tests/test_protocol_versions.py`
- `./scripts/ruff-local`
- `./scripts/mypy-local`
- `./scripts/pytest-local -q` (`1586 passed`, `20 skipped`, coverage `90.03%`)
- Focused wrapper regressions for the HTTP demo launcher and cache/API-key
  mount plan:
  `./scripts/pytest-local -q --no-cov tests/test_mcp_docker_local.py -k 'http_plan or http_demo or ons_geo_cache_mounts'`
- STDIO client interop smoke for `tools/list`, `tools/call`,
  `resources/list`, and `resources/read`
  (`103` tools, `41` resources, no JSON-RPC errors)
- Obsidian KB rebuild:
  `python3 scripts/build_obsidian_kb.py --mode canon --git-ref WORKTREE --output-root "Obsidian/MCP Geo Knowledge Base" --manifest-out data/knowledge_base/obsidian_kb_manifest.json`
- Obsidian KB validation:
  `python3 scripts/validate_obsidian_kb.py --manifest data/knowledge_base/obsidian_kb_manifest.json --fail-on drift coverage recursion orphan`
- Postmortem wiki JSON sanity check with `jq -e type`
- Postmortem wiki Markdown link check

Focused runtime coverage includes HTTP and STDIO tests for legacy and RC modes,
header mismatch handling, `server/discover`, cache metadata, MRTR-style
input-required results, trace `_meta`, resource-not-found error-code mapping,
and JSON Schema 2020-12 guardrails.

## Open Follow-ups

- Rerun the RC alignment after upstream publishes the final 2026-07-28 spec and
  remove the release-candidate feature flag only after compatibility is proven.
- Add Tasks support only if a concrete MCP Geo long-running workflow is selected.
- Revisit Apps widget bridge code for `ui/notifications/request-teardown` and
  pre-handshake send guards when the next widget feature is touched.
- Track SDK issue closure across TypeScript, Python, and Go before defaulting
  new deployments to the RC/final protocol.
