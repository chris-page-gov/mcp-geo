from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app

client = TestClient(app)


def test_os_tool_upstream_url_contracts(monkeypatch):
    from tools import os_common

    calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get_json(url: str, params: dict[str, Any] | None = None):
        calls.append((url, params))
        if url.endswith("/collections"):
            return 200, {"collections": []}
        if "/collections/" in url and url.endswith("/items"):
            return 200, {"features": []}
        if "search/links/v1/identifierTypes/" in url:
            return 200, {"identifiers": []}
        if "search/names/v1/find" in url:
            return 200, {
                "results": [
                    {
                        "GAZETTEER_ENTRY": {
                            "ID": "X1",
                            "NAME1": "Example",
                            "TYPE": "Town",
                            "LOCAL_TYPE": "Town",
                            "GEOMETRY": {"LAT": 51.5, "LNG": -0.1},
                        }
                    }
                ]
            }
        return 200, {"results": [{"DPA": {"UPRN": "1", "ADDRESS": "A", "LAT": 51.5, "LNG": -0.1}}]}

    monkeypatch.setattr(os_common.client, "api_key", "test-key", raising=False)
    monkeypatch.setattr(os_common.client, "get_json", fake_get_json, raising=True)

    payloads = [
        {"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"},
        {"tool": "os_places.search", "text": "Example"},
        {"tool": "os_places.by_uprn", "uprn": "1"},
        {"tool": "os_places.nearest", "lat": 51.5, "lon": -0.1},
        {"tool": "os_places.within", "bbox": [-0.2, 51.5, -0.1, 51.6]},
        {"tool": "os_names.find", "text": "London"},
        {"tool": "os_features.query", "collection": "buildings", "bbox": [-0.2, 51.5, -0.1, 51.6]},
        {"tool": "os_features.collections"},
        {"tool": "os_linked_ids.get", "identifier": "100021892956"},
    ]
    for payload in payloads:
        resp = client.post("/tools/call", json=payload)
        assert resp.status_code == 200, payload

    urls = [url for url, _ in calls]
    assert any(url.endswith("/search/places/v1/postcode") for url in urls)
    assert any(url.endswith("/search/places/v1/find") for url in urls)
    assert any(url.endswith("/search/places/v1/uprn") for url in urls)
    assert any(url.endswith("/search/places/v1/nearest") for url in urls)
    assert any(url.endswith("/search/places/v1/bbox") for url in urls)
    assert any(url.endswith("/search/names/v1/find") for url in urls)
    assert any(url.endswith("/features/ngd/ofa/v1/collections/buildings/items") for url in urls)
    assert any(url.endswith("/features/ngd/ofa/v1/collections") for url in urls)
    assert any("/search/links/v1/identifierTypes/uprn/100021892956" in url for url in urls)

    postcode_params = next(
        params for url, params in calls if url.endswith("/search/places/v1/postcode")
    )
    assert postcode_params == {"postcode": "SW1A2AA", "output_srs": "WGS84"}

    nearest_params = next(
        params for url, params in calls if url.endswith("/search/places/v1/nearest")
    )
    assert nearest_params == {"point": "51.5,-0.1", "srs": "WGS84", "output_srs": "WGS84"}

    bbox_params = next(params for url, params in calls if url.endswith("/search/places/v1/bbox"))
    assert bbox_params.get("srs") == "WGS84"
    assert bbox_params.get("output_srs") == "WGS84"
    bbox_parts = [float(part) for part in str(bbox_params.get("bbox", "")).split(",")]
    assert len(bbox_parts) == 4


def test_ons_tool_upstream_url_contracts(monkeypatch):
    from tools import ons_codes, ons_data, ons_search

    monkeypatch.setattr(settings, "ONS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ONS_SEARCH_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "ONS_DATASET_CACHE_ENABLED", False, raising=False)

    json_calls: list[tuple[str, dict[str, Any] | None]] = []
    page_calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get_json(
        url: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,  # noqa: ARG001
    ):
        json_calls.append((url, params))
        if url.endswith("/datasets"):
            return 200, {
                "items": [{"id": "gdp", "state": "published", "links": {}}],
                "offset": params.get("offset", 0) if isinstance(params, dict) else 0,
                "limit": params.get("limit", 5) if isinstance(params, dict) else 5,
                "total_count": 1,
            }
        if url.endswith("/observations"):
            return 200, {"observations": [{"value": 1}], "total": 1}
        if "/versions/1" in url and "/dimensions/" not in url and not url.endswith("/versions"):
            return 200, {"dimensions": [{"id": "time"}, {"id": "geography"}]}
        if url.endswith("/dimensions/time/options"):
            return 200, {"items": [{"id": "2024 Q1"}]}
        if url.endswith("/dimensions/geography/options"):
            return 200, {"items": [{"id": "E09000001"}]}
        return 200, {"items": []}

    def fake_get_all_pages(
        url: str,
        params: dict[str, Any] | None = None,
        item_key: str = "items",  # noqa: ARG001
    ):
        page_calls.append((url, params))
        if url.endswith("/datasets/gdp/editions"):
            return 200, [{"edition": "time-series", "state": "published"}]
        if url.endswith("/datasets/gdp/editions/time-series/versions"):
            return 200, [{"version": "1", "state": "published"}]
        if url.endswith("/dimensions/time/options"):
            return 200, [{"id": "2024 Q1"}]
        return 200, []

    monkeypatch.setattr(ons_data.ons_client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(ons_data.ons_client, "get_all_pages", fake_get_all_pages, raising=True)
    monkeypatch.setattr(ons_search._SEARCH_CLIENT, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_get_all_pages, raising=True)

    payloads = [
        {"tool": "ons_search.query", "term": "gdp", "limit": 5, "offset": 0},
        {
            "tool": "ons_data.query",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "geography": "E09000001",
            "measure": "value",
        },
        {
            "tool": "ons_data.dimensions",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
        },
        {"tool": "ons_data.editions", "dataset": "gdp"},
        {"tool": "ons_data.versions", "dataset": "gdp", "edition": "time-series"},
        {"tool": "ons_codes.list", "dataset": "gdp", "edition": "time-series", "version": "1"},
        {
            "tool": "ons_codes.options",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "dimension": "time",
        },
    ]
    for payload in payloads:
        resp = client.post("/tools/call", json=payload)
        assert resp.status_code == 200, payload

    json_urls = [url for url, _ in json_calls]
    page_urls = [url for url, _ in page_calls]

    assert any(url.endswith("/datasets") for url in json_urls)
    assert any(
        url.endswith("/datasets/gdp/editions/time-series/versions/1/observations")
        for url in json_urls
    )
    assert any(url.endswith("/datasets/gdp/editions/time-series/versions/1") for url in json_urls)
    assert any(
        url.endswith("/datasets/gdp/editions/time-series/versions/1/dimensions/time/options")
        for url in json_urls
    )
    assert any(url.endswith("/datasets/gdp/editions") for url in page_urls)
    assert any(url.endswith("/datasets/gdp/editions/time-series/versions") for url in page_urls)
    assert any(
        url.endswith("/datasets/gdp/editions/time-series/versions/1/dimensions/time/options")
        for url in page_urls
    )

    search_params = next(params for url, params in json_calls if url.endswith("/datasets"))
    assert search_params == {"search": "gdp", "limit": 5, "offset": 0}


def test_nomis_tool_upstream_url_contracts(monkeypatch):
    from tools import nomis_data

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    calls: list[tuple[str, dict[str, Any] | None]] = []

    def fake_get_json(
        url: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,  # noqa: ARG001
    ):
        calls.append((url, params))
        if url.endswith("/dataset/def.sdmx.json"):
            return 200, {
                "structure": {
                    "keyfamilies": {"keyfamily": [{"id": "NM_1_1", "name": "Example dataset"}]}
                }
            }
        if "/dataset/NM_1_1/def.sdmx.json" in url:
            return 200, {
                "structure": {
                    "keyfamilies": {"keyfamily": [{"id": "NM_1_1", "name": "Example dataset"}]}
                }
            }
        if "dataset/NM_1_1.overview.json" in url:
            return 200, {"overview": {"dimensions": {"dimension": []}}}
        if url.endswith("/concept/GEOGRAPHY.def.sdmx.json"):
            return 200, {"structure": {}}
        if url.endswith("/codelist/CL_1_1_SEX.def.sdmx.json"):
            return 200, {"structure": {}}
        if url.endswith("/dataset/NM_1_1.jsonstat.json"):
            return 200, {"dataset": {"value": []}}
        return 200, {}

    monkeypatch.setattr(nomis_data.nomis_client, "get_json", fake_get_json, raising=True)

    payloads = [
        {"tool": "nomis.datasets"},
        {"tool": "nomis.datasets", "dataset": "NM_1_1"},
        {"tool": "nomis.concepts", "concept": "GEOGRAPHY"},
        {"tool": "nomis.codelists", "codelist": "CL_1_1_SEX"},
        {
            "tool": "nomis.query",
            "dataset": "NM_1_1",
            "format": "jsonstat",
            "params": {"time": "2021"},
        },
    ]
    for payload in payloads:
        resp = client.post("/tools/call", json=payload)
        assert resp.status_code == 200, payload

    urls = [url for url, _ in calls]
    assert any(url.endswith("/dataset/def.sdmx.json") for url in urls)
    assert any(url.endswith("/dataset/NM_1_1/def.sdmx.json") for url in urls)
    assert any("dataset/NM_1_1.overview.json" in url for url in urls)
    assert any(url.endswith("/concept/GEOGRAPHY.def.sdmx.json") for url in urls)
    assert any(url.endswith("/codelist/CL_1_1_SEX.def.sdmx.json") for url in urls)
    assert any(url.endswith("/dataset/NM_1_1.jsonstat.json") for url in urls)


def test_admin_lookup_upstream_url_contracts(monkeypatch):
    from tools import admin_lookup

    monkeypatch.setattr(settings, "ADMIN_LOOKUP_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(admin_lookup, "get_boundary_cache", lambda: None)

    calls: list[tuple[str, dict[str, Any]]] = []

    def fake_get_json(url: str, params: dict[str, Any]):
        calls.append((url, params))
        source = next((item for item in admin_lookup.ADMIN_SOURCES if item.service in url), None)
        if source is None:
            return 200, {"features": []}
        return 200, {
            "features": [
                {
                    "attributes": {
                        source.id_field: f"{source.level}_ID",
                        source.name_field: f"{source.level} Name",
                    }
                }
            ]
        }

    monkeypatch.setattr(admin_lookup._ARCGIS_CLIENT, "get_json", fake_get_json, raising=True)

    resp = client.post(
        "/tools/call",
        json={"tool": "admin_lookup.containing_areas", "lat": 51.5, "lon": -0.1},
    )
    assert resp.status_code == 200
    assert resp.json().get("live") is True

    assert len(calls) == len(admin_lookup.ADMIN_SOURCES)
    for url, params in calls:
        assert url.endswith("/FeatureServer/0/query")
        assert params.get("f") == "json"
        assert params.get("geometryType") == "esriGeometryPoint"
        assert params.get("spatialRel") == "esriSpatialRelIntersects"
        assert params.get("geometry") == "-0.1,51.5"
