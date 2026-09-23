---
title: Torre Universal — rebanada vertical del Constitutive Baseline Ratchet sobre PERSISTENT_STATE
date: 2026-09-23
revised: 2026-09-23 (R1 — reconciliación contra realidad medida; ver §0.bis)
status: DESIGN — aprobado por el Owner (7 secciones), RECONCILIADO contra dueños ejecutables
tier: T3
covers:
  - torre-universal
  - ucr-cif
  - constitutive-baseline-ratchet
  - resident-institutional-kernel
  - mission-baseline-capsule
  - persistent-state-family
  - baseline-consumption-telemetry
  - baseline-tower-lift
  - marginal-institutional-lift
  - project-mission-genome
---

# Torre Universal — rebanada vertical sobre la familia PERSISTENT_STATE

## 0. Qué pidió el Owner, literalmente

> «que por ejemplo, si yo avanzo con QuickLease, la próxima vez que yo pida algo en
> InfinityOps, se haga con más ingeniería, más cosas tenidas en cuenta, más completitud, sin
> necesidad de que yo pida cada cosa»

En el dataset fuente eso tiene un nombre propio y **no** es el flywheel universal: es el
**Constitutive Baseline Ratchet**. Su granularidad no es «universal», es **familia de sistema**.
QuickLease e InfinityOps no comparten dominio; sí comparten familias — CRUD con estado
persistente · superficie web con efectos · integración con servicio externo · migración de
esquema. La herencia viaja por la familia, no por el proyecto.

La fuente enuncia esa misma petición como **Baseline Lift global** (B 90.556–90.566):
*«InfinityOps lo paga una vez. ORCA X lo hereda. KobiiCraft lo hereda. CostaLuz lo hereda. El
próximo software que todavía no existe lo hereda.»* No es interpretación de la sesión: es el
mismo mecanismo, nombrado por el corpus.

## 0.bis Reconciliación R1 — qué cambió y por qué

Este diseño se aprobó antes de que se midieran los dueños ejecutables del estate y antes de que
nadie leyera la mitad del corpus que define la Torre. **Tres de sus premisas estaban muertas.**
Revisarlo no es retroceso: es el trinquete funcionando. Cada fila cita la evidencia.

| § | clasificación | qué cambió |
|---|---|---|
| 0 | **CORREGIDO** | la petición del Owner ahora cita su enunciado canónico (B 90.556) |
| 1 | **CORREGIDO** | cobertura re-anclada; el sufijo dejó de ser opaco en lo que toca a la Torre |
| 2 | UNCHANGED | decisiones del brainstorming, intactas |
| 3 | **REEMPLAZADO POR DUEÑO EXISTENTE** | el «Baseline & Policy Plane» **no es NUEVO** |
| 4 | UNCHANGED | `PERSISTENT_STATE-B<n>` sigue siendo la unidad |
| 5 | **CORREGIDO** | el gate A/B/C/D se ancla en la aritmética canónica del Lift |
| 6 | **CORREGIDO** | el Resident Kernel no está ausente: está **disperso** |
| 7 | **CORREGIDO** | la cápsula **extiende** al dueño vivo; estados explícitos obligatorios |
| 8 | **CORREGIDO** | CRR/RFR exigen **O0 antes** del tratamiento |
| 9 | **CORREGIDO** | entran Tower Score, Hidden Invention y KSEIP al backlog |
| 10 | UNCHANGED | los riesgos declarados siguen vigentes |
| 11 | **CORREGIDO** | done-gate ampliado con G-1/G-3/G-5/G-7 |
| **12** | **NUEVO** | semántica canónica de la Torre, recuperada del corpus |
| **13** | **ABIERTO** | preguntas de evidencia que este diseño NO puede cerrar todavía |

Evidencia: `vault/audits/ucr_cif/04_SOURCE_RECONCILIATION.md` ·
`05_PHASE4_PLAN_AUDIT.md` · `06_NOVELTY_GATE_TRIGGER.md` · `07_Q4_EXISTING_OWNER.md` ·
`08_TOWER_SEMANTIC_RECOVERED.md` · `vault/knowledge_base/ucr_cif/TORRE_UNIVERSAL_HANDOFF.md`.

## 1. Procedencia y qué NO se afirma

Fuente canónica: `C:\Users\User\Downloads\Dataset Claude Power Pack Universal Construction
Ratchet & Compounding Intelligence Fabric 1 (1).txt` — 3.086.894 bytes, **167.842 líneas
físicas**, 81.754 no vacías, sha256 `a082a5714e616630…4195b`.

**Medición, no estimación:** el tokenizador del harness devolvió 62.249 tokens para 9.000
líneas ⇒ ≈1,16 M tokens frente a una ventana de 1 M. El fichero no cabe entero.

**Cobertura acumulada, con su denominador declarado:**

| pasada | rango | denominador |
|---|---|---|
| Fase 1 (inventario) | B 1–75.350 | **46,4 %** de las líneas no vacías (37.947/81.754) |
| lectura 2026-09-23 | B 1–40.200 | subconjunto de la anterior |
| **R1 (esta revisión)** | **76.160–76.250 · 89.810–90.700 · 92.060–92.140 · 102.270–102.300** | ~1.100 líneas físicas, dirigidas |

`04_SOURCE_RECONCILIATION.md` probó que el export de 75.350 líneas es **prefijo byte a byte
del canónico al 100,0000 %**: son el mismo fichero, extendido. Por tanto 1.394 conceptos, 336
leyes y 71 sistemas top-level son **SUELOS**, no poblaciones. «28 sistemas espina» no es la
población.

**Lo que R1 sí cerró:** la Torre estaba definida en el sufijo, y ahora está leída (§12).
**Lo que sigue sin leerse:** el resto del sufijo. Este diseño no afirma nada sobre él. Si un
mecanismo descrito allí contradice lo de abajo, **gana el dataset** y este spec se corrige otra
vez.

Contaminación conocida: B 60.381–63.920 es documentación de terceros (Codex/PDF/DOCX) pegada al
fichero, no material del Owner. Dos instrumentos independientes coinciden en ese rango.

## 2. Decisiones del Owner tomadas en el brainstorming

| Pregunta | Respuesta |
|---|---|
| Primera familia de sistema | **Estado persistente / CRUD** (`PERSISTENT_STATE`) |
| Alcance de la captura | **Resident Kernel mínimo, host-level** |
| Enfoque | **A — rebanada vertical sobre UNA familia** |
| Fuera de alcance | **al backlog**, no descartado |
| Cobertura de corpus | **forma A — D2A-gated** |
| Tower Score escalar | **fuera de alcance** |

## 3. Un solo sustrato, no diez fabrics — y cuatro de los cinco owners YA EXISTEN

El §79 del propio dataset prohíbe construir los diez fabrics como silos con sus propios grafos,
registros y detectores. La estancia ya pagó esa factura: 156 módulos importaban limpios, pasaban
sus tests y ningún hook los alcanzaba — incluido el árbitro de ACCEPTANCE de recovery, que nunca
juzgó una recuperación real. De ahí la Liveness Standard, y de ahí que el primer artefacto tenga
que ser un **bucle cerrado con telemetría de consumo**, nunca un registro.

**CORRECCIÓN R1 — la tabla original declaraba NUEVO lo que ya tiene dueño ejecutable:**

| Owner | Qué guarda | Estado R0 | **Estado R1 — medido** |
|---|---|---|---|
| Capability Baseline Graph | familias, instancias, capabilities, autoridad, ciclo de vida | NUEVO | **D2A PENDIENTE** — renombrado desde «Institutional System Graph» al término del corpus (B 92.075). No se crea sin barrido por mecanismo |
| Evidence & Knowledge Plane | Vault + UKDL + confianza + linaje | EXISTE | **EXISTE** |
| Evaluation Plane | tests, adversarios, mutaciones, contrafactuales | EXISTE | **EXISTE** |
| Baseline & Policy Plane | compilador de baseline y aplicabilidad | ~~NUEVO~~ | **EXISTE — `modules/capability_runtime/applicability.py`.** **Seis** puertas deterministas antes de cualquier score (`:120` `:138` `:146` `:151` `:158` `:164`), `NOT_APPLICABLE`, anti-triggers, activación graduada, `evaluate_all` fail-open (`:226`). **El delta real es sólo el estado persistido** |
| Event Stream | eventos de construcción, fallos, intervenciones | PARCIAL | **PARCIAL** (hooks) |

**`NO CONSTRUIR UN SEGUNDO UBC` es ahora una restricción del diseño, no una recomendación.**

Los «fabrics» (UFIA, IFC, USIFB, RCFC, UDFLL…) siguen siendo **modos de análisis** sobre esos
owners. Señal de fallo estructural: si un fabric pide su propia base de datos, se está
convirtiendo en otro silo.

## 4. La unidad: `PERSISTENT_STATE-B<n>`

No existe un baseline global. Existe una **generación versionada por familia**, con un conjunto
constitutivo explícito, y cada entrada nace con su evidencia o no nace.

`B0` **no se inventa**: se backfillea de lo que QuickLease ya demuestre en producción.

Candidatas de la familia, según el dataset (cada una entra sólo si pasa §5):

- identidad de esquema y versión declaradas
- escritura atómica (no hay estado medio observable)
- **supervivencia a reinicio verificada** — no inferida de que el fichero exista
- contención de corrupción: un campo malo no envenena el agregado
- contrato de migración con forward **y** rollback
- `UNKNOWN ≠ ZERO` en lecturas vacías o ausentes
- clave de caché que represente **todas** las dimensiones semánticas de lo cacheado
- autoridad declarada cuando hay más de una representación del mismo hecho

## 5. El gate que convierte un avance en baseline

Cuatro clasificaciones; **sólo C y D ascienden**:

- **A — incidental.** Resolvió un caso. No se generaliza.
- **B — específica del producto.** Correcta aquí, sin significado fuera.
- **C — mejora repetidamente sistemas del mismo tipo.**
- **D — constitutiva.** Construir otra instancia de la familia sin ella sería, objetivamente, una
  regresión de completitud.

La prueba es **la pregunta contrafactual**, barata y falsable:

> ¿Consideraríamos **incompleta** una instancia nueva de esta familia que no tuviera esto?

Sí ⇒ InfinityOps ya no empieza sin ello. No ⇒ queda registrado como B, con su razón, y no
contamina el baseline. Un A o un B registrados son resultado válido del gate, no un fracaso.

**ANCLAJE R1 — el gate A/B/C/D es la forma cualitativa de la aritmética canónica** (B 76.176–
76.223, §12.2): A y B son exactamente los sumandos que el corpus **descuenta** antes de subir la
Torre (específico de producto, trade-offs no transferibles); C y D son el **Marginal
Institutional Lift**. No son dos modelos: son el mismo, uno con etiquetas y otro con aritmética.

Cada promoción registra: evidencia de origen (proyecto, incidente, **commit causal** — B 88.781
exige que un Lift apunte a commits causales), clasificación, respuesta contrafactual, y el
**Baseline Propagation Set** — IMMEDIATE · RATCHET-ON-TOUCH · OPTIONAL MIGRATION.

## 6. Resident Institutional Kernel — captura host-level

**CORRECCIÓN R1: el kernel no está ausente, está DISPERSO.** Medido: 4.393 hits en 483
ficheros; `hooks/` y `tools/` ya cargan el mecanismo. Lo que falta no es la capacidad sino un
**dueño**. Por tanto esto es `EXTEND/CONNECT`, no `CREATE`, y HR-NOVELTY-001 aplica antes de
declarar lo contrario.

Pequeño por contrato. **No carga CPP.** Garantiza seis cosas en cualquier repo, esté CPP activo o
no: *capture · identity · provenance · baseline lookup · critical enforcement · writeback*
(`UC-14: UNIVERSAL CAPTURE IS HOST-LEVEL`).

Captura **DISCOVERY EVENTS**, no sólo bugs: fallos de test, excepciones, migraciones fallidas,
fixes sin efecto, hipótesis falsadas, workarounds, **correcciones del Owner** y sorpresas
positivas. Niveles D0–D7: se captura el 100%, se institucionaliza selectivamente. Meter cada error
de compilación en UKDL destruye la señal; ésa es la regla, no una preferencia.

**HR-001 se respeta sin excepción.** El registro del kernel vive bajo `~/.claude`, que es fuente
de extensión: el parche se deja **preparado y verificado para el Owner**, nunca aplicado por el
agente, y nunca se rodea. El entregable incluye:

- el parche de registro, listo para pegar
- un **health check** que diga si el kernel está registrado y vivo
- un **self-test** que conduzca la rama roja (kernel desregistrado ⇒ captura ausente ⇒ gate rojo)
- **detección de instalación rancia**: un kernel registrado con una versión que ya no existe debe
  reportarse como AUSENTE, no como sano

## 7. La cápsula que ve InfinityOps

**CORRECCIÓN R1 (G-1, CRITICAL) — la cápsula NO tiene inyector propio.** El borde
`prompt → MissionContext → applicability → inyección ambiente` **ya existe, está registrado y es
alcanzable**: `hooks/hook-dispatcher.js:526` → `hooks/gsd_x_tier.js` → `modules/gsd_x/tier.py:257`.
Su propio comentario de registro enuncia la reivindicación de producto de esta cápsula palabra
por palabra: *«so the posture stops depending on the operator remembering to ask for it»*.

Un inyector nuevo sería **autoridad paralela sobre un efecto vivo**, con dos escritores de la
postura de arranque y ninguna regla de precedencia. Por tanto:

> **La Mission Baseline Capsule se entrega EXTENDIENDO `modules/gsd_x/tier.py` +
> `hooks/gsd_x_tier.js`. Un efecto, un dueño.**

Contenido de la cápsula (sin cambios respecto a R0):

- baseline heredado de la familia, nombrado por su generación (`PERSISTENT_STATE-B0`…)
- capabilities activadas, **cada una con su razón**
- familias de fallo plausibles **para este diff concreto**
- contrato de evidencia por claim
- **qué NO aplica y por qué** — la parte que mantiene la cápsula pequeña

Dos reglas no negociables:

- **`APPLICABILITY PRECEDES ACTIVATION`.** No existe «se aplica el baseline universal entero».
- **`FALSE ACTIVATION IS A BUG`.** `MISSED ACTIVATION IS A BUG` es su gemela.

### 7.a Estados de la cápsula — obligatorios y distinguibles (G-3, CRITICAL)

Hoy la cadena `UserPromptSubmit` tiene una deadline viva de **3.000 ms**
(`hook-dispatcher.js:758`), `gsd_x_tier` es **advisory por diseño** (`:521-524`), y un prompt
frío medido cuesta 13.543 ms. **Los miembros no críticos se abandonan.** En consecuencia, hoy
una cápsula abandonada y una que no tenía nada que decir **son el mismo observable**, y
cualquier prueba de consumo sobre ese canal es infalsable.

El diseño exige estados con identidad propia, nunca «sin salida»:

`AVAILABLE` · `NOT_APPLICABLE` · `EMPTY_BY_EVIDENCE` · `ABANDONED_BY_DEADLINE` ·
`PRODUCER_FAILURE` · `STALE` · `UNKNOWN`

Kernel vMAX-NULL-ERROR aplica: `EMPTY ≠ TIMED OUT ≠ NOT APPLICABLE ≠ PRODUCER FAILURE`.

**IC-009 se respeta:** la reparación **no** es meter trabajo síncrono caro en `UserPromptSubmit`
ni subir la deadline como primer reflejo. La decisión de carril (precómputo persistido previo al
prompt · mínimo acotado síncrono con enriquecimiento posterior · modo degradado explícito) es la
**puerta G-3** y se decide con medición, antes de tocar O4.

### 7.b El genoma alimenta PUERTAS, no sólo el score (G-4)

`applicability.py` evalúa **seis** puertas deterministas **antes** de cualquier score.
`tier.py:251-253` deja `owners`, `prerequisites` y `held_scopes` **vacíos a propósito**: *«a hook
cannot establish them and guessing would defeat the point»*. Rellenarlos mal no degrada el
resultado: lo **invierte** — un genoma rancio o parcial **bloquea** capacidades.

**Verificado en fuente ejecutable, no en cita (R1).** La puerta 2 es literalmente
`if ctx.resolved_owners and c.owner… not in …` (`:146`): **un conjunto vacío la DESACTIVA, y uno
parcial la convierte en veto universal.** La puerta 4 se comporta igual con `held_scopes`
(`:158`). G-4 no era una hipótesis del auditor — está en el código, y es la razón exacta por la
que un campo ausente debe **omitirse** en vez de enviarse vacío.

Por defecto el genoma alimenta **score y `available_evidence`**. `held_scopes` y
`resolved_owners` exigen frescura probada. **Un campo ausente significa *no medido* (se omite),
nunca *conjunto vacío*.**

**Y la cápsula NO necesita inventar su vocabulario de estados.** La puerta 1.5 (`:126-143`) ya
distingue *dormant* de *blocked*, con la razón escrita en el módulo: *«A capability the mission
never reached for is DORMANT, not BLOCKED. The four blocking verdicts all mean "this capability
is wanted here and cannot run"»*, y con la medición que lo forzó (un typo de una línea en CLI
reportaba el instalador transaccional como `BLOCKED_BY_MISSING_EVIDENCE`). Ésa es, ya
implementada y ya falsada por un benchmark cross-domain, la distinción `NOT_APPLICABLE` ≠
`BLOCKED` del §7.a. Lo que el §7.a **añade** son los estados del *canal* —
`ABANDONED_BY_DEADLINE`, `PRODUCER_FAILURE`, `STALE` —, que son los que hoy no existen en
ninguna parte.

### 7.c Identidad del genoma (G-5)

La clave del genoma sale de `modules/repo_identity/identity.py`
(`canonical_repo` `:56` / `repo_key` `:92`, con `legacy_keys` `:97` y `ledger_paths` `:134`
— **leídos, no citados**). **No se inventa un esquema propio**: ese módulo existe porque
sluguear el cwd creaba una segunda identidad con su ledger vacío al hacer `cd` a un
subdirectorio. Aserción obligatoria: el genoma de un subdirectorio resuelve a la misma clave que
el de la raíz, y el `.git` de un worktree es un **fichero**, no un directorio — este árbol tiene
7 worktrees activos, así que el caso es real.

## 8. La prueba de que funciona

> `A LEARNING IS NOT INSTITUTIONALIZED WHEN IT IS STORED. IT IS INSTITUTIONALIZED WHEN FUTURE
> BEHAVIOR CHANGES BECAUSE OF IT.`

El done-gate no es «el registro existe». Es **telemetría de consumo**, por entrada del baseline:
ofrecida · recuperada · usada · **cambió una decisión** · previno un fallo · falsa activación ·
ignorada. Una entrada sin consumidor no está institucionalizada y se marca como tal.

**Observabilidad simétrica (obligatoria).** Los caminos de éxito ledgerean igual que los de
fallo. Origen: el daemon de auto-compact ledgereaba sus tres caminos de fallo y ninguno de sus
dos de éxito, así que sólo podía responder «nunca» — un cero que parecía hallazgo.

Dos métricas de aceptación, ambas con objetivo cero:

- **CRR — Completeness Regression Rate.** Construcciones nuevas que arrancan por debajo de la
  mejor completitud ya demostrada de su clase.
- **RFR — Rediscovered Feature Rate.** Veces que el Owner tiene que volver a pedir algo que ya fue
  constitutivo en un sistema equivalente.

**CORRECCIÓN R1 (G-7, HIGH) — las dos son TASAS SOBRE UNA POBLACIÓN.** Una sola misión no mueve
una tasa, y la misma misión no se puede correr dos veces con el mismo agente honestamente: la
segunda está contaminada por la primera. CRR/RFR aparecen en 5 ficheros del repo, todos de
diseño o auditoría: **no existe medición previa**. Por tanto **O0 no es opcional** y va **antes**
de que la cápsula exista — en cuanto el trinquete corra ya no hay forma de saber cómo era antes.

**Drill de mutación obligatorio:** se desconecta el compilador de baseline y la cápsula debe dejar
de emitirse, con el gate en rojo sobre su propia aserción. Restauración verificada por hash.

**Control positivo:** una misión que NO toca estado persistente no debe recibir cápsula de esta
familia. Sin ese control, un compilador que activa siempre pasaría todos los tests de activación.

## 9. Fuera de alcance — declarado, al backlog

IFC-RLAAS · RCFC completo · USIFB · UFIA-EBF como fabric propio · los corpus externos
(EssentialsX, LuckPerms, Fable 5, KME) · SEEIP · HIC-OAR · el resto de familias de sistema ·
el UBC completo multi-familia · la Meta-Ratchet y los Improvement Derivatives de v2.

**Añadidos en R1:** **Tower Score escalar** (decisión del Owner, y el corpus coincide — §12.3) ·
**Hidden Invention / benchmark KSEIP** · **Construction Return** y **composición/síntesis** como
implementaciones (su *descubrimiento de dueño* sí es de esta misión, §13).

Registrado en `vault/backlog/2026-09-23_torre-universal-out-of-scope.md` con razón por ítem.

**Segunda pasada (2026-09-23).** La lista de arriba está organizada por *sistema del dataset*, que
tiene un punto ciego: el propósito del Owner es un comportamiento, no un sistema. El backlog
recibió tres grupos más — precondiciones de medición (A), mecanismos que ningún fabric nombra (B)
y deuda de estate que bloquea el bucle (C). **El grupo A no es diferido**: son precondiciones de
esta misma rebanada y están en el §11.a.

## 10. Riesgos y lo que este diseño NO promete

- **No promete** que el kernel capture en repos que el Owner nunca abra con Claude Code.
- **No promete** que `B0` sea correcto a la primera. Nacerá con evidencia débil y se corregirá
  **por consumo**.
- **No promete** nada sobre el sufijo del corpus todavía sin leer (§1).
- **Riesgo principal:** que esto se convierta en el silo número once. Mitigación estructural: los
  owners del §3, cuatro de los cuales **ya existen**, y la prohibición de base de datos propia.
- **Riesgo secundario:** falsa activación. Mitigación: se mide como bug, con el control positivo.
- **Riesgo nuevo en R1:** que el genoma rancio **invierta** la aplicabilidad (§7.b). Mitigación:
  ausente ⇒ omitido, nunca conjunto vacío.

## 11. Done-gate de esta rebanada

### 11.a Precondiciones — antes de la primera promoción, no después

Sin ellas el resto del gate no se puede falsar, y la primera **caduca**.

- **P1 · A/A de CRR y RFR medido, con el método predeclarado por escrito antes de la primera
  medición contada.** Un umbral elegido después de ver los números no es un umbral.
- **P2 · Clasificador de familia con las dos ramas alcanzables sobre entradas reales** — una
  misión que debe clasificar dentro y otra que debe quedar fuera, nombradas antes de
  implementarlo.
- **P3 · Catálogo de familias descubierto de una señal estructural del estate, con suelo de
  población**: un barrido que deja de encontrar nada falla, no reporta limpio.
- **P4 · Techo de tokens de la cápsula**, y superarlo es un fallo del compilador, no una nota.
- **P5 · (R1) G-3 decidido y la cápsula con estados distinguibles** — sin esto, O4 es infalsable
  y por tanto no es prueba.
- **P6 · (R1) O0 sellada** — veredictos «sin cápsula» sobre una población reservada, registrados
  **antes** de que la cápsula exista.

### 11.b Observaciones — todas, o no está hecho

1. `PERSISTENT_STATE-B0` existe con ≥1 entrada promovida por el gate del §5, con su evidencia de
   origen real en QuickLease, su **commit causal** y su respuesta contrafactual escrita.
2. El Resident Kernel captura DISCOVERY EVENTS en un repo sin CPP, demostrado en vivo.
3. El parche de `~/.claude` está preparado, con health check, self-test y detección de instalación
   rancia. **Aplicado por el Owner, nunca por el agente** (HR-001).
4. Una misión real en InfinityOps recibe una Mission Baseline Capsule derivada de evidencia de
   QuickLease **a través del dueño existente** (`gsd_x/tier.py`), y la telemetría registra al
   menos un evento **«cambió una decisión»**.
5. El control positivo pasa: una misión sin estado persistente no recibe esta cápsula.
6. El drill de mutación va rojo al desconectar el compilador, y la restauración se verifica por
   hash.
7. `python modules/liveness/reachability.py` no nombra ningún módulo nuevo inalcanzable.
8. **(R1)** Una cápsula abandonada por deadline es **distinguible** de una vacía por evidencia,
   en el log, sin leer el código.
9. **(R1)** El genoma de un subdirectorio y el de la raíz resuelven a la **misma** `repo_key`.
10. **(R1)** Ningún dueño duplicado aparece: un solo escritor de la postura de arranque.

Nada de lo anterior es «documentado». Cada punto es una observación.

## 12. Semántica canónica de la Torre (NUEVO en R1)

Recuperada del sufijo que ninguna pasada había leído. Detalle y procedencia línea a línea:
`vault/audits/ucr_cif/08_TOWER_SEMANTIC_RECOVERED.md`.

### 12.1 La definición

> **B 102.293:** `Baseline Tower Lift = verified capability delta, deduplicated against existing
> capability state.`

`verified` (un delta no verificado no es Lift) · `capability delta` (la unidad es la capacidad,
no el commit ni el sprint) · `deduplicated` (**el anti-doble-conteo está dentro de la
definición**, no es política añadida después).

### 12.2 Project Challenge ≠ Tower Lift — la aritmética

```
Gross Feature Lift                              1.000
  − ya cubierto por el estado institucional        400   ← HERENCIA, no logro
  − específico de producto                         200   ← delta de dominio
  − trade-offs no transferibles                    100
  = Marginal Institutional Lift                    300   ← lo único que sube la Torre
```

Y sobre él: `Direct Marginal` · `Transitive` · **`Compositional`** · `Meta-Lift`. El corpus es
explícito en que **el Compositional puede superar al Direct** (B 76.203): dos features con
idéntico valor local pueden valer +50 y +1.500 institucionales «porque resuelve una primitive que
beneficiará veinte proyectos».

Los números del corpus son un ejemplo didáctico. Se adoptan **los términos y la estructura**;
ninguna magnitud se importa a ningún artefacto.

### 12.3 No hay conjunto fijo de «Lifts», y no hay escalar

El corpus contiene **al menos cuatro descomposiciones distintas** de Lift — 8 en B 90.491, 6 en
B 92.130 **sobre el mismo sujeto**, 9 en B 101.803, más la aritmética de B 76.192. Fijar el
diseño sobre «los ocho» habría elevado el ejemplo trabajado de **una** absorción a ontología de
la institución. Lo que sí se repite entre las tres listas de dominio, y por tanto es estructural:
**Direct Capability · Failure-Immunity · Skill · Metrology · Meta-Engineering**.

> **B 92.075:** «La "torre" debe ser una proyección del **Capability Baseline Graph**, no una
> métrica que podamos inflar. Lo correcto es medir primero el Marginal Institutional Lift y
> después convertirlo a Tower Height.»

La altura es **derivada y posterior**. Esto corrobora la decisión del Owner desde la fuente.

### 12.4 Universal ≠ «todas las reglas aplican a todo»

«Universal» significa **ascendencia institucional compartida**, no checklist global. La Torre se
sitúa **por encima** de los baselines constitutivos por familia y no los borra:

```
civilización de ingeniería universal
  → baseline de la familia de sistema aplicable
    → genoma de proyecto/misión
      → realidad actual del repo
        → estado de arranque de la misión
```

`APPLICABILITY PRECEDES ACTIVATION` es lo que hace que esa cadena no sea un volcado de contexto.

## 13. Preguntas de evidencia abiertas (NUEVO en R1)

Ninguna se cierra por prosa. Cada una nombra su instrumento.

| # | pregunta | estado |
|---|---|---|
| E1 | ¿Tiene dueño **Construction Return**? | `project challenge` y `construction return` dieron **0 sobre regex acotada por nombre** ⇒ **INSTRUMENT BLIND**, no ausencia. Exige barrido por mecanismo: escritores de lecciones, promoción de deltas, writeback de conocimiento, registros de capability |
| E2 | ¿Tiene dueño **composición/síntesis**? | igual: buscar el mecanismo (Opportunity Delegation, IFC, capability_runtime, knowledge graph), no el símbolo «Composition Engine» |
| E3 | ¿Cubre HR-NOVELTY-001 a su propio sujeto? | **NO hoy.** El trigger está acotado por vocabulario (`fabric`, `operating system`, `kernel`, `compendium`); la descripción funcional del Ratchet lo atraviesa entera. `applies=False` sobre el Ratchet es **UNKNOWN**. 12 de 13 preguntas siguen abiertas; Q4 → `EXTEND_EXISTING_OWNER` |
| E4 | ¿Escribe el heartbeat una clase propia para el abandono por deadline? | **NO MEDIDO.** Es la mitad de G-3 que nadie ha comprobado |
| E5 | ¿Qué hay en el resto del sufijo del corpus? | sin leer. Cualquier ausencia afirmada sobre él es inválida |

**Regla que gobierna las cinco:** `NINGUNA AFIRMACIÓN DE AUSENCIA ESTÁ COMPLETA HASTA QUE EL
INSTRUMENTO DE OBSERVACIÓN HAYA DEMOSTRADO PODER VER EL MUNDO POSITIVO.` Seis instancias del
mismo defecto se midieron en un solo día — tres en instrumentos del estate, tres propias de la
sesión de revisión.
