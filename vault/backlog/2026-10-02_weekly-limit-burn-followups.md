# Backlog — seguimiento del incidente de límite semanal (2026-10-02)

Origen: `vault/plans/weekly-limit-burn-rca-2026-10-02.md` (90 % del límite semanal en 40 h 40 min).
Ya cerrado en esta sesión: lector de uso corregido y reconciliado (`c05cfa3`), registro del
incidente (`8a4f036`), trigger económico de rollover (`139b19d`) y exclusión de workers Ralph sin
marcador (`65bb95b`). Lo de abajo es lo que queda abierto.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 1 | **Medir el ahorro real del rollover económico** | 0 | S | High | PENDIENTE (esperando datos) | Tras unas horas de uso: filas `rollover_econ_evaluating`, `rollover_kclear_asked route=economic` y `rollover_econ_withdrawn` en el ledger de `gsd_long_run`; contexto medio por llamada con `token_ground_truth.window_usage` frente a la ventana del 2026-10-02 en los mismos proyectos. Si no baja, revertir (`CPP_ROLLOVER_ECONOMIC=0` o revert de `139b19d`/`65bb95b`). |
| 2 | **Alarma semanal ponderada** en lugar de la de solo salida | 0 | M | Critical | PENDIENTE | `cost_gate.weekly_burn` mide solo output (≈10-15 % del peso estimado). Nueva señal: llamadas/h, relectura de caché/h, sesiones vivas y proyección al límite. Debe disparar pronto al reproducir las horas reales del incidente. Arreglar también el timeout de 40 s que falla en silencio (`modules/wrapper/prelaunch.py:253`) y los tres barridos completos del corpus. Calibración: lectura del medidor de una semana anterior (pregunta abierta al Owner) o, si no, las semanas medidas en RCA §3. |
| 3 | **Comando de informe de uso por ventana/estate** | 1 | M | High | PENDIENTE | Hacer alcanzable lo que esta auditoría hizo a mano en scripts: totales, Pareto por sesión/proyecto, desglose por modelo, subagentes por `agentType`/`.meta.json`, cercanía a prompts humanos (interactivo vs desatendido). Sobre `window_usage` (dedupe entre archivos, subagentes incluidos). Puede fusionarse con #2. |
| 4 | **Transcripts de GEX44 en el ledger** | 1 | M | High | PENDIENTE | El Owner confirma que GEX44 usa (casi siempre) la misma cuenta; no se ha leído nada de allí. Medir su parte de la ventana con el mismo lector, por SSH y solo lectura. |
| 5 | **Pared del 45 % en workers Ralph sin marcador** | 1 | S | High | SIN VERIFICAR | La pared también decide por `mission_id` del marcador de autorun, que los workers `claude --bg` no tienen (sesión `4ec01521`). Comprobar si la pared les pide `/kclear` en vez del relevo de misión; si es así, reutilizar `_mission_owner()`. |
| 6 | **Modelo de los subagentes de ejecución** | 1 | M | High | NO PROBADO | El 53,5 % de la relectura de subagentes viene de agentes sin `model` que heredan Opus (general-purpose "Execute plan", gsd-executor). A/B de calidad Sonnet vs Opus antes de cambiar nada; no aplicar a misiones en curso sin el visto bueno del Owner. |
| 7 | **Recortar el suelo de gobernanza (~29k por llamada)** | 1 | L | High | PROPUESTA | CLAUDE.md global + `~/CLAUDE.md` + reglas ≈ 115k caracteres que se cargan en todas las llamadas, también las de subagentes (≈11 % de la relectura, estimado). Opciones: `paths:` en reglas de dominio, mover más reglas a skills (como el 29/30-09). Solo con ablación de calidad; no debilitar doctrina protegida. |
| 8 | **Suelo de los subagentes (95k de mediana)** | 2 | L | Medium | PENDIENTE | Un subagente arranca con casi todo el contexto del padre. Ver qué puede reducir Agent Capability Virtualization (S5+) o un contexto mínimo para agentes de ejecución. |
| 9 | **Concurrencia: CO-08 solo informa** | 2 | S | High | DECISIÓN DEL OWNER | El aviso decía "29 sesiones calientes, límite blando 2" y no frena nada. Decidir si sigue informativo, avisa más fuerte o bloquea nuevas sesiones por encima del límite. |
| 10 | **UKDL y baseline** | 1 | S | Medium | PENDIENTE | Hard Rule: el input en caché no es gratis; uso sin atribuir ≠ 0. Trap: una tasa alta de acierto de caché no significa contexto barato (la RCA de junio cayó aquí). Trap: deduplicar por archivo no basta (3.044 llamadas en dos archivos). Trap: lanzar equipos grandes de agentes durante una emergencia de cuota. Process Rule: incidente de cuota → ledger del estate → Pareto → atribución → mitigación segura → prevención estructural. Propagar a CBR/UBC. |
| 11 | **Coste por avance verificado** | 2 | M | Medium | PENDIENTE | Llamadas por commit / obligación cerrada en las sesiones más caras; distinguir valor entregado, aprendizaje, inversión reutilizable y desperdicio (no hecho en la RCA). |
| 12 | **Tests desactualizados de la suite GSD** | 2 | S | Low | DE OTRO PANEL | `V-GSDLR-WD-ROLLOVER-ASKS-KCLEAR` y `V-GSDLR-WD-TEXT-NAMES-ROUTE` fallan igual en un HEAD limpio: esperan una pulsación de `/kclear` que el watchdog dejó de enviar el 29-09 (`route="self"`). Actualizar al comportamiento actual. |
| 13 | **Fuga de aislamiento en `test_rollover_active_path`** | 3 | S | Low | PENDIENTE | Deja flags `rollact-*` en el `%TEMP%` real (se vio `claude-ctxwd-rollecon-rollact-*.json`). Aislar como `test_rollover_economic`. |

## Orden recomendado

1. **#2 y #1**: la alarma es lo que habría avisado antes del 90 %, y #1 decide si el arreglo
   del rollover se queda.
2. **#5**: riesgo vivo sobre las misiones que el Owner quiere intactas; es barato de comprobar.
3. **#4 y #3**: cierran los huecos de atribución (remoto) y convierten la auditoría en algo
   que se responde solo.
4. **#7, #6 y #8**: las palancas grandes de suelo y modelo, todas con prueba de calidad antes.

## Pregunta abierta al Owner

¿Qué porcentaje marcaba el medidor semanal el jueves anterior a mediodía, o se llega al límite
todas las semanas? Fija los umbrales de #2.
