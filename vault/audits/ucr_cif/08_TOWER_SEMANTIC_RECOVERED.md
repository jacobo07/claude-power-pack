---
title: UCR-CIF — O5: la semántica canónica de la Torre, recuperada del sufijo no inventariado
date: 2026-09-23
status: MEASURED — leído del corpus canónico, con número de línea por cada afirmación
instrument: scratchpad/enumerate_lifts.py (enumera la CLASE, no una muestra) + extract_range.py
corpus: "…Fabric 1 (1).txt" · 3.086.894 bytes · 167.842 líneas · sha256 a082a5714e616630a6eafa7d2d5e0ffecb152989b3e81e194d74ee165454195b
supersedes: la frase «los ocho Lifts de la Torre Universal» de TORRE_UNIVERSAL_HANDOFF.md §4.1
---

# O5 — la Torre tiene definición canónica, y no son «ocho Lifts»

## 1. Por qué este fichero existe

`TORRE_UNIVERSAL_HANDOFF.md` §4.1 y `04_SOURCE_RECONCILIATION.md` §4 sitúan **«los ocho
*Lifts* de la Torre Universal»** en B 89.813–90.636 y los tratan como el conjunto canónico que
la misión debe recuperar antes de definir la Torre. La región se leyó entera. **Los ocho
existen, están exactamente donde el audit dijo, y no son lo que el handoff creía que eran.**

## 2. Lo primero que hay que corregir: no hay UN conjunto de Lifts

El instrumento fue una **enumeración de la clase completa** — las 73 líneas del corpus que
contienen `lift` —, no una muestra alrededor del puntero citado. Esa elección es la que produjo
el hallazgo: la región 90.491 no es la más densa. Hay **al menos cuatro descomposiciones
distintas**, cada una para una absorción distinta:

| líneas | nº | descomposición | sujeto |
|---|---|---|---|
| **90.491–90.519** | **8** | Direct Capability · Code Review Baseline · Failure Immunity · Skill · Metrology · Security · Completion · Meta-Engineering | absorción de CodeRabbit |
| **92.130–92.275** | **6** | Direct Review Capability · Failure-Immunity · Software-Engineer Skill · Metrology · Meta-Engineering · Structural Prevention | *el mismo* sujeto, remodelado |
| **101.803–102.015** | **9** | Direct RE · Software Understanding · Debugging · Architecture · Code Review · Metrology · Tooling · Human-Intervention · Skill | absorción de Reverse Engineering |
| **76.192–76.219** | **—** | Gross Feature · Marginal Institutional · Direct Marginal · Transitive · Compositional · Meta | **no es una lista de dominio: es la aritmética** |

Dos de esas listas describen **el mismo sujeto** con distinto número (8 y 6, separadas por 1.639
líneas). Eso descarta por sí solo que exista un conjunto fijo: el corpus está **pensando en voz
alta**, no publicando una taxonomía.

**Consecuencia:** «recuperar los ocho Lifts canónicos» era una tarea mal planteada. Fijar el
diseño de la Torre sobre los ocho de la línea 90.491 habría convertido el ejemplo trabajado de
**una** absorción en la ontología de la institución entera.

Lo que sí se repite entre las tres listas de dominio —y por tanto es estructural, no de dominio—
es: **Direct Capability · Failure-Immunity · Skill · Metrology · Meta-Engineering**. Las demás
(Security, Completion, Structural Prevention, Debugging, Architecture, Tooling,
Human-Intervention) aparecen en una sola lista y son del dominio absorbido.

## 3. La definición canónica — existe, y es una sola línea

> **B 102.293:** `Baseline Tower Lift = verified capability delta, deduplicated against existing
> capability state.`

Tres cláusulas, las tres con carga:

- **`verified`** — un delta no verificado no es Lift. Alinea con la Liveness Standard y con
  `A LEARNING IS NOT INSTITUTIONALIZED WHEN IT IS STORED` del §8 del diseño aprobado.
- **`capability delta`** — la unidad es la capacidad, no el commit, la línea ni el sprint.
- **`deduplicated against existing capability state`** — el anti-doble-conteo está **dentro de
  la definición**, no es una política añadida después. Es el mecanismo que el prompt pedía en
  su §XXVII bajo «lifecycle/supersession prevents double counting», y el corpus lo pone en la
  definición misma.

Esto cierra la fila «semántica canónica de Torre → **NO EXISTE**» del §5 del handoff. Matiz que
importa: esa fila hablaba del **dueño en disco**, y sigue siendo cierta — no hay dueño en el
repo. Lo que no existía era el dueño, no la semántica.

## 4. Project Challenge vs Tower Lift — resuelto por la aritmética del corpus

El §XII del prompt pedía separar esfuerzo de ganancia institucional. El corpus ya lo hace, con
un ejemplo numérico trabajado (B 76.176–76.223), y su vocabulario es **más fuerte** que el que
el prompt proponía, así que se adopta el del corpus:

```
Gross Feature Lift                                  1.000   lo que la feature parece valer
  − ya cubierto por el estado institucional            400   ← HERENCIA, no logro
  − específico de producto                             200   ← delta de dominio
  − trade-offs no transferibles                        100
  ─────────────────────────────────────────────────────────
  = Marginal Institutional Lift                        300   ← lo único que sube la Torre
```

> **B 76.198:** «Eso evita inflar la torre.»

Y después, la parte que el prompt intuía como «composition/meta lift» y que el corpus ya
cuantifica (B 76.213–76.223):

```
Direct Marginal Lift   +300
Transitive Lift        +150
Compositional Lift     +500   ← «puede superar al marginal» (B 76.203)
Meta-Lift              +200
────────────────────────────
contribución potencial +1.150
```

**El Compositional Lift excediendo al Direct es el argumento estructural del prompt entero**: dos
features con idéntico valor local pueden valer +50 y +1.500 institucionales «porque resuelve una
primitive que beneficiará veinte proyectos» (B 76.238–76.244).

Ninguna de estas magnitudes es una medición. Son un ejemplo aritmético del corpus para enseñar
la **forma** del cálculo. Se adoptan los **términos y la estructura**; los números no se
importan a ningún artefacto.

## 5. El corpus prohíbe el Tower Score por su cuenta

El Owner dejó el escalar fuera de alcance. El corpus coincide, y por una razón propia:

> **B 92.075:** «La "torre" debe ser una proyección del **Capability Baseline Graph**, no una
> métrica que podamos inflar diciendo "esto vale +5.000". Lo correcto es medir primero el
> Marginal Institutional Lift y después convertirlo a Tower Height.»

Dos consecuencias operativas:

1. **El sustrato canónico de la Torre es el Capability Baseline Graph**, y la Torre es una
   **proyección** sobre él. Esto es exactamente lo que el §XXVII del prompt pedía («derived
   institutional view over existing authorities») y lo que el §XXVIII prohibía convertir en un
   fichero gigante. La fuente y el prompt coinciden sin haberse leído.
2. **La altura es derivada y va después.** Cualquier escalar futuro se calcula *desde* el
   Marginal Institutional Lift verificado, nunca al revés.

## 6. Lo que el «Baseline Lift global» significa — la petición del Owner, en canon

> **B 90.556–90.566:** «Eso es un **Baseline Lift global**. InfinityOps lo paga una vez. ORCA X
> lo hereda. KobiiCraft lo hereda. CostaLuz lo hereda. **El próximo software que todavía no
> existe lo hereda.**»

Es, palabra por palabra, la petición del Owner del §0 del diseño aprobado —«si yo avanzo con
QuickLease, la próxima vez que pida algo en InfinityOps…»— enunciada por la propia fuente. No es
una interpretación de la sesión: es el mismo mecanismo, nombrado.

Y su ley transversal candidata (B 90.653):

> **EVERY MATERIAL SOFTWARE CHANGE MUST BE INDEPENDENTLY CHALLENGED AT THE STRONGEST REVIEW
> LEVEL JUSTIFIED BY ITS RISK, NOVELTY, BLAST RADIUS AND CLAIMS; EVERY MATERIAL REVIEW DISCOVERY
> MUST THEN BE CAPITALIZED SO FUTURE SOFTWARE NEEDS LESS REVIEW TO AVOID THE SAME FAILURE.**

## 7. Leyes de la Torre encontradas de paso

| línea | ley |
|---|---|
| 88.781 | «56. Baseline lift must point to **causal commits**» — un Lift sin commit causal no es un Lift |
| 101.138 | «55. El Tower Lift se vuelve explícito» |
| 102.082 | «RE Lift ≠ sólo RE Lift» — una absorción rinde fuera de su dominio |
| 92.456 | «La escalera de madurez determinaría el Tower Lift» — R0…R6 en 101.751–101.759 |
| 110.396 / 111.458 | **Second-Order** y **Third-Order Baseline Lift** — el corpus llega a tres órdenes |

## 8. `Mission Genome` NO es una invención de la sesión

> **B 90.584:** «qué reviewer debe activarse según **Mission Genome**»

El término es del corpus. El §XXVI del prompt lo trataba como candidato a inventar; es
vocabulario de la fuente, y su uso allí es exactamente el que la misión necesita: **seleccionar
qué se activa**, que es lo que `applicability.py` ya hace. Refuerza `EXTEND_EXISTING_OWNER`.

## 9. Cobertura — qué autoriza este fichero a afirmar

Leídas en esta pasada: **76.160–76.250 · 89.810–90.700 · 92.060–92.140 · 102.270–102.300**, más
la enumeración completa de las 73 líneas `lift` sobre las 167.842. Eso es **~1.100 líneas
físicas leídas del sufijo**, no el sufijo.

- **Autoriza:** que existe definición canónica; que no hay un conjunto fijo de Lifts; la
  aritmética del §4; la prohibición del escalar del §5.
- **NO autoriza:** ninguna afirmación de completitud sobre las descomposiciones. La enumeración
  cubre el token `lift` en un corpus bilingüe; **`elevación`, `alza`, `subida`, `ganancia` no se
  buscaron**, y una lista escrita sólo con esos términos sería invisible a este instrumento.
  Un cero de este barrido es UNKNOWN.
- **`project challenge` y `construction return` dieron 0 sobre regex acotada por nombre.** Por
  la ley de esta misión eso es **INSTRUMENT BLIND**, no ausencia, y quedan para búsqueda por
  mecanismo. No se reportan como inexistentes.

## 10. Errores de instrumento cometidos al producir este fichero

Los tres son míos, y los tres iban contra evidencia que resultó correcta. Registrados porque la
ley de la misión aplica también a quien la ejecuta.

1. **Conteo de líneas por `Get-Content | Measure-Object -Line`: 81.779 en vez de 167.842.**
   `-Line` puntúa una línea vacía como cero, y el corpus alterna contenido y blanco. Estuve a
   una frase de reportar como falsado un handoff correcto. El conteo por bytes (`\n`) es el
   instrumento; el de PowerShell no lo es para este fichero.
2. **«El puntero 89.813 está falsado».** `04_SOURCE_RECONCILIATION.md` cita un **rango**,
   89.813–90.636. Leí su **primera línea**, encontré un encabezado de CodeRabbit, y declaré
   falsado el rango entero. Los Lifts están en 90.491, dentro del rango citado. El audit era
   exacto; lo que comprimió el rango a un número fue el handoff, y lo que no leyó el rango fui
   yo.
3. **«La cobertura es 44,89 %, no 46,4 %».** Ambas son correctas sobre denominadores distintos:
   44,89 % = 75.350/167.842 líneas **físicas**; 46,4 % = 37.947/81.754 líneas **no vacías**. La
   segunda mide contenido y es la mejor de las dos. No había nada que corregir.

Patrón común: **tres veces medí con un instrumento más pobre que el que ya estaba en el
expediente, y las tres veces concluí contra el expediente.** Es la misma familia que el cero del
ledger de compact, el sondeo del UBC y el trigger de HR-NOVELTY — cuarta, quinta y sexta
instancia del defecto que esta misión existe para cerrar.
