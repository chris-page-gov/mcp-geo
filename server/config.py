from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OS_API_KEY: str = ""
    DEBUG_ERRORS: bool = False
    LOG_JSON: bool = False
    RATE_LIMIT_PER_MIN: int = 120  # default per client IP
    METRICS_ENABLED: bool = True
    RATE_LIMIT_BYPASS: bool = True  # bypass limiter (tests toggle off when needed)

    # Pydantic v2 style configuration (replaces deprecated inner Config class)
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

load_dotenv()


settings = Settings()
