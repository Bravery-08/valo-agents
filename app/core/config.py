from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "valoagents"
    environment: str = "development"
    debug: bool = True

    # CORS
    cors_origins: List[AnyHttpUrl] = []

    # HTTP client
    http_timeout_seconds: float = 15.0
    http_max_retries: int = 2

    # Caching
    map_pool_ttl_seconds: int = 900  # 15 minutes
    agents_ttl_seconds: int = 900  # 15 minutes
    agents_cache_maxsize: int = 128

    # External endpoints
    map_pool_url: str = "https://www.thespike.gg/valorant/maps/map-pool"
    agents_api_url: str = (
        "https://api.tracker.gg/api/v2/valorant/insights/agents?playlist=competitive&map={map}&division=radiant"
    )

    # pydantic-settings v2 style configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()