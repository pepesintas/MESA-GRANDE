"""Sistema de 3 pasos de Aleix Andreu (según la transcripción de su vídeo fijado).

1. DIRECCIÓN (draw on liquidity) en velas de 15 min o 1 h: ¿qué FVG se respetan (el precio los
   mitiga y da un impulso) y cuáles no (los atraviesa)? El objetivo es el siguiente punto
   estructural: los mínimos (o máximos) de esa temporalidad.
2. ZONA DE REACCIÓN: un FVG de esa temporalidad a favor de la dirección al que el precio vuelve.
3. CONFIRMACIÓN en 1 min (él a veces baja a 30 s): un IFVG. Dentro de la zona se forma un FVG en
   contra y el precio lo invierte: entrada "con el stop loss debajo y el take profit en el objetivo".

Supuestos nuestros (la transcripción no los concreta; todos son parámetros):
- Stop "debajo": más allá del extremo del retroceso desde que se tocó la zona (`stop=extremo`) o
  más allá del IFVG (`stop=ifvg`).
- Entrada a mercado en la apertura de la vela siguiente a la inversión.
- Ratio mínimo de 1,5 (el de su challenge) para aceptar la operación (`exigir_dol`, `objetivo_r`).
- Datos solo de la sesión de Nueva York (sin los FVG de Asia/Londres); sin velas de 30 s.
"""

from __future__ import annotations

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk
from .fvg import CandleBuilder, FvgOrderFlow, detect_fvg


class AleixIFVG(Strategy):
    name = "aleix"
    description = "Aleix: dirección por FVG respetados (15m) → zona FVG (15m) → IFVG (1m)"
    defaults = {
        "htf_min": 15,                 # temporalidad de los pasos 1 y 2 (él usa 15 min o 1 h)
        "ltf_min": 1,                  # temporalidad del IFVG (paso 3)
        "fvg_min_ticks_htf": 4,
        "fvg_min_ticks_ltf": 2,
        "flujo_eventos": 1,            # eventos seguidos para fijar la dirección
        "flujo_dias": 3,               # días que sigue vivo un FVG sin resolver
        "respeto": "impulso",          # impulso: lo mitiga y se aleja | toque: basta con tocarlo
        "zona_minutos": 60,            # cuánto dura una zona tras tocarla
        "direccion": "ambas",
        "hora_inicio": "09:30",
        "hora_limite_entrada": "11:30",
        "hora_salida": "15:50",
        "stop": "extremo",             # extremo | ifvg
        "stop_margen_ticks": 2,
        "objetivo": "dol",             # dol: el siguiente punto estructural (su vídeo) | r: fijo en R (su challenge)
        "objetivo_r": 1.5,             # ratio del objetivo fijo, y ratio mínimo exigido hasta la DOL
        "exigir_dol": True,            # solo si el siguiente punto estructural está a ≥ objetivo_r·riesgo
        "max_operaciones": 1,
        "contratos": 1,
        "riesgo_usd": 0.0,
        "max_contratos": 10,
    }

    def __init__(self, **params):
        super().__init__(**params)
        self._flow: FvgOrderFlow | None = None
        self._zones: list[tuple[int, float, float, int]] = []   # FVG de 15 min aún sin tocar
        self._pivots: list[tuple[int, float, int]] = []         # (+1 máximo / −1 mínimo, precio, día)
        self._day = 0

    # --- día --------------------------------------------------------------------
    def on_day_start(self, ctx):
        tick = ctx.instrument.tick_size
        if self._flow is None:
            self._flow = FvgOrderFlow(self.p["fvg_min_ticks_htf"] * tick, self.p["flujo_eventos"],
                                      self.p["flujo_dias"], self.p["respeto"])
        self._flow.new_day()
        self._day += 1
        keep = int(self.p["flujo_dias"])
        self._zones = [z for z in self._zones if self._day - z[3] <= keep]
        self._pivots = [p for p in self._pivots if self._day - p[2] <= keep]
        self._htf = CandleBuilder(self.p["htf_min"], ctx.session_open_min)
        self._ltf = CandleBuilder(self.p["ltf_min"], ctx.session_open_min)
        self._htf_candles: list[tuple] = []
        self._ltf_candles: list[tuple] = []
        self._active = None      # zona activa: dict(side, bottom, top, until, extreme)
        self._counter: list[tuple[float, float]] = []   # FVG de 1 min en contra dentro de la zona
        self._prev_high = float(ctx.daily["high"].iloc[-1]) if len(ctx.daily) else None
        self._prev_low = float(ctx.daily["low"].iloc[-1]) if len(ctx.daily) else None
        self._start = ctx.to_min(self.p["hora_inicio"])
        self._limit = ctx.to_min(self.p["hora_limite_entrada"])
        self._exit = ctx.to_min(self.p["hora_salida"])

    # --- pasos 1 y 2: velas de 15 min ------------------------------------------------
    def _on_htf(self, candle) -> None:
        self._flow.on_candle(*candle)
        _, _, _, c = candle
        # una zona sin tocar se invalida si una vela cierra al otro lado
        self._zones = [z for z in self._zones if not ((z[0] < 0 and c > z[2]) or (z[0] > 0 and c < z[1]))]
        self._htf_candles.append(candle)
        k = self._htf_candles
        if len(k) >= 3:
            found = detect_fvg(*k[-3:], self.p["fvg_min_ticks_htf"] * self._tick)
            if found is not None:
                self._zones.append((found[0], found[1], found[2], self._day))
            (_, h1, l1, _), (_, h2, l2, _), (_, h3, l3, _) = k[-3:]
            if h2 > h1 and h2 > h3:
                self._pivots.append((1, h2, self._day))
            if l2 < l1 and l2 < l3:
                self._pivots.append((-1, l2, self._day))

    def _touch_zones(self, ctx, bias: int) -> None:
        """Una zona se consume al tocarla; se activa si va a favor de la dirección."""
        h, l = ctx.h, ctx.l  # noqa: E741
        remaining = []
        for z in self._zones:
            side, bottom, top, _ = z
            touched = (side < 0 and h >= bottom) or (side > 0 and l <= top)
            if not touched:
                remaining.append(z)
                continue
            if self._active is None and side == bias and direction_allowed(self.p["direccion"], side):
                self._active = {
                    "side": side, "bottom": bottom, "top": top,
                    "until": ctx.minute + int(self.p["zona_minutos"]),
                    "extreme": h if side < 0 else l,
                    "since": len(self._ltf_candles),
                }
                self._counter = []
        self._zones = remaining

    def dol(self, side: int, price: float) -> float | None:
        """Siguiente punto estructural en la dirección `side` desde `price`."""
        if side < 0:
            levels = [p for s, p, _ in self._pivots if s < 0 and p < price]
            if self._prev_low is not None and self._prev_low < price:
                levels.append(self._prev_low)
            return max(levels) if levels else None
        levels = [p for s, p, _ in self._pivots if s > 0 and p > price]
        if self._prev_high is not None and self._prev_high > price:
            levels.append(self._prev_high)
        return min(levels) if levels else None

    # --- barra a barra --------------------------------------------------------------
    def on_bar(self, ctx):
        self._tick = ctx.instrument.tick_size
        candle = self._htf.update(ctx)
        if candle is not None:
            self._on_htf(candle)
        ltf = self._ltf.update(ctx)
        if ltf is not None:
            self._ltf_candles.append(ltf)

        m = ctx.minute
        if ctx.position is not None:
            if m >= self._exit:
                ctx.exit("hora_salida")
            return
        if ctx.trades_today >= self.p["max_operaciones"] or m < self._start or m >= self._limit:
            self._active = None
            return

        if self._active is None:
            self._touch_zones(ctx, self._flow.bias)
            if self._active is None:
                return
        z = self._active
        side = z["side"]
        z["extreme"] = max(z["extreme"], ctx.h) if side < 0 else min(z["extreme"], ctx.l)
        c = ctx.c
        if (side < 0 and c > z["top"]) or (side > 0 and c < z["bottom"]) or m >= z["until"]:
            self._active = None   # la zona no se ha respetado o ha caducado
            return
        if ltf is None:
            return
        # paso 3: ¿se invierte algún FVG de 1 min en contra?
        inverted = None
        for fb, ft in self._counter:
            if (side < 0 and ltf[3] < fb) or (side > 0 and ltf[3] > ft):
                inverted = (fb, ft)
                break
        k = self._ltf_candles
        if len(k) >= 3 and len(k) - 1 >= z["since"]:
            found = detect_fvg(*k[-3:], self.p["fvg_min_ticks_ltf"] * self._tick)
            if found is not None and found[0] == -side:
                self._counter.append((found[1], found[2]))
        if inverted is not None:
            self._enter(ctx, side, inverted)

    def _enter(self, ctx, side: int, ifvg: tuple[float, float]) -> None:
        inst = ctx.instrument
        margin = self.p["stop_margen_ticks"] * inst.tick_size
        entry = ctx.c
        z = self._active
        if self.p["stop"] == "ifvg":
            stop = ifvg[1] + margin if side < 0 else ifvg[0] - margin
        else:
            stop = z["extreme"] + margin if side < 0 else z["extreme"] - margin
        risk = (entry - stop) * side
        self._active = None
        if risk <= 0:
            return
        target_dol = self.dol(side, entry)
        min_dist = float(self.p["objetivo_r"]) * risk
        if self.p["exigir_dol"] and (target_dol is None or abs(target_dol - entry) < min_dist):
            return
        if self.p["objetivo"] == "dol":
            if target_dol is None:
                return
            target = target_dol
        else:
            target = entry + side * min_dist
        n = size_for_risk(inst, risk, self.p["contratos"], self.p["riesgo_usd"], self.p["max_contratos"])
        if n <= 0:
            return
        ctx.submit(Order(Side(side), OrderType.MARKET, stop_loss=inst.round_to_tick(stop),
                         take_profit=inst.round_to_tick(target), contracts=n, tag="aleix"))
