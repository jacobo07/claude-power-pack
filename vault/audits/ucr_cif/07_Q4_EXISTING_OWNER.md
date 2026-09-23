---
title: UCR-CIF — O2/Q4: ¿basta extender un dueño existente? Verificado contra la fuente
date: 2026-09-23
status: MEASURED — leído el código, no la cita del auditor
answers: HR-NOVELTY-001 Q4 ("Why is extending an existing owner insufficient?")
---

# Q4 — el dueño existe, y el hueco no es el que el plan creía

El audit de fase 4 (`05_PHASE4_PLAN_AUDIT.md`, G-1) sostenía que O3 duplicaría un dueño vivo.
Era una cita de subagente sin verificar. **Verificada contra la fuente: en sustancia es
correcta, con dos correcciones.**

## 1. El borde existe y está vivo

`hooks/hook-dispatcher.js:526` registra `gsd_x_tier.js` en `UserPromptSubmit-chain`, y su
comentario (`:512-515`) enuncia la reivindicación de producto de O4 palabra por palabra:

> *"Computes the ExecutionOS Lite tier from the prompt's measured evidence instead of leaving
> it to the model's self-assessment, **so the posture stops depending on the operator
> remembering to ask for it**"*

`modules/gsd_x/tier.py:257` cierra el circuito:
`MissionContext(description=prompt, available_evidence=ev)` → `evaluate_all(...)` → `classify(...)`.

Así que **prompt → MissionContext → applicability → inyección ambiente** no hay que construirlo.
Existe, está registrado y su propia nota documenta la prueba de alcanzabilidad.

## 2. El hueco real, enunciado por el propio dueño

`modules/gsd_x/tier.py:251-253`, docstring de `classify_prompt`:

> *"Owners, prerequisites and held scopes stay **EMPTY**: **a hook cannot establish them and
> guessing would defeat the point**. Evidence is the exception, and only because it is
> observable."*

Eso es el hueco, dicho por quien manda. No falta el mecanismo: falta **estado durable** que un
hook no puede calcular desde un prompt. Y es exactamente lo que un Project Genome persistido
aportaría — `resolved_owners`, `satisfied_prerequisites`, `held_scopes`.

### Pero eso es lo peligroso, no lo gratis

G-4 del mismo audit señala que esos tres campos alimentan **puertas deterministas** de
`applicability.py`, evaluadas antes de cualquier score. `tier.py` los deja vacíos **a propósito**.
Rellenarlos mal no degrada el resultado: lo **invierte** — un genoma incompleto bloquea
capacidades en vez de habilitarlas.

De modo que la parte «nueva» de O3 es precisamente la que el dueño existente evitó por diseño, y
la evitó con una razón escrita. Eso no la prohíbe; sube el listón de evidencia que debe traer.

## 3. Respuesta a Q4

**Extender el dueño existente ES suficiente en mecanismo.** Lo que no existe es estado
persistido por familia de sistema que alimente `MissionContext` con más que `description` y
`available_evidence`.

Clasificación que esto sugiere, en el vocabulario que el propio gate ofrece:
**`EXTEND_EXISTING_OWNER` más un módulo de estado persistido**, no un sistema nuevo. Un
inyector de cápsula aparte sería un segundo escritor de la postura de arranque sin regla de
precedencia entre ambos.

Esto responde **una** de las 13 preguntas. Las otras doce siguen pendientes, y Q4 es la que
más pesa contra la creación: el propio gate dice que *missing evidence on any question → not a
new dataset*.

## 4. Dos correcciones al auditor

### 4.1 G-3 CONFIRMADO, y peor de lo que lo contó

`'UserPromptSubmit-chain': 3000` está en `hook-dispatcher.js:758`. La cita era exacta. Y el
comentario que la acompaña (`:752-757`) es explícito:

> *"what a busy host now drops is **advisory injection**"*

`gsd_x_tier` es deliberadamente **no crítico** (`:521-524`: *"it is advisory, so it must not sit
in the lane reserved for guards whose absence is the harm"*). En un host cargado se cae por
diseño. Si la cápsula fuera premisa de la misión, ese carril sería el equivocado.

**Lo que el auditor no vio:** el comentario del registro en `:525` dice *"Measured child
~1.2-1.4 s against **this chain's 11500 ms deadline**"*. **Está rancio.** La deadline viva son
3.000 ms. Un comentario que afirma casi 4× la holgura real, justo al lado del registro, hace que
cualquier lector concluya que el hook cabe cómodo. Es documentación que contradice al código en
el punto exacto donde alguien iría a comprobarlo.

### 4.2 El heartbeat que G-3 pedía YA EXISTE

G-3 proponía «heartbeat por invocación escrito en toda decisión, no sólo cuando hay inyección».
`:522-524` dice que ya es así: *"Silence is a VALID result … so the evidence that it ran is its
heartbeat, never its stdout"*.

Lo que **no** está verificado es la otra mitad: que exista una clase distinta para
`ABANDONED_BY_DEADLINE` frente a `ran-and-said-nothing`. Sin ella, una cápsula abandonada por
deadline y una que no tenía nada que decir siguen siendo el mismo observable. **No medido** —
primer paso: leer qué escribe el heartbeat de `gsd_x_tier.js` y si el dispatcher registra el
abandono por deadline con identidad propia.

## 5. Estado de verificación de este fichero

| afirmación | fuente |
|---|---|
| el borde prompt→applicability existe y está registrado | leído: `hook-dispatcher.js:526`, `tier.py:257` |
| owners/prereqs/held_scopes se dejan vacíos a propósito | leído: `tier.py:251-253` |
| deadline de 3.000 ms | leído: `hook-dispatcher.js:758` |
| el comentario de `:525` está rancio | leído, ambos números |
| el heartbeat existe | leído: `:522-524` — **la afirmación del comentario**, no su ejecución |
| clase propia para abandono por deadline | **NO MEDIDO** |
