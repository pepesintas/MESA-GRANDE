"""Descarga de barras de 1 minuto de futuros CME desde Databento (de pago, por uso).

Requiere `pip install databento` y DATABENTO_API_KEY en el entorno o en .env.
Consulta SIEMPRE el coste antes (--solo-coste): la descarga se cobra.
Símbolos continuos: NQ.v.0 (rola por volumen), NQ.c.0 (por calendario), ES.v.0, MNQ.v.0...
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def _api_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    env = Path(__file__).resolve().parents[2] / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("DATABENTO_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        raise SystemExit("Falta DATABENTO_API_KEY (en el entorno o en trading-bot/.env)")
    return key


def download(symbol: str, start: str, end: str, out: str | Path | None = None, dataset: str = "GLBX.MDP3",
             only_cost: bool = False) -> pd.DataFrame | None:
    try:
        import databento as db
    except ImportError:
        raise SystemExit("Instala el cliente: pip install databento") from None
    client = db.Historical(_api_key())
    stype = "continuous" if "." in symbol else "raw_symbol"
    query = dict(dataset=dataset, symbols=[symbol], stype_in=stype, schema="ohlcv-1m", start=start, end=end)
    cost = client.metadata.get_cost(**query)
    print(f"Coste estimado de la descarga: {cost:.2f} USD")
    if only_cost:
        return None
    df = client.timeseries.get_range(**query).to_df()
    df = df[["open", "high", "low", "close", "volume"]]
    df.index.name = "timestamp"  # ts_event de Databento = inicio de la barra, en UTC
    if out:
        out = Path(out)
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out) if out.suffix in (".parquet", ".pq") else df.to_csv(out)
        print(f"Guardadas {len(df):,} barras en {out}")
    return df
