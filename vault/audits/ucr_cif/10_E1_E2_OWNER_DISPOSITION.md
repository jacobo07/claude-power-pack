---
title: UCR-CIF — E1/E2: Construction Return y Composición tienen dueño. Los ceros eran del instrumento.
date: 2026-09-23
status: MEASURED — dos instrumentos sobre la misma población, ambos reportados
instrument: scratchpad/e1e2_sweep.py — sonda por NOMBRE y sonda por MECANISMO, con suelo de población (400) que hace fallar el barrido en vez de reportar limpio
closes: E1 y E2 del spec R1 §13 · secciones 52 y 53 del prompt de misión ("no vague future work")
---

# E1/E2 — tipados, con dueño nombrado

## 1. El diseño del barrido, que es la mitad del resultado

Se corrieron **dos instrumentos sobre la misma población** y se reportan los dos, para que la
ceguera del primero sea visible en vez de asumida. La población se barrió sobre `modules/`,
`tools/`, `hooks/`, `commands/`, `agents/`: **1.256 ficheros**, con **suelo de 400** — un barrido
que deja de encontrar nada **falla con exit 2**, no reporta limpio.

| sonda | E1 Construction Return | E2 Composición |
|---|---:|---:|
| **por NOMBRE** (lo que buscó la sesión anterior) | **0 hits** | 3 hits, ninguno un dueño |
| **por MECANISMO** (lo que la capacidad *haría*) | **235 ficheros** | **217 ficheros** |

**El `NO IDENTIFICADO` de las dos filas del §5 del handoff era un cero acotado por vocabulario.**
Séptima y octava instancia del mismo defecto en esta jornada.

## 2. E1 — Construction Return: `EXTEND`, y el dueño es FD-07

> **Dueño: `modules/fable_distillation/fd_07_flywheel.py`.**

No es una coincidencia de palabras. Su API implementa la definición canónica de la Torre
(B 102.293) cláusula por cláusula, en otro vocabulario:

| `Baseline Tower Lift = verified capability delta, deduplicated against existing capability state` | FD-07, leído |
|---|---|
| **`capability delta`** | `classify_delta(claim, existing_fps, existing_token_sets)` → `NEW` · `STRONGER` · `DUP` · `DISCARD` |
| **`deduplicated against existing capability state`** | Jaccard contra los depósitos previos; `DUP` = *«the floor already holds it»*; `_fingerprint(destination, claim)` |
| **`verified`** | `Deposit.portability_proven: bool` — **siempre `False`, y el comentario dice `# always False here -- honest`** |

La tercera fila es la que más pesa. FD-07 **se niega a afirmar que un delta esté verificado**, y
lo documenta: *«ESTIMATED, not FD-04 tested — the transfer test is the EXECUTION-v2 follow-up;
flagged as such so the portability slope never rises on an unproven downgrade»*. Eso es la
cláusula `verified` de la definición canónica, retenida honestamente, escrita meses antes de que
nadie leyera esa línea del corpus.

Y la aritmética del §12.2 del spec también está ahí: `DISCARD` + `DUP` son exactamente el
descuento del corpus (*«400 ya estaban cubiertos por CPP»*), y `NEW` + `STRONGER` son el
**Marginal Institutional Lift**.

**Fragmentos adicionales, todos vivos, ninguno dueño:**

| fragmento | qué aporta |
|---|---|
| `modules/graphify/session_writeback.py` → `writeback(cwd, quiet, force)` | escritura al grafo de conocimiento, con guardia y estado |
| `modules/fable_distillation/ukdl_queue.py` | cola de candidatos a UKDL |
| `tools/ceps.py` + `tools/ceps_promote_stop.py` | promoción por el lado del error recurrente |
| `modules/frontier_intelligence/session_compiler.py` | compilación de sesión |
| `modules/duplicate_to_advantage/d2a_engine.py` | veredicto de duplicado antes de construir |
| `commands/compound.md` (Compound Learnings) | materialización de artefactos aprobados |

**Disposición: `EXTEND` — nunca `CREATE`.** El prompt de esta misión lo decía en su sección 69
—*«Use existing FIOS / FD-07 owner. Do not manufacture portable assets»*— mientras el handoff
mantenía la fila en `NO IDENTIFICADO`. La respuesta estaba dentro del propio encargo.

**Borde que falta (esto sí es el delta real):** ningún fragmento cierra el lazo hacia la
*aplicabilidad*. FD-07 deposita y clasifica; nadie convierte un depósito `NEW`/`STRONGER` en una
entrada de baseline por familia que `applicability.py` pueda consumir en el arranque de la
siguiente misión. **Construction Return escribe; Project Birth lee; no hay conector.** Ése es el
hueco, y es mucho más pequeño que «no hay dueño».

## 3. E2 — Composición / síntesis: `CONNECT`

> **No existe un «Composition Engine», y tampoco hace falta.** El mecanismo está repartido en
> 217 ficheros y su anfitrión natural ya existe.

| fragmento | qué aporta | fichero |
|---|---|---|
| **composición de capacidades** | `compile_stack(ctx, contracts, contracts_dir)` — compone la pila aplicable a una misión | `modules/capability_runtime/applicability.py` |
| invocación | resolución y llamada | `modules/capability_runtime/invocation.py` |
| coste de oportunidad | qué se deja de hacer | `modules/ias_c2/opportunity_cost.py` |
| asignación del siguiente mejor paso | cola y recomendación | `modules/backlog_autopilot/engine.py` · `commands/what-now.md` |
| minería de patrón repetido | 95 ficheros tocan el mecanismo | CEPS |
| propuesta de orden superior | clasificación de novedad | `modules/spec_gate/gate.py` · `commands/capability.md` |

**Disposición: `CONNECT`, anfitrión `modules/capability_runtime/`.** `compile_stack` ya es la
composición; lo que no existe es que su salida alimente una **detección de que la combinación
desbloquea una capacidad nueva** — el `Compositional Lift` del §12.2, que el corpus dice que
*puede superar al Direct* (B 76.203).

**No se implementa en esta misión.** Hidden Invention sigue en backlog por decisión del Owner, y
la sección 30 del prompt pide descubrimiento de dueño, no síntesis.

## 4. Lo que este fichero NO afirma

- **No** afirma que FD-07 esté *alcanzado* en producción. Mide que existe y qué hace, leído. Si
  nadie lo invoca, es la Liveness Standard quien lo dice — `python modules/liveness/reachability.py`
  es el instrumento, y **no se ha corrido en esta pasada**.
- **No** afirma que los 235 ficheros E1 sean todos dueños. Son la **superficie del mecanismo**;
  el dueño es uno y está nombrado.
- **No** afirma cobertura del sufijo del corpus para estos dos conceptos: `project challenge` y
  `construction return` siguen dando 0 por nombre **en el corpus**, y eso sigue siendo
  INSTRUMENT BLIND allí, no aquí.
- El solapamiento E1∩E2 (87 ficheros) **no** se ha desambiguado. Un fichero que toca los dos
  mecanismos puede ser dueño de uno y consumidor del otro; el barrido no lo distingue.

## 5. Consecuencia para la Torre

Tres de las cinco filas problemáticas del §5 del handoff han caído contra un barrido por
mecanismo:

| concepto | handoff | medido |
|---|---|---|
| Applicability / UBC | OWNED | OWNED — confirmado en fuente |
| Resident Kernel | *ausente* → **disperso** | disperso, 4.393 hits / 483 ficheros |
| **Construction Return** | **NO IDENTIFICADO** | **`EXTEND` → FD-07** |
| **Composición / síntesis** | **NO IDENTIFICADO** | **`CONNECT` → `capability_runtime`** |
| semántica canónica de Torre | NO EXISTE | **existe en el corpus** (B 102.293); sin dueño en disco |

**La Torre está mucho más construida de lo que cualquier documento de esta misión creía.** Lo que
falta no son sistemas: son **conectores** entre dueños que ya existen y no se hablan — que es
exactamente lo que la sección 79 del prompt pedía descubrir antes de construir nada.
