# Backlog — cosecha de handoffs pendientes (2026-10-03)

Origen: Owner, sesión 70d16064: *"add absolutely everything to the backlog, including what's useful
from [lo antiguo]"*. Barrido de todo fichero `*handoff*` / `*RESUMPTION*` del repo y de
`memory/handoffs/` (fuera: copias en `.claude/worktrees/`, espejos de `_knowledge_graph/`,
`vault/token_logs/`). Cada fila cita su fuente; el texto completo y el contexto viven allí.

**Cómo se filtró.** Una fila entra si su fuente la deja abierta. Se cotejó contra `git log` desde
2026-09-26 y contra el estado actual de los ficheros; lo que ya consta hecho va a la sección final
"Cerrado al verificar", con la prueba, para que no reaparezca. Lo no re-verificado se marca
`SIN VERIFICAR` en Estado: es lo que dice la fuente, no lo observado hoy.
**Límite del instrumento:** el barrido buscó encabezados "Next / Pending / Open / Owed" y líneas
`NEXT`. Un handoff que escribe sus pendientes en otra forma no aparece aquí; `product-demo`,
`family-baselines`, `HANDOFF_W14` y el handoff kme de `.planning/` no dieron ninguna línea.

No duplica: donde la tarea ya está en `vault/plans/deferred-backlog.md` (D1–D10) o en otro fichero de
`vault/backlog/`, la fila lo referencia.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

## A. Decisiones y pasos del Owner (HR-001 o producto)

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / fuente |
|---|---|---|---|---|---|---|
| A1 | **Mover UNA regla R2 a skill (B-prime)**: cwst, tfps o ssea | 1 | S | High | ESPERA AL OWNER | R2 24/24 válido, pasa en ambos brazos (`d50cb079`). Edición en `~/.claude/` (HR-001): cuerpo → skill, puntero + backup como movimientos 1-3; luego `p3_runner.py run-jprime --set R2 --only <x>` (4 runs) antes del siguiente. Registrar veredicto por fichero en plan §14. Fuente: `vault/plans/cognitive-control-plane-RESUMPTION.md` §4 1d. |
| A2 | `gsd-x-n7` **F7: opción (a) o (b)** | 1 | S | High | ESPERA AL OWNER, SIN VERIFICAR | Bloquea el resto de N7; sin respuesta, no poner FACTS.json en ninguna raíz real de misión (desactiva en silencio toda obligación derivada de prosa). Fuente: `vault/specs/gsd-x-n7.RESUMPTION.md` L185. |
| A3 | Instalar el contrato del revisor | 1 | S | Medium | ESPERA AL OWNER | `python tools/install_reviewer_contract.py --install` (HR-001, consta ABSENT). Fuentes: `external-capability-assimilation.RESUMPTION.md`, handoffs `05c497a1`, `ea725130`. |
| A4 | Quitar el registro duplicado del hook CDIO en `~/.claude/settings.json` | 2 | S | Medium | ESPERA AL OWNER, SIN VERIFICAR | `design_gate.py` corre dos veces por escritura visual. Borrar la entrada directa, dejar la del dispatcher; re-correr `tools/test_hook_boundary.py`. Fuente: `vault/plans/cdio-enforcement-trust-root-resumption-2026-09-13.md` L57. |
| A5 | CDIO: ¿la denegación ampliada (6 majors → 52 = BLOCK) es la severidad deseada? | 2 | S | Medium | DECISIÓN DE PRODUCTO | Palanca: `SEVERITY_DEDUCTION["major"]` o `APPROVE_MIN`. Fuente: ídem, abierto 1. |
| A6 | CDIO D2/D3: REVISE inalcanzable; `score_review([])` = 100/APPROVE | 2 | M | High | DECISIÓN DEL OWNER, SIN VERIFICAR | Cambia la composición del score. D3 pide un estado de abstención distinto del neutro (CLAUDE.md ya habla de `ABSTAIN`: verificar si D3 se cerró). Fuente: `cdio-callable-liveness-resumption-2026-09-13.md`. |
| A7 | Ablandar o no el veto de frontera (memoria cognitiva) | 2 | S | Medium | DECISIÓN DEL OWNER | Fuente: `vault/plans/cognitive-memory-virtualization-RESUMPTION.md` acción 1. |
| A8 | Pregunta de modo de permisos del worker; luego una corrida GSD real | 2 | S | Medium | DECISIÓN DEL OWNER | Fuente: `vault/specs/mission-continuity.RESUMPTION.md` acción 3. |
| A9 | Noche pp-eval: `PASS_TIMEOUT_MS` 180 s → 600 s, o 1 fuente por pasada | 2 | S | Medium | DECISIÓN DEL OWNER, SIN VERIFICAR | La pasada de 20:04Z murió por timeout del worker a 180 s. Fuente: handoff `05c497a1`. |
| A10 | Borrar el backup de identidad (sha256 `167f16fe…`) y `index.identity-1790970811.bak` (111,7 MB) | 3 | S | Low | ESPERA FRASE LITERAL | Solo con la frase tecleada *"delete the identity backup"*; re-hashear antes. Fuentes: handoffs `fa590a33`, `0dc5ef92`, `fa65b059`. |
| A11 | ¿Cuenta el `owner_go` de un spec como intención de una goal? Y elegir una goal para la prueba viva de S3 | 2 | S | Medium | DECISIÓN DEL OWNER | S3 (observar una misión Ralph) necesita una goal elegida por el Owner. Fuentes: handoff `969d8063`, `vault/specs/goal-observe-ralph-mission.md` §Production Reality. |
| A12 | Rollover: hunks huérfanos en `rollover.py` (bloque decide + arreglo torn-append) | 2 | S | Medium | DECISIÓN DEL OWNER | Fuentes: handoff `fa65b059`, `memory/project_session_handoff.md`. |
| A13 | Dueño canónico de `hooks/tests/` (11 en repo vs 48 en `~/.claude/hooks/tests/`) | 3 | S | Medium | DECISIÓN DEL OWNER | El drill documentado en `hook-dispatcher.js:540` no se puede correr desde el repo. Fuente: `vault/knowledge_base/ucr_cif/TORRE_UNIVERSAL_HANDOFF.md` §10. |
| A14 | Despliegues en staging pendientes (HR-001) | 2 | S | Medium | ESPERA AL OWNER, SIN VERIFICAR | `vault/staged/2026-09-23_deploy_deadline_abandon_names.md`, `vault/staged/2026-09-23_deploy_autocompact_ledger.md`. Fuente: TORRE §10. |
| A15 | Promover a B1 el candidato web_surface (pausa + reduced-motion), y la conciliación MIOSA | 3 | S | Medium | REVISIÓN DEL OWNER | Fuentes: handoffs `83135faa`, `8b2c7516`. |
| A16 | V-HOOK-BOUNDARY test frente a promover `findDesignMd` al repo contenedor | 3 | S | Low | DECISIÓN DEL OWNER | Fuente: handoff `83135faa`. |
| A17 | Push de `feature/knowledge-acquisition` | 3 | S | Low | SOLO SI EL OWNER LO PIDE | La rama lleva commits de otros escritores. Fuentes: handoffs `83135faa`, `fa590a33`. |
| A18 | Apuntar el panel UWCP a `vault/specs/uwcp.AMENDMENTS.md` (Q1); promoción del ratchet X8 tras UWCP Golden 01 | 3 | S | Medium | ESPERA AL OWNER | Fuente: `vault/specs/uwcp-assimilation.RESUMPTION.md`. |
| A19 | Confirmar o rechazar las 3 lecturas del spec (HANDOFF W14 §5); pasar el handoff a `kc-diffint-wt` antes de W9/W12/W14 | 2 | S | Medium | ESPERA AL OWNER | Fuente: `vault/tower/SUBSTRATE_RESUMPTION.md`. |
| A20 | Activar 6 hooks construidos y no registrados | — | — | — | YA EN `deferred-backlog.md` D2 | No duplicar. |

## B. Ingeniería en curso (septiembre–octubre)

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / fuente |
|---|---|---|---|---|---|---|
| B1 | Virtualización de agentes **S5 telemetría → S6 foundry (solo baja de clase) → S7 cierre** (UKDL, liveness, gate de creación de agentes) | 1 | L | High | PENDIENTE | S4 cerrado (`535d691a`). Deuda: "C++" sola nunca enruta a cpp-reviewer; las corridas herméticas no cargan hooks de usuario; GEX44 sin `carrier_bash_guard`. Medir la planitud del padre con carriers instalados. Fuente: `vault/specs/agent-capability-virtualization.RESUMPTION.md` acción 3, handoff `f3099e7b`. |
| B2 | El hub elige la cápsula más nueva por directorio (`rolloverFocus`) | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Con dos paneles en un mismo dir, el foco puede ser el del otro. Fuentes: handoff `614697c1`, ACV deuda. |
| B3 | gsd-x: **ola W3 de conciliación** (commits ajenos tras `e0f541f`) | 2 | M | Medium | PENDIENTE | Inventario con `tools/gsd_x_recon_streams.py`; una afirmación OBSERVED por stream; avanzar RECONCILED-THROUGH; `test_gsd_x_dataset` en GEX44. Fuente: `vault/specs/gsd-x-n8.RESUMPTION.md` paso 5. |
| B4 | gsd-x: re-medir la latencia del hook gsd_x con holgura de RAM (límite hijo 6 s) | 2 | S | Medium | PENDIENTE | Medianas, no lecturas sueltas. Fuentes: n8 paso 3(c), handoff `e06381e2`. |
| B5 | gsd-x: primera promoción real `ratchet.promote` → B1 → B1 inyectado | 2 | M | High | PENDIENTE | Toda familia sigue en B0. Fuente: n8 paso 3(a). |
| B6 | gsd-x: `donegate.judge` sin llamadores en producción | 2 | M | Medium | DECISIÓN (spec §7 lo deja solo-informe) | Fuente: n8 paso 3(b). |
| B7 | gsd-x: invertir `V-FACTSV2-PRODUCER-REACH` y reescribir el párrafo HONEST BOUNDARY | 1 | S | High | PENDIENTE, SIN VERIFICAR | Ya existe un hecho gating (`99e96e1`); el gate debe ponerse rojo. Fuente: n8 Gap 5. |
| B8 | gsd-x: productores para los **5 hechos gating aún UNPRODUCED** | 2 | L | High | PENDIENTE | Una misión estructurada real bloquea, correctamente, nombrándolos. No commitear un FACTS.json producido (caduca en minutos). Fuente: n8. |
| B9 | gsd-x: el campo `message` de `cmd_check` encabeza con la razón equivocada | 3 | S | Low | PENDIENTE | Usar `block_reasons`. Fuente: n8. |
| B10 | gsd-x: cerrar F5 (`cmd_check` no debe aceptar una raíz que nadie derivó) | 2 | S | High | PENDIENTE, SIN VERIFICAR | Fuente: n7 acción 2. |
| B11 | gsd-x N5: contrato de portabilidad de `sh`; declarar el runtime en el manifiesto; quitar las rutas absolutas `C:/Users/User/...` del predicado (E11) | 2 | M | Medium | PENDIENTE | Sin magia de entorno (no anteponer Git `bin` al PATH). D1/D2/D4 ya reportados upstream (#5133, GHSA-27c7-mm4w-qwgp). Fuentes: n5, n6. |
| B12 | gsd-x N5: **simulacro de ship W1** en un proyecto GSD desechable (rojo / verde / control negativo) | 2 | M | High | BLOQUEADO por B11 y D1/D2 upstream | Hoy pararía en exit 127 y parecería el polo rojo pasando. Fuentes: n5, n6. |
| B13 | gsd-x N5: capa de decisión sobre el detector de drift de GSD Core (sin segundo detector) | 3 | M | Medium | PENDIENTE | Fuente: n5. |
| B14 | gsd-x N5: `-GhostSelfTest` no está libre de efectos (el escaneo vivo de husks corre antes de mirar el flag) | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Mover la comprobación del flag encima del bloque de husks. Fuente: n5. |
| B15 | gsd-x N3/N4: mutante `dormancy-reverted` SOBREVIVE en `test_gsd_x_mutation.py` | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Escribir el test que lo mata o clasificarlo como equivalente con argumento trazado. Fuente: n3. |
| B16 | gsd-x: `.github/` no existe — nada aplica los gates al hacer merge | 3 | M | Medium | NECESITA PERMISO DE ADMIN DEL REPO | Workflow con las cuatro comprobaciones + protección de `main`. Fuentes: n3, n4, n5. |
| B17 | gsd-x: 56 afirmaciones sin `depends_on` (inventario congelado, solo encoge) | 3 | M | Low | PENDIENTE | Fuentes: n3–n5. |
| B18 | gsd-x: sustituir el adaptador de realidad en prosa (GSDX-M04) por hechos estructurados; registrar el manifiesto en un punto del ciclo de vida y ver la parada en una ola real (GSDX-M05/M12) | 2 | L | High | PENDIENTE, SIN VERIFICAR | Antes de Consequence Closure. Fuente: n4. |
| B19 | gsd-x: `GSDX-C08` (re-entrada orca-exact) sigue UNPROVEN | 3 | M | Low | PENDIENTE | Fuente: n3. |
| B20 | SDD-OS W4/W5: estado de decisión antes de `jit fn(data)`; gate de escritura del node-launcher en sombra | 2 | M | Medium | PENDIENTE, SIN VERIFICAR | W1–W3 hechos (`e725c373`, `f53141a0`, `5a0a0ced`). Re-baselinar los dos pares nuevos de `mutation_ratchet` (hashes cambiados). A/B de `test_dataset_build` en árboles idénticos (291 s vs 98 s). Fuentes: handoffs `d64d2f98`, `58421b93`. |
| B21 | Rollover: drill de `rollover_replay` vía `tools/mutation_drill.py` (4 mutantes con nombre) | 1 | S | High | EN CURSO EN OTRO PANEL | `tools/rollover_replay.py` y su test están sucios ahora. No tocar hasta que ese panel haga commit. Fuentes: handoff `fa65b059`, `memory/project_session_handoff.md`. |
| B22 | Rollover: encontrar un CONTINUE real impulsado por el horizonte (el control negativo sigue PARTIAL) | 2 | M | Medium | PENDIENTE | Fuente: ídem. |
| B23 | Rollover: probar que el despacho AUTOMÁTICO tecleó el `/clear`; la pregunta `8167513f`; ejercitar `tmux-exact` en GEX44 | 2 | M | Medium | PENDIENTE | Hace falta una sesión con trabajo real (una worktree ociosa no sirve). Fuentes: `interactive-context-rollover.RESUMPTION.md`, handoff `624f4750`. |
| B24 | Rollover: primera fila viva del ledger de `kresume_courier` con `outcome=ARMED`; gates `V-KRC-AMBIGUOUS-REFUSED` y `V-KRC-WATCHDOG-PICKS-OWN-PROCESS` + 2 mutantes | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | El courier existe (`3993e769`). Seguimientos: el `/clear` nunca llegó, arranque lento del daemon, los tests escriben el almacén real de cápsulas. Fuentes: handoffs `624f4750`, `62f6a1a7`. |
| B25 | Arreglar la renovación ciega a cuota: `renewal_refusal` debe negarse mientras haya `provider_hold` | 1 | S | High | PENDIENTE | Primero el test. Fuentes: `external-capability-assimilation.RESUMPTION.md`, handoff `ea725130`. |
| B26 | Tras el reset de cuota del 4-oct: smoke con ≥ 1 `turn_continued` del supervisor (la mitad que falta de T11); handoff final | 1 | S | High | ESPERA AL RESET | Misión PARTIAL en 22/32/33. Fuentes: ídem, handoff `05c497a1`. |
| B27 | Confirmar el próximo cruce automático: `successor_claimed` sigue a `reset_gate` sin `/kresume` manual | 2 | S | Medium | OBSERVAR | La tarjeta de rollover está en el char ~4,9k de ~7,7k de SessionStart; el host trunca cerca de 9 KB: valorar poner el hub primero. Fuente: ídem. |
| B28 | Diagnosticar la misión `m-860e4176f1d6` (inactiva en epoch 1, 0 continuaciones / 0 commits) | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Transcript + ledger. Fuente: handoff `05c497a1`. |
| B29 | Continuidad de misiones: vigilar W8 (`m-7cebf2b33bf3`); si va bien, filas E18+, addendum de certificación, commit de `commands/cpp-gsd-long.md` (sección v3) + hunk UKDL | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Fuente: `vault/specs/mission-continuity.RESUMPTION.md`. |
| B30 | Continuidad: primera parada viva `no_progress`; ruta COMPLETED nunca vista en una corrida real; no probados reboot, varios días, fsync ante corte | 3 | L | Medium | PENDIENTE | Fuentes: handoffs `958a5394`, `b0d83764`. |
| B31 | Detector `no_progress` de Ralph mira el cwd de la misión, no la worktree del worker | 2 | S | High | DEL PANEL DUEÑO, SOLO REPORTAR | Paró `m-3fa466eb6cc8` por la razón equivocada. Fuentes: `cognitive-resource-os-RESUMPTION.md` §2b, handoff `fe1c49ea`. |
| B32 | Carrera check-then-delete al reclamar un lock caducado en `gsd_mission._Lock` | 2 | S | Medium | PENDIENTE | Fuente: handoff `b0d83764`. |
| B33 | Plegar los drills de copia aislada en `tools/lane_r_mutate.py`; ítems 8-14 del ratchet piden segundo proyecto + prueba de transferencia | 3 | M | Low | PENDIENTE (UWCP es dueño) | Fuente: handoff `958a5394`. |
| B34 | Rotación de epochs del padre: correr el juez (si `rotations_certified` ≥ 3, evidencia a spec §5 + lección); re-correr `gsd_epoch.py census` | 2 | S | Medium | PENDIENTE | Fuente: `vault/specs/parent-context-epoch-rotation.RESUMPTION.md`. |
| B35 | pp-eval: leer `~/.claude/state/pp-eval/nights.jsonl`; 5 drills sin correr; banco ≥ 8 tareas | — | — | — | YA EN `deferred-backlog.md` D4–D6 | No duplicar. T7 (banco pp_eval desde tareas P3) coordinar con el panel activo. |
| B36 | CRO: entrega por evento de `instrument-before-claim` / `real-context-reachability` (auto-activación 1/12) | 2 | M | High | PENDIENTE, SIN VERIFICAR | `instrument-before-claim` ya es skill auto-activable (`efdb5e0c`); verificar si la tasa subió. Fuentes: handoffs `e9d6887e`, `fe1c49ea`. |
| B37 | CRO: P4 ejecución durable, P5 reutilización de memoria, P6 fusión de enrutado | 3 | L | Medium | PENDIENTE | Fuente: handoff `fe1c49ea`. |
| B38 | CRO: inspeccionar los 22 directorios sobrantes en `C:\Users\User\Apps\p3-runs` antes de limpiar nada | 3 | S | Low | PENDIENTE | Inspección, no borrado (skill `destructive-state-authorization`). Fuente: handoff `fe1c49ea`. |
| B39 | CRO-01: re-correr 01-02 en GEX44 con el venv aprobado (`/gsd-execute-phase 1 --ws cognitive-resource-os`) | 2 | S | Medium | APROBADO 2026-09-28, SIN VERIFICAR SI CORRIÓ | Fuente: `cognitive-resource-os-RESUMPTION.md` §4 acción 1 y §2b. |
| B40 | CRO: seguimiento del fallo de prefijo (medir intervalo entre sesiones sdk-cli frente al TTL, cero llamadas); arreglar 04-REVIEW CR-01/WR-01/WR-02 antes de reutilizar `ab_runner.py` | 3 | M | Medium | PENDIENTE | Excluir las claves `-tmp-claude-1000-cro-p04-ab-arm{A,B}` de futuros baselines GEX44. Fuente: ídem §2e, §4. Relación: `2026-10-03_token-economy-wave2.md` #16. |
| B41 | CRO: huecos de instrumento (USD por entrypoint a 7 d, cuota de escritura 1 h, entrypoint de sesiones MEASURED_ZERO); registrar `claude --version` del portátil | 3 | M | Low | PENDIENTE | Fuente: ídem §2e. |
| B42 | Consolidar parsers: proponer `tis_observed` como único dueño del uso de transcripts a los paneles de `tco_compact_gate` / `token_ground_truth` | 3 | M | Medium | PROPONER, NO IMPONER | Un llamador por commit, con su acuerdo. Fuente: ídem §4a. |
| B43 | CCP: sonda de modelo G5 tras el reset del 07-oct | 2 | S | Medium | ESPERA AL RESET | Fuente: handoff `f19774a9`. |
| B44 | CCP L1 diferido: una base de almacén relativa/enlazada convierte cada dir en alias | 3 | S | Low | DIFERIDO CON DISPARADOR | Fuente: `cognitive-control-plane-RESUMPTION.md`, handoffs `223fedf2`, `db8ae5cd`. |
| B45 | CCP: c9 mutantes (siete de s12 + tres de s13) con el CLI estándar de `mutation_drill.py`; RCA s18 con los hechos c5–c8; handoff S3 a `claude-power-pack-da` | 3 | M | Medium | PENDIENTE, SIN VERIFICAR | `mutation_drill.py` ya soporta el caso (`94c55903`). Fuente: handoff `b3c38ac8`. |
| B46 | Economía: medir el ahorro vivo del rollover y la alarma semanal ponderada | — | — | — | YA EN `2026-10-02_weekly-limit-burn-followups.md` | No duplicar. Fuente: handoff `e4c2d161`. |
| B47 | Palancas sin dueño: enmascarar la salida de herramientas (~52 % más barato, JetBrains), sondas sdk, hueco de RTK en PowerShell | 3 | M | Medium | PENDIENTE, SIN VERIFICAR | Comprobar si la ola 2 de token-economy ya las recoge. Fuente: handoff `969d8063`. |
| B48 | Torre: **clasificador de familia** (bloqueante único de CRR/RFR/BIR); conector FD-07 → `applicability.py`; las 12 preguntas de HR-NOVELTY | 2 | L | High | PENDIENTE | Señal candidata: composición de ficheros del repo. Ojo a G-4 (genoma parcial invierte la aplicabilidad). Relación: `2026-09-23_torre-universal-out-of-scope.md`. Fuente: TORRE §8. |
| B49 | Torre: solapamiento E1∩E2 (87 ficheros) sin desambiguar; `liveness/reachability.py` no corrido en esa pasada | 3 | S | Low | PENDIENTE | Fuente: TORRE §10. |
| B50 | UWCP S1-8c (A2): `OBS_LOST` → `UNKNOWN` en `claude.py:144` / `codex.py:262`; sonda tri-estado; luego S1-8d (lock codex X0) | 2 | M | High | PENDIENTE, SIN VERIFICAR | Re-correr solos M5–M8 de los drills de workspace (la primera corrida fue INVALID por suites concurrentes). Fuente: `vault/specs/uwcp.RESUMPTION.md`. |
| B51 | UWCP S3 fingerprint (`goal/baseline.py`) y S4 adaptador de nodo + almacén de leases en VPS | 3 | L | Medium | PENDIENTE | S4 escribe en el VPS: reglas DEPLOY antes. Fuente: ídem. |
| B52 | UWCP Lane L: filas OWED del corpus (reproducir primero los contraejemplos TLC S1-8c FalseLost y A2f Expire como tests rojos); REMOTE_REALITY en GEX44 | 3 | L | Medium | PENDIENTE | Fuente: `uwcp-assimilation.RESUMPTION.md`. |
| B53 | Exact-target continuation: leer `report` tras el próximo cruce (primera prueba real de `f2462ee`); simulacro de dos paneles (Fase 1 T2-3) | 3 | S | Medium | BLOQUEADO: necesita una segunda terminal abierta | Fuente: `vault/specs/exact-target-continuation.RESUMPTION.md`. |
| B54 | CDIO: test que lance `design_gate.py` como el hook y afirme el `deny`; disparador automático para el ratchet de callables y la suite de frontera | 2 | M | High | PENDIENTE, SIN VERIFICAR | CLAUDE.md ya cita `tools/test_hook_boundary.py` (V-HOOK-*): verificar si cubre (9). Fuentes: los dos handoffs CDIO de 2026-09-13. |
| B55 | CDIO: `hooks/cdio_visual_advisory.js` dice que un documento SKIP "clears the anti-slop floor" y omite ABSTAIN | 2 | S | Medium | PENDIENTE, SIN VERIFICAR | Estaba bloqueado por 68 líneas ajenas sin commit. Fuente: ídem. |
| B56 | CDIO: el salto del harness (que el harness HONRE el `deny`) no está probado; sin fixture de subida hasta un ancestro ni de parada en `.git` | 3 | M | Medium | PENDIENTE | Fuente: cdio-enforcement abierto 2-3. |
| B57 | CDIO: comprobaciones mecánicas derivables de DESIGN.md (pares de contraste, escala de espaciado, niveles tipográficos) | 3 | M | Medium | PENDIENTE | Nada automático observa una superficie renderizada: no afirmar los suelos WCAG en producción. Fuente: cdio-callable abierto 5-6. |
| B58 | CDIO: `callable_reach` sin alcanzabilidad transitiva; `V-DESIGN-HARD-FILTERS-REACHED` no exige el filtro de experiencia; "dependencia resuelta" = declarada en `package.json` | 3 | L | Low | PENDIENTE | Fuente: cdio-callable abierto 7, 10, 11. |
| B59 | Motion grammar: procesar una 2ª referencia de movimiento (`REF-MOTION-001`) para habilitar la promoción | 3 | M | Medium | PENDIENTE | Fuente: handoff `83135faa`. |
| B60 | **Promover candidatos UKDL atascados** (motion grammar, mission-continuity, rotación de epochs, horizon-constant / successor-join / torn-append, N3 ×5, N4 ×13, `USEA_TRAPS.md`, `ukdl_candidates` de ACV/UCR, puntero router CDIO) | 2 | M | Medium | PENDIENTE | El bloqueo cambió de nombre: el escritor continuo es el auto-apéndice CEPS (GSDX-M09), así que "un rato tranquilo" no llega. Aterrizar solo esas filas con staging por hunk. Fuentes: n8 paso 6, handoffs `83135faa`, `958a5394`, `fa65b059`, CDIO, USEA. |
| B61 | Mutation drill: falta un seam `test_env` para un sujeto cuyo test vive en otro directorio | — | — | — | CERRADO POR `94c55903`, VERIFICAR | `post-edit-diagnostics.RESUMPTION.md` aún lo da por abierto. |
| B62 | Post-edit diagnostics v2 para TypeScript (checker con proyecto) | 3 | M | Low | AUSENTE POR DISEÑO | Fuente: `post-edit-diagnostics.RESUMPTION.md`. |
| B63 | DRK: adaptadores vivos (arch_check, d2a_engine, `spec_gate.classify_tier`, `acis.epistemic_ladder`, `cost_collapse.route`, owner_queue) hacia `decision_kernel.py` | 3 | M | Medium | PENDIENTE | Verificar firmas antes (HR-PREMISE-001). Fuente: `vault/plans/DRK_RESUMPTION.md`. |
| B64 | Raíz `RESUMPTION_FILE.md`: experimento del muro nativo; A/B de `continuation: "stop-block"`; `CHAIN_DEADLINE_MS` para `Stop-chain`; `runtime` en `.planning/config.json` de 4 proyectos GSD; explicar la asimetría pass/block del overlay; cronometrar con holgura | 3 | M | Medium | PENDIENTE, SIN VERIFICAR | Fuente: `RESUMPTION_FILE.md`. |
| B65 | SQI: inventario de umbrales (§15.7), cada cambio un evento de gobierno; apuntar `run_sqi.py` al resto del estate (TUA-X 390 tests huérfanos, escáner de CostaLuz, dos repos Elixir); presentar al Owner los 4 hallazgos PP (default sin argumentos roto, sin pytest config raíz, invocación canónica, 63 paquetes desprotegidos incl. `secret_firewall`, `cascade_prevention`) | 2 | M | High | PENDIENTE | No existe ningún inventario de umbrales en el árbol. Fuente: `RESUMPTION_FILE.md` §4 (bloque SQI). |
| B66 | USEA: correr el contraste de resultados (gasto autorizado el 2026-09-13, condicionado a RAM: `admit(samples=5)` = QUALIFIED); llevar al Owner la brecha LAW II / LAW IX (una línea en `~/.claude/`); re-medir la apertura del denominador de liveness (`tools/` quedaba fuera) | 2 | M | High | PENDIENTE | No encoger la corrida ni forzarla. Fuente: `vault/knowledge_base/usea/USEA_RESUMPTION.md`. |
| B67 | Statusline / despliegue de hooks: desplegar la copia de `~/.claude/hooks` de `gsd-statusline.js` tras verificar vivo == HEAD | 3 | S | Low | VERIFICAR | El arreglo está en el repo (`fde1bb4d`); falta comprobar que vive. Fuente: handoff `e9d6887e`. |
| B68 | Wiki: commitear las páginas PP (cbr, maturity-transfer, sources, raw, `cbr_probe.py`) por pathspec | 3 | S | Low | VERIFICAR | `4868e2fb` commiteó el análisis CBR; comprobar si quedan ficheros sueltos. Fuente: handoff `62f6a1a7`. |

## C. Otros repos (anotados en handoffs de este repo)

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / fuente |
|---|---|---|---|---|---|---|
| C1 | KSR: fila `KSR-B-073` (integridad de guardado) en `KSR_BACKLOG.json`; 2 ítems KobiiCraft en `post-launch-backlog.md` (praxis skip, gates py) | 2 | S | Medium | PENDIENTE EN EL OTRO REPO | Fuente: handoff `62f6a1a7`. |
| C2 | PR #472: capturas antes/después de GEX44 al cuerpo del PR, merge con OK del Owner; `/quicklease/contact` agota 45 s en build de prod; reglas oscuras 5-6 con Tab real; backlog 2 y 3 de ese repo | 2 | M | Medium | PENDIENTE EN EL OTRO REPO | Fuente: handoff `298b1bce`. |
| C3 | io-focus (InfinityOps): arreglo `restoreFocus` de FocusDialog, vitest + tsc, despliegue en GEX44 (:3100/:4100), `verify-focus.sh`, pasar STD-112/113 a LIVE | 2 | M | Medium | PENDIENTE EN EL OTRO REPO, SIN VERIFICAR | Fuente: handoff `8b2c7516`. |

## D. Lo antiguo (julio–agosto y antes): lo que sigue sirviendo

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / fuente |
|---|---|---|---|---|---|---|
| D1 | **UCR-CIF**: re-verificar KIND en las 71 filas `system` y 73 `subsystem`; resolver las 9 restantes (umbrella UCR-CIF, HIC-OAR, UDFLL, Constitutive Baseline Ratchet, Capability Authority Registry, Knowledge Compiler/Linker, Meta-Failure Genome, Institutional SLOs & Chaos, Long-Horizon Campaign) sondeando la función, nunca el acrónimo; Atlas / glosario / matrices de relación y flywheel con aristas causales tipadas | 3 | L | Medium | PENDIENTE | La misión siguió en la Torre (fases C, H selladas 2026-09-23; F bloqueada, ver B48). Las fases 2 / 3b / 5 del RESUMPTION de agosto no constan cerradas. Fuente: `vault/knowledge_base/ucr_cif/UCR_CIF_RESUMPTION.md` §4. |
| D2 | **CDICF A2**: esquema del Component Manifest (`vault/schemas/component_manifest.json`, no existe) + fijar los 5 commits upstream y rellenar los campos NOT PINNED de `vendor/NOTICE.md` | 3 | M | Medium | PENDIENTE | Fuente: `vault/audits/cdicf/CDICF_RESUMPTION.md`. Spec ligado: `vault/plans/cdicf-corpus-2026-08-06.md` (NOT_READY). |
| D3 | **CDICF legal**: titular del copyright de Tailark; ¿`nilbuild/driver.js` es canónico o redirección de `kamranahmedse/driver.js`? | 2 | S | High | PENDIENTE | Bloquea la atribución. Un componente sin licencia clara no se distribuye. Fuente: ídem. |
| D4 | CDICF A3: emisor de `registry.json` con instalación determinista fijada a commit + rollback | 3 | M | Medium | BLOQUEADO por D2, D3 | Fuente: ídem. |
| D5 | **CrawlOS dataset 4** (HTTP Fetch and Transport Intelligence); leer antes la Parte XVII del dataset 3 | 3 | L | Medium | PENDIENTE | No existe fichero 04 en `vault/knowledge_base/crawl_os/`. Fuente: `CRAWLOS_RESUMPTION.md` §4. |
| D6 | CrawlOS: comprobación de auditoría de citas en `tools/test_crawl_os.py` (frases de lista de campos duplicadas entre datasets) | 3 | S | Low | PENDIENTE | Guarda de regresión contra re-enunciados. Fuente: ídem. |
| D7 | **CPP-ACI**: STOP #1, aprobar o no la arquitectura (recomendada: delta circulatorio, ~6–8 datasets) | 3 | S | Medium | ESPERA AL OWNER desde 2026-07-12 | No hay nada construido. Antes de construir, HR-NOVELTY-001 (13 preguntas) aplica: varias mega-propuestas de este repo resultaron ya cubiertas al medirse. Fuente: `vault/knowledge_base/cpp_aci/BUILD_STATUS.md`, `HANDOFF.md`. |
| D8 | CPP-IAS: Partes VIII (1.227) y XVI (1.161) de IAS-F1 bajo la banda 1.300–1.500; ejemplos de media geométrica de IAS-F2 Parte XVIII no verificados por script; bucles COMPOUNDING_GRAPH no ejercitados | 3 | S | Low | NO BLOQUEA EL SELLO | Fuente: `vault/knowledge_base/cpp_ias/HANDOFF.md`. |
| D9 | Skills de mydeepchat no instaladas (CP-005): `ascii-video`, `agent-sort` | 3 | M | Low | CANDIDATAS | Las demás de esa lista ya tienen equivalente instalado (ver "Cerrado al verificar"). La fuente sigue en `vault/audits/mydeepchat_skills_raw.jsonl`. Ninguna está instalada. Fuente: `vault/handoffs/HANDOFF_2026-04-30_to_2026-05-01.md`. |
| D10 | CP-007: citar BL-0001..BL-0009 como suelo en `parts/sleepy/agent-governance.md` y BL-0008 en el bootstrap de proyecto | 3 | S | Low | SIN VERIFICAR | Fuente: ídem. |

## Cerrado al verificar (no reabrir sin nueva evidencia)

- Tally R2 / REPORT.md R2 → `d50cb079` (24/24 válido, pasa en ambos brazos).
- CCP: ack del par `0f4a8796`, ranking C4.1, detector de re-derivación, PRG, cambio de
  `usage_index._store_dirs`, `estate_displacement` → `fanout_ledger` → `cognitive-control-plane-RESUMPTION.md` §3–4, `9b28175c`.
- **CLAE Partes 27–30** (`RE_BASELINE_RESUMPTION.md`) → las cuatro SEALED, `parts_sealed: 33` en `CLAE_INDEX.md`.
- **DAIF-00 en adelante** (`DAIF_RESUMPTION.md`) → `DAIF_INDEX.md` marca los datasets `SEALED`, ninguno en un estado intermedio.
- gsd-x: conciliación repo-wide hasta `e0f541f`, re-pin, M08/M05, `test_gsd_x_dataset` 11/11 → n8 paso 5. Hecho gating (`99e96e1`), agujero silent-OUT (`2a80b35`), frontera recompilada.
- Informe upstream D1/D2/D4 → presentado como #5133 + GHSA-27c7-mm4w-qwgp.
- SDD-OS W1–W3 → `e725c373`, `f53141a0`, `5a0a0ced`.
- Statusline con % bruto → `fde1bb4d`.
- `kobiiclaw-autoresearch.js` → retirado `06c20284` (Owner, 2026-09-28).
- ACV S3/S3b/S4 → `535d691a` (S4 cerrado, opción b).
- Post-edit diagnostics Gap 2 v1 → `88e8c91`, vivo.
- Síntesis wiki token-economy → `dfe30814` / `084b46db`.
- `mutation_drill.py` con test fuera del directorio del sujeto → `94c55903`.
- CP-005 (2026-04-30), equivalentes ya instalados: `content-engine` ≈ `social-content`; `ui-demo` ≈ `/product-demo`;
  `blueprint` ≈ `/ultra` + `superpowers:writing-plans`; `gstack-openclaw-ceo-review` ≈ lente `musk`.
  CP-006 (hook orquestador multi-edit): a mi juicio, no medido, lo cubren la doctrina de batches y `agent-solo-guard.js`; reabrir si el Owner lo quiere.
- Avisos `vault/handoffs/mirror-drift-2026-05-2*.md` (~60 ficheros, la misma acción) → la causa raíz es `deferred-backlog.md` D1.
