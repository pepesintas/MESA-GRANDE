"""Datos sintéticos (paseo aleatorio) para probar que el motor funciona.

Un paseo aleatorio no tiene ventaja explotable: cualquier estrategia debe perder
aproximadamente las comisiones. Si algo "gana" aquí, hay un bug (lookahead).
NO sirve para sacar conclusiones sobre ninguna estrategia.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .loader import SESSIONS, Session


def generate_synthetic_bars(
    days: int = 500,
    start: str = "2022-01-03",
    start_price: float = 15000.0,
    daily_vol: float = 0.013,
    drift_per_day: float = 0.0,
    tick_size: float = 0.25,
    session: Session = SESSIONS["nueva_york"],
    substeps: int = 6,
    seed: int | None = 42,
) -> pd.DataFrame:
    """Barras de 1 minuto con volatilidad intradía en U (más movimiento en apertura y cierre).

    drift_per_day: deriva diaria en fracción del precio (p. ej. 0.0005 = mercado alcista suave).
    """
    rng = np.random.default_rng(seed)
    n_min = session.end_min - session.start_min
    t = np.arange(n_min)
    weights = 1.0 + 1.5 * np.exp(-t / 30.0) + 0.8 * np.exp(-(n_min - 1 - t) / 30.0)
    minute_sigma = np.sqrt(weights / weights.sum())  # fracción de la varianza diaria por minuto
    step_sigma = np.repeat(minute_sigma / np.sqrt(substeps), substeps)
    drift_step = drift_per_day / (n_min * substeps)

    dates = pd.bdate_range(start=start, periods=days)
    opens, highs, lows, closes = [], [], [], []
    price = start_price
    for d in range(days):
        if d > 0:
            price += price * daily_vol * 0.35 * rng.standard_normal()  # hueco nocturno
        scale = price * daily_vol
        incr = scale * (step_sigma * rng.standard_normal(step_sigma.size) + drift_step)
        path = (price + np.cumsum(incr)).reshape(n_min, substeps)
        # la barra abre en el primer precio negociado del minuto
        o = path[:, 0]
        c = path[:, -1]
        h = path.max(axis=1)
        lo = path.min(axis=1)
        opens.append(o)
        highs.append(h)
        lows.append(lo)
        closes.append(c)
        price = c[-1]

    def _tick(a: np.ndarray) -> np.ndarray:
        return np.round(np.concatenate(a) / tick_size) * tick_size

    wall = (
        np.repeat(dates.values, n_min)
        + np.tile(pd.to_timedelta(session.start_min + t, unit="min").values, days)
    )
    idx = pd.DatetimeIndex(wall).tz_localize(session.tz).tz_convert("UTC")
    df = pd.DataFrame(
        {"open": _tick(opens), "high": _tick(highs), "low": _tick(lows), "close": _tick(closes)},
        index=idx,
    )
    df["volume"] = rng.integers(50, 500, size=len(df)).astype(float)
    df.index.name = "timestamp"
    return df
