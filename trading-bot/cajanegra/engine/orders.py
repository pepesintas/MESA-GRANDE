from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum

import pandas as pd


class Side(IntEnum):
    LONG = 1
    SHORT = -1


class OrderType(str, Enum):
    MARKET = "market"  # se ejecuta en la apertura de la barra siguiente
    STOP = "stop"      # entrada por ruptura: se activa si el precio toca `price`
    LIMIT = "limit"    # entrada en retroceso: se ejecuta si el precio cruza `price`


@dataclass
class Order:
    side: Side
    type: OrderType = OrderType.MARKET
    price: float | None = None
    stop_loss: float | None = None     # precio absoluto
    take_profit: float | None = None   # precio absoluto
    sl_points: float | None = None     # alternativa: distancia desde el precio de ejecución
    tp_points: float | None = None
    contracts: int = 1
    expires_min: int | None = None     # minuto del día (hora mercado) a partir del cual se cancela
    tag: str = ""

    def __post_init__(self):
        self.side = Side(self.side)
        self.type = OrderType(self.type)
        if self.type is not OrderType.MARKET and self.price is None:
            raise ValueError(f"Una orden {self.type.value} necesita `price`")


@dataclass
class Position:
    side: Side
    contracts: int
    entry_price: float
    entry_index: int
    entry_time: pd.Timestamp
    entry_at_open: bool
    stop_loss: float | None
    take_profit: float | None
    initial_stop: float | None
    tag: str = ""
    mae_points: float = 0.0
    mfe_points: float = 0.0
    extra: dict = field(default_factory=dict)
