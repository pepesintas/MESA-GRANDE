import pytest

from cajanegra.risk.prop_rules import AccountRules, Economics, PropAccount


def day(acc, pnl, lo=None, hi=None, dd=None, n=1):
    lo = min(pnl, 0.0) if lo is None else lo
    hi = max(pnl, 0.0) if hi is None else hi
    dd = max(hi - lo, 0.0) if dd is None else dd
    return acc.process_day(pnl, lo, hi, dd, n)


def test_static_drawdown_uses_intraday_low():
    acc = PropAccount(AccountRules(drawdown_maximo=1000, tipo_drawdown="estatico"))
    assert day(acc, 500, hi=600) == "activa"
    assert day(acc, 0, lo=-1400) == "activa"          # 50500 - 1400 = 49100 > 49000
    assert day(acc, -100, lo=-1500) == "suspendida"   # 49000 tocado
    assert acc.reason == "drawdown máximo"


def test_trailing_eod_ignores_intraday_peaks():
    acc = PropAccount(AccountRules(drawdown_maximo=2000, tipo_drawdown="trailing_cierre"))
    day(acc, 500, hi=1800)              # el pico intradía no mueve el suelo
    assert acc.floor == pytest.approx(48_500)
    day(acc, 1000)
    assert acc.floor == pytest.approx(49_500)
    assert day(acc, -1900) == "activa"  # 51500 - 1900 = 49600 > 49500
    assert day(acc, 0, lo=-100) == "suspendida"


def test_trailing_intraday_peak_then_retrace_fails():
    rules = AccountRules(drawdown_maximo=2000, tipo_drawdown="trailing_intradia")
    acc = PropAccount(rules)
    # sube +1500 y luego cae a -600: retroceso 2100 >= 2000 aunque el mínimo (-600) esté lejos del suelo inicial
    assert day(acc, -600, lo=-600, hi=1500, dd=2100) == "suspendida"

    acc2 = PropAccount(rules)
    # cae primero a -600 y luego sube a +1500: retroceso máximo 600, sobrevive
    assert day(acc2, 1500, lo=-600, hi=1500, dd=600) == "activa"
    assert acc2.floor == pytest.approx(49_500)


def test_drawdown_lock_stops_trailing():
    acc = PropAccount(AccountRules(drawdown_maximo=2000, tipo_drawdown="trailing_cierre", bloqueo_drawdown=100))
    day(acc, 2500)
    assert acc.floor == pytest.approx(50_100)  # 52500 - 2000 = 50500, bloqueado en 50100
    day(acc, 3000)
    assert acc.floor == pytest.approx(50_100)


def test_daily_loss_limit_suspend_day_caps_loss():
    rules = AccountRules(drawdown_maximo=3000, tipo_drawdown="estatico", perdida_diaria_max=1000)
    acc = PropAccount(rules)
    assert day(acc, -200, lo=-1200) == "activa"  # la firma liquidó en -1000
    assert acc.balance == pytest.approx(49_000)


def test_daily_loss_limit_eliminates():
    rules = AccountRules(drawdown_maximo=3000, tipo_drawdown="estatico", perdida_diaria_max=1000, accion_perdida_diaria="elimina")
    acc = PropAccount(rules)
    assert day(acc, -1000) == "suspendida"
    assert acc.reason == "pérdida diaria máxima"


def test_target_needs_min_days_and_consistency():
    rules = AccountRules(objetivo_beneficio=3000, drawdown_maximo=2000, dias_minimos=3, consistencia_max_dia=0.5)
    acc = PropAccount(rules)
    assert day(acc, 3200) == "activa"  # objetivo en 1 día pero faltan días y consistencia
    assert day(acc, 100) == "activa"
    assert day(acc, 100) == "activa"   # 3400 total, mejor día 3200 > 50%
    assert day(acc, 3000) == "aprobada"  # 6400 total, mejor día 3200 <= 3200


def test_no_trade_days_do_not_count_but_time_limit_does():
    rules = AccountRules(objetivo_beneficio=1000, dias_minimos=2, dias_maximos=3)
    acc = PropAccount(rules)
    assert day(acc, 0, n=0) == "activa"
    assert acc.days_traded == 0
    assert day(acc, 1500) == "activa"
    assert day(acc, 0, n=0) == "caducada"


def test_winning_days_rule():
    rules = AccountRules(objetivo_beneficio=500, dias_ganadores_minimos=3, ganancia_minima_dia=150)
    acc = PropAccount(rules)
    day(acc, 600)
    day(acc, 100)  # no cuenta como ganador
    assert acc.status == "activa"
    day(acc, 200)
    assert day(acc, 150) == "aprobada"


def test_economics():
    eco = Economics(coste_evaluacion=50, cobro_evaluacion="mensual", reparto=0.9, retiro_maximo=2000, colchon_retiro=100)
    assert eco.evaluation_cost(10) == 50
    assert eco.evaluation_cost(22) == 100
    assert eco.payout(1100) == pytest.approx(900)
    assert eco.payout(5000) == pytest.approx(1800)


def test_withdrawable_fraction_cap_and_minimum():
    eco = Economics(retiro_fraccion=0.5, retiro_maximo=3000, retiro_minimo=500, reparto=0.9)
    assert eco.withdrawable(800) == 0.0          # 400 < mínimo
    assert eco.withdrawable(1200) == pytest.approx(600)
    assert eco.withdrawable(10_000) == pytest.approx(3000)
    assert eco.payout(1200) == pytest.approx(540)


def test_payout_cycles_reset_counters():
    rules = AccountRules(objetivo_beneficio=0.01, objetivo_ciclo=0.01, dias_ganadores_minimos=2, ganancia_minima_dia=150)
    acc = PropAccount(rules)
    day(acc, 200)
    assert day(acc, 200) == "aprobada"
    acc.withdraw(200)
    assert acc.status == "activa" and acc.profit == pytest.approx(200)
    assert day(acc, 200) == "activa"   # el ciclo nuevo vuelve a pedir 2 días ganadores
    assert day(acc, 160) == "aprobada"
