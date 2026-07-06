# ULTRA PLAN MODE → EXECUTION MODE: La Señal P0 como Árbitro de Ruta

**Informe de investigación · Claude Code Planning Substrates · 2026-06-29**

---

## Resumen ejecutivo

Claude Code expone **dos sustratos de planificación distintos** —*Plan Mode* (local, in-process) y *Ultraplan* (remoto, cloud-offloaded)— que convergen en una única transición operativa: **plan aprobado → modo ejecución**. La directiva del prompt, `MODO: ULTRA PLAN MODE → EXECUTION MODE (el P0 de señal decide)`, no describe un flujo lineal obligatorio, sino una **bifurcación gobernada por una señal de prioridad cero (P0)**: el *blast radius* estimado de la tarea (número de archivos, número de módulos, horizonte temporal y certeza del alcance) determina *cuál* de los dos sustratos planifica, y solo después se entra a ejecución.

La tesis central es que **la elección de sustrato es la decisión P0**, no un detalle de implementación. Elegir mal —Plan Mode para una refactorización de 40 archivos cross-module, o Ultraplan para arreglar un bug de 3 archivos— degrada calidad de plan, consume cómputo innecesario, o satura el contexto local. El presente informe consolida toda la evidencia disponible sobre ambos sustratos, su máquina de estados, la (no confirmada) arquitectura de 5 fases de Plan Mode V2, y formaliza el heurístico de selección que la señal P0 encarna.

> **Nota de confianza:** parte del material sobre Plan Mode V2 proviene de *CCLeaks* y está **sin confirmar**. Se marca explícitamente en su sección. Lo relativo a Plan Mode V1 y a Ultraplan (research preview) está respaldado por la documentación de comportamiento observado.

---

## 1. Los dos sustratos de planificación

| Dimensión | **Plan Mode** (local) | **Ultraplan** (cloud) |
|---|---|---|
| Estado / naturaleza | Estado de ejecución *read-only* in-process | Sesión cloud dedicada (research preview) |
| Motor | Sesión local actual | **Opus 4.6** dentro de **Cloud Container Runtime (CCR)** |
| Ventana | Sin límite duro propio | **Hasta 30 minutos** en modo read-only |
| Gating técnico | `toolPermissionContext = 'plan'` (vs `'auto'` / `'default'`) | Sesión remota desacoplada del proceso local |
| Requisitos | Ninguno externo | **Repo GitHub + cuenta web `code.claude.com`** |
| Paralelismo de exploración | 1 hilo local | **Max/Enterprise: 3 agentes** · **Standard: 1 agente** |
| Coordinación multi-worker | N/A | **Scratchpad compartido** `/tmp/claude-{uid}/{cwd}/{sessionId}/scratchpad/` (perms `0o700`) |
| Salida | `plan.md` ordenado | Plan refinable, reimportable a sesión local |
| Compute footprint | Consume contexto/cómputo local | **Offload** — alivia laptops con memoria limitada |

### 1.1 Restricción de exclusión mutua (crítica)

Ultraplan y **Remote Control no pueden correr simultáneamente**: ambos consumen el mismo recurso `claude.ai/code`. Esto es una restricción de planificación operativa de primer orden —si una sesión de Remote Control está activa, Ultraplan está bloqueado, y la ruta P0 *debe* recaer en Plan Mode local o esperar.

---

## 2. Plan Mode (local) — arquitectura y máquina de estados

Plan Mode es un **estado de ejecución de solo lectura** gobernado por la variable `toolPermissionContext`. Cuando vale `'plan'`, las herramientas de mutación quedan inhibidas; el agente puede leer, buscar y razonar, pero no escribir hasta que el plan sea aprobado y el contexto vuelva a `'default'`/`'auto'`.

### 2.1 Máquina de estados (V1)

```
EnterPlanModeTool        (requiere aprobación EXPLÍCITA del usuario)
        │
        ▼
AskUserQuestionTool / BriefTool   (resuelve ambigüedad)
        │
        ▼
ExitPlanModeTool         (entrega estrategia de implementación concreta;
                          el usuario DEBE aprobar para volver a impl. mode)
```

- **`EnterPlanModeTool`** — transición de entrada; **no es automática**, requiere consentimiento explícito del usuario.
- **`AskUserQuestionTool` / `BriefTool`** — fase de desambiguación: el agente *no adivina*, formula preguntas hasta cerrar el alcance.
- **`ExitPlanModeTool`** — entrega la **estrategia de implementación concreta**. La salida de esta fase es el *gate* hacia ejecución: sin aprobación del usuario, no hay vuelta a *implementation mode*.

### 2.2 Activación

| Método | Detalle |
|---|---|
| **Shift+Tab ×2** | Cicla `default → auto-accept → plan` |
| **`/plan`** | Disponible desde **v2.1.0+** |

### 2.3 Artefacto de salida: `plan.md`

El `plan.md` ordenado contiene, como contrato mínimo:

1. **Task summary** — resumen de la tarea.
2. **Files to modify / create** — inventario explícito de superficies de cambio.
3. **Execution steps** — pasos ordenados.
4. **Dependencies** — dependencias entre pasos/archivos.
5. **Edge cases / risks** — casos límite y riesgos.

Este artefacto es el **input directo de la fase de ejecución**: la transición `PLAN → EXECUTION` consume `plan.md` como semilla de tareas.

---

## 3. Ultraplan (cloud) — el sustrato de gran escala

Ultraplan (`/ultraplan`, **research preview**) **enruta la fase de planificación a una sesión cloud dedicada**. Es el sustrato diseñado para alcances que excederían sanamente el contexto y el cómputo locales.

### 3.1 Arquitectura

- **Motor:** Opus 4.6 dentro del **Cloud Container Runtime (CCR)**.
- **Ventana:** hasta **30 minutos** en **modo read-only** (espejo del principio de Plan Mode: explorar sin mutar).
- **Disparadores (tres vías):**
  1. El comando `/ultraplan`.
  2. La **palabra `ultraplan` en cualquier prompt** (disparador léxico).
  3. **Refinar un plan local** (escalada desde Plan Mode hacia el sustrato cloud).
- **Requisitos:** repositorio **GitHub** + cuenta web **`code.claude.com`**.

### 3.2 Paralelismo de exploración por tier

| Tier | Agentes de exploración paralelos |
|---|---|
| **Max / Enterprise** | **3** |
| **Standard** | **1** |

El paralelismo es la ventaja diferencial del sustrato cloud: tres agentes pueden barrer simultáneamente tres superficies del repo. Esto se coordina mediante el **scratchpad compartido cross-worker**:

```
/tmp/claude-{uid}/{cwd}/{sessionId}/scratchpad/   (modo 0o700, owner-only)
```

El scratchpad es el bus de hallazgos compartidos entre workers —un worker deposita lo que descubre y los otros lo leen, evitando re-exploración redundante. El permiso `0o700` confina el acceso al owner del proceso.

> **Cross-doctrina de host (relevante para este repo):** la doctrina local de KobiiCraft **limita a 2 los Agent/Explore paralelos en Windows** por fragilidad del bridge MSYS2. El paralelismo de 3 agentes de Ultraplan ocurre **en CCR (Linux cloud)**, no en el host local, por lo que **no colisiona** con el cap-2 de Windows. La distinción importa: el cap-2 protege el transporte local; el paralelismo-3 vive en el contenedor remoto.

---

## 4. Plan Mode V2 — las 5 fases gated *(CCLeaks · SIN CONFIRMAR)*

> ⚠️ **Confianza baja.** Lo siguiente proviene de *CCLeaks* y **no está confirmado**. Se documenta por completitud; **no debe tratarse como contrato estable**.

Plan Mode V2 estructuraría el trabajo en **5 fases gated**:

| # | Fase | Función |
|---|---|---|
| 1 | **Interview** | Desambiguación dirigida (entrevista al usuario) |
| 2 | **Planning** | Construcción del plan |
| 3 | **Execution** | Aplicación de cambios |
| 4 | **Verification** | Verificación de resultados |
| 5 | **Review** | Revisión final |

**Controles asociados (también sin confirmar):**

- **Interview** estaría **feature-flagged** tras `tengu_plan_mode_interview_phase`.
- **Variantes de tamaño de plan** en A/B testing, nombradas **`trim` / `cut` / `cap`** (presumiblemente niveles crecientes de poda del plan).
- **Control de razonamiento `UltraThink`** con modos **`adaptive` / `enabled` / `disabled`**.

La relevancia para la directiva del prompt es directa: **si V2 se confirmara**, las fases 3–5 (Execution → Verification → Review) formalizarían el lado "EXECUTION MODE" de la transición que el prompt nombra, con verificación y revisión como gates post-ejecución —alineado con el estándar de completitud del proyecto (tests por la razón correcta + evidencia empírica).

---

## 5. El heurístico de selección — **la señal P0 decide**

El núcleo de la directiva `el P0 de señal decide` es el **heurístico documentado de selección de modo**. La señal P0 es el conjunto de propiedades de la tarea que determina, *antes de cualquier acción*, qué sustrato planifica.

### 5.1 Tabla de decisión

| Señal P0 (propiedad de la tarea) | → **Plan Mode** | → **Ultraplan** |
|---|---|---|
| **Conteo de archivos** | **3–10 archivos** (foco acotado) | **10+ archivos** |
| **Dispersión modular** | Dentro de un módulo / acotado | **A través de múltiples módulos** |
| **Horizonte temporal** | Tarea inmediata, un plan ahora | **Multi-día / multi-ticket** |
| **Certeza del alcance** | *Blast radius* conocido | **Blast radius incierto** |
| **Restricción de hardware** | Sin presión de memoria | **Laptop con memoria limitada** (offload de cómputo) |
| **Necesidad** | "Necesito un plan ya" | Exploración profunda previa al plan |

### 5.2 Formalización de la señal P0

La señal P0 puede leerse como un **OR de gatillos de escalada a Ultraplan**: *cualquiera* de los siguientes empuja la decisión del sustrato local al sustrato cloud:

1. `files ≥ 10`, **o**
2. `modules > 1` (cross-module), **o**
3. `horizon = multi-day | multi-ticket`, **o**
4. `blast_radius = uncertain`, **o**
5. `host_memory = constrained`.

Si **ninguno** dispara y la tarea cae en `3 ≤ files ≤ 10` con alcance conocido → **Plan Mode** es la ruta correcta. Esta es la lectura operativa de *"el P0 de señal decide"*: **una sola propiedad dominante de la tarea —la de mayor prioridad— resuelve la bifurcación, sin necesidad de evaluar el resto.**

### 5.3 Por qué P0 y no una media ponderada

El framing como **prioridad cero** (no como score continuo) es deliberado: un único gatillo crítico —p. ej. *blast radius incierto*— basta para justificar el offload a Ultraplan, **aunque** el conteo de archivos parezca bajo. La incertidumbre de alcance es, por sí sola, razón suficiente para los 30 min read-only + 3 agentes de exploración del CCR. La señal P0 es **cortocircuitante**: el primer gatillo que se cumple decide.

---

## 6. La transición `ULTRA PLAN MODE → EXECUTION MODE`

La directiva nombra una **secuencia con bifurcación condicional**, no un pipeline rígido. Reconstruida:

```
                 ┌─────────────────────────────────────────┐
                 │   EVALUAR SEÑAL P0 (blast radius, files, │
                 │   modules, horizon, host memory)          │
                 └───────────────┬──────────────────────────┘
                                 │
              P0 dispara escalada │ ninguno dispara
                ┌────────────────┴───────────────┐
                ▼                                 ▼
        ┌───────────────┐                 ┌───────────────┐
        │  ULTRAPLAN     │                 │   PLAN MODE    │
        │  (CCR/Opus 4.6 │                 │  (local,       │
        │   read-only    │                 │   read-only,   │
        │   ≤30min,      │                 │   plan.md)     │
        │   1–3 agentes) │                 └───────┬───────┘
        └───────┬───────┘                          │
                │  plan refinado                    │ ExitPlanModeTool
                │  reimportado a sesión local       │ (aprobación usuario)
                └────────────────┬──────────────────┘
                                 ▼
                       ┌──────────────────┐
                       │  EXECUTION MODE   │
                       │  (toolPermission  │
                       │   = auto/default; │
                       │   mutaciones ON)  │
                       └──────────────────┘
```

**Puntos clave de la transición:**

1. **El plan es read-only en ambas ramas.** Ni Plan Mode (V1) ni Ultraplan mutan el repo. La mutación empieza solo al cruzar a Execution.
2. **El gate de cruce es aprobación humana.** En Plan Mode V1, `ExitPlanModeTool` exige aprobación explícita del usuario antes de volver a *implementation mode*. Ultraplan entrega un plan refinable que se reimporta a la sesión local —y de ahí al mismo gate de aprobación.
3. **Ultraplan puede *alimentar* a Plan Mode.** El tercer disparador de Ultraplan ("refinar un plan local") significa que la ruta no es exclusiva: un plan nacido local puede escalarse al cloud para profundizarlo, y volver. Las dos ramas no son mutuamente excluyentes en el tiempo, solo en el instante de decisión P0.
4. **Si V2 se confirma**, "EXECUTION MODE" no es terminal: lo siguen **Verification** y **Review** como gates post-ejecución.

---

## 7. Tabla comparativa consolidada

| Atributo | Plan Mode V1 | Ultraplan | Plan Mode V2 *(no confirmado)* |
|---|---|---|---|
| Localidad | Local in-process | Cloud (CCR) | Local (presumido) |
| Modelo | Sesión local | Opus 4.6 | — |
| Read-only | Sí (`tpc='plan'`) | Sí (≤30 min) | Sí (fases 1–2) |
| Fases | Enter → Q&A → Exit | Explore → plan | Interview→Plan→Exec→Verify→Review |
| Paralelismo | 1 | 1 (Std) / 3 (Max/Ent) | — |
| Activación | Shift+Tab×2, `/plan` (v2.1.0+) | `/ultraplan`, palabra "ultraplan", refinar plan local | feature-flag `tengu_plan_mode_interview_phase` |
| Requiere GitHub+web | No | **Sí** | — |
| Exclusión con Remote Control | No | **Sí** (comparten `claude.ai/code`) | — |
| Coordinación | N/A | Scratchpad `0o700` | — |
| Aplicabilidad P0 | 3–10 files, alcance conocido | 10+ files, cross-module, multi-día, incierto, memoria limitada | — |
| Salida | `plan.md` (summary/files/steps/deps/risks) | Plan refinable reimportable | — |

---

## 8. Guía operativa y soluciones no obvias

### 8.1 Recomendaciones directas

1. **Decide el sustrato *antes* de explorar.** El error de coste más alto es empezar a leer archivos en local (consumiendo contexto) para una tarea que era claramente Ultraplan. Evalúa la señal P0 en la primera respuesta.
2. **Trata "blast radius incierto" como gatillo dominante.** Aunque parezca una tarea de 4 archivos, si no puedes acotar el radio de impacto, escala a Ultraplan: los 3 agentes de exploración existen precisamente para *reducir* esa incertidumbre.
3. **No arranques Ultraplan con Remote Control activo.** Verifica el estado de `claude.ai/code` primero; la exclusión mutua es silenciosa y bloqueante.

### 8.2 Soluciones que podrías no haber considerado

- **Patrón híbrido "local→cloud→local":** usa el tercer disparador de Ultraplan ("refinar plan local") como flujo *deliberado*: redacta un `plan.md` rápido en Plan Mode local para fijar tu intención, luego escálalo a Ultraplan para que los 3 agentes lo estresen y completen casos límite, y reimporta. Combina la baja latencia local con la profundidad cloud.
- **Offload como estrategia anti-OOM, no solo anti-contexto:** la doctrina del host (Windows + bridge MSYS2 frágil, hasta ~39 procesos node huérfanos por iteración) hace de Ultraplan no solo un alivio de tokens sino un **aislamiento de la planificación pesada fuera del host frágil**. La exploración de gran escala en CCR no toca el transporte local que tantos cuelgues ha producido.
- **El scratchpad como artefacto auditable:** dado que vive en ruta determinista (`/tmp/claude-{uid}/{cwd}/{sessionId}/scratchpad/`), los hallazgos cross-worker son inspeccionables post-hoc —útil para reconstruir *por qué* un plan tomó cierta forma, alineado con el estándar de evidencia persistida del proyecto.
- **Disparador léxico como riesgo:** que la **palabra "ultraplan" en cualquier prompt** dispare el sustrato cloud implica un *side-effect* léxico: mencionar "ultraplan" en prosa explicativa puede activarlo involuntariamente. Trátalo como token con efecto, no como término neutro.

---

## 9. Caveats y niveles de confianza

| Afirmación | Confianza |
|---|---|
| Plan Mode V1: máquina de estados, `toolPermissionContext`, activación, `plan.md` | **Alta** (comportamiento observado) |
| Ultraplan: CCR/Opus 4.6, 30 min, disparadores, requisitos, tiers, scratchpad, exclusión con Remote Control | **Alta** (research preview documentado) |
| Heurístico de selección P0 (3–10 vs 10+, cross-module, etc.) | **Media-Alta** (heurístico documentado) |
| Plan Mode V2: 5 fases, feature flags, variantes `trim/cut/cap`, `UltraThink` adaptive/enabled/disabled | **Baja — SIN CONFIRMAR (CCLeaks)** |

### Vacíos de información (no resueltos por la investigación)

1. **Semántica exacta de `trim/cut/cap`** —se infiere que son niveles de poda de plan, no confirmado.
2. **Comportamiento de `UltraThink adaptive`** —no se documenta el criterio de adaptación.
3. **Latencia/coste de la reimportación** Ultraplan→local —no cuantificado.
4. **Qué ocurre al expirar los 30 min** read-only de Ultraplan sin plan terminado —no documentado.

---

## 10. Conclusión

La directiva `MODO: ULTRA PLAN MODE → EXECUTION MODE (el P0 de señal decide)` codifica un principio operativo limpio: **la planificación es una decisión de enrutamiento antes que una de contenido.** La señal P0 —dominada por el *blast radius* y el conteo de archivos/módulos— selecciona entre un sustrato local de baja latencia (Plan Mode, 3–10 archivos, read-only, `plan.md` → aprobación → ejecución) y un sustrato cloud de gran profundidad (Ultraplan, 10+ archivos / cross-module / incierto, Opus 4.6 en CCR, hasta 3 agentes coordinados por scratchpad). Ambos confluyen en el **mismo gate de aprobación humana** antes de cruzar a Execution Mode, donde —si Plan Mode V2 se materializa— Verification y Review cerrarían el ciclo con evidencia.

El valor práctico está en internalizar la naturaleza **cortocircuitante** de la señal P0: el primer gatillo crítico decide, y decidir el sustrato *antes* de leer un solo archivo es la jugada que ahorra contexto, cómputo y —en este host Windows— estabilidad del propio transporte.

## Sources

- <https://deepwiki.com/fbin87/claude-code/3.5-plan-mode-and-workflow-control-tools>
- <https://devops.com/claude-codes-ultraplan-bridges-the-gap-between-planning-and-execution/>
- <https://aiskill.market/blog/ultraplan-plan-mode-v2-skills-in-the-planning-loop>
- <https://www.anthropiccertifications.com/learn/claude-code-workflows/plan-mode-vs-direct>
- <https://aiproductivity.ai/guides/claude-code-ultraplan-planning-mode/>

## Run metadata

- **Prompt:** MODO: ULTRA PLAN MODE → EXECUTION MODE (el P0 de señal decide)
- **Depth / breadth:** 2 / 3
- **Queries used:** 3 (budget 30)
- **Layers fired:**
  - search: ddg
  - markdown: trafilatura
  - llm: claude.exe
- **Priority class:** win32:IDLE_PRIORITY_CLASS
- **Lock:** acquired
- **Duration:** 414.4 s
- **Errors during run:** 3
- **Started at:** 2026-06-29T20:10:40Z
- **Module version:** deep_research 0.1.0

<details>
<summary>Error log</summary>

- `fetch_page 'https://sangampandey.info/blog/ultraplan-claude-code-plannin...': page-fetch: https://sangampandey.info/blog/ultraplan-claude-code-planning: HTTP Error 402: Payment Required`
- `extract_learnings: claude.exe: subprocess failed: Command '['C:\\Users\\User\\.local\\bin\\claude.exe', '-p', '--disable-slash-commands', '--disallowed-tools', '*', '--append-system-prompt', "You are an expert researcher. Today is 2026-06-29. Follow these instructions when responding:\n - You may be asked to research subjects that is after your knowledge cutoff, assume the user is right when presented with news.\n - The user is a highly experienced analyst, no need to simplify it, be as detailed as possible and make sure your response is correct.\n - Be highly organized.\n - Suggest solutions that I didn't think about.\n - Be proactive and anticipate my needs.\n - Treat me as an expert in all subject matter.\n - Mistakes erode my trust, so be accurate and thorough.\n - Provide detailed explanations, I'm comfortable with lots of detail.\n - Value good arguments over authorities, the source is irrelevant.\n - Consider new technologies and contrarian ideas, not just the conventional wisdom.\n - You may use high levels of speculation or prediction, just flag it for me."]' timed out after 120 seconds; anthropic-sdk: ANTHROPIC_API_KEY not set`
- `web_search 'P0 signal verdict ROJO macroform antipro...': ddg: 0 hits parsed (possible block or empty SERP); brave: BRAVE_API_KEY not set; apify: APIFY_TOKEN / APIFU_API_KEY not set`

</details>
