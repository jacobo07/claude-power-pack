# Backlog — lo que queda de CP50 C2 (recon-factory Phase 7) (2026-10-10)

Origen: panel main de claude-power-pack, Owner "fund it" (financiar C2) y luego "put the rest of the mission in the
backlog" (2026-10-10). **No corre nada**: la misión C2a `m-e6ea9c26d377` está retenida por su cost breaker (owner
hold) y su worker ya no existe (pid 37460 muerto). El sweep no la relanza ni la renueva mientras siga el hold.

## Estado al aparcar

- Goal `cp50-c2`: tope 4.000.000, usado 1.572.766 (settled 570.371, **open 1.002.395** = lease del worker muerto),
  **quedan 2.427.234**. Ligado por cwd a `C:\Users\User\Apps\recon_work\wt_cp50_c2`, host DESKTOP-PMT5BS8.
- Worktree `wt_cp50_c2`, rama `cp50-c2` en `3c86ae2` (= keosdtk-home). **El código de C2a NO está commiteado**:
  `arm_a.py`, `test_arm_a.py` y la edición `targets_for` de `gex44/capsule_build.py` están en STAGED. El commit lo
  rechazó el gate kobishield de snapshot `.ksr_vault` (drift aun en un worktree recién creado, igual que cp50-c1). No se
  usó `--no-verify`. Copia durable: `vault/backlog/2026-10-10_cp50-c2a-partial.patch` (36.141 bytes; `git apply
  --check --reverse --cached` rc=0 contra el índice).
- Recibo `gen3/C2a-receipt.md` (PP `35165d69`): **PARTIAL**, ARM_A_DRILL=7/8, BENCH_DRILL=8/8. FAIL
  V-ARMA-CAPSULE-IDENTITY: `targets_for=[id]` no genera un capsule id distinto de `cap1-984a35109f79`. `prepare` no se
  ejecutó: no hay unidades, cápsula de cohorte ni job; nada enviado a GEX44. Las cápsulas reales no se tocaron
  (última escritura 2026-10-09).
- Financiación y paquetes: PP `e5099387` (dossier `C2A-DOSSIER.md`, `packets/C2a.md`, `route-C2a.json`,
  `C2-RESUMPTION.md`). RF Phase 7: 0 de 4 jobs usados; `RF_CURRENT_PHASE` sigue en 3.
- Piloto = posiciones 1-5 del draw G0: main:80426354, main:8044D4A8, main:804263A4, main:8044064C, main:8042A4D0.

Escala de `/what-now`: prioridad 0-3 (0 = P0), esfuerzo S/M/L/XL, impacto Critical/High/Medium/Low.

## Pendiente (en este orden)

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 1 | **Explicar la varianza de C2a** | 1 | S | High | HECHO 2026-10-10: `gen3/C2a-receipt.md` § Variance. 875k = stop/2, no una previsión; 9 llamadas = 1,50M (bajo el objetivo); el exceso son 3 llamadas no planificadas (2 reintentos de commit por el gate + texto final) | El hold exige "explain the variance and recompute the remaining work before release": processed 2.106.279 frente a estimate 875.000 (breaker 2x = 1,75M), con 8 llamadas. Medir el transcript del worker `58ac31ae-46c6-47a7-9c28-03546fd2584f` (dedupe por message.id). La admisión pedía 1.467.018: el estimador infravaloró ~1,4x. Luego `gsd_mission.py release` o reemplazar con `--supersedes`. |
| 2 | **Commit del código C2a** | 1 | S | High | BLOQUEADO (gate) | Decidir qué hacer con el gate `.ksr_vault` en `wt_cp50_c2` (falla ya en `3c86ae2`, sin cambios en `.ksr_vault`). Precedente C1: copiar los ficheros byte a byte a keosdtk-home; aquí NO, porque es trabajo PARTIAL. Opción: arreglar el snapshot del gate (dueño: KSR) o que el Owner autorice el bypass para este commit. |
| 3 | **C2a-fix: el capsule id debe cubrir `targets`** | 1 | M | High | ARMADO 2026-10-10: misión `m-f5d386e909a5` (supersedes m-e6ea9c26d377, ahora HALTED), paquete `gen3/packets/C2a-fix.md`, ruta ADMISSIBLE need 841.212 / target 1,05M / stop 1,2M, estimate 600k. Causa raíz: `cap_id` = hash del árbol (capsule_build.py:574) y `targets` sólo van al manifiesto (:612); el fix escribe `units/TARGETS.jsonl` antes del hash. Sin commit en wt_cp50_c2: patch a `vault/backlog/2026-10-10_cp50-c2a-fix.patch` | Leer cómo `_stage_and_seal` deriva el id y su rama EXISTS; incluir `targets` en el id sólo cuando `targets_for` no es None (sin `targets_for` la cápsula debe seguir byte a byte igual). Re-ejecutar test_arm_a 8/8 + test_bench 8/8, luego `arm_a.py prepare --first 1 --last 5` (local, sin send). Lease pequeña: la mayor parte de C2a ya existe. |
| 4 | **C2b: piloto en GEX44** | 1 | M | High | PENDIENTE | Pre-checks (PINS, slot_ledger, GEX44 libre), `RF_CURRENT_PHASE = 7` en stage.py (commit), send del job de C2a (job 1 de 4), wait, repatriate, `candidate.py judge <job_id>`, `arm_a.py records --first 1 --last 5`. Recibo = tabla de coste por función. La fase se lee al enviar (stage.py:1136), así que un build local no gasta cupo. |
| 5 | **C3: proyección de CP50** | 1 | S | Critical | PENDIENTE | Coste CP50 = p50/p95 por función del piloto x 50 x brazos + presupuesto de jobs GEX44. El Owner financia CP50 desde ese número (plan D5). |
| 6 | **Presupuesto restante** | 1 | S | High | DECIDIDO 2026-10-10: la "reserva fantasma" era gasto real (autopsia: worker 2.106.279); liquidada con goal-settle, quedan 1.893.721. C2a-fix cabe sin subir el tope (stop 1,2M + cierre ~0,65M = 1,85M peor caso). C2b NO cabe después: subir el tope con `goal-declare --owner` en TTY, dimensionado con lo medido en C2a-fix | Quedan 2.427.234, de los que 1.002.395 son una reserva fantasma del worker muerto. Si no se libera, C2a-fix + C2b (~1,5M medido en P3b-2) puede no caber. Subir el tope = `goal-declare --owner` en una ventana PowerShell aparte (TTY). |
| 7 | **Merge de cp50-c2 en keosdtk-home** | 2 | S | Medium | PENDIENTE | Cuando C2 esté completo: sólo arm_a.py, test_arm_a.py, capsule_build.py, por pathspec, nunca rutas `.ksr_vault`. |

## Deuda abierta

| # | Tarea | P | Esf. | Impacto | Estado | Qué falta / cómo se cierra |
|---|---|---|---|---|---|---|
| 8 | **4 model matches sin promover** | 2 | M | Medium | PENDIENTE | `capsule_build.py:46` `MODEL` (main:80296024, main:803EEBD0, main:80154F40, main:802932F4). La cápsula P3b se construyó para 298 unidades; P3b-2 promovió 294. Es la deuda "model matches" que el ROADMAP de Phase 3 dejaba como UNKNOWN. |
| 9 | **Reservas fantasma** | 2 | S | Medium | PENDIENTE | rf-p3b 169.870; cp50-c1 150.000; cp50-c1b 615.729 (leak); gsdx-factory 232.321; rf-p3b2 751.885; cp50-c2 1.002.395. |
| 10 | **Metadato de fase en candidate** | 3 | S | Low | PENDIENTE | `stage.build` escribe `cand_selection.phase = CURRENT_PHASE` (match_accel, 4) también para jobs del RF root. Sólo metadato; el cupo se cuenta bien al enviar. |
| 11 | **Rama cp50-c1 con ficheros staged rancios** | 3 | S | Low | PENDIENTE | bench.py y test_bench.py ya están en recon `9929c29`; retirar el worktree `wt_cp50_c1` cuando nadie lo use. |

## Cómo retomarlo

1. Desde un panel nuevo, **sin `cd`/Set-Location a `wt_cp50_c2`** (liga el panel al goal): leer este fichero,
   `gen3/C2-RESUMPTION.md` y `gen3/C2a-receipt.md`.
2. `python tools/mission_spend.py goal-status --goal cp50-c2` y `gsd_mission.py status` de `m-e6ea9c26d377`.
3. Fila 1, luego fila 2, luego fila 3 como lease nueva (dossier + paquete + ruta + admit), nunca en el panel
   coordinador.
