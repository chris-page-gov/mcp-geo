---
type: "agent_control"
title: "Canonical AGENTS"
vault_role: "agent_control"
generated: false
protected: true
updated: "2026-04-14"
---
# AGENTS.md — Canonical Obsidian Agent Contract

This vault-root `AGENTS.md` is the canonical cross-tool instruction contract
for `obsidian` agent-control mode in this repository.

## Scope and precedence

- Repo-root `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, and
  `.github/copilot-instructions.md` are adapters in `obsidian` mode.
- This file is the smallest authoritative control surface inside the vault.
- Use supporting notes for current state and navigation rather than reading
  long legacy trackers by default.

## Mandatory read order

1. [[00 Home/00 - Agent Home]]
2. [[10 State/Current Focus]]
3. [[10 State/Work Queue]]
4. [[10 State/Verification]]
5. Generated digests only as compact supporting context:
   [[20 Generated/Repo Map Digest]],
   [[20 Generated/Active Plan Summary]],
   [[20 Generated/Recent Verification Summary]],
   [[20 Generated/Release Summary]]

## Non-negotiables

- Treat this vault as the current control plane for navigation and active
  state while `obsidian` mode is enabled.
- Do not edit `.obsidian/` unless the user explicitly asks.
- Treat `20 Generated/` notes as generated evidence, not hand-edited notes.
- Update `CONTEXT.md`, `PROGRESS.MD`, and `CHANGELOG.md` in the repo when
  workstream state materially changes.
- Use repo wrappers such as `scripts/pytest-local`, `scripts/ruff-local`, and
  `scripts/mypy-local` for host-side validation.

## Repo cues

- Root `AGENTS.md` remains the universal repo entrypoint in `classic` mode.
- The steering vault is `Obsidian/MCP Geo Agent Control/`.
- The broader repo-navigation vault remains
  `Obsidian/MCP Geo Knowledge Base/`.
