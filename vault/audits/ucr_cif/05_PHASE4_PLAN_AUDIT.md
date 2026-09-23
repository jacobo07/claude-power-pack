---
title: UCR-CIF — Fase 4 ONESHOT, auditoría adversarial del plan Torre Universal (O1–O4)
date: 2026-09-23
status: RECIBIDO — hallazgos del subagente `oneshot-architect-auditor`, pendientes de verificación independiente salvo donde se indica
verdict: ARCHITECTURAL REPAIR REQUIRED en O3/O4 · O1 y O2 READY
mode_verdict: PLAN MODE correcto — no escalar a ULTRA-PLAN
---

# Fase 4 — auditoría adversarial del plan

## 0. Procedencia y por qué este fichero lo escribo yo

Estos hallazgos los produjo el subagente `oneshot-architect-auditor` (fase 4 del protocolo
ONESHOT). **No pudo escribir su propio entregable**: `Write` está deshabilitada en subagentes
en esta sesión. Lo registró como instrumento ausente en vez de rodear la puerta — correcto — y
entregó el informe como mensaje. Se transcribe aquí para que no muera en una conversación que
se compacta.

**Son salida de modelo, no medición del Owner.** Cada cita `file:line` es del auditor salvo
donde la columna diga otra cosa. Un hallazgo con cita no verificada es una hipótesis con
dirección, no un hecho.

| hallazgo | estado de verificación |
|---|---|
| G-1 … G-5, G-7 | **citado por el auditor, NO verificado independientemente** |
| G-6 | **RESUELTO por medición propia** — ver `04_SOURCE_RECONCILIATION.md` |

## 1. Premisas del plan que el auditor confirma CIERTAS

No son huecos; son el suelo sobre el que O3 puede apoyarse.

- **`applicability.py` existe y hace lo que el plan dice.** `modules/capability_runtime/applicability.py:116` `evaluate()`, `:222` `evaluate_all()`, `:234` `compile_stack()`; cinco puertas deterministas antes de cualquier score (`:120,:138,:146,:151,:158,:164`); verdicts en `:210-216`; stdlib-only y fail-open (`:226`).
- **FD-04 es código ejecutable, no doctrina.** `modules/fable_distillation/fd_04_contrast.py`, `fd_04_prover.py`, `fd_04_acceleration.py`, con gates propios. **Pero mide otra variable — G-2.**
- **HR-NOVELTY-001 es ejecutable hoy.** `modules/spec_gate/gate.py:287` `check_novelty_gate()`, 13 preguntas en `:237`, triggers `:255`.
- **`applicability.py` es alcanzable en producción**, no es módulo huérfano: `settings.json → hook-dispatcher.js:526 → hooks/gsd_x_tier.js → modules/gsd_x/tier.py:49`.

## 2. Los siete huecos

### G-1 · CRITICAL — O3 crearía un SEGUNDO dueño de un efecto ya vivo
`hooks/hook-dispatcher.js:512-526` (registro) · `modules/gsd_x/tier.py:49,:257` (consumidor)

El comentario del registro dice literalmente *"Computes the ExecutionOS Lite tier from the
prompt's measured evidence instead of leaving it to the model's self-assessment, **so the
posture stops depending on the operator remembering to ask for it**"*. Ésa es, palabra por
palabra, la reivindicación de producto de O4. Y `tier.py:49` ya importa `Applicability`,
`MissionContext`, `Verdict`, `evaluate_all`; `:257` ya construye `MissionContext(description=prompt…)`.

El borde «prompt → MissionContext → applicability → inyección ambiente vía hook» **ya está
construido y es alcanzable**. Un inyector de cápsula nuevo sería autoridad paralela sobre el
mismo efecto, con dos escritores de la postura de arranque y ninguna regla de precedencia.

**Arreglo propuesto:** reescribir O3 como EXTEND de `modules/gsd_x/tier.py` + `hooks/gsd_x_tier.js`.
Lo genuinamente nuevo es el **estado persistido** que alimenta `MissionContext` — hoy se
reconstruye desde cero en cada prompt. **HR-NOVELTY-001 aplica a O3, no sólo al Ratchet.**

### G-2 · HIGH — el harness de FD-04 mide la variable equivocada
`modules/fable_distillation/fd_04_contrast.py:1-13,:44-47,:49`

Su variable independiente es **el sustrato de modelo**, no la presencia de la cápsula:
*"poses a deposited judgment as a cold question to a cheaper substrate (`claude -p --model <m>`)"*,
con `_LADDER = (("sonnet","small-model"),("opus","mid-model"))`. Responde *«¿un modelo más
barato reproduce este juicio?»*. El A/A que el plan necesita es *«¿el MISMO agente arranca más
alto CON vs SIN cápsula?»*. Reutilizarlo da un número real a otra pregunta.

**Agravante medido:** `_CLI_TIMEOUT_S = 240` × escalera de dos modelos, spawneando `claude -p`,
en un host al 10 % de RAM libre — el instrumento consume el recurso que mide.

**Arreglo:** no reutilizar el harness. Sí reutilizar su **disciplina de controles**
(`controls_hold()` en `:88`: el polo positivo debe reproducir, la respuesta vacía debe fallar,
y la corrida se descarta si los controles no se sostienen).

### G-3 · CRITICAL — O4 es INFALSIFICABLE: el canal puede abandonarse en silencio
`hooks/hook-dispatcher.js:758` (`UserPromptSubmit-chain: 3000`) · `:521-524` (gsd_x_tier **no** es `critical`) · `:735-757` (la medición que lo justifica)

Medido el 2026-09-22 y escrito en el propio fichero: un prompt ordinario cuesta **13.543 ms en
frío / 4.408 ms en caliente**, y uno pegado de 10 KB **11.611–11.820 ms**, contra una deadline
de **3.000 ms**. Los miembros no críticos se abandonan.

Una cápsula calculada-y-abandonada y una que no tenía nada que decir **son el mismo
observable**. Un verde y un silencio no se distinguen, y un rojo acusa al contenido cuando la
causa es la deadline.

**Arreglo:** heartbeat por invocación escrito en TODA decisión —no sólo cuando hay inyección—
y una clase de log propia `ABANDONED_BY_DEADLINE` distinta de `ran-and-said-nothing`. Y decidir
el carril: si la cápsula es premisa de la misión, no puede vivir en el carril advisory de una
cadena que se pasa de deadline en cada prompt frío.

*(Nota propia: esto es el gemelo exacto del defecto que se acaba de cerrar en el daemon de
auto-compact — un camino cuyo éxito no deja registro sólo puede responder «nunca». Ver
`vault/backlog/2026-09-23_autocompact-withdrawal-race.md`.)*

### G-4 · HIGH — el genoma alimenta PUERTAS, no sólo el score
`modules/capability_runtime/applicability.py:158-161` (gate 4 `held_scopes`) · `:146-148` (gate 2 `resolved_owners`) · `:151-155` (gate 3) · `:138-143` (sin trigger → dormant)

Los campos que el Mission Baseline Capsule / Project Genome aportarían entran en **puertas
deterministas que se evalúan antes de cualquier score**. Un genoma incompleto o rancio
**bloquea** capacidades en vez de habilitarlas — el efecto inverso al objetivo del plan. Hoy no
ocurre porque `tier.py:257` construye el contexto sólo con `description` + `available_evidence`.

**Arreglo:** declarar por escrito, antes de construir, qué campos del genoma pueden tocar las
puertas y cuáles sólo el score. Por defecto el genoma alimenta score y `available_evidence`;
`held_scopes` y `resolved_owners` exigen frescura probada. **Un campo ausente debe significar
*no medido* (omitir), nunca *conjunto vacío*** — en `:146` un conjunto vacío desactiva la
puerta y uno parcial la convierte en veto universal.

### G-5 · HIGH — el artefacto persistido necesita el dueño canónico de identidad de repo
`modules/repo_identity/identity.py:1-34,:41-49,:56`

Ese módulo existe **exactamente** porque los ledgers per-repo se nombraban slugueando el cwd,
de modo que un `cd` a un subdirectorio creaba una segunda identidad con su ledger vacío
(medido 2026-09-05). Un Project Genome con clave propia repetiría un defecto ya pagado.

**Arreglo:** O3 obtiene su clave de `repo_identity.canonical_repo`/`repo_key`, con aserción de
que el genoma de un subdirectorio resuelve a la misma clave que el de la raíz. Ojo a `:46-49`:
el `.git` de un worktree es un **fichero**, no un directorio — y este árbol tiene worktrees
activos (`.claude/worktrees/gsd-x/`), así que el caso es real, no hipotético.

### G-6 · MEDIUM — **RESUELTO, no pendiente**
El auditor avisaba de que O1 no tenía rama para «no contenido» y de que el sufijo `(1)` es el
patrón clásico de re-descarga. El aviso era correcto como crítica del plan. **La medición ya
corrió**: B es superset estricto de A, 37.947/37.947 = 100,0 %, mapeo monótono hasta la línea
75.350 de B. Ver `04_SOURCE_RECONCILIATION.md`. La rama `NOT_CONTAINED` no se necesitó.

### G-7 · HIGH — falta una O0: no hay control previo al cambio
Contrato del diseño aprobado: `docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md:223-224`

El orden **entre** ondas es correcto (O1 re-ancla el denominador que O2 necesita; O2 decide
EXTEND-vs-CREATE antes de que O3 construya). El defecto es **interno a O3**: el suelo de ruido
«sin cápsula» debe capturarse *antes* de que la cápsula exista, o el umbral se elige viendo los
números.

Y hay un problema de definición: CRR y RFR son **tasas sobre una población de misiones a lo
largo del tiempo**. **Una sola misión (O4) no puede mover una tasa**, y la misma misión no se
puede correr dos veces con el mismo agente honestamente — la segunda está contaminada por la
primera.

**Arreglo:** insertar **O0** antes de O3 — predeclarar por escrito el oráculo (qué significa
«arranca más alto», observable), la población sujeto, los chequeos de validez por corrida y los
umbrales, y **registrar los veredictos «sin cápsula» sobre un conjunto reservado de
descripciones de misión ANTES de que la cápsula exista**. Y separar las dos afirmaciones que O4
confunde: (a) *el borde causal existe* — probable por mutación+hash, oráculo determinista;
(b) *la misión arranca más alto* — requiere O0.

CRR/RFR aparecen sólo en 5 ficheros del repo, todos de diseño o auditoría: **no existe ninguna
medición previa**, así que O0 no es opcional.

## 3. Veredicto de modo

**PLAN MODE correcto. No escalar a ULTRA-PLAN** — su coste ya está pagado por el diseño
aprobado; reabrir arquitectura sería planificación duplicada.

- **O1 y O2 → EXECUTION MODE, ejecutables ya.** Ambas son mediciones sobre instrumentos que
  existen. *(O1 ya ejecutada.)*
- **O3 y O4 → bloqueadas hasta cerrar G-1, G-3 y G-7.**

**DONE GRADE máximo alcanzable hoy: SPECIFIED.** Nada de O3/O4 está IMPLEMENTED ni WIRED.

## 4. DO NOT BUILD

Un segundo inyector ambiente de postura de misión · un esquema de identidad de repo propio para
el genoma · un harness A/A nuevo desde cero (extender la disciplina de controles de
`fd_04_contrast`, no el instrumento) · cualquier medición A/A que gaste `claude -p` en este host
antes de bajar la presión de RAM.

## 5. Candidato a UKDL

G-4 es transferible más allá de este plan: **un campo de estado persistido que alimenta una
puerta determinista invierte su propio objetivo cuando está rancio.** Es el gemelo de «ausencia
no es cero» aplicado a puertas en vez de a métricas. No promovido — requiere el proceso
habitual.
