import numpy as np
import pytest

from cajanegra.data import generate_synthetic_bars
from cajanegra.engine import Backtester, CostModel
from cajanegra.instruments import get_instrument
from cajanegra.strategies import FirstFVG, OpeningRangeBreakout, get_strategy
from conftest import make_bars

MNQ = get_instrument("MNQ").with_costs(0.0)
NO_SLIP = CostModel(slippage_ticks=0)
FLAT = (104, 104.5, 103.5, 104)

BULL_FVG_DAY = [
    (100, 101, 99.5, 100.5),       # vela 1: máximo 101, mínimo 99.5
    (100.5, 104, 100.5, 103.75),   # vela 2: desplazamiento alcista
    (103.75, 105, 102.5, 104.5),   # vela 3: mínimo 102.5 > 101 -> FVG [101, 102.5]
    (104.5, 105, 103, 104),        # no vuelve al hueco
    (104, 104.5, 102, 102.25),     # retrocede y cruza 102.5 -> entrada
    (102.25, 110, 102, 109.75),    # alcanza objetivo 2R
    FLAT, FLAT,
]


def run(strategy, rows):
    return Backtester(make_bars(rows), MNQ, costs=NO_SLIP).run(strategy)


def test_first_bullish_fvg_limit_entry_stop_and_target():
    res = run(FirstFVG(filtro_tendencia="ninguno"), BULL_FVG_DAY)
    assert len(res.trades) == 1
    t = res.trades.iloc[0]
    assert t.lado == "largo" and t.precio_entrada == 102.5
    # stop bajo la vela 1 (99.5) con 2 ticks de margen = 99.0 -> riesgo 3.5 -> objetivo 2R = 109.5
    assert t.riesgo_usd == pytest.approx(3.5 * MNQ.point_value)
    assert t.motivo == "objetivo" and t.precio_salida == 109.5


def test_midpoint_entry_and_fvg_stop():
    rows = BULL_FVG_DAY[:4] + [(104, 104.5, 101.5, 102), (102, 110, 102, 109.75), FLAT, FLAT]
    res = run(FirstFVG(filtro_tendencia="ninguno", entrada="medio", stop="fvg", objetivo_r=1.0), rows)
    t = res.trades.iloc[0]
    assert t.precio_entrada == 101.75  # mitad de [101, 102.5]
    # stop bajo el hueco: 101 - 0.5 = 100.5 -> riesgo 1.25 -> objetivo 103.0 (se alcanza en la barra siguiente)
    assert t.precio_salida == 103.0


def test_long_only_skips_day_when_first_fvg_is_bearish():
    bear_first = [(110, 110.5, 109, 109.5), (109.5, 109.5, 106, 106.25), (106.25, 107.5, 105, 105.5)] + BULL_FVG_DAY
    res = run(FirstFVG(filtro_tendencia="ninguno", direccion="largos"), bear_first)
    assert res.trades.empty  # el primer FVG fue bajista: hoy no se opera


def test_trend_filter_open_blocks_countertrend():
    # FVG alcista, pero el precio sigue por debajo de la apertura del día
    rows = [(110, 110, 99, 100)] + BULL_FVG_DAY
    res = run(FirstFVG(filtro_tendencia="apertura"), rows)
    assert res.trades.empty


def test_orb_stop_entry_at_range_high():
    rows = [(100, 101, 99, 100.5), (100.5, 101.5, 100, 101), (101, 101.25, 100.25, 101),  # rango 99-101.5
            (101, 102.5, 100.75, 102.25), (102.25, 108, 102, 107.5)] + [FLAT] * 3
    strat = OpeningRangeBreakout(minutos_rango=3, rango_min_ticks=1, objetivo_r=2.0)
    t = run(strat, rows).trades.iloc[0]
    assert t.lado == "largo" and t.precio_entrada == 101.75   # máximo del rango + 1 tick
    # stop = mínimo del rango - 1 tick = 98.75 -> riesgo 3 -> objetivo 107.75
    assert t.motivo == "objetivo" and t.precio_salida == 107.75


def test_risk_based_sizing():
    strat = FirstFVG(filtro_tendencia="ninguno", riesgo_usd=50, contratos=1)
    t = run(strat, BULL_FVG_DAY).trades.iloc[0]
    assert t.contratos == 7  # 50 / (3.5 puntos * 2 USD) = 7.1


def test_unknown_param_rejected():
    with pytest.raises(ValueError):
        get_strategy("fvg", parametro_inventado=1)


@pytest.mark.parametrize("name,kw", [
    ("orb", {}),
    ("fvg", {"filtro_tendencia": "ninguno", "direccion": "ambas"}),
    ("fvg", {"filtro_tendencia": "flujo_fvg", "direccion": "ambas", "flujo_timeframe_min": 5, "solo_primero": False}),
    ("zona_ruido", {}),
    ("zona_ruido", {"stop_continuo": True}),
    ("ultima_media_hora", {}),
])
def test_no_edge_on_random_walk(name, kw):
    """Detector de lookahead: en un paseo aleatorio el resultado bruto medio debe ser ~0.
    Un motor o una estrategia que 'vea el futuro' daría un resultado claramente positivo."""
    bars = generate_synthetic_bars(days=1200, seed=3)
    res = Backtester(bars, MNQ, costs=NO_SLIP).run(get_strategy(name, **kw))
    g = res.trades["pnl_bruto"]
    se = g.std(ddof=1) / np.sqrt(len(g))
    assert len(g) > 500
    assert g.mean() < 3 * se, f"ventaja sospechosa en datos aleatorios: {g.mean():.2f} $ (se {se:.2f})"
