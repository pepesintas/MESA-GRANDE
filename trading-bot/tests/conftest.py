import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cajanegra.strategies.base import Strategy  # noqa: E402


def make_bars(rows, day="2024-03-04", start="09:30", tz="America/New_York"):
    """rows: lista de (open, high, low, close) consecutivos de 1 minuto."""
    idx = pd.date_range(f"{day} {start}", periods=len(rows), freq="1min", tz=tz).tz_convert("UTC")
    df = pd.DataFrame(rows, columns=["open", "high", "low", "close"], index=idx, dtype=float)
    df["volume"] = 100.0
    return df


def make_days(days_rows, start_day="2024-03-04"):
    """Varias sesiones: lista de listas de filas."""
    dates = pd.bdate_range(start_day, periods=len(days_rows))
    return pd.concat([make_bars(rows, day=str(d.date())) for d, rows in zip(dates, days_rows)])


class Scripted(Strategy):
    """Estrategia de prueba: envía órdenes predefinidas al cierre de ciertas barras."""

    name = "scripted"
    defaults = {"plan": {}, "exits": (), "moves": {}}

    def __init__(self, **params):
        super().__init__(**params)
        self.seen_lengths = []

    def on_bar(self, ctx):
        self.seen_lengths.append((ctx.k, len(ctx.closes)))
        for order in self.p["plan"].get(ctx.k, []):
            ctx.submit(order)
        if ctx.k in self.p["exits"]:
            ctx.exit("manual")
        if ctx.k in self.p["moves"]:
            ctx.move_stop(self.p["moves"][ctx.k])


@pytest.fixture
def scripted():
    return Scripted
