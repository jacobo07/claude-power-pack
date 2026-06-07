# PP Dataset Part XIII -- Resource Governor OS: RAM, CPU, Disk, Process, Pane and Workload Degradation for Cursor + Claude Code Survival

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 18092-19352 (1261 lines)
**Part number:** 13 (roman XIII)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XIII
# Resource Governor OS: RAM, CPU, Disk, Process, Pane and Workload Degradation for Cursor + Claude Code Survival

## 260. RESOURCE GOVERNOR OS

### 260.1 Propósito

Claude Power Pack debe añadir una capa superior de gobierno de recursos.

La Parte XII define RAM Stewardship OS y supervivencia a OOM.
La Parte XIII amplía esa visión:

No solo RAM.
También:
- CPU,
- procesos huérfanos,
- disco,
- logs,
- watchers,
- dev servers,
- test runners,
- indexing,
- browser automation,
- pane count,
- parallel workload,
- terminal topology,
- Claude context,
- output size,
- evidence size,
- retry loops.

Canonical Name:
Resource Governor OS

Abreviatura:
RG-OS

Objetivo:
Evitar que el entorno de desarrollo se degrade hasta romper Cursor, Claude Code, terminales, panes, registry, backlog o recoverability.

### 260.2 Principio central

A project can crash from resource debt before it crashes from code bugs.

El Power Pack debe prevenir deuda de recursos igual que previene:
- secret leaks,
- bug cascades,
- cost explosion,
- output drift,
- pane collision.

### 260.3 Regla central

Antes de cualquier tarea pesada, PP debe estimar:
- RAM pressure,
- CPU pressure,
- disk/log pressure,
- process pressure,
- pane pressure,
- context pressure,
- recovery readiness.

Si el entorno no está sano, debe degradar, pausar o dividir la tarea.

### 260.4 Hard Rule candidata

HR-RESOURCE-001:
Claude Power Pack must not start heavy work if RAM, CPU, disk, pane, process or context pressure is above safe thresholds without checkpoint, degradation plan and recovery path.

---

## 261. RESOURCE PRESSURE VECTOR

### 261.1 Propósito

Un solo número de RAM no basta.

Crear un vector de presión de recursos.

RESOURCE_PRESSURE_VECTOR
timestamp:
workspace_id:
repo_path:
pane_id:
ram_level:
cpu_level:
disk_level:
process_level:
pane_level:
context_level:
log_level:
test_level:
browser_level:
indexing_level:
overall_level:
recommended_mode:
actions_required:

### 261.2 Levels

Cada dimensión usa:

R0 -- Normal
R1 -- Watch
R2 -- Caution
R3 -- High
R4 -- Critical
R5 -- Emergency
R6 -- Crash Recovery

### 261.3 Overall Level

overall_level = max(weighted levels)

Weights:
- secret-bearing resource issue: critical boost.
- RAM M4+: critical boost.
- disk almost full: critical boost.
- duplicate panes/session collision: critical boost.
- OOM suspected: recovery mode.
- registry corruption: recovery mode.

### 261.4 Rule

The highest-risk resource dimension controls autonomy.

If RAM is critical but CPU is normal, system still enters critical mode.

---

## 262. GRACEFUL DEGRADATION MODES

### 262.1 Propósito

Cuando hay presión de recursos, el sistema no debe fallar de golpe.
Debe degradar.

### 262.2 Modes

D0 -- Full Capability
Todo permitido.

D1 -- Lightweight Mode
Reducir output, evitar scans amplios, mantener hooks esenciales.

D2 -- Checkpoint Mode
Guardar estado antes de seguir.

D3 -- Conservative Mode
Solo tareas ligeras, targeted tests, no browser/dev heavy.

D4 -- Recovery-First Mode
No new feature work. Cleanup/checkpoint/recovery only.

D5 -- Emergency Preservation Mode
Preservar topología, handoff, backlog, locks. Preparar safe exit.

D6 -- Restore Mode
Tras crash/OOM. Recuperar antes de trabajar.

### 262.3 Degradation Decision

DEGRADATION_DECISION
current_mode:
trigger:
blocked_actions:
allowed_actions:
required_checkpoints:
cleanup_actions:
manual_actions:
resume_condition:

### 262.4 Hard Rule candidata

HR-RESOURCE-DEGRADE-001:
Under critical resource pressure, PP must degrade capability rather than continue normal autonomous execution.

---

## 263. WORKLOAD CLASSIFIER

### 263.1 Propósito

Cada tarea debe clasificarse por consumo de recursos antes de ejecutarse.

### 263.2 Workload Classes

WC0 -- Tiny
- docs,
- small prompt,
- small backlog item,
- no commands.

WC1 -- Light
- grep,
- small file read,
- small code edit,
- targeted lint.

WC2 -- Moderate
- targeted tests,
- small module implementation,
- small index update.

WC3 -- Heavy
- full test suite,
- builds,
- large repo scans,
- multi-file refactor,
- dev server.

WC4 -- Very Heavy
- browser automation,
- Docker,
- Java/Maven large build,
- media processing,
- large dataset indexing.

WC5 -- Dangerous Under Pressure
- multi-pane heavy work,
- full workspace restore,
- full repo + tests + browser,
- unknown script,
- process cleanup without ownership.

### 263.3 Workload Record

WORKLOAD_RECORD
task_id:
pane_id:
class:
estimated_ram:
estimated_cpu:
estimated_disk:
estimated_duration:
parallel_safe:
requires_checkpoint:
requires_exclusive_lock:
forbidden_under_levels:
validation:
fallback_lighter_task:

### 263.4 Rule

WC3+ requires resource check.
WC4+ requires checkpoint.
WC5 requires explicit safe plan.

---

## 264. PANE PRESSURE CONTROL

### 264.1 Propósito

El número de panes abiertos también es un recurso.

Cada pane puede tener:
- Claude process,
- shell,
- wrapper,
- hooks,
- dev server,
- test runner,
- logs,
- context.

### 264.2 Pane Pressure

PANE_PRESSURE
active_panes:
busy_panes:
heavy_panes:
stale_panes:
recovery_pending_panes:
duplicate_conversation_risk:
parallel_heavy_count:
recommended_action:

### 264.3 Pane Pressure Rules

If active_panes high and memory pressure high:
- pause low-priority panes,
- restore sequentially,
- avoid opening new panes,
- do not run parallel heavy tasks.

If stale_panes exist:
- recover or close intentionally before starting new parallel work.

If duplicate conversation risk:
- block new resume.

### 264.4 Hard Rule candidata

HR-PANE-PRESSURE-001:
Do not open, restore or assign additional Cursor panes when pane pressure and RAM pressure are high unless recovery requires it and restore is sequential.

---

## 265. PAUSE / RESUME SYSTEM FOR PANES

### 265.1 Propósito

No siempre hay que cerrar o matar panes.
A veces hay que pausar.

Canonical Name:
Pane Pause/Resume System

### 265.2 Pause Reasons

- high RAM,
- high CPU,
- heavy task in another pane,
- collision risk,
- dependency wait,
- recovery pending,
- Owner low energy,
- cost firebreak,
- stale context,
- secret incident.

### 265.3 Pause Record

PANE_PAUSE_RECORD
pane_id:
conversation_id:
task_id:
reason:
paused_at:
handoff_path:
locks_retained:
locks_released:
resume_condition:
safe_resume_command:
status:

### 265.4 Pause Flow

1. checkpoint pane,
2. write handoff,
3. release non-critical locks,
4. retain critical task ownership if needed,
5. mark pane paused,
6. avoid killing terminal unless needed.

### 265.5 Resume Flow

1. verify resource pressure improved,
2. verify conversation ownership,
3. verify cwd,
4. verify task still valid,
5. restore locks,
6. resume.

### 265.6 Hard Rule candidata

HR-PANE-PAUSE-001:
Under resource pressure, prefer pausing/checkpointing low-priority panes over killing terminals or losing topology.

---

## 266. CPU PRESSURE GOVERNANCE

### 266.1 Propósito

CPU saturation causes:
- Cursor freeze,
- tool timeouts,
- false crash detection,
- retry loops,
- slow tests,
- poor interactivity,
- watchdog delays.

### 266.2 CPU Levels

C0 Normal
C1 Watch
C2 Caution
C3 High
C4 Critical
C5 Saturated
C6 Recovery

### 266.3 CPU Risk Processes

- test runners,
- TypeScript compilers,
- Java/Maven,
- Docker,
- browser automation,
- indexing,
- multiple Claude processes,
- dev servers,
- hot reload watchers,
- video/image processing.

### 266.4 CPU Actions

At C3:
- avoid new heavy task,
- reduce parallelism,
- delay indexing.

At C4:
- checkpoint,
- pause low-priority panes,
- stop orphan CPU-heavy processes if owned.

At C5:
- no new work,
- recovery/prevention only.

### 266.5 Hard Rule candidata

HR-CPU-001:
Repeated tool timeouts under high CPU must trigger resource containment, not blind retries.

---

## 267. DISK AND LOG PRESSURE GOVERNANCE

### 267.1 Problema

Disk/log pressure can break:
- registry writes,
- journal writes,
- evidence storage,
- tests,
- builds,
- recovery snapshots,
- Cursor stability.

### 267.2 Disk Pressure Signals

- low free disk,
- huge logs,
- runaway evidence files,
- build artifacts,
- node_modules bloat,
- target/build dirs,
- coverage reports,
- screenshots/videos,
- repeated cold boot evidence,
- crash reports,
- dumps.

### 267.3 Disk Levels

D0 Normal
D1 Watch
D2 Caution
D3 Low Space
D4 Critical
D5 Write Unsafe
D6 Recovery Blocked

### 267.4 Disk Actions

At D3:
- rotate logs,
- summarize evidence,
- delete safe temp files,
- avoid heavy build artifacts.

At D4:
- checkpoint minimal,
- block large evidence writes,
- block indexing,
- block full builds unless needed.

At D5:
- do not attempt operations requiring reliable writes,
- preserve minimal recovery state only.

### 267.5 Hard Rule candidata

HR-DISK-001:
If disk space is critically low, PP must avoid large writes, evidence dumps, indexing and builds, and prioritize preserving minimal recovery state.

---

## 268. LOG ROTATION AND EVIDENCE LIMITS

### 268.1 Propósito

Evitar que logs/evidence crezcan indefinidamente.

### 268.2 Log Rotation Policy

Each runtime log should have:
- max size,
- max files,
- compression optional,
- secret scan before archive,
- deletion policy,
- local-only classification.

### 268.3 Evidence Size Policy

Evidence should store:
- summary,
- command,
- exit code,
- last relevant lines,
- path to local raw log only if safe,
- secret scan status.

Avoid:
- full logs,
- full transcripts,
- repeated stdout,
- large traces,
- binary dumps.

### 268.4 Hard Rule candidata

HR-LOG-001:
Runtime logs and evidence must be size-limited, rotated, secret-scanned and summarized. Unbounded logs are prohibited.

---

## 269. RETRY LOOP GOVERNANCE

### 269.1 Problema

Retries bajo presión de recursos causan cascadas.

Pattern:
command fails -> retry -> memory rises -> timeout -> retry -> Cursor freezes -> crash.

### 269.2 Retry Budget

RETRY_BUDGET
operation:
max_retries:
current_retries:
failure_reason:
resource_level:
new_information_between_retries:
continue_allowed:
fallback:

### 269.3 Retry Rules

Retry only if:
- failure reason understood,
- resource pressure acceptable,
- new information or changed condition exists,
- retry will not duplicate side effects.

No retry if:
- OOM suspected,
- CPU saturated,
- same error twice,
- command heavy,
- no new info,
- secret risk,
- registry corruption.

### 269.4 Hard Rule candidata

HR-RETRY-001:
Do not retry failed heavy operations under resource pressure unless new information or changed conditions make success materially more likely.

---

## 270. DEV SERVER GOVERNOR

### 270.1 Propósito

Dev servers are major resource sources.

### 270.2 Dev Server Registry

DEV_SERVER_RECORD
server_id:
pane_id:
task_id:
repo_path:
cwd:
command_safe:
port:
process_id:
started_at:
last_used_at:
memory_mb:
cpu_percent:
owner:
safe_to_stop:
dependencies:
status:

### 270.3 Rules

- register every dev server PP starts,
- do not start duplicate server on same port,
- detect orphan servers,
- stop only owned and safe,
- avoid running multiple heavy dev servers under high RAM.

### 270.4 Hard Rule candidata

HR-DEVSERVER-001:
PP must register dev servers it starts and avoid duplicate/orphan servers consuming resources.

---

## 271. BROWSER AUTOMATION GOVERNOR

### 271.1 Problema

Browser automation can explode RAM.

### 271.2 Rules

Before browser automation:
- RAM check,
- CPU check,
- checkpoint,
- max browser instances,
- timeout,
- close browser after task,
- avoid parallel browser tasks,
- capture bounded evidence.

### 271.3 Browser Record

BROWSER_TASK_RECORD
task_id:
pane_id:
browser_processes:
memory_budget:
timeout:
evidence_limit:
closed_after:
status:

### 271.4 Hard Rule candidata

HR-BROWSER-001:
Browser automation must be bounded by RAM, timeout, instance count and evidence size. Browser processes must be closed or registered after use.

---

## 272. INDEXING GOVERNOR

### 272.1 Propósito

Indexing is useful for cost reduction but risky for RAM/disk.

### 272.2 Indexing Rules

- chunked,
- streaming,
- resumable,
- file size caps,
- binary skip,
- generated dir skip,
- secret scan,
- checkpoint,
- disk check,
- memory check.

### 272.3 Index Job Record

INDEX_JOB
job_id:
repo_path:
started_at:
status:
files_seen:
files_indexed:
files_skipped:
memory_peak:
disk_written:
resume_cursor:
secret_findings:
safe_to_resume:

### 272.4 Hard Rule candidata

HR-INDEX-GOV-001:
All indexing jobs must be chunked, resumable, resource-bounded and secret-safe.

---

## 273. BUILD AND TEST GOVERNOR

### 273.1 Propósito

Full builds/tests can cause CPU/RAM spikes.

### 273.2 Build/Test Decision

Before running:
- what is the smallest validation?
- is full suite necessary?
- what changed?
- can targeted test prove enough?
- current resource pressure?
- expected duration?
- output limit?

### 273.3 Build/Test Modes

BT0 static check
BT1 targeted test
BT2 module test
BT3 full test
BT4 full build
BT5 integration/browser
BT6 production-like

### 273.4 Rule

Use smallest validation sufficient for claim.
Full suite only when needed or before merge/deploy.

### 273.5 Hard Rule candidata

HR-BUILDTEST-001:
Build/test execution must choose the smallest validation level sufficient for the claim under current resource pressure.

---

## 274. RESOURCE-AWARE CPC RESTORE

### 274.1 Propósito

Integrar RG-OS con CPC-OS recovery.

### 274.2 Restore Decision Inputs

- expected pane count,
- current RAM,
- current CPU,
- disk safety,
- number of Claude sessions,
- heavy task flags,
- priority per pane,
- dependency order,
- Owner preference.

### 274.3 Restore Modes

RM0 Full auto restore.
RM1 Sequential auto restore.
RM2 Critical panes first.
RM3 Manual exact restore.
RM4 Recovery blocked until resources improve.

### 274.4 Rule

If resources are critical after crash, restore topology in safest possible mode, not fastest possible mode.

### 274.5 Hard Rule candidata

HR-RESOURCE-RESTORE-001:
CPC-OS restore must consider current resource pressure and may restore panes sequentially or manually to avoid immediate repeat crash.

---

## 275. RESOURCE-AWARE WHAT-NOW MODE

### 275.1 Propósito

Cuando Owner pida “qué hago ahora”, el sistema debe mirar recursos.

### 275.2 If Resources Normal

Recommend highest ROI task.

### 275.3 If RAM/CPU High

Recommend:
- checkpoint,
- cleanup,
- pause panes,
- run light docs/backlog task,
- split heavy task,
- close orphan process,
- summarize context.

### 275.4 If Disk Low

Recommend:
- log cleanup,
- evidence rotation,
- remove safe build artifacts,
- avoid indexing/builds.

### 275.5 If Recovery Pending

Recommend:
- recovery first,
- no unrelated task.

### 275.6 Hard Rule candidata

HR-WHATNOW-RESOURCE-001:
Next-best-action must account for resource pressure. Do not recommend heavy tasks when the environment is unstable.

---

## 276. RESOURCE INCIDENT RECORD

### 276.1 Propósito

Registrar incidentes de recursos para aprender.

RESOURCE_INCIDENT
incident_id:
timestamp:
workspace_id:
repo_path:
type:
level:
trigger:
affected_panes:
affected_tasks:
root_cause:
actions_taken:
state_preserved:
data_loss:
secret_risk:
recovery_status:
prevention_backlog:
hard_rule_candidate:

### 276.2 Incident Types

- OOM
- CPU saturation
- disk full
- log explosion
- retry loop
- orphan process
- duplicate dev server
- browser runaway
- indexing runaway
- parallel pane overload
- Cursor freeze
- terminal topology loss

### 276.3 Rule

Repeated resource incidents must generate backlog and hard rule candidates.

---

## 277. RESOURCE AUTOPSY

### 277.1 Propósito

Después de incidente, hacer autopsia.

RESOURCE_AUTOPSY
incident:
timeline:
root_cause:
trigger_task:
trigger_pane:
trigger_process:
resource_peak:
preventable:
missed_warning:
checkpoint_status:
recovery_status:
future_prevention:
backlog:
hard_rules:

### 277.2 Questions

- qué tarea disparó presión?
- qué pane la ejecutaba?
- había checkpoint?
- había procesos huérfanos?
- había parallel heavy workload?
- había retry loop?
- logs/evidence crecieron?
- se preservó topología?
- se restauró correctamente?

---

## 278. RESOURCE DASHBOARD COMMANDS

### 278.1 Commands

```text
/resource-status
/resource-clean
/resource-autopsy
/resource-mode
/processes-owned
/devservers
/pane-pressure
/log-clean
/retry-budget

278.2 /resource-status

Output: RESOURCE_STATUS overall_level: ram: cpu: disk: panes: processes: logs: recommendation: blocked_actions:

278.3 /resource-clean

Must:

propose cleanup,

not kill unknown processes,

not delete unsafe logs,

not remove recovery artifacts,

require confirmation for destructive cleanup.


278.4 /resource-mode

Shows current degradation mode.


---

279. RESOURCE GOVERNOR TESTS

279.1 Test: Resource Vector

Simulate high RAM, normal CPU, normal disk.

Expected:

overall high,

autonomy reduced.


279.2 Test: Critical Disk

Expected:

large evidence writes blocked,

minimal recovery state preserved.


279.3 Test: Retry Loop

Same heavy command fails twice under high RAM.

Expected:

third retry blocked,

resource incident created.


279.4 Test: Pane Pressure

Many panes + high RAM.

Expected:

new pane blocked,

pause suggested.


279.5 Test: Dev Server Duplicate

Starting same port twice.

Expected:

duplicate blocked.


279.6 Test: Browser Runaway

Expected:

timeout and cleanup plan.


279.7 Test: Indexing Large Files

Expected:

chunking,

skip binary/large,

no full memory load.


279.8 Test: Resource-Aware Recovery

OOM crash with 4 panes and high RAM on restart.

Expected:

sequential/critical-first restore, not all at once.


279.9 Test: Resource-Aware What Now

High CPU/RAM.

Expected:

recommends cleanup/checkpoint/light task.


279.10 Test: Unknown Process Protection

Expected:

unknown process not killed.



---

280. IMPLEMENTATION PHASES

Phase A -- Resource Vector

Implement:

RAM/CPU/disk/pane/process/log levels,

/resource-status,

no destructive actions.


Phase B -- Degradation Modes

Implement:

D0-D6,

blocked actions,

allowed actions,

checkpoint requirement.


Phase C -- Workload Classifier

Implement:

WC0-WC5,

memory/cpu/disk flags,

integration with backlog.


Phase D -- Process Ownership

Implement:

owned process registry,

dev server registry,

orphan detection,

no unknown kills.


Phase E -- Retry Governor

Implement:

retry budgets,

heavy retry blocking,

incident records.


Phase F -- Resource-Aware CPC Restore

Implement:

restore mode based on pressure,

sequential restore,

critical panes first.


Phase G -- Autopsy and Dashboard

Implement:

resource incidents,

resource autopsy,

dashboard commands.



---

281. CLAUDE CODE PROMPT FOR PART XIII

PROMPT:

Act as the implementation engineer for Claude Power Pack Resource Governor OS.

MISSION: Implement a resource governance layer that prevents RAM/CPU/disk/process/pane pressure from crashing Cursor, Claude Code or CPC-OS, and that degrades execution safely under pressure.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing RAM Stewardship, CPC-OS, orphan-dev-server-reaper, monitoring, TIS/TCO, hooks and session tools if present.

NON-NEGOTIABLES:

Do not kill Cursor.

Do not kill unknown processes.

Do not open external CMD.

Do not delete recovery artifacts.

Do not store raw secrets in logs, reports or process records.

Do not run destructive cleanup automatically.

Do not start heavy work under critical resource pressure.

Do not retry heavy failed commands blindly.

Do not restore all panes simultaneously after resource crash if pressure is still high.

Do not recommend heavy “what now” tasks when resources are unstable.


STARTING PHASE: Implement Phase A only:

1. Resource Pressure Vector.


2. /resource-status.


3. RAM/CPU/disk/pane/process/log level classification.


4. Non-destructive recommendations.


5. Tests for vector scoring and critical pressure.



REQUIRED OUTPUT:

files changed,

tests added,

tests run,

resource levels implemented,

destructive actions avoided,

secret safety status,

remaining risks,

next phase.


STOP IF:

process ownership cannot be determined,

cleanup would be destructive,

output may include secrets,

implementation requires broad refactor,

Cursor/CPC state is not understood.


ACCEPTANCE:

resource vector works,

critical level lowers autonomy,

/resource-status concise report works,

no process killing in Phase A,

no raw secrets stored,

tests pass.



---

282. PART XIII CANONICAL PRINCIPLES

282.1 Resources Are Governance

RAM, CPU, disk, process count, pane count and context size affect execution safety.

282.2 Degrade Before Crash

The system should reduce capability before it collapses.

282.3 Heavy Work Needs Budget

Large tests, builds, indexing, browser automation and multi-pane restore need resource checks.

282.4 Unknown Processes Are Untouchable

If PP cannot prove ownership, it cannot kill the process.

282.5 Logs Can Become Resource Bugs

Unbounded logs and evidence can break disk, memory and secrecy.

282.6 Retry Loops Are Cascades

Repeated failure under resource pressure is a system bug.

282.7 Restore Safely, Not Fastest

After resource crash, sequential recovery may be better than full parallel restore.

282.8 What-Now Must Read the Machine

Next tasks must match current system health.

282.9 Resource Incidents Must Teach

Repeated resource failures become backlog, tests and hard rules.

282.10 A Stable Workbench Beats Maximum Parallelism

The Owner gains more from a recoverable, calm, stable Cursor workspace than from unsafe parallel overload.

END OF PART XIII.

Continuación directa sobre el dataset base del Claude Power Pack y las extensiones CPC-OS / RAM Stewardship / Resource Governor. 

