"""Línea de comandos:  python -m cajanegra <comando> [opciones]   (usa -h para ver la ayuda)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import SESSIONS, generate_synthetic_bars, load_bars
from .engine import Backtester, CostModel
from .instruments import INSTRUMENTS, get_instrument
from .news import NewsCalendar
from .report import backtest_report, evaluation_report, walkforward_report
from .research.evaluation import block_bootstrap, rolling_starts, summarize
from .research.walkforward import walk_forward
from .risk import DailyRiskGuard
from .risk.prop_rules import FirmConfig
from .strategies import STRATEGIES, get_strategy

ROOT = Path(__file__).resolve().parents[1]
MICROS = {"MNQ", "MES", "MYM", "M2K"}

AVISO_SINTETICO = (
    "⚠ DATOS SINTÉTICOS (paseo aleatorio). Estos números NO dicen nada sobre la estrategia:\n"
    "  en datos aleatorios cualquier estrategia debe perder aprox. las comisiones. Sirve para\n"
    "  ver el flujo completo. Para conclusiones reales hacen falta años de datos reales."
)


def _value(v: str):
    low = v.lower()
    if low in ("true", "si", "sí"):
        return True
    if low in ("false", "no"):
        return False
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def _params(items: list[str] | None) -> dict:
    out = {}
    for it in items or []:
        if "=" not in it:
            raise SystemExit(f"Parámetro mal formado: {it} (usa nombre=valor)")
        k, v = it.split("=", 1)
        out[k.strip()] = _value(v.strip())
    return out


def _grid(items: list[str] | None) -> dict:
    return {k: [_value(x) for x in str(v).split(",")] for k, v in ((i.split("=", 1)) for i in items or [])}


def _load(args):
    if args.datos:
        bars = load_bars(args.datos, tz_source=args.tz_datos, label=args.etiqueta, header=not args.sin_cabecera)
        return bars, False
    print(AVISO_SINTETICO, "\n")
    return generate_synthetic_bars(days=args.dias_sinteticos, seed=args.semilla), True


def _firm(args) -> FirmConfig | None:
    return FirmConfig.from_toml(args.reglas) if args.reglas else None


def _backtester(args, bars, firm: FirmConfig | None) -> Backtester:
    inst = get_instrument(args.instrumento).with_costs(args.comision)
    cap = args.max_contratos
    if cap is None and firm is not None and firm.max_contratos:
        cap = firm.max_contratos * (10 if inst.symbol in MICROS else 1)
    guard = DailyRiskGuard(
        max_trades=args.max_operaciones,
        max_daily_loss=args.max_perdida_dia,
        daily_profit_target=args.objetivo_dia,
        max_consecutive_losses=args.max_perdidas_seguidas,
        max_contracts=cap,
    )
    news = None
    if args.noticias:
        path = Path(args.noticias)
        news = NewsCalendar.from_forexfactory_json(path) if path.suffix == ".json" else NewsCalendar.from_csv(path)
        news = news.filter(currencies=args.monedas_noticias.split(","), impacts=("alto",))
    return Backtester(
        bars, inst, session=SESSIONS[args.sesion],
        costs=CostModel(slippage_ticks=args.slippage),
        guard=guard, news=news, news_before_min=args.noticias_antes, news_after_min=args.noticias_despues,
        flatten_before_news=args.cerrar_antes_noticias, flat_time=args.hora_cierre,
    )


def _evaluate(days, firm: FirmConfig, args) -> tuple[dict, dict]:
    roll = summarize(rolling_starts(days, firm, horizon=args.horizonte))
    boot = summarize(block_bootstrap(days, firm, n_sims=args.simulaciones, horizon=args.horizonte, seed=args.semilla))
    return roll, boot


def _save(outdir: str | None, res, report: str, extra: dict | None = None):
    if not outdir:
        return
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    res.trades.to_csv(out / "operaciones.csv", index=False)
    res.days.to_csv(out / "dias.csv", index=False)
    (out / "resumen.txt").write_text(report, encoding="utf-8")
    if extra:
        (out / "evaluacion.json").write_text(json.dumps(extra, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nResultados guardados en {out}/")


def cmd_backtest(args):
    bars, _ = _load(args)
    firm = _firm(args)
    bt = _backtester(args, bars, firm)
    strat = get_strategy(args.estrategia, **_params(args.param))
    res = bt.run(strat, args.desde, args.hasta)
    report = backtest_report(res)
    extra = None
    if firm is not None:
        roll, boot = _evaluate(res.days, firm, args)
        report += "\n\n" + evaluation_report(firm, roll, boot, args.horizonte)
        extra = {"arranques_historicos": roll, "bootstrap": boot}
    print(report)
    _save(args.salida, res, report, extra)


def cmd_walkforward(args):
    bars, _ = _load(args)
    firm = _firm(args)
    bt = _backtester(args, bars, firm)
    grid = _grid(args.grid)
    n = 1
    for v in grid.values():
        n *= len(v)
    print(f"Probando {n} combinaciones por ventana...\n")
    wf = walk_forward(
        bt, args.estrategia, grid, fixed=_params(args.param), is_sessions=args.sesiones_is,
        oos_sessions=args.sesiones_oos, metric=args.metrica, min_trades=args.min_operaciones,
        progress=lambda r: print(f"  ventana OOS {r['oos_desde']}→{r['oos_hasta']}: {r['parametros']}"),
    )
    report = "\n" + walkforward_report(wf.windows)
    if firm is not None:
        roll, boot = _evaluate(wf.days, firm, args)
        report += "\n\nSolo con los tramos fuera de muestra:\n" + evaluation_report(firm, roll, boot, args.horizonte)
    print(report)
    if args.salida:
        out = Path(args.salida)
        out.mkdir(parents=True, exist_ok=True)
        wf.windows.to_csv(out / "ventanas.csv", index=False)
        wf.trades.to_csv(out / "operaciones_oos.csv", index=False)
        wf.days.to_csv(out / "dias_oos.csv", index=False)
        (out / "resumen.txt").write_text(report, encoding="utf-8")
        print(f"\nResultados guardados en {out}/")


def cmd_demo(args):
    print(AVISO_SINTETICO, "\n")
    bars = generate_synthetic_bars(days=args.dias_sinteticos, seed=args.semilla)
    firm = FirmConfig.from_toml(ROOT / "config/reglas/futuros_50k_trailing_cierre.toml")
    inst = get_instrument("MNQ")
    bt = Backtester(bars, inst, guard=DailyRiskGuard(max_daily_loss=600, max_trades=2, max_contracts=50))
    strat = get_strategy("fvg", riesgo_usd=300, max_contratos=50)
    res = bt.run(strat)
    print(backtest_report(res))
    print()
    roll = summarize(rolling_starts(res.days, firm, horizon=args.horizonte))
    boot = summarize(block_bootstrap(res.days, firm, n_sims=500, horizon=args.horizonte, seed=args.semilla))
    print(evaluation_report(firm, roll, boot, args.horizonte))


def cmd_sintetico(args):
    bars = generate_synthetic_bars(days=args.dias_sinteticos, seed=args.semilla, drift_per_day=args.deriva)
    out = Path(args.salida)
    out.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(out) if out.suffix in (".parquet", ".pq") else bars.to_csv(out)
    print(f"Guardadas {len(bars):,} barras sintéticas en {out}")


def cmd_descargar(args):
    from .data.databento_fetch import download

    download(args.simbolo, args.desde, args.hasta, args.salida, only_cost=args.solo_coste)


def cmd_comparar_firmas(args):
    import glob

    from .research.firm_compare import best_by_firm, compare_firms
    from .report import money, pct

    files = args.reglas or sorted(glob.glob(str(ROOT / "config/reglas/firmas/*.toml")))
    firms = {}
    for f in files:
        c = FirmConfig.from_toml(f)
        firms[c.nombre] = c
    edges = [float(x) for x in args.esperanza.split(",")]
    risks = [float(x) for x in args.riesgo.split(",")]
    print(f"Comparando {len(firms)} firmas · ventajas {edges} R · riesgos {risks} $ · "
          f"{args.simulaciones} trayectorias · {args.horizonte} sesiones por fase\n")
    if args.riesgo_fondeada or args.payoff_fondeada:
        print(f"Fondeada operada aparte: riesgo {args.riesgo_fondeada or 'igual'} $, "
              f"payoff {args.payoff_fondeada or args.payoff} R\n")
    table = compare_firms(firms, edges, risks, n_paths=args.simulaciones, horizon=args.horizonte,
                          payoff_r=args.payoff, prob_operar=args.prob_operar, seed=args.semilla,
                          risk_funded=args.riesgo_fondeada, payoff_funded=args.payoff_fondeada)
    best = best_by_firm(table)
    for e, grp in best.groupby("esperanza_r", sort=True):
        print(f"Ventaja {e:+.2f} R por operación (mejor riesgo para cada firma):")
        for _, r in grp.iterrows():
            print(f"  {r['firma']:32s} riesgo {money(r['riesgo_usd']):>7}  aprueba {pct(r['p_aprobar']):>6}  "
                  f"cobra {pct(r['p_cobrar']):>6}  coste {money(r['coste_medio']):>6}  "
                  f"VALOR ESPERADO {money(r['valor_esperado']):>8}")
        print()
    if args.salida:
        out = Path(args.salida)
        out.mkdir(parents=True, exist_ok=True)
        table.to_csv(out / "comparativa_firmas.csv", index=False)
        best.to_csv(out / "mejor_riesgo_por_firma.csv", index=False)
        print(f"Tablas guardadas en {out}/")


def cmd_estrategias(args):
    for name, cls in STRATEGIES.items():
        print(f"{name}: {cls.description}")
        for k, v in cls.defaults.items():
            print(f"    {k} = {v}")
        print()
    print("Instrumentos:", ", ".join(f"{k} ({v.description})" for k, v in INSTRUMENTS.items()))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cajanegra", description="Laboratorio de estrategias intradía para cuentas de fondeo")
    sub = p.add_subparsers(dest="cmd", required=True)

    def data_opts(sp):
        g = sp.add_argument_group("datos")
        g.add_argument("--datos", help="CSV/Parquet de barras de 1 minuto (sin esto: datos sintéticos)")
        g.add_argument("--tz-datos", default="UTC", help="zona horaria de los timestamps si no la traen (p. ej. America/New_York)")
        g.add_argument("--etiqueta", default="start", choices=["start", "end"], help="el timestamp marca inicio o fin de barra")
        g.add_argument("--sin-cabecera", action="store_true")
        g.add_argument("--dias-sinteticos", type=int, default=750)
        g.add_argument("--semilla", type=int, default=42)

    def run_opts(sp):
        g = sp.add_argument_group("simulación")
        g.add_argument("--instrumento", default="MNQ", choices=sorted(INSTRUMENTS))
        g.add_argument("--estrategia", default="fvg", choices=sorted(STRATEGIES))
        g.add_argument("--param", action="append", help="parámetro de la estrategia nombre=valor (repetible)")
        g.add_argument("--sesion", default="nueva_york", choices=sorted(SESSIONS))
        g.add_argument("--desde")
        g.add_argument("--hasta")
        g.add_argument("--comision", type=float, help="USD por contrato y lado (por defecto la del instrumento)")
        g.add_argument("--slippage", type=float, default=1.0, help="ticks de deslizamiento por lado")
        g.add_argument("--hora-cierre", help="cerrar todo a esta hora (HH:MM)")
        r = sp.add_argument_group("riesgo diario")
        r.add_argument("--max-perdida-dia", type=float, help="USD: corta la posición y para el día")
        r.add_argument("--max-operaciones", type=int)
        r.add_argument("--objetivo-dia", type=float, help="USD: al alcanzarlo, no más entradas")
        r.add_argument("--max-perdidas-seguidas", type=int)
        r.add_argument("--max-contratos", type=int)
        n = sp.add_argument_group("noticias")
        n.add_argument("--noticias", help="calendario CSV (fecha_hora,moneda,impacto,evento) o JSON de Forex Factory")
        n.add_argument("--monedas-noticias", default="USD")
        n.add_argument("--noticias-antes", type=int, default=5)
        n.add_argument("--noticias-despues", type=int, default=5)
        n.add_argument("--cerrar-antes-noticias", action="store_true")
        f = sp.add_argument_group("fondeo")
        f.add_argument("--reglas", help="fichero TOML de reglas de la firma (config/reglas/...)")
        f.add_argument("--horizonte", type=int, default=120, help="sesiones máximas por fase en la simulación")
        f.add_argument("--simulaciones", type=int, default=2000)
        sp.add_argument("--salida", help="carpeta donde guardar operaciones, días y resumen")

    sp = sub.add_parser("backtest", help="simular una estrategia y (opcional) la evaluación de una firma")
    data_opts(sp)
    run_opts(sp)
    sp.set_defaults(func=cmd_backtest)

    sp = sub.add_parser("walkforward", help="optimizar en el pasado y validar fuera de muestra")
    data_opts(sp)
    run_opts(sp)
    sp.add_argument("--grid", action="append", help="rejilla nombre=v1,v2,v3 (repetible)")
    sp.add_argument("--sesiones-is", type=int, default=500)
    sp.add_argument("--sesiones-oos", type=int, default=125)
    sp.add_argument("--metrica", default="beneficio_dd", choices=["beneficio_dd", "sharpe", "beneficio"])
    sp.add_argument("--min-operaciones", type=int, default=30)
    sp.set_defaults(func=cmd_walkforward)

    sp = sub.add_parser("demo", help="recorrido completo con datos sintéticos")
    sp.add_argument("--dias-sinteticos", type=int, default=750)
    sp.add_argument("--semilla", type=int, default=42)
    sp.add_argument("--horizonte", type=int, default=120)
    sp.set_defaults(func=cmd_demo)

    sp = sub.add_parser("sintetico", help="generar un fichero de datos sintéticos")
    sp.add_argument("--dias-sinteticos", type=int, default=750)
    sp.add_argument("--semilla", type=int, default=42)
    sp.add_argument("--deriva", type=float, default=0.0, help="deriva diaria (p. ej. 0.0005 = alcista)")
    sp.add_argument("--salida", default="data/sintetico.parquet")
    sp.set_defaults(func=cmd_sintetico)

    sp = sub.add_parser("descargar", help="descargar barras de 1 minuto de Databento (de pago)")
    sp.add_argument("--simbolo", default="NQ.v.0")
    sp.add_argument("--desde", required=True)
    sp.add_argument("--hasta", required=True)
    sp.add_argument("--salida", default="data/nq_1m.parquet")
    sp.add_argument("--solo-coste", action="store_true", help="solo consultar lo que costaría")
    sp.set_defaults(func=cmd_descargar)

    sp = sub.add_parser("comparar-firmas", help="qué firma conviene más para una misma estrategia")
    sp.add_argument("--reglas", nargs="*", help="ficheros TOML (por defecto config/reglas/firmas/*.toml)")
    sp.add_argument("--esperanza", default="-0.05,0,0.05,0.1,0.15,0.2,0.3", help="ventajas en R por operación")
    sp.add_argument("--riesgo", default="100,150,200,250,350,500,750", help="riesgos por operación en USD")
    sp.add_argument("--payoff", type=float, default=2.0, help="R que gana un acierto")
    sp.add_argument("--riesgo-fondeada", type=float, help="riesgo por operación en la fondeada (si es distinto)")
    sp.add_argument("--payoff-fondeada", type=float, help="R que gana un acierto en la fondeada (si es distinto)")
    sp.add_argument("--prob-operar", type=float, default=0.85, help="probabilidad de operar cada día")
    sp.add_argument("--simulaciones", type=int, default=1000)
    sp.add_argument("--horizonte", type=int, default=120, help="sesiones máximas por fase y en la fondeada")
    sp.add_argument("--semilla", type=int, default=0)
    sp.add_argument("--salida")
    sp.set_defaults(func=cmd_comparar_firmas)

    sp = sub.add_parser("estrategias", help="listar estrategias, parámetros e instrumentos")
    sp.set_defaults(func=cmd_estrategias)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
