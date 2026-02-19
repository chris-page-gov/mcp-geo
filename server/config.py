try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv() -> None:
        return None

try:
    from pydantic_settings import BaseSettings
except ImportError:  # pragma: no cover - optional dependency fallback
    class BaseSettings:  # minimal shim for tests without pydantic-settings
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class Settings(BaseSettings):
    OS_API_KEY: str = ""
    DEBUG_ERRORS: bool = False
    LOG_JSON: bool = True
    RATE_LIMIT_PER_MIN: int = 207  # calibrated default per client IP
    METRICS_ENABLED: bool = True
    RATE_LIMIT_BYPASS: bool = True  # bypass limiter (tests toggle off when needed)
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
    MCP_TOOLS_DEFAULT_TOOLSET: str = ""
    MCP_TOOLS_DEFAULT_INCLUDE_TOOLSETS: str = ""
    MCP_TOOLS_DEFAULT_EXCLUDE_TOOLSETS: str = ""

    # Pydantic v2 style configuration (replaces deprecated inner Config class)
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # VS Code MCP config often supplies empty strings for unset env vars
        # (e.g. "${env:ONS_LIVE_ENABLED}" -> ""). Treat those as missing.
        "env_ignore_empty": True,
        "extra": "ignore",
    }

load_dotenv()


settings = Settings()
