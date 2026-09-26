import glob

import numpy as np
import pytest

from cajanegra.cli import main
from cajanegra.research.firm_compare import EdgeModel, best_by_firm, compare_firms, simulate_days
from cajanegra.risk.prop_rules import FirmConfig


def test_edge_model_expectancy_matches():
    m = EdgeModel(esperanza_r=0.15, payoff_r=2.0, prob_operar=1.0)
    d = simulate_days(m, 200, 4000, 100, seed=1)
    r = d[..., 0] / 200
    assert r.mean() == pytest.approx(0.15, abs=0.02)
    assert (d[..., 1] <= 0).all() and (d[..., 2] >= 0).all()
    assert (d[..., 3] >= 0).all()


def test_no_trade_days_are_empty():
    d = simulate_days(EdgeModel(0.1, prob_operar=0.5), 200, 50, 100, seed=2)
    empty = d[..., 4] == 0
    assert 0.3 < empty.mean() < 0.7
    assert np.all(d[empty] == 0)


def test_more_edge_means_more_passes_and_value():
    firms = {c.nombre: c for c in (FirmConfig.from_toml(f) for f in sorted(glob.glob("config/reglas/firmas/*.toml")))}
    tab = compare_firms(firms, edges=[-0.3, 0.6], risks=[250], n_paths=150, horizon=60, seed=3)
    for name in firms:
        lo = tab[(tab.firma == name) & (tab.esperanza_r == -0.3)].iloc[0]
        hi = tab[(tab.firma == name) & (tab.esperanza_r == 0.6)].iloc[0]
        assert hi.p_aprobar > lo.p_aprobar + 0.3
        assert hi.valor_esperado > lo.valor_esperado
    best = best_by_firm(tab)
    assert len(best) == 2 * len(firms)


def test_cli_compare(capsys):
    main(["comparar-firmas", "--esperanza", "0.1", "--riesgo", "250", "--simulaciones", "30", "--horizonte", "40"])
    out = capsys.readouterr().out
    assert "VALOR ESPERADO" in out and "Topstep" in out
