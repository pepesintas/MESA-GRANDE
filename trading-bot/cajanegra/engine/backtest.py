"""Motor de backtest barra a barra para day trading (una posición a la vez).

Modelo de ejecución (conservador a propósito: mejor sorpresas buenas en real):
- La estrategia decide al CIERRE de la barra i; sus órdenes solo pueden ejecutarse desde i+1.
- Mercado: apertura de la barra siguiente + deslizamiento.
- Stop de entrada: si el precio toca el nivel; si abre más allá, se ejecuta en la apertura. + deslizamiento.
- Límite de entrada: exige que el precio CRUCE el nivel (tocarlo no basta). Sin deslizamiento.
- Si stop y objetivo caben en la misma barra, se asume que saltó el STOP.
- En la barra de una entrada intrabarra (stop/límite) solo se evalúa el stop, nunca el objetivo.
- Al ejecutarse una entrada se cancelan las demás órdenes de entrada (OCO implícito).
- Cierre forzoso al cierre de la última barra de la sesión o de la primera barra >= flat_time.
- El equity intradía (para reglas de drawdown de las firmas) usa los extremos de cada barra;
  dentro de una barra se asume primero el extremo favorable y luego el adverso (peor caso).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..data.loader import SESSIONS, Session, prepare_session
from ..instruments import Instrument
from ..news.calendar import NewsCalendar
from ..risk.guard import DailyRiskGuard
from ..strategies.base import Strategy
from .orders import Order, OrderType, Position, Side

log = logging.getLogger(__name__)


def hhmm_to_min(value: str | int | None) -> int | None:
    if value is None or isinstance(value, int):
        return value
    h, m = str(value).split(":")
    return int(h) * 60 + int(m)


@dataclass
class CostModel:
    slippage_ticks: float = 1.0           # por lado, en órdenes a mercado y stops
    limit_needs_trade_through: bool = True


@dataclass
class _DayState:
    position: Position | None = None
    working: list[Order] = field(default_factory=list)
    pending_exit: str | None = None
    realized: float = 0.0
    day_min: float = 0.0
    day_max: float = 0.0
    run_peak: float = 0.0   # pico de equity intradía hasta ahora
    dd_intra: float = 0.0   # mayor retroceso desde ese pico (para drawdown trailing intradía)
    trades_opened: int = 0
    consecutive_losses: int = 0
    trades: list[dict] = field(default_factory=list)


class Context:
    """Vista de la estrategia sobre el mercado. Solo expone barras hasta la actual."""

    def __init__(self, bt: "Backtester"):
        self._bt = bt
        self.instrument: Instrument = bt.instrument
        self.date: pd.Timestamp | None = None
        self.daily: pd.DataFrame = bt.daily.iloc[:0]  # sesiones ANTERIORES (open/high/low/close/range)
        self.i = 0
        self.i0 = 0
        self._st = _DayState()

    # --- tiempo -------------------------------------------------------------
    @property
    def k(self) -> int:
        """Índice de la barra actual dentro de la sesión (0 = primera barra)."""
        return self.i - self.i0

    @property
    def minute(self) -> int:
        return int(self._bt.minute[self.i])

    @property
    def time(self) -> str:
        m = self.minute
        return f"{m // 60:02d}:{m % 60:02d}"

    @property
    def session_open_min(self) -> int:
        """Minuto del día en que abre la sesión (p. ej. 570 = 09:30)."""
        return self._bt.session.start_min

    @property
    def timestamp(self) -> pd.Timestamp:
        return self._bt.index[self.i]

    # --- barra actual y sesión hasta ahora ---------------------------------
    @property
    def o(self) -> float:
        return float(self._bt.o[self.i])

    @property
    def h(self) -> float:
        return float(self._bt.h[self.i])

    @property
    def l(self) -> float:  # noqa: E743
        return float(self._bt.l[self.i])

    @property
    def c(self) -> float:
        return float(self._bt.c[self.i])

    @property
    def opens(self) -> np.ndarray:
        return self._bt.o[self.i0 : self.i + 1]

    @property
    def highs(self) -> np.ndarray:
        return self._bt.h[self.i0 : self.i + 1]

    @property
    def lows(self) -> np.ndarray:
        return self._bt.l[self.i0 : self.i + 1]

    @property
    def closes(self) -> np.ndarray:
        return self._bt.c[self.i0 : self.i + 1]

    @property
    def volumes(self) -> np.ndarray:
        return self._bt.v[self.i0 : self.i + 1]

    @property
    def minutes(self) -> np.ndarray:
        return self._bt.minute[self.i0 : self.i + 1]

    @property
    def in_news_blackout(self) -> bool:
        return bool(self._bt.blackout[self.i])

    # --- cuenta ---------------------------------------------------------------
    @property
    def position(self) -> Position | None:
        return self._st.position

    @property
    def working_orders(self) -> list[Order]:
        return list(self._st.working)

    @property
    def trades_today(self) -> int:
        return self._st.trades_opened

    @property
    def realized_today(self) -> float:
        return self._st.realized

    # --- acciones -------------------------------------------------------------
    def submit(self, order: Order) -> bool:
        """Añade una orden de entrada. Solo se aceptan estando sin posición."""
        if self._st.position is not None:
            log.debug("Orden ignorada: ya hay posición abierta (%s)", order)
            return False
        self._st.working.append(order)
        return True

    def cancel_orders(self) -> None:
        self._st.working.clear()

    def exit(self, reason: str = "estrategia") -> None:
        """Cierra la posición a mercado en la apertura de la barra siguiente."""
        if self._st.position is not None:
            self._st.pending_exit = reason

    def move_stop(self, price: float) -> None:
        if self._st.position is not None:
            self._st.position.stop_loss = self.instrument.round_to_tick(price)

    @staticmethod
    def to_min(hhmm: str) -> int:
        return hhmm_to_min(hhmm)


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    days: pd.DataFrame
    strategy: str
    params: dict
    instrument: Instrument


DAY_COLUMNS = ["fecha", "pnl", "min_equity", "max_equity", "dd_intradia", "n_trades"]

_TRADE_COLUMNS = [
    "fecha", "lado", "contratos", "hora_entrada", "precio_entrada", "hora_salida", "precio_salida",
    "motivo", "pnl_bruto", "comisiones", "pnl_neto", "riesgo_usd", "r", "mae_usd", "mfe_usd",
    "duracion_min", "etiqueta",
]


class Backtester:
    def __init__(
        self,
        bars: pd.DataFrame,
        instrument: Instrument,
        session: Session = SESSIONS["nueva_york"],
        costs: CostModel | None = None,
        guard: DailyRiskGuard | None = None,
        news: NewsCalendar | None = None,
        news_before_min: int = 5,
        news_after_min: int = 5,
        flatten_before_news: bool = False,
        flat_time: str | None = None,
    ):
        df = bars if {"session_date", "minute"} <= set(bars.columns) else prepare_session(bars, session)
        if df.empty:
            raise ValueError("No hay barras dentro de la sesión elegida. ¿Zona horaria de los datos correcta?")
        self.df = df
        self.instrument = instrument
        self.session = session
        self.costs = costs or CostModel()
        self.guard = guard
        self.flatten_before_news = flatten_before_news
        self.flat_min = hhmm_to_min(flat_time)
        self.slip = self.costs.slippage_ticks * instrument.tick_size

        self.index = df.index
        self.o = df["open"].to_numpy(dtype=float)
        self.h = df["high"].to_numpy(dtype=float)
        self.l = df["low"].to_numpy(dtype=float)
        self.c = df["close"].to_numpy(dtype=float)
        self.v = df["volume"].to_numpy(dtype=float)
        self.minute = df["minute"].to_numpy(dtype=np.int64)

        sd = df["session_date"].to_numpy()
        change = np.flatnonzero(sd[1:] != sd[:-1]) + 1
        self.day_starts = np.r_[0, change]
        self.day_ends = np.r_[change, len(df)]
        self.dates = pd.DatetimeIndex(sd[self.day_starts])
        self.daily = pd.DataFrame(
            {
                "open": self.o[self.day_starts],
                "high": np.maximum.reduceat(self.h, self.day_starts),
                "low": np.minimum.reduceat(self.l, self.day_starts),
                "close": self.c[self.day_ends - 1],
            },
            index=self.dates,
        )
        self.daily["range"] = self.daily["high"] - self.daily["low"]

        if news is not None and len(news):
            self.blackout = news.blackout_mask(self.index, news_before_min, news_after_min)
        else:
            self.blackout = np.zeros(len(df), dtype=bool)

    # ------------------------------------------------------------------------
    def run(self, strategy: Strategy, start=None, end=None) -> BacktestResult:
        mask = np.ones(len(self.dates), dtype=bool)
        if start is not None:
            mask &= self.dates >= pd.Timestamp(start)
        if end is not None:
            mask &= self.dates <= pd.Timestamp(end)

        ctx = Context(self)
        trades: list[dict] = []
        days: list[dict] = []
        for d in np.flatnonzero(mask):
            st = self._run_day(strategy, ctx, int(d))
            trades.extend(st.trades)
            days.append(
                {
                    "fecha": self.dates[d],
                    "pnl": st.realized,
                    "min_equity": st.day_min,
                    "max_equity": st.day_max,
                    "dd_intradia": st.dd_intra,
                    "n_trades": st.trades_opened,
                }
            )
        trades_df = pd.DataFrame(trades, columns=_TRADE_COLUMNS)
        days_df = pd.DataFrame(days, columns=DAY_COLUMNS)
        return BacktestResult(trades_df, days_df, strategy.name, dict(strategy.p), self.instrument)

    # ------------------------------------------------------------------------
    def _run_day(self, strategy: Strategy, ctx: Context, d: int) -> _DayState:
        i0, i1 = int(self.day_starts[d]), int(self.day_ends[d])
        st = _DayState()
        ctx._st = st
        ctx.date = self.dates[d]
        ctx.daily = self.daily.iloc[:d]
        ctx.i0 = ctx.i = i0
        strategy.on_day_start(ctx)

        for i in range(i0, i1):
            m = self.minute[i]
            # A) caducidad de órdenes y bloqueo por noticias
            if st.working:
                if self.blackout[i]:
                    st.working.clear()
                else:
                    st.working = [w for w in st.working if w.expires_min is None or m < w.expires_min]
            # B) entradas
            if st.position is None and st.working:
                if self._entry_block(st):
                    st.working.clear()
                else:
                    self._try_entry(i, st)
            # C) gestión de la posición abierta
            if st.position is not None:
                self._manage(i, st)
            # D) cierre de sesión / antes de noticias
            last = i == i1 - 1 or (self.flat_min is not None and m >= self.flat_min)
            if st.position is not None:
                pre_news = self.flatten_before_news and i + 1 < i1 and self.blackout[i + 1]
                if last or pre_news:
                    self._close(i, st, self.c[i] - st.position.side * self.slip, "cierre_sesion" if last else "noticias")
            if last:
                st.working.clear()
                break
            # E) decisión de la estrategia al cierre de la barra
            ctx.i = i
            strategy.on_bar(ctx)
        return st

    def _entry_block(self, st: _DayState) -> str | None:
        if self.guard is None:
            return None
        return self.guard.entry_block_reason(st.trades_opened, st.realized, st.consecutive_losses)

    def _entry_fill(self, w: Order, i: int):
        """Devuelve (precio de ejecución, precio de activación, ¿ejecutada en la apertura?) o None."""
        o, h, l = self.o[i], self.h[i], self.l[i]
        s = int(w.side)
        if w.type is OrderType.MARKET:
            return o + s * self.slip, o, True
        if w.type is OrderType.STOP:
            if s > 0 and h >= w.price:
                return max(w.price, o) + self.slip, w.price, o >= w.price
            if s < 0 and l <= w.price:
                return min(w.price, o) - self.slip, w.price, o <= w.price
            return None
        tt = self.costs.limit_needs_trade_through
        if s > 0 and (l < w.price if tt else l <= w.price):
            return min(w.price, o), w.price, o <= w.price
        if s < 0 and (h > w.price if tt else h >= w.price):
            return max(w.price, o), w.price, o >= w.price
        return None

    def _try_entry(self, i: int, st: _DayState) -> None:
        best = None
        for w in st.working:
            res = self._entry_fill(w, i)
            if res is None:
                continue
            # si se activan varias en la misma barra, gana la más cercana a la apertura
            dist = abs(res[1] - self.o[i])
            if best is None or dist < best[0]:
                best = (dist, w, res)
        if best is None:
            return
        _, w, (fill, _, at_open) = best
        st.working.clear()
        self._open(i, st, w, fill, at_open)

    def _open(self, i: int, st: _DayState, w: Order, fill: float, at_open: bool) -> None:
        inst = self.instrument
        n = int(w.contracts)
        if self.guard is not None and self.guard.max_contracts is not None:
            n = min(n, self.guard.max_contracts)
        if n <= 0:
            return
        s = Side(w.side)
        sl = w.stop_loss if w.stop_loss is not None else (fill - s * w.sl_points if w.sl_points else None)
        tp = w.take_profit if w.take_profit is not None else (fill + s * w.tp_points if w.tp_points else None)
        sl = inst.round_to_tick(sl) if sl is not None else None
        tp = inst.round_to_tick(tp) if tp is not None else None
        pos = Position(s, n, fill, i, self.index[i], at_open, sl, tp, sl, w.tag)
        comm = inst.commission_per_side * n
        pos.extra["commission"] = comm
        st.realized -= comm
        self._track(st, st.realized, st.realized)
        st.position = pos
        st.trades_opened += 1
        # corchetes ya atravesados en la ejecución: salen al momento
        if sl is not None and (sl - fill) * s >= 0:
            self._close(i, st, fill - s * self.slip, "stop")
        elif tp is not None and (tp - fill) * s <= 0:
            self._close(i, st, fill, "objetivo")

    def _effective_stop(self, st: _DayState, p: Position):
        stop, reason = p.stop_loss, "stop"
        g = self.guard
        if g is not None and g.max_daily_loss is not None:
            inst = self.instrument
            n = p.contracts
            comm_exit = inst.commission_per_side * n
            pts = (-g.max_daily_loss - st.realized + comm_exit) / (inst.point_value * n)
            gp = inst.round_to_tick(p.entry_price + p.side * pts, "up" if p.side > 0 else "down")
            if stop is None or (gp - stop) * p.side > 0:
                stop, reason = gp, "limite_diario"
        return stop, reason

    @staticmethod
    def _track(st: _DayState, low_eq: float, high_eq: float) -> None:
        st.day_min = min(st.day_min, low_eq)
        st.day_max = max(st.day_max, high_eq)
        st.run_peak = max(st.run_peak, high_eq)
        st.dd_intra = max(st.dd_intra, st.run_peak - low_eq)

    def _mark(self, st: _DayState, p: Position, adverse_px: float, favorable_px: float) -> None:
        pv_n = self.instrument.point_value * p.contracts
        adv = (adverse_px - p.entry_price) * p.side
        fav = (favorable_px - p.entry_price) * p.side
        p.mae_points = max(p.mae_points, -adv)
        p.mfe_points = max(p.mfe_points, fav)
        self._track(st, st.realized + adv * pv_n, st.realized + fav * pv_n)

    def _manage(self, i: int, st: _DayState) -> None:
        p = st.position
        s = p.side
        o, h, l = self.o[i], self.h[i], self.l[i]
        if st.pending_exit:
            px = o - s * self.slip
            self._mark(st, p, px, px)
            self._close(i, st, px, st.pending_exit)
            return
        intrabar_entry = p.entry_index == i and not p.entry_at_open
        adverse = l if s > 0 else h
        favorable = h if s > 0 else l
        stop_px, stop_reason = self._effective_stop(st, p)
        tp = p.take_profit
        stop_hit = stop_px is not None and (adverse - stop_px) * s <= 0
        tp_hit = not intrabar_entry and tp is not None and (favorable - tp) * s >= 0
        if stop_hit:
            gap = not intrabar_entry and (o - stop_px) * s <= 0
            px = (o if gap else stop_px) - s * self.slip
            fav = favorable if tp is None else (min(favorable, tp) if s > 0 else max(favorable, tp))
            self._mark(st, p, px, fav)
            self._close(i, st, px, stop_reason)
        elif tp_hit:
            px = o if (not intrabar_entry and (o - tp) * s >= 0) else tp
            self._mark(st, p, adverse, px)
            self._close(i, st, px, "objetivo")
        else:
            self._mark(st, p, adverse, favorable)

    def _close(self, i: int, st: _DayState, px: float, reason: str) -> None:
        p = st.position
        inst = self.instrument
        n = p.contracts
        pv_n = inst.point_value * n
        gross = (px - p.entry_price) * p.side * pv_n
        comm_exit = inst.commission_per_side * n
        comm_total = p.extra["commission"] + comm_exit
        st.realized += gross - comm_exit
        self._track(st, st.realized, st.realized)
        net = gross - comm_total
        risk = abs(p.entry_price - p.initial_stop) * pv_n if p.initial_stop is not None else math.nan
        exit_time = self.index[i]
        st.trades.append(
            {
                "fecha": self.dates[np.searchsorted(self.day_starts, i, side="right") - 1],
                "lado": "largo" if p.side > 0 else "corto",
                "contratos": n,
                "hora_entrada": p.entry_time,
                "precio_entrada": p.entry_price,
                "hora_salida": exit_time,
                "precio_salida": px,
                "motivo": reason,
                "pnl_bruto": gross,
                "comisiones": comm_total,
                "pnl_neto": net,
                "riesgo_usd": risk,
                "r": net / risk if risk and risk > 0 else math.nan,
                "mae_usd": p.mae_points * pv_n,
                "mfe_usd": p.mfe_points * pv_n,
                "duracion_min": (exit_time - p.entry_time).total_seconds() / 60.0 + 1.0,
                "etiqueta": p.tag,
            }
        )
        st.consecutive_losses = st.consecutive_losses + 1 if net < 0 else 0
        st.position = None
        st.pending_exit = None
