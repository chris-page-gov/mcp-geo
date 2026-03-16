from typing import Any

from tools import admin_lookup


class DummyResp:
    def __init__(self, status_code: int, payload: dict[str, Any]):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


def _patch_admin_sources(monkeypatch):
    source = admin_lookup.AdminSource(
        level="TEST",
        service="ExampleService",
        id_field="TEST_ID",
        name_field="TEST_NAME",
        lat_field="LAT",
        lon_field="LON",
    )
    monkeypatch.setattr(admin_lookup, "ADMIN_SOURCES", [source])
    monkeypatch.setattr(admin_lookup, "LEVEL_ORDER", [source.level])
    monkeypatch.setattr(admin_lookup, "LEVEL_INDEX", {source.level: 0})
    return source


def _patch_admin_sources_multi(monkeypatch):
    sources = [
        admin_lookup.AdminSource(
            level="TEST_A",
            service="ExampleServiceA",
            id_field="ID_A",
            name_field="NAME_A",
            lat_field="LAT",
            lon_field="LON",
        ),
        admin_lookup.AdminSource(
            level="TEST_B",
            service="ExampleServiceB",
            id_field="ID_B",
            name_field="NAME_B",
            lat_field="LAT",
            lon_field="LON",
        ),
    ]
    monkeypatch.setattr(admin_lookup, "ADMIN_SOURCES", sources)
    monkeypatch.setattr(admin_lookup, "LEVEL_ORDER", [source.level for source in sources])
    monkeypatch.setattr(
        admin_lookup,
        "LEVEL_INDEX",
        {source.level: idx for idx, source in enumerate(sources)},
    )
    return sources


def test_arcgis_client_caches_success(monkeypatch):
    client = admin_lookup._ArcGisClient()
    calls = {"count": 0}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        return DummyResp(200, {"features": []})

    monkeypatch.setattr(admin_lookup.requests, "get", fake_get)
    status1, data1 = client.get_json("http://example", {"q": "x"})
    status2, data2 = client.get_json("http://example", {"q": "x"})
    assert status1 == 200 and data1 == {"features": []}
    assert status2 == 200 and data2 == {"features": []}
    assert calls["count"] == 1


def test_arcgis_client_retries_on_timeout(monkeypatch):
    client = admin_lookup._ArcGisClient()
    calls = {"count": 0}

    def fake_get(url, params, timeout):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] == 1:
            raise admin_lookup.req_exc.Timeout("boom")
        return DummyResp(200, {"features": []})

    monkeypatch.setattr(admin_lookup.requests, "get", fake_get)
    status, data = client.get_json("http://example", {"q": "y"})
    assert status == 200
    assert data == {"features": []}
    assert calls["count"] == 2


def test_arcgis_client_invalid_json_returns_error(monkeypatch):
    client = admin_lookup._ArcGisClient()

    class BadResp:
        status_code = 200
        text = "nope"

        def json(self) -> dict[str, Any]:
            raise ValueError("boom json parse")

    def fake_get(url, params, timeout):  # noqa: ARG001
        return BadResp()

    monkeypatch.setattr(admin_lookup.requests, "get", fake_get)
    status, data = client.get_json("http://example", {"q": "x"})
    assert status == 502
    assert data["code"] == "UPSTREAM_INVALID_RESPONSE"


def test_live_find_by_name_builds_results(monkeypatch):
    _patch_admin_sources(monkeypatch)
    captured = {}

    def fake_fetch(url, params):
        captured["where"] = params.get("where")
        return {
            "features": [
                {"attributes": {"TEST_ID": "X1", "TEST_NAME": "Example Name"}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_find_by_name("Example", limit=5)
    assert results == [{"id": "X1", "level": "TEST", "name": "Example Name"}]
    assert "UPPER(TEST_NAME) LIKE '%EXAMPLE%'" in captured["where"]


def test_live_find_by_name_with_levels_and_match(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)
    captured = []

    def fake_fetch(url, params):  # noqa: ARG001
        captured.append(params.get("where"))
        if "ExampleServiceA" in url:
            return {"features": [{"attributes": {"ID_A": "X1", "NAME_A": "Warwick"}}]}
        return {"features": [{"attributes": {"ID_B": "X2", "NAME_B": "North Warwickshire"}}]}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_find_by_name(
        "Warwick",
        limit=5,
        levels=["TEST_A"],
        match="starts_with",
    )
    assert results == [{"id": "X1", "level": "TEST_A", "name": "Warwick"}]
    assert captured and "LIKE 'WARWICK%'" in captured[0]


def test_live_containing_areas_builds_chain(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):
        assert params["geometry"] == "-0.1,51.5"
        return {
            "features": [
                {"attributes": {"TEST_ID": "X2", "TEST_NAME": "Example Area"}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results, meta = admin_lookup._live_containing_areas(51.5, -0.1)
    assert results == [{"id": "X2", "level": "TEST", "name": "Example Area"}]
    assert meta == {
        "source": "arcgis",
        "partial": False,
        "failedSources": None,
        "allFailed": False,
    }


def test_live_area_geometry_returns_bbox(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return {"extent": {"xmin": 0, "ymin": 1, "xmax": 2, "ymax": 3}}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    bbox, meta, geometry = admin_lookup._live_area_geometry("X3")
    assert bbox == [0.0, 1.0, 2.0, 3.0]
    assert meta == {
        "level": "TEST",
        "source": "arcgis",
        "partial": False,
        "failedSources": None,
        "allFailed": False,
    }
    assert geometry is None


def test_live_area_geometry_computes_bbox_from_geometry(monkeypatch):
    _patch_admin_sources(monkeypatch)
    geometry = {"rings": [[[0, 0], [2, 0], [2, 1], [0, 1], [0, 0]]]}

    def fake_fetch(url, params):  # noqa: ARG001
        return {"features": [{"geometry": geometry}]}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    bbox, meta, returned_geometry = admin_lookup._live_area_geometry("X3", include_geometry=True)
    assert bbox == [0.0, 0.0, 2.0, 1.0]
    assert meta == {
        "level": "TEST",
        "source": "arcgis",
        "partial": False,
        "failedSources": None,
        "allFailed": False,
    }
    assert returned_geometry == geometry


def test_live_find_by_name_skips_failed_sources(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)
    calls = {"count": 0}

    def fake_fetch(url, params):  # noqa: ARG001
        calls["count"] += 1
        if "ExampleServiceA" in url:
            return None
        return {"features": [{"attributes": {"ID_B": "X5", "NAME_B": "Example Name"}}]}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_find_by_name("Example", limit=5)
    assert results == [{"id": "X5", "level": "TEST_B", "name": "Example Name"}]
    assert calls["count"] == 2


def test_normalize_levels_and_infer():
    assert admin_lookup._normalize_levels("ward, lsoa, nope") == ["WARD", "LSOA"]
    assert admin_lookup._normalize_levels(["msoa", "WARD"]) == ["MSOA", "WARD"]
    assert admin_lookup._normalize_levels(123) is None
    assert admin_lookup._infer_levels_from_text("LSOA unemployment rate") == ["LSOA"]
    assert admin_lookup._infer_levels_from_text("MSOA population") == ["MSOA"]
    assert admin_lookup._infer_levels_from_text("OA boundary") == ["OA"]
    assert admin_lookup._infer_levels_from_text("Ward boundary") == ["WARD"]
    assert admin_lookup._infer_levels_from_text("District council list") == ["DISTRICT"]
    assert admin_lookup._infer_levels_from_text("County services") == ["COUNTY"]
    assert admin_lookup._infer_levels_from_text("UK region data") == ["REGION"]
    assert admin_lookup._infer_levels_from_text("Nationwide statistics") == ["NATION"]


def test_ordered_sources_respects_levels(monkeypatch):
    sources = _patch_admin_sources_multi(monkeypatch)
    ordered = admin_lookup._ordered_sources(["TEST_B", "TEST_A"])
    assert [source.level for source in ordered] == ["TEST_B", "TEST_A"]
    filtered = admin_lookup._ordered_sources(["TEST_A"])
    assert [source.level for source in filtered] == ["TEST_A"]
    monkeypatch.setattr(admin_lookup, "ADMIN_SOURCES", [])
    assert admin_lookup._ordered_sources(["TEST_A"]) == []


def test_score_match_prioritizes_exact_name():
    exact = admin_lookup._score_match("Warwick", "WARWICK", "WARD")
    partial = admin_lookup._score_match("North Warwickshire", "WARWICK", "DISTRICT")
    assert exact < partial


def test_live_containing_areas_skips_failed_sources(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)
    calls = {"count": 0}

    def fake_fetch(url, params):  # noqa: ARG001
        calls["count"] += 1
        if "ExampleServiceA" in url:
            return None
        return {"features": [{"attributes": {"ID_B": "X6", "NAME_B": "Example Area"}}]}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results, meta = admin_lookup._live_containing_areas(51.5, -0.1)
    assert results == [{"id": "X6", "level": "TEST_B", "name": "Example Area"}]
    assert meta["partial"] is True
    assert meta["failedSources"] == ["ExampleServiceA"]
    assert calls["count"] == 2


def test_live_area_geometry_skips_failed_sources(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)
    calls = {"count": 0}

    def fake_fetch(url, params):  # noqa: ARG001
        calls["count"] += 1
        if "ExampleServiceA" in url:
            return None
        return {"extent": {"xmin": 1, "ymin": 2, "xmax": 3, "ymax": 4}}

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    bbox, meta, geometry = admin_lookup._live_area_geometry("X7")
    assert bbox == [1.0, 2.0, 3.0, 4.0]
    assert meta == {
        "level": "TEST_B",
        "source": "arcgis",
        "partial": True,
        "failedSources": ["ExampleServiceA"],
        "allFailed": False,
    }
    assert geometry is None
    assert calls["count"] == 2


def test_live_containing_areas_all_failed(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return None

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results, meta = admin_lookup._live_containing_areas(51.5, -0.1)
    assert results is None
    assert meta["allFailed"] is True
    assert meta["failedSources"] == ["ExampleServiceA", "ExampleServiceB"]


def test_live_area_geometry_all_failed(monkeypatch):
    _patch_admin_sources_multi(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return None

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    bbox, meta, geometry = admin_lookup._live_area_geometry("X8")
    assert bbox is None
    assert geometry is None
    assert meta["code"] == "ERROR"
    assert meta["allFailed"] is True
    assert meta["failedSources"] == ["ExampleServiceA", "ExampleServiceB"]


def test_live_find_by_id_returns_match(monkeypatch):
    _patch_admin_sources(monkeypatch)

    def fake_fetch(url, params):  # noqa: ARG001
        return {
            "features": [
                {"attributes": {"TEST_ID": "X4", "TEST_NAME": "Example", "LAT": 10, "LON": -1}},
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    hit, err = admin_lookup._live_find_by_id("X4")
    assert err is None
    assert hit == {"id": "X4", "level": "TEST", "name": "Example", "lat": 10, "lon": -1}


def test_default_admin_sources_use_current_ward_and_district_vintages():
    ward = next(source for source in admin_lookup.ADMIN_SOURCES if source.level == "WARD")
    district = next(source for source in admin_lookup.ADMIN_SOURCES if source.level == "DISTRICT")

    assert ward.service == "Wards_December_2024_Boundaries_UK_BGC"
    assert ward.id_field == "WD24CD"
    assert ward.name_field == "WD24NM"

    assert district.service == "Local_Authority_Districts_December_2024_Boundaries_UK_BGC"
    assert district.id_field == "LAD24CD"
    assert district.name_field == "LAD24NM"


def test_live_find_by_name_returns_current_harold_wood_ward(monkeypatch):
    def fake_fetch(url, params):  # noqa: ARG001
        assert "Wards_December_2024_Boundaries_UK_BGC" in url
        assert params["where"] == "UPPER(WD24NM) = 'HAROLD WOOD'"
        return {
            "features": [
                {
                    "attributes": {
                        "WD24CD": "E05013973",
                        "WD24NM": "Harold Wood",
                    }
                }
            ]
        }

    monkeypatch.setattr(admin_lookup, "_fetch_arcgis", fake_fetch)
    results = admin_lookup._live_find_by_name(
        "Harold Wood",
        limit=5,
        levels=["WARD"],
        match="exact",
    )
    assert results == [{"id": "E05013973", "level": "WARD", "name": "Harold Wood"}]
