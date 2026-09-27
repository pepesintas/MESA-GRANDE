# El plan de Aleix Andreu, simulado

*27-sep-2026. A partir de un audio suyo (su "paso a paso para la primera cuenta de fondeo y el
primer payout"), dos capturas de sus reels y la transcripción de su vídeo fijado (el sistema de
entrada en 3 pasos, implementado como la estrategia `aleix`).*

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

## Su sistema de entrada (vídeo fijado): los 3 pasos

La mayor parte del vídeo es presentación del "Vision Club" (su historia, testimonios). La estrategia:

1. **Dirección = draw on liquidity (DOL)**, en temporalidad mayor (**15 min o 1 h**): "¿qué FVG se
   están respetando y cuáles no?". Respetado = el precio lo mitiga **y da un impulso** hacia un
   nuevo punto estructural; no respetado = el precio lo atraviesa ("se lo revienta"). Si se
   respetan los bajistas y no los alcistas, el objetivo son **los mínimos de esa temporalidad**
   (y al revés).
2. **Zona de reacción:** un FVG de esa temporalidad a favor de la dirección al que el precio vuelve
   en retroceso ("entrar cuando el precio aún esté debajo, no arriba").
3. **Confirmación en 1 min (a veces 30 s): IFVG.** Dentro de la zona, un FVG en contra que el precio
   "se come": ahí entra, **"con el stop loss debajo y el take profit en el objetivo"**. Operaciones
   rápidas (en su ejemplo, 3 minutos): "SL o TP".

**Implementado como la estrategia `aleix`** (`cajanegra/strategies/aleix.py`), con tests que
reproducen su ejemplo de venta vela a vela, el espejo de compra y los casos en que no debe operar.

| Parámetro | Por defecto | Qué es |
|---|---|---|
| `htf_min` / `ltf_min` | 15 / 1 | Temporalidades de los pasos 1–2 (él usa 15 min o 1 h) y del paso 3 |
| `respeto` | `impulso` | FVG respetado = lo mitiga y después cierra al otro lado a favor (`toque`: basta con tocarlo) |
| `zona_minutos` | 60 | Cuánto espera la confirmación tras tocar la zona |
| `stop` | `ifvg` | **Verificado con sus dos ejemplos:** el stop se ajusta al borde del IFVG de 1 min, no al extremo de todo el retroceso (`extremo`: opción alternativa, sigue disponible) |
| `objetivo` | `dol` | **Take profit en el objetivo** (máximos/mínimos de la temporalidad mayor o de ayer). `r`: fijo, como en su challenge |
| `objetivo_r` / `exigir_dol` | 1,5 / sí | Ratio mínimo hasta el objetivo para aceptar la operación (y ratio del objetivo fijo) |
| `objetivo_r_max` | 2,0 | **Verificado:** "si el objetivo está muy lejos, targetea directamente un 1 a 2" → tope al objetivo=dol en 2R; `None` lo desactiva |
| `hora_limite_entrada` | 11:30 | Sesión de la mañana de Nueva York (él dedica ~2 h al día) |
| `max_operaciones` | 1 | Una por día (su challenge busca 1 TP por día por la consistencia) |

```bash
# su sistema tal cual (objetivo en la DOL) con el riesgo de su challenge
python -m cajanegra backtest --datos data/nq_1m.parquet --instrumento NQ --estrategia aleix \
    --param riesgo_usd=1000 --param max_contratos=5 --reglas config/reglas/firmas/topstep_50k.toml
# su challenge literal: objetivo fijo 1,5R
python -m cajanegra backtest --datos data/nq_1m.parquet --instrumento NQ --estrategia aleix \
    --param objetivo=r --param riesgo_usd=1000 --param max_contratos=5
# ¿qué variantes aguantan fuera de muestra?
python -m cajanegra walkforward --datos data/nq_1m.parquet --instrumento NQ --estrategia aleix \
    --grid htf_min=15,60 --grid stop=extremo,ifvg --grid objetivo=dol,r --grid zona_minutos=30,60,120
```

En datos sintéticos opera poco (≈ 1 de cada 8 sesiones con todos los filtros): encaja con sus
"solo trades A+". Recordatorios: el estudio de MPM no encontró ventaja neta en el FVG solo, pero
este sistema añade dirección de 15 min + zona + inversión en 1 min, así que merece su propia prueba;
y con stops cortos los costes pesan (0,045–0,075 R por operación con minis, ver arriba).

También existe el filtro `flujo_fvg` en la estrategia `fvg` (solo el paso 1), útil para probar la
dirección de Aleix con otras entradas.

### Validado con sus propios ejemplos (fotogramas del vídeo, TradingView, NQ1!)

Extraídos con ffmpeg del vídeo fijado (nunca subido al repo: ver `traspaso_local.md`). En los dos
casos usó la herramienta de posición de TradingView, que muestra el precio y el R:R exactos:

| Fecha (real, en el gráfico) | Lado | Entrada | Stop | Objetivo (DOL) | Distancia stop | R:R |
|---|---|---|---|---|---|---|
| 8-sep-2026, ~10:00 hora NY (justo en la apertura) | Venta | 29.502,75 | 29.535,25 | 29.447,75 | 32,5 pt | 1,66 |
| 26-ago-2026, ~08:15 hora NY (**antes** de las 09:30) | Compra | 29.605,75 | 29.568,50 | 29.681,00 | 37,25 pt | 2,02 |

Confirma: instrumento **NQ1!** (Nasdaq-100 continuo), temporalidad mayor **15 min**, estructura del
mercado analizada usando también velas de horas previas (en el ejemplo del 8-sep mira desde la
01:15, sesión de Asia/Londres, aunque la entrada dispara en NY), y el indicador de terceros
**"LuxAlgo - Sessions"** activo en su gráfico (marca las sesiones). El stop en los dos casos es
mucho más corto que el tamaño de la zona de 15 min: confirma `stop="ifvg"`, no el retroceso completo.
Con datos reales de esos dos días, el primer test será comprobar que el bot marca la misma dirección,
zona e IFVG que él; si no coinciden, se ajustan los parámetros antes de mirar ningún resultado.

**Nuevo, de la última parte del vídeo:** "si el objetivo está muy lejos, targetea directamente un
1 a 2" → implementado como `objetivo_r_max=2.0` (tope al objetivo=dol; su segundo ejemplo, R:R 2,02,
es justo ese caso). Repitió también, calculadora en mano, la gestión de cuentas del primer audio:
evaluación 50.000→53.000 $ con dos TP de 1.500 $ (1:1,5, arriesgando 1.000 $), y fondeada con 5 días
de 150 $+ para poder retirar. **Un matiz a vigilar:** en su propia calculadora del club, con un
beneficio de 1.300 $ retira los **1.300 $ enteros**, no el 50 % — puede ser porque el 50 % es un
tope sobre el *balance* (no sobre el beneficio) y con beneficios pequeños nunca se alcanza, lo que
sería coherente con nuestro modelo; o puede que su calculadora simplifique la regla real de la
firma. Tratar sus cifras de retiro con margen hasta confirmarlo con la firma elegida.

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

## Lo que falta por confirmar de su sistema

Resuelto con el vídeo completo (48 min revisados fotograma a fotograma) y sus dos ejemplos reales:
el objetivo es la DOL con tope en 2R si queda muy lejos, la dirección se mira en 15 min o 1 h,
"respetar" incluye el impulso posterior, **el stop va justo tras el borde del IFVG de 1 min** (no
el extremo de todo el retroceso), y **no hay ningún gráfico del S&P en todo el vídeo** — sin
evidencia de que use divergencia SMT (puede que lo mencione en otro vídeo suyo). Sesiones:
confirmado que al menos un ejemplo entra a las 08:15 hora de Nueva York, **antes** de la apertura
(09:30) — no opera exclusivamente en el rango 09:30–11:30 que supusimos al principio. Queda:

1. **Cómo entra exactamente:** ¿a mercado al cerrar la vela que invierte, o con límite en el
   retesteo del IFVG? El precio de entrada en sus dos ejemplos coincide con un nivel estructural
   limpio, lo que sugiere posible límite; mantenemos mercado (opción conservadora) hasta confirmar.
2. **El rango horario completo:** con un solo dato (08:15) no sabemos si opera toda la sesión de
   Asia/Londres o solo desde poco antes de Nueva York. Con datos de 24 h se puede acotar mejor
   viendo en qué horas aparecen sus configuraciones en más días.
3. **Qué es exactamente un "trade A+"** en la cuenta fondeada (probablemente: un setup con los 3
   pasos muy limpios y buen R:R, pero no lo define con esas palabras en este vídeo).
4. **La regla de retiro exacta** de la firma que use de verdad (ver el matiz sobre el 50 % arriba).

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
