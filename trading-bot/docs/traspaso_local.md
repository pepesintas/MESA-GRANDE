# Traspaso a tu Mac (sesión local)

*27-sep-2026. La sesión pasa de la nube a tu ordenador para poder usar el vídeo de Aleix
(`~/Downloads/videoplayback.mp4`), descargar datos reales sin bloqueos y, más adelante, ejecutar
el bot desde tu propio equipo (Topstep exige operar desde tu ordenador, no desde un servidor).*

## 1. Mover la sesión (Terminal del Mac)

```bash
# Claude Code, si no lo tienes
curl -fsSL https://claude.ai/install.sh | bash

# el proyecto
git clone https://github.com/pepesintas/MESA-GRANDE.git
cd MESA-GRANDE

# traer esta sesión con toda la conversación (elige "Bot de trading automático")
claude --teleport
```

Requiere haber iniciado sesión con tu cuenta de claude.ai (`/login` dentro de Claude si lo pide).
A partir de aquí se trabaja **en la sesión local**; la de la nube queda como estaba.

## 2. Preparar el entorno (lo puede hacer Claude en local)

```bash
brew install python@3.12 ffmpeg          # el proyecto necesita Python 3.11 o superior
cd trading-bot
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,parquet]"
python -m pytest                          # deben pasar todos los tests
```

## 3. Pendientes, en orden

1. **Vídeo de Aleix → fotogramas** (fuera del repo, que es público):
   ```bash
   mkdir -p ~/Downloads/fotogramas_aleix/hojas
   # hojas de contacto: 16 fotogramas por imagen, uno cada 5 s, para localizar los gráficos
   ffmpeg -i ~/Downloads/videoplayback.mp4 -vf "fps=1/5,scale=480:-1,tile=4x4" ~/Downloads/fotogramas_aleix/hojas/h_%03d.png
   # después, fotogramas a tamaño completo de los momentos clave, p. ej. minuto 7:12
   ffmpeg -ss 00:07:12 -i ~/Downloads/videoplayback.mp4 -frames:v 1 ~/Downloads/fotogramas_aleix/m07s12.png
   ```
   Buscar en los tres ejemplos (26-ago, 28-ago y 8-sep): dónde pone **exactamente el stop**, si entra
   a mercado o en el retesteo del IFVG, dónde está el **take profit**, temporalidades y hora de la vela.
2. **Resto de subtítulos de Aleix** → completar `docs/aleix.md` y ajustar los parámetros de la
   estrategia `aleix` (stop, entrada, sesiones, uso del S&P, qué es un "trade A+").
3. **Datos reales del NQ:** clave de Databento en `trading-bot/.env`, consultar coste y descargar:
   ```bash
   python -m cajanegra descargar --simbolo NQ.v.0 --desde 2016-01-01 --hasta 2026-09-26 --solo-coste
   ```
4. **Validar el bot con los ejemplos de Aleix:** en esos tres días el bot debe marcar la misma
   dirección, zona e IFVG que él. Si no, ajustar antes de mirar resultados.
5. **Backtests de 10 años y walk-forward** de `aleix` y `zona_ruido`; simulación con las reglas de
   Topstep y del plan de gestión de Aleix (`docs/aleix.md`, sección "Reproducirlo").
6. **Vuelta 4** (ejecución: API de TopstepX desde el Mac, modo copiloto) y **vuelta 5**
   (recomendación final y plan de compra) de la investigación.

## Dónde está cada cosa

| Documento | Contenido |
|---|---|
| `README.md` | El sistema, comandos y hoja de ruta |
| `docs/fondeo.md` | Firmas: política de bots, reglas, costes, comparativa |
| `docs/estrategias.md` | Estrategias con evidencia y su encaje con las firmas |
| `docs/probabilidades_y_backtesting.md` | Tasas base, win rate, plataformas y protocolo de backtest |
| `docs/aleix.md` | Su plan de gestión simulado y su sistema de 3 pasos |
| `CLAUDE.md` | Reglas del proyecto para Claude |

Nunca subir al repo: vídeos, fotogramas, subtítulos de cursos, datos de mercado (`data/`) ni claves (`.env`).
