# PP Dataset -- CPC-OS Full Spec (Cursor Pane Continuity)

**Source:** PP_DATASET_20260531T122242Z (1).md, lines 10304-15425
**Dataset part:** Part VIII+IX+X
**Ingested:** 2026-06-01 (BL-DATASET-001 M0)
**Lines in this file:** 5122

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART VIII
# Cursor Pane Continuity OS + Exact Restart/Resume Router + Multi-Terminal Backlog Isolation + Crash Recovery

## 141. CURSOR PANE CONTINUITY OS

### 141.1 Propósito

Claude Power Pack debe añadir una capa específica para continuidad exacta de sesiones dentro de Cursor.

El objetivo es que cuando el Owner haga `/restart`, Claude Code no mate la terminal ni obligue a abrir una nueva terminal manualmente.

El comportamiento deseado:

1. El Owner ejecuta `/restart` dentro de una sesión de Claude Code.
2. El Power Pack guarda exactamente:
   - conversación activa,
   - session/conversation ID,
   - repo/cwd,
   - pane/terminal donde estaba,
   - tarea activa,
   - backlog asignado,
   - estado de ejecución,
   - handoff seguro,
   - comando exacto de resume.
3. Claude Code hace exit limpio.
4. El control vuelve al shell de la terminal integrada de Cursor.
5. El wrapper/router detecta que el exit fue un restart intencional.
6. Sin matar la terminal, ejecuta el comando correcto de Claude resume para la conversación exacta.
7. La sesión continúa en el mismo pane de Cursor.
8. El pane registry JSON queda actualizado.

Este sistema solo debe operar sobre terminales integradas de Cursor, no sobre CMD normal suelto, PowerShell externo, Windows Terminal externo ni terminales no registradas.

### 141.2 Nombre canónico

Canonical Name:
Cursor Pane Continuity OS

Abreviatura:
CPC-OS

Componentes:
- Cursor Pane Registry
- Exact Resume Router
- Restart Transaction Manager
- Pane Backlog Allocator
- Pane Collision Guard
- Crash Recovery Orchestrator
- Session Switch Router
- Cursor Terminal Restoration Adapter

### 141.3 Principio central

A Claude session is not just a process. It is a routed execution lane.

Cada pane de Cursor debe tener identidad, conversación activa, backlog propio, lock de scope y estado recuperable.

---

## 142. PROBLEMA QUE RESUELVE

### 142.1 Problema actual

Cuando se hace restart de Claude Code, el flujo típico puede ser frágil:

- se mata la terminal,
- se abre una terminal nueva,
- se pega un comando manual,
- se pierde el contexto exacto,
- se reanuda la sesión equivocada,
- se duplican sesiones,
- varias terminales pueden trabajar en la misma tarea,
- si Cursor crashea no se sabe qué panes estaban activos,
- si el ordenador se apaga se pierde el mapa de sesiones,
- no hay router central que diga qué conversación vive en qué pane.

### 142.2 Objetivo

Crear un sistema que haga que los panes de Cursor sean recuperables, enrutable y coordinados.

El Owner debe poder tener:

- Pane 1: conversación 1111 trabajando en tarea A.
- Pane 2: conversación 2222 trabajando en tarea B.
- Pane 3: conversación 3333 trabajando en tarea C.

Y el Power Pack debe saber:
- cuántos panes hay,
- qué conversación está en cada pane,
- qué repo/cwd usa cada pane,
- qué tarea tiene asignada,
- qué archivos tiene bloqueados,
- cuándo hizo heartbeat por última vez,
- si está vivo, pausado, crasheado o stale,
- cómo reanudarlo exactamente.

---

## 143. CURSOR-ONLY TERMINAL REQUIREMENT

### 143.1 Regla crítica

Este sistema debe operar únicamente en terminal integrada de Cursor.

No debe abrir CMD normal.
No debe abrir Windows Terminal externo.
No debe abrir PowerShell externo fuera de Cursor.
No debe crear procesos de Claude invisibles fuera del workspace.
No debe restaurar sesiones en un cwd incorrecto.
No debe pegar comandos en una terminal no identificada.

### 143.2 Cursor Terminal Detection

Cada sesión debe verificar si está dentro de entorno compatible con Cursor.

Señales posibles:
- variables de entorno de VS Code/Cursor,
- terminal integrada,
- cwd dentro de workspace abierto,
- wrapper lanzado desde terminal de Cursor,
- pane_id registrado,
- workspace_id registrado,
- parent process compatible.

Si no puede verificar que está en Cursor:
- no debe ejecutar auto-restore,
- debe generar Owner-side instruction,
- debe marcar estado como `external_terminal_blocked`.

### 143.3 Hard Rule candidata

HR-CURSOR-001:
Never perform automatic restart/resume routing into normal CMD, external PowerShell, Windows Terminal or unknown terminal. Cursor Pane Continuity OS only operates inside verified Cursor integrated terminals.

---

## 144. PANE REGISTRY JSON

### 144.1 Propósito

Mantener un archivo JSON como fuente de verdad de sesiones/panes activos.

Ubicación sugerida:

```text
~/.claude/pp_runtime/cursor_panes/pane_registry.json

También puede haber snapshot por proyecto:

<repo>/.claude-power-pack/pane_registry.snapshot.json

Pero la fuente global debe vivir en ~/.claude/pp_runtime/.

144.2 Requisitos del JSON

El JSON debe ser:

atomic-write only,

lock-protected,

corruption-resistant,

versioned,

schema-validated,

recoverable from journal,

no raw secrets,

no huge prompts,

no full conversation text,

no API keys,

no terminal raw logs.


144.3 Registry Schema

PANE_REGISTRY schema_version: updated_at: host_id: cursor_instance_id: active_workspace: panes:

pane_id: pane_index: cursor_window_id: workspace_id: repo_path: cwd: shell: terminal_kind: is_cursor_integrated: process_id: claude_process_id: active_conversation_id: active_session_id: resume_command_template: last_resume_command_redacted: task_id: backlog_item_id: scope_lock_id: status: lifecycle_state: last_heartbeat: last_seen_at: created_at: updated_at: restart_intent: switch_intent: crash_recovery_needed: owner_visible_label: notes_safe: locks:

lock_id: pane_id: task_id: repo_path: file_patterns: reason: created_at: expires_at: journal_pointer: integrity: sha256: last_valid_backup:


144.4 Allowed pane statuses

active

paused

restarting

switching

resumed

stale

crashed

orphaned

closed

external_blocked

recovery_pending

recovery_failed


144.5 Registry Write Rule

Every registry update must use:

1. read current JSON,


2. validate schema,


3. acquire lock,


4. write to temp file,


5. fsync if possible,


6. atomic replace,


7. write journal entry,


8. keep backup of last valid registry,


9. release lock.



Never write pane_registry.json directly.


---

145. EXACT RESTART / RESUME ROUTER

145.1 Propósito

Cuando el Owner hace /restart, no se debe perder el hilo exacto.

El sistema debe reanudar la conversación exacta donde estaba.

145.2 Importante

El comando exacto de resume no debe hardcodearse hasta verificar el CLI real disponible en el entorno.

Usar placeholder canónico:

<CLAUDE_RESUME_CMD> <conversation_or_session_id>

Ejemplo conceptual:

claude --resume <id>

Pero el Power Pack debe detectar y validar el comando real antes de instalarlo.

145.3 Restart Transaction

Un restart no es un simple exit.

Debe ser una transacción:

RESTART_TRANSACTION restart_id: pane_id: repo_path: cwd: old_conversation_id: old_session_id: target_conversation_id: target_session_id: reason: initiated_by: created_at: handoff_packet_path: registry_before_hash: registry_after_hash: exit_code_expected: resume_command: status: failure_recovery:

145.4 Restart Flow

1. Owner escribe /restart.


2. PP crea Restart Transaction.


3. PP captura handoff seguro.


4. PP guarda conversation/session ID exacto.


5. PP marca pane status restarting.


6. PP escribe restart intent en runtime file.


7. Claude Code hace exit limpio con código o marker reconocible.


8. Shell wrapper en el mismo Cursor pane detecta restart intent.


9. Shell wrapper ejecuta resume command en el mismo pane.


10. SessionStart hook confirma conversation ID.


11. Registry actualiza status resumed.


12. Si falla, status recovery_failed y se muestra comando manual seguro.



145.5 No terminal kill rule

El restart no debe matar la terminal integrada.

Debe cerrar el proceso Claude y devolver control al shell del mismo pane.

Hard Rule candidata: HR-RESTART-001: /restart must never kill the Cursor terminal pane. It must create a restart transaction, exit Claude cleanly, and let the Cursor-integrated shell wrapper resume the exact session in-place.

145.6 Shell Wrapper Requirement

Para que el restart pueda “mandar el comando al CMD de Cursor” después del exit, debe existir un wrapper padre.

Sin wrapper, cuando Claude sale, el proceso ya no puede escribir mágicamente en el shell.

Por tanto, el diseño correcto es:

el Owner lanza Claude mediante un comando wrapper dentro de Cursor,

wrapper ejecuta Claude,

cuando Claude termina, wrapper lee restart intent,

si hay restart intent, wrapper ejecuta resume command,

si no hay restart intent, devuelve shell normal.


Canonical wrapper name: claude-pp

Conceptual behavior:

claude-pp starts Claude
Claude exits
claude-pp checks restart intent
if restart intent exists: run resume command
else: return to shell

No es un CMD normal externo. Es el shell activo dentro de la terminal integrada de Cursor.

145.7 Restart Intent File

Ubicación sugerida:

~/.claude/pp_runtime/cursor_panes/restart_intents/<pane_id>.json

Schema:

RESTART_INTENT intent_id: pane_id: repo_path: cwd: conversation_id: session_id: resume_command: created_at: expires_at: status: handoff_path: safe_to_execute: cursor_only: registry_hash: reason:

145.8 Expiration

Restart intents deben expirar.

Si un intent tiene más de X minutos:

no ejecutar automáticamente,

marcar stale,

pedir confirmación o mostrar comando manual.


Esto evita que un restart viejo se dispare en una terminal equivocada.


---

146. SESSION SWITCH ROUTER

146.1 Propósito

El Owner también quiere cambiar una terminal/pane de una conversación a otra.

Ejemplo: Pane 2 está en conversación 2222. El Owner quiere cambiar Pane 2 a conversación 4444. El registry debe actualizar active_conversation_id de Pane 2 a 4444 y reanudar esa conversación en ese mismo pane.

146.2 Switch Flow

1. Owner ejecuta comando de switch.


2. PP crea Switch Transaction.


3. Guarda handoff de conversación actual.


4. Marca conversación anterior como paused.


5. Actualiza pane active_conversation_id target.


6. Verifica que target conversation no está activa en otro pane.


7. Si está activa en otro pane, bloquea o pide decisión.


8. Sale de Claude actual.


9. Wrapper reanuda target conversation.


10. Registry confirma.



146.3 Switch Transaction Schema

SWITCH_TRANSACTION switch_id: pane_id: from_conversation_id: to_conversation_id: from_session_id: to_session_id: repo_path: cwd: handoff_from: resume_command_to: collision_check: status: created_at: completed_at:

146.4 Collision Rule

La misma conversación no debe estar activa en dos panes a la vez salvo override explícito.

Hard Rule candidata: HR-PANE-SESSION-001: A conversation/session ID must not be active in more than one Cursor pane unless explicitly marked read-only/observer or Owner-overridden.

146.5 Switch Command

Comando futuro sugerido:

/switch-session <conversation_id>

También:

/pane-switch <conversation_id>

Debe ser Cursor-only y registry-aware.


---

147. MULTI-PANE SESSION REGISTRY

147.1 Objetivo

Cuando el Owner abra una terminal nueva en Cursor, el Power Pack debe registrar automáticamente un pane nuevo.

147.2 SessionStart Behavior

En cada SessionStart:

detectar cwd,

detectar workspace,

detectar terminal,

asignar pane_id estable,

registrar conversation/session ID,

actualizar heartbeat,

asociar backlog si existe,

detectar si es nueva terminal o reanudación,

detectar si reemplaza una conversación anterior.


147.3 Pane ID Generation

pane_id debe ser estable dentro del workspace pero no depender de datos frágiles.

Posibles inputs:

workspace path hash,

terminal start timestamp,

parent process chain,

shell PID,

cwd,

random UUID persisted locally.


Nunca usar solo PID como identidad permanente, porque cambia.

147.4 Pane Registry Count

El JSON debe poder responder:

cuántas terminales/panes hay activos,

cuántas sesiones Claude hay activas,

qué conversación corresponde a cada pane,

qué panes están stale,

qué panes necesitan recovery,

qué panes tienen backlog asignado.


147.5 Commands

Comandos futuros:

/panes
/pane-status
/pane-heartbeat
/pane-close
/pane-recover
/pane-assign
/pane-switch

147.6 Pane Status Output

PANE_STATUS_REPORT active_panes: stale_panes: crashed_panes: orphaned_panes: pane_table:

pane_id: pane_index: repo: cwd: conversation_id: task: backlog_item: status: last_heartbeat: lock_scope: collisions: recovery_needed:



---

148. CRASH RECOVERY ORCHESTRATOR

148.1 Propósito

Si Cursor se cierra, crashea, se apaga el ordenador, hay out-of-memory o se va la luz, al volver a abrir Cursor el sistema debe poder reconstruir el estado.

148.2 Realidad técnica

El Power Pack puede registrar y preparar la restauración, pero la apertura física exacta de panes en Cursor puede depender de:

capacidades de Cursor/VS Code,

tasks configuradas,

terminal profiles,

workspace restore behavior,

wrapper scripts,

extensiones o comandos disponibles.


Por tanto, el sistema debe ser honesto:

1. Si puede restaurar automáticamente panes dentro de Cursor, lo hace.


2. Si no puede, genera un Recovery Plan con comandos exactos para abrir cada pane.


3. Nunca abre CMD normal externo como fallback silencioso.



148.3 Crash Recovery State

CRASH_RECOVERY_STATE detected_at: previous_registry: active_panes_before_crash: stale_threshold: panes_to_restore: restore_mode: manual_steps_required: cursor_only: safe_to_restore: collisions: warnings:

148.4 Recovery Flow

1. Cursor vuelve a abrir workspace.


2. SessionStart / bootstrap hook lee pane_registry.


3. Detecta panes stale/crashed.


4. Verifica workspace actual.


5. Genera restore plan.


6. Si auto-restore está soportado:

abre número de terminales requeridas,

lanza wrapper en cada una,

reanuda conversación exacta.



7. Si no:

muestra comandos manuales por pane,

conserva mapping exacto.




148.5 Restore Plan

RESTORE_PLAN workspace: panes_to_restore:

pane_index: repo_path: cwd: conversation_id: resume_command: backlog_item: lock_scope: priority: restore_order: collision_warnings: manual_commands: auto_restore_supported: owner_action_required:


148.6 Hard Rule candidata

HR-CURSOR-RECOVERY-001: Crash recovery must restore Cursor pane state from registry or produce a safe manual restore plan. It must never silently resume sessions in the wrong repo, wrong pane, wrong conversation or external terminal.


---

149. PANE BACKLOG ALLOCATOR

149.1 Propósito

Cada pane debe tener una tarea clara y no colisionar con otros panes.

Si el Owner tiene 3 terminales abiertas, cada una debe avanzar el proyecto en una línea de trabajo distinta.

149.2 Pane Backlog Model

Cada pane puede tener:

active_task

next_task

blocked_task

scope_lock

file_lock

dependency_lock

status

collision_risk

handoff


149.3 Pane Task Assignment

PANE_TASK_ASSIGNMENT task_id: pane_id: project: title: category: priority: scope: allowed_files: forbidden_files: expected_outputs: validation: done_criteria: collision_locks: depends_on: blocks: assigned_at: expires_at: status:

149.4 No-Collision Requirement

Antes de asignar una tarea a un pane:

revisar tareas activas en otros panes,

revisar archivos bloqueados,

revisar scope solapado,

revisar branch,

revisar migration/deploy locks,

revisar si otro pane tiene la misma conversación,

revisar si otro pane está en el mismo bug.


149.5 Collision Types

same file collision

same feature collision

same test collision

same deploy collision

same branch collision

same conversation collision

same backlog item collision

dependency order collision

generated artifact collision

global config collision


149.6 Collision Guard Output

PANE_COLLISION_REPORT status: pass | warning | blocked pane_id: requested_task: collisions: affected_panes: affected_files: recommended_resolution: safe_alternative_task:

149.7 Hard Rule candidata

HR-PANE-BACKLOG-001: Before assigning a task to a Cursor pane, check active pane registry for conversation, file, scope and backlog collisions.


---

150. PANE-SPECIFIC BACKLOG REGENERATION

150.1 Propósito

El backlog debe regenerarse cuando:

se añade una idea,

se completa una tarea,

falla una tarea,

cambia una conversación activa,

se abre/cierra pane,

se detecta collision,

se crea una Hard Rule,

aparece un cascade record,

cambia el estado del proyecto.


150.2 Backlog Regeneration Inputs

project state snapshot,

pane registry,

current locks,

active tasks,

completed tasks,

failed tasks,

new Owner ideas,

CEPS events,

cascade records,

cost autopsy,

secret findings,

verify failures,

demo/revenue readiness.


150.3 Backlog Output

MULTI_PANE_BACKLOG project: generated_at: global_priority: pane_assignments:

pane_id: current_task: next_task: safe_parallel_tasks: forbidden_tasks_due_to_collision: unassigned_tasks: blocked_tasks: recommended_new_pane: recommended_close_pane: collision_warnings:


150.4 Regeneration Rule

Backlog regeneration must preserve ongoing work.

No reasignar una tarea activa a otro pane salvo:

pane crashed,

owner switched,

task failed,

lock expired,

explicit override.



---

151. FILE AND SCOPE LOCKING

151.1 Propósito

Evitar que dos panes trabajen en lo mismo.

151.2 Lock Types

file_lock

directory_lock

feature_lock

bug_lock

test_lock

deploy_lock

migration_lock

config_lock

global_hook_lock

hard_rule_lock

learning_lock


151.3 Lock Schema

SCOPE_LOCK lock_id: type: owner_pane_id: task_id: repo_path: patterns: reason: created_at: expires_at: status: override_allowed: conflict_policy:

151.4 Lock Expiration

Locks deben expirar si:

pane stale,

heartbeat perdido,

task completed,

task failed,

Owner releases lock,

crash recovery reassigns.


Pero nunca liberar lock de deploy/migration automáticamente sin review.

151.5 Lock Conflict Policy

Si hay conflicto:

1. bloquear tarea nueva,


2. ofrecer tarea alternativa,


3. pedir Owner override solo si tiene sentido,


4. registrar collision event.




---

152. EXACT CONVERSATION HANDOFF

152.1 Propósito

Antes de restart, switch o crash recovery, cada conversación debe dejar handoff seguro.

152.2 Handoff Content

EXACT_CONVERSATION_HANDOFF conversation_id: session_id: pane_id: repo_path: cwd: task_id: backlog_item_id: current_goal: completed: not_completed: files_touched: files_intended_next: validation_status: secret_scan_status: cascade_status: cost_status: locks_held: next_safe_command: resume_command: created_at: safe_summary: raw_secrets_included: false

152.3 No Full Conversation Dump

No guardar conversación completa raw si puede contener secretos o ruido.

Guardar:

state summary,

exact IDs,

task status,

evidence paths,

next action,

constraints.


No guardar:

API keys,

.env,

raw terminal logs,

full private prompts,

credentials,

huge transcript.


152.4 Exactness Definition

“Exacta” no significa guardar todo el texto raw. Significa poder reanudar la misma conversation/session ID con el estado operativo correcto y sin pérdida de tarea.


---

153. RESTART BUG-PROOFING

153.1 Bugs posibles

restart reanuda conversación equivocada,

restart se ejecuta en terminal externa,

restart mata pane en vez de salir limpio,

restart intent viejo se reutiliza,

restart duplica sesión,

registry se corrompe,

handoff no se escribe,

conversation ID no existe,

resume command falla,

cwd incorrecto,

pane status queda restarting para siempre,

dos panes reclaman misma conversación,

wrapper no detecta intent,

shell queda en estado raro,

secrets aparecen en handoff,

crash durante registry write.


153.2 Prevention Gates

Antes de restart:

validate Cursor integrated terminal,

validate conversation/session ID exists,

write handoff,

write restart intent,

atomic update registry,

set expiration,

verify resume command template,

check no same conversation active elsewhere,

secret-scan handoff,

create rollback manual command.


Después de restart:

verify resumed conversation ID,

verify cwd,

update registry,

clear intent,

mark previous transaction complete,

restore locks,

assign backlog.


153.3 Restart Failure Recovery

If resume fails:

do not retry infinite loop,

mark recovery_failed,

show manual command,

preserve handoff,

do not clear registry,

do not open external CMD,

do not create duplicate pane.


153.4 Hard Rule candidata

HR-RESTART-002: A restart intent must be single-use, expiring, pane-bound and conversation-bound. Never execute stale or pane-mismatched restart intents.


---

154. CRASH RECOVERY BUG-PROOFING

154.1 Bugs posibles

stale pane treated as active,

active pane treated as crashed,

restoration opens too many panes,

restoration loses cwd,

wrong conversation resumed,

tasks duplicated,

locks lost,

backlog overwritten,

stale registry used,

JSON corrupted,

recovery command contains secret,

external CMD opened,

auto-restore loops forever.


154.2 Prevention Gates

heartbeat timestamps,

registry hash,

last valid backup,

restore dry-run,

workspace match,

cursor-only check,

max restore attempts,

no duplicate conversation IDs,

no duplicate task IDs,

manual fallback,

recovery journal.


154.3 Recovery Idempotency

Running recovery twice must not duplicate panes or tasks.

Each restore action must have:

restore_action_id,

target pane,

target conversation,

status,

executed_at,

idempotency key.


154.4 Hard Rule candidata

HR-RECOVERY-002: Crash recovery must be idempotent. Running the same recovery plan twice must not create duplicate panes, duplicate Claude sessions or duplicate backlog assignments.


---

155. JSON CORRUPTION PREVENTION

155.1 Problema

El pane registry será crítico. Si se corrompe, se pierde routing.

155.2 Required Protections

atomic write,

schema validation,

file lock,

journal append,

last valid backup,

checksum,

recovery from journal,

no concurrent writes without lock,

human-readable repair report.


155.3 Registry Journal

Ubicación:

~/.claude/pp_runtime/cursor_panes/pane_registry.journal.jsonl

Cada entrada:

REGISTRY_JOURNAL_ENTRY event_id: timestamp: event_type: pane_id: conversation_id: before_hash: after_hash: transaction_id: status: safe_summary:

155.4 JSON Repair Flow

If registry corrupt:

1. stop auto-routing,


2. load last valid backup,


3. replay journal if safe,


4. validate,


5. generate repair report,


6. require Owner confirmation if uncertain.



155.5 Hard Rule candidata

HR-PANE-REGISTRY-001: Pane registry writes must be atomic, locked, journaled and schema-validated. If registry validation fails, block routing and recover from last valid backup.


---

156. CURSOR TERMINAL RESTORATION ADAPTER

156.1 Propósito

Separar la lógica de estado del mecanismo concreto de abrir terminales en Cursor.

No mezclar:

registry,

restart,

backlog,

Cursor UI automation.


Crear adapter independiente.

Canonical Name: Cursor Terminal Restoration Adapter

156.2 Adapter Responsibilities

detect Cursor integrated terminal,

identify workspace,

map pane_id to terminal,

generate restore commands,

optionally open terminal if supported,

never open external CMD silently,

verify cwd,

verify wrapper installed,

report unsupported operations honestly.


156.3 Adapter Modes

Mode A: In-Pane Resume Mismo pane, wrapper reanuda conversación tras exit.

Mode B: Manual Restore Plan No auto-open; muestra comandos por pane.

Mode C: Workspace Task Restore Usa tareas del workspace si Cursor/VS Code lo soporta.

Mode D: Unsupported Bloquea auto-restore y da instrucciones.

156.4 Adapter Safety Rule

If the adapter cannot prove it is operating inside Cursor, it must not execute restoration.


---

157. PANE HEARTBEAT SYSTEM

157.1 Propósito

Saber qué panes siguen vivos.

157.2 Heartbeat

Cada pane debe actualizar:

last_heartbeat,

current conversation,

current task,

cwd,

process id,

status,

lock state.


157.3 Heartbeat Frequency

Debe ser suficientemente frecuente para detectar crash, pero no tan frecuente que genere coste o ruido.

Puede actualizar:

on SessionStart,

on UserPromptSubmit,

on Stop,

on significant tool execution,

on SessionEnd,

periodically if lightweight.


157.4 Stale Detection

Si no hay heartbeat tras threshold:

mark stale,

do not immediately reassign high-risk locks,

wait for recovery decision.


157.5 Heartbeat Rule

Heartbeat must be lightweight, secret-free and atomic.


---

158. PANE COMMANDS TO ADD

158.1 /panes

Muestra panes activos.

Output:

pane table,

conversation IDs,

tasks,

statuses,

collisions,

stale panes.


158.2 /restart

Reinicia conversación actual exacta en mismo pane.

Must:

create restart transaction,

write handoff,

write restart intent,

exit cleanly,

wrapper resumes.


158.3 /switch-session <id>

Cambia pane actual a otra conversación.

Must:

save current handoff,

collision check,

update registry,

resume target.


158.4 /pane-recover

Genera plan de recovery desde registry.

158.5 /pane-assign

Asigna backlog item a pane.

158.6 /pane-release

Libera lock/tarea del pane actual.

158.7 /pane-backlog

Muestra backlog específico del pane.

158.8 /pane-router-status

Diagnostica wrapper, registry, cursor detection, restore capability.


---

159. MULTI-PANE BACKLOG COMMANDS

159.1 /parallel-plan

Genera plan seguro para varios panes.

Input:

número de panes deseado,

repo,

objetivo global.


Output:

pane 1 task,

pane 2 task,

pane 3 task,

no-collision locks,

execution order,

merge/validation plan.


159.2 /parallel-rebalance

Reasigna tareas si:

un pane terminó,

un pane falló,

un pane crasheó,

una nueva prioridad apareció.


159.3 /parallel-collisions

Detecta colisiones activas entre panes.

159.4 /parallel-merge-plan

Cuando varios panes modifican partes distintas, genera plan para consolidar.

159.5 Hard Rule candidata

HR-PARALLEL-001: Multi-pane execution must maintain explicit task, file and scope separation. Parallel panes may not modify overlapping files or dependent features without an ordered merge plan.


---

160. TASK LOCKS FOR PARALLEL CLAUDE CODE

160.1 Problema

Si varios Claude Code trabajan en el mismo repo, pueden pisarse.

160.2 Lock Examples

Pane 1:

build Secret Firewall detector.

locks modules/secret_firewall/

locks tests/test_secret_firewall.py


Pane 2:

build Backlog Autopilot docs.

locks docs/backlog_autopilot.md

no access to secret_firewall module.


Pane 3:

build verify probe.

must wait until module path exists.

dependency lock on Pane 1.


160.3 Lock Granularity

Preferred order:

1. feature lock


2. directory lock


3. file lock


4. function lock if safe


5. command lock


6. deploy lock



160.4 Merge Safety

Before merging outputs from multiple panes:

git status check,

diff hygiene,

no secret scan failures,

tests per pane,

integration tests,

conflict detection,

output receipt per pane.



---

161. SESSION ID ACCURACY

161.1 Problema

Todo este sistema depende de guardar el ID exacto.

161.2 ID Types

Distinguir:

conversation_id

session_id

transcript_id

process_id

pane_id

task_id

backlog_item_id

restart_transaction_id


No mezclar.

161.3 ID Source of Truth

El ID exacto debe venir de:

Claude Code session metadata,

official CLI output,

local session files,

hook payload,

validated transcript registry.


No inferir desde texto visible si hay fuente mejor.

161.4 ID Validation

Antes de resume:

ID non-empty,

format valid,

exists in local Claude session store if accessible,

not active in another pane,

matches repo/cwd if metadata exists.


161.5 Hard Rule candidata

HR-SESSION-ID-001: Never resume, switch or restore a Claude conversation from an inferred or unvalidated ID. Use validated session metadata or block with manual recovery instructions.


---

162. BUG-PROOF IMPLEMENTATION PHASES

Phase 0 -- Investigation Only

Objetivo: Verificar técnicamente cómo Claude Code expone session/conversation ID, cómo /restart puede interceptarse, cómo Cursor terminal puede detectarse y qué comando real de resume existe.

No construir todavía.

Output:

verified resume command,

verified session ID source,

verified Cursor terminal signals,

wrapper feasibility,

limitations,

no assumptions.


Phase 1 -- Pane Registry MVP

Implementar:

pane_registry.json,

atomic writes,

schema validation,

backups,

journal,

pane registration on SessionStart,

pane status command.


Gate:

no JSON corruption under concurrent updates.


Phase 2 -- Heartbeat + Stale Detection

Implementar:

heartbeat updates,

stale detection,

pane count,

orphan detection.


Gate:

stale pane detected without deleting registry.


Phase 3 -- Restart Transaction MVP

Implementar:

restart intent,

handoff,

wrapper detection,

in-pane resume,

single-use intent.


Gate:

/restart resumes same conversation in same Cursor pane.


Phase 4 -- Session Switch MVP

Implementar:

switch transaction,

collision check,

handoff old session,

resume target session.


Gate:

pane 2 can switch from conversation 2222 to 4444 safely.


Phase 5 -- Crash Recovery Plan

Implementar:

restore plan,

stale/crashed pane detection,

manual commands,

optional Cursor adapter.


Gate:

after simulated crash, system produces exact restore plan.


Phase 6 -- Multi-Pane Backlog Allocator

Implementar:

pane task assignment,

file/scope locks,

collision guard,

pane-specific backlog.


Gate:

3 panes get 3 non-colliding tasks.


Phase 7 -- Auto-Restore Adapter

Implementar only if technically verified:

Cursor workspace task restore,

integrated terminal creation,

pane command injection if safe.


Gate:

auto-restore never opens external CMD and never resumes wrong session.



---

163. MANDATORY INVESTIGATION QUESTIONS FOR CLAUDE CODE

Antes de implementar, Claude Code debe responder con evidencia:

1. ¿Dónde guarda Claude Code el conversation/session ID localmente?


2. ¿Qué comando exacto permite reanudar una conversación concreta?


3. ¿El comando acepta conversation ID, session ID o transcript ID?


4. ¿Cómo se detecta con certeza que se está en terminal integrada de Cursor?


5. ¿Se puede distinguir Cursor de VS Code?


6. ¿Se puede abrir una nueva terminal integrada de Cursor programáticamente desde el repo?


7. ¿Se puede inyectar un comando en una terminal existente de Cursor de forma segura?


8. ¿O es obligatorio usar wrapper padre dentro de cada terminal?


9. ¿Qué pasa si Claude sale con exit code específico?


10. ¿Se puede crear un /restart command que escriba intent antes de salir?


11. ¿Qué hooks se ejecutan antes/después de exit?


12. ¿Qué pasa si Cursor crashea antes de SessionEnd?


13. ¿Qué datos hay en hook payloads?


14. ¿Qué datos son seguros para guardar?


15. ¿Cómo evitar que dos panes reanuden la misma conversación?



Si alguna respuesta no se puede verificar, bloquear auto-restore y usar manual restore plan.


---

164. ACCEPTANCE TESTS

164.1 Test: Registry Atomicity

Simular 3 panes escribiendo registry.

Expected:

JSON válido,

no pérdida de panes,

journal coherente,

backup creado.


164.2 Test: Same Pane Restart

Pane 1 con conversation 1111 ejecuta /restart.

Expected:

restart intent created,

handoff created,

Claude exits,

wrapper resumes 1111,

pane registry status resumed,

no new external terminal.


164.3 Test: Stale Intent Block

Restart intent viejo existe.

Expected:

not executed,

marked stale,

manual recovery shown.


164.4 Test: Wrong Pane Intent Block

Pane 2 intenta ejecutar intent de Pane 1.

Expected:

blocked,

collision report,

no resume.


164.5 Test: Session Switch

Pane 2 conversation 2222 switches to 4444.

Expected:

2222 paused,

handoff stored,

4444 resumed,

registry updated.


164.6 Test: Duplicate Conversation Collision

Pane 1 already active with 1111. Pane 3 tries to resume 1111.

Expected:

blocked unless explicit override.


164.7 Test: Cursor-Only Enforcement

Run wrapper outside Cursor.

Expected:

auto-restore blocked,

no external CMD opened,

manual instruction shown.


164.8 Test: Crash Recovery Plan

Simulate stale panes.

Expected:

restore plan lists exact pane count,

exact conversations,

exact cwd,

no duplicates,

manual commands safe.


164.9 Test: Backlog Collision

Pane 1 works on file A. Pane 2 is assigned task touching file A.

Expected:

collision blocked,

alternative task proposed.


164.10 Test: Registry Corruption

Corrupt pane_registry.json.

Expected:

routing blocked,

last valid backup loaded,

journal replay attempted,

repair report generated.


164.11 Test: Secret Safety in Handoff

Handoff input contains fake secret.

Expected:

redacted,

raw secret not stored,

secret scan warning.


164.12 Test: No Infinite Restart Loop

Resume command fails.

Expected:

max retry reached,

recovery_failed,

manual command displayed,

no infinite loop.



---

165. FAILURE MODES AND BLOCKERS

165.1 Block auto-restart if:

not inside Cursor terminal,

no wrapper installed,

resume command unknown,

session ID unknown,

registry invalid,

restart intent stale,

pane mismatch,

target conversation active elsewhere,

cwd missing,

handoff failed,

secret scan failed,

lock conflict unresolved.


165.2 Block auto-restore if:

Cursor automation unsupported,

workspace mismatch,

registry corrupt and unrecoverable,

duplicate sessions detected,

restore plan unsafe,

external terminal would be needed,

session metadata missing.


165.3 Degrade gracefully

If automation blocked, output:

SAFE_MANUAL_RECOVERY reason_auto_blocked: pane: repo: cwd: conversation_id: safe_resume_command: backlog_item: warnings: next_step:


---

166. OWNER-SIDE UX

166.1 Desired commands

Owner experience:

/restart

Reinicia misma conversación en mismo pane.

/panes

Muestra sesiones activas.

/switch-session 4444

Cambia pane actual a conversación 4444.

/pane-recover

Recupera panes tras crash.

/parallel-plan 3

Crea plan para 3 terminales sin colisión.

166.2 UX principle

The Owner should not manage IDs manually unless recovery automation is blocked.

The system should show IDs, but not force manual copy-paste in normal path.

166.3 No noise rule

No mostrar registry completo salvo debug.

Mostrar:

pane number,

conversation short ID,

task,

status,

next action.



---

167. DATASET ADDITION: CRITICAL HARD RULES

HR-CURSOR-001

Cursor Pane Continuity OS may only auto-route sessions inside verified Cursor integrated terminals. Never use normal CMD, external PowerShell or Windows Terminal as silent fallback.

HR-RESTART-001

/restart must not kill the Cursor terminal pane. It must create a restart transaction, save handoff, write restart intent, exit Claude cleanly and let the Cursor shell wrapper resume in-place.

HR-RESTART-002

Restart intents are single-use, expiring, pane-bound and conversation-bound. Stale or pane-mismatched intents must be blocked.

HR-PANE-REGISTRY-001

Pane registry writes must be atomic, locked, journaled, schema-validated and recoverable from last valid backup.

HR-SESSION-ID-001

Never resume, switch or restore a Claude conversation from inferred or unvalidated ID. Use verified session metadata or block.

HR-PANE-SESSION-001

The same conversation/session ID must not be active in multiple panes unless explicitly marked observer/read-only or Owner-overridden.

HR-CURSOR-RECOVERY-001

Crash recovery must restore from registry or produce a safe manual restore plan. It must never silently resume wrong repo, wrong pane, wrong conversation or external terminal.

HR-RECOVERY-002

Crash recovery must be idempotent. Running the same recovery plan twice must not duplicate panes, sessions or backlog assignments.

HR-PANE-BACKLOG-001

Before assigning work to a pane, check active registry for conversation, file, scope, deploy and backlog collisions.

HR-PARALLEL-001

Parallel panes must maintain explicit task, file and scope separation. Overlapping work requires ordered merge plan.

HR-HANDOFF-001

Restart, switch and crash recovery must create secret-safe handoff packets before changing session state.

HR-WRAPPER-001

Automatic in-pane resume requires a parent shell wrapper. If wrapper is missing, do not fake command injection; provide manual recovery.


---

168. IMPLEMENTATION PROMPT FOR CLAUDE CODE

Use this prompt to implement the investigation + design safely.

PROMPT:

Act as the implementation engineer for Claude Power Pack.

MISSION: Design and implement the first safe slice of Cursor Pane Continuity OS.

SOURCE OF TRUTH: Use the current Claude Power Pack repo on disk. Verify existing hooks and tools before adding anything. Do not assume command names, session ID format or Cursor automation capability.

CRITICAL REQUIREMENT: This system is Cursor-only. Do not open, target, automate or fallback to normal CMD, external PowerShell, Windows Terminal or any terminal outside Cursor integrated terminal.

PHASE: Start with Phase 0 Investigation Only unless explicitly told otherwise.

INVESTIGATE WITH EVIDENCE:

1. How Claude Code exposes current session/conversation ID.


2. The exact supported resume command.


3. Whether resume uses conversation ID, session ID or transcript ID.


4. What hook payloads contain.


5. How to detect Cursor integrated terminal.


6. Whether Cursor terminal restoration can be automated.


7. Whether a parent shell wrapper is required.


8. Existing PP hooks related to terminal-slot-recorder, Lazarus, restart-target-consumer and mark-live-session.


9. Existing files that should be reused.


10. Risks and blockers.



DO NOT:

Do not implement auto-restore before verifying feasibility.

Do not modify ~/.claude/settings.json directly.

Do not kill terminals.

Do not open external CMD.

Do not hardcode resume command until verified.

Do not infer session IDs from unreliable text.

Do not create duplicate session routes.

Do not store raw secrets in handoff, registry, journal or logs.


OUTPUT: Return:

verified facts,

unknowns,

safe architecture,

proposed files,

proposed commands,

proposed tests,

blockers,

smallest safe implementation slice,

exact acceptance criteria.


IF IMPLEMENTING PHASE 1: Implement only Pane Registry MVP:

atomic pane_registry.json,

schema validation,

journal,

last valid backup,

pane status command,

tests for concurrent writes and corruption recovery.


FINAL RECEIPT: Include files changed, tests run, secret safety status, Cursor-only enforcement status, remaining risks and next phase.


---

169. STRATEGIC CONCLUSION

This addition is not a convenience feature.

It is a multi-session execution operating system.

If done right, Claude Power Pack will be able to coordinate several Cursor terminal panes like parallel workers:

each pane has exact identity,

each conversation is recoverable,

/restart resumes in-place,

/switch-session changes route safely,

crash recovery restores exact state,

backlog is distributed without collision,

JSON registry remains corruption-resistant,

no external CMD fallback,

no duplicate conversations,

no lost tasks,

no hidden terminal chaos.


Canonical principle:

A Cursor pane is an execution lane.
An execution lane must have identity, memory, task, lock, heartbeat, recovery and collision control.

END OF PART VIII.

Continuación directa. Esta Parte IX refuerza el sistema de /restart, panes, registry JSON, crash recovery y backlog paralelo para que Claude Code no lo implemente de forma frágil sobre el PP actual. 

# CLAUDE POWER PACK -- EXTENSION DATASET PART IX
# Cursor Pane Continuity Hardening: State Machines, Wrappers, Idempotency, Recovery, Collision Control and Bug-Proof Guarantees

## 170. CPC-OS HARDENING LAYER

### 170.1 Propósito

La Parte VIII define el Cursor Pane Continuity OS.

La Parte IX endurece ese sistema para que no salga bugueado.

Objetivo:
Convertir `/restart`, `/switch-session`, pane registry, crash recovery y multi-pane backlog en un sistema transaccional, idempotente, verificable y resistente a fallos.

Esto es crítico porque el sistema tocará:
- sesiones activas,
- terminales integradas de Cursor,
- conversación exacta,
- wrappers de shell,
- JSON registry,
- handoffs,
- locks,
- backlog paralelo,
- recovery tras crash.

Un bug aquí puede provocar:
- pérdida de conversación,
- sesión equivocada,
- terminal duplicada,
- pane muerto,
- trabajos colisionando,
- registry corrupto,
- restart loop infinito,
- recuperación falsa,
- backlog pisado,
- confianza rota.

### 170.2 Principio central

Session continuity is infrastructure, not UX sugar.

No se debe implementar como “script que pega comandos”.
Debe implementarse como sistema transaccional con:
- estados,
- invariantes,
- locks,
- journal,
- rollback,
- idempotency keys,
- tests de caos,
- fallback manual seguro.

---

## 171. CANONICAL STATE MACHINES

### 171.1 Propósito

Cada flujo crítico debe tener una máquina de estados explícita.

Sin state machine, Claude Code tenderá a usar booleanos sueltos:
- restarting: true
- active: true
- crashed: true

Eso es frágil.

### 171.2 Pane Lifecycle State Machine

Estados permitidos:

```text
UNREGISTERED
REGISTERING
ACTIVE
IDLE
BUSY
PAUSED
RESTART_REQUESTED
RESTARTING
RESUMING
RESUMED
SWITCH_REQUESTED
SWITCHING
STALE
CRASH_SUSPECTED
RECOVERY_PENDING
RECOVERING
RECOVERED
CLOSED
ORPHANED
FAILED
EXTERNAL_BLOCKED

171.3 Pane Lifecycle Transitions

Permitidas:

UNREGISTERED -> REGISTERING
REGISTERING -> ACTIVE
ACTIVE -> BUSY
BUSY -> IDLE
BUSY -> RESTART_REQUESTED
RESTART_REQUESTED -> RESTARTING
RESTARTING -> RESUMING
RESUMING -> RESUMED
RESUMED -> ACTIVE
ACTIVE -> SWITCH_REQUESTED
SWITCH_REQUESTED -> SWITCHING
SWITCHING -> ACTIVE
ACTIVE -> STALE
BUSY -> STALE
STALE -> CRASH_SUSPECTED
CRASH_SUSPECTED -> RECOVERY_PENDING
RECOVERY_PENDING -> RECOVERING
RECOVERING -> RECOVERED
RECOVERED -> ACTIVE
ACTIVE -> CLOSED
STALE -> ORPHANED
ANY_SAFE_STATE -> FAILED
ANY_UNVERIFIED_TERMINAL -> EXTERNAL_BLOCKED

171.4 Forbidden Transitions

Prohibidas:

UNREGISTERED -> RESUMING
ACTIVE -> RECOVERED
BUSY -> CLOSED without handoff
RESTARTING -> ACTIVE without resume verification
SWITCHING -> ACTIVE without target conversation verification
STALE -> ACTIVE without heartbeat verification
FAILED -> RESUMING without explicit recovery transaction
EXTERNAL_BLOCKED -> RESUMING

171.5 State Transition Record

Cada transición debe registrarse:

STATE_TRANSITION transition_id: pane_id: from_state: to_state: reason: transaction_id: timestamp: validated: validation_evidence: safe_summary:

171.6 Hard Rule candidata

HR-CPC-STATE-001: Cursor pane lifecycle changes must use explicit state machine transitions. Forbidden transitions must block routing and produce a recovery report.


---

172. RESTART STATE MACHINE

172.1 Estados

NO_RESTART
RESTART_REQUESTED
HANDOFF_WRITING
HANDOFF_WRITTEN
INTENT_WRITING
INTENT_WRITTEN
REGISTRY_MARKED_RESTARTING
CLAUDE_EXITING
SHELL_WRAPPER_ACTIVE
RESUME_COMMAND_SELECTED
RESUME_EXECUTING
RESUME_VERIFYING
RESUME_CONFIRMED
INTENT_CONSUMED
REGISTRY_MARKED_RESUMED
RESTART_COMPLETE
RESTART_FAILED
MANUAL_RECOVERY_REQUIRED

172.2 Transiciones críticas

No se puede pasar a CLAUDE_EXITING hasta que:

handoff está escrito,

handoff secret scan pasó,

restart intent está escrito,

registry está marcado como restarting,

resume command template existe,

intent tiene expiry,

pane_id coincide,

conversation_id está validado.


No se puede pasar a RESTART_COMPLETE hasta que:

Claude vuelve a arrancar,

conversation/session ID coincide,

cwd coincide,

pane_id coincide,

intent se consume,

registry se actualiza,

no hay duplicate active conversation.


172.3 Restart Failure States

Fallos posibles:

HANDOFF_FAILED

INTENT_WRITE_FAILED

REGISTRY_WRITE_FAILED

CLAUDE_EXIT_FAILED

WRAPPER_NOT_FOUND

RESUME_COMMAND_UNKNOWN

RESUME_COMMAND_FAILED

RESUME_ID_MISMATCH

PANE_ID_MISMATCH

CWD_MISMATCH

DUPLICATE_SESSION_DETECTED

INTENT_STALE

SECRET_SCAN_FAILED


172.4 Restart Recovery Rule

Cada fallo debe tener acción segura:

no retry infinito,

no terminal externa,

no borrar handoff,

no borrar registry,

mostrar manual recovery,

marcar estado exacto.



---

173. SESSION SWITCH STATE MACHINE

173.1 Estados

NO_SWITCH
SWITCH_REQUESTED
SOURCE_HANDOFF_WRITING
SOURCE_HANDOFF_WRITTEN
TARGET_VALIDATING
COLLISION_CHECKING
TARGET_RESERVED
REGISTRY_MARKED_SWITCHING
SOURCE_EXITING
TARGET_RESUMING
TARGET_VERIFYING
TARGET_CONFIRMED
SOURCE_MARKED_PAUSED
SWITCH_COMPLETE
SWITCH_FAILED
MANUAL_SWITCH_REQUIRED

173.2 Switch Preconditions

Antes de cambiar Pane 2 de conversación 2222 a 4444:

Pane 2 existe.

Pane 2 está en Cursor.

Conversación 2222 está activa o pausada en Pane 2.

Conversación 4444 existe o es reanudable.

Conversación 4444 no está activa en otro pane.

Source handoff escrito.

Target resume command validado.

Registry lock adquirido.

No file/scope lock incompatible.


173.3 Switch Hard Rule

HR-CPC-SWITCH-001: A session switch must save the current conversation handoff before changing the pane active conversation. If target validation or collision check fails, source session remains authoritative.


---

174. CRASH RECOVERY STATE MACHINE

174.1 Estados

NO_RECOVERY
STALE_DETECTED
CRASH_SUSPECTED
REGISTRY_LOADING
REGISTRY_VALIDATED
REGISTRY_REPAIRED
RESTORE_PLAN_BUILDING
RESTORE_PLAN_READY
AUTO_RESTORE_CHECKING
AUTO_RESTORE_BLOCKED
MANUAL_RESTORE_READY
RESTORING_PANE
VERIFYING_RESTORED_PANE
PANE_RESTORED
RECOVERY_COMPLETE
RECOVERY_PARTIAL
RECOVERY_FAILED

174.2 Recovery Preconditions

Auto-recovery solo permitido si:

Cursor terminal support verificado,

workspace coincide,

registry válido o reparado,

no duplicate active sessions,

restore commands safe,

intents no stale,

no external CMD fallback,

no secret risk en commands,

idempotency keys no ejecutadas ya.


174.3 Manual Recovery Is Valid

Si auto-restore no puede probarse, no es fallo.

Debe producir:

número exacto de panes anteriores,

conversación por pane,

cwd por pane,

comando de resume por pane,

backlog asignado,

orden de recuperación,

collision warnings.


174.4 Recovery Hard Rule

HR-CPC-RECOVERY-003: Automatic crash recovery is allowed only when Cursor integrated terminal restoration is verified. Otherwise produce a manual restore plan and do not improvise external terminal automation.


---

175. WRAPPER CONTRACT

175.1 Problema

Cuando Claude Code hace exit, ya no puede escribir comandos en la terminal por sí mismo.

Para que /restart reanude en el mismo pane, debe existir un proceso padre wrapper.

175.2 Canonical Wrapper

Nombre canónico: claude-pp

Responsabilidad:

lanzar Claude Code,

preservar cwd,

detectar exit reason,

leer restart intent,

validar pane_id,

ejecutar resume command,

evitar loops,

registrar resultado,

volver al shell normal si no hay intent.


175.3 Wrapper Contract

WRAPPER_CONTRACT wrapper_name: version: launched_from_cursor: pane_id: workspace_id: repo_path: cwd: shell_kind: supports_restart: supports_switch: supports_recovery: max_resume_attempts: intent_dir: registry_path: logs_path: secret_safe_logging: external_terminal_allowed: false

175.4 Wrapper Must Not

El wrapper no debe:

abrir CMD externo,

abrir PowerShell externo,

ignorar Cursor-only check,

ejecutar intents stale,

ejecutar intents de otro pane,

reintentar infinitamente,

imprimir secrets,

borrar registry corrupto,

resumir conversación no validada.


175.5 Wrapper Exit Codes

Definir exit code semantics:

0  normal exit
10 restart requested and completed
11 restart requested but failed safely
20 switch requested and completed
21 switch requested but failed safely
30 manual recovery required
40 cursor-only check failed
50 registry invalid
60 secret safety block
70 unknown failure

175.6 Wrapper Logs

Logs deben ser:

secret-free,

compactos,

structured,

rotativos,

no raw stdout de Claude,

no raw .env,

no full transcript.


175.7 Hard Rule candidata

HR-CPC-WRAPPER-002: In-place restart requires a verified parent wrapper. If Claude was not launched through the wrapper, /restart may create a handoff and manual resume command but must not pretend it can auto-type after exit.


---

176. REGISTRY INVARIANTS

176.1 Propósito

El pane registry debe tener invariantes que nunca se rompen.

176.2 Global Invariants

INVARIANT-001: Every pane_id is unique.

INVARIANT-002: Every active conversation_id is active in at most one pane unless explicitly observer-mode.

INVARIANT-003: Every active pane must have cwd and repo_path.

INVARIANT-004: Every restarting pane must have restart_transaction_id.

INVARIANT-005: Every switching pane must have switch_transaction_id.

INVARIANT-006: Every busy pane must have task_id or explicit unknown_task reason.

INVARIANT-007: Every task assigned to a pane must have collision status.

INVARIANT-008: Every lock must point to existing pane_id or be expired/released.

INVARIANT-009: Every registry write must update checksum.

INVARIANT-010: No registry field may contain raw secret-like value.

176.3 Registry Validation Report

REGISTRY_VALIDATION_REPORT status: schema_valid: checksum_valid: backup_available: journal_available: pane_count: active_conversation_duplicates: orphan_locks: stale_panes: secret_findings: repair_possible: routing_allowed:

176.4 Routing Block Rule

If registry invariants fail, block:

restart,

switch,

auto-recovery,

parallel assignment.


Allow:

status report,

repair,

manual recovery plan.



---

177. TRANSACTION JOURNALING

177.1 Propósito

Cada operación crítica debe dejar journal.

177.2 Transaction Types

pane_register

heartbeat

restart

resume

switch

crash_recovery

pane_close

backlog_assign

lock_acquire

lock_release

registry_repair

manual_override


177.3 Transaction Schema

TRANSACTION_RECORD transaction_id: type: pane_id: conversation_id: task_id: started_at: completed_at: state_before: state_after: registry_hash_before: registry_hash_after: status: idempotency_key: safe_summary: error_code: manual_action_required:

177.4 Journal Rule

The registry is current state. The journal is history. The backup is recovery.

No critical operation should update current state without journal.

177.5 Idempotency Key

Cada transacción debe tener key estable:

<transaction_type>:<pane_id>:<conversation_id>:<timestamp_bucket_or_uuid>

Para recovery:

recovery:<workspace_id>:<pane_id>:<conversation_id>:<crash_epoch>


---

178. IDEMPOTENCY HARDENING

178.1 Problema

Los restores/restarts pueden ejecutarse dos veces.

178.2 Idempotency Requirements

Si /restart se ejecuta dos veces:

no duplicar intents,

no duplicar handoffs,

no crear segunda sesión activa,

no borrar estado válido.


Si recovery se ejecuta dos veces:

no abrir dos panes para la misma conversación,

no reasignar misma tarea,

no duplicar locks.


Si switch se repite:

si ya está en target conversation, reportar already_switched.


178.3 Idempotent Results

Cada operación debe poder devolver:

completed_now

already_completed

blocked

stale

failed_safely


178.4 Hard Rule candidata

HR-CPC-IDEMPOTENCY-001: Restart, switch and recovery operations must be idempotent. Re-running the same transaction must not duplicate sessions, panes, locks, handoffs or backlog assignments.


---

179. HEARTBEAT HARDENING

179.1 Problema

Heartbeat mal diseñado puede generar falsos crashes o coste excesivo.

179.2 Heartbeat Payload

HEARTBEAT pane_id: conversation_id: session_id: process_id: cwd: repo_path: task_id: state: timestamp: wrapper_active: cursor_integrated: safe_summary: secret_free: true

179.3 Heartbeat Events

Actualizar en:

wrapper start,

Claude start,

SessionStart,

UserPromptSubmit,

Stop,

restart requested,

switch requested,

handoff written,

resume confirmed,

SessionEnd,

wrapper exit.


179.4 Stale Thresholds

Definir thresholds por estado:

ACTIVE: stale if no heartbeat after moderate threshold.

BUSY: longer threshold.

RESTARTING: short threshold; should transition quickly.

RESUMING: short threshold; if exceeded, recovery needed.

PAUSED: not stale; intentionally inactive.

CLOSED: terminal closed intentionally.

179.5 False Positive Guard

No marcar crashed solo porque no hubo heartbeat si:

pane está paused,

task larga sin hook events pero process alive,

system sleep detected,

Cursor restart detected.



---

180. CURSOR DETECTION HARDENING

180.1 Problema

Detectar Cursor incorrectamente puede lanzar sesiones fuera de Cursor.

180.2 Detection Levels

CD0: Unknown terminal.

CD1: VS Code/Cursor-like integrated terminal.

CD2: Cursor-like environment detected.

CD3: Cursor workspace + integrated terminal + wrapper active.

CD4: Verified Cursor Pane Continuity environment.

180.3 Auto Routing Requirement

Auto restart/resume requires CD3+. Auto crash recovery requires CD4.

If below:

block auto route,

show manual instructions.


180.4 Detection Evidence

Store:

env signals,

parent process signals,

workspace path,

wrapper marker,

pane_id,

terminal profile,

confidence.


Do not store:

env values,

secrets,

full process dump if sensitive.


180.5 Hard Rule candidata

HR-CPC-CURSOR-DETECT-001: Auto-routing requires verified Cursor integrated terminal evidence. Low-confidence Cursor detection must degrade to manual recovery.


---

181. MULTI-PANE COLLISION HARDENING

181.1 Problema

Varios panes trabajando en paralelo pueden generar conflictos silenciosos.

181.2 Collision Matrix

Collision Type	Severity	Default

same conversation active twice	critical	block
same file write	high	block
same directory refactor	high	block
same test suite mutation	medium	warn/block
same deploy target	critical	block
same global config	critical	block
same hard rule file	critical	block
same generated evidence dir	medium	warn
same backlog item	high	block
dependency order overlap	medium	sequence


181.3 Parallel Work Modes

Mode 1: Independent files.

Mode 2: Independent features.

Mode 3: Producer-consumer sequence.

Mode 4: Review-only observer.

Mode 5: Blocked due to collision.

181.4 Observer Mode

Una conversación puede abrirse en otro pane solo si:

read-only observer,

no writes,

no backlog assignment,

no locks,

explicit Owner override.


181.5 Collision Event

COLLISION_EVENT collision_id: type: panes: conversations: files: tasks: severity: detected_at: decision: alternative_task: owner_override:


---

182. BACKLOG ROUTER HARDENING

182.1 Propósito

El backlog multi-pane debe asignar tareas sin colisión y con sentido estratégico.

182.2 Assignment Preconditions

Antes de asignar:

registry válido,

pane vivo,

no conversation duplicate,

locks compatibles,

task tiene done criteria,

task tiene validation,

task no es busywork,

task cabe en pane context,

task no depende de tarea sin completar.


182.3 Assignment Modes

AUTO: PP asigna tarea segura.

SUGGEST: PP recomienda, Owner decide.

BLOCK: PP detecta colisión/riesgo.

MANUAL: Owner asigna explícitamente.

182.4 Pane Task Queue

Cada pane puede tener:

current_task
next_task
parking_lot
blocked_tasks
completed_recently
failed_recently

182.5 Backlog Regeneration Invariants

no perder tareas activas,

no duplicar tarea completada,

no reasignar tarea locked,

no ignorar P0 secret/cascade risk,

no priorizar cosmetic sobre safety,

no crear tasks sin validation.


182.6 Hard Rule candidata

HR-CPC-BACKLOG-ROUTER-001: Pane backlog assignment must preserve active work, respect locks, avoid duplicates and prioritize P0 safety/cascade/recovery risks above new feature work.


---

183. HANDOFF HARDENING

183.1 Problema

Un handoff pobre hace que resume sea “misma conversación” pero mal estado operativo.

183.2 Handoff Minimum Required Fields

conversation/session ID,

pane_id,

repo_path,

cwd,

current task,

exact last safe state,

files touched,

files not to touch,

validation status,

secret status,

locks,

next action,

stop conditions,

backlog link.


183.3 Handoff Must Exclude

raw secrets,

raw .env,

full terminal logs,

full transcript,

huge datasets,

irrelevant conversation,

unverified claims,

stale assumptions.


183.4 Handoff Quality Score

Dimensions:

exact session routing,

task continuity,

safety,

validation,

next action,

collision awareness,

secret-free,

compactness.


Minimum: 80/100 for restart/switch. 90/100 for crash recovery.

183.5 Handoff Failure Rule

If safe handoff cannot be written, block restart/switch and output manual safe summary.


---

184. RESUME COMMAND HARDENING

184.1 Problema

Hardcodear el comando de resume puede romper todo.

184.2 Resume Command Registry

Ubicación sugerida:

~/.claude/pp_runtime/cursor_panes/resume_command_registry.json

Campos:

RESUME_COMMAND_REGISTRY schema_version: detected_cli: detected_version: resume_syntax: id_type: validated_at: validation_method: supports_session_id: supports_conversation_id: supports_transcript_id: requires_cwd: notes: safe_template:

184.3 Command Validation

Antes de usar:

CLI exists,

version known,

help output confirms resume syntax,

dry-run or safe validation if possible,

ID type understood,

no secrets in command.


184.4 No Hardcode Rule

HR-CPC-RESUME-001: Do not hardcode Claude resume syntax or ID type. Detect, validate and store resume command capability before enabling auto-restart or switch.


---

185. PANE RECOVERY UI CONTRACT

185.1 Propósito

Cuando algo falle, el Owner necesita una salida clara.

185.2 Recovery UI Output

CURSOR_PANE_RECOVERY_REPORT status: what_happened: auto_recovery_possible: why_or_why_not: panes_detected: panes_to_restore: manual_commands: collisions: unsafe_items: recommended_order: next_step:

185.3 Panic Avoidance

No decir:

“lost”

“impossible”

“everything gone”


Si hay registry/handoff:

explain exact recovery path.


Si no hay:

explain what can still be reconstructed.


185.4 Manual Command Safety

Manual commands must:

run inside Cursor terminal,

include cwd,

include validated resume ID,

not include secrets,

avoid external CMD.



---

186. CHAOS TESTING FOR CPC-OS

186.1 Propósito

No basta con happy path.

Hay que simular fallos.

186.2 Chaos Tests

Test A: Crash during registry write.

Expected:

backup valid,

journal replay,

no corrupted routing.


Test B: Crash after handoff but before intent.

Expected:

no auto-restart,

manual recovery available.


Test C: Crash after intent but before Claude exit.

Expected:

stale intent handling,

no duplicate resume.


Test D: Wrapper resumes wrong cwd.

Expected:

block and report CWD mismatch.


Test E: Two panes claim same conversation.

Expected:

duplicate collision block.


Test F: Registry lock stuck.

Expected:

stale lock detection,

safe repair path.


Test G: Restart command fails.

Expected:

no infinite loop,

recovery_failed,

manual command.


Test H: Cursor detection uncertain.

Expected:

auto-route blocked.


Test I: Backlog assigns same file to two panes.

Expected:

collision.


Test J: Handoff contains fake secret.

Expected:

redacted and warning.


Test K: Resume ID missing.

Expected:

block, no inferred ID.


Test L: Owner switches Pane 2 to conversation 4444 while Pane 4 has 4444 active.

Expected:

block or observer override required.


186.3 Chaos Acceptance

CPC-OS passes chaos if:

no external terminal opens,

no duplicate conversation resumes,

no registry corruption persists,

no raw secrets stored,

no infinite loop,

manual recovery always available.



---

187. DEVELOPMENT PHASES WITH BUG-PROOF GATES

187.1 Phase 0 Gate -- Reality Discovery

Must verify:

session ID source,

resume command,

Cursor detection,

wrapper requirement,

existing PP hooks overlap.


No implementation beyond docs/probes.

187.2 Phase 1 Gate -- Registry Only

Must pass:

schema validation,

atomic writes,

concurrent write simulation,

backup restore,

journal append,

secret scan.


No restart yet.

187.3 Phase 2 Gate -- Wrapper Dry Run

Must pass:

wrapper launches command,

detects Cursor,

reads empty/no intent,

exits normally,

no external terminal.


No real resume yet.

187.4 Phase 3 Gate -- Restart Intent Dry Run

Must pass:

creates intent,

validates expiry,

consumes once,

rejects stale,

rejects wrong pane.


No actual Claude resume yet unless command verified.

187.5 Phase 4 Gate -- Real In-Pane Restart

Must pass:

same pane,

same cwd,

same conversation,

registry updated,

no duplicate.


187.6 Phase 5 Gate -- Switch Session

Must pass:

source handoff,

target validation,

collision check,

target resume,

source paused.


187.7 Phase 6 Gate -- Recovery Plan

Must pass:

stale detection,

restore plan,

safe manual commands,

no external CMD.


187.8 Phase 7 Gate -- Multi-Pane Backlog

Must pass:

assignment,

locks,

collision detection,

rebalancing.


187.9 Phase 8 Gate -- Auto-Restore

Only if Cursor adapter support proven.

Must pass:

idempotency,

no duplicates,

no wrong pane,

no external terminal.



---

188. CPC-OS VERIFY PROBES

188.1 Probes to add

tools/verify_cursor_pane_registry.py
tools/verify_cursor_restart_router.py
tools/verify_cursor_switch_router.py
tools/verify_cursor_crash_recovery.py
tools/verify_pane_backlog_allocator.py
tools/verify_cpc_os.py

188.2 Probe output standard

CURSOR_PANE_REGISTRY_PROBE = N/M
CURSOR_RESTART_ROUTER_PROBE = N/M
CURSOR_SWITCH_ROUTER_PROBE = N/M
CURSOR_CRASH_RECOVERY_PROBE = N/M
PANE_BACKLOG_ALLOCATOR_PROBE = N/M
CPC_OS_PROBE = N/M

188.3 verify_spp future rows

Add:

cursor-pane-registry

cursor-restart-router

cursor-switch-router

cursor-crash-recovery

pane-backlog-allocator

cpc-os


188.4 Probe Rule

If CPC-OS probes fail, disable auto-restart/auto-recovery and degrade to manual plan.


---

189. CPC-OS TEST SUITES

189.1 Unit tests

tests/test_cpc_state_machine.py
tests/test_pane_registry.py
tests/test_restart_transaction.py
tests/test_switch_transaction.py
tests/test_crash_recovery_plan.py
tests/test_pane_locks.py
tests/test_pane_backlog_allocator.py
tests/test_cursor_detection.py
tests/test_resume_command_registry.py
tests/test_cpc_handoff.py

189.2 Integration tests

tests/integration/test_restart_intent_consumption.py
tests/integration/test_registry_journal_repair.py
tests/integration/test_multi_pane_collision.py
tests/integration/test_switch_session_collision.py
tests/integration/test_crash_recovery_idempotency.py
tests/integration/test_wrapper_no_external_terminal.py

189.3 Safety tests

tests/safety/test_handoff_secret_redaction.py
tests/safety/test_registry_no_raw_secrets.py
tests/safety/test_recovery_commands_no_secrets.py
tests/safety/test_external_terminal_block.py

189.4 Chaos tests

tests/chaos/test_registry_write_crash.py
tests/chaos/test_restart_mid_transaction_crash.py
tests/chaos/test_duplicate_conversation_race.py
tests/chaos/test_stale_intent_replay.py
tests/chaos/test_wrapper_resume_failure_loop.py


---

190. CPC-OS MASTER IMPLEMENTATION PROMPT

Use this prompt when sending CPC-OS hardening to Claude Code.

PROMPT:

Act as the implementation engineer for Claude Power Pack CPC-OS.

MISSION: Implement Cursor Pane Continuity OS safely and incrementally. The goal is exact in-Cursor restart/resume, session switching, pane registry, crash recovery and multi-pane backlog coordination without bugs, duplicate sessions, wrong resumes, registry corruption or external terminal fallback.

SOURCE OF TRUTH: Use the repo on disk. Verify existing hooks, Lazarus/session tools, terminal-slot-recorder, restart-target-consumer and mark-live-session before designing new files.

CRITICAL NON-NEGOTIABLES:

Cursor integrated terminal only.

Never open or target normal CMD, external PowerShell or Windows Terminal.

Do not hardcode resume command syntax.

Do not infer session IDs.

Do not auto-restore until Cursor automation is verified.

Do not implement broad phases at once.

Do not write raw secrets to registry, handoff, journal, logs or recovery commands.

Do not modify ~/.claude/settings.json directly without Owner-side script, dry-run, backup and validation.

Do not create duplicate conversation sessions.

Do not allow restart loops.

Do not assign same task/files to multiple panes.


PHASE ORDER:

1. Phase 0: investigation only.


2. Phase 1: registry MVP.


3. Phase 2: wrapper dry-run.


4. Phase 3: restart intent dry-run.


5. Phase 4: real in-pane restart.


6. Phase 5: switch session.


7. Phase 6: crash recovery plan.


8. Phase 7: multi-pane backlog allocator.


9. Phase 8: auto-restore only if verified.



CURRENT TASK: Implement only the selected phase. If no phase is specified, do Phase 0 only.

REQUIRED OUTPUT:

verified facts,

unknowns,

files changed,

tests added,

tests run,

safety status,

Cursor-only status,

secret status,

registry integrity status,

remaining risks,

next safe phase.


STOP IF:

Cursor detection is uncertain,

resume command is unknown,

session ID source is unknown,

registry cannot be written atomically,

wrapper cannot be verified,

a command would open external terminal,

a secret appears in output,

task scope expands beyond current phase.


ACCEPTANCE: Do not mark complete unless phase-specific gate passes.


---

191. PART IX CANONICAL PRINCIPLES

191.1 State Machines Prevent Terminal Chaos

Pane, restart, switch and recovery flows must be explicit state machines, not loose booleans.

191.2 Wrapper Is Mandatory For In-Place Restart

After Claude exits, only the parent shell wrapper can resume in the same Cursor terminal.

191.3 Cursor-Only Means Cursor-Only

No normal CMD fallback. No external terminal workaround. No silent process outside Cursor.

191.4 Registry Is Critical Infrastructure

Atomic writes, locks, journal, backup, checksum and schema validation are mandatory.

191.5 Recovery Must Be Idempotent

Running recovery twice must not duplicate panes, sessions, tasks or locks.

191.6 Conversation IDs Must Be Verified

No inferred IDs. No guessed resume targets. No stale intent replay.

191.7 Backlog Parallelism Requires Locks

Multiple panes need file, scope, feature and deploy locks.

191.8 Manual Recovery Is Better Than Unsafe Automation

If auto-restore cannot be proven safe, produce exact manual commands.

191.9 Chaos Tests Are Required

Happy path tests are insufficient for CPC-OS.

191.10 The Goal Is Exact Continuity

Same Cursor pane, same repo, same cwd, same conversation, same task state, no duplicate, no external terminal, no secret leak.

END OF PART IX.

Continuación directa. Esta Parte X sigue sobre el sistema CPC-OS encima del Power Pack actual, que ya tiene hooks de sesión, Lazarus/restart-related tooling, TIS/TCO, CEPS y hard rules como base. 

# CLAUDE POWER PACK -- EXTENSION DATASET PART X
# Cursor Pane Continuity OS: Race Conditions, Wrapper Protocols, Recovery Guarantees, Parallel Execution Safety and Zero-Bug Implementation Doctrine

## 192. CPC-OS ZERO-BUG DOCTRINE

### 192.1 Propósito

Esta Parte X endurece aún más el Cursor Pane Continuity OS.

La prioridad ya no es solo que `/restart`, `/switch-session`, pane registry y crash recovery funcionen.

La prioridad es que no fallen de forma peligrosa.

Un fallo peligroso sería:
- reanudar conversación equivocada,
- abrir terminal fuera de Cursor,
- duplicar una sesión activa,
- asignar dos panes al mismo archivo,
- perder handoff,
- corromper JSON,
- ejecutar restart intent viejo,
- iniciar bucle infinito de restart,
- marcar como recovered algo que no se verificó,
- perder backlog activo,
- guardar secretos en registry/handoff/journal,
- mezclar session_id con conversation_id,
- restaurar cwd incorrecto,
- continuar en repo equivocado.

### 192.2 Principio central

CPC-OS must prefer safe non-automation over unsafe automation.

Si no se puede verificar:
- Cursor terminal,
- session ID,
- resume command,
- wrapper,
- cwd,
- registry integrity,
- collision status,

entonces el sistema debe bloquear auto-routing y producir manual recovery plan.

---

## 193. RACE CONDITION PREVENTION

### 193.1 Problema

CPC-OS tendrá varios procesos/panes escribiendo o leyendo estado compartido.

Race conditions posibles:
- dos panes escriben `pane_registry.json` al mismo tiempo,
- dos panes intentan reclamar misma conversación,
- recovery corre mientras restart está en progreso,
- backlog se regenera mientras un pane toma tarea,
- heartbeat marca stale durante restart legítimo,
- switch-session cambia target mientras wrapper consume intent,
- registry repair ocurre mientras otro proceso escribe,
- lock expira mientras pane sigue trabajando,
- crash recovery reasigna tarea que todavía está activa.

### 193.2 Solución

Todas las operaciones críticas deben usar lock + transaction + revalidation.

No basta con:
1. leer estado,
2. decidir,
3. escribir.

Debe ser:

1. acquire lock,
2. read latest state,
3. validate invariants,
4. apply change in memory,
5. validate new state,
6. write temp,
7. atomic replace,
8. journal,
9. release lock,
10. re-read if operation depends on exact current state.

### 193.3 Critical Sections

Operaciones que requieren lock exclusivo:

- pane registration,
- pane close,
- restart intent creation,
- restart intent consumption,
- session switch,
- crash recovery plan activation,
- backlog assignment,
- lock acquisition,
- lock release,
- registry repair,
- conversation active claim,
- conversation release,
- task reassignment.

### 193.4 Lock File

Ubicación sugerida:

```text
~/.claude/pp_runtime/cursor_panes/pane_registry.lock

193.5 Lock Requirements

atomic acquisition,

timeout,

stale lock detection,

owner/process metadata,

no infinite wait,

repair command if stuck,

never delete lock blindly.


193.6 Stale Lock Handling

If lock is stale:

1. verify owner process dead if possible,


2. inspect journal,


3. inspect registry checksum,


4. create stale lock report,


5. recover only if safe,


6. otherwise manual intervention.



193.7 Hard Rule candidata

HR-CPC-RACE-001: Any operation that changes pane registry, conversation ownership, restart intent, switch intent, recovery state, pane backlog or scope locks must acquire an exclusive lock and revalidate state immediately before writing.


---

194. CONVERSATION OWNERSHIP MODEL

194.1 Propósito

Evitar que dos panes crean ser dueños de la misma conversación.

194.2 Conversation Ownership

Cada conversación puede estar en uno de estos estados:

UNSEEN
AVAILABLE
CLAIMED_ACTIVE
CLAIMED_PAUSED
CLAIMED_RESTARTING
CLAIMED_SWITCHING
CLAIMED_RECOVERING
OBSERVER_READ_ONLY
ORPHANED
UNKNOWN

194.3 Ownership Record

CONVERSATION_OWNERSHIP conversation_id: session_id: owner_pane_id: owner_workspace_id: owner_repo_path: ownership_state: claimed_at: last_verified_at: claim_transaction_id: observer_panes: allow_duplicate: false reason: expires_at:

194.4 Claim Rule

Antes de reanudar una conversación:

buscar ownership,

verificar si ya está claimed active,

si active en otro pane, bloquear,

si stale/orphaned, entrar recovery flow,

si paused, permitir switch/resume con transaction,

si observer, solo read-only.


194.5 Release Rule

Una conversación solo se libera si:

pane close confirmed,

switch completed,

restart completed,

recovery reclaims,

Owner releases manually,

stale timeout + process dead + no heartbeat.


194.6 Hard Rule candidata

HR-CPC-OWNERSHIP-001: A conversation must be claimed before resume and released only through a validated transaction. Duplicate active ownership is blocked by default.


---

195. PANE ID STABILITY

195.1 Problema

PID cambia. Terminal index puede cambiar. Cursor window puede cambiar.

Si pane_id depende de algo frágil, recovery fallará.

195.2 Pane Identity Layers

Use layered identity:

pane_uuid: generado y persistido.

workspace_id: hash de workspace path.

terminal_instance_hint: metadata de wrapper.

shell_pid: runtime only.

claude_pid: runtime only.

pane_index: display only.

cursor_window_id: best effort.


195.3 Stable Pane ID

pane_id debe ser UUID persistido en runtime file de pane.

Ubicación posible:

~/.claude/pp_runtime/cursor_panes/pane_markers/<pane_uuid>.json

195.4 Pane Marker

PANE_MARKER pane_id: workspace_id: repo_path: created_at: last_seen_at: wrapper_instance_id: cursor_detect_level: shell_kind: safe_label:

195.5 Pane Index

pane_index es solo visual:

Pane 1,

Pane 2,

Pane 3.


No usar pane_index como source of truth.

195.6 Hard Rule candidata

HR-CPC-PANE-ID-001: Pane identity must use a persisted UUID. Process IDs and display indexes are runtime hints only and must not be used as permanent pane identity.


---

196. WRAPPER PROTOCOL V2

196.1 Propósito

Definir contrato más fuerte para claude-pp.

196.2 Wrapper Stages

WRAPPER_INIT
CURSOR_DETECTION
PANE_MARKER_LOAD_OR_CREATE
REGISTRY_REGISTER
CLAUDE_LAUNCH
CLAUDE_RUNNING
CLAUDE_EXIT_DETECTED
EXIT_REASON_CLASSIFICATION
INTENT_LOOKUP
INTENT_VALIDATION
RESUME_OR_EXIT_DECISION
RESUME_EXECUTION
RESUME_VERIFICATION
REGISTRY_UPDATE
WRAPPER_DONE

196.3 Wrapper Inputs

cwd

optional conversation_id

optional resume flag

optional pane_id

optional task_id

env marker

command args

runtime directory


196.4 Wrapper Outputs

heartbeat records

registry updates

wrapper logs

exit status

manual recovery message if needed.


196.5 Wrapper Exit Reason Classification

Possible reasons:

normal_exit

restart_requested

switch_requested

crash_or_error

manual_exit

unknown_exit

secret_block

registry_error

cursor_block


196.6 Wrapper Retry Policy

Max resume attempts:

default 1.

optional 2 only if failure is transient and safe.

never infinite.


Retry forbidden if:

ID mismatch,

cwd mismatch,

pane mismatch,

duplicate active conversation,

stale intent,

secret scan fail,

Cursor detection fail.


196.7 Wrapper Safety

The wrapper must never:

store raw Claude output,

store transcript raw,

store secrets,

print env values,

open external terminal,

silently change cwd,

consume another pane’s intent,

continue after registry invariant failure.



---

197. RESTART INTENT V2

197.1 Propósito

Hacer restart intents seguros, de un solo uso y resistentes a replay.

197.2 Restart Intent Fields

RESTART_INTENT_V2 schema_version: intent_id: intent_type: restart pane_id: workspace_id: repo_path: cwd: conversation_id: session_id: id_type: resume_command_template_id: resume_command_safe_preview: handoff_path: created_at: expires_at: single_use: true consumed_at: consumed_by_wrapper_id: state: preconditions: cursor_only: pane_match: cwd_match: conversation_validated: registry_hash: handoff_hash: secret_scan_passed: idempotency_key: signature_or_checksum: safe_to_execute:

197.3 Intent States

CREATED
VALIDATED
READY
CONSUMING
CONSUMED
STALE
BLOCKED
FAILED
CANCELLED

197.4 Intent Consumption Rule

Before consuming:

intent exists,

state READY,

not expired,

not consumed,

pane_id matches wrapper,

workspace matches,

cwd exists,

conversation claim allowed,

registry hash compatible,

handoff exists,

secret scan passed.


After consuming:

mark CONSUMING,

execute resume,

verify,

mark CONSUMED only after success,

else FAILED with reason.


197.5 Hard Rule candidata

HR-CPC-INTENT-001: Restart and switch intents must be single-use transaction objects with expiry, pane binding, workspace binding, checksum and consumption state. Plain marker files are not sufficient.


---

198. SWITCH INTENT V2

198.1 Propósito

Switch de conversación debe ser tan seguro como restart.

198.2 Switch Intent Fields

SWITCH_INTENT_V2 intent_id: intent_type: switch pane_id: workspace_id: repo_path: cwd: from_conversation_id: to_conversation_id: from_session_id: to_session_id: source_handoff_path: target_validation_status: collision_check_status: ownership_claim_status: created_at: expires_at: state: idempotency_key: safe_to_execute:

198.3 Switch Preconditions

source conversation active in pane,

source handoff secret-safe,

target conversation resumable,

target not active elsewhere,

target cwd compatible or explicitly changed,

backlog task updated,

locks transferred or released safely.


198.4 Switch Failure Safety

If target resume fails:

do not lose source handoff,

source remains recoverable,

pane marked switch_failed,

manual restore commands for source and target.



---

199. RECOVERY PLAN V2

199.1 Propósito

Recovery plan debe ser ejecutable, idempotente y seguro.

199.2 Recovery Plan Fields

RECOVERY_PLAN_V2 plan_id: workspace_id: created_at: based_on_registry_hash: based_on_journal_until: cursor_auto_supported: manual_required: panes_before_crash: restore_actions:

action_id: pane_display_index: pane_id: repo_path: cwd: conversation_id: session_id: id_type: resume_command_safe: backlog_item: locks_to_restore: depends_on: status: idempotency_key: collision_checks: unsafe_to_auto_restore: manual_commands: owner_notes: expires_at:


199.3 Restore Action States

PENDING
READY
EXECUTING
VERIFIED
SKIPPED_ALREADY_ACTIVE
BLOCKED_COLLISION
FAILED_SAFE
MANUAL_REQUIRED

199.4 Recovery Plan Rule

A recovery plan is not a log. It is an executable transaction plan.

If it cannot be executed safely, it must still provide manual safe commands.


---

200. MANUAL RECOVERY COMMAND CONTRACT

200.1 Propósito

Cuando no se puede auto-restaurar, el Owner necesita comandos seguros para pegar en Cursor.

200.2 Manual Command Requirements

Cada comando debe:

empezar con cd al cwd correcto o instrucción de abrir terminal en cwd,

usar wrapper si existe,

usar resume command validado,

incluir conversation/session ID,

no incluir secrets,

indicar pane destino,

indicar task/backlog,

ser copy-pasteable,

advertir si otra conversación ya está activa.


200.3 Manual Recovery Format

MANUAL_RECOVERY_COMMAND pane_label: repo_path: cwd: conversation_short_id: task: command: warning: after_run_validation:

200.4 Rule

Manual recovery commands must be safer than auto-recovery, not less safe.


---

201. BACKLOG-PANE ISOLATION V2

201.1 Propósito

El backlog por pane no solo evita colisiones, también debe aprovechar paralelismo real.

201.2 Parallel Task Classes

PTC-1: Independent docs/task Safe for parallel execution.

PTC-2: Independent module Safe if directories differ.

PTC-3: Shared tests Requires sequencing.

PTC-4: Shared core architecture Not safe parallel unless one pane is review-only.

PTC-5: Deploy/global config Exclusive lock.

PTC-6: Secret/security Exclusive lock + high scrutiny.

PTC-7: Generated evidence/report Parallel allowed only with unique output paths.

201.3 Pane Assignment Strategy

For N panes:

1. Assign highest priority exclusive risk task to Pane 1.


2. Assign independent safe task to Pane 2.


3. Assign review/test/doc task to Pane 3.


4. Avoid shared core files.


5. Avoid same test files.


6. Avoid same generated output paths.


7. Keep one pane for integration/merge if needed.



201.4 Pane Backlog Refresh

Refresh after:

task complete,

task failed,

pane crash,

switch,

restart,

collision,

new Owner idea,

hard rule created,

secret finding,

cost firebreak,

cascade record.


201.5 Backlog Isolation Rule

HR-CPC-BACKLOG-ISO-001: Pane backlog assignments must classify parallel safety class before execution. Exclusive tasks cannot be assigned to multiple panes.


---

202. MERGE AND CONSOLIDATION PROTOCOL

202.1 Problema

Si varios panes trabajan en paralelo, habrá que consolidar.

202.2 Merge Preconditions

Before consolidation:

all active pane receipts collected,

git status clean or understood,

secret scan pass,

tests per pane run,

no unresolved collisions,

no uncommitted generated junk,

no duplicate hard rules,

no conflicting docs.


202.3 Pane Receipt

PANE_EXECUTION_RECEIPT pane_id: conversation_id: task_id: files_changed: validation: secret_scan: locks_released: remaining_risks: handoff_path: merge_notes:

202.4 Consolidation Plan

CONSOLIDATION_PLAN project: panes_included: files_by_pane: conflicts: validation_order: merge_order: tests_to_run: secret_scan_required: rollback_plan: final_owner_summary:

202.5 Hard Rule candidata

HR-CPC-MERGE-001: Parallel pane work must not be considered complete until pane receipts are collected and consolidation validation passes.


---

203. COMMAND UX HARDENING

203.1 /restart

Must show minimal confirmation:

Restart prepared:
- pane: Pane 2
- conversation: abc123
- cwd: ...
- handoff: written
- resume: ready
Exiting Claude; wrapper will resume in this same Cursor pane.

If wrapper missing:

Restart handoff created, but in-place auto-resume is unavailable because Claude was not launched through claude-pp wrapper.
Manual recovery command:
...

203.2 /panes

Must show concise table:

Pane | Conversation | Status | Task | Locks | Last heartbeat
1    | 1111         | busy   | Secret scanner MVP | modules/secret_firewall | 30s ago
2    | 2222         | idle   | Backlog docs        | docs/backlog            | 12s ago
3    | 3333         | stale  | Cost audit          | none                    | 18m ago

203.3 /switch-session

Must show:

source saved,

target checked,

collision status,

manual fallback.


203.4 /pane-recover

Must show:

auto possible yes/no,

why,

restore commands,

risks.


203.5 UX Rule

CPC commands should be operationally clear, not verbose.


---

204. SECURITY FOR CPC-OS FILES

204.1 Sensitive Runtime Files

CPC-OS files:

pane_registry.json

journal.jsonl

restart intents

switch intents

handoffs

wrapper logs

recovery plans

pane backlog

lock files


204.2 Security Classification

These files are internal operational state.

They should not contain raw secrets, but may contain:

local paths,

conversation IDs,

repo names,

task names,

process IDs.


204.3 Handling Rules

do not commit by default,

store under ~/.claude/pp_runtime/,

add local gitignore where needed,

sanitize before sharing,

no raw terminal output,

no env values,

no credentials,

no private transcript dumps.


204.4 Hard Rule candidata

HR-CPC-RUNTIME-SEC-001: CPC-OS runtime files must remain local, secret-free and excluded from normal commits. They may store routing metadata, not raw conversation transcripts or credentials.


---

205. OBSERVABILITY WITHOUT NOISE

205.1 Propósito

CPC-OS debe ser observable, pero no molesto.

205.2 Metrics

active_panes

stale_panes

crashed_panes

restart_success_count

restart_failure_count

switch_success_count

switch_failure_count

recovery_plan_count

duplicate_session_blocks

collision_blocks

registry_repair_count

average_resume_time

unsafe_auto_restore_blocks

manual_recovery_count


205.3 Alerts

Alert only for:

duplicate active conversation,

registry corruption,

secret in handoff,

restart loop risk,

Cursor detection failure during auto-route,

recovery failure,

global config collision,

deploy lock collision.


205.4 Silence Rule

No alert for normal heartbeat, normal pane registration, normal idle state.


---

206. CPC-OS COMPATIBILITY MATRIX

206.1 Purpose

CPC-OS must know what is supported on each environment.

206.2 Matrix Fields

COMPATIBILITY_MATRIX os: shell: cursor_version: claude_cli_version: wrapper_supported: cursor_detection_level: in_pane_restart_supported: session_switch_supported: manual_recovery_supported: auto_terminal_open_supported: known_limitations: last_verified:

206.3 Supported Modes

Windows + Cursor integrated PowerShell:

likely primary target.


Windows + Cursor integrated CMD:

support if wrapper works.


Windows + external CMD:

blocked for auto.


Windows Terminal:

blocked for auto.


VS Code:

separate compatibility, not assume Cursor.


Linux/macOS:

future compatibility, not first priority unless Owner uses.


206.4 Rule

Do not generalize Cursor behavior from external terminals.


---

207. CPC-OS DOCUMENTATION REQUIREMENTS

207.1 Required Docs

docs/cpc_os/README.md
docs/cpc_os/ARCHITECTURE.md
docs/cpc_os/STATE_MACHINES.md
docs/cpc_os/WRAPPER_CONTRACT.md
docs/cpc_os/RECOVERY.md
docs/cpc_os/TESTING.md
docs/cpc_os/TROUBLESHOOTING.md
docs/cpc_os/SECURITY.md

207.2 Docs Must Include

what CPC-OS does,

what it does not do,

Cursor-only requirement,

wrapper requirement,

restart flow,

switch flow,

recovery flow,

registry schema,

failure modes,

manual recovery,

no external CMD fallback,

secret safety,

tests.


207.3 Troubleshooting Must Include

wrapper missing,

resume command unknown,

registry corrupt,

stale intent,

duplicate session,

wrong cwd,

Cursor detection failed,

lock stuck,

recovery partial,

pane stale.



---

208. CPC-OS FINAL ACCEPTANCE CONTRACT

208.1 MVP Acceptance

CPC-OS MVP is accepted only when:

pane registry works atomically,

pane heartbeat works,

/panes shows accurate state,

wrapper launches Claude inside Cursor,

restart intent dry-run works,

stale intent blocked,

wrong pane intent blocked,

registry corruption recovers,

manual recovery plan works,

no external terminal fallback exists,

no raw secrets stored.


208.2 Restart Acceptance

/restart accepted only when:

same pane,

same Cursor integrated terminal,

same cwd,

same conversation/session ID,

handoff safe,

intent consumed once,

registry updated,

no duplicate session,

no infinite loop.


208.3 Switch Acceptance

/switch-session accepted only when:

source handoff safe,

target validated,

target not active elsewhere,

registry updated,

source marked paused,

target confirmed active.


208.4 Crash Recovery Acceptance

Crash recovery accepted only when:

exact previous pane count detected or honestly uncertain,

restore plan generated,

commands safe,

no external terminal,

idempotent,

no duplicate sessions,

locks/backlog preserved or safely marked unresolved.


208.5 Parallel Backlog Acceptance

Parallel backlog accepted only when:

each pane has distinct task,

locks do not overlap,

dependencies sequenced,

collisions blocked,

merge plan exists,

validation per pane defined.



---

209. CPC-OS FAILURE LANGUAGE

209.1 Propósito

El sistema debe ser honesto cuando no puede automatizar.

209.2 Correct Language

Use:

“Auto-restore is blocked because Cursor integrated terminal control was not verified.”

“Manual recovery is available.”

“The registry is recoverable from backup.”

“The target conversation is already active in Pane 2.”

“Restart handoff was written, but wrapper is missing.”

“Resume command syntax is not verified; refusing to guess.”


Avoid:

“I’ll just open CMD.”

“Should be fine.”

“Probably resumed.”

“It seems active.”

“I guessed the session ID.”

“I restored everything” without verification.


209.3 Rule

Unverified recovery must be described as unverified.


---

210. PART X CANONICAL PRINCIPLES

210.1 CPC-OS Is Transactional Infrastructure

Every restart, switch, recovery and backlog assignment is a transaction.

210.2 No Guessing Session Identity

Session/conversation IDs must be verified or blocked.

210.3 No External Terminal Fallback

Cursor-only is a hard boundary.

210.4 Wrapper Owns In-Pane Resume

Claude cannot type after exit. The parent wrapper must resume.

210.5 Registry Consistency Beats Convenience

If registry invariants fail, block routing.

210.6 Recovery Must Be Idempotent

No duplicates, no loops, no replay of stale intents.

210.7 Parallelism Requires Ownership

Each pane needs task ownership, file/scope locks and merge plan.

210.8 Manual Recovery Is a First-Class Path

Safe manual recovery is not failure. Unsafe automation is failure.

210.9 Runtime Files Are Local and Secret-Free

Registry, handoff and journal are operational metadata, not transcript storage.

210.10 Exact Continuity Requires Proof

Same pane, same Cursor terminal, same cwd, same conversation, same task, verified.

END OF PART X.