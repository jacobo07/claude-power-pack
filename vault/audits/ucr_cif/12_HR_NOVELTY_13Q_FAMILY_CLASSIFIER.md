---
title: UCR-CIF — HR-NOVELTY-001 corrido entero contra el sujeto real: el clasificador de familia
date: 2026-09-23
status: MEASURED — 13/13 respondidas contra barrido descubierto, no contra lista curada
subject: clasificador de familia de sistema + catálogo de familias (bloqueante único de CRR/RFR/BIR)
verdict: NEW_SCANNER_OR_GATE + EXTEND_EXISTING_OWNER — NO es un sistema institucional nuevo
closes: E3 del spec R1 §13 · fase C del encargo
---

# HR-NOVELTY-001 — 13/13, contra un sujeto concreto

## 0. Por qué contra ESTE sujeto y no en abstracto

El encargo pedía cerrar «las 12 preguntas restantes». Correrlas en abstracto no decide nada: la
regla existe para juzgar **una propuesta**. O0 produjo la propuesta real — **el clasificador de
familia es el bloqueante único de CRR, RFR y BIR** — así que las trece se corren contra él.

## 1. Primero, una corrección al audit 06

`06_NOVELTY_GATE_TRIGGER.md` concluye que el trigger *«está acotado por el NOMBRE, no por el
mecanismo»*. Leído el código, **eso es medio cierto y la otra mitad importa**.

`modules/spec_gate/gate.py:272` ya lleva un **segundo instrumento, independiente del
vocabulario**:

```
_NOVELTY_SHAPE = r"\b\d{1,3}\s+(?:new\s+|proposed\s+)?(?:datasets?|dataset\s+famil(y|ies)|corpora|meta-systems?)\b"
```

Y su comentario documenta exactamente el defecto que el audit 06 «descubre», medido **el
2026-08-04**, un mes y medio antes:

> *«A keyword list is bounded by its own vocabulary: an idiom nobody thought to add reads as zero,
> and zero never trips a gate … it fired on the IIG compendium and stayed silent on UCEIMR …
> purely because that title splits the two words of "universal runtime". The shape, not the noun,
> is what all seven incidents shared: an enumerated catalog of datasets. Counting them is
> vocabulary-independent.»*

**Por tanto el gate tiene DOS triggers, no uno**, y ya aprendió esta lección por su cuenta. Lo que
sigue siendo cierto del audit 06: el Constitutive Baseline Ratchet **no dispara ninguno de los
dos**, y su `applies=False` sigue siendo **UNKNOWN**. Lo que deja de ser cierto es la implicación
de que nadie había pensado en el problema.

## 2. Las trece, contra el clasificador de familia

Cada respuesta cita medición de esta sesión o `file:line`. Q4 no se rehace.

| # | pregunta | respuesta medida |
|---|---|---|
| **1** | ¿Qué problema concreto no tiene dueño hoy? | Clasificar un repo/misión en una **familia de sistema**. Sonda por nombre sobre `modules/`+`tools/`: `system_family`·`family_catalog`·`classify_family` → **0 ficheros**. El candidato por mecanismo, los triggers de `applicability.py`, clasifica por **capacidad** — otro eje. **Sin dueño.** |
| **2** | ¿Qué resultado nuevo produciría? | Hace **computables CRR, RFR y BIR**, hoy imposibles por falta de denominador (`11_O0`). Y da al Ratchet su granularidad, que el spec §0 define como *familia*, no proyecto. |
| **3** | ¿Qué consumidor real lo necesita? | Tres, existentes y nombrados: `MissionContext`/`applicability.py` (selección de baseline), el plano de evaluación (las tres métricas), y el conector FD-07→baseline. |
| **4** | ¿Por qué no basta extender un dueño? | **YA RESPONDIDA** → `EXTEND_EXISTING_OWNER` + estado persistido. `07_Q4_EXISTING_OWNER.md`. No se rehace. |
| **5** | ¿Qué primitiva nueva exige? | Un **eje taxonómico** que no existe. Pero es una **etiqueta**, no un sustrato: cabe como campo de `MissionContext`, no como almacén propio. |
| **6** | ¿Qué decisiones tomaría que hoy nadie toma? | *«¿Qué generación de baseline hereda esta misión?»* Hoy no lo decide nada: `tier.py:251-253` deja `owners`/`prerequisites`/`held_scopes` vacíos **a propósito**. |
| **7** | ¿Qué evidencia produciría? | Etiqueta de familia + confianza + **la señal estructural de la que salió**, por `repo_key`. Falsable: dos ramas alcanzables sobre entradas reales (P2 del spec). |
| **8** | ¿Qué clase de fallo previene? | **Regresión de completitud** — una instancia nueva de familia conocida arrancando por debajo de la mejor completitud demostrada. Es literalmente CRR (B 27.603). |
| **9** | ¿Qué interfaces con dueños existentes? | Lee `repo_identity.repo_key` (`:92`); escribe un campo en `MissionContext`; consume depósitos FD-07. **Tres dueños existentes, ninguno nuevo.** |
| **10** | ¿Cómo se mediría su valor? | **BIR** — % del baseline constitutivo aplicable heredado automáticamente (B 27.573, objetivo ~100 % de lo aplicable). Más el control de dos ramas. |
| **11** | ¿Qué complejidad introduce? | La real: **un catálogo curado mide memoria, no realidad**. Exige descubrimiento estructural con **suelo de población** — un barrido que deja de encontrar nada **falla**, no reporta limpio. Y G-4: si la etiqueta alimenta `held_scopes`/`resolved_owners`, un valor parcial **invierte** la aplicabilidad. |
| **12** | ¿Qué condición justificaría retirarlo? | Que los triggers de aplicabilidad absorban el eje familia, **o** que BIR se estabilice cerca del 100 % y la etiqueta deje de cambiar ninguna decisión — medible con la propia telemetría de consumo del §8 del spec. |
| **13** | ¿Por qué no es una capa retórica? | Porque es el **bloqueante medido** de tres métricas, no una capa sobre ellas. Falsable en una frase: constrúyase, y si CRR/RFR/BIR siguen sin poder computarse, era retórica. |

## 3. Veredicto

> **`NEW_SCANNER_OR_GATE` + `EXTEND_EXISTING_OWNER`. NO es un sistema institucional nuevo.**

Un barrido descubierto que emite una etiqueta con suelo de población (el *scanner*), y esa
etiqueta entrando como **campo** de un `MissionContext` que ya existe (el *extend*). Sin grafo
propio, sin registro propio, sin base de datos propia — los tres olores que el §3 del spec
declara señal de fallo estructural.

**Lo que el veredicto prohíbe explícitamente:** un «Family Intelligence Fabric», un catálogo
curado a mano, y cualquier almacén nuevo. La tentación es real porque el eje no existe; la
respuesta a Q5 es que lo que falta es una *etiqueta*, no un *sustrato*.

## 4. El trigger — decisión: NO TOCAR

El encargo (§14) pedía decidir si el trigger se generaliza, consume señal de aguas arriba, o se
deja. Decidido con evidencia:

**No se toca**, por tres razones medidas:

1. **Ya tiene dos instrumentos** (`_NOVELTY_TRIGGER` por vocabulario, `_NOVELTY_SHAPE` por forma),
   y el segundo nació exactamente de esta crítica. Un tercer patrón sería la tercera capa sobre
   un problema que el dueño ya trata.
2. **El gate es advisory por contrato** (`:293`: *«Advisory: returns the questions … Does not
   itself decide the verdict»*). Ampliarlo no bloquea nada nuevo; sólo añade falsos positivos.
3. **El defecto real no está en el trigger, está en el sitio de la propuesta.** Este fichero lo
   demuestra: las trece se corrieron **sin que ningún trigger disparara**, porque la disciplina
   la puso el proponente. Un trigger que hay que ampliar cada vez que alguien escribe bien es un
   trigger que sustituye al juicio en vez de respaldarlo.

**Lo que sí cambia, y no es código:** `applies=False` **no puede reportarse como inocencia** —
regla ya sellada en el spec R1 §13 E3. El gate informa; no absuelve.

## 5. Lo que este fichero NO afirma

- **No** afirma que el clasificador deba construirse **ya**. Afirma que, si se construye, su
  clasificación correcta es la del §3 — y que no necesita pasar por HR-NOVELTY otra vez.
- **No** afirma que las trece respuestas sean completas para *otro* sujeto. Son de éste.
- La sonda de Q1 fue **por nombre**; el candidato por mecanismo se inspeccionó y clasifica otro
  eje. La afirmación defendible es **«no hay dueño del eje familia»**, no un cero absoluto.
- **No** se corrió el gate sobre el texto de esta propuesta. Habría devuelto `applies=False` —
  que es precisamente por lo que las trece se contestaron a mano.
