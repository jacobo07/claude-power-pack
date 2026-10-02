# Backlog — economía de tokens, ola 2 (2026-10-03)

Origen: investigación de la sesión ab73b303 (Owner: "next level research and massive brainstorming").
Síntesis: `wiki/syntheses/token-economy-brainstorm.md` (commit `dfe30814`); ola 1:
`wiki/syntheses/token-economy-levers.md` (`084b46db`). Instrumentos (cero cuota, 7 días de
transcripts): `wiki/tools/token_economy_{deep,listings,coldstart,coldstart_bydir,prefix_stability,ttl_net}.py`
con su `.2026-10-02.out`. Complementa `2026-10-02_weekly-limit-burn-followups.md`; donde una
tarea ya está allí, esta fila la referencia en vez de duplicarla.

Los dólares son estimación a precio de lista, no el medidor semanal; las cotas se solapan y no se
suman.

## Hallazgos que motivan las filas

- **El precio, más que el volumen.** Escribir un token en caché cuesta ~40× más que leerlo; la
  mayoría de las escrituras son evitables.
- **Los arranques de sesión empiezan casi de cero**: la primera llamada escribe el 85 % de su
  contexto (91 % en subagentes). Leerlo en vez de escribirlo: hasta 12,4 % del gasto. Las carpetas
  de proyecto normales comparten ~32k; las de worktree/misión (~550 sesiones) solo ~2,5k.
- **Volver de una pausa causa la mayoría de las reconstrucciones**: 224 de 307 tras > 1 h inactivo
  (caché caducada), ~$541.
- **TTL de 5 min descartado**: es configurable (`CLAUDE_CODE_PROMPT_CACHE_TTL`) pero costaría
  ~$1.262 más por semana (1.327 llamadas vuelven a los 5-60 min). La fila de TTL de la ola 1 queda
  retirada.
- **280 de 319 skills listadas no se invocaron** en 7 días; su descripción viaja en cada llamada.
- Menores: thinking = 27,6 % de la salida (effort ya `medium`); 30 % de los Read reabren un fichero
  ya leído; ~20 llamadas por prompt con casi nada de batching; los avisos de hooks cuestan ~$200 /
  semana en relecturas.
- **Corrección registrada:** el primer desglose atribuía ~45 % a salidas de hooks y snapshots de
  prompt; esos registros no llegan al modelo. Sustituido por un ajuste contra el crecimiento medido
  del contexto (R² 0,20, aproximado).
- Aviso del Stop (2026-10-03): `[claude_md_linter] WARN: ~/.claude/CLAUDE.md = 39812 chars (>= 38000)`
  — "Reduce by retiring a rule, not by externalizing a trigger". Y `FIOS IRR: ... tokens unmeasured`.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 1 | **Rollover al volver de inactividad > 1 h** (A1) | 1 | S | High | DECISIÓN DEL OWNER (¿redactar ya?) | La caché ya está fría, así que un epoch fresco desde la cápsula cuesta menos que reescribir ~300k. Cota ≤ 6,5 % (los $541 de reescritura) más relecturas posteriores menores. Es del dueño del rollover (SPEC-ECON-ROLLOVER): entregar como propuesta (paso S6 de la misión state-centric), sin editar `tools/rollover.py` ni `context-watchdog.py`. |
| 2 | **Ocultar las skills no usadas** (B1) | 1 | S | Medium | DECISIÓN DEL OWNER | `skillOverrides: "name-only"` en settings.json para las 280 no invocadas; mantener las 39 usadas y toda skill nombrada en una tabla de activación de un CLAUDE.md. settings.json es paso del Owner (HR-001). Cota ≈ -5k tok/llamada ≈ 1,5-2 %. Verificar una semana después con `token_economy_coldstart.py` [K] y un floor probe. Página: `wiki/improvements/hide-unused-skills.md`. |
| 3 | **Dieta de avisos de hooks** (B3) | 1 | S | Medium | PENDIENTE | `additionalContext` repetido (Tower baseline en cada prompt, GK-12 en cada Grep/PowerShell, skill advisor en Write, cross-project baseline en PowerShell) → una vez por sesión y luego un puntero de una línea, como `power-pack-reminder.js`. Primero un censo por hook. ~$202 / 7 d. Código propio de PP, el cambio más pequeño. Página: `wiki/improvements/hook-injection-diet.md`. |
| 4 | **Experimento de caché de arranque** (A3) | 1 | S | High | DECISIÓN DEL OWNER (cuota antes del reset 2026-10-07 17:00Z) | Dos sesiones por brazo en la misma carpeta, con y sin `--exclude-dynamic-system-prompt-sections` (presente en CLI 2.1.288); comparar la lectura de caché de la primera llamada de la segunda sesión. ~4 llamadas pequeñas. Decide si existe una palanca de hasta 12,4 %. Página: `wiki/improvements/cold-start-cache-sharing.md`. |
| 5 | **Calibrar cómo cuenta el límite semanal las lecturas de caché** (E1) | 1 | M | Critical | PENDIENTE | Un antes/después controlado del % semanal frente a tokens de transcript, para ordenar estas palancas por medidor y no por dólares. Comparte la calibración con la fila #2 del backlog 2026-10-02. |
| 6 | **Arranque estable en worktrees/misiones** (A2) | 2 | S | Medium | PENDIENTE | ~550 sesiones comparten solo ~2,5k frente a ~32k. Diff de los `prompt_snapshot` de dos epochs consecutivos en `wt_keosdtk_home` (cero cuota); si es texto por epoch en el system prompt, moverlo al primer mensaje de usuario. ~1,5 %. Dueño: Ralph / `gsd_epoch`. |
| 7 | **Origen de los cambios de modelo a mitad de sesión** (A4) | 2 | S | Low | PENDIENTE | 36 reconstrucciones, ~$88. Candidatos: advisor model, `opusplan`, skills con `model:` en frontmatter. |
| 8 | **TTL de 5 min** (A5) | 3 | S | Low | DESCARTADO | Medido: neto +$1.262 / semana. No aplicar `CLAUDE_CODE_PROMPT_CACHE_TTL=5m`. Fila conservada para que nadie lo re-derive. |
| 9 | **Relecturas de ficheros (30 % de los Read)** (B8) | 2 | S | Medium | PENDIENTE | Separar relecturas tras edición de las inútiles; paginar PDFs; contact sheets en vez de imágenes fotograma a fotograma. El hook anti-thrash solo cubre relecturas sin cambios. |
| 10 | **Batching de herramientas independientes** (C1) | 3 | M | Medium | DECISIÓN DEL OWNER | ~1,1 herramientas por llamada y ~20 llamadas por prompt. Choca con los topes de paralelismo de la doctrina Windows (≤ 4 Read, Agent en solitario); decidir si se relajan donde el puente es fiable. |
| 11 | **Identificar los ~317 tok/llamada no registrados** (B13) | 2 | S | Medium | PENDIENTE | El ajuste encuentra una inyección fija por llamada que el transcript no guarda (hasta ~9 % de la relectura). Nombrarla antes de actuar. |
| 12 | **Effort bajo para subagentes mecánicos** (D2) | 2 | S | Low | NO PROBADO | Thinking = 27,6 % de la salida (≈ 3,6 % del gasto). Junto con la fila #6 del backlog 2026-10-02 (modelo de subagentes); A/B de calidad antes. |
| 13 | **Llevar los seis instrumentos al usage index** (E2) | 2 | M | Medium | PENDIENTE | Hoy son scripts sueltos en `wiki/tools/`; sin medidor recurrente una palanca regresa en silencio. Fusionable con la fila #3 del backlog 2026-10-02 (comando de informe). |
| 14 | **CLAUDE.md global en 39.812 caracteres** | 2 | S | Medium | DECISIÓN DEL OWNER | Linter: ≥ 38.000; el aviso del harness salta a 40.000. Reducir retirando una regla, no externalizando un trigger. Relacionado con la fila #7 del backlog 2026-10-02 y `wiki/improvements/always-loaded-prefix-audit.md`. |
| 15 | **FIOS IRR informa "tokens unmeasured" en cada Stop** | 3 | S | Low | PENDIENTE | Ver si su campo de tokens puede leer del usage index en vez de quedar sin medir. |

## Orden recomendado

1. **#1, #3 y #2**: el dinero más barato por unidad de esfuerzo (precio y prefijo), sin cuota.
2. **#4 y #5**: deciden el tamaño real de la palanca mayor y cambian la unidad de medida a la del
   medidor.
3. **#6, #7, #11**: investigación de cero cuota que puede abrir más palancas.
4. El resto cuando una de las anteriores lo pida.

## Preguntas abiertas al Owner

- ¿Redacto ya la propuesta de rollover por inactividad para el dueño del rollover (#1)?
- ¿Puedo gastar unas pocas llamadas de cuota en el experimento de caché de arranque antes del reset (#4)?
- ¿Construyo la lista de skills a conservar para `skillOverrides` (#2)?
