from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

from server.config import settings
ROOT = Path(__file__).resolve().parent.parent.parent
UI_DIR = ROOT / "ui"
SKILL_PATH = ROOT / "SKILL.md"
BOUNDARY_MANIFEST_PATH = ROOT / "docs" / "Boundaries.json"
BOUNDARY_RUNS_DIR = ROOT / "data" / "boundary_runs"
ONS_CATALOG_PATH = ROOT / "resources" / "ons_catalog.json"
OS_CATALOG_PATH = ROOT / "resources" / "os_catalog.json"
LAYERS_CATALOG_PATH = ROOT / "resources" / "layers_catalog.json"
LANDIS_PRODUCTS_PATH = ROOT / "resources" / "landis_products.json"
LANDIS_SOIL_DATA_STRUCTURES_PATH = ROOT / "resources" / "landis" / "soil_data_structures.md"
LANDIS_SOIL_CLASSIFICATION_PATH = ROOT / "resources" / "landis" / "soil_classification.md"
LANDIS_LICENCE_CURRENT_PATH = ROOT / "resources" / "landis" / "licence_current.md"
LANDIS_PORTAL_INVENTORY_PATH = (
    ROOT / "research" / "landis-data-source" / "landis_portal_inventory_2026-04-04.json"
)
LANDIS_ARCHIVE_TRIAGE_PATH = (
    ROOT / "research" / "landis-data-source" / "landis_archive_triage_2026-04-05.json"
)
LANDIS_FULL_RELEASE_MANIFEST_PATH = (
    ROOT / "research" / "landis-data-source" / "landis_full_release_manifest_2026-04-05.json"
)
PROTECTED_LANDSCAPES_PATH = ROOT / "resources" / "protected_landscapes_england.json"
PEAT_LAYERS_PATH = ROOT / "resources" / "peat_layers_england.json"
NOMIS_WORKFLOWS_PATH = ROOT / "resources" / "nomis_workflows.json"
ONS_GEO_SOURCES_PATH = ROOT / "resources" / "ons_geo_sources.json"
ONS_GEO_CACHE_INDEX_PATH = ROOT / "resources" / "ons_geo_cache_index.json"
BOUNDARY_PACK_SOURCES_PATH = ROOT / "resources" / "boundary_pack_sources.json"
CODE_LIST_PACK_SOURCES_PATH = ROOT / "resources" / "code_list_pack_sources.json"
BOUNDARY_PACKS_INDEX_PATH = ROOT / "resources" / "boundary_packs_index.json"
CODE_LIST_PACKS_INDEX_PATH = ROOT / "resources" / "code_list_packs_index.json"
OFFLINE_MAP_CATALOG_PATH = ROOT / "resources" / "offline_map_catalog.json"
MAP_EMBEDDING_STYLE_PROFILES_PATH = ROOT / "resources" / "map_embedding_style_profiles.json"
EXPORTS_DIR = ROOT / "data" / "exports"
ONS_EXPORTS_DIR = ROOT / "data" / "ons_exports"
OFFLINE_PACKS_DIR = ROOT / "data" / "offline_packs"
MAP_SCENARIO_PACKS_DIR = ROOT / "data" / "map_scenario_packs"
STAKEHOLDER_BENCHMARK_PACK_PATH = (
    ROOT / "data" / "benchmarking" / "stakeholder_eval" / "benchmark_pack_v1.json"
)
STAKEHOLDER_BENCHMARK_LIVE_ALIAS_PATH = (
    ROOT / "data" / "benchmarking" / "stakeholder_eval" / "live_run_latest.json"
)


def _resolve_data_path(raw: str | None, default: str) -> Path:
    value = str(raw or default)
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / value
    return path


OS_CACHE_DIR = _resolve_data_path(getattr(settings, "OS_DATA_CACHE_DIR", None), "data/cache/os")
ONS_CACHE_DIR = _resolve_data_path(getattr(settings, "ONS_DATASET_CACHE_DIR", None), "data/cache/ons")
OS_EXPORTS_DIR = _resolve_data_path(None, "data/os_exports")

DATA_RESOURCE_PREFIX = "resource://mcp-geo/"
ONS_CACHE_PREFIX = f"{DATA_RESOURCE_PREFIX}ons-cache/"
ONS_EXPORTS_PREFIX = f"{DATA_RESOURCE_PREFIX}ons-exports/"
OS_CACHE_PREFIX = f"{DATA_RESOURCE_PREFIX}os-cache/"
OS_EXPORTS_PREFIX = f"{DATA_RESOURCE_PREFIX}os-exports/"
OFFLINE_PACKS_PREFIX = f"{DATA_RESOURCE_PREFIX}offline-packs/"
MAP_SCENARIO_PACKS_PREFIX = f"{DATA_RESOURCE_PREFIX}map-scenario-packs/"
MCP_APPS_MIME = "text/html;profile=mcp-app"
OFFLINE_PACK_INLINE_MAX_BYTES = 512 * 1024

_UI_ASSET_PATHS = {
    "vendor/maplibre-gl.css": "/ui/vendor/maplibre-gl.css",
    "vendor/maplibre-gl.js": "/ui/vendor/maplibre-gl.js",
    "vendor/maplibre-gl-csp-worker.js": "/ui/vendor/maplibre-gl-csp-worker.js",
    "vendor/shp.min.js": "/ui/vendor/shp.min.js",
    "shared/compact_contract.css": "/ui/shared/compact_contract.css",
    "shared/compact_contract.js": "/ui/shared/compact_contract.js",
}
_UI_ASSET_REF_PATTERN = re.compile(
    r'(?P<attr>\b(?:src|href)=)(?P<quote>["\'])'
    r'(?P<path>'
    r'vendor/maplibre-gl\.css|'
    r'vendor/maplibre-gl\.js|'
    r'vendor/maplibre-gl-csp-worker\.js|'
    r'vendor/shp\.min\.js|'
    r'shared/compact_contract\.css|'
    r'shared/compact_contract\.js'
    r')(?P=quote)'
)


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
                "https://tile.openstreetmap.org",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ],
            "resourceDomains": [
                "self",
                "https://api.os.uk",
                "https://fonts.googleapis.com",
                "https://fonts.gstatic.com",
                "https://tile.openstreetmap.org",
            ],
            "workerDomains": ["self", "blob:"],
        },
        "permissions": {"sameOrigin": True},
    },
    {
        "slug": "boundary-explorer",
        "name": "ui_boundary_explorer",
        "title": "Map Lab",
        "description": (
            "Map Lab workspace for learning and building UK maps with boundaries, UPRNs, "
            "buildings, links, selector-based collections, and export."
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
                "https://tile.openstreetmap.org",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ],
            "resourceDomains": [
                "self",
                "https://api.os.uk",
                "https://fonts.googleapis.com",
                "https://fonts.gstatic.com",
                "https://tile.openstreetmap.org",
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
        "slug": "simple-map-lab",
        "name": "ui_simple_map_lab",
        "title": "Simple Map Lab",
        "description": (
            "Minimal lab for simple map delivery tests: OS vector proxy auth fallback and PMTiles "
            "browser-render trials."
        ),
        "file": "simple_map.html",
        "annotations": {
            "audience": ["user"],
            "priority": 0.6,
            "capabilities": ["map", "benchmark", "auth", "pmtiles"],
        },
        "csp": None,
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
        "slug": "landis-products",
        "name": "data_landis_products",
        "title": "LandIS Product Registry",
        "description": "Checked-in registry for the LandIS MVP product, metadata, and provenance surface.",
        "path": LANDIS_PRODUCTS_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "landis"},
    },
    {
        "slug": "landis-docs-soil-data-structures",
        "name": "data_landis_docs_soil_data_structures",
        "title": "LandIS Soil Data Structures",
        "description": "Operational join guidance for LandIS association, series, and horizon data.",
        "path": LANDIS_SOIL_DATA_STRUCTURES_PATH,
        "mimeType": "text/markdown",
        "annotations": {"type": "guide", "domain": "landis"},
    },
    {
        "slug": "landis-docs-soil-classification",
        "name": "data_landis_docs_soil_classification",
        "title": "LandIS Soil Classification Guidance",
        "description": "Operational classification and caveat guidance for LandIS-derived outputs.",
        "path": LANDIS_SOIL_CLASSIFICATION_PATH,
        "mimeType": "text/markdown",
        "annotations": {"type": "guide", "domain": "landis"},
    },
    {
        "slug": "landis-licence-current",
        "name": "data_landis_licence_current",
        "title": "LandIS Licence and Open Access Status",
        "description": "Current LandIS open-access and licence validation note for the MVP.",
        "path": LANDIS_LICENCE_CURRENT_PATH,
        "mimeType": "text/markdown",
        "annotations": {"type": "guide", "domain": "landis"},
    },
    {
        "slug": "landis-portal-inventory",
        "name": "data_landis_portal_inventory",
        "title": "LandIS Portal Inventory",
        "description": "Authenticated inventory of the mirrored LandIS portal catalog.",
        "path": LANDIS_PORTAL_INVENTORY_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "landis"},
    },
    {
        "slug": "landis-archive-triage",
        "name": "data_landis_archive_triage",
        "title": "LandIS Archive Triage",
        "description": "Machine-readable triage manifest for the local LandIS archive and release inventory.",
        "path": LANDIS_ARCHIVE_TRIAGE_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "landis"},
    },
    {
        "slug": "landis-full-release-manifest",
        "name": "data_landis_full_release_manifest",
        "title": "LandIS Full Release Manifest",
        "description": "Supplementary public/data.gov release manifest captured alongside the portal mirror.",
        "path": LANDIS_FULL_RELEASE_MANIFEST_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "landis"},
    },
    {
        "slug": "protected-landscapes-england",
        "name": "data_protected_landscapes_england",
        "title": "Protected Landscapes (England)",
        "description": "AONB/National Landscape lookup dataset used for AOI-first survey routing.",
        "path": PROTECTED_LANDSCAPES_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "dataset", "domain": "boundaries"},
    },
    {
        "slug": "peat-layers-england",
        "name": "data_peat_layers_england",
        "title": "Peat Evidence Layers (England)",
        "description": (
            "Peat evidence/proxy layer registry with AOI query strategy, provenance, confidence, and caveats."
        ),
        "path": PEAT_LAYERS_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "dataset", "domain": "environment"},
    },
    {
        "slug": "offline-map-catalog",
        "name": "data_offline_map_catalog",
        "title": "Offline Map Catalog",
        "description": "PMTiles/MBTiles offline pack catalog and retrieval contracts.",
        "path": OFFLINE_MAP_CATALOG_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "maps"},
    },
    {
        "slug": "map-embedding-style-profiles",
        "name": "data_map_embedding_style_profiles",
        "title": "Map Embedding Style Profiles",
        "description": "Lightweight style profiles for constrained MCP/AI host embedding contexts.",
        "path": MAP_EMBEDDING_STYLE_PROFILES_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "guide", "domain": "maps"},
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
        "slug": "ons-geo-sources",
        "name": "data_ons_geo_sources",
        "title": "ONS Geography Source Manifest",
        "description": (
            "Manifest of exact and best-fit ONS geography products (ONSPD/ONSUD and NSPL/NSUL)."
        ),
        "path": ONS_GEO_SOURCES_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "manifest", "domain": "ons"},
    },
    {
        "slug": "ons-geo-cache-index",
        "name": "data_ons_geo_cache_index",
        "title": "ONS Geography Cache Index",
        "description": "Index/status for local ONS geography cache refresh runs.",
        "path": ONS_GEO_CACHE_INDEX_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "index", "domain": "ons"},
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
    {
        "slug": "stakeholder-benchmark-pack",
        "name": "data_stakeholder_benchmark_pack",
        "title": "Stakeholder Benchmark Pack",
        "description": "Scenario pack used by the playground benchmarks workbench and live-run harness.",
        "path": STAKEHOLDER_BENCHMARK_PACK_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "benchmark", "domain": "evaluation"},
    },
    {
        "slug": "stakeholder-benchmark-live-run-latest",
        "name": "data_stakeholder_benchmark_live_run_latest",
        "title": "Stakeholder Benchmark Live Run (Latest)",
        "description": "Stable alias to the latest reviewed stakeholder benchmark live-run artifact.",
        "path": STAKEHOLDER_BENCHMARK_LIVE_ALIAS_PATH,
        "mimeType": "application/json",
        "annotations": {"type": "benchmark-live", "domain": "evaluation"},
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


def _os_cache_files() -> list[Path]:
    if not OS_CACHE_DIR.exists():
        return []
    return sorted(path for path in OS_CACHE_DIR.glob("*.json") if path.is_file())


def _os_export_files() -> list[Path]:
    if not OS_EXPORTS_DIR.exists():
        return []
    return sorted(path for path in OS_EXPORTS_DIR.rglob("*") if path.is_file())


def _is_path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_disallowed_path_tokens(relative_path: str) -> bool:
    if not relative_path:
        return True
    lowered = relative_path.lower()
    if "%2f" in lowered or "%5c" in lowered:
        return True
    if "\\" in relative_path or "\x00" in relative_path:
        return True
    if relative_path.startswith("/"):
        return True
    normalized = relative_path.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return any(part in {".", ".."} for part in parts)


def _resolve_scoped_path(root: Path, relative_path: str) -> Path | None:
    if _has_disallowed_path_tokens(relative_path):
        return None
    resolved_root = root.resolve()
    candidate = (resolved_root / relative_path).resolve()
    if not _is_path_within(candidate, resolved_root):
        return None
    return candidate


def _offline_pack_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pmtiles":
        return "application/vnd.pmtiles"
    if suffix == ".mbtiles":
        return "application/vnd.sqlite3"
    return "application/octet-stream"


def _offline_pack_download_url(uri: str) -> str:
    return f"/resources/download?uri={quote(uri, safe='')}"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _offline_pack_payload(*, path: Path, uri: str) -> tuple[dict[str, Any], str]:
    size_bytes = path.stat().st_size
    sha256 = _sha256_file(path)
    payload = {
        "name": path.name,
        "uri": uri,
        "downloadUrl": _offline_pack_download_url(uri),
        "mediaType": _offline_pack_media_type(path),
        "bytes": size_bytes,
        "sha256": sha256,
    }
    if size_bytes <= OFFLINE_PACK_INLINE_MAX_BYTES:
        payload["encoding"] = "base64"
        payload["blob"] = base64.b64encode(path.read_bytes()).decode("ascii")
    else:
        payload["encoding"] = "external"
        payload["blobOmitted"] = True
        payload["inlineMaxBytes"] = OFFLINE_PACK_INLINE_MAX_BYTES
        payload["message"] = "Offline pack too large for inline payload; use downloadUrl."
    return payload, sha256


def _trusted_offline_pack_entries() -> list[tuple[str, Path]]:
    if not OFFLINE_MAP_CATALOG_PATH.exists():
        return []
    try:
        catalog = json.loads(OFFLINE_MAP_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    packs = catalog.get("packs")
    if not isinstance(packs, list):
        return []
    try:
        resolved_root = OFFLINE_PACKS_DIR.resolve()
    except OSError:
        return []
    available = {pack_path.name: pack_path.resolve() for pack_path in _offline_pack_files()}
    seen_uris: set[str] = set()
    resolved: list[tuple[str, Path]] = []
    for pack in packs:
        if not isinstance(pack, dict):
            continue
        resource_uri = pack.get("resourceUri")
        if not isinstance(resource_uri, str) or not resource_uri.startswith(OFFLINE_PACKS_PREFIX):
            continue
        filename = resource_uri[len(OFFLINE_PACKS_PREFIX) :]
        if (
            not filename
            or _has_disallowed_path_tokens(filename)
            or Path(filename).name != filename
            or resource_uri in seen_uris
        ):
            continue
        path = available.get(filename)
        if path is None or not _is_path_within(path, resolved_root):
            continue
        seen_uris.add(resource_uri)
        resolved.append((resource_uri, path))
    return resolved


def _offline_pack_path_by_uri() -> dict[str, Path]:
    return {resource_uri: path for resource_uri, path in _trusted_offline_pack_entries()}


def resolve_offline_pack_download(uri: str) -> tuple[Path, str] | None:
    trusted_paths = _offline_pack_path_by_uri()
    path = trusted_paths.get(uri)
    if path is not None:
        return path, _offline_pack_media_type(path)
    return None


def _offline_pack_files() -> list[Path]:
    if not OFFLINE_PACKS_DIR.exists():
        return []
    resolved_root = OFFLINE_PACKS_DIR.resolve()
    files: list[Path] = []
    for path in OFFLINE_PACKS_DIR.glob("*"):
        if not path.is_file():
            continue
        try:
            resolved_path = path.resolve()
        except OSError:
            continue
        if not _is_path_within(resolved_path, resolved_root):
            continue
        files.append(path)
    return sorted(files)


def _map_scenario_pack_files() -> list[Path]:
    if not MAP_SCENARIO_PACKS_DIR.exists():
        return []
    return sorted(path for path in MAP_SCENARIO_PACKS_DIR.glob("*.json") if path.is_file())


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
    os_cache_files = _os_cache_files()
    if os_cache_files:
        resources.append(
            {
                "uri": data_resource_uri("os-cache-index"),
                "name": "data_os_cache_index",
                "title": "OS Cache Index",
                "description": "Index of locally cached OS API responses.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "os"},
                "type": "data",
            }
        )
    os_export_files = _os_export_files()
    if os_export_files:
        resources.append(
            {
                "uri": data_resource_uri("os-exports-index"),
                "name": "data_os_exports_index",
                "title": "OS Export Resource Index",
                "description": "Index of resource-backed OS export artifacts.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "os"},
                "type": "data",
            }
        )
    offline_pack_entries = _trusted_offline_pack_entries()
    if offline_pack_entries:
        resources.append(
            {
                "uri": data_resource_uri("offline-packs-index"),
                "name": "data_offline_packs_index",
                "title": "Offline Pack Resource Index",
                "description": "Index of PMTiles/MBTiles offline pack artifacts.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "maps"},
                "type": "data",
            }
        )
    scenario_pack_files = _map_scenario_pack_files()
    if scenario_pack_files:
        resources.append(
            {
                "uri": data_resource_uri("map-scenario-packs-index"),
                "name": "data_map_scenario_packs_index",
                "title": "Map Scenario Packs Index",
                "description": "Notebook-generated scenario packs with provenance metadata.",
                "mimeType": "application/json",
                "annotations": {"type": "index", "domain": "maps"},
                "type": "data",
            }
        )
        for path in scenario_pack_files:
            resources.append(
                {
                    "uri": f"{MAP_SCENARIO_PACKS_PREFIX}{path.name}",
                    "name": f"data_map_scenario_pack_{path.stem}",
                    "title": f"Map Scenario Pack: {path.name}",
                    "description": "Notebook-generated map scenario pack artifact.",
                    "mimeType": "application/json",
                    "annotations": {"type": "dataset", "domain": "maps"},
                    "type": "data",
                }
            )
    return resources


def _etag_from_bytes(content: bytes, variant: str = "") -> str:
    base = content + variant.encode()
    h = hashlib.sha256(base).hexdigest()[:16]
    return f'W/"{h}"'


def _normalize_ui_asset_paths(content: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        path = match.group("path")
        normalized = _UI_ASSET_PATHS.get(path, path)
        return f'{match.group("attr")}{match.group("quote")}{normalized}{match.group("quote")}'

    return _UI_ASSET_REF_PATTERN.sub(_replace, content)


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
    if slug == "os-cache-index":
        return {"slug": slug}
    if slug == "os-exports-index":
        return {"slug": slug}
    if slug == "offline-packs-index":
        return {"slug": slug}
    if slug == "map-scenario-packs-index":
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("exports/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("ons-exports/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("os-cache/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("os-exports/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("offline-packs/"):
        return {"slug": slug}
    if isinstance(slug, str) and slug.startswith("map-scenario-packs/"):
        return {"slug": slug}
    if identifier.startswith(ONS_CACHE_PREFIX) or slug.startswith("ons-cache/"):
        return {"slug": slug}
    return None


def load_ui_content(
    entry: dict[str, Any], *, asset_mode: str = "relative"
) -> tuple[str, str]:
    path = UI_DIR / entry["file"]
    content = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".html" and asset_mode == "absolute":
        content = _normalize_ui_asset_paths(content)
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


def _load_text_file(path: Path) -> tuple[str, str]:
    content = path.read_text(encoding="utf-8")
    etag = _etag_from_bytes(content.encode("utf-8"), str(path))
    return content, etag


def _load_benchmark_live_alias(path: Path) -> tuple[str, str, dict[str, Any] | None]:
    if not path.exists():
        content = json.dumps(
            {"isError": True, "code": "NOT_FOUND", "message": "Benchmark live-run alias not found."}
        )
        return content, _etag_from_bytes(b"missing", "stakeholder-benchmark-live-run-latest"), None

    alias_raw = path.read_text(encoding="utf-8")
    try:
        alias_payload = json.loads(alias_raw)
    except json.JSONDecodeError:
        content = json.dumps(
            {
                "isError": True,
                "code": "INVALID_CONFIGURATION",
                "message": "Benchmark live-run alias JSON is invalid.",
            }
        )
        return content, _etag_from_bytes(alias_raw.encode("utf-8"), str(path)), None
    if not isinstance(alias_payload, dict):
        content = json.dumps(
            {
                "isError": True,
                "code": "INVALID_CONFIGURATION",
                "message": "Benchmark live-run alias JSON must be an object.",
            }
        )
        return content, _etag_from_bytes(alias_raw.encode("utf-8"), str(path)), None
    target_name = alias_payload.get("aliasOf")
    if not isinstance(target_name, str) or not target_name.strip():
        content = json.dumps(
            {
                "isError": True,
                "code": "INVALID_CONFIGURATION",
                "message": "Benchmark live-run alias is missing aliasOf.",
            }
        )
        return content, _etag_from_bytes(content.encode("utf-8"), str(path)), None

    target_path = _resolve_scoped_path(path.parent, target_name.strip())
    if target_path is None or not target_path.exists() or not target_path.is_file():
        content = json.dumps(
            {
                "isError": True,
                "code": "NOT_FOUND",
                "message": "Benchmark live-run target not found.",
            }
        )
        return content, _etag_from_bytes(content.encode("utf-8"), str(path)), None

    target_raw = target_path.read_text(encoding="utf-8")
    try:
        payload = json.loads(target_raw)
    except json.JSONDecodeError:
        content = json.dumps(
            {
                "isError": True,
                "code": "INVALID_CONFIGURATION",
                "message": "Benchmark live-run target JSON is invalid.",
            }
        )
        return content, _etag_from_bytes(target_raw.encode("utf-8"), str(target_path)), None
    if isinstance(payload, dict):
        payload["latestAlias"] = {
            "aliasFile": path.name,
            "targetFile": target_path.name,
            "aliasUpdated": alias_payload.get("aliasUpdated"),
            "note": alias_payload.get("note"),
        }
    content = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return content, _etag_from_bytes(content.encode("utf-8"), str(target_path)), {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "path": str(target_path),
        "aliasPath": str(path),
    }


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
    if slug == "landis-products":
        if not LANDIS_PRODUCTS_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "LandIS product registry not found."}
            )
            return content, _etag_from_bytes(b"missing", "landis-products"), None
        return (*_load_json_file(LANDIS_PRODUCTS_PATH), None)
    if slug == "landis-docs-soil-data-structures":
        if not LANDIS_SOIL_DATA_STRUCTURES_PATH.exists():
            content = json.dumps(
                {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "LandIS soil data structures resource not found.",
                }
            )
            return content, _etag_from_bytes(b"missing", "landis-docs-soil-data-structures"), None
        return (*_load_text_file(LANDIS_SOIL_DATA_STRUCTURES_PATH), None)
    if slug == "landis-docs-soil-classification":
        if not LANDIS_SOIL_CLASSIFICATION_PATH.exists():
            content = json.dumps(
                {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "LandIS soil classification resource not found.",
                }
            )
            return content, _etag_from_bytes(b"missing", "landis-docs-soil-classification"), None
        return (*_load_text_file(LANDIS_SOIL_CLASSIFICATION_PATH), None)
    if slug == "landis-licence-current":
        if not LANDIS_LICENCE_CURRENT_PATH.exists():
            content = json.dumps(
                {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "LandIS licence resource not found.",
                }
            )
            return content, _etag_from_bytes(b"missing", "landis-licence-current"), None
        return (*_load_text_file(LANDIS_LICENCE_CURRENT_PATH), None)
    if slug == "landis-portal-inventory":
        if not LANDIS_PORTAL_INVENTORY_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "LandIS portal inventory not found."}
            )
            return content, _etag_from_bytes(b"missing", "landis-portal-inventory"), None
        return (*_load_json_file(LANDIS_PORTAL_INVENTORY_PATH), None)
    if slug == "landis-archive-triage":
        if not LANDIS_ARCHIVE_TRIAGE_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "LandIS archive triage not found."}
            )
            return content, _etag_from_bytes(b"missing", "landis-archive-triage"), None
        return (*_load_json_file(LANDIS_ARCHIVE_TRIAGE_PATH), None)
    if slug == "landis-full-release-manifest":
        if not LANDIS_FULL_RELEASE_MANIFEST_PATH.exists():
            content = json.dumps(
                {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "LandIS full release manifest not found.",
                }
            )
            return content, _etag_from_bytes(b"missing", "landis-full-release-manifest"), None
        return (*_load_json_file(LANDIS_FULL_RELEASE_MANIFEST_PATH), None)
    if slug == "protected-landscapes-england":
        if not PROTECTED_LANDSCAPES_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Protected landscapes catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "protected-landscapes-england"), None
        return (*_load_json_file(PROTECTED_LANDSCAPES_PATH), None)
    if slug == "peat-layers-england":
        if not PEAT_LAYERS_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Peat layers catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "peat-layers-england"), None
        return (*_load_json_file(PEAT_LAYERS_PATH), None)
    if slug == "offline-map-catalog":
        if not OFFLINE_MAP_CATALOG_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Offline map catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "offline-map-catalog"), None
        return (*_load_json_file(OFFLINE_MAP_CATALOG_PATH), None)
    if slug == "map-embedding-style-profiles":
        if not MAP_EMBEDDING_STYLE_PROFILES_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Map embedding style profiles not found."}
            )
            return content, _etag_from_bytes(b"missing", "map-embedding-style-profiles"), None
        return (*_load_json_file(MAP_EMBEDDING_STYLE_PROFILES_PATH), None)
    if slug == "nomis-workflows":
        if not NOMIS_WORKFLOWS_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "NOMIS workflows catalog not found."}
            )
            return content, _etag_from_bytes(b"missing", "nomis-workflows"), None
        return (*_load_json_file(NOMIS_WORKFLOWS_PATH), None)
    if slug == "ons-geo-sources":
        if not ONS_GEO_SOURCES_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "ONS geo sources manifest not found."}
            )
            return content, _etag_from_bytes(b"missing", "ons-geo-sources"), None
        return (*_load_json_file(ONS_GEO_SOURCES_PATH), None)
    if slug == "ons-geo-cache-index":
        if not ONS_GEO_CACHE_INDEX_PATH.exists():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "ONS geo cache index not found."}
            )
            return content, _etag_from_bytes(b"missing", "ons-geo-cache-index"), None
        return (*_load_json_file(ONS_GEO_CACHE_INDEX_PATH), None)
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
    if slug == "stakeholder-benchmark-pack":
        if not STAKEHOLDER_BENCHMARK_PACK_PATH.exists():
            content = json.dumps(
                {
                    "isError": True,
                    "code": "NOT_FOUND",
                    "message": "Stakeholder benchmark pack not found.",
                }
            )
            return content, _etag_from_bytes(b"missing", "stakeholder-benchmark-pack"), None
        return (*_load_json_file(STAKEHOLDER_BENCHMARK_PACK_PATH), None)
    if slug == "stakeholder-benchmark-live-run-latest":
        return _load_benchmark_live_alias(STAKEHOLDER_BENCHMARK_LIVE_ALIAS_PATH)
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
                "performance": {
                    "degraded": True,
                    "reason": "cache_unavailable",
                    "impact": (
                        "Boundary cache is unavailable; tools may rely on slower live lookups "
                        "or reduced fallback behavior."
                    ),
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
            status.setdefault(
                "performance",
                {
                    "degraded": status.get("maturity", {}).get("state") != "ready",
                    "reason": "cache_state_unknown",
                    "impact": (
                        "Boundary cache health is unknown; fallback behavior may affect response "
                        "time and geometry reliability."
                    ),
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
        for cache_path in _ons_cache_files():
            items.append(
                {
                    "name": cache_path.name,
                    "uri": f"{ONS_CACHE_PREFIX}{cache_path.name}",
                    "bytes": cache_path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "ons-cache-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "ons-exports-index":
        items = []
        for export_path in _ons_export_files():
            items.append(
                {
                    "name": export_path.name,
                    "uri": f"{ONS_EXPORTS_PREFIX}{export_path.name}",
                    "bytes": export_path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "ons-exports-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "os-cache-index":
        items = []
        for cache_path in _os_cache_files():
            items.append(
                {
                    "name": cache_path.name,
                    "uri": f"{OS_CACHE_PREFIX}{cache_path.name}",
                    "bytes": cache_path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "os-cache-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "os-exports-index":
        items = []
        for export_path in _os_export_files():
            try:
                rel = export_path.relative_to(OS_EXPORTS_DIR).as_posix()
            except ValueError:
                rel = export_path.name
            items.append(
                {
                    "name": rel,
                    "uri": f"{OS_EXPORTS_PREFIX}{rel}",
                    "bytes": export_path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "os-exports-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "offline-packs-index":
        items = []
        for resource_uri, pack_path in _trusted_offline_pack_entries():
            try:
                size_bytes = pack_path.stat().st_size
            except OSError:
                continue
            items.append(
                {
                    "name": pack_path.name,
                    "uri": resource_uri,
                    "bytes": size_bytes,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "offline-packs-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if slug == "map-scenario-packs-index":
        items = []
        for scenario_path in _map_scenario_pack_files():
            items.append(
                {
                    "name": scenario_path.name,
                    "uri": f"{MAP_SCENARIO_PACKS_PREFIX}{scenario_path.name}",
                    "bytes": scenario_path.stat().st_size,
                }
            )
        content = json.dumps({"items": items}, ensure_ascii=True, separators=(",", ":"))
        return (
            content,
            _etag_from_bytes(content.encode("utf-8"), "map-scenario-packs-index"),
            {"generatedAt": datetime.now(timezone.utc).isoformat()},
        )
    if isinstance(slug, str) and slug.startswith("ons-cache/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(ONS_CACHE_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid ONS cache path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not path.exists():
            content = json.dumps({"isError": True, "code": "NOT_FOUND", "message": "ONS cache file not found."})
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        return (*_load_json_file(path), None)
    if isinstance(slug, str) and slug.startswith("ons-exports/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(ONS_EXPORTS_DIR, filename)
        if path is None:
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
    if isinstance(slug, str) and slug.startswith("os-cache/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(OS_CACHE_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid OS cache path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not path.exists() or not path.is_file():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "OS cache file not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        return (*_load_json_file(path), None)
    if isinstance(slug, str) and slug.startswith("os-exports/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(OS_EXPORTS_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid OS export path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not path.exists() or not path.is_file():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "OS export not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        suffix = path.suffix.lower()
        if suffix == ".json":
            content, etag = _load_json_file(path)
            return content, etag, {
                "generatedAt": datetime.now(timezone.utc).isoformat(),
                "path": str(path),
                "mimeType": "application/json",
            }
        content = path.read_text(encoding="utf-8")
        etag = _etag_from_bytes(content.encode("utf-8"), slug)
        mime_type = "text/csv" if suffix == ".csv" else "text/plain"
        return content, etag, {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "path": str(path),
            "mimeType": mime_type,
        }
    if isinstance(slug, str) and slug.startswith("offline-packs/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(OFFLINE_PACKS_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid offline pack path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        resource_uri = f"{OFFLINE_PACKS_PREFIX}{filename}"
        resolved = resolve_offline_pack_download(resource_uri)
        if resolved is None:
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Offline pack not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        path, _media_type = resolved
        payload, sha256 = _offline_pack_payload(path=path, uri=resource_uri)
        content = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        etag = _etag_from_bytes(sha256.encode("ascii"), slug)
        return content, etag, {"generatedAt": datetime.now(timezone.utc).isoformat(), "path": str(path)}
    if isinstance(slug, str) and slug.startswith("map-scenario-packs/"):
        filename = slug.split("/", 1)[1]
        path = _resolve_scoped_path(MAP_SCENARIO_PACKS_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid scenario pack path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if not path.exists() or not path.is_file():
            content = json.dumps(
                {"isError": True, "code": "NOT_FOUND", "message": "Scenario pack not found."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        content, etag = _load_json_file(path)
        return content, etag, {"generatedAt": datetime.now(timezone.utc).isoformat(), "path": str(path)}
    if isinstance(slug, str) and slug.startswith("ons-cache"):
        filename = slug.split("ons-cache", 1)[-1].lstrip("/")
        path = _resolve_scoped_path(ONS_CACHE_DIR, filename)
        if path is None:
            content = json.dumps(
                {"isError": True, "code": "INVALID_INPUT", "message": "Invalid ONS cache path."}
            )
            return content, _etag_from_bytes(content.encode("utf-8"), slug), None
        if path.exists():
            return (*_load_json_file(path), None)
    if isinstance(slug, str) and slug.startswith("exports/"):
        rel = slug.split("/", 1)[1]
        candidate = _resolve_scoped_path(EXPORTS_DIR, rel)
        if candidate is None:
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
    "OFFLINE_PACKS_PREFIX",
    "MAP_SCENARIO_PACKS_PREFIX",
    "OS_CACHE_PREFIX",
    "OS_EXPORTS_PREFIX",
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
    "resolve_offline_pack_download",
    "resolve_skill_resource",
    "resolve_ui_resource",
]
