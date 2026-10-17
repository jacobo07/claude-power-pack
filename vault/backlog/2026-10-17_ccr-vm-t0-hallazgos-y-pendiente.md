# Backlog — CCR boundary CWS (goal ccr-vm): hallazgos de T0A y lo que queda (2026-10-17)

Origen: panel coordinador de claude-power-pack, Owner "añade todo eso al backlog" (2026-10-17). No corre nada.
Plan aprobado: `vault/plans/ccr-boundary-cws-plan-2026-10-17.md`. Entregables de T0A: rama `ccr-vm/t0` (worktree
`C:\Users\User\Apps\pp-ccr-vm`) commit `6624e27d`: `vault/programs/ccr-vm/T0A-reality.md` y `WU-T0A-receipt.md`.

## Hallazgos de T0A (etiqueta: MEASURED / READ / UNVERIFIED)

- **CCR está en modo shadow en todo** (MEASURED). Últimas 24 h hasta 2026-10-17 15:51: 16 de 16 arranques con
  `compatible=false` (2.1.302 x10, 2.1.301 x6). `COMPAT` sigue en `['2.1.296']`
  (`mods/cpp-cognitive-runtime/hooks/policy.ts:8`). El campo `mode` no aparece en las líneas `start`, así que no se
  puede probar que alguna corriera sin shadow; `register.ts:54,84` dice que ninguna puede.
- **UCVM, UTVM, SSM y UCWSM no tienen código** (READ). Solo existen en documentos de plan. Clase: SPEC_ONLY.
- **Un solo dueño para la compilación de contexto**: `modules/cognitive_os/context.py` más el libro de límites de v5,
  con CCR como plano de ejecución y enlazado. No hace falta ULTRA-PLAN.
- **No hay admisión antes de la petición al modelo** (READ). Solo antes de llamadas a herramientas y antes de
  lanzamientos (`session_budget_guard.js`, `econ_admission.js`, `gsd_mission.py:2672 admit_route`).
- **La matriz del Mod no se re-sondeó en 2.1.302** (UNVERIFIED). No hay `.d.ts` generados bajo
  `mods/cpp-cognitive-runtime` ni `~/.claude/ccr`. Todas las filas siguen "heredadas de 2.1.296".
- **Sin verificar**: si el carril PreToolUse-Agent está registrado; el alcance real de los módulos de `cognitive_os`
  (el grep por nombre de fichero es ruidoso; `guarantee_ledger.py` sale sin referencias externas); dónde están el proof
  graph, el Estate Controller, el Capital Allocator, la reserva de límites y el Mission Cost Tree.

## Pendiente, en orden

1. **T0B** (unidad nueva, panel nuevo con contexto pequeño): `WU-T0B.md` + `route-T0B.json` (20 llamadas, stop 3,7M).
   Tareas: re-sondeo real de la matriz en 2.1.302 (generar tipos o sonda headless), suelo del host frente al suelo de
   CPP, tres experimentos de reclamación, un flamegraph (script que solo imprime totales), factibilidad de rotación,
   diseño del benchmark de elasticidad, `ccr-vm-tranches.md`. Armar con `envelope` y `admit` en UNA llamada.
2. **Decisión del Owner, bloquea T1**: ensanchar `COMPAT` a las versiones verificadas, o una puerta de versión que
   re-sonde en cada actualización del host (la "Unit Zero" del 2026-10-16, dentro de v5 Env 1 en L17).
3. **Presupuesto de ccr-vm**: tope 9,0M. Al 2026-10-17 llevaba 3,62M usados y quedaban 5,38M. T0A costó 383K. Casi
   todo lo gastado es del panel coordinador. Si tras T0B no alcanza para T1, pedir un paquete nuevo.
4. **Limpieza de lo armado**: misión `m-3c994f67f25f` en `HALTED` (cierre normal tras la entrega); mezclar o
   descartar la rama `ccr-vm/t0`; el commit `3d97a6b2` del plan y los WU vive en `feature/knowledge-acquisition`.
5. **Documentos de plan obsoletos**: `WU-T0.md` queda sustituido por `WU-T0A.md` y `WU-T0B.md`; `route-T0.json` y
   `route-T0AB.json` ya no se usan (la ruta de 45 llamadas costaba 15,1M por el modelo de crecimiento).

## Lecciones para el vault (candidatas, sin promover)

- **Un panel coordinador que entra en el worktree de un goal queda ligado a ese goal** y gasta su tope. Llevaba
  241K de contexto por llamada y consumió cerca de 3,2M de los 9,0M. Declara el goal y arma desde un panel pequeño.
- **El modelo de admisión sobreestimó T0A unas 13 veces** (previsto 4,96M, medido 383K). Crecimiento 1815 por
  llamada y razón física 2,4 salen de muestras pequeñas (n=5 y n=4); recalibrar con este dato.
- **`goal-declare --owner` pide un terminal interactivo**: falla con `EOFError` bajo el prefijo `!` y con
  entrada que se parte en dos líneas. Ejecutar en una ventana PowerShell aparte.
- **`capital-apply` solo cuenta una aprobación escrita después de un mensaje que muestre el sha256 completo**, y la
  frase válida es `approve <goal> only`. `approve ccr-vm T0` no es válida.

## Fuera de alcance

Cambios de código en `mods/`, `modules/` o `tools/`, releases, `settings.json`, capital de Tennis, T1 a T11.
