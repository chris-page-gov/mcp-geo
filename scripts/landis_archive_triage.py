from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORTAL_ARCHIVE = Path.home() / "Data" / "landis_portal_archive_2026-04-04"
DEFAULT_FULL_RELEASE_ARCHIVE = Path.home() / "Data" / "landis_full_release_archive_2026-04-05"
DEFAULT_OUTPUT = (
    ROOT / "research" / "landis-data-source" / "landis_archive_triage_2026-04-05.json"
)

_FAMILY_RULES: list[tuple[str, str, str]] = [
    ("NATMAP", "natmap", "warehouse_next"),
    ("NationalSoilMap", "natmap", "warehouse_next"),
    ("SOILSERIES", "natmap", "deferred_join"),
    ("HORIZON", "natmap", "deferred_join"),
    ("NSI", "nsi", "warehouse_next"),
    ("AUGER", "auger", "deferred"),
    ("SoilCatalogue", "catalogue", "resource_only"),
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _classify_item(title: str, item_type: str) -> tuple[str, str]:
    for prefix, family, surfacing in _FAMILY_RULES:
        if title.startswith(prefix):
            return family, surfacing
    if item_type in {"Web Map", "Web Experience", "Hub Page", "Hub Site Application"}:
        return "archive", "resource_only"
    if item_type == "Feature Service":
        return "archive", "archive_only"
    return "archive", "resource_only"


def _record_count(summary: dict[str, Any]) -> int | None:
    layers = summary.get("layers")
    if not isinstance(layers, list) or not layers:
        return None
    counts = [layer.get("recordCount") for layer in layers if isinstance(layer, dict)]
    ints = [int(value) for value in counts if isinstance(value, int)]
    return sum(ints) if ints else None


def _geometry_type(summary: dict[str, Any]) -> str | None:
    layers = summary.get("layers")
    if not isinstance(layers, list) or not layers:
        return None
    first = layers[0]
    return str(first.get("geometryType")) if isinstance(first, dict) and first.get("geometryType") else None


def _portal_items(portal_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for category in ("data_source", "application", "documentation", "supporting_asset"):
        category_dir = portal_root / category
        if not category_dir.exists():
            continue
        for item_dir in sorted(path for path in category_dir.iterdir() if path.is_dir()):
            inventory_path = item_dir / "inventory_record.json"
            if not inventory_path.exists():
                continue
            inventory = _read_json(inventory_path)
            detail_path = item_dir / "item_detail.json"
            detail = _read_json(detail_path) if detail_path.exists() else {}
            download_summary_path = item_dir / "feature_service" / "download_summary.json"
            summary = _read_json(download_summary_path) if download_summary_path.exists() else {}
            title = str(inventory.get("title") or item_dir.name)
            item_type = str(inventory.get("type") or category)
            runtime_family, surfacing_class = _classify_item(title, item_type)
            items.append(
                {
                    "archiveId": str(inventory.get("id") or item_dir.name),
                    "title": title,
                    "aliases": [item_dir.name],
                    "itemType": item_type,
                    "archiveCategory": category,
                    "runtimeFamily": runtime_family,
                    "surfacingClass": surfacing_class,
                    "recordCount": _record_count(summary),
                    "geometryType": _geometry_type(summary),
                    "serviceUrl": summary.get("serviceUrl") or inventory.get("url"),
                    "tags": detail.get("tags", []),
                    "snippet": detail.get("snippet") or inventory.get("snippet"),
                    "itemPath": str(item_dir),
                    "inventoryPath": str(inventory_path),
                    "metadataPath": str(detail_path) if detail_path.exists() else None,
                    "downloadSummaryPath": (
                        str(download_summary_path) if download_summary_path.exists() else None
                    ),
                }
            )
    return items


def build_manifest(portal_root: Path, full_release_root: Path) -> dict[str, Any]:
    full_manifest = _read_json(full_release_root / "full_release_manifest.json")
    return {
        "version": "2026-04-05-phase2",
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "portalArchiveDir": str(portal_root),
        "fullReleaseArchiveDir": str(full_release_root),
        "portalItems": _portal_items(portal_root),
        "supplementaryPublicItems": full_manifest.get("publicItems", []),
        "supplementaryDataGovPackages": full_manifest.get("dataGovPackages", []),
        "summary": {
            "portalItems": len(_portal_items(portal_root)),
            "supplementaryPublicItems": len(full_manifest.get("publicItems", [])),
            "supplementaryDataGovPackages": len(full_manifest.get("dataGovPackages", [])),
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a machine-readable LandIS archive triage manifest.")
    parser.add_argument("--portal-archive", type=Path, default=DEFAULT_PORTAL_ARCHIVE)
    parser.add_argument("--full-release-archive", type=Path, default=DEFAULT_FULL_RELEASE_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest = build_manifest(
        args.portal_archive.expanduser().resolve(),
        args.full_release_archive.expanduser().resolve(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
