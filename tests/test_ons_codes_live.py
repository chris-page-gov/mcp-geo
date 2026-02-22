from typing import Any, Dict, Tuple

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_ons_codes_list_cached(monkeypatch, tmp_path):
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_DATASET_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(config.settings, "ONS_DATASET_CACHE_DIR", str(tmp_path), raising=False)

    def fake_get_json(url: str, params: Dict[str, Any] | None = None, use_cache: bool = True) -> Tuple[int, Dict[str, Any]]:  # noqa: ARG001
        return 200, {"dimensions": [{"id": "time"}]}

    monkeypatch.setattr(ons_codes._CLIENT, "get_json", fake_get_json)

    resp = client.post(
        "/tools/call",
        json={"tool": "ons_codes.list", "dataset": "gdp", "edition": "time-series", "version": "1"},
    )
    assert resp.status_code == 200
    assert resp.json()["dimensions"] == ["time"]

    resp_cached = client.post(
        "/tools/call",
        json={"tool": "ons_codes.list", "dataset": "gdp", "edition": "time-series", "version": "1"},
    )
    assert resp_cached.status_code == 200
    assert resp_cached.json()["cached"] is True


def test_ons_codes_options_cached(monkeypatch, tmp_path):
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_DATASET_CACHE_ENABLED", True, raising=False)
    monkeypatch.setattr(config.settings, "ONS_DATASET_CACHE_DIR", str(tmp_path), raising=False)

    def fake_get_all_pages(url: str, params: Dict[str, Any] | None = None, item_key: str = "items"):
        return 200, [{"id": "2023 Q1"}, {"id": "2023 Q2"}]

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_get_all_pages)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_codes.options",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "dimension": "time",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["options"] == ["2023 Q1", "2023 Q2"]

    resp_cached = client.post(
        "/tools/call",
        json={
            "tool": "ons_codes.options",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "dimension": "time",
        },
    )
    assert resp_cached.status_code == 200
    assert resp_cached.json()["cached"] is True


def test_ons_codes_options_accepts_nested_code_ids(monkeypatch):
    from server import config
    from tools import ons_codes

    monkeypatch.setattr(config.settings, "ONS_DATASET_CACHE_ENABLED", False, raising=False)

    def fake_get_all_pages(url: str, params: Dict[str, Any] | None = None, item_key: str = "items"):  # noqa: ARG001
        return 200, [
            {"label": "Jan-24", "links": {"code": {"id": "Jan-24"}}},
            {"label": "Feb-24", "links": {"code": {"id": "Feb-24"}}},
        ]

    monkeypatch.setattr(ons_codes._CLIENT, "get_all_pages", fake_get_all_pages)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "ons_codes.options",
            "dataset": "gdp",
            "edition": "time-series",
            "version": "1",
            "dimension": "time",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["options"] == ["Jan-24", "Feb-24"]
