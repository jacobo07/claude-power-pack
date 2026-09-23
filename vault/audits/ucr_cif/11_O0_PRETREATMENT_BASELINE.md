---
title: UCR-CIF — O0: el suelo previo al tratamiento, congelado antes de que exista cápsula
date: 2026-09-23
status: MEASURED — captura de SÓLO LECTURA; no altera el tratamiento (done-gate 70)
instrument: scratchpad/o0_capture.py (P1+P2) · scratchpad/o0_telemetry.py (P3)
captured_at_utc: 2026-09-23T15:06:47Z
subject_head: 9d6e6b9 (rama feature/knowledge-acquisition)
closes: G-7 / P6 · done-gate 61–71 de la fase E
---

# O0 — el suelo, congelado

## 0. Por qué O0 podía capturarse hoy

**Porque el tratamiento no existe todavía.** No se ha creado ningún artefacto de runtime de la
Torre (gate 21 de la fase A). El suelo «sin cápsula persistida» sigue intacto, y **caduca en
cuanto el conector FD-07 → `applicability.py` se construya**. Capturarlo ahora era la única
ventana.

## 1. Definiciones canónicas — recuperadas exactas (done-gate 61)

Estaban en **B 27.573–27.611**, es decir **dentro del 46,4 % que la Fase 1 ya había
inventariado**. No hacía falta leer el sufijo: hacía falta mirar.

| métrica | definición literal del corpus | objetivo |
|---|---|---|
| **BIR** — Baseline Inheritance Rate (B 27.573) | *«Cuando construimos una instancia nueva de una familia conocida: ¿qué porcentaje de su constitutive baseline se heredó automáticamente?»* | *«cerca del 100 % de lo aplicable»* |
| **RFR** — Rediscovered Feature Rate (B 27.590) | *«Cuántas veces el usuario tuvo que volver a pedir una capability que ya había sido constitutiva en un sistema equivalente.»* | → 0 |
| **CRR** — Completeness Regression Rate (B 27.603) | *«Cuántas nuevas construcciones empiezan por debajo de la mejor completitud ya demostrada de su clase.»* | → 0 |

**BIR no aparecía en ningún documento de esta misión.** Es la tercera métrica, es un porcentaje
con denominador claro, y es la que más directamente mide lo que el Owner pidió.

Y la ley que las tres sirven (B 27.618):

> **THE BEST VERIFIED COMPLETE IMPLEMENTATION OF A SYSTEM FAMILY DEFINES THE MINIMUM STARTING
> MATURITY FOR FUTURE APPLICABLE IMPLEMENTATIONS OF THAT FAMILY.**

## 2. Lo que O0 NO puede capturar, y por qué no es un fallo del instrumento

**CRR, RFR y BIR son métricas de POBLACIÓN DE FAMILIA** — cuentan *construcciones nuevas de una
familia de sistema*, no prompts ni sesiones. Esa población es escasa (QuickLease, InfinityOps,
Orca X, KobiiCraft…), y sobre todo:

> **No existe clasificador de familia.** Sonda por nombre sobre `modules/` + `tools/`:
> `system_family`, `family_catalog`, `classify_family` → **0 ficheros**. Los triggers de
> `applicability.py` clasifican por **capacidad**, no por **familia**, que es un eje distinto.

Eso confirma que **P2 y P3 del spec §11.a siguen sin construir**, y convierte a CRR/RFR/BIR en
**no capturables hoy**. Reportar un número sería exactamente la trampa que el propio encargo
prohíbe: *una tasa sin denominador*. **No se reporta ninguno.**

*(Aviso de apertura: la sonda de clasificador fue **por nombre**. El candidato por mecanismo
—triggers de aplicabilidad— se inspeccionó y clasifica otro eje. Aun así, la afirmación
defendible es «no hay dueño del eje familia», no un cero absoluto.)*

## 3. Lo que SÍ se capturó — tres planos con población real

### P1 · plano de prompt — aplicabilidad ambiente (`gsd-x-heartbeat.json`, sha `80246d76e67ad1c1`)

| | |
|---|---|
| juicios | **927** |
| ventana | 2026-09-19T10:37:52Z → 2026-09-23T15:03:42Z (**4,18 días**) |
| por tier | FORENSIC 299 · DEEP 136 · LIGHT 450 · STANDARD 37 · ABSTAIN 5 |
| **suelo (polo negativo)** | **450** — toda capacidad resolvió `NOT_APPLICABLE` |
| **informativo (polo positivo)** | **472** — al menos una capacidad en `MANDATORY` |
| abstenciones | 5 |
| fallos del productor | `child_timeouts: 6` |
| **cuota informativa** | **50,9 %** |
| **ambos polos presentes** | **SÍ** ✅ |

### P2 · ledger de depósitos FD-07 — 11 repos, 215 filas, 2026-07-09 → 2026-09-20

`NEW: 215`. **Cero `DUP`, cero `STRONGER`, cero `DISCARD`.** Ese 100 % encendió la alarma del
propio script (*«one pole is empty … treat this floor as UNVALIDATED»*) y resultó ser un
artefacto del instrumento, no un defecto del sistema — ver §4.

Reparto: `hard_rule` 87 · `dataset_part` 86 · `benchmark` 38 · `asset` 3 · `prompt_fragment` 1.
`portability_proven=True`: **0 de 215**, que es el valor **esperado y honesto** — FD-07 lo
escribe `False` por contrato al depositar.

### P3 · censo de JUICIOS — `co12_readiness/signals.jsonl` (11.366 líneas, 9 tipos)

Aquí está el número que el ledger no puede enseñar:

| | |
|---|---|
| turnos de flywheel | **5.074** |
| **hallazgos procesados** | **26.183** |
| depositados | **221** — tasa de depósito **0,8 %** |
| **deduplicados (`DUP`)** | **25.962** — **tasa de dedup 99,2 %** |
| descartados | **0** |
| turnos truncados | 91 |
| **ambos polos presentes** | **SÍ** ✅ |

## 4. El hallazgo que corrige mi propio E1

El ledger dice `NEW: 215/215`. Leído solo, eso dice que **la cláusula más dura de la definición
canónica de la Torre —`deduplicated against existing capability state`— no tiene ninguna
evidencia de haber disparado jamás**. Así lo reporté en la primera pasada de este fichero.

Es falso, y la causa está en `fd_07_flywheel.py:336-344`:

```
if cls == "DISCARD":            res.discarded += 1;  continue
if fp in seen_fps or cls == "DUP": res.dup += 1;     continue
```

**`DUP` y `DISCARD` se cuentan en memoria y nunca llegan a `_writeback`.** El ledger es un
registro de **supervivientes**, no de **juicios**. Su denominador son depósitos, no hallazgos.

Los juicios sí sobreviven, en `_record_turn_signal` → `record_signal('fd_flywheel_turn')`. Y ahí
la cláusula no es que haya disparado: **es el camino más ejercitado de la estancia, 25.962 veces,
el 99,2 %.**

> **Mismo defecto que el ledger de auto-compact, con el signo invertido.** Aquél registraba sólo
> los FALLOS y por eso sólo podía responder «nunca entregó». Éste registra sólo los ÉXITOS y por
> eso sólo podía responder «nunca dedujo». **La asimetría de observabilidad miente en las dos
> direcciones**, y sólo se detecta leyendo el segundo instrumento.

Lo que lo salvó no fue perspicacia: fue que el script **se niega a imprimir un cero** y avisa
cuando un polo está vacío. Un barrido que hubiera impreso `DUP: 0` sin más habría producido un
hallazgo falso y grave contra un sistema sano.

### 4.b Las tres cláusulas, con evidencia de producción

| cláusula de B 102.293 | evidencia |
|---|---|
| `capability delta` | 26.183 procesados · 221 depositados |
| `deduplicated against existing capability state` | **25.962 (99,2 %)** |
| `verified` | señales `fd_portability_proven`: **19** · `fd_portability_recheck`: 7 · `fd_portability_residue`: 1 |

**Construction Return no sólo tiene dueño: está intensamente ejercitado**, y las tres cláusulas
de la definición canónica de la Torre tienen evidencia de producción.

## 5. Contaminación — ya presente, declarada (done-gate 65)

**El suelo NO es «sin tratamiento».** Dos tratamientos parciales ya corren:

1. **Aplicabilidad ambiente**: 472 juicios informativos en 4,18 días ya cambian la postura de
   arranque.
2. **El flywheel FD-07**: 5.074 turnos ya capturan deltas de construcción.

Por tanto O0 se define honestamente como **«sin cápsula PERSISTIDA, con aplicabilidad ambiente
por prompt y con captura FD-07 activa»**. Cualquier lectura futura que compare contra cero estará
comparando contra un mundo que no existía ya en 2026-09-23.

**Apertura adicional que acota P2/P3:** `_is_frontier_session()` — el flywheel **sólo corre con
`PP_FRONTIER_SESSION=1`** (lanzamiento Opus). Los 26.183 hallazgos son de sesiones frontier, no
de todas. El denominador está acotado por el sustrato, no por el repo.

## 6. Discrepancias que no se esconden (done-gate 66)

- **221 señales `fd_delta_deposited` frente a 215 filas de ledger.** Seis depósitos señalizados
  que no están en el ledger. No se explica aquí; se deja medido. Podría ser rotación, un repo
  cuyo ledger se borró, o una escritura perdida. **No se promedia ni se redondea.**
- **`discarded: 0` sobre 26.183.** La rama `DISCARD` (`< _MIN_DELTA_TOKENS`) **nunca ha
  disparado**. Es la única de las cuatro sin evidencia de producción.
- El heartbeat **no puede ver su propio abandono**: los 215–408 casos en que el dispatcher
  abandonó `gsd_x_tier` (ver `09_G3_DECISION.md`) no aparecen entre los 927 juicios. **La
  población real de prompts es mayor que 927**, y sólo el log del dispatcher la ve. Dos
  instrumentos, dos aperturas; ninguno solo es el denominador.

## 7. Estado del done-gate de la fase E

| # | ítem | estado |
|---|---|---|
| 61 | CRR/RFR canónicos recuperados | **SÍ** — y BIR además |
| 62 | población / denominador definidos | **SÍ para P1/P3** · **NO para CRR/RFR/BIR** (falta el eje familia) |
| 63 | mecanismo de observación validado | **SÍ** — ambos polos en los dos planos |
| 64 | huella de tiempo / revisión | **SÍ** — hashes, ventanas, HEAD `9d6e6b9` |
| 65 | contaminación evaluada | **SÍ** — dos tratamientos parciales, declarados |
| 66 | datos históricos sólo si fiables | **SÍ** — discrepancias publicadas, no promediadas |
| 67 | una misión no es una tasa | **SÍ** — no se reporta ningún CRR/RFR |
| 68 | suelo «sin cápsula» capturado antes del tratamiento | **SÍ** |
| 69 | persistido en el dueño de evidencia | **SÍ** — este fichero, commitado |
| 70 | O0 no altera el tratamiento | **SÍ** — sólo lectura |
| 71 | el instrumento ve los dos mundos | **SÍ** — probado en P1 y P3 |

**O0 SELLADA para los planos con población. CRR/RFR/BIR quedan BLOQUEADAS por la ausencia del
eje de familia — que es P2/P3 del spec §11.a, y ahora tiene una razón medida, no una casilla.**

## 8. Lo que esto cambia para la siguiente onda

El conector FD-07 → `applicability.py` (acción 2 del handoff) tiene ahora su suelo:
**0,8 % de tasa de depósito, 99,2 % de dedup, 927 juicios de aplicabilidad al 50,9 % informativo.**
Si la Torre funciona, esos números se mueven en una dirección declarable **antes** de tocarlos.

Y el clasificador de familia deja de ser una casilla del spec: es el **bloqueante único** de las
tres métricas que el Owner pidió.
