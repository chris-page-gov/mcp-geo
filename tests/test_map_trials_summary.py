import json
from pathlib import Path

from scripts.map_trials.summarize_playwright_trials import load_result_stats


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
