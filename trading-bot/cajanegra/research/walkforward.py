"""Validación walk-forward: optimizar en el pasado, operar en el "futuro" que el optimizador no vio.

Es la defensa principal contra el sobreajuste: el resultado que cuenta es la curva
concatenada de los tramos fuera de muestra (OOS), nunca el mejor resultado dentro de muestra.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import pandas as pd

from ..engine.backtest import Backtester, BacktestResult
from ..strategies import get_strategy
from .metrics import daily_stats


def param_grid(grid: dict[str, list]) -> list[dict]:
    if not grid:
        return [{}]
    keys = list(grid)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(grid[k] for k in keys))]


def score(result: BacktestResult, metric: str = "beneficio_dd", min_trades: int = 30) -> float:
    if len(result.trades) < min_trades:
        return -math.inf
    d = daily_stats(result.days)
    if metric == "sharpe":
        return d["sharpe_anual"]
    if metric == "beneficio":
        return d["beneficio_neto"]
    return d["beneficio_neto"] / max(d["max_drawdown_intradia"], 1.0)


@dataclass
class WalkForwardResult:
    windows: pd.DataFrame
    trades: pd.DataFrame   # solo tramos fuera de muestra
    days: pd.DataFrame


def walk_forward(
    bt: Backtester,
    strategy: str,
    grid: dict[str, list],
    fixed: dict | None = None,
    is_sessions: int = 500,
    oos_sessions: int = 125,
    metric: str = "beneficio_dd",
    min_trades: int = 30,
    progress=None,
) -> WalkForwardResult:
    fixed = fixed or {}
    combos = param_grid(grid)
    dates = bt.dates
    rows, trades, days = [], [], []
    k = 0
    while k + is_sessions < len(dates):
        is_start, is_end = dates[k], dates[k + is_sessions - 1]
        oos_start = dates[k + is_sessions]
        oos_end = dates[min(k + is_sessions + oos_sessions, len(dates)) - 1]
        best = None
        for params in combos:
            res = bt.run(get_strategy(strategy, **fixed, **params), is_start, is_end)
            sc = score(res, metric, min_trades)
            if best is None or sc > best[0]:
                best = (sc, params, res)
        sc_is, params, res_is = best
        oos = bt.run(get_strategy(strategy, **fixed, **params), oos_start, oos_end)
        rows.append(
            {
                "is_desde": is_start.date(), "is_hasta": is_end.date(),
                "oos_desde": oos_start.date(), "oos_hasta": oos_end.date(),
                "parametros": params,
                "puntuacion_is": sc_is,
                "puntuacion_oos": score(oos, metric, min_trades=1),
                "beneficio_is": res_is.days["pnl"].sum(),
                "beneficio_oos": oos.days["pnl"].sum(),
                "operaciones_oos": len(oos.trades),
            }
        )
        trades.append(oos.trades)
        days.append(oos.days)
        if progress:
            progress(rows[-1])
        k += oos_sessions
    if not rows:
        raise ValueError(f"Hacen falta más de {is_sessions} sesiones para una ventana walk-forward (hay {len(dates)}).")
    return WalkForwardResult(
        pd.DataFrame(rows),
        pd.concat(trades, ignore_index=True),
        pd.concat(days, ignore_index=True),
    )
