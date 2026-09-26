"""Primer FVG (Fair Value Gap) a favor de la tendencia tras la apertura.

Hipótesis de partida para la estrategia de @aleixandreu ("operar en mercado alcista en el
primer FVG"), basada en la definición estándar ICT del "First Presented FVG". Todos los
detalles son parámetros: cuando tengamos sus reglas exactas se ajustan aquí.

FVG alcista (3 velas): mínimo de la vela 3 > máximo de la vela 1. La zona del hueco es
[máximo vela 1, mínimo vela 3]. La vela 2 es el desplazamiento.
"""

from __future__ import annotations

import math

import numpy as np

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk


class FirstFVG(Strategy):
    name = "fvg"
    description = "Primer Fair Value Gap tras la apertura, a favor del sesgo del mercado"
    defaults = {
        "direccion": "largos",           # largos (mercado alcista) | cortos | ambas
        "filtro_tendencia": "media_diaria",  # ninguno | media_diaria | cierre_anterior | apertura (combinables con +)
        "media_dias": 20,
        "timeframe_min": 1,              # velas de 1, 2, 3, 5... minutos para detectar el FVG
        "hora_inicio": "09:30",          # el patrón debe empezar a partir de esta hora
        "solo_primero": True,            # True: solo el primer FVG del día (válido o no)
        "fvg_min_ticks": 4,              # tamaño mínimo del hueco
        "entrada": "borde",              # borde: límite en el borde del hueco | medio: 50% del hueco | inmediata
        "stop": "vela1",                 # vela1: bajo el mínimo de la vela 1 | fvg: bajo el hueco
        "stop_margen_ticks": 2,
        "objetivo_r": 2.0,
        "invalidar_si_cierra_fuera": True,  # cancelar si una vela cierra al otro lado del hueco
        "hora_limite_entrada": "11:00",
        "hora_salida": "15:50",
        "contratos": 1,
        "riesgo_usd": 0.0,
        "max_contratos": 10,
    }

    def on_day_start(self, ctx):
        self.fvg = None          # (lado, fondo, techo, stop_ref)
        self.seen_first = False
        self.done = False
        self.bias = self._daily_bias(ctx)
        self.start_min = ctx.to_min(self.p["hora_inicio"])
        self.limit_min = ctx.to_min(self.p["hora_limite_entrada"])
        self.exit_min = ctx.to_min(self.p["hora_salida"])
        self.tf = int(self.p["timeframe_min"])
        self.candles: list[tuple[float, float, float, float]] = []

    def _filters(self) -> list[str]:
        return [f.strip() for f in str(self.p["filtro_tendencia"]).split("+") if f.strip()]

    def _daily_bias(self, ctx) -> int:
        """+1 alcista, -1 bajista, 0 indefinido. Solo usa sesiones anteriores."""
        if "media_diaria" not in self._filters():
            return 0
        closes = ctx.daily["close"]
        n = int(self.p["media_dias"])
        if len(closes) < n:
            return 0
        return 1 if closes.iloc[-1] > closes.iloc[-n:].mean() else -1

    def _side_allowed(self, ctx, side: int) -> bool:
        if not direction_allowed(self.p["direccion"], side):
            return False
        for f in self._filters():
            if f == "media_diaria" and self.bias != side:
                return False
            if f == "cierre_anterior":
                if len(ctx.daily) == 0 or (ctx.c - ctx.daily["close"].iloc[-1]) * side <= 0:
                    return False
            if f == "apertura" and (ctx.c - ctx.opens[0]) * side <= 0:
                return False
        return True

    def _new_candle(self, ctx) -> bool:
        """Cierra una vela de `timeframe_min` minutos si esta barra completa el bloque."""
        m = ctx.minute
        if m < self.start_min or (m - self.start_min + 1) % self.tf != 0:
            return False
        block_start = m - self.tf + 1
        sel = ctx.minutes >= block_start
        o = ctx.opens[sel]
        if len(o) == 0:
            return False
        self.candles.append((float(o[0]), float(ctx.highs[sel].max()), float(ctx.lows[sel].min()), float(ctx.closes[sel][-1])))
        return True

    def _detect(self, ctx):
        if len(self.candles) < 3:
            return None
        (o1, h1, l1, c1), (o2, h2, l2, c2), (o3, h3, l3, c3) = self.candles[-3:]
        min_gap = self.p["fvg_min_ticks"] * ctx.instrument.tick_size
        if l3 - h1 >= min_gap and c2 > o2:
            return (1, h1, l3, l1)       # alcista: zona [h1, l3], stop bajo la vela 1
        if l1 - h3 >= min_gap and c2 < o2:
            return (-1, h3, l1, h1)      # bajista: zona [h3, l1], stop sobre la vela 1
        return None

    def _order(self, ctx, side, bottom, top, stop_ref):
        inst = ctx.instrument
        tick = inst.tick_size
        margin = self.p["stop_margen_ticks"] * tick
        if self.p["stop"] == "fvg":
            stop = bottom - margin if side > 0 else top + margin
        else:
            stop = stop_ref - margin if side > 0 else stop_ref + margin
        mode = self.p["entrada"]
        if mode == "inmediata":
            entry, otype = ctx.c, OrderType.MARKET
        elif mode == "medio":
            entry, otype = inst.round_to_tick((bottom + top) / 2), OrderType.LIMIT
        else:
            entry, otype = (top if side > 0 else bottom), OrderType.LIMIT
        risk = (entry - stop) * side
        if risk <= 0:
            return None
        r = float(self.p["objetivo_r"])
        target = inst.round_to_tick(entry + side * r * risk) if r > 0 else None
        n = size_for_risk(inst, risk, self.p["contratos"], self.p["riesgo_usd"], self.p["max_contratos"])
        if n <= 0:
            return None
        return Order(Side(side), otype, price=None if otype is OrderType.MARKET else entry,
                     stop_loss=inst.round_to_tick(stop), take_profit=target, contracts=n,
                     expires_min=self.limit_min, tag="fvg")

    def on_bar(self, ctx):
        m = ctx.minute
        pos = ctx.position
        if pos is not None:
            if m >= self.exit_min:
                ctx.exit("hora_salida")
            return
        if self.done or ctx.trades_today > 0:
            self.done = True
            ctx.cancel_orders()
            return
        # orden pendiente: ¿el hueco se ha invalidado?
        if self.fvg is not None and ctx.working_orders:
            side, bottom, top, _ = self.fvg
            if self.p["invalidar_si_cierra_fuera"] and ((side > 0 and ctx.c < bottom) or (side < 0 and ctx.c > top)):
                ctx.cancel_orders()
                self.fvg = None
                if self.p["solo_primero"]:
                    self.done = True
            return
        if m >= self.limit_min - 1 or not self._new_candle(ctx):
            return
        found = self._detect(ctx)
        if found is None:
            return
        side, bottom, top, stop_ref = found
        if self.p["solo_primero"] and self.seen_first:
            return
        first = not self.seen_first
        self.seen_first = True
        if not self._side_allowed(ctx, side):
            if self.p["solo_primero"] and first:
                self.done = True  # el primer FVG va contra el sesgo: hoy no se opera
            return
        order = self._order(ctx, side, bottom, top, stop_ref)
        if order is None:
            if self.p["solo_primero"]:
                self.done = True
            return
        self.fvg = found
        ctx.submit(order)
