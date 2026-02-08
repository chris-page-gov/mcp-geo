#!/usr/bin/env python3
"""Refresh the local Ordnance Survey API + downloads catalog index.

This is analogous to scripts/ons_catalog_refresh.py, but targets OS endpoints
and includes download-only products (via OS Downloads API).

Usage:
  python3 scripts/os_catalog_refresh.py
  python3 scripts/os_catalog_refresh.py --output resources/os_catalog.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.config import settings

OS_API_ROOT = "https://api.os.uk"

# Stable sample identifiers used to build probe requests without needing chained calls.
_SAMPLE_UPRN = "100023336956"  # 10 Downing Street (stable UPRN)
_SAMPLE_USRN = "8400071"
_SAMPLE_ROADLINK_TOID = "osgb5000005158744708"
_SAMPLE_CORRELATION_METHOD = "BLPU_UPRN_RoadLink_TOID_9"

_SAMPLE_BNG_POINT = "530000,180000"
_SAMPLE_WGS84_POINT = "51.503,-0.127"  # lat,lon ordering for Places radius
_SAMPLE_BBOX_STR = "-0.13,51.49,-0.11,51.51"
# NGD items endpoints can be very sensitive to bbox size in dense areas. Keep this probe bbox
# intentionally small so the catalog live validation run is stable and bounded.
_SAMPLE_NGD_ITEMS_BBOX_STR = "-0.127,51.503,-0.126,51.504"
_SAMPLE_BNG_BBOX_STR = "529750,179750,530250,180250"  # < 1km^2 (Places bbox constraint)
_SAMPLE_POLYGON = {
    "type": "Polygon",
    "coordinates": [
        [
            [-0.15, 51.49],
            [-0.12, 51.49],
            [-0.12, 51.51],
            [-0.15, 51.51],
            [-0.15, 51.49],
        ]
    ],
}


def _resolve_path(raw: str) -> Path:
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / raw
    return path


def _strip_key_param(url: str) -> str:
    parts = urlsplit(url)
    query = [(k, v) for (k, v) in parse_qsl(parts.query, keep_blank_values=True) if k.lower() != "key"]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _fetch_json(url: str, api_key: str, params: dict[str, Any] | None = None) -> Any:
    merged = dict(params or {})
    if api_key:
        merged["key"] = api_key
    full_url = url
    if merged:
        full_url = f"{url}?{urlencode(merged)}"
    req = Request(full_url, headers={"User-Agent": "mcp-geo-os-catalog/0"})
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body = exc.read()
        try:
            detail = json.loads(body)
        except Exception:
            detail = body[:200].decode("utf-8", "ignore")
        raise RuntimeError(f"OS API error {exc.code} while fetching {url}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"OS API connection error while fetching {url}: {exc}") from exc


def _extract_docs(landing: Any) -> list[str]:
    if not isinstance(landing, dict):
        return []
    docs: list[str] = []
    for link in landing.get("links", []) or []:
        if not isinstance(link, dict):
            continue
        if link.get("rel") != "documentation":
            continue
        href = link.get("href")
        if isinstance(href, str) and href.strip():
            docs.append(_strip_key_param(href.strip()))
    return docs


def _add_item(items: list[dict[str, Any]], entry: dict[str, Any]) -> None:
    entry_id = entry.get("id")
    if not isinstance(entry_id, str) or not entry_id.strip():
        raise ValueError("Catalog item missing id")
    if any(existing.get("id") == entry_id for existing in items):
        raise ValueError(f"Duplicate catalog id: {entry_id}")
    items.append(entry)


def _probe(
    *,
    item_id: str,
    title: str,
    description: str,
    category: str,
    url: str,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    body: Any | None = None,
    required: bool = True,
    expects: dict[str, Any] | None = None,
    docs: list[str] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item_id,
        "kind": "probe",
        "category": category,
        "title": title,
        "description": description,
        "required": required,
        "request": {
            "method": method,
            "url": _strip_key_param(url),
            "params": params or {},
        },
    }
    if body is not None:
        payload["request"]["body"] = body
    if expects:
        payload["expects"] = expects
    if docs:
        payload["docs"] = docs
    if meta:
        payload["meta"] = meta
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh OS API/downloads catalog index")
    parser.add_argument(
        "--output",
        default=getattr(settings, "OS_CATALOG_PATH", "resources/os_catalog.json"),
        help="Output JSON path (default: settings OS_CATALOG_PATH)",
    )
    args = parser.parse_args()

    api_key = (getattr(settings, "OS_API_KEY", "") or os.getenv("OS_API_KEY", "")).strip()
    if not api_key:
        raise SystemExit("OS_API_KEY is required to build the OS catalog.")

    # Landing pages (used primarily to extract canonical documentation links).
    places_landing = _fetch_json(f"{OS_API_ROOT}/search/places/v1", api_key)
    names_landing = _fetch_json(f"{OS_API_ROOT}/search/names/v1", api_key)
    links_landing = _fetch_json(f"{OS_API_ROOT}/search/links/v1", api_key)
    match_landing = _fetch_json(f"{OS_API_ROOT}/search/match/v1", api_key)
    ngd_landing = _fetch_json(f"{OS_API_ROOT}/features/ngd", api_key)
    wfs_landing = _fetch_json(f"{OS_API_ROOT}/features/v1", api_key)
    raster_landing = _fetch_json(f"{OS_API_ROOT}/maps/raster", api_key)
    vector_landing = _fetch_json(f"{OS_API_ROOT}/maps/vector/v1", api_key)
    ota_landing = _fetch_json(f"{OS_API_ROOT}/maps/vector/ngd", api_key)
    downloads_landing = _fetch_json(f"{OS_API_ROOT}/downloads", api_key)
    osnet_landing = _fetch_json(f"{OS_API_ROOT}/positioning/osnet/v1", api_key)

    items: list[dict[str, Any]] = []

    # Search: Places
    places_docs = _extract_docs(places_landing)
    _add_item(
        items,
        _probe(
            item_id="os.search.places.find",
            title="OS Places API: Find",
            description="Free text search for addresses and places.",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/find",
            params={"query": "10 Downing Street", "maxresults": 1, "output_srs": "WGS84"},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.postcode",
            title="OS Places API: Postcode",
            description="Lookup addresses and UPRNs by postcode.",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/postcode",
            params={"postcode": "SW1A 2AA", "maxresults": 1, "output_srs": "WGS84"},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.uprn",
            title="OS Places API: UPRN",
            description="Lookup a single address by UPRN.",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/uprn",
            params={"uprn": _SAMPLE_UPRN, "output_srs": "WGS84"},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
            meta={"uprn": _SAMPLE_UPRN},
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.nearest",
            title="OS Places API: Nearest",
            description="Nearest address record to a British National Grid point.",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/nearest",
            params={"point": _SAMPLE_BNG_POINT, "radius": 100},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.bbox",
            title="OS Places API: BBox",
            description="Search within a British National Grid bbox (< 1km^2).",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/bbox",
            params={"bbox": _SAMPLE_BNG_BBOX_STR, "maxresults": 1},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.radius",
            title="OS Places API: Radius",
            description="Search within a radius of a WGS84 point (lat,lon).",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/radius",
            params={
                "point": _SAMPLE_WGS84_POINT,
                "radius": 100,
                "srs": "WGS84",
                "output_srs": "WGS84",
                "maxresults": 1,
            },
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.places.polygon",
            title="OS Places API: Polygon",
            description="Search within a GeoJSON polygon (POST body is the Polygon object).",
            category="search",
            url=f"{OS_API_ROOT}/search/places/v1/polygon",
            method="POST",
            params={"srs": "WGS84", "output_srs": "WGS84", "maxresults": 1},
            body=_SAMPLE_POLYGON,
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=places_docs,
        ),
    )

    # Search: Names
    names_docs = _extract_docs(names_landing)
    _add_item(
        items,
        _probe(
            item_id="os.search.names.find",
            title="OS Names API: Find",
            description="Free text search for named features (gazetteer).",
            category="search",
            url=f"{OS_API_ROOT}/search/names/v1/find",
            params={"query": "Warwick", "maxresults": 1},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=names_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.names.nearest",
            title="OS Names API: Nearest",
            description="Nearest named features to a British National Grid point.",
            category="search",
            url=f"{OS_API_ROOT}/search/names/v1/nearest",
            params={"point": _SAMPLE_BNG_POINT, "radius": 100},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=names_docs,
        ),
    )

    # Search: Linked Identifiers
    links_docs = _extract_docs(links_landing)
    _add_item(
        items,
        _probe(
            item_id="os.search.links.identifiers",
            title="OS Linked Identifiers API: identifiers/{id}",
            description="Lookup linked identifiers for a base identifier (example UPRN).",
            category="search",
            url=f"{OS_API_ROOT}/search/links/v1/identifiers/{_SAMPLE_UPRN}",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=links_docs,
            meta={"identifier": _SAMPLE_UPRN},
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.links.identifierTypes.uprn",
            title="OS Linked Identifiers API: identifierTypes/uprn/{id}",
            description="Lookup linked identifiers using an explicit identifier type (UPRN).",
            category="search",
            url=f"{OS_API_ROOT}/search/links/v1/identifierTypes/uprn/{_SAMPLE_UPRN}",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=links_docs,
            meta={"uprn": _SAMPLE_UPRN},
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.links.featureTypes.roadlink",
            title="OS Linked Identifiers API: featureTypes/RoadLink/{id}",
            description="Lookup correlations for a feature type identifier (RoadLink TOID).",
            category="search",
            url=f"{OS_API_ROOT}/search/links/v1/featureTypes/RoadLink/{_SAMPLE_ROADLINK_TOID}",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=links_docs,
            meta={"toid": _SAMPLE_ROADLINK_TOID},
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.search.links.productVersionInfo",
            title="OS Linked Identifiers API: productVersionInfo/{correlationMethod}",
            description="Resolve current product version info for a correlation method id.",
            category="search",
            url=f"{OS_API_ROOT}/search/links/v1/productVersionInfo/{_SAMPLE_CORRELATION_METHOD}",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=links_docs,
            meta={"correlationMethod": _SAMPLE_CORRELATION_METHOD},
        ),
    )

    # Search: Match & Cleanse (often entitlement-gated; probe for key permissions)
    match_docs = _extract_docs(match_landing)
    _add_item(
        items,
        _probe(
            item_id="os.search.match.match",
            title="OS Match & Cleanse API: match",
            description="Address matching/cleansing operation (entitlement-gated for some keys).",
            category="search",
            url=f"{OS_API_ROOT}/search/match/v1/match",
            required=False,
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=match_docs,
        ),
    )

    # Features: WFS (XML)
    wfs_docs = _extract_docs(wfs_landing)
    _add_item(
        items,
        _probe(
            item_id="os.features.wfs.capabilities",
            title="OS Features API (WFS): GetCapabilities",
            description="WFS capabilities document (XML).",
            category="features",
            url=f"{OS_API_ROOT}/features/v1/wfs",
            params={"service": "WFS", "request": "GetCapabilities"},
            expects={"status": [200], "contentTypePrefix": "application/xml"},
            docs=wfs_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.features.wfs.archive.capabilities",
            title="OS Features API (WFS Archive): GetCapabilities",
            description="WFS product archive capabilities (often entitlement-gated).",
            category="features",
            url=f"{OS_API_ROOT}/features/v1/wfs/archive",
            params={"service": "WFS", "request": "GetCapabilities"},
            required=False,
            expects={"status": [200], "contentTypePrefix": "application/xml"},
            docs=wfs_docs,
        ),
    )

    # Features: NGD OGC API Features collections + per-collection probes.
    ngd_docs = _extract_docs(ngd_landing)
    collections = _fetch_json(f"{OS_API_ROOT}/features/ngd/ofa/v1/collections", api_key)
    raw_collections: list[dict[str, Any]] = []
    if isinstance(collections, dict) and isinstance(collections.get("collections"), list):
        raw_collections = [c for c in collections["collections"] if isinstance(c, dict)]

    _add_item(
        items,
        _probe(
            item_id="os.features.ngd.collections",
            title="OS NGD API – Features: Collections",
            description="List available NGD feature collections (OGC API Features).",
            category="features",
            url=f"{OS_API_ROOT}/features/ngd/ofa/v1/collections",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=ngd_docs,
            meta={"count": len(raw_collections)},
        ),
    )
    for coll in raw_collections:
        coll_id = coll.get("id")
        if not isinstance(coll_id, str) or not coll_id.strip():
            continue
        coll_id = coll_id.strip()
        title = coll.get("title") if isinstance(coll.get("title"), str) else coll_id
        desc = coll.get("description") if isinstance(coll.get("description"), str) else ""
        _add_item(
            items,
            _probe(
                item_id=f"os.features.ngd.collection.{coll_id}.items",
                title=f"OS NGD items: {coll_id}",
                description=desc or f"Probe items endpoint for collection {coll_id}.",
                category="features",
                url=f"{OS_API_ROOT}/features/ngd/ofa/v1/collections/{coll_id}/items",
                params={"bbox": _SAMPLE_NGD_ITEMS_BBOX_STR, "limit": 1},
                expects={"status": [200], "contentTypePrefix": "application/geo+json"},
                docs=ngd_docs,
                meta={"collectionId": coll_id, "collectionTitle": title},
            ),
        )

    # Maps: Raster (WMTS + ZXY tile)
    raster_docs = _extract_docs(raster_landing)
    _add_item(
        items,
        _probe(
            item_id="os.maps.raster.wmts.capabilities",
            title="OS Maps API (Raster WMTS): GetCapabilities",
            description="WMTS capabilities document (XML).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/raster/v1/wmts",
            params={"service": "WMTS", "request": "GetCapabilities"},
            expects={"status": [200], "contentTypePrefix": "application/xml"},
            docs=raster_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.raster.zxy.tile",
            title="OS Maps API (Raster ZXY): Sample tile",
            description="Fetch a single PNG tile (kept small; no bulk downloads).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/raster/v1/zxy/Light_3857/7/63/42.png",
            expects={"status": [200], "contentTypePrefix": "image/png", "minBytes": 64},
            docs=raster_docs,
            meta={"z": 7, "x": 63, "y": 42, "layer": "Light_3857"},
        ),
    )

    # Maps: Vector (VTS + NGD Tiles OTA)
    vector_docs = _extract_docs(vector_landing)
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.vts.metadata",
            title="OS Vector Tile API (VTS): service metadata",
            description="ArcGIS-style VTS service metadata (JSON).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/v1/vts",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=vector_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.vts.style",
            title="OS Vector Tile API (VTS): style JSON",
            description="Fetch a named MapLibre style JSON from VTS.",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/v1/vts/resources/styles",
            params={"style": "OS_VTS_3857_Light.json", "srs": "3857"},
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=vector_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.vts.tile",
            title="OS Vector Tile API (VTS): sample tile",
            description="Fetch a single PBF vector tile (kept small; no bulk downloads).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/v1/vts/tile/7/42/63.pbf",
            params={"srs": "3857"},
            expects={"status": [200], "contentTypePrefix": "application/octet-stream", "minBytes": 64},
            docs=vector_docs,
            meta={"z": 7, "x": 63, "y": 42},
        ),
    )

    ota_docs = _extract_docs(ota_landing)
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.ngd.ota.root",
            title="OS NGD API – Tiles (OTA): landing",
            description="OGC API Tiles landing document (JSON).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/ngd/ota/v1",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=ota_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.ngd.ota.collections",
            title="OS NGD API – Tiles (OTA): collections",
            description="List tile collections (OGC API Tiles).",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/ngd/ota/v1/collections",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=ota_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.ngd.ota.tilematrixsets",
            title="OS NGD API – Tiles (OTA): tileMatrixSets",
            description="List TileMatrixSets supported by the service.",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/ngd/ota/v1/tilematrixsets",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=ota_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.maps.vector.ngd.ota.conformance",
            title="OS NGD API – Tiles (OTA): conformance",
            description="List OGC conformance classes implemented by this service.",
            category="maps",
            url=f"{OS_API_ROOT}/maps/vector/ngd/ota/v1/conformance",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=ota_docs,
        ),
    )

    # Downloads: Products + OpenAPI (YAML).
    downloads_docs = _extract_docs(downloads_landing)
    _add_item(
        items,
        _probe(
            item_id="os.downloads.openapi",
            title="OS Downloads API: OpenAPI specification",
            description="Downloads API OpenAPI YAML (metadata only; no file downloads).",
            category="downloads",
            url=f"{OS_API_ROOT}/downloads/v1/openapi.yaml",
            expects={"status": [200], "contentTypePrefix": "application/yaml"},
            docs=downloads_docs,
        ),
    )

    products = _fetch_json(f"{OS_API_ROOT}/downloads/v1/products", api_key)
    products_list: list[dict[str, Any]] = []
    if isinstance(products, list):
        products_list = [p for p in products if isinstance(p, dict)]
    _add_item(
        items,
        _probe(
            item_id="os.downloads.products",
            title="OS Downloads API: Products list",
            description="List available download products (metadata only).",
            category="downloads",
            url=f"{OS_API_ROOT}/downloads/v1/products",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=downloads_docs,
            meta={"count": len(products_list)},
        ),
    )

    for product in products_list:
        product_id = product.get("id")
        if not isinstance(product_id, str) or not product_id.strip():
            continue
        product_id = product_id.strip()
        name = product.get("name") if isinstance(product.get("name"), str) else product_id
        desc = product.get("description") if isinstance(product.get("description"), str) else ""
        version = product.get("version") if isinstance(product.get("version"), str) else None
        _add_item(
            items,
            _probe(
                item_id=f"os.downloads.product.{product_id}.meta",
                title=f"OS Downloads product: {name} (meta)",
                description=desc or "Product metadata lookup.",
                category="downloads",
                url=f"{OS_API_ROOT}/downloads/v1/products/{product_id}",
                expects={"status": [200], "contentTypePrefix": "application/json"},
                docs=downloads_docs,
                meta={"productId": product_id, "productName": name, "version": version},
            ),
        )
        _add_item(
            items,
            _probe(
                item_id=f"os.downloads.product.{product_id}.downloads",
                title=f"OS Downloads product: {name} (downloads)",
                description="List download options (do not follow redirect URLs).",
                category="downloads",
                url=f"{OS_API_ROOT}/downloads/v1/products/{product_id}/downloads",
                expects={"status": [200], "contentTypePrefix": "application/json"},
                docs=downloads_docs,
                meta={"productId": product_id, "productName": name, "version": version},
            ),
        )

    # Account-specific listing (may expose tenant-created packages; probe only, do not snapshot contents).
    _add_item(
        items,
        _probe(
            item_id="os.downloads.dataPackages",
            title="OS Downloads API: dataPackages",
            description="List account-specific data packages (probe for permissions only).",
            category="downloads",
            url=f"{OS_API_ROOT}/downloads/v1/dataPackages",
            required=False,
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=downloads_docs,
        ),
    )

    # Positioning: OS Net (OpenAPI + sample station + log + RINEX years)
    osnet_docs = _extract_docs(osnet_landing)
    _add_item(
        items,
        _probe(
            item_id="os.positioning.osnet.openapi",
            title="OS Net API: OpenAPI specification",
            description="OS Net API OpenAPI YAML.",
            category="positioning",
            url=f"{OS_API_ROOT}/positioning/osnet/v1/openapi.yaml",
            expects={"status": [200], "contentTypePrefix": "application/yaml"},
            docs=osnet_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.positioning.osnet.rinex.years",
            title="OS Net API: RINEX years listing",
            description="List years that have RINEX data.",
            category="positioning",
            url=f"{OS_API_ROOT}/positioning/osnet/v1/rinex",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=osnet_docs,
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.positioning.osnet.station.detail",
            title="OS Net API: station detail (AMER)",
            description="Fetch station detail for a known station id (avoids large list responses).",
            category="positioning",
            url=f"{OS_API_ROOT}/positioning/osnet/v1/stations/AMER",
            expects={"status": [200], "contentTypePrefix": "application/json"},
            docs=osnet_docs,
            meta={"stationId": "AMER"},
        ),
    )
    _add_item(
        items,
        _probe(
            item_id="os.positioning.osnet.station.log",
            title="OS Net API: station log (AMER)",
            description="Fetch station log (text/plain).",
            category="positioning",
            url=f"{OS_API_ROOT}/positioning/osnet/v1/stations/AMER/log",
            expects={"status": [200], "contentTypePrefix": "text/plain"},
            docs=osnet_docs,
            meta={"stationId": "AMER"},
        ),
    )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": OS_API_ROOT,
        "placeholder": False,
        "items": items,
    }

    out_path = _resolve_path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"Wrote {len(items)} OS catalog entries to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
