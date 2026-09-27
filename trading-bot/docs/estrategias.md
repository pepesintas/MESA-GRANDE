# Estrategias: qué tiene evidencia y qué encaja con las firmas

*Vuelta 3 de la investigación, 27-sep-2026. Las cuatro estrategias están programadas en
`cajanegra/strategies/` y pasan el detector de "mirar al futuro" en datos aleatorios.*

## Resumen

| Estrategia (nombre en el lab) | Evidencia | Resultado publicado | Perfil | Encaje con firmas | Prioridad |
|---|---|---|---|---|---|
| **Zona de ruido** (`zona_ruido`) | Paper 2024 en SPY + aplicación independiente a NQ/ES | SPY 2007–2024: +19,6 %/año neto, Sharpe 1,33. **NQ: +24,3 %/año, Sharpe 1,67, acierto 38 %, payoff 2,25 (≈ +0,23 R/op.)** | Acierto medio, ganancias 2,25R | **El mejor** de los perfiles probados | **1** |
| **Última media hora** (`ultima_media_hora`) | Dos papers en el *Journal of Financial Economics*: SPY 1993–2013 y **más de 60 futuros 1974–2020** | El efecto existe en casi todos los mercados; tamaño de la ventaja en NQ tras costes: por medir | ~50 % de acierto, movimientos pequeños, 1 op./día | Bueno si la ventaja aguanta los costes | **2** |
| **Primer FVG** (`fvg`, hipótesis de Aleix) | Estudio en ES, NQ, oro y plata 2019–2026 (MPM Research) | **La reacción en el FVG es real pero la ventaja operable no**: los costes se la comen; el scalping de 5–15 min es la peor versión | Depende de las reglas | Sin ventaja = lotería | **3** (con las reglas exactas de Aleix) |
| **ORB** (`orb`) | Paper 2023 en QQQ | Acierto 24 %, +0,13 R/op. en bruto; una réplica en 5 índices (sep-2026) lo deja en **cero tras costes** | Poco acierto, ganancias grandes | El peor perfil para firmas (rachas largas) | Referencia |

## Encaje con las firmas según el perfil

Simulación con las reglas reales de las cinco firmas (`comparar-firmas`), mejor riesgo por firma, 800 trayectorias:

| Perfil | Ventaja | Acierto | Mejor valor por cuenta | Rango entre firmas |
|---|---|---|---|---|
| Zona de ruido NQ (publicado) | +0,235 R | 38 % | 1.876 $ (cobra el 64 %) | 1.450–1.876 $ |
| Zona de ruido con **la mitad** de ventaja | +0,117 R | 34 % | 693 $ (cobra el 40 %) | 444–693 $ |
| Zona de ruido con la ventaja del ORB | +0,13 R | 35 % | 774 $ | 516–774 $ |
| ORB publicado | +0,13 R | 24 % | 582 $ | 367–582 $ |
| ORB con la mitad de ventaja | +0,065 R | 23 % | 289 $ | 156–289 $ |
| FVG sin ventaja neta (MPM) | 0 | 33 % | 122 $ (lotería: 18 % cobra) | 24–122 $ |

**Lectura:** a igual ventaja, el perfil de la zona de ruido vale un 35–40 % más por cuenta que el
del ORB (menos rachas que rompan el drawdown). Incluso con la mitad de la ventaja publicada, la
zona de ruido tendría valor esperado positivo en las cinco firmas.

## Reglas implementadas

**Zona de ruido** (Zarattini, Aziz y Barbon 2024):
- σ(t) = media de los últimos 14 días de |cierre(t) / apertura − 1| al mismo minuto.
- Zona = [min(apertura, cierre de ayer)·(1−σ), max(apertura, cierre de ayer)·(1+σ)].
- Cada media hora desde las 10:00: por encima de la zona → largo; por debajo → corto.
- Salida si en una revisión el precio cierra al otro lado de max(zona, VWAP) (largos) o
  min(zona, VWAP) (cortos); todo cerrado al final de la sesión.
- Añadido para firmas (`stop_continuo=true`): stop real de protección más allá del stop dinámico
  con un colchón de 0,5·σ(t), solo para movimientos extremos entre revisiones.

**Última media hora** (Gao et al. 2018; Baltussen et al. 2021): a las 15:30 opera en la
dirección de la rentabilidad desde el cierre de ayer (`senal=resto_del_dia`) o de la primera
media hora (`senal=primera_media_hora`) y cierra al final de la sesión. `umbral_pct` filtra días
de poco movimiento; `stop_puntos` añade stop de protección.

## Qué hacer con la estrategia de Aleix

El estudio de MPM probó el FVG "de manual" y no encontró ventaja neta, así que **si la estrategia
de Aleix funciona es por algo más que el FVG**: su filtro de tendencia, la hora, el contexto de
liquidez, o su criterio discrecional. Hace falta escribir exactamente:

1. Cómo decide que el mercado es alcista (¿diario?, ¿4 h?, ¿por encima de qué?).
2. Qué FVG vale (temporalidad, tamaño mínimo, "el primero" desde qué hora).
3. Dónde entra (borde, mitad del hueco, confirmación), dónde pone el stop y dónde sale.
4. Qué días o situaciones descarta (noticias, huecos grandes...).

Idea a probar con datos: usar el FVG **como mejora de la entrada** dentro de una señal con
evidencia (entrar en el retroceso a un FVG tras una ruptura de la zona de ruido) en lugar de
como señal por sí solo.

## Orden de pruebas con datos reales

```bash
python -m cajanegra backtest --datos data/nq_1m.parquet --estrategia zona_ruido \
    --param stop_continuo=true --param riesgo_usd=200 --param max_contratos=50 \
    --reglas config/reglas/firmas/tradeify_select_flex_50k.toml
python -m cajanegra walkforward --datos data/nq_1m.parquet --estrategia zona_ruido \
    --grid dias_sigma=10,14,20 --grid multiplicador=0.8,1,1.2 --grid cada_min=15,30
python -m cajanegra backtest --datos data/nq_1m.parquet --estrategia ultima_media_hora --param umbral_pct=0.25
```

1. Replicar la zona de ruido en NQ y compararla con lo publicado (si no se parece, buscar el fallo antes de seguir).
2. Última media hora, con y sin umbral.
3. FVG con las reglas exactas de Aleix, y como filtro de entrada de la zona de ruido.
4. ORB como referencia.

## Fuentes

[Beat the Market: noise area (SSRN)](https://ssrn.com/abstract=4824172) ·
[Resumen del paper (Concretum)](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/) ·
[Intraday Momentum for ES and NQ (Quantitativo)](https://www.quantitativo.com/p/intraday-momentum-for-es-and-nq) ·
[Mejoras de salida (Maróy, SSRN)](https://papers.ssrn.com/sol3/Delivery.cfm/5095349.pdf?abstractid=5095349&mirid=1) ·
[Gao, Han, Li y Zhou, Market intraday momentum (JFE)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351) ·
[Baltussen et al., Hedging demand and market intraday momentum (JFE)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598) ·
[MPM Research: ¿funciona el FVG?](https://mpmmarkets.com/research/does-the-fair-value-gap-strategy-work) ·
[Zarattini y Aziz, ORB (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622) ·
[Réplica ORB en 5 índices](https://www.mql5.com/en/blogs/post/776235)
