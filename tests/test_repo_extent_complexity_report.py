from __future__ import annotations

from pathlib import Path

from scripts.repo_extent_complexity_report import (
    _normalize_git_rename_path,
    build_manager_report_card,
    build_report,
    python_cc_scores,
    render_manager_report_card,
    render_markdown,
)


def test_normalize_git_rename_path_handles_brace_format() -> None:
    raw = "tools/{old_name => new_name}.py"
    assert _normalize_git_rename_path(raw) == "tools/new_name.py"


def test_python_cc_scores_returns_expected_complexity_points() -> None:
    source = """
def alpha(x):
    if x > 0 and x < 10:
        return x
    return 0

def beta(items):
    total = 0
    for item in items:
        if item % 2 == 0:
            total += item
    return total
"""
    scores = python_cc_scores(source)
    assert len(scores) == 2
    assert max(scores) >= 3
    assert min(scores) >= 2


def test_build_report_workspace_scope_excludes_generated_output_paths(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "reports").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "cache").mkdir(parents=True, exist_ok=True)

    (tmp_path / "scripts" / "core.py").write_text(
        "def f(x):\n    if x:\n        return x\n    return 0\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "reports" / "generated.md").write_text("# generated\n", encoding="utf-8")
    (tmp_path / "data" / "cache" / "dump.json").write_text('{"ok": true}\n', encoding="utf-8")

    report = build_report(
        root=tmp_path,
        scope="workspace",
        lookback_days=30,
        top_hotspots=5,
        include_github=False,
        github_repo=None,
        exclude_globs=[],
    )

    scope = report["scopes"]["workspace"]
    assert scope["files_total"] == 3
    assert scope["files_functional"] == 1
    assert scope["non_blank_loc_functional"] > 0
    assert scope["excluded_generated_or_policy"] >= 2
    assert scope["language_breakdown"][0]["language"] == "Python"

    markdown = render_markdown(report)
    assert "MCP Geo Repository Extent and Complexity" in markdown
    assert "Scope: `workspace`" in markdown
    assert "Top Hotspots (`complexity x churn`)" in markdown
    assert "Hotspot concentration (top 5 share)" in markdown

    manager = render_manager_report_card(report)
    assert "Report Card" in manager
    assert "Terminology Glossary" in manager
    assert "Metric Basis and Sources" in manager
    assert "Functional implementation footprint" in manager


def test_manager_report_card_marks_in_flight_delta_not_applicable_for_single_scope() -> None:
    report = {
        "lookback_days": 30,
        "git_activity": {
            "commit_count": 0,
            "active_authors": 0,
            "additions": 0,
            "deletions": 0,
        },
        "scopes": {
            "git_tracked": {
                "non_blank_loc_functional": 1200,
                "files_functional": 6,
                "excluded_generated_or_policy": 1,
                "python_complexity": {
                    "functions_count": 20,
                    "mean_cc": 3.1,
                    "p90_cc": 6.0,
                    "max_cc": 11,
                    "high_risk_functions_cc_ge_15": 0,
                },
                "hotspot_total_score": 10.0,
                "top_5_hotspot_share": 0.2,
                "hotspots": [],
            }
        },
    }

    card = build_manager_report_card(report)
    in_flight_row = next(
        row
        for row in card["metric_rows"]
        if row.get("metric") == "In-flight scope delta"
    )
    assert in_flight_row["assessment"] == "N/A"
    assert str(in_flight_row["value"]).startswith("N/A")
    assert "In-flight delta" not in card["priority_risks"]
    assert any(
        "not assessed in single-scope mode" in line
        for line in card["practical_implications"]
    )
