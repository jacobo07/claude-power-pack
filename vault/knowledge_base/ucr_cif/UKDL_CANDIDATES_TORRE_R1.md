---
title: UCR-CIF — candidatos UKDL de la pasada R1, con el barrido de propiedad que los precede
date: 2026-09-23
status: CANDIDATOS — redactados para fusión, NO fusionados (razón en §0)
merge_target: vault/knowledge_base/ukdl-universal.md (familia CONT y familia de instrumentos)
---

# Candidatos UKDL — R1

## 0. Por qué esto no está ya dentro del UKDL

`vault/knowledge_base/ukdl-universal.md` estaba **sucio** en el momento de escribir esto: otro
escritor (las entradas automáticas de CEPS al final del fichero) tiene hunks sin commitear.

**El pathspec de git es granular a FICHERO, no a hunk.** Commitear el UKDL habría arrastrado las
líneas de CEPS dentro de mi commit y bajo mi mensaje — el daño exacto que
`rules/concurrent-writers-shared-tree.md` §1 describe. Y mi punto de inserción natural (la familia
`CONT`) está a mitad de fichero, así que ni siquiera separar por posición ayuda.

Por tanto: redactados aquí, **fusión debida** cuando el fichero esté quieto. Esto es deuda
declarada, no una segunda autoridad de reglas.

## 1. Barrido de propiedad PRIMERO — tres candidatos RECHAZADOS por ser sinónimos

`EXTEND > NEW. No rule inflation.` El UKDL tiene **106 HR · 185 PR · 360 T** y 648 apariciones de
«absence». Barrido antes de redactar:

| candidato del encargo | veredicto | dueño existente |
|---|---|---|
| `NAME-SCOPED-SEARCH-PRODUCES-FALSE-ABSENCE` | **RECHAZADO — ya es suyo** | `T-SQI-NARROW-VOCABULARY-BLINDS-THE-GATE-001` («zero cannot fall», línea 4738): *«Give it a narrow vocabulary and it reports zero for every file written in an idiom it does not recognize»*, con `UNKNOWN, never zero` |
| `RATE-WITHOUT-A-POPULATION` | **RECHAZADO — ya es suyo** | `NEVER-GATE-ON-A-RATIO` + `T-REFERENCE-SHRINK-001` (denominador que encoge) + *«a count over the wrong population is wrong»* |
| «ambos polos obligatorios en un gate» | **RECHAZADO — ya es suyo** | línea 5685: *«a gate that always fires and a gate that never fires are the same defect wearing different signs»* |

**Tres de los ocho candidatos del encargo ya estaban escritos.** Añadirlos habría sido inflación.

## 2. `HR-CONT-05` — una premisa no puede viajar por un carril advisory cuyo fallo es indistinguible del silencio legítimo

**Hermano de `HR-CONT-04`, no sinónimo.** HR-CONT-04 cubre un advisory que **desplaza** un camino
load-bearing (un `return` temprano por encima del mecanismo). Éste cubre lo contrario: **nada se
desplaza**; la premisa simplemente no llega, y **no se puede distinguir de que no tuviera nada que
decir**.

**TRIGGER.** Colocar en un carril advisory cualquier estado del que dependa una afirmación de
producto («la misión arrancó con madurez heredada», «la postura se aplicó»).

**ACCIÓN.** STOP. Medir la tasa real de abandono de ese carril, y exigir que el consumidor pueda
distinguir *abandonado* de *vacío por evidencia*. Si no puede, la afirmación no es falsable y no
se hace.

**ORIGEN, medido.** `UserPromptSubmit-chain`, deadline viva 3.000 ms, `gsd_x_tier` advisory por
diseño. Log de producción 2026-09-15→09-23: **815 abandonos de cadena**, 639 en esa cadena, y
`gsd_x_tier` **nombrado en 215 (33,6 %)** — suelo, porque la rama `before pool` abandonó 965 slots
más sin nombrar ninguno. RAM libre al abandonar: mediana 8,2 %, **máximo 28,2 %** — no es sólo
inanición.

**COROLARIO que no es obvio.** El dispatcher **sí** distingue el abandono con clase propia
(`CHAIN-DEADLINE-ABANDONED`, greppable, con presión de host y reaping). Lo escribe a **su** log.
El consumidor sólo ve el merge de stdout. **En la capa del productor abandonado ≠ silencioso; en
la capa del consumidor son el mismo observable.** Un diagnóstico perfecto en el sitio equivocado
no es observabilidad.

**EXCEPCIÓN.** Ninguna. Subir la deadline no vale: *«a budget is a constant and a spawn's cost is
a function of host load, so raising it only moves the cliff»* — `hook-dispatcher.js:979`.

**Cross-ref:** `HR-CONT-04` · `PR-CONT-06` (delivery is not submission) · `T-CONT-12`.

## 3. `T-TELEMETRY-ASYMMETRY-LIES-BOTH-WAYS` — un ledger parcial miente en la dirección de lo que omite

**Trampa.** Un mecanismo que registra **sólo un lado** de su máquina de estados sólo puede
responder una cosa, y esa respuesta parece un hallazgo.

**Medido DOS VECES en un día, con el signo invertido — que es lo que lo hace regla:**

| instrumento | qué registra | única respuesta posible | veredicto falso producido |
|---|---|---|---|
| ledger de auto-compact | los 3 caminos de **fallo**, ninguno de éxito | «nunca entregó» | «26 peticiones, 0 entregas jamás» |
| ledger de depósitos FD-07 | sólo los **éxitos** (`continue` en `DUP` y `DISCARD`, `fd_07_flywheel.py:336-344`) | «nunca dedujo» | `NEW 215/215` ⇒ *«la cláusula `deduplicated` no ha disparado nunca»* |

La segunda era **catastróficamente falsa**: el censo real de juicios
(`record_signal('fd_flywheel_turn')`) da **26.183 hallazgos procesados y 25.962 deduplicados —
99,2 %**. La cláusula más dura de la definición canónica de la Torre no es que haya disparado: es
**el camino más ejercitado de la estancia**.

**Regla.** Un ledger es **un registro de supervivientes hasta que se demuestre lo contrario**.
Antes de leer una distribución como propiedad del sistema, preguntar **qué rama hace `continue`
antes de escribir**. Y enumerar los estados con significado distinto: ejecutó · tuvo éxito ·
falló · vacío a propósito · saltado · abandonado.

**Detector barato, y es el que salvó esta medición:** un barrido que **se niega a imprimir un
cero** y avisa cuando un polo está vacío. El script escribió *«one pole is empty … treat this
floor as UNVALIDATED»* y eso obligó a buscar el segundo instrumento.

**Extiende** a `T-SQI-NARROW-VOCABULARY-BLINDS-THE-GATE-001`: aquél es ceguera en el
**vocabulario**, éste en la **grabación**. Mismo cero falso, capa distinta.

## 4. `T-AFFIRMATIVE-VERDICT-ON-THE-WRONG-QUESTION` — un «sí» mal leído es peor que un cero mal leído

**Trampa.** «Zero cannot fall» protege contra un cero que no puede bajar. No protege contra un
**veredicto afirmativo** emitido sobre una pregunta que no era la del encargo. Un cero falso
**bloquea**; un sí falso **autoriza a construir**.

**Origen, medido 2026-09-23.** Para descubrir un catálogo de familias de sistema se sondeó el campo
`task_class` de 215 depósitos FD-07 en 11 repos. El script terminó con:

> `VERDICT: 27 classes recur across repos -- a usable discovery seed.`

Mecánicamente correcto y **sustancialmente falso**. Las 27 clases que recurren son
`absence-does-not-describe-itself`, `measured-not-tolerated`, `one-instrument-per-property`… —
**nombres de lección epistémica, no familias de sistema**. El script preguntó *«¿recurre?»* cuando
la pregunta era *«¿es familia?»*. **La recurrencia no es familiaridad.**

**Regla.** Todo veredicto afirmativo de un instrumento propio se lee **contra sus propios datos
crudos** antes de cobrarse, y la pregunta que el predicado responde se escribe al lado de la
pregunta del encargo. Si no son la misma frase, el verde no cuenta.

**Cross-ref:** `FOUNDING-FINDING-IS-A-HYPOTHESIS` · `zero cannot fall` (el hermano de signo
contrario).

## 5. `PR-BASELINE-BEFORE-TREATMENT` — el suelo se captura antes de encender lo que lo mueve

**Cobertura previa: CERO.** `baseline before`, `pre-treatment`, `antes del tratamiento` → 0
apariciones en el UKDL.

**Regla.** Cuando una capacidad va a mover una métrica de población, el suelo previo se captura
**antes de activarla**, porque **caduca**: en cuanto el trinquete corre, ya no hay forma de saber
cómo era antes. Y se captura con la contaminación **declarada**, no con un cero inventado.

**Origen.** O0 de la Torre, capturable el 2026-09-23 **sólo porque no existía todavía ninguna
cápsula**. Se congelaron 927 juicios de aplicabilidad (50,9 % informativo) y 26.183 hallazgos
procesados (0,8 % de depósito, 99,2 % de dedup), con dos tratamientos parciales **ya corriendo** y
declarados como tales. Comparar contra cero habría comparado contra un mundo que ya no existía.

**Corolario.** Si la métrica cuenta una población que no se puede enumerar —CRR/RFR/BIR cuentan
*construcciones de una familia*, y no existe clasificador de familia— **no se reporta ningún
número**. Una tasa sin denominador no es una medida. *(Esa mitad ya la posee
`NEVER-GATE-ON-A-RATIO`; aquí sólo se cruza.)*

## 6. Candidato NO promovido, a propósito

El encargo (§17) proponía **derivar las constantes documentadas de la autoridad viva** a raíz del
comentario rancio de `hook-dispatcher.js:525` (*«this chain's 11500 ms deadline»* frente a los
**3.000 ms** vivos de `:758` — rancio por un factor de 3,8, justo al lado del registro donde
alguien iría a comprobarlo).

**El incidente está probado; la reparación no se hizo.** Se corrigió otra asimetría del mismo
fichero (nombrar los miembros abandonados), no ésta. Promover una regla de proceso que exige
derivación sin haberla implementado sería exactamente lo que
`documented-capability-must-be-executable` llama forma 3: **un documento que afirma una
observancia que no existe**.

Queda como **incidente registrado y reparación debida**, no como regla.

## 7. Estado de fusión

| regla | acción |
|---|---|
| `HR-CONT-05` | insertar en la familia `CONT`, junto a `HR-CONT-04` |
| `T-TELEMETRY-ASYMMETRY-LIES-BOTH-WAYS` | insertar junto a `T-SQI-NARROW-VOCABULARY-BLINDS-THE-GATE-001`, como extensión declarada |
| `T-AFFIRMATIVE-VERDICT-ON-THE-WRONG-QUESTION` | misma vecindad; es el hermano de signo contrario |
| `PR-BASELINE-BEFORE-TREATMENT` | familia de proceso; cruzar con `NEVER-GATE-ON-A-RATIO` |
| los 3 del §1 | **no fusionar** — ya son suyos |

**Precondición de la fusión:** `git status --porcelain -- vault/knowledge_base/ukdl-universal.md`
debe salir vacío. Si no, esperar; nunca commitear el fichero con hunks ajenos dentro.
