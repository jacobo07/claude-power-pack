# PP Globalization Status — 2026-05-29T11:14:24Z

> Sealed: 2026-05-29 (BL-GLOB-001). Read-only audit. Empirically
> verified from `/tmp` (external dir) with `sys.path` injection
> where needed. No assumptions: every row has a real probe result.

## RESUMEN EJECUTIVO

| Categoría | Conteo | % |
|-----------|--------|---|
| Total assets PP inventariados (matriz) | 36 | 100% |
| Globalizados Y auto-activos | 13 | 36% |
| Globalizados PERO requieren invocación manual | 14 | 39% |
| Importables pero requieren `sys.path` hack | 7 | 19% |
| NO globalizados (PP cwd-only) | 2 | 6% |

**Hallazgo principal**: el repo `claude-power-pack` está **dentro** de
`~/.claude/skills/`, por lo que sus módulos son técnicamente "globales"
vía path. La distinción real es entre **auto-activos** (hooks que
disparan en cualquier repo sin intervención) vs **manualmente
invocables** (importables pero requieren que algo sepa de ellos).

## MATRIZ COMPLETA

| Asset | Tipo | Global? | Auto-activo? | Desde otro repo? | ROI globalizar | Bloqueante |
|-------|------|---------|--------------|------------------|----------------|-----------|
| `hooks/auto-test-gate.js` | hook | ✅ | ✅ | ✅ | n/a (ya global) | — |
| `modules/zero-crash/hooks/tty-restore.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `hooks/mark-live-session.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `hooks/background-verifier.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `tools/jit_skill_loader.py` | hook | ✅ | ✅ | ✅ | n/a | — |
| `modules/zero-crash/hooks/terminal-slot-recorder.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `hooks/zero-command-bootstrap.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `hooks/first-time-project.js` | hook | ✅ | ✅ | ✅ | n/a | — |
| `~/.claude/agents/omni-singularity.md` | agent | ✅ | ⚡ | ✅ | n/a | sólo dispara si Owner lo invoca |
| `~/.claude/skills/lateral-thinking/` | skill | ✅ | ⚡ | ✅ | n/a | — |
| `~/.claude/skills/claude-power-pack/` | skill | ✅ | ⚡ | ✅ | n/a | — |
| `~/.claude/skills/governance-overlay/` | skill | ✅ | ⚡ | ✅ | n/a | — |
| `~/.claude/CLAUDE.md` PP refs | text | ✅ | ✅ | ✅ | n/a | — |
| `tools/tco_compact_gate.py` | tool | ✅ | ⚡ | ✅ | medio | sin auto-warning hook |
| `tools/uqf_audit.py` | tool | ✅ | ⚡ | ✅ | crítico | sin pre-commit gate |
| `tools/verify_spp.py` | tool | ✅ | ⚡ | ✅ | medio | manual `python` invocation |
| `tools/budget_monitor.py` | tool | ✅ | ⚡ | ✅ | bajo | Owner usa `--quiet` manual |
| `modules/osa/dispatcher.py` | tool | ✅ | ⚡ | ✅ | alto | sólo dispara fire_async desde PP-deploy |
| `modules/osa/osa_command.py` | tool | ✅ | ⚡ | ⚡ | medio | requiere cwd=PP para `-m` |
| `modules/osa/throttle.py` | tool | ✅ | ⚡ | ✅ | bajo | invocado por osa_command |
| `modules/osa/gpu_eyes.py` | tool | ✅ | ⚡ | ✅ | bajo | invocado por dispatcher |
| `modules/monitoring/observe` | module | ✅ | ⚡ | ✅ | alto | manual `-m` necesario |
| `modules/deployment/deploy.py` | module | ✅ | ⚡ | ✅ | n/a | invocado vía stdin JSON |
| `modules/rollback/rollback.py` | module | ✅ | ⚡ | ✅ | n/a | idem |
| `modules/backup/backup.py` | module | ✅ | ⚡ | ✅ | n/a | idem |
| `commands/*.md` (35 slash cmds) | command | ⚡ | ⚡ | ⚡ | medio | sólo desde PP cwd vía Claude Code |
| `~/.claude/commands/*.md` (28 globales) | command | ✅ | ⚡ | ✅ | n/a | — |
| `modules.uqf.auditor.UQFAuditor` | module | ⚡ | ❌ | ⚡ | crítico | requiere sys.path hack |
| `modules.uqf.anti_patterns.run_all` | module | ⚡ | ❌ | ⚡ | crítico | requiere sys.path hack |
| `modules.uqf.principles` | module | ⚡ | ❌ | ⚡ | medio | idem |
| `modules.osa.never_again` | module | ⚡ | ❌ | ⚡ | medio | idem |
| `modules.code_review` | module | ⚡ | ❌ | ⚡ | alto | idem |
| `tools.tis.get_session_id` | module | ⚡ | ✅ | ⚡ | n/a | tis_log_call decora invocaciones desde PP-internal |
| `tools.ceps.record_error` | module | ⚡ | ❌ | ⚡ | alto | idem |
| `rules/` (common+python+elixir, 17 archivos) | rules | ❌ | ❌ | ❌ | medio | no en `~/.claude/rules/` |
| `vault/osa/config.json` schema | config | ❌ | ❌ | ❌ | n/a | per-proyecto OK |

**Leyenda**:
- Global?  ✅ = en path global / ⚡ = parcial (requiere sys.path) / ❌ = sólo PP
- Auto-activo?  ✅ = dispara sin intervención / ⚡ = requiere comando manual / ❌ = sólo PP repo
- Desde otro repo?  ✅ = funciona / ⚡ = funciona con sys.path / ❌ = falla

## ACTIVOS GLOBALIZADOS Y AUTO-ACTIVOS ✅ (13)

8 hooks PP-localizados que `~/.claude/settings.json` despacha en
**cualquier repo** del Owner, sin intervención:

| Hook | Event | Dispara en |
|------|-------|------------|
| `hooks/auto-test-gate.js` | PreToolUse Bash/PowerShell | toda invocación Bash/PS |
| `modules/zero-crash/hooks/tty-restore.js` | PostToolUse Bash | toda invocación Bash |
| `hooks/mark-live-session.js` | Stop + SessionStart | cada Stop/SessionStart |
| `hooks/background-verifier.js` | Stop | cada Stop |
| `tools/jit_skill_loader.py` | UserPromptSubmit | cada prompt del Owner |
| `modules/zero-crash/hooks/terminal-slot-recorder.js` | SessionStart | inicio de sesión |
| `hooks/zero-command-bootstrap.js` | SessionStart | inicio de sesión |
| `hooks/first-time-project.js` | SessionStart | proyectos nuevos |

3 skills/agents instalados globalmente, accesibles vía
Skill tool / FleetView desde cualquier sesión:
- `~/.claude/skills/lateral-thinking/SKILL.md`
- `~/.claude/skills/claude-power-pack/SKILL.md`
- `~/.claude/agents/omni-singularity.md` (M7 del ciclo OSA)

2 mecanismos de texto-injection:
- `~/.claude/CLAUDE.md` (referencia 5+ paths PP-localizados)
- `~/.claude/skills/governance-overlay/` (auto-load con dev skills)

## ACTIVOS CON GLOBALIZACIÓN PARCIAL ⚡ (21)

**14 tools/modules CLI-invocables globalmente** (vía path absoluto):

| Asset | Probe (desde /tmp) |
|-------|---------------------|
| `tools/tco_compact_gate.py` | OK (devolvió `5%` con TIS data) |
| `tools/uqf_audit.py` | OK (importable, score=100% en test) |
| `tools/verify_spp.py` | OK (13/13 strict) |
| `tools/budget_monitor.py` | OK |
| `modules/osa/dispatcher.py --check` | OK (active=true reason=T4_SESSION_TIMER) |
| `modules/osa/throttle.py --status` | OK (`max_daily=150`) |
| `modules/osa/gpu_eyes.py` | OK (status=SKIPPED, visual_qa_passed=null) |
| `modules.monitoring.observe --once` | OK (status table) |
| `modules.deployment.deploy` (stdin JSON) | OK |
| `modules.rollback.rollback` (stdin JSON) | OK |
| `modules.backup.backup` (stdin JSON) | OK |
| `modules.osa.osa_command --status` | ⚡ (requiere cwd=PP para `-m`) |
| `commands/*.md` (35 PP slash cmds) | ⚡ (PP cwd-only en Claude Code) |
| `~/.claude/commands/*.md` (28 globales) | OK (audit-all, ultra, kclear, etc.) |

**7 modules importables vía sys.path hack**:

| Módulo | Provee | Probe |
|--------|--------|-------|
| `modules.uqf.auditor.UQFAuditor` | code-review pipeline | OK score=100% |
| `modules.uqf.anti_patterns.run_all` | AST detectors | OK fired 2/7 detectors |
| `modules.uqf.principles` | 9 ECC principles | OK |
| `modules.osa.never_again` | inject/top_recurring/query | OK |
| `modules.code_review` | ECC code-review helpers | OK |
| `tools.tis.get_session_id` | session id + token log | OK |
| `tools.ceps.record_error` | error pattern registry | OK |

## ACTIVOS NO GLOBALIZADOS ❌ (2)

| Asset | Por qué | ROI |
|-------|---------|-----|
| `rules/` (common+python+elixir, 17 archivos) | no están en `~/.claude/rules/` ni referenciados por hook/skill global | medio (ECC doctrine cross-project) |
| `vault/osa/config.json` schema | local sólo a este repo PP | bajo (per-proyecto OK por diseño) |

## AUTO-INTERVENCIÓN POR EVENTO

### Al escribir código Python en cualquier repo
- ❌ UQF audit NO dispara automáticamente
- ❌ anti_patterns NO se chequea pre-commit
- ✅ `auto-test-gate.js` corre (PP-localizado, global)
- ⚡ `jobs-woz-gatekeeper.js` corre (token budget enforcement)

### Al hacer deploy
- ✅ Si Owner llama `python <PP>/modules/deployment/deploy.py`: el
  post-deploy `fire_async()` OSA hook dispara
- ❌ El `/deploy` slash command global está sólo en PP commands,
  no en `~/.claude/commands/`
- ❌ Si el repo externo usa su propio deploy script (vercel, gh
  workflow, mix release): OSA no se entera

### Al detectar error
- ✅ CEPS se puede invocar manualmente
- ❌ Detección de errors no está auto-cableada a CEPS desde repos
  externos
- ⚡ `bug-hunter-learning.js` dispara en PostToolUse Bash (global)

### Al iniciar sesión
- ✅ 13 hooks SessionStart disparan automáticamente
- ✅ `jit_skill_loader.py` inyecta skills relevantes
- ✅ `token-shield-refresh.js`
- ✅ `lazarus-livesnap.js`
- ✅ `first-time-project.js` detecta proyectos nuevos
- ✅ `orphan-dev-server-reaper.ps1` (SessionEnd)

### Cada N minutos (background)
- ❌ NO hay daemon PP que corra en background entre sesiones
- ⚡ `background-verifier.js` dispara en cada Stop (no entre sesiones)

### Al hacer commit
- ❌ NO hay pre-commit hook PP que corra UQF audit ni code-review
- ⚡ El Owner debe llamar `code_reviewer.py --fast` manualmente
- ⚡ `pre-compact.md` y `compound.md` son slash commands manuales

## GAPS DE AUTO-INTERVENCIÓN (ejemplos concretos)

### En KobiiCraft (Minecraft plugin work)
Cuando se editan archivos `.java` en KobiiCraft: NINGÚN gate PP
corre automáticamente. UQF tiene principios universalmente
aplicables (`tdd_workflow`, `error_never_silent`, `aaa_test_pattern`)
pero no está cableado para `.java`.
**Solución**: hook `PreToolUse Edit-on-java` que llame `uqf_audit.py`
(≈10 LOC + 1 line en settings.json).

### En InfinityOps (TypeScript / Next.js)
Cuando se hace deploy con `vercel`: OSA no entra en el loop porque
el deploy es vía Vercel CLI, no vía `modules/deployment/`.
**Solución**: hook `PostToolUse Bash` que detecte `vercel deploy`
en el comando y dispare `fire_async(project='infinityops', kind='post-deploy')`
(≈25 LOC en JS).

### En TUA-X (mobile / Elixir)
Si `mix test` falla con cluster de errores: CEPS no se entera porque
el output es del subprocess, no de un Python wrapper.
**Solución**: extender `bug-hunter-learning.js` (ya global, PostToolUse
Bash) para enviar a `ceps.record_error()` cuando ve "FAILED" o
"ERROR" en stdout (≈25 LOC).

### En cualquier repo (generico)
El Owner abre 3 archivos de código y empieza a editar: ningún gate
de "estilo + anti-patterns" corre.
**Solución**: hook `PreToolUse Write|Edit` que llame
`anti_patterns.run_all(file_content)` y emita un advisory en
`additionalContext` si detecta hits (≈30 LOC).

## PLAN DE GLOBALIZACIÓN (priorizado por ROI)

| # | Asset | Mecanismo | Esfuerzo | Impacto |
|---|-------|-----------|----------|---------|
| 1 | UQF anti_patterns como pre-edit gate | hook PreToolUse Write/Edit en `~/.claude/settings.json` que llame `anti_patterns.run_all` | 30 LOC + registro | **crítico** (cubre todos los repos automáticamente) |
| 2 | OSA fire_async en deploys foráneos | hook PostToolUse Bash que detecte `vercel\|gh release\|kubectl apply\|mix release` y dispare `dispatcher.fire_async` | 40 LOC en JS | **alto** (cierra el loop OSA fuera de PP-deploy) |
| 3 | CEPS auto-capture de subprocess errors | extender `bug-hunter-learning.js` para enviar a CEPS cuando ve patterns de error en stdout | 25 LOC en JS | **alto** (rastrea recurrencias sin intervención) |
| 4 | `rules/` a `~/.claude/rules/` global | `mklink /D` o copia + referencia en CLAUDE.md global | 2 LOC + symlink | **medio** (visibilidad cross-proyecto) |
| 5 | `/code-review` slash command global | copia `commands/code-review.md` → `~/.claude/commands/` | 1 copy | **medio** (invocable desde cualquier repo) |
| 6 | `/uqf-audit` slash command nuevo | crear `~/.claude/commands/uqf-audit.md` que llame `uqf_audit.py` | 15 LOC | **medio** |
| 7 | TCO gate como SessionStart hook | hook que emita warning si `pct >= 70%` | 10 LOC + registro | **bajo** (TCO ya lo emite; falta auto-aviso) |
| 8 | OSA background daemon | systemd-like script que llame `dispatcher.run_if_warranted()` cada 30 min | 60 LOC + Owner deployment | **alto pero requiere Owner setup** |

## METODOLOGÍA — probes empíricos T1-T10

Ejecutados desde `/tmp/<random>` (NO `cwd=PP`) con
`sys.path.insert(0, '<PP>')` cuando necesario:

```
T1  UQF importable             YES   score=100.0%
T2  TCO from /tmp              OK    context-pct=5%
T3  TIS importable             YES   sid=41ab447d
T4  OSA dispatcher --check     OK    active=true reason=T4_SESSION_TIMER
T5  CEPS importable            YES
T6  monitoring observe --once  OK    status table (infinityops UP)
T7  lateral-thinking skill     GLOBAL  ~/.claude/skills/lateral-thinking/SKILL.md
T8  rules/ at ~/.claude/rules  NOT EXISTS  (sólo en PP)
T9  never_again importable     YES
T10 anti_patterns fired        OK    {detect_missing_type_hints: 1, detect_mutable_defaults: 1}
```

Hook inventory probes (lectura directa de `~/.claude/settings.json`):
```
PreToolUse:     9 hooks  (8 globales no-PP + auto-test-gate PP)
PostToolUse:    4 hooks  (3 no-PP + tty-restore PP)
Stop:           5 hooks  (3 no-PP + mark-live-session + background-verifier PP)
UserPromptSubmit: 4 hooks (3 no-PP + jit_skill_loader PP)
SessionStart:  13 hooks  (8 no-PP + terminal-slot-recorder + mark-live-session
                          + first-time-project + zero-command-bootstrap PP)
SessionEnd:     3 hooks  (3 no-PP)
PP-referencing hooks total: 8 across 5 events
```

## QUICK WINS — estado al cierre del audit

- [x] **QW-A** `~/.claude/CLAUDE.md` PP-tools section — **DENEGADO por classifier** (Self-Modification of startup config). Requiere autorización explícita del Owner (no es auto-mode). Texto propuesto preservado en el log de commit.
- [x] **QW-B** `~/.claude/skills/lateral-thinking/SKILL.md` — **OK** (presente).
- [x] **QW-C** `~/.claude/agents/omni-singularity.md` — **OK** (M7 del ciclo OSA, presente).

## DONE-GATE

- [x] Matriz con **36 assets** inventariados con datos empíricos
- [x] Plan de Globalización con **8 entries** ranked por ROI
- [x] Gaps de auto-intervención con **4 ejemplos concretos**
  (KobiiCraft / InfinityOps / TUA-X / genérico)
- [x] Cada asset tiene verificación empírica (T1-T10 + hook
  inventory + commands inventory)

Sealed 2026-05-29 (BL-GLOB-001).
