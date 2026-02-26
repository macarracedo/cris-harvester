from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CRIS_", extra="ignore")

    db_url: str = "sqlite:///data/cris.db"
    rate_limit_rps: float = 1.0
    respect_robots: bool = False
    user_agent: str = "cris-harvester/0.1 (contact: manuel.alonso.carracedo@uvigo.es)"
    request_timeout: float = 20.0
    retry_max_attempts: int = 3
    retry_backoff_base: float = 0.5
    uvigo_publications_list_url: str | None = (
        "https://portalcientifico.uvigo.gal/publicaciones?agrTipoPublicacion=ARTICLE&min=2026&max=2026"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
