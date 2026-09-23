# TORRE UNIVERSAL — HANDOFF

**Escrito 2026-09-23. Actualizado 2026-09-23 (pasada R1).** Autocontenido: una sesión fría
continúa desde aquí sin que el Owner vuelva a explicar el concepto. Actualizar tras cada unidad
sellada, nunca sólo al final.

---

## 1. Identidad y estado del árbol

| | |
|---|---|
| repo | `C:\Users\User\.claude\skills\claude-power-pack` |
| rama | `feature/knowledge-acquisition` |
| **pin base de la pasada R1** | **`d2351a0`** (estado al recibir el encargo) |
| rango autoritativo R1 | **`d2351a0..HEAD`** — rango, no cuenta: el commit de este fichero cambiaría cualquier número escrito aquí |
| rango acumulado | `dea16d4..HEAD` |
| upstream | `origin/feature/knowledge-acquisition` — **verificar relación antes de empujar; no se empujó en R1** |
| último commit de contenido R1 | `260e088` (E1/E2), seguido por el commit de este handoff |
| rutas sucias | **445**, todas ajenas — **cero mission-owned sucias** |
| worktrees | **7 activos**, incluido `C:\Users\User\Apps\pp-ucr-cif` en `ucr-cif/construction` |
| host | 4 %–11 % de RAM libre durante toda la pasada |

**Consecuencia operativa:** cualquier oráculo ancho (suite completa, `tsc` global, lint de repo)
es **INCONCLUSIVE** por construcción. Commits con pathspec obligatorio, leer cabeceras de hunk
antes de commitear, y preferir **fichero NUEVO** a extender uno compartido. El contador de sucias
se movió 449 → 444 → 445 durante la pasada: hay escritores concurrentes vivos.

`RESUMPTION_FILE.md` en la raíz pertenece a **otra misión** (`/cpp-gsd-long`). **No sobrescribir.**
Este fichero es el dueño durable de la Torre; el pin de la misión de corpus sigue siendo
`UCR_CIF_RESUMPTION.md`.

## 2. Qué es esta misión

> *«que por ejemplo, si yo avanzo con QuickLease, la próxima vez que yo pida algo en InfinityOps,
> se haga con más ingeniería, más cosas tenidas en cuenta, más completitud, sin necesidad de que
> yo pida cada cosa»*

La fuente enuncia esa petición literalmente como **Baseline Lift global** (B 90.556): *«InfinityOps
lo paga una vez. ORCA X lo hereda. KobiiCraft lo hereda. CostaLuz lo hereda. El próximo software
que todavía no existe lo hereda.»*

Diseño aprobado y **reconciliado (R1)**:
`docs/superpowers/specs/2026-09-23-torre-universal-persistent-state-design.md`.

## 3. Semántica canónica — RESUELTA en R1

> **B 102.293:** `Baseline Tower Lift = verified capability delta, deduplicated against existing
> capability state.`

Y la aritmética que separa esfuerzo de ganancia (B 76.176–76.223):

```
Gross Feature Lift                          1.000
  − ya cubierto institucionalmente            400   ← HERENCIA, no logro
  − específico de producto                    200
  − trade-offs no transferibles               100
  = Marginal Institutional Lift               300   ← lo único que sube la Torre
```

Más `Direct Marginal` · `Transitive` · **`Compositional`** · `Meta-Lift`, donde el corpus dice
explícitamente que el Compositional **puede superar al Direct**.

**No hay un conjunto fijo de «ocho Lifts».** Hay ≥4 descomposiciones (8 en B 90.491, **6 en
B 92.130 sobre el mismo sujeto**, 9 en B 101.803, más la aritmética). Fijar el diseño sobre «los
ocho» habría elevado el ejemplo de UNA absorción a ontología de la institución. Estructural entre
las tres listas: **Direct Capability · Failure-Immunity · Skill · Metrology · Meta-Engineering**.

**Sin escalar, y lo dice la fuente** (B 92.075): la torre es una **proyección del Capability
Baseline Graph**; la altura se deriva del Marginal Institutional Lift, nunca al revés.

Detalle con procedencia línea a línea: `vault/audits/ucr_cif/08_TOWER_SEMANTIC_RECOVERED.md`.

## 4. Lo FALSADO — acumulado

De pasadas anteriores, todo sigue en pie:

1. El corpus canónico es el de **167.842 líneas** y contiene **estrictamente** al de 75.350
   (prefijo byte a byte, 100,0000 %). Fase 1 cubre el **46,4 %** de las líneas no vacías. 1.394
   conceptos / 336 leyes / 71 sistemas son **SUELOS**. «28 sistemas espina» no es la población.
2. **El UBC no hay que construirlo** — `modules/capability_runtime/applicability.py`.
3. **El Resident Kernel no está ausente: está DISPERSO** (4.393 hits / 483 ficheros).
4. **Q4 → `EXTEND_EXISTING_OWNER`.**
5. `continuation_transport` **no** está sin ejercitar.
6. «26 peticiones de /compact, 0 entregas» era **FALSO** — observabilidad asimétrica.

Añadido en R1:

7. **`applicability.py` tiene SEIS puertas, no cinco**, y G-4 está en el código, no era hipótesis:
   la puerta 2 es `if ctx.resolved_owners and …`, así que **un conjunto vacío la DESACTIVA y uno
   parcial la convierte en veto universal**.
8. **Construction Return y Composición SÍ tienen dueño** (§5). Las filas `NO IDENTIFICADO` eran
   ceros acotados por nombre.
9. **`gsd_x_tier`, el dueño vivo del Project Birth, se abandona en producción** entre 215 y ~408
   de 639 abandonos de su cadena.

### 4.b Falsaciones contra mí mismo, en esta pasada

Cinco, todas contra evidencia que resultó correcta, todas por medir con un instrumento más pobre
que el que ya estaba en el expediente:

- `Get-Content | Measure-Object -Line` dio **81.779** en vez de 167.842 (puntúa la línea vacía
  como cero). Estuve a una frase de reportar como falsado un handoff correcto.
- Declaré falsado el puntero `89.813` tras leer **su primera línea**. El audit citaba un **rango**
  89.813–90.636 y los Lifts están en 90.491, dentro.
- Llamé «corrección» a 44,89 % vs 46,4 %: son dos denominadores, ambos correctos.
- Un regex de agrupado capturó el **timestamp** en vez del nombre de cadena.
- Dije «NO DRILL» leyendo el árbol equivocado; el drill existe en `~/.claude/hooks/tests/`.

**La ley de la misión aplica a quien la ejecuta.**

## 5. Dueños — actualizado en R1

| concepto de la Torre | dueño en disco | estado |
|---|---|---|
| Applicability / UBC | `modules/capability_runtime/applicability.py` | **OWNED** — verificado en fuente |
| Project Birth (inyección ambiente) | `modules/gsd_x/tier.py` + `hooks/gsd_x_tier.js`, registrado en `hook-dispatcher.js:526` | **OWNED y vivo — pero su ENTREGA falla bajo carga** |
| identidad de repo | `modules/repo_identity/identity.py` (`canonical_repo:56`, `repo_key:92`) | **OWNED — usar, no reinventar** |
| gate de novedad | `modules/spec_gate/gate.py:287` | **OWNED** — trigger acotado por nombre |
| **Construction Return** | **`modules/fable_distillation/fd_07_flywheel.py`** | **`EXTEND`** |
| **composición / síntesis** | **`modules/capability_runtime/`** (`compile_stack`) | **`CONNECT`** |
| semántica canónica de Torre | — (existe en el corpus, B 102.293) | **sin dueño en disco** |

**FD-07 implementa la definición canónica cláusula por cláusula**: `classify_delta` = capability
delta; Jaccard contra depósitos previos = deduplicated; y `portability_proven` **siempre `False`,
`# always False here -- honest`** = la cláusula `verified`, retenida a propósito.

**EL DELTA REAL, y es pequeño:** Construction Return **escribe**; Project Birth **lee**; **no hay
conector**. Nadie convierte un depósito `NEW`/`STRONGER` en una entrada de baseline por familia
que `applicability.py` consuma al arrancar la siguiente misión.

Detalle: `vault/audits/ucr_cif/10_E1_E2_OWNER_DISPOSITION.md`.

## 6. G-3 — DECIDIDO en R1

815 abandonos reales de cadena en 8 días, leídos del log de producción (no drill: el host estaba
al 0,2–9,6 % y el instrumento habría consumido el recurso que mide).

- `UserPromptSubmit-chain`: **639** abandonos · `SessionStart-chain`: **69** (⇒ **no es puerto
  seguro**) · RAM libre al abandonar: mediana 8,2 %, **máximo 28,2 %** (no es sólo inanición).
- **`gsd_x_tier` nombrado en 215 de 639 (33,6 %)**, y es un **suelo**: la rama `before pool`
  skippeó 965 slots sin nombrar ninguno.

**Decisión: `A′ + C`.** El productor **no corre en ninguna cadena con deadline de latencia** y
persiste; `UserPromptSubmit` **sólo lee**; y la degradación es legible **por el consumidor**, no
sólo por `logError`. Rechazadas D, B (el coste ligante son **seis spawns**, no lógica de hook —
IC-009) y A ingenua.

Estados obligatorios: `AVAILABLE` · `NOT_APPLICABLE` · `EMPTY_BY_EVIDENCE` · `PRODUCER_FAILURE` ·
`STALE` · `UNKNOWN`. Seis mundos, seis observables ⇒ **O4 ya puede fallar**.

Detalle: `vault/audits/ucr_cif/09_G3_DECISION.md`.

## 7. Puertas — estado real tras R1

| fase | estado |
|---|---|
| **A — reconciliación del spec** | **SELLADA** (`2512bb3`, `91d551f`) |
| **B — semántica de la Torre** | **PARCIAL** — lo crítico recuperado (`955c3b4`); el resto del sufijo sin leer |
| **C — 12 preguntas HR-NOVELTY** | **NO INICIADA** |
| **D — G-3** | **SELLADA** (`60048a0`) |
| **E — O0 baseline** | **SELLADA** (`f58de7f`) — capturada **antes** de que exista cápsula, que era la única ventana |
| **F — estado persistido mínimo** | **NO INICIADA** (correctamente: E era precondición) |
| E1/E2 descubrimiento de dueño | **CERRADO** (`260e088`, `9d6e6b9`) |

Tower Score: **N/A por decisión del Owner, y el corpus coincide.** KSEIP: backlog.

### 7.a O0 — el suelo, un renglón por plano

- **P1 aplicabilidad ambiente:** 927 juicios / 4,18 días · 450 suelo · 472 informativo ·
  **50,9 % informativo** · ambos polos presentes.
- **P3 censo de juicios FD-07:** 5.074 turnos · **26.183 hallazgos** · 221 depositados
  (**0,8 %**) · **25.962 deduplicados (99,2 %)** · 0 descartados.
- **Contaminación declarada:** el suelo **no** es «sin tratamiento». Aplicabilidad ambiente y
  flywheel ya corren; el flywheel además **sólo en sesiones frontier** (`PP_FRONTIER_SESSION=1`).
- **CRR / RFR / BIR: NO capturables hoy.** Cuentan *construcciones de una familia*, y **no existe
  clasificador de familia**. Una tasa sin denominador no se reporta. Definiciones canónicas
  exactas recuperadas en B 27.573–27.611 — **dentro del 46,4 % ya inventariado**; no hacía falta
  leer el sufijo, hacía falta mirar. **BIR** (Baseline Inheritance Rate) no aparecía en ningún
  documento de esta misión.

**Corrección a §5, importante.** El ledger de depósitos marca `NEW 215/215`, lo que leído solo
diría que la cláusula `deduplicated` no disparó jamás. **Es falso.** `fd_07_flywheel.py:336-344`
hace `continue` en `DUP` y en `DISCARD`, así que el ledger registra **supervivientes, no
juicios**. En el censo real esa cláusula es **el camino más ejercitado de la estancia** (25.962).
Mismo defecto que el ledger de auto-compact **con el signo invertido**: aquél registraba sólo
fallos y sólo podía responder «nunca entregó»; éste registra sólo éxitos y sólo podía responder
«nunca dedujo».

Detalle: `vault/audits/ucr_cif/11_O0_PRETREATMENT_BASELINE.md`.

## 8. Siguientes tres acciones

1. **El clasificador de familia.** Dejó de ser una casilla del spec (§11.a P2/P3): es el
   **bloqueante único** de CRR, RFR y BIR, las tres métricas que el Owner pidió. Sonda por nombre:
   `system_family` / `family_catalog` / `classify_family` → **0 ficheros**; los triggers de
   `applicability.py` clasifican por **capacidad**, que es otro eje. Exige señal estructural del
   estate y **suelo de población** — un barrido que deja de encontrar nada falla, no reporta
   limpio.
2. **El conector FD-07 → `applicability.py`.** Es el delta real de la Torre y es pequeño: un
   depósito `NEW`/`STRONGER` debe poder convertirse en entrada de baseline por familia que
   `MissionContext` consuma. **Ojo a G-4**: alimentar `held_scopes`/`resolved_owners` con un genoma
   parcial **invierte** la aplicabilidad. Por defecto: score y `available_evidence`; campo ausente
   se **omite**, nunca se envía vacío.
3. **Las 12 preguntas de HR-NOVELTY**, por mecanismo y con control positivo. Q4 ya está respondida
   y es la que más pesa contra crear.

## 9. Decisiones del Owner ya selladas

Canónico = fichero de 167k · datasets autorizados, cobertura forma A · HR-NOVELTY-001 clasifica
pero no detiene · Tower Score escalar **fuera** · la misión Torre **absorbe** la rebanada
PERSISTENT_STATE · Hidden Invention / KSEIP al backlog · fuera de alcance al backlog, no al
descarte.

## 10. Deuda abierta, nombrada

- **`hooks/tests/` diverge**: 11 ficheros en el repo, 48 en `~/.claude/hooks/tests/`, y el repo no
  tiene `fixtures/`. `hook-dispatcher.js:540` documenta un drill que **en el repo no se puede
  ejecutar**. Qué árbol es el dueño canónico es decisión del Owner.
- **Despliegue pendiente (HR-001)**: `vault/staged/2026-09-23_deploy_deadline_abandon_names.md`
  y `vault/staged/2026-09-23_deploy_autocompact_ledger.md`. El agente no escribe bajo
  `~/.claude/hooks/`.
- **Carrera de la retirada del auto-compact**: `vault/backlog/2026-09-23_autocompact-withdrawal-race.md`.
- **Solapamiento E1∩E2** (87 ficheros) sin desambiguar.
- **`liveness/reachability.py` no se ha corrido** en esta pasada.

## 11. Instrucción de arranque

Leer §1 (árbol), §4 (falsado, **incluido 4.b**), §5 (dueños) y §7 (puertas) antes de proponer
ninguna construcción. Después ejecutar la acción 1 del §8.

**Antes de afirmar cualquier ausencia: buscar el MECANISMO, nunca el acrónimo.** Ese error ya
ocurrió **ocho veces** documentadas, cinco de ellas en la pasada que escribió este párrafo.
