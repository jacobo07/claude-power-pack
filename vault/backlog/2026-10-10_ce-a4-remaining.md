# Backlog — resto de CE Amendment A4 (estate rearm), aparcado por el Owner 2026-10-10

Goal `ce-a4`: cap 16.600.000 (bajado de 21,7M tras F0, `41ed853b`); `goal-status` 2026-10-10: used 3.293.955,
remaining 13.306.045, open 0. Worktree `C:\Users\User\Apps\pp-ce-a4`, rama `ce/a4` (NO mergeada a main).
Plan: `vault/plans/ce-a4-estate-rearm-2026-10-08.md` (secciones 6, 6.1, 6b, 6c). Complementa
`2026-10-10_ce-unify-remaining.md`, sin repetir sus filas.

**Corrección a ese archivo:** en `ce/a4` ya hay commit y recibo de P1 (`5089ddb6`), P2 (`06b56638`), P6
(`578ee31c`), P3 (`1ab26746`, `05627b38`) y P5 (`97d58d8b`). P1, P3 y P5 son *install patches*: falta aplicarlos
al árbol vivo (hooks globales: HR-001, los copia el Owner). P4 no aparece en `ce/a4`.

Hecho en A4: F0 (main `c8fc9f8a`: suelo slim MEDIDO 18.739 frente a 122,6k por defecto); W0 (`83ef9a7b`,
`eb32996a`; 1.451.117 contra un tope de 1,2M, cruzado) + W0-residual (`0a2b9dd4` matriz + gate de dos polos,
`36bacc75` recibo; 389.226 de 480k). P0 probado: worker en segundo plano con commits en el worktree, sin rechazo.

Escala de `/what-now`: prioridad 0-3, esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low. Coste esperado = tabla 6c.

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 1 | **W1a — integrar los deltas de rama** (cost-collapse G1/G2 + dossier + autopsia T2, envelope obligatorio gen3-t1, meter gen3-t3, slim-workers, gen2-completion C3) | 1 | L | Critical | PENDIENTE | Cada familia: su suite verde en HEAD + mutación roja antes. Libera el hold de `m-b76843b319af`. Parte de S9 (envelope obligatorio). ~3,0M, worker STRONG. |
| 2 | **Aplicar al árbol vivo los install patches P1/P3/P5** | 1 | S | High | ESPERA OWNER | Hooks globales (HR-001): el Owner copia; luego la suite pasa en el árbol vivo. |
| 3 | **W1b — binding por defecto del goal, null-config, re-admisión de relevo; regex GOAL_STATE** | 1 | M | Critical | BLOQUEADO (Owner) | Corre en goal `ce-a3b` (1,58M). El Owner copia la regex acotada a `~/.claude/hooks/session_budget_guard.js`. Es la protección contra los sobrecostes de panel coordinador (gen3 ~6,2M; F0 4,65M frente a 1M). |
| 4 | **W1c — Presence U6b-U6d, canarios, pasar a `enforce`, retirar la prosa de flags de `/cpp-gsd-long`** | 2 | M | High | PENDIENTE | Modelo, autocompact y suelo desde el transcript crudo; mutantes V-BASE en rojo. ~1,5M slim. |
| 5 | **W1-gate — canarios 1, 2, 7, 13, 14** | 2 | S | High | PENDIENTE | Tabla de la ola 1 con todas las filas MEDIDAS (tranche_driver). ~0,4M. |
| 6 | **W2a — ejecutar la cola de estate + migrar gsdx-pcc** | 2 | L | High | PENDIENTE | Cierres deterministas (`m-9bee7894f20f` = CLOSE_NO_WORK); migración comparada con el ritmo incumbente de 162,2M. ~2,5M. |
| 7 | **W2b — work extinction, transacción de prueba, compresión de llamadas** | 2 | L | High | PENDIENTE | Incluye S4: gasto del coordinador MEDIDO ≤ 0,6M. ~2,5M. |
| 8 | **W2c — cadena sin padre, ciclo de vida, WAITING sin calor + wake** | 2 | M | Critical | PENDIENTE | Elimina el traspaso manual entre unidades. ~1,0M slim. |
| 9 | **W3 — CBR (S9: "ninguna misión sin presupuesto" con fila real `envelope_auto_assigned`), PGO, UKDL, KV** | 3 | L | High | PENDIENTE | Canario 15 (self-host). Las 3 reglas de consolidación (sección 6b) entran en UKDL cuando ese archivo no tenga cambios de otro panel. ~2,5M. |
| 10 | **Mergear `ce/a4` a main** | 2 | S | High | PENDIENTE | Tras W1a o al cierre; commits por pathspec, nunca un merge a ciegas. |
| 11 | **Limpieza: `m-4bf75e9e8ecc` (W0 duplicado, en hold) y worktree T1c `jobs/62ac7eb5/tmp/wt`** | 3 | S | Low | PENDIENTE | Leer antes de borrar; el diff de T1c ya está en `03e1b0c3`. |
| 12 | **`ce-a4-RESUMPTION.md` desfasado** (no recoge W0r ni P1-P6) | 3 | S | Medium | PENDIENTE | Rehacerlo desde git log y recibos antes de reanudar. |

## Reanudar

Panel nuevo con cwd = el worktree; `mission_spend.py goal-status --goal ce-a4`; `git -C <worktree> log --oneline`.
Armar la siguiente unidad sin recibo vía packet + ruta; solo lanza ADMISSIBLE. Coordinador ≤ 0,6M; un tope cruzado
para la unidad y nunca se sube.
