from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    satquery_env: Literal["development", "production", "testing"] = "development"
    simulation_engine: Literal["local", "gmat"] = "local"
    default_body: str = "earth"
    default_satellite_count: int = 20
    database_url: str = "sqlite:///./satquery.db"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
