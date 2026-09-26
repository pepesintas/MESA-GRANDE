"""Carga de barras OHLCV (1 minuto) desde CSV/Parquet y recorte por sesión.

Convención interna: el timestamp de cada barra es su hora de INICIO.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_TS_CANDIDATES = ("timestamp", "ts_event", "datetime", "date_time", "time", "date")
_ALIASES = {"o": "open", "h": "high", "l": "low", "c": "close", "last": "close", "v": "volume", "vol": "volume"}
_HAS_OFFSET = re.compile(r"(Z|[+-]\d{2}:?\d{2})$")


@dataclass(frozen=True)
class Session:
    name: str
    tz: str
    start: str  # "HH:MM" hora local del mercado
    end: str

    @property
    def start_min(self) -> int:
        h, m = self.start.split(":")
        return int(h) * 60 + int(m)

    @property
    def end_min(self) -> int:
        h, m = self.end.split(":")
        return int(h) * 60 + int(m)


SESSIONS = {
    "nueva_york": Session("nueva_york", "America/New_York", "09:30", "16:00"),
    "londres": Session("londres", "Europe/London", "08:00", "16:30"),
}


def _parse_timestamps(raw: pd.Series, tz_source: str) -> pd.DatetimeIndex:
    if pd.api.types.is_numeric_dtype(raw):
        mag = float(np.nanmax(np.abs(raw.to_numpy(dtype="float64"))))
        unit = "ns" if mag > 1e17 else "us" if mag > 1e14 else "ms" if mag > 1e11 else "s"
        return pd.DatetimeIndex(pd.to_datetime(raw, unit=unit, utc=True))
    if isinstance(raw.dtype, pd.DatetimeTZDtype):
        return pd.DatetimeIndex(raw).tz_convert("UTC")
    first = str(raw.iloc[0]).strip()
    if _HAS_OFFSET.search(first):
        return pd.DatetimeIndex(pd.to_datetime(raw, utc=True, format="mixed"))
    naive = pd.DatetimeIndex(pd.to_datetime(raw, format="mixed"))
    local = naive.tz_localize(tz_source, ambiguous="NaT", nonexistent="NaT")
    return local.tz_convert("UTC")


def load_bars(path: str | Path, tz_source: str = "UTC", label: str = "start", header: bool = True) -> pd.DataFrame:
    """Lee barras y devuelve un DataFrame con índice UTC y columnas open/high/low/close/volume.

    tz_source: zona horaria de los timestamps si vienen sin zona (p. ej. "America/New_York").
    label: "start" si el timestamp marca el inicio de la barra, "end" si marca el cierre.
    header: False para ficheros sin cabecera (timestamp, open, high, low, close[, volume]).
    """
    path = Path(path)
    if path.suffix.lower() in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, header=0 if header else None)
        if not header:
            names = ["timestamp", "open", "high", "low", "close", "volume"][: df.shape[1]]
            df.columns = names
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.rename(columns={k: v for k, v in _ALIASES.items() if k in df.columns and v not in df.columns})

    if "date" in df.columns and "time" in df.columns:
        raw_ts = df["date"].astype(str) + " " + df["time"].astype(str)
    else:
        col = next((c for c in _TS_CANDIDATES if c in df.columns), None)
        if col is None:
            raise ValueError(f"No encuentro la columna de fecha/hora. Columnas: {list(df.columns)}")
        raw_ts = df[col]

    missing = [c for c in ("open", "high", "low", "close") if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas de precio: {missing}")

    idx = _parse_timestamps(raw_ts.reset_index(drop=True), tz_source)
    out = pd.DataFrame(
        {
            "open": pd.to_numeric(df["open"], errors="coerce").to_numpy(),
            "high": pd.to_numeric(df["high"], errors="coerce").to_numpy(),
            "low": pd.to_numeric(df["low"], errors="coerce").to_numpy(),
            "close": pd.to_numeric(df["close"], errors="coerce").to_numpy(),
            "volume": pd.to_numeric(df["volume"], errors="coerce").to_numpy() if "volume" in df.columns else 0.0,
        },
        index=idx,
    )
    out.index.name = "timestamp"
    out = out[out.index.notna()].dropna(subset=["open", "high", "low", "close"])
    out = out.sort_index()
    out = out[~out.index.duplicated(keep="last")]

    if label == "end" and len(out) > 1:
        step = pd.Series(out.index).diff().median()
        out.index = out.index - step

    # Reparaciones mínimas: high/low deben contener open/close. Filas imposibles se descartan.
    bad = out["high"] < out["low"]
    if bad.any():
        log.warning("Descartadas %d barras con high < low", int(bad.sum()))
        out = out[~bad]
    out["high"] = out[["open", "high", "low", "close"]].max(axis=1)
    out["low"] = out[["open", "high", "low", "close"]].min(axis=1)
    out["volume"] = out["volume"].fillna(0.0)
    return out


def prepare_session(bars: pd.DataFrame, session: Session) -> pd.DataFrame:
    """Convierte a hora del mercado, se queda con las barras de la sesión y añade
    las columnas `session_date` (fecha de la sesión) y `minute` (minuto del día)."""
    local = bars.tz_convert(session.tz)
    minute = (local.index.hour * 60 + local.index.minute).to_numpy()
    wall_date = local.index.tz_localize(None).normalize()
    s, e = session.start_min, session.end_min
    if s < e:
        mask = (minute >= s) & (minute < e)
        session_date = wall_date
    else:  # la sesión cruza medianoche: lo posterior a `start` cuenta para el día siguiente
        mask = (minute >= s) | (minute < e)
        session_date = wall_date + pd.to_timedelta((minute >= s).astype(int), unit="D")
    out = local[mask].copy()
    out["session_date"] = np.asarray(session_date)[mask]
    out["minute"] = minute[mask]
    return out
