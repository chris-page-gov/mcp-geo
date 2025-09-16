from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OS_API_KEY: str = ""
    DEBUG_ERRORS: bool = False
    LOG_JSON: bool = False

    # Pydantic v2 style configuration (replaces deprecated inner Config class)
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

load_dotenv()


settings = Settings()
