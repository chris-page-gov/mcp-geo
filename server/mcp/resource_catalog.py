from __future__ import annotations

import hashlib
from pathlib import Path
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from server.config import settings
ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = ROOT / "ui"
SKILL_PATH = ROOT / "SKILL.md"
BOUNDARY_MANIFEST_PATH = ROOT / "docs" / "Boundaries.json"
BOUNDARY_RUNS_DIR = ROOT / "data" / "boundary_runs"
ONS_CACHE_DIR = ROOT / "data" / "cache" / "ons"
ONS_CATALOG_PATH = ROOT / "resources" / "ons_catalog.json"
OS_CATALOG_PATH = ROOT / "resources" / "os_catalog.json"
LAYERS_CATALOG_PATH = ROOT / "resources" / "layers_catalog.json"
NOMIS_WORKFLOWS_PATH = ROOT / "resources" / "nomis_workflows.json"
BOUNDARY_PACK_SOURCES_PATH = ROOT / "resources" / "boundary_pack_sources.json"
CODE_LIST_PACK_SOURCES_PATH = ROOT / "resources" / "code_list_pack_sources.json"
BOUNDARY_PACKS_INDEX_PATH = ROOT / "resources" / "boundary_packs_index.json"
CODE_LIST_PACKS_INDEX_PATH = ROOT / "resources" / "code_list_packs_index.json"
EXPORTS_DIR = ROOT / "data" / "exports"
ONS_EXPORTS_DIR = ROOT / "data" / "ons_exports"

DATA_RESOURCE_PREFIX = "resource://mcp-geo/"
ONS_CACHE_PREFIX = f"{DATA_RESOURCE_PREFIX}ons-cache/"
ONS_EXPORTS_PREFIX = f"{DATA_RESOURCE_PREFIX}ons-exports/"
MCP_APPS_MIME = "text/html;profile=mcp-app"


def data_resource_uri(name: str) -> str:
    return f"{DATA_RESOURCE_PREFIX}{name}"


_UI_RESOURCE_BASES: list[dict[str, Any]] = [
    {
        "slug": "geography-selector",
        "name": "ui_geography_selector",
        "title": "Geography Selector",
        "description": "Interactive selector for UK administrative areas.",
        "file": "geography_selector.html",
        "annotations": {
            "audience": ["user"],
            "priority": 1.0,
            "capabilities": ["search", "selection", "hierarchy", "map"],
        },
        "csp": {
            "connectDomains": [
                "self",
                "https://api.os.uk",
                "https://unpkg.com",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ],
            "resourceDomains": [
                "self",
                "https://api.os.uk",
                "https://fonts.googleapis.com",
                "https://fonts.gstatic.com",
                "https://unpkg.com",
            ],
            "workerDomains": ["self", "blob:"],
        },
        "permissions": {"sameOrigin": True},
    },
    {
        "slug": "boundary-explorer",
        "name": "ui_boundary_explorer",
        "title": "Boundary Explorer",
        "description": (
            "Interactive explorer for UK boundaries with progressive disclosure for UPRNs, buildings, "
            "and transport links, plus local layer import and export."
        ),
        "file": "boundary_explorer.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.95,
            "capabilities": [
                "search",
                "selection",
                "hierarchy",
                "map",
                "inventory",
                "aggregation",
                "local-layers",
                "export",
            ],
        },
        "csp": {
            "connectDomains": [
                "self",
                "https://api.os.uk",
                "https://unpkg.com",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ],
            "resourceDomains": [
                "self",
                "https://api.os.uk",
                "https://fonts.googleapis.com",
                "https://fonts.gstatic.com",
                "https://unpkg.com",
            ],
            "workerDomains": ["self", "blob:"],
        },
        "permissions": {"sameOrigin": True},
    },
    {
        "slug": "statistics-dashboard",
        "name": "ui_statistics_dashboard",
        "title": "Statistics Dashboard",
        "description": "Visual dashboard for ONS observations and comparisons.",
        "file": "statistics_dashboard.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.9,
            "capabilities": ["charts", "comparison", "export"],
        },
        "csp": None,
    },
    {
        "slug": "feature-inspector",
        "name": "ui_feature_inspector",
        "title": "Feature Inspector",
        "description": "Inspect OS NGD features and linked identifiers.",
        "file": "feature_inspector.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.7,
            "capabilities": ["properties", "map", "linked-ids"],
        },
        "csp": None,
    },
    {
        "slug": "route-planner",
        "name": "ui_route_planner",
        "title": "Route Planner",
        "description": "Plan routes with waypoints and directions.",
        "file": "route_planner.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.8,
            "capabilities": ["routing", "waypoints", "directions"],
        },
        "csp": None,
    },
    {
        "slug": "warwick-leamington-3d",
        "name": "ui_warwick_leamington_3d",
        "title": "Warwick + Leamington (3D)",
        "description": "3D view of Warwick and Royal Leamington Spa wards with OS Places premises types.",
        "file": "warwick_leamington_3d.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.75,
            "capabilities": ["map", "3d", "wards", "premises", "os-places"],
        },
        "csp": {
            "connectDomains": [
                "self",
                "https://demotiles.maplibre.org",
                "https://unpkg.com",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ],
            "resourceDomains": [
                "self",
                "https://demotiles.maplibre.org",
                "https://fonts.googleapis.com",
                "https://fonts.gstatic.com",
                "https://unpkg.com",
            ],
            "workerDomains": ["self", "blob:"],
        },
        "permissions": {"sameOrigin": True},
    },
]

SKILLS_RESOURCE: dict[str, Any] = {
    "uri": "skills://mcp-geo/getting-started",
    "name": "skills_getting_started",
    "title": "MCP Geo Skills",
    "description": "Getting started guidance for MCP Geo tools and resources.",
    "mimeType": "text/markdown",
    "annotations": {"audience": ["assistant"], "priority": 1.0},
}

DATA_RESOURCE_DEFS: list[dict[str, Any]] = [
    {
        "slug": "boundary-manifest",
        "name": "data_boundary_manifest",
        "title": "Boundary Manifest",
        "description": "Boundary dataset manifest driving the ingestion pipeline.",
        "path": BOUNDARY_MANIFEST_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "dataset", "domain": "boundaries"},
    },
    {
        "slug": "ons-catalog",
        "name": "data_ons_catalog",
        "title": "ONS Dataset Catalog",
        "description": "Curated ONS dataset catalog index for selection and ranking.",
        "path": ONS_CATALOG_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "ons"},
    },
    {
        "slug": "os-catalog",
        "name": "data_os_catalog",
        "title": "OS API Catalog",
        "description": (
            "Catalog of Ordnance Survey API endpoints and download products, with sample probes for "
            "live validation."
        ),
        "path": OS_CATALOG_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "os"},
    },
    {
        "slug": "layers-catalog",
        "name": "data_layers_catalog",
        "title": "Layers Catalog",
        "description": "Catalog mapping user-friendly layer concepts to OS NGD collections and rendering hints.",
        "path": LAYERS_CATALOG_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "maps"},
    },
    {
        "slug": "nomis-workflows",
        "name": "data_nomis_workflows",
        "title": "NOMIS Workflow Profiles",
        "description": "Dataset-specific NOMIS workflow profiles and routing hints.",
        "path": NOMIS_WORKFLOWS_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "guide", "domain": "nomis"},
    },
    {
        "slug": "boundary-pack-sources",
        "name": "data_boundary_pack_sources",
        "title": "Boundary Pack Sources",
        "description": "Source manifest for boundary packs managed via hybrid fetch cache.",
        "path": BOUNDARY_PACK_SOURCES_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "manifest", "domain": "boundaries"},
    },
    {
        "slug": "code-list-pack-sources",
        "name": "data_code_list_pack_sources",
        "title": "Code-list Pack Sources",
        "description": "Source manifest for code-list packs managed via hybrid fetch cache.",
        "path": CODE_LIST_PACK_SOURCES_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "manifest", "domain": "codes"},
    },
    {
        "slug": "boundary-packs-index",
        "name": "data_boundary_packs_index",
        "title": "Boundary Packs Index",
        "description": "Hybrid cache index for boundary packs (checksum + cache path status).",
        "path": BOUNDARY_PACKS_INDEX_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "boundaries"},
    },
    {
        "slug": "code-list-packs-index",
        "name": "data_code_list_packs_index",
        "title": "Code-list Packs Index",
        "description": "Hybrid cache index for code-list packs (checksum + cache path status).",
        "path": CODE_LIST_PACKS_INDEX_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "codes"},
    },
]


def _build_openai_widget_csp(csp: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not csp:
        return None
    mapping = {
        "connectDomains": "connect_domains",
        "resourceDomains": "resource_domains",
        "frameDomains": "frame_domains",
        "redirectDomains": "redirect_domains",
    }
    converted: dict[str, Any] = {}
    for source, target in mapping.items():
        value = csp.get(source)
        if value:
            converted[target] = value
    return converted or None


def _build_ui_meta(
    description: str,
    csp: Optional[dict[str, Any]],
    permissions: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    meta: dict[str, Any] = {"ui": {"prefersBorder": True}}
    if csp:
        meta["ui"]["csp"] = csp
    if permissions:
        meta["ui"]["permissions"] = permissions
    widget_domain = getattr(settings, "OPENAI_WIDGET_DOMAIN", "")
    if widget_domain:
        meta["ui"]["domain"] = widget_domain
    openai_csp = _build_openai_widget_csp(csp)
    if openai_csp:
        meta["openai/widgetCSP"] = openai_csp
    meta["openai/widgetPrefersBorder"] = True
    if description:
        meta["openai/widgetDescription"] = description
    if widget_domain:
        meta["openai/widgetDomain"] = widget_domain
    return meta


def _build_ui_resource_defs() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for base in _UI_RESOURCE_BASES:
        meta = _build_ui_meta(
            base["description"],
            base.get("csp"),
            base.get("permissions"),
        )
        entries.append(
            {
                "uri": f"ui://mcp-geo/{base['slug']}",
                "name": base["name"],
                "title": base["title"],
                "description": base["description"],
                "file": base["file"],
                "mimeType": MCP_APPS_MIME,
                "annotations": base["annotations"],
                "resourceMeta": meta,
            }
        )
    return entries


_UI_RESOURCE_DEFS: list[dict[str, Any]] = _build_ui_resource_defs()


def list_ui_resources() -> list[dict[str, Any]]:
    return [
        {
            "uri": entry["uri"],
            "name": entry["name"],
            "title": entry["title"],
            "description": entry["description"],
            "mimeType": entry["mimeType"],
            "annotations": entry["annotations"],
            "_meta": entry.get("resourceMeta"),
            "type": "ui",
        }
        for entry in _UI_RESOURCE_DEFS
    ]


def list_skill_resources() -> list[dict[str, Any]]:
    return [
        {
            "uri": SKILLS_RESOURCE["uri"],
            "name": SKILLS_RESOURCE["name"],
            "title": SKILLS_RESOURCE["title"],
            "description": SKILLS_RESOURCE["description"],
            "mimeType": SKILLS_RESOURCE["mimeType"],
            "annotations": SKILLS_RESOURCE["annotations"],
            "type": "skills",
        }
    ]


def _latest_run_report_path() -> Optional[Path]:
    if not BOUNDARY_RUNS_DIR.exists():
        return None
    candidates = sorted(BOUNDARY_RUNS_DIR.glob("*/run_report.json"))
    if not candidates:
        return None
    return candidates[-1]


def _ons_cache_files() -> list[Path]:
    if not ONS_CACHE_DIR.exists():
        return []
    return sorted(path for path in ONS_CACHE_DIR.glob("*.json") if path.is_file())


def _ons_export_files() -> list[Path]:
    if not ONS_EXPORTS_DIR.exists():
        return []
    return sorted(path for path in ONS_EXPORTS_DIR.glob("*.json") if path.is_file())


def list_data_resources() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for entry in DATA_RESOURCE_DEFS:
        path = entry.get("path")
        if isinstance(path, Path) and not path.exists():
            continue
        resources.append(
            {
                "uri": data_resource_uri(entry["slug"]),
                "name": entry["name"],
                "title": entry["title"],
                "description": entry["description"],
                "mimeType": entry["mimeType"],
                "annotations": entry.get("annotations"),
                "type": "data",
            }
        )

    latest_report = _latest_run_report_path()
    if latest_report:
        resources.append(
            {
                "uri": data_resource_uri("boundary-latest-report"),
                "name": "data_boundary_latest_report",
                "title": "Boundary Pipeline Latest Report",
                "description": "Most recent boundary pipeline run report.",
                "mimeType": "application/json",
                "annotations": {"type": "report", "domain": "boundaries"},
                "type": "data",
            }
        )

    resources.append(
        {
            "uri": data_resource_uri("boundary-cache-status"),
            "name": "data_boundary_cache_status",
            "title": "Boundary Cache Status",
            "description": "Live status summary for the PostGIS boundary cache.",
            "mimeType": "application/json",
            "annotations": {"type": "status", "domain": "boundaries"},
            "type": "data",
        }
    )

    cache_files = _ons_cache_files()
    if cache_files:
        resources.append(
            {
                "uri": data_resource_uri("ons-cache-index"),
                "name": "data_ons_cache_index",
                "title": "ONS Codes Cache Index",
                "description": "Index of locally cached ONS code list responses.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "ons"},
                "type": "data",
            }
        )
        for path in cache_files:
            resources.append(
                {
                    "uri": f"{ONS_CACHE_PREFIX}{path.name}",
                    "name": f"data_ons_cache_{path.stem}",
                    "title": f"ONS Cache: {path.name}",
                    "description": "Cached ONS code list response.",
                    "mimeType": "application/json",
                    "annotations": {"type": "dataset", "domain": "ons"},
                    "type": "data",
                }
            )
    export_files = _ons_export_files()
    if export_files:
        resources.append(
            {
                "uri": data_resource_uri("ons-exports-index"),
                "name": "data_ons_exports_index",
                "title": "ONS Export Resource Index",
                "description": "Index of resource-backed ONS filter output exports.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "ons"},
                "type": "data",
            }
        )
    return resources


def _etag_from_bytes(content: bytes, variant: str = "") -> str:
    base = content + variant.encode()
    h = hashlib.sha256(base).hexdigest()[:16]
    return f'W/"{h}"'


def resolve_ui_resource(identifier: str) -> Optional[dict[str, Any]]:
    for entry in _UI_RESOURCE_DEFS:
        if identifier in (entry["uri"], entry["name"]):
            return entry
    return None


def resolve_skill_resource(identifier: str) -> Optional[dict[str, Any]]:
    if identifier in (SKILLS_RESOURCE["uri"], SKILLS_RESOURCE["name"]):
        return SKILLS_RESOURCE
    return None


def resolve_data_resource(identifier: str) -> Optional[dict[str, Any]]:
    if identifier.startswith(DATA_RESOURCE_PREFIX):
        slug = identifier[len(DATA_RESOURCE_PREFIX):]
    else:
        slug = identifier

    for entry in DATA_RESOURCE_DEFS:
        if slug in (entry["slug"], entry["name"]):
            return {**entry, "slug": entry["slug"]}
    if slug == "boundary-latest-report":
        return {"slug": slug}
    if slug == "boundary-cache-status":
        return {"slug": slug}
    if slug == "ons-cache-index":
        return {"slug": slug}
    if slug == "ons-exports-index":
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("exports/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("ons-exports/"):
        return {"slug": slug}
    if identifier.startswith(ONS_CACHE_PREFIX) or slug.startswith("ons-cache/"):
        return {"slug": slug}
    if identifier.startswith(ONS_EXPORTS_PREFIX):
        return {"slug": slug}
    return None


def load_ui_content(entry: dict[str, Any]) -> tuple[str, str]:
    path = UI_DIR / entry["file"]
    content = path.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), entry["uri"])
    return content, etag


def load_skill_content() -> tuple[str, str]:
    content = SKILL_PATH.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), SKILLS_RESOURCE["uri"])
    return content, etag


def _load_json_file(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), str(path))
    return content, etag


def load_data_content(entry: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    slug = entry.get("slug")
    if slug == "boundary-manifest":
        return (*_load_json_file(BOUNDARY_MANIFEST_PATH), None)
    if slug == "ons-catalog":
        if not ONS_CATALOG_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "ONS catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "ons-catalog"), None
        return (*_load_json_file(ONS_CATALOG_PATH), None)
    if slug == "os-catalog":
        if not OS_CATALOG_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "OS catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "os-catalog"), None
        return (*_load_json_file(OS_CATALOG_PATH), None)
    if slug == "layers-catalog":
        if not LAYERS_CATALOG_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Layers catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "layers-catalog"), None
        return (*_load_json_file(LAYERS_CATALOG_PATH), None)
    if slug == "nomis-workflows":
        if not NOMIS_WORKFLOWS_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "NOMIS workflows catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "nomis-workflows"), None
        return (*_load_json_file(NOMIS_WORKFLOWS_PATH), None)
    if slug == "boundary-pack-sources":
        if not BOUNDARY_PACK_SOURCES_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Boundary pack sources not found."}
            )
            return content, _etag_from_bytes(b"missing", "boundary-pack-sources"), None
        return (*_load_json_file(BOUNDARY_PACK_SOURCES_PATH), None)
    if slug == "code-list-pack-sources":
        if not CODE_LIST_PACK_SOURCES_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Code-list pack sources not found."}
            )
            return content, _etag_from_bytes(b"missing", "code-list-pack-sources"), None
        return (*_load_json_file(CODE_LIST_PACK_SOURCES_PATH), None)
    if slug == "boundary-packs-index":
        if not BOUNDARY_PACKS_INDEX_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Boundary packs index not found."}
            )
            return content, _etag_from_bytes(b"missing", "boundary-packs-index"), None
        return (*_load_json_file(BOUNDARY_PACKS_INDEX_PATH), None)
    if slug == "code-list-packs-index":
        if not CODE_LIST_PACKS_INDEX_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Code-list packs index not found."}
            )
            return content, _etag_from_bytes(b"missing", "code-list-packs-index"), None
        return (*_load_json_file(CODE_LIST_PACKS_INDEX_PATH), None)
    if slug == "boundary-latest-report":
        latest = _latest_run_report_path()
        if not latest:
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "No run report found."}
            )
            return content, _etag_from_bytes(b"missing", "boundary-latest-report"), None
        content, etag = _load_json_file(latest)
        return content, etag, {"generatedAt": datetime.now(timezone.utc).isoformat()}
    if slug == "boundary-cache-status":
        try:
            from server.boundary_cache import get_boundary_cache
            from server.config import settings
            cache = get_boundary_cache()
            configured = bool(getattr(settings, "BOUNDARY_CACHE_ENABLED", False))
            dsn_set = bool(getattr(settings, "BOUNDARY_CACHE_DSN", ""))
        except Exception:
            cache = None
            configured = False
            dsn_set = False
        if not cache:
            payload = {
                "enabled": False,
                "configured": configured,
                "dsnSet": dsn_set,
                "maturity": {"state": "disabled", "reason": "cache_unavailable"},
                "staleness": {
                    "maxAgeDays": int(getattr(settings, "BOUNDARY_CACHE_MAX_AGE_DAYS", 180)),
                    "freshDatasetIds": [],
                    "staleDatasetIds": [],
                    "unknownFreshnessDatasetIds": [],
                },
                "reloadHint": "Run scripts/boundary_cache_ingest.py to populate PostGIS.",
            }
        else:
            status = cache.status() or {}
            if "enabled" not in status:
                status["enabled"] = True
            status.setdefault("maturity", {"state": "unknown", "reason": "maturity_unreported"})
            status.setdefault(
                "staleness",
                {
                    "maxAgeDays": int(getattr(settings, "BOUNDARY_CACHE_MAX_AGE_DAYS", 180)),
                    "freshDatasetIds": [],
                    "staleDatasetIds": [],
                    "unknownFreshnessDatasetIds": [],
                },
            )
            status["configured"] = configured
            status["dsnSet"] = dsn_set
            status["reloadHint"] = "Run scripts/boundary_cache_ingest.py to populate PostGIS."
            payload = status
        content = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "boundary-cache-status"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "ons-cache-index":
        items = []
        for path in _ons_cache_files():
            items.append({"name": path.name, "uri": f"{ONS_CACHE_PREFIX}{path.name}", "bytes": path.stat().st_size})
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "ons-cache-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "ons-exports-index":
        items = []
        for path in _ons_export_files():
            items.append(
                {
                    "name": path.name,
                    "uri": f"{ONS_EXPORTS_PREFIX}{path.name}",
                    "bytes": path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "ons-exports-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if isinstance(slug, str) and slug.startswith("ons-cache/"):
        filename = slug.split("/", 1)[1]
        path = ONS_CACHE_DIR / filename
        if not path.exists():
            content = json.dumps({"isError": True, "code": "NOT_FOUND", "message": "ONS cache file not found."})
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        return (*_load_json_file(path), None)
    if isinstance(slug, str) and slug.startswith("ons-exports/"):
        filename = slug.split("/", 1)[1]
        path = (ONS_EXPORTS_DIR / filename).resolve()
        exports_root = ONS_EXPORTS_DIR.resolve()
        if not str(path).startswith(str(exports_root)):
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid ONS export path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not path.exists() or not path.is_file():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "ONS export not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        content, etag = _load_json_file(path)
        return content, etag, {"generatedAt": datetime.now(timezone.utc).isoformat(), "path": str(path)}
    if isinstance(slug, str) and slug.startswith("ons-cache"):
        filename = slug.split("ons-cache", 1)[-1].lstrip("/")
        path = ONS_CACHE_DIR / filename
        if path.exists():
            return (*_load_json_file(path), None)
    if isinstance(slug, str) and slug.startswith("exports/"):
        rel = slug.split("/", 1)[1]
        candidate = (EXPORTS_DIR / rel).resolve()
        exports_root = EXPORTS_DIR.resolve()
        if not str(candidate).startswith(str(exports_root)):
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid export path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not candidate.exists() or not candidate.is_file():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Export not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        content, etag = _load_json_file(candidate)
        return content, etag, {"generatedAt": datetime.now(timezone.utc).isoformat(), "path": str(candidate)}
    content = json.dumps({"isError": True, "code": "NOT_FOUND", "message": "Resource not found."})
    return content, _etag_from_bytes(content.encode("utf-8"), "missing"), None


__all__ = [
    "DATA_RESOURCE_PREFIX",
    "ONS_CACHE_PREFIX",
    "SKILL_PATH",
    "SKILLS_RESOURCE",
    "UI_DIR",
    "data_resource_uri",
    "list_data_resources",
    "list_skill_resources",
    "list_ui_resources",
    "load_data_content",
    "load_skill_content",
    "load_ui_content",
    "resolve_data_resource",
    "resolve_skill_resource",
    "resolve_ui_resource",
]
