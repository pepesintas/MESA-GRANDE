import pytest

from cajanegra.engine import Backtester, CostModel, Order, OrderType, Side
from cajanegra.instruments import get_instrument
from cajanegra.news import NewsCalendar, NewsEvent
from cajanegra.risk import DailyRiskGuard
from conftest import Scripted, make_bars, make_days

MNQ = get_instrument("MNQ").with_costs(0.0)  # sin comisiones para cuadrar precios a mano
NO_SLIP = CostModel(slippage_ticks=0)


def run(rows, plan=None, exits=(), moves=None, costs=NO_SLIP, inst=MNQ, **kw):
    bt = Backtester(make_bars(rows), inst, costs=costs, **kw)
    strat = Scripted(plan=plan or {}, exits=exits, moves=moves or {})
    return bt.run(strat), strat


FLAT = (100, 100.5, 99.5, 100)


def test_market_order_fills_next_open_with_slippage():
    rows = [FLAT, (101, 102, 100.5, 101.5), FLAT, FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG)]}, costs=CostModel(slippage_ticks=2))
    t = res.trades.iloc[0]
    assert t.precio_entrada == 101 + 0.5  # apertura de la barra 1 + 2 ticks
    assert t.motivo == "cierre_sesion"
    assert t.precio_salida == 100 - 0.5  # cierre última barra - 2 ticks


def test_strategy_never_sees_future_bars():
    rows = [FLAT] * 5
    _, strat = run(rows)
    assert strat.seen_lengths == [(0, 1), (1, 2), (2, 3), (3, 4)]  # la última barra cierra la sesión


def test_stop_entry_triggers_only_when_touched_and_gaps_fill_at_open():
    rows = [FLAT, (100, 100.75, 99.5, 100.5), (102, 103, 101.5, 102.5), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG, OrderType.STOP, price=101)]})
    t = res.trades.iloc[0]
    assert t.hora_entrada == make_bars(rows).index[2]  # la barra 1 no llega a 101
    assert t.precio_entrada == 102  # abrió por encima del stop: se ejecuta en la apertura


def test_limit_entry_requires_trade_through():
    rows = [FLAT, (100.5, 101, 100, 100.5), (100.5, 101, 99.75, 100), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG, OrderType.LIMIT, price=100)]})
    t = res.trades.iloc[0]
    assert t.hora_entrada == make_bars(rows).index[2]  # en la barra 1 solo tocó 100
    assert t.precio_entrada == 100


def test_stop_wins_when_stop_and_target_in_same_bar():
    rows = [FLAT, (100, 100.25, 99.75, 100), (100, 105, 95, 100), FLAT]
    order = Order(Side.LONG, stop_loss=98, take_profit=102)
    res, _ = run(rows, plan={0: [order]})
    t = res.trades.iloc[0]
    assert t.motivo == "stop" and t.precio_salida == 98


def test_target_not_allowed_on_intrabar_entry_bar_but_stop_is():
    # entrada stop en 101 dentro de la barra 1, cuyo máximo alcanza también el objetivo
    rows = [FLAT, (100, 104, 99.75, 103), (103, 103.5, 102.5, 103), FLAT]
    order = Order(Side.LONG, OrderType.STOP, price=101, stop_loss=99, take_profit=103)
    res, _ = run(rows, plan={0: [order]})
    t = res.trades.iloc[0]
    assert t.motivo == "objetivo"
    assert t.hora_salida == make_bars(rows).index[2]  # no en la barra de entrada
    assert t.precio_salida == 103  # abrió justo en el objetivo

    rows_stop = [FLAT, (100, 101.5, 98.5, 99), FLAT, FLAT]
    res2, _ = run(rows_stop, plan={0: [order]})
    t2 = res2.trades.iloc[0]
    assert t2.motivo == "stop" and t2.hora_salida == make_bars(rows_stop).index[1]


def test_short_mirror_and_gap_through_stop():
    rows = [FLAT, (100, 100.25, 99.5, 99.75), (103, 104, 102.5, 103), FLAT]
    order = Order(Side.SHORT, stop_loss=101, take_profit=95)
    res, _ = run(rows, plan={0: [order]})
    t = res.trades.iloc[0]
    assert t.lado == "corto" and t.precio_entrada == 100
    assert t.motivo == "stop" and t.precio_salida == 103  # hueco por encima del stop
    assert t.pnl_bruto == pytest.approx(-3 * MNQ.point_value)


def test_oco_only_one_entry_and_nearest_trigger_wins():
    rows = [FLAT, (100, 102, 98, 100), FLAT, FLAT]
    plan = {0: [Order(Side.SHORT, OrderType.STOP, price=99.5), Order(Side.LONG, OrderType.STOP, price=101)]}
    res, _ = run(rows, plan=plan)
    assert len(res.trades) == 1
    assert res.trades.iloc[0].lado == "corto"  # 99.5 está más cerca de la apertura (100) que 101


def test_commissions_and_day_pnl_consistency():
    inst = get_instrument("MNQ")  # 0.75 por lado
    rows = [FLAT, (100, 101, 99.5, 100.5), (100.5, 101, 100, 101), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG, contracts=2)]}, inst=inst)
    t = res.trades.iloc[0]
    assert t.comisiones == pytest.approx(0.75 * 2 * 2)
    assert t.pnl_neto == pytest.approx(t.pnl_bruto - 3.0)
    assert res.days.pnl.sum() == pytest.approx(res.trades.pnl_neto.sum())


def test_intraday_equity_extremes_use_bar_extremes():
    rows = [FLAT, (100, 100.5, 99, 100), (100, 104, 99.5, 103), (103, 103, 101, 102), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG)]})
    day = res.days.iloc[0]
    pv = MNQ.point_value
    assert day.min_equity == pytest.approx((99 - 100) * pv)
    assert day.max_equity == pytest.approx((104 - 100) * pv)
    assert day.pnl == pytest.approx((100 - 100) * pv)  # cierre de sesión en la última barra (100)


def test_manual_exit_and_move_stop():
    rows = [FLAT, (100, 101, 99.75, 101), (101, 102, 100.75, 101.5), (101.5, 101.5, 100.5, 101), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG, stop_loss=98)]}, moves={2: 101})
    t = res.trades.iloc[0]
    assert t.motivo == "stop" and t.precio_salida == 101  # stop movido a 101

    res2, _ = run(rows, plan={0: [Order(Side.LONG)]}, exits=(1,))
    assert res2.trades.iloc[0].motivo == "manual" and res2.trades.iloc[0].precio_salida == 101


def test_daily_loss_guard_acts_as_stop_and_blocks_new_entries():
    pv = MNQ.point_value  # 2 USD/punto
    rows = [FLAT, (100, 100.25, 99.75, 100), (100, 100, 90, 91), (91, 91, 90, 90.5), FLAT]
    guard = DailyRiskGuard(max_daily_loss=10 * pv)  # 10 puntos
    plan = {0: [Order(Side.LONG)], 2: [Order(Side.LONG)]}
    res, _ = run(rows, plan=plan, guard=guard)
    assert len(res.trades) == 1
    t = res.trades.iloc[0]
    assert t.motivo == "limite_diario" and t.precio_salida == 90
    assert res.days.iloc[0].pnl == pytest.approx(-10 * pv)


def test_max_trades_guard():
    rows = [FLAT] * 8
    plan = {k: [Order(Side.LONG)] for k in range(0, 6, 2)}
    exits = (1, 3, 5)
    res, _ = run(rows, plan=plan, exits=exits, guard=DailyRiskGuard(max_trades=2))
    assert len(res.trades) == 2


def test_order_expiry_and_flat_time():
    rows = [FLAT] * 3 + [(100, 103, 99.5, 102)] + [FLAT] * 3
    order = Order(Side.LONG, OrderType.STOP, price=102, expires_min=9 * 60 + 33)
    res, _ = run(rows, plan={0: [order]})
    assert res.trades.empty  # caducó a las 09:33, justo antes de la ruptura

    res2, _ = run(rows, plan={0: [Order(Side.LONG)]}, flat_time="09:33")
    t = res2.trades.iloc[0]
    assert t.motivo == "cierre_sesion" and t.precio_salida == 102


def test_news_blackout_blocks_entries_and_flattens():
    rows = [FLAT] * 3 + [(100, 103, 99.5, 102)] + [FLAT] * 4
    bars = make_bars(rows)
    ev = NewsCalendar([NewsEvent(bars.index[4], "USD", "alto", "CPI")])
    bt = Backtester(bars, MNQ, costs=NO_SLIP, news=ev, news_before_min=1, news_after_min=2)
    res = bt.run(Scripted(plan={1: [Order(Side.LONG, OrderType.STOP, price=102)]}))
    assert res.trades.empty  # la orden se cancela al entrar en la ventana de la noticia

    bt2 = Backtester(bars, MNQ, costs=NO_SLIP, news=ev, news_before_min=1, news_after_min=2, flatten_before_news=True)
    res2 = bt2.run(Scripted(plan={0: [Order(Side.LONG)]}))
    t = res2.trades.iloc[0]
    assert t.motivo == "noticias" and t.hora_salida == bars.index[2]


def test_multiple_days_reset_state():
    day = [FLAT, (100, 101, 99.5, 101), FLAT]
    res, _ = run_days([day, day, day], plan={0: [Order(Side.LONG)]})
    assert len(res.trades) == 3 and len(res.days) == 3


def run_days(days_rows, plan):
    bt = Backtester(make_days(days_rows), MNQ, costs=NO_SLIP)
    return bt.run(Scripted(plan=plan)), None


def test_intraday_drawdown_from_running_peak():
    # sube 4 puntos (pico) y luego cae hasta -1: retroceso desde el pico = 5 puntos
    rows = [FLAT, (100, 100.5, 99.75, 100.5), (100.5, 104, 100.5, 103.5), (103.5, 103.5, 99, 99.5), FLAT]
    res, _ = run(rows, plan={0: [Order(Side.LONG)]})
    day = res.days.iloc[0]
    pv = MNQ.point_value
    assert day.max_equity == pytest.approx(4 * pv)
    assert day.min_equity == pytest.approx(-1 * pv)
    assert day.dd_intradia == pytest.approx(5 * pv)
