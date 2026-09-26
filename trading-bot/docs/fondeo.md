# Fondeo: mapa de opciones para CAJA NEGRA

*Investigación en curso (bucle de exploración). Vuelta 1 (mapa) y vuelta 2 (comparativa): 26-sep-2026.*
*Las reglas de las firmas cambian a menudo: todo lo de aquí se verifica en la web oficial
el día de comprar. Marcado **(oficial)** = centro de ayuda/web de la firma;
**(terceros)** = comparadores o blogs, a menudo con enlaces de afiliado.*

## Resumen de la vuelta 1

1. **El filtro nº 1 para nosotros es la política de bots en la cuenta FONDEADA**, no en la
   evaluación. Varias firmas grandes dejan usar bots para aprobar pero los prohíben después.
2. **Permiten bot propio en cuenta fondeada (oficial):** Topstep (vía API TopstepX, solo desde
   tu ordenador), MyFundedFutures, FundedNext Futures, TradeDay, Tradeify (bot exclusivo de
   esa firma), Lucid (con aprobación previa por escrito) y Take Profit Trader (bajo tu responsabilidad).
3. **Descartadas para bot:** Apex (prohíbe cualquier automatización en cuentas PA/Live),
   Alpha Futures y Phidias (solo semi-automático: el bot avisa, tú ejecutas).
4. **Drawdown al cierre (EOD) >> intradía** para nosotros: con el intradía, un beneficio
   flotante que no cierras te sube el suelo y te puede suspender en un simple retroceso.
5. **Riesgo de contraparte real:** más de 80 firmas cerraron entre 2024 y 2025 y en 2026 siguen
   cerrando. Retirar pronto y a menudo; no acumular beneficios dentro de la cuenta.
6. **Candidatas para modelar en la vuelta 2:** Topstep, MyFundedFutures, Lucid, Tradeify, TradeDay.

## Vías para conseguir capital

| Vía | Cómo funciona | Encaje con el bot |
|---|---|---|
| **Firma de futuros** | Pagas una evaluación; si la apruebas operas una cuenta (casi siempre simulada) y la firma te paga un % del beneficio. | ✅ Nuestra vía principal: NQ/MNQ, reglas claras, varias permiten bots. |
| **Firma CFD/forex** | Igual, con CFD del Nasdaq (NAS100/US100) en MT5, cTrader... Drawdown estático y pérdida diaria que elimina. | ⚠️ Posible (FTMO permite EAs), pero el motor está hecho para futuros; habría que adaptar tamaños y costes. |
| **Cuenta propia en un bróker** | Tu dinero, sin reglas de firma. MNQ permite empezar con poco capital. | ✅ Ideal para validar el bot con ejecuciones REALES a tamaño mínimo antes de pagar evaluaciones. |
| **Financiación instantánea** | Sin evaluación, más cara y con reglas más duras. | ❌ Peor valor esperado salvo con una ventaja ya demostrada. |
| **Historial verificable → capital externo** | Con un historial real largo se puede buscar capital de terceros. | A largo plazo y regulado; no ahora. |

## Firmas de futuros (cuenta de 50K como referencia)

| Firma | Bots en cuenta fondeada | Drawdown (50K) | Límite diario | Consistencia | Coste aprox. | Retiros |
|---|---|---|---|---|---|---|
| **Topstep** | ✅ Vía API TopstepX/ProjectX, 29 $/mes (14,50 $ con código). **Solo desde tu PC: VPS, VPN y servidores remotos prohibidos** para enviar órdenes. Sin HFT. (oficial) | 2.000 $, se actualiza al cierre pero se vigila en tiempo real con el flotante (oficial) | No en TopstepX; sí en otras plataformas (oficial) | Mejor día ≤ ~50–55 % en la evaluación; si no, sube el objetivo (oficial, verificar %) | ~49 $/mes en promoción (165 $ tarifa) + activación según plan (terceros; tiene opción "sin activación") | 90/10 desde el primer dólar en cuentas creadas desde el 12-ene-2026 (terceros) |
| **MyFundedFutures** | ✅ Estrategias propias; prohibido HFT y explotar las ejecuciones simuladas (oficial) | 2.000 $; plan Rapid trailing intradía en fondeada, variante **Rapid EOD** al cierre (oficial) | Sin límite diario en Rapid (oficial) | Sin consistencia en Rapid (oficial) | ~77–107 $ pago único según plan (terceros) | Colchón de 2.100 $ antes del primer retiro, luego cada 24 h, 90/10 (oficial) |
| **Lucid (LucidFlex)** | ✅ Bots y copiadores permitidos **con aprobación previa por escrito** (oficial) | EOD, se bloquea al superar el saldo de bloqueo (oficial) | Opcional en fondeada (oficial) | ≤ 50 % en evaluación; **ninguna en fondeada** (oficial) | ~175 $ pago único (terceros) | 5 días con beneficio mínimo por ciclo, sin colchón, 90/10 (oficial) |
| **Tradeify** | ✅ Si demuestras que el bot es tuyo; **prohibido usarlo también en otras firmas** y los bots vendidos a varios. Pueden pedir vídeo demostrando que lo controlas (oficial) | EOD vigilado en tiempo real; se bloquea en saldo inicial + 100 $ (oficial) | 1.250 $ en Growth y Lightning (oficial) | Select: mejor día ≤ 40 %; Growth: sin consistencia (oficial) | — | Select: hasta 50 % del beneficio, máx. 3.000 $ por retiro (oficial) |
| **TradeDay** | ✅ Bots propios; prohibidos los comprados a terceros o compartidos (oficial) | 2.000 $ a elegir: EOD, intradía o estático; se congela en el saldo inicial (oficial) | — | 45 % con mínimo 3 días (terceros) | Cuota mensual o única según oferta (verificar) | Desde el día 1, sin colchón, hasta 90 % (oficial) |
| **FundedNext Futures** | ✅ En challenge y fondeada vía integraciones con Tradovate; **no se puede cambiar de bot a manual (ni al revés) entre fases** (oficial) | — | — | — | — | — |
| **Take Profit Trader** | ✅ Automatización y copiadores bajo tu total responsabilidad (oficial) | PRO: intradía (oficial) | — | — | — | PRO: retiros diarios desde el día 1 por encima del colchón; hasta 5 cuentas PRO (oficial) |
| **Apex** | ❌ Prohibido en PA/Live: IA, bots, algoritmos, copy trading de terceros. Incluso exigen que la cuenta no esté "influida" por ningún otro sistema (oficial) | — | — | — | — | Solo sirve para aprobar evaluaciones; **descartada** |
| **Alpha Futures** | ❌ Prohibido en todas las cuentas; señales permitidas si tú colocas y gestionas la orden (oficial) | 4 % trailing al cierre (oficial) | — | — | Pago único (terceros) | Hasta 50 % del beneficio cada 5 días ganadores de ≥ 200 $, 90 % (oficial) |
| **Phidias** | ❌ Solo semi-automático con supervisión manual (oficial) | EOD o estático según cuenta (oficial) | — | — | Pago único, sin activación (terceros) | 80/20 a 90/10 según cuenta (oficial) |
| **Bulenox** | ❓ No encontrado | — | — | — | — | Noticias permitidas; cierre obligatorio a las 15:59 CT (oficial) |

Reglas transversales a tener en cuenta:
- **HFT y microscalping prohibidos en todas.** Tradeify exige que más del 50 % del beneficio venga
  de operaciones de al menos 10 segundos. Nuestras estrategias duran minutos: sin problema.
- **Apex obliga desde marzo de 2026 a enviar cada orden con stop y objetivo** (terceros). Nuestro
  motor ya trabaja con órdenes con stop y objetivo; es buena práctica en todas.
- **Copiar operaciones entre tus propias cuentas** suele estar permitido (Topstep lo integra;
  Take Profit Trader hasta 5 PRO). Recuerda: copiar no diversifica.

## Firmas CFD (referencia)

- **FTMO (oficial):** permite EAs/robots; tú respondes de cumplir los objetivos. Límite de
  asignación de **400.000 $ por cliente o por estrategia**: si mucha gente usa el mismo bot
  comercial, choca con ese límite. Pérdida diaria máxima del 5 % del saldo inicial, medida
  sobre el **punto más bajo de equity** del día, aunque sea un instante.
- Encaje: bueno si algún día operamos el CFD del Nasdaq, pero para NQ/MNQ son mejores las de futuros.

## Riesgo de contraparte y marco legal

- Entre 2024 y 2025 dejaron de operar más de 80 firmas; en 2026 SeacrestFunded (antes MyFundedFX)
  cerró su actividad el 6 de febrero y FundingTicks cerró de forma ordenada devolviendo el dinero (terceros).
- **Señales de alarma:** pagos que se retrasan, reglas que se endurecen, cambios aplicados hacia atrás.
- **Medidas:** preferir firmas con años de historial de pagos, retirar en cuanto se pueda, no acumular
  beneficio en la cuenta, no pagar grandes cuotas por adelantado y repartir entre dos firmas.
- **CNMV:** ha alertado del riesgo de engaño en cuentas fondeadas vinculadas a cursos y recomienda
  comprobar sus registros. Casi todas las cuentas "fondeadas" son **simuladas**: lo que cobras es un
  pago de la firma, no rendimiento de mercado. Fiscalidad en España: consultar con un asesor.

## Implicaciones para el diseño del bot

1. **Topstep obliga a ejecutar desde tu PC:** el bot tiene que correr en tu ordenador durante la
   sesión de Nueva York (15:30–22:00 hora de España), no en un servidor en la nube.
2. **Tradeify pide exclusividad:** si vamos con ellos, ese bot no se usa en otra firma.
3. **Lucid pide aprobación por escrito antes de usar el bot.**
4. **FundedNext no deja cambiar de modo entre fases:** hay que decidir bot o manual desde el primer día.
5. **Apex, Alpha y Phidias solo sirven en modo copiloto,** y en Apex ni eso con seguridad: descartadas.

## Vuelta 2: ¿qué firma conviene más? (comparativa cuantitativa)

*26-sep-2026. Reglas reales de las cinco candidatas en `config/reglas/firmas/*.toml` (cada dato
marcado como oficial, terceros o supuesto). Reproducible con `python -m cajanegra comparar-firmas`.*

**Método.** Una misma estrategia hipotética (como mucho una operación al día, el 85 % de los días,
con stop y objetivo) genera 1.000 trayectorias de días; **todas las firmas reciben exactamente los
mismos días**, así las diferencias se deben solo a sus reglas. Se simula la evaluación y, si se
aprueba, **120 sesiones de cuenta fondeada cobrando cada vez que las reglas lo permiten** (el
suelo de drawdown no baja al retirar). La ventaja se mide en R: +0,1 R = de media ganas por
operación un 10 % de lo que arriesgas, ya descontadas comisiones.

**Valor esperado por cuenta comprada** (cobros menos costes, 50K, riesgo de 250 $ por operación):

| Firma | Sin ventaja (0 R) | +0,1 R, ganancias 2R | +0,2 R, ganancias 2R | +0,1 R, ganancias 1R (más acierto) |
|---|---|---|---|---|
| LucidFlex | 23 $ | 413 $ (35 % cobra) | 1.124 $ (51 % cobra) | 860 $ (49 % cobra) |
| MFFU Rapid EOD | -19 $ | 409 $ (19 % cobra) | 1.354 $ (39 % cobra) | 503 $ (29 % cobra) |
| Topstep | 62 $ | 439 $ (35 % cobra) | 1.153 $ (52 % cobra) | 780 $ (49 % cobra) |
| TradeDay Quick Pay | 137 $ | 596 $ (39 % cobra) | 1.355 $ (56 % cobra) | 1.076 $ (52 % cobra) |
| Tradeify Select Flex | 33 $ | 423 $ (35 % cobra) | 1.134 $ (51 % cobra) | 870 $ (49 % cobra) |

### Conclusiones de la vuelta 2

1. **La firma importa menos que la ventaja y el tamaño.** Entre Topstep, Tradeify, Lucid y MFFU la
   diferencia es de ±15 %, dentro del margen de error de reglas medio supuestas. Pasar de +0,1 R a
   +0,2 R multiplica el valor por 2,5–3.
2. **Tamaño óptimo: 200–250 $ de riesgo por operación en una cuenta de 50K** (10–12 % del
   drawdown máximo). Es donde la probabilidad de cobrar es máxima en todas las firmas. Con 100 $ se
   tarda tanto que no compensa; con 500 $ o más se suspende demasiado.
3. **Sin ventaja no hay negocio.** Con riesgo moderado el valor esperado ronda cero. Solo sale
   positivo arriesgando muy fuerte (750 $ por operación), y entonces cobra solo un 8 % de las
   cuentas: es una lotería, las firmas vigilan ese comportamiento y no es un plan.
4. **A igual ventaja, más acierto con menos recorrido es mejor:** con ganancias de 1R en lugar de 2R
   la probabilidad de cobrar sube del 35 % al 49 % y el valor casi se duplica. Guía para diseñar la
   estrategia: priorizar acierto alto y salidas más cercanas.
5. **TradeDay Quick Pay sale primera en todos los escenarios** gracias a retiros desde 250 $, sin
   colchón y sin límite de porcentaje, pese a repartir 80/20 y a que su drawdown fondeado es
   intradía. Pero es la firma con reglas **menos verificadas** (casi todo de terceros): hay que
   confirmarlas antes de fiarse de este resultado.
6. **MFFU Rapid EOD** es la peor con poca ventaja (el colchón de 2.100 $ retrasa el primer cobro) y
   de las mejores con mucha ventaja.
7. **Topstep:** a su valor hay que restarle la API del bot (14,50–29 $/mes), unos 100–170 $ en seis
   meses. A cambio es la firma con más años pagando (desde 2012).

### Limitaciones

- La estrategia es un modelo estilizado. La conclusión real sale de repetir esto con los días de
  un backtest de verdad: `python -m cajanegra backtest --datos ... --reglas config/reglas/firmas/X.toml`.
- No incluye el riesgo de que la firma no pague, los impuestos, lo que queda en la cuenta al final
  del horizonte, ni el paso a cuenta real con reglas distintas tras varios cobros.
- El camino intradía (cuánto retrocede una operación ganadora antes de ganar) es un supuesto que
  pesa en las firmas con drawdown intradía.

### Lista corta para el bot (a confirmar en la vuelta 5)

| Firma | Por qué sí | Pega |
|---|---|---|
| **Tradeify Select Flex** | Bot propio permitido, EOD, sin colchón, pago único | Exclusividad: ese bot no se puede usar en otra firma |
| **Topstep** | API oficial para bots, la más veterana | Solo desde tu PC; API de pago; cuota mensual |
| **LucidFlex** | EOD, fondeada sin consistencia ni colchón | Aprobación por escrito del bot; varias reglas aún supuestas |
| **MFFU Rapid EOD** | Bots permitidos, retiros diarios | Colchón de 2.100 $ antes de cobrar |
| **TradeDay Quick Pay** | Mejor valor en el modelo | Reglas por verificar; drawdown intradía en la fondeada |

## Fuentes

Oficiales: [Topstep API](https://help.topstep.com/en/articles/11187768-topstepx-api-access) ·
[Topstep parámetros](https://help.topstep.com/en/articles/8284197-trading-combine-parameters) ·
[Topstep consistencia](https://help.topstep.com/en/articles/8284208-consistency-at-topstep) ·
[Topstep límite diario](https://help.topstep.com/en/articles/10490293-daily-loss-limit-in-the-trading-combine-and-express-funded-account) ·
[Apex actividades prohibidas](https://apextraderfunding.com/help-center/getting-started/prohibited-activities/) ·
[Apex PA](https://support.apextraderfunding.com/hc/en-us/articles/31519788944411-Performance-Account-PA-and-Compliance) ·
[Tradeify guías](https://help.tradeify.co/en/articles/10468318-guidelines-for-traders) ·
[Tradeify drawdown](https://help.tradeify.co/en/articles/10495897-rules-trailing-max-drawdowns) ·
[Tradeify Select](https://help.tradeify.co/en/articles/12853921-select-evaluation-accounts) ·
[Lucid otras actividades](https://support.lucidtrading.com/en/articles/11404728-other-activities) ·
[LucidFlex drawdown](https://support.lucidtrading.com/en/articles/12945815-lucidflex-drawdown) ·
[LucidFlex retiros](https://support.lucidtrading.com/en/articles/12945796-lucidflex-payouts) ·
[MFFU juego limpio](https://help.myfundedfutures.com/en/articles/8444599-fair-play-and-prohibited-trading-practices) ·
[MFFU Rapid 50K](https://help.myfundedfutures.com/en/articles/13134709-rapid-plan-50k-a-comprehensive-look) ·
[MFFU Rapid EOD 50K](https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look) ·
[Alpha Futures prácticas prohibidas](https://help.alpha-futures.com/en/articles/9508585-prohibited-trading-practices) ·
[Alpha Futures retiros](https://help.alpha-futures.com/en/articles/9492051-payout-policy) ·
[Phidias reglas](https://phidiaspropfirm.com/rules) ·
[TradeDay cómo funciona](https://www.tradeday.com/how-it-works) ·
[FundedNext Futures bots](https://helpfutures.fundednext.com/en/articles/14298560-is-the-usage-of-automated-trading-systems-eas-and-bots-allowed-in-fundednext-futures) ·
[Take Profit Trader términos](https://takeprofittrader.com/terms) ·
[Bulenox FAQ](https://bulenox.com/faq) ·
[FTMO estrategias permitidas](https://ftmo.com/en/faq/which-instruments-can-i-trade-and-what-strategies-am-i-allowed-to-use/) ·
[FTMO trading algorítmico](https://ftmo.com/en/blog/what-is-algorithmic-trading-and-how-to-use-it-for-the-ftmo-challenge/) ·
[CNMV entidades no autorizadas](https://www.cnmv.es/portal/advertenciaslistado?tipoAdv=1&lang=en)

Vuelta 2 (oficiales): [Topstep retiros](https://help.topstep.com/en/articles/8284233-topstep-payout-policy) ·
[Topstep precios](https://help.topstep.com/en/articles/14289835-topstep-pricing-and-payment-questions) ·
[LucidFlex evaluación](https://support.lucidtrading.com/en/articles/12945790-lucidflex-evaluation-account) ·
[Tradeify Select Flex retiros](https://help.tradeify.co/en/articles/12853966-select-flex-and-select-daily-payout-policies) ·
[MFFU Rapid EOD 50K](https://help.myfundedfutures.com/en/articles/16158363-rapid-eod-50k-a-comprehensive-look)

Vuelta 2 (terceros): [MFFU Rapid EOD precio](https://www.eltraderfinanciado.com/en/news/myfundedfutures/my-funded-futures-launches-rapid-eod-50k-august-2026) ·
[Tradeify precios](https://blog.traderspost.io/article/tradeify-pricing-evaluation-guide) ·
[TradeDay Quick Pay](https://damnpropfirms.com/futures-prop-firms/tradeday/) ·
[TradeDay retiros](https://www.quantvps.com/blog/tradeday-payout-rules)

Terceros: [PropScope](https://propscope.net/en/) ·
[Topstep vs MFFU](https://traderssecondbrain.com/guides/topstep-vs-myfundedfutures) ·
[Lucid vs Apex vs Topstep](https://proptradingvibes.com/blog/lucid-trading-vs-apex-vs-topstep) ·
[Firmas cerradas 2026](https://edge-ledger.io/prop-firm-payout-tracker) ·
[Historial de cierres](https://propnavi.io/en/blog/prop-firm-shutdowns-history/) ·
[Algo trading en firmas de futuros](https://propfirmplus.com/algo-trading-on-futures-prop-firms-whats-actually-allowed-in-2026/)
