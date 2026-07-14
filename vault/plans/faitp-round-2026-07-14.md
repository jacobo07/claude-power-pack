# FAITP — Round 2026-07-14 · Reality Audit + STOP #1 proposal

> Estado: **STOP #1 — esperando aprobación del Owner. Cero tokens Fable consumidos.**
> Modo detectado: **PLAN** (no ULTRA-PLAN). Justificación en §0.

---

## 0. ROI MODE DETECTOR — veredicto con evidencia

**PLAN**, no ULTRA-PLAN.

ULTRA-PLAN se reserva para mutación constitucional o sistema nuevo desde cero
(PR-MODE-SELECTION-001). El Reality Scan demuestra que FAITP **no funda nada**:
cada artefacto que el spec propone ya tiene padre sellado en el repo.

| FAITP propone | Padre sellado ya existente | Evidencia |
|---|---|---|
| Planning Constitution (20 principios) | FD-00 root law + ACIS laws + PR-* en UKDL | `FD_INDEX.md:19-22`; `acis_01_generation_zero_laws.md` (8 leyes con falsador) |
| Architectural Judgment Records | ACIS theorem schema (E2 falsable) + deposits ledger | `acis_00_epistemic_ladder_and_theorem_schema.md` |
| Frontier Residual Map | FD-04 + CO-12 (metric owner) | `fd_04_prover.py` docstring: "FD feeds the signal, CO-12 stays the single accountant" |
| Duplicate-to-Advantage | D2A, SCS C85 | `modules/decision_review/`, sellado |
| Candidate-question selection | FIOS `question_harvester` + `session_compiler` | `SESSION_ZERO_2026-07-11T112609Z.md` (16 preguntas, 1 worthy) |
| UKDL 3 niveles | ya es la estructura de `ukdl-universal.md` | HR / PR / T |

La brecha **no es arquitectónica — es empírica**. Construir constitución nueva
sería duplicar familias selladas (GK-00 "one system, no parallels") a 3-5× coste.

---

## 1. FAITP REALITY AUDIT — hallazgo central

> **El instrumento que probaría todo lo que FAITP quiere probar no existe.**

`modules/fable_distillation/fd_04_prover.py` es el ÚNICO productor que puede
marcar `portability_proven=True`. Un grep case-insensitive de
`opus|sonnet|contrast|cross-model` sobre ese fichero devuelve **0 matches**.

El "portability prover" sólo sabe hacer 4 cosas: `file_exists`, `dir_exists`,
`attr`, `grep` — más `attestation` (texto humano). **No puede ejecutar otro
modelo.** Por tanto:

- No existe ningún baseline de Opus. Ni uno.
- No existe ninguna corrida de contraste Fable-vs-Opus-vs-Opus+PP.
- El Frontier Residual Map **no puede calcularse hoy** — le falta el numerador.
- El Supersession Criterion (§ del spec) es **inmedible por construcción**.
- `vault/benchmarks/ledger.json` son *smoke tests de latencia* (`tco_gate_ms`,
  `session_hub_ms`), no evaluaciones de calidad de modelo.

### 1.1 Estado real del ledger de depósitos (evidencia primaria)

`~/.claude/state/fable_distillation/deposits_*.jsonl` — **10 depósitos**, 2 sesiones
Fable ejecutadas (`fable-session-2-2026-07-11`, `acis-generation-zero-2026-07-11`).

| | count | detalle |
|---|---|---|
| Depósitos totales | 10 | última escritura 2026-07-11 13:45 |
| `portability_proven=true` | **5** | los 5 con `achieved_target: deterministic` |
| No probados | **5** | 3× `frontier-only`, 2× `mid-model` |
| Probados contra **otro modelo** | **0** | todas las pruebas son `file_exists` / `grep` |
| Candidatos UKDL en cola | **2** | `status: candidate -- Owner promotes`, 3 días sin promover |

**La naturaleza de las 5 "pruebas" existentes:** verifican que el *claim* es
fácticamente cierto (que `process_governor.py` existe donde el depósito dice).
**No verifican que la capacidad sea portable.** Probar que un fichero existe no
prueba que Opus habría encontrado esa arquitectura. Es prueba de *veracidad*,
no de *transferencia* — y FAITP exige lo segundo.

Los dos depósitos que sí declaran `portability_target: mid-model` — la Hard Rule
de MCP-lifecycle y la regla ACIS de no-autopromoción — son exactamente los que
**siguen sin probar**. El mecanismo `attestation` existe para ellos y nunca corrió.

### 1.2 Escalera epistemológica (ACIS, viva)

`epistemic_ladder.py`: 8 depósitos → **5×E3 + 3×E2, cero E4+**. Ninguna regla
cita todavía un `deposit_ref`, así que nada ha subido a nivel-ley. La escalera
funciona y está diciendo la verdad: **el stack no tiene conocimiento probado
por un actor distinto del que lo produjo.**

---

## 2. Overlap map — las 15 capacidades candidatas

Clasificación con evidencia. **4 NEW · 4 EXTEND · 7 REFERENCE.**

| # | Capacidad | Verdicto | Evidencia / padre |
|---|---|---|---|
| 1 | mode selection | **REFERENCE** | PR-MODE-SELECTION-001 sellado; router en PP CLAUDE.md |
| 2 | scope discipline | **REFERENCE** | HR-ONESHOT-002 (deviación >40%), `one_shot/lock.py` fidelity_score |
| 3 | existing-system reasoning | **REFERENCE** | D2A SCS C85 + HR-PREMISE-001 |
| 4 | architecture under uncertainty | **EXTEND** | ACIS E2 falsable; falta condicionalidad (§D del spec) en el registro |
| 5 | failure-centric planning | **REFERENCE** | CEPS + `cascade_prevention` + catálogo T-* |
| 6 | handoff design | **REFERENCE** | RESUMPTION_FILE + `modules/daif` session-continuity compiler |
| 7 | cross-system architecture | **REFERENCE** | Graphify (956 coordenadas) + mapas de integración FD/CO/PM |
| 8 | **simplification & retirement** | **NEW** | 0 artefactos `retirement threshold` en todo el repo. El veto Woz es estético, no un mecanismo de retiro |
| 9 | self-evolving systems | **EXTEND** | `evolution_engine.py` propone y nunca aplica; falta el criterio de aceptación |
| 10 | constitutional architecture | **REFERENCE** | FD-00 + digest HARD-RULES (SCS C92) |
| 11 | production evidence design | **REFERENCE** | Reality Contract + V-gates + Liveness Standard |
| 12 | **reversibility & blast radius** | **NEW** | No es una dimensión puntuada en ninguna parte. HR-CASCADE-002 cubre sólo `rm -rf` |
| 13 | unknown-unknown discovery | **EXTEND** | harvester vivo (5 fuentes) — rendimiento observado: 1 worthy / 16 |
| 14 | **hard-rule conflict resolution** | **NEW** | SCS C92 halló el kill switch INERTE; clase PLUGIN-INSTALL con 0 reglas; nada detecta conflictos *entre* HR |
| 15 | **frontier residue identification** | **NEW (instrumento)** | `fd_04_prover.py`: 0 matches de opus/sonnet/contrast |

---

## 3. La conclusión de ROI que el audit fuerza

> **La acción de mayor ROI de esta ronda NO es una sesión Fable.**

Gastar tokens frontier ahora deposita más claims en un ledger que ya tiene 5 sin
probar y 2 candidatos UKDL congelados. Eso viola la ley que el propio stack selló:
**PR-PROOF-OR-HYPOTHESIS-001** — un delta sin prueba de portabilidad es hipótesis,
no capital. La ronda produciría *más hipótesis*, no más capital.

Y sin el instrumento de contraste, seis de los criterios de completitud de FAITP
(transfer tests en casos no vistos · Frontier Residual Map · retirement thresholds ·
supersession criterion · distillation-by-contrast · "qué vio Fable que Opus no vio")
son **literalmente incomputables**. La ronda no podría cerrarse aunque Fable
respondiera perfectamente.

---

## 4. Propuesta — dos arcos, el segundo gated por el primero

### ARCO A — El instrumento (cero tokens Fable)

Construir lo que falta, con Opus/Claude Code, que es exactamente donde el spec
dice que Fable **no** debe usarse ("no código, no implementación").

- **A1 · Contrast harness** — EXTEND de `fd_04_prover.py`: un método de prueba
  `cross_model` que corre el mismo hard case en `Agent(model=opus)` y
  `Agent(model=sonnet)` contra la respuesta Fable ya depositada, y puntúa con un
  rúbrica determinista. El harness del host ya soporta `model:` en el tool Agent —
  la capacidad existe, el cableado no.
- **A2 · Correr A1 sobre los 5 depósitos no probados.** Salida: el **primer
  Frontier Residual Map con números reales**, no declarado.
- **A3 · Desatascar la cola UKDL** — 2 candidatos llevan 3 días en
  `status: candidate`. Promoción o descarte explícito (T-OWNER-QUEUE-INVISIBLE-001).
- **A4 · Retirement thresholds** (capacidad #8) — derivables *sólo después* de A2.

**Coste estimado: ~120k tokens Opus. Tokens Fable: 0.**

### ARCO B — Fable, sólo sobre el residuo que sobreviva a A (gated)

Tras A2, sabremos qué capacidades Opus reprodujo. Sólo lo que Opus **falló** va a
Fable. Portfolio mínimo candidato hoy (a re-priorizar con los datos de A2):

| # | Pregunta candidata | Por qué Fable y no Opus | Activo esperado | Saturación |
|---|---|---|---|---|
| B1 | Resolución de conflictos entre Hard Rules (#14) | Requiere razonamiento constitucional sobre 40+ HR con precedencia no declarada; Opus tiende a obedecer la última leída | Hard Rule de precedencia + detector de conflictos | 2 respuestas sin conflicto nuevo |
| B2 | Blast radius / reversibilidad como dimensión puntuada (#12) | Juicio sobre irreversibilidad con evidencia débil — el residuo frontier clásico | Process Rule + gate | 2 respuestas sin dimensión nueva |

**B1 y B2 sólo se ejecutan si A2 demuestra que Opus no las resuelve.** Si Opus las
resuelve, se retiran de Fable por Automatic Capability Retirement — y esa retirada
*es* el entregable de la ronda.

**Presupuesto Fable segmentado (techo, sólo si se abre el Arco B):**

| categoría | % | tokens |
|---|---|---|
| reality (ya gastado en Opus) | — | 0 |
| divergence | 30% | 24k |
| convergence | 25% | 20k |
| critique | 25% | 20k |
| synthesis | 10% | 8k |
| next-question-generation | 10% | 8k |
| **total techo Fable** | | **80k** |

---

## 5. Criterios de éxito y parada

**Éxito de la ronda (no negociable):**
- El Frontier Residual Map tiene números medidos, no declarados. Es la primera vez.
- ≥1 capacidad **retirada** de Fable con evidencia (bajada a Opus/determinista).
- Los 5 depósitos no probados salen del limbo: PROVEN, FAILED o DISCARD explícito.
- La cola UKDL queda en 0 candidatos sin decidir.
- `REMOTE_DELTA = 0 0`.

**Parada anticipada:** si A2 demuestra que Opus reproduce las 15 capacidades, la
ronda **cierra sin abrir el Arco B** y el entregable es la retirada masiva. Ese
sería el mejor resultado posible: dependencia frontier reducida a cero con evidencia.

**Production Reality Gates:** cada V-gate del arco A observado en verde ×3 hermético
antes de sellar. Micro-commits con pathspec. Push al cierre de cada arco.

---

## 6. Deuda declarada al entrar

- 4 commits locales sin pushear (`REMOTE_DELTA = 0 4`) — se resuelve en el primer
  micro-commit del Arco A.
- DAIF (SCS C95): 8 datasets / 160 Parts sellados como **spec, no sistema corriendo**.
  Esta ronda es precisamente la "primera vertical de prueba" que su cierre reclamaba.
