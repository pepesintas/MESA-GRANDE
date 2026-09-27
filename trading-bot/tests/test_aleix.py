"""El sistema de 3 pasos de Aleix con velas construidas a mano (15 min simulados con velas de 3 min)."""

import pandas as pd

from cajanegra.engine import Backtester, CostModel
from cajanegra.instruments import get_instrument
from cajanegra.strategies import AleixIFVG
from conftest import make_bars, make_days

MNQ = get_instrument("MNQ").with_costs(0.0)


def split(o, h, l, c):  # noqa: E741
    """Una vela 'grande' en 3 velas de 1 minuto con el mismo OHLC."""
    if c < o:
        return [(o, h, o, h), (h, h, l, l), (l, max(l, c), min(l, c), c)]
    return [(o, o, l, l), (l, h, l, h), (h, h, min(h, c), c)]


def sell_day(c4_close=195.0, a_low=189.3):
    htf = [
        (200, 201, 199, 199.5),
        (199.5, 199.5, 195, 195.5),
        (195.5, 197, 194, 194.5),          # FVG bajista 1: [197, 199]
        (194.5, 197.5 if c4_close < 199 else 199.8, 194, c4_close),  # lo respeta (o no) -> dirección
        (195, 195.5, 191, 191.5),
        (191.5, 192, 189, 189.5),          # FVG bajista 2 (zona de reacción): [192, 194]
    ]
    rows = [bar for spec in htf for bar in split(*spec)]
    rows += [
        (189.5, 190.5, a_low, 190.3),      # a: retroceso
        (190.3, 192.6, 190.2, 192.4),      # b: entra en la zona -> se activa
        (192.4, 193.0, 192.1, 192.8),      # c: FVG alcista de 1 min [190.5, 192.1] (en contra)
        (192.8, 192.9, 191.5, 191.8),      # d
        (191.8, 191.9, 189.9, 190.0),      # e: cierra por debajo de 190.5 -> IFVG -> vender
        (190.0, 190.2, 186.0, 186.5),      # f: entra en la apertura (190)
        (186.5, 186.6, 184.5, 184.8),      # g: objetivo 1,5R
    ] + [(184.8, 185, 184.6, 184.8)] * 4
    return rows


def mirror(rows):
    return [(400 - o, 400 - l, 400 - h, 400 - c) for o, h, l, c in rows]


def run(rows, prev=None, **kw):
    params = dict(htf_min=3, exigir_dol=False, objetivo="r") | kw
    bars = make_days([prev, rows]) if prev else make_bars(rows)
    return Backtester(bars, MNQ, costs=CostModel(slippage_ticks=0)).run(AleixIFVG(**params))


def et(ts):
    return pd.Timestamp(ts).tz_convert("America/New_York").strftime("%H:%M")


def test_sell_after_bias_zone_and_ifvg():
    res = run(sell_day())
    assert len(res.trades) == 1
    t = res.trades.iloc[0]
    assert t.lado == "corto" and t.precio_entrada == 190.0 and et(t.hora_entrada) == "09:53"
    # stop sobre el extremo del retroceso (193) + 2 ticks = 193,5 -> riesgo 3,5 -> objetivo 1,5R = 184,75
    assert t.riesgo_usd == 3.5 * MNQ.point_value
    assert t.motivo == "objetivo" and t.precio_salida == 184.75


def test_buy_is_the_mirror_image():
    t = run(mirror(sell_day())).trades.iloc[0]
    assert t.lado == "largo" and t.precio_entrada == 210.0 and t.precio_salida == 215.25


def test_target_at_next_structural_low():
    t = run(sell_day(), objetivo="dol").trades.iloc[0]
    assert t.precio_salida == 189.0   # mínimo estructural de las velas de 15 min


def test_needs_room_to_the_draw_on_liquidity():
    assert run(sell_day(), exigir_dol=True).trades.empty          # el siguiente mínimo (189) está a menos de 1,5R
    prev = [(182, 183, 180, 181)] * 5                              # ayer marcó 180: objetivo lejano
    res = run(sell_day(a_low=188.8), prev=prev, exigir_dol=True)
    assert len(res.trades) == 1 and res.trades.iloc[0].precio_salida == 184.75


def test_no_trade_when_bearish_fvgs_are_not_respected():
    assert run(sell_day(c4_close=199.5)).trades.empty  # el FVG bajista se invalida: dirección alcista


def test_default_takes_profit_at_the_draw_on_liquidity_with_minimum_ratio():
    prev = [(182, 183, 180, 181)] * 5
    day = sell_day(a_low=188.8)[:-4] + [(184.8, 185, 179.5, 180.2), (180.2, 180.5, 180, 180.3)]
    bars = make_days([prev, day])
    res = Backtester(bars, MNQ, costs=CostModel(slippage_ticks=0)).run(AleixIFVG(htf_min=3))
    t = res.trades.iloc[0]
    # objetivo = mínimo de ayer (siguiente punto estructural), ratio 10 / 3,5 ≈ 2,9 ≥ 1,5
    assert t.motivo == "objetivo" and t.precio_salida == 180.0
