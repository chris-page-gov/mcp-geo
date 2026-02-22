from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

DEFAULT_HARNESS = "data/evaluation_results_live_review_2026-02-21_after_patch2_full.json"
DEFAULT_PROBE = "data/live_missing_tools_probe_report_2026-02-21.json"
DEFAULT_OUTPUT = "data/spec_tool_operability_coverage_2026-02-21.json"
OPTIONAL_BY_ENTITLEMENT_TOOLS = {
    "os_features.wfs_archive_capabilities",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def _calc_operability(harness: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    utilization = harness.get("utilization", {})
    per_tool = utilization.get("perTool", {})
    missing_tools_raw = utilization.get("missingTools", [])
    if not isinstance(per_tool, dict) or not isinstance(missing_tools_raw, list):
        raise ValueError("Unexpected utilization schema in harness report")

    covered_tools = {name for name in per_tool if name not in {"tools/search", "resources/read"}}
    missing_tools = {name for name in missing_tools_raw if isinstance(name, str) and name.strip()}
    default_registered = len(covered_tools) + len(missing_tools)
    registered_tools = int(utilization.get("registeredTools", default_registered))

    probe_rows = probe.get("results", [])
    if not isinstance(probe_rows, list):
        raise ValueError("Unexpected probe schema")
    probe_pass = {
        row.get("tool")
        for row in probe_rows
        if (
            isinstance(row, dict)
            and row.get("outcome") == "pass"
            and isinstance(row.get("tool"), str)
        )
    }
    probe_blocked_auth = {
        row.get("tool")
        for row in probe_rows
        if isinstance(row, dict)
        and row.get("outcome") == "blocked_auth"
        and isinstance(row.get("tool"), str)
    }

    all_registered = covered_tools | missing_tools
    if registered_tools != len(all_registered):
        # Keep computation deterministic when report metadata and payload diverge.
        registered_tools = len(all_registered)

    functional_tools = covered_tools | probe_pass
    unresolved = sorted(all_registered - functional_tools - probe_blocked_auth)
    optional_entitlement_tools = sorted(
        tool for tool in all_registered if tool in OPTIONAL_BY_ENTITLEMENT_TOOLS
    )
    optional_entitlement_set = set(optional_entitlement_tools)

    functional_percent = (
        round((len(functional_tools) / registered_tools) * 100, 2) if registered_tools else 0.0
    )
    blocked_percent = (
        round((len(probe_blocked_auth) / registered_tools) * 100, 2) if registered_tools else 0.0
    )
    release_gate_registered = max(registered_tools - len(optional_entitlement_set), 0)
    release_gate_functional = len(functional_tools - optional_entitlement_set)
    release_gate_percent = (
        round((release_gate_functional / release_gate_registered) * 100, 2)
        if release_gate_registered
        else 100.0
    )

    question_count = int(harness.get("summary", {}).get("total_questions", 0))
    total_score = int(harness.get("summary", {}).get("total_score", 0))
    score_pct = float(harness.get("summary", {}).get("percentage", 0.0))
    question_fail_ids = []
    for row in harness.get("results", []):
        if not isinstance(row, dict):
            continue
        question_id = row.get("question_id")
        score = row.get("score")
        if isinstance(question_id, str) and isinstance(score, int) and score < 80:
            question_fail_ids.append(question_id)

    requirements = [
        {
            "id": "REQ-LIVE-TOOLS-01",
            "statement": "Every registered tool must have live execution evidence.",
            "measure": (
                "((harness-covered tools + probe covered tools + blocked-by-auth tools) "
                "/ registered tools)"
            ),
            "actual": f"{len(functional_tools) + len(probe_blocked_auth)}/{registered_tools}",
            "valuePercent": round(
                ((len(functional_tools) + len(probe_blocked_auth)) / registered_tools) * 100, 2
            )
            if registered_tools
            else 0.0,
            "status": "pass" if not unresolved else "fail",
        },
        {
            "id": "REQ-LIVE-TOOLS-02",
            "statement": (
                "Release-gated functional operability should be >= 95% after excluding "
                "optional-by-entitlement tools."
            ),
            "measure": "(functional tools excluding optional entitlement tools / gated tools) >= 95%",
            "actual": f"{release_gate_functional}/{release_gate_registered}",
            "valuePercent": release_gate_percent,
            "status": "pass" if release_gate_percent >= 95.0 else "fail",
        },
        {
            "id": "REQ-LIVE-TOOLS-03",
            "statement": "Question-level live harness score should be >= 90%.",
            "measure": "(total score / max score) >= 90%",
            "actual": f"{total_score}/{question_count * 100 if question_count else 0}",
            "valuePercent": round(score_pct, 2),
            "status": "pass" if score_pct >= 90.0 else "fail",
        },
        {
            "id": "REQ-LIVE-TOOLS-05",
            "statement": "Optional-by-entitlement tools must be explicitly classified and tracked.",
            "measure": (
                "optional entitlement tools are listed and each has functional or blocked_auth evidence"
            ),
            "actual": f"{len(optional_entitlement_tools)} listed",
            "valuePercent": 100.0
            if optional_entitlement_set <= (functional_tools | probe_blocked_auth)
            else 0.0,
            "status": "pass"
            if optional_entitlement_set <= (functional_tools | probe_blocked_auth)
            else "fail",
        },
    ]

    return {
        "checkedAtUtc": datetime.now(UTC).isoformat(),
        "registeredTools": registered_tools,
        "harnessCoveredTools": len(covered_tools),
        "probeCoveredTools": len(probe_pass),
        "blockedAuthTools": sorted(probe_blocked_auth),
        "optionalEntitlementTools": optional_entitlement_tools,
        "functionalTools": len(functional_tools),
        "functionalCoveragePercent": functional_percent,
        "releaseGateFunctionalTools": release_gate_functional,
        "releaseGateRegisteredTools": release_gate_registered,
        "releaseGateFunctionalCoveragePercent": release_gate_percent,
        "blockedCoveragePercent": blocked_percent,
        "unresolvedTools": unresolved,
        "liveQuestionScorePercent": round(score_pct, 2),
        "liveLowScoreQuestionIds": question_fail_ids,
        "requirements": requirements,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute measurable live operability coverage metrics."
    )
    parser.add_argument("--harness", default=DEFAULT_HARNESS, help="Harness results JSON path.")
    parser.add_argument(
        "--probe",
        default=DEFAULT_PROBE,
        help="Missing-tool probe report JSON path.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Coverage report output JSON path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    harness = _load_json(Path(args.harness))
    probe = _load_json(Path(args.probe))
    report = _calc_operability(harness, probe)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        "Spec operability coverage: "
        f"{report['functionalTools']}/{report['registeredTools']} functional "
        f"({report['functionalCoveragePercent']}%), "
        f"release_gate={report['releaseGateFunctionalTools']}/"
        f"{report['releaseGateRegisteredTools']} "
        f"({report['releaseGateFunctionalCoveragePercent']}%), "
        f"blocked_auth={len(report['blockedAuthTools'])}, "
        f"unresolved={len(report['unresolvedTools'])}"
    )
    print(f"Saved report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
