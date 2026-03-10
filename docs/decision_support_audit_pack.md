# Decision Support Audit Pack (DSAP)

Codex should start DSAP work by reading `AGENTS.md`, `CONTEXT.md`, `PROGRESS.MD`, and
`docs/client_trace_strategy.md`.

## Purpose

The Decision Support Audit Pack (DSAP) is a governed audit-output design for MCP-Geo.
It extends the existing trace/session tooling and does not replace it. The current
session wrappers, MCP JSON-RPC proxies, UI event logging, and `trace_report.py`
remain the capture and session-summary layer. DSAP adds a normalized, governable,
point-in-time audit layer on top of those retained artifacts.

The DSAP is intended to support:

- FOI support
- government and internal audit
- legal or investigation workflows
- engineering reconstruction and incident review

## Terms

- Decision Support Audit Pack: A sealed, point-in-time audit bundle for one conversation,
  one decision episode, or one requested snapshot, with normalized records, retained
  evidence references, integrity metadata, and disclosure metadata.
- Audit Card: A compact machine-readable and human-readable front sheet describing what
  the pack covers, its scope, completeness grade, disclosure profile, retention class,
  legal-hold status, integrity status, and key caveats.
- Event Ledger: The canonical append-only JSONL stream of normalized events derived from
  retained evidence. It is the primary replay and reconstruction surface.
- Evidence Register: The index of retained evidence items and blobs, including file
  paths, hashes, capture time, evidence class, and held-status.
- Source Register: The normalized record of source access events and source materials
  referenced or accessed during the conversation or episode.
- Decision Record: The explicit record of assumptions, uncertainties, conclusions, and
  completeness statements that were user-visible or otherwise explicitly captured.
- Disclosure Profile: The rule set describing what a derived pack may expose for a
  defined audience without changing the sealed original.

## Design Principles

- Observable not speculative: record what was actually observed in traces, transcripts,
  or retained evidence; do not invent missing rationale or missing evidence.
- Append-only evidence: preserve retained evidence blobs and append derivative records;
  do not mutate prior evidence.
- Point-in-time fixity: produce a pack whose hashes and manifests can be verified later.
- Conversation, episode, and snapshot support: allow audit scope to cover an entire
  conversation, a narrower decision episode, or a specific requested snapshot.
- Explicit completeness grading: every pack declares completeness as grade `A`, `B`, or
  `C`, with stated reasons.
- Disclosure separate from retention: disclosure rules produce derived views; retention
  policy and legal hold apply to the underlying retained evidence.
- Security by default: secrets are redacted from derivative views and disclosure output;
  chain-of-thought is not recorded.

## Core Entities

- Conversation: The top-level user-assistant interaction scope, typically aligned to a
  trace-session directory or equivalent conversation identifier.
- DecisionEpisode: A bounded subset of a conversation covering one decision-support
  moment or issue, with its own scope and completeness.
- AuditPack: The governed bundle for a conversation, episode, or snapshot.
- Event: One canonical normalized event in the Event Ledger.
- EvidenceItem: One retained artifact or blob referenced by the pack, such as a trace
  line, transcript export, UI event record, or source payload.
- SourceAccess: One normalized record describing access to an external or internal
  source, including request/response evidence and held-status.

## Canonical Event Taxonomy

The taxonomy is extensible, but DSAP must support at least these canonical event types:

- `conversation.started`
- `conversation.snapshot_requested`
- `conversation.closed`
- `message.user_visible`
- `message.assistant_visible`
- `message.assistant_conclusion`
- `mcp.session.initialized`
- `mcp.tools.list`
- `mcp.tool.call`
- `mcp.tool.result`
- `mcp.resource.read`
- `mcp.elicitation.requested`
- `mcp.elicitation.responded`
- `ui.choice.made`
- `source.http.requested`
- `source.http.responded`
- `decision.assumption_logged`
- `decision.uncertainty_logged`
- `decision.conclusion_recorded`
- `audit_pack.created`
- `audit_pack.sealed`
- `audit_pack.redacted`
- `audit_pack.legal_hold_applied`

## Required Outputs

Each DSAP should be able to produce these outputs, either immediately or in later
milestones:

- `audit-card.json`
- `audit-card.md`
- `conversation-record.json`
- `decision-record.json`
- `event-ledger.jsonl`
- `evidence-register.json`
- `source-register.json`
- `redaction-manifest.json`
- `integrity-manifest.json`
- `transcript-visible.md`
- `generated/report.md`
- `bundle/DSAP-<guid>.zip`

## Completeness Grades

- Grade `A`: Full or near-full retained evidence for the scoped pack, including the
  Event Ledger, retained evidence references, and explicit decision/disclosure metadata.
- Grade `B`: Material evidence retained, but with declared omissions such as missing
  transcript export, partial source access traces, or incomplete episode tagging.
- Grade `C`: Partial historical reconstruction from retained traces only, with clear gap
  statements and no silent filling-in of missing evidence.

## Disclosure Profiles

- `internal_full`: Full internal disclosure of retained evidence references, normalized
  records, hashes, and operational metadata, subject to normal secret redaction.
- `internal_restricted`: Internal disclosure with access-sensitive fields, some source
  payloads, or protected data references withheld or summarized.
- `foi_redacted`: Derived disclosure profile intended for FOI-style release, preserving
  audit structure while redacting protected content and sensitive operational detail.

## Integrity Requirements

- Every retained file and every derived DSAP output must carry a SHA-256 hash.
- `integrity-manifest.json` must list file path, byte size, SHA-256, and verification
  status for every included artifact.
- Verification must re-hash artifacts and fail closed on mismatch.
- The sealed original pack remains immutable; any redacted derivative references the
  original manifest and records derivation lineage.

## Retention and Hold

- Every pack declares a `retention_class`.
- Every pack declares `legal_hold` as a first-class state.
- `legal_hold` blocks deletion or scheduled disposal of retained evidence until released
  by authorized policy workflow.

## Source of Truth

The Event Ledger plus the retained evidence blobs are the source of truth. Audit Cards,
Decision Records, Source Registers, and redacted derivatives are secondary views derived
from that source of truth.

## Relationship to Existing Trace/Session Tooling

DSAP extends the current tracing/session model:

- `scripts/trace_session.py`, `scripts/vscode_trace_snapshot.py`, and the MCP trace
  proxies remain the primary capture tools.
- `scripts/trace_report.py` remains the session summary and report surface.
- DSAP normalization consumes session artifacts such as `session.json`,
  `mcp-stdio-trace.jsonl`, `mcp-http-trace.jsonl`, `ui-events.jsonl`, and optional
  visible transcript exports.
- DSAP must not replace the current tracing stack or silently reconstruct evidence not
  present in those artifacts.

## Proposed Implementation Layout

Implement DSAP additively under `server/audit/`:

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
- `server/audit/schemas/`

Recommended responsibilities:

- `normalise.py`: canonical event schema, evidence mapping, normalization from existing
  trace/session artifacts
- `episode_builder.py`: decision-episode slicing and episode metadata
- `source_register.py`: normalized source access records and held-status handling
- `decision_record.py`: explicit assumptions, uncertainties, conclusions
- `redaction.py`: derivative redaction rules and manifest generation
- `integrity.py`: SHA-256 hashing, sealing, and verification
- `pack_builder.py`: pack assembly and bundle generation
- `disclosure.py`: disclosure-profile-specific export logic
- `retention.py`: retention class and legal-hold semantics

## Suggested HTTP Endpoints

Suggested additive API surface:

- `GET /audit/packs` to list discoverable packs under the configured audit-pack root
- `POST /audit/normalise` to normalize a session or uploaded artifact set into an Event
  Ledger
- `POST /audit/packs` to assemble a DSAP from a scoped conversation or episode
- `GET /audit/packs/{pack_id}` to fetch Audit Card metadata
- `GET /audit/packs/{pack_id}/bundle` to download the sealed or derived bundle
- `GET /audit/packs/{pack_id}/bundle/hash` to fetch the bundle SHA-256 sidecar
- `POST /audit/packs/{pack_id}/verify` to verify integrity against the manifest
- `POST /audit/packs/{pack_id}/redact` to produce a derived disclosure-profile bundle
- `POST /audit/packs/{pack_id}/legal-hold` to apply or release legal hold

## Suggested CLI Commands

Suggested additive CLI commands:

- `python scripts/trace_report.py <session-dir>` to keep generating the existing report,
  now with normalized audit outputs where available
- `python -m server.audit.normalise <session-dir>` to emit `event-ledger.jsonl`
- `python -m server.audit.pack_builder <session-dir>` to assemble a DSAP bundle
- `python -m server.audit.integrity verify <pack-dir>` to verify hashes and seal status

## Minimum Acceptance Criteria

- Existing trace/session workflows continue to work without configuration changes.
- DSAP normalization is additive and does not replace current raw trace artifacts.
- A traced session can produce a canonical `event-ledger.jsonl`.
- The canonical Event Ledger records only observed evidence and explicit gaps.
- No chain-of-thought is captured.
- No secrets are emitted in normalized outputs.
- The design supports completeness grading, disclosure profiles, retention class, and
  legal-hold semantics even where later milestones implement them fully.
