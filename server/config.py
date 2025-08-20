import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Add your config keys here
    OS_API_KEY: str = ""
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

load_dotenv()
settings = Settings()
