# DSAP Implementation Runbook

This work is additive. It must preserve existing trace/session workflows and must not
replace the current tracing stack.

## Working Rules

- Start by reading `AGENTS.md`, `CONTEXT.md`, `PROGRESS.MD`, and
  `docs/client_trace_strategy.md`.
- Treat DSAP as an audit layer on top of existing traces, session metadata, UI event
  logs, and optional transcript exports.
- Preserve existing `scripts/trace_session.py`, trace proxies, UI event logging, and
  `scripts/trace_report.py` behavior except for additive outputs.

## Non-goals

- No chain-of-thought capture or reconstruction
- No silent reconstruction of missing evidence
- No replacement of the current tracing stack
- No logging of secrets

## Required Files

Create and maintain these files as the implementation grows:

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
- `server/audit/schemas/audit_card.schema.json`
- `server/audit/schemas/event.schema.json`
- `server/audit/schemas/source_access.schema.json`
- `server/audit/schemas/decision_record.schema.json`
- `server/audit/schemas/integrity_manifest.schema.json`

## Milestone Order

1. Milestone 1 canonical event schema and normalisation
2. Milestone 2 integrity and pack assembly
3. Milestone 3 episode support and decision record
4. Milestone 4 source register and held-status semantics
5. Milestone 5 disclosure profiles and redaction
6. Milestone 6 retention, hold, and APIs

## Implementation Expectations

- Milestone 1 must normalize existing session artifacts into a canonical Event Ledger.
- All work must be additive and preserve current trace/session outputs.
- Existing reports and bundles should continue to work.
- Tests are required under `tests/`.
- Update `documentation.md` and `PROGRESS.MD` as work progresses.

## Acceptance Tests

- DSAP from live-style traced session fixture
- DSAP from historical session with full evidence
- DSAP from partial historical session declaring gaps
- integrity verification catches tampering
- redaction preserves original and emits derivative
- source register distinguishes held-status states
- regression coverage for existing trace/session flows

## Suggested Prompt to Start Codex

Implement Milestone 1 only first. Read `AGENTS.md`, `CONTEXT.md`, `PROGRESS.MD`,
and `docs/client_trace_strategy.md`, then add the canonical event schema and
normalisation pipeline under `server/audit/` without replacing the current tracing
stack. Preserve existing trace/session workflows, add focused tests, update
`documentation.md` and `PROGRESS.MD`, and stop after Milestone 1 with a summary of
remaining milestones.

