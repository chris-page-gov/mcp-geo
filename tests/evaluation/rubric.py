"""Evaluation Rubric for MCP Geo Server."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ScoreLevel(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    FAIL = "fail"


@dataclass
class DimensionScore:
    dimension: str
    points: float
    max_points: float
    level: ScoreLevel
    details: str
    deductions: List[str] = field(default_factory=list)


@dataclass
class QuestionScore:
    question_id: str
    question_text: str
    total_score: float
    max_score: float = 100.0
    percentage: float = 0.0
    level: ScoreLevel = ScoreLevel.FAIL
    dimensions: List[DimensionScore] = field(default_factory=list)
    tool_calls: List[str] = field(default_factory=list)
    response_summary: str = ""
    audit_log: str = ""

    def __post_init__(self):
        self.percentage = (self.total_score / self.max_score) * 100 if self.max_score else 0.0
        self.level = self._calculate_level()

    def _calculate_level(self) -> ScoreLevel:
        if self.percentage >= 90:
            return ScoreLevel.EXCELLENT
        if self.percentage >= 75:
            return ScoreLevel.GOOD
        if self.percentage >= 60:
            return ScoreLevel.ACCEPTABLE
        if self.percentage >= 40:
            return ScoreLevel.POOR
        return ScoreLevel.FAIL


@dataclass
class EvaluationResult:
    timestamp: str
    total_questions: int
    total_score: float
    max_score: float
    percentage: float
    level: ScoreLevel
    question_scores: List[QuestionScore] = field(default_factory=list)
    by_difficulty: Dict[str, float] = field(default_factory=dict)
    by_intent: Dict[str, float] = field(default_factory=dict)
    summary: str = ""


class Rubric:
    INTENT_RECOGNITION_MAX = 25
    TOOL_SELECTION_MAX = 25
    EFFICIENCY_MAX = 20
    RESPONSE_QUALITY_MAX = 20
    ERROR_HANDLING_MAX = 10

    def score_intent_recognition(
        self,
        expected_intent: str,
        detected_intent: Optional[str],
        confidence: float = 0.0,
    ) -> DimensionScore:
        max_points = self.INTENT_RECOGNITION_MAX
        deductions: List[str] = []

        if detected_intent is None:
            return DimensionScore(
                dimension="intent_recognition",
                points=0,
                max_points=max_points,
                level=ScoreLevel.FAIL,
                details="No intent detected",
                deductions=["Missing routing intent"],
            )

        if detected_intent == expected_intent:
            if confidence >= 0.8:
                points = 25
                level = ScoreLevel.EXCELLENT
                details = f"Correct intent ({expected_intent}) with high confidence ({confidence:.2f})"
            elif confidence >= 0.5:
                points = 20
                level = ScoreLevel.GOOD
                details = f"Correct intent ({expected_intent}) with medium confidence ({confidence:.2f})"
                deductions.append("Confidence below 0.8 (-5 points)")
            else:
                points = 15
                level = ScoreLevel.ACCEPTABLE
                details = f"Correct intent ({expected_intent}) with low confidence ({confidence:.2f})"
                deductions.append("Low confidence (-10 points)")
        else:
            points = 0
            level = ScoreLevel.FAIL
            details = f"Wrong intent: expected {expected_intent}, got {detected_intent}"
            deductions.append("Completely wrong intent")

        return DimensionScore(
            dimension="intent_recognition",
            points=points,
            max_points=max_points,
            level=level,
            details=details,
            deductions=deductions,
        )

    def score_tool_selection(
        self,
        required_tools: List[str],
        forbidden_tools: List[str],
        actual_tools: List[str],
    ) -> DimensionScore:
        max_points = self.TOOL_SELECTION_MAX
        deductions: List[str] = []

        required_used = [t for t in required_tools if t in actual_tools]
        required_missing = [t for t in required_tools if t not in actual_tools]
        required_ratio = len(required_used) / len(required_tools) if required_tools else 1.0

        forbidden_used = [t for t in forbidden_tools if t in actual_tools]

        if required_ratio == 1.0:
            base_score = 25
        elif required_ratio >= 0.75:
            base_score = 20
            deductions.append(f"Missing tools: {required_missing} (-5 points)")
        elif required_ratio >= 0.5:
            base_score = 15
            deductions.append(f"Missing tools: {required_missing} (-10 points)")
        elif required_ratio > 0:
            base_score = 10
            deductions.append(f"Missing most required tools: {required_missing}")
        else:
            base_score = 0
            deductions.append("No required tools used")

        if forbidden_used:
            if base_score == 25 and len(forbidden_used) == 1:
                base_score = 20
                deductions.append(f"Used forbidden tool: {forbidden_used}")
            else:
                base_score = 0
                deductions.append(f"Used forbidden tools: {forbidden_used}")

        if base_score >= 20:
            level = ScoreLevel.EXCELLENT if base_score == 25 else ScoreLevel.GOOD
        elif base_score >= 15:
            level = ScoreLevel.ACCEPTABLE
        elif base_score >= 10:
            level = ScoreLevel.POOR
        else:
            level = ScoreLevel.FAIL

        return DimensionScore(
            dimension="tool_selection",
            points=base_score,
            max_points=max_points,
            level=level,
            details=f"Used {len(required_used)}/{len(required_tools)} required tools",
            deductions=deductions,
        )

    def score_efficiency(self, actual_tool_calls: int, max_expected_calls: Optional[int]) -> DimensionScore:
        max_points = self.EFFICIENCY_MAX
        if max_expected_calls is None:
            return DimensionScore(
                dimension="efficiency",
                points=max_points,
                max_points=max_points,
                level=ScoreLevel.EXCELLENT,
                details="No max tool call guidance provided",
            )
        if actual_tool_calls <= max_expected_calls:
            return DimensionScore(
                dimension="efficiency",
                points=20,
                max_points=max_points,
                level=ScoreLevel.EXCELLENT,
                details="Within expected tool calls",
            )
        extra = actual_tool_calls - max_expected_calls
        if extra <= 2:
            points = 15
            level = ScoreLevel.GOOD
        elif extra <= 5:
            points = 10
            level = ScoreLevel.ACCEPTABLE
        elif extra <= 10:
            points = 5
            level = ScoreLevel.POOR
        else:
            points = 0
            level = ScoreLevel.FAIL
        return DimensionScore(
            dimension="efficiency",
            points=points,
            max_points=max_points,
            level=level,
            details=f"{extra} extra tool calls",
        )

    def score_response_quality(
        self,
        response: str,
        required_keywords: List[str],
        forbidden_keywords: List[str],
        expected_values: Dict[str, Any],
    ) -> DimensionScore:
        max_points = self.RESPONSE_QUALITY_MAX
        response_lower = response.lower()
        deductions: List[str] = []

        forbidden_found = [kw for kw in forbidden_keywords if kw.lower() in response_lower]
        if forbidden_found:
            return DimensionScore(
                dimension="response_quality",
                points=0,
                max_points=max_points,
                level=ScoreLevel.FAIL,
                details=f"Forbidden keywords found: {forbidden_found}",
                deductions=["Forbidden content"],
            )

        keywords_found = [kw for kw in required_keywords if kw.lower() in response_lower]
        keyword_ratio = len(keywords_found) / len(required_keywords) if required_keywords else 1.0

        values_found = 0
        for _, value in expected_values.items():
            if str(value) in response:
                values_found += 1
        values_ratio = values_found / len(expected_values) if expected_values else 1.0

        score_ratio = min(keyword_ratio, values_ratio)
        if score_ratio >= 0.9:
            points = 20
            level = ScoreLevel.EXCELLENT
        elif score_ratio >= 0.75:
            points = 15
            level = ScoreLevel.GOOD
        elif score_ratio >= 0.5:
            points = 10
            level = ScoreLevel.ACCEPTABLE
        elif score_ratio > 0:
            points = 5
            level = ScoreLevel.POOR
        else:
            points = 0
            level = ScoreLevel.FAIL

        if keywords_found != required_keywords:
            missing = [kw for kw in required_keywords if kw not in keywords_found]
            if missing:
                deductions.append(f"Missing keywords: {missing}")

        return DimensionScore(
            dimension="response_quality",
            points=points,
            max_points=max_points,
            level=level,
            details="Response keyword/value coverage",
            deductions=deductions,
        )

    def score_error_handling(
        self,
        had_errors: bool,
        error_messages: List[str],
        graceful_handling: bool,
    ) -> DimensionScore:
        max_points = self.ERROR_HANDLING_MAX
        if not had_errors:
            return DimensionScore(
                dimension="error_handling",
                points=10,
                max_points=max_points,
                level=ScoreLevel.EXCELLENT,
                details="No errors encountered",
            )
        if graceful_handling:
            return DimensionScore(
                dimension="error_handling",
                points=7,
                max_points=max_points,
                level=ScoreLevel.GOOD,
                details="Errors handled gracefully",
                deductions=[],
            )
        return DimensionScore(
            dimension="error_handling",
            points=0,
            max_points=max_points,
            level=ScoreLevel.FAIL,
            details="Unhandled errors",
            deductions=error_messages[:2],
        )


RUBRIC_DESCRIPTION = """
# Evaluation Rubric for MCP Geo Server

## Scoring Dimensions

### 1. Intent Recognition (0-25 points)
Measures how accurately the system identifies what the user wants.

| Score | Criteria |
|-------|----------|
| 25 | Correct intent with high confidence (>0.8) |
| 20 | Correct intent with medium confidence (0.5-0.8) |
| 15 | Correct intent with low confidence (<0.5) |
| 10 | Related but incorrect intent |
| 0 | Completely wrong intent |

### 2. Tool Selection (0-25 points)
Measures whether the right tools were used.

| Score | Criteria |
|-------|----------|
| 25 | All required tools used, no forbidden tools |
| 20 | All required tools, 1 minor forbidden tool |
| 15 | Most required tools (>50%) |
| 10 | Some required tools |
| 0 | No required tools or multiple forbidden tools |

### 3. Efficiency (0-20 points)
Measures whether the task was completed without unnecessary steps.

| Score | Criteria |
|-------|----------|
| 20 | At or below expected tool calls |
| 15 | 1-2 extra calls |
| 10 | 3-5 extra calls |
| 5 | 6-10 extra calls |
| 0 | More than 10 extra calls |

### 4. Response Quality (0-20 points)
Measures the accuracy and completeness of the response.

| Score | Criteria |
|-------|----------|
| 20 | All required keywords, expected values, no forbidden |
| 15 | Most required keywords (>75%) |
| 10 | Some required keywords (>50%) |
| 5 | Few required keywords |
| 0 | Forbidden keywords or no relevant content |

### 5. Error Handling (0-10 points)
Measures how gracefully errors are handled.

| Score | Criteria |
|-------|----------|
| 10 | No errors OR graceful handling with helpful message |
| 7 | Error occurred but handled gracefully |
| 5 | Error occurred, partially handled |
| 0 | Unhandled error or crash |
"""
