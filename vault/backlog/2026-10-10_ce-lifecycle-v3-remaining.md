# Backlog — lo que queda de la misión ce-lifecycle-v3 (2026-10-10)

Origen: misión /cpp-gsd-long "Universal Work Unit Lifecycle Economics", coordinador 3339c6c2. El Owner pidió
aparcar el resto en el backlog (2026-10-10). **No hay ninguna misión armada ni corriendo para este goal**; nada
avanza solo hasta que se retome.

## Estado al aparcar

- Goal `ce-lifecycle-v3`: tope 14.000.000 (journal seq 102, opción 3 del Owner), usado 9.079.339, **quedan
  4.920.661**, open 0. Ligado por cwd a `C:\Users\User\Apps\pp-ce-lifecycle-v3`.
- Worktree `Apps\pp-ce-lifecycle-v3`, rama `ce/lifecycle-v3`, último commit `e2fa4e42`. Plan:
  `vault/plans/ce-lifecycle-v3-work-unit-economics-plan-2026-10-09.md` (APROBADO, opción A + obligación
  OB-APPROVAL-TO-ARM, `ec7f78a0`). Paquetes y recibos: `vault/programs/cognitive-economy/lifecycle/`.
- **En vivo** (rama `feature/knowledge-acquisition` de este repo):

  | Capa | Commit | Qué añade |
  |---|---|---|
  | L1 | `3f9b57cc` | Ligado prospectivo del goal y halt-continue |
  | L3 | `37a5f3c0` | Lease edge, precio por llamada física, steward, COMPLETED solo con recibo |
  | L4 | `ed566db0` | El steward liquida todo worker terminal, aprobación de un solo uso, admisión que lee el goal |
  | L5 | `f3c0f8a0` | Etapa advance del sweep: un registro de aprobación arma la siguiente unidad listada |

- Probado en vivo con ADV2b: el steward liquidó solo al worker y a la renovación (seq 114), y la renovación
  automática tras el disparo del breaker funcionó sin relevo.
- Instalación sin modelo: `tools/lifecycle_stage_merge.py` + `tools/lifecycle_install_apply.ps1` (en el
  worktree). Recibos `install/L{1,3,4,5}-install-receipt.md`.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

## Cadena del ciclo de vida (pendiente, en este orden)

Los paquetes existen pero son de v2. Antes de armarlos hay que rebasarlos: rangos citados, checkpoint primero,
tamaño por llamadas físicas (~2,4× los pasos declarados, primera llamada ~18,5K, +~1,7K por llamada) y una
ruta `route-WU-*.json` por unidad.

| # | Unidad | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 1 | **WU-PKT: rebasar los paquetes y preparar la cadena** | 1 | M | High | PENDIENTE | Unidad armada (no en el panel coordinador, que es el sobrecoste). Rebasa 1C..CLOSE, escribe sus rutas y el front matter `{status: APPROVED, units: [...], packet_dir}` del plan. El registro de aprobación `<state>/approvals/<id>.json` es autoridad del Owner: proponerlo, no escribirlo sin su visto bueno. Con eso, L5 arma la cadena sola. |
| 2 | **WU-1C** goal roots: rechazar un declare solapado, añadir `goal-unroot` | 1 | M | High | PAQUETE v2 | `WU-1C.md` / `WU-1C2.md` (el segundo es el reintento; quedarse con uno). |
| 3 | **WU-1D** `arm --goal` con registro de ligado del lanzador; cierra WU-1 | 1 | M | High | PAQUETE v2 | `WU-1D.md`. |
| 4 | **WU-INST** instalación certificada de hashes aprobados en el checkout vivo | 2 | M | Medium | PAQUETE v2 | `WU-INST.md`. Ya existen las piezas sin modelo (stage merge + install script); la unidad debe absorberlas en vez de reconstruirlas. |
| 5 | **WU-TRIP** gasto sin progreso durable dispara un checkpoint; un hold sobre un worker VIVO lo termina | 1 | M | High | PAQUETE v2 | `WU-TRIP.md`. Cubre el caso visto en ADV2b: 1,05M sin commit. |
| 6 | **WU-FLOOR** Fresh Focus Floor: medir primero, cortar solo el residuo probado | 2 | M | Medium | PAQUETE v2 | `WU-FLOOR.md`. |
| 7 | **WU-GEX** ligado de goal en GEX44: Proof of Need primero | 3 | M | Low | PAQUETE v2 | `WU-GEX.md`. Puede salir del alcance si no hay necesidad medida. |
| 8 | **WU-CLOSE** UNKNOWN falla cerrado, canarios, conocimiento, handoff ctx-rent | 1 | M | High | PAQUETE v2 | `WU-CLOSE.md`. Incluye la promoción a UKDL/CBR (fila 12). |

## Deuda abierta

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 9 | **Presupuesto de la cadena** | 1 | S | High | DECISIÓN DEL OWNER (más adelante) | Quedan 4,92M para una cadena estimada en ~5M. ADV2b costó 1,19M frente a 0,8M previstos. Probablemente falte ~1M. Una subida de tope solo la hace el Owner en una ventana PowerShell aparte (el prefijo `!` pasa por bash, sin TTY y dentro del agente). |
| 10 | **Cierre manual frente a la renovación automática** | 1 | S | High | PENDIENTE | La renovación se lanza en el mismo pase del sweep que deja HALTED al worker; el coordinador cerró a mano a la vez y hubo dos escritores (`0c16b89f`). Hacer que el cierre manual exija `gsd_mission.py hold`, o que la renovación respete un cierre en curso. Encaja en WU-TRIP. |
| 11 | **Mutantes sin probar** | 2 | S | Medium | PENDIENTE | S5d (COMPLETED excluido otra vez; match solo a inicio de línea) y F3. Los de ADV2b sí están probados (3/3 KILLED). |
| 12 | **Promoción a UKDL/CBR + documentación de incidentes (parte S7)** | 2 | M | Medium | PENDIENTE | Envenenamiento del goal por cwd (×2), reservas fantasma, estimador lineal (139K previstos, 449K reales), merge de instalación con CRLF, recibo con PARTIAL en la prosa. |
| 13 | **Ediciones E4a ajenas sin commitear en vivo** | 2 | S | Medium | DE OTRO PANEL | `tools/gsd_mission.py`, `tools/route_admission.py`, `tools/test_session_budget_guard.py` (3.877 bytes). Dueño: cadena cost-collapse (ahora en GEX44). No hacer stash ni reset. |
| 14 | **Pruebas intermitentes** | 3 | S | Low | PENDIENTE | V-SBG-LATENCY (312 ms con el host cargado) y V-LIFE-PREMODEL-TRANSPORT (pasa al repetir). V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED falla siempre (previo). |
| 15 | **Baseline para el script de instalación** | 3 | S | Low | PENDIENTE | Hoy sale con 2 ante cualquier rc≠0 y hay que leer a mano que el fallo es el previo. Un fichero de baseline con los FAIL conocidos lo resolvería. |
| 16 | **Actualizar el plan v3 con la opción 3** | 3 | S | Low | PENDIENTE | El plan aún describe la opción A; añadir el tope 14M y la cadena financiada. |

## Cómo retomarlo

1. Desde un panel nuevo, sin hacer `cd` al worktree (liga el panel al goal): leer este fichero y el plan v3.
2. `python tools/mission_spend.py goal-status --goal ce-lifecycle-v3` para confirmar el saldo.
3. Armar WU-PKT (fila 1) con `gsd_mission.py arm-chain` desde `--cwd` absoluto, con ruta dimensionada por el
   estimador vivo (si `arm-chain` queda retenido, completar con envelope + admit + release, nunca un duplicado).
