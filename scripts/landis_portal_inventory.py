#!/usr/bin/env python3
"""Build an authenticated LandIS portal inventory from an Atlas browser session.

This script is intended for local operator use after signing into the LandIS
portal in ChatGPT Atlas on macOS. It discovers an ArcGIS access token from the
Atlas Chromium history database, enumerates the protected LandIS portal catalog,
enriches key item types, and writes both JSON and Markdown inventories.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import sqlite3
import tempfile
import urllib.parse
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ATLAS_HISTORY_ROOTS = (
    Path.home() / "Library/Application Support/com.openai.atlas/browser-data/host",
    Path.home() / "Library/Application Support/com.openai.atlas.beta/browser-data/host",
)
ATLAS_TOKEN_REGEX = re.compile(r"access_token=([^&#]+)")
ARCGIS_ORG_ID = "BsCa1SurMySYByZ3"
PORTAL_BASE_URL = "https://portal.landis.org.uk"
SHARING_BASE_URL = "https://cranfield-portal.maps.arcgis.com/sharing/rest"
SERVICE_TIMEOUT = 30


def _service_timeout() -> int:
    value = os.environ.get("LANDIS_PORTAL_HTTP_TIMEOUT")
    if not value:
        return SERVICE_TIMEOUT
    try:
        timeout = int(value)
    except ValueError:
        return SERVICE_TIMEOUT
    return timeout if timeout > 0 else SERVICE_TIMEOUT

DOCUMENTATION_TYPES = {"Hub Page", "PDF", "StoryMap"}
APPLICATION_TYPES = {
    "Desktop Style",
    "Form",
    "Hub Site Application",
    "Web Experience",
    "Web Map",
}
DATA_SOURCE_TYPES = {"Feature Service"}
SUPPORTING_ASSET_TYPES = {"Image"}


class InventoryError(RuntimeError):
    """Raised when the inventory cannot be completed."""


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "mcp-geo-landis-inventory/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=_service_timeout()) as response:
        payload = response.read()
    return json.loads(payload.decode("utf-8"))


def _strip_html(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _copy_history_db() -> Path:
    candidates = [
        history_path
        for root in ATLAS_HISTORY_ROOTS
        if root.exists()
        for history_path in root.glob("user-*/History")
    ]
    if not candidates:
        raise InventoryError("No Atlas history database found.")
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    temp = tempfile.NamedTemporaryFile(prefix="atlas-history-", suffix=".sqlite", delete=False)
    temp.close()
    shutil.copy2(latest, temp.name)
    return Path(temp.name)


def discover_atlas_token() -> str:
    temp_history = _copy_history_db()
    connection = sqlite3.connect(temp_history)
    try:
        rows = connection.execute(
            """
            select url
            from urls
            where url like '%access_token=%'
            order by last_visit_time desc
            limit 50
            """
        ).fetchall()
    finally:
        connection.close()
        temp_history.unlink(missing_ok=True)
    for (url,) in rows:
        match = ATLAS_TOKEN_REGEX.search(url)
        if match:
            return urllib.parse.unquote(match.group(1))
    raise InventoryError(
        "No LandIS ArcGIS access token found in Atlas history. Sign into the LandIS portal in Atlas first."
    )


def arcgis_get(path: str, token: str, **params: Any) -> dict[str, Any]:
    query = {"f": "json", "token": token, **params}
    return _fetch_json(f"{SHARING_BASE_URL}{path}?{urllib.parse.urlencode(query, doseq=True)}")


def arcgis_service_get(url: str, token: str, **params: Any) -> dict[str, Any]:
    query = {"f": "json", "token": token, **params}
    return _fetch_json(f"{url}?{urllib.parse.urlencode(query, doseq=True)}")


def list_catalog_items(token: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    start = 1
    while True:
        payload = arcgis_get(
            "/search",
            token,
            q=f"orgid:{ARCGIS_ORG_ID}",
            start=start,
            num=100,
            sortField="title",
            sortOrder="asc",
        )
        page_items = payload.get("results", [])
        items.extend(page_items)
        next_start = payload.get("nextStart", -1)
        if next_start == -1 or not page_items:
            return items
        start = next_start


def _public_item_url(item: dict[str, Any]) -> str | None:
    item_type = item.get("type")
    if item_type == "Hub Site Application":
        return PORTAL_BASE_URL
    if item_type == "Hub Page":
        slug = item.get("properties", {}).get("slug") or ""
        page_slug = slug.split("|")[-1] if slug else ""
        return f"{PORTAL_BASE_URL}/pages/{page_slug}" if page_slug else None
    if item.get("url"):
        return item["url"]
    if item_type in {"PDF", "Image", "Form", "Desktop Style"}:
        return f"{SHARING_BASE_URL}/content/items/{item['id']}/data"
    return f"https://cranfield-portal.maps.arcgis.com/home/item.html?id={item['id']}"


def _extract_markdown_headings(data: dict[str, Any]) -> list[str]:
    headings: list[str] = []
    markdown_blobs: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "markdown" and isinstance(value, str):
                    markdown_blobs.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    for blob in markdown_blobs:
        for match in re.finditer(r"<h[1-6][^>]*>(.*?)</h[1-6]>", blob, re.IGNORECASE | re.DOTALL):
            heading = _strip_html(match.group(1))
            if heading and heading not in headings:
                headings.append(heading)
    return headings


def _extract_web_experience_summary(data: dict[str, Any]) -> dict[str, Any]:
    page_labels = []
    for page in data.get("pages", {}).values():
        label = page.get("label")
        if label:
            page_labels.append(label)
    widget_count = len(data.get("widgets", {}))
    return {
        "pageLabels": page_labels,
        "widgetCount": widget_count,
    }


def _extract_web_map_summary(data: dict[str, Any]) -> dict[str, Any]:
    operational_layers = data.get("operationalLayers", [])
    base_map_layers = data.get("baseMap", {}).get("baseMapLayers", [])
    return {
        "operationalLayerCount": len(operational_layers),
        "operationalLayers": [
            {
                "title": layer.get("title"),
                "url": layer.get("url"),
                "itemId": layer.get("itemId"),
                "layerType": layer.get("layerType"),
            }
            for layer in operational_layers
        ],
        "baseMapLayerCount": len(base_map_layers),
    }


def _extract_service_summary(url: str, token: str) -> dict[str, Any]:
    service = arcgis_service_get(url, token)
    return {
        "serviceDescription": _strip_html(service.get("serviceDescription")),
        "capabilities": service.get("capabilities"),
        "maxRecordCount": service.get("maxRecordCount"),
        "spatialReference": service.get("spatialReference"),
        "layers": [
            {"id": layer.get("id"), "name": layer.get("name")}
            for layer in service.get("layers", [])
        ],
        "tables": [
            {"id": table.get("id"), "name": table.get("name")}
            for table in service.get("tables", [])
        ],
    }


def enrich_item(item: dict[str, Any], token: str) -> dict[str, Any]:
    detail = arcgis_get(f"/content/items/{item['id']}", token)
    enriched: dict[str, Any] = {
        "id": detail["id"],
        "title": detail.get("title"),
        "type": detail.get("type"),
        "owner": detail.get("owner"),
        "created": detail.get("created"),
        "modified": detail.get("modified"),
        "snippet": _strip_html(detail.get("snippet")),
        "description": _strip_html(detail.get("description")),
        "tags": detail.get("tags") or [],
        "typeKeywords": detail.get("typeKeywords") or [],
        "licenseInfo": _strip_html(detail.get("licenseInfo")),
        "accessInformation": _strip_html(detail.get("accessInformation")),
        "documentation": _strip_html(detail.get("documentation")),
        "url": detail.get("url"),
        "publicUrl": _public_item_url(detail),
        "arcgisItemUrl": f"https://cranfield-portal.maps.arcgis.com/home/item.html?id={detail['id']}",
        "dataUrl": f"{SHARING_BASE_URL}/content/items/{detail['id']}/data",
        "properties": detail.get("properties") or {},
        "categories": detail.get("categories") or [],
        "classification": (
            "data_source"
            if detail.get("type") in DATA_SOURCE_TYPES
            else "documentation"
            if detail.get("type") in DOCUMENTATION_TYPES
            else "application"
            if detail.get("type") in APPLICATION_TYPES
            else "supporting_asset"
            if detail.get("type") in SUPPORTING_ASSET_TYPES
            else "other"
        ),
    }

    item_type = enriched["type"]
    if item_type == "Feature Service" and enriched["url"]:
        enriched["serviceSummary"] = _extract_service_summary(enriched["url"], token)
    elif item_type == "Hub Page":
        try:
            page_data = arcgis_get(f"/content/items/{detail['id']}/data", token)
        except Exception as exc:  # pragma: no cover - defensive reporting
            enriched["dataError"] = str(exc)
        else:
            enriched["hubPageSummary"] = {
                "headings": _extract_markdown_headings(page_data),
            }
    elif item_type == "Web Map":
        try:
            map_data = arcgis_get(f"/content/items/{detail['id']}/data", token)
        except Exception as exc:  # pragma: no cover - defensive reporting
            enriched["dataError"] = str(exc)
        else:
            enriched["webMapSummary"] = _extract_web_map_summary(map_data)
    elif item_type == "Web Experience":
        try:
            experience_data = arcgis_get(f"/content/items/{detail['id']}/data", token)
        except Exception as exc:  # pragma: no cover - defensive reporting
            enriched["dataError"] = str(exc)
        else:
            enriched["webExperienceSummary"] = _extract_web_experience_summary(experience_data)

    return enriched


def build_inventory(token: str) -> dict[str, Any]:
    raw_items = list_catalog_items(token)
    enriched_items = [enrich_item(item, token) for item in raw_items]
    type_counts = Counter(item["type"] for item in enriched_items)
    class_counts = Counter(item["classification"] for item in enriched_items)
    return {
        "generatedAt": datetime.now(UTC).isoformat(),
        "source": {
            "portalUrl": PORTAL_BASE_URL,
            "orgId": ARCGIS_ORG_ID,
            "authentication": "Atlas browser session token discovered from local authenticated history",
            "notes": [
                "No bearer token is written to the output files.",
                "PublicUrl values may still require authenticated access depending on the ArcGIS item type.",
            ],
        },
        "summary": {
            "totalItems": len(enriched_items),
            "typeCounts": dict(sorted(type_counts.items())),
            "classificationCounts": dict(sorted(class_counts.items())),
        },
        "items": enriched_items,
    }


def _iso_from_epoch_ms(value: int | None) -> str | None:
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, tz=UTC).isoformat()


def _render_feature_service(item: dict[str, Any]) -> list[str]:
    service = item.get("serviceSummary", {})
    layer_names = ", ".join(layer["name"] for layer in service.get("layers", [])) or "none"
    table_names = ", ".join(table["name"] for table in service.get("tables", [])) or "none"
    lines = [
        f"### {item['title']}",
        f"- Item ID: `{item['id']}`",
        f"- Owner: `{item['owner']}`",
        f"- Modified: `{_iso_from_epoch_ms(item.get('modified'))}`",
        f"- Service URL: {item.get('url')}",
        f"- Public/portal URL: {item.get('publicUrl')}",
        f"- Tags: {', '.join(item.get('tags') or []) or 'none'}",
        f"- Summary: {item.get('snippet') or item.get('description') or 'n/a'}",
        f"- Capabilities: {service.get('capabilities') or 'n/a'}",
        f"- Layers: {layer_names}",
        f"- Tables: {table_names}",
    ]
    if service.get("serviceDescription"):
        lines.append(f"- Service description: {service['serviceDescription']}")
    return lines


def _render_documentation_item(item: dict[str, Any]) -> list[str]:
    lines = [
        f"### {item['title']}",
        f"- Item ID: `{item['id']}`",
        f"- Type: `{item['type']}`",
        f"- Owner: `{item['owner']}`",
        f"- Modified: `{_iso_from_epoch_ms(item.get('modified'))}`",
        f"- Public/portal URL: {item.get('publicUrl')}",
        f"- Item URL: {item.get('arcgisItemUrl')}",
        f"- Tags: {', '.join(item.get('tags') or []) or 'none'}",
        f"- Summary: {item.get('snippet') or item.get('description') or 'n/a'}",
    ]
    headings = item.get("hubPageSummary", {}).get("headings", [])
    if headings:
        lines.append(f"- Extracted headings: {', '.join(headings)}")
    if item.get("licenseInfo"):
        lines.append(f"- Licence note: {item['licenseInfo']}")
    return lines


def _render_application_item(item: dict[str, Any]) -> list[str]:
    lines = [
        f"### {item['title']}",
        f"- Item ID: `{item['id']}`",
        f"- Type: `{item['type']}`",
        f"- Owner: `{item['owner']}`",
        f"- Modified: `{_iso_from_epoch_ms(item.get('modified'))}`",
        f"- Public/portal URL: {item.get('publicUrl')}",
        f"- Tags: {', '.join(item.get('tags') or []) or 'none'}",
        f"- Summary: {item.get('snippet') or item.get('description') or 'n/a'}",
    ]
    if "webMapSummary" in item:
        layer_titles = ", ".join(
            layer.get("title") or "untitled" for layer in item["webMapSummary"]["operationalLayers"]
        )
        lines.append(f"- Operational layers: {layer_titles or 'none'}")
    if "webExperienceSummary" in item:
        page_labels = ", ".join(item["webExperienceSummary"].get("pageLabels", [])) or "none"
        lines.append(f"- Experience pages: {page_labels}")
        lines.append(
            f"- Widget count: {item['webExperienceSummary'].get('widgetCount', 0)}"
        )
    if item.get("licenseInfo"):
        lines.append(f"- Licence note: {item['licenseInfo']}")
    return lines


def _render_supporting_assets(items: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Title | Item ID | Owner | Public URL |",
        "| --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(
            f"| {item['title']} | `{item['id']}` | `{item['owner']}` | {item.get('publicUrl') or ''} |"
        )
    return lines


def build_markdown(inventory: dict[str, Any]) -> str:
    items = inventory["items"]
    feature_services = [item for item in items if item["classification"] == "data_source"]
    documentation_items = [item for item in items if item["classification"] == "documentation"]
    application_items = [item for item in items if item["classification"] == "application"]
    supporting_assets = [item for item in items if item["classification"] == "supporting_asset"]

    lines = [
        "# LandIS Portal Inventory",
        "",
        f"Generated: `{inventory['generatedAt']}`",
        "",
        "This inventory was generated from an authenticated LandIS portal session in ChatGPT Atlas. "
        "It records the accessible ArcGIS catalog items without storing the session token.",
        "",
        "## Summary",
        "",
        f"- Portal URL: {inventory['source']['portalUrl']}",
        f"- ArcGIS organisation ID: `{inventory['source']['orgId']}`",
        f"- Total accessible items: `{inventory['summary']['totalItems']}`",
        f"- Data sources: `{inventory['summary']['classificationCounts'].get('data_source', 0)}`",
        f"- Documentation items: `{inventory['summary']['classificationCounts'].get('documentation', 0)}`",
        f"- Applications/maps/styles/forms: `{inventory['summary']['classificationCounts'].get('application', 0)}`",
        f"- Supporting media assets: `{inventory['summary']['classificationCounts'].get('supporting_asset', 0)}`",
        "",
        "### Type Counts",
        "",
    ]
    for item_type, count in sorted(inventory["summary"]["typeCounts"].items()):
        lines.append(f"- `{item_type}`: `{count}`")

    lines.extend(
        [
            "",
            "## Data Sources",
            "",
            "The following Feature Services are the authoritative machine-readable data sources currently "
            "visible through the authenticated LandIS portal route.",
            "",
        ]
    )
    for item in feature_services:
        lines.extend(_render_feature_service(item))
        lines.append("")

    lines.extend(
        [
            "## Documentation",
            "",
            "These items provide user-facing explanatory material, licence notes, and curated guidance.",
            "",
        ]
    )
    for item in documentation_items:
        lines.extend(_render_documentation_item(item))
        lines.append("")

    lines.extend(
        [
            "## Applications, Maps, And Supporting Portal Items",
            "",
            "These items are not raw datasets, but they expose or organize the portal content.",
            "",
        ]
    )
    for item in application_items:
        lines.extend(_render_application_item(item))
        lines.append("")

    lines.extend(
        [
            "## Supporting Media Assets",
            "",
            "The portal also contains image assets used by StoryMaps and pages. They are listed here for completeness.",
            "",
        ]
    )
    lines.extend(_render_supporting_assets(supporting_assets))
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("research/landis-data-source/landis_portal_inventory_2026-04-04.json"),
        help="Path for the machine-readable inventory JSON output.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/reports/landis_portal_inventory_2026-04-04.md"),
        help="Path for the human-readable Markdown inventory output.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Optional ArcGIS bearer token. If omitted, discover from Atlas history.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    token = args.token or discover_atlas_token()
    inventory = build_inventory(token)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(build_markdown(inventory), encoding="utf-8")
    print(
        json.dumps(
            {
                "outputJson": str(args.output_json),
                "outputMd": str(args.output_md),
                "totalItems": inventory["summary"]["totalItems"],
                "typeCounts": inventory["summary"]["typeCounts"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
