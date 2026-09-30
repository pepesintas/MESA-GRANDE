# Revisión del Trading Bot (Caja Negra) — 30-sep-2026

## Qué revisé y qué no

**Revisado:** los dos repositorios de GitHub que contienen el bot:
- `pepesintas/TradingSystem` (privado, último commit 30-sep) → **es el vigente**.
- `pepesintas/bot-trading` (público, 27-sep) → copia anterior y desfasada (sin salida parcial, sin `live/`, sin `ESTADO.md`).

Leí el motor, la estrategia `zona_ruido`, el simulador de fondeo, el módulo en vivo, el CLI, los tests, las reglas de firmas y los documentos (`ESTADO.md`, `docs/estrategias.md`, `docs/errores_backtesting.md`, validación QuantConnect). Ejecuté los 83 tests (pasan) y 4 experimentos propios (más abajo).

**No pude revisar:**
- **La carpeta local del ordenador de trading** (desde la nube no se ve). Si hay algo que no esté en Git, no está en esta revisión.
- **La conversación anterior.** Solo tengo lo que quedó escrito en el repo.
- **Los datos de mercado** (`data/*.parquet`, gitignored). Por eso **no pude reproducir** 34,9 % / 24,1 % / +250 $ / 2.780 $/mes. Los experimentos usan datos sintéticos.
- **Reglas actuales de Topstep:** solo pude ver resúmenes de búsqueda; `help.topstep.com` está bloqueado desde este entorno.

En la carpeta `MESA-GRANDE` no hay nada del bot (es una web con `index.html` y un proxy de OpenAI).

---

## Veredicto en tres líneas

1. **La ingeniería es buena:** no hay lookahead (lo comprobé con una prueba más dura que la del repo), la contabilidad de P&L cuadra al céntimo, el método (walk-forward, registro de errores) es de nivel alto.
2. **La conclusión económica está mucho menos firme de lo que dice `ESTADO.md`:** con esta muestra, +250 $/intento es estadísticamente indistinguible de 0, y el plan de "20 cuentas" **choca con una regla de Topstep** (máx. 5 cuentas Express Funded activas).
3. **Antes de escribir el `runner` en vivo** hay que arreglar 3-4 cosas pequeñas (abajo). Ninguna cuesta más de una tarde.

---

## A. Problemas que afectan a la decisión de comprar cuentas

### A1. El plan de "20 cuentas escalonadas" no es viable tal como está escrito — **crítico**
- Topstep permite **hasta 5 Express Funded Accounts activas a la vez** ([fuente](https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit) y resultados de búsqueda de su help center; verifícalo tú en la web, no pude abrirla). Con 5, los ~2.780 $/mes se dividen por 4.
- La cifra **2.780 $/mes (rango 646-4.166, 1 % de perder)** aparece **solo en `ESTADO.md`**. No hay script, ni test, ni sección en `docs/` que la genere. No es reproducible ni auditable.
- Las 20 cuentas operarían **la misma señal**: no diversifican, aprueban y suspenden a la vez (lo dice vuestro propio README). Escalar multiplica media **y** riesgo. Si la ventaja real fuera 0, 20 cuentas = 20× las cuotas (49 $/mes + 149 $ de activación cada una) sin nada a cambio.
- Riesgo operativo: Topstep exige que toda la actividad salga de **tu dispositivo personal** (VPS/remotos prohibidos). Un corte de internet o PC durante una posición afectaría a todas a la vez.
- Hace falta escribir `scripts/escala.py` que genere esa cifra desde los días reales, con el tope de cuentas y la correlación completa (misma serie de P&L, arranques desfasados).

### A2. Los intervalos de confianza son enormes y las cifras se presentan sin ellos — **crítico**
- `rolling_starts` usa arranques en **todos** los días: ventanas solapadas. En 2022-10→2026-09 hay ~1.000 sesiones; con evaluación de 60 sesiones eso son **~16 ventanas independientes**.
- 35 % de aprobar con n≈16 → **IC 95 % ≈ 18 %-61 %**. Cobrar (24 %) → **10 %-49 %**. El bootstrap por bloques no arregla esto: baraja los mismos días, no crea información nueva ni colas que no estén en la muestra.
- `docs/estrategias.md` ya mide que **las 20 mejores operaciones de 2.047 son el 96 % del beneficio** y que sin ellas el total es +1.730 $. Con la salida parcial la concentración sigue alta. El resultado de cada simulación depende de si cae o no una de esas ~20 operaciones en la ventana.
- Recomendación: informar siempre P(aprobar), P(cobrar) y VE **con intervalo** y un test de sensibilidad "quitando las N mejores operaciones/días".

### A3. Contaminación de la muestra "fuera de muestra"
Tras 9-10 hipótesis probadas sobre los mismos 10 años (colchón, rango, volatilidad, margen, lockout, riesgo, tamaño de cuenta, vehículo, parcial…), ni 2016-2022 ni 2022-2026 son ya "fuera de muestra" en sentido estricto. Cada decisión (riesgo 800 $, parcial 50 %@1R, Topstep) se eligió mirando esos mismos datos.
- Lo bueno: vuestra regla "solo sobrevive lo que se razona por mecanismo" reduce el problema.
- Lo que falta: **un tramo reservado que nadie haya mirado** (p. ej. todo lo posterior a una fecha fija, o directamente paper trading) para juzgar la configuración final **una sola vez**.
- La ventaja ya cayó a un tercio (3.532 → 1.154 $/ventana OOS). El VE **−95 $** del 29-sep con la ventaja reciente pasó a **+250 $** el 30-sep cambiando vehículo, riesgo y parcial, no porque hubiera evidencia nueva de ventaja. Eso es exactamente el patrón que vuestro registro de errores describe como sospechoso.

### A4. El slippage decide todo y el simulador asume el caso bueno para esta estrategia
- Vuestro barrido muestra que la ventaja **se agota entre 3 y 4 ticks**.
- `zona_ruido` entra **a mercado justo al romper el borde a las :00/:30** (momento de adverse selection) y ~22-29 % de las operaciones salen por el **stop duro** (con 2 % de acierto). El modelo aplica 1 tick fijo a ambos casos.
- Mejora: slippage dependiente de la volatilidad (múltiplo de σ o del rango de la barra) y mayor en stops y en la primera barra tras :00/:30. Ejecutar el barrido con esa versión.
- Antes de comprar ninguna cuenta: la pregunta 1 del dosier (slippage real en MNQ) es la correcta. Yo lo mediría con **paper trading real en TopstepX** (que vale 29 $/mes) o con órdenes de 1 micro durante 4-6 semanas, no con la opinión de un operador.

### A5. La validación con QuantConnect es más estrecha de lo que sugiere "fase 0 cerrada"
- Cubre **ene-2024 → jun-2026** (2,5 años), con **riesgo 300 $ y sin salida parcial**. La configuración que se propone comprar (800 $ + parcial + Topstep) **no está validada cruzadamente**.
- Compara lógica de señales (92,5 % de coincidencia; buen resultado), **no** ejecución real. QC también es un simulador.
- Los desajustes se concentran en la **semana de vencimiento trimestral** (13,8 % vs 5,8 %). Los 10 años de historia usan `NQ.v.0` (E-mini, sin ajustar, rolado por volumen) con especificaciones de MNQ: el cierre "de ayer" cruza el cambio de contrato 4 veces al año y **desplaza la zona** esos días. El loader no detecta ni marca saltos de rolado.
- Mejora: detectar el rolado (salto de precio entre cierre y apertura con cambio de contrato o gap > umbral) y excluir o recalcular `prev_close` con el mismo contrato; comparar resultados con y sin esas ~40 sesiones.

### A6. Reglas de Topstep en el TOML: revisar antes de confiar en el simulador
- El TOML no tiene `perdida_diaria_max`. Topstep tiene un Daily Loss Limit **opcional** ([resultado de búsqueda](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account)). Si lo activas (y en cuenta real conviene), el simulador sobreestima P(aprobar) con 4 operaciones/día y 800 $ de riesgo.
- Riesgo 800 $/operación con MLL de 2.000 $ = **40 % del colchón en una sola operación**; tres pérdidas en un día lo revientan. El simulador lo refleja, pero el bot en vivo necesita el mismo tope como **kill switch** propio.
- `max_contratos = 5` es "(supuesto)". La XFA tiene un plan de escalado por beneficio que no está modelado (empieza con menos contratos). Con riesgo 500 $ en la fondeada puede no importar, pero conviene comprobarlo.
- Las plantillas están bien marcadas como (oficial)/(supuesto); pasa los (supuesto) a (oficial) desde la web antes de comprar.

---

## B. Errores concretos en el código

### B1. El "acierto" con salida parcial está inflado por contabilidad — **confirmado**
`_cerrar_parcial` anota la parte parcial como una **fila propia** ganadora. `trade_stats` cuenta filas, así que el acierto sube aunque no cambie nada.
- Experimento (paseo aleatorio, misma señal, 1.552 posiciones): **sin parcial 30,7 % → con parcial 48,2 %** contado por filas, pero **41,0 %** contado por posición.
- Consecuencia: "acierto 39,5 % → 54,9 %" y "esperanza +0,08 R → +0,29 R" de `docs/estrategias.md` **no son comparables** (doble de filas). Lo que sí es real es el efecto sobre los **días ganadores** (P&L diario, no afectado).
- Los resultados de fondeo (P(cobrar)) salen del P&L diario, así que **no se invalidan**; sí conviene reexplicar la narrativa.
- Arreglo: añadir columna `id_posicion` y calcular acierto/R por posición. También `consecutive_losses` solo mira el tramo final de la posición.

### B2. `BrokerSimulado`: stop huérfano crea una posición fantasma — **confirmado**
`cerrar_todo()` no cancela los stops colocados. Reproducido: entro 4 largos con stop → `cerrar_todo` → posición 0 → una barra que toca el stop → **abre −4 cortos**. En un bróker real es el escenario que más daño hace.
- Arreglo: `cerrar_todo` (y todo cierre) debe cancelar stops del símbolo; el runner debe reconciliar contra `posicion()` tras cada acción.
- Además: `revisar_stops` rellena al precio exacto del stop (el backtest rellena a la apertura si hay gap y aplica slippage); `Timestamp.utcnow()` está deprecado (`Pandas4Warning`, desaparece en pandas 4) → `pd.Timestamp.now("UTC")`; comisión por defecto 0,61 $ vs 0,75 $ en `instruments.py` (elige una; la real de Topstep es 0,61).
- **`live/` tiene 0 tests.** Es exactamente el código donde un fallo cuesta dinero.

### B3. Calentamiento perdido con `--desde` y en cada ventana walk-forward — **confirmado**
`run(start=…)` salta los días anteriores, así que `_history` (σ de 14 días) arranca vacío: en mi prueba **la primera operación tras `--desde` llegó 18 días naturales tarde**. En walk-forward, cada tramo IS y OOS pierde ~14 de 125 sesiones (≈11 % del OOS) y las cifras "por ventana" quedan sesgadas a la baja.
- Arreglo: pre-cargar las N sesiones previas a `start` en la estrategia (llamar a `on_day_start`/acumular sin operar).
- Nota para el `runner`: en vivo el histórico σ debe **cargarse al arrancar** desde parquet; si no, el bot pasará los primeros 14 días sin operar (o, peor, operará con σ de menos días).

### B4. Barras de 1 minuto ausentes
Databento `ohlcv-1m` **omite minutos sin negociación**. La estrategia revisa **solo** en minutos exactos (`(end_min - primera) % 30 == 0`); si falta la barra de las 09:59/10:29…, esa revisión (entrada **y** stop dinámico) se salta 30 minutos, sin aviso. En vivo, igual. Cuenta cuántos minutos faltan en RTH en los parquets; si hay, rellena hacia delante con barras planas (volumen 0) en el loader y en `ContextoVivo`.

### B5. Fallos silenciosos (ya os pasó el 28-sep)
`size_for_risk` devuelve 0 y la estrategia hace `return` sin rastro. Ya escondió seis años sin operar. Añadir contadores de "señal descartada" (tamaño 0, día apagado, pausa, límite de operaciones) y **un aviso automático en el informe** si algún año tiene <X % de sesiones con señal.

### B6. Inconsistencia menor de conservadurismo
La documentación dice "límites: el precio tiene que **cruzar**", pero objetivos y salida parcial se llenan **al tocar** el nivel. Probé exigir +1 tick en la parcial: **sin efecto** en sintéticos, así que el riesgo real está en la cola de la cola (prioridad de cola), no en el motor. Baja prioridad; documentarlo o hacerlo consistente.

### B7. Huecos de tests
- **Cero tests de `parcial_*`**, la única modificación de estrategia que se declara validada.
- **Cero tests de `live/`.**
- El detector de lookahead (`test_no_edge_on_random_walk`) es unilateral (`media < 3·se`), con una sola semilla, sin costes y **no cubre parcial**. Es un buen sensor pero débil. Añadir la **prueba de invarianza de prefijo** (abajo): es determinista y mucho más estricta.

---

## C. Cosas que están bien (mantener)

- **Sin lookahead.** Prueba de invarianza de prefijo con la configuración real (stop continuo + parcial): los trades sobre los primeros N días son **idénticos** con o sin datos futuros. 352/352 iguales.
- **Contabilidad consistente:** Σ P&L de operaciones = Σ P&L diario al céntimo, también con parciales.
- Modelo de fills conservador donde importa (stop antes que objetivo, entrada intrabarra sin objetivo, gap → apertura), simulador de reglas de firma bien estructurado (trailing cierre/intradía, bloqueo, consistencia, ciclos de retiro).
- Disciplina de método: registro de errores, "nada sin walk-forward", ideas por mecanismo. Es lo más valioso del repo.
- Diseño de `ContextoVivo` para que **el mismo objeto de estrategia** corra en vivo; y orden correcto: simulado → paper → dinero.
- Sin secretos en el historial de ninguno de los dos repos.

---

## D. Higiene del repositorio

| Qué | Detalle |
|---|---|
| **Dos repos duplicados** | `bot-trading` (público) está desfasado y **expone la estrategia y sus reglas**. Consolidar en `TradingSystem` y **archivar o hacer privado** `bot-trading`. |
| `CLAUDE.md` | Cita `docs/traspaso_local.md`, que **no existe**; dice "el repo es público" y `TradingSystem` es privado (confunde a futuras sesiones). |
| `README.md` | Hoja de ruta desactualizada (fase 2 "siguiente" cuando ya hecha; módulo `strategies` solo lista `orb`/`fvg`; cita bloqueo CPI/NFP pero el calendario es solo FOMC). |
| `config/noticias/fomc.csv` | Incluye 2019-10-04 y 2025-08-22 (no son reuniones: discursos), etiquetados como "comunicado de tipos". El filtro salió "sin efecto"; no afecta al resultado, pero límpialo. |
| `scripts/*.py` | Rutas y parámetros fijos, sin tests; `robustez.py` y `cartera.py` usan `ultima_media_hora`, ya descartada. |
| `docs/estrategias.md` | Termina en "Conclusión de la vuelta 4" con "no se compra ninguna cuenta"; `ESTADO.md` la contradice el día siguiente sin apuntar qué evidencia cambió. Un solo documento de decisión con fecha y evidencia evitaría eso. |

---

## E. Plan de mejoras, por orden de valor

1. **(½ día)** Contabilidad por posición (B1) y tests de `parcial_*`; test de invarianza de prefijo permanente.
2. **(½ día)** Arreglar B2 (cancelar stops al cerrar) + tests de `live/`; sustituir `utcnow`.
3. **(½ día)** Pre-calentamiento del histórico de σ (B3) y rellenado de minutos ausentes (B4); repetir los números clave y ver cuánto cambian.
4. **(1 día)** Intervalos de confianza y análisis "sin las N mejores operaciones" en `evaluation_report`; separar y **congelar** un tramo final como holdout.
5. **(1 día)** `scripts/escala.py`: reproducir los "2.780 $/mes" con máx. 5 cuentas, correlación completa y arranques desfasados. Si no sale positivo con IC, no comprar.
6. **(1 día)** Slippage dependiente de volatilidad/hora y detección de rolado en el loader; volver a correr la validación con QC **con la configuración final** (800 $ + parcial).
7. **Después:** `runner.py` con kill switch propio (pérdida diaria, MLL restante, máx. operaciones), reconciliación de posición en cada barra, cierre a las 15:59 garantizado, y **paper trading** midiendo slippage antes de cualquier cuenta de pago.
8. Corregir las reglas (supuesto) del TOML de Topstep desde la web oficial, incluida la DLL opcional y el plan de escalado.

---

## F. Experimentos que hice (datos sintéticos; scripts no incluidos en el repo)

| Prueba | Resultado |
|---|---|
| Invarianza de prefijo (parcial + stop continuo, 400 días) | 352 = 352 operaciones idénticas → **sin lookahead** |
| Acierto con/sin parcial, paseo aleatorio, 1.500 días | 30,7 % vs **48,2 %** por filas / **41,0 %** por posición |
| Suma P&L operaciones vs días (parcial, 600 días) | −19.605,50 = −19.605,50 |
| Parcial exigiendo +1 tick | sin cambio material (−49.996 → −49.788 $) |
| `--desde` con calentamiento | 1ª operación **18 días naturales** tarde |
| `BrokerSimulado.cerrar_todo` + stop vivo | abre −4 cortos fantasma |
| IC 95 % de 35 % con n≈16 / n≈8 | 18 %-61 % / 14 %-69 % |

Sin los datos reales no puedo confirmar ni desmentir los números de fondeo; lo que sí puedo decir es que **la incertidumbre que los rodea es mucho mayor que la que el documento de estado transmite**.
