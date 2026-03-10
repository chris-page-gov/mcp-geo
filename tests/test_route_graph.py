from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from server.config import settings
from server.route_graph import (
    RouteGraph,
    RouteGraphMetadata,
    _build_steps,
    _merge_line_geometries,
    _mode_changes,
    _polygon_wkt,
)


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def execute(self, _query, _params=None):
        return None

    def fetchone(self):
        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self):
        return list(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, cursor_rows):
        self._cursor_rows = list(cursor_rows)

    def cursor(self):
        rows = self._cursor_rows.pop(0) if self._cursor_rows else []
        return FakeCursor(rows)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _graph(tmp_path) -> RouteGraph:
    return RouteGraph(
        dsn="postgresql://example",
        schema="routing",
        edges_table="graph_edges",
        nodes_table="graph_nodes",
        metadata_table="graph_metadata",
        restrictions_table="edge_restrictions",
        turn_restrictions_table="turn_restrictions",
        runtime_dir=str(tmp_path),
        provenance_file="os_mrn_downloads.json",
        max_stops=8,
        soft_avoid_penalty_seconds=180.0,
    )


def test_route_graph_descriptor_reads_metadata_and_provenance(monkeypatch, tmp_path):
    provenance_path = tmp_path / "os_mrn_downloads.json"
    provenance_path.write_text(json.dumps({"selectedProduct": {"name": "OS MRN"}}), encoding="utf-8")
    graph = _graph(tmp_path)
    metadata_row = {
        "graph_version": "mrn-2026-03-01",
        "built_at": datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc),
        "source_product": "OS MRN",
        "source_release_date": date(2026, 3, 1),
        "source_download_id": "download-1",
        "source_download_name": "os-mrn.zip",
        "source_license": "Open Government Licence v3.0",
        "profiles": ["drive", "walk", "cycle", "emergency", "multimodal"],
        "node_count": 42,
        "edge_count": 84,
        "provenance_path": str(provenance_path),
        "status": "ready",
    }
    monkeypatch.setattr(settings, "ROUTE_GRAPH_ENABLED", True, raising=False)
    monkeypatch.setattr(
        graph,
        "_connect",
        lambda: FakeConn(
            [
                [{"extname": "postgis"}, {"extname": "pgrouting"}],
                [metadata_row],
            ]
        ),
    )

    descriptor = graph.descriptor()
    assert descriptor["graph"]["ready"] is True
    assert descriptor["graph"]["graphVersion"] == "mrn-2026-03-01"
    assert descriptor["graph"]["sourceReleaseDate"] == "2026-03-01"
    assert descriptor["graph"]["provenance"]["selectedProduct"]["name"] == "OS MRN"


def test_route_graph_compute_route_success(monkeypatch, tmp_path):
    graph = _graph(tmp_path)
    metadata = RouteGraphMetadata(
        ready=True,
        reason=None,
        graph_version="mrn-2026-03-01",
        built_at="2026-03-01T00:00:00+00:00",
        source_product="OS MRN",
        source_release_date="2026-03-01",
        source_download_id="download-1",
        source_download_name="os-mrn.zip",
        source_license="OGLv3",
        profiles=["drive", "walk", "cycle", "emergency", "multimodal"],
        node_count=10,
        edge_count=20,
        provenance_path=None,
        provenance=None,
    )
    segments = [
        {
            "edgeId": 1001,
            "name": "Churchgate",
            "mode": "drive",
            "distanceMeters": 500.0,
            "durationSeconds": 60.0,
            "geometry": {"type": "LineString", "coordinates": [[-1.0, 52.0], [-0.9, 51.9]]},
            "flags": {},
        },
        {
            "edgeId": 1002,
            "name": "Churchgate",
            "mode": "drive",
            "distanceMeters": 700.0,
            "durationSeconds": 90.0,
            "geometry": {"type": "LineString", "coordinates": [[-0.9, 51.9], [-0.8, 51.8]]},
            "flags": {},
        },
    ]
    monkeypatch.setattr(graph, "_descriptor_metadata", lambda: metadata)
    monkeypatch.setattr(graph, "_connect", lambda: FakeConn([]))
    monkeypatch.setattr(graph, "_load_metadata", lambda _conn: metadata)
    node_ids = iter(
        [
            {"nodeId": 1, "distanceMeters": 10.0},
            {"nodeId": 2, "distanceMeters": 12.0},
        ]
    )
    monkeypatch.setattr(graph, "_nearest_node", lambda _conn, _lat, _lon: next(node_ids))
    monkeypatch.setattr(graph, "_run_leg", lambda _conn, **_kwargs: list(segments))
    monkeypatch.setattr(
        graph,
        "_restriction_warnings",
        lambda _conn, **_kwargs: [{"message": "Bridge height restriction advisory"}],
    )

    status, body = graph.compute_route(
        [
            {"label": "Start", "lat": 52.0, "lon": -1.0},
            {"label": "End", "lat": 51.8, "lon": -0.8},
        ],
        profile="drive",
        constraints={"avoidAreas": [], "avoidIds": [], "softAvoid": True},
    )
    assert status == 200
    assert body["distanceMeters"] == 1200.0
    assert body["durationSeconds"] == 150.0
    assert body["steps"][0]["instruction"] == "Follow Churchgate"
    assert body["warnings"][0]["message"] == "Bridge height restriction advisory"
    assert body["resolvedStops"][0]["nodeId"] == 1


def test_route_graph_compute_route_returns_no_route(monkeypatch, tmp_path):
    graph = _graph(tmp_path)
    metadata = RouteGraphMetadata(
        ready=True,
        reason=None,
        graph_version="mrn-2026-03-01",
        built_at=None,
        source_product=None,
        source_release_date=None,
        source_download_id=None,
        source_download_name=None,
        source_license=None,
        profiles=["drive"],
        node_count=None,
        edge_count=None,
        provenance_path=None,
        provenance=None,
    )
    monkeypatch.setattr(graph, "_descriptor_metadata", lambda: metadata)
    monkeypatch.setattr(graph, "_connect", lambda: FakeConn([]))
    monkeypatch.setattr(graph, "_load_metadata", lambda _conn: metadata)
    monkeypatch.setattr(graph, "_nearest_node", lambda _conn, _lat, _lon: {"nodeId": 1, "distanceMeters": 0.0})
    monkeypatch.setattr(graph, "_run_leg", lambda _conn, **_kwargs: [])

    status, body = graph.compute_route(
        [
            {"label": "Start", "lat": 52.0, "lon": -1.0},
            {"label": "End", "lat": 51.8, "lon": -0.8},
        ],
        profile="drive",
        constraints={"avoidAreas": [], "avoidIds": [], "softAvoid": True},
    )
    assert status == 404
    assert body["code"] == "NO_ROUTE"


def test_route_graph_restriction_queries(monkeypatch, tmp_path):
    graph = _graph(tmp_path)
    conn = FakeConn(
        [
            [
                {
                    "restriction_id": "r1",
                    "edge_id": 1001,
                    "category": "hazard",
                    "severity": "medium",
                    "message": "Flood advisory",
                }
            ],
            [
                {
                    "from_edge": 1001,
                    "to_edge": 1002,
                    "via_node": 2,
                    "restriction_type": "no_left_turn",
                    "message": "Turn restriction present",
                }
            ],
        ]
    )
    edge_warnings = graph._edge_restriction_rows(conn, [1001])
    turn_warnings = graph._turn_restriction_rows(conn, [(1001, 1002)])
    assert edge_warnings[0]["restrictionId"] == "r1"
    assert turn_warnings[0]["restrictionType"] == "no_left_turn"


def test_route_graph_run_leg_handles_default_flags(monkeypatch, tmp_path):
    graph = _graph(tmp_path)
    conn = FakeConn(
        [
            [
                {
                    "edge_id": 1001,
                    "external_id": "edge-1001",
                    "name": "Churchgate",
                    "mode": "drive",
                    "length_m": 365.0,
                    "cost": 55.0,
                    "geometry": '{"type":"LineString","coordinates":[[-0.94,53.32],[-0.945,53.321]]}',
                    "flags": {},
                }
            ]
        ]
    )
    monkeypatch.setattr(graph, "_edge_sql", lambda *_args, **_kwargs: "SELECT 1")

    segments = graph._run_leg(
        conn,
        start_node=1,
        end_node=2,
        profile="drive",
        constraints={"avoidAreas": [], "avoidIds": [], "softAvoid": True},
    )

    assert len(segments) == 1
    assert segments[0]["edgeId"] == 1001
    assert segments[0]["flags"] == {}


def test_route_graph_avoid_predicates_rejects_unparseable_avoid_areas(tmp_path):
    graph = _graph(tmp_path)
    conn = FakeConn([])

    with pytest.raises(ValueError, match="avoidAreas entries must use bounding-box arrays"):
        graph._avoid_predicates(
            conn,
            {"avoidAreas": ["flood restrictions"], "avoidIds": [], "softAvoid": False},
        )


def test_route_graph_compute_route_returns_invalid_input_for_bad_avoid_areas(monkeypatch, tmp_path):
    graph = _graph(tmp_path)
    metadata = RouteGraphMetadata(
        ready=True,
        reason=None,
        graph_version="mrn-2026-03-01",
        built_at="2026-03-01T00:00:00+00:00",
        source_product="OS MRN",
        source_release_date="2026-03-01",
        source_download_id="download-1",
        source_download_name="os-mrn.zip",
        source_license="OGLv3",
        profiles=["drive", "walk", "cycle", "emergency", "multimodal"],
        node_count=10,
        edge_count=20,
        provenance_path=None,
        provenance=None,
    )
    monkeypatch.setattr(graph, "_descriptor_metadata", lambda: metadata)
    monkeypatch.setattr(graph, "_connect", lambda: FakeConn([]))
    monkeypatch.setattr(graph, "_load_metadata", lambda _conn: metadata)
    node_ids = iter(
        [
            {"nodeId": 1, "distanceMeters": 10.0},
            {"nodeId": 2, "distanceMeters": 12.0},
        ]
    )
    monkeypatch.setattr(graph, "_nearest_node", lambda _conn, _lat, _lon: next(node_ids))

    def fake_run_leg(_conn, **_kwargs):
        raise ValueError(
            "avoidAreas entries must use bounding-box arrays or GeoJSON Polygon/MultiPolygon geometry."
        )

    monkeypatch.setattr(graph, "_run_leg", fake_run_leg)

    status, body = graph.compute_route(
        [
            {"label": "Start", "lat": 52.0, "lon": -1.0},
            {"label": "End", "lat": 51.8, "lon": -0.8},
        ],
        profile="drive",
        constraints={"avoidAreas": ["flood restrictions"], "avoidIds": [], "softAvoid": False},
    )
    assert status == 400
    assert body["code"] == "INVALID_INPUT"
    assert "avoidAreas entries must use bounding-box arrays" in body["message"]


def test_route_graph_geometry_and_step_helpers():
    first = {"type": "LineString", "coordinates": [[-1.0, 52.0], [-0.9, 51.9]]}
    second = {"type": "LineString", "coordinates": [[-0.9, 51.9], [-0.8, 51.8]]}
    merged = _merge_line_geometries(first, second)
    assert merged["coordinates"] == [[-1.0, 52.0], [-0.9, 51.9], [-0.8, 51.8]]

    steps = _build_steps(
        [
            {
                "edgeId": 1001,
                "name": "Churchgate",
                "mode": "drive",
                "distanceMeters": 500.0,
                "durationSeconds": 60.0,
                "geometry": first,
            },
            {
                "edgeId": 1002,
                "name": "Churchgate",
                "mode": "drive",
                "distanceMeters": 700.0,
                "durationSeconds": 90.0,
                "geometry": second,
            },
            {
                "edgeId": 1003,
                "name": "Station Link",
                "mode": "rail",
                "distanceMeters": 900.0,
                "durationSeconds": 300.0,
                "geometry": second,
            },
        ],
        leg_index=0,
    )
    assert len(steps) == 2
    assert steps[0]["distanceMeters"] == 1200.0
    assert _mode_changes(
        [
            {"edgeId": 1001, "mode": "walk"},
            {"edgeId": 1002, "mode": "rail"},
        ]
    ) == [{"index": 1, "fromMode": "walk", "toMode": "rail", "edgeId": 1002}]


def test_route_graph_polygon_wkt_helpers():
    assert _polygon_wkt([-1.0, 51.0, -0.5, 51.5]).startswith("POLYGON((")
    assert _polygon_wkt(
        {
            "type": "Polygon",
            "coordinates": [[[-1.0, 51.0], [-0.5, 51.0], [-0.5, 51.5], [-1.0, 51.0]]],
        }
    ).startswith("POLYGON(")
    assert _polygon_wkt({"type": "MultiPolygon", "coordinates": []}) is None
