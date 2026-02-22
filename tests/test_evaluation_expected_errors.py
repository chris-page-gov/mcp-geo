from __future__ import annotations

from tests.evaluation.harness import EvaluationHarness
from tests.evaluation.questions import Difficulty, EvaluationQuestion, ExpectedOutcome, Intent, ToolCallSpec


def _error_handling_points(result) -> float:  # type: ignore[no-untyped-def]
    for dim in result.score.dimensions:
        if dim.dimension == "error_handling":
            return dim.points
    raise AssertionError("Missing error_handling dimension")


def test_expected_error_is_not_penalized(monkeypatch) -> None:
    harness = EvaluationHarness(use_routing=False)

    def fake_call_tool(_tool: str, _payload: dict[str, object]):
        return 400, {"isError": True, "code": "INVALID_INPUT", "message": "bad input"}

    monkeypatch.setattr(harness.client, "call_tool", fake_call_tool)

    question = EvaluationQuestion(
        id="ERR001",
        question="Trigger expected validation error",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.EDGE,
        description="Expected validation error should be scored as graceful.",
        expected=ExpectedOutcome(required_tools=["demo.tool"], max_tool_calls=1),
        tool_calls=[ToolCallSpec("demo.tool", {}, expect_error=True)],
    )

    result = harness.run_single_question(question)
    assert result.error is None
    assert _error_handling_points(result) == 10


def test_missing_expected_error_is_marked_unhandled(monkeypatch) -> None:
    harness = EvaluationHarness(use_routing=False)

    def fake_call_tool(_tool: str, _payload: dict[str, object]):
        return 200, {"ok": True}

    monkeypatch.setattr(harness.client, "call_tool", fake_call_tool)

    question = EvaluationQuestion(
        id="ERR002",
        question="Expected error is not returned",
        intent=Intent.UNKNOWN,
        difficulty=Difficulty.EDGE,
        description="Missing expected error should be scored as unhandled.",
        expected=ExpectedOutcome(required_tools=["demo.tool"], max_tool_calls=1),
        tool_calls=[ToolCallSpec("demo.tool", {}, expect_error=True)],
    )

    result = harness.run_single_question(question)
    assert result.error is not None
    assert "expected error not returned" in result.error
    assert _error_handling_points(result) == 0
