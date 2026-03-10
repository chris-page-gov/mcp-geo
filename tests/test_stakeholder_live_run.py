from __future__ import annotations

from copy import deepcopy

import scripts.stakeholder_live_run as stakeholder_live_run


def test_address_match_score_prefers_exact_candidate() -> None:
    exact = stakeholder_live_run.address_match_score(
        "81 COBWELL RD, RETFORD DN22 7DD",
        "81, COBWELL ROAD, RETFORD, DN22 7DD",
    )
    loose = stakeholder_live_run.address_match_score(
        "81 COBWELL RD, RETFORD DN22 7DD",
        "91, COBWELL ROAD, RETFORD, DN22 7DD",
    )

    assert exact > loose
    assert exact >= 0.85


def test_point_in_polygon_handles_clipped_benchmark_polygon() -> None:
    polygon = [
        (-0.946200, 53.321400),
        (-0.946200, 53.318800),
        (-0.943000, 53.318800),
        (-0.943000, 53.321400),
        (-0.946200, 53.321400),
    ]

    assert stakeholder_live_run.point_in_polygon(-0.9445, 53.3195, polygon) is True
    assert stakeholder_live_run.point_in_polygon(-0.9475, 53.3195, polygon) is False


def test_build_overall_summary_counts_live_outcomes() -> None:
    results = [
        {
            "scenarioId": "SG01",
            "liveOutcome": "partial",
            "firstClassProductReady": False,
            "liveEvidenceCalls": 3,
            "toolCalls": [{"tool": "os_places.search", "liveEvidence": True}],
        },
        {
            "scenarioId": "SG03",
            "liveOutcome": "blocked",
            "firstClassProductReady": False,
            "liveEvidenceCalls": 0,
            "toolCalls": [{"tool": "os_mcp.route_query", "liveEvidence": False}],
        },
    ]

    summary = stakeholder_live_run.build_overall_summary(results)

    assert summary["scenarioCount"] == 2
    assert summary["firstClassProductReadyCount"] == 0
    assert summary["liveOutcomeCounts"] == {"blocked": 1, "partial": 1}
    assert summary["scenarioIdsWithLiveEvidence"] == ["SG01"]
    assert summary["liveToolNames"] == ["os_places.search"]


def test_render_markdown_includes_interpretation_note() -> None:
    pack = {
        "scenarios": [
            {"id": "SG01", "supportLevel": "partial"},
        ]
    }
    run_data = {
        "runtime": {
            "osApiKeyPresent": True,
            "osApiKeyFile": "/Users/crpage/.secrets/os_api_key",
            "boundaryCacheEnabled": False,
        },
        "overall": {
            "scenarioCount": 1,
            "firstClassProductReadyCount": 0,
            "liveOutcomeCounts": {"partial": 1},
            "scenarioIdsWithLiveEvidence": ["SG01"],
        },
        "results": [
            {
                "scenarioId": "SG01",
                "title": "Example",
                "benchmarkSupportLevel": "partial",
                "liveOutcome": "partial",
                "firstClassProductReady": False,
                "summary": "Live evidence available.",
                "confirmedCapabilities": ["Capability"],
                "confirmedGaps": ["Gap"],
                "evidence": {"inputRecords": 1},
                "successfulToolCalls": 1,
                "toolCallCount": 1,
                "liveEvidenceCalls": 1,
                "toolCallAggregate": [
                    {
                        "tool": "os_places.search",
                        "calls": 1,
                        "ok": 1,
                        "liveEvidenceCalls": 1,
                        "cached": 0,
                    }
                ],
            }
        ],
    }

    report = stakeholder_live_run.render_markdown(pack, run_data)

    assert "gold-answer completeness score" in report
    assert "| SG01 | partial | partial | False | 1/1 | 1 |" in report
    assert "`inputRecords`: `1`" in report


class _FakeRunner:
    def __init__(self, responses):
        self._responses = responses

    def call(self, tool: str, **payload):
        response = self._responses[tool]
        call = deepcopy(response["call"])
        call.setdefault("tool", tool)
        call.setdefault("request", payload)
        body = deepcopy(response["body"])
        return call, body


def test_run_sg03_reports_graph_not_ready_with_correct_router(monkeypatch) -> None:
    origin_match = {"uprn": "10000000001", "lat": 53.321, "lon": -0.944}
    destination_match = {"uprn": "10000000002", "lat": 53.322, "lon": -0.943}

    def fake_resolve_address(_runner, text: str):
        return (
            {
                "tool": "os_places.search",
                "statusCode": 200,
                "ok": True,
                "durationMs": 12.0,
                "cached": False,
                "source": "OS Places live",
                "liveEvidence": True,
                "responseSummary": {"count": 1},
            },
            origin_match if "Library" in text else destination_match,
        )

    monkeypatch.setattr(stakeholder_live_run, "resolve_address", fake_resolve_address)
    runner = _FakeRunner(
        {
            "os_mcp.route_query": {
                "call": {"statusCode": 200, "ok": True, "source": "Router", "liveEvidence": False},
                "body": {
                    "intent": "route_planning",
                    "recommended_tool": "os_route.get",
                    "workflow_steps": ["os_route.get", "os_apps.render_route_planner"],
                    "recommended_parameters": {
                        "stops": [{"query": "origin"}, {"query": "destination"}],
                        "profile": "emergency",
                        "constraints": {
                            "avoidAreas": ["flood restrictions"],
                            "avoidIds": [],
                            "softAvoid": True,
                        },
                    },
                },
            },
            "os_route.descriptor": {
                "call": {
                    "statusCode": 200,
                    "ok": True,
                    "source": "Routing engine",
                    "liveEvidence": False,
                },
                "body": {"status": "not_ready", "graph": {"ready": False, "reason": "route_graph_disabled"}},
            },
            "os_route.get": {
                "call": {
                    "statusCode": 503,
                    "ok": False,
                    "source": "error",
                    "liveEvidence": False,
                },
                "body": {
                    "isError": True,
                    "code": "ROUTE_GRAPH_NOT_READY",
                    "message": "Route graph is not ready.",
                },
            },
            "os_apps.render_route_planner": {
                "call": {"statusCode": 200, "ok": True, "source": "UI shell", "liveEvidence": False},
                "body": {"resourceUri": "ui://mcp-geo/route-planner", "status": "ok"},
            },
        }
    )

    result = stakeholder_live_run.run_sg03(runner, {"id": "SG03", "title": "Routing", "supportLevel": "partial"})

    assert result["liveOutcome"] == "blocked"
    assert result["firstClassProductReady"] is False
    assert result["evidence"]["routeQueryRecommendedTool"] == "os_route.get"
    assert result["evidence"]["graphReady"] is False
    assert result["evidence"]["routeCode"] == "ROUTE_GRAPH_NOT_READY"
    assert "graph readiness" in result["summary"]


def test_run_sg03_reports_full_when_route_executes(monkeypatch) -> None:
    origin_match = {"uprn": "10000000001", "lat": 53.321, "lon": -0.944}
    destination_match = {"uprn": "10000000002", "lat": 53.322, "lon": -0.943}

    def fake_resolve_address(_runner, text: str):
        return (
            {
                "tool": "os_places.search",
                "statusCode": 200,
                "ok": True,
                "durationMs": 12.0,
                "cached": False,
                "source": "OS Places live",
                "liveEvidence": True,
                "responseSummary": {"count": 1},
            },
            origin_match if "Library" in text else destination_match,
        )

    monkeypatch.setattr(stakeholder_live_run, "resolve_address", fake_resolve_address)
    runner = _FakeRunner(
        {
            "os_mcp.route_query": {
                "call": {"statusCode": 200, "ok": True, "source": "Router", "liveEvidence": False},
                "body": {
                    "intent": "route_planning",
                    "recommended_tool": "os_route.get",
                    "workflow_steps": ["os_route.get", "os_apps.render_route_planner"],
                    "recommended_parameters": {
                        "stops": [{"query": "origin"}, {"query": "destination"}],
                        "profile": "emergency",
                        "constraints": {
                            "avoidAreas": ["flood restrictions"],
                            "avoidIds": [],
                            "softAvoid": True,
                        },
                    },
                },
            },
            "os_route.descriptor": {
                "call": {
                    "statusCode": 200,
                    "ok": True,
                    "source": "Routing engine",
                    "liveEvidence": False,
                },
                "body": {
                    "status": "ready",
                    "graph": {"ready": True, "reason": None, "graphVersion": "mrn-v1"},
                },
            },
            "os_route.get": {
                "call": {
                    "statusCode": 200,
                    "ok": True,
                    "source": "Routing engine",
                    "liveEvidence": False,
                },
                "body": {
                    "profile": "emergency",
                    "distanceMeters": 1234.5,
                    "durationSeconds": 210.0,
                    "route": {"type": "Feature", "geometry": {"type": "LineString", "coordinates": []}},
                    "steps": [{"instruction": "Head north"}],
                    "warnings": [{"type": "soft_avoid"}],
                    "graph": {"graphVersion": "mrn-v1"},
                },
            },
            "os_apps.render_route_planner": {
                "call": {"statusCode": 200, "ok": True, "source": "UI shell", "liveEvidence": False},
                "body": {"resourceUri": "ui://mcp-geo/route-planner", "status": "ok"},
            },
        }
    )

    result = stakeholder_live_run.run_sg03(runner, {"id": "SG03", "title": "Routing", "supportLevel": "partial"})

    assert result["liveOutcome"] == "full"
    assert result["firstClassProductReady"] is True
    assert result["evidence"]["distanceReturned"] is True
    assert result["evidence"]["turnByTurnReturned"] is True
    assert result["evidence"]["routeDistanceMeters"] == 1234.5
