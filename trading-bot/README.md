# CAJA NEGRA · bot de day trading para cuentas de fondeo

Laboratorio para **investigar, validar y (más adelante) operar** estrategias intradía en
futuros de índices (Nasdaq `NQ/MNQ`, S&P `ES/MES`...) pensando desde el primer día en las
**reglas de las firmas de fondeo**.

> Por fuera es una caja negra (datos → señales). Por dentro cada regla es explícita y
> comprobable: una regla que no se puede testear no se puede operar con dinero.

## La idea en una frase

Antes de comprar una sola cuenta, el sistema responde con datos reales a:
**«Con esta estrategia y las reglas de esta firma, ¿qué probabilidad tengo de aprobar,
de cobrar, y cuánto gano o pierdo de media por cada cuenta que compro?»**

## Arquitectura

```
 datos históricos 1m ──► MOTOR DE BACKTEST ──► resúmenes diarios ──► SIMULADOR DE FONDEO
 (Databento / CSV)        (sin mirar al futuro,    (pnl, peor y mejor      (reglas de la firma:
                           fills conservadores)     momento intradía)       drawdown, límite diario,
        ▲                        ▲    ▲                                     consistencia, costes)
        │                        │    │                                            │
 calendario de noticias ─────────┘    └── ESTRATEGIA (ORB, primer FVG, ...)        ▼
 (bloqueo CPI/FOMC/NFP)                  + GUARDIÁN DE RIESGO DIARIO     P(aprobar), P(cobrar),
                                                                          valor esperado por cuenta
                                   WALK-FORWARD: optimiza en el pasado,
                                   valida en el tramo que no vio
```

| Módulo | Qué hace |
|---|---|
| `cajanegra/data` | Carga CSV/Parquet (cualquier zona horaria), recorta la sesión (Nueva York, Londres), genera datos sintéticos, descarga de Databento. |
| `cajanegra/engine` | Motor barra a barra. La estrategia decide al cierre de cada vela; ejecuta desde la siguiente. |
| `cajanegra/strategies` | `orb` (ruptura del rango de apertura) y `fvg` (primer Fair Value Gap a favor del sesgo). |
| `cajanegra/risk` | Guardián diario (pérdida máxima, nº de operaciones, pérdidas seguidas) y reglas de fondeo. |
| `cajanegra/research` | Métricas, tabla por año, walk-forward, simulación de evaluación y valor esperado. |
| `cajanegra/news` | Calendario económico y ventanas de bloqueo alrededor de noticias de alto impacto. |
| `config/reglas` | Plantillas TOML de firmas (futuros trailing al cierre, trailing intradía, CFD dos fases). |

## Puesta en marcha

```bash
cd trading-bot
pip install -e ".[dev,parquet]"
python -m pytest            # incluye un detector de "mirar al futuro"
python -m cajanegra demo    # recorrido completo con datos sintéticos
python -m cajanegra estrategias   # parámetros disponibles
```

### Backtest con datos reales

```bash
# 1) Datos: consulta el coste y descarga (Databento, de pago por uso; clave en .env)
python -m cajanegra descargar --simbolo NQ.v.0 --desde 2016-01-01 --hasta 2026-09-01 --solo-coste
python -m cajanegra descargar --simbolo NQ.v.0 --desde 2016-01-01 --hasta 2026-09-01 --salida data/nq_1m.parquet

# 2) Estrategia + evaluación de la firma
python -m cajanegra backtest --datos data/nq_1m.parquet --instrumento MNQ \
    --estrategia fvg --param riesgo_usd=250 --param max_contratos=50 \
    --max-perdida-dia 600 --max-operaciones 2 \
    --reglas config/reglas/futuros_50k_trailing_cierre.toml --salida resultados/fvg_base

# 3) Validación honesta: optimiza en 2 años, prueba en los 6 meses siguientes, y avanza
python -m cajanegra walkforward --datos data/nq_1m.parquet --estrategia fvg \
    --grid objetivo_r=1.5,2,3 --grid entrada=borde,medio --grid timeframe_min=1,5 \
    --reglas config/reglas/futuros_50k_trailing_cierre.toml
```

```bash
# 4) ¿Qué firma conviene más para una misma estrategia? (reglas reales en config/reglas/firmas)
python -m cajanegra comparar-firmas --esperanza 0,0.1,0.2 --riesgo 150,200,250,350
```

Investigación de firmas (política de bots, reglas, costes, comparativa): [`docs/fondeo.md`](docs/fondeo.md).
Probabilidades, win rate y plataformas de backtesting: [`docs/probabilidades_y_backtesting.md`](docs/probabilidades_y_backtesting.md).

Cualquier CSV sirve si tiene fecha/hora y `open, high, low, close[, volume]`. Opciones:
`--tz-datos America/New_York` si las horas vienen sin zona, `--etiqueta end` si el
timestamp marca el cierre de la vela, `--sin-cabecera` para ficheros sin cabecera.

## Estrategias

**`fvg` — primer FVG a favor de la tendencia** (hipótesis de la estrategia de @aleixandreu).
FVG alcista = mínimo de la vela 3 por encima del máximo de la vela 1 (vela 2 de
desplazamiento). Con los valores por defecto: solo largos cuando el cierre de ayer está
sobre la media de 20 días, se toma el **primer** FVG tras las 09:30 (hora de Nueva York),
entrada límite en el borde del hueco, stop bajo la vela 1, objetivo 2R, sin entradas
después de las 11:00. Todo es parametrizable (`timeframe_min`, `entrada=medio`,
`stop=fvg`, `filtro_tendencia=media_diaria+apertura`, ...). **Hay que ajustarlo a sus
reglas exactas** en cuanto las tengamos.

**`orb` — ruptura del rango de apertura.** Referencia pública (Zarattini & Aziz, 2023)
para tener siempre un punto de comparación.

### Añadir una estrategia (p. ej. de un creador de contenido)

1. Escribe las reglas **sin ambigüedad**: sesgo, qué patrón, dónde entra, dónde va el stop,
   dónde sale, a qué horas, cuántas operaciones al día. Si no se puede escribir así, no se
   puede probar.
2. Crea `cajanegra/strategies/mi_estrategia.py` heredando de `Strategy` (mira `fvg.py`):
   `on_day_start(ctx)` y `on_bar(ctx)`; usa `ctx.highs`, `ctx.closes`, `ctx.daily`, `ctx.submit(Order(...))`.
3. Regístrala en `cajanegra/strategies/__init__.py` y añade un test con velas a mano.

## Reglas de fondeo (`config/reglas/*.toml`)

Cada firma se describe con una o más `[[fase]]`, una `[fondeada]` (el objetivo es el
beneficio necesario para el primer retiro) y `[economia]`. Tipos de drawdown:

- `estatico`: el suelo no se mueve.
- `trailing_cierre`: el suelo sube con el balance al cierre del día.
- `trailing_intradia`: el suelo sube con el **flotante máximo** del día (el más duro).
- `bloqueo_drawdown`: el suelo deja de subir al llegar a `capital_inicial + bloqueo`.

`perdida_diaria_max` con `accion_perdida_diaria = "suspende_dia"` (te cierran y paras hoy)
o `"elimina"` (pierdes la cuenta). También `dias_minimos`, `dias_ganadores_minimos`,
`consistencia_max_dia`, `dias_maximos`, `max_contratos` (en micros se multiplica por 10).

⚠ **Las plantillas llevan números ilustrativos.** Las reglas de las firmas cambian a menudo:
copia las vigentes de la tuya antes de fiarte de nada.

## Modelo de ejecución (conservador a propósito)

- La estrategia decide al **cierre** de cada vela; sus órdenes solo se ejecutan desde la siguiente.
- Mercado y stops: 1 tick de deslizamiento por lado (configurable). Si el precio abre más
  allá del nivel, se ejecuta en la apertura (peor precio).
- Límites: el precio tiene que **cruzar** el nivel; tocarlo no basta.
- Si stop y objetivo caben en la misma vela, se asume que saltó el **stop**.
- En la vela de una entrada intrabarra solo se evalúa el stop.
- El equity intradía usa los extremos de cada vela (así se miden las reglas de las firmas).
- Test de control: en un paseo aleatorio el resultado bruto medio debe ser ≈ 0R. Si una
  estrategia "gana" ahí, hay un bug.

## Hoja de ruta

| Fase | Qué | Estado |
|---|---|---|
| 1. Laboratorio | Motor, reglas de fondeo, evaluación, walk-forward, ORB, FVG | ✅ hecho |
| 2. Datos reales | 8–10 años de NQ/ES en 1 minuto + calendario histórico de noticias | siguiente |
| 3. Estrategias | Codificar las reglas exactas de Aleix y otras; validar fuera de muestra | |
| 4. Copiloto | Señales en tiempo real por Telegram (entrada, stop, objetivo, tamaño) + informe premercado con noticias | |
| 5. Papel | 1–2 meses en demo comparando real vs. backtest | |
| 6. Fondeo | 1 evaluación, modo copiloto o automático **si la firma lo permite** | |
| 7. Escalar | Más cuentas solo si lo real cuadra con lo simulado | |

## Advertencias honestas

- Ningún backtest garantiza nada. El enemigo nº 1 es el **sobreajuste**: una estrategia
  retorcida hasta que el pasado sale bonito. Por eso el walk-forward y los datos fuera de muestra.
- Muchas firmas **limitan o prohíben** bots totalmente automáticos, el HFT o copiar
  operaciones entre cuentas de distintas personas. Revisa sus términos antes de automatizar;
  el modo copiloto (el bot avisa, tú ejecutas) es compatible con casi todas.
- Varias cuentas con la misma estrategia **no diversifican**: aprueban y suspenden a la vez.
- Los datos de mercado (`data/`) y las claves (`.env`) nunca se suben al repositorio.
