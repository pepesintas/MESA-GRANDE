"""Primer FVG (Fair Value Gap) a favor de la tendencia tras la apertura.

Hipótesis de partida para la estrategia de @aleixandreu ("operar en mercado alcista en el
primer FVG"), basada en la definición estándar ICT del "First Presented FVG". Todos los
detalles son parámetros: cuando tengamos sus reglas exactas se ajustan aquí.

FVG alcista (3 velas): mínimo de la vela 3 > máximo de la vela 1. La zona del hueco es
[máximo vela 1, mínimo vela 3]. La vela 2 es el desplazamiento.

Filtro `flujo_fvg` (paso 1 del sistema de Aleix: la "draw on liquidity" se deduce de qué FVG
se respetan y cuáles no): ver `FvgOrderFlow`.
"""

from __future__ import annotations

from collections import deque

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk


def detect_fvg(c1, c2, c3, min_gap: float):
    """(lado, fondo, techo, extremo de la vela 1) si las 3 velas forman un FVG; si no, None."""
    (o1, h1, l1, _), (o2, _, _, cl2), (_, h3, l3, _) = c1, c2, c3
    if l3 - h1 >= min_gap and cl2 > o2:
        return (1, h1, l3, l1)       # alcista: zona [h1, l3], stop bajo la vela 1
    if l1 - h3 >= min_gap and cl2 < o2:
        return (-1, h3, l1, h1)      # bajista: zona [h3, l1], stop sobre la vela 1
    return None


class CandleBuilder:
    """Velas de `tf` minutos alineadas con `start_min`, a partir de barras de 1 minuto."""

    def __init__(self, tf: int, start_min: int):
        self.tf, self.start = int(tf), int(start_min)

    def update(self, ctx):
        m = ctx.minute
        if m < self.start or (m - self.start + 1) % self.tf != 0:
            return None
        sel = ctx.minutes >= m - self.tf + 1
        o = ctx.opens[sel]
        if len(o) == 0:
            return None
        return (float(o[0]), float(ctx.highs[sel].max()), float(ctx.lows[sel].min()), float(ctx.closes[sel][-1]))


class FvgOrderFlow:
    """Sesgo según qué FVG se respetan y cuáles no.

    - FVG alcista respetado → +1. Con `mode="impulso"` (Aleix: "mitiga el FVG y da un impulso
      hacia un nuevo punto estructural"): el precio vuelve al hueco y después una vela cierra por
      encima de él. Con `mode="toque"`: basta con volver al hueco sin cerrar por debajo.
    - FVG alcista no respetado: una vela cierra por debajo del hueco → −1.
    - FVG bajista: simétrico (respetado → −1; no respetado, cierre por encima → +1).
    Sesgo = dirección de los últimos `events_needed` eventos si coinciden; si no, 0.
    Los FVG sin resolver caducan tras `max_age_days` sesiones.
    """

    def __init__(self, min_gap: float, events_needed: int = 1, max_age_days: int = 3, mode: str = "impulso"):
        if mode not in ("impulso", "toque"):
            raise ValueError("mode debe ser 'impulso' o 'toque'")
        self.min_gap = min_gap
        self.need = int(events_needed)
        self.max_age = int(max_age_days)
        self.mode = mode
        self.fvgs: list[list] = []   # [lado, fondo, techo, día, tocado]
        self.events: deque[int] = deque(maxlen=20)
        self.candles: list[tuple] = []
        self.day = 0

    def new_day(self) -> None:
        self.day += 1
        self.candles = []
        self.fvgs = [f for f in self.fvgs if self.day - f[3] <= self.max_age]

    def on_candle(self, o: float, h: float, l: float, c: float) -> None:  # noqa: E741
        keep = []
        for f in self.fvgs:
            side, bottom, top, _, touched = f
            if (side > 0 and c < bottom) or (side < 0 and c > top):
                self.events.append(-side)          # no respetado: lo atraviesa
                continue
            touched = touched or (l <= top if side > 0 else h >= bottom)
            if touched:
                impulse = c > top if side > 0 else c < bottom
                if self.mode == "toque" or impulse:
                    self.events.append(side)        # respetado
                    continue
                f[4] = True
            keep.append(f)
        self.fvgs = keep
        self.candles.append((o, h, l, c))
        if len(self.candles) >= 3:
            found = detect_fvg(*self.candles[-3:], self.min_gap)
            if found is not None:
                self.fvgs.append([found[0], found[1], found[2], self.day, False])

    @property
    def bias(self) -> int:
        if len(self.events) < self.need:
            return 0
        last = list(self.events)[-self.need:]
        return last[0] if all(e == last[0] for e in last) else 0


class FirstFVG(Strategy):
    name = "fvg"
    description = "Primer Fair Value Gap tras la apertura, a favor del sesgo del mercado"
    defaults = {
        "direccion": "largos",           # largos (mercado alcista) | cortos | ambas
        "filtro_tendencia": "media_diaria",  # ninguno | media_diaria | cierre_anterior | apertura | flujo_fvg (combinables con +)
        "media_dias": 20,
        "flujo_timeframe_min": 15,       # flujo_fvg: velas en las que se miden los FVG respetados/no respetados
        "flujo_eventos": 1,              # flujo_fvg: eventos seguidos en la misma dirección para fijar sesgo
        "flujo_dias": 3,                 # flujo_fvg: días que sigue vivo un FVG sin resolver
        "flujo_respeto": "impulso",      # flujo_fvg: impulso (toca y luego se aleja) | toque
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

    def __init__(self, **params):
        super().__init__(**params)
        self._flow: FvgOrderFlow | None = None

    def on_day_start(self, ctx):
        if "flujo_fvg" in self._filters():
            if self._flow is None:
                self._flow = FvgOrderFlow(self.p["fvg_min_ticks"] * ctx.instrument.tick_size,
                                          self.p["flujo_eventos"], self.p["flujo_dias"], self.p["flujo_respeto"])
            self._flow.new_day()
            self._flow_builder = CandleBuilder(self.p["flujo_timeframe_min"], ctx.session_open_min)
        self.fvg = None          # (lado, fondo, techo, stop_ref)
        self.seen_first = False
        self.done = False
        self.bias = self._daily_bias(ctx)
        self.start_min = ctx.to_min(self.p["hora_inicio"])
        self.limit_min = ctx.to_min(self.p["hora_limite_entrada"])
        self.exit_min = ctx.to_min(self.p["hora_salida"])
        self._entry_builder = CandleBuilder(self.p["timeframe_min"], self.start_min)
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
            if f == "flujo_fvg" and (self._flow is None or self._flow.bias != side):
                return False
        return True

    def _new_candle(self, ctx) -> bool:
        """Cierra una vela de `timeframe_min` minutos si esta barra completa el bloque."""
        candle = self._entry_builder.update(ctx)
        if candle is None:
            return False
        self.candles.append(candle)
        return True

    def _detect(self, ctx):
        if len(self.candles) < 3:
            return None
        return detect_fvg(*self.candles[-3:], self.p["fvg_min_ticks"] * ctx.instrument.tick_size)

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
        if self._flow is not None:
            candle = self._flow_builder.update(ctx)
            if candle is not None:
                self._flow.on_candle(*candle)
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
