from __future__ import annotations

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
