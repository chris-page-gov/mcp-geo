#!/usr/bin/env python3
"""Create and verify a full LandIS release archive on local storage.

This script treats the existing authenticated ArcGIS portal archive as one
verified component and then mirrors the remaining public LandIS release
surfaces:

1. Public LandIS website dataset/service pages that are linked from the
   current official navigation but absent from the mirrored portal slice.
2. Relevant `data.gov.uk` Cranfield/LandIS package metadata and their published
   resource URLs.

The script writes a machine-readable release manifest plus a completion
verification manifest. It is designed to be rerunnable and resumable.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.landis_release_reconciliation import (
    DEFAULT_ARCHIVE_MANIFEST_PATH,
    PORTAL_INVENTORY_PATH,
    PUBLIC_ITEMS,
    USER_AGENT,
    build_manifest as build_public_manifest,
)
DEFAULT_DESTINATION = Path("/Volumes/ExtSSD-Data/Data/landis_full_release_archive_2026-04-05")
DEFAULT_PUBLIC_MANIFEST = (
    REPO_ROOT / "research" / "landis-data-source" / "landis_release_reconciliation_2026-04-05.json"
)
DEFAULT_FULL_MANIFEST = (
    REPO_ROOT / "research" / "landis-data-source" / "landis_full_release_manifest_2026-04-05.json"
)

DATA_GOV_QUERIES: tuple[str, ...] = (
    "landis cranfield",
    "cranfield natmap",
    "cranfield nsi",
    "cranfield soil series",
    "cranfield leacs",
    "cranfield auger",
    "cranfield soilscapes",
    "cranfield peat",
    "cranfield horizon",
    "cranfield host",
)

INCLUDE_TITLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^NATMAP", re.I),
    re.compile(r"^NSI\b", re.I),
    re.compile(r"^Horizon\b", re.I),
    re.compile(r"^Host Class\b", re.I),
    re.compile(r"^LEACS\b", re.I),
    re.compile(r"^Mapunit\b", re.I),
    re.compile(r"^Soil Series\b", re.I),
    re.compile(r"^Soilscapes\b", re.I),
    re.compile(r"^Modern Correlatives for Old Soil Series$", re.I),
    re.compile(r"^Standard Horizons used in Classified Soil Pits$", re.I),
    re.compile(r"^Soil Pits$", re.I),
    re.compile(r"^Texture Group$", re.I),
    re.compile(r"^Horizons$", re.I),
    re.compile(r"^Profile horizon properties of auger bores$", re.I),
    re.compile(r"^Site properties of auger bores$", re.I),
    re.compile(r"^Peaty Soils Location$", re.I),
    re.compile(r"^Moorland Deep Peat AP Status$", re.I),
)

EXCLUDE_TITLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"Eddy Covariance", re.I),
    re.compile(r"Woodland Creation", re.I),
    re.compile(r"Sheep urine", re.I),
    re.compile(r"Pontbren", re.I),
    re.compile(r"Peatland condition", re.I),
    re.compile(r"England Peat Status GHG", re.I),
    re.compile(r"Carbon Storage", re.I),
    re.compile(r"Carbon Sequestration", re.I),
)


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._")
    return cleaned or "item"


def _fetch_bytes(url: str) -> tuple[int | str, bytes, dict[str, str], str | None]:
    request = Request(_request_url(url), headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=60) as response:
            payload = response.read()
            return response.status, payload, dict(response.headers.items()), response.geturl()
    except HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers.items()), None
    except URLError as exc:
        return "url_error", b"", {}, str(exc)
    except Exception as exc:  # pragma: no cover - defensive network guard
        return "url_error", b"", {}, repr(exc)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _detect_extension(content_type: str, fallback: str) -> str:
    content_type = (content_type or "").lower()
    if "application/json" in content_type:
        return ".json"
    if "application/pdf" in content_type:
        return ".pdf"
    if "text/html" in content_type:
        return ".html"
    if "text/plain" in content_type:
        return ".txt"
    if "image/png" in content_type:
        return ".png"
    if "image/jpeg" in content_type:
        return ".jpg"
    if "application/xml" in content_type or "text/xml" in content_type:
        return ".xml"
    return fallback


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _normalized_url(url: str) -> str:
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}"


def _cache_key_url(url: str) -> str:
    parts = urlsplit(url)
    query = parts.query
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def _request_url(url: str) -> str:
    parts = urlsplit(url)
    path = quote(parts.path, safe="/:@")
    query = quote(parts.query, safe="=&:%/+")
    return urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def _url_cache_path(url: str, destination: Path, headers: dict[str, str]) -> Path:
    digest = hashlib.sha256(_cache_key_url(url).encode("utf-8")).hexdigest()[:16]
    parts = urlsplit(url)
    basename = Path(parts.path).name or "index"
    ext = Path(basename).suffix or _detect_extension(headers.get("Content-Type", ""), ".bin")
    stem = Path(basename).stem or "index"
    return destination / "shared_url_fetches" / f"{stem}_{digest}{ext}"


def _download_url(url: str, destination: Path) -> dict[str, Any]:
    attempts = [url]
    normalized = _normalized_url(url).lower()
    if normalized.endswith("/mapserver") or normalized.endswith("/featureserver"):
        attempts.append(f"{url}?f=pjson")
    if normalized.endswith("/wfs"):
        attempts.append(f"{url}?service=WFS&request=GetCapabilities")

    last_status: int | str = "url_error"
    last_error: str | None = None
    for attempt in attempts:
        status, payload, headers, final = _fetch_bytes(attempt)
        if status != 200:
            last_status = status
            last_error = final if isinstance(final, str) else f"download failed with status {status}"
            continue
        path = _url_cache_path(attempt, destination, headers)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(payload)
        return {
            "status": "ok",
            "url": url,
            "requestedUrl": attempt,
            "finalUrl": _cache_key_url(final or attempt),
            "path": str(path),
            "bytes": len(payload),
            "sha256": _sha256_bytes(payload),
            "contentType": headers.get("Content-Type", ""),
        }

    return {
        "status": last_status,
        "url": url,
        "error": last_error,
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _portal_component_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "path": str(path)}
    payload = _load_json(path)
    results = payload.get("results", [])
    errors = [result for result in results if result.get("status") == "error"]
    archive_root = str(path.parent)
    return {
        "status": "ok" if not errors else "error",
        "path": str(path),
        "archiveRoot": archive_root,
        "results": len(results),
        "errors": len(errors),
        "errorTitles": [result.get("title") for result in errors[:20]],
    }


def _iter_data_gov_candidates() -> dict[str, dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    for query in DATA_GOV_QUERIES:
        url = f"https://www.data.gov.uk/api/3/action/package_search?rows=100&q={quote(query)}"
        status, payload, _, error = _fetch_bytes(url)
        if status != 200:
            raise RuntimeError(f"data.gov.uk search failed for {query}: {error or status}")
        data = json.loads(payload.decode("utf-8"))
        for result in data["result"]["results"]:
            title = result.get("title") or ""
            if not any(pattern.search(title) for pattern in INCLUDE_TITLE_PATTERNS):
                continue
            if any(pattern.search(title) for pattern in EXCLUDE_TITLE_PATTERNS):
                continue
            candidates[result["name"]] = {
                "title": title,
                "name": result["name"],
                "metadataModified": result.get("metadata_modified"),
            }
    return candidates


def _fetch_package_show(name: str) -> dict[str, Any]:
    url = f"https://www.data.gov.uk/api/3/action/package_show?id={quote(name)}"
    status, payload, _, error = _fetch_bytes(url)
    if status != 200:
        raise RuntimeError(f"package_show failed for {name}: {error or status}")
    return json.loads(payload.decode("utf-8"))["result"]


def _download_public_items(destination: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in PUBLIC_ITEMS:
        item_dir = destination / "public_site" / _safe_name(item.name)
        item_dir.mkdir(parents=True, exist_ok=True)
        existing_path = item_dir / "entry.json"
        if existing_path.exists():
            existing = _load_json(existing_path)
            if existing.get("status") == "ok" and existing.get("pagePath") and Path(existing["pagePath"]).exists():
                entries.append(existing)
                continue
        status, payload, headers, final = _fetch_bytes(item.url)
        record: dict[str, Any] = {
            "name": item.name,
            "kind": item.kind,
            "family": item.family,
            "url": item.url,
            "status": status,
        }
        if status == 200:
            page_path = item_dir / "page.html"
            page_path.write_bytes(payload)
            record.update(
                {
                    "status": "ok",
                    "finalUrl": _normalized_url(final or item.url),
                    "pagePath": str(page_path),
                    "bytes": len(payload),
                    "sha256": _sha256_bytes(payload),
                    "contentType": headers.get("Content-Type", ""),
                }
            )
        else:
            record["error"] = final if isinstance(final, str) else f"HTTP {status}"
        _write_json(item_dir / "entry.json", record)
        entries.append(record)
    return entries


def _download_data_gov_packages(destination: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    candidates = _iter_data_gov_candidates()
    for name in sorted(candidates):
        package = _fetch_package_show(name)
        package_dir = destination / "data_gov" / _safe_name(name)
        package_dir.mkdir(parents=True, exist_ok=True)
        _write_json(package_dir / "package_show.json", package)

        existing_path = package_dir / "entry.json"
        existing: dict[str, Any] | None = _load_json(existing_path) if existing_path.exists() else None

        page_url = f"https://www.data.gov.uk/dataset/{name}"
        page_record: dict[str, Any] = {
            "name": name,
            "title": package.get("title"),
            "pageUrl": page_url,
            "licenseTitle": package.get("license_title"),
            "metadataModified": package.get("metadata_modified"),
        }
        if (
            existing
            and existing.get("status") == "ok"
            and existing.get("pagePath")
            and Path(existing["pagePath"]).exists()
        ):
            page_record.update(
                {
                    "status": "ok",
                    "pagePath": existing.get("pagePath"),
                    "pageBytes": existing.get("pageBytes"),
                    "pageSha256": existing.get("pageSha256"),
                    "finalPageUrl": existing.get("finalPageUrl"),
                    "pageContentType": existing.get("pageContentType"),
                }
            )
        else:
            page_status, page_payload, page_headers, page_final = _fetch_bytes(page_url)
            page_record["status"] = page_status
            if page_status == 200:
                page_path = package_dir / "package_page.html"
                page_path.write_bytes(page_payload)
                page_record.update(
                    {
                        "status": "ok",
                        "pagePath": str(page_path),
                        "pageBytes": len(page_payload),
                        "pageSha256": _sha256_bytes(page_payload),
                        "finalPageUrl": _normalized_url(page_final or page_url),
                        "pageContentType": page_headers.get("Content-Type", ""),
                    }
                )
            else:
                page_record["pageError"] = (
                    page_final if isinstance(page_final, str) else f"HTTP {page_status}"
                )

        resources: list[dict[str, Any]] = []
        existing_resources = {
            resource.get("url"): resource
            for resource in (existing.get("resources") if existing else [])
            if isinstance(resource, dict) and resource.get("url")
        }
        for resource in package.get("resources") or []:
            resource_url = resource.get("url")
            if not resource_url:
                continue
            cached = existing_resources.get(resource_url)
            if cached and cached.get("status") == "ok" and cached.get("path") and Path(cached["path"]).exists():
                download = {
                    "status": cached.get("status"),
                    "url": cached.get("url"),
                    "requestedUrl": cached.get("requestedUrl"),
                    "finalUrl": cached.get("finalUrl"),
                    "path": cached.get("path"),
                    "bytes": cached.get("bytes"),
                    "sha256": cached.get("sha256"),
                    "contentType": cached.get("contentType"),
                }
            else:
                download = _download_url(resource_url, destination)
            resources.append(
                {
                    "name": resource.get("name"),
                    "format": resource.get("format"),
                    "description": resource.get("description"),
                    **download,
                }
            )
        page_record["resources"] = resources
        _write_json(package_dir / "entry.json", page_record)
        entries.append(page_record)
    return entries


def _build_full_manifest(
    destination: Path,
    portal_manifest_path: Path,
    public_manifest_path: Path,
    public_entries: list[dict[str, Any]],
    data_gov_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    public_manifest = _load_json(public_manifest_path)
    portal_component = _portal_component_status(portal_manifest_path)
    verified_resource_errors = sum(
        1
        for entry in data_gov_entries
        for resource in entry.get("resources", [])
        if not _resource_is_verified(resource, entry.get("resources", []))
    )
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "destination": str(destination),
        "portalComponent": portal_component,
        "repoPublicReconciliationManifest": str(public_manifest_path),
        "repoPublicReconciliationGeneratedAt": public_manifest.get("generatedAt"),
        "publicItems": public_entries,
        "dataGovPackages": data_gov_entries,
        "summary": {
            "publicItems": len(public_entries),
            "publicItemErrors": sum(1 for entry in public_entries if entry.get("status") != "ok"),
            "dataGovPackages": len(data_gov_entries),
            "dataGovPackageErrors": sum(1 for entry in data_gov_entries if entry.get("status") != "ok"),
            "dataGovResourceErrors": verified_resource_errors,
        },
    }


def _verify_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    portal = manifest["portalComponent"]
    checks.append(
        {
            "name": "portal_component",
            "status": "ok" if portal.get("status") == "ok" and portal.get("errors") == 0 else "error",
            "details": portal,
        }
    )

    for entry in manifest["publicItems"]:
        page_path = entry.get("pagePath")
        ok = entry.get("status") == "ok" and page_path and Path(page_path).exists()
        checks.append(
            {
                "name": f"public:{entry['name']}",
                "status": "ok" if ok else "error",
                "details": {"pagePath": page_path, "status": entry.get("status")},
            }
        )

    for entry in manifest["dataGovPackages"]:
        page_path = entry.get("pagePath")
        ok = entry.get("status") == "ok" and page_path and Path(page_path).exists()
        checks.append(
            {
                "name": f"data_gov:{entry['name']}",
                "status": "ok" if ok else "error",
                "details": {"pagePath": page_path, "status": entry.get("status")},
            }
        )
        for resource in entry.get("resources", []):
            path = resource.get("path")
            resource_ok = _resource_is_verified(resource, entry.get("resources", []))
            checks.append(
                {
                    "name": f"resource:{entry['name']}:{resource.get('url')}",
                    "status": "ok" if resource_ok else "error",
                    "details": {
                        "path": path,
                        "status": resource.get("status"),
                        "finalUrl": resource.get("finalUrl"),
                    },
                }
            )

    errors = [check for check in checks if check["status"] != "ok"]
    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "complete": len(errors) == 0,
        "checkCount": len(checks),
        "errorCount": len(errors),
        "errors": errors[:200],
        "checks": checks,
    }


def _resource_is_verified(resource: dict[str, Any], siblings: list[dict[str, Any]]) -> bool:
    path = resource.get("path")
    if resource.get("status") == "ok" and path and Path(path).exists():
        return True

    url = (resource.get("url") or "").lower()
    if not url.endswith("/mapserver"):
        return False

    for sibling in siblings:
        sibling_path = sibling.get("path")
        sibling_url = (sibling.get("url") or "").lower()
        if sibling is resource or sibling.get("status") != "ok" or not sibling_path:
            continue
        if not Path(sibling_path).exists():
            continue
        if any(
            marker in sibling_url
            for marker in ("/featureserver", "/wms", "/wfs", "/ogc/features/")
        ):
            return True
    return False


def run(destination: Path, public_manifest_path: Path, full_manifest_path: Path, portal_manifest_path: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)

    if not public_manifest_path.exists():
        public_manifest = build_public_manifest(portal_manifest_path)
        public_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        public_manifest_path.write_text(json.dumps(public_manifest, indent=2) + "\n", encoding="utf-8")

    public_entries = _download_public_items(destination)
    data_gov_entries = _download_data_gov_packages(destination)

    manifest = _build_full_manifest(
        destination,
        portal_manifest_path,
        public_manifest_path,
        public_entries,
        data_gov_entries,
    )
    full_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(full_manifest_path, manifest)
    _write_json(destination / "full_release_manifest.json", manifest)

    verification = _verify_manifest(manifest)
    _write_json(destination / "verification_manifest.json", verification)

    if not verification["complete"]:
        raise SystemExit("Full LandIS release archive verification failed; see verification_manifest.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--public-manifest", type=Path, default=DEFAULT_PUBLIC_MANIFEST)
    parser.add_argument("--full-manifest", type=Path, default=DEFAULT_FULL_MANIFEST)
    parser.add_argument("--portal-manifest", type=Path, default=DEFAULT_ARCHIVE_MANIFEST_PATH)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.verify_only:
        manifest = _load_json(args.destination / "full_release_manifest.json")
        verification = _verify_manifest(manifest)
        _write_json(args.destination / "verification_manifest.json", verification)
        if not verification["complete"]:
            raise SystemExit("Verification failed")
        print(args.destination / "verification_manifest.json")
        return

    run(args.destination, args.public_manifest, args.full_manifest, args.portal_manifest)
    print(args.destination / "verification_manifest.json")


if __name__ == "__main__":
    main()
