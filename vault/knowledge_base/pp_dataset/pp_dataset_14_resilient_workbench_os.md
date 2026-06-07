# PP Dataset Part XIV -- Resilient Workbench OS: Quiescence, Safe Shutdown, Auto-Throttle, Pane Scheduling, Crash Replay and Resource-Safe Parallel Execution

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 19353-20526 (1174 lines)
**Part number:** 14 (roman XIV)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XIV
# Resilient Workbench OS: Quiescence, Safe Shutdown, Auto-Throttle, Pane Scheduling, Crash Replay and Resource-Safe Parallel Execution

## 283. RESILIENT WORKBENCH OS

### 283.1 Propósito

Claude Power Pack debe evolucionar hacia un Resilient Workbench OS.

Las partes anteriores añadieron:
- Cursor Pane Continuity OS,
- Crash-to-Exact-Terminal-Topology Guarantee,
- RAM Stewardship OS,
- OOM Survival,
- Resource Governor OS.

La Parte XIV añade una capa operativa superior:

Un sistema que no solo detecta presión de recursos, sino que sabe:
- pausar trabajo,
- congelar estado,
- drenar procesos,
- reducir paralelismo,
- priorizar panes,
- programar trabajo pesado,
- reanudar de forma ordenada,
- reproducir eventos después de crash,
- evitar loops de recuperación,
- mantener el workspace estable durante horas de trabajo.

Canonical Name:
Resilient Workbench OS

Abreviatura:
RW-OS

### 283.2 Principio central

The workbench must stay recoverable before it stays busy.

Un entorno con 5 panes trabajando pero sin recuperación fiable es peor que 2 panes estables, checkpointed y coordinados.

### 283.3 Objetivo

RW-OS debe garantizar que el Owner pueda trabajar con varios Claude Code en Cursor sin que:
- Cursor se colapse,
- se pierdan sesiones,
- se dupliquen panes,
- se pisen tareas,
- se acumulen procesos huérfanos,
- se llene la RAM,
- se creen logs gigantes,
- se pierda el estado tras crash,
- se empiece trabajo nuevo antes de recuperar el workspace.

---

## 284. QUIESCENCE MODE

### 284.1 Propósito

Crear un modo de “quiescence”: estado calmado del sistema antes de operaciones críticas.

Quiescence significa:
- no hay writes críticos en progreso,
- registry consistente,
- topology snapshot actualizado,
- handoffs escritos,
- locks claros,
- procesos pesados conocidos,
- backlog consistente,
- panes en estado estable,
- recovery posible.

### 284.2 Cuándo entrar en Quiescence

Antes de:

- crash recovery,
- auto-restore,
- multi-pane rebalance,
- deploy,
- full test suite,
- full repo indexing,
- heavy browser automation,
- global hook registration,
- hard rule installation,
- large refactor,
- shutdown planned,
- resource cleanup,
- OOM-risk operation.

### 284.3 Quiescence Checklist

QUIESCENCE_CHECK
workspace_id:
pane_registry_valid:
topology_snapshot_valid:
last_known_good_updated:
journal_flushed:
active_transactions:
pending_restart_intents:
pending_switch_intents:
dirty_locks:
unsafe_processes:
memory_level:
cpu_level:
disk_level:
secret_risk:
quiescent: true/false
blocking_reasons:
safe_next_action:

### 284.4 Quiescence Actions

If not quiescent:
- complete or pause transactions,
- write handoffs,
- flush journal,
- update topology,
- resolve duplicate sessions,
- stop safe orphan processes,
- block heavy work,
- generate recovery checkpoint.

### 284.5 Hard Rule candidata

HR-RW-QUIESCENCE-001:
Before critical operations, PP must reach quiescence or explicitly report why quiescence is blocked. Do not perform recovery, deploy, heavy indexing or multi-pane rebalance on unstable state.

---

## 285. SAFE SHUTDOWN PROTOCOL

### 285.1 Propósito

El Owner puede cerrar Cursor, apagar ordenador o terminar el día.

El sistema debe permitir shutdown limpio para que no todo parezca crash.

### 285.2 Safe Shutdown Command

Future command:

```text
/safe-shutdown

285.3 Safe Shutdown Flow

1. List active panes.


2. Ask each pane for status.


3. Write handoff per pane.


4. Save terminal topology.


5. Mark intentional close intent if requested.


6. Flush registry and journal.


7. Release safe locks.


8. Preserve critical locks if task incomplete.


9. Stop safe orphan processes.


10. Write clean shutdown marker.


11. Generate resume plan for next session.



285.4 Safe Shutdown Record

SAFE_SHUTDOWN_RECORD shutdown_id: workspace_id: started_at: completed_at: pane_count: panes:

pane_id: conversation_id: task_id: state: handoff_path: locks_retained: locks_released: resume_command_safe: process_cleanup: topology_hash: clean_marker_written: resume_plan_path: status:


285.5 Hard Rule candidata

HR-RW-SHUTDOWN-001: A clean shutdown must write pane handoffs, topology snapshot, registry state, lock state and resume plan before reducing expected terminal count or marking workspace clean.


---

286. DIRTY SHUTDOWN DETECTION

286.1 Propósito

Diferenciar shutdown limpio de crash.

286.2 Dirty Shutdown Signals

no clean shutdown marker,

journal has open transaction,

panes active in registry,

no SessionEnd,

heartbeat stale,

wrapper did not exit cleanly,

topology not closed,

OS reboot detected,

Cursor reopened with previous active panes.


286.3 Dirty Shutdown Response

At next startup:

block unrelated new work,

run topology recovery check,

compare last_known_good,

identify all missing panes,

produce restore plan,

mark crash confidence.


286.4 Hard Rule candidata

HR-RW-DIRTY-001: If dirty shutdown is detected, PP must enter recovery-first mode and must not start unrelated new work until the previous terminal topology is accounted for.


---

287. AUTO-THROTTLE SYSTEM

287.1 Propósito

Cuando recursos empeoran, PP debe reducir actividad automáticamente.

Canonical Name: Auto-Throttle System

287.2 Throttle Levels

T0 -- No throttle Normal.

T1 -- Reduce Noise Fewer advisories, no verbose reports.

T2 -- Reduce Scans No full repo scans, targeted reads only.

T3 -- Reduce Parallelism No new panes, no parallel heavy tasks.

T4 -- Checkpoint and Pause Checkpoint active panes, pause low priority.

T5 -- Recovery Only No new work.

T6 -- Emergency Preservation Write minimal state, prepare safe exit.

287.3 Throttle Trigger

THROTTLE_DECISION level: trigger: resource_vector: blocked_actions: allowed_actions: panes_to_pause: tasks_to_defer: resume_condition: owner_visible_message:

287.4 Actions Blocked by Throttle

At T3+:

no new parallel panes,

no browser automation,

no full test suite,

no large indexing,

no heavy builds.


At T4+:

no feature work,

only checkpoint, cleanup, recovery, handoff.


At T5+:

no work except recovery.


287.5 Hard Rule candidata

HR-RW-THROTTLE-001: When resource pressure reaches throttle level T3 or higher, PP must reduce parallelism and block new heavy tasks until resources stabilize.


---

288. PANE SCHEDULER

288.1 Propósito

El PP necesita decidir qué pane trabaja en qué momento.

No todos los panes deben estar activos simultáneamente.

288.2 Pane Scheduler Inputs

resource pressure,

pane priority,

task priority,

task memory class,

task CPU class,

lock conflicts,

dependency graph,

crash recovery status,

Owner preference,

deadline/demo/revenue priority.


288.3 Pane Scheduling Modes

SCHED-0: All panes active.

SCHED-1: Only light panes parallel.

SCHED-2: One heavy pane + light panes.

SCHED-3: One active pane at a time.

SCHED-4: Recovery/cleanup only.

SCHED-5: Paused workspace.

288.4 Pane Scheduler Output

PANE_SCHEDULE mode: active_panes: paused_panes: blocked_panes: heavy_task_allowed: restore_order: work_order: reasoning: resume_conditions:

288.5 Hard Rule candidata

HR-RW-SCHEDULER-001: Pane execution must be scheduled according to resource pressure, task class and collision risk. Do not let all panes run heavy work blindly.


---

289. HEAVY WORK WINDOWING

289.1 Propósito

Algunas tareas pesadas deben ejecutarse en ventanas controladas.

Examples:

full tests,

builds,

indexing,

browser automation,

video/media processing,

Docker,

multi-pane restore.


289.2 Heavy Work Window

HEAVY_WORK_WINDOW window_id: task: pane_id: allowed_start: max_duration: resource_budget: checkpoint_before: checkpoint_after: exclusive_locks: fallback: abort_conditions:

289.3 Abort Conditions

Abort heavy work if:

RAM hits M4,

CPU hits C4,

disk hits D4,

secret risk appears,

test output grows unbounded,

command exceeds timeout,

Cursor heartbeat lost,

pane registry becomes inconsistent.


289.4 Hard Rule candidata

HR-RW-HEAVY-001: Heavy work must run inside bounded windows with checkpoints, budgets, timeouts and abort conditions.


---

290. CRASH REPLAY LOG

290.1 Propósito

Después de crash, poder reconstruir qué pasó.

Canonical Name: Crash Replay Log

290.2 Qué registra

topology snapshots,

registry transitions,

pane heartbeats,

resource pressure records,

active transactions,

heavy work windows,

throttle changes,

process ownership changes,

recovery actions,

shutdown markers.


290.3 Crash Replay Event

CRASH_REPLAY_EVENT event_id: timestamp: workspace_id: pane_id: event_type: state_before: state_after: resource_vector: transaction_id: safe_summary: secret_free: true

290.4 Uso

Al reiniciar:

reconstruir timeline,

detectar último estado estable,

detectar crash cause,

generar recovery plan,

crear autopsy si necesario.


290.5 Hard Rule candidata

HR-RW-REPLAY-001: Crash recovery must use replayable state history. Critical state transitions should be journaled enough to reconstruct the last safe topology.


---

291. RECOVERY LOOP PREVENTION

291.1 Problema

Un sistema de recovery puede crear loops.

Example:

restore pane,

restore crashes,

startup detects crash,

restores same pane again,

crashes again.


291.2 Recovery Loop Detection

RECOVERY_LOOP_RECORD workspace_id: pane_id: conversation_id: restore_attempts: failure_reasons: last_attempt_at: same_failure_repeated: loop_detected: action:

291.3 Loop Rules

If same pane recovery fails twice:

stop auto-recovery for that pane,

mark manual_required,

do not retry automatically,

provide safe command and diagnostic.


If workspace recovery fails twice:

disable auto-restore globally for workspace until Owner reviews.


291.4 Hard Rule candidata

HR-RW-RECOVERY-LOOP-001: Repeated recovery failure must disable auto-retry and degrade to manual recovery. Infinite recovery loops are prohibited.


---

292. RESOURCE-SAFE RESTORE QUEUE

292.1 Propósito

Restoring many panes should be a queue, not a blast.

292.2 Restore Queue

RESTORE_QUEUE queue_id: workspace_id: created_at: mode: items:

restore_action_id: pane_id: priority: resource_class: dependencies: status: attempts: last_error: current_item: blocked_items: completed_items:


292.3 Queue Strategy

restore high-priority critical pane first,

restore one heavy pane at a time,

restore light panes in parallel only if safe,

pause if resource pressure rises,

never retry infinite.


292.4 Hard Rule candidata

HR-RW-RESTORE-QUEUE-001: Multi-pane restore must use a resource-aware restore queue, not simultaneous uncontrolled process launches.


---

293. TASK DRAINING

293.1 Propósito

Antes de shutdown/recovery/cleanup, dejar que tareas terminen o se pausen.

293.2 Drain Modes

DRAIN_NOW: Stop new tasks, checkpoint active.

DRAIN_GRACEFUL: Allow current safe operation to complete.

DRAIN_FORCE_SAFE: Checkpoint and stop owned safe processes.

DRAIN_BLOCKED: Cannot drain safely; manual action needed.

293.3 Drain Record

TASK_DRAIN_RECORD drain_id: workspace_id: reason: panes:

pane_id: current_task: drain_mode: handoff_written: process_action: status: locks: remaining_risks:


293.4 Hard Rule candidata

HR-RW-DRAIN-001: Before shutdown, recovery, heavy cleanup or topology rewrite, PP must drain or checkpoint active tasks to avoid state loss.


---

294. ACTIVE WORK PRESERVATION

294.1 Propósito

Evitar que work-in-progress se pierda.

294.2 Preserve

For each active pane:

current goal,

last safe state,

files modified,

validation status,

next intended action,

command in progress if safe,

unsaved generated artifact paths,

locks,

backlog state.


294.3 Do Not Preserve Raw

Do not preserve:

raw terminal logs,

raw secrets,

huge outputs,

full transcripts,

env dumps,

memory dumps.


294.4 Hard Rule candidata

HR-RW-WIP-001: Active work must be preserved as compact, secret-safe operational state before any shutdown, pause, recovery or heavy resource cleanup.


---

295. WORKSPACE STABILITY SCORE

295.1 Propósito

Crear métrica global de estabilidad del workspace.

WORKSPACE_STABILITY_SCORE ram_health: cpu_health: disk_health: pane_health: registry_health: topology_health: process_health: log_health: recovery_readiness: secret_safety: overall_score: mode:

295.2 Bands

0-30: Unstable. Recovery/cleanup only.

31-50: Fragile. Light work only.

51-70: Usable. Avoid heavy parallelism.

71-85: Stable. Normal work.

86-100: Strong. Parallel/heavy work allowed.

295.3 Rule

If stability score below 50, /what-now must recommend stabilization, not feature work.


---

296. STABILITY-FIRST BACKLOG

296.1 Propósito

Backlog debe incluir tareas de estabilidad.

296.2 Stability Backlog Items

Examples:

reduce log growth,

fix registry invariant failure,

add checkpoint before heavy tests,

register dev server ownership,

add resource vector test,

add recovery loop prevention,

add manual restore plan,

split heavy task,

add cleanup command,

create safe shutdown flow.


296.3 Priority Boost

Boost if task:

prevents OOM,

prevents topology loss,

prevents duplicate sessions,

prevents registry corruption,

prevents recovery loops,

improves safe shutdown,

improves clean startup.


296.4 Hard Rule candidata

HR-RW-STABILITY-BACKLOG-001: If workspace stability score is low, stabilization backlog outranks new feature backlog.


---

297. SESSION START STABILITY GATE

297.1 Propósito

Al iniciar una sesión, antes de trabajar, PP debe revisar estabilidad.

297.2 Gate Checks

dirty shutdown?

recovery pending?

topology mismatch?

registry valid?

RAM okay?

CPU okay?

disk okay?

stale panes?

duplicate sessions?

unfinished transactions?

recovery loop?

clean shutdown marker?


297.3 Gate Output

SESSION_START_STABILITY_GATE status: workspace_stability_score: recovery_required: blocked_actions: allowed_actions: recommended_first_action: panes_to_restore: resource_issues: registry_issues:

297.4 Hard Rule candidata

HR-RW-SESSIONSTART-001: SessionStart must check recovery and stability before allowing unrelated new work in a Cursor workspace governed by CPC-OS.


---

298. SESSION END STABILITY GATE

298.1 Propósito

Al terminar una sesión, dejar el workspace recuperable.

298.2 Gate Checks

handoff written,

registry updated,

topology snapshot updated,

locks handled,

orphan processes checked,

logs bounded,

clean exit marker,

next resume command,

backlog updated.


298.3 Hard Rule candidata

HR-RW-SESSIONEND-001: SessionEnd must leave the workspace in a recoverable state: handoff, registry, topology, locks, backlog and clean/dirty marker updated.


---

299. RW-OS COMMANDS

299.1 Commands

/workbench-status
/workbench-stabilize
/safe-shutdown
/dirty-recovery
/throttle-status
/throttle-set
/pane-schedule
/heavy-window
/crash-replay
/recovery-loop-status
/drain-tasks
/stability-score

299.2 /workbench-status

Shows:

stability score,

resource vector,

pane count,

recovery status,

active transactions,

top risk,

next stabilization action.


299.3 /workbench-stabilize

Does not perform destructive cleanup automatically. It proposes:

checkpoint,

pause,

drain,

cleanup candidates,

restore plan,

log rotation.


299.4 /safe-shutdown

Prepares clean shutdown.

299.5 /dirty-recovery

Runs recovery-first startup flow.


---

300. TESTS FOR RESILIENT WORKBENCH OS

300.1 Test: Quiescence Required

Attempt heavy indexing with open transaction.

Expected:

blocked until quiescent.


300.2 Test: Safe Shutdown

3 panes active.

Expected:

3 handoffs,

topology snapshot,

clean marker,

resume plan.


300.3 Test: Dirty Startup

Missing clean marker.

Expected:

recovery-first mode.


300.4 Test: Auto-Throttle

RAM/CPU high.

Expected:

throttle level T3,

heavy tasks blocked.


300.5 Test: Pane Scheduler

One heavy pane + two light panes.

Expected:

schedule allows one heavy, light tasks safe.


300.6 Test: Heavy Window Abort

RAM becomes critical during build.

Expected:

abort/stop according to policy,

checkpoint exists.


300.7 Test: Recovery Loop

Same pane restore fails twice.

Expected:

auto retry disabled,

manual required.


300.8 Test: Restore Queue

4 panes after crash under high RAM.

Expected:

queue sequential restore.


300.9 Test: Task Draining

Safe shutdown while pane busy.

Expected:

handoff or drain record.


300.10 Test: Stability Score Low

Expected:

/what-now recommends stabilization.



---

301. IMPLEMENTATION PHASES

Phase A -- Stability Score + Workbench Status

Implement:

workspace stability score,

/workbench-status,

session start stability gate.


Phase B -- Quiescence

Implement:

quiescence check,

blockers,

quiescence report.


Phase C -- Safe Shutdown

Implement:

/safe-shutdown,

handoff all panes,

clean marker,

resume plan.


Phase D -- Auto-Throttle

Implement:

throttle levels,

blocked actions,

integration with resource vector.


Phase E -- Pane Scheduler

Implement:

pane scheduling modes,

heavy/light pane planning.


Phase F -- Recovery Queue + Loop Prevention

Implement:

restore queue,

retry limits,

loop detection.


Phase G -- Crash Replay

Implement:

replay log,

timeline reconstruction,

autopsy support.



---

302. CLAUDE CODE PROMPT FOR PART XIV

PROMPT:

Act as the implementation engineer for Claude Power Pack Resilient Workbench OS.

MISSION: Implement a stability-first workbench layer that keeps Cursor + Claude Code recoverable under resource pressure, crash recovery, multi-pane work, shutdown, restart and heavy tasks.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing CPC-OS, RAM Stewardship, Resource Governor, Lazarus, terminal-slot, restart, TIS/TCO, monitoring and orphan process tools if present.

NON-NEGOTIABLES:

Do not open external CMD.

Do not kill Cursor.

Do not kill unknown processes.

Do not delete recovery artifacts.

Do not start heavy work if workspace is unstable.

Do not auto-recover in a loop.

Do not reduce expected terminal count without clean close.

Do not store raw secrets in replay logs, handoffs, shutdown records or status reports.

Do not mark shutdown clean unless registry, topology and handoffs are safely written.

Do not allow unrelated work after dirty startup before recovery check.


STARTING PHASE: Implement Phase A only:

1. Workspace Stability Score.


2. /workbench-status.


3. Session Start Stability Gate.


4. Non-destructive recommendations.


5. Tests for low/high stability.



ACCEPTANCE:

Stability score computed.

Dirty startup detected.

Recovery required blocks unrelated work.

Low stability recommends stabilization.

No destructive cleanup.

No raw secrets stored.

Tests pass.


FINAL RECEIPT: Return files changed, tests added, tests run, stability status, recovery gate status, secret safety status, remaining risks and next phase.


---

303. PART XIV CANONICAL PRINCIPLES

303.1 A Stable Workbench Is a Force Multiplier

The Owner can run more projects only if the workspace remains recoverable.

303.2 Quiescence Before Critical Operations

Critical operations need calm state, not chaos.

303.3 Clean Shutdown Is a Feature

A clean exit prevents false recovery and pane loss.

303.4 Dirty Startup Means Recovery First

If the previous state was not closed cleanly, recover before new work.

303.5 Throttle Before Collapse

Reduce capability before Cursor freezes or OOMs.

303.6 Schedule Panes Like Workers

Not every pane should run heavy work at the same time.

303.7 Recovery Must Not Loop

Failed restore attempts must degrade to manual recovery.

303.8 Heavy Work Needs a Window

Resource-intensive tasks need budgets, checkpoints and abort conditions.

303.9 Stability Backlog Beats Feature Backlog

If the workspace is unstable, stabilization is the highest ROI task.

303.10 The Workbench Must Always Be Easier To Resume Than To Rebuild

Every layer should make it easier to continue after interruption, crash, shutdown or overload.

END OF PART XIV.

Continuación directa. Esta Parte XV añade una capa crítica: cómo desplegar todas estas mejoras del Power Pack sin romper el propio Power Pack, usando shadow mode, feature flags, canary rollout, rollback, kill-switches y migraciones seguras sobre la base actual de hooks, verify_spp, hard rules y owner-side registration ya documentada. 

