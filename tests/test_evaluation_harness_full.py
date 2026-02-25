import json
from typing import Any

from server.config import settings
from tests.evaluation.harness import EvaluationHarness
from tests.evaluation.questions import ALL_QUESTIONS, Difficulty, Intent
from tools.registry import list_tools


def _install_os_handlers(handlers: dict[str, Any]) -> None:
    def places_handler(url: str, params: dict[str, Any]):
        return 200, {
            "results": [
                {
                    "DPA": {
                        "UPRN": "1000000001",
                        "ADDRESS": "1 Example Street",
                        "LAT": 51.5,
                        "LNG": -0.12,
                        "CLASS": "R",
                        "LOCAL_CUSTODIAN_CODE": 123,
                    }
                }
            ]
        }

    def names_handler(url: str, params: dict[str, Any]):
        return 200, {
            "results": [
                {
                    "GAZETTEER_ENTRY": {
                        "ID": "G1",
                        "NAME1": "Example Feature",
                        "TYPE": "Feature",
                        "DISTANCE": 12.3,
                        "GEOMETRY": [0, 0],
                    }
                }
            ]
        }

    def features_handler(url: str, params: dict[str, Any]):
        return 200, {
            "features": [
                {
                    "id": "feat-1",
                    "geometry": {"type": "Polygon"},
                    "properties": {"name": "Example"},
                }
            ]
        }

    def linked_ids_handler(url: str, params: dict[str, Any]):
        return 200, {"identifiers": [{"uprn": "1000000001"}]}

    handlers["places"] = places_handler
    handlers["names"] = names_handler
    handlers["features"] = features_handler
    handlers["identifierTypes"] = linked_ids_handler


def _install_ons_stubs(monkeypatch) -> None:
    from tools import ons_common, ons_search

    def fake_ons_get_json(
        url: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ):
        if "/observations" in url:
            return 200, {
                "observations": [
                    {
                        "geography": "K02000001",
                        "measure": "chained_volume_measure",
                        "time": "2023 Q1",
                        "value": 525.1,
                    },
                    {
                        "geography": "K02000001",
                        "measure": "chained_volume_measure",
                        "time": "2023 Q2",
                        "value": 526.3,
                    },
                ],
                "total": 2,
            }
        if url.endswith("/version/1"):
            return 200, {"dimensions": [{"id": "time"}, {"id": "geography"}]}
        if "/dimensions/" in url and url.endswith("/options"):
            if "/dimensions/time/" in url:
                return 200, {"items": [{"id": "2023 Q1"}, {"id": "2023 Q2"}]}
            return 200, {"items": [{"id": "K02000001"}]}
        return 200, {}

    def fake_search_get_json(url: str, params: dict[str, Any]):
        return 200, {
            "items": [
                {
                    "id": "gdp",
                    "title": "GDP",
                    "description": "Gross domestic product",
                    "keywords": ["gdp"],
                    "state": "published",
                    "links": {},
                }
            ],
            "offset": params.get("offset", 0),
            "limit": params.get("limit", 20),
            "total_count": 1,
        }

    monkeypatch.setattr(ons_common.client, "get_json", fake_ons_get_json)
    monkeypatch.setattr(ons_search._SEARCH_CLIENT, "get_json", fake_search_get_json)


def _install_nomis_stubs(monkeypatch) -> None:
    from tools import nomis_common

    def fake_nomis_get_json(
        url: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ):
        if url.endswith(("def.sdmx.json", "def.json")):
            if "/dataset/" in url:
                return 200, {"datasets": [{"id": "NM_1", "name": "Nomis Dataset"}]}
            if "/concept/" in url:
                return 200, {"concepts": [{"id": "C001", "name": "Nomis Concept"}]}
            if "/codelist/" in url:
                return 200, {"codelists": [{"id": "CL_1", "name": "Nomis Codelist"}]}
        if url.endswith(("jsonstat.json", "generic.sdmx.json")):
            return 200, {"dataset": "NM_1", "value": [1, 2]}
        return 200, {}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_nomis_get_json)


def _install_admin_lookup_stubs(monkeypatch) -> None:
    from tools import admin_lookup

    def fake_arcgis_get_json(url: str, params: dict[str, Any]):
        if params.get("returnExtentOnly") == "true":
            return 200, {"extent": {"xmin": -0.2, "ymin": 51.4, "xmax": -0.1, "ymax": 51.6}}
        attrs: dict[str, Any] = {}
        for source in admin_lookup.ADMIN_SOURCES:
            attrs[source.id_field] = f"{source.level}_ID"
            attrs[source.name_field] = f"{source.level} Name"
            if source.lat_field:
                attrs[source.lat_field] = 51.5
            if source.lon_field:
                attrs[source.lon_field] = -0.12
        return 200, {"features": [{"attributes": attrs}]}

    monkeypatch.setattr(admin_lookup._ARCGIS_CLIENT, "get_json", fake_arcgis_get_json)


def test_evaluation_harness_full_coverage(monkeypatch, tmp_path, mock_os_client):
    _install_os_handlers(mock_os_client)
    _install_ons_stubs(monkeypatch)
    _install_nomis_stubs(monkeypatch)
    _install_admin_lookup_stubs(monkeypatch)
    from tools import os_common, os_features, os_linked_ids, os_names, os_places, os_places_extra

    fake_client = os_common.client
    monkeypatch.setattr(os_places, "client", fake_client)
    monkeypatch.setattr(os_places_extra, "client", fake_client)
    monkeypatch.setattr(os_names, "client", fake_client)
    monkeypatch.setattr(os_features, "client", fake_client)
    monkeypatch.setattr(os_linked_ids, "client", fake_client)
    # Keep exports local to the test tempdir (avoid writing into the repo worktree).
    from server.mcp import resource_catalog
    from tools import os_map

    exports_dir = tmp_path / "exports"
    monkeypatch.setattr(os_map, "_EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(resource_catalog, "EXPORTS_DIR", exports_dir)
    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ONS_SEARCH_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    ui_log_path = tmp_path / "ui-events.jsonl"
    monkeypatch.setattr(settings, "UI_EVENT_LOG_PATH", str(ui_log_path), raising=False)

    harness = EvaluationHarness(
        include_os_api=True,
        include_ons_live=True,
        use_routing=True,
        log_dir=tmp_path / "audit",
    )
    result = harness.run_evaluation()

    expected_difficulties = set(Difficulty)
    expected_intents = set(Intent)
    assert {q.difficulty for q in ALL_QUESTIONS} == expected_difficulties
    assert {q.intent for q in ALL_QUESTIONS} == expected_intents
    assert result.total_questions == len(ALL_QUESTIONS)

    called_tools = {tool for r in harness.results for tool in r.tool_calls}
    registered_tools = {tool for tool in list_tools() if not tool.startswith("temp.")}
    # The core evaluation question bank intentionally prioritizes canonical routes.
    # Newly added specialist OS surfaces are covered by dedicated unit/contract tests
    # and can be folded into evaluation questions in a later expansion pass.
    specialist_tools = {
        "os_downloads.list_products",
        "os_downloads.get_product",
        "os_downloads.list_product_downloads",
        "os_downloads.list_data_packages",
        "os_downloads.prepare_export",
        "os_downloads.get_export",
        "os_features.wfs_capabilities",
        "os_features.wfs_archive_capabilities",
        "os_linked_ids.identifiers",
        "os_linked_ids.feature_types",
        "os_linked_ids.product_version_info",
        "os_maps.wmts_capabilities",
        "os_maps.raster_tile",
        "os_offline.descriptor",
        "os_offline.get",
        "os_qgis.vector_tile_profile",
        "os_qgis.export_geopackage_descriptor",
        "os_net.rinex_years",
        "os_net.station_get",
        "os_net.station_log",
        "ons_geo.by_postcode",
        "ons_geo.by_uprn",
        "ons_geo.cache_status",
        "os_places.radius",
        "os_places.polygon",
        "os_landscape.find",
        "os_landscape.get",
        "os_tiles_ota.collections",
        "os_tiles_ota.tilematrixsets",
        "os_tiles_ota.conformance",
        "os_mcp.select_toolsets",
    }
    missing_tools = sorted((registered_tools - called_tools) - specialist_tools)
    assert not missing_tools, f"Missing tool coverage: {missing_tools}"
    assert "tools/search" in called_tools
    assert "resources/read" in called_tools

    peat_result = next(r for r in harness.results if r.question.id == "I018")
    assert peat_result.error is None
    route_payload = next(
        item["response"]
        for item in peat_result.raw_responses
        if item.get("tool") == "os_mcp.route_query"
    )
    assert route_payload.get("intent") == "environmental_survey"
    survey_plan = route_payload.get("surveyPlan", [])
    assert any(step.get("tool") == "os_peat.evidence_paths" for step in survey_plan)

    peat_payload = next(
        item["response"]
        for item in peat_result.raw_responses
        if item.get("tool") == "os_peat.evidence_paths"
    )
    aoi = peat_payload.get("aoi", {})
    assert aoi.get("source") == "os_landscape.get"
    evidence = peat_payload.get("evidenceSummary", {})
    assert "england-peat-map" in evidence.get("directLayerIds", [])
    assert "ngd-hydrology-proxy" in evidence.get("proxyLayerIds", [])
    assert peat_payload.get("confidence", {}).get("level") in {"medium", "high"}
    assert peat_payload.get("caveats")

    audit_files = list((tmp_path / "audit").glob("*.txt"))
    assert len(audit_files) == len(ALL_QUESTIONS)
    assert ui_log_path.exists()

    output_path = tmp_path / "evaluation_results.json"
    harness.save_results(output_path)
    harness.save_audit_logs(output_path.with_suffix(".audit.txt"))
    data = json.loads(output_path.read_text())
    assert "utilization" in data
    assert "effectiveness" in data
