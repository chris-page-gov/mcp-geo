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
    assert report["optionalEntitlementTools"] == []
    assert report["functionalTools"] == 2
    assert report["functionalCoveragePercent"] == 66.67
    assert report["releaseGateFunctionalTools"] == 2
    assert report["releaseGateRegisteredTools"] == 3
    assert report["releaseGateFunctionalCoveragePercent"] == 66.67
    assert report["liveLowScoreQuestionIds"] == ["Q2"]

    req_statuses = {item["id"]: item["status"] for item in report["requirements"]}
    assert req_statuses["REQ-LIVE-TOOLS-01"] == "pass"
    assert req_statuses["REQ-LIVE-TOOLS-02"] == "fail"
    assert req_statuses["REQ-LIVE-TOOLS-03"] == "pass"
    assert req_statuses["REQ-LIVE-TOOLS-05"] == "pass"


def test_calc_operability_excludes_optional_entitlement_from_release_gate() -> None:
    harness = {
        "summary": {"total_questions": 1, "total_score": 100, "percentage": 100.0},
        "utilization": {
            "registeredTools": 2,
            "perTool": {"tool.alpha": {}, "resources/read": {}},
            "missingTools": ["os_features.wfs_archive_capabilities"],
        },
        "results": [{"question_id": "Q1", "score": 100}],
    }
    probe = {
        "results": [
            {"tool": "os_features.wfs_archive_capabilities", "outcome": "blocked_auth"},
        ]
    }

    report = coverage._calc_operability(harness, probe)

    assert report["registeredTools"] == 2
    assert report["functionalTools"] == 1
    assert report["functionalCoveragePercent"] == 50.0
    assert report["optionalEntitlementTools"] == ["os_features.wfs_archive_capabilities"]
    assert report["releaseGateFunctionalTools"] == 1
    assert report["releaseGateRegisteredTools"] == 1
    assert report["releaseGateFunctionalCoveragePercent"] == 100.0

    req_statuses = {item["id"]: item["status"] for item in report["requirements"]}
    assert req_statuses["REQ-LIVE-TOOLS-01"] == "pass"
    assert req_statuses["REQ-LIVE-TOOLS-02"] == "pass"
    assert req_statuses["REQ-LIVE-TOOLS-05"] == "pass"
