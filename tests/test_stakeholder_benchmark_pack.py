from __future__ import annotations

import json
from pathlib import Path

import scripts.stakeholder_benchmark_pack as stakeholder_pack


def _configure_output_paths(monkeypatch, tmp_path: Path) -> None:
    pack_root = tmp_path / "data" / "benchmarking" / "stakeholder_eval"
    monkeypatch.setattr(stakeholder_pack, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(stakeholder_pack, "PACK_ROOT", pack_root)
    monkeypatch.setattr(stakeholder_pack, "FIXTURE_ROOT", pack_root / "fixtures")
    monkeypatch.setattr(stakeholder_pack, "REFERENCE_ROOT", pack_root / "reference_outputs")
    monkeypatch.setattr(stakeholder_pack, "PACK_JSON_PATH", pack_root / "benchmark_pack_v1.json")
    monkeypatch.setattr(
        stakeholder_pack,
        "REPORT_PATH",
        tmp_path / "docs" / "reports" / "MCP-Geo_evaluation_questions.md",
    )
    monkeypatch.setattr(
        stakeholder_pack,
        "WORKFLOW_REPORT_PATH",
        tmp_path
        / "docs"
        / "reports"
        / f"mcp_geo_stakeholder_benchmark_workflow_{stakeholder_pack.DATE_STAMP}.md",
    )


def test_write_pack_outputs_generates_valid_pack(monkeypatch, tmp_path: Path) -> None:
    _configure_output_paths(monkeypatch, tmp_path)

    validation = stakeholder_pack.write_pack_outputs()

    assert validation["ok"] is True
    assert not validation["errors"]
    assert all(score["score"] >= 90 for score in validation["scores"])
    assert (
        tmp_path
        / "data"
        / "benchmarking"
        / "stakeholder_eval"
        / "fixtures"
        / "scenario_01_vulnerable_households.csv"
    ).exists()
    assert (
        tmp_path
        / "data"
        / "benchmarking"
        / "stakeholder_eval"
        / "reference_outputs"
        / "sg10.json"
    ).exists()


def test_rendered_report_includes_full_reference_outputs(monkeypatch, tmp_path: Path) -> None:
    _configure_output_paths(monkeypatch, tmp_path)

    stakeholder_pack.write_pack_outputs()
    report = (
        tmp_path / "docs" / "reports" / "MCP-Geo_evaluation_questions.md"
    ).read_text(encoding="utf-8")

    assert report.count("**Reference Output (JSON)**") == 10
    assert '"suggested_export_format"' in report
    assert '"structured_route_summary"' in report
    assert (
        f"[mcp_geo_stakeholder_benchmark_workflow_{stakeholder_pack.DATE_STAMP}.md]"
        f"(mcp_geo_stakeholder_benchmark_workflow_{stakeholder_pack.DATE_STAMP}.md)"
    ) in report


def test_sg04_uses_current_rutland_transparency_comparator() -> None:
    pack = stakeholder_pack.build_pack()
    scenario = next(item for item in pack["scenarios"] if item["id"] == "SG04")

    assert "A roads 77 km" in scenario["comparatorSummary"]
    assert "B/C roads 221 km" in scenario["comparatorSummary"]
    assert scenario["referenceOutput"]["summary_table_by_class"] == [
        {"road_class": "A", "length_km": 77.0},
        {"road_class": "B/C", "length_km": 221.0},
        {"road_class": "U", "length_km": 222.0},
        {"road_class": "Total roads", "length_km": 520.0},
    ]
    assert json.dumps(scenario["referenceOutput"], sort_keys=True)
