# Backlog — resto de la misión ce-unify (2026-10-10)

Origen: misión `m-5a42ed8f28cc` (goal ce-unify, cap 1,2M, COMPLETED; WU-U1 = solo análisis). Sus artefactos
están en la rama `ce/unify` (worktree `C:\Users\User\Apps\pp-ce-unify`, HEAD `36b3cc9f`), NO en el árbol vivo:
- plan final: `vault/plans/ce-unify-final-plan-2026-10-09.md` (`91aa46d2`)
- ledger de obligaciones (50 filas: ALREADY-DONE 2, EXTEND 19, OWNED 16, REJECT 7, UNKNOWN 6):
  `vault/programs/cognitive-economy/unify/obligation-ledger.md`
- incidente de coste: `vault/programs/cognitive-economy/unify/incident-ce-lifecycle-v2-overrun.md`
- recibo: `vault/programs/cognitive-economy/unify/WU-U1-receipt.md` (`68d62f23`, `36b3cc9f`)

No es un programa nuevo (HR-NOVELTY-001): cada fila tiene ya un goal dueño. No se pide autoridad por encima de
los caps existentes. Presupuesto por unidad = llamadas × 18K + 15K × llamadas × (llamadas−1)/2 (modelo medido
de worker, WU-S1/S3). Financiación medida por el dossier a las 11:30Z del 2026-10-09: ce-a4 14.654.307 − 563.845
abiertos = 14.090.462 libres; ce-lifecycle-v3 1.434.095 − 1.896.885 = −462.790. Re-medir con
`tools/mission_spend.py goal-status --goal <g>` antes de armar.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

| # | Tarea | P | Esf. | Impacto | Estado | Dueño | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|---|
| 1 | **P1 — goal-autopsy al árbol vivo** (ledger D-01) | 1 | S | High | PENDIENTE | ce-a4 W1a | Solo existe en la rama `ce/a3b-r` (`tools/mission_spend.py` + `test_goal_autopsy.py`, 10/10 allí). Hecho = `mission_spend.py goal-autopsy` en vivo reproduce la tabla de ce-a3b y la suite pasa en HEAD. 6 llamadas → 333.000. |
| 2 | **P2 — plegar las filas EXTEND en los packets de ce-a4** | 1 | S | Medium | PENDIENTE | ce-a4 W0/W1/W3 | Filas D-04, 07, 09-12, 17, 18, 20, 22, 24, 26, 27, 29, 32, 34, 37, 46. Hecho = cada fila aparece como línea con nombre en un packet dueño; ningún tipo de fichero nuevo. 5 llamadas → 240.000. |
| 3 | **P6 — decidir las filas UNKNOWN** (D-06, 08, 15, 16, 31, 40) | 1 | S | Medium | PENDIENTE | ce-a4 W0 | Con el ledger y una misión autopsiada (necesita #1). Hecho = cada fila pasa a OWNED/EXTEND/REJECT con una línea medida, o sigue UNKNOWN nombrando el número que falta. 5 llamadas → 240.000. |
| 4 | **P3 — cláusulas de Cognitive CI**: delta de hot-tokens (D-28), cuota de meta-trabajo (D-22), disparador de incidente de tokens (D-24) | 2 | M | High | PENDIENTE | ce-a4 W3 | Sobre `cep_gen2` + `reachability.py`. Hecho = cada cláusula tiene un test con violación plantada que se pone en rojo. 8 llamadas → 564.000. |
| 5 | **P5 — cláusula CI: un Close que usa `arm` sin `--no-launch` falla** | 2 | S | High | PENDIENTE | ce-a4 W3 | Causa: el Close de R5c (`m-447ca8005684`) lanzó dos misiones sin packet, 866.883 medidos. Barrer los sitios de lanzamiento de ENTRY_MATRIX. Hecho = un Close plantado con `arm` sin el flag se pone en rojo. 4 llamadas → 162.000. |
| 6 | **P4 — confirmar que L1 acota el settle retroactivo** (residuo del incidente) | 2 | S | High | ESPERA AUTORIDAD | ce-lifecycle-v3 (unidad S) | Con L1 `3f9b57cc` y el journal seq 91-94. Hecho = repetir un bind por Set-Location en una rama con L1 registra 0 de settle retroactivo. 4 llamadas → 162.000. **Sin fondos** (v3 en −462.790): WAITING_FOR_AUTHORITY hasta que remaining − open de v3 cubra 162.000. |
| 7 | **Lease de ce-unify sin liquidar** | 2 | S | Medium | ASIGNADA | ce-lifecycle-v3 S5 | goal-status: used 750.000, open 750.000, settled 0 con la misión COMPLETED. No liquidar a mano: es el primer canario vivo del cierre certificado de S5 (plan v3, commit `48a0bc02`). |
| 8 | **Cifra del sobrecoste de lifecycle-v2 sin cuadrar** | 3 | S | Low | PENDIENTE | ce-lifecycle-v3 S7 (incidente) | La tabla da 33,02M y el settle del journal 32,58M; WU-U1 no leyó el journal. Cuadrar desde el journal antes de citar la cifra en UKDL. |
| 9 | **RESUMPTION.md de lifecycle con cabecera ce-lifecycle-v2 en la ruta v3** | 3 | S | Low | PENDIENTE | ce-lifecycle-v3 | Lo señala el recibo de WU-U1; los packets v3 no se leyeron. Corregir la cabecera para que un panel nuevo no reanude el linaje equivocado. |

Total P1-P6: 1.701.000 (ce-a4 1.539.000 con fondos; ce-lifecycle-v3 162.000 esperando autoridad).

## Orden recomendado

1. **#1, #2, #3** (P1, P2, P6): #3 necesita la autopsia de #1.
2. **#4, #5** (P3, P5).
3. **#6** (P4) solo cuando v3 tenga fondos.
4. **#7-#9** los cierran los dueños de v3; aquí solo constan para que no se pierdan.

## Reglas para cada unidad (del plan final)

Rutas absolutas y `git -C`, nunca Set-Location a otra raíz `Apps\pp-*`; todo `arm` con `--no-launch`; parar a los
dos fallos; los caps no se suben. Armar por la gramática compilada (dossier + packet + envelope + gate).

## Pregunta abierta al Owner

- El trabajo de ce-unify vive solo en la rama `ce/unify`. ¿Se publica al árbol vivo, o lo absorbe ce-a4 al
  plegar #2?
