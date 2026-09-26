import pandas as pd
import pytest

from cajanegra.cli import main
from cajanegra.data import generate_synthetic_bars, load_bars
from cajanegra.engine import Backtester
from cajanegra.instruments import get_instrument
from cajanegra.research.walkforward import param_grid, walk_forward


def test_param_grid():
    assert param_grid({"a": [1, 2], "b": ["x"]}) == [{"a": 1, "b": "x"}, {"a": 2, "b": "x"}]
    assert param_grid({}) == [{}]


def test_walk_forward_windows_are_out_of_sample_and_contiguous():
    bars = generate_synthetic_bars(days=160, seed=5)
    bt = Backtester(bars, get_instrument("MNQ"))
    wf = walk_forward(bt, "orb", {"minutos_rango": [5, 15]}, is_sessions=60, oos_sessions=40, min_trades=5)
    w = wf.windows
    assert len(w) == 3
    for _, row in w.iterrows():
        assert row["oos_desde"] > row["is_hasta"]
    oos_dates = pd.to_datetime(wf.days["fecha"])
    assert oos_dates.is_monotonic_increasing and oos_dates.is_unique
    assert oos_dates.min() == bt.dates[60]


def test_loader_roundtrip_csv_naive_local_time(tmp_path):
    bars = generate_synthetic_bars(days=3, seed=1)
    local = bars.tz_convert("America/New_York").tz_localize(None)
    f = tmp_path / "bars.csv"
    local.to_csv(f)
    back = load_bars(f, tz_source="America/New_York")
    pd.testing.assert_frame_equal(back, bars, check_freq=False, check_index_type=False)
    assert (back.index == bars.index).all()


def test_loader_end_label_and_headerless(tmp_path):
    f = tmp_path / "raw.csv"
    f.write_text("2024-03-04 09:31:00,100,101,99,100.5,10\n2024-03-04 09:32:00,100.5,102,100,101,12\n")
    df = load_bars(f, tz_source="America/New_York", label="end", header=False)
    assert str(df.index[0].tz_convert("America/New_York").time()) == "09:30:00"
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_cli_backtest_with_rules_and_output(tmp_path, capsys):
    out = tmp_path / "res"
    main(["backtest", "--dias-sinteticos", "60", "--estrategia", "orb", "--param", "minutos_rango=5",
          "--reglas", "config/reglas/futuros_50k_trailing_cierre.toml", "--simulaciones", "50",
          "--horizonte", "30", "--max-perdida-dia", "500", "--salida", str(out)])
    text = capsys.readouterr().out
    assert "EVALUACIÓN DE FONDEO" in text and "VALOR ESPERADO POR CUENTA" in text
    for name in ("operaciones.csv", "dias.csv", "resumen.txt", "evaluacion.json"):
        assert (out / name).exists()


def test_cli_rejects_bad_param():
    with pytest.raises(SystemExit):
        main(["backtest", "--dias-sinteticos", "10", "--param", "no_existe=1"])
