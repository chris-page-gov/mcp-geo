from __future__ import annotations

import json

from tests.evaluation.audit_logger import AuditLogger
from tests.evaluation.harness import EvaluationHarness
from tests.evaluation.questions import (
    Difficulty,
    EvaluationQuestion,
    ExpectedOutcome,
    Intent,
    ToolCallSpec,
)


def test_audit_logger_records_rate_limit_429_summary(tmp_path) -> None:
    logger = AuditLogger(log_dir=tmp_path)
    logger.start_query("Trigger a rate limited tool")
    logger.record_tool_call(
        tool_name="demo.tool",
        inputs={},
        outputs={"isError": True, "code": "RATE_LIMITED", "message": "Too many requests"},
        duration_ms=12.5,
        status_code=429,
        success=False,
        error="Too many requests",
    )
    logger.record_tool_call(
        tool_name="demo.ok",
        inputs={},
        outputs={"ok": True},
        duration_ms=5.0,
        status_code=200,
        success=True,
    )
    logger.record_response("[]")

    record = logger.end_query()
    assert record is not None
    assert record.rate_limit_429_count == 1
    assert record.rate_limit_429_by_tool == {"demo.tool": 1}

    audit_text = (tmp_path / f"{record.audit_id}.txt").read_text()
    assert "429 Rate-limit hits: 1" in audit_text
    assert "429 by tool: {'demo.tool': 1}" in audit_text


def test_harness_audit_includes_429_counts_for_question(tmp_path, monkeypatch) -> None:
    harness = EvaluationHarness(use_routing=True, log_dir=tmp_path / "audit")

    def always_rate_limited(tool: str, payload: dict[str, object]):  # noqa: ARG001
        return 429, {"isError": True, "code": "RATE_LIMITED", "message": "Too many requests"}

    monkeypatch.setattr(harness.client, "call_tool", always_rate_limited)

    question = EvaluationQuestion(
        id="RL001",
        question="Rate limit exercise",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.EDGE,
        description="Force 429 responses to verify audit summary.",
        expected=ExpectedOutcome(required_tools=["demo.tool"], max_tool_calls=1),
        tool_calls=[ToolCallSpec("demo.tool", {})],
    )

    result = harness.run_single_question(question)
    assert result.audit_record is not None
    assert result.audit_record.rate_limit_429_count == 2
    assert result.audit_record.rate_limit_429_by_tool == {
        "os_mcp.route_query": 1,
        "demo.tool": 1,
    }

    harness.results = [result]
    utilization = harness._build_utilization_report()
    assert utilization["perTool"]["os_mcp.route_query"]["rateLimited429"] == 1
    assert utilization["perTool"]["demo.tool"]["rateLimited429"] == 1

    output_path = tmp_path / "results.json"
    harness.save_results(output_path)
    output_data = json.loads(output_path.read_text())
    assert output_data["summary"]["rate_limit_429_total"] == 2
    assert output_data["results"][0]["rate_limit_429_count"] == 2

