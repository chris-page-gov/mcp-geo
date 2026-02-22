from __future__ import annotations

from scripts import spec_tool_operability_coverage as coverage


def test_calc_operability_counts_and_requirements() -> None:
    harness = {
        "summary": {"total_questions": 2, "total_score": 180, "percentage": 90.0},
        "utilization": {
            "registeredTools": 3,
            "perTool": {"tool.alpha": {}, "resources/read": {}},
            "missingTools": ["tool.beta", "tool.gamma"],
        },
        "results": [
            {"question_id": "Q1", "score": 100},
            {"question_id": "Q2", "score": 70},
        ],
    }
    probe = {
        "results": [
            {"tool": "tool.beta", "outcome": "pass"},
            {"tool": "tool.gamma", "outcome": "blocked_auth"},
        ]
    }

    report = coverage._calc_operability(harness, probe)

    assert report["registeredTools"] == 3
    assert report["harnessCoveredTools"] == 1
    assert report["probeCoveredTools"] == 1
    assert report["blockedAuthTools"] == ["tool.gamma"]
    assert report["functionalTools"] == 2
    assert report["functionalCoveragePercent"] == 66.67
    assert report["liveLowScoreQuestionIds"] == ["Q2"]

    req_statuses = {item["id"]: item["status"] for item in report["requirements"]}
    assert req_statuses["REQ-LIVE-TOOLS-01"] == "pass"
    assert req_statuses["REQ-LIVE-TOOLS-02"] == "fail"
    assert req_statuses["REQ-LIVE-TOOLS-03"] == "pass"
