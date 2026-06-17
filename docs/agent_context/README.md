# Agent Context Index

This directory holds repo-specific context that is useful but too detailed for
hot-path instruction files.

Use this split to keep agent startup efficient:

- `CONTEXT.md`: current active handoff only.
- `AGENTS.md`: stable repo rules and compact checklists.
- `PROGRESS.MD`: active workstreams and recent release gates only.
- `docs/agent_context/*`: historical notes, operational playbooks, and
  domain-specific extension contracts.

Current Codex guidance favours short, deterministic repository instructions
with task-specific linked references over very long always-loaded instruction
files. Keep new detailed guidance here unless every agent needs it on every
turn.

Useful upstream references:

- OpenAI Codex best practices: https://developers.openai.com/codex/learn/best-practices
- AGENTS.md guidance: https://developers.openai.com/codex/guides/agents-md
- Codex skills: https://developers.openai.com/codex/skills
- Codex memories: https://developers.openai.com/codex/memories
