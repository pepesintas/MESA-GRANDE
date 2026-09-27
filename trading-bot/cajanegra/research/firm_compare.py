"""¿Qué firma conviene más para una MISMA estrategia?

Genera trayectorias de días de una estrategia hipotética (1 operación al día como mucho, con
stop y objetivo) y las pasa por las reglas de cada firma. Todas las firmas ven exactamente los
mismos días (números aleatorios comunes), así las diferencias se deben solo a las reglas.

La "ventaja" se mide en R: esperanza por operación en múltiplos del riesgo (0 = sin ventaja,
+0.1 R = ganas de media un 10 % de lo que arriesgas por operación, ya descontadas comisiones).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..risk.prop_rules import FirmConfig
from .evaluation import simulate_path, summarize


@dataclass(frozen=True)
class EdgeModel:
    esperanza_r: float          # esperanza neta por operación, en R
    payoff_r: float = 2.0       # un acierto gana payoff_r veces el riesgo
    prob_operar: float = 0.85   # probabilidad de que haya operación un día
    comision_usd: float = 3.0   # ida y vuelta, ya incluida en la esperanza

    @property
    def win_prob(self) -> float:
        # esperanza = p·payoff − (1 − p)  →  p = (esperanza + 1) / (payoff + 1)
        return (self.esperanza_r + 1.0) / (self.payoff_r + 1.0)


def simulate_days(model: EdgeModel, risk_usd: float, n_paths: int, n_days: int, seed: int | None = 0) -> np.ndarray:
    """Array (n_paths, n_days, 5) con pnl, min_equity, max_equity, dd_intradia, n_trades por día.

    Camino intradía típico: un acierto retrocede antes hasta un 70 % del riesgo y luego alcanza
    el objetivo; un fallo avanza antes a favor hasta la mitad del objetivo y luego toca el stop.
    """
    rng = np.random.default_rng(seed)
    shape = (n_paths, n_days)
    trade = rng.random(shape) < model.prob_operar
    win = rng.random(shape) < model.win_prob
    adverse = rng.random(shape) * 0.7
    favorable = rng.random(shape) * 0.5 * model.payoff_r
    r, c, k = risk_usd, model.comision_usd, model.payoff_r
    # resultados netos (la esperanza ya descuenta comisiones); la comisión de entrada solo
    # afecta al camino intradía
    win_amt = k * r
    loss_amt = r
    pnl = np.where(win, win_amt, -loss_amt)
    mn = np.where(win, -adverse * r - c / 2, -loss_amt)
    mx = np.where(win, win_amt, np.maximum(favorable * r - c / 2, 0.0))
    dd = np.where(win, adverse * r + c / 2, mx - mn)
    out = np.stack([pnl, mn, mx, dd, np.ones(shape)], axis=-1)
    out[~trade] = 0.0
    return out


def _row_fn(arr: np.ndarray):
    seq = [tuple(x) for x in arr.tolist()]
    n = len(seq)
    return lambda t: seq[t] if t < n else None


def compare_firms(
    firms: dict[str, FirmConfig],
    edges: list[float],
    risks: list[float],
    n_paths: int = 1000,
    horizon: int = 120,
    payoff_r: float = 2.0,
    prob_operar: float = 0.85,
    seed: int = 0,
    risk_funded: float | None = None,
    payoff_funded: float | None = None,
) -> pd.DataFrame:
    """`risks` y `payoff_r` se aplican a la evaluación; si se indica `risk_funded` y/o
    `payoff_funded`, la cuenta fondeada se opera con esos valores (misma ventaja en R)."""
    phases = max(len(f.fases) for f in firms.values()) + 1
    split = risk_funded is not None or payoff_funded is not None
    rows = []
    for e in edges:
        model = EdgeModel(esperanza_r=e, payoff_r=payoff_r, prob_operar=prob_operar)
        funded_model = EdgeModel(esperanza_r=e, payoff_r=payoff_funded or payoff_r, prob_operar=prob_operar)
        for risk in risks:
            days = simulate_days(model, risk, n_paths, horizon * phases, seed=seed)
            fdays = (simulate_days(funded_model, risk_funded or risk, n_paths, horizon * phases, seed=seed + 1)
                     if split else None)
            paths_per_firm = {name: [] for name in firms}
            for i in range(n_paths):
                row = _row_fn(days[i])
                frow = _row_fn(fdays[i]) if split else None
                for name, firm in firms.items():
                    paths_per_firm[name].append(simulate_path(row, firm, horizon, row_funded=frow))
            for name, paths in paths_per_firm.items():
                s = summarize(pd.DataFrame(paths))
                rows.append({
                    "firma": name, "esperanza_r": e, "riesgo_usd": risk,
                    "p_aprobar": s["p_aprobar"], "p_cobrar": s["p_retiro"],
                    "cobrado_si_cobra": s["cobrado_medio_si_cobra"],
                    "sesiones_aprobar": s["sesiones_mediana_aprobar"],
                    "coste_medio": s["coste_medio"],
                    "valor_esperado": s["valor_esperado_por_cuenta"],
                })
    return pd.DataFrame(rows)


def best_by_firm(table: pd.DataFrame) -> pd.DataFrame:
    """Para cada firma y ventaja, el riesgo por operación que maximiza el valor esperado."""
    idx = table.groupby(["firma", "esperanza_r"])["valor_esperado"].idxmax()
    return table.loc[idx].sort_values(["esperanza_r", "valor_esperado"], ascending=[True, False]).reset_index(drop=True)
