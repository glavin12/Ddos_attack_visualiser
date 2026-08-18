"""SQLAlchemy 2.x ORM models for the normalized database schema.

The database stores durable normalized Radar observations. It does NOT store
every synthetic globe particle.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


class RadarObservation(Base):
    __tablename__ = "radar_observations"
    __table_args__ = (
        Index("idx_radar_observations_refresh_id", "refresh_id"),
        Index(
            "idx_radar_observations_layer_collected_at",
            "layer",
            "collected_at",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    refresh_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    endpoint_key: Mapped[str] = mapped_column(String(64))
    layer: Mapped[str] = mapped_column(String(2))
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    window_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cloudflare_last_updated: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    normalization: Mapped[str] = mapped_column(String(16))
    unit: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now()
    )


class AttackPair(Base):
    __tablename__ = "attack_pairs"
    __table_args__ = (
        Index("idx_attack_pairs_observation_id", "observation_id"),
        Index(
            "idx_attack_pairs_observation_layer_share",
            "observation_id",
            "layer",
            "share",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    observation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("radar_observations.id")
    )
    layer: Mapped[str] = mapped_column(String(2))
    source_country_code: Mapped[str] = mapped_column(String(2))
    source_country_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_country_code: Mapped[str] = mapped_column(String(2))
    target_country_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    share: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    rank: Mapped[int | None] = mapped_column(nullable=True)
    unit: Mapped[str] = mapped_column(String(16))


class CountryDistribution(Base):
    __tablename__ = "country_distributions"
    __table_args__ = (
        Index("idx_country_distributions_observation_id", "observation_id"),
        Index(
            "idx_country_distributions_layer_role_share",
            "layer",
            "role",
            "share",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    observation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("radar_observations.id")
    )
    layer: Mapped[str] = mapped_column(String(2))
    role: Mapped[str] = mapped_column(String(8))
    country_code: Mapped[str] = mapped_column(String(2))
    country_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    share: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    rank: Mapped[int | None] = mapped_column(nullable=True)
    unit: Mapped[str] = mapped_column(String(16))


class AttackCharacteristic(Base):
    __tablename__ = "attack_characteristics"
    __table_args__ = (
        Index("idx_attack_characteristics_observation_id", "observation_id"),
        Index(
            "idx_attack_characteristics_layer_category_share",
            "layer",
            "category",
            "share",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    observation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("radar_observations.id")
    )
    layer: Mapped[str] = mapped_column(String(2))
    category: Mapped[str] = mapped_column(String(16))
    value: Mapped[str] = mapped_column(Text)
    share: Mapped[Decimal] = mapped_column(Numeric(10, 8))
    unit: Mapped[str] = mapped_column(String(16))


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    __table_args__ = (
        UniqueConstraint(
            "source_feed",
            "indicator",
            name="uq_threat_indicators_feed_indicator",
        ),
        Index("idx_threat_indicators_last_seen", "last_seen"),
        Index("idx_threat_indicators_created_at", "created_at"),
        Index(
            "idx_threat_indicators_source_feed_last_seen",
            "source_feed",
            "last_seen",
        ),
        Index("idx_threat_indicators_country_code", "country_code"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    source_feed: Mapped[str] = mapped_column(String(16))
    indicator: Mapped[str] = mapped_column(Text)
    indicator_type: Mapped[str] = mapped_column(String(8))
    resolved_ip: Mapped[str] = mapped_column(String(64))
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    country_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    threat_family: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    greynoise_classification: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    greynoise_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now()
    )


class TimeSeriesPoint(Base):
    __tablename__ = "timeseries_points"
    __table_args__ = (
        Index("idx_timeseries_points_observation_id", "observation_id"),
        Index(
            "idx_timeseries_points_observation_timestamp",
            "observation_id",
            "timestamp",
        ),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    observation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("radar_observations.id")
    )
    layer: Mapped[str] = mapped_column(String(2))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    value: Mapped[float] = mapped_column()
    normalization: Mapped[str] = mapped_column(String(16))
    unit: Mapped[str] = mapped_column(String(16))
