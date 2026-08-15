"""Adapter for the ``/summary`` endpoints.

Maps ``summary_0`` maps (protocol / vector / HTTP method -> share) into
canonical :class:`~ddos_attack_project.domain.models.AttackCharacteristic`
objects.
"""

from __future__ import annotations

from ddos_attack_project.domain.enums import (
    CharacteristicCategory,
    Layer,
)
from ddos_attack_project.domain.models import (
    AttackCharacteristic,
    RadarObservation,
)
from ddos_attack_project.radar.adapters.common import percentage_to_share
from ddos_attack_project.radar.external import CloudflareSummaryResult


def adapt_characteristics(
    result: CloudflareSummaryResult,
    *,
    observation: RadarObservation,
    category: CharacteristicCategory,
) -> list[AttackCharacteristic]:
    """Convert a summary response into canonical characteristic shares."""
    layer = Layer(observation.layer)
    characteristics: list[AttackCharacteristic] = []
    for value, raw_share in result.summary_0.items():
        characteristics.append(
            AttackCharacteristic(
                observation_id=observation.id,
                layer=layer,
                category=category,
                value=value,
                share=percentage_to_share(raw_share),
                unit=observation.unit,
            )
        )
    return characteristics
