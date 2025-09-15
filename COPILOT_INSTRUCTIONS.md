# Copilot Instructions

These instructions help AI assistants contribute effectively and safely.

## Project Purpose

Catalogue files on mounted disks / volumes, store or query metadata (sizes, paths) via DuckDB, and support analytics / ad‑hoc queries.

## Tech Stack

- Python 3.11+
- DuckDB for querying metadata
- Testing: pytest + coverage
- Lint/Format: Ruff + Black
- Type checking: mypy
- Dependency / env tooling: uv (preferred), pip during container build for base dev tools

## Conventions

- Source code in `src/disk_catalogue`.
- Tests in `tests/` mirroring module structure.
- Keep functions small; prefer pure / side‑effect free logic where possible.
- Use type hints everywhere and `from __future__ import annotations` in new modules.
- Keep line length <= 100.
- Document public functions with concise docstrings (1‑2 line summary + args/returns if non-trivial.)
- Do NOT introduce hard tab characters; use spaces only (enforced by `.editorconfig`).
- Markdown style: first line must be a single H1, increment heading levels by 1, fenced code blocks MUST specify a language (`bash`, `python`, `sql`, etc.).
- No trailing whitespace; lists should use `-` (preferred) or numbered lists; avoid asterisks + tabs.
- For nested lists indent by 2 spaces (never tabs). If editing existing content containing tabs, replace them.
- When modifying `build.md`, run a quick scan for tabs (search `"\t"`) and remove any before finalizing.

## Dependency Management

- Base dev dependencies baked into the image.
- New runtime deps: add to `[project].dependencies` in `pyproject.toml` then run `uv pip install -e .` (or `pip install -e .`).
- New dev-only deps: add under `[project.optional-dependencies].dev`.

## Testing & Quality Gates

1. Run `pytest` (quick) or `pytest --cov` for coverage.
2. Run `ruff check .` and `ruff format --check .` (or `black .`).
3. Run `mypy .` (must pass in CI).
4. Markdown lint: ensure no hard tabs and proper fenced code languages. (If a markdown linter is added later, fix all warnings in the touched files.)

## Commit / PR Guidelines

- Small, focused commits; imperative tense in subject ("Add scanner for recursive file collection").
- Include reasoning or tradeoffs in commit body when non-obvious.
- Update `CHANGELOG.md` for user-visible changes.
- Before committing, verify: no tab characters (`git grep $'\t' || true` should return nothing you authored), and `ruff check` + `mypy` pass.

## Adding Features

1. Start with a failing test describing behavior.
2. Implement minimal code to pass tests.
3. Refactor while keeping coverage.
4. Update docs / changelog.
5. Re-run a tab scan on changed markdown files if any were edited.

## Non-Goals (avoid implementing unless discussed)

- Full-text indexing of file contents.
- Complex distributed crawling.
- Persisting large blobs outside DuckDB.

## Security / Safety

- Never execute untrusted shell input.
- Avoid following symlinks outside the root scan path without explicit opt-in.

## Future Ideas (Backlog Hints)

- Persist scan results into a DuckDB table and incremental updates.
- CLI entry point.
- Parallel scanning with thread / process pools.
- File hashing (configurable) for duplicate detection.
- Add automated markdown lint (e.g., `markdownlint-cli`) and a pre-commit hook to enforce no hard tabs.

## How to Ask for Clarification

If requirements are ambiguous, propose 1–2 concrete interpretations and proceed with the most reasonable after a short wait for feedback.

---

AI assistants: adhere to these instructions. When unsure, ask or create a small draft PR for review.
