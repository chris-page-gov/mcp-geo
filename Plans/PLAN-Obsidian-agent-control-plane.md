# Obsidian Agent Control Plane

Date: 2026-04-14
Status: done
Owner: Codex / Chris Page

## Summary

Implement a switchable agent-control system that keeps root `AGENTS.md` as the
universal entrypoint while supporting two deterministic profiles:

- `classic`: current root-file-driven workflow
- `obsidian`: root files become thin adapters into a dedicated control vault at
  `Obsidian/MCP Geo Agent Control/`

The rollout is tracked as a normal repo workstream. Each green milestone should
update `PROGRESS.MD`, `CHANGELOG.md`, and `CONTEXT.md`, then be committed and
pushed before the next slice begins.

## Chosen defaults

- `AGENTS.md` remains the root cross-tool contract in both modes.
- `Obsidian/MCP Geo Agent Control/` is separate from
  `Obsidian/MCP Geo Knowledge Base/`.
- `CONTEXT.md` and `PROGRESS.MD` remain in the repo as compatibility shims in
  `obsidian` mode.
- `CHANGELOG.md` remains the release ledger and is not moved into the vault.
- v1 evaluation is a dedicated smoke pack, not unattended-harness integration.
- Official Obsidian CLI support is required for `obsidian` mode validation.
  The current local app version is below the required threshold, so upgrade and
  CLI enablement remain explicit prerequisites for full validation.

## Milestones

### OACP-0 Checked-in plan and tracker baseline

- Add this plan file.
- Add the `PROGRESS.MD` workstream and `CHANGELOG.md` baseline entry.
- Align `CONTEXT.md` with the new workstream and defaults.

### OACP-1 Dedicated control vault scaffold and digest model

- Create `Obsidian/MCP Geo Agent Control/` with curated control notes:
  `00 Home`, `Current Focus`, `Work Queue`, `Decisions`, `Verification`, and
  `Change Summary`.
- Add generated compact digests for repo map, active plan summary, recent
  verification summary, and release summary.
- Define one mandatory read order in the home note.
- Ensure generated updates never overwrite curated control notes.

### OACP-2 Obsidian CLI wrapper and preflight

- Add a repo wrapper around the official Obsidian CLI for note read and search.
- Validate:
  - Obsidian app version `>=1.12.7`
  - CLI enabled in app settings
  - CLI can address the control vault
- Fail with precise prerequisite messages when local setup is not ready.

### OACP-3 Switchable classic and obsidian profiles

- Add `scripts/switch_agent_mode.py --mode classic|obsidian`.
- In `classic` mode, regenerate the baseline root adapter surfaces.
- In `obsidian` mode:
  - rewrite `AGENTS.md` as a short bootstrap into the control-vault home note
  - rewrite `CLAUDE.md`, `GEMINI.md`, and `.github/copilot-instructions.md`
    as thin adapters to the same contract
  - slim `CONTEXT.md` and `PROGRESS.MD` into compatibility summaries
- Write a machine-readable active-mode manifest under `data/agent_control/`.

### OACP-4 Instruction-focused smoke evaluation pack

- Add a small pack for Codex, Claude, Gemini, and VS Code that compares
  `classic` and `obsidian` modes on:
  - active profile discovery
  - current-focus lookup
  - work-queue lookup
  - repo-navigation lookup
  - update-discipline behavior
  - guardrail adherence around `.obsidian/` and protected notes
- Keep this separate from the unattended capability harness.

### OACP-5 Runbook, final docs, and validation closure

- Publish the mode-switch runbook and evaluation workflow.
- Distinguish the new control vault from the existing knowledge-base vault in
  repo docs.
- Run the focused validation slices for the new scripts and tests.
- Update `PROGRESS.MD`, `CHANGELOG.md`, and `CONTEXT.md` with final state.

## Validation plan

- Unit tests:
  - mode switching rewrites the expected root files
  - repeated switches are idempotent
  - curated notes survive rebuilds
  - generated digests reflect the current repo state
  - Obsidian CLI preflight reports specific failure reasons
- Integration tests:
  - `classic` mode build/validate passes
  - `obsidian` mode build/validate passes when prerequisites are met
  - root adapters for Claude, Gemini, and Copilot point to one active contract
- Acceptance:
  - `classic -> obsidian -> classic` is deterministic
  - `obsidian` mode routes agents into the control vault, not the large root
    trackers
  - the smoke pack produces comparable evidence for both modes

## Commit cadence

Recommended commit sequence:

1. `docs(plan): add Obsidian agent control plane plan and tracker baseline`
2. `feat(obsidian): scaffold agent control vault and generated digest model`
3. `feat(obsidian): add Obsidian CLI wrapper and validation preflight`
4. `feat(agent-mode): add classic/obsidian switcher and root adapter generation`
5. `test(eval): add instruction smoke pack for classic vs obsidian modes`
6. `docs(obsidian): finalize runbook, tracker updates, and changelog`
