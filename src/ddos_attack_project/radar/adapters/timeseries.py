"""Adapter for the ``/timeseries`` endpoints.

Maps ``serie_0`` timestamp/value arrays into canonical
:class:`~ddos_attack_project.domain.models.TimeSeriesPoint` objects.

Timeseries values use ``MIN0_MAX`` normalization and are NOT divided by 100.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from ddos_attack_project.domain.enums import Layer
from ddos_attack_project.domain.models import RadarObservation, TimeSeriesPoint
from ddos_attack_project.radar.adapters.common import NormalizationError
from ddos_attack_project.radar.external import CloudflareTimeSeriesResult


def adapt_timeseries(
    result: CloudflareTimeSeriesResult,
    *,
    observation: RadarObservation,
) -> list[TimeSeriesPoint]:
    """Convert a timeseries response into canonical points."""
    layer = Layer(observation.layer)
    series = result.serie_0
    if len(series.timestamps) != len(series.values):
        raise NormalizationError(
            "timeseries timestamp/value length mismatch: "
            f"{len(series.timestamps)} vs {len(series.values)}"
        )

    points: list[TimeSeriesPoint] = []
    for timestamp, raw_value in zip(series.timestamps, series.values):
        points.append(
            TimeSeriesPoint(
                observation_id=observation.id,
                layer=layer,
                timestamp=timestamp,
                value=_parse_relative_value(raw_value),
                normalization=observation.normalization,
                unit=observation.unit,
            )
        )
    return points


def _parse_relative_value(raw_value: str) -> float:
    """Parse a ``MIN0_MAX`` value without dividing it by 100."""
    if not isinstance(raw_value, str):
        raise NormalizationError(f"expected a string value, got {raw_value!r}")
    try:
        value = Decimal(raw_value)
    except InvalidOperation as exc:
        raise NormalizationError(f"unparseable timeseries value {raw_value!r}") from exc
    if value < Decimal("0") or value > Decimal("1"):
        raise NormalizationError(
            f"timeseries value {raw_value!r} outside [0, 1]"
        )
    return float(value)
