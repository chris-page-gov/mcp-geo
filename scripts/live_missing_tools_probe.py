from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from server.main import app

DEFAULT_INPUT = "data/evaluation_results_live_review_2026-02-21_after_patch2_full.json"
DEFAULT_OUTPUT = "data/live_missing_tools_probe_report.json"

_AUTH_CODES = {
    "NO_API_KEY",
    "OS_API_KEY_MISSING",
    "OS_API_KEY_INVALID",
    "OS_API_KEY_EXPIRED",
    "ACCESS_DENIED",
    "UNAUTHORIZED",
}

_DEPENDENCY_ORDER = [
    "os_downloads.list_products",
    "os_downloads.get_product",
    "os_downloads.list_product_downloads",
    "os_downloads.list_data_packages",
    "os_downloads.prepare_export",
    "os_downloads.get_export",
    "os_offline.descriptor",
    "os_offline.get",
    "os_landscape.find",
    "os_landscape.get",
    "os_features.wfs_capabilities",
    "os_features.wfs_archive_capabilities",
    "os_linked_ids.identifiers",
    "os_linked_ids.feature_types",
    "os_linked_ids.product_version_info",
    "os_maps.wmts_capabilities",
    "os_maps.raster_tile",
    "os_mcp.select_toolsets",
    "os_net.rinex_years",
    "os_net.station_get",
    "os_net.station_log",
    "os_places.radius",
    "os_places.polygon",
    "os_qgis.vector_tile_profile",
    "os_qgis.export_geopackage_descriptor",
    "os_tiles_ota.collections",
    "os_tiles_ota.conformance",
    "os_tiles_ota.tilematrixsets",
]


@dataclass
class ProbeContext:
    downloads_product_id: str | None = None
    downloads_export_id: str | None = None
    offline_pack_id: str | None = None
    landscape_id: str | None = None


def _load_missing_tools(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    missing = payload.get("utilization", {}).get("missingTools", [])
    if not isinstance(missing, list):
        raise ValueError(f"Invalid missingTools structure in {path}")
    cleaned = [tool for tool in missing if isinstance(tool, str) and tool.strip()]
    return sorted(set(cleaned))


def _ordered_missing_tools(missing: list[str]) -> list[str]:
    ordered: list[str] = []
    known = set(missing)
    for tool in _DEPENDENCY_ORDER:
        if tool in known:
            ordered.append(tool)
    for tool in missing:
        if tool not in ordered:
            ordered.append(tool)
    return ordered


def _payload_for(tool: str, ctx: ProbeContext) -> dict[str, Any] | None:
    if tool == "os_downloads.list_products":
        return {}
    if tool == "os_downloads.get_product":
        return {"productId": ctx.downloads_product_id or "openroads"}
    if tool == "os_downloads.list_product_downloads":
        return {"productId": ctx.downloads_product_id or "openroads"}
    if tool == "os_downloads.list_data_packages":
        return {}
    if tool == "os_downloads.prepare_export":
        return {"productId": ctx.downloads_product_id or "openroads"}
    if tool == "os_downloads.get_export":
        if not ctx.downloads_export_id:
            return None
        return {"exportId": ctx.downloads_export_id}
    if tool == "os_offline.descriptor":
        return {}
    if tool == "os_offline.get":
        if not ctx.offline_pack_id:
            return None
        return {"packId": ctx.offline_pack_id}
    if tool == "os_landscape.find":
        return {"text": "Bowland", "limit": 5}
    if tool == "os_landscape.get":
        if not ctx.landscape_id:
            return None
        return {"id": ctx.landscape_id, "includeGeometry": True}
    if tool == "os_features.wfs_capabilities":
        return {}
    if tool == "os_features.wfs_archive_capabilities":
        return {}
    if tool == "os_linked_ids.identifiers":
        return {"identifier": "100021892956"}
    if tool == "os_linked_ids.feature_types":
        return {"featureType": "RoadLink", "identifier": "osgb5000005158744708"}
    if tool == "os_linked_ids.product_version_info":
        return {"correlationMethod": "BLPU_UPRN_RoadLink_TOID_9"}
    if tool == "os_maps.wmts_capabilities":
        return {}
    if tool == "os_maps.raster_tile":
        return {"style": "Road_3857", "z": 7, "x": 63, "y": 42}
    if tool == "os_mcp.select_toolsets":
        return {"query": "maps and boundaries", "maxTools": 10}
    if tool == "os_net.rinex_years":
        return {}
    if tool == "os_net.station_get":
        return {"stationId": "AMER"}
    if tool == "os_net.station_log":
        return {"stationId": "AMER"}
    if tool == "os_places.radius":
        return {"lat": 51.5074, "lon": -0.1278, "radiusMeters": 250}
    if tool == "os_places.polygon":
        return {
            "polygon": [
                [-0.141, 51.499],
                [-0.112, 51.499],
                [-0.112, 51.518],
                [-0.141, 51.518],
                [-0.141, 51.499],
            ]
        }
    if tool == "os_qgis.vector_tile_profile":
        return {"style": "OS_VTS_3857_Light"}
    if tool == "os_qgis.export_geopackage_descriptor":
        return {"sourceResourceUri": "resource://mcp-geo/os-exports/demo.json"}
    if tool == "os_tiles_ota.collections":
        return {}
    if tool == "os_tiles_ota.conformance":
        return {}
    if tool == "os_tiles_ota.tilematrixsets":
        return {}
    return None


def _classify(status_code: int, body: Any) -> str:
    code: str | None = None
    is_error = False
    if isinstance(body, dict):
        raw_code = body.get("code")
        code = raw_code if isinstance(raw_code, str) else None
        is_error = bool(body.get("isError"))

    if status_code == 200 and not is_error:
        return "pass"
    if status_code in {401, 403} or (code in _AUTH_CODES):
        return "blocked_auth"
    if status_code == 404 or code == "NOT_FOUND":
        return "data_not_found"
    if status_code == 400 or code == "INVALID_INPUT":
        return "invalid_input"
    if status_code == 429 or code == "RATE_LIMITED":
        return "rate_limited"
    if status_code >= 500:
        return "upstream_or_server_error"
    if is_error:
        return "tool_error"
    return "unknown"


def _post_tool_call(client: TestClient, tool: str, arguments: dict[str, Any]) -> tuple[int, Any]:
    body = {"tool": tool, **arguments}
    response = client.post("/tools/call", json=body)
    try:
        payload = response.json()
    except Exception:  # pragma: no cover - defensive for non-JSON transport errors
        payload = {"raw": response.text}
    return response.status_code, payload


def _refresh_context(tool: str, body: Any, ctx: ProbeContext) -> None:
    if not isinstance(body, dict):
        return
    if tool == "os_downloads.list_products":
        products = body.get("products")
        if isinstance(products, list):
            for product in products:
                if isinstance(product, dict):
                    candidate = product.get("id")
                    if isinstance(candidate, str) and candidate.strip():
                        ctx.downloads_product_id = candidate
                        break
    elif tool == "os_downloads.prepare_export":
        export_id = body.get("exportId")
        if isinstance(export_id, str) and export_id.strip():
            ctx.downloads_export_id = export_id
    elif tool == "os_offline.descriptor":
        packs = body.get("packs")
        if isinstance(packs, list):
            for pack in packs:
                if isinstance(pack, dict):
                    candidate = pack.get("id")
                    if isinstance(candidate, str) and candidate.strip():
                        ctx.offline_pack_id = candidate
                        break
    elif tool == "os_landscape.find":
        results = body.get("results")
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    candidate = result.get("id")
                    if isinstance(candidate, str) and candidate.strip():
                        ctx.landscape_id = candidate
                        break


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        outcome = row.get("outcome", "unknown")
        counts[outcome] = counts.get(outcome, 0) + 1
    total = len(rows)
    passing = counts.get("pass", 0)
    return {
        "total": total,
        "pass": passing,
        "passPercent": round((passing / total) * 100, 2) if total else 0.0,
        "outcomeCounts": counts,
    }


def run_probe(input_path: Path, output_path: Path) -> dict[str, Any]:
    missing_tools = _ordered_missing_tools(_load_missing_tools(input_path))
    ctx = ProbeContext()
    rows: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for tool in missing_tools:
            payload = _payload_for(tool, ctx)
            if payload is None:
                rows.append(
                    {
                        "tool": tool,
                        "payload": None,
                        "status": None,
                        "outcome": "fixture_missing",
                        "code": None,
                        "message": "No payload fixture available",
                    }
                )
                continue

            status_code, body = _post_tool_call(client, tool, payload)
            _refresh_context(tool, body, ctx)
            code = None
            if isinstance(body, dict):
                raw_code = body.get("code")
                if isinstance(raw_code, str):
                    code = raw_code
            message = (
                body.get("message")
                if isinstance(body, dict) and isinstance(body.get("message"), str)
                else None
            )
            rows.append(
                {
                    "tool": tool,
                    "payload": payload,
                    "status": status_code,
                    "outcome": _classify(status_code, body),
                    "code": code,
                    "message": message,
                }
            )

    report = {
        "checkedAtUtc": datetime.now(UTC).isoformat(),
        "input": str(input_path),
        "summary": _summarize(rows),
        "results": rows,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe tools missing from evaluation harness utilization output."
    )
    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Harness JSON file to read missing tools from.",
    )
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Path to write probe JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_probe(Path(args.input), Path(args.output))
    summary = report["summary"]
    print(
        "Missing-tool probe: "
        f"{summary['pass']}/{summary['total']} pass "
        f"({summary['passPercent']}%). "
        f"Outcomes: {summary['outcomeCounts']}"
    )
    print(f"Saved report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
