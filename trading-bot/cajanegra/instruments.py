"""Especificaciones de contratos de futuros."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Instrument:
    symbol: str
    description: str
    tick_size: float
    tick_value: float  # USD por tick y contrato
    commission_per_side: float  # USD por contrato y lado (aprox., incluye tasas)

    @property
    def point_value(self) -> float:
        return self.tick_value / self.tick_size

    def round_to_tick(self, price: float, mode: str = "nearest") -> float:
        ticks = price / self.tick_size
        if mode == "up":
            ticks = math.ceil(ticks - 1e-9)
        elif mode == "down":
            ticks = math.floor(ticks + 1e-9)
        else:
            ticks = round(ticks)
        return ticks * self.tick_size

    def with_costs(self, commission_per_side: float | None = None) -> "Instrument":
        if commission_per_side is None:
            return self
        return replace(self, commission_per_side=commission_per_side)


# Comisiones aproximadas y algo conservadoras para cuentas de fondeo (Rithmic/Tradovate).
# Verifica las de tu firma y ajústalas con --comision.
INSTRUMENTS: dict[str, Instrument] = {
    "NQ": Instrument("NQ", "E-mini Nasdaq-100 (CME)", 0.25, 5.00, 2.50),
    "MNQ": Instrument("MNQ", "Micro E-mini Nasdaq-100 (CME)", 0.25, 0.50, 0.75),
    "ES": Instrument("ES", "E-mini S&P 500 (CME)", 0.25, 12.50, 2.50),
    "MES": Instrument("MES", "Micro E-mini S&P 500 (CME)", 0.25, 1.25, 0.75),
    "YM": Instrument("YM", "E-mini Dow (CBOT)", 1.0, 5.00, 2.50),
    "MYM": Instrument("MYM", "Micro E-mini Dow (CBOT)", 1.0, 0.50, 0.75),
    "RTY": Instrument("RTY", "E-mini Russell 2000 (CME)", 0.10, 5.00, 2.50),
    "M2K": Instrument("M2K", "Micro E-mini Russell 2000 (CME)", 0.10, 0.50, 0.75),
}


def get_instrument(symbol: str) -> Instrument:
    try:
        return INSTRUMENTS[symbol.upper()]
    except KeyError:
        raise ValueError(
            f"Instrumento desconocido: {symbol}. Disponibles: {', '.join(INSTRUMENTS)}"
        ) from None
