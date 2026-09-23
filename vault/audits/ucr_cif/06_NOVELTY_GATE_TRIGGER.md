---
title: UCR-CIF — O2, primer resultado: el trigger de HR-NOVELTY-001 no alcanza a su sujeto
date: 2026-09-23
status: MEASURED — gate ejercitado desde ambos polos
instrument: modules/spec_gate/gate.py::check_novelty_gate, conducido con sujeto + control negativo + control positivo
---

# O2 — el gate no dispara sobre el Constitutive Baseline Ratchet

## 1. Lo medido

`check_novelty_gate()` conducido con tres entradas:

| entrada | `applies` | `matched` |
|---|---|---|
| **SUJETO** — Constitutive Baseline Ratchet, descrito en términos funcionales | **False** | None |
| control negativo — «Fix a typo in the README heading» | False | None |
| **control positivo** — «a new institutional intelligence **fabric** and governance **operating system** … **kernel** … **compendium**» | **True** | `'fabric'` |

La descripción del sujeto fue la que la misión enviaría de verdad: *baseline institucional por
familia de sistema, que promueve mejoras probadas a un conjunto constitutivo de capacidades,
emite una Mission Baseline Capsule al arrancar la misión y escribe los deltas de construcción
de vuelta al estado institucional.*

## 2. Por qué hizo falta el control positivo

La primera corrida llevaba sólo sujeto y control negativo. **Ambos volvieron `False`**, lo cual
es ininterpretable: un gate que no puede disparar y un gate que aprueba producen exactamente la
misma respuesta. Sin el polo positivo, `applies=False` sobre el sujeto se habría leído como
«no es un mega-sistema» cuando también podía significar «el trigger está roto».

El polo positivo dispara con `matched='fabric'`, así que **el trigger está vivo**. Eso convierte
el `False` del sujeto en un hallazgo sobre el trigger, no en un aprobado sobre el sujeto.

## 3. El hallazgo

**El trigger está acotado por el vocabulario de la propuesta.** Reconoce nombres —`fabric`,
`operating system`, `kernel`, `compendium`— no mecanismos. Una propuesta escrita en términos
funcionales, que es como la escribiría un autor cuidadoso y también como la escribiría alguien
que quiere esquivar el gate, lo atraviesa entera.

La ironía es exacta y está en el propio mensaje del gate:

> *"answer all 13 questions … with cited file:line evidence from a DISCOVERED sweep of this repo
> (**grep for the mechanism, not the name**)"*

Exige a la evidencia la disciplina que su propio trigger no aplica.

**Consecuencia operativa inmediata:** `applies=False` sobre el Constitutive Baseline Ratchet es
**UNKNOWN, no inocencia**. No puede reportarse como «el gate no aplicaba». La regla cubre este
sujeto por intención —la propia `UCR_CIF_RESUMPTION.md` dice que HR-NOVELTY-001 no se ha corrido
para los 6 candidatos CREATE, y el Ratchet es uno— y el trigger simplemente no lo ve.

## 4. Tercera instancia del mismo defecto en un día

| instrumento | cero producido | causa |
|---|---|---|
| ledger de auto-compact | «compact nunca entregado» (falso) | consultado con el vocabulario del camino *resume* |
| audit D2A, sondeo del UBC | «cero coincidencias en 84 módulos» (falso) | buscado con el vocabulario del corpus, no el del módulo |
| **trigger de HR-NOVELTY-001** | «no es un mega-sistema» | acotado por el nombre, no por el mecanismo |

`Zero cannot fall`: un cero acotado por el vocabulario del instrumento es UNKNOWN. El audit D2A
ya registró haber cometido este error dos veces, una de ellas propia. Esta es la tercera en la
misma jornada, en tres instrumentos que nadie relacionaba.

## 5. Lo que este fichero NO hace

- **No corre las 13 preguntas.** Ese es el trabajo real y sigue pendiente. Requiere un barrido
  descubierto del repo por mecanismo. La evidencia parcial ya existe:
  `02_D2A_OWNERSHIP_AUDIT.md` §5.2 mide el Ratchet en 4 hits / 4 ficheros, 1 hit por fichero,
  sin dueño — eso alimenta Q1 y Q4, no las trece.
- **No propone arreglar el trigger.** Ampliarlo a mecanismos es una decisión con coste de falsos
  positivos, y el gate es advisory por contrato. Se registra; no se toca.
- **No afirma que el Ratchet sea nuevo.** Afirma que el instrumento que debía decidirlo no lo vio.

## 6. Primer paso cuando se retome

Correr las 13 preguntas a mano contra un barrido descubierto, empezando por Q4 —*¿por qué no
basta extender un dueño existente?*— porque el audit de fase 4 sostiene que **O3 ya tiene dueño
vivo** (`modules/gsd_x/tier.py` + `hooks/gsd_x_tier.js`), y si eso se confirma, Q4 falla y la
clasificación correcta es `EXTEND_EXISTING_OWNER` antes de construir nada.
