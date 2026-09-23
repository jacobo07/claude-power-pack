---
title: UCR-CIF — P3: el primer candidato a señal de familia NO sirve, y mi propio script dijo que sí
date: 2026-09-23
status: MEASURED — resultado NEGATIVO, y el negativo es el entregable
instrument: scratchpad/family_signal.py sobre 215 depósitos FD-07 / 11 repos, con suelo de población 100
decides: P3 del spec §11.a — de qué señal estructural se descubre el catálogo de familias
---

# P3 — `task_class` no lleva el eje de familia

## 1. Por qué se probó esto primero

El veredicto de `12_HR_NOVELTY_13Q` clasifica el clasificador de familia como
`NEW_SCANNER_OR_GATE`, y P3 del spec exige que el catálogo se **descubra de una señal
estructural del estate**, nunca se cure a mano — *«curarlo a mano mide memoria, no realidad»*.

El candidato obvio: los depósitos FD-07 llevan `task_class`, y hay **215 filas reales en 11
repos**. Población de verdad, con suelo.

## 2. Lo medido

| | |
|---|---|
| filas | 215 |
| `task_class` distintos | **162** |
| **singletons** | **128 de 162 — 79 %** |
| clases en ≥2 repos | 27 |

## 3. El resultado, y por qué mi propio instrumento lo leyó mal

El script terminó con:

> `VERDICT: 27 classes recur across repos -- a usable discovery seed.`

**Ese veredicto es falso, y la forma en que es falso es la lección.** Las 27 clases que recurren
entre repos son:

`absence-does-not-describe-itself` · `one-instrument-per-property` · `measured-not-tolerated` ·
`silence-cost` · `substitution-audibility` · `async-stop-is-not-stopped` ·
`capability-must-be-exercisable` · `syscall-order-durability-proof` · `measurement-regime` …

Eso **no son familias de sistema**. Son **nombres de lección epistémica**. De las 27, sólo
`persistence` se parece remotamente a una familia.

El script preguntó *«¿recurre esta clase entre repos?»* cuando la pregunta era *«¿lleva esta
clase el eje FAMILIA?»*. **La recurrencia no es familiaridad**, y un predicado mecánicamente
correcto sobre la pregunta equivocada devuelve un verde que nadie debería cobrar.

> **VEREDICTO REAL: `task_class` NO lleva el eje de familia. Lleva el eje de *tema de lección*.
> El catálogo de familias NO puede descubrirse de los depósitos FD-07.**

Sexta instancia propia del día de la misma familia de defecto — y la primera en la que el
instrumento **emitió un veredicto afirmativo explícito** que hubo que rechazar leyendo sus
propios datos. Un cero mal leído es peligroso; **un «sí» mal leído lo es más, porque autoriza a
construir.**

## 4. El hallazgo colateral, que sí vale

Esos 27 temas recurrentes entre repos **son evidencia de que la Torre ya funciona en otro eje**:
el estate acumula lecciones de ingeniería transferibles, y las mismas reaparecen en repos que no
comparten dominio — Orca X, TUA-X, Jacobo, KobiiSports Resort.

No es el eje que P3 necesita. Es, literalmente, **Marginal Institutional Lift observado**: deltas
que dejaron de ser de un proyecto. Se registra aquí porque la siguiente onda no debería
redescubrirlo.

## 5. Señales candidatas que quedan, sin probar

Nombradas para que la siguiente pasada no vuelva a empezar por la lista vacía:

| señal | por qué podría llevar el eje familia | coste de probarla |
|---|---|---|
| **composición de ficheros del repo** | migraciones/`*.sql`/Prisma ⇒ familia *migración de esquema*; rutas HTTP ⇒ *superficie web con efectos*; clientes de API externa ⇒ *integración externa*; ledgers `.jsonl`/sqlite ⇒ `PERSISTENT_STATE` | bajo — barrido de ficheros con suelo |
| contratos de `capability_runtime` | llevan `scope` y `triggers`; el scope podría proyectar a familia | medio — hay que leer los contratos |
| `repo_identity` + manifiesto de toolchain | tecnología ≠ familia, pero acota | bajo |

**La primera es la más prometedora y la más barata**, y es estructural por construcción: no
depende de que nadie haya etiquetado nada.

## 6. Estado de P2 — predeclaración NO hecha, a propósito

P2 exige nombrar **por escrito y antes de implementar** una misión que debe clasificar dentro y
otra que debe quedar fuera. **No se predeclara aquí**, porque predeclarar sujetos contra una
señal que todavía no está elegida sería elegir los sujetos que la señal futura sepa clasificar —
que es exactamente cómo un clasificador aprueba su propio examen.

Orden correcto para la siguiente pasada: **elegir la señal (§5) → predeclarar los dos sujetos →
implementar → conducir ambas ramas.** En ese orden.

## 7. Lo que este fichero NO afirma

- **No** afirma que no exista señal de familia en el estate. Afirma que **la primera candidata,
  la que tenía más población y mejor pinta, no lo es** — y nombra tres que quedan.
- **No** invalida los 215 depósitos ni FD-07. `task_class` hace bien su trabajo; simplemente no
  es el trabajo que P3 necesita.
- **No** se probó la composición de ficheros. Es una hipótesis con coste estimado, no un
  resultado.
