"""Momentum intradía por "zona de ruido" (noise area).

Zarattini, Aziz y Barbon (2024), "Beat the Market: An Effective Intraday Momentum Strategy
for S&P500 ETF (SPY)": SPY 2007–2024, +19,6 % anual neto, Sharpe 1,33. Aplicación a NQ/ES
(Quantitativo): NQ +24,3 % anual, Sharpe 1,67, acierto 38 %, payoff 2,25.

Reglas (versión del paper):
- σ(t): media de los últimos N días de |cierre(t) / apertura del día − 1| al mismo minuto t.
- Límite superior = max(apertura, cierre de ayer) · (1 + σ(t));
  límite inferior = min(apertura, cierre de ayer) · (1 − σ(t)).
- Cada media hora (10:00, 10:30, ... ): por encima del límite superior → largo; por debajo del
  inferior → corto.
- Stop dinámico revisado en esas mismas horas: largo sale si cierra por debajo de
  max(límite superior, VWAP); corto si cierra por encima de min(límite inferior, VWAP).
- Todo se cierra al final de la sesión.

Añadido para firmas de fondeo (`stop_continuo`): stop real en el mercado más allá del stop
dinámico, con un colchón proporcional a σ(t); solo salta en movimientos extremos entre revisiones.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk


class NoiseAreaMomentum(Strategy):
    name = "zona_ruido"
    description = "Momentum intradía: ruptura de la zona de ruido con stop dinámico (VWAP)"
    defaults = {
        "dias_sigma": 14,             # días para medir el movimiento "normal" a cada minuto
        "multiplicador": 1.0,         # ancho de la zona (1.0 = paper)
        "cada_min": 30,               # revisar señales y stops cada N minutos
        "primera_revision": "10:00",
        "hora_limite_entrada": "15:30",
        "direccion": "ambas",
        "stop_continuo": False,       # True: además, stop real de protección (recomendable en firmas)
        "colchon_sigma": 0.5,         # el stop de protección va este múltiplo de σ(t)·precio más allá
        "stop_min_ticks": 20,         # distancia mínima para calcular el tamaño
        "contratos": 1,
        "riesgo_usd": 0.0,            # >0: contratos = riesgo / distancia al stop dinámico
        "max_contratos": 10,
        "max_operaciones": 4,
    }

    def __init__(self, **params):
        super().__init__(**params)
        self._history: deque[np.ndarray] = deque(maxlen=int(self.p["dias_sigma"]))
        self._today: np.ndarray | None = None

    # --- estado diario --------------------------------------------------------
    def on_day_start(self, ctx):
        if self._today is not None:
            self._history.append(self._today)
        self._n = 390
        self._today = np.full(self._n, np.nan)
        self._open = None
        self._pv = 0.0   # suma precio·volumen para el VWAP
        self._vol = 0.0
        self._sum_c = 0.0
        self._cnt = 0
        self._prev_close = float(ctx.daily["close"].iloc[-1]) if len(ctx.daily) else None
        self._first = ctx.to_min(self.p["primera_revision"])
        self._limit = ctx.to_min(self.p["hora_limite_entrada"])

    def _sigma(self, j: int) -> float:
        if len(self._history) < int(self.p["dias_sigma"]):
            return math.nan
        vals = [d[j] for d in self._history if j < len(d) and not math.isnan(d[j])]
        return float(np.mean(vals)) if vals else math.nan

    def _vwap(self) -> float:
        return self._pv / self._vol if self._vol > 0 else self._sum_c / max(self._cnt, 1)

    def bounds(self, j: int):
        """(límite inferior, límite superior, σ) al minuto j de la sesión; None si falta historia."""
        s = self._sigma(j)
        if math.isnan(s) or self._prev_close is None or self._open is None:
            return None
        s *= float(self.p["multiplicador"])
        return min(self._open, self._prev_close) * (1 - s), max(self._open, self._prev_close) * (1 + s), s

    # --- barras -----------------------------------------------------------------
    def on_bar(self, ctx):
        c = ctx.c
        j = ctx.minute - ctx.session_open_min
        if self._open is None:
            self._open = ctx.opens[0]
        if 0 <= j < self._n:
            self._today[j] = abs(c / self._open - 1.0)
        typical = (ctx.h + ctx.l + c) / 3.0
        vol = float(ctx.volumes[-1])
        self._pv += typical * vol
        self._vol += vol
        self._sum_c += typical
        self._cnt += 1

        end_min = ctx.minute + 1  # hora a la que cierra esta barra
        if end_min < self._first or (end_min - self._first) % int(self.p["cada_min"]) != 0:
            return
        b = self.bounds(j)
        if b is None:
            return
        lo, up, sigma = b
        vwap = self._vwap()
        cushion = float(self.p["colchon_sigma"]) * sigma * c
        pos = ctx.position
        if pos is not None:
            trail = max(up, vwap) if pos.side > 0 else min(lo, vwap)
            if (c - trail) * pos.side < 0:
                ctx.exit("stop_dinamico")
            elif self.p["stop_continuo"]:
                protect = trail - pos.side * cushion
                current = pos.stop_loss
                if current is None or (protect - current) * pos.side > 0:
                    ctx.move_stop(protect)
            return
        if end_min > self._limit or ctx.trades_today >= self.p["max_operaciones"]:
            return
        side = 1 if c > up else -1 if c < lo else 0
        if side == 0 or not direction_allowed(self.p["direccion"], side):
            return
        trail = max(up, vwap) if side > 0 else min(lo, vwap)
        inst = ctx.instrument
        dist = abs(c - trail) + (cushion if self.p["stop_continuo"] else 0.0)
        dist = max(dist, self.p["stop_min_ticks"] * inst.tick_size)
        n = size_for_risk(inst, dist, self.p["contratos"], self.p["riesgo_usd"], self.p["max_contratos"])
        if n <= 0:
            return
        stop = inst.round_to_tick(c - side * dist) if self.p["stop_continuo"] else None
        ctx.submit(Order(Side(side), OrderType.MARKET, stop_loss=stop, contracts=n, tag="zona_ruido"))
