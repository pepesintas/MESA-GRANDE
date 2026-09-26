"""Utilidades compartidas por las estrategias."""

from __future__ import annotations

import math

from ..instruments import Instrument


def size_for_risk(inst: Instrument, risk_points: float, contratos: int, riesgo_usd: float, max_contratos: int) -> int:
    """Contratos fijos, o los que caben en `riesgo_usd` para esa distancia de stop."""
    if riesgo_usd and riesgo_usd > 0:
        per_contract = risk_points * inst.point_value + 2 * inst.commission_per_side
        n = math.floor(riesgo_usd / per_contract) if per_contract > 0 else 0
    else:
        n = int(contratos)
    return max(0, min(n, int(max_contratos)))


def direction_allowed(direccion: str, side: int) -> bool:
    return direccion == "ambas" or (direccion == "largos" and side > 0) or (direccion == "cortos" and side < 0)
