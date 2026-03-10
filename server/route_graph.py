from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from server.config import settings
from server.error_taxonomy import classify_error
from server.logging import log_upstream_error

try:
    import psycopg
    from psycopg import sql
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - optional dependency fallback
    psycopg = None  # type: ignore[assignment]
    sql = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]


SUPPORTED_ROUTE_PROFILES = ("drive", "walk", "cycle", "emergency", "multimodal")


@dataclass(frozen=True)
class RouteGraphMetadata:
    ready: bool
    reason: str | None
    graph_version: str | None
    built_at: str | None
    source_product: str | None
    source_release_date: str | None
    source_download_id: str | None
    source_download_name: str | None
    source_license: str | None
    profiles: list[str]
    node_count: int | None
    edge_count: int | None
    provenance_path: str | None
    provenance: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "reason": self.reason,
            "graphVersion": self.graph_version,
            "builtAt": self.built_at,
            "sourceProduct": self.source_product,
            "sourceReleaseDate": self.source_release_date,
            "sourceDownloadId": self.source_download_id,
            "sourceDownloadName": self.source_download_name,
            "sourceLicense": self.source_license,
            "supportedProfiles": self.profiles,
            "nodeCount": self.node_count,
            "edgeCount": self.edge_count,
            "provenancePath": self.provenance_path,
            "provenance": self.provenance,
        }


class RouteGraph:
    def __init__(
        self,
        *,
        dsn: str,
        schema: str,
        edges_table: str,
        nodes_table: str,
        metadata_table: str,
        restrictions_table: str,
        turn_restrictions_table: str,
        runtime_dir: str,
        provenance_file: str,
        max_stops: int,
        soft_avoid_penalty_seconds: float,
    ) -> None:
        self._dsn = dsn
        self._schema = schema
        self._edges_table = edges_table
        self._nodes_table = nodes_table
        self._metadata_table = metadata_table
        self._restrictions_table = restrictions_table
        self._turn_restrictions_table = turn_restrictions_table
        self._runtime_dir = runtime_dir
        self._provenance_file = provenance_file
        self._max_stops = max_stops
        self._soft_avoid_penalty_seconds = max(0.0, soft_avoid_penalty_seconds)

    @classmethod
    def from_settings(cls) -> "RouteGraph":
        dsn = getattr(settings, "ROUTE_GRAPH_DSN", "") or getattr(settings, "BOUNDARY_CACHE_DSN", "")
        return cls(
            dsn=dsn,
            schema=getattr(settings, "ROUTE_GRAPH_SCHEMA", "routing"),
            edges_table=getattr(settings, "ROUTE_GRAPH_EDGES_TABLE", "graph_edges"),
            nodes_table=getattr(settings, "ROUTE_GRAPH_NODES_TABLE", "graph_nodes"),
            metadata_table=getattr(settings, "ROUTE_GRAPH_METADATA_TABLE", "graph_metadata"),
            restrictions_table=getattr(settings, "ROUTE_GRAPH_RESTRICTIONS_TABLE", "edge_restrictions"),
            turn_restrictions_table=getattr(
                settings,
                "ROUTE_GRAPH_TURN_RESTRICTIONS_TABLE",
                "turn_restrictions",
            ),
            runtime_dir=getattr(settings, "ROUTE_GRAPH_RUNTIME_DIR", "data/runtime/routing"),
            provenance_file=getattr(settings, "ROUTE_GRAPH_PROVENANCE_FILE", "os_mrn_downloads.json"),
            max_stops=int(getattr(settings, "ROUTE_GRAPH_MAX_STOPS", 8)),
            soft_avoid_penalty_seconds=float(
                getattr(settings, "ROUTE_GRAPH_SOFT_AVOID_PENALTY_SECONDS", 180.0)
            ),
        )

    def enabled(self) -> bool:
        return bool(getattr(settings, "ROUTE_GRAPH_ENABLED", False)) and bool(self._dsn)

    def max_stops(self) -> int:
        return self._max_stops

    def _connect(self):
        if psycopg is None:
            raise RuntimeError("psycopg is not installed")
        return psycopg.connect(self._dsn, row_factory=dict_row)

    def _log_graph_error(self, detail: str) -> None:
        log_upstream_error(
            service="route_graph",
            code="ROUTE_GRAPH_ERROR",
            detail=detail,
            error_category=classify_error("ROUTE_GRAPH_ERROR"),
        )

    def _extensions_ready(self, conn: Any) -> tuple[bool, str | None]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT extname
                FROM pg_extension
                WHERE extname IN ('postgis', 'pgrouting');
                """
            )
            rows = cur.fetchall() or []
        present = {str(row.get("extname")) for row in rows if isinstance(row, dict)}
        if "postgis" not in present:
            return False, "postgis_missing"
        if "pgrouting" not in present:
            return False, "pgrouting_missing"
        return True, None

    def _table_identifier(self, table_name: str):
        if sql is None:
            raise RuntimeError("psycopg sql module unavailable")
        return sql.Identifier(self._schema, table_name)

    def _load_provenance(self) -> tuple[str | None, dict[str, Any] | None]:
        path = Path(self._runtime_dir).expanduser() / self._provenance_file
        if not path.exists():
            return None, None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return str(path), None
        return str(path), payload if isinstance(payload, dict) else None

    def _load_metadata(self, conn: Any) -> RouteGraphMetadata:
        metadata_table = self._table_identifier(self._metadata_table)
        provenance_path, provenance = self._load_provenance()
        query = sql.SQL(
            """
            SELECT
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
            FROM {table}
            ORDER BY is_active DESC, built_at DESC NULLS LAST
            LIMIT 1;
            """
        ).format(table=metadata_table)
        with conn.cursor() as cur:
            cur.execute(query)
            row = cur.fetchone()
        if not row:
            return RouteGraphMetadata(
                ready=False,
                reason="graph_metadata_missing",
                graph_version=None,
                built_at=None,
                source_product=None,
                source_release_date=None,
                source_download_id=None,
                source_download_name=None,
                source_license=None,
                profiles=list(SUPPORTED_ROUTE_PROFILES),
                node_count=None,
                edge_count=None,
                provenance_path=provenance_path,
                provenance=provenance,
            )
        built_at = row.get("built_at")
        source_release_date = row.get("source_release_date")
        profiles = row.get("profiles")
        if not isinstance(profiles, list) or not profiles:
            profiles = list(SUPPORTED_ROUTE_PROFILES)
        status = str(row.get("status") or "").strip().lower()
        ready = status in {"", "ready", "active"}
        row_provenance_path = row.get("provenance_path")
        return RouteGraphMetadata(
            ready=ready,
            reason=None if ready else (status or "graph_not_ready"),
            graph_version=str(row.get("graph_version")) if row.get("graph_version") else None,
            built_at=_isoformat_datetime(built_at),
            source_product=str(row.get("source_product")) if row.get("source_product") else None,
            source_release_date=_isoformat_date(source_release_date),
            source_download_id=str(row.get("source_download_id"))
            if row.get("source_download_id")
            else None,
            source_download_name=str(row.get("source_download_name"))
            if row.get("source_download_name")
            else None,
            source_license=str(row.get("source_license")) if row.get("source_license") else None,
            profiles=[str(profile) for profile in profiles],
            node_count=_as_int(row.get("node_count")),
            edge_count=_as_int(row.get("edge_count")),
            provenance_path=str(row_provenance_path) if row_provenance_path else provenance_path,
            provenance=provenance,
        )

    def descriptor(self) -> dict[str, Any]:
        graph = self._descriptor_metadata()
        return {
            "supportedProfiles": list(SUPPORTED_ROUTE_PROFILES),
            "constraintTypes": ["avoidAreas", "avoidIds", "softAvoid"],
            "maxStops": self._max_stops,
            "graph": graph.as_dict(),
        }

    def _descriptor_metadata(self) -> RouteGraphMetadata:
        provenance_path, provenance = self._load_provenance()
        if not self.enabled():
            return RouteGraphMetadata(
                ready=False,
                reason="route_graph_disabled",
                graph_version=None,
                built_at=None,
                source_product=None,
                source_release_date=None,
                source_download_id=None,
                source_download_name=None,
                source_license=None,
                profiles=list(SUPPORTED_ROUTE_PROFILES),
                node_count=None,
                edge_count=None,
                provenance_path=provenance_path,
                provenance=provenance,
            )
        if psycopg is None or sql is None:
            return RouteGraphMetadata(
                ready=False,
                reason="psycopg_missing",
                graph_version=None,
                built_at=None,
                source_product=None,
                source_release_date=None,
                source_download_id=None,
                source_download_name=None,
                source_license=None,
                profiles=list(SUPPORTED_ROUTE_PROFILES),
                node_count=None,
                edge_count=None,
                provenance_path=provenance_path,
                provenance=provenance,
            )
        try:
            with self._connect() as conn:
                extensions_ready, reason = self._extensions_ready(conn)
                if not extensions_ready:
                    return RouteGraphMetadata(
                        ready=False,
                        reason=reason,
                        graph_version=None,
                        built_at=None,
                        source_product=None,
                        source_release_date=None,
                        source_download_id=None,
                        source_download_name=None,
                        source_license=None,
                        profiles=list(SUPPORTED_ROUTE_PROFILES),
                        node_count=None,
                        edge_count=None,
                        provenance_path=provenance_path,
                        provenance=provenance,
                    )
                return self._load_metadata(conn)
        except Exception as exc:
            self._log_graph_error(str(exc))
            return RouteGraphMetadata(
                ready=False,
                reason="route_graph_error",
                graph_version=None,
                built_at=None,
                source_product=None,
                source_release_date=None,
                source_download_id=None,
                source_download_name=None,
                source_license=None,
                profiles=list(SUPPORTED_ROUTE_PROFILES),
                node_count=None,
                edge_count=None,
                provenance_path=provenance_path,
                provenance=provenance,
            )

    def compute_route(
        self,
        resolved_stops: list[dict[str, Any]],
        *,
        profile: str,
        constraints: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        descriptor = self._descriptor_metadata()
        if not descriptor.ready:
            return 503, {
                "isError": True,
                "code": "ROUTE_GRAPH_NOT_READY",
                "message": "Route graph is not ready.",
                "graph": descriptor.as_dict(),
            }
        if len(resolved_stops) < 2:
            return 400, {
                "isError": True,
                "code": "INVALID_INPUT",
                "message": "At least two resolved stops are required.",
            }
        try:
            with self._connect() as conn:
                metadata = self._load_metadata(conn)
                node_snaps = [
                    self._nearest_node(conn, stop["lat"], stop["lon"])
                    for stop in resolved_stops
                ]
                enriched_stops = []
                for stop, snap in zip(resolved_stops, node_snaps, strict=False):
                    enriched = dict(stop)
                    enriched["nodeId"] = snap["nodeId"]
                    enriched["distanceToNetworkMeters"] = snap["distanceMeters"]
                    enriched_stops.append(enriched)

                all_legs: list[dict[str, Any]] = []
                all_segments: list[dict[str, Any]] = []
                for index in range(len(enriched_stops) - 1):
                    start = enriched_stops[index]
                    end = enriched_stops[index + 1]
                    segments = self._run_leg(
                        conn,
                        start_node=int(start["nodeId"]),
                        end_node=int(end["nodeId"]),
                        profile=profile,
                        constraints=constraints or {},
                    )
                    if not segments:
                        return 404, {
                            "isError": True,
                            "code": "NO_ROUTE",
                            "message": "No valid route found between the requested stops.",
                            "graph": metadata.as_dict(),
                            "resolvedStops": enriched_stops,
                        }
                    leg = self._build_leg(index=index, start=start, end=end, segments=segments)
                    all_legs.append(leg)
                    all_segments.extend(segments)

                edge_ids = [segment["edgeId"] for segment in all_segments]
                transition_pairs = [
                    (all_segments[idx]["edgeId"], all_segments[idx + 1]["edgeId"])
                    for idx in range(len(all_segments) - 1)
                ]
                warnings = self._restriction_warnings(conn, edge_ids=edge_ids, transitions=transition_pairs)
                route_geometry = _merge_segment_geometries(all_segments)
                mode_changes = _mode_changes(all_segments)
                return 200, {
                    "resolvedStops": enriched_stops,
                    "distanceMeters": round(sum(leg["distanceMeters"] for leg in all_legs), 3),
                    "durationSeconds": round(sum(leg["durationSeconds"] for leg in all_legs), 3),
                    "route": {
                        "type": "Feature",
                        "geometry": route_geometry,
                        "properties": {
                            "profile": profile,
                            "graphVersion": metadata.graph_version,
                        },
                    },
                    "legs": all_legs,
                    "steps": [step for leg in all_legs for step in leg["steps"]],
                    "modeChanges": mode_changes,
                    "warnings": warnings,
                    "restrictions": warnings,
                    "graph": metadata.as_dict(),
                }
        except Exception as exc:
            self._log_graph_error(str(exc))
            return 500, {
                "isError": True,
                "code": "ROUTE_GRAPH_ERROR",
                "message": "Route graph execution failed.",
            }

    def _nearest_node(self, conn: Any, lat: float, lon: float) -> dict[str, Any]:
        nodes_table = self._table_identifier(self._nodes_table)
        query = sql.SQL(
            """
            SELECT
                id,
                ST_Distance(
                    geom::geography,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
                ) AS distance_m
            FROM {table}
            ORDER BY geom <-> ST_SetSRID(ST_MakePoint(%s, %s), 4326)
            LIMIT 1;
            """
        ).format(table=nodes_table)
        with conn.cursor() as cur:
            cur.execute(query, (lon, lat, lon, lat))
            row = cur.fetchone()
        if not row:
            raise RuntimeError("Route graph nodes are unavailable")
        return {
            "nodeId": int(row["id"]),
            "distanceMeters": round(float(row.get("distance_m") or 0.0), 3),
        }

    def _run_leg(
        self,
        conn: Any,
        *,
        start_node: int,
        end_node: int,
        profile: str,
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        edges_sql = self._edge_sql(conn, profile=profile, constraints=constraints)
        edges_table = self._table_identifier(self._edges_table)
        query = sql.SQL(
            """
            WITH path AS (
                SELECT *
                FROM pgr_dijkstra(%s, %s, %s, true)
            ),
            segments AS (
                SELECT
                    path.seq,
                    path.path_seq,
                    path.node AS start_node,
                    LEAD(path.node) OVER (ORDER BY path.seq) AS end_node,
                    path.edge,
                    path.cost,
                    path.agg_cost,
                    edge.id AS edge_id,
                    edge.external_id,
                    edge.name,
                    edge.mode,
                    COALESCE(edge.length_m, ST_Length(edge.geom::geography)) AS length_m,
                    CASE
                        WHEN LEAD(path.node) OVER (ORDER BY path.seq) = edge.source
                             AND path.node = edge.target
                        THEN ST_AsGeoJSON(ST_Reverse(edge.geom))
                        ELSE ST_AsGeoJSON(edge.geom)
                    END AS geometry,
                    COALESCE(edge.flags, '{{}}'::jsonb) AS flags
                FROM path
                JOIN {edges_table} edge
                  ON edge.id = path.edge
                WHERE path.edge <> -1
            )
            SELECT *
            FROM segments
            ORDER BY seq;
            """
        ).format(edges_table=edges_table)
        with conn.cursor() as cur:
            cur.execute(query, (edges_sql, start_node, end_node))
            rows = cur.fetchall() or []
        out: list[dict[str, Any]] = []
        for row in rows:
            geometry = row.get("geometry")
            try:
                geometry_obj = json.loads(geometry) if isinstance(geometry, str) else None
            except json.JSONDecodeError:
                geometry_obj = None
            out.append(
                {
                    "edgeId": int(row["edge_id"]),
                    "externalId": row.get("external_id"),
                    "name": row.get("name") or "Unnamed segment",
                    "mode": row.get("mode") or profile,
                    "distanceMeters": round(float(row.get("length_m") or 0.0), 3),
                    "durationSeconds": round(float(row.get("cost") or 0.0), 3),
                    "geometry": geometry_obj,
                    "flags": row.get("flags") or {},
                }
            )
        return out

    def _edge_sql(self, conn: Any, *, profile: str, constraints: dict[str, Any]) -> str:
        if sql is None:
            raise RuntimeError("psycopg sql module unavailable")
        edges_table = self._table_identifier(self._edges_table)
        cost_column = sql.Identifier(f"cost_{profile}")
        reverse_cost_column = sql.Identifier(f"reverse_cost_{profile}")
        hard_predicate, soft_predicate = self._avoid_predicates(conn, constraints)
        hard_clause = sql.SQL("FALSE") if not hard_predicate else sql.SQL(hard_predicate)
        soft_clause = sql.SQL("FALSE") if not soft_predicate else sql.SQL(soft_predicate)
        penalty = sql.Literal(self._soft_avoid_penalty_seconds)
        query = sql.SQL(
            """
            SELECT
                id,
                source,
                target,
                CASE
                    WHEN COALESCE({cost_column}, -1) < 0 THEN -1
                    WHEN {hard_clause} THEN -1
                    ELSE COALESCE({cost_column}, -1)
                         + CASE WHEN {soft_clause} THEN {penalty} ELSE 0 END
                END AS cost,
                CASE
                    WHEN COALESCE({reverse_cost_column}, -1) < 0 THEN -1
                    WHEN {hard_clause} THEN -1
                    ELSE COALESCE({reverse_cost_column}, -1)
                         + CASE WHEN {soft_clause} THEN {penalty} ELSE 0 END
                END AS reverse_cost
            FROM {edges_table}
            """
        ).format(
            edges_table=edges_table,
            cost_column=cost_column,
            reverse_cost_column=reverse_cost_column,
            hard_clause=hard_clause,
            soft_clause=soft_clause,
            penalty=penalty,
        )
        return query.as_string(conn)

    def _avoid_predicates(self, conn: Any, constraints: dict[str, Any]) -> tuple[str | None, str | None]:
        if sql is None:
            raise RuntimeError("psycopg sql module unavailable")
        soft_avoid = bool(constraints.get("softAvoid", True))
        raw_ids = constraints.get("avoidIds") if isinstance(constraints, dict) else None
        raw_areas = constraints.get("avoidAreas") if isinstance(constraints, dict) else None
        predicates: list[str] = []

        if isinstance(raw_ids, list):
            ids = [str(item).strip() for item in raw_ids if str(item).strip()]
            if ids:
                literals = sql.SQL(", ").join(sql.Literal(item) for item in ids).as_string(conn)
                predicates.append(
                    f"(id::text IN ({literals}) OR COALESCE(external_id, '') IN ({literals}))"
                )

        if isinstance(raw_areas, list):
            for area in raw_areas:
                polygon_wkt = _polygon_wkt(area)
                if not polygon_wkt:
                    continue
                literal = sql.Literal(polygon_wkt).as_string(conn)
                predicates.append(
                    f"ST_Intersects(geom, ST_GeomFromText({literal}, 4326))"
                )

        if not predicates:
            return None, None
        predicate = " OR ".join(predicates)
        return (None, predicate) if soft_avoid else (predicate, None)

    def _restriction_warnings(
        self,
        conn: Any,
        *,
        edge_ids: list[int],
        transitions: list[tuple[int, int]],
    ) -> list[dict[str, Any]]:
        warnings: list[dict[str, Any]] = []
        warnings.extend(self._edge_restriction_rows(conn, edge_ids))
        warnings.extend(self._turn_restriction_rows(conn, transitions))
        return warnings

    def _edge_restriction_rows(self, conn: Any, edge_ids: list[int]) -> list[dict[str, Any]]:
        if not edge_ids:
            return []
        restrictions_table = self._table_identifier(self._restrictions_table)
        query = sql.SQL(
            """
            SELECT DISTINCT
                restriction_id,
                edge_id,
                category,
                severity,
                message
            FROM {table}
            WHERE edge_id = ANY(%s)
            ORDER BY severity DESC NULLS LAST, restriction_id NULLS LAST;
            """
        ).format(table=restrictions_table)
        try:
            with conn.cursor() as cur:
                cur.execute(query, (edge_ids,))
                rows = cur.fetchall() or []
        except Exception:
            return []
        return [
            {
                "type": "edge_restriction",
                "restrictionId": row.get("restriction_id"),
                "edgeId": row.get("edge_id"),
                "category": row.get("category"),
                "severity": row.get("severity"),
                "message": row.get("message"),
            }
            for row in rows
            if isinstance(row, dict)
        ]

    def _turn_restriction_rows(
        self,
        conn: Any,
        transitions: list[tuple[int, int]],
    ) -> list[dict[str, Any]]:
        if not transitions:
            return []
        turn_table = self._table_identifier(self._turn_restrictions_table)
        query = sql.SQL(
            """
            SELECT
                from_edge,
                to_edge,
                via_node,
                restriction_type,
                message
            FROM {table}
            WHERE active IS DISTINCT FROM FALSE
              AND (from_edge, to_edge) IN (
                SELECT pair.from_edge, pair.to_edge
                FROM unnest(%s::bigint[], %s::bigint[]) AS pair(from_edge, to_edge)
              );
            """
        ).format(table=turn_table)
        from_edges = [pair[0] for pair in transitions]
        to_edges = [pair[1] for pair in transitions]
        try:
            with conn.cursor() as cur:
                cur.execute(query, (from_edges, to_edges))
                rows = cur.fetchall() or []
        except Exception:
            return []
        return [
            {
                "type": "turn_restriction",
                "fromEdge": row.get("from_edge"),
                "toEdge": row.get("to_edge"),
                "viaNode": row.get("via_node"),
                "restrictionType": row.get("restriction_type"),
                "message": row.get("message"),
            }
            for row in rows
            if isinstance(row, dict)
        ]

    def _build_leg(
        self,
        *,
        index: int,
        start: dict[str, Any],
        end: dict[str, Any],
        segments: list[dict[str, Any]],
    ) -> dict[str, Any]:
        steps = _build_steps(segments, leg_index=index)
        geometry = _merge_segment_geometries(segments)
        return {
            "legIndex": index,
            "from": start.get("label") or start.get("query") or start.get("uprn") or "Start",
            "to": end.get("label") or end.get("query") or end.get("uprn") or "End",
            "distanceMeters": round(sum(segment["distanceMeters"] for segment in segments), 3),
            "durationSeconds": round(sum(segment["durationSeconds"] for segment in segments), 3),
            "geometry": geometry,
            "steps": steps,
        }


def _build_steps(segments: list[dict[str, Any]], *, leg_index: int) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for segment in segments:
        if (
            current
            and current["name"] == segment["name"]
            and current["mode"] == segment["mode"]
        ):
            current["distanceMeters"] += segment["distanceMeters"]
            current["durationSeconds"] += segment["durationSeconds"]
            current["edgeIds"].append(segment["edgeId"])
            current["geometry"] = _merge_line_geometries(current["geometry"], segment.get("geometry"))
            continue
        current = {
            "legIndex": leg_index,
            "instruction": f"Follow {segment['name']}",
            "name": segment["name"],
            "mode": segment["mode"],
            "distanceMeters": segment["distanceMeters"],
            "durationSeconds": segment["durationSeconds"],
            "edgeIds": [segment["edgeId"]],
            "geometry": segment.get("geometry"),
        }
        steps.append(current)
    for step in steps:
        step["distanceMeters"] = round(float(step["distanceMeters"]), 3)
        step["durationSeconds"] = round(float(step["durationSeconds"]), 3)
    return steps


def _mode_changes(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    previous_mode: str | None = None
    for index, segment in enumerate(segments):
        mode = str(segment.get("mode") or "")
        if previous_mode and mode and mode != previous_mode:
            changes.append(
                {
                    "index": index,
                    "fromMode": previous_mode,
                    "toMode": mode,
                    "edgeId": segment.get("edgeId"),
                }
            )
        if mode:
            previous_mode = mode
    return changes


def _merge_segment_geometries(segments: list[dict[str, Any]]) -> dict[str, Any]:
    geometry: dict[str, Any] | None = None
    for segment in segments:
        geometry = _merge_line_geometries(geometry, segment.get("geometry"))
    return geometry or {"type": "LineString", "coordinates": []}


def _merge_line_geometries(
    current: dict[str, Any] | None,
    segment_geometry: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not segment_geometry or segment_geometry.get("type") != "LineString":
        return current
    coords = segment_geometry.get("coordinates")
    if not isinstance(coords, list):
        return current
    if not current:
        return {"type": "LineString", "coordinates": coords}
    existing = current.get("coordinates")
    if not isinstance(existing, list):
        return {"type": "LineString", "coordinates": coords}
    merged = list(existing)
    next_coords = list(coords)
    if merged and next_coords and merged[-1] == next_coords[0]:
        merged.extend(next_coords[1:])
    else:
        merged.extend(next_coords)
    return {"type": "LineString", "coordinates": merged}


def _polygon_wkt(value: Any) -> str | None:
    if isinstance(value, list) and len(value) == 4:
        try:
            min_lon, min_lat, max_lon, max_lat = [float(item) for item in value]
        except (TypeError, ValueError):
            return None
        return (
            "POLYGON(("
            f"{min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, "
            f"{min_lon} {max_lat}, {min_lon} {min_lat}"
            "))"
        )
    if isinstance(value, dict):
        value_type = str(value.get("type") or "").lower()
        coordinates = value.get("coordinates")
        if value_type == "polygon":
            return _ringed_polygon_wkt(coordinates)
        if value_type == "multipolygon" and isinstance(coordinates, list):
            rings = []
            for polygon in coordinates:
                polygon_wkt = _ringed_polygon_wkt(polygon)
                if not polygon_wkt:
                    continue
                rings.append(polygon_wkt.replace("POLYGON", "", 1))
            if rings:
                return f"MULTIPOLYGON({', '.join(rings)})"
    return None


def _ringed_polygon_wkt(coordinates: Any) -> str | None:
    if not isinstance(coordinates, list) or not coordinates:
        return None
    rings: list[str] = []
    for ring in coordinates:
        if not isinstance(ring, list) or len(ring) < 4:
            return None
        points: list[str] = []
        for point in ring:
            if not isinstance(point, list) or len(point) < 2:
                return None
            try:
                lon = float(point[0])
                lat = float(point[1])
            except (TypeError, ValueError):
                return None
            points.append(f"{lon} {lat}")
        rings.append(f"({', '.join(points)})")
    return f"POLYGON({', '.join(rings)})"


def _isoformat_datetime(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return None


def _isoformat_date(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return None


def _as_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
