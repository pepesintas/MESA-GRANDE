"""Métricas de rendimiento de un backtest."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def trade_stats(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"operaciones": 0}
    pnl = trades["pnl_neto"]
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    gross_win, gross_loss = wins.sum(), -losses.sum()
    r = trades["r"].dropna()
    return {
        "operaciones": int(len(trades)),
        "acierto": float((pnl > 0).mean()),
        "ganancia_media": float(wins.mean()) if len(wins) else 0.0,
        "perdida_media": float(losses.mean()) if len(losses) else 0.0,
        "factor_beneficio": float(gross_win / gross_loss) if gross_loss > 0 else math.inf,
        "esperanza_por_operacion": float(pnl.mean()),
        "esperanza_r": float(r.mean()) if len(r) else math.nan,
        "beneficio_neto": float(pnl.sum()),
        "comisiones": float(trades["comisiones"].sum()),
        "largos": int((trades["lado"] == "largo").sum()),
        "cortos": int((trades["lado"] == "corto").sum()),
    }


def _max_streak(mask: np.ndarray) -> int:
    best = cur = 0
    for m in mask:
        cur = cur + 1 if m else 0
        best = max(best, cur)
    return best


def daily_stats(days: pd.DataFrame) -> dict:
    if days.empty:
        return {"sesiones": 0}
    pnl = days["pnl"].to_numpy()
    traded = days["n_trades"].to_numpy() > 0
    equity = np.cumsum(pnl)
    peak = np.maximum.accumulate(np.r_[0.0, equity])[1:]
    max_dd = float((peak - equity).max())
    # drawdown contando el peor momento intradía de cada día
    intraday_low = np.r_[0.0, equity[:-1]] + days["min_equity"].to_numpy()
    max_dd_intra = float(np.maximum(peak - intraday_low, 0).max())
    std = pnl.std(ddof=1) if len(pnl) > 1 else 0.0
    tp = pnl[traded]
    return {
        "sesiones": int(len(days)),
        "dias_operados": int(traded.sum()),
        "dias_positivos": float((tp > 0).mean()) if len(tp) else 0.0,
        "mejor_dia": float(pnl.max()),
        "peor_dia": float(pnl.min()),
        "sharpe_anual": float(pnl.mean() / std * math.sqrt(252)) if std > 0 else 0.0,
        "max_drawdown_cierre": max_dd,
        "max_drawdown_intradia": max_dd_intra,
        "racha_dias_perdedores": _max_streak(pnl < 0),
        "beneficio_neto": float(pnl.sum()),
    }


def yearly_table(trades: pd.DataFrame, days: pd.DataFrame) -> pd.DataFrame:
    if days.empty:
        return pd.DataFrame()
    d = days.assign(año=pd.DatetimeIndex(days["fecha"]).year)
    tbl = d.groupby("año").agg(beneficio=("pnl", "sum"), dias_operados=("n_trades", lambda s: int((s > 0).sum())))
    if not trades.empty:
        t = trades.assign(año=pd.DatetimeIndex(trades["fecha"]).year)
        g = t.groupby("año")["pnl_neto"]
        tbl["operaciones"] = g.size()
        tbl["acierto"] = g.apply(lambda s: (s > 0).mean())
    return tbl.fillna(0)
