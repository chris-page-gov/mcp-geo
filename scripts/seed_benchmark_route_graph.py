#!/usr/bin/env python3
"""Seed a small deterministic route graph for stakeholder benchmark runs."""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_SQL = (REPO_ROOT / "scripts" / "route_graph_schema.sql").read_text(encoding="utf-8")
GRAPH_VERSION = "stakeholder-benchmark-2026-03-10"
NODE_ROWS = [
    {
        "id": 910001,
        "label": "Retford Library",
        "lat": 53.3243106,
        "lon": -0.9422989,
    },
    {
        "id": 910002,
        "label": "Goodwin Hall",
        "lat": 53.3219807,
        "lon": -0.9451639,
    },
    {
        "id": 910003,
        "label": "Retford Fire Station",
        "lat": 53.3194261,
        "lon": -0.9419241,
    },
    {
        "id": 910004,
        "label": "Tuxford Fire Station",
        "lat": 53.2286318,
        "lon": -0.8950427,
    },
]
EDGE_ROWS = [
    {
        "id": 920001,
        "source": 910001,
        "target": 910002,
        "name": "Churchgate to Chancery Lane",
        "length_m": 365.0,
        "cost_drive": 55.0,
        "cost_emergency": 40.0,
    },
    {
        "id": 920002,
        "source": 910003,
        "target": 910002,
        "name": "Wharf Road Response Link",
        "length_m": 470.0,
        "cost_drive": 75.0,
        "cost_emergency": 50.0,
    },
    {
        "id": 920003,
        "source": 910004,
        "target": 910002,
        "name": "Tuxford Response Link",
        "length_m": 11100.0,
        "cost_drive": 960.0,
        "cost_emergency": 900.0,
    },
]


def _dsn() -> str:
    return os.getenv("ROUTE_GRAPH_DSN") or os.getenv("BOUNDARY_CACHE_DSN") or ""


def main() -> int:
    if psycopg is None:
        print(json.dumps({"status": "error", "message": "psycopg is not installed"}))
        return 1
    dsn = _dsn()
    if not dsn:
        print(
            json.dumps(
                {"status": "error", "message": "Missing ROUTE_GRAPH_DSN or BOUNDARY_CACHE_DSN"}
            )
        )
        return 1

    try:
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
                cur.execute("DELETE FROM routing.edge_restrictions WHERE edge_id = ANY(%s)", ([row["id"] for row in EDGE_ROWS],))
                cur.execute("DELETE FROM routing.turn_restrictions WHERE from_edge = ANY(%s) OR to_edge = ANY(%s)", ([row["id"] for row in EDGE_ROWS], [row["id"] for row in EDGE_ROWS]))
                cur.execute("DELETE FROM routing.graph_edges WHERE id = ANY(%s)", ([row["id"] for row in EDGE_ROWS],))
                cur.execute("DELETE FROM routing.graph_nodes WHERE id = ANY(%s)", ([row["id"] for row in NODE_ROWS],))
                cur.execute("UPDATE routing.graph_metadata SET is_active = FALSE WHERE graph_version <> %s", (GRAPH_VERSION,))

                for row in NODE_ROWS:
                    cur.execute(
                        """
                        INSERT INTO routing.graph_nodes (id, geom, modes)
                        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), ARRAY['drive','walk','cycle','emergency','multimodal'])
                        """,
                        (row["id"], row["lon"], row["lat"]),
                    )

                def _node(node_id: int) -> dict[str, float]:
                    return next(item for item in NODE_ROWS if item["id"] == node_id)

                for row in EDGE_ROWS:
                    start = _node(row["source"])
                    end = _node(row["target"])
                    cur.execute(
                        """
                        INSERT INTO routing.graph_edges (
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
                            flags,
                            geom
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            'drive',
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            '{"benchmarkSeed": true}'::jsonb,
                            ST_SetSRID(
                                ST_MakeLine(
                                    ST_MakePoint(%s, %s),
                                    ST_MakePoint(%s, %s)
                                ),
                                4326
                            )
                        )
                        """,
                        (
                            row["id"],
                            row["source"],
                            row["target"],
                            f"benchmark-edge-{row['id']}",
                            row["name"],
                            row["length_m"],
                            row["cost_drive"],
                            row["cost_drive"],
                            row["length_m"] / 1.4,
                            row["length_m"] / 1.4,
                            row["length_m"] / 4.2,
                            row["length_m"] / 4.2,
                            row["cost_emergency"],
                            row["cost_emergency"],
                            row["cost_drive"],
                            row["cost_drive"],
                            start["lon"],
                            start["lat"],
                            end["lon"],
                            end["lat"],
                        ),
                    )

                cur.execute(
                    """
                    INSERT INTO routing.edge_restrictions (
                        restriction_id,
                        edge_id,
                        category,
                        severity,
                        message,
                        penalty_factor,
                        properties
                    )
                    VALUES (
                        'benchmark-flood-advisory',
                        %s,
                        'hazard',
                        'medium',
                        'Benchmark flood advisory near the Retford town-centre link.',
                        1.0,
                        '{"benchmarkSeed": true}'::jsonb
                    )
                    """,
                    (920001,),
                )

                cur.execute(
                    """
                    INSERT INTO routing.graph_metadata (
                        graph_version,
                        is_active,
                        built_at,
                        source_product,
                        source_download_id,
                        source_download_name,
                        source_license,
                        profiles,
                        node_count,
                        edge_count,
                        provenance_path,
                        coverage,
                        notes,
                        status
                    )
                    VALUES (
                        %s,
                        TRUE,
                        NOW(),
                        'Benchmark seeded route graph',
                        'stakeholder-benchmark-seed',
                        'Public-site deterministic seed graph',
                        'Internal benchmark use',
                        '["drive","walk","cycle","emergency","multimodal"]'::jsonb,
                        %s,
                        %s,
                        %s,
                        '{"scope":"Retford and Tuxford benchmark anchors"}'::jsonb,
                        '["Not a full MRN ingest","Provides deterministic routing for stakeholder benchmark scenarios"]'::jsonb,
                        'ready'
                    )
                    ON CONFLICT (graph_version)
                    DO UPDATE SET
                        is_active = EXCLUDED.is_active,
                        built_at = EXCLUDED.built_at,
                        source_product = EXCLUDED.source_product,
                        source_download_id = EXCLUDED.source_download_id,
                        source_download_name = EXCLUDED.source_download_name,
                        source_license = EXCLUDED.source_license,
                        profiles = EXCLUDED.profiles,
                        node_count = EXCLUDED.node_count,
                        edge_count = EXCLUDED.edge_count,
                        provenance_path = EXCLUDED.provenance_path,
                        coverage = EXCLUDED.coverage,
                        notes = EXCLUDED.notes,
                        status = EXCLUDED.status
                    """,
                    (
                        GRAPH_VERSION,
                        len(NODE_ROWS),
                        len(EDGE_ROWS),
                        str(REPO_ROOT / "scripts" / "seed_benchmark_route_graph.py"),
                    ),
                )
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "graphVersion": GRAPH_VERSION,
                "nodeCount": len(NODE_ROWS),
                "edgeCount": len(EDGE_ROWS),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
