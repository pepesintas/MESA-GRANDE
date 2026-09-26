"""¿Pasaría esta estrategia la evaluación de la firma? ¿Cuánto vale cada cuenta comprada?

Dos métodos sobre los resúmenes diarios del backtest:
- Arranques históricos: empezar la evaluación en cada día real de la historia y ver qué pasó.
  Respeta rachas y regímenes reales.
- Bootstrap por bloques: barajar bloques de días para generar miles de historias alternativas.
  Da una idea de la dispersión (mala suerte posible) más allá de la historia concreta.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from ..risk.prop_rules import AccountRules, FirmConfig, PropAccount

_COLS = ["pnl", "min_equity", "max_equity", "dd_intradia", "n_trades"]


def _run_account(rules: AccountRules, row: Callable[[int], tuple | None], t0: int, horizon: int):
    acc = PropAccount(rules)
    t = t0
    while t - t0 < horizon:
        r = row(t)
        if r is None:
            return acc, t, "sin_datos"
        acc.process_day(*r)
        t += 1
        if acc.status != "activa":
            return acc, t, acc.status
    return acc, t, "sin_resolver"


def simulate_path(
    row: Callable[[int], tuple | None], firm: FirmConfig, horizon: int = 120, max_payouts: int | None = None
) -> dict:
    """Recorre las fases de evaluación y, si se aprueban, opera la cuenta fondeada `horizon`
    sesiones retirando cada vez que las reglas lo permiten (o hasta `max_payouts` retiros)."""
    eco = firm.economia
    t = 0
    for fase in firm.fases:
        acc, t_end, status = _run_account(fase, row, t, horizon)
        t = t_end
        if status != "aprobada":
            coste = eco.evaluation_cost(t)
            if status == "sin_datos":
                resultado = "sin_datos"
            elif status == "suspendida":
                resultado = "evaluación suspendida"
            else:
                resultado = "evaluación sin terminar"
            return {
                "resultado": resultado, "motivo": acc.reason, "aprobada": False,
                "sesiones_evaluacion": t, "sesiones_fondeada": 0, "n_retiros": 0,
                "retiro": 0.0, "coste": coste, "neto": -coste,
            }
    coste = eco.evaluation_cost(t) + eco.coste_activacion
    out = {"aprobada": True, "sesiones_evaluacion": t, "coste": coste, "motivo": ""}
    if firm.fondeada is None:
        out.update(resultado="evaluación aprobada", sesiones_fondeada=0, n_retiros=0, retiro=0.0, neto=-coste)
        return out
    acc = PropAccount(firm.fondeada)
    paid, n, u = 0.0, 0, 0
    while u < horizon:
        r = row(t + u)
        if r is None:
            out.update(resultado="sin_datos", sesiones_fondeada=u, n_retiros=n, retiro=paid, neto=paid - coste)
            return out
        acc.process_day(*r)
        u += 1
        if acc.status == "aprobada":  # en la fondeada: retiro disponible
            gross = eco.withdrawable(acc.profit)
            if gross > 0:
                acc.withdraw(gross)
                paid += gross * eco.reparto
                n += 1
                if max_payouts is not None and n >= max_payouts:
                    break
            else:
                acc.status = "activa"
        if acc.status in ("suspendida", "caducada"):
            break
    lost = acc.status in ("suspendida", "caducada")
    if n == 0:
        resultado = "fondeada perdida sin cobrar" if lost else "fondeada activa sin cobrar"
    else:
        resultado = "cobró y perdió la cuenta" if lost else "cobró y sigue activa"
    out.update(resultado=resultado, motivo=acc.reason, sesiones_fondeada=u, n_retiros=n, retiro=paid, neto=paid - coste)
    return out


def _rows(days: pd.DataFrame) -> list[tuple]:
    return list(days[_COLS].itertuples(index=False, name=None))


def rolling_starts(days: pd.DataFrame, firm: FirmConfig, horizon: int = 120, step: int = 1) -> pd.DataFrame:
    """Una simulación por cada posible día de inicio real (cada `step` sesiones). Los caminos que se
    quedan sin historia antes de terminar se descartan."""
    rows = _rows(days)
    n = len(rows)
    out = []
    for s in range(0, n, step):
        res = simulate_path(lambda t, s=s: rows[s + t] if s + t < n else None, firm, horizon)
        res["inicio"] = days["fecha"].iloc[s]
        out.append(res)
    df = pd.DataFrame(out)
    return df[df["resultado"] != "sin_datos"].reset_index(drop=True)


def block_bootstrap(
    days: pd.DataFrame, firm: FirmConfig, n_sims: int = 2000, block: int = 5, horizon: int = 120, seed: int | None = 0
) -> pd.DataFrame:
    rows = _rows(days)
    n = len(rows)
    if n == 0:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    total = horizon * (len(firm.fases) + (1 if firm.fondeada else 0))
    n_blocks = -(-total // block)
    out = []
    for _ in range(n_sims):
        starts = rng.integers(0, max(1, n - block + 1), size=n_blocks)
        seq = (starts[:, None] + np.arange(block)[None, :]).ravel()[:total]
        seq = np.minimum(seq, n - 1)
        out.append(simulate_path(lambda t, seq=seq: rows[seq[t]] if t < total else None, firm, horizon))
    return pd.DataFrame(out)


def summarize(paths: pd.DataFrame) -> dict:
    if paths.empty:
        return {"simulaciones": 0}
    passed = paths["aprobada"]
    paid = paths["retiro"] > 0
    fails = paths.loc[paths["motivo"] != "", "motivo"].value_counts()
    return {
        "simulaciones": int(len(paths)),
        "p_aprobar": float(passed.mean()),
        "p_retiro": float(paid.mean()),
        "p_retiro_si_fondeada": float(paid[passed].mean()) if passed.any() else 0.0,
        "sesiones_mediana_aprobar": float(paths.loc[passed, "sesiones_evaluacion"].median()) if passed.any() else float("nan"),
        "coste_medio": float(paths["coste"].mean()),
        "cobrado_medio_si_cobra": float(paths.loc[paid, "retiro"].mean()) if paid.any() else 0.0,
        "retiros_medios_si_cobra": float(paths.loc[paid, "n_retiros"].mean()) if paid.any() else 0.0,
        "valor_esperado_por_cuenta": float(paths["neto"].mean()),
        "resultados": paths["resultado"].value_counts().to_dict(),
        "motivos_suspension": fails.to_dict(),
    }
