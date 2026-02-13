from __future__ import annotations

from fastapi.testclient import TestClient

from server.main import app

client = TestClient(app)


def test_os_places_radius_calls_radius_endpoint(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_places_extra

    captured: dict[str, object] = {}

    def fake_get_json(url: str, params):  # noqa: ANN001
        captured["url"] = url
        captured["params"] = params
        return 200, {"results": [{"DPA": {"UPRN": "1", "ADDRESS": "A", "LAT": 51.5, "LNG": -0.1}}]}

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(fake_get_json),
            "post_json": staticmethod(lambda *_args, **_kwargs: (500, {})),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)

    resp = client.post(
        "/tools/call",
        json={"tool": "os_places.radius", "lat": 51.5, "lon": -0.1, "radiusMeters": 100},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert str(captured["url"]).endswith("/radius")
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["point"] == "51.5,-0.1"
    assert params["srs"] == "WGS84"


def test_os_places_polygon_calls_polygon_endpoint(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from tools import os_places_extra

    captured: dict[str, object] = {}

    def fake_post_json(url: str, body=None, params=None):  # noqa: ANN001
        captured["url"] = url
        captured["body"] = body
        captured["params"] = params
        return 200, {"results": [{"DPA": {"UPRN": "2", "ADDRESS": "B", "LAT": 51.6, "LNG": -0.2}}]}

    fake_client = type(
        "C",
        (),
        {
            "get_json": staticmethod(lambda *_args, **_kwargs: (500, {})),
            "post_json": staticmethod(fake_post_json),
            "base_places": "http://example",
        },
    )()
    monkeypatch.setattr(os_places_extra, "client", fake_client)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_places.polygon",
            "polygon": [[-0.2, 51.5], [-0.1, 51.5], [-0.1, 51.6], [-0.2, 51.6], [-0.2, 51.5]],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 1
    assert str(captured["url"]).endswith("/polygon")
    params = captured["params"]
    assert isinstance(params, dict)
    assert params["srs"] == "WGS84"
    geo_body = captured["body"]
    assert isinstance(geo_body, dict)
    assert geo_body["type"] == "Polygon"


def test_os_places_radius_and_polygon_invalid_inputs() -> None:
    radius = client.post(
        "/tools/call",
        json={"tool": "os_places.radius", "lat": "bad", "lon": -0.1, "radiusMeters": 100},
    )
    assert radius.status_code == 400
    assert radius.json()["code"] == "INVALID_INPUT"

    polygon = client.post(
        "/tools/call",
        json={"tool": "os_places.polygon", "polygon": [[-0.2, 51.5], [-0.1, 51.5]]},
    )
    assert polygon.status_code == 400
    assert polygon.json()["code"] == "INVALID_INPUT"
