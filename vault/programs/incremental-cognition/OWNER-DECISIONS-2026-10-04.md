# Incremental Cognition -- Owner decisions on the owner bundle (2026-10-04) + resume point

Governing documents: the mission's own `vault/programs/incremental-cognition/owner-bundle.md` on branch
`mission/incremental-cognition-run` (GEX44 clone `~/missions/incremental-cognition`, worker worktree
`.claude/worktrees/ic-run`) and `vault/specs/gex44-mission-plane.md` for every GEX44-plane step.
Mission: `m-7a8e9ac0b451` (RUNNING at 21:12 CEST, phase 6, 2/4 plans).

## Resume (a fresh session reads this block first)

1. Gate before ANY item below: mission `m-7a8e9ac0b451` is terminal (or its worker has exited) AND laptop free
   RAM >= 4 GB. Read state with `CPP_CLAUDE_EXE=/home/kobii/.local/bin/claude python3 tools/gsd_mission.py status`
   on GEX44 in `~/.claude/skills/claude-power-pack` (parse from the first `[`).
2. Re-read the bundle at the branch TIP (rows may have been added by plans 06-03 / 06-04) before acting.
3. Order: row 1 -> row 2 -> rows 4-10 + 12 -> row 3 (opportunistic) -> GEX44: row 16 -> rows 13/15 -> row 17
   (T2: spec before the first edit) -> rows 11 / 28 durable state -> rows 20-27 -> row 18 at merge time.
4. Update the Status column below after every sealed item, never only at the end.

Standing limits that the authorization does NOT lift: no quota spend (rows 11, 12); no `/login` on the Owner's
behalf and no retry while a7 reads `LOGIN_EXPIRED` unchanged (row 14); own commits/hunks only, pathspec-scoped;
both GEX44 preflights before every arm (row 19).

## Decisions (normalized; Owner text verbatim below)

| row | decision | status |
|---|---|---|
| 1 | laptop sync after the mission ends and >= 4 GB free | AUTHORIZED, PENDING_GATE |
| 2 | 7 cherry-picks + 6 suites + post-deploy check after the sync, >= 4 GB; own commits/hunks only | AUTHORIZED, PENDING_GATE |
| 3 | capture the real held-mission relay in the laptop live sweep | AUTHORIZED, OPPORTUNISTIC |
| 4-10 | run D-I (+L ranking) in full when the laptop is free; skip a measurement still valid with unchanged dependencies | AUTHORIZED, PENDING_GATE |
| 11 | live champion/challenger: DECLINED for now | DEFERRED_BY_OWNER_QUOTA (not failed, not cancelled; reopen after the next quota reset) |
| 12 | Option B (no quota); Option A only after the reset and only if it adds new information | AUTHORIZED (B) |
| 13 | a7 dry-run; apply only if dry-run/preflight clean and no unexpected diff | AUTHORIZED, CONDITIONAL |
| 14 | a7 `/login` is the Owner's; sole interactive boundary of a7 | OWNER_ACTION |
| 15 | a5 dry-run + apply: clean preflight, drift understood, evidence saved | AUTHORIZED, CONDITIONAL |
| 16 | upgrade GEX44 Node to 24.14.0 (22.23.2 only on a concrete compatibility finding); reversible, validated, no other runtime broken | AUTHORIZED |
| 17a | FIX: a7 hooks must resolve against a7's own owner/manifest, never a5's tree | AUTHORIZED (T2) |
| 17b | FIX: installer deploys every hook script a declared hook needs; contract/regression test | AUTHORIZED (T2) |
| 17c | SCOPE: the bare-git trap rule applies on Windows only; keep the universal pattern only in its correct envelope | AUTHORIZED (T2) |
| 18 | keep `60e7947d`; no squash, no rebase; re-point `PP_COMMIT_FLOOR` only if merge evidence requires it | DECIDED |
| 19 | keep: both preflights before every arm on GEX44 | DECIDED (standing) |
| 20-27 | accept review-fix decisions once `/gsd-verify-work 2/3/4/5` confirms contracts, ownership and PRG are preserved; amend autonomously on a concrete contradiction | AUTHORIZED |
| 22 | read `tools/test_kme_pillars.py` in full before that sign-off | AUTHORIZED, REQUIRED |
| 28 | close as STALE/RESOLVED: the mission is armed on GEX44; update durable state | AUTHORIZED |
| 29-30 | keep BLOCKED_BY_DEPENDENCY; re-evaluate when `cpp-cognitive-economy` lands a reachable commit, without asking again | DECIDED |

## Owner text (verbatim, 2026-10-04)

1. **Row 1:** Sí. Haz el sync del portátil en cuanto termine la misión actual y haya ≥4 GB libres.
2. **Row 2:** Sí. Después del sync y con ≥4 GB libres, haz los 7 cherry-picks, ejecuta las 6 suites y el post-deploy check. Sólo commits/hunks propios.
3. **Row 3:** Sí. Captura la evidencia real del held-mission relay en el live sweep del portátil.
4. **Rows 4–10:** Sí. Ejecuta D–I completos cuando el portátil esté libre. No repitas mediciones ya válidas si las dependencias no han cambiado.
5. **Row 11:** **DECLINE por ahora.** No gastes quota en champion/challenger live hasta el siguiente reset. Déjalo explícitamente como `DEFERRED_BY_OWNER_QUOTA`, no como fallo ni cancelación definitiva.
6. **Row 12:** **Option B.** No gastar quota ahora. Genera la referencia sin una ejecución adicional de modelo; reabrir Option A sólo después del reset si sigue aportando información nueva.
7. **Row 13:** Autorizado el dry-run de a7. Si el dry-run/preflight es limpio y no aparecen diferencias inesperadas, autorizado también el apply.
8. **Row 14:** Requiere mi `/login`. Déjalo como único boundary interactivo de a7; no hagas retries mientras `LOGIN_EXPIRED` siga sin cambio.
9. **Row 15:** Autorizado dry-run y apply de a5 bajo el mismo criterio: preflight limpio, drift entendido y evidencia guardada.
10. **Row 16:** **APRUEBO el upgrade de Node en GEX44. Usa Node 24.14.0** salvo que la Reality Scan encuentre una razón concreta de compatibilidad para preferir 22.23.2. Reversible, validado y sin romper otros runtimes.
11. **Row 17a — hooks de a7 resolviendo a a5:** **FIX.** a7 no debe depender silenciosamente del árbol de a5. Cada environment debe resolver contra su owner/manifiesto correcto.
12. **Row 17b — installer no copia hook scripts:** **FIX.** El installer debe desplegar todo lo necesario para que los hooks declarados sean realmente ejecutables. Añade contract/regression test.
13. **Row 17c — bare-git trap sólo Windows:** **SCOPE IT.** No lo apliques universalmente en GEX44/Linux. Haz explícita su aplicabilidad Windows y conserva el patrón universal sólo en el envelope correcto.
14. **Row 18:** **Mantén `60e7947d`; no squash, no rebase.** Preserva provenance. Sólo re-pointa `PP_COMMIT_FLOOR` si la evidencia del merge demuestra que es necesario; no lo cambies preventivamente.
15. **Row 19:** Mantener. Ambos preflights obligatorios antes de cada arm en GEX44.
16. **Rows 20–27:** **Acepta las review-fix decisions cuando `/gsd-verify-work 2/3/4/5` confirme que preservan contratos, ownership y PRG.** Si el verifier encuentra una contradicción concreta, améndala autónomamente; no vuelvas a pedirme aprobación por cambios rutinarios dentro de ese envelope.
17. **Row 22:** **Sí, lee `test_kme_pillars.py` completo antes del sign-off.** No aceptes el review basándote en el skim.
18. **Row 28:** **CLOSE AS STALE/RESOLVED.** La misión ya está armada en GEX44; actualiza el estado durable para que no siga apareciendo como Owner decision abierta.
19. **Rows 29–30:** Mantén `BLOCKED_BY_DEPENDENCY`. En cuanto `cpp-cognitive-economy` produzca un commit alcanzable, reevalúa automáticamente y continúa; no preguntes de nuevo si no aparece un nuevo boundary de autoridad.
20. **Pregunta final:** **Sí.** Empieza el laptop sync y luego D–I + L automáticamente cuando termine la misión actual y haya ≥4 GB libres. Después continúa con todo el trabajo autorizado que quede READY; no vuelvas a interrumpirme por pasos rutinarios.
