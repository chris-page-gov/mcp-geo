from __future__ import annotations

from typing import Any

import tools.landis_catalog
import tools.landis_derive
import tools.landis_metadata
import tools.landis_soilscapes
from server.landis import LandisWarehouseDisabled, LandisWarehouseUnavailable
from tools.registry import get


def setup_function() -> None:
    from server import landis as landis_runtime

    landis_runtime.load_landis_registry.cache_clear()
    landis_runtime.get_landis_warehouse.cache_clear()


def _tool(name: str):
    tool = get(name)
    assert tool is not None
    return tool


def test_landis_catalog_list_products_returns_registry_entries() -> None:
    status, body = _tool("landis_catalog.list_products").call({})
    assert status == 200
    ids = {entry["id"] for entry in body["products"]}
    assert "soilscapes" in ids
    assert "pipe-risk" in ids
    assert body["registry"]["registryUri"] == "resource://mcp-geo/landis-products"


def test_landis_metadata_get_missing_product() -> None:
    status, body = _tool("landis_metadata.get").call({"productId": "missing"})
    assert status == 404
    assert body["code"] == "NOT_FOUND"


def test_landis_metadata_get_existing_product() -> None:
    status, body = _tool("landis_metadata.get").call({"productId": "soilscapes"})
    assert status == 200
    assert body["product"]["id"] == "soilscapes"
    assert body["metadata"]["citations"]


def test_landis_catalog_list_products_validates_and_filters_inputs() -> None:
    status, body = tools.landis_catalog._list_products({"limit": 0})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = tools.landis_catalog._list_products({"offset": -1})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = tools.landis_catalog._list_products({"q": ["bad"]})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = tools.landis_catalog._list_products({"family": ["bad"]})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = tools.landis_catalog._list_products({"family": "documentation", "q": "classification"})
    assert status == 200
    assert body["total"] >= 1
    assert all(item["family"] == "documentation" for item in body["products"])


def test_landis_metadata_requires_product_id() -> None:
    status, body = tools.landis_metadata._get_metadata({})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


class _FakeWarehouse:
    def __init__(self, *, point: Any = None, area: Any = None, pipe: Any = None) -> None:
        self._point = point
        self._area = area
        self._pipe = pipe

    def soilscapes_point(self, *, lat: float, lon: float) -> Any:
        if isinstance(self._point, Exception):
            raise self._point
        return self._point

    def soilscapes_area_summary(self, *, geometry: dict[str, Any]) -> Any:
        if isinstance(self._area, Exception):
            raise self._area
        return self._area

    def pipe_risk_summary(self, *, geometry: dict[str, Any]) -> Any:
        if isinstance(self._pipe, Exception):
            raise self._pipe
        return self._pipe


def test_landis_soilscapes_point_live_disabled(monkeypatch) -> None:
    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(point=LandisWarehouseDisabled("landis_live_disabled")),
    )
    status, body = _tool("landis_soilscapes.point").call({"lat": 52.0, "lon": -1.5})
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"


def test_landis_soilscapes_point_validates_and_handles_not_found(monkeypatch) -> None:
    status, body = tools.landis_soilscapes._point({"lat": "52.0", "lon": -1.5})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    status, body = tools.landis_soilscapes._point({"lat": 52.0, "lon": "bad"})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(point=None),
    )
    status, body = tools.landis_soilscapes._point({"lat": 52.0, "lon": -1.5})
    assert status == 404
    assert body["code"] == "NOT_FOUND"


def test_landis_soilscapes_point_success(monkeypatch) -> None:
    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(
            point={
                "soilscape": {
                    "code": "12",
                    "name": "Freely draining slightly acid but base-rich soils",
                    "dominantTexture": "loamy",
                    "drainageClass": "freely draining",
                    "carbonStatus": "moderate",
                    "habitatNote": "mixed arable and grassland",
                    "scaleLabel": "Generalized Soilscapes",
                },
                "provenance": {"productId": "soilscapes", "warehouseBacked": True},
            }
        ),
    )
    status, body = _tool("landis_soilscapes.point").call({"lat": 52.0, "lon": -1.5})
    assert status == 200
    assert body["soilscape"]["code"] == "12"
    assert body["provenance"]["productId"] == "soilscapes"
    assert body["caveats"]


def test_landis_soilscapes_area_summary_invalid_input() -> None:
    status, body = _tool("landis_soilscapes.area_summary").call({})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"


def test_landis_soilscapes_area_summary_live_disabled_and_not_found(monkeypatch) -> None:
    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(area=LandisWarehouseDisabled("landis_warehouse_unconfigured")),
    )
    status, body = tools.landis_soilscapes._area_summary({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 501
    assert "WAREHOUSE_DSN" in body["message"]

    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(area=None),
    )
    status, body = tools.landis_soilscapes._area_summary({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 404
    assert body["code"] == "NOT_FOUND"


def test_landis_soilscapes_area_summary_upstream_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(area=LandisWarehouseUnavailable("boom")),
    )
    status, body = _tool("landis_soilscapes.area_summary").call({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 502
    assert body["code"] == "UPSTREAM_CONNECT_ERROR"


def test_landis_derive_pipe_risk_success(monkeypatch) -> None:
    monkeypatch.setattr(
        tools.landis_derive,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(
            pipe={
                "riskBand": "high",
                "scores": {
                    "overall": 4.0,
                    "weightedCorrosion": 3.8,
                    "weightedShrinkSwell": 3.1,
                    "worstCorrosion": 4,
                    "worstShrinkSwell": 3,
                },
                "corrosionClasses": [{"code": "C4", "label": "High", "score": 4, "percent": 70.0}],
                "shrinkSwellClasses": [
                    {"code": "S3", "label": "Moderate", "score": 3, "percent": 70.0}
                ],
                "provenance": {"productId": "pipe-risk", "warehouseBacked": True},
            }
        ),
    )
    status, body = _tool("landis_derive.pipe_risk").call({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 200
    assert body["riskBand"] == "high"
    assert body["rawEvidence"]["corrosionClasses"][0]["code"] == "C4"
    assert body["verificationChecklist"]


def test_landis_derive_pipe_risk_invalid_and_error_paths(monkeypatch) -> None:
    status, body = tools.landis_derive._pipe_risk({})
    assert status == 400
    assert body["code"] == "INVALID_INPUT"

    monkeypatch.setattr(
        tools.landis_derive,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(pipe=LandisWarehouseDisabled("landis_live_disabled")),
    )
    status, body = tools.landis_derive._pipe_risk({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 501
    assert body["code"] == "LIVE_DISABLED"

    monkeypatch.setattr(
        tools.landis_derive,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(pipe=LandisWarehouseUnavailable("boom")),
    )
    status, body = tools.landis_derive._pipe_risk({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 502
    assert body["code"] == "UPSTREAM_CONNECT_ERROR"

    monkeypatch.setattr(
        tools.landis_derive,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(pipe=None),
    )
    status, body = tools.landis_derive._pipe_risk({"bbox": [-1.6, 52.0, -1.4, 52.2]})
    assert status == 404
    assert body["code"] == "NOT_FOUND"


def test_landis_end_to_end_with_admin_area_geometry(monkeypatch) -> None:
    geometry = {
        "type": "Polygon",
        "coordinates": [[[-1.6, 52.0], [-1.4, 52.0], [-1.4, 52.2], [-1.6, 52.2], [-1.6, 52.0]]],
    }
    admin_tool = _tool("admin_lookup.area_geometry")
    original_handler = admin_tool.handler
    admin_tool.handler = lambda _payload: (
        200,
        {"bbox": [-1.6, 52.0, -1.4, 52.2], "geometry": geometry},
    )
    monkeypatch.setattr(
        tools.landis_soilscapes,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(
            area={
                "areaSqM": 1000.0,
                "classes": [
                    {"code": "12", "name": "Freely draining", "areaSqM": 800.0, "percent": 80.0}
                ],
                "dominantClass": {
                    "code": "12",
                    "name": "Freely draining",
                    "areaSqM": 800.0,
                    "percent": 80.0,
                },
                "provenance": {"productId": "soilscapes", "warehouseBacked": True},
            }
        ),
    )
    monkeypatch.setattr(
        tools.landis_derive,
        "get_landis_warehouse",
        lambda: _FakeWarehouse(
            pipe={
                "riskBand": "medium",
                "scores": {
                    "overall": 3.0,
                    "weightedCorrosion": 2.7,
                    "weightedShrinkSwell": 2.5,
                    "worstCorrosion": 3,
                    "worstShrinkSwell": 2,
                },
                "corrosionClasses": [
                    {"code": "C3", "label": "Moderate", "score": 3, "percent": 60.0}
                ],
                "shrinkSwellClasses": [{"code": "S2", "label": "Low", "score": 2, "percent": 60.0}],
                "provenance": {"productId": "pipe-risk", "warehouseBacked": True},
            }
        ),
    )
    try:
        status, admin_body = admin_tool.call({"areaId": "E09000033", "includeGeometry": True})
        assert status == 200
        status, area_body = _tool("landis_soilscapes.area_summary").call(
            {"geometry": admin_body["geometry"]}
        )
        assert status == 200
        status, risk_body = _tool("landis_derive.pipe_risk").call(
            {"geometry": admin_body["geometry"]}
        )
        assert status == 200
        assert area_body["provenance"]["productId"] == "soilscapes"
        assert area_body["caveats"]
        assert risk_body["provenance"]["productId"] == "pipe-risk"
        assert risk_body["verificationChecklist"]
    finally:
        admin_tool.handler = original_handler
