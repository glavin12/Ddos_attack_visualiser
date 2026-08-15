"""Adapter for the ``/top/locations`` origin and target endpoints.

Maps ``top_0`` records into canonical
:class:`~ddos_attack_project.domain.models.DistributionEntry` objects.

Origin and target records must remain separate. They are never combined to
reconstruct source->target pairs.
"""

from __future__ import annotations

from ddos_attack_project.domain.enums import DistributionRole, Layer
from ddos_attack_project.domain.models import (
    DistributionEntry,
    RadarObservation,
)
from ddos_attack_project.radar.adapters.common import (
    percentage_to_share,
    validate_country_code,
)
from ddos_attack_project.radar.external import (
    CloudflareTopLocationRecord,
    CloudflareTopLocationsResult,
)


def adapt_distributions(
    result: CloudflareTopLocationsResult,
    *,
    observation: RadarObservation,
    role: DistributionRole,
) -> list[DistributionEntry]:
    """Convert a locations response into canonical distribution entries."""
    layer = Layer(observation.layer)
    entries: list[DistributionEntry] = []
    for record in result.top_0:
        code, name = _country_from_record(record, role)
        entries.append(
            DistributionEntry(
                observation_id=observation.id,
                layer=layer,
                role=role,
                country_code=validate_country_code(code),
                country_name=name,
                share=percentage_to_share(record.value),
                rank=record.rank,
                unit=observation.unit,
            )
        )
    return entries


def _country_from_record(
    record: CloudflareTopLocationRecord,
    role: DistributionRole,
) -> tuple[str, str | None]:
    if role == DistributionRole.ORIGIN:
        if record.origin_country_alpha2 is None:
            raise ValueError("origin record missing origin country")
        return record.origin_country_alpha2, record.origin_country_name or None
    if record.target_country_alpha2 is None:
        raise ValueError("target record missing target country")
    return record.target_country_alpha2, record.target_country_name or None
