import os
import re
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv() -> None:
        return None

if TYPE_CHECKING:
    from pydantic_settings import BaseSettings as _PydanticBaseSettings
else:
    try:
        from pydantic_settings import BaseSettings as _PydanticBaseSettings
    except ImportError:  # pragma: no cover - optional dependency fallback
        class _PydanticBaseSettings:  # minimal shim for tests without pydantic-settings
            def __init__(self, **kwargs):
                annotations = getattr(type(self), "__annotations__", {})
                for key in annotations:
                    if key in kwargs:
                        value = kwargs[key]
                    else:
                        value = os.environ.get(key, getattr(type(self), key, None))
                    setattr(self, key, value)
                for key, value in kwargs.items():
                    setattr(self, key, value)


class Settings(_PydanticBaseSettings):
    OS_API_KEY: str = ""
    AUDIT_PACK_ROOT: str = "logs/audit-packs"
    DEBUG_ERRORS: bool = False
    LOG_JSON: bool = True
    RATE_LIMIT_PER_MIN: int = 207  # calibrated default per client IP
    METRICS_ENABLED: bool = True
    RATE_LIMIT_BYPASS: bool = False  # secure default; tests/dev may opt in explicitly
    RATE_LIMIT_EXEMPT_PATH_PREFIXES: str = (
        "/maps/vector/vts/tile,/maps/raster/osm,/maps/static/osm"
    )
    ADMIN_LOOKUP_LIVE_ENABLED: bool = True
    ADMIN_LOOKUP_ARCGIS_BASE: str = (
        "https://services1.arcgis.com/ESMARspQHYMw9BZ9/ArcGIS/rest/services"
    )
    ONS_CACHE_TTL: float = 60.0
    ONS_CACHE_SIZE: int = 256
    ONS_LIVE_ENABLED: bool = True
    ONS_SEARCH_LIVE_ENABLED: bool = True
    ONS_SELECT_LIVE_ENABLED: bool = True
    ONS_DATASET_API_BASE: str = "https://api.beta.ons.gov.uk/v1"
    ONS_CATALOG_PATH: str = "resources/ons_catalog.json"
    OS_CATALOG_PATH: str = "resources/os_catalog.json"
    NOMIS_LIVE_ENABLED: bool = True
    NOMIS_API_BASE: str = "https://www.nomisweb.co.uk/api/v01"
    NOMIS_UID: str = ""
    NOMIS_SIGNATURE: str = ""
    ONS_DATASET_CACHE_ENABLED: bool = True
    ONS_DATASET_CACHE_DIR: str = "data/cache/ons"
    ONS_GEO_CACHE_DIR: str = "data/cache/ons_geo"
    ONS_GEO_CACHE_DB: str = "ons_geo_cache.sqlite"
    ONS_GEO_CACHE_INDEX_PATH: str = "resources/ons_geo_cache_index.json"
    ONS_GEO_PRIMARY_DERIVATION: str = "exact"
    COUNCIL_TAX_BAND_LIVE_ENABLED: bool = True
    COUNCIL_TAX_BASE_URL: str = "https://www.tax.service.gov.uk/check-council-tax-band"
    COUNCIL_TAX_HTTP_TIMEOUT_SECONDS: float = 10.0
    COUNCIL_TAX_HTTP_RETRIES: int = 2
    COUNCIL_TAX_USER_AGENT: str = "mcp-geo-council-tax-pilot/0.1"
    OS_EXPORT_INLINE_MAX_BYTES: int = 200_000
    OS_DATA_CACHE_DIR: str = "data/cache/os"
    OS_DATA_CACHE_TTL: float = 3600.0
    OS_DATA_CACHE_SIZE: int = 512
    OS_HTTP_TIMEOUT_CONNECT_SECONDS: float = 2.0
    OS_HTTP_TIMEOUT_READ_SECONDS: float = 8.0
    OS_HTTP_RETRIES: int = 3
    OS_FEATURES_DEFAULT_LIMIT: int = 50
    OS_FEATURES_MAX_LIMIT: int = 100
    OS_FEATURES_DEFAULT_INCLUDE_GEOMETRY: bool = False
    OS_FEATURES_THIN_DEFAULT: bool = True
    OS_FEATURES_THIN_PROPERTY_LIMIT: int = 8
    OS_FEATURES_LOCAL_SCAN_PAGE_BUDGET: int = 1
    OS_FEATURES_MAX_POLYGON_VERTICES: int = 2000
    OS_FEATURES_MAX_BBOX_AREA_DEG2: float = 4.0
    OS_FEATURES_TIMEOUT_CONNECT_SECONDS: float = 2.0
    OS_FEATURES_TIMEOUT_READ_SECONDS: float = 12.0
    OS_FEATURES_RETRIES: int = 3
    OS_FEATURES_TIMEOUT_DEGRADED_LIMIT: int = 25
    UI_EVENT_LOG_PATH: str = "logs/ui-events.jsonl"
    PLAYGROUND_EVENT_LOG_PATH: str = "logs/playground-events.jsonl"
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    OSM_TILE_BASE: str = "https://tile.openstreetmap.org"
    OSM_TILE_CACHE_TTL: float = 3600.0
    OSM_TILE_CACHE_SIZE: int = 512
    OSM_TILE_USER_AGENT: str = "mcp-geo-playground"
    OSM_TILE_CONTACT: str = "https://github.com/chris-page-gov/mcp-geo"
    CIRCUIT_BREAKER_ENABLED: bool = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RESET_SECONDS: float = 30.0
    CIRCUIT_BREAKER_HALF_OPEN_SUCCESSES: int = 1
    BOUNDARY_CACHE_ENABLED: bool = False
    BOUNDARY_CACHE_DSN: str = ""
    BOUNDARY_CACHE_SCHEMA: str = "public"
    BOUNDARY_CACHE_TABLE: str = "admin_boundaries"
    BOUNDARY_DATASET_TABLE: str = "boundary_datasets"
    BOUNDARY_CACHE_MAX_AGE_DAYS: int = 180
    BOUNDARY_CACHE_FALLBACK_LIVE: bool = True
    OPENAI_WIDGET_DOMAIN: str = ""
    MCP_APPS_RESOURCE_LINK: bool = False
    MCP_APPS_CONTENT_MODE: str = ""
    MCP_HTTP_AUTH_MODE: str = "off"
    MCP_HTTP_AUTH_TOKEN: str = ""
    MCP_HTTP_JWT_HS256_SECRET: str = ""
    MCP_HTTP_JWT_ISSUER: str = ""
    MCP_HTTP_JWT_AUDIENCE: str = ""
    MCP_HTTP_JWT_REQUIRED_SCOPES: str = ""
    MCP_HTTP_SESSION_TTL: float = 900.0
    MCP_HTTP_SESSION_TOOL_CALL_LIMIT: int = 100
    MCP_TOOLS_DEFAULT_TOOLSET: str = ""
    MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS: str = ""
    MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS: str = ""
    MCP_RESOURCE_HTTP_LINKS_ENABLED: bool = False
    MCP_PUBLIC_BASE_URL: str = ""
    ROUTE_GRAPH_ENABLED: bool = False
    ROUTE_GRAPH_DSN: str = ""
    ROUTE_GRAPH_SCHEMA: str = "routing"
    ROUTE_GRAPH_EDGES_TABLE: str = "graph_edges"
    ROUTE_GRAPH_NODES_TABLE: str = "graph_nodes"
    ROUTE_GRAPH_METADATA_TABLE: str = "graph_metadata"
    ROUTE_GRAPH_RESTRICTIONS_TABLE: str = "edge_restrictions"
    ROUTE_GRAPH_TURN_RESTRICTIONS_TABLE: str = "turn_restrictions"
    ROUTE_GRAPH_RUNTIME_DIR: str = "data/runtime/routing"
    ROUTE_GRAPH_PROVENANCE_FILE: str = "os_mrn_downloads.json"
    ROUTE_GRAPH_MAX_STOPS: int = 8
    ROUTE_GRAPH_SOFT_AVOID_PENALTY_SECONDS: float = 180.0

    # Pydantic v2 style configuration (replaces deprecated inner Config class)
    model_config: ClassVar[dict[str, object]] = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # VS Code MCP config often supplies empty strings for unset env vars
        # (e.g. "${env:ONS_LIVE_ENABLED}" -> ""). Treat those as missing.
        "env_ignore_empty": True,
        "extra": "ignore",
    }


_ENV_PLACEHOLDER_RE = re.compile(r"^\$\{(?:env:)?([A-Z0-9_]+)\}$")


def _is_placeholder_secret_value(key: str, value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    if candidate == key:
        return True
    match = _ENV_PLACEHOLDER_RE.fullmatch(candidate)
    if match:
        return match.group(1) == key
    return False


def normalize_env_secret(
    key: str,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    env = environ if environ is not None else os.environ
    value = (env.get(key) or "").strip()
    if not _is_placeholder_secret_value(key, value):
        return
    env.pop(key, None)


def hydrate_env_secret_from_file(
    key: str,
    environ: MutableMapping[str, str] | None = None,
) -> None:
    env = environ if environ is not None else os.environ
    normalize_env_secret(key, env)
    value = (env.get(key) or "").strip()
    if value:
        return
    file_path = (env.get(f"{key}_FILE") or "").strip()
    if not file_path:
        return
    try:
        file_value = Path(file_path).expanduser().read_text(encoding="utf-8").strip()
    except OSError:
        return
    if file_value:
        env[key] = file_value


load_dotenv()
for _secret_key in (
    "OS_API_KEY",
    "NOMIS_UID",
    "NOMIS_SIGNATURE",
    "MCP_HTTP_AUTH_TOKEN",
    "MCP_HTTP_JWT_HS256_SECRET",
):
    hydrate_env_secret_from_file(_secret_key)


settings = Settings()
