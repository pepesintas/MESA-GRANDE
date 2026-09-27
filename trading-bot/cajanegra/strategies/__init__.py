from .base import Strategy
from .fvg import FirstFVG
from .last_half_hour import LastHalfHourMomentum
from .noise_area import NoiseAreaMomentum
from .orb import OpeningRangeBreakout

STRATEGIES: dict[str, type[Strategy]] = {
    OpeningRangeBreakout.name: OpeningRangeBreakout,
    FirstFVG.name: FirstFVG,
    NoiseAreaMomentum.name: NoiseAreaMomentum,
    LastHalfHourMomentum.name: LastHalfHourMomentum,
}


def get_strategy(name: str, **params) -> Strategy:
    try:
        cls = STRATEGIES[name]
    except KeyError:
        raise ValueError(f"Estrategia desconocida: {name}. Disponibles: {', '.join(STRATEGIES)}") from None
    return cls(**params)


__all__ = [
    "Strategy", "STRATEGIES", "get_strategy",
    "FirstFVG", "LastHalfHourMomentum", "NoiseAreaMomentum", "OpeningRangeBreakout",
]
