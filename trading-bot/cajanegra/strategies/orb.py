"""Ruptura del rango de apertura (Opening Range Breakout).

Referencia pública: Zarattini & Aziz (2023), "Can Day Trading Really Be Profitable?"
(ORB de 5 minutos en QQQ). Aquí sirve como estrategia base con la que comparar.
"""

from __future__ import annotations

import math

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk


class OpeningRangeBreakout(Strategy):
    name = "orb"
    description = "Ruptura del rango de los primeros N minutos de la sesión"
    defaults = {
        "minutos_rango": 15,
        "entrada": "stop",              # stop: órdenes stop en los extremos | cierre: vela cerrada fuera
        "direccion": "ambas",           # ambas | largos | cortos
        "stop": "rango",                # rango: extremo opuesto | medio: mitad del rango
        "objetivo_r": 2.0,              # 0 = sin objetivo (sale por hora)
        "hora_limite_entrada": "11:00",
        "hora_salida": "15:50",
        "contratos": 1,
        "riesgo_usd": 0.0,              # >0: dimensiona para arriesgar este importe por operación
        "max_contratos": 10,
        "max_operaciones": 1,
        "rango_min_ticks": 8,
        "rango_max_atr": 0.0,           # >0: descarta días con rango > X veces el rango diario medio
    }

    def on_day_start(self, ctx):
        self.hi = self.lo = None
        self.valid = False
        self.done = False
        rngs = ctx.daily["range"].tail(14)
        self.atr = float(rngs.mean()) if len(rngs) >= 14 else math.nan
        self.or_end = ctx.session_open_min + int(self.p["minutos_rango"])
        self.limit_min = ctx.to_min(self.p["hora_limite_entrada"])
        self.exit_min = ctx.to_min(self.p["hora_salida"])

    def _levels(self, ctx, side: int, entry_ref: float):
        tick = ctx.instrument.tick_size
        if self.p["stop"] == "medio":
            stop = ctx.instrument.round_to_tick((self.hi + self.lo) / 2)
        else:
            stop = self.lo - tick if side > 0 else self.hi + tick
        risk = (entry_ref - stop) * side
        if risk <= 0:
            return None
        r = float(self.p["objetivo_r"])
        target = entry_ref + side * r * risk if r > 0 else None
        n = size_for_risk(ctx.instrument, risk, self.p["contratos"], self.p["riesgo_usd"], self.p["max_contratos"])
        return (stop, target, n) if n > 0 else None

    def _submit(self, ctx, side: int, otype: OrderType, entry_ref: float):
        if not direction_allowed(self.p["direccion"], side):
            return
        lv = self._levels(ctx, side, entry_ref)
        if lv is None:
            return
        stop, target, n = lv
        price = entry_ref if otype is OrderType.STOP else None
        ctx.submit(Order(Side(side), otype, price=price, stop_loss=stop, take_profit=target,
                         contracts=n, expires_min=self.limit_min, tag="orb"))

    def _arm(self, ctx):
        tick = ctx.instrument.tick_size
        self._submit(ctx, 1, OrderType.STOP, self.hi + tick)
        self._submit(ctx, -1, OrderType.STOP, self.lo - tick)

    def on_bar(self, ctx):
        m = ctx.minute
        if self.hi is None:
            if m >= self.or_end - 1:  # esta barra cierra el rango
                sel = ctx.minutes < self.or_end
                self.hi = float(ctx.highs[sel].max())
                self.lo = float(ctx.lows[sel].min())
                rng = self.hi - self.lo
                ok = rng >= self.p["rango_min_ticks"] * ctx.instrument.tick_size
                if self.p["rango_max_atr"] > 0 and not math.isnan(self.atr):
                    ok = ok and rng <= self.p["rango_max_atr"] * self.atr
                self.valid = ok
                if ok and self.p["entrada"] == "stop" and m < self.limit_min:
                    self._arm(ctx)
            return
        if not self.valid:
            return
        if ctx.position is not None:
            if m >= self.exit_min:
                ctx.exit("hora_salida")
            return
        if m >= self.limit_min - 1 or ctx.trades_today >= self.p["max_operaciones"] or ctx.working_orders:
            return
        c = ctx.c
        if self.p["entrada"] == "cierre":
            if c > self.hi:
                self._submit(ctx, 1, OrderType.MARKET, c)
            elif c < self.lo:
                self._submit(ctx, -1, OrderType.MARKET, c)
        elif self.lo <= c <= self.hi:  # rearmar tras una salida solo si el precio vuelve al rango
            self._arm(ctx)
