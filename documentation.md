# DSAP Implementation Log

Codex should update this file as work proceeds. Each meaningful DSAP change should add a
dated log entry and keep the work plan and checklist current.

## Change Log Template

### YYYY-MM-DD

**Scope**

Describe the scope of the change.

**Changes made**

List the code, docs, or tests added or changed.

**Files touched**

List the key files touched.

**Validation**

List commands run and the outcome.

**Decisions**

Record decisions, assumptions, and explicit tradeoffs.

**Risks / gaps**

Record anything deferred, incomplete, or uncertain.

**Next step**

Record the next planned stage or task.

## Seeded Work Plan

- Stage 1 evidence normalisation
  Scope: canonical event schema, event taxonomy, session artifact discovery, and
  normalization to `event-ledger.jsonl` without replacing existing tracing.
- Stage 2 pack assembly and integrity
  Scope: audit card, integrity manifest, SHA-256 verification, and DSAP bundle
  assembly.
- Stage 3 episodes and decision record
  Scope: `DecisionEpisode` support, explicit assumptions, uncertainties, and
  conclusion records.
- Stage 4 source register and disclosure
  Scope: source register, held-status semantics, disclosure profiles, and derived
  redaction outputs.
- Stage 5 retention and API surface
  Scope: retention classes, legal hold, HTTP endpoints, and CLI packaging.

## Review Checklist

- existing flows still work
- DSAP from full fixture
- DSAP from partial fixture
- explicit completeness grading
- redaction does not mutate sealed original
- integrity catches tampering
- tests pass
- `PROGRESS.MD` updated
- `CONTEXT.md` updated if assumptions changed

## Current Log

### 2026-03-10

**Scope**

Initialize the DSAP documentation set and deliver Milestone 1 evidence normalization.

**Changes made**

- add the DSAP design document
- add the DSAP implementation runbook
- scaffold `server/audit/` for later milestones without changing runtime behavior
- implement the canonical event schema and normalization pipeline in
  `server/audit/normalise.py`
- add `server/audit/schemas/event.schema.json` and milestone-placeholder schemas for
  later DSAP outputs
- extend `scripts/trace_report.py` additively so it now writes `event-ledger.jsonl`
- extend `scripts/trace_session.py` additively so `session.json` records `endedAt`
  and `exitCode`
- add focused regression tests

**Files touched**

- `docs/decision_support_audit_pack.md`
- `implement.md`
- `documentation.md`
- `server/audit/__init__.py`
- `server/audit/normalise.py`
- `server/audit/episode_builder.py`
- `server/audit/source_register.py`
- `server/audit/decision_record.py`
- `server/audit/redaction.py`
- `server/audit/integrity.py`
- `server/audit/pack_builder.py`
- `server/audit/disclosure.py`
- `server/audit/retention.py`
- `server/audit/schemas/*.json`
- `scripts/trace_report.py`
- `scripts/trace_session.py`
- `scripts/trace_utils.py`
- `tests/test_audit_normalise.py`
- `tests/test_trace_report_audit.py`
- `tests/test_trace_session.py`
- `PROGRESS.MD`
- `CONTEXT.md`
- `CHANGELOG.md`

**Validation**

- `python3 -m py_compile server/audit/normalise.py scripts/trace_report.py scripts/trace_session.py scripts/trace_utils.py`
  Result: pass
- `./.venv/bin/pytest -q --no-cov tests/test_audit_normalise.py tests/test_trace_report_audit.py tests/test_trace_report_host_metadata.py tests/test_trace_session.py`
  Result: `6 passed`
- `./.venv/bin/pytest -q tests/test_audit_normalise.py tests/test_trace_report_audit.py tests/test_trace_report_host_metadata.py tests/test_trace_session.py`
  Result: targeted tests passed but the repo-wide coverage gate failed on the narrow slice,
  so focused validation was rerun with `--no-cov`

**Decisions**

- DSAP is additive and must consume existing trace/session artifacts.
- Missing evidence will be declared by omission or explicit future gap handling, not
  silently reconstructed.
- Milestone 1 stops at canonical event normalization and session integration; integrity,
  disclosure, retention, and pack assembly remain for later milestones.
- Future DSAP modules are scaffolded as placeholders so later milestones can land without
  changing the established package layout.

**Risks / gaps**

- Later milestones still need integrity, disclosure, retention, legal-hold semantics,
  decision records, and source-register assembly.
- Milestone 1 intentionally does not emit completeness grades, disclosure outputs, or
  sealed bundles yet.
- Visible transcript normalization currently expects structured JSON or JSONL exports, not
  free-form Markdown transcript parsing.

**Next step**

Start Stage 2 pack assembly and integrity, using the new `event-ledger.jsonl` as the
normalized source layer.

### 2026-03-10

**Scope**

Deliver DSAP Milestones 2-6 additively on top of the existing normalization
pipeline.

**Changes made**

- implement DSAP pack assembly in `server/audit/pack_builder.py`, including
  retained-evidence materialization, completeness grading, required outputs,
  and `bundle/DSAP-<guid>.zip`
- implement additive episode slicing, decision records, source-register
  assembly, disclosure/redaction derivation, integrity manifest generation and
  verification, and retention-state/legal-hold handling
- add additive audit HTTP endpoints under `server/audit/api.py` and register
  them in `server/main.py`
- extend normalization additively to consume optional `decision-log.json` /
  `decision-log.jsonl` artifacts when present
- replace placeholder DSAP schemas with working audit-card, decision-record,
  source-access, and integrity-manifest schemas
- add acceptance-focused tests covering full fixture assembly, partial
  historical pack grading, tamper detection, derived redaction outputs,
  held-status semantics, and the audit API surface

**Files touched**

- `server/audit/__init__.py`
- `server/audit/api.py`
- `server/audit/disclosure.py`
- `server/audit/episode_builder.py`
- `server/audit/integrity.py`
- `server/audit/normalise.py`
- `server/audit/pack_builder.py`
- `server/audit/redaction.py`
- `server/audit/schemas/*.json`
- `server/config.py`
- `server/main.py`
- `tests/audit_test_utils.py`
- `tests/test_audit_api.py`
- `tests/test_audit_pack_builder.py`
- `documentation.md`
- `PROGRESS.MD`
- `CONTEXT.md`
- `CHANGELOG.md`

**Validation**

- `python3 -m py_compile server/audit/__init__.py server/audit/api.py server/audit/decision_record.py server/audit/disclosure.py server/audit/episode_builder.py server/audit/integrity.py server/audit/normalise.py server/audit/pack_builder.py server/audit/redaction.py server/audit/retention.py server/audit/source_register.py server/main.py`
  Result: pass
- `./.venv/bin/pytest -q --no-cov tests/test_audit_pack_builder.py tests/test_audit_api.py tests/test_audit_normalise.py tests/test_trace_report_audit.py tests/test_trace_report_host_metadata.py tests/test_trace_session.py`
  Result: `12 passed`

**Decisions**

- Keep retention state additive in `retention-state.json` so legal-hold changes
  do not require replacing the sealed original artifact set.
- Treat redaction as a derived disclosure view under `disclosures/<profile>/`
  and keep the original pack immutable.
- Grade completeness conservatively: missing end markers, missing visible
  transcript evidence, or unheld evidence force Grade `C`; lesser declared gaps
  fall to Grade `B`.

**Risks / gaps**

- The audit API currently resolves pack IDs under the configured default pack
  root; custom `outputRoot` values returned from `POST /audit/packs` are still
  usable directly but not discoverable again by pack ID unless they share that
  root.
- `integrity-manifest.json` intentionally excludes a hash for itself and the
  bundle zip to avoid circular sealing dependencies; verification still covers
  all retained evidence blobs plus the primary derived pack outputs.
- No full-repo regression run was executed in this turn.

**Next step**

Use the DSAP pack builder and API against real traced sessions, then decide
whether pack discovery/listing and bundle-hash sidecar coverage should be added
as follow-on work.

### 2026-03-10

**Scope**

Add DSAP follow-on support for pack discovery/listing and bundle hash sidecars.

**Changes made**

- add paged pack discovery in `server/audit/pack_builder.py` and `GET /audit/packs`
- add bundle SHA-256 sidecar generation for original and redacted DSAP zip bundles
- expose bundle hash metadata through pack metadata and `GET /audit/packs/{pack_id}/bundle/hash`
- extend disclosure metadata discovery so pack metadata reports available derived profiles
- add focused API and builder assertions for pagination and bundle sidecar hashing

**Files touched**

- `docs/decision_support_audit_pack.md`
- `server/audit/api.py`
- `server/audit/integrity.py`
- `server/audit/pack_builder.py`
- `server/audit/redaction.py`
- `tests/test_audit_api.py`
- `tests/test_audit_pack_builder.py`
- `documentation.md`
- `PROGRESS.MD`
- `CONTEXT.md`
- `CHANGELOG.md`

**Validation**

- `python3 -m py_compile server/audit/integrity.py server/audit/pack_builder.py server/audit/api.py server/audit/redaction.py tests/test_audit_api.py tests/test_audit_pack_builder.py`
  Result: pass
- `./.venv/bin/pytest -q --no-cov tests/test_audit_pack_builder.py tests/test_audit_api.py`
  Result: `7 passed`
- `./.venv/bin/pytest -q --no-cov tests/test_audit_pack_builder.py tests/test_audit_api.py tests/test_audit_normalise.py tests/test_trace_report_audit.py tests/test_trace_report_host_metadata.py tests/test_trace_session.py`
  Result: `13 passed`

**Decisions**

- Keep bundle hashing separate from `integrity-manifest.json` to avoid circular sealing while still giving the zip artifact its own verifiable SHA-256 sidecar.
- Restrict pack discovery to the configured `AUDIT_PACK_ROOT` so listing stays deterministic and does not scan arbitrary filesystem locations.

**Risks / gaps**

- Pack discovery remains root-scoped; packs created under ad hoc non-default roots are still returned directly at creation time but are not listed later unless they live under the configured audit-pack root.
- Bundle sidecars are metadata companions rather than sealed contents of the zip itself.

**Next step**

Run the DSAP surface against real session directories under the shared audit root and decide whether pack deletion/disposal workflows need an explicit admin API.

Read `AGENTS.md`, `CONTEXT.md`, `PROGRESS.MD`, `docs/client_trace_strategy.md`,
`docs/decision_support_audit_pack.md`, and `implement.md`, then start with Stage 1.
