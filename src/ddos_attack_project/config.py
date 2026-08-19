"""Application configuration loaded from environment variables.

Secrets such as ``CF_API_TOKEN`` and ``SUPABASE_DATABASE_URL`` are never
logged or exposed to the frontend.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # --- Database ---
    database_url: str = Field(
        validation_alias=AliasChoices("DATABASE_URL", "SUPABASE_DATABASE_URL")
    )

    # --- Cloudflare Radar ---
    cf_api_token: str = Field(
        validation_alias=AliasChoices("CF_API_TOKEN", "cloudflare_API_TOKEN")
    )
    radar_base_url: str = "https://api.cloudflare.com/client/v4/radar"
    radar_refresh_seconds: int = Field(default=21_600, ge=30)
    radar_timeout_seconds: float = Field(default=15.0, gt=0)
    radar_attacks_limit: int = Field(default=100, ge=1, le=1000)
    radar_locations_limit: int = Field(default=50, ge=1, le=1000)
    radar_date_range: str = "1d"
    radar_history_date_range: str = "7d"
    radar_history_agg_interval: str = "1h"
    radar_pulse_interval_seconds: float = Field(default=30.0, ge=5.0)
    radar_pulse_max_routes: int = Field(default=30, ge=1, le=100)

    # --- Threat Intelligence ---
    threat_fox_auth: str | None = Field(
        default=None,
        validation_alias=AliasChoices("THREAT_FOX_AUTH", "threat_fox_auth"),
    )
    greynoise_comm_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GREYNOISE_COMM_KEY", "greynoise_comm_key"),
    )
    maxmind_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MAXMIND_KEY", "maxmind_key"),
    )
    maxmind_city_db_path: str = Field(
        default="./data/GeoLite2-City.mmdb"
    )
    threatintel_poll_urlhaus_seconds: int = Field(default=300, ge=60)
    threatintel_poll_feodo_seconds: int = Field(default=1800, ge=60)
    threatintel_poll_threatfox_seconds: int = Field(default=300, ge=60)
    threatintel_prune_after_days: int = Field(default=7, ge=1)
    threatintel_prune_interval_seconds: int = Field(default=3600, ge=60)
    threatintel_greynoise_enrichment_top_n: int = Field(default=20, ge=0)
    threatintel_max_indicators_per_feed: int = Field(default=200, ge=1)
    threatintel_http_timeout_seconds: float = Field(default=20.0, gt=0)

    # --- API ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
