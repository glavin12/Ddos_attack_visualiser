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
    radar_refresh_seconds: int = Field(default=300, ge=30)
    radar_timeout_seconds: float = Field(default=15.0, gt=0)
    radar_attacks_limit: int = Field(default=100, ge=1, le=1000)
    radar_locations_limit: int = Field(default=50, ge=1, le=1000)
    radar_date_range: str = "1d"
    radar_history_date_range: str = "7d"
    radar_history_agg_interval: str = "1h"

    # --- Simulation ---
    ws_event_interval_ms: int = Field(default=1200, ge=50)
    ambient_event_interval_ms: int = Field(default=2000, ge=50)
    max_active_events: int = Field(default=30, ge=1)
    event_lifetime_ms: int = Field(default=5000, ge=100)
    ws_stats_interval_ms: int = Field(default=1000, ge=100)

    # --- API ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
