#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class SpecTarget:
    name: str
    submodule_path: str
    tracked_paths: tuple[str, ...]
    notes: str = ""


@dataclass
class TargetAudit:
    name: str
    submodule_path: str
    local_head: str | None
    remote_head: str | None
    drift_status: str
    missing_paths: list[str]
    notes: str


SPEC_TARGETS: tuple[SpecTarget, ...] = (
    SpecTarget(
        name="mcp_core",
        submodule_path="docs/vendor/mcp/repos/modelcontextprotocol",
        tracked_paths=(
            "docs/specification/2024-11-05",
            "docs/specification/2025-03-26",
            "docs/specification/2025-06-18",
            "docs/specification/2025-11-25",
        ),
        notes="Core MCP specification revisions tracked in README/spec_tracking.",
    ),
    SpecTarget(
        name="mcp_apps",
        submodule_path="docs/vendor/mcp/repos/ext-apps",
        tracked_paths=(
            "specification/2026-01-26/apps.mdx",
            "specification/draft/apps.mdx",
        ),
        notes="Stable MCP-Apps spec plus retained draft path.",
    ),
    SpecTarget(
        name="mcp_auth",
        submodule_path="docs/vendor/mcp/repos/ext-auth",
        tracked_paths=("specification/draft",),
        notes="Draft auth extensions tracked for design review only.",
    ),
    SpecTarget(
        name="agent_skills",
        submodule_path="docs/vendor/agentskills",
        tracked_paths=("docs/specification.mdx",),
        notes="Vendored Agent Skills specification.",
    ),
    SpecTarget(
        name="mcp_inspector",
        submodule_path="docs/vendor/mcp/repos/inspector",
        tracked_paths=("README.md",),
        notes="Supporting inspector reference; canonical docs remain upstream.",
    ),
    SpecTarget(
        name="openai_apps_sdk_examples",
        submodule_path="docs/vendor/openai/repos/openai-apps-sdk-examples",
        tracked_paths=("README.md",),
        notes="Supporting example repo, not the canonical OpenAI docs source.",
    ),
)


def _run_git(path: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["/usr/bin/git", "-C", str(path), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def _remote_head(path: Path) -> str | None:
    result = _run_git(path, "ls-remote", "origin", "HEAD")
    if not result:
        return None
    return result.split()[0]


def _drift_status(local_head: str | None, remote_head: str | None) -> str:
    if not local_head:
        return "missing_local_git_state"
    if not remote_head:
        return "remote_unavailable"
    if local_head == remote_head:
        return "up_to_date"
    return "behind_or_diverged"


def audit_target(target: SpecTarget) -> TargetAudit:
    submodule_root = REPO_ROOT / target.submodule_path
    local_head = _run_git(submodule_root, "rev-parse", "HEAD")
    remote_head = _remote_head(submodule_root)
    missing_paths = [
        str(Path(target.submodule_path) / relative_path)
        for relative_path in target.tracked_paths
        if not (submodule_root / relative_path).exists()
    ]
    return TargetAudit(
        name=target.name,
        submodule_path=target.submodule_path,
        local_head=local_head,
        remote_head=remote_head,
        drift_status=_drift_status(local_head, remote_head),
        missing_paths=missing_paths,
        notes=target.notes,
    )


def build_summary(audits: list[TargetAudit]) -> dict[str, int]:
    summary = {
        "targets": len(audits),
        "up_to_date": 0,
        "behind_or_diverged": 0,
        "remote_unavailable": 0,
        "missing_local_git_state": 0,
        "missing_paths": 0,
    }
    for audit in audits:
        summary[audit.drift_status] = summary.get(audit.drift_status, 0) + 1
        if audit.missing_paths:
            summary["missing_paths"] += 1
    return summary


def render_text(audits: list[TargetAudit]) -> str:
    lines = ["Specification Drift Audit", ""]
    for audit in audits:
        lines.append(f"[{audit.name}] {audit.drift_status}")
        lines.append(f"submodule: {audit.submodule_path}")
        lines.append(f"local: {audit.local_head or 'unavailable'}")
        lines.append(f"remote: {audit.remote_head or 'unavailable'}")
        if audit.missing_paths:
            lines.append("missing_paths:")
            for path in audit.missing_paths:
                lines.append(f"  - {path}")
        else:
            lines.append("missing_paths: none")
        lines.append(f"notes: {audit.notes}")
        lines.append("")
    summary = build_summary(audits)
    lines.append("Summary")
    for key, value in summary.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit vendored specification submodules for origin-head drift and "
            "validate the local spec paths referenced by this repo."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Return exit code 1 when any target is behind or has missing tracked paths.",
    )
    args = parser.parse_args(argv)

    audits = [audit_target(target) for target in SPEC_TARGETS]
    if args.json:
        payload = {
            "repoRoot": str(REPO_ROOT),
            "targets": [asdict(audit) for audit in audits],
            "summary": build_summary(audits),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(audits))

    if not args.fail_on_drift:
        return 0
    for audit in audits:
        if audit.drift_status != "up_to_date" or audit.missing_paths:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
