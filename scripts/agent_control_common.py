from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "Obsidian" / "MCP Geo Agent Control"
DEFAULT_MANIFEST_PATH = REPO_ROOT / "data" / "agent_control" / "control_vault_manifest.json"
DEFAULT_ACTIVE_MODE_MANIFEST_PATH = REPO_ROOT / "data" / "agent_control" / "active_mode.json"

CURATED_NOTES: tuple[tuple[str, str, bool], ...] = (
    ("00 Home/00 - Agent Home.md", "Agent Home", True),
    ("10 State/Current Focus.md", "Current Focus", False),
    ("10 State/Work Queue.md", "Work Queue", False),
    ("10 State/Decisions.md", "Decisions", False),
    ("10 State/Verification.md", "Verification", False),
    ("10 State/Change Summary.md", "Change Summary", False),
)

GENERATED_NOTES: tuple[tuple[str, str], ...] = (
    ("20 Generated/Repo Map Digest.md", "Repo Map Digest"),
    ("20 Generated/Active Plan Summary.md", "Active Plan Summary"),
    ("20 Generated/Recent Verification Summary.md", "Recent Verification Summary"),
    ("20 Generated/Release Summary.md", "Release Summary"),
)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def today_utc() -> str:
    return dt.datetime.now(dt.UTC).date().isoformat()


def render_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {json.dumps(str(item))}")
            continue
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = json.dumps(str(value))
        lines.append(f"{key}: {rendered}")
    lines.append("---")
    return "\n".join(lines)


def git_ls_files(repo_root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return sorted(
            str(path.relative_to(repo_root))
            for path in repo_root.rglob("*")
            if path.is_file() and ".git" not in path.parts
        )
    return sorted(line.strip() for line in completed.stdout.splitlines() if line.strip())


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    capture = False
    section_lines: list[str] = []
    for line in lines:
        if line.strip() == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            section_lines.append(line)
    return "\n".join(section_lines).strip()


def unique_preserving_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def parse_markdown_bullets(text: str, limit: int) -> list[str]:
    bullets: list[str] = []
    current: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("- "):
            if current:
                bullets.append(" ".join(current))
                current = []
            current.append(stripped[2:])
            continue
        if current and stripped and not stripped.startswith("#"):
            current.append(stripped)
            continue
        if current:
            bullets.append(" ".join(current))
            current = []
        if len(bullets) >= limit:
            break
    if current and len(bullets) < limit:
        bullets.append(" ".join(current))
    return bullets[:limit]


def render_curated_note(title: str, protected: bool) -> str:
    updated = today_utc()
    frontmatter = render_frontmatter(
        {
            "type": "agent_control",
            "title": title,
            "vault_role": "agent_control",
            "generated": False,
            "protected": protected,
            "updated": updated,
        }
    )
    if title == "Agent Home":
        body = """# Agent Home

## Mandatory Read Order

1. Read root `AGENTS.md`.
2. Read [[Current Focus]].
3. Read [[Work Queue]].
4. Read [[Verification]].
5. Use the generated digests only as compact supporting context:
   [[Repo Map Digest]], [[Active Plan Summary]],
   [[Recent Verification Summary]], [[Release Summary]].

## Guardrails

- This vault is separate from `Obsidian/MCP Geo Knowledge Base/`.
- Treat `20 Generated/` notes as generated evidence, not hand-edited notes.
- Do not modify `.obsidian/` unless the user explicitly asks.
"""
    elif title == "Current Focus":
        body = """# Current Focus

## Active priorities

- Build the switchable `classic` / `obsidian` agent-control plane.
- Keep root `AGENTS.md` as the universal entrypoint.
- Replace large default tracker reads with a compact control-vault path.

## Current blocker

- Official Obsidian CLI validation needs Obsidian `>=1.12.7`.
- The current local app version observed during planning was `1.8.7`.
"""
    elif title == "Work Queue":
        body = """# Work Queue

## Active

- OACP-1 Dedicated control vault scaffold and digest model

## Next

- OACP-2 Obsidian CLI wrapper and validation preflight
- OACP-3 Switchable classic/obsidian mode profiles
- OACP-4 Instruction-focused smoke evaluation pack

## Completion rule

- Commit and push each green milestone before starting the next slice.
"""
    elif title == "Decisions":
        body = """# Decisions

## Chosen defaults

- Root `AGENTS.md` stays the universal contract.
- `Obsidian/MCP Geo Agent Control/` is the steering vault.
- `Obsidian/MCP Geo Knowledge Base/` remains the repo-navigation vault.
- `CONTEXT.md` and `PROGRESS.MD` become compatibility shims in `obsidian` mode.
- `CHANGELOG.md` remains the canonical release ledger.
"""
    elif title == "Verification":
        body = """# Verification

## Where to look first

- [[Recent Verification Summary]]
- `CONTEXT.md` -> `Verification Status`
- `PROGRESS.MD` milestone notes with focused validation commands

## Expected use

- Record the narrowest meaningful checks for each slice.
- Prefer command evidence over prose-only assertions.
"""
    else:
        body = """# Change Summary

## Current change cluster

- Use this note for short human-readable summaries of the current rollout.
- Keep summaries compact and link to generated evidence where possible.
"""
    return f"{frontmatter}\n{body.rstrip()}\n"


def parse_plan_entries(repo_root: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    plans_dir = repo_root / "Plans"
    for path in sorted(plans_dir.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True):
        text = path.read_text(encoding="utf-8")
        status_match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
        date_match = re.search(r"^Date:\s*(.+)$", text, re.MULTILINE)
        milestones = re.findall(r"^###\s+(.+)$", text, re.MULTILINE)[:4]
        entries.append(
            {
                "path": str(path.relative_to(repo_root)),
                "title": first_heading(text, path.stem),
                "status": status_match.group(1).strip() if status_match else "unknown",
                "date": date_match.group(1).strip() if date_match else "",
                "milestones": milestones,
            }
        )
    return entries


def parse_unreleased_bullets(changelog_text: str) -> list[str]:
    section = extract_section(changelog_text, "## [Unreleased]")
    return parse_markdown_bullets(section, limit=6)


def parse_recent_releases(changelog_text: str) -> list[str]:
    matches = re.findall(r"^## \[([^\]]+)\] - ([0-9-]+)$", changelog_text, re.MULTILINE)
    rendered = [f"{version} ({date})" for version, date in matches if version != "Unreleased"]
    return rendered[:4]


def parse_verification_commands(progress_text: str) -> list[str]:
    commands = re.findall(
        r"`([^`\n]*(?:pytest|ruff|py_compile|playwright|validate)[^`\n]*)`",
        progress_text,
    )
    return unique_preserving_order(commands)[:6]


def render_generated_note(
    title: str,
    body: str,
    source_paths: list[str],
) -> str:
    frontmatter = render_frontmatter(
        {
            "type": "agent_control_generated",
            "title": title,
            "vault_role": "agent_control",
            "generated": True,
            "protected": True,
            "updated": today_utc(),
            "source_paths": source_paths,
        }
    )
    return f"{frontmatter}\n{body.rstrip()}\n"


def repo_map_note(repo_root: Path) -> tuple[str, list[str]]:
    top_level = sorted({path.split("/", 1)[0] for path in git_ls_files(repo_root)})
    key_runtime = [
        name
        for name in ["server", "tools", "resources", "scripts", "tests", "playground", "ui"]
        if name in top_level
    ]
    knowledge = [
        name
        for name in ["docs", "research", "Obsidian", "Plans", "skills", "RELEASE_NOTES"]
        if name in top_level
    ]
    control_files = [
        name
        for name in ["AGENTS.md", "CONTEXT.md", "PROGRESS.MD", "CHANGELOG.md"]
        if (repo_root / name).exists()
    ]
    body = "\n".join(
        [
            "# Repo Map Digest",
            "",
            "## Core runtime surfaces",
            *(f"- `{item}/`" for item in key_runtime),
            "",
            "## Knowledge and planning surfaces",
            *(f"- `{item}/`" if "." not in item else f"- `{item}`" for item in knowledge),
            "",
            "## Root control files",
            *(f"- `{item}`" for item in control_files),
            "",
            "## Reading hint",
            "- Start with `AGENTS.md`, then the state notes under `10 State/`.",
        ]
    )
    sources = ["AGENTS.md", "CONTEXT.md", "PROGRESS.MD", "CHANGELOG.md", "Plans/"]
    return body, sources


def active_plan_note(repo_root: Path) -> tuple[str, list[str]]:
    entries = parse_plan_entries(repo_root)
    lines = [
        "# Active Plan Summary",
        "",
        "## Current plans",
    ]
    for entry in entries[:5]:
        status_text = f" | status `{entry['status']}`" if entry["status"] else ""
        date_text = f" | date `{entry['date']}`" if entry["date"] else ""
        lines.append(f"- `{entry['path']}`: {entry['title']}{status_text}{date_text}")
        for milestone in entry["milestones"]:
            lines.append(f"  - {milestone}")
    if len(lines) == 3:
        lines.append("- No plan files found.")
    sources = [entry["path"] for entry in entries[:5]]
    return "\n".join(lines), sources or ["Plans/"]


def recent_verification_note(repo_root: Path) -> tuple[str, list[str]]:
    context_text = (repo_root / "CONTEXT.md").read_text(encoding="utf-8")
    progress_text = (repo_root / "PROGRESS.MD").read_text(encoding="utf-8")
    verification_section = extract_section(context_text, "## Verification Status")
    verification_bullets = [
        line.strip()[2:]
        for line in verification_section.splitlines()
        if line.strip().startswith("- ")
    ][:5]
    commands = parse_verification_commands(progress_text)
    lines = [
        "# Recent Verification Summary",
        "",
        "## Verification status highlights",
    ]
    if verification_bullets:
        lines.extend(f"- {item}" for item in verification_bullets)
    else:
        lines.append("- See `CONTEXT.md` -> `Verification Status` for the current summary.")
    lines.extend(
        [
            "",
            "## Recent recorded validation commands",
        ]
    )
    if commands:
        lines.extend(f"- `{command}`" for command in commands)
    else:
        lines.append("- No validation commands were extracted from `PROGRESS.MD`.")
    return "\n".join(lines), ["CONTEXT.md", "PROGRESS.MD"]


def release_summary_note(repo_root: Path) -> tuple[str, list[str]]:
    changelog_text = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = parse_unreleased_bullets(changelog_text)
    releases = parse_recent_releases(changelog_text)
    lines = [
        "# Release Summary",
        "",
        "## Unreleased highlights",
    ]
    if unreleased:
        lines.extend(f"- {item}" for item in unreleased)
    else:
        lines.append("- No unreleased bullets found.")
    lines.extend(["", "## Recent tagged releases"])
    if releases:
        lines.extend(f"- `{item}`" for item in releases)
    else:
        lines.append("- No released versions were parsed from `CHANGELOG.md`.")
    return "\n".join(lines), ["CHANGELOG.md", "RELEASE_NOTES/"]


def ensure_obsidian_defaults(output_root: Path) -> None:
    obsidian_root = output_root / ".obsidian"
    obsidian_root.mkdir(parents=True, exist_ok=True)
    defaults = {
        "app.json": {"promptDelete": False},
        "core-plugins.json": [],
    }
    for name, payload in defaults.items():
        path = obsidian_root / name
        if path.exists():
            continue
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_if_missing(path: Path, text: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_control_vault(
    repo_root: Path,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
) -> dict[str, Any]:
    output_root = output_root.resolve()
    manifest_path = manifest_path.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    ensure_obsidian_defaults(output_root)

    for note_path, title, protected in CURATED_NOTES:
        write_if_missing(output_root / note_path, render_curated_note(title, protected))

    generated_payloads = {
        "20 Generated/Repo Map Digest.md": repo_map_note(repo_root),
        "20 Generated/Active Plan Summary.md": active_plan_note(repo_root),
        "20 Generated/Recent Verification Summary.md": recent_verification_note(repo_root),
        "20 Generated/Release Summary.md": release_summary_note(repo_root),
    }
    generated_entries: list[dict[str, Any]] = []
    for note_path, title in GENERATED_NOTES:
        body, sources = generated_payloads[note_path]
        write_text(output_root / note_path, render_generated_note(title, body, sources))
        generated_entries.append(
            {
                "path": note_path,
                "title": title,
                "source_paths": sources,
            }
        )

    manifest = {
        "output_root": str(output_root),
        "generated_on": today_utc(),
        "curated_notes": [
            {"path": note_path, "title": title, "protected": protected}
            for note_path, title, protected in CURATED_NOTES
        ],
        "generated_notes": generated_entries,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest
