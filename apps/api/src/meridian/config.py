from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(alias="DATABASE_URL")
    database_url_sync: str = Field(alias="DATABASE_URL_SYNC")
    redis_url: str = Field(alias="REDIS_URL")

    meridian_api_key: str = Field(alias="MERIDIAN_API_KEY", default="dev-meridian-key")

    census_api_key: str | None = Field(alias="CENSUS_API_KEY", default=None)
    bls_api_key: str | None = Field(alias="BLS_API_KEY", default=None)
    fred_api_key: str | None = Field(alias="FRED_API_KEY", default=None)
    attom_api_key: str | None = Field(alias="ATTOM_API_KEY", default=None)
    enable_paid_adapters: bool = Field(alias="ENABLE_PAID_ADAPTERS", default=False)

    cache_ttl_census: int = Field(alias="CACHE_TTL_CENSUS", default=2_592_000)
    cache_ttl_zillow: int = Field(alias="CACHE_TTL_ZILLOW", default=604_800)
    cache_ttl_realtor: int = Field(alias="CACHE_TTL_REALTOR", default=604_800)
    cache_ttl_permits: int = Field(alias="CACHE_TTL_PERMITS", default=604_800)
    cache_ttl_bls: int = Field(alias="CACHE_TTL_BLS", default=86_400)
    cache_ttl_fred: int = Field(alias="CACHE_TTL_FRED", default=86_400)

    log_level: str = Field(alias="LOG_LEVEL", default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
