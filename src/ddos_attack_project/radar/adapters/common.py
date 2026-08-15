"""Shared helpers for the Cloudflare adapters.

These functions are the normalization boundary: they convert Cloudflare's
string percentage values into canonical 0..1 shares and extract observation
metadata from the response envelope.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

from ddos_attack_project.domain.enums import Normalization, Unit
from ddos_attack_project.domain.models import RadarObservation
from ddos_attack_project.radar.external import CloudflareMeta


class NormalizationError(ValueError):
    """Raised when a Cloudflare value cannot be normalized honestly."""


def percentage_to_share(raw_value: str) -> Decimal:
    """Convert a Cloudflare percentage string into a 0..1 share.

    Cloudflare returns percentage values as strings on a 0..100 scale:

        "6.844203" -> Decimal("0.06844203")

    Timeseries ``MIN0_MAX`` values must NOT go through this function.
    """
    if not isinstance(raw_value, str):
        raise NormalizationError(f"expected a string percentage, got {raw_value!r}")
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise NormalizationError(f"unparseable percentage value {raw_value!r}") from exc

    share = value / Decimal("100")
    if share < Decimal("0") or share > Decimal("1"):
        raise NormalizationError(
            f"percentage {raw_value!r} maps to share {share} outside [0, 1]"
        )
    return share


def build_observation(
    *,
    refresh_id: str,
    endpoint_key: str,
    layer: str,
    collected_at: datetime,
    meta: CloudflareMeta | None,
    default_normalization: Normalization,
    default_unit: Unit,
) -> RadarObservation:
    """Build a :class:`RadarObservation` from a response envelope.

    Metadata fields that Cloudflare does not provide remain ``None`` rather
    than being invented. ``unit`` and ``normalization`` fall back to the
    expected endpoint values only when the response omits them.
    """
    window_start: datetime | None = None
    window_end: datetime | None = None
    if meta and meta.date_range:
        window_start = meta.date_range[0].start_time
        window_end = meta.date_range[0].end_time

    last_updated = meta.last_updated if meta else None

    unit = default_unit
    normalization = default_normalization
    if meta:
        if meta.units and meta.units[0].value:
            try:
                unit = Unit(meta.units[0].value)
            except ValueError:
                raise NormalizationError(
                    f"unknown unit {meta.units[0].value!r} from Cloudflare"
                )
        if meta.normalization:
            try:
                normalization = Normalization(meta.normalization)
            except ValueError:
                raise NormalizationError(
                    f"unknown normalization {meta.normalization!r} from Cloudflare"
                )

    return RadarObservation(
        refresh_id=refresh_id,
        endpoint_key=endpoint_key,
        layer=layer,
        collected_at=collected_at,
        window_start=window_start,
        window_end=window_end,
        cloudflare_last_updated=last_updated,
        normalization=normalization,
        unit=unit,
    )


def validate_country_code(code: str) -> str:
    """Validate a Cloudflare country code using the canonical domain rules."""
    if (
        not isinstance(code, str)
        or len(code) != 2
        or not code.isalnum()
        or code.upper() != code
    ):
        raise NormalizationError(f"invalid country code {code!r}")
    return code


__all__ = [
    "NormalizationError",
    "build_observation",
    "percentage_to_share",
    "validate_country_code",
]
