# PP Dataset Part XXI -- Sovereign Agent Fleet OS: Work Orders, Agent Routing, Multi-Repo Execution, Global Locks, Evidence Vault, Merge Queue and Fleet-Level Reliability

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 28402-29642 (1241 lines)
**Part number:** 21 (roman XXI)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XXI
# Sovereign Agent Fleet OS: Work Orders, Agent Routing, Multi-Repo Execution, Global Locks, Evidence Vault, Merge Queue and Fleet-Level Reliability

## 445. SOVEREIGN AGENT FLEET OS

### 445.1 Propósito

La Parte XX creó el Sovereign Control Plane OS.

La Parte XXI convierte ese control plane en una flota de ejecución coordinada.

Claude Power Pack no debe limitarse a saber:
- qué repos existen,
- qué políticas aplican,
- qué riesgos hay,
- qué estándares faltan.

Debe poder coordinar ejecución real entre:
- panes de Cursor,
- conversaciones Claude Code,
- agentes especializados,
- repos,
- workspaces,
- tareas paralelas,
- validators,
- reviewers,
- recovery agents,
- benchmark runners,
- meta-analysis agents.

Canonical Name:
Sovereign Agent Fleet OS

Abreviatura:
SAF-OS

### 445.2 Principio central

A fleet without contracts becomes chaos.

Si varios agentes trabajan a la vez, cada agente necesita:
- identidad,
- rol,
- tarea,
- scope,
- locks,
- presupuesto,
- criterios de done,
- evidencia,
- límites,
- handoff,
- merge plan,
- rollback,
- estado visible.

### 445.3 Objetivo

SAF-OS debe permitir que el Owner tenga múltiples Claude Code/panes/agentes trabajando en paralelo sin que:

- dos agentes trabajen en lo mismo,
- se pisen archivos,
- se dupliquen conversaciones,
- se rompa el registry,
- se ignore el PRG,
- se hagan cambios sin evidencia,
- se pierdan tareas tras crash,
- se filtren secretos,
- se creen branches incompatibles,
- se mergee trabajo sin validación,
- se declare done sin receipt.

### 445.4 Hard Rule candidata

HR-SAF-001:
No autonomous or semi-autonomous agent may execute repo work without a registered Work Order, scope, locks, validation contract and evidence requirement.

---

## 446. WORK ORDER SYSTEM

### 446.1 Propósito

Toda tarea ejecutable debe convertirse en Work Order.

Un Work Order es un contrato de ejecución.

No es una idea.
No es una nota.
No es un prompt suelto.

Es una unidad rastreable de trabajo que puede asignarse, ejecutarse, validarse, pausarse, recuperarse y auditarse.

### 446.2 Work Order Schema

WORK_ORDER
work_order_id:
title:
project:
repo_path:
workspace_id:
source:
source_type:
priority:
category:
objective:
scope:
allowed_files:
forbidden_files:
expected_outputs:
done_criteria:
production_reality_gate:
validation_plan:
secret_policy:
resource_budget:
cost_budget:
risk_level:
cascade_risk:
rollback_plan:
assigned_agent:
assigned_pane:
locks_required:
dependencies:
blocking_conditions:
handoff_required:
evidence_required:
status:
created_at:
updated_at:

### 446.3 Work Order Statuses

- proposed
- approved
- assigned
- in_progress
- paused
- blocked
- validating
- failed
- completed_pending_review
- completed_verified
- rejected
- cancelled
- recovered
- archived

### 446.4 Work Order Sources

Work Orders pueden venir de:

- Owner request,
- `/what-now`,
- stack backlog,
- failure forecast,
- UFE,
- meta-analysis,
- PRG failure,
- governance drift,
- resource incident,
- CPC recovery issue,
- benchmark failure,
- standard diff,
- project twin gap,
- control plane risk engine,
- manual Owner idea.

### 446.5 Hard Rule candidata

HR-WORKORDER-001:
Every executable task must be represented as a Work Order before agent assignment, except trivial read-only answers.

---

## 447. AGENT REGISTRY

### 447.1 Propósito

SAF-OS necesita saber qué agentes existen y para qué sirven.

### 447.2 Agent Types

- Claude Code Pane Agent
- Review Agent
- Secret Safety Agent
- Resource Governor Agent
- Production Reality Gate Agent
- Test Runner Agent
- Benchmark Agent
- Recovery Agent
- Backlog Agent
- Meta-Analysis Agent
- Documentation Agent
- Merge Agent
- Governance Sync Agent
- Sentinel Agent

### 447.3 Agent Registry Schema

AGENT_REGISTRY_ENTRY
agent_id:
name:
type:
capabilities:
allowed_projects:
allowed_actions:
forbidden_actions:
trust_level:
resource_profile:
cost_profile:
secret_handling:
can_write_code:
can_modify_registry:
can_modify_settings:
can_run_tests:
can_touch_production:
requires_owner_approval:
last_seen:
health:
status:

### 447.4 Agent States

- available
- assigned
- busy
- paused
- blocked
- unhealthy
- stale
- crashed
- quarantined
- disabled
- retired

### 447.5 Hard Rule candidata

HR-AGENT-REGISTRY-001:
Every agent participating in fleet execution must be registered with capabilities, trust level, allowed actions and forbidden actions.

---

## 448. CAPABILITY-BASED ROUTING

### 448.1 Propósito

No todas las tareas deben ir al mismo agente.

El sistema debe asignar tareas según:
- capacidad,
- riesgo,
- coste,
- recursos,
- contexto,
- historial,
- trust level,
- disponibilidad,
- proyecto,
- tipo de tarea.

### 448.2 Routing Inputs

- Work Order type,
- project type,
- governance packs,
- secret risk,
- resource pressure,
- required tools,
- files involved,
- prior failures,
- agent capability,
- agent health,
- pane availability,
- owner priority.

### 448.3 Routing Decision

AGENT_ROUTING_DECISION
work_order_id:
candidate_agents:
selected_agent:
selected_pane:
reason:
rejected_agents:
risk:
resource_fit:
cost_fit:
expected_quality:
fallback_agent:
owner_approval_required:

### 448.4 Routing Rules

Secret-heavy work:
- require Secret Safety Agent or Secret Firewall gate.

Recovery work:
- require Recovery Agent / CPC-aware agent.

Heavy tests:
- require Resource Governor approval.

UI/API reality work:
- require PRG Agent.

Cross-repo governance:
- require Control Plane trust boundary.

### 448.5 Hard Rule candidata

HR-ROUTING-001:
Work Orders must route to agents based on capability, risk, trust and resource fit, not arbitrary availability.

---

## 449. GLOBAL LOCK SERVICE

### 449.1 Propósito

Varios agentes trabajando en paralelo necesitan locks globales.

No basta con locks por pane.
Tiene que haber locks a nivel stack/control plane.

### 449.2 Lock Types

- repo_lock
- branch_lock
- file_lock
- directory_lock
- feature_lock
- test_lock
- deploy_lock
- migration_lock
- registry_lock
- settings_lock
- policy_lock
- governance_pack_lock
- project_twin_lock
- secret_incident_lock
- recovery_lock
- merge_lock

### 449.3 Global Lock Schema

GLOBAL_LOCK
lock_id:
type:
scope:
project:
repo_path:
resource:
owner_agent:
owner_pane:
work_order_id:
reason:
created_at:
expires_at:
renewal_policy:
release_conditions:
conflict_policy:
status:

### 449.4 Lock Conflict Policy

If conflict:
- block,
- queue,
- suggest alternative work,
- convert to read-only review,
- require owner override,
- split work order.

### 449.5 Hard Rule candidata

HR-GLOBAL-LOCK-001:
Fleet execution must acquire global locks for shared resources before modifying repos, runtime registries, policies, settings, recovery state or deployment targets.

---

## 450. WORK ORDER QUEUE

### 450.1 Propósito

Gestionar tareas globalmente.

### 450.2 Queue Types

- global_queue
- project_queue
- pane_queue
- agent_queue
- recovery_queue
- validation_queue
- merge_queue
- blocked_queue
- owner_review_queue

### 450.3 Queue Item

WORK_QUEUE_RECORD
queue_id:
work_order_id:
priority:
assigned_to:
status:
dependencies:
locks:
estimated_effort:
resource_class:
risk:
next_action:
created_at:
updated_at:

### 450.4 Queue Rules

- P0 safety/recovery beats feature work.
- Secret incidents beat normal backlog.
- Recovery pending blocks unrelated new work in affected workspace.
- Merge queue must not be skipped.
- Owner review queue must be visible.

### 450.5 Hard Rule candidata

HR-FLEET-QUEUE-001:
Fleet queues must prioritize safety, recovery, secrets, false done and high-ROI blockers above feature expansion.

---

## 451. AGENT WORK CONTRACT

### 451.1 Propósito

Cada agente recibe un contrato claro.

### 451.2 Contract Schema

AGENT_WORK_CONTRACT
contract_id:
work_order_id:
agent_id:
mission:
scope:
allowed_actions:
forbidden_actions:
inputs:
source_of_truth:
validation:
done_gate:
evidence_required:
secret_policy:
resource_budget:
cost_budget:
handoff_required:
stop_conditions:
final_receipt_format:

### 451.3 Required Stop Conditions

Stop if:
- secret appears,
- scope expansion needed,
- lock conflict,
- resource pressure critical,
- validation impossible,
- repo state contradicts plan,
- done-gate cannot pass,
- production risk emerges,
- dependency missing,
- agent lacks capability.

### 451.4 Hard Rule candidata

HR-AGENT-CONTRACT-001:
Agents must receive explicit Work Contracts with scope, forbidden actions, validation, stop conditions and evidence requirements.

---

## 452. EVIDENCE VAULT

### 452.1 Propósito

Todas las tareas completadas necesitan evidencia.

Canonical Name:
Evidence Vault

### 452.2 Location

Global:

```text
~/.claude/pp_control_plane/evidence_vault/

Project-local:

<repo>/.claude-power-pack/evidence/

452.3 Evidence Vault Rules

sanitized only,

no raw secrets,

no unbounded logs,

linked to Work Order,

linked to agent,

linked to validation,

linked to done-gate,

versioned,

retrievable,

compact summary first.


452.4 Evidence Record

EVIDENCE_VAULT_RECORD evidence_id: work_order_id: agent_id: project: type: validation_level: command_safe: result: artifact_paths: secret_scan_status: size: created_at: safe_to_share: limitations:

452.5 Hard Rule candidata

HR-EVIDENCE-VAULT-001: Fleet-level done claims must link to sanitized Evidence Vault records.


---

453. AGENT EXECUTION RECEIPTS

453.1 Propósito

Cada agente debe entregar recibo.

453.2 Receipt Schema

AGENT_EXECUTION_RECEIPT receipt_id: work_order_id: agent_id: pane_id: status: summary: files_changed: commands_run: tests_run: done_gate_result: production_reality_gate: secret_scan: resource_usage: cost_estimate: locks_acquired: locks_released: evidence: remaining_risks: next_recommended_action: handoff_path:

453.3 Receipt Requirements

No receipt:

no completion,

no merge,

no backlog close,

no done.


453.4 Hard Rule candidata

HR-AGENT-RECEIPT-001: An agent cannot mark a Work Order complete without an Agent Execution Receipt.


---

454. VALIDATION ROUTER

454.1 Propósito

Separar ejecución de validación cuando haga falta.

No siempre el mismo agente que implementa debe validar.

454.2 Validation Agents

unit test validator,

integration validator,

PRG validator,

secret validator,

resource validator,

recovery validator,

output contract validator,

benchmark validator.


454.3 Validation Request

VALIDATION_REQUEST request_id: work_order_id: implementation_agent: validator_agent: validation_type: required_evidence: inputs: expected_result: status:

454.4 Validation Result

VALIDATION_RESULT request_id: status: passed: failed_checks: evidence: confidence: done_allowed: next_action:

454.5 Hard Rule candidata

HR-VALIDATION-ROUTER-001: High-risk Work Orders require independent or specialized validation before completion.


---

455. MERGE QUEUE

455.1 Propósito

Cuando varios agentes/panes modifican código, el merge debe ser controlado.

Canonical Name: Fleet Merge Queue

455.2 Merge Queue Item

MERGE_QUEUE_ITEM merge_id: work_orders: agents: project: repo_path: files_changed: conflicts: validation_required: secret_scan_required: resource_check_required: done_gate_required: merge_order: rollback_plan: status:

455.3 Merge Preconditions

receipts collected,

locks released or transferred,

tests pass,

secret scan pass,

no unresolved collisions,

PRG pass if user-facing,

no fake done,

evidence linked,

rollback path exists.


455.4 Hard Rule candidata

HR-MERGE-QUEUE-001: Parallel agent work must enter Merge Queue before being considered integrated or complete.


---

456. AGENT REPUTATION AND RELIABILITY SCORE

456.1 Propósito

No todos los agentes serán igual de fiables.

456.2 Score Dimensions

completion accuracy,

false done rate,

secret safety,

scope fidelity,

validation quality,

cost efficiency,

resource discipline,

handoff quality,

recovery behavior,

owner correction rate.


456.3 Agent Reliability Record

AGENT_RELIABILITY agent_id: tasks_completed: tasks_failed: false_done_count: secret_incidents: scope_drift_count: average_validation_level: average_cost: owner_corrections: reliability_score: trust_adjustment: status:

456.4 Use

route critical tasks to reliable agents,

demote noisy agents,

require validator for low-score agents,

quarantine unsafe agents.


456.5 Hard Rule candidata

HR-AGENT-RELIABILITY-001: Agent routing should consider historical reliability, not just declared capability.


---

457. AGENT QUARANTINE

457.1 Propósito

Si un agente causa fallos repetidos, debe aislarse.

457.2 Quarantine Triggers

raw secret leak,

repeated false done,

repeated scope drift,

corrupts registry,

ignores locks,

causes recovery loop,

high resource abuse,

invalid receipts,

unsafe process cleanup,

repeated owner correction.


457.3 Quarantine Record

AGENT_QUARANTINE agent_id: reason: trigger_event: started_at: allowed_actions: blocked_actions: required_review: reinstatement_conditions: status:

457.4 Hard Rule candidata

HR-AGENT-QUARANTINE-001: Agents causing critical safety, recovery, secret or false-done failures must be quarantined until reviewed.


---

458. FLEET OBSERVABILITY

458.1 Propósito

El Owner necesita ver qué está haciendo la flota.

458.2 Fleet Status

FLEET_STATUS active_agents: active_panes: active_work_orders: blocked_work_orders: validation_pending: merge_pending: recovery_pending: high_risk_items: resource_pressure: next_global_action:

458.3 Command

/fleet-status

458.4 Other Commands

/work-orders
/agent-registry
/agent-status
/agent-quarantine
/locks-global
/merge-queue
/evidence-vault
/validation-queue

458.5 Hard Rule candidata

HR-FLEET-OBS-001: Fleet execution must be observable through compact status commands.


---

459. FLEET COST GOVERNANCE

459.1 Propósito

Múltiples agentes pueden disparar costes.

459.2 Fleet Cost Budget

FLEET_COST_BUDGET period: global_budget: project_budgets: agent_budgets: work_order_budgets: current_spend: forecast_spend: overrun_risk: actions:

459.3 Cost Rules

high-cost work requires ROI,

repeated agents reading same files should use shared context packs,

validators should use evidence, not reread everything,

no duplicate research across agents,

no redundant full repo scans.


459.4 Hard Rule candidata

HR-FLEET-COST-001: Fleet execution must share context/evidence and avoid duplicate expensive work across agents.


---

460. SHARED CONTEXT PACKS FOR AGENTS

460.1 Propósito

Evitar que cada agente lea lo mismo.

460.2 Context Pack

SHARED_CONTEXT_PACK pack_id: project: repo_path: work_orders: scope: included_files: excluded_files: summary: standards: risks: validation_commands: secret_scan_status: freshness: created_at: expires_at:

460.3 Rules

context packs must be secret-safe,

task-scoped,

freshness-labeled,

not full repo dumps,

invalidated after major changes.


460.4 Hard Rule candidata

HR-FLEET-CONTEXT-001: Agents working on related tasks should use shared, secret-safe context packs instead of duplicating large reads.


---

461. CROSS-REPO WORK CAMPAIGNS

461.1 Propósito

Algunas mejoras aplican a varios repos.

Ejemplos:

añadir passive failure capture,

añadir PRG,

añadir no-fake-done gate,

añadir .env.example validation,

añadir secret scan,

añadir governance manifest.


461.2 Campaign Schema

CROSS_REPO_WORK_CAMPAIGN campaign_id: title: objective: target_repos: policy_source: work_orders: rollout_mode: dry_run: risk: rollback: progress: status:

461.3 Campaign Rules

dry-run first,

repo-specific manifests respected,

trust boundaries respected,

no bulk writes without approval,

evidence per repo,

rollback per repo.


461.4 Hard Rule candidata

HR-CAMPAIGN-001: Cross-repo changes must be executed as campaigns with per-repo Work Orders, dry-run, evidence and rollback.


---

462. FLEET RECOVERY

462.1 Propósito

Si la flota crashea, recuperar no solo panes, sino Work Orders y agentes.

462.2 Fleet Recovery Record

FLEET_RECOVERY_RECORD recovery_id: trigger: affected_agents: affected_panes: affected_work_orders: registry_state: locks_state: merge_queue_state: validation_queue_state: restore_plan: manual_required: status:

462.3 Recovery Requirements

After crash:

restore pane topology,

restore agent registry,

restore active Work Orders,

restore locks,

restore queues,

identify incomplete receipts,

prevent duplicate agents,

resume or reassign safely.


462.4 Hard Rule candidata

HR-FLEET-RECOVERY-001: Crash recovery must restore fleet execution state, not only terminal sessions.


---

463. FLEET-LEVEL PRODUCTION REALITY GATE

463.1 Propósito

Cuando varios agentes contribuyen a una feature, PRG debe validarse a nivel feature completa.

463.2 Fleet PRG

FLEET_PRG feature: work_orders: agents: surface_checks: integration_checks: UI_CLI_API_workflow_checks: auth_checks: placeholder_checks: error_handling: evidence: done_allowed:

463.3 Rule

No individual agent can declare whole feature done if integration PRG has not passed.

463.4 Hard Rule candidata

HR-FLEET-PRG-001: Multi-agent feature completion requires fleet-level Production Reality Gate after integration.


---

464. FLEET IMPLEMENTATION PHASES

Phase A -- Work Order System MVP

Implement:

Work Order schema,

status lifecycle,

read-only /work-orders,

create from backlog item.


Phase B -- Agent Registry MVP

Implement:

agent registry,

capabilities,

trust levels,

status.


Phase C -- Global Lock Service

Implement:

lock schema,

lock acquire/release dry-run,

conflict detection.


Phase D -- Agent Work Contract

Implement:

contract generation,

stop conditions,

output receipt requirement.


Phase E -- Evidence Vault

Implement:

evidence record schema,

link to Work Order,

secret-safe storage.


Phase F -- Validation Queue

Implement:

validation request/result,

specialized validators.


Phase G -- Merge Queue

Implement:

merge queue schema,

preconditions,

receipts collection.


Phase H -- Fleet Status

Implement:

/fleet-status,

active agents,

queues,

locks,

risks.



---

465. CLAUDE CODE PROMPT FOR PART XXI

PROMPT:

Act as the implementation engineer for Claude Power Pack Sovereign Agent Fleet OS.

MISSION: Implement the next layer of stack execution: Work Orders, Agent Registry, capability-based routing, global locks, evidence vault, validation queue, merge queue, agent receipts, agent reliability and fleet recovery.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing Control Plane, CPC-OS, Workbench, Resource Governor, Project Twins, Stack Index, Governance Packs, UFE, Meta-Analysis, Output Contracts, Secret Firewall and Backlog systems if present.

NON-NEGOTIABLES:

Do not let any agent execute repo work without Work Order.

Do not allow overlapping file/scope work without global lock conflict resolution.

Do not mark Work Order complete without Agent Execution Receipt.

Do not merge parallel work without Merge Queue validation.

Do not store raw secrets in Work Orders, evidence, receipts, queues or agent registry.

Do not route high-risk work to untrusted or unhealthy agents.

Do not let validators rely on claims instead of evidence.

Do not duplicate expensive reads across agents when shared context pack can be used.

Do not run fleet automation in write mode before dry-run/advisory mode.

Do not bypass project trust boundaries.


IMPLEMENT FIRST:

1. Work Order schema.


2. Work Order lifecycle.


3. Agent Registry schema.


4. Agent Work Contract schema.


5. Agent Execution Receipt schema.


6. Global Lock schema.


7. /fleet-status read-only summary.


8. Tests for work order creation, assignment blocked without lock, receipt required for completion, no raw secrets.



ACCEPTANCE:

Work Orders can be created from backlog/meta-analysis.

Agents can be registered with capabilities.

Work Orders require scope and done criteria.

Completion requires receipt.

Lock conflict can block assignment.

Fleet status shows active work.

No raw secrets stored.

Tests pass.


FINAL RECEIPT: Return files changed, tests added, tests run, Work Order status, Agent Registry status, Global Lock status, receipt status, fleet status, secret safety status, remaining risks and next phase.


---

466. HARD RULE SET FOR PART XXI

HR-SAF-001

No agent may execute repo work without a registered Work Order, scope, locks, validation contract and evidence requirement.

HR-WORKORDER-001

Every executable task must be represented as a Work Order except trivial read-only answers.

HR-AGENT-REGISTRY-001

Every fleet agent must be registered with capabilities, trust and forbidden actions.

HR-ROUTING-001

Work Orders route by capability, risk, trust and resource fit.

HR-GLOBAL-LOCK-001

Fleet execution must acquire global locks for shared resources.

HR-FLEET-QUEUE-001

Fleet queues prioritize safety, recovery, secrets, false done and high-ROI blockers.

HR-AGENT-CONTRACT-001

Agents receive explicit Work Contracts.

HR-EVIDENCE-VAULT-001

Fleet-level done claims must link to sanitized Evidence Vault records.

HR-AGENT-RECEIPT-001

Agents cannot mark Work Orders complete without Execution Receipt.

HR-VALIDATION-ROUTER-001

High-risk Work Orders require specialized validation.

HR-MERGE-QUEUE-001

Parallel agent work must enter Merge Queue before integration.

HR-AGENT-RELIABILITY-001

Agent routing should consider historical reliability.

HR-AGENT-QUARANTINE-001

Unsafe agents must be quarantined.

HR-FLEET-OBS-001

Fleet execution must be observable.

HR-FLEET-COST-001

Fleet execution must avoid duplicate expensive work.

HR-FLEET-CONTEXT-001

Related agents should use shared context packs.

HR-CAMPAIGN-001

Cross-repo changes must be campaigns with dry-run, evidence and rollback.

HR-FLEET-RECOVERY-001

Crash recovery must restore fleet execution state.

HR-FLEET-PRG-001

Multi-agent features require fleet-level Production Reality Gate.


---

467. PART XXI CANONICAL PRINCIPLES

467.1 Work Without Work Orders Is Chaos

Every executable unit needs a contract.

467.2 Agents Need Identity

No anonymous autonomous execution.

467.3 Parallelism Requires Locks

Speed without locks creates collisions.

467.4 Receipts Create Trust

No receipt, no completion.

467.5 Validators Need Evidence

Claims are not validation.

467.6 Merge Is A Gate

Parallel work is not integrated until merge validation passes.

467.7 Reliability Must Affect Routing

Unsafe agents should not get critical work.

467.8 Shared Context Reduces Cost

Fleet agents should not pay the same context cost repeatedly.

467.9 Fleet Recovery Must Restore Work, Not Just Panes

Recover Work Orders, locks, queues, agents and evidence state.

467.10 The Stack Becomes An Execution Fleet

The next order of magnitude is not one smarter Claude session. It is a coordinated fleet of bounded, validated, recoverable agents working under a sovereign control plane.

END OF PART XXI.

