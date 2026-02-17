import json
from pathlib import Path

from scripts.map_trials.summarize_playwright_trials import latency_summary, load_result_stats, percentile


def test_load_result_stats_counts_nested_suites(tmp_path: Path):
    report = {
        "suites": [
            {
                "title": "root",
                "specs": [],
                "suites": [
                    {
                        "title": "child",
                        "specs": [
                            {
                                "title": "spec-a",
                                "tests": [
                                    {"results": [{"status": "passed"}]},
                                    {"results": [{"status": "skipped"}]},
                                ],
                            }
                        ],
                        "suites": [
                            {
                                "title": "grandchild",
                                "specs": [
                                    {
                                        "title": "spec-b",
                                        "tests": [{"results": [{"status": "failed"}]}],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }

    path = tmp_path / "playwright.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    counts = load_result_stats(path)
    assert counts["passed"] == 1
    assert counts["skipped"] == 1
    assert counts["failed"] == 1


def test_percentile_interpolates_between_points() -> None:
    values = [10.0, 20.0, 30.0, 40.0]
    assert percentile(values, 0.0) == 10.0
    assert percentile(values, 1.0) == 40.0
    assert percentile(values, 0.5) == 25.0


def test_latency_summary_reports_percentiles_and_budget_pass_rate() -> None:
    observations = [
        {"details": {"latencyMs": 10.0, "latencyBudgetMs": 20.0, "latencyPass": True}},
        {"details": {"latencyMs": 20.0, "latencyBudgetMs": 25.0, "latencyPass": True}},
        {"details": {"latencyMs": 30.0, "latencyBudgetMs": 25.0, "latencyPass": False}},
    ]
    summary = latency_summary(observations)
    assert summary["samples"] == 3.0
    assert summary["p50"] == 20.0
    assert summary["max"] == 30.0
    assert summary["budgetChecks"] == 3.0
    assert summary["budgetPasses"] == 2.0
    assert summary["budgetPassRate"] == 2.0 / 3.0
