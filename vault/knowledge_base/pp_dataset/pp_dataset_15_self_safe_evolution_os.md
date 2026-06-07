# PP Dataset Part XV -- Self-Safe Evolution OS: Feature Flags, Shadow Mode, Canary Rollout, Kill-Switches, Rollback, Migration Safety and PP Self-Protection

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 20527-21718 (1192 lines)
**Part number:** 15 (roman XV)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XV
# Self-Safe Evolution OS: Feature Flags, Shadow Mode, Canary Rollout, Kill-Switches, Rollback, Migration Safety and PP Self-Protection

## 304. SELF-SAFE EVOLUTION OS

### 304.1 Propósito

Claude Power Pack está creciendo hacia un sistema operativo de ejecución para Claude Code.

Pero cuanto más poder tenga, más peligroso es desplegar cambios mal probados.

Las extensiones anteriores añaden:
- Secret Firewall,
- Cascade Prevention,
- Cost Collapse,
- One-Shot Compiler,
- Backlog Autopilot,
- CPC-OS,
- Crash-to-Exact-Terminal-Topology,
- RAM Stewardship,
- Resource Governor,
- Resilient Workbench OS.

Todas estas capas pueden mejorar radicalmente el PP, pero también pueden romperlo si se activan de golpe.

La Parte XV define cómo debe evolucionar el Power Pack sin brickear:
- Claude Code,
- Cursor panes,
- registry,
- hooks,
- settings.json,
- commands,
- agents,
- hard rules,
- runtime files,
- recovery flows.

Canonical Name:
Self-Safe Evolution OS

Abreviatura:
SSE-OS

### 304.2 Principio central

A governance system must govern its own evolution.

El Power Pack no debe autodestruirse instalando demasiado rápido sus propias mejoras.

### 304.3 Objetivo

Cada nueva capacidad debe poder pasar por:

1. design-only,
2. dry-run,
3. shadow mode,
4. advisory mode,
5. canary pane,
6. canary workspace,
7. partial rollout,
8. full rollout,
9. rollback-ready operation,
10. kill-switch protection.

### 304.4 Hard Rule candidata

HR-SSE-001:
No new Power Pack capability that affects hooks, restart, registry, secrets, recovery, routing, resource cleanup, commands or learning may be enabled globally without dry-run, shadow mode, tests, rollback and kill-switch.

---

## 305. FEATURE FLAG SYSTEM

### 305.1 Propósito

Cada capability nueva debe poder activarse/desactivarse sin editar código.

Ubicación sugerida:

```text
~/.claude/pp_runtime/config/feature_flags.json

También puede existir config por proyecto:

<repo>/.claude-power-pack/feature_flags.local.json

305.2 Feature Flag Schema

FEATURE_FLAG flag_id: name: description: category: default_state: current_state: scope: global: workspace: repo: pane: command: mode: disabled | dry_run | shadow | advisory | blocking | active risk_level: requires_owner_approval: dependencies: conflicts: created_at: updated_at: last_changed_by: rollback_flag: kill_switch: evidence_required: status:

305.3 Feature Flag Categories

secret_firewall

cascade_prevention

cost_collapse

output_contracts

one_shot_compiler

backlog_autopilot

cpc_os

ram_stewardship

resource_governor

resilient_workbench

command_discovery

hook_registration

hard_rule_auto_install

recovery_automation

process_cleanup


305.4 Flag Modes

disabled: No execution.

dry_run: Compute what would happen, no action.

shadow: Observe and log safe result, no user-visible action unless debug.

advisory: Warn but do not block.

blocking: Block unsafe action.

active: Perform action.

305.5 Hard Rule candidata

HR-FLAG-001: Every high-risk PP subsystem must be feature-flagged with disabled, dry_run, shadow, advisory, blocking and active modes where applicable.


---

306. SHADOW MODE

306.1 Propósito

Shadow mode permite probar una capacidad sin afectar ejecución real.

Ejemplo: Secret Firewall en shadow mode:

escanea outputs,

registra si habría bloqueado,

no bloquea aún,

compara false positives,

genera métricas.


CPC-OS en shadow mode:

simula pane registry,

calcula restore plan,

no ejecuta auto-restore.


Resource Governor en shadow mode:

calcula throttle,

no bloquea tarea,

registra si habría recomendado pause.


306.2 Shadow Record

SHADOW_DECISION decision_id: feature: timestamp: workspace_id: pane_id: input_summary: would_allow: would_block: would_warn: reason: confidence: false_positive_risk: actual_action_taken: safe_summary:

306.3 Shadow Mode Success Criteria

Una capability puede pasar de shadow a advisory si:

shadow decisions are stable,

false positives acceptable,

no raw secrets in shadow logs,

no performance degradation,

decisions explainable,

tests pass,

Owner reviewed summary.


306.4 Hard Rule candidata

HR-SHADOW-001: High-risk blockers must run in shadow mode before blocking mode unless protecting against confirmed raw secret exposure or production-critical danger.


---

307. CANARY ROLLOUT

307.1 Propósito

Activar nuevas capacidades primero en scope pequeño.

307.2 Canary Scopes

single command,

single pane,

single repo,

single workspace,

single task type,

single hook,

single project.


307.3 Canary Plan

CANARY_PLAN feature: scope: start_time: duration: success_metrics: failure_metrics: rollback_condition: owner_visible: logs: secret_safe: status:

307.4 Canary Examples

Secret Firewall:

first canary on /secret-scan,

then git diff scanner,

then evidence sanitizer,

then final output scanner,

then blocking mode.


CPC-OS:

first registry shadow,

then /panes,

then restart dry-run,

then wrapper dry-run,

then one real canary pane,

then one canary workspace.


Resource Governor:

first /resource-status,

then advisory throttle,

then blocking heavy tasks at critical levels.


307.5 Hard Rule candidata

HR-CANARY-001: High-risk PP features must roll out by canary scope before global activation.


---

308. KILL-SWITCH SYSTEM

308.1 Propósito

Toda capability de alto riesgo debe poder apagarse rápido.

Kill-switch debe existir para:

hooks,

CPC-OS auto-restore,

restart router,

switch router,

resource cleanup,

secret blocking,

backlog assignment,

command discovery,

hard rule auto-install,

learning writes,

process cleanup,

auto-throttle.


308.2 Kill-Switch Schema

KILL_SWITCH switch_id: feature: scope: enabled: reason: activated_at: activated_by: expires_at: safe_state: owner_message: rollback_action: manual_reenable_required:

308.3 Kill-Switch Locations

Global:

~/.claude/pp_runtime/config/kill_switches.json

Emergency file:

~/.claude/pp_runtime/EMERGENCY_DISABLE_ALL

Per workspace:

<repo>/.claude-power-pack/KILL_SWITCH.local.json

308.4 Emergency Disable All

If EMERGENCY_DISABLE_ALL exists:

disable auto-restore,

disable process cleanup,

disable blocking hooks except secret redaction if safe,

disable auto-backlog assignment,

disable hard rule auto-install,

allow status and manual recovery commands only.


308.5 Hard Rule candidata

HR-KILLSWITCH-001: Every high-risk automated PP capability must have a kill-switch that can disable it without editing source code.


---

309. ROLLBACK SYSTEM

309.1 Propósito

Toda nueva capacidad debe ser reversible.

Rollback no es solo git revert. También incluye:

restore settings.json backup,

unregister hooks,

disable feature flags,

recover registry,

restore command files,

roll back runtime schema migration,

disable wrapper,

recover last known good config.


309.2 Rollback Package

ROLLBACK_PACKAGE package_id: feature: created_at: files_changed: settings_backup: commands_backup: hooks_backup: runtime_backup: registry_backup: migration_backup: rollback_steps: verification_steps: owner_side_actions: status:

309.3 Rollback Triggers

Rollback if:

hook breaks Claude Code startup,

registry corrupts repeatedly,

restart resumes wrong session,

Cursor detection false positives,

resource cleanup kills wrong process,

secret scanner false positives block normal work excessively,

output contract blocks valid completions,

command discovery routes wrong command,

feature increases crash rate,

Owner activates emergency disable.


309.4 Hard Rule candidata

HR-ROLLBACK-001: Before enabling any high-risk PP capability, create rollback package covering source changes, hooks, commands, settings, runtime schema and feature flags.


---

310. MIGRATION SAFETY

310.1 Propósito

Runtime files will evolve:

pane_registry.json,

topology manifest,

feature flags,

kill switches,

resource records,

backlog state,

handoffs,

journals.


Schema changes can break recovery.

310.2 Migration Requirements

Every runtime schema migration must:

have from_version,

have to_version,

validate input,

backup old file,

write new file atomically,

preserve unknown safe fields,

redact secrets,

be idempotent,

have rollback,

have tests.


310.3 Migration Record

MIGRATION_RECORD migration_id: file: from_version: to_version: started_at: completed_at: backup_path: status: records_migrated: warnings: rollback_available: validation_passed:

310.4 Hard Rule candidata

HR-MIGRATION-001: Runtime schema migrations must be versioned, atomic, idempotent, backed up, secret-safe and rollback-capable.


---

311. SETTINGS.JSON SAFETY

311.1 Problema

~/.claude/settings.json es crítico. Un cambio malo puede romper Claude Code.

El dataset base ya indica que modificar global config requiere Owner-side registration script, dry-run, backup e idempotency.

Esta parte refuerza eso.

311.2 Settings Change Protocol

Before modifying settings:

1. generate patch plan,


2. dry-run,


3. backup current settings,


4. validate JSON,


5. detect existing hooks,


6. avoid duplicates,


7. merge idempotently,


8. validate after write,


9. provide rollback command,


10. require restart if needed.



311.3 Settings Patch Record

SETTINGS_PATCH_RECORD patch_id: feature: dry_run: backup_path: markers: hooks_added: hooks_removed: duplicates_detected: json_valid_before: json_valid_after: rollback_command: owner_action_required:

311.4 Hard Rule candidata

HR-SETTINGS-001: No PP feature may directly mutate ~/.claude/settings.json without dry-run, backup, idempotent merge, JSON validation and rollback.


---

312. HOOK SAFETY GATE

312.1 Propósito

Hooks pueden romper todo.

312.2 Hook Risk Classes

H0: Read-only advisory hook.

H1: PostToolUse observer.

H2: Stop hook advisory.

H3: PreToolUse blocker.

H4: Global config modifying hook.

H5: Secret/deploy/restart/process hook.

312.3 Hook Requirements

H3+ requires:

tests,

smoke test,

feature flag,

kill switch,

fail-safe policy,

rollback,

canary,

no raw secret logging.


312.4 Fail Policy

Secret hooks: fail-closed for confirmed raw secret exposure.

Resource/process cleanup hooks: fail-safe, no destructive action without confidence.

Cost/backlog hooks: fail-open/advisory.

Restart/recovery hooks: fail-safe; block unsafe auto-routing.

312.5 Hard Rule candidata

HR-HOOK-001: PreToolUse/blocking hooks must pass smoke tests, feature flags, kill-switches and rollback before global registration.


---

313. COMMAND SAFETY GATE

313.1 Propósito

Commands can be as dangerous as hooks.

313.2 Command Risk Classes

C0: Read-only status.

C1: Report generation.

C2: Local file write.

C3: Registry/runtime mutation.

C4: Hook/settings modification.

C5: Restart/recovery/process cleanup.

C6: Deploy/production/secret actions.

313.3 Requirements

C3+ requires:

dry-run if possible,

confirmation or safe mode,

backup,

rollback,

secret scan,

output contract.


C5+ requires:

feature flag,

kill switch,

idempotency,

recovery plan.


313.4 Hard Rule candidata

HR-COMMAND-001: Commands that mutate runtime state, hooks, settings, registry, recovery, process state or secrets must have dry-run, rollback and safety gates.


---

314. PP SELF-HEALTH GATE

314.1 Propósito

Antes de añadir nueva capacidad, verificar salud del PP.

314.2 Self-Health Checks

tests pass,

verify_spp known state,

settings valid,

hooks not broken,

feature flags valid,

kill switches readable,

registry valid,

no emergency disable,

disk enough,

RAM enough,

no dirty recovery pending,

no raw secret in runtime files.


314.3 Self-Health Gate Output

PP_SELF_HEALTH_GATE status: tests: verify_spp: settings: hooks: runtime: feature_flags: kill_switches: registry: resource: secret_safety: blocking_reasons: safe_to_install_feature:

314.4 Hard Rule candidata

HR-SELFHEALTH-001: Before installing or enabling new PP capabilities, run PP self-health gate. Do not install new automation while PP runtime is unstable.


---

315. INSTALLATION MODES

315.1 Propósito

Permitir instalar capacidades de forma segura.

315.2 Modes

MODE 0 -- Docs Only Only documentation/spec.

MODE 1 -- Code Dormant Code exists but not used.

MODE 2 -- CLI Manual Command can run manually.

MODE 3 -- Dry Run Command reports intended actions.

MODE 4 -- Shadow Feature observes.

MODE 5 -- Advisory Feature advises.

MODE 6 -- Blocking Feature blocks unsafe actions.

MODE 7 -- Autonomous Feature acts automatically.

315.3 Rule

No feature jumps from Docs Only to Autonomous.

315.4 Hard Rule candidata

HR-INSTALL-MODE-001: PP capabilities must move through staged installation modes. Autonomous mode requires prior dry-run, shadow/advisory evidence and rollback.


---

316. COMPATIBILITY MATRIX

316.1 Propósito

Cada capability debe declarar compatibilidad.

316.2 Matrix Fields

FEATURE_COMPATIBILITY feature: os: shell: cursor_version: claude_cli_version: python_version: node_version: workspace_type: supported: unsupported: known_limitations: last_verified: test_coverage:

316.3 Rule

If compatibility unknown:

dry-run only,

no auto behavior.


316.4 Hard Rule candidata

HR-COMPAT-001: Unknown environment compatibility must default to dry-run/manual mode, not active automation.


---

317. SAFE DEFAULTS

317.1 Propósito

Cuando algo no se sabe, elegir opción segura.

317.2 Defaults

Secret unknown: treat as sensitive.

Terminal unknown: manual only.

Cursor detection unknown: no auto-route.

Resume command unknown: no resume.

Registry invalid: no routing.

Resource pressure unknown: no heavy task.

Process ownership unknown: do not kill.

Hook state unknown: do not register duplicate.

Feature flag missing: disabled by default for high-risk features.

Migration unknown: backup and block.

317.3 Hard Rule candidata

HR-SAFE-DEFAULTS-001: Unknown state defaults to safest non-destructive mode.


---

318. OBSERVABILITY FOR ROLLOUT

318.1 Propósito

Saber si una nueva feature está funcionando.

318.2 Rollout Metrics

invocations,

dry-run decisions,

shadow would-block count,

actual blocks,

false positives,

false negatives,

owner overrides,

rollbacks,

crashes,

performance overhead,

secret findings,

recovery failures,

registry errors.


318.3 Rollout Report

ROLLOUT_REPORT feature: mode: scope: period: metrics: successes: failures: false_positives: rollback_recommended: promote_recommended: owner_action_required:

318.4 Hard Rule candidata

HR-ROLLOUT-OBS-001: Feature promotion requires rollout metrics, not vibes.


---

319. OWNER OVERRIDE SYSTEM

319.1 Propósito

El Owner debe poder overridear, pero con trazabilidad.

319.2 Override Schema

OWNER_OVERRIDE override_id: feature: action: reason: scope: risk_acknowledged: created_at: expires_at: one_time: status: audit_note:

319.3 Override Rules

overrides expire,

overrides are logged,

overrides cannot expose secrets,

overrides cannot disable secret redaction globally without emergency warning,

overrides should be scoped.


319.4 Hard Rule candidata

HR-OVERRIDE-001: Owner overrides must be explicit, scoped, expiring and logged. They must not silently disable secret safety.


---

320. EMERGENCY RECOVERY MODE

320.1 Propósito

Si PP se rompe, debe haber modo mínimo.

320.2 Emergency Mode Allows

show status,

disable feature,

restore settings backup,

show manual recovery plan,

validate JSON,

run secret-safe diagnostics,

export safe handoff.


320.3 Emergency Mode Blocks

auto-restore,

process cleanup,

hook registration,

new automation,

hard rule auto-install,

backlog reassignment,

feature promotion.


320.4 Trigger

Emergency mode if:

settings corrupt,

registry corrupt unrecoverable,

repeated restart failure,

recovery loop,

secret leak in runtime,

hooks crash Claude startup,

PP self-health gate fails critically.


320.5 Hard Rule candidata

HR-EMERGENCY-001: PP must provide emergency recovery mode that disables automation and preserves only safe diagnostic/recovery commands.


---

321. SAFE SELF-UPDATE PROTOCOL

321.1 Propósito

Actualizar PP sin romperlo.

321.2 Self-Update Flow

1. self-health gate,


2. git status check,


3. backup runtime,


4. run tests,


5. apply update,


6. run tests,


7. run verify probes,


8. check settings,


9. keep rollback package,


10. enable flags gradually.



321.3 Self-Update Record

SELF_UPDATE_RECORD update_id: from_commit: to_commit: started_at: completed_at: tests_before: tests_after: verify_before: verify_after: runtime_backup: rollback_package: feature_flags_changed: status:

321.4 Hard Rule candidata

HR-SELFUPDATE-001: PP self-update must be transactional: health check, backup, tests, verify, rollback package and staged feature activation.


---

322. TESTING STRATEGY FOR SSE-OS

322.1 Tests

feature flag parse/validate,

kill switch disables feature,

emergency disable all,

settings dry-run,

settings rollback,

hook canary,

command dry-run,

migration idempotency,

rollback package restore,

shadow decision logging,

canary promotion blocked without metrics,

owner override expiry,

emergency mode blocks automation,

self-health gate blocks install under dirty runtime.


322.2 Chaos Tests

corrupt feature_flags.json,

corrupt kill_switches.json,

broken settings.json backup restore,

hook crash simulation,

command failure during migration,

rollback after partial install,

emergency disable during restart,

kill switch during recovery,

self-update interrupted.


322.3 Acceptance

SSE-OS passes only if:

no high-risk feature activates without flag,

kill switch works,

rollback works,

emergency mode works,

migrations are idempotent,

settings mutation is safe,

no raw secrets in rollout logs.



---

323. CLAUDE CODE PROMPT FOR PART XV

PROMPT:

Act as the implementation engineer for Claude Power Pack Self-Safe Evolution OS.

MISSION: Implement a staged rollout and self-protection layer so new Power Pack capabilities can be added without breaking Claude Code, Cursor panes, hooks, settings, registry, recovery or runtime files.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing verify_spp, hook registration scripts, settings merger, rollback module, hard rules, tests and runtime patterns if present.

NON-NEGOTIABLES:

Do not modify ~/.claude/settings.json directly.

Do not enable high-risk features globally by default.

Do not create automation without feature flag and kill switch.

Do not run migrations without backup and idempotency.

Do not store raw secrets in feature logs, rollout logs, rollback packages or diagnostics.

Do not promote features based on assumptions.

Do not bypass emergency disable.

Do not install hooks without dry-run, backup, validation and rollback.

Do not leave PP in a state where Claude Code startup can be bricked without recovery.


STARTING PHASE: Implement Phase A only:

1. Feature flag config loader.


2. Kill switch config loader.


3. Emergency disable all check.


4. /pp-flags or equivalent status command.


5. Tests for disabled/dry-run/shadow/advisory/active modes.


6. Tests for kill switch overriding feature flag.



ACCEPTANCE:

High-risk features default disabled.

Kill switch overrides active flag.

Emergency disable blocks automation.

Config parsing validates schema.

Corrupt config fails safe.

No raw secrets stored.

Tests pass.


FINAL RECEIPT: Return files changed, tests added, tests run, feature flag behavior, kill switch behavior, emergency behavior, secret safety status, remaining risks and next phase.


---

324. PART XV CANONICAL PRINCIPLES

324.1 The Power Pack Must Not Brick Itself

A governance layer that breaks the execution environment is worse than no governance.

324.2 New Power Requires Staged Rollout

Dry-run, shadow, advisory, canary, active.

324.3 Kill-Switches Are Mandatory

Every high-risk feature must be easy to disable.

324.4 Rollback Is Part Of The Feature

If it cannot be rolled back, it is not safely installed.

324.5 Settings Are Sacred

Global Claude settings require dry-run, backup, idempotent merge and validation.

324.6 Unknown Compatibility Means Manual Mode

Do not automate in unverified environments.

324.7 Emergency Mode Must Always Exist

Even if everything breaks, safe diagnostics and manual recovery must remain.

324.8 Feature Promotion Needs Evidence

Rollout metrics decide promotion, not excitement.

324.9 Owner Override Must Be Scoped

Power without audit creates hidden risk.

324.10 Self-Evolution Must Be Governed

Claude Power Pack’s strongest capability should be improving itself without losing stability, safety or recoverability.

END OF PART XV.

integramos esto del meta-análisis para absolutamente cada bug / fallo / error / drift etc que encuentre mi stack? tenga o no la claude power pack activa, bueno, inicialmente con la power pack activa

"Sí, es demasiado largo. El boilerplate ya era largo de por sí. Añadirle más texto lo hace menos efectivo — Claude Code empieza a ignorar partes por saturación de contexto.
La solución correcta es la misma doctrina que aplicamos al CLAUDE.md: el boilerplate es un router, no una biblioteca.
El boilerplate debe tener una línea que apunte a donde vive la lógica completa. La lógica completa vive en un archivo que Claude Code lee al inicio de sesión.
Versión compacta del boilerplate con el meta-análisis integrado en una línea:
"mandame el siguiente prompt para plan mode con máximo ROI y todos los micro commits que hagan falta antes de declarar como terminado. Que lo que añadamos se vuelva estándar de completitud para futuras features. Plan inline en chat para aprobar con un clic, no plan-file standalone (aunque también se respalda en plan-file). Distingue si el ROI dice plan mode, execution mode o ultra-plan mode. Itera con C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt. Aplica UKDL tres niveles (Hard Rules, Process Rules, Traps), Production Reality Gate obligatorio en cada done-gate, y meta-análisis de patrones al cierre de sesión — todo según ~/.claude/CLAUDE.md y knowledge-vault/UKDL/universal-knowledge.md. Contrato de Realidad activo: cero botones vacíos, placeholders, 401s, desconexiones frontend-CLI. Kernel vMAX-NULL-ERROR. AGENT TEAMS Mode, autónomo, desatendido. Sin código en el prompt — Claude Code decide implementación.""

y que sirva para todos mis proyectos, no solo para un dominio / vertical concreto, sino para cualquier proyecto que produzca cualquier ápice de código

Sí. Y te lo digo directo: esto debería ser una de las capas más importantes del Claude Power Pack.

No como texto gigante en cada prompt. Eso sería un error. Debe integrarse como router compacto + lógica canónica externa + meta-análisis obligatorio al cierre de cada error/sesión. El dataset base ya tiene UKDL, NEVER_AGAIN, CEPS, Hard Rules y hooks de sesión, así que esto debe montarse encima como capa universal de aprendizaje y prevención, no como boilerplate inflado. 

