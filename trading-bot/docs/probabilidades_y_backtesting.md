# Probabilidades, win rate y dónde hacer backtesting

*27-sep-2026. Complementa a [`fondeo.md`](fondeo.md) (firmas) y al [`README`](../README.md) (el sistema).*

## 1. Lo que dicen los datos (tasas base)

| Estudio / fuente | Resultado |
|---|---|
| Brasil, todos los que empezaron a hacer day trading en futuros 2013–2015 (Chague, De-Losso y Giovannetti) | De quienes insistieron más de 300 días, **el 97 % perdió dinero**; solo el 1,1 % ganó más que el salario mínimo. Sin evidencia de que aprendieran con la experiencia. |
| Taiwán 1992–2006 (Barber, Lee, Liu y Odean) | **Menos del 1 %** de los day traders gana de forma predecible tras comisiones. De media pierden 0,24 % al día. |
| Firmas de fondeo (datos de la industria, no auditados) | Aprueba el **5–15 % por intento**; solo **~7 % de los traders llega a cobrar**; de los fondeados, ~45 % cobra al menos una vez. |
| Estrategia ORB publicada (Zarattini y Aziz, QQQ 2016–2023) | **Acierta solo el 24 %** de las veces y aun así gana +0,13 R por operación. |
| Réplica de esa ORB en 5 índices (blog, 25-sep-2026) | Reproduce el resultado **bruto**, pero **neto de costes queda en cero**. |

Lección: las ventajas intradía existen pero son finas; los costes y la indisciplina se las comen.
Un bot resuelve la indisciplina; los costes solo se vencen con ventaja real medida.

## 2. Win rate: la cifra que más engaña

El porcentaje de acierto no dice nada sin saber **cuánto gana un acierto frente a lo que pierde un fallo**:

| Un acierto gana… | Acierto para no perder | Para +0,1 R por operación | Para +0,2 R | Operaciones para demostrar +0,1 R* |
|---|---|---|---|---|
| 0,5 R | 66,7 % | 73,3 % | 80,0 % | ~180 |
| 1 R | 50,0 % | 55,0 % | 60,0 % | ~400 |
| 1,5 R | 40,0 % | 44,0 % | 48,0 % | ~620 |
| 2 R | 33,3 % | 36,7 % | 40,0 % | ~840 |
| 3 R | 25,0 % | 27,5 % | 30,0 % | ~1.280 |

\* Para que la ventaja supere dos veces su error estándar. 10 años de NQ dan ~2.100 operaciones
(una al día el 85 % de los días); 1 año solo ~210; un mes de demo, ~18.

- Un "80 % de acierto" en redes puede perder dinero si el objetivo es pequeño y el stop grande.
- **FVG de Aleix con objetivo 2R:** en datos aleatorios nuestro motor da un ~30–33 % de acierto
  (sin ventaja). Una ventaja real se vería como **37–40 % o más** mantenido durante años.
- La vuelta 2 mostró que, a igual ventaja, las estrategias de **más acierto y salidas más cortas
  cobran más** en las firmas (menos rachas que rompan el drawdown).

## 3. Probabilidades del proyecto (estimación propia, razonada)

*Estimación subjetiva a partir de las tasas base y de nuestras simulaciones; no es un dato medido.
Se irá sustituyendo por números reales en cuanto tengamos backtests con datos del NQ.*

| Etapa | Probabilidad | Por qué |
|---|---|---|
| Encontrar una estrategia con ≥ +0,1 R neta que aguante walk-forward en 10 años de NQ | **25–40 %** | Hay efectos intradía documentados, pero finos; los costes se comen la mayoría. Probaremos varias (FVG, ORB, momentum intradía...) sin hacer trampas estadísticas. |
| Que esa ventaja se mantenga en demo y en real | **50–60 %** | Lo habitual es que el resultado real sea peor que el backtest. |
| Con +0,1 R y 250 $ de riesgo: aprobar una evaluación | **~40–45 %** por intento | Simulación de la vuelta 2. |
| … y cobrar al menos una vez en 6 meses | **~35 %** por cuenta | Idem. Valor esperado ≈ +400–600 $ por cuenta. |
| Sin ventaja: cobrar por suerte | ~17–21 % por cuenta | Pero el valor esperado ronda 0: es apostar. |

**En conjunto:** ~12–25 % (25–40 % × 50–60 %) de que el proyecto acabe en una operativa rentable con cuentas de
fondeo en el primer año, frente al ~7 % de los traders que llega a cobrar. Y un **75–85 %** de que
el laboratorio concluya que no hay ventaja suficiente **antes** de gastar en cuentas: ese
resultado también es valioso, porque ahorra dinero. Varias cuentas con la misma estrategia no
multiplican las probabilidades: aprueban y suspenden juntas.

## 4. Dónde hacer backtesting del NQ

### Automático (para validar el bot)

| Plataforma | Qué aporta | Coste | Uso en el proyecto |
|---|---|---|---|
| **CAJA NEGRA** (este repo) + datos reales | Única con las reglas de las firmas, probabilidad de aprobar y valor esperado por cuenta. Motor conservador y testeado. | Datos: Databento (histórico por uso; ver coste exacto con `descargar --solo-coste`) o compra única de ficheros (FirstRate Data, etc.) | Motor principal |
| **QuantConnect** | Según su documentación, datos de futuros CME (incluido NQ) de tick a diario **gratis** en su nube; Python. | Plan gratuito para backtest | Segunda opinión con otro motor: si no cuadra, hay un bug |
| **NinjaTrader 8** | Strategy Analyzer con optimización y walk-forward; Market Replay tick a tick. Plataforma que aceptan muchas firmas. | Gratis para simulación | Validar la ejecución antes de ir a real |
| **TradingView** | Pine Script, probador de estrategias y Bar Replay; muy visual. | Datos CME en tiempo real de pago | Revisión visual de operaciones (menos preciso dentro de cada vela) |
| **Sierra Chart / MultiCharts** | Herramientas profesionales, replay muy fiel. | De pago | Opcional |

### Manual (para aprender la estrategia de Aleix y escribir sus reglas)

| Plataforma | Qué ofrece | Coste |
|---|---|---|
| **NQ Replay** (nqbacktest.online) | Más de 10 años de NQ en 1 minuto, vela a vela, **con superposiciones ICT (FVG)**: encaja con la estrategia de Aleix | Gratis; Pro desde 12,99 $/mes |
| **TestMax** | NQ y ES con datos de 1 segundo, modo reto de fondeo | Gratis; Pro 14,99 $/mes |
| **NinjaTrader Market Replay** | Replay tick a tick de datos reales CME (el más realista) | Gratis |
| **TradesViz** | Simulador de futuros con replay | Plan Platinum |
| **FX Replay** | Muy usado, pero más orientado a forex; futuros solo en Pro | Pro |

El replay manual sirve para **entender y escribir las reglas** (y detectar qué hace Aleix que no
cuenta), no para demostrar la ventaja: nadie hace 800 operaciones a mano bien registradas.

## 5. Qué significa "backtesting a lo bestia" (protocolo)

1. **10+ años de NQ en 1 minuto** (2015–2026): volatilidad de 2018, COVID 2020, mercado bajista
   de 2022 y alcista de 2023–2025. Una estrategia que solo funciona en uno de esos años no vale.
2. **Muestra mínima:** ~840 operaciones si el objetivo es 2R, ~400 si es 1R (tabla del punto 2).
3. **Walk-forward:** solo cuenta el resultado fuera de muestra.
4. **Estrés de costes:** repetir con 2 ticks de deslizamiento; si la ventaja desaparece, no la había.
5. **Robustez:** los parámetros vecinos deben dar resultados parecidos; comprobar también en ES y
   año por año.
6. **Segundo motor:** repetir la estrategia final en QuantConnect o NinjaTrader.
7. **Simulación con las reglas de la firma elegida** (probabilidad de aprobar y valor esperado).
8. **Demo 1–2 meses:** no prueba la ventaja (son pocas operaciones); prueba que la ejecución real
   coincide con el backtest (entradas, deslizamiento, fallos técnicos).
9. Solo entonces, **una** cuenta. Escalar solo si lo real cuadra con lo simulado.

## Fuentes

[Chague, De-Losso y Giovannetti (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101) ·
[Barber, Lee, Liu y Odean](https://www.sciencedirect.com/science/article/abs/pii/S1386418113000190) ·
[Zarattini y Aziz, ORB (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622) ·
[Réplica ORB en 5 índices](https://www.mql5.com/en/blogs/post/776235) ·
[Estadísticas de firmas (QuantVPS)](https://www.quantvps.com/blog/prop-firm-statistics) ·
[Pass rate por trader vs por intento](https://alexfirdaus.com/prop-firm-pass-rate/) ·
[QuantConnect futuros](https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/algoseek/us-futures) ·
[QuantConnect precios](https://www.quantconnect.com/pricing/) ·
[Databento futuros](https://databento.com/futures) ·
[Databento planes CME](https://databento.com/blog/introducing-new-cme-pricing-plans) ·
[NQ Replay](https://nqbacktest.online/) ·
[TestMax NQ](https://test-max.com/features/nasdaq-futures-backtesting/) ·
[TradesViz futuros](https://www.tradesviz.com/futures-backtesting-software/) ·
[FX Replay](https://fxreplay.com/) ·
[Comparativa de software de backtesting](https://www.tradezella.com/blog/best-backtesting-software)
