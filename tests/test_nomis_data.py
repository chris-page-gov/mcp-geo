from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient

from server.main import app


client = TestClient(app)


def test_nomis_live_disabled(monkeypatch):
    from server import config

    monkeypatch.setattr(config.settings, "NOMIS_LIVE_ENABLED", False)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 501
    assert resp.json()["code"] == "LIVE_DISABLED"
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 501
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 501
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1"})
    assert resp.status_code == 501


def test_nomis_query_success(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        return 200, {"dataset": "NM_1_1", "value": 123}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.query", "dataset": "NM_1_1", "params": {"geography": "TYPE499"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["live"] is True
    assert body["data"]["value"] == 123


def test_nomis_query_normalizes_date_and_drops_cell_for_jsonstat(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        if url.endswith(
            "/dataset/NM_17_5.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
        ):
            return 200, {"overview": {"dimensions": {"dimension": []}}}
        assert url.endswith("/dataset/NM_17_5.jsonstat.json")
        params = params or {}
        assert params.get("time") == "latest"
        assert "date" not in params
        assert "cell" not in params
        return 200, {"dataset": "NM_17_5", "value": 321}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_17_5",
            "params": {
                "geography": "E07000222",
                "date": "latest",
                "cell": "0",
                "variable": "1",
                "measures": "20599",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"] == 321
    assert "paramNormalization" in body["queryAdjusted"]


def test_nomis_query_resolves_gss_geography_ids(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    overview = {
        "overview": {
            "dimensions": {
                "dimension": [
                    {"concept": "time", "codes": {"code": [{"value": "2021"}]}},
                    {
                        "concept": "geography",
                        "types": {
                            "type": [
                                {"name": "2022 wards", "value": "TYPE153"},
                            ]
                        },
                    },
                    {
                        "concept": "c2021_restype_3",
                        "codes": {"code": [{"value": "0"}]},
                    },
                    {
                        "concept": "measures",
                        "codes": {"code": [{"value": "20100"}]},
                    },
                ]
            }
        }
    }

    def geo_def(value: int, gss: str, name: str) -> Dict[str, Any]:
        return {
            "structure": {
                "codelists": {
                    "codelist": [
                        {
                            "code": [
                                {
                                    "value": value,
                                    "description": {"value": name},
                                    "annotations": {
                                        "annotation": [
                                            {"annotationtitle": "GeogCode", "annotationtext": gss},
                                            {"annotationtitle": "TypeCode", "annotationtext": 297},
                                            {"annotationtitle": "TypeName", "annotationtext": "Wards"},
                                        ]
                                    },
                                }
                            ]
                        }
                    ]
                }
            }
        }

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        params = params or {}
        if url.endswith(
            "/dataset/NM_2021_1.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
        ):
            return 200, overview
        if url.endswith("/dataset/NM_2021_1/geography/TYPE153.def.sdmx.json"):
            search = params.get("search")
            if search == "E05012621":
                return 200, geo_def(641733691, "E05012621", "Leamington Brunswick")
            if search == "E05012622":
                return 200, geo_def(641733692, "E05012622", "Leamington Clarendon")
            return 200, geo_def(0, str(search), "Unknown")
        if url.endswith("/dataset/NM_2021_1.jsonstat.json"):
            assert params.get("geography") == "641733691,641733692"
            return 200, {"value": 123}
        return 500, {"error": f"Unexpected URL {url}"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_2021_1",
            "params": {"geography": "E05012621,E05012622", "measures": "20100"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"] == 123
    assert body["queryAdjusted"]["geographyResolvedFromGss"] is True
    assert body["queryAdjusted"]["originalGeography"] == "E05012621,E05012622"
    assert body["queryAdjusted"]["resolvedGeography"] == "641733691,641733692"
    resolution = body["queryAdjusted"]["geographyResolution"]
    assert resolution["level"] == "WARD"
    assert resolution["usedDatasetTypeLookup"] is True
    assert resolution["usedLegacyLookup"] is False


def test_nomis_query_resolves_legacy_ward_gss_by_name_fallback(monkeypatch):
    from tools import nomis_common, nomis_data
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    overview = {
        "overview": {
            "dimensions": {
                "dimension": [
                    {"concept": "time", "codes": {"code": [{"value": "2021"}]}},
                    {
                        "concept": "geography",
                        "types": {
                            "type": [
                                {"name": "2022 wards", "value": "TYPE153"},
                            ]
                        },
                    },
                    {
                        "concept": "c2021_restype_3",
                        "codes": {"code": [{"value": "0"}]},
                    },
                    {
                        "concept": "measures",
                        "codes": {"code": [{"value": "20100"}]},
                    },
                ]
            }
        }
    }

    def geo_def(value: int, gss: str, name: str) -> Dict[str, Any]:
        return {
            "structure": {
                "codelists": {
                    "codelist": [
                        {
                            "code": [
                                {
                                    "value": value,
                                    "description": {"value": name},
                                    "annotations": {
                                        "annotation": [
                                            {"annotationtitle": "GeogCode", "annotationtext": gss},
                                            {"annotationtitle": "TypeCode", "annotationtext": 153},
                                            {
                                                "annotationtitle": "TypeName",
                                                "annotationtext": "2022 wards",
                                            },
                                        ]
                                    },
                                }
                            ]
                        }
                    ]
                }
            }
        }

    def empty_geo_def() -> Dict[str, Any]:
        return {
            "structure": {
                "codelists": {
                    "codelist": [
                        {
                            "name": {"value": "geography"},
                        }
                    ]
                }
            }
        }

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        params = params or {}
        if url.endswith(
            "/dataset/NM_2021_1.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
        ):
            return 200, overview
        if url.endswith("/dataset/NM_2021_1/geography/TYPE153.def.sdmx.json"):
            search = params.get("search")
            if search == "E05000312":
                return 200, empty_geo_def()
            if search == "Harold Wood":
                return 200, geo_def(641734965, "E05013973", "Harold Wood")
            return 200, empty_geo_def()
        if url.endswith("/geography/TYPE297.def.sdmx.json"):
            return 200, empty_geo_def()
        if url.endswith("/dataset/NM_2021_1.jsonstat.json"):
            assert params.get("geography") == "641734965"
            assert params.get("time") == "2021"
            assert params.get("c2021_restype_3") == "0"
            assert params.get("measures") == "20100"
            return 200, {"value": [10330]}
        return 500, {"error": f"Unexpected URL {url}"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    monkeypatch.setattr(
        nomis_data,
        "_lookup_admin_area_for_gss",
        lambda gss: {"name": "Harold Wood", "level": "WARD"} if gss == "E05000312" else None,
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_2021_1",
            "params": {
                "geography": "E05000312",
                "measures": "20100",
                "time": "2021",
                "c2021_restype_3": "0",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"][0] == 10330
    resolution = body["queryAdjusted"]["geographyResolution"]
    assert resolution["usedDatasetTypeLookup"] is True
    assert resolution["usedNameFallback"] is True
    assert resolution["usedLegacyLookup"] is False
    mapping = body["queryAdjusted"]["mapping"][0]
    assert mapping["gss"] == "E05000312"
    assert mapping["currentGss"] == "E05013973"
    assert mapping["searchedName"] == "Harold Wood"


def test_nomis_query_resolves_district_gss_via_legacy_lookup(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    def geo_def(value: int, gss: str, name: str) -> Dict[str, Any]:
        return {
            "structure": {
                "codelists": {
                    "codelist": [
                        {
                            "code": [
                                {
                                    "value": value,
                                    "description": {"value": name},
                                    "annotations": {
                                        "annotation": [
                                            {"annotationtitle": "GeogCode", "annotationtext": gss},
                                            {"annotationtitle": "TypeCode", "annotationtext": 486},
                                            {"annotationtitle": "TypeName", "annotationtext": "Districts"},
                                        ]
                                    },
                                }
                            ]
                        }
                    ]
                }
            }
        }

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        params = params or {}
        if url.endswith(
            "/dataset/NM_17_5.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
        ):
            return 200, {"overview": {"dimensions": {"dimension": []}}}
        if url.endswith("/geography/TYPE486.def.sdmx.json"):
            assert params.get("search") == "E07000222"
            return 200, geo_def(123456789, "E07000222", "Warwick")
        if url.endswith("/dataset/NM_17_5.jsonstat.json"):
            assert params.get("geography") == "123456789"
            assert params.get("time") == "latest"
            return 200, {"dataset": "NM_17_5", "value": 321}
        return 500, {"error": f"Unexpected URL {url}"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_17_5",
            "params": {
                "geography": "E07000222",
                "time": "latest",
                "variable": "1",
                "measures": "20599",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"] == 321
    assert body["queryAdjusted"]["resolvedGeography"] == "123456789"
    resolution = body["queryAdjusted"]["geographyResolution"]
    assert resolution["level"] == "DISTRICT"
    assert resolution["usedDatasetTypeLookup"] is False
    assert resolution["usedLegacyLookup"] is True
    assert resolution["datasetType"] == {"name": "districts", "value": "TYPE486"}


def test_nomis_query_error_surface_includes_guidance(monkeypatch):
    from tools import nomis_common, nomis_data

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        return 200, {"error": "Cannot create query"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    monkeypatch.setattr(
        nomis_data,
        "_fetch_dataset_overview",
        lambda dataset: {
            "dimensions": [
                {"concept": "geography"},
                {"concept": "time"},
                {"concept": "variable"},
                {"concept": "measures", "sampleValues": ["20599", "21001", "21002", "21003"]},
            ]
        },
    )
    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_17_5",
            "params": {
                "geography": "E07000222",
                "date": "latest",
                "cell": "0",
                "measures": "20100",
            },
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "NOMIS_QUERY_ERROR"
    assert "variable" in body["missingDimensions"]
    assert "Provided measures='20100'" in body["hint"]
    assert "queryAdjusted" in body


def test_nomis_query_autoretries_with_dimension_autoadjustments(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        if url.endswith(
            "/dataset/NM_2028_1.overview.json?select=DatasetInfo,Coverage,Keywords,Dimensions,Codes"
        ):
            return 200, {
                "overview": {
                    "dimensions": {
                        "dimension": [
                            {"concept": "time", "codes": {"code": [{"value": "2021"}]}},
                            {"concept": "geography", "codes": {"code": []}},
                            {
                                "concept": "c_sex",
                                "codes": {"code": [{"value": "0"}, {"value": "1"}, {"value": "2"}]},
                            },
                            {
                                "concept": "measures",
                                "codes": {"code": [{"value": "20100"}, {"value": "20301"}]},
                            },
                        ]
                    }
                }
            }

        if url.endswith("/dataset/NM_2028_1.jsonstat.json"):
            params = params or {}
            if (
                params.get("geography") == "E08000026"
                and params.get("time") == "2021"
                and params.get("c_sex") == "0"
                and params.get("measures") == "20100"
                and "c2021_age_92" not in params
            ):
                return 200, {"value": {"0": 123}}
            return 200, {"error": "Cannot create query"}

        return 500, {"error": f"Unexpected URL {url}"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_2028_1",
            "params": {
                "geography": "E08000026",
                "c2021_age_92": "0",
                "measures": "20100",
            },
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["value"]["0"] == 123
    adjusted = body.get("queryAdjusted", {}).get("dimensionAutoAdjust", {})
    assert adjusted.get("added") == {"time": "2021", "c_sex": "0"}
    assert adjusted.get("removed", {}).get("c2021_age_92") == "0"


def test_nomis_concepts_and_codelists_use_sdmx_json_endpoints(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    seen: Dict[str, str] = {}

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        seen["url"] = url
        return 200, {"items": []}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.concepts", "concept": "GEOGRAPHY", "format": "json"},
    )
    assert resp.status_code == 200
    assert seen["url"].endswith("/concept/GEOGRAPHY.def.sdmx.json")

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.codelists", "codelist": "CL_1_1_SEX", "format": "json"},
    )
    assert resp.status_code == 200
    assert seen["url"].endswith("/codelist/CL_1_1_SEX.def.sdmx.json")


def test_nomis_concepts_and_codelists_fallback_to_dataset_definition(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    dataset_def = {
        "structure": {
            "keyfamilies": {
                "keyfamily": [
                    {
                        "id": "NM_1_1",
                        "components": {
                            "dimension": [
                                {"conceptref": "GEOGRAPHY", "codelist": "CL_1_1_GEOGRAPHY"}
                            ],
                            "attribute": [
                                {"conceptref": "SEX", "codelist": "CL_1_1_SEX"}
                            ],
                            "primarymeasure": {"conceptref": "OBS_VALUE"},
                        },
                    }
                ]
            }
        }
    }

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        if url.endswith("/dataset/def.sdmx.json"):
            return 200, dataset_def
        if "/concept/" in url or "/codelist/" in url:
            return 502, {
                "isError": True,
                "code": "UPSTREAM_INVALID_RESPONSE",
                "message": "NOMIS API returned invalid JSON.",
            }
        return 404, {"isError": True, "code": "NOMIS_API_ERROR", "message": "not found"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    concepts_resp = client.post(
        "/tools/call",
        json={"tool": "nomis.concepts", "concept": "GEOGRAPHY"},
    )
    assert concepts_resp.status_code == 200
    concepts_body = concepts_resp.json()
    assert concepts_body["derived"] is True
    assert concepts_body["data"]["count"] == 1
    assert concepts_body["data"]["concepts"][0]["id"] == "GEOGRAPHY"

    codelists_resp = client.post(
        "/tools/call",
        json={"tool": "nomis.codelists", "codelist": "CL_1_1_SEX"},
    )
    assert codelists_resp.status_code == 200
    codelists_body = codelists_resp.json()
    assert codelists_body["derived"] is True
    assert codelists_body["data"]["count"] == 1
    assert codelists_body["data"]["codelists"][0]["id"] == "CL_1_1_SEX"


def test_nomis_query_error_surface(monkeypatch):
    from tools import nomis_common

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        return 200, {"error": "Cannot create query"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.query", "dataset": "NM_1_1", "params": {"geography": "TYPE499"}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["code"] == "NOMIS_QUERY_ERROR"


def test_nomis_query_incomplete_hint_variants(monkeypatch):
    from tools import nomis_common, nomis_data
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)

    def fake_get_json(  # noqa: ARG001
        url: str,
        params: Dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Tuple[int, Dict[str, Any]]:
        if url.endswith("/dataset/NM_1_1.jsonstat.json"):
            return 200, {"error": "Query is incomplete"}
        return 500, {"error": f"Unexpected URL {url}"}

    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    monkeypatch.setattr(
        nomis_data,
        "_fetch_dataset_overview",
        lambda dataset: {"dimensions": [{"concept": "time"}, {"concept": "geography"}]},
    )

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.query", "dataset": "NM_1_1", "params": {"geography": "TYPE486"}},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "Required dimensions likely missing" in body["hint"]
    assert "time" in body["missingDimensions"]

    resp = client.post(
        "/tools/call",
        json={
            "tool": "nomis.query",
            "dataset": "NM_1_1",
            "params": {"geography": "TYPE486", "time": "latest"},
        },
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "All required dimensions appear present" in body["hint"]
    assert body["missingDimensions"] == []


def test_nomis_datasets_and_concepts(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, {"items": []}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 200
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 200
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 200


def test_nomis_invalid_inputs(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "dataset": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.concepts", "concept": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.concepts", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.codelists", "codelist": 123})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.codelists", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1", "format": "xml"})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1", "params": "bad"})
    assert resp.status_code == 400


def test_nomis_extract_error_list():
    from tools import nomis_data

    assert nomis_data._extract_nomis_error({"errors": ["a", "b"]}) == "a; b"
    assert nomis_data._extract_nomis_error({"error": "boom"}) == "boom"
    assert nomis_data._extract_nomis_error("bad") is None


def test_nomis_extract_text_variants():
    from tools import nomis_data

    assert nomis_data._extract_text(123) == "123"
    assert nomis_data._extract_text([None, {"value": "  value "}, "ignored"]) == "value"


def test_nomis_dataset_summary_falls_back_to_first_keyfamily():
    from tools import nomis_data

    payload = {
        "structure": {
            "keyfamilies": {
                "keyfamily": [
                    {
                        "id": "NM_1111_1",
                        "name": {"value": "Fallback Name"},
                        "annotations": {
                            "annotation": {
                                "annotationtitle": "MetadataText0",
                                "annotationtext": "Fallback Description",
                            }
                        },
                    }
                ]
            }
        }
    }

    summary = nomis_data._extract_dataset_definition_summary("NM_UNKNOWN_1", payload)
    assert summary["id"] == "NM_UNKNOWN_1"
    assert summary["name"] == "Fallback Name"
    assert summary["description"] == "Fallback Description"


def test_nomis_upstream_error_passthrough(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 503, {"isError": True, "code": "NOMIS_API_ERROR", "message": "boom"}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 503
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": "NM_1"})
    assert resp.status_code == 503


def test_nomis_datasets_transient_upstream_error_degrades(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 501, {"isError": True, "code": "UPSTREAM_CONNECT_ERROR", "message": "timeout"}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["degraded"] is True
    assert body["live"] is False
    assert body["datasets"] == []
    assert body["upstreamError"]["code"] == "UPSTREAM_CONNECT_ERROR"

    # Dataset-specific requests should still propagate upstream errors.
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "dataset": "NM_1_1"})
    assert resp.status_code == 501


def test_nomis_error_payloads(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, {"error": "boom"}

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets"})
    assert resp.status_code == 502
    resp = client.post("/tools/call", json={"tool": "nomis.concepts"})
    assert resp.status_code == 502
    resp = client.post("/tools/call", json={"tool": "nomis.codelists"})
    assert resp.status_code == 502


def test_nomis_query_requires_dataset(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    resp = client.post("/tools/call", json={"tool": "nomis.query", "dataset": ""})
    assert resp.status_code == 400


def test_nomis_datasets_summary_limit_and_filter(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    payload = {
        "structure": {
            "keyfamilies": {
                "keyfamily": [
                    {"id": "NM_1_1", "name": {"value": "Population estimates"}},
                    {"id": "NM_2_2", "name": {"value": "Employment by industry"}},
                    {"id": "NM_3_3", "name": {"value": "Population by age"}},
                ]
            }
        }
    }

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, payload

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert body["returned"] == 2
    assert body["truncated"] is True
    assert len(body["datasets"]) == 2

    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "q": "population", "limit": 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["returned"] == 2
    assert body["truncated"] is False
    assert all("population" in item["name"].lower() for item in body["datasets"])


def test_nomis_datasets_multi_term_filter_uses_token_scoring(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    payload = {
        "structure": {
            "keyfamilies": {
                "keyfamily": [
                    {"id": "NM_2021_1", "name": {"value": "TS001 - Usual resident population"}},
                    {"id": "NM_127_1", "name": {"value": "Model-based estimates of unemployment"}},
                    {"id": "NM_2402_1", "name": {"value": "Residential property sales"}},
                ]
            }
        }
    }

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, payload

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.datasets", "q": "population census 2021", "limit": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert body["datasets"][0]["id"] == "NM_2021_1"


def test_nomis_datasets_include_raw(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    payload = {"structure": {"keyfamilies": {"keyfamily": [{"id": "NM_1_1", "name": "Population"}]}}}

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, payload

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.datasets", "limit": 1, "includeRaw": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["raw"] == payload


def test_nomis_dataset_definition_compact_by_default(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    payload = {
        "structure": {
            "keyfamilies": {
                "keyfamily": [
                    {
                        "id": "NM_2055_1",
                        "name": {"value": "TS037 - General health"},
                        "annotations": {
                            "annotation": [
                                {"annotationtitle": "Status", "annotationtext": "Current"},
                                {
                                    "annotationtitle": "SubDescription",
                                    "annotationtext": "All usual residents",
                                },
                            ]
                        },
                        "components": {
                            "dimension": [
                                {"conceptref": "GEOGRAPHY"},
                                {"conceptref": "C2021_HEALTH_6"},
                            ],
                            "primarymeasure": {"conceptref": "OBS_VALUE"},
                        },
                    }
                ]
            }
        }
    }

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, payload

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.datasets", "dataset": "NM_2055_1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset"] == "NM_2055_1"
    assert body["summary"]["id"] == "NM_2055_1"
    assert body["summary"]["name"] == "TS037 - General health"
    assert body["summary"]["primaryMeasure"] == "OBS_VALUE"
    assert body["data"]["dataset"]["id"] == "NM_2055_1"
    assert "structure" not in body["data"]
    assert "hints" in body


def test_nomis_dataset_definition_include_raw(monkeypatch):
    from tools import nomis_common
    from server.config import settings

    payload = {"structure": {"keyfamilies": {"keyfamily": [{"id": "NM_2055_1"}]}}}

    def fake_get_json(url: str, params=None, use_cache=True):  # noqa: ARG001
        return 200, payload

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    monkeypatch.setattr(nomis_common.client, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "nomis.datasets", "dataset": "NM_2055_1", "includeRaw": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == payload
    assert body["raw"] == payload


def test_nomis_datasets_limit_validation(monkeypatch):
    from server.config import settings

    monkeypatch.setattr(settings, "NOMIS_LIVE_ENABLED", True, raising=False)
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "limit": 0})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "limit": True})
    assert resp.status_code == 400
    resp = client.post("/tools/call", json={"tool": "nomis.datasets", "includeRaw": "yes"})
    assert resp.status_code == 400


def test_nomis_workflow_resource_is_available():
    resp = client.get("/resources/read", params={"uri": "resource://mcp-geo/nomis-workflows"})
    assert resp.status_code == 200
    payload = resp.json()["contents"][0]["text"]
    assert "labour_market_area_compare" in payload
    assert "census_theme_profile" in payload
