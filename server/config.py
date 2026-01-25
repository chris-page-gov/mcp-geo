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
    LOG_JSON: bool = False
    RATE_LIMIT_PER_MIN: int = 120  # default per client IP
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
    ONS_DATASET_API_BASE: str = "https://api.beta.ons.gov.uk/v1"
    ONS_DATASET_CACHE_ENABLED: bool = True
    ONS_DATASET_CACHE_DIR: str = "data/cache/ons"
    UI_EVENT_LOG_PATH: str = "logs/ui-events.jsonl"
    PLAYGROUND_EVENT_LOG_PATH: str = "logs/playground-events.jsonl"

    # Pydantic v2 style configuration (replaces deprecated inner Config class)
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

load_dotenv()


settings = Settings()
