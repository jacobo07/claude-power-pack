# PP Dataset Part XXII -- Sovereign Execution Runtime: Leases, Worktrees, Sagas, Scheduler, Validator Quorum, Queue Reconciliation and Crash-Safe Agent Fleet Execution

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 29643-30655 (1013 lines)
**Part number:** 22 (roman XXII)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XXII
# Sovereign Execution Runtime: Leases, Worktrees, Sagas, Scheduler, Validator Quorum, Queue Reconciliation and Crash-Safe Agent Fleet Execution

## 468. SOVEREIGN EXECUTION RUNTIME

### 468.1 Propósito

La Parte XXI creó el Sovereign Agent Fleet OS: Work Orders, Agent Registry, Global Locks, Evidence Vault, Validation Queue, Merge Queue y Fleet Recovery.

La Parte XXII baja esa flota a runtime real.

Objetivo:
Convertir Work Orders en ejecución controlada, aislada, recuperable y verificable.

Canonical Name:
Sovereign Execution Runtime

Abreviatura:
SER

### 468.2 Problema

Una flota de agentes sin runtime puede fallar por:

- agentes que empiezan tareas pero no las terminan,
- locks que quedan colgados,
- branches mezcladas,
- work orders duplicados,
- validadores que validan claims en vez de evidencia,
- merge queue saltada,
- procesos muertos sin handoff,
- crashes durante una ejecución,
- tareas que quedan “in_progress” para siempre,
- agentes que pisan el mismo repo,
- trabajo que se completa pero no se integra,
- ejecución que no se puede reproducir.

### 468.3 Principio central

Execution must be lease-based, isolated, auditable and recoverable.

Ningún agente debe “poseer” una tarea indefinidamente.
Debe recibir un lease temporal, renovar heartbeat y devolver evidencia.

---

## 469. EXECUTION LEASE SYSTEM

### 469.1 Propósito

Evitar tareas zombis, locks eternos y agentes colgados.

Cada Work Order asignado debe tener un lease.

### 469.2 Lease Schema

EXECUTION_LEASE
lease_id:
work_order_id:
agent_id:
pane_id:
project:
repo_path:
scope:
granted_at:
expires_at:
renewal_interval:
last_heartbeat:
status:
locks_held:
resource_budget:
cost_budget:
renewal_policy:
revocation_reason:
recovery_action:

### 469.3 Lease Statuses

- requested
- granted
- active
- renewing
- expired
- revoked
- completed
- failed
- recovered
- quarantined

### 469.4 Lease Rules

- no lease, no execution,
- no heartbeat, lease expires,
- expired lease triggers recovery,
- revoked lease must stop work,
- completed lease requires receipt,
- locks release or transfer on lease completion.

### 469.5 Hard Rule candidata

HR-SER-LEASE-001:
Every executing Work Order must have an active Execution Lease. Expired leases must trigger recovery, not silent continuation.

---

## 470. WORKTREE / BRANCH ISOLATION SYSTEM

### 470.1 Propósito

Evitar que varios agentes escriban en el mismo working tree.

Canonical Name:
Worktree Isolation System

### 470.2 Regla

Para cambios no triviales, cada Work Order debe ejecutarse en branch/worktree aislado cuando sea posible.

### 470.3 Isolation Modes

ISO-0:
Read-only. No branch needed.

ISO-1:
Same branch, small safe edit.

ISO-2:
Feature branch required.

ISO-3:
Git worktree required.

ISO-4:
Separate clone/sandbox required.

ISO-5:
Manual only due to high risk.

### 470.4 Worktree Record

WORKTREE_EXECUTION_CONTEXT
context_id:
work_order_id:
agent_id:
repo_path:
base_branch:
work_branch:
worktree_path:
isolation_mode:
created_at:
status:
merge_target:
cleanup_required:
secret_scan_status:

### 470.5 Hard Rule candidata

HR-SER-WORKTREE-001:
Parallel code-changing Work Orders should use branch/worktree isolation unless explicitly proven unnecessary.

---

## 471. EXECUTION CAPSULE

### 471.1 Propósito

Cada ejecución debe tener cápsula completa.

### 471.2 Capsule Schema

EXECUTION_CAPSULE
capsule_id:
work_order_id:
agent_id:
lease_id:
worktree_context:
input_contract:
governance_packs:
done_gates:
locks:
resource_budget:
cost_budget:
evidence_paths:
handoff_path:
receipt_path:
rollback_plan:
status:

### 471.3 Capsule Rule

La cápsula es la unidad de recuperación.

Si hay crash, el runtime debe poder mirar cápsula y saber:
- qué se estaba haciendo,
- dónde,
- por quién,
- con qué locks,
- qué falta,
- cómo recuperar.

### 471.4 Hard Rule candidata

HR-SER-CAPSULE-001:
Every non-trivial Work Order execution must create an Execution Capsule before modifying files.

---

## 472. SAGA EXECUTION PATTERN

### 472.1 Propósito

Algunas tareas tienen varios pasos y pueden fallar en medio.

Usar patrón Saga:
- cada paso tiene acción,
- validación,
- compensación,
- rollback parcial.

### 472.2 Saga Schema

EXECUTION_SAGA
saga_id:
work_order_id:
steps:
  - step_id:
    name:
    action:
    validation:
    compensation:
    status:
current_step:
status:
rollback_available:

### 472.3 Saga Step Status

- pending
- running
- passed
- failed
- compensated
- skipped
- blocked

### 472.4 Required For

- schema migrations,
- settings changes,
- hook registration,
- registry changes,
- cross-repo campaigns,
- deploy,
- recovery,
- branch/worktree merge,
- governance sync.

### 472.5 Hard Rule candidata

HR-SER-SAGA-001:
Multi-step high-risk operations must use Saga-style execution with validation and compensation steps.

---

## 473. CRASH-SAFE QUEUE RECONCILIATION

### 473.1 Propósito

Tras crash, las queues deben reconciliarse.

### 473.2 Queues Affected

- Work Order Queue,
- Validation Queue,
- Merge Queue,
- Recovery Queue,
- Owner Review Queue,
- Agent Queue,
- Lock Queue.

### 473.3 Reconciliation Flow

1. Load last known queues.
2. Validate schema.
3. Check leases.
4. Mark expired leases.
5. Check receipts.
6. Check worktrees.
7. Check locks.
8. Check pending validations.
9. Rebuild queue state.
10. Generate recovery actions.

### 473.4 Queue Reconciliation Record

QUEUE_RECONCILIATION
reconciliation_id:
trigger:
queues_checked:
expired_leases:
orphan_work_orders:
orphan_locks:
pending_receipts:
pending_validations:
pending_merges:
actions_taken:
status:

### 473.5 Hard Rule candidata

HR-SER-QUEUE-001:
After crash or dirty shutdown, fleet queues must be reconciled before assigning new Work Orders.

---

## 474. VALIDATOR QUORUM SYSTEM

### 474.1 Propósito

Algunas tareas no deben pasar por un único validador.

### 474.2 Quorum Types

Q0:
No validation needed beyond receipt.

Q1:
Self-validation allowed.

Q2:
One specialized validator.

Q3:
Two validators: technical + PRG/secret/resource.

Q4:
Quorum required: implementation, tests, PRG, secret, merge.

Q5:
Owner approval required.

### 474.3 Quorum Schema

VALIDATOR_QUORUM
quorum_id:
work_order_id:
required_validators:
validator_results:
minimum_pass:
blocking_failures:
owner_review_required:
done_allowed:
status:

### 474.4 Required For

- secret-sensitive work,
- deploy,
- recovery,
- cross-repo policy changes,
- global hooks,
- settings changes,
- production demo features,
- user-facing UI,
- multi-agent integration.

### 474.5 Hard Rule candidata

HR-SER-QUORUM-001:
High-risk Work Orders require validator quorum before completion.

---

## 475. EXECUTION SCHEDULER

### 475.1 Propósito

Decidir qué Work Orders se ejecutan y cuándo.

### 475.2 Scheduler Inputs

- priority,
- dependencies,
- locks,
- resource pressure,
- agent availability,
- trust level,
- deadlines,
- Owner value,
- risk,
- recovery state,
- cost budget,
- merge queue load.

### 475.3 Scheduling Decision

SCHEDULING_DECISION
decision_id:
candidate_work_orders:
selected_work_orders:
deferred_work_orders:
blocked_work_orders:
reasoning:
resource_fit:
risk_fit:
expected_owner_value:
status:

### 475.4 Scheduler Rules

- recovery beats feature work,
- secret incident beats normal work,
- merge/validation debt beats new parallel execution,
- high resource pressure reduces concurrency,
- stale Work Orders must be reconciled,
- blocked dependencies must not execute.

### 475.5 Hard Rule candidata

HR-SER-SCHEDULER-001:
The fleet scheduler must prioritize recovery, validation, merge debt, secret safety and high-ROI blockers before starting new feature work.

---

## 476. WORK STEALING WITH SAFETY

### 476.1 Propósito

Si un pane/agente termina, puede tomar otra tarea, pero sin caos.

### 476.2 Work Stealing Preconditions

Allowed only if:

- agent is healthy,
- trust level sufficient,
- no lock conflict,
- task is stealable,
- lease can be granted,
- context pack available,
- resource budget OK,
- dependencies satisfied.

### 476.3 Work Stealing Record

WORK_STEALING_DECISION
agent_id:
available_pane:
candidate_tasks:
selected_task:
rejected_tasks:
reason:
locks:
lease:
status:

### 476.4 Hard Rule candidata

HR-SER-WORKSTEAL-001:
Idle agents may steal work only through scheduler-approved leases and lock checks.

---

## 477. STARVATION AND STALE WORK PREVENTION

### 477.1 Propósito

Evitar que ciertas tareas nunca se ejecuten o queden bloqueadas eternamente.

### 477.2 Starvation Signals

- Work Order pending too long,
- validation pending too long,
- merge pending too long,
- owner review queue ignored,
- blocker unresolved,
- expired lease repeated,
- dependency never completed.

### 477.3 Starvation Record

STARVATION_RECORD
item:
queue:
age:
reason:
impact:
recommended_action:
priority_boost:
status:

### 477.4 Hard Rule candidata

HR-SER-STARVATION-001:
Important Work Orders, validations and merges must not remain stale indefinitely; scheduler must surface starvation.

---

## 478. EXECUTION HEARTBEAT V2

### 478.1 Propósito

Heartbeat debe capturar estado de ejecución, no solo pane vivo.

### 478.2 Heartbeat Schema

EXECUTION_HEARTBEAT
heartbeat_id:
timestamp:
agent_id:
pane_id:
work_order_id:
lease_id:
current_step:
files_touched:
resource_usage:
cost_usage:
status:
blockers:
safe_summary:
secret_free: true

### 478.3 Heartbeat Rule

Heartbeat must be:
- lightweight,
- secret-free,
- structured,
- lease-linked,
- used for recovery.

### 478.4 Hard Rule candidata

HR-SER-HEARTBEAT-001:
Execution heartbeat must link pane, agent, Work Order and lease so crash recovery can reconstruct active work.

---

## 479. PARTIAL COMPLETION HANDLING

### 479.1 Propósito

Muchas tareas quedan parcialmente completadas.

Partial completion must be first-class.

### 479.2 Partial Completion Record

PARTIAL_COMPLETION
work_order_id:
agent_id:
completed_parts:
incomplete_parts:
files_changed:
validation_done:
validation_missing:
risks:
recommended_next_work_order:
safe_to_merge:
status:

### 479.3 Rules

- partial is not done,
- partial can produce follow-up Work Order,
- partial may be mergeable only if safe,
- partial must have receipt,
- partial must not be hidden.

### 479.4 Hard Rule candidata

HR-SER-PARTIAL-001:
Partial completion must be explicitly recorded and routed to follow-up, validation, merge or rollback.

---

## 480. EXECUTION ROLLBACK OR COMPENSATION

### 480.1 Propósito

Si un Work Order falla, runtime decide rollback o compensation.

### 480.2 Options

- rollback branch,
- revert commit,
- discard worktree,
- keep partial changes,
- create follow-up Work Order,
- manual review,
- quarantine agent,
- escalate to owner.

### 480.3 Rollback Decision

ROLLBACK_DECISION
work_order_id:
failure:
changes_made:
risk:
rollback_available:
compensation_available:
recommended_action:
owner_approval_required:
status:

### 480.4 Hard Rule candidata

HR-SER-ROLLBACK-001:
Failed Work Orders must end with rollback, compensation, follow-up Work Order or explicit manual review.

---

## 481. INTEGRATION DEBT TRACKER

### 481.1 Propósito

Parallel work creates integration debt.

### 481.2 Integration Debt Record

INTEGRATION_DEBT
debt_id:
source_work_orders:
project:
files_changed:
unmerged_branches:
pending_validations:
pending_prg:
pending_secret_scan:
pending_merge:
risk:
priority:
status:

### 481.3 Rule

Too much integration debt blocks new parallel work.

### 481.4 Hard Rule candidata

HR-SER-INTEGRATION-DEBT-001:
If integration debt exceeds threshold, scheduler must prioritize validation/merge over new implementation.

---

## 482. EXECUTION REPLAY

### 482.1 Propósito

Poder reconstruir qué hizo un agente.

No raw logs.
Structured replay.

### 482.2 Replay Event

EXECUTION_REPLAY_EVENT
event_id:
timestamp:
work_order_id:
agent_id:
event_type:
state_before:
state_after:
command_safe:
files:
evidence:
safe_summary:
secret_free: true

### 482.3 Use

- audit,
- recovery,
- debugging,
- meta-analysis,
- agent reliability,
- rollback.

### 482.4 Hard Rule candidata

HR-SER-REPLAY-001:
Agent execution should be replayable from structured secret-safe events, not raw terminal transcripts.

---

## 483. EXECUTION SANDBOX POLICY

### 483.1 Propósito

Definir cuándo usar sandbox.

### 483.2 Sandbox Required For

- unknown scripts,
- migrations,
- generated code from uncertain source,
- destructive commands,
- dependency upgrades,
- code modifying many files,
- external tool calls,
- untrusted repo,
- high-risk agent.

### 483.3 Sandbox Record

EXECUTION_SANDBOX
sandbox_id:
work_order_id:
repo_snapshot:
allowed_actions:
network_allowed:
write_allowed:
secret_access:
status:
result:

### 483.4 Hard Rule candidata

HR-SER-SANDBOX-001:
Unknown or high-risk execution must run in sandbox/dry-run mode before touching real repo state.

---

## 484. FLEET SLA SYSTEM

### 484.1 Propósito

Definir expectativas operativas.

### 484.2 SLA Types

- response time,
- validation time,
- merge time,
- recovery time,
- evidence time,
- owner review time,
- lease renewal time.

### 484.3 SLA Record

FLEET_SLA
sla_id:
scope:
target:
current:
breach:
impact:
recommended_action:
status:

### 484.4 Rule

SLA breach creates backlog/escalation.

### 484.5 Hard Rule candidata

HR-SER-SLA-001:
Critical Work Orders and recovery tasks must have SLA targets so stalls become visible.

---

## 485. EXECUTION MODE ESCALATION

### 485.1 Propósito

Runtime debe poder subir o bajar modo.

### 485.2 Escalation Triggers

- secret risk detected,
- resource pressure,
- validation failure,
- scope expansion,
- repeated failure,
- PRG violation,
- agent reliability issue,
- lock conflict,
- recovery state.

### 485.3 Mode Escalation Record

EXECUTION_MODE_ESCALATION
work_order_id:
from_mode:
to_mode:
trigger:
reason:
actions_required:
status:

### 485.4 Modes

- normal execution,
- constrained execution,
- validation-only,
- recovery-first,
- owner-review,
- ultra-plan,
- abort/rollback.

### 485.5 Hard Rule candidata

HR-SER-ESCALATION-001:
Runtime must escalate execution mode when risk changes; initial mode is not permanent.

---

## 486. IMPLEMENTATION PHASES FOR PART XXII

### Phase A -- Execution Lease MVP

Implement:
- lease schema,
- lease status,
- heartbeat-linked leases,
- expired lease detection.

### Phase B -- Execution Capsule

Implement:
- capsule schema,
- link Work Order + agent + locks + evidence + receipt.

### Phase C -- Worktree Isolation Planning

Implement:
- isolation mode decision,
- dry-run worktree plan,
- no actual branch automation initially.

### Phase D -- Queue Reconciliation

Implement:
- queue recovery after crash,
- orphan Work Order detection,
- expired lease handling.

### Phase E -- Validator Quorum

Implement:
- quorum schema,
- validation requirement by risk.

### Phase F -- Scheduler MVP

Implement:
- scheduling decision,
- blocked/deferred work,
- starvation detection.

### Phase G -- Execution Replay

Implement:
- structured replay events,
- secret-safe audit.

### Phase H -- Rollback/Compensation

Implement:
- rollback decision records,
- partial completion routing.

---

## 487. CLAUDE CODE PROMPT FOR PART XXII

PROMPT:

Act as the implementation engineer for Claude Power Pack Sovereign Execution Runtime.

MISSION:
Implement the runtime layer for the Sovereign Agent Fleet OS: execution leases, execution capsules, worktree isolation planning, queue reconciliation, validator quorum, scheduler, execution heartbeats, partial completion, rollback decisions and structured execution replay.

SOURCE OF TRUTH:
Use the repo on disk. Reuse Work Orders, Agent Registry, Global Locks, Evidence Vault, Validation Queue, Merge Queue, CPC-OS, Resource Governor, Control Plane and Secret Firewall if present.

NON-NEGOTIABLES:
- No agent execution without Work Order and active lease.
- Do not modify repo state without scope, locks and execution capsule.
- Do not run parallel code-changing work without branch/worktree isolation plan.
- Do not store raw secrets in leases, capsules, heartbeats, replay events or receipts.
- Do not mark expired leases as active.
- Do not assign new work before queue reconciliation after crash.
- Do not merge partial work without explicit partial completion record and validation.
- Do not use raw terminal transcripts as execution replay.
- Do not execute high-risk unknown scripts outside sandbox/dry-run planning.
- Do not skip validator quorum for high-risk Work Orders.

IMPLEMENT FIRST:
1. Execution Lease schema.
2. Lease lifecycle.
3. Execution Heartbeat schema linked to lease.
4. Execution Capsule schema.
5. Expired lease detection.
6. Queue Reconciliation dry-run schema.
7. Tests for lease grant, heartbeat renewal, expiry, no execution without lease, and no raw secrets.

ACCEPTANCE:
- Work Order can receive active lease.
- Lease expires without heartbeat.
- Expired lease blocks completion.
- Execution Capsule links Work Order, agent, locks and evidence.
- Queue reconciliation can detect orphan in-progress Work Order.
- No raw secrets stored.
- Tests pass.

FINAL RECEIPT:
Return files changed, tests added, tests run, lease status, capsule status, reconciliation status, secret safety status, remaining risks and next phase.

---

## 488. HARD RULE SET FOR PART XXII

### HR-SER-LEASE-001
Every executing Work Order must have an active Execution Lease.

### HR-SER-WORKTREE-001
Parallel code-changing Work Orders should use branch/worktree isolation unless proven unnecessary.

### HR-SER-CAPSULE-001
Non-trivial Work Orders must create Execution Capsule before modifying files.

### HR-SER-SAGA-001
High-risk multi-step operations require Saga execution.

### HR-SER-QUEUE-001
After crash, queues must be reconciled before new assignment.

### HR-SER-QUORUM-001
High-risk Work Orders require validator quorum.

### HR-SER-SCHEDULER-001
Scheduler prioritizes recovery, validation, merge debt, secrets and high-ROI blockers.

### HR-SER-WORKSTEAL-001
Work stealing requires scheduler-approved lease and lock checks.

### HR-SER-STARVATION-001
Important stale queue items must surface.

### HR-SER-HEARTBEAT-001
Execution heartbeat must link pane, agent, Work Order and lease.

### HR-SER-PARTIAL-001
Partial completion must be recorded and routed.

### HR-SER-ROLLBACK-001
Failed Work Orders must end with rollback, compensation, follow-up or manual review.

### HR-SER-INTEGRATION-DEBT-001
High integration debt blocks new parallel implementation.

### HR-SER-REPLAY-001
Execution must be replayable from structured secret-safe events.

### HR-SER-SANDBOX-001
Unknown/high-risk execution requires sandbox/dry-run before real repo mutation.

### HR-SER-SLA-001
Critical Work Orders and recovery tasks require SLA visibility.

### HR-SER-ESCALATION-001
Execution mode must escalate when risk changes.

---

## 489. PART XXII CANONICAL PRINCIPLES

### 489.1 Leases Prevent Zombie Work

Tasks must expire, renew or recover.

### 489.2 Isolation Prevents Collision

Parallel agents need branch/worktree boundaries.

### 489.3 Execution Needs Capsules

Recovery requires a complete execution context.

### 489.4 Sagas Beat Fragile Scripts

High-risk multi-step work needs compensation.

### 489.5 Queues Must Reconcile After Crash

Dirty state cannot receive new work blindly.

### 489.6 Validators Need Quorum

Critical work needs multiple forms of evidence.

### 489.7 Partial Is Not Done

Partial completion must be explicit.

### 489.8 Replay Must Be Structured

Raw transcripts are unsafe and noisy.

### 489.9 Scheduler Controls Fleet Chaos

Agents do not self-assign critical work randomly.

### 489.10 The Runtime Makes The Fleet Real

A fleet is not real until work is leased, isolated, validated, evidenced, recoverable and mergeable.

END OF PART XXII.

