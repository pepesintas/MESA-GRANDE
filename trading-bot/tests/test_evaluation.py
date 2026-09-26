import pandas as pd
import pytest

from cajanegra.research.evaluation import block_bootstrap, rolling_starts, simulate_path, summarize
from cajanegra.risk.prop_rules import AccountRules, Economics, FirmConfig


def days_df(pnls):
    return pd.DataFrame(
        {
            "fecha": pd.bdate_range("2024-01-01", periods=len(pnls)),
            "pnl": pnls,
            "min_equity": [min(p, 0) for p in pnls],
            "max_equity": [max(p, 0) for p in pnls],
            "dd_intradia": [abs(min(p, 0)) for p in pnls],
            "n_trades": [1] * len(pnls),
        }
    )


FIRM = FirmConfig(
    nombre="test",
    fases=[AccountRules(objetivo_beneficio=1000, drawdown_maximo=1000, tipo_drawdown="trailing_cierre")],
    fondeada=AccountRules(objetivo_beneficio=500, drawdown_maximo=1000, tipo_drawdown="trailing_cierre"),
    economia=Economics(coste_evaluacion=100, coste_activacion=50, reparto=0.9),
)


def test_path_pass_and_first_payout():
    rows = [(500, 0, 500, 0, 1)] * 10
    res = simulate_path(lambda t: rows[t] if t < len(rows) else None, FIRM, max_payouts=1)
    assert res["resultado"] == "cobró y sigue activa"
    assert res["sesiones_evaluacion"] == 2
    assert res["retiro"] == pytest.approx(450)
    assert res["neto"] == pytest.approx(450 - 150)


def test_funded_phase_collects_every_payout_until_horizon():
    rows = [(500, 0, 500, 0, 1)] * 20
    res = simulate_path(lambda t: rows[t] if t < len(rows) else None, FIRM, horizon=6)
    assert res["n_retiros"] == 6 and res["retiro"] == pytest.approx(6 * 450)


def test_payout_leaves_account_closer_to_floor():
    # gana 1500 en fondeada, retira todo; el suelo (trailing al cierre) no baja -> una pérdida pequeña suspende
    firm = FirmConfig(
        nombre="t",
        fases=[AccountRules(objetivo_beneficio=100, drawdown_maximo=1000)],
        fondeada=AccountRules(objetivo_beneficio=1500, drawdown_maximo=1000, tipo_drawdown="trailing_cierre"),
        economia=Economics(reparto=1.0),
    )
    rows = [(100, 0, 100, 0, 1), (1500, 0, 1500, 0, 1), (-600, -600, 0, 600, 1)] + [(0, 0, 0, 0, 0)] * 5
    res = simulate_path(lambda t: rows[t] if t < len(rows) else None, firm, horizon=5)
    assert res["n_retiros"] == 1 and res["resultado"] == "cobró y perdió la cuenta"


def test_all_losing_days_never_pass():
    s = summarize(rolling_starts(days_df([-300] * 40), FIRM))
    assert s["p_aprobar"] == 0 and s["valor_esperado_por_cuenta"] == pytest.approx(-100)


def test_rolling_drops_censored_paths_and_bootstrap_is_reproducible():
    d = days_df([400, -200, 300, 500, -100, 600, 200, -300, 400, 500] * 6)
    roll = rolling_starts(d, FIRM, horizon=30)
    assert (roll["resultado"] != "sin_datos").all()
    b1 = summarize(block_bootstrap(d, FIRM, n_sims=200, seed=1, horizon=30))
    b2 = summarize(block_bootstrap(d, FIRM, n_sims=200, seed=1, horizon=30))
    assert b1 == b2
    assert 0 <= b1["p_retiro"] <= b1["p_aprobar"] <= 1
