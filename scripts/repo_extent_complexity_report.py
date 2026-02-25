#!/usr/bin/env python3
"""Generate repository extent and complexity statistics for mcp-geo."""

from __future__ import annotations

import argparse
import ast
import fnmatch
import json
import math
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

OUTPUT_TITLE_DEFAULT = "MCP Geo Repository Extent and Complexity"
MANAGER_REPORT_TITLE_DEFAULT = "MCP Geo Repository Report Card (Manager View)"

DEFAULT_EXCLUDE_GLOBS = (
    "docs/reports/**",
    "logs/**",
    "tmp/**",
    "build/**",
    "dist/**",
    "node_modules/**",
    ".venv/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".mypy_cache/**",
    "**/__pycache__/**",
    "mcp_geo.egg-info/**",
    "data/cache/**",
    "docs/vendor/**",
    "ui/vendor/**",
)

CODE_EXTENSIONS = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".ps1": "PowerShell",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sql": "SQL",
}

CONFIG_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
}

DOC_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
}

DATA_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".geojson",
    ".jsonl",
    ".parquet",
    ".db",
    ".sqlite",
}

BRANCH_KEYWORDS = {
    "JavaScript": (
        "if",
        "else if",
        "switch",
        "case",
        "for",
        "while",
        "catch",
        "&&",
        "||",
        "?",
    ),
    "TypeScript": (
        "if",
        "else if",
        "switch",
        "case",
        "for",
        "while",
        "catch",
        "&&",
        "||",
        "?",
    ),
    "Shell": ("if", "elif", "case", "for", "while"),
    "Go": ("if", "switch", "case", "for", "&&", "||"),
    "Rust": ("if", "match", "for", "while", "&&", "||"),
    "Java": ("if", "else if", "switch", "case", "for", "while", "catch", "&&", "||"),
    "Kotlin": ("if", "when", "for", "while", "catch", "&&", "||"),
}


@dataclass
class FileStats:
    path: str
    scope: str
    language: str
    category: str
    size_bytes: int
    lines: int
    non_blank_lines: int
    complexity_points: float
    churn_lines_lookback: int
    hotspot_score: float
    generated_by_linguist: bool
    excluded_by_policy: bool
    is_binary: bool
    python_function_count: int
    python_max_cc: int
    python_mean_cc: float


def _run(cmd: list[str], cwd: Path, input_text: str | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _is_git_repo(root: Path) -> bool:
    code, _, _ = _run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root)
    return code == 0


def _git_file_list(root: Path, include_untracked: bool) -> list[str]:
    if include_untracked:
        cmd = ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    else:
        cmd = ["git", "ls-files", "-z"]
    code, out, _ = _run(cmd, cwd=root)
    if code != 0:
        return []
    return [item for item in out.split("\x00") if item]


def _workspace_walk(root: Path) -> list[str]:
    ignored_dirs = {
        ".git",
        ".venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
    paths: list[str] = []
    for path in root.rglob("*"):
        if path.is_dir():
            if path.name in ignored_dirs:
                continue
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        paths.append(str(path.relative_to(root).as_posix()))
    return sorted(paths)


def _normalize_git_rename_path(raw_path: str) -> str:
    if " => " not in raw_path:
        return raw_path
    if "{" in raw_path and "}" in raw_path:
        prefix, tail = raw_path.split("{", 1)
        middle, suffix = tail.split("}", 1)
        _, new = middle.split(" => ", 1)
        return f"{prefix}{new}{suffix}"
    return raw_path.split(" => ", 1)[1]


def _git_churn(root: Path, lookback_days: int) -> dict[str, int]:
    since = (datetime.now(UTC) - timedelta(days=lookback_days)).date().isoformat()
    cmd = ["git", "log", f"--since={since}", "--numstat", "--format="]
    code, out, _ = _run(cmd, cwd=root)
    if code != 0:
        return {}
    churn: dict[str, int] = defaultdict(int)
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add_s, del_s, raw_path = parts
        add = int(add_s) if add_s.isdigit() else 0
        delete = int(del_s) if del_s.isdigit() else 0
        path = _normalize_git_rename_path(raw_path)
        churn[path] += add + delete
    return dict(churn)


def _git_activity(root: Path, lookback_days: int) -> dict[str, Any]:
    since = (datetime.now(UTC) - timedelta(days=lookback_days)).date().isoformat()
    commits_cmd = ["git", "rev-list", "--count", f"--since={since}", "HEAD"]
    authors_cmd = ["git", "log", f"--since={since}", "--format=%ae"]
    numstat_cmd = ["git", "log", f"--since={since}", "--numstat", "--format="]

    commit_code, commits_out, _ = _run(commits_cmd, cwd=root)
    author_code, authors_out, _ = _run(authors_cmd, cwd=root)
    stat_code, numstat_out, _ = _run(numstat_cmd, cwd=root)

    commits = int(commits_out.strip()) if commit_code == 0 and commits_out.strip().isdigit() else 0
    authors = (
        {line.strip().lower() for line in authors_out.splitlines() if line.strip()}
        if author_code == 0
        else set()
    )

    additions = 0
    deletions = 0
    if stat_code == 0:
        for line in numstat_out.splitlines():
            parts = line.split("\t")
            if len(parts) != 3:
                continue
            add_s, del_s, _ = parts
            additions += int(add_s) if add_s.isdigit() else 0
            deletions += int(del_s) if del_s.isdigit() else 0

    return {
        "lookback_days": lookback_days,
        "commit_count": commits,
        "active_authors": len(authors),
        "additions": additions,
        "deletions": deletions,
    }


def _parse_origin_github_slug(root: Path) -> str | None:
    code, out, _ = _run(["git", "remote", "get-url", "origin"], cwd=root)
    if code != 0:
        return None
    remote = out.strip()
    if remote.startswith("git@github.com:"):
        slug = remote.removeprefix("git@github.com:")
        return slug.removesuffix(".git")
    if "github.com/" in remote:
        slug = remote.split("github.com/", 1)[1]
        return slug.removesuffix(".git").split("?", 1)[0]
    return None


def _fetch_github_stats(root: Path, slug: str) -> dict[str, Any] | None:
    codefreq_cmd = ["gh", "api", f"repos/{slug}/stats/code_frequency"]
    contrib_cmd = ["gh", "api", f"repos/{slug}/stats/contributors"]

    code_code, code_out, _ = _run(codefreq_cmd, cwd=root)
    contrib_code, contrib_out, _ = _run(contrib_cmd, cwd=root)
    if code_code != 0 or contrib_code != 0:
        return None

    try:
        code_data = json.loads(code_out)
        contrib_data = json.loads(contrib_out)
    except json.JSONDecodeError:
        return None

    if not isinstance(code_data, list) or not isinstance(contrib_data, list):
        return None

    recent_weeks = code_data[-26:]
    additions = sum(
        int(week[1]) for week in recent_weeks if isinstance(week, list) and len(week) >= 2
    )
    deletions = sum(
        abs(int(week[2])) for week in recent_weeks if isinstance(week, list) and len(week) >= 3
    )

    active_recent = 0
    for contributor in contrib_data:
        weeks = contributor.get("weeks") if isinstance(contributor, dict) else None
        if not isinstance(weeks, list):
            continue
        last_13 = weeks[-13:]
        commits = sum(int(w.get("c", 0)) for w in last_13 if isinstance(w, dict))
        if commits > 0:
            active_recent += 1

    return {
        "repo": slug,
        "weeks_sampled": len(recent_weeks),
        "additions_26w": additions,
        "deletions_26w": deletions,
        "active_contributors_13w": active_recent,
        "source": "GitHub Stats API via gh",
    }


def _batch_linguist_attrs(root: Path, files: list[str]) -> dict[str, dict[str, str]]:
    if not files:
        return {}
    input_text = "\n".join(files) + "\n"
    cmd = [
        "git",
        "check-attr",
        "--stdin",
        "linguist-generated",
        "linguist-vendored",
        "linguist-documentation",
    ]
    code, out, _ = _run(cmd, cwd=root, input_text=input_text)
    if code != 0:
        return {}

    attrs: dict[str, dict[str, str]] = defaultdict(dict)
    for line in out.splitlines():
        parts = line.split(": ", 2)
        if len(parts) != 3:
            continue
        path, key, value = parts
        attrs[path][key] = value
    return dict(attrs)


def _attr_true(value: str | None) -> bool:
    if value is None:
        return False
    return value.lower() in {"set", "true", "yes", "on"}


def _is_binary_file(path: Path) -> bool:
    try:
        head = path.read_bytes()[:4096]
    except OSError:
        return True
    return b"\x00" in head


def _category_and_language(path: str) -> tuple[str, str]:
    suffix = Path(path).suffix.lower()
    if suffix in CODE_EXTENSIONS:
        return "code", CODE_EXTENSIONS[suffix]
    if suffix in CONFIG_EXTENSIONS:
        return "config", suffix.lstrip(".").upper() or "Config"
    if suffix in DOC_EXTENSIONS:
        return "documentation", suffix.lstrip(".").upper() or "Doc"
    if suffix in DATA_EXTENSIONS:
        return "data", suffix.lstrip(".").upper() or "Data"
    return "other", suffix.lstrip(".").upper() or "Unknown"


def _matches_glob(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


class _CyclomaticVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.stack: list[int] = []
        self.scores: list[int] = []

    def _bump(self, value: int = 1) -> None:
        if self.stack:
            self.stack[-1] += value

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.stack.append(1)
        self.generic_visit(node)
        self.scores.append(self.stack.pop())

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.stack.append(1)
        self.generic_visit(node)
        self.scores.append(self.stack.pop())

    def visit_If(self, node: ast.If) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        self._bump(max(len(node.values) - 1, 1))
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        self._bump()
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> Any:
        self._bump(max(len(node.ifs), 1))
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> Any:
        self._bump(max(len(node.cases), 1))
        self.generic_visit(node)


def python_cc_scores(source: str) -> list[int]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = _CyclomaticVisitor()
    visitor.visit(tree)
    return visitor.scores


def keyword_complexity(language: str, source: str) -> float:
    keywords = BRANCH_KEYWORDS.get(language)
    if not keywords:
        return 1.0
    lowered = source.lower()
    count = 0
    for token in keywords:
        count += lowered.count(token)
    return max(1.0, 1.0 + (count / 4.0))


def _human_int(value: int) -> str:
    return f"{value:,}"


def _human_float(value: float, precision: int = 1) -> str:
    return f"{value:.{precision}f}"


def _human_m(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return str(value)


def _human_percent(value: float, precision: int = 1) -> str:
    return f"{value * 100:.{precision}f}%"


def _risk_from_thresholds(value: float, *, low: float, moderate: float, high: float) -> str:
    if value <= low:
        return "Low"
    if value <= moderate:
        return "Moderate"
    if value <= high:
        return "High"
    return "Very High"


def _risk_rank(label: str) -> int:
    return {"Low": 1, "Moderate": 2, "High": 3, "Very High": 4}.get(label, 0)


def _pick_primary_scope(scopes: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    for preferred in ("workspace", "git_tracked"):
        if preferred in scopes:
            return preferred, scopes[preferred]
    if scopes:
        key = next(iter(scopes))
        return key, scopes[key]
    return "none", {}


def _markdown_table_row(columns: list[str]) -> str:
    escaped = [column.replace("|", r"\|") for column in columns]
    return "| " + " | ".join(escaped) + " |"


def build_manager_report_card(report: dict[str, Any]) -> dict[str, Any]:
    scopes = report.get("scopes") or {}
    scope_name, scope_data = _pick_primary_scope(scopes)
    has_workspace_scope = "workspace" in scopes
    has_tracked_scope = "git_tracked" in scopes
    has_dual_scope = has_workspace_scope and has_tracked_scope
    git_activity = report.get("git_activity") or {}
    python = scope_data.get("python_complexity") or {}

    functional_loc = int(scope_data.get("non_blank_loc_functional", 0) or 0)
    files_functional = int(scope_data.get("files_functional", 0) or 0)
    excluded_count = int(scope_data.get("excluded_generated_or_policy", 0) or 0)

    commits = int(git_activity.get("commit_count", 0) or 0)
    active_authors = int(git_activity.get("active_authors", 0) or 0)
    additions = int(git_activity.get("additions", 0) or 0)
    deletions = int(git_activity.get("deletions", 0) or 0)
    changed_lines = additions + deletions
    change_intensity = changed_lines / max(functional_loc, 1)

    mean_cc = float(python.get("mean_cc", 0.0) or 0.0)
    p90_cc = float(python.get("p90_cc", 0.0) or 0.0)
    max_cc = int(python.get("max_cc", 0) or 0)
    functions_count = int(python.get("functions_count", 0) or 0)
    high_cc_count = int(python.get("high_risk_functions_cc_ge_15", 0) or 0)
    high_cc_ratio = high_cc_count / max(functions_count, 1)

    hotspots = scope_data.get("hotspots") or []
    hotspot_total_score = float(scope_data.get("hotspot_total_score", 0.0) or 0.0)
    top5_share = float(scope_data.get("top_5_hotspot_share", 0.0) or 0.0)

    workspace_loc = int(((scopes.get("workspace") or {}).get("non_blank_loc_functional", 0)) or 0)
    tracked_loc = int(((scopes.get("git_tracked") or {}).get("non_blank_loc_functional", 0)) or 0)
    in_flight_delta = workspace_loc - tracked_loc if has_dual_scope else None
    in_flight_ratio: float | None = None
    in_flight_risk_basis = "N/A"
    if has_dual_scope and in_flight_delta is not None:
        if tracked_loc > 0:
            in_flight_ratio = abs(in_flight_delta) / tracked_loc
            in_flight_risk_basis = (
                "Relative delta `abs(workspace - git_tracked) / git_tracked`."
            )
        else:
            in_flight_risk_basis = (
                "Absolute delta fallback because tracked functional LOC is zero."
            )

    footprint_risk = _risk_from_thresholds(functional_loc, low=15_000, moderate=45_000, high=90_000)
    change_risk = _risk_from_thresholds(change_intensity, low=0.5, moderate=1.5, high=3.0)
    structural_risk = _risk_from_thresholds(p90_cc, low=5.0, moderate=10.0, high=15.0)
    concentration_risk = _risk_from_thresholds(top5_share, low=0.20, moderate=0.35, high=0.50)
    high_cc_risk = _risk_from_thresholds(high_cc_ratio, low=0.03, moderate=0.07, high=0.12)
    if not has_dual_scope:
        in_flight_risk = "N/A"
    elif in_flight_ratio is not None:
        in_flight_risk = _risk_from_thresholds(in_flight_ratio, low=0.02, moderate=0.08, high=0.15)
    else:
        in_flight_risk = _risk_from_thresholds(
            abs(in_flight_delta or 0),
            low=200,
            moderate=1_000,
            high=5_000,
        )
    in_flight_value = (
        f"{_human_int(in_flight_delta or 0)} LOC difference "
        f"(workspace {_human_m(workspace_loc)} vs tracked {_human_m(tracked_loc)}"
        + (
            f", delta {_human_percent(in_flight_ratio, 1)} of tracked)"
            if in_flight_ratio is not None
            else ", tracked baseline is zero)"
        )
        if has_dual_scope
        else "N/A (requires both `workspace` and `git_tracked` scopes)"
    )
    in_flight_assessment = in_flight_risk if has_dual_scope else "N/A"

    risk_signals = [
        {"name": "Footprint scale", "risk": footprint_risk},
        {"name": "Change load", "risk": change_risk},
        {"name": "Structural complexity", "risk": structural_risk},
        {"name": "Hotspot concentration", "risk": concentration_risk},
        {"name": "High-complexity function share", "risk": high_cc_risk},
    ]
    if has_dual_scope:
        risk_signals.append({"name": "In-flight delta", "risk": in_flight_risk})
    overall_risk = (
        max(risk_signals, key=lambda item: _risk_rank(item["risk"]))["risk"]
        if risk_signals
        else "Low"
    )
    priority_risks = [
        item["name"]
        for item in sorted(risk_signals, key=lambda item: _risk_rank(item["risk"]), reverse=True)
        if _risk_rank(item["risk"]) >= _risk_rank("High")
    ]

    metric_rows = [
        {
            "metric": "Functional implementation footprint",
            "value": f"{_human_m(functional_loc)} LOC across {_human_int(files_functional)} files",
            "assessment": footprint_risk,
            "terminology": (
                "Functional LOC counts non-blank lines in code files, "
                "excluding generated/output files."
            ),
            "basis": (
                "Local file inventory (`git ls-files` / workspace walk) + "
                "policy/Linguist exclusions."
            ),
            "practical_meaning": (
                "Higher size increases onboarding, review, and "
                "regression-testing effort."
            ),
        },
        {
            "metric": "Recent change load",
            "value": (
                f"{_human_int(changed_lines)} lines changed in {_human_int(commits)} commits "
                f"({_human_int(active_authors)} active authors, intensity {change_intensity:.2f}x)"
            ),
            "assessment": change_risk,
            "terminology": (
                "Change intensity is recent changed lines divided by current "
                "functional LOC."
            ),
            "basis": f"`git log --numstat --since={report.get('lookback_days', 0)}d`.",
            "practical_meaning": (
                "Higher change load means more coordination pressure and "
                "release-risk exposure."
            ),
        },
        {
            "metric": "Structural complexity (Python)",
            "value": (
                f"P90 CC {p90_cc:.1f}, mean {mean_cc:.1f}, max {max_cc} "
                f"across {_human_int(functions_count)} functions"
            ),
            "assessment": structural_risk,
            "terminology": (
                "Cyclomatic complexity approximates the number of decision "
                "paths in a function."
            ),
            "basis": (
                "AST parsing of Python functions, aligned to Radon-style "
                "CC interpretation bands."
            ),
            "practical_meaning": (
                "Higher complexity raises defect probability and test-case volume."
            ),
        },
        {
            "metric": "High-complexity function share",
            "value": (
                f"{_human_int(high_cc_count)} of {_human_int(functions_count)} functions "
                f"(CC >= 15, {_human_percent(high_cc_ratio)})"
            ),
            "assessment": high_cc_risk,
            "terminology": (
                "CC >= 15 is treated as elevated complexity requiring "
                "tighter tests/review."
            ),
            "basis": (
                "Count of Python functions where cyclomatic complexity "
                "threshold is exceeded."
            ),
            "practical_meaning": (
                "A higher share indicates concentrated maintainability and "
                "reliability risk."
            ),
        },
        {
            "metric": "Hotspot concentration",
            "value": (
                f"Top-5 hotspots hold {_human_percent(top5_share)} of hotspot score "
                f"(total score {_human_float(hotspot_total_score, 1)})"
            ),
            "assessment": concentration_risk,
            "terminology": "Hotspot score = complexity points x log2(1 + churn lines).",
            "basis": (
                "Complexity model + churn from local git history over the "
                "lookback window."
            ),
            "practical_meaning": (
                "Higher concentration means a few files dominate change "
                "failure risk."
            ),
        },
        {
            "metric": "In-flight scope delta",
            "value": in_flight_value,
            "assessment": in_flight_assessment,
            "terminology": "Compares current workspace complexity with committed complexity.",
            "basis": (
                in_flight_risk_basis
                if has_dual_scope
                else "Only one scope was collected in this run."
            ),
            "practical_meaning": (
                "Larger deltas indicate release plans may differ from current working state."
                if has_dual_scope
                else "Run in `--scope both` mode to assess release drift risk."
            ),
        },
        {
            "metric": "Generated/output exclusion control",
            "value": f"{_human_int(excluded_count)} files excluded in primary scope `{scope_name}`",
            "assessment": "Control",
            "terminology": (
                "Generated outputs are files produced by scripts/builds, "
                "not hand-maintained logic."
            ),
            "basis": "GitHub Linguist attrs + deterministic exclusion policy globs.",
            "practical_meaning": (
                "Prevents report inflation so management decisions reflect "
                "real implementation load."
            ),
        },
    ]

    practical_implications = [
        (
            "Prioritize refactoring/integration tests in top hotspots first; "
            "that is where reliability effort yields the highest return."
            if _risk_rank(concentration_risk) >= _risk_rank("High")
            else "Hotspot concentration is manageable; continue routine hotspot monitoring."
        ),
        (
            "Budget additional review and test time for complex Python modules "
            "before major releases."
            if _risk_rank(structural_risk) >= _risk_rank("High")
            else "Structural complexity is within routine operating range for current scope."
        ),
        (
            "Plan for tighter release coordination because recent change volume "
            "is high relative to system size."
            if _risk_rank(change_risk) >= _risk_rank("High")
            else "Recent change load is proportionate to repo size."
        ),
        (
            (
                "Expect potential release drift between local work and committed branch; "
                "consider a sync checkpoint."
                if _risk_rank(in_flight_risk) >= _risk_rank("High")
                else (
                    "Workspace-to-branch delta is limited; release-state "
                    "reporting is representative."
                )
            )
            if has_dual_scope
            else (
                "In-flight delta is not assessed in single-scope mode; use "
                "`--scope both` for this signal."
            )
        ),
    ]

    return {
        "primary_scope": scope_name,
        "overall_risk": overall_risk,
        "priority_risks": priority_risks,
        "metric_rows": metric_rows,
        "top_hotspots": hotspots[:5],
        "practical_implications": practical_implications,
        "glossary": [
            {
                "term": "Functional LOC",
                "plain_english": (
                    "Non-blank lines in implementation code, after excluding "
                    "generated/output files."
                ),
            },
            {
                "term": "Cyclomatic Complexity (CC)",
                "plain_english": "A proxy for how many decision paths code contains.",
            },
            {
                "term": "P90 complexity",
                "plain_english": (
                    "The value that 90% of functions are at or below; "
                    "highlights the heavier tail."
                ),
            },
            {
                "term": "Churn",
                "plain_english": "How many lines changed recently (adds + deletes) in git history.",
            },
            {
                "term": "Hotspot",
                "plain_english": (
                    "Code that is both complex and changed frequently, so it "
                    "carries higher risk."
                ),
            },
            {
                "term": "Dual scope",
                "plain_english": (
                    "Comparing committed files (`git_tracked`) versus current "
                    "local files (`workspace`)."
                ),
            },
        ],
        "sources": [
            {
                "name": "Local git inventory and churn",
                "details": (
                    "Uses `git ls-files` and `git log --numstat` in the "
                    "configured lookback window."
                ),
            },
            {
                "name": "Generated-output filtering",
                "details": (
                    "Uses GitHub Linguist attrs (`linguist-generated`, "
                    "`linguist-vendored`) plus policy globs."
                ),
                "url": "https://github.com/github-linguist/linguist",
            },
            {
                "name": "Cyclomatic complexity interpretation",
                "details": (
                    "Python AST-derived CC values interpreted using common "
                    "Radon guidance bands."
                ),
                "url": "https://radon.readthedocs.io/en/master/intro.html#cyclomatic-complexity",
            },
            {
                "name": "Hotspot practice",
                "details": (
                    "Hotspot framing follows complexity x churn approaches "
                    "used in code-health tooling."
                ),
                "url": "https://docs.enterprise.codescene.io/versions/6.7.8/guides/technical/hotspots.html",
            },
            {
                "name": "Optional GitHub repository statistics",
                "details": "When enabled, aggregates GitHub Stats API via `gh` CLI.",
                "url": "https://docs.github.com/rest/metrics/statistics",
            },
        ],
    }


def render_manager_report_card(
    report: dict[str, Any],
    title: str = MANAGER_REPORT_TITLE_DEFAULT,
) -> str:
    card = report.get("manager_report_card") or build_manager_report_card(report)
    lines: list[str] = [
        f"# {title}",
        "",
        f"Generated: `{report.get('generated_at', '')}`",
        f"Reporting scope used for the card: `{card.get('primary_scope', 'unknown')}`",
        f"Lookback window: `{report.get('lookback_days', 0)}` days",
        "",
        "## Executive Snapshot",
        "",
        (
            "This report card is designed for non-technical management. "
            "It summarizes maintenance risk, delivery pressure, and concentration risk "
            "using repository evidence and standard software-health metrics."
        ),
        "",
        f"- Overall risk signal: `{card.get('overall_risk', 'Unknown')}`",
    ]

    priority_risks = card.get("priority_risks") or []
    if priority_risks:
        lines.append(
            "- Priority risks to watch: " + ", ".join(f"`{risk}`" for risk in priority_risks)
        )
    else:
        lines.append(
            "- Priority risks to watch: none currently above high-risk threshold."
        )

    lines.extend(
        [
            "",
            "## Report Card",
            "",
            _markdown_table_row(
                [
                    "Indicator",
                    "Current value",
                    "Assessment",
                    "Terminology (plain English)",
                    "Practical meaning",
                    "Basis / source",
                ]
            ),
            _markdown_table_row(["---", "---", "---", "---", "---", "---"]),
        ]
    )

    for row in card.get("metric_rows") or []:
        lines.append(
            _markdown_table_row(
                [
                    str(row.get("metric", "")),
                    str(row.get("value", "")),
                    str(row.get("assessment", "")),
                    str(row.get("terminology", "")),
                    str(row.get("practical_meaning", "")),
                    str(row.get("basis", "")),
                ]
            )
        )

    lines.extend(["", "## Practical Interpretation", ""])
    for statement in card.get("practical_implications") or []:
        lines.append(f"- {statement}")

    lines.extend(["", "## Top Hotspots (Management Attention)", ""])
    hotspots = card.get("top_hotspots") or []
    if not hotspots:
        lines.append("- No hotspots identified in the selected scope.")
    else:
        for item in hotspots:
            score = _human_float(float(item.get("hotspot_score", 0.0)), 2)
            complexity = _human_float(float(item.get("complexity_points", 0.0)), 2)
            churn = _human_int(int(item.get("churn_lines_lookback", 0) or 0))
            lines.append(
                "- "
                f"`{item.get('path', '')}`: score `{score}` "
                f"(complexity `{complexity}`, churn `{churn}`)."
            )

    lines.extend(["", "## Terminology Glossary", ""])
    for entry in card.get("glossary") or []:
        lines.append(f"- `{entry.get('term', '')}`: {entry.get('plain_english', '')}")

    lines.extend(["", "## Metric Basis and Sources", ""])
    for source in card.get("sources") or []:
        url = source.get("url")
        if url:
            lines.append(f"- {source.get('name', '')}: {source.get('details', '')} ({url})")
        else:
            lines.append(f"- {source.get('name', '')}: {source.get('details', '')}")

    lines.extend(
        [
            "",
            "## Notes and Limits",
            "",
            "- This is a risk-oriented management snapshot, not a release gate by itself.",
            "- Non-Python complexity uses branch-keyword proxies; Python uses AST-level CC.",
            (
                "- Generated/output files are intentionally excluded to avoid "
                "inflating implementation scope."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def build_report(
    root: Path,
    scope: str,
    lookback_days: int,
    top_hotspots: int,
    include_github: bool,
    github_repo: str | None,
    exclude_globs: list[str],
) -> dict[str, Any]:
    is_git = _is_git_repo(root)

    files_by_scope: dict[str, list[str]] = {}
    if scope in {"tracked", "both"}:
        files_by_scope["git_tracked"] = (
            _git_file_list(root, include_untracked=False) if is_git else []
        )
    if scope in {"workspace", "both"}:
        if is_git:
            files_by_scope["workspace"] = _git_file_list(root, include_untracked=True)
        else:
            files_by_scope["workspace"] = _workspace_walk(root)

    merged_files: dict[str, set[str]] = {}
    for scope_name, values in files_by_scope.items():
        merged_files[scope_name] = set(values)

    all_files: set[str] = set()
    for values in merged_files.values():
        all_files.update(values)

    linguist = _batch_linguist_attrs(root, sorted(all_files)) if is_git else {}
    churn = _git_churn(root, lookback_days) if is_git else {}
    git_activity = _git_activity(root, lookback_days) if is_git else {}

    combined_excludes = list(DEFAULT_EXCLUDE_GLOBS) + exclude_globs
    file_stats: list[FileStats] = []

    for scope_name, paths in merged_files.items():
        for rel_path in sorted(paths):
            abs_path = root / rel_path
            if not abs_path.exists() or not abs_path.is_file():
                continue

            size_bytes = abs_path.stat().st_size
            attr_values = linguist.get(rel_path, {})
            generated_by_linguist = _attr_true(attr_values.get("linguist-generated")) or _attr_true(
                attr_values.get("linguist-vendored")
            )
            marked_documentation = _attr_true(attr_values.get("linguist-documentation"))
            excluded_by_policy = _matches_glob(rel_path, combined_excludes)
            is_binary = _is_binary_file(abs_path)
            category, language = _category_and_language(rel_path)

            lines = 0
            non_blank = 0
            complexity_points = 0.0
            function_count = 0
            python_max_cc = 0
            python_mean_cc = 0.0

            if not is_binary:
                text = abs_path.read_text(encoding="utf-8", errors="ignore")
                split = text.splitlines()
                lines = len(split)
                non_blank = sum(1 for line in split if line.strip())

                if category == "code":
                    if language == "Python":
                        scores = python_cc_scores(text)
                        function_count = len(scores)
                        python_max_cc = max(scores, default=0)
                        python_mean_cc = statistics.mean(scores) if scores else 0.0
                        complexity_points = float(sum(scores) if scores else 1.0)
                    else:
                        complexity_points = keyword_complexity(language, text)

            file_stats.append(
                FileStats(
                    path=rel_path,
                    scope=scope_name,
                    language=language,
                    category=category if not marked_documentation else "documentation",
                    size_bytes=size_bytes,
                    lines=lines,
                    non_blank_lines=non_blank,
                    complexity_points=complexity_points,
                    churn_lines_lookback=churn.get(rel_path, 0),
                    hotspot_score=0.0,
                    generated_by_linguist=generated_by_linguist,
                    excluded_by_policy=excluded_by_policy,
                    is_binary=is_binary,
                    python_function_count=function_count,
                    python_max_cc=python_max_cc,
                    python_mean_cc=python_mean_cc,
                )
            )

    seen_scope_path: set[tuple[str, str]] = set()
    deduped: list[FileStats] = []
    for item in file_stats:
        key = (item.scope, item.path)
        if key in seen_scope_path:
            continue
        seen_scope_path.add(key)
        deduped.append(item)
    file_stats = deduped

    for item in file_stats:
        if item.complexity_points <= 0.0:
            item.hotspot_score = 0.0
            continue
        item.hotspot_score = item.complexity_points * math.log2(1 + item.churn_lines_lookback)

    per_scope: dict[str, dict[str, Any]] = {}
    for scope_name in merged_files:
        scope_items = [item for item in file_stats if item.scope == scope_name]
        scope_text = [item for item in scope_items if not item.is_binary]
        scope_functional = [
            item
            for item in scope_text
            if item.category == "code"
            and not item.generated_by_linguist
            and not item.excluded_by_policy
        ]
        language_loc: Counter[str] = Counter()
        language_files: Counter[str] = Counter()
        directory_loc: Counter[str] = Counter()

        for item in scope_functional:
            language_loc[item.language] += item.non_blank_lines
            language_files[item.language] += 1
            top_dir = item.path.split("/", 1)[0] if "/" in item.path else "."
            directory_loc[top_dir] += item.non_blank_lines

        python_items = [item for item in scope_functional if item.language == "Python"]
        python_cc_values: list[int] = []
        for item in python_items:
            if item.python_function_count == 0:
                continue
            text = (root / item.path).read_text(encoding="utf-8", errors="ignore")
            python_cc_values.extend(python_cc_scores(text))

        sorted_by_hotspot = sorted(
            scope_functional,
            key=lambda entry: entry.hotspot_score,
            reverse=True,
        )
        hotspots = sorted_by_hotspot[:top_hotspots]
        hotspot_total_score = sum(item.hotspot_score for item in scope_functional)
        top_5_hotspot_share = (
            sum(item.hotspot_score for item in sorted_by_hotspot[:5]) / hotspot_total_score
            if hotspot_total_score > 0.0
            else 0.0
        )

        per_scope[scope_name] = {
            "files_total": len(scope_items),
            "files_text": len(scope_text),
            "files_binary": len(scope_items) - len(scope_text),
            "files_functional": len(scope_functional),
            "non_blank_loc_functional": sum(item.non_blank_lines for item in scope_functional),
            "excluded_generated_or_policy": sum(
                1 for item in scope_items if item.generated_by_linguist or item.excluded_by_policy
            ),
            "language_breakdown": [
                {
                    "language": language,
                    "files": language_files[language],
                    "non_blank_loc": language_loc[language],
                }
                for language in language_loc
            ],
            "directory_breakdown": [
                {
                    "directory": directory,
                    "non_blank_loc": loc,
                }
                for directory, loc in directory_loc.most_common(10)
            ],
            "python_complexity": {
                "functions_count": len(python_cc_values),
                "mean_cc": round(statistics.mean(python_cc_values), 3) if python_cc_values else 0.0,
                "p90_cc": round(statistics.quantiles(python_cc_values, n=10)[8], 3)
                if len(python_cc_values) >= 10
                else max(python_cc_values, default=0),
                "max_cc": max(python_cc_values, default=0),
                "high_risk_functions_cc_ge_15": sum(1 for value in python_cc_values if value >= 15),
            },
            "hotspot_total_score": round(hotspot_total_score, 3),
            "top_5_hotspot_share": round(top_5_hotspot_share, 4),
            "hotspots": [
                {
                    "path": item.path,
                    "language": item.language,
                    "complexity_points": round(item.complexity_points, 3),
                    "churn_lines_lookback": item.churn_lines_lookback,
                    "hotspot_score": round(item.hotspot_score, 3),
                }
                for item in hotspots
            ],
        }

    github_stats = None
    if include_github:
        slug = github_repo or _parse_origin_github_slug(root)
        if slug:
            github_stats = _fetch_github_stats(root, slug)

    report = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "root": str(root),
        "scope": scope,
        "lookback_days": lookback_days,
        "top_hotspots": top_hotspots,
        "exclude_globs": combined_excludes,
        "git_available": is_git,
        "git_activity": git_activity,
        "github_stats": github_stats,
        "scopes": per_scope,
    }
    report["manager_report_card"] = build_manager_report_card(report)
    return report


def render_markdown(report: dict[str, Any], title: str = OUTPUT_TITLE_DEFAULT) -> str:
    lines: list[str] = [
        f"# {title}",
        "",
        f"Generated: `{report['generated_at']}`",
        f"Repo root: `{report['root']}`",
        f"Scope mode: `{report['scope']}`",
        f"Lookback window: `{report['lookback_days']}` days",
        "",
        "## Method Summary",
        "",
        "- Uses two inventory scopes:",
        "  - `git_tracked`: files in `git ls-files`.",
        "  - `workspace`: tracked + untracked non-ignored files.",
        "- Excludes generated/output surfaces from functional complexity via:",
        "  - GitHub Linguist attributes (`linguist-generated`, `linguist-vendored`).",
        "  - Deterministic policy globs (for example `docs/reports/**`, `logs/**`).",
        "- Complexity model:",
        "  - Python: AST-based cyclomatic complexity per function.",
        "  - Non-Python code: branch-keyword complexity proxy.",
        "- Hotspot score: `complexity_points * log2(1 + churn_lines)`.",
        "",
    ]

    git_activity = report.get("git_activity") or {}
    if git_activity:
        lines.extend(
            [
                "## Change Dynamics",
                "",
                f"- Commits in lookback: `{_human_int(git_activity.get('commit_count', 0))}`",
                f"- Active authors: `{_human_int(git_activity.get('active_authors', 0))}`",
                f"- Additions: `{_human_int(git_activity.get('additions', 0))}`",
                f"- Deletions: `{_human_int(git_activity.get('deletions', 0))}`",
                "",
            ]
        )

    github_stats = report.get("github_stats")
    if isinstance(github_stats, dict):
        lines.extend(
            [
                "## GitHub Stats (Optional)",
                "",
                f"- Repo: `{github_stats.get('repo', '')}`",
                f"- Weekly sample window: `{github_stats.get('weeks_sampled', 0)}` weeks",
                f"- Additions (26w): `{_human_int(github_stats.get('additions_26w', 0))}`",
                f"- Deletions (26w): `{_human_int(github_stats.get('deletions_26w', 0))}`",
                f"- Active contributors (13w): "
                f"`{_human_int(github_stats.get('active_contributors_13w', 0))}`",
                "",
            ]
        )

    for scope_name, scope_data in (report.get("scopes") or {}).items():
        lines.extend(
            [
                f"## Scope: `{scope_name}`",
                "",
                f"- Files (total/text/binary): "
                f"`{_human_int(scope_data['files_total'])}` / "
                f"`{_human_int(scope_data['files_text'])}` / "
                f"`{_human_int(scope_data['files_binary'])}`",
                f"- Functional files: `{_human_int(scope_data['files_functional'])}`",
                f"- Functional non-blank LOC: `{_human_m(scope_data['non_blank_loc_functional'])}`",
                f"- Excluded as generated/output policy: "
                f"`{_human_int(scope_data['excluded_generated_or_policy'])}`",
                f"- Hotspot concentration (top 5 share): "
                f"`{_human_percent(scope_data.get('top_5_hotspot_share', 0.0))}`",
                "",
                "### Language Footprint",
                "",
            ]
        )

        language_rows = sorted(
            scope_data["language_breakdown"],
            key=lambda row: row["non_blank_loc"],
            reverse=True,
        )
        if not language_rows:
            lines.append("- No functional code files found in this scope.")
        else:
            for row in language_rows[:12]:
                lines.append(
                    f"- `{row['language']}`: `{_human_m(row['non_blank_loc'])}` LOC in "
                    f"`{_human_int(row['files'])}` files"
                )

        lines.extend(
            [
                "",
                "### Top Directories by Functional LOC",
                "",
            ]
        )

        directory_rows = scope_data["directory_breakdown"]
        if not directory_rows:
            lines.append("- No directory data available.")
        else:
            for row in directory_rows:
                lines.append(f"- `{row['directory']}`: `{_human_m(row['non_blank_loc'])}` LOC")

        py = scope_data["python_complexity"]
        lines.extend(
            [
                "",
                "### Python Complexity",
                "",
                f"- Functions analyzed: `{_human_int(py['functions_count'])}`",
                f"- Mean cyclomatic complexity: `{_human_float(py['mean_cc'], 2)}`",
                f"- P90 cyclomatic complexity: `{_human_float(py['p90_cc'], 2)}`",
                f"- Max cyclomatic complexity: `{_human_int(py['max_cc'])}`",
                f"- Functions with CC >= 15: `{_human_int(py['high_risk_functions_cc_ge_15'])}`",
                "",
                "### Top Hotspots (`complexity x churn`)",
                "",
            ]
        )

        hotspots = scope_data["hotspots"]
        if not hotspots:
            lines.append("- No hotspots detected (likely no code in scope).")
        else:
            for item in hotspots:
                lines.append(
                    f"- `{item['path']}` | `{item['language']}` | "
                    f"`score={_human_float(item['hotspot_score'], 2)}` | "
                    f"`complexity={_human_float(item['complexity_points'], 2)}` | "
                    f"`churn={_human_int(item['churn_lines_lookback'])}`"
                )

        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- This report prioritizes functional complexity and excludes known output/generated",
            "  areas by default to avoid inflating system size with build/report artifacts.",
            "- Customize inclusion/exclusion with `--exclude-glob` and scope flags.",
            "- Use JSON output for dashboarding or longitudinal snapshots.",
            "",
        ]
    )

    return "\n".join(lines)


def _default_output_path(root: Path) -> Path:
    date_part = datetime.now(UTC).date().isoformat()
    filename = f"repo_extent_complexity_{date_part}.md"
    return root / "docs" / "reports" / filename


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate repo extent and complexity stats with hotspot analysis."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current working directory).",
    )
    parser.add_argument(
        "--scope",
        choices=("tracked", "workspace", "both"),
        default="both",
        help="Which file inventory scopes to analyze.",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=180,
        help="Git churn/activity lookback window in days.",
    )
    parser.add_argument(
        "--top-hotspots",
        type=int,
        default=15,
        help="Number of hotspots to include per scope.",
    )
    parser.add_argument(
        "--include-github",
        action="store_true",
        help="Attempt GitHub Stats API lookup via gh CLI.",
    )
    parser.add_argument(
        "--github-repo",
        default=None,
        help="Optional owner/repo override for GitHub stats.",
    )
    parser.add_argument(
        "--exclude-glob",
        action="append",
        default=[],
        help="Additional glob patterns to exclude from functional metrics.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Markdown output path (default: docs/reports/repo_extent_complexity_<date>.md).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )
    parser.add_argument(
        "--title",
        default=OUTPUT_TITLE_DEFAULT,
        help=f"Markdown title (default: {OUTPUT_TITLE_DEFAULT!r}).",
    )
    parser.add_argument(
        "--manager-output",
        type=Path,
        default=None,
        help="Optional manager-facing report-card markdown output path.",
    )
    parser.add_argument(
        "--manager-title",
        default=MANAGER_REPORT_TITLE_DEFAULT,
        help=f"Manager report-card title (default: {MANAGER_REPORT_TITLE_DEFAULT!r}).",
    )
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    report = build_report(
        root=root,
        scope=args.scope,
        lookback_days=args.lookback_days,
        top_hotspots=args.top_hotspots,
        include_github=args.include_github,
        github_repo=args.github_repo,
        exclude_globs=args.exclude_glob,
    )

    output_path = args.output.expanduser() if args.output else _default_output_path(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown(report, title=args.title), encoding="utf-8")
    print(f"Wrote markdown report: {output_path}")

    if args.manager_output:
        manager_path = args.manager_output.expanduser()
        manager_path.parent.mkdir(parents=True, exist_ok=True)
        manager_path.write_text(
            render_manager_report_card(report, title=args.manager_title),
            encoding="utf-8",
        )
        print(f"Wrote manager report card: {manager_path}")

    if args.json_output:
        json_path = args.json_output.expanduser()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote JSON report: {json_path}")


if __name__ == "__main__":
    main()
