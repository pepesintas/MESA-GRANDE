"""Momentum de la última media hora.

Gao, Han, Li y Zhou (2018, Journal of Financial Economics): la rentabilidad de la primera media
hora (desde el cierre de ayer) predice la de la última media hora (SPY 1993–2013).
Baltussen, Da, Lammers y Martens (2021, JFE): en más de 60 futuros (1974–2020) el resto del día
predice los últimos 30 minutos; lo atribuyen a la cobertura de gamma de creadores de mercado.

Reglas: a las 15:30 (hora de Nueva York) se opera en la dirección de la señal y se cierra al final
de la sesión.
"""

from __future__ import annotations

from ..engine.orders import Order, OrderType, Side
from .base import Strategy
from .common import direction_allowed, size_for_risk


class LastHalfHourMomentum(Strategy):
    name = "ultima_media_hora"
    description = "Opera los últimos 30 minutos en la dirección del resto del día"
    defaults = {
        "senal": "resto_del_dia",     # resto_del_dia (Baltussen) | primera_media_hora (Gao)
        "hora_entrada": "15:30",
        "umbral_pct": 0.0,            # solo si |señal| supera este % (p. ej. 0.25)
        "direccion": "ambas",
        "stop_puntos": 0.0,           # >0: stop de protección (recomendable en firmas)
        "contratos": 1,
        "riesgo_usd": 0.0,            # con stop_puntos > 0: contratos = riesgo / stop
        "max_contratos": 10,
    }

    def on_day_start(self, ctx):
        self._prev_close = float(ctx.daily["close"].iloc[-1]) if len(ctx.daily) else None
        self._first_half = None
        self._entry = ctx.to_min(self.p["hora_entrada"])
        self._done = False

    def on_bar(self, ctx):
        if self._prev_close is None or self._done:
            return
        end_min = ctx.minute + 1
        if self._first_half is None and end_min >= ctx.session_open_min + 30:
            self._first_half = ctx.c / self._prev_close - 1.0
        if end_min != self._entry:
            return
        self._done = True
        if self.p["senal"] == "primera_media_hora":
            signal = self._first_half
        else:
            signal = ctx.c / self._prev_close - 1.0
        if signal is None or abs(signal) * 100 <= self.p["umbral_pct"] or signal == 0:
            return
        side = 1 if signal > 0 else -1
        if not direction_allowed(self.p["direccion"], side):
            return
        stop_pts = float(self.p["stop_puntos"])
        n = size_for_risk(ctx.instrument, stop_pts, self.p["contratos"],
                          self.p["riesgo_usd"] if stop_pts > 0 else 0.0, self.p["max_contratos"])
        if n <= 0:
            return
        ctx.submit(Order(Side(side), OrderType.MARKET, sl_points=stop_pts or None, contracts=n, tag="ultima_media_hora"))
