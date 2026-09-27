# El plan de Aleix Andreu, simulado

*27-sep-2026. A partir de un audio suyo (su "paso a paso para la primera cuenta de fondeo y el
primer payout"), dos capturas de sus reels y el inicio de su vídeo fijado (el sistema de entrada,
del que tenemos el paso 1 de 3).*

## Su plan

| | Evaluación (challenge) | Cuenta fondeada |
|---|---|---|
| Firmas | Topstep y Alpha Futures, cuentas de 50K | Las mismas |
| Actitud | "Agresiva": no tratarla como una fondeada | "Con respeto" |
| Riesgo por operación | 1.000 $ (3–5 contratos): **"dos balas"** | 350 $ (1 contrato) |
| Objetivo | 1.500 $ (1,5R) | 700 $ (2R) |
| Cómo se aprueba / se cobra | Dos operaciones ganadoras seguidas de 1.500 $ en días distintos (objetivo de 3.000 $ con el 50 % de consistencia) | Dos aciertos, completar los días ganadores y retirar ~1.000 $ |
| Tipo de estrategia | "Win rate alto y RR bajo" | |
| Antes de nada | Backtest para comprobar que la estrategia es rentable para pasar cuentas | |

## Lo que dice la simulación

Mismas herramientas que en la vuelta 2 (`comparar-firmas`), 1.000 trayectorias por caso,
120 sesiones de cuenta fondeada cobrando todo lo que las reglas permiten. "Ventaja" = esperanza
por operación en R, ya descontados costes.

**Su plan frente a riesgo constante de 250 $ (objetivo 2R):**

| Ventaja (acierto a 1,5R) | Plan Aleix en Topstep | Riesgo 250 $ en Topstep | Plan Aleix en Alpha | Riesgo 250 $ en Alpha |
|---|---|---|---|---|
| 0 (40 %) | aprueba 29 % en **4 sesiones**, cobra 14 %, **136 $** | aprueba 25 % en 36 sesiones, cobra 16 %, 67 $ | aprueba 29 %, cobra 14 %, **99 $** | cobra 16 %, −63 $ |
| +0,1 R (44 %) | aprueba 36 % en 4 sesiones, cobra 22 %, 380 $ | aprueba 40 % en 37 sesiones, cobra 32 %, **410 $** | 354 $ | 293 $ |
| +0,2 R (48 %) | aprueba 43 % en 4 sesiones, cobra 30 %, 873 $ | aprueba 58 % en 33 sesiones, cobra 48 %, **1.104 $** | 857 $ | **1.014 $** |
| +0,35 R (54 %) | aprueba 53 %, cobra 43 %, 2.371 $ | aprueba 81 %, cobra 75 %, **3.294 $** | 2.370 $ | **3.255 $** |

**Mejor combinación encontrada** (riesgo en evaluación 250–1.000 $ y en fondeada 250–350 $, objetivos 1,5R o 2R):

| Ventaja | Topstep | Alpha |
|---|---|---|
| +0,1 R | 250 $ @ 1,5R en las dos fases → 583 $ | 250 $ @ 2R y fondeada 250 $ @ 1,5R → 470 $ (con 500 $ @ 1,5R en la evaluación: 461 $ aprobando en 14 sesiones en vez de 38) |
| +0,2 R | 250 $ @ 1,5R en las dos fases → **1.642 $** | 250 $ @ 1,5R en las dos fases → **1.535 $** |

### Dónde tiene razón

1. **Backtest antes de comprar nada.** Es exactamente el método de este proyecto.
2. **"Win rate alto y RR bajo funciona mejor":** confirmado dos veces (vuelta 2 y aquí). Su propio
   plan mejora si en la fondeada usa 1,5R en vez de 2R.
3. **Su plan está hecho a medida de Topstep y Alpha:** el 50 % de consistencia permite aprobar con
   dos días de 1.500 $. En firmas con consistencia del 30 % (MFFU, TradeDay) su plan rinde mucho peor.
4. **Velocidad:** aprueba o suspende en ~4 sesiones de mediana. Si la ventaja es modesta, gastar
   poco tiempo por intento tiene valor aunque no salga en el valor por cuenta.

### Dónde los números no le dan la razón

1. **"Dos balas" maximiza la velocidad, no el dinero.** Con ventaja real, arriesgar 250 $ en lugar
   de 1.000 $ deja un 20–40 % más por cuenta porque se suspende mucho menos (58 % frente a 43 % de
   aprobados con +0,2 R).
2. **Sin ventaja su plan es una lotería:** aprueba el 29 % y cobra el 14 %. Que el valor esperado
   salga ligeramente positivo es el efecto "opción" (pierdes como mucho la cuota); en real, con
   errores y deslizamiento, ronda cero.
3. **350 $ en la fondeada es algo más de lo óptimo:** con 250 $ se sobrevive más y se cobra más veces.

### Costes de operar así

Arriesgar 1.000 $ con 3–5 contratos obliga a stops muy cortos:

| Tamaño | Stop | Objetivo 1,5R | Comisión + deslizamiento por operación perdedora |
|---|---|---|---|
| NQ × 3 | 16,7 puntos | 25 puntos | 45 $ = **0,045 R** |
| NQ × 5 | 10 puntos | 15 puntos | 75 $ = **0,075 R** |
| MNQ × 30 | 16,7 puntos | 25 puntos | 75 $ = 0,075 R |
| MNQ × 50 | 10 puntos | 15 puntos | 125 $ = 0,125 R |

Con stops de 10 puntos la estrategia necesita una ventaja bruta clara solo para cubrir costes; es
el terreno donde el estudio de MPM vio que la ventaja del FVG desaparece. Mejor 3 minis que 50 micros.

### Compatibilidad con el bot

- **Topstep:** bot permitido vía API TopstepX, ejecutando desde tu propio ordenador.
- **Alpha Futures:** **prohíbe los bots** en todas las cuentas; solo modo copiloto (el bot avisa y tú ejecutas).

### Sobre "10 payouts en 10 cuentas esta semana"

Con su plan, incluso con una ventaja fuerte (+0,35 R), cobra ~43 % de las cuentas compradas. Diez
de diez solo cuadra contando **las cuentas que ya estaban fondeadas**, no los challenges
suspendidos por el camino. No es incompatible con lo que dice, pero conviene leerlo así. Tiene
además interés comercial (enlaza su sistema en la bio) y la CNMV ha advertido sobre cuentas
fondeadas vinculadas a cursos: razón de más para verificarlo todo con backtest.

## Plan recomendado (combinando su método y los números)

1. **Backtest primero** (su paso 1 y el nuestro): solo seguimos si la estrategia da ≥ +0,1 R neta
   fuera de muestra.
2. **Firma:** Topstep para el bot; Alpha solo en modo copiloto.
3. **Estrategia de acierto alto y objetivo corto** (~1,5R).
4. **Evaluación:** 250 $ por operación si priorizas valor; hasta 500 $ si priorizas rapidez (aprueba
   en ~2–3 semanas perdiendo poco valor). 1.000 $ solo si aceptas suspender más de la mitad.
5. **Fondeada:** 250 $ @ 1,5R y retirar en cuanto lo permitan las reglas.

## Su sistema de entrada (vídeo fijado): lo que tenemos

La mayor parte del vídeo es presentación del "Vision Club" (su historia, testimonios de alumnos con
retiros) y la estrategia se corta al empezar el **paso 1 de 3**:

> Paso 1: saber hacia dónde va el precio = la **draw on liquidity (DOL)**, el objetivo del precio.
> Para determinarla: "¿qué FVG se están respetando y qué FVG no se están respetando?"

**Implementado** como filtro de dirección `flujo_fvg` en la estrategia `fvg`
(`cajanegra/strategies/fvg.py`, clase `FvgOrderFlow`), con tests:

- FVG alcista **respetado** (el precio vuelve al hueco y la vela no cierra por debajo) → sesgo alcista.
- FVG alcista **no respetado** (una vela cierra por debajo) → sesgo bajista. Simétrico para bajistas.
- El sesgo lo marcan los últimos `flujo_eventos` eventos si coinciden; se mide en velas de
  `flujo_timeframe_min` minutos (15 por defecto) y los FVG sin resolver caducan a los `flujo_dias` días.

```bash
python -m cajanegra backtest --datos data/nq_1m.parquet --estrategia fvg \
    --param filtro_tendencia=flujo_fvg --param direccion=ambas --param flujo_timeframe_min=15
```

Limitación: con datos solo de la sesión de Nueva York no vemos los FVG de la noche (Asia/Londres),
que un trader ICT sí usa. Con datos de 24 h se puede ampliar.

**Faltan los pasos 2 y 3** (previsiblemente: dónde esperar la entrada y qué la confirma). Si pegas el
resto de la transcripción, los convierto en reglas igual que el paso 1.

## Capturas: reglas de la cuenta fondeada

Las capturas confirman la gestión del challenge (2 balas, 2 %, 1:1,5, dos TP de 1.500 $ con el
50 % de consistencia) y añaden la de la fondeada: **solo trades A+, riesgo del 0,5–1 %, objetivo de
llevar la cuenta a +4 % (+2.000 $)** antes de retirar (con el 50 % retirable salen ~1.000 $).

Simulación (challenge de Aleix fijo, 1.500 trayectorias, Topstep y Alpha):

| Fondeada | Ventaja +0,1 R: cobra / valor | Ventaja +0,2 R: cobra / valor |
|---|---|---|
| 0,5 % (250 $) @ 1,5R, retirar en cuanto se pueda | 30 % / 437 $ | 38 % / 996 $ |
| 0,5 % @ 1,5R, esperar a +4 % (Aleix) | 21 % / 395 $ | 32 % / 976 $ |
| 1 % (500 $) @ 1,5R, retirar en cuanto se pueda | 20 % / 442 $ | 27 % / 1.046 $ |
| 1 % @ 1,5R, esperar a +4 % (Aleix) | 17 % / 434 $ | 24 % / 1.054 $ |

*(Topstep; Alpha da cifras casi iguales. Con 2R todas las variantes salen algo peor que con 1,5R.)*

- **Esperar a +4 % no cambia el valor esperado**: se cobra menos veces pero más cantidad. Dado el
  riesgo de que la firma cierre o cambie reglas, **mejor retirar en cuanto se pueda**.
- Su rango de **0,5–1 % es razonable**; el 0,5 % cobra más a menudo, el 1 % algo más de valor.
- "Solo trades A+" significa operar menos y con más acierto: coherente con todo lo anterior, pero
  solo el backtest dirá qué es un A+ en reglas.
- Lo que más valor quita sigue siendo **el challenge con 2 balas**: con una ventaja real, pasar a
  250 $ @ 1,5R en la evaluación sube el valor por cuenta de ~440 $ a ~580 $ (+0,1 R) y de ~1.050 $ a
  ~1.640 $ (+0,2 R), a costa de tardar semanas en vez de días.

## Sobre los testimonios

Los casos del vídeo (retiros de 12.000–24.000 €, "cuatro payouts en dos meses") son los que
salieron bien: él mismo dice que no todos los que aprenden la estrategia obtienen resultados, y no
da cuántos de los "más de 150" alumnos cobran de forma sostenida. Frente a eso, las tasas generales:
~7 % de los traders de fondeo llega a cobrar y el 97 % de quienes hacen day trading durante más de
300 días pierde dinero. No dice que su sistema no funcione; dice que hay que medirlo nosotros.

## Lo que necesitamos de Aleix

El resto del vídeo fijado (pasos 2 y 3). Preguntas concretas:

1. ¿Qué opera exactamente: NQ, ES, micros? ¿En qué horario?
2. ¿Qué es para él un mercado alcista y en qué temporalidad lo mira?
3. ¿Qué FVG vale (temporalidad, tamaño, "el primero" desde qué hora)?
4. ¿Dónde entra, dónde pone el stop (¿10–17 puntos de NQ?) y dónde el objetivo?
5. ¿Qué días no opera (noticias, huecos...)?

## Reproducirlo

```bash
python -m cajanegra comparar-firmas \
  --reglas config/reglas/firmas/topstep_50k.toml config/reglas/firmas/alpha_standard_50k.toml \
  --riesgo 1000 --payoff 1.5 --riesgo-fondeada 350 --payoff-fondeada 2 --esperanza 0,0.1,0.2,0.35
```

Con datos reales: dos backtests de la misma estrategia (riesgo de evaluación y de fondeada) y
`rolling_starts(dias_eval, firma, days_funded=dias_fondeada)` en `cajanegra/research/evaluation.py`.

Fuentes de reglas: [Alpha Futures consistencia](https://help.alpha-futures.com/en/articles/9492048-consistency-rule) ·
[Alpha Futures Standard](https://help.alpha-futures.com/en/articles/11632512-standard-account-overview) ·
[Alpha Futures retiros](https://help.alpha-futures.com/en/articles/9492051-payout-policy) ·
[Alpha Futures prácticas prohibidas](https://help.alpha-futures.com/en/articles/9508585-prohibited-trading-practices) ·
[Alpha Standard (terceros)](https://saveonpropfirms.com/blog/alpha-futures-standard-plan) · resto en [`fondeo.md`](fondeo.md).
