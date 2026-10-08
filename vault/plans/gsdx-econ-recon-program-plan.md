---
status: APPROVED (Owner "y", 2026-10-08, pane 530d9700) -- all four items of section 11: program T1=8M + tranche ladder to 100M; cost-collapse D-C pre-answered (continue past E4b inside its 69.8M cap); full WSR out of scope; reap the two HALTED-but-live EDD workers on GEX44 after verifying no uncommitted work
date: 2026-10-08
program: gsdx-factory
covers: [cognitive-economics-baseline, proof-of-non-work, boundary-admission, context-image, proof-reuse, gsdx-reconstruction-factory, kme-l, ksr-factorization, kme-benchmark, cbr-reconstruction-birth, construction-return]
depends-on: [cost-collapse (vault/plans/cost-collapse-convergence-plan.md on cost-collapse/main), ctx-rent]
supersedes: pre-arm budget of 2026-10-08 (70M / 150M / 320M)
---

# Programa gsdx-factory — A: elevación de la economía cognitiva · B: Reconstruction Factory recompilada

## 1. Realidad verificada (2026-10-08 ~22:30Z)

| Hecho | Valor | Fuente |
|---|---|---|
| m-c474d0bfc3e6 (RUNNING, GEX44) | misión **ql-quickie (QuickLease)**, worktree w2, dueño 3953e9f0 vivo. No es PP; no hay conflicto | `gsd_mission status` + transcript en `-home-kobii-missions-ql-quickie--claude-worktrees-w2` |
| GEX44 | 20 núcleos, carga 1,7; 52 GB RAM libre; 1,1 TB disco | `nproc/free/df/uptime` |
| Workers zombie en GEX44 | m-5ddc61864481 y m-0729ac737bec en estado HALTED, pero con procesos `--resume` vivos | `pgrep` |
| Goal cost-collapse | 57,1M usados de 69,8M (+4,2M en ~1 h: activo) | `mission_spend goal-status` |
| Goal ctx-rent-s2 | 3,11M de 3,0M (sobrepasado) | ídem |
| Impuesto del plano de control en cost-collapse | **49% medido** (coordinadores 27,97M de 57,2M) | plan de convergencia de cost-collapse |
| Desviación de previsión de los workers | +40%, por número de llamadas (el coste por llamada cuadra ±7%) | ídem |
| Coste mínimo por llamada según tipo de proceso | worker de nivel superior 110.835 · **slim-t2 13.507 · slim-t1 8.848** · pane del portátil 124.493 · clone de GEX44 81.492 | `route-floors.json`, `recent_floor` |
| Llamadas por transición de estado verificada | ~12–15 (estimado) | plan de convergencia de cost-collapse |
| Peso del coste mínimo en un worker | ~67% del contexto | ídem |
| EDD fase 1 compilada | 3,31M según memoria, 5,76M según el brief. **Discrepancia sin resolver**; se usa 5,76M | — |
| Fragmentación | ~30 worktrees `pp-*`; cost-collapse va 36 commits por delante del árbol vivo. `gsd_dossier`, `route_admission`, EAC y el admission dependiente **solo existen en rama** | `git rev-list` |
| Escaneo de capacidades en el árbol vivo | Proof of Non-Work 0 · ContextImage 0 · proof reuse 0 · Mission IR 0 · physical-calls 0 · control-plane-tax 0 · rotación de epoch 13 ficheros · CBR (tower families) vivo | `capscan.py` |
| KME-L | 102 sesiones / 34.871 llamadas; relecturas <0,06%, reintentos <0,01%; `late_rollover` ≤27% (techo, no ahorro). El escaneo de 568→102 sesiones es CPU/disco | `L-KME-L-2026-10-05.md` |
| Reconstrucción en GEX44 | `~/ksr`, `~/kme-{corpus,l-corpus,refs,build,runtime}`, `recon_tools`, `recon_work/dtk_*`, `_gsdx_recon` (milestone v1 cerrado el 2026-09-21) | `ls` |

## 2. Matriz de dueños

| Sistema | Disposición |
|---|---|
| cost-collapse (EAC, veredicto WATCHED, admission dependiente, successor por receipt, transacción de prueba, autopsia de llamadas, impuesto del coordinador, aterrizaje E4b) | **DEPENDENCY.** No se duplica; este programa lo consume |
| ctx-rent / CVM (`parent-context-epoch-rotation`, capsule-v2, rollover, `mission_capsule`) | DEPENDENCY + REUSE |
| incremental-cognition (`kme_replay rank`, pilares, materialidad 3%) | REUSE como minero de oportunidades |
| autonomous-optimization (m-75d9c9944f13, HALTED) | REUSE de sus salidas; **SUPERSEDED** como misión |
| `modules/gsd_x`, `_gsdx_recon`, `recon_tools`, `~/ksr`, KME | EXTEND |
| CBR (`modules/tower`: baselines de familia que ya se inyectan vivas en cada prompt) | EXTEND con la familia `reconstruction` |
| UCR-CIF / Construction Return (`tower/capsule`, rama `ucr-cif/construction`) | EXTEND; estado de aterrizaje UNKNOWN, se resuelve en A-G1 |
| Capability Runtime, Graphify, `mission_spend` (goal/admission), lifecycle (`ce-lifecycle*`) | REUSE |
| Proof of Non-Work, ContextImage, reutilización de pruebas por fingerprint | **No existen.** EXTEND `gsd_dossier` y la transacción de prueba de E3C2; no se crea un sistema nuevo |

## 3. Por qué los 150M todavía contenían impuesto eliminable

1. **El bloque de coordinación (E=18M) estaba infravalorado.** cost-collapse midió un 49% de impuesto de control. Con la gramática antigua, el coste real de los 150M habría superado esa cifra.
2. **Cada paquete se presupuestó como worker de nivel superior** (~111K mínimos por llamada). Status, prueba, receipt y edición mecánica pueden ir en slim-t2 (13,5K), unas 8 veces menos por llamada.
3. **La verificación (D=18M) contaba cognición para vigilar pruebas deterministas**, además de un ritual de tres red teams con Opus.
4. **Los bloques B5 y A del original se solapan** con el compilador de misión de la Misión A (es el mismo código).
5. **WS0 ya está hecho en su mayor parte** con este escaneo, y D2A es una herramienta sin modelo.

## 4. Parte A: elevación del baseline (solo lo que la Misión B necesita)

**A-DEP: cadena de cost-collapse** (E4a → E3C1 → E3C2 → E4b) con su propio goal y límite. Aporta: veredicto único, EAC vivo, admission dependiente con datos reales, **successor arrancado por receipt (sin padre)**, transacción de prueba, autopsia de llamadas por categoría, impuesto del coordinador, call compression y **aterrizaje en el árbol vivo**. Su plan para por decisión del Owner tras E4b (D-C): se pide responderla aquí (ver §11).

**Huecos que este programa sí construye** (todos EXTEND):

| Unidad | Qué hace | Tier | Previsión |
|---|---|---|---|
| A-G1 | **Proof of Non-Work / evaluación parcial.** Un pase sin modelo en `gsd_dossier` que dispone cada obligación del paquete (NO_WORK / ALREADY_SATISFIED / REUSE / MERGE / DETERMINISTIC / *_COGNITION / UNKNOWN). Compara contra commits, receipts, ledger de goals, registro de liveness y `capscan`. Una obligación sin disposición no se arma (fail closed) | Sonnet top | 1,5M |
| A-G2 | **Reutilización de pruebas.** El receipt de prueba de E3C2 lleva un fingerprint de dependencias (sha de entradas, toolchain, comando). Si el fingerprint no cambia, se reutiliza; si cambia, se ejecuta solo el cierre afectado | slim-t2 | 1,2M |
| A-G3 | **ContextImage = dossier + tier.** Una regla de rutado Work Class → slim-t1/slim-t2/top dentro de `route_admission`, y una **frontera de admission del modelo**: un paquete sin obligación semántica abierta no lanza modelo | slim-t2 | 0,8M |
| A-G4 | **Canarios A1–A10 consolidados.** Se reutilizan los de la cadena (A5, A7, A8, A9, A10) y se añaden A1, A2, A3 y A6 en una sola unidad de prueba | slim-t2 | 1,5M |
| A-G5 | **Ratchet CBR.** Familia tower `software_construction`/`reconstruction` B1: los pasos 1–3 pasan a ser regla de baseline inyectada; promoción a los dos installs (portátil y GEX44) | Sonnet top | 1,0M |
| Coordinación A | — | — | ≤0,5M |

**Total de la Parte A: unos 6,5M** (más el resto de cost-collapse dentro de su propio goal: ≤12,7M, que se reporta aparte y nunca se oculta).

**Gate mínimo de la Parte A:** A-DEP ha aterrizado en el árbol vivo (E4b), A-G1 a A-G4 están en verde por los dos polos, y el canario A5 (handoff sin padre) ha lanzado una unidad desde el sweep vivo sin ninguna llamada de coordinación. **Moratoria:** cualquier mejora de A que no tenga un consumidor en B queda congelada.

## 5. Parte B: grafo de trabajo recompilado (cada obligación original con su disposición)

La lista es provisional: A-G1 la vuelve a disponer de forma determinista antes de armar nada.

| Obligación original | Disposición | Previsión |
|---|---|---|
| WS0: realidad, D2A, iteración | ALREADY_SATISFIED en su mayor parte; `/d2a-family` = DETERMINISTIC | 0,3M |
| A1: candidatos de optimización | REUSE de `kme_replay rank` + salidas de autonomous-optimization; EXTEND con registro y precio | 1,5M |
| A2: KME-L | **Corregido:** optimización de CPU/disco (índice incremental de selección de sesiones), DETERMINISTIC. Ahorro de tokens = NO, porque la medida es <0,1% | 1,0M |
| A3: segundo patrón + rechazo de ROI negativo | REUSE: el 49% de impuesto de control es el segundo patrón; el rollover a 200k (−$29 neto) y relecturas <3% son el rechazo. Falta formalizarlo como disposición de candidato | 1,0M |
| A4: champion/challenger | ALREADY_SATISFIED (flip D3 de `route_admission`); falta medir el dividendo realizado | 0,5M |
| Descubrir un candidato que el prompt no nombre | CHEAP_COGNITION sobre la autopsia de llamadas de E3C2 | 0,5M |
| B1: inventario de reconstrucción | DETERMINISTIC (manifiestos en GEX44) | 0,3M |
| B2: factorización KSR por población | DETERMINISTIC en CPU de GEX44 (hash de instrucciones normalizadas, firmas SDK, homología con WSR) + STRONG para diseñar la herramienta. **Estado de las herramientas KSR: UNKNOWN** | 7,5M |
| B3: vía rápida (clasificador de mismatch del compilador) | STRONG | 5,0M |
| B4: benchmark de reconstrucción KME (refs reales + holdout sellado) | STRONG | 6,0M |
| B5: pases del compilador de misión | **MERGE** con A-G1; solo queda la parte específica de reconstrucción | 1,0M |
| C1–C3: CBR birth sin omisión, construction return, retiro | EXTEND tower; la herencia en consumidor fresco se fusiona con D | 2,5M |
| D: verificación | Transacción de prueba determinista; **1** red team con Opus dirigido (no 3); `mutation_drill` DETERMINISTIC; worker fresco + escalado 100x sintético | 6,0M |
| E: coordinación | Successor por receipt; un pane fresco de ≤5 llamadas por ola, ~6 olas | 3,5M |
| F: UKDL / vault | Extracción automática de receipts + una pasada barata | 1,25M |
| Meta-análisis y cierre | — | 1,0M |
| Full WSR (~34k funciones) | **Fuera de alcance** (DEFERRED_EXTERNAL, decisión registrada) | — |

**Total de la Parte B: unos 38,9M.**

## 6. Previsión (processed tokens, deduplicados por `message.id`)

| Banda | Programa (A + B) | Base |
|---|---|---|
| Cota inferior | **~40M** | grafo de §4 + §5 sin desviación |
| Completado verificado esperado | **~60–65M** | +40% de desviación medida en llamadas aplicada a los workers |
| Envolvente de seguridad (autoridad operativa máxima) | **100M** | |
| Techo catastrófico (airbag, no es autoridad) | 140M | |

Aparte y siempre reportado: lo que queda de cost-collapse (≤12,7M).

- **¿Es defendible 70–90M?** Sí, con margen: el esperado queda por debajo incluso con el +40%.
- **¿Es plausible 40–60M?** Sí, pero prematuro. Depende de dos cosas con n≤2: la calidad de los slim workers en trabajo de construcción y la extinción del coordinador probada en vivo. Se confirma de forma adversarial antes de ratchetear defaults agresivos.
- **Llamadas:** de ~1.070 a ~700 físicas, de las cuales unas 400 serían slim (~25K de media) y unas 270 top-level. **La palanca principal no es el número de llamadas sino el coste mínimo por llamada**, más la desaparición del coordinador.
- **GEX44:** su coste mínimo es un 35% menor que el del portátil (81K frente a 124K). B2–B4 corren allí porque los datos (KSR, KME) ya están allí. Las unidades A-G se quedan en el portátil (D-B de cost-collapse; el árbol vivo está aquí).

## 7. Autoridad del programa

- Goal único `gsdx-factory`. Al aprobar se declara **solo la tranche T1 = Parte A (8M)**.
- T2 (recompilación de B + oleada B1–B2) se admite con los **receipts reales de T1** (admission dependiente), y así sucesivamente.
- La autoridad acumulada nunca pasa de 100M sin **una** petición acotada.
- Cada unidad: lease + reserva de checkpoint/prueba (~4 llamadas de cierre protegidas).
- Tripwires sin esperar al tope: unidad >1,25× EAC → CHECKPOINT; gasto sin progreso → trip; coordinador >5 llamadas o >200K → rotar; coste por obligación comparable que no baje entre olas → parar el drenaje y diagnosticar.

## 8. Cómo se demuestra que el programa se abarata mientras corre

Después de cada ola: obligaciones planeadas, extinguidas, deterministas, de modelo y frontier; tokens; llamadas físicas; llamadas por transición; impuesto de control (ledger del goal menos workers); reutilización de pruebas; CAPEX/OPEX. **Criterio:** las Work Classes comparables bajan de coste. Si la curva sale plana: parar el drenaje, investigar, arreglar la máquina y volver a drenar.

## 9. Canarios, CI y Production Reality

- Los canarios A1–A10 y B1–B8 del brief se mapean a A-G4 y a las olas de B.
- **Cognitive CI:** ningún paquete con `supervise --actions-only`; ninguna obligación sin disposición; gates V-* por los dos polos más una mutación.
- **Production Reality:** una capacidad solo cuenta cuando está en el árbol vivo **y** en el install de GEX44, verificado por ancestría de hash. Lo que solo existe en rama = NO VIVO.
- **Rollback/deopt:** tag de rollback por cada aterrizaje; kill switch de la gramática antigua conservado; un veredicto UNKNOWN = no lanzable.

## 10. Conocimiento

Fallos ya detectados en este escaneo, para sembrar en KV/UKDL en la primera ola:

- **Trap:** capacidades solo en rama tratadas como baseline (36 commits por delante).
- **Trap:** workers HALTED con proceso vivo (impuesto de espera en caliente).
- **Trap:** discrepancia EDD 3,31M frente a 5,76M (cifra sin fuente única).
- **Process Rule:** el impuesto del coordinador se presupuesta de forma explícita, nunca a cero.

Los candidatos a Hard Rule del brief se deduplican contra UKDL antes de escribirse.

## 11. Una aprobación cubre

1. Este programa, con T1 = 8M y la escalera de tranches hasta 100M.
2. **D-C de cost-collapse:** que siga tras E4b dentro de su límite actual de 69,8M, sin parar de nuevo.
3. Fuera de alcance confirmado: full WSR.
4. Limpiar los dos workers HALTED vivos de EDD en GEX44 (m-5ddc61864481, m-0729ac737bec) tras verificar que no tienen trabajo sin commitear.
