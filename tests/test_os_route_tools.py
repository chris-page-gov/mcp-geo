from fastapi.testclient import TestClient
import pytest

from server.main import app
from tools import os_route

client = TestClient(app)


class FakeRouteGraph:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def descriptor(self):
        return {
            "supportedProfiles": ["drive", "walk", "cycle", "emergency", "multimodal"],
            "constraintTypes": ["avoidAreas", "avoidIds", "softAvoid"],
            "maxStops": 8,
            "graph": {"ready": True, "graphVersion": "test-graph"},
        }

    def max_stops(self):
        return 8

    def compute_route(self, resolved_stops, *, profile, constraints):
        self.calls.append(
            {
                "resolved_stops": resolved_stops,
                "profile": profile,
                "constraints": constraints,
            }
        )
        return self.result


def test_os_route_descriptor_uses_graph_status(monkeypatch):
    fake = FakeRouteGraph((200, {"ok": True}))
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)

    resp = client.post("/tools/call", json={"tool": "os_route.descriptor"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["graph"]["graphVersion"] == "test-graph"


def test_os_route_get_success_with_coordinates_and_defaults(monkeypatch):
    fake = FakeRouteGraph(
        (
            200,
            {
                "resolvedStops": [],
                "distanceMeters": 2400.0,
                "durationSeconds": 420.0,
                "route": {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-1.51, 52.41], [-0.12, 51.51]],
                    },
                    "properties": {"profile": "emergency"},
                },
                "legs": [{"distanceMeters": 2400.0, "durationSeconds": 420.0, "steps": []}],
                "steps": [{"instruction": "Follow Example Road", "distanceMeters": 2400.0}],
                "modeChanges": [],
                "warnings": [],
                "graph": {"ready": True, "graphVersion": "mrn-2026-03-01"},
            },
        )
    )
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_route.get",
            "stops": [
                {"coordinates": [-1.5106, 52.4081]},
                {"coordinates": [-0.1278, 51.5074]},
            ],
            "profile": "EMERGENCY",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["profile"] == "emergency"
    assert body["distanceMeters"] == 2400.0
    assert fake.calls[0]["profile"] == "emergency"
    assert fake.calls[0]["constraints"]["softAvoid"] is True
    resolved_stops = fake.calls[0]["resolved_stops"]
    assert resolved_stops[0]["lat"] == 52.4081
    assert resolved_stops[0]["lon"] == -1.5106


def test_os_route_get_returns_ambiguous_stop(monkeypatch):
    fake = FakeRouteGraph((200, {}))
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)
    monkeypatch.setattr(os_route, "_places_search", lambda payload: (200, {"results": []}))
    monkeypatch.setattr(
        os_route,
        "_names_find",
        lambda payload: (
            200,
            {
                "results": [
                    {"name1": "Springfield", "lat": 52.1, "lon": -1.1},
                    {"name1": "Springfield", "lat": 52.2, "lon": -1.2},
                ]
            },
        ),
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_route.get",
            "stops": [{"query": "Springfield"}, {"coordinates": [-0.1278, 51.5074]}],
        },
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["code"] == "AMBIGUOUS_STOP"


def test_os_route_get_surfaces_graph_not_ready(monkeypatch):
    fake = FakeRouteGraph(
        (
            503,
            {
                "isError": True,
                "code": "ROUTE_GRAPH_NOT_READY",
                "message": "Route graph is not ready.",
                "graph": {"ready": False, "reason": "graph_metadata_missing"},
            },
        )
    )
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_route.get",
            "stops": [
                {"coordinates": [-1.5106, 52.4081]},
                {"coordinates": [-0.1278, 51.5074]},
            ],
        },
    )
    assert resp.status_code == 503
    body = resp.json()
    assert body["code"] == "ROUTE_GRAPH_NOT_READY"


def test_os_route_get_preserves_mode_changes_and_warnings(monkeypatch):
    fake = FakeRouteGraph(
        (
            200,
            {
                "resolvedStops": [],
                "distanceMeters": 4200.0,
                "durationSeconds": 1500.0,
                "route": {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-1.51, 52.41], [-1.5, 52.4], [-0.12, 51.51]],
                    },
                    "properties": {"profile": "multimodal"},
                },
                "legs": [{"distanceMeters": 4200.0, "durationSeconds": 1500.0, "steps": []}],
                "steps": [{"instruction": "Walk to station"}],
                "modeChanges": [{"fromMode": "walk", "toMode": "rail"}],
                "warnings": [{"message": "Platform change at interchange"}],
                "graph": {"ready": True, "graphVersion": "mrn-2026-03-01"},
            },
        )
    )
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)
    monkeypatch.setattr(os_route, "_places_search", lambda payload: (200, {"results": []}))
    monkeypatch.setattr(
        os_route,
        "_names_find",
        lambda payload: (
            200,
            {
                "results": [
                    {
                        "name1": str(payload.get("text")),
                        "lat": 52.4081 if str(payload.get("text")) == "Coventry" else 51.5074,
                        "lon": -1.5106 if str(payload.get("text")) == "Coventry" else -0.1278,
                    }
                ]
            },
        ),
    )

    resp = client.post(
        "/tools/call",
        json={
            "tool": "os_route.get",
            "stops": [{"query": "Coventry"}, {"query": "London"}],
            "profile": "multimodal",
            "constraints": {"avoidIds": ["167647/3"], "softAvoid": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["modeChanges"] == [{"fromMode": "walk", "toMode": "rail"}]
    assert body["warnings"][0]["message"] == "Platform change at interchange"
    assert fake.calls[0]["constraints"]["avoidIds"] == ["167647/3"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "stops must contain at least two route stops"),
        (
            {
                "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
                "via": "Coventry",
            },
            "via must be a list when provided",
        ),
        (
            {
                "stops": [{"bad": True}, {"coordinates": [-0.1, 51.5]}],
            },
            "Each stop must include exactly one of query, uprn, or coordinates",
        ),
        (
            {
                "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
                "constraints": "avoid-everything",
            },
            "constraints must be an object when provided",
        ),
    ],
)
def test_route_get_validation_errors(monkeypatch, payload, message):
    monkeypatch.setattr(os_route, "_route_graph", lambda: FakeRouteGraph((200, {})))
    status, body = os_route._route_get(payload)
    assert status == 400
    assert body["message"] == message


def test_route_get_limits_total_stop_count(monkeypatch):
    fake = FakeRouteGraph((200, {}))
    monkeypatch.setattr(fake, "max_stops", lambda: 2)
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)

    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
            "via": [{"query": "Coventry"}],
        }
    )
    assert status == 400
    assert "Combined stops and via entries support at most 2 entries" in body["message"]


def test_route_get_limits_base_stop_count(monkeypatch):
    fake = FakeRouteGraph((200, {}))
    monkeypatch.setattr(fake, "max_stops", lambda: 1)
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)

    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
        }
    )
    assert status == 400
    assert "stops supports at most 1 entries" in body["message"]


def test_route_get_rejects_delivery_and_inline_max_errors(monkeypatch):
    monkeypatch.setattr(os_route, "_route_graph", lambda: FakeRouteGraph((200, {})))
    monkeypatch.setattr(os_route, "parse_delivery", lambda *_args, **_kwargs: (None, "bad delivery"))
    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
        }
    )
    assert status == 400
    assert body["message"] == "bad delivery"

    monkeypatch.setattr(os_route, "parse_delivery", lambda *_args, **_kwargs: ("inline", None))
    monkeypatch.setattr(os_route, "parse_inline_max_bytes", lambda *_args, **_kwargs: (None, "bad inline"))
    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
        }
    )
    assert status == 400
    assert body["message"] == "bad inline"


def test_route_get_resource_delivery_exports_payload(monkeypatch):
    fake = FakeRouteGraph(
        (
            200,
            {
                "resolvedStops": [{"label": "Start"}, {"label": "End"}],
                "distanceMeters": 200.0,
                "durationSeconds": 30.0,
                "route": {"type": "Feature", "geometry": {"type": "LineString", "coordinates": []}},
                "legs": [],
                "steps": [],
                "modeChanges": [],
                "warnings": [],
                "graph": {"ready": True, "graphVersion": "mrn-2026-03-01"},
            },
        )
    )
    monkeypatch.setattr(os_route, "_route_graph", lambda: fake)
    monkeypatch.setattr(os_route, "select_delivery_mode", lambda **_kwargs: "resource")
    monkeypatch.setattr(
        os_route,
        "write_resource_payload",
        lambda **_kwargs: {
            "resourceUri": "resource://os-route/123",
            "bytes": 512,
            "sha256": "abc",
            "path": "/tmp/os-route-123.json",
        },
    )

    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
            "delivery": "resource",
        }
    )
    assert status == 200
    assert body["delivery"] == "resource"
    assert body["resourceUri"] == "resource://os-route/123"
    assert body["graph"]["graphVersion"] == "mrn-2026-03-01"


def test_resolve_stop_supports_uprn_and_postcode_branches(monkeypatch):
    monkeypatch.setattr(
        os_route,
        "_places_by_uprn",
        lambda payload: (
            200,
            {
                "result": {
                    "address": f"{payload['uprn']} Example Street",
                    "lat": 52.4,
                    "lon": -1.5,
                }
            },
        ),
    )
    status, body = os_route._resolve_stop({"uprn": "100023336959"}, index=0)
    assert status == 200
    assert body["source"] == "os_places.by_uprn"
    assert body["uprn"] == "100023336959"

    monkeypatch.setattr(
        os_route,
        "_by_postcode",
        lambda _payload: (200, {"uprns": [{"address": "10 Downing Street", "lat": 51.5, "lon": -0.12, "uprn": "1"}]}),
    )
    status, body = os_route._resolve_stop({"query": "SW1A 2AA"}, index=1)
    assert status == 200
    assert body["source"] == "os_places.by_postcode"

    monkeypatch.setattr(os_route, "_by_postcode", lambda _payload: (200, {"uprns": []}))
    status, body = os_route._resolve_stop({"query": "DN22 6PE"}, index=2)
    assert status == 404
    assert body["code"] == "STOP_NOT_FOUND"

    monkeypatch.setattr(
        os_route,
        "_by_postcode",
        lambda _payload: (
            200,
            {
                "uprns": [
                    {"address": "A", "lat": 51.5, "lon": -0.12},
                    {"address": "B", "lat": 51.5, "lon": -0.11},
                ]
            },
        ),
    )
    status, body = os_route._resolve_stop({"query": "EC1A 1BB"}, index=3)
    assert status == 409
    assert body["code"] == "AMBIGUOUS_STOP"


def test_resolve_stop_places_and_names_fallbacks(monkeypatch):
    monkeypatch.setattr(
        os_route,
        "_places_search",
        lambda _payload: (
            200,
            {
                "results": [
                    {
                        "address": "Retford Library, 17 Churchgate",
                        "lat": 53.322,
                        "lon": -0.943,
                        "uprn": "1001",
                    },
                    {"address": "Retford Library Annexe", "lat": 53.321, "lon": -0.944, "uprn": "1002"},
                ]
            },
        ),
    )
    status, body = os_route._resolve_stop({"query": "Retford Library"}, index=0)
    assert status == 200
    assert body["source"] == "os_places.search"
    assert body["confidence"] == "medium"
    assert len(body["alternatives"]) == 1

    monkeypatch.setattr(
        os_route,
        "_places_search",
        lambda _payload: (200, {"results": [{"address": "Coventry", "lat": 52.4081, "lon": -1.5106}]}),
    )
    status, body = os_route._resolve_stop({"query": "Coventry"}, index=1)
    assert status == 200
    assert body["source"] == "os_places.search"
    assert body["confidence"] == "high"

    monkeypatch.setattr(os_route, "_places_search", lambda _payload: (200, {"results": []}))
    monkeypatch.setattr(
        os_route,
        "_names_find",
        lambda _payload: (
            200,
            {
                "results": [
                    {"name1": "Coventry", "lat": 52.4081, "lon": -1.5106},
                    {"name1": "Coventry Airport", "lat": 52.369, "lon": -1.479},
                ]
            },
        ),
    )
    status, body = os_route._resolve_stop({"query": "Coventry"}, index=2)
    assert status == 200
    assert body["source"] == "os_names.find"
    assert body["confidence"] == "medium"
    assert len(body["alternatives"]) == 2

    monkeypatch.setattr(
        os_route,
        "_names_find",
        lambda _payload: (
            200,
            {
                "results": [
                    {"name1": "Springfield", "lat": 52.1, "lon": -1.1},
                    {"name1": "Springfield", "lat": 52.2, "lon": -1.2},
                ]
            },
        ),
    )
    status, body = os_route._resolve_stop({"query": "Springfield"}, index=3)
    assert status == 409
    assert body["code"] == "AMBIGUOUS_STOP"

    monkeypatch.setattr(os_route, "_names_find", lambda _payload: (200, {"results": []}))
    status, body = os_route._resolve_stop({"query": "Missing Hamlet"}, index=4)
    assert status == 404
    assert body["code"] == "STOP_NOT_FOUND"


def test_resolve_stop_returns_upstream_error_for_address_like_failures(monkeypatch):
    monkeypatch.setattr(os_route, "_places_search", lambda _payload: (200, {"results": []}))
    monkeypatch.setattr(os_route, "_names_find", lambda _payload: (503, {"code": "UPSTREAM"}))

    status, body = os_route._resolve_stop({"query": "17 Church Road"}, index=0)
    assert status == 404
    assert body["code"] == "STOP_NOT_FOUND"
    assert body["upstream"] == {"code": "UPSTREAM"}


def test_route_get_wraps_stop_resolution_value_errors(monkeypatch):
    monkeypatch.setattr(os_route, "_route_graph", lambda: FakeRouteGraph((200, {})))
    monkeypatch.setattr(os_route, "_resolve_stop", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad stop")))

    status, body = os_route._route_get(
        {
            "stops": [{"coordinates": [-1.5, 52.4]}, {"coordinates": [-0.1, 51.5]}],
        }
    )
    assert status == 404
    assert body["code"] == "STOP_NOT_FOUND"
    assert body["message"] == "bad stop"


def test_resolved_stop_payload_requires_coordinates():
    with pytest.raises(ValueError, match="missing coordinates"):
        os_route._resolved_stop_payload(
            input_stop={"query": "Nowhere"},
            index=0,
            label="Nowhere",
            lat=None,
            lon=None,
            source="test",
            confidence="low",
        )
