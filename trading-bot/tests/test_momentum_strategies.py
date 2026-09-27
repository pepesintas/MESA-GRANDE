import pandas as pd

from cajanegra.engine import Backtester, CostModel
from cajanegra.instruments import get_instrument
from cajanegra.strategies import LastHalfHourMomentum, NoiseAreaMomentum
from conftest import make_days

MNQ = get_instrument("MNQ").with_costs(0.0)
NO_SLIP = CostModel(slippage_ticks=0)


def run(days_rows, strat):
    bars = make_days(days_rows)
    return Backtester(bars, MNQ, costs=NO_SLIP).run(strat), bars


def et(ts):
    return pd.Timestamp(ts).tz_convert("America/New_York").strftime("%H:%M")


def test_noise_area_breakout_entry_and_dynamic_exit():
    # 3 días de calentamiento: a cada minuto el precio está un 0,5 % sobre la apertura -> σ = 0,005
    # (la estrategia no ve la última vela de cada sesión, por eso el día dura más que las revisiones)
    warm = [(100, 100.5, 100, 100.5)] + [(100.5, 100.5, 100.5, 100.5)] * 64
    test_day = (
        [(100.5, 100.6, 100.4, 100.5)] * 29
        + [(100.5, 102.1, 100.5, 102.0)]        # 09:59 -> cierra 102 > límite superior (101,00)
        + [(102, 102.2, 101.8, 102)] * 29        # entra a las 10:00 en la apertura (102)
        + [(102, 102, 99.9, 100)]                # 10:29 -> cierra 100 < max(límite, VWAP)
        + [(100, 100.1, 99.9, 100)] * 3          # sale a las 10:30 en la apertura (100)
    )
    res, _ = run([warm, warm, warm, test_day], NoiseAreaMomentum(dias_sigma=3))
    assert len(res.trades) == 1
    t = res.trades.iloc[0]
    assert t.lado == "largo" and t.precio_entrada == 102.0 and et(t.hora_entrada) == "10:00"
    assert t.motivo == "stop_dinamico" and t.precio_salida == 100.0 and et(t.hora_salida) == "10:30"


def test_noise_area_needs_warmup():
    warm = [(100, 100.5, 100, 100.5)] + [(100.5, 100.5, 100.5, 100.5)] * 59
    breakout = [(100.5, 100.6, 100.4, 100.5)] * 29 + [(100.5, 103, 100.5, 103)] * 5
    res, _ = run([warm, warm, breakout], NoiseAreaMomentum(dias_sigma=3))
    assert res.trades.empty  # solo hay 2 días de historia


def _last_half_hour_days():
    day1 = [(100, 100, 100, 100)] * 5                          # cierre de ayer = 100
    day2 = [(100, 100, 99, 99)] + [(99, 99, 99, 99)] * 29       # primera media hora: -1 %
    day2 += [(101, 101, 101, 101)] * 360                        # a las 15:30: +1 % sobre ayer
    return [day1, day2]


def test_last_half_hour_follows_rest_of_day_signal():
    res, _ = run(_last_half_hour_days(), LastHalfHourMomentum())
    t = res.trades.iloc[0]
    assert t.lado == "largo" and et(t.hora_entrada) == "15:30" and t.motivo == "cierre_sesion"


def test_last_half_hour_first_half_hour_signal_variant():
    res, _ = run(_last_half_hour_days(), LastHalfHourMomentum(senal="primera_media_hora"))
    assert res.trades.iloc[0].lado == "corto"


def test_last_half_hour_threshold_skips_small_moves():
    res, _ = run(_last_half_hour_days(), LastHalfHourMomentum(umbral_pct=2.0))
    assert res.trades.empty
