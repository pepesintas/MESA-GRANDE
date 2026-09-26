"""Calendario económico y ventanas de bloqueo por noticias (CPI, FOMC, NFP...).

Uso principal: filtro de riesgo. Muchas firmas de fondeo restringen operar alrededor
de noticias de alto impacto, y son los minutos con más deslizamiento.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

_IMPACT = {
    "high": "alto", "alto": "alto", "3": "alto",
    "medium": "medio", "medio": "medio", "2": "medio",
    "low": "bajo", "bajo": "bajo", "1": "bajo",
    "holiday": "festivo", "festivo": "festivo",
}


def _norm_impact(value) -> str:
    return _IMPACT.get(str(value).strip().lower(), str(value).strip().lower())


@dataclass(frozen=True)
class NewsEvent:
    time: pd.Timestamp  # UTC
    currency: str
    impact: str  # alto | medio | bajo | festivo
    title: str


class NewsCalendar:
    def __init__(self, events: list[NewsEvent]):
        self.events = sorted(events, key=lambda e: e.time)

    def __len__(self) -> int:
        return len(self.events)

    @classmethod
    def from_csv(cls, path: str | Path, tz: str = "America/New_York") -> "NewsCalendar":
        """CSV con columnas: fecha_hora, moneda, impacto, evento (hora local `tz` si no trae zona)."""
        df = pd.read_csv(path)
        ts = pd.to_datetime(df["fecha_hora"], format="mixed")
        ts = ts.dt.tz_localize(tz) if ts.dt.tz is None else ts
        events = [
            NewsEvent(t.tz_convert("UTC"), str(m).upper(), _norm_impact(i), str(ev))
            for t, m, i, ev in zip(ts, df["moneda"], df["impacto"], df["evento"])
        ]
        return cls(events)

    @classmethod
    def from_forexfactory_json(cls, source: str | Path | list) -> "NewsCalendar":
        """Formato del feed semanal público de Forex Factory
        (campos: title, country, date ISO con zona, impact)."""
        data = source
        if not isinstance(source, list):
            data = json.loads(Path(source).read_text())
        events = []
        for row in data:
            try:
                t = pd.Timestamp(row["date"]).tz_convert("UTC")
            except (KeyError, ValueError, TypeError):
                continue
            events.append(NewsEvent(t, str(row.get("country", "")).upper(), _norm_impact(row.get("impact", "")), str(row.get("title", ""))))
        return cls(events)

    def filter(self, currencies=("USD",), impacts=("alto",)) -> "NewsCalendar":
        cur = {c.upper() for c in currencies} if currencies else None
        imp = set(impacts) if impacts else None
        return NewsCalendar([
            e for e in self.events
            if (cur is None or e.currency in cur) and (imp is None or e.impact in imp)
        ])

    def blackout_mask(self, index: pd.DatetimeIndex, before_min: int = 5, after_min: int = 5) -> np.ndarray:
        """True en las barras cuyo inicio cae en [evento - before_min, evento + after_min)."""
        idx = index.as_unit("ns").asi8  # siempre en ns (pandas 3 usa µs por defecto)
        mark = np.zeros(len(idx) + 1, dtype=np.int64)
        for e in self.events:
            t = e.time.value
            lo = np.searchsorted(idx, t - before_min * 60_000_000_000, side="left")
            hi = np.searchsorted(idx, t + after_min * 60_000_000_000, side="left")
            if hi > lo:
                mark[lo] += 1
                mark[hi] -= 1
        return np.cumsum(mark[:-1]) > 0
