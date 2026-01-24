"""Test harness for MCP Geo evaluation questions."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from server.main import app
from tests.evaluation.audit_logger import AuditLogger, AuditRecord
from tests.evaluation.questions import (
    ALL_QUESTIONS,
    AMBIGUOUS_QUESTIONS,
    ADVANCED_QUESTIONS,
    BASIC_QUESTIONS,
    EDGE_CASE_QUESTIONS,
    INTERMEDIATE_QUESTIONS,
    Difficulty,
    EvaluationQuestion,
    Intent,
    ToolCallSpec,
    get_questions,
)
from tests.evaluation.rubric import (
    DimensionScore,
    EvaluationResult,
    QuestionScore,
    Rubric,
    ScoreLevel,
)
from tools.registry import list_tools


@dataclass
class TestResult:
    question: EvaluationQuestion
    score: QuestionScore
    audit_record: Optional[AuditRecord] = None
    raw_responses: List[Dict[str, Any]] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    detected_intent: Optional[str] = None
    detected_confidence: float = 0.0
    duration_ms: float = 0.0
    error: Optional[str] = None


class MCPHttpClient:
    def __init__(self):
        self.client = TestClient(app)

    def call_tool(self, tool: str, payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
        body = {"tool": tool, **payload}
        resp = self.client.post("/tools/call", json=body)
        return resp.status_code, resp.json()

    def search_tools(self, payload: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
        resp = self.client.post("/tools/search", json=payload)
        return resp.status_code, resp.json()

    def get_resource(self, params: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
        resp = self.client.get("/resources/read", params=params)
        return resp.status_code, resp.json()


class EvaluationHarness:
    def __init__(
        self,
        *,
        verbose: bool = False,
        include_os_api: bool = False,
        include_ons_live: bool = False,
        use_routing: bool = True,
        log_dir: Optional[Path] = None,
    ):
        self.client = MCPHttpClient()
        self.verbose = verbose
        self.include_os_api = include_os_api
        self.include_ons_live = include_ons_live
        self.use_routing = use_routing
        self.rubric = Rubric()
        self.audit_logger = AuditLogger(log_dir=log_dir)
        self.results: List[TestResult] = []
        self.last_evaluation: Optional[EvaluationResult] = None

    def _resolve_payload(self, payload: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        for key, value in payload.items():
            if isinstance(value, str) and value.startswith("$"):
                resolved[key] = context.get(value[1:], value)
            else:
                resolved[key] = value
        return resolved

    def _record_context(self, response: Dict[str, Any], context: Dict[str, Any]) -> None:
        if "filterId" in response:
            context["filterId"] = response.get("filterId")

    def _call_spec(self, spec: ToolCallSpec, context: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
        payload = self._resolve_payload(spec.payload, context)
        if spec.call_type == "tools_search":
            return self.client.search_tools(payload)
        if spec.call_type == "resource":
            return self.client.get_resource(payload)
        return self.client.call_tool(spec.name, payload)

    def run_single_question(self, question: EvaluationQuestion) -> TestResult:
        start_time = time.time()
        tool_calls: List[str] = []
        raw_responses: List[Dict[str, Any]] = []
        detected_intent: Optional[str] = None
        detected_confidence = 0.0
        error_messages: List[str] = []
        unexpected_errors: List[str] = []
        context: Dict[str, Any] = {}

        self.audit_logger.start_query(
            question.question,
            metadata={"question_id": question.id, "expected_intent": question.intent.value},
        )

        if self.use_routing:
            status, routing_data = self.client.call_tool(
                "os_mcp.route_query",
                {"query": question.question},
            )
            tool_calls.append("os_mcp.route_query")
            raw_responses.append({"tool": "os_mcp.route_query", "response": routing_data})
            detected_intent = routing_data.get("intent")
            detected_confidence = routing_data.get("confidence", 0.0)
            self.audit_logger.record_routing(
                intent=detected_intent or "unknown",
                confidence=detected_confidence,
                recommended_tool=routing_data.get("recommended_tool", "unknown"),
                workflow_steps=routing_data.get("workflow_steps", []),
            )
            if status >= 400:
                unexpected_errors.append(f"route_query status={status}")

        for spec in question.tool_calls:
            call_start = time.time()
            status, response = self._call_spec(spec, context)
            duration_ms = (time.time() - call_start) * 1000
            tool_calls.append(spec.name)
            raw_responses.append({"tool": spec.name, "response": response})
            success = 200 <= status < 300

            self.audit_logger.record_tool_call(
                tool_name=spec.name,
                inputs=self._resolve_payload(spec.payload, context),
                outputs=response,
                duration_ms=duration_ms,
                success=success,
                error=None if success else response.get("message") if isinstance(response, dict) else None,
            )

            self._record_context(response, context)

            if not success or response.get("isError"):
                message = response.get("code") or response.get("message") or f"status={status}"
                error_messages.append(str(message))
                if not spec.expect_error:
                    unexpected_errors.append(str(message))

        duration_ms = (time.time() - start_time) * 1000
        full_response = json.dumps(raw_responses)

        score = self._score_result(
            question=question,
            detected_intent=detected_intent,
            detected_confidence=detected_confidence,
            tool_calls=tool_calls,
            response_text=full_response,
            error_messages=error_messages,
            unexpected_errors=unexpected_errors,
        )

        self.audit_logger.record_response(full_response)
        if unexpected_errors:
            self.audit_logger.record_error("; ".join(unexpected_errors))
        audit_record = self.audit_logger.end_query()

        result = TestResult(
            question=question,
            score=score,
            audit_record=audit_record,
            raw_responses=raw_responses,
            tool_calls=tool_calls,
            detected_intent=detected_intent,
            detected_confidence=detected_confidence,
            duration_ms=duration_ms,
            error="; ".join(unexpected_errors) if unexpected_errors else None,
        )
        if self.verbose:
            self._print_result(result)
        return result

    def _score_result(
        self,
        *,
        question: EvaluationQuestion,
        detected_intent: Optional[str],
        detected_confidence: float,
        tool_calls: List[str],
        response_text: str,
        error_messages: List[str],
        unexpected_errors: List[str],
    ) -> QuestionScore:
        required_tools = list(question.expected.required_tools)
        if self.use_routing:
            required_tools = ["os_mcp.route_query"] + required_tools

        dimensions: List[DimensionScore] = []
        dimensions.append(
            self.rubric.score_intent_recognition(
                expected_intent=question.intent.value,
                detected_intent=detected_intent,
                confidence=detected_confidence,
            )
        )
        dimensions.append(
            self.rubric.score_tool_selection(
                required_tools=required_tools,
                forbidden_tools=question.expected.forbidden_tools,
                actual_tools=tool_calls,
            )
        )
        dimensions.append(
            self.rubric.score_efficiency(
                actual_tool_calls=len(tool_calls),
                max_expected_calls=question.expected.max_tool_calls,
            )
        )
        dimensions.append(
            self.rubric.score_response_quality(
                response=response_text,
                required_keywords=question.expected.required_keywords,
                forbidden_keywords=question.expected.forbidden_keywords,
                expected_values=question.expected.expected_values,
            )
        )
        had_errors = bool(error_messages)
        graceful = not unexpected_errors
        dimensions.append(
            self.rubric.score_error_handling(
                had_errors=had_errors,
                error_messages=error_messages,
                graceful_handling=graceful,
            )
        )

        total_score = sum(d.points for d in dimensions)
        return QuestionScore(
            question_id=question.id,
            question_text=question.question,
            total_score=total_score,
            dimensions=dimensions,
            tool_calls=tool_calls,
            response_summary=response_text[:500],
        )

    def run_questions(self, questions: List[EvaluationQuestion]) -> List[TestResult]:
        results = []
        for idx, question in enumerate(questions, start=1):
            if self.verbose:
                print(f"\n[{idx}/{len(questions)}] {question.question[:60]}")
            results.append(self.run_single_question(question))
        return results

    def run_evaluation(
        self,
        *,
        difficulty: Optional[Difficulty] = None,
        intent: Optional[Intent] = None,
        question_ids: Optional[List[str]] = None,
    ) -> EvaluationResult:
        if question_ids:
            questions = [q for q in ALL_QUESTIONS if q.id in question_ids]
        else:
            questions = get_questions(intent=intent, difficulty=difficulty)

        if not self.include_os_api:
            questions = [q for q in questions if not q.requires_os_api]
        if not self.include_ons_live:
            questions = [q for q in questions if not q.requires_ons_live]

        if not questions:
            raise ValueError("No questions selected for evaluation")

        print(f"\n{'=' * 60}")
        print("MCP Geo Evaluation")
        print(f"Questions: {len(questions)}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'=' * 60}\n")

        self.results = self.run_questions(questions)

        total_score = sum(r.score.total_score for r in self.results)
        max_score = len(self.results) * 100
        percentage = (total_score / max_score) * 100 if max_score else 0

        by_difficulty: Dict[str, float] = {}
        for diff in Difficulty:
            diff_results = [r for r in self.results if r.question.difficulty == diff]
            if diff_results:
                diff_score = sum(r.score.total_score for r in diff_results)
                diff_max = len(diff_results) * 100
                by_difficulty[diff.value] = (diff_score / diff_max) * 100

        by_intent: Dict[str, float] = {}
        for intent_type in Intent:
            intent_results = [r for r in self.results if r.question.intent == intent_type]
            if intent_results:
                intent_score = sum(r.score.total_score for r in intent_results)
                intent_max = len(intent_results) * 100
                by_intent[intent_type.value] = (intent_score / intent_max) * 100

        level = ScoreLevel.FAIL
        if percentage >= 90:
            level = ScoreLevel.EXCELLENT
        elif percentage >= 75:
            level = ScoreLevel.GOOD
        elif percentage >= 60:
            level = ScoreLevel.ACCEPTABLE
        elif percentage >= 40:
            level = ScoreLevel.POOR

        result = EvaluationResult(
            timestamp=datetime.now().isoformat(),
            total_questions=len(self.results),
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            level=level,
            question_scores=[r.score for r in self.results],
            by_difficulty=by_difficulty,
            by_intent=by_intent,
            summary=self._generate_summary(),
        )
        self.last_evaluation = result
        self._print_summary(result)
        return result

    def _build_utilization_report(self) -> Dict[str, Any]:
        tool_stats: Dict[str, Dict[str, Any]] = {}
        total_calls = 0
        for result in self.results:
            record = result.audit_record
            if not record:
                continue
            for call in record.tool_calls:
                total_calls += 1
                stats = tool_stats.setdefault(
                    call.tool_name,
                    {"calls": 0, "success": 0, "errors": 0},
                )
                stats["calls"] += 1
                if call.success:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1
        for stats in tool_stats.values():
            calls = stats["calls"]
            stats["successRate"] = round((stats["success"] / calls) * 100, 2) if calls else 0.0
        registered_tools = set(list_tools())
        called_tools = set(tool_stats.keys())
        missing_tools = sorted(registered_tools - called_tools)
        coverage_pct = (
            (len(registered_tools) - len(missing_tools)) / len(registered_tools) * 100
            if registered_tools
            else 0.0
        )
        return {
            "totalCalls": total_calls,
            "uniqueToolsCalled": len(called_tools),
            "registeredTools": len(registered_tools),
            "coveragePercent": round(coverage_pct, 2),
            "missingTools": missing_tools,
            "perTool": tool_stats,
        }

    def _build_effectiveness_report(self, evaluation: Optional[EvaluationResult]) -> Dict[str, Any]:
        total_questions = len(self.results)
        pass_threshold = 75.0
        if total_questions:
            avg_score = sum(r.score.percentage for r in self.results) / total_questions
            passed = sum(1 for r in self.results if r.score.percentage >= pass_threshold)
        else:
            avg_score = 0.0
            passed = 0
        tool_effectiveness: Dict[str, Dict[str, Any]] = {}
        for result in self.results:
            for tool in result.question.expected.required_tools:
                stats = tool_effectiveness.setdefault(
                    tool,
                    {"questions": 0, "averageScore": 0.0},
                )
                stats["questions"] += 1
                stats["averageScore"] += result.score.percentage
        for stats in tool_effectiveness.values():
            if stats["questions"]:
                stats["averageScore"] = round(stats["averageScore"] / stats["questions"], 2)
        return {
            "overall": {
                "percentage": (
                    round(evaluation.percentage, 2)
                    if evaluation
                    else round(avg_score, 2)
                ),
                "level": evaluation.level.value if evaluation else ScoreLevel.FAIL.value,
                "averageScore": round(avg_score, 2),
                "passRate": (
                    round((passed / total_questions) * 100, 2)
                    if total_questions
                    else 0.0
                ),
                "passThreshold": pass_threshold,
            },
            "byDifficulty": evaluation.by_difficulty if evaluation else {},
            "byIntent": evaluation.by_intent if evaluation else {},
            "perTool": tool_effectiveness,
        }

    def _generate_summary(self) -> str:
        passed = sum(1 for r in self.results if r.score.percentage >= 75)
        failed = len(self.results) - passed
        lines = [f"Passed: {passed}/{len(self.results)} ({passed/len(self.results)*100:.0f}%)"]
        lines.append(f"Failed: {failed}")
        low_scores = sorted(self.results, key=lambda r: r.score.total_score)[:5]
        if low_scores:
            lines.append("\nLowest Scoring Questions:")
            for r in low_scores:
                lines.append(f"  - [{r.question.id}] {r.score.total_score:.0f}%: {r.question.question[:40]}")
        return "\n".join(lines)

    def _print_result(self, result: TestResult) -> None:
        status = "✓" if result.score.percentage >= 75 else "✗"
        print(f"{status} [{result.question.id}] {result.question.question[:50]}")
        print(f"   Score: {result.score.total_score:.0f}/100 ({result.score.percentage:.0f}%)")
        print(f"   Intent: {result.detected_intent} (expected: {result.question.intent.value})")
        print(f"   Tools: {' -> '.join(result.tool_calls)}")
        if result.error:
            print(f"   Error: {result.error[:100]}")

    def _print_summary(self, result: EvaluationResult) -> None:
        print(f"\n{'=' * 60}")
        print("EVALUATION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Overall Score: {result.total_score:.0f}/{result.max_score:.0f} ({result.percentage:.1f}%)")
        print(f"Level: {result.level.value.upper()}")
        print()
        print("By Difficulty:")
        for diff, pct in sorted(result.by_difficulty.items()):
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {diff:15} [{bar}] {pct:.1f}%")
        print()
        print("By Intent:")
        for intent, pct in sorted(result.by_intent.items()):
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {intent:20} [{bar}] {pct:.1f}%")
        print()
        print(result.summary)
        print(f"\n{'=' * 60}\n")

    def save_results(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        utilization = self._build_utilization_report()
        effectiveness = self._build_effectiveness_report(self.last_evaluation)
        results_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": len(self.results),
                "total_score": sum(r.score.total_score for r in self.results),
                "percentage": (
                    sum(r.score.percentage for r in self.results) / len(self.results)
                    if self.results
                    else 0
                ),
            },
            "utilization": utilization,
            "effectiveness": effectiveness,
            "results": [
                {
                    "question_id": r.question.id,
                    "question": r.question.question,
                    "expected_intent": r.question.intent.value,
                    "detected_intent": r.detected_intent,
                    "confidence": r.detected_confidence,
                    "score": r.score.total_score,
                    "percentage": r.score.percentage,
                    "level": r.score.level.value,
                    "tool_calls": r.tool_calls,
                    "duration_ms": r.duration_ms,
                    "error": r.error,
                    "dimensions": [
                        {
                            "dimension": d.dimension,
                            "points": d.points,
                            "max_points": d.max_points,
                            "level": d.level.value,
                            "details": d.details,
                        }
                        for d in r.score.dimensions
                    ],
                }
                for r in self.results
            ],
        }
        output_path.write_text(json.dumps(results_data, indent=2))
        print(f"Results saved to {output_path}")

    def save_audit_logs(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logs: List[str] = []
        for result in self.results:
            if result.audit_record:
                logs.append(self.audit_logger.format_for_llm(result.audit_record))
        output_path.write_text("\n\n".join(logs))
        print(f"Audit logs saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MCP Geo Evaluation")
    parser.add_argument(
        "--difficulty",
        choices=[d.value for d in Difficulty] + ["all"],
        default="all",
    )
    parser.add_argument(
        "--intent",
        choices=[i.value for i in Intent] + ["all"],
        default="all",
    )
    parser.add_argument("--questions", type=str, help="Comma-separated question IDs")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/evaluation/evaluation_results.json"),
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--include-os-api", action="store_true", help="Run questions requiring OS_API_KEY")
    parser.add_argument("--include-ons-live", action="store_true", help="Run questions requiring live ONS API")
    parser.add_argument("--no-routing", action="store_true", help="Skip os_mcp.route_query")

    args = parser.parse_args()

    difficulty = Difficulty(args.difficulty) if args.difficulty != "all" else None
    intent = Intent(args.intent) if args.intent != "all" else None
    question_ids = args.questions.split(",") if args.questions else None

    harness = EvaluationHarness(
        verbose=args.verbose,
        include_os_api=args.include_os_api,
        include_ons_live=args.include_ons_live,
        use_routing=not args.no_routing,
    )

    result = harness.run_evaluation(
        difficulty=difficulty,
        intent=intent,
        question_ids=question_ids,
    )
    harness.save_results(args.output)
    harness.save_audit_logs(args.output.with_suffix(".audit.txt"))

    sys.exit(0 if result.percentage >= 60 else 1)


if __name__ == "__main__":
    main()
