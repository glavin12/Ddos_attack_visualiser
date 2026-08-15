"""Adapter for the ``/top/attacks`` endpoints.

Maps ``top_0`` records (source -> target country pairs) into canonical
:class:`~ddos_attack_project.domain.models.AttackPair` objects.
"""

from __future__ import annotations

from ddos_attack_project.domain.enums import Layer
from ddos_attack_project.domain.models import AttackPair, RadarObservation
from ddos_attack_project.radar.adapters.common import (
    percentage_to_share,
    validate_country_code,
)
from ddos_attack_project.radar.external import CloudflareTopAttacksResult


def adapt_attack_pairs(
    result: CloudflareTopAttacksResult,
    *,
    observation: RadarObservation,
) -> list[AttackPair]:
    """Convert a top-attacks response into canonical attack pairs."""
    layer = Layer(observation.layer)
    pairs: list[AttackPair] = []
    for record in result.top_0:
        pairs.append(
            AttackPair(
                observation_id=observation.id,
                layer=layer,
                source_country_code=validate_country_code(
                    record.origin_country_alpha2
                ),
                source_country_name=record.origin_country_name or None,
                target_country_code=validate_country_code(
                    record.target_country_alpha2
                ),
                target_country_name=record.target_country_name or None,
                share=percentage_to_share(record.value),
                rank=record.rank,
                unit=observation.unit,
            )
        )
    return pairs
