## Added

- Documented a repeatable two-stage LLM-wiki postmortem workflow and added a
  Codex session inventory script that writes private candidate registers under
  the gitignored `postmortem/` tree while keeping `postmortem-public/` as the
  publishable derivative.
- Extended the private inventory with repeated-session rollups for scheduled
  automations, retry batches, and short status/check-monitoring runs, including
  summed token, message, and tool-call metrics for compact curation.
- Added the first public-safe Stage 2 capture selection queue, choosing seven
  Codex sessions from the existing Claude example documents and the ONS UPRN
  client-failure incident for follow-on LLM-wiki curation.
- Documented the restartable Stage 2 execution contract for unreliable
  connectivity, with private checkpoint state under gitignored `postmortem/`
  and bounded one-conversation/one-capture resume slices.
- Curated the first restartable Stage 2 slice as CONV-002, covering the CV1
  3HB Claude map-failure/control-probe examples and updating public registers
  for CAP-002 through CAP-004.
- Curated the second restartable Stage 2 slice as CONV-003, covering the
  Leamington/Warwick stats-routing examples and updating public registers for
  CAP-005 and CAP-006.
- Curated the final selected Stage 2 slice as CONV-004, covering the ONS UPRN
  shard-ingestion incident and marking CAP-007 plus the selected batch
  complete.
