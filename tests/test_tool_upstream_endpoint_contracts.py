from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from server.config import settings
from server.main import app

client = TestClient(app)


def test_os_tool_upstream_url_contracts(monkeypatch):
    from tools import os_common

    calls: list[tuple[str, dict[str, Any] | None, str]] = []

    def fake_get_json(url: str, params: dict[str, Any] | None = None):
        calls.append((url, params, "get_json"))
        if url.endswith("/collections"):
            return 200, {"collections": []}
        if "/collections/" in url and url.endswith("/items"):
            return 200, {"features": []}
        if "/collections/" in url and url.endswith("/queryables"):
            return 200, {"type": "object", "properties": {}}
        if "search/links/v1/identifierTypes/" in url:
            return 200, {"identifiers": []}
        if "/search/links/v1/identifiers/" in url:
            return 200, {"identifiers": []}
        if "/search/links/v1/featureTypes/" in url:
            return 200, {"identifiers": []}
        if "/search/links/v1/productVersionInfo/" in url:
            return 200, {"version": "2026.1"}
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
        if "/downloads/v1/products/" in url and url.endswith("/downloads"):
            return 200, [{"id": "download-1", "fileName": "sample.zip"}]
        if "/downloads/v1/products/" in url:
            return 200, {"id": "openroads", "name": "Open Roads"}
        if url.endswith("/downloads/v1/products"):
            return 200, [{"id": "openroads", "name": "Open Roads"}]
        if url.endswith("/downloads/v1/dataPackages"):
            return 200, [{"id": "pkg-1"}]
        if url.endswith("/maps/vector/ngd/ota/v1/collections"):
            return 200, {"collections": []}
        if url.endswith("/maps/vector/ngd/ota/v1/tilematrixsets"):
            return 200, {"tileMatrixSets": []}
        if url.endswith("/maps/vector/ngd/ota/v1/conformance"):
            return 200, {"conformsTo": []}
        if url.endswith("/positioning/osnet/v1/rinex"):
            return 200, {"years": [2025]}
        if "/positioning/osnet/v1/stations/" in url:
            return 200, {"id": "AMER"}
        return 200, {"results": [{"DPA": {"UPRN": "1", "ADDRESS": "A", "LAT": 51.5, "LNG": -0.1}}]}

    def fake_post_json(
        url: str,
        body: dict[str, Any] | None = None,  # noqa: ARG001
        params: dict[str, Any] | None = None,
    ):
        calls.append((url, params, "post_json"))
        return 200, {"results": [{"DPA": {"UPRN": "2", "ADDRESS": "B", "LAT": 51.6, "LNG": -0.2}}]}

    def fake_get_bytes(url: str, params: dict[str, Any] | None = None):
        calls.append((url, params, "get_bytes"))
        if "stations/AMER/log" in url:
            content_type = "text/plain"
            content = b"log line"
        elif "zxy/" in url:
            content_type = "image/png"
            content = b"\x89PNG\r\n\x1a\n"
        else:
            content_type = "application/xml"
            content = b"<xml/>"
        return 200, {"contentType": content_type, "content": content}

    monkeypatch.setattr(os_common.client, "api_key", "test-key", raising=False)
    monkeypatch.setattr(os_common.client, "get_json", fake_get_json, raising=True)
    monkeypatch.setattr(os_common.client, "post_json", fake_post_json, raising=True)
    monkeypatch.setattr(os_common.client, "get_bytes", fake_get_bytes, raising=True)

    payloads = [
        {"tool": "os_places.by_postcode", "postcode": "SW1A 2AA"},
        {"tool": "os_places.search", "text": "Example"},
        {"tool": "os_places.by_uprn", "uprn": "1"},
        {"tool": "os_places.nearest", "lat": 51.5, "lon": -0.1},
        {"tool": "os_places.within", "bbox": [-0.2, 51.5, -0.1, 51.6]},
        {"tool": "os_places.radius", "lat": 51.5, "lon": -0.1, "radiusMeters": 100},
        {
            "tool": "os_places.polygon",
            "polygon": [[-0.2, 51.5], [-0.1, 51.5], [-0.1, 51.6], [-0.2, 51.6], [-0.2, 51.5]],
        },
        {"tool": "os_poi.search", "text": "cafe"},
        {"tool": "os_poi.nearest", "lat": 51.5, "lon": -0.1},
        {"tool": "os_poi.within", "bbox": [-0.2, 51.5, -0.1, 51.6]},
        {"tool": "os_names.find", "text": "London"},
        {"tool": "os_features.query", "collection": "buildings", "bbox": [-0.2, 51.5, -0.1, 51.6]},
        {"tool": "os_features.collections"},
        {"tool": "os_features.wfs_capabilities"},
        {"tool": "os_features.wfs_archive_capabilities"},
        {"tool": "os_linked_ids.get", "identifier": "100021892956"},
        {"tool": "os_linked_ids.identifiers", "identifier": "100021892956"},
        {
            "tool": "os_linked_ids.feature_types",
            "featureType": "RoadLink",
            "identifier": "osgb5000005158744708",
        },
        {
            "tool": "os_linked_ids.product_version_info",
            "correlationMethod": "BLPU_UPRN_RoadLink_TOID_9",
        },
        {"tool": "os_maps.wmts_capabilities"},
        {"tool": "os_maps.raster_tile", "style": "Road_3857", "z": 7, "x": 63, "y": 42},
        {"tool": "os_qgis.vector_tile_profile", "style": "OS_VTS_3857_Light"},
        {
            "tool": "os_qgis.export_geopackage_descriptor",
            "sourceResourceUri": "resource://mcp-geo/os-exports/demo.json",
        },
        {"tool": "os_tiles_ota.collections"},
        {"tool": "os_tiles_ota.tilematrixsets"},
        {"tool": "os_tiles_ota.conformance"},
        {"tool": "os_net.rinex_years"},
        {"tool": "os_net.station_get", "stationId": "AMER"},
        {"tool": "os_net.station_log", "stationId": "AMER"},
        {"tool": "os_downloads.list_products"},
        {"tool": "os_downloads.get_product", "productId": "openroads"},
        {"tool": "os_downloads.list_product_downloads", "productId": "openroads"},
        {"tool": "os_downloads.list_data_packages"},
        {"tool": "os_downloads.prepare_export", "productId": "openroads"},
    ]
    for payload in payloads:
        resp = client.post("/tools/call", json=payload)
        assert resp.status_code == 200, payload

    prepare_resp = client.post(
        "/tools/call", json={"tool": "os_downloads.prepare_export", "productId": "openroads"}
    )
    assert prepare_resp.status_code == 200
    export_id = prepare_resp.json().get("exportId")
    assert isinstance(export_id, str) and export_id
    get_export_resp = client.post(
        "/tools/call", json={"tool": "os_downloads.get_export", "exportId": export_id}
    )
    assert get_export_resp.status_code == 200

    urls = [url for url, _, _ in calls]
    assert any(url.endswith("/search/places/v1/postcode") for url in urls)
    assert any(url.endswith("/search/places/v1/find") for url in urls)
    assert any(url.endswith("/search/places/v1/uprn") for url in urls)
    assert any(url.endswith("/search/places/v1/nearest") for url in urls)
    assert any(url.endswith("/search/places/v1/bbox") for url in urls)
    assert any(url.endswith("/search/places/v1/radius") for url in urls)
    assert any(url.endswith("/search/places/v1/polygon") for url in urls)
    assert any(
        url.endswith("/search/places/v1/polygon") and method == "post_json"
        for url, _params, method in calls
    )
    assert any(url.endswith("/search/names/v1/find") for url in urls)
    assert any(
        url.endswith("/features/ngd/ofa/v1/collections/bld-fts-buildingpart-2/items")
        for url in urls
    )
    assert any(url.endswith("/features/ngd/ofa/v1/collections") for url in urls)
    assert any("/search/links/v1/identifierTypes/uprn/100021892956" in url for url in urls)
    assert any("/search/links/v1/identifiers/100021892956" in url for url in urls)
    assert any("/search/links/v1/featureTypes/RoadLink/osgb5000005158744708" in url for url in urls)
    assert any("/search/links/v1/productVersionInfo/BLPU_UPRN_RoadLink_TOID_9" in url for url in urls)
    assert any(url.endswith("/features/v1/wfs") for url in urls)
    assert any(url.endswith("/features/v1/wfs/archive") for url in urls)
    assert any(url.endswith("/maps/raster/v1/wmts") for url in urls)
    assert any(url.endswith("/maps/raster/v1/zxy/Road_3857/7/63/42.png") for url in urls)
    assert any(url.endswith("/maps/vector/ngd/ota/v1/collections") for url in urls)
    assert any(url.endswith("/maps/vector/ngd/ota/v1/tilematrixsets") for url in urls)
    assert any(url.endswith("/maps/vector/ngd/ota/v1/conformance") for url in urls)
    assert any(url.endswith("/positioning/osnet/v1/rinex") for url in urls)
    assert any(url.endswith("/positioning/osnet/v1/stations/AMER") for url in urls)
    assert any(url.endswith("/positioning/osnet/v1/stations/AMER/log") for url in urls)
    assert any(url.endswith("/downloads/v1/products") for url in urls)
    assert any(url.endswith("/downloads/v1/products/openroads") for url in urls)
    assert any(url.endswith("/downloads/v1/products/openroads/downloads") for url in urls)
    assert any(url.endswith("/downloads/v1/dataPackages") for url in urls)

    postcode_params = next(
        params for url, params, _ in calls if url.endswith("/search/places/v1/postcode")
    )
    assert postcode_params == {"postcode": "SW1A2AA", "output_srs": "WGS84"}

    nearest_params = next(
        params for url, params, _ in calls if url.endswith("/search/places/v1/nearest")
    )
    assert nearest_params == {"point": "51.5,-0.1", "srs": "WGS84", "output_srs": "WGS84"}

    bbox_params = next(params for url, params, _ in calls if url.endswith("/search/places/v1/bbox"))
    assert bbox_params.get("srs") == "WGS84"
    assert bbox_params.get("output_srs") == "WGS84"
    bbox_parts = [float(part) for part in str(bbox_params.get("bbox", "")).split(",")]
    assert len(bbox_parts) == 4

    poi_calls = [
        (url, params)
        for url, params, _ in calls
        if isinstance(params, dict) and params.get("dataset") == "DPA,LPI"
    ]
    assert any(url.endswith("/search/places/v1/find") for url, _ in poi_calls)
    assert any(url.endswith("/search/places/v1/nearest") for url, _ in poi_calls)
    assert any(url.endswith("/search/places/v1/bbox") for url, _ in poi_calls)


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
                "items": [{"id": "gdp-to-four-decimal-places", "state": "published", "links": {}}],
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
        if url.endswith("/datasets/gdp-to-four-decimal-places/editions"):
            return 200, [{"edition": "time-series", "state": "published"}]
        if url.endswith("/datasets/gdp-to-four-decimal-places/editions/time-series/versions"):
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
        url.endswith("/datasets/gdp-to-four-decimal-places/editions/time-series/versions/1/observations")
        for url in json_urls
    )
    observation_params = next(
        params
        for url, params in json_calls
        if url.endswith("/datasets/gdp-to-four-decimal-places/editions/time-series/versions/1/observations")
    )
    assert isinstance(observation_params, dict)
    assert observation_params["limit"] == 500
    assert observation_params["page"] == 1
    assert any(
        url.endswith("/datasets/gdp-to-four-decimal-places/editions/time-series/versions/1")
        for url in json_urls
    )
    assert any(
        url.endswith(
            "/datasets/gdp-to-four-decimal-places/editions/time-series/versions/1/dimensions/time/options"
        )
        for url in (json_urls + page_urls)
    )
    assert any(url.endswith("/datasets/gdp-to-four-decimal-places/editions") for url in page_urls)
    assert any(
        url.endswith("/datasets/gdp-to-four-decimal-places/editions/time-series/versions")
        for url in page_urls
    )
    assert any(
        url.endswith(
            "/datasets/gdp-to-four-decimal-places/editions/time-series/versions/1/dimensions/time/options"
        )
        for url in page_urls
    )

    search_params = next(params for url, params in json_calls if url.endswith("/datasets"))
    assert search_params == {"limit": 500, "offset": 0}


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
