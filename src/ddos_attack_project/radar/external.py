"""Cloudflare Radar external API response models.

These models mirror Cloudflare's raw JSON field names and are the only place
in the application that should care about them. The rest of the system uses
``domain.models``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CloudflareDateRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    start_time: datetime = Field(validation_alias="startTime")
    end_time: datetime = Field(validation_alias="endTime")


class CloudflareConfidenceInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    level: Any | None = None
    annotations: list[Any] = Field(default_factory=list)


class CloudflareUnit(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    name: str | None = Field(default=None, validation_alias="name")
    value: str | None = Field(default=None, validation_alias="value")


class CloudflareMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    date_range: list[CloudflareDateRange] = Field(
        default_factory=list, validation_alias="dateRange"
    )
    confidence_info: CloudflareConfidenceInfo | None = Field(
        default=None, validation_alias="confidenceInfo"
    )
    normalization: str | None = None
    agg_interval: str | None = Field(default=None, validation_alias="aggInterval")
    last_updated: datetime | None = Field(default=None, validation_alias="lastUpdated")
    units: list[CloudflareUnit] = Field(default_factory=list)


class CloudflareTopAttackRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    origin_country_alpha2: str = Field(validation_alias="originCountryAlpha2")
    origin_country_name: str = Field(validation_alias="originCountryName")
    target_country_alpha2: str = Field(validation_alias="targetCountryAlpha2")
    target_country_name: str = Field(validation_alias="targetCountryName")
    value: str
    rank: int | None = None


class CloudflareTopLocationRecord(BaseModel):
    """A country-level origin or target record from a ``locations`` response."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    origin_country_alpha2: str | None = Field(
        default=None, validation_alias="originCountryAlpha2"
    )
    origin_country_name: str | None = Field(
        default=None, validation_alias="originCountryName"
    )
    target_country_alpha2: str | None = Field(
        default=None, validation_alias="targetCountryAlpha2"
    )
    target_country_name: str | None = Field(
        default=None, validation_alias="targetCountryName"
    )
    value: str
    rank: int | None = None


class CloudflareSummaryResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    summary_0: dict[str, str]
    meta: CloudflareMeta | None = None


class CloudflareTimeSeries(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    timestamps: list[datetime]
    values: list[str]


class CloudflareTimeSeriesResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    serie_0: CloudflareTimeSeries
    meta: CloudflareMeta | None = None


class CloudflareEnvelope(BaseModel):
    """Top-level Cloudflare API envelope shared by every endpoint."""

    model_config = ConfigDict(extra="ignore")

    success: bool
    errors: list[Any] = Field(default_factory=list)
    result: dict[str, Any] = Field(default_factory=dict)


class CloudflareTopAttacksResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    top_0: list[CloudflareTopAttackRecord]
    meta: CloudflareMeta | None = None


class CloudflareTopLocationsResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    top_0: list[CloudflareTopLocationRecord]
    meta: CloudflareMeta | None = None
