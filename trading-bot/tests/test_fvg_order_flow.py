import pandas as pd

from cajanegra.engine import Backtester, CostModel
from cajanegra.instruments import get_instrument
from cajanegra.strategies import FirstFVG
from cajanegra.strategies.fvg import FvgOrderFlow
from conftest import make_bars

MNQ = get_instrument("MNQ").with_costs(0.0)
BULL = [(100, 101, 99.5, 100.5), (100.5, 104, 100.5, 103.75), (103.75, 105, 102.5, 104.5)]  # FVG [101, 102.5]
BEAR = [(110, 110.5, 109, 109.5), (109.5, 109.5, 106, 106.25), (106.25, 107.5, 105, 105.5)]  # FVG [107.5, 109]


def flow_after(candles, need=1):
    f = FvgOrderFlow(min_gap=1.0, events_needed=need)
    f.new_day()
    for c in candles:
        f.on_candle(*c)
    return f


def test_bullish_fvg_respected_gives_bullish_bias():
    f = flow_after(BULL + [(104.5, 104.6, 102.0, 104.0)])  # vuelve al hueco y cierra por encima del fondo
    assert list(f.events) == [1] and f.bias == 1 and not f.fvgs


def test_bullish_fvg_disrespected_gives_bearish_bias():
    f = flow_after(BULL + [(104.5, 104.6, 100.0, 100.75)])  # cierra por debajo del fondo (101)
    assert f.bias == -1


def test_bearish_fvg_respected_and_disrespected():
    assert flow_after(BEAR + [(105.5, 108.0, 105.4, 106.0)]).bias == -1   # vuelve al hueco y lo respeta
    assert flow_after(BEAR + [(105.5, 110.0, 105.4, 109.5)]).bias == 1    # cierra por encima del techo


def test_needs_agreeing_events_and_fvgs_expire():
    f = flow_after(BULL + [(104.5, 104.6, 102.0, 104.0)], need=2)
    assert f.bias == 0  # un solo evento no basta
    g = FvgOrderFlow(min_gap=1.0, max_age_days=1)
    g.new_day()
    for c in BULL:
        g.on_candle(*c)
    assert len(g.fvgs) == 1
    g.new_day()
    g.new_day()
    assert g.fvgs == []


def _day(third_close_low, third_close):
    flat = (104, 104.5, 103.5, 104)
    rows = BULL + [(104.5, 104.6, third_close_low, third_close)] + [flat] * 6
    rows += [(104, 105, 103.8, 104.5), (104.5, 108, 104.5, 107.75), (107.75, 109, 106.5, 108.5),  # FVG de entrada [105, 106.5]
             (108.5, 108.6, 106.0, 106.25), (106.25, 113, 106, 112.75), flat, flat]
    return rows


def run(rows):
    strat = FirstFVG(filtro_tendencia="flujo_fvg", flujo_timeframe_min=1, hora_inicio="09:40")
    return Backtester(make_bars(rows), MNQ, costs=CostModel(slippage_ticks=0)).run(strat)


def test_strategy_trades_long_when_order_flow_is_bullish():
    res = run(_day(102.0, 104.0))
    assert len(res.trades) == 1
    t = res.trades.iloc[0]
    assert t.lado == "largo" and t.precio_entrada == 106.5 and t.motivo == "objetivo"
    assert pd.Timestamp(t.hora_entrada).tz_convert("America/New_York").strftime("%H:%M") == "09:43"


def test_strategy_skips_long_when_order_flow_is_bearish():
    assert run(_day(100.0, 100.75)).trades.empty


def test_impulse_mode_waits_for_price_to_leave_the_gap():
    touch_only = BULL + [(104.5, 104.6, 102.0, 102.3)]    # toca y cierra dentro del hueco
    assert flow_after(touch_only).bias == 0                # modo impulso: aún no está respetado
    f = FvgOrderFlow(min_gap=1.0, mode="toque")
    f.new_day()
    for c in touch_only:
        f.on_candle(*c)
    assert f.bias == 1                                     # modo toque: ya cuenta
    g = flow_after(touch_only + [(102.3, 104.0, 102.2, 103.5)])  # después cierra por encima: impulso
    assert g.bias == 1
