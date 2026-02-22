from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from server import stdio_adapter
from server.main import app

_FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "psr_peat_floor_question.json"
client = TestClient(app)


def _load_fixture() -> dict[str, Any]:
    payload = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Fixture must be a JSON object")
    return payload


def _assert_evidence_contract(payload: dict[str, Any], expected: dict[str, Any]) -> None:
    for field in expected["requiredEvidenceFields"]:
        assert field in payload

    aoi = payload.get("aoi", {})
    assert isinstance(aoi, dict)
    assert aoi.get("source") == expected["aoiSource"]
    assert isinstance(aoi.get("bbox"), list)
    assert len(aoi.get("bbox", [])) == 4

    evidence_summary = payload.get("evidenceSummary", {})
    assert isinstance(evidence_summary, dict)
    direct_ids = evidence_summary.get("directLayerIds", [])
    proxy_ids = evidence_summary.get("proxyLayerIds", [])
    assert isinstance(direct_ids, list)
    assert isinstance(proxy_ids, list)
    for layer_id in expected["requiredDirectLayerIds"]:
        assert layer_id in direct_ids
    for layer_id in expected["requiredProxyLayerIds"]:
        assert layer_id in proxy_ids

    confidence = payload.get("confidence", {})
    assert isinstance(confidence, dict)
    assert confidence.get("level") in {"medium", "high"}
    assert isinstance(confidence.get("score"), float)
    assert payload.get("caveats")


def test_psr_peat_floor_question_http_contract() -> None:
    fixture = _load_fixture()
    expected = fixture["expected"]

    route_resp = client.post(
        "/tools/call",
        json={"tool": "os_mcp.route_query", "query": fixture["question"]},
    )
    assert route_resp.status_code == 200
    route_body = route_resp.json()
    assert route_body.get("intent") == expected["intent"]
    assert route_body.get("recommended_tool") == expected["recommendedTool"]
    survey_plan = route_body.get("surveyPlan", [])
    assert isinstance(survey_plan, list)
    assert any(step.get("tool") == "os_peat.evidence_paths" for step in survey_plan)

    peat_resp = client.post(
        "/tools/call",
        json={"tool": "os_peat.evidence_paths", **fixture["evidenceRequest"]},
    )
    assert peat_resp.status_code == 200
    _assert_evidence_contract(peat_resp.json(), expected)


def test_psr_peat_floor_question_stdio_contract() -> None:
    fixture = _load_fixture()
    expected = fixture["expected"]

    route_call = stdio_adapter.handle_call_tool(
        {"name": "os_mcp_route_query", "arguments": {"query": fixture["question"]}}
    )
    assert route_call.get("ok") is True
    route_data = route_call.get("data", {})
    assert isinstance(route_data, dict)
    assert route_data.get("intent") == expected["intent"]
    assert route_data.get("recommended_tool") == expected["recommendedTool"]
    survey_plan = route_data.get("surveyPlan", [])
    assert isinstance(survey_plan, list)
    assert any(step.get("tool") == "os_peat.evidence_paths" for step in survey_plan)

    peat_call = stdio_adapter.handle_call_tool(
        {"name": "os_peat_evidence_paths", "arguments": fixture["evidenceRequest"]}
    )
    assert peat_call.get("ok") is True
    peat_data = peat_call.get("data", {})
    assert isinstance(peat_data, dict)
    _assert_evidence_contract(peat_data, expected)
