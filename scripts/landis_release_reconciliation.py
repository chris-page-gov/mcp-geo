#!/usr/bin/env python3
"""Generate a LandIS release-surface reconciliation manifest.

This compares three public-facing surfaces:

1. The authenticated ArcGIS portal inventory already captured in-repo.
2. Public LandIS website dataset/service pages that are linked from the
   current navigation but are not present in the mirrored ArcGIS portal slice.
3. Matching `data.gov.uk` package metadata where it exists.

The output is a machine-readable JSON manifest that records:
- public page reachability and page size
- whether each item appears in the current portal inventory
- likely related portal datasets, where known
- candidate `data.gov.uk` package matches
- a conservative approximate size estimate when a public page is dataset-like
  and there is a defensible analogue in the portal inventory
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parent.parent
PORTAL_INVENTORY_PATH = (
    REPO_ROOT / "research" / "landis-data-source" / "landis_portal_inventory_2026-04-04.json"
)
DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "research" / "landis-data-source" / "landis_release_reconciliation_2026-04-05.json"
)
DEFAULT_ARCHIVE_MANIFEST_PATH = Path(
    "/Users/crpage/Data/landis_portal_archive_2026-04-04/download_manifest.json"
)
USER_AGENT = "Mozilla/5.0 (compatible; mcp-geo landis release reconciliation)"


@dataclass(frozen=True)
class PublicItem:
    family: str
    kind: str
    name: str
    url: str
    data_gov_query: str
    related_portal_titles: tuple[str, ...]
    estimate_kind: str
    estimate_note: str


PUBLIC_ITEMS: tuple[PublicItem, ...] = (
    PublicItem(
        family="natmap",
        kind="dataset",
        name="NATMAP HOST",
        url="https://www.landis.org.uk/data/nmhost.cfm",
        data_gov_query="cranfield natmap host",
        related_portal_titles=("NationalSoilMap", "NATMAPtopsoiltexture", "NATMAPavailablewater"),
        estimate_kind="portal_analogue_polygon",
        estimate_note=(
            "Public page says this is derived from the National Soil Map; use the current "
            "portal thematic NATMAP polygon layers as the nearest size analogue."
        ),
    ),
    PublicItem(
        family="natmap",
        kind="dataset",
        name="NATMAP wetness",
        url="https://www.landis.org.uk/data/nmwetness.cfm",
        data_gov_query="cranfield natmap wetness",
        related_portal_titles=("NationalSoilMap", "NATMAPtopsoiltexture", "NATMAPavailablewater"),
        estimate_kind="portal_analogue_polygon",
        estimate_note=(
            "Public page says this is derived from the National Soil Map; use the current "
            "portal thematic NATMAP polygon layers as the nearest size analogue."
        ),
    ),
    PublicItem(
        family="soilseries",
        kind="dataset",
        name="Series Hydrology",
        url="https://www.landis.org.uk/data/sshydrology.cfm",
        data_gov_query="cranfield soil series hydrology",
        related_portal_titles=("SOILSERIES", "HORIZONhydraulics"),
        estimate_kind="portal_analogue_series_table",
        estimate_note=(
            "Public page describes series-level tabular data; use SOILSERIES rather than "
            "the larger horizon tables as the nearest size analogue."
        ),
    ),
    PublicItem(
        family="soilseries",
        kind="dataset",
        name="Series Agronomy",
        url="https://www.landis.org.uk/data/ssagronomy.cfm",
        data_gov_query="cranfield soil series agronomy",
        related_portal_titles=("SOILSERIES",),
        estimate_kind="portal_analogue_series_table",
        estimate_note=(
            "Public page describes series-level tabular data; use SOILSERIES as the nearest "
            "size analogue."
        ),
    ),
    PublicItem(
        family="soilseries",
        kind="dataset",
        name="Series Pesticides",
        url="https://www.landis.org.uk/data/sspesticides.cfm",
        data_gov_query="cranfield soil series pesticide",
        related_portal_titles=("SOILSERIES",),
        estimate_kind="portal_analogue_series_table",
        estimate_note=(
            "Public page describes series-level tabular data; use SOILSERIES as the nearest "
            "size analogue."
        ),
    ),
    PublicItem(
        family="soilseries",
        kind="dataset",
        name="Series Leacs",
        url="https://www.landis.org.uk/data/ssleacs.cfm",
        data_gov_query="cranfield soil series leacs",
        related_portal_titles=("SOILSERIES",),
        estimate_kind="portal_analogue_series_table",
        estimate_note=(
            "Public page describes series-level tabular data; use SOILSERIES as the nearest "
            "size analogue."
        ),
    ),
    PublicItem(
        family="peat",
        kind="dataset",
        name="Lowland Peat",
        url="https://www.landis.org.uk/data/lowlandpeat.cfm",
        data_gov_query="cranfield peat lowland",
        related_portal_titles=("NATMAPcarbon", "NATMAPsoilscapes"),
        estimate_kind="unknown",
        estimate_note=(
            "Public page confirms a dedicated lowland peat project, but the current sources "
            "do not provide a defensible machine-size estimate."
        ),
    ),
    PublicItem(
        family="service",
        kind="service",
        name="Soilscapes Viewer",
        url="https://www.landis.org.uk/services/soilscapes.cfm",
        data_gov_query="cranfield soilscapes",
        related_portal_titles=("NATMAPsoilscapes",),
        estimate_kind="service",
        estimate_note="Interactive/public service page rather than a directly sized dataset.",
    ),
    PublicItem(
        family="service",
        kind="service",
        name="Soils Guide",
        url="https://www.landis.org.uk/soilsguide/index.cfm",
        data_gov_query="cranfield soils guide landis",
        related_portal_titles=(),
        estimate_kind="service",
        estimate_note="Documentation/service page rather than a directly sized dataset.",
    ),
    PublicItem(
        family="service",
        kind="service",
        name="Soil Alerts",
        url="https://www.landis.org.uk/soilsguide/soil_alerts.cfm",
        data_gov_query="cranfield soil alerts landis",
        related_portal_titles=(),
        estimate_kind="service",
        estimate_note="Decision-support service page rather than a directly sized dataset.",
    ),
    PublicItem(
        family="service",
        kind="service",
        name="CatchIS",
        url="https://www.landis.org.uk/services/catchis.cfm",
        data_gov_query="cranfield catchis",
        related_portal_titles=(),
        estimate_kind="service",
        estimate_note="Toolkit/service page rather than a directly sized dataset.",
    ),
    PublicItem(
        family="service",
        kind="service",
        name="Leacs",
        url="https://www.landis.org.uk/services/leacs.cfm",
        data_gov_query="cranfield leacs",
        related_portal_titles=("SOILSERIES",),
        estimate_kind="service",
        estimate_note="Application/service page; not a directly sized release package.",
    ),
    PublicItem(
        family="service",
        kind="service",
        name="Treefit",
        url="https://www.landis.org.uk/services/treefit.cfm",
        data_gov_query="cranfield treefit",
        related_portal_titles=(),
        estimate_kind="service",
        estimate_note="Service/database page rather than a directly sized dataset.",
    ),
)


def fetch_text(url: str) -> tuple[int | str, str, str | None]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=30) as response:
            payload = response.read().decode("utf-8", "ignore")
            return response.status, payload, None
    except HTTPError as exc:
        return exc.code, "", str(exc)
    except URLError as exc:
        return "url_error", "", str(exc)


def strip_html(source: str) -> str:
    cleaned = re.sub(r"<script.*?</script>", " ", source, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    return " ".join(cleaned.split())


def page_probe(item: PublicItem) -> dict[str, Any]:
    status, html_text, error = fetch_text(item.url)
    if not html_text:
        return {"status": status, "error": error}
    title_match = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    text = strip_html(html_text)
    return {
        "status": status,
        "pageBytes": len(html_text.encode("utf-8", "ignore")),
        "pageTitle": re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None,
        "mentionsDownload": bool(re.search(r"\b(download|extract|licen[sc]e)\b", text, re.I)),
        "mentionsFeatureServer": bool(re.search(r"FeatureServer|ArcGIS", html_text, re.I)),
        "mentionsPublicData": bool(re.search(r"open access|open licence|public data", text, re.I)),
        "textSample": text[:600],
    }


def data_gov_probe(query: str) -> dict[str, Any]:
    url = f"https://www.data.gov.uk/api/3/action/package_search?rows=10&q={quote(query)}"
    status, payload, error = fetch_text(url)
    if not payload:
        return {"status": status, "error": error}
    data = json.loads(payload)
    results = data["result"]["results"]
    return {
        "status": status,
        "query": query,
        "count": data["result"]["count"],
        "matches": [
            {
                "title": result.get("title"),
                "name": result.get("name"),
                "licenseTitle": result.get("license_title"),
                "metadataModified": result.get("metadata_modified"),
                "url": f"https://www.data.gov.uk/dataset/{result.get('name')}",
            }
            for result in results
        ],
    }


def load_portal_inventory(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_archive_counts(path: Path | None) -> dict[str, int]:
    if path is None or not path.exists():
        return {}
    payload = json.loads(path.read_text())
    counts: dict[str, int] = {}
    for result in payload.get("results", []):
        export = result.get("serviceExport") or {}
        total = 0
        for layer in export.get("layers", []) or []:
            total += int(layer.get("recordCount", 0) or 0)
        for table in export.get("tables", []) or []:
            total += int(table.get("recordCount", 0) or 0)
        if result.get("title"):
            counts[result["title"]] = total
    return counts


def portal_record_count(item: dict[str, Any], archive_counts: dict[str, int]) -> int:
    title = item.get("title")
    if title and title in archive_counts:
        return archive_counts[title]
    summary = item.get("serviceSummary") or {}
    total = 0
    for layer in summary.get("layers", []) or []:
        total += int(layer.get("recordCount", 0) or 0)
    for table in summary.get("tables", []) or []:
        total += int(table.get("recordCount", 0) or 0)
    return total


def normalized_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if len(token) >= 3}


def data_gov_match_score(item_name: str, candidate_title: str) -> float:
    item_tokens = normalized_tokens(item_name)
    title_tokens = normalized_tokens(candidate_title)
    if not item_tokens or not title_tokens:
        return 0.0
    overlap = item_tokens & title_tokens
    return len(overlap) / len(item_tokens)


def data_gov_probe(query: str, item_name: str) -> dict[str, Any]:
    url = f"https://www.data.gov.uk/api/3/action/package_search?rows=20&q={quote(query)}"
    status, payload, error = fetch_text(url)
    if not payload:
        return {"status": status, "error": error}
    data = json.loads(payload)
    results = data["result"]["results"]
    matches = []
    for result in results:
        title = result.get("title") or ""
        score = data_gov_match_score(item_name, title)
        if score <= 0:
            continue
        matches.append(
            {
                "title": title,
                "name": result.get("name"),
                "licenseTitle": result.get("license_title"),
                "metadataModified": result.get("metadata_modified"),
                "score": round(score, 3),
                "url": f"https://www.data.gov.uk/dataset/{result.get('name')}",
            }
        )
    matches.sort(key=lambda item: (-item["score"], item["title"]))
    return {
        "status": status,
        "query": query,
        "count": data["result"]["count"],
        "matches": matches[:10],
    }


def size_estimate(
    public_item: PublicItem,
    portal_by_title: dict[str, dict[str, Any]],
    archive_counts: dict[str, int],
) -> dict[str, Any]:
    related = []
    for title in public_item.related_portal_titles:
        if title in portal_by_title:
            candidate = portal_by_title[title]
            related.append(
                {
                    "title": title,
                    "classification": candidate.get("classification"),
                    "serviceType": candidate.get("type"),
                    "recordCount": portal_record_count(candidate, archive_counts),
                }
            )
    if public_item.estimate_kind == "portal_analogue_polygon" and related:
        counts = [entry["recordCount"] for entry in related if entry["recordCount"] > 0]
        counts = sorted(counts)
        return {
            "classification": "inferred",
            "approximateRecordCount": counts[1:] if len(counts) > 2 else counts,
            "approximateOrderOfMagnitude": "10^4 polygons",
            "basis": public_item.estimate_note,
            "relatedPortalDatasets": related,
        }
    if public_item.estimate_kind == "portal_analogue_series_table" and related:
        counts = [entry["recordCount"] for entry in related if entry["recordCount"] > 0]
        counts = sorted(counts)
        return {
            "classification": "inferred",
            "approximateRecordCount": counts,
            "approximateOrderOfMagnitude": "10^3 rows",
            "basis": public_item.estimate_note,
            "relatedPortalDatasets": related,
        }
    return {
        "classification": "unknown" if public_item.estimate_kind == "unknown" else "not_applicable",
        "approximateRecordCount": None,
        "approximateOrderOfMagnitude": None,
        "basis": public_item.estimate_note,
        "relatedPortalDatasets": related,
    }


def build_manifest(archive_manifest_path: Path | None = None) -> dict[str, Any]:
    portal_inventory = load_portal_inventory(PORTAL_INVENTORY_PATH)
    portal_items = portal_inventory["items"]
    portal_by_title = {item["title"]: item for item in portal_items}
    archive_counts = load_archive_counts(archive_manifest_path)

    entries: list[dict[str, Any]] = []
    for public_item in PUBLIC_ITEMS:
        exact_portal_match = portal_by_title.get(public_item.name)
        related_portal = [
            {
                "title": title,
                "exists": title in portal_by_title,
                "recordCount": (
                    portal_record_count(portal_by_title[title], archive_counts)
                    if title in portal_by_title
                    else None
                ),
            }
            for title in public_item.related_portal_titles
        ]
        entries.append(
            {
                "family": public_item.family,
                "kind": public_item.kind,
                "name": public_item.name,
                "publicUrl": public_item.url,
                "publicProbe": page_probe(public_item),
                "portalPresence": {
                    "exactTitlePresent": exact_portal_match is not None,
                    "exactTitle": exact_portal_match.get("title") if exact_portal_match else None,
                    "relatedPortalDatasets": related_portal,
                },
                "dataGovProbe": data_gov_probe(public_item.data_gov_query, public_item.name),
                "approximateSize": size_estimate(public_item, portal_by_title, archive_counts),
            }
        )

    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "portalInventoryPath": str(PORTAL_INVENTORY_PATH),
        "archiveManifestPath": str(archive_manifest_path) if archive_manifest_path else None,
        "portalSummary": {
            "totalItems": len(portal_items),
            "dataSources": sum(1 for item in portal_items if item.get("classification") == "data_source"),
            "nonDataItems": sum(1 for item in portal_items if item.get("classification") != "data_source"),
        },
        "scopeNote": (
            "This manifest focuses on public LandIS website items that are currently linked in the "
            "official navigation but are not present as exact titles in the mirrored ArcGIS portal slice."
        ),
        "entries": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--archive-manifest", type=Path, default=DEFAULT_ARCHIVE_MANIFEST_PATH)
    args = parser.parse_args()
    manifest = build_manifest(args.archive_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
