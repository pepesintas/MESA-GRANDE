# CAJA NEGRA — notas para Claude

- Proyecto en español de cara al usuario (README, CLI, informes, parámetros de estrategia);
  identificadores internos en inglés.
- Ejecuta `python -m pytest` antes de cualquier commit. `tests/test_strategies.py::test_no_edge_on_random_walk`
  es el detector de lookahead: nunca lo relajes para que pase.
- Invariantes del motor (`cajanegra/engine/backtest.py`): la estrategia solo ve barras hasta la actual;
  las órdenes se ejecutan desde la barra siguiente; fills conservadores (stop antes que objetivo,
  límites exigen cruzar el nivel). Cualquier cambio que haga los resultados "mejores" es sospechoso.
- pandas 3 usa resolución µs en fechas: convierte con `.as_unit("ns")` antes de usar `.asi8`.
- Las reglas de firmas en `config/reglas` son plantillas ilustrativas; no afirmes que son las de una firma real.
- Nunca subas datos de mercado (`data/`) ni `.env`.
