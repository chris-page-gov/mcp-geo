# Repository Guidelines

## Project Structure & Module Organization
- `src/disk_catalogue/`: Python package (scanner and public API).
- `tests/`: Pytest suite (`test_*.py`).
- `scripts/`: Dev and data tooling (lint, tests, CSV/DuckDB helpers).
- `output/`: Generated CSVs from drive scans (gitignored).
- Root SQL/CSV docs: `duckdb_schema.sql`, `sample_queries.sql`, `drive_manifest.csv`.

## Build, Test, and Development Commands
- Install (editable, with dev tools): `pip install -e .[dev]` (or `uv pip install -e .[dev]`).
- Run tests (with coverage via pyproject): `pytest` or `scripts/run_tests.sh`.
- Lint/format/type-check: `scripts/lint.sh` (runs ruff, black --check, mypy).
- Format code: `ruff format .` (or `black .`).

## Coding Style & Naming Conventions
- Python 3.11, 4‑space indent, LF endings; max line length 100.
- Use `ruff` (rules: E,F,W,I,B,C4,UP,RUF) and `black` for formatting.
- Types: `mypy --strict` is enabled; add/maintain type hints.
- Naming: modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Package import path is `disk_catalogue` (ensure code lives under `src/`).

## Testing Guidelines
- Framework: `pytest` with `pytest-cov` (configured in `pyproject.toml`).
- Name tests `test_*.py`; prefer small, deterministic unit tests.
- Keep/raise coverage when changing behavior; add tests for regressions.
- Use `tmp_path` and fixtures for filesystem interactions.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (see `commit-template.txt`): `type(scope): subject`.
  Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci.
- PRs: include clear description, linked issues, and before/after notes. For data/CLI changes, show example command/output.
- Run `scripts/lint.sh` and `pytest` locally before opening a PR.

## Docs & Changelog Sync
- Always update `CHANGELOG.md` (Unreleased) for user-visible changes: new scripts/CLI flags, schema/view changes, devcontainer behavior, or Git ignore patterns.
- Keep docs current when code changes:
  - `README.md`: quick start, catalogue/queries examples, new commands.
  - `README_cataloguing.md`: end-to-end workflow, orchestrator usage, identifiers (`Drive`, `RelativePath`, `FileKey`).
  - `sample_queries.sql`: add/edit queries if views/columns change.
  - Script headers (`scripts/*.sh`, `scripts/*.py`): usage and outputs.
- If you touch devcontainer or mounts, note it in README “Dev Container” and in the changelog.
- Do not bump version; maintainers will cut releases. Leave changes under [Unreleased].

## Changelog, Versioning, and Commit Practices
- Working changes (non-release):
  - Append to `CHANGELOG.md` under `[Unreleased]` with clear bullets (Added/Changed/Fixed/Removed).
  - Commit with a docs-focused message, e.g.: `docs(changelog): note ingest view changes and new scan script`.
  - Ensure docs/tests align with the changelog entry.
- Preparing a release (maintainers):
  1) Sync with the default branch: `git fetch origin && git switch main && git rebase origin/main`.
  2) Choose the next SemVer. Update in two places:
     - `pyproject.toml` → `[project].version`
     - `src/disk_catalogue/__init__.py` → `__version__`
  3) Finalize `CHANGELOG.md`:
     - Move items from `[Unreleased]` to a new `## [x.y.z] - YYYY-MM-DD` section.
     - Leave `[Unreleased]` in place for future work (empty or with a placeholder).
  4) Commit with a concise release message whose body mirrors the changelog bullets:
     - Subject: `chore(release): vX.Y.Z`
     - Body: copy the `Added/Changed/Fixed` bullets from the new section.
     - Example:
       - `chore(release): v0.1.2` + body listing each change exactly as in the changelog.
  5) Tag the release: `git tag -a vX.Y.Z -m "Release vX.Y.Z"` and push: `git push && git push --tags`.
  6) Verify: run `scripts/lint.sh`, `scripts/run_tests.sh`, and a quick schema validate.
- Post‑release: start adding new items back under `[Unreleased]` for subsequent PRs.

## CI Releases
- This repo includes a GitHub Actions workflow that creates a Release on tag push (`v*`).
- The workflow:
  - Builds Python distributions (`dist/*`).
  - Extracts the notes for the matching version from `CHANGELOG.md`.
  - Publishes a GitHub Release and uploads `dist/*` as assets.
- To publish: follow the release steps above and push the tag. The action runs automatically.

## Security & Configuration Tips
- Do not commit secrets or local paths; `.env*`, output CSVs, and DuckDB files are gitignored.
- Do not commit real drive manifests. Commit `drive_manifest.template.csv`; keep `drive_manifest.csv` untracked (gitignored).
- When scanning drives, prefer the dev container and read‑only mounts (see `build.md`).
- Large data belongs in `output/` and stays out of version control.

## Agent-Specific Notes
- Make minimal, focused changes; do not rename files or APIs without discussion.
- Obey these guidelines for any files you touch and update docs/tests alongside code changes.
