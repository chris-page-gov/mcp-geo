import os
import uuid
from pathlib import Path

import pytest

from server.config import settings
from tests.evaluation.harness import EvaluationHarness
from tests.evaluation.live_capture import LiveApiCapture, LiveApiRecorder

RUN_LIVE = os.getenv("RUN_LIVE_API_TESTS") == "1"
LIVE_DSN = os.getenv("MCP_GEO_LIVE_DB_DSN")
OS_KEY = os.getenv("OS_API_KEY")

_SKIP_REASON = (
    "Live API test requires RUN_LIVE_API_TESTS=1, MCP_GEO_LIVE_DB_DSN, and OS_API_KEY."
)
pytestmark = pytest.mark.skipif(not (RUN_LIVE and LIVE_DSN and OS_KEY), reason=_SKIP_REASON)


class LiveEvaluationHarness(EvaluationHarness):
    def __init__(self, *args, capture: LiveApiCapture, **kwargs):
        super().__init__(*args, **kwargs)
        self._capture = capture
        self._current_question_id = "unknown"

    def run_single_question(self, question):
        self._current_question_id = question.id
        return super().run_single_question(question)

    def _call_spec(self, spec, context):
        question_id = self._current_question_id
        correlation_id = f"{question_id}:{spec.name}:{uuid.uuid4().hex[:8]}"
        with self._capture.context(
            question_id=question_id,
            tool_name=spec.name,
            correlation_id=correlation_id,
        ):
            return super()._call_spec(spec, context)


def test_live_api_evaluation_capture(monkeypatch):
    recorder = LiveApiRecorder(LIVE_DSN)
    recorder.ensure_schema()
    capture = LiveApiCapture(recorder, run_id=uuid.uuid4().hex)
    capture.install(monkeypatch)

    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ONS_SEARCH_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / "evaluation_results_live.json"

    try:
        harness = LiveEvaluationHarness(
            capture=capture,
            include_os_api=True,
            include_ons_live=True,
            use_routing=True,
            log_dir=data_dir / "audit",
        )
        result = harness.run_evaluation()
        harness.save_results(output_path)
        harness.save_audit_logs(output_path.with_suffix(".audit.txt"))

        assert result.total_questions > 0
        assert recorder.count_calls(capture.run_id) > 0
    finally:
        recorder.close()
