"""Informes de texto en español."""

from __future__ import annotations

import math

import pandas as pd

from .engine.backtest import BacktestResult
from .research.metrics import daily_stats, trade_stats, yearly_table
from .risk.prop_rules import FirmConfig


def money(x: float) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    s = f"{abs(x):,.0f}".replace(",", ".")
    return f"{'-' if x < 0 else ''}{s} $"


def pct(x: float) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x * 100:.1f}%"


def backtest_report(res: BacktestResult) -> str:
    ts, ds = trade_stats(res.trades), daily_stats(res.days)
    params = ", ".join(f"{k}={v}" for k, v in res.params.items())
    out = [
        f"ESTRATEGIA  {res.strategy}  ·  {res.instrument.symbol} ({res.instrument.description})",
        f"parámetros  {params}",
    ]
    if res.days.empty:
        return "\n".join(out + ["Sin sesiones en el rango elegido."])
    d0, d1 = res.days["fecha"].iloc[0].date(), res.days["fecha"].iloc[-1].date()
    out.append(f"periodo     {d0} → {d1}  ({ds['sesiones']} sesiones, {ds['dias_operados']} con operaciones)")
    if ts["operaciones"] == 0:
        return "\n".join(out + ["", "No hubo operaciones."])
    pf = ts["factor_beneficio"]
    out += [
        "",
        f"  Beneficio neto ........ {money(ts['beneficio_neto'])}   (comisiones pagadas {money(ts['comisiones'])})",
        f"  Operaciones ........... {ts['operaciones']}  (largos {ts['largos']}, cortos {ts['cortos']})",
        f"  Acierto ............... {pct(ts['acierto'])}",
        f"  Ganancia / pérdida media {money(ts['ganancia_media'])} / {money(ts['perdida_media'])}",
        f"  Factor de beneficio ... {'∞' if math.isinf(pf) else f'{pf:.2f}'}",
        f"  Esperanza ............. {money(ts['esperanza_por_operacion'])} por operación  ({ts['esperanza_r']:+.2f} R)",
        f"  Días positivos ........ {pct(ds['dias_positivos'])}   mejor {money(ds['mejor_dia'])} · peor {money(ds['peor_dia'])}",
        f"  Máx. drawdown ......... {money(ds['max_drawdown_cierre'])} al cierre · {money(ds['max_drawdown_intradia'])} intradía",
        f"  Sharpe anual (diario) . {ds['sharpe_anual']:.2f}",
        f"  Peor racha ............ {ds['racha_dias_perdedores']} días perdedores seguidos",
        "",
        "  Por año:",
    ]
    yt = yearly_table(res.trades, res.days)
    for year, row in yt.iterrows():
        out.append(
            f"    {year}  {money(row['beneficio']):>12}   {int(row.get('operaciones', 0)):>4} ops   acierto {pct(row.get('acierto', 0))}"
        )
    motivos = res.trades["motivo"].value_counts()
    out += ["", "  Salidas: " + ", ".join(f"{k} {v}" for k, v in motivos.items())]
    return "\n".join(out)


def evaluation_report(firm: FirmConfig, roll: dict, boot: dict) -> str:
    out = [f"EVALUACIÓN DE FONDEO  ·  {firm.nombre}"]
    if firm.aviso:
        out.append(f"  ⚠ {firm.aviso}")
    for title, s in (("Arranques históricos (empezar cualquier día real)", roll), ("Bootstrap por bloques (historias alternativas)", boot)):
        out += ["", f"  {title}:"]
        if not s or s.get("simulaciones", 0) == 0:
            out.append("    sin datos suficientes")
            continue
        med = s["sesiones_mediana_aprobar"]
        out += [
            f"    simulaciones ................ {s['simulaciones']}",
            f"    probabilidad de aprobar ..... {pct(s['p_aprobar'])}"
            + ("" if math.isnan(med) else f"   (mediana {med:.0f} sesiones)"),
            f"    probabilidad de cobrar ...... {pct(s['p_retiro'])}   ({pct(s['p_retiro_si_fondeada'])} de las fondeadas)",
            f"    retiro medio si cobras ...... {money(s['retiro_medio_si_cobra'])}",
            f"    coste medio por intento ..... {money(s['coste_medio'])}",
            f"    VALOR ESPERADO POR CUENTA ... {money(s['valor_esperado_por_cuenta'])}",
        ]
        out.append("    desenlaces: " + ", ".join(f"{k} {v}" for k, v in s["resultados"].items()))
        if s["motivos_suspension"]:
            out.append("    motivos de suspensión: " + ", ".join(f"{k} {v}" for k, v in s["motivos_suspension"].items()))
    out += ["", "  (Solo se cuenta el primer retiro. Cuentas con la misma estrategia NO diversifican: fallan juntas.)"]
    return "\n".join(out)


def walkforward_report(windows: pd.DataFrame) -> str:
    out = ["WALK-FORWARD (optimiza en el pasado, prueba en el tramo siguiente)"]
    for _, w in windows.iterrows():
        p = ", ".join(f"{k}={v}" for k, v in w["parametros"].items()) or "(sin parámetros)"
        out.append(
            f"  IS {w['is_desde']}→{w['is_hasta']}  {money(w['beneficio_is']):>10}  |  "
            f"OOS {w['oos_desde']}→{w['oos_hasta']}  {money(w['beneficio_oos']):>10}  ({w['operaciones_oos']} ops)  [{p}]"
        )
    total_is = windows["beneficio_is"].sum()
    total_oos = windows["beneficio_oos"].sum()
    out.append(f"  Total fuera de muestra: {money(total_oos)}   (dentro de muestra sumaba {money(total_is)})")
    return "\n".join(out)
