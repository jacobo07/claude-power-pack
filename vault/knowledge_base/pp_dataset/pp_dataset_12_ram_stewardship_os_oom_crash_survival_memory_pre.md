# PP Dataset Part XII -- RAM Stewardship OS + OOM Crash Survival + Memory Pressure Governance for Cursor Pane Continuity OS

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 16708-18091 (1384 lines)
**Part number:** 12 (roman XII)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XII
# RAM Stewardship OS + OOM Crash Survival + Memory Pressure Governance for Cursor Pane Continuity OS

## 232. RAM STEWARDSHIP OS

### 232.1 Propósito

Claude Power Pack debe añadir una capa de limpieza, cuidado constante y supervivencia ante presión de RAM.

El objetivo no es solo detectar out-of-memory crashes después de que ocurran.

El objetivo es:

1. Prevenir que Cursor, Claude Code, wrappers, hooks, Node, Python o procesos auxiliares lleguen a OOM.
2. Reducir memoria antes de que el sistema se vuelva inestable.
3. Hacer checkpoints antes de zonas peligrosas.
4. Preservar pane topology, conversaciones, backlog y locks.
5. Sobrevivir a crashes por OOM.
6. Restaurar la topología exacta tras reinicio.
7. Evitar cascadas de memoria: RAM alta -> Cursor freeze -> terminales muertas -> registry stale -> sesiones perdidas -> backlog corrupto.

Canonical Name:
RAM Stewardship OS

Abreviatura:
RS-OS

### 232.2 Principio central

Memory pressure is a first-class execution risk.

La RAM no debe tratarse como un detalle del sistema operativo.
Debe formar parte del modelo de ejecución, igual que:
- secretos,
- coste,
- cascadas,
- backlog,
- panes,
- restart,
- recovery.

### 232.3 Hard Rule candidata

HR-RAM-001:
Before and during long-running Claude Code work, PP must monitor memory pressure, checkpoint recoverable state, and degrade safely before OOM risk can destroy Cursor pane continuity.

---

## 233. OOM CRASH SURVIVAL GUARANTEE

### 233.1 Propósito

Añadir garantía explícita:

Si Cursor, Claude Code, el wrapper, Node, Python, un test runner, un dev server, un indexer, un browser automation process o el sistema entero cae por OOM, el Power Pack debe poder volver al último estado recuperable.

Esto conecta directamente con:
- terminal topology manifest,
- last_known_good_topology,
- pane registry,
- restart intents,
- handoffs,
- backlog assignments,
- scope locks,
- clean shutdown markers,
- crash confidence.

### 233.2 OOM Survival Guarantee

Después de un OOM crash:

- no perder terminal_count esperado,
- no perder pane-to-conversation mapping,
- no perder cwd,
- no perder backlog por pane,
- no perder locks críticos,
- no asumir clean close,
- no confiar en PIDs antiguos,
- no reanudar solo la última sesión,
- no abrir CMD externo,
- no duplicar sesiones,
- no empezar trabajo nuevo sin recovery check.

### 233.3 Hard Rule candidata

HR-RAM-OOM-001:
After suspected OOM crash, CPC-OS must treat the shutdown as crash_suspected, preserve last known terminal topology, ignore old process IDs, and run topology recovery before unrelated work.

---

## 234. MEMORY PRESSURE LEVELS

### 234.1 Propósito

Definir niveles de presión de RAM para que PP actúe antes del crash.

### 234.2 Levels

M0 -- Normal
RAM suficiente. No action.

M1 -- Watch
Uso de memoria subiendo. Registrar y observar.

M2 -- Caution
Riesgo moderado. Reducir procesos no esenciales.

M3 -- High Pressure
Puede afectar Cursor/Claude. Checkpoint obligatorio.

M4 -- Critical
OOM probable. Bloquear tareas costosas y liberar memoria.

M5 -- OOM Imminent
Detener actividad no esencial, guardar estado, preparar restart/recovery.

M6 -- OOM Crash Detected
Ejecutar crash recovery al volver.

### 234.3 Suggested Signals

Windows signals:
- available physical memory,
- committed memory,
- process working set,
- Cursor process memory,
- Claude process memory,
- Node helper memory,
- Python hook memory,
- dev server memory,
- browser automation memory,
- Java/Maven memory,
- Docker memory if present,
- system paging pressure.

Generic signals:
- process RSS,
- swap usage,
- high GC churn,
- repeated process kills,
- terminal unresponsive,
- Cursor freeze,
- tool timeout bursts,
- OOM error text,
- exit codes consistent with memory kill.

### 234.4 Memory Pressure Record

MEMORY_PRESSURE_RECORD
timestamp:
workspace_id:
pane_id:
repo_path:
level:
available_memory_mb:
system_memory_percent:
cursor_memory_mb:
claude_memory_mb:
node_memory_mb:
python_memory_mb:
top_processes:
trigger:
action_taken:
checkpoint_created:
recovery_required:
safe_summary:

---

## 235. RAM WATCHDOG

### 235.1 Propósito

Crear watchdog ligero de RAM.

Canonical Name:
RAM Watchdog

Responsabilidad:
- detectar presión de RAM,
- no gastar demasiados recursos,
- no leer secretos,
- no producir ruido,
- activar checkpoints,
- recomendar cleanup,
- bloquear tareas peligrosas si M4+.

### 235.2 Watchdog Requirements

El watchdog debe ser:
- lightweight,
- stdlib-first,
- cross-platform where possible,
- Windows-first for Cursor,
- non-invasive,
- secret-free,
- fail-safe,
- low-frequency enough to avoid overhead,
- event-driven when possible.

### 235.3 Watchdog Triggers

Ejecutar en:
- SessionStart,
- before long task,
- before full repo scan,
- before tests/build,
- before browser automation,
- before dev server launch,
- before multi-pane restore,
- before `/restart`,
- before `/switch-session`,
- before `/parallel-plan`,
- Stop hook,
- crash recovery bootstrap.

### 235.4 Watchdog Output

RAM_WATCHDOG_REPORT
status:
memory_level:
available_mb:
top_risk_processes:
cursor_risk:
claude_risk:
actions_recommended:
actions_taken:
checkpoint_status:
continue_allowed:
reason:

### 235.5 Hard Rule candidata

HR-RAM-WATCHDOG-001:
RAM Watchdog must run before high-memory operations such as full repo scans, large tests, browser automation, multi-pane restore, indexing, dev server launch and long Claude Code tasks.

---

## 236. MEMORY CHECKPOINTING

### 236.1 Propósito

Antes de memoria crítica, guardar estado recuperable.

### 236.2 Checkpoint Types

- pane registry checkpoint,
- terminal topology checkpoint,
- conversation handoff checkpoint,
- backlog checkpoint,
- lock checkpoint,
- cost state checkpoint,
- cascade state checkpoint,
- current task checkpoint,
- clean failure checkpoint,
- restore plan checkpoint.

### 236.3 Memory Checkpoint Schema

MEMORY_SAFETY_CHECKPOINT
checkpoint_id:
timestamp:
workspace_id:
pane_id:
conversation_id:
session_id:
repo_path:
cwd:
task_id:
backlog_item_id:
memory_level:
topology_snapshot_hash:
registry_hash:
handoff_path:
locks:
current_state_summary:
next_safe_action:
secret_scan_status:
safe_to_restore:
created_because:

### 236.4 Checkpoint Rule

At M3+, checkpoint before continuing.
At M4+, checkpoint and reduce memory before continuing.
At M5+, checkpoint and prepare safe shutdown/restart.

### 236.5 Hard Rule candidata

HR-RAM-CHECKPOINT-001:
At high memory pressure, PP must checkpoint pane topology, conversation state, backlog and locks before continuing memory-intensive work.

---

## 237. MEMORY CLEANUP ACTIONS

### 237.1 Propósito

Definir acciones seguras de limpieza.

No toda limpieza debe matar procesos.
Primero se degrada suavemente.

### 237.2 Cleanup Ladder

Level 1 -- Reduce PP noise
- avoid verbose logs,
- pause non-critical advisories,
- skip heavy scans,
- delay backlog regeneration,
- avoid deep research,
- avoid full repo scan.

Level 2 -- Compact state
- write context pack,
- write handoff,
- summarize repeated reads,
- close large in-memory artifacts,
- rotate logs,
- avoid storing raw outputs.

Level 3 -- Stop non-essential child processes
- stale dev servers,
- orphan watchers,
- old test runners,
- unused browser automation,
- duplicate indexers.

Level 4 -- Graceful pane-level restart
- checkpoint current pane,
- `/restart` safely,
- same pane resume.

Level 5 -- Workspace recovery preparation
- checkpoint all panes,
- topology snapshot,
- manual restore plan,
- pause new work.

Level 6 -- Emergency OOM survival
- stop heavy operations,
- mark crash_possible,
- preserve last_known_good_topology,
- exit safely if possible.

### 237.3 Forbidden Cleanup

Do not:
- kill Cursor,
- kill random terminals,
- kill unknown user processes,
- clear registry,
- delete handoffs,
- delete logs needed for recovery,
- close panes without marking clean close,
- kill a pane with uncheckpointed state,
- kill database/dev server if another pane depends on it,
- run broad kill commands,
- use taskkill without process ownership verification.

### 237.4 Hard Rule candidata

HR-RAM-CLEANUP-001:
Memory cleanup must prefer checkpoint, compaction and graceful shutdown over killing processes. Never kill Cursor panes or unknown processes without ownership verification and recovery state.

---

## 238. PROCESS OWNERSHIP MAP

### 238.1 Propósito

Para limpiar RAM sin romper cosas, PP debe saber qué proceso pertenece a qué pane/tarea.

### 238.2 Process Ownership Record

PROCESS_OWNERSHIP
process_id:
parent_process_id:
process_name:
command_safe:
pane_id:
conversation_id:
task_id:
repo_path:
cwd:
started_by:
started_at:
purpose:
memory_mb:
safe_to_stop:
stop_method:
depends_on:
last_seen:
status:

### 238.3 Process Classes

- Claude process
- wrapper process
- Cursor process
- shell process
- Node hook
- Python hook
- dev server
- test runner
- browser automation
- Java/Maven
- Docker container
- indexer
- unknown process

### 238.4 Stop Safety

A process is safe to stop only if:
- PP started it,
- owner pane known,
- task state checkpointed,
- no other pane depends on it,
- stop method defined,
- not Cursor itself,
- not shell hosting active pane,
- not database unless safe,
- not production process.

### 238.5 Hard Rule candidata

HR-RAM-PROCESS-001:
PP may only stop memory-heavy processes that it can attribute to a pane/task and classify as safe_to_stop. Unknown processes must not be killed automatically.

---

## 239. OOM CRASH DETECTION

### 239.1 Propósito

Detectar que un crash probablemente fue por OOM.

### 239.2 Signals

- OS event log contains OOM/resource exhaustion,
- process exit code indicates memory failure,
- Cursor vanished without clean shutdown,
- Claude process killed abruptly,
- high memory pressure before heartbeat loss,
- swap/paging spike,
- “JavaScript heap out of memory”,
- “Allocation failed”,
- “ENOMEM”,
- “OutOfMemoryError”,
- Python MemoryError,
- Node heap fatal error,
- Windows low memory notification,
- terminal disappeared without clean close.

### 239.3 OOM Confidence

OOM0:
No evidence.

OOM1:
Memory pressure was elevated.

OOM2:
Crash after high memory.

OOM3:
OOM-like error detected.

OOM4:
OS/process confirms OOM.

### 239.4 OOM Recovery Trigger

OOM2+:
- treat as crash_suspected,
- topology recovery required.

OOM3+:
- add RAM incident record,
- generate prevention backlog.

OOM4:
- create OOM autopsy.

---

## 240. OOM INCIDENT RECORD

### 240.1 Schema

OOM_INCIDENT
incident_id:
timestamp:
workspace_id:
repo_path:
affected_panes:
memory_level_before:
oom_confidence:
suspected_root_process:
top_memory_processes:
lost_processes:
topology_preserved:
recovery_plan_created:
panes_restored:
manual_required:
data_loss_risk:
secret_risk:
cost_impact:
prevention_actions:
backlog_items_created:
status:

### 240.2 Incident Rule

Every OOM crash should produce:
- incident record,
- recovery plan,
- prevention backlog item,
- hard rule candidate if repeated.

---

## 241. OOM AUTOPSY

### 241.1 Propósito

Entender por qué ocurrió OOM para evitar repetición.

### 241.2 Autopsy Questions

- Qué proceso consumía más RAM?
- Qué tarea lo inició?
- Qué pane lo tenía asignado?
- Había full repo scan?
- Había browser automation?
- Había test runner pesado?
- Había dev server huérfano?
- Había múltiples Claude sessions?
- Había indexación grande?
- Había logs enormes?
- Había output gigante?
- Hubo cost firebreak previo?
- Hubo checkpoint?
- Se restauró topología?

### 241.3 OOM Autopsy Output

OOM_AUTOPSY
root_cause:
contributing_factors:
affected_panes:
lost_state:
recovered_state:
memory_peak_estimate:
prevention:
cleanup_actions:
new_limits:
hard_rule_candidate:
backlog_items:

---

## 242. RAM-AWARE PARALLEL PANE EXECUTION

### 242.1 Problema

Varios panes paralelos multiplican uso de RAM.

3 terminales con Claude + tests + dev servers pueden llevar Cursor a OOM.

### 242.2 RAM Budget Per Pane

Cada pane debe tener presupuesto aproximado:

PANE_RAM_BUDGET
pane_id:
task_id:
expected_memory_mb:
max_memory_mb:
current_memory_mb:
memory_class:
can_run_parallel:
heavy_processes_allowed:
checkpoint_required:
status:

### 242.3 Task Memory Classes

MC0 -- Light
Docs, prompt, backlog.

MC1 -- Moderate
Small code edits, grep, unit tests.

MC2 -- Heavy
Full test suite, build, index, large file scans.

MC3 -- Very Heavy
Browser automation, video/image processing, Docker, Java builds.

MC4 -- Critical
Multiple heavy processes, full workspace indexing, huge datasets.

### 242.4 Parallel Safety Rule

No more than one MC3/MC4 task should run in parallel unless system RAM is clearly sufficient.

### 242.5 Hard Rule candidata

HR-RAM-PARALLEL-001:
Parallel pane execution must consider RAM budget. Do not schedule multiple heavy memory tasks across panes without memory capacity check and checkpoint.

---

## 243. RAM-AWARE BACKLOG ROUTER

### 243.1 Propósito

El backlog por pane debe considerar RAM.

Si RAM está alta:
- asignar tareas ligeras,
- pausar heavy tasks,
- mover builds/tests a momentos controlados,
- evitar multi-pane heavy execution.

### 243.2 RAM-Aware Assignment

Backlog item must include:

- memory_class,
- expected_peak_mb,
- can_parallelize,
- requires_checkpoint,
- safe_when_memory_level:
- forbidden_when_memory_level:

### 243.3 Assignment Rule

At M3:
- avoid MC3/MC4 unless urgent.

At M4:
- only MC0/MC1 allowed.

At M5:
- no new work; checkpoint/recovery only.

### 243.4 RAM-Aware Next Best Action

If memory pressure high, `/what-now` should recommend:
- checkpoint,
- cleanup,
- close orphan processes,
- split task,
- create context pack,
- run lighter validation,
- defer heavy build.

---

## 244. RAM-AWARE CONTEXT MANAGEMENT

### 244.1 Problema

Context bloat increases memory and cost.

### 244.2 Actions

- prefer context packs,
- avoid loading huge datasets,
- avoid repeated full file reads,
- summarize before continuing,
- compact before long tasks,
- split task into phases,
- avoid large generated outputs,
- rotate logs,
- limit evidence size.

### 244.3 Context Memory Rule

HR-RAM-CONTEXT-001:
If context or output grows large during high memory pressure, PP must create compact artifacts and stop repeated raw loading before continuing.

---

## 245. DEV SERVER AND ORPHAN PROCESS CLEANUP

### 245.1 Problema

Dev servers, watchers, test runners and browsers often survive after tasks and consume RAM.

### 245.2 Orphan Detection

A process may be orphan if:
- parent pane closed,
- task completed,
- no heartbeat,
- port still open,
- process cwd matches repo,
- command matches known dev server,
- no active lock references it.

### 245.3 Safe Cleanup Flow

1. identify process,
2. map to pane/task,
3. verify no dependency,
4. checkpoint if needed,
5. graceful stop,
6. verify stopped,
7. record cleanup.

### 245.4 Forbidden

Do not kill:
- database with active pane dependency,
- production tunnel,
- Cursor,
- shell,
- active Claude process,
- unknown process,
- process outside repo ownership.

### 245.5 Hard Rule candidata

HR-RAM-ORPHAN-001:
Orphan process cleanup must verify repo/pane ownership and dependency status before stopping memory-heavy processes.

---

## 246. MEMORY-SAFE TEST EXECUTION

### 246.1 Problema

Test suites can trigger OOM.

### 246.2 Test Memory Policy

Before running heavy tests:
- check RAM level,
- know test memory class,
- checkpoint pane,
- avoid parallel heavy tests,
- set timeouts,
- capture limited output,
- scan output for secrets,
- avoid huge logs.

### 246.3 If RAM High

Use:
- targeted tests,
- single test file,
- dry run,
- static validation,
- smaller command.

### 246.4 Hard Rule candidata

HR-RAM-TEST-001:
Do not run memory-heavy full test/build suites under high memory pressure. Use targeted validation or checkpoint first.

---

## 247. MEMORY-SAFE INDEXING

### 247.1 Problema

Indexing repos, datasets or logs can consume huge RAM.

### 247.2 Rules

- chunk input,
- stream processing,
- avoid loading all files at once,
- skip generated/binary/large files,
- secret scan before indexing,
- cap file size,
- persist incremental index,
- resume indexing after crash.

### 247.3 Hard Rule candidata

HR-RAM-INDEX-001:
Indexing must be streaming, chunked, size-capped, secret-safe and resumable. Never load entire large repo/dataset into memory when incremental indexing works.

---

## 248. MEMORY-SAFE EVIDENCE

### 248.1 Problema

Huge logs/evidence can blow RAM and leak secrets.

### 248.2 Evidence Limits

Evidence should store:
- command,
- exit code,
- last N lines,
- summarized failure,
- path to full local log if safe,
- secret scan status.

Avoid:
- huge stdout,
- full build logs,
- full traces,
- full transcripts,
- raw browser dumps.

### 248.3 Evidence Rule

HR-RAM-EVIDENCE-001:
Evidence capture must be size-limited, secret-scanned and summarized. Do not store unbounded command output.

---

## 249. MEMORY-SAFE WRAPPER

### 249.1 Propósito

`claude-pp` wrapper itself must not cause memory issues.

### 249.2 Wrapper RAM Rules

- do not buffer full Claude output,
- stream where possible,
- store only metadata,
- limit log size,
- rotate logs,
- avoid reading huge registry into memory repeatedly,
- use atomic small JSON writes,
- avoid spawning duplicate watchers.

### 249.3 Wrapper OOM Handling

If wrapper detects memory critical:
- write checkpoint,
- mark pane memory_critical,
- avoid launching heavy resume,
- show manual recovery if needed.

### 249.4 Hard Rule candidata

HR-RAM-WRAPPER-001:
The wrapper must not buffer full terminal output or transcripts in memory. It should stream, summarize and store metadata only.

---

## 250. MEMORY-SAFE CURSOR TOPOLOGY RESTORE

### 250.1 Problema

Restoring many panes at once can spike RAM.

### 250.2 Restore Strategy

If N panes need restore:
- compute memory level first,
- restore sequentially if RAM limited,
- restore critical panes first,
- delay low-priority panes,
- create manual plan for remaining panes,
- avoid launching all heavy sessions simultaneously.

### 250.3 Restore Modes

RT0:
Restore all panes automatically.

RT1:
Restore sequentially.

RT2:
Restore critical panes, manual for rest.

RT3:
Manual restore only.

RT4:
Recovery blocked until memory improves.

### 250.4 Hard Rule candidata

HR-RAM-RESTORE-001:
Crash recovery must be RAM-aware. Do not restore all panes simultaneously if memory pressure is high; restore sequentially or provide manual plan.

---

## 251. RAM HEALTH DASHBOARD

### 251.1 Propósito

Mostrar al Owner estado de RAM sin ruido.

### 251.2 Command

Future command:

```text
/ram-status

Output: RAM_STATUS memory_level: available_mb: cursor_memory: claude_sessions: heavy_processes: orphan_candidates: pane_budgets: recommendation:

251.3 Other Commands

/ram-clean
/ram-checkpoint
/ram-autopsy
/oom-recover
/oom-autopsy

251.4 No Noise Rule

No alertar por RAM normal. Alertar en M3+ o si hay trend peligroso.


---

252. OOM RECOVERY COMMAND

252.1 /oom-recover

Propósito: Recuperar tras OOM crash.

Flow:

1. detect last known topology,


2. detect OOM confidence,


3. build topology restore plan,


4. check current RAM,


5. choose restore mode,


6. restore/manual plan,


7. generate OOM incident.



252.2 Output

OOM_RECOVERY_REPORT oom_confidence: last_topology: current_memory: restore_mode: panes_to_restore: manual_commands: blocked_panes: prevention_backlog: next_safe_action:


---

253. RAM AND SECRET SAFETY

253.1 Problema

RAM dumps, logs and crash reports can contain secrets.

253.2 Rule

Do not generate memory dumps automatically.

If crash reports exist:

scan/redact before storing,

do not upload,

do not paste,

do not commit,

do not index.


253.3 Hard Rule candidata

HR-RAM-SECRET-001: Memory dumps, crash reports and large diagnostic logs may contain secrets. Treat them as secret-bearing until scanned and redacted.


---

254. RAM CASCADE PREVENTION

254.1 RAM Cascade Pattern

High RAM -> tool timeout -> repeated retries -> more processes -> Cursor freeze -> no clean shutdown -> topology recovery -> duplicate restore risk.

254.2 Prevention

RAM Watchdog,

cost firebreak,

retry limits,

process ownership,

checkpoint at M3,

stop at M5,

topology manifest,

sequential restore.


254.3 Hard Rule candidata

HR-RAM-CASCADE-001: Repeated tool failures under high memory pressure must trigger RAM cascade containment, not more retries.


---

255. RAM-AWARE AUTONOMY LADDER

255.1 Autonomy by RAM Level

M0-M1: Normal autonomy.

M2: Autonomy allowed, monitor.

M3: High-risk tasks require checkpoint.

M4: Only low-memory tasks and cleanup.

M5: No new work. Checkpoint and prepare recovery.

M6: Recovery only.

255.2 Rule

Memory pressure lowers autonomy level automatically.


---

256. TESTS FOR RAM STEWARDSHIP OS

256.1 Test: Memory Pressure Escalation

Simulate M0 -> M5.

Expected:

watchdog records levels,

checkpoint at M3,

cleanup recommendation at M4,

no new work at M5.


256.2 Test: OOM Crash Recovery

Simulate OOM crash with 3 panes.

Expected:

crash_suspected,

OOM incident,

topology restore plan,

no pane loss.


256.3 Test: Orphan Process Cleanup

Simulate dev server from closed pane.

Expected:

identified as orphan,

safe_to_stop true only if no dependencies.


256.4 Test: Unknown Process Not Killed

Expected:

unknown process not killed.


256.5 Test: Heavy Parallel Tasks Blocked

Expected:

MC3 + MC3 parallel blocked under limited RAM.


256.6 Test: Evidence Size Limit

Expected:

huge output summarized,

not stored raw.


256.7 Test: Memory Dump Treated As Secret

Expected:

crash dump classified secret-bearing.


256.8 Test: Sequential Restore Under High RAM

Expected:

not all panes restored at once.


256.9 Test: Wrapper Does Not Buffer Full Output

Expected:

wrapper logs metadata only.


256.10 Test: Repeated Failures Under High RAM

Expected:

RAM cascade containment, not retries.



---

257. IMPLEMENTATION PHASES

Phase A -- RAM Watchdog MVP

Implement:

memory level detection,

process summary,

/ram-status,

lightweight reports.


Phase B -- Checkpoint on Memory Pressure

Implement:

M3 checkpoint,

topology snapshot,

handoff snapshot,

backlog/lock snapshot.


Phase C -- Safe Cleanup

Implement:

process ownership map,

orphan detection,

safe stop plan,

no unknown kills.


Phase D -- OOM Detection

Implement:

OOM confidence,

OOM incident record,

/oom-autopsy.


Phase E -- OOM Recovery

Implement:

/oom-recover,

topology restore plan integration,

RAM-aware restore mode.


Phase F -- RAM-Aware Backlog

Implement:

memory_class per backlog item,

RAM-aware pane assignment,

heavy task blocking.


Phase G -- Chaos Tests

Implement:

simulated OOM,

high RAM retry loop,

partial restore,

orphan process cleanup.



---

258. CLAUDE CODE PROMPT FOR PART XII

PROMPT:

Act as the implementation engineer for Claude Power Pack RAM Stewardship OS.

MISSION: Implement a RAM care and OOM survival layer that prevents memory pressure from destroying Cursor Pane Continuity OS, preserves terminal topology, checkpoints active work, safely cleans orphan processes, and restores after OOM crashes.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing CPC-OS, Lazarus, terminal-slot, restart, TIS/TCO, orphan-dev-server-reaper or monitoring components if present.

NON-NEGOTIABLES:

Do not kill Cursor.

Do not kill unknown processes.

Do not kill active pane shells.

Do not trust old PIDs after crash/reboot.

Do not open external CMD.

Do not store raw secrets in crash reports, logs, handoffs, topology, memory reports or evidence.

Do not generate memory dumps automatically.

Do not run memory-heavy tests/builds under high memory pressure without checkpoint.

Do not restore all panes simultaneously if RAM is critical.

Do not start unrelated work after suspected OOM crash before recovery check.


STARTING PHASE: Implement Phase A + Phase B only:

1. RAM Watchdog MVP.


2. Memory pressure levels.


3. /ram-status.


4. Checkpoint trigger at high memory.


5. Integration with topology manifest/checkpoint if present.


6. Tests for memory pressure escalation.



REQUIRED OUTPUT:

files changed,

tests added,

tests run,

RAM levels implemented,

checkpoint behavior,

secret safety status,

process killing status,

remaining risks,

next phase.


STOP IF:

process ownership cannot be verified,

a cleanup action would kill unknown process,

memory report may contain secrets,

implementation requires broad refactor,

Cursor/CPC state is not understood.


ACCEPTANCE:

M0-M5 pressure simulation works.

M3 triggers checkpoint.

M5 blocks new work.

/ram-status produces concise report.

No raw secrets stored.

No process is killed in MVP.

Tests pass.



---

259. PART XII CANONICAL PRINCIPLES

259.1 RAM Is Execution Infrastructure

Memory pressure can break continuity, cost, output, backlog and recovery.

259.2 OOM Is a Crash Class

OOM must trigger topology recovery, not normal restart assumptions.

259.3 Checkpoint Before Critical Memory

At high RAM pressure, preserve state before pushing forward.

259.4 Cleanup Must Be Safe

Never kill unknown processes. Never kill Cursor. Never kill active pane shells.

259.5 Parallel Work Needs RAM Budget

Multiple panes multiply memory pressure.

259.6 Restore Sequentially If Needed

After OOM, restoring all panes at once may recreate the crash.

259.7 Logs And Dumps May Contain Secrets

Memory diagnostics are secret-bearing until scanned.

259.8 High Memory Means Lower Autonomy

The system must become more conservative as RAM pressure rises.

259.9 A Failed Heavy Task Should Not Be Retried Blindly

Under RAM pressure, repeated retries create cascades.

259.10 Survive First, Then Continue

When memory is unstable, preserve topology, handoff, backlog and locks before doing more work.

END OF PART XII.

Continuación directa sobre el Claude Power Pack actual y las extensiones CPC-OS/RAM Stewardship que venimos construyendo. El baseline ya documenta hooks de sesión, Lazarus/restart-related tooling, budget monitor, orphan-dev-server-reaper, TIS/TCO y proactive agents, así que esta Parte XIII debe integrarse encima de eso, no duplicarlo. 

