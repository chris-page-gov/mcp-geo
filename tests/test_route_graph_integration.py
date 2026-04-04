from __future__ import annotations

import os
import uuid

import pytest

from server.config import settings
from server.route_graph import RouteGraph

psycopg = pytest.importorskip("psycopg")


def _integration_dsn() -> str | None:
    return os.getenv("MCP_GEO_LIVE_DB_DSN") or os.getenv("BOUNDARY_CACHE_DSN")


@pytest.mark.integration
def test_route_graph_compute_route_with_postgis_minigraph():
    dsn = _integration_dsn()
    if not dsn:
        pytest.skip("No PostGIS DSN configured for route graph integration test")

    schema = f"routing_test_{uuid.uuid4().hex[:8]}"
    try:
        conn = psycopg.connect(dsn, autocommit=True)
    except Exception as exc:  # pragma: no cover - env dependent
        pytest.skip(f"Unable to connect to PostGIS: {exc}")

    try:
        with conn.cursor() as cur:
            try:
                cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
                cur.execute("CREATE EXTENSION IF NOT EXISTS pgrouting;")
            except Exception as exc:  # pragma: no cover - env dependent
                pytest.skip(f"Unable to enable required extensions: {exc}")
            try:
                cur.execute(f"CREATE SCHEMA {schema};")
                cur.execute(
                    f"""
                    CREATE TABLE {schema}.graph_metadata (
                        graph_version TEXT,
                        is_active BOOLEAN,
                        built_at TIMESTAMPTZ,
                        source_product TEXT,
                        source_release_date DATE,
                        source_download_id TEXT,
                        source_download_name TEXT,
                        source_license TEXT,
                        profiles JSONB,
                        node_count BIGINT,
                        edge_count BIGINT,
                        provenance_path TEXT,
                        status TEXT
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {schema}.graph_nodes (
                        id BIGINT PRIMARY KEY,
                        geom geometry(Point, 4326) NOT NULL
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {schema}.graph_edges (
                        id BIGINT PRIMARY KEY,
                        source BIGINT NOT NULL,
                        target BIGINT NOT NULL,
                        external_id TEXT,
                        name TEXT,
                        mode TEXT,
                        length_m DOUBLE PRECISION,
                        cost_drive DOUBLE PRECISION,
                        reverse_cost_drive DOUBLE PRECISION,
                        cost_walk DOUBLE PRECISION,
                        reverse_cost_walk DOUBLE PRECISION,
                        cost_cycle DOUBLE PRECISION,
                        reverse_cost_cycle DOUBLE PRECISION,
                        cost_emergency DOUBLE PRECISION,
                        reverse_cost_emergency DOUBLE PRECISION,
                        cost_multimodal DOUBLE PRECISION,
                        reverse_cost_multimodal DOUBLE PRECISION,
                        flags JSONB DEFAULT '{{}}'::jsonb,
                        geom geometry(LineString, 4326) NOT NULL
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {schema}.edge_restrictions (
                        restriction_id TEXT,
                        edge_id BIGINT,
                        category TEXT,
                        severity TEXT,
                        message TEXT
                    );
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {schema}.turn_restrictions (
                        from_edge BIGINT,
                        to_edge BIGINT,
                        via_node BIGINT,
                        restriction_type TEXT,
                        message TEXT,
                        active BOOLEAN DEFAULT TRUE
                    );
                    """
                )
                cur.execute(
                    f"""
                    INSERT INTO {schema}.graph_metadata (
                        graph_version,
                        is_active,
                        built_at,
                        source_product,
                        source_release_date,
                        source_download_id,
                        source_download_name,
                        source_license,
                        profiles,
                        node_count,
                        edge_count,
                        provenance_path,
                        status
                    )
                    VALUES (
                        'mini-graph',
                        TRUE,
                        NOW(),
                        'OS MRN',
                        CURRENT_DATE,
                        'download-1',
                        'mini-package',
                        'Open Government Licence v3.0',
                        '["drive","walk","cycle","emergency","multimodal"]'::jsonb,
                        3,
                        2,
                        NULL,
                        'ready'
                    );
                    """
                )
                cur.execute(
                    f"""
                    INSERT INTO {schema}.graph_nodes (id, geom)
                    VALUES
                        (1, ST_SetSRID(ST_MakePoint(-1.5106, 52.4081), 4326)),
                        (2, ST_SetSRID(ST_MakePoint(-1.4000, 52.3000), 4326)),
                        (3, ST_SetSRID(ST_MakePoint(-0.1278, 51.5074), 4326));
                    """
                )
                cur.execute(
                    f"""
                    INSERT INTO {schema}.graph_edges (
                        id,
                        source,
                        target,
                        external_id,
                        name,
                        mode,
                        length_m,
                        cost_drive,
                        reverse_cost_drive,
                        cost_walk,
                        reverse_cost_walk,
                        cost_cycle,
                        reverse_cost_cycle,
                        cost_emergency,
                        reverse_cost_emergency,
                        cost_multimodal,
                        reverse_cost_multimodal,
                        geom
                    )
                    VALUES
                        (
                            1001,
                            1,
                            2,
                            'edge-1001',
                            'Midlands Link',
                            'drive',
                            16000,
                            900,
                            900,
                            7200,
                            7200,
                            3600,
                            3600,
                            720,
                            720,
                            900,
                            900,
                            ST_SetSRID(
                                ST_MakeLine(
                                    ST_MakePoint(-1.5106, 52.4081),
                                    ST_MakePoint(-1.4000, 52.3000)
                                ),
                                4326
                            )
                        ),
                        (
                            1002,
                            2,
                            3,
                            'edge-1002',
                            'Capital Link',
                            'drive',
                            145000,
                            5400,
                            5400,
                            32400,
                            32400,
                            16200,
                            16200,
                            4320,
                            4320,
                            5400,
                            5400,
                            ST_SetSRID(
                                ST_MakeLine(
                                    ST_MakePoint(-1.4000, 52.3000),
                                    ST_MakePoint(-0.1278, 51.5074)
                                ),
                                4326
                            )
                        );
                    """
                )
            except Exception as exc:  # pragma: no cover - env dependent
                pytest.skip(f"Unable to prepare route graph integration schema: {exc}")

        original_enabled = getattr(settings, "ROUTE_GRAPH_ENABLED", False)
        settings.ROUTE_GRAPH_ENABLED = True
        try:
            graph = RouteGraph(
                dsn=dsn,
                schema=schema,
                edges_table="graph_edges",
                nodes_table="graph_nodes",
                metadata_table="graph_metadata",
                restrictions_table="edge_restrictions",
                turn_restrictions_table="turn_restrictions",
                runtime_dir="data/runtime/routing",
                provenance_file="os_mrn_downloads.json",
                max_stops=8,
                soft_avoid_penalty_seconds=180.0,
            )

            status, body = graph.compute_route(
                [
                    {"label": "Coventry", "lat": 52.4081, "lon": -1.5106},
                    {"label": "London", "lat": 51.5074, "lon": -0.1278},
                ],
                profile="drive",
                constraints={"avoidAreas": [], "avoidIds": [], "softAvoid": True},
            )
        finally:
            settings.ROUTE_GRAPH_ENABLED = original_enabled
        assert status == 200
        assert body["graph"]["graphVersion"] == "mini-graph"
        assert body["distanceMeters"] > 1000
        assert body["durationSeconds"] > 0
        assert body["route"]["geometry"]["type"] == "LineString"
        assert body["legs"]
        assert body["steps"]
    finally:
        try:
            with conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE;")
        except Exception:
            pass
        conn.close()
