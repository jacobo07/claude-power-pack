# PP Dataset Part XI -- Crash-to-Exact-Terminal-Topology Guarantee for Cursor Pane Continuity OS

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 15429-16707 (1279 lines)
**Part number:** 11 (roman XI)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XI
# Crash-to-Exact-Terminal-Topology Guarantee for Cursor Pane Continuity OS

## 211. CRASH-TO-EXACT-TERMINAL-TOPOLOGY GUARANTEE

### 211.1 Propósito

Claude Power Pack debe reforzar CPC-OS con una garantía explícita:

Ante cualquier crash, cierre inesperado, apagón, out-of-memory, cierre de Cursor, cierre accidental del workspace o caída del sistema, al volver a abrir Cursor debe restaurarse la topología de terminales que existía antes del fallo.

Topología significa:

- número de terminales integradas abiertas,
- pane_id lógico de cada terminal,
- conversación/session activa en cada pane,
- cwd exacto,
- repo/workspace exacto,
- task/backlog asignado,
- locks activos,
- estado de ejecución,
- comando seguro de resume,
- handoff asociado.

La prioridad no es solo “reanudar Claude”.
La prioridad es reconstruir el tablero de trabajo paralelo exactamente como estaba.

### 211.2 Canonical Name

Canonical Name:
Crash-to-Exact-Terminal-Topology Guarantee

Abreviatura:
CETTG

También puede llamarse:
Cursor Terminal Topology Restore Guarantee

### 211.3 Invariante crítica

If Cursor had N integrated terminal panes before crash, CPC-OS must restore N logical execution lanes after recovery, each mapped to its last known conversation/task/cwd, unless technically impossible.

Si es imposible automatizarlo, debe producir un plan manual exacto con N comandos, uno por terminal, dentro de Cursor.

### 211.4 Hard Rule candidata

HR-CPC-TOPOLOGY-001:
After crash recovery, CPC-OS must restore the last known terminal topology: same number of logical panes, same conversation mapping, same cwd, same backlog assignments and same locks. If automatic restore is not verified, output an exact manual restore plan instead of silently degrading.

---

## 212. TERMINAL TOPOLOGY MANIFEST

### 212.1 Propósito

El pane_registry.json no debe limitarse a “sesiones activas”.
Debe guardar una fotografía explícita de la topología de terminales.

Ubicación sugerida:

```text
~/.claude/pp_runtime/cursor_panes/terminal_topology_manifest.json

212.2 Manifest Schema

TERMINAL_TOPOLOGY_MANIFEST schema_version: workspace_id: workspace_path: cursor_instance_id: last_stable_snapshot_at: terminal_count: logical_panes:

pane_index: pane_id: pane_uuid: repo_path: cwd: terminal_kind: shell_kind: wrapper_active: cursor_integrated_verified: conversation_id: session_id: id_type: task_id: backlog_item_id: lifecycle_state: locks: resume_command_safe: handoff_path: last_heartbeat: restore_priority: restore_required: restore_status: topology_hash: last_valid_backup: journal_pointer:


212.3 Terminal Count Rule

El campo terminal_count debe representar el número de panes lógicos que deben recuperarse.

No debe derivarse solo de procesos vivos, porque tras crash no habrá procesos vivos.

Debe derivarse de:

última snapshot estable,

pane registry,

heartbeat history,

wrapper state,

handoff state,

journal.


212.4 Snapshot Rule

Cada vez que cambie la topología, guardar snapshot:

pane opened,

pane closed intentionally,

pane switched session,

pane restarted,

pane assigned task,

pane released task,

pane became paused,

pane became closed,

pane became stale,

pane recovered.


No esperar al crash. El estado debe estar guardado antes de que ocurra.


---

213. LAST KNOWN GOOD TOPOLOGY

213.1 Propósito

No basta con tener “estado actual”. Debe existir last_known_good_topology.

Ubicación:

~/.claude/pp_runtime/cursor_panes/last_known_good_topology.json

213.2 Definición

Una topología es “known good” si:

registry válido,

checksum válido,

no duplicate active conversation,

no corrupt JSON,

no secret findings,

pane count coherente,

locks válidos,

handoffs existentes,

resume commands seguros,

cwd existentes o marcados como missing,

snapshot escrita atómicamente.


213.3 Promotion Rule

Solo promover snapshot a last_known_good si pasa validación completa.

Nunca promover:

snapshot durante registry corruption,

snapshot con duplicate sessions,

snapshot con handoff inseguro,

snapshot con secrets,

snapshot parcial de recovery fallido,

snapshot con terminal external_blocked.


213.4 Hard Rule candidata

HR-CPC-LKG-001: Only validated, secret-safe, duplicate-free, checksum-valid terminal topology snapshots may become last_known_good_topology.


---

214. THREE-LAYER CRASH RECOVERY MODEL

214.1 Propósito

Diferenciar tipos de crash y su respuesta.

214.2 Layer 1 -- Claude Process Crash

Cursor sigue abierto, terminal sigue viva, Claude murió.

Recovery:

wrapper detecta exit inesperado,

consulta intent/registry,

reanuda si seguro,

mantiene mismo pane físico.


214.3 Layer 2 -- Cursor Window / Workspace Crash

Cursor se cierra o se crashea, pero sistema sigue.

Recovery:

al abrir workspace,

bootstrap lee last_known_good_topology,

reconstruye panes lógicos,

genera o ejecuta restore plan.


214.4 Layer 3 -- Machine Crash / Power Loss

Ordenador se apaga, se va la luz, OOM severo.

Recovery:

al volver a abrir Cursor,

no confiar en procesos previos,

usar únicamente last_known_good_topology + journal,

todos los panes previos se consideran recovery_pending,

reabrir/restaurar N terminales si está soportado,

si no, manual plan con N terminales.


214.5 Rule

Machine crash recovery must never rely on live process IDs from before crash. PIDs are invalid after reboot.


---

215. RESTORE EXACT PANE COUNT FIRST

215.1 Principio

La recuperación debe restaurar primero la topología, luego las conversaciones.

Orden correcto:

1. cargar last_known_good_topology,


2. determinar N panes que existían,


3. reconstruir N logical lanes,


4. verificar workspace,


5. abrir/preparar N terminales integradas si auto soportado,


6. asignar cada pane lógico a una terminal,


7. ejecutar resume correspondiente,


8. verificar conversación/cwd,


9. restaurar backlog/locks,


10. marcar recovery complete.



Orden incorrecto:

reanudar una conversación cualquiera,

abrir una terminal suelta,

ignorar pane count,

restaurar solo la última sesión,

perder panes secundarios.


215.2 Hard Rule candidata

HR-CPC-RESTORE-ORDER-001: Crash recovery must restore terminal topology before resuming conversations. Do not resume isolated sessions until the required pane count and pane mapping are known.


---

216. TOPOLOGY RESTORE PLAN

216.1 Schema

TOPOLOGY_RESTORE_PLAN plan_id: workspace_id: workspace_path: based_on_snapshot: based_on_snapshot_hash: created_at: expected_terminal_count: auto_restore_supported: manual_restore_required: restore_actions:

restore_action_id: pane_index: pane_id: repo_path: cwd: conversation_id: session_id: id_type: task_id: backlog_item_id: locks_to_restore: handoff_path: resume_command_safe: terminal_creation_required: cursor_integrated_required: status: idempotency_key: restore_order: collision_checks: missing_paths: unsafe_items: manual_commands: verification_steps: expires_at:


216.2 Restore Action States

PENDING
TERMINAL_NEEDED
TERMINAL_READY
RESUME_PENDING
RESUME_RUNNING
VERIFYING
RESTORED
SKIPPED_INTENTIONALLY_CLOSED
BLOCKED
MANUAL_REQUIRED
FAILED_SAFE

216.3 Idempotency

Cada restore action debe tener idempotency key.

Si se ejecuta dos veces:

no duplica terminal,

no duplica sesión,

no duplica task,

no duplica lock.



---

217. TERMINAL CREATION ADAPTER

217.1 Propósito

Para restaurar N terminales, CPC-OS necesita un adapter separado.

Canonical Name: Cursor Terminal Creation Adapter

217.2 Responsabilidad

verificar si Cursor permite crear terminal integrada desde workspace,

abrir nueva terminal integrada si soportado,

establecer cwd correcto,

lanzar claude-pp wrapper,

asociar pane_id lógico,

bloquear si solo puede abrir terminal externa.


217.3 Adapter Modes

AUTO_SUPPORTED: Puede abrir terminal integrada de Cursor de forma verificable.

TASK_SUPPORTED: Puede usar tareas del workspace para crear terminales.

MANUAL_ONLY: No puede abrir terminales automáticamente, pero puede generar comandos.

UNSUPPORTED: No se puede verificar Cursor terminal creation.

217.4 Strict Rule

No terminal creation adapter may open normal CMD, external PowerShell or Windows Terminal as fallback.

217.5 Hard Rule candidata

HR-CPC-TERMINAL-CREATE-001: Terminal restoration must target Cursor integrated terminals only. If Cursor terminal creation cannot be verified, generate manual Cursor restore instructions instead of opening external terminals.


---

218. MANUAL EXACT TOPOLOGY RESTORE

218.1 Propósito

Si auto restore no está verificado, el sistema debe seguir cumpliendo la garantía de forma manual.

218.2 Manual Plan Requirements

Debe decir:

“Antes del crash había N terminales.”

“Abre N terminales integradas en Cursor.”

“En terminal 1 pega este comando.”

“En terminal 2 pega este comando.”

“En terminal 3 pega este comando.”

etc.


218.3 Manual Restore Output

MANUAL_EXACT_TOPOLOGY_RESTORE status: reason_auto_restore_blocked: expected_terminal_count: instructions:

pane_index: open_in_cursor_terminal: true cwd: command: conversation_id_short: task: locks: validation_after_resume: warnings: collision_notes: what_not_to_do:

do_not_open_external_cmd

do_not_resume_same_conversation_twice

do_not_change_cwd

do_not_ignore_pane_order


218.4 Manual Command Example Format

# Cursor Terminal Pane 1
cd "<repo_path>"
claude-pp --resume <conversation_id>

El comando real debe usar el resume syntax validado del entorno.


---

219. WORKSPACE BOOTSTRAP RECOVERY

219.1 Propósito

Al abrir Cursor en un workspace, CPC-OS debe detectar si hay recuperación pendiente.

219.2 Bootstrap Flow

1. Cursor workspace opens.


2. Owner opens first integrated terminal or configured startup task runs.


3. claude-pp or bootstrap hook starts.


4. CPC-OS checks last_known_good_topology.


5. If previous shutdown was clean, do nothing.


6. If crash suspected, show recovery prompt.


7. If auto restore supported, offer/execute restore.


8. If manual only, print exact plan.



219.3 Clean Shutdown Marker

Ubicación:

~/.claude/pp_runtime/cursor_panes/clean_shutdown_markers/<workspace_id>.json

If clean shutdown marker missing or stale:

assume crash_possible,

compare topology,

propose recovery.


219.4 Shutdown States

clean_shutdown

cursor_closed_cleanly

workspace_closed_cleanly

claude_exited_cleanly

crash_suspected

machine_reboot_suspected

unknown_shutdown


219.5 Hard Rule candidata

HR-CPC-BOOTSTRAP-001: On workspace bootstrap, CPC-OS must check for crash-suspected topology before starting new unrelated work.


---

220. DO NOT LOSE SECONDARY PANES

220.1 Problema

Muchos sistemas de resume recuperan solo la última sesión.

Eso es insuficiente.

Si había 4 panes, recuperar solo 1 es fallo parcial.

220.2 Rule

Recovery must account for every pane in last_known_good_topology.

Cada pane debe acabar en uno de estos estados:

restored,

intentionally_skipped,

manually_required,

blocked_with_reason,

orphaned_with_recovery_command,

closed_intentionally_before_crash.


No puede desaparecer sin explicación.

220.3 Recovery Completion Report

RECOVERY_COMPLETION_REPORT expected_panes: restored_panes: manual_required_panes: blocked_panes: skipped_panes: missing_panes: topology_restored: true/false partial_recovery: true/false next_actions:

220.4 Hard Rule candidata

HR-CPC-NO-PANE-LOSS-001: Crash recovery is not complete until every pane from last_known_good_topology is restored, intentionally skipped, manually assigned, or blocked with explicit reason.


---

221. CRASH DETECTION SIGNALS

221.1 Propósito

Detectar crash sin depender de una sola señal.

221.2 Signals

no clean shutdown marker,

stale heartbeat,

wrapper exit not recorded,

Cursor workspace reopened,

registry says active but process missing,

restart/switch transaction incomplete,

OS boot time newer than heartbeat,

pane marker exists but no active process,

journal has unclosed transaction,

last topology not closed.


221.3 Crash Confidence

CC0: No crash.

CC1: Possible stale state.

CC2: Likely Cursor close/crash.

CC3: Likely machine reboot/power loss.

CC4: Confirmed inconsistent state requiring recovery.

221.4 Recovery Trigger

CC2+ should trigger topology recovery check.

CC3+ should not trust old PIDs.

CC4 should block new work until recovery decision.


---

222. TERMINAL TOPOLOGY JOURNAL

222.1 Propósito

Además del registry, guardar eventos de topología.

Ubicación:

~/.claude/pp_runtime/cursor_panes/topology_journal.jsonl

222.2 Event Types

pane_created

pane_registered

pane_closed_intentionally

pane_restarted

pane_switched

pane_task_assigned

pane_task_completed

pane_task_failed

pane_stale_detected

topology_snapshot_promoted

recovery_plan_created

pane_restored

recovery_completed

recovery_partial

recovery_blocked


222.3 Journal Event Schema

TOPOLOGY_JOURNAL_EVENT event_id: timestamp: workspace_id: pane_id: pane_index: conversation_id: task_id: event_type: topology_hash_before: topology_hash_after: safe_summary: secret_free: true

222.4 Use

Si manifest se corrompe:

recuperar desde last_known_good,

aplicar journal hasta último evento válido,

reconstruir topology.



---

223. PANE RESTORE VERIFICATION

223.1 Propósito

No basta con abrir terminal y ejecutar resume.

Hay que verificar.

223.2 Verification Checklist

Para cada pane restaurado:

terminal is Cursor integrated,

cwd matches,

repo exists,

wrapper active,

conversation/session ID matches,

no duplicate active conversation,

backlog item restored,

locks restored or marked unresolved,

heartbeat updated,

handoff acknowledged,

status marked RESTORED.


223.3 Verification Failure

If verification fails:

mark pane restore failed_safe,

do not count as restored,

do not delete recovery action,

provide manual command,

block topology_restored=true.


223.4 Hard Rule candidata

HR-CPC-RESTORE-VERIFY-001: A pane is not restored until Cursor terminal, cwd, conversation ID, registry state and heartbeat are verified.


---

224. RESTORE ORDERING

224.1 Problema

Algunas tareas dependen de otras.

No siempre hay que restaurar panes en orden visual.

224.2 Ordering Priority

1. Pane with deploy/global lock.


2. Pane with secret/security incident.


3. Pane with incomplete restart/switch transaction.


4. Pane with active file locks.


5. Pane with highest priority backlog item.


6. Idle panes.


7. Observer panes.



224.3 Dependency Ordering

Si Pane 3 dependía de Pane 1:

restaurar Pane 1 primero,

Pane 3 queda pending hasta que Pane 1 confirme.


224.4 Restore Order Report

RESTORE_ORDER_REPORT restore_order: dependencies: reasoning: blocked_until: safe_parallel_restores:


---

225. CLEAN SHUTDOWN VS CRASH

225.1 Propósito

No toda ausencia de terminal es crash.

El Owner puede cerrar terminales intencionalmente.

225.2 Clean Close Flow

Si Owner cierra un pane intencionalmente:

SessionEnd/Wrapper debe marcar pane closed,

liberar locks seguros,

actualizar topology,

reducir terminal_count,

promover last_known_good.


225.3 Crash Difference

Si pane desaparece sin clean close:

no reducir terminal_count,

marcar recovery_pending,

conservar task/locks,

no reasignar automáticamente hasta recovery decision.


225.4 Hard Rule candidata

HR-CPC-CLOSE-001: Only intentional clean pane close may reduce expected terminal_count. Crash/stale disappearance must preserve pane in recovery topology.


---

226. RESTORE UX CONTRACT

226.1 Auto Restore Message

If auto restore possible:

Crash recovery detected.
Previous Cursor topology: 3 terminal panes.
Restoring:
- Pane 1 → conversation 1111 → task A
- Pane 2 → conversation 2222 → task B
- Pane 3 → conversation 3333 → task C
No external CMD will be opened.

226.2 Manual Restore Message

If manual:

Crash recovery detected.
Previous Cursor topology: 3 terminal panes.

Auto-restore is blocked because Cursor terminal creation is not verified.

Open 3 integrated terminals in Cursor and run:

Pane 1:
cd "..."
claude-pp --resume 1111

Pane 2:
cd "..."
claude-pp --resume 2222

Pane 3:
cd "..."
claude-pp --resume 3333

226.3 Partial Recovery Message

Recovered 2/3 panes.
Pane 3 requires manual recovery because target conversation is already claimed / cwd missing / resume command failed.


---

227. “ALWAYS RETURN TO OPEN TERMINALS” INTERPRETATION

227.1 Clarificación técnica

La intención del Owner es:

“Siempre que haya crash, quiero volver a tener las terminales que tenía abiertas.”

Implementación correcta:

always preserve last known terminal topology,

always detect crash-suspected state,

always attempt exact restore if verified,

always generate exact manual plan if auto not verified,

never silently drop panes,

never restore only last session,

never open external CMD.


227.2 Absolute vs Technical Guarantee

No se debe prometer lo técnicamente imposible si Cursor no permite abrir terminales automáticamente.

Pero sí debe garantizarse:

1. El sistema siempre recuerda cuántas terminales había.


2. El sistema siempre recuerda qué conversación iba en cada una.


3. El sistema siempre intenta restaurarlas en Cursor.


4. Si no puede auto-restaurar, siempre da instrucciones exactas para recrearlas.


5. Nunca pierde panes sin explicación.


6. Nunca sustituye Cursor por CMD normal.



227.3 Hard Rule candidata

HR-CPC-ALWAYS-RESTORE-001: After any crash-suspected startup, CPC-OS must not start unrelated work until it has checked last_known_good_topology and either restored, manually planned, intentionally skipped, or explicitly blocked every previously open pane.


---

228. TESTS FOR EXACT TERMINAL TOPOLOGY RECOVERY

228.1 Test: Three Pane Crash

Setup:

Pane 1 conversation 1111.

Pane 2 conversation 2222.

Pane 3 conversation 3333.

Simulate crash without clean shutdown.


Expected:

recovery detects 3 expected panes,

restore plan has 3 actions,

no pane missing,

commands map correctly.


228.2 Test: Clean Close One Pane

Setup:

3 panes.

Owner clean closes Pane 3.

Crash later.


Expected:

terminal_count expected = 2,

Pane 3 not restored,

close event recorded.


228.3 Test: Stale Disappearance Not Clean Close

Setup:

3 panes.

Pane 3 disappears without clean close.


Expected:

terminal_count remains 3,

Pane 3 recovery_pending.


228.4 Test: Auto Restore Unsupported

Expected:

no external CMD,

exact manual plan for all panes.


228.5 Test: Partial Restore

Setup:

3 panes.

Pane 2 conversation already claimed.


Expected:

Pane 1 restored,

Pane 3 restored,

Pane 2 blocked with explicit reason,

topology_restored=false,

partial_recovery=true.


228.6 Test: Registry Corrupt, LKG Valid

Expected:

load last_known_good_topology,

recover all panes from LKG,

journal replay if safe.


228.7 Test: Machine Reboot

Setup:

old PIDs invalid.


Expected:

ignore old PIDs,

use pane_uuid and conversation IDs,

restore plan safe.


228.8 Test: Wrong CWD

Expected:

pane not marked restored,

manual correction shown.


228.9 Test: No Pane Loss

Expected:

every pane accounted for in completion report.


228.10 Test: Recovery Before New Work

Expected:

if crash_suspected CC2+, new unrelated Claude task blocked until recovery decision.



---

229. PHASE XI IMPLEMENTATION ORDER

229.1 Phase A -- Topology Manifest

Implement:

terminal_topology_manifest.json,

last_known_good_topology.json,

topology journal,

snapshot promotion.


229.2 Phase B -- Clean Close vs Crash Detection

Implement:

clean shutdown markers,

crash confidence,

stale disappearance logic,

terminal_count preservation.


229.3 Phase C -- Restore Plan Generator

Implement:

exact N-pane restore plan,

manual commands,

no pane loss report.


229.4 Phase D -- Bootstrap Recovery Check

Implement:

workspace bootstrap recovery detection,

block unrelated work until recovery decision.


229.5 Phase E -- Auto Terminal Adapter

Only if technically verified:

Cursor integrated terminal creation,

no external fallback,

verification.


229.6 Phase F -- Full Chaos Tests

Implement:

3-pane crash,

clean close,

stale pane,

partial recovery,

registry corruption,

reboot.



---

230. CLAUDE CODE PROMPT FOR PART XI

Use this prompt to implement this safely.

PROMPT:

Act as the implementation engineer for Claude Power Pack CPC-OS.

MISSION: Reinforce crash recovery so that after any crash, Cursor Pane Continuity OS restores the exact last known terminal topology: same number of Cursor integrated terminal panes, same pane-to-conversation mapping, same cwd, same backlog assignments and same locks.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing CPC-OS/session/Lazarus/restart/terminal-slot components if present. Verify before modifying.

NON-NEGOTIABLES:

Cursor integrated terminals only.

Never open normal CMD, external PowerShell or Windows Terminal.

Never silently restore only the last session if multiple panes existed.

Never reduce terminal_count unless pane was closed cleanly.

Never trust old PIDs after crash/reboot.

Never mark a pane restored without verifying Cursor terminal, cwd, conversation ID and heartbeat.

Never store raw secrets in topology manifest, handoff, journal or recovery plan.

Never start unrelated work after crash-suspected startup until recovery is resolved or explicitly skipped.

If auto terminal creation is not verified, produce exact manual restore plan for every pane.


IMPLEMENTATION PHASE: Start with Topology Manifest + Last Known Good Topology + Restore Plan Generator. Do not implement auto terminal creation until feasibility is verified.

REQUIRED FEATURES:

1. terminal_topology_manifest.json schema.


2. last_known_good_topology.json promotion rule.


3. topology_journal.jsonl.


4. clean close vs crash distinction.


5. crash confidence scoring.


6. exact N-pane restore plan.


7. manual restore commands for each pane.


8. no-pane-loss completion report.


9. tests for 3-pane crash and clean-close reduction.


10. secret-safe storage.



ACCEPTANCE:

Simulated 3-pane crash produces 3-pane restore plan.

Clean close of one pane reduces expected count.

Unclean disappearance preserves pane for recovery.

Auto unsupported path produces manual Cursor restore plan.

No external terminal command is generated.

Every pane is accounted for.

No raw secrets stored.

Tests pass.


FINAL RECEIPT: Return files changed, tests added, tests run, topology recovery status, Cursor-only enforcement status, secret safety status, remaining risks and next implementation phase.


---

231. PART XI CANONICAL PRINCIPLES

231.1 Crash Recovery Means Topology Recovery

Restoring one Claude session is not enough. Restore the whole terminal topology.

231.2 Pane Count Is State

The number of open Cursor terminals is part of recoverable state.

231.3 Clean Close Reduces Count, Crash Does Not

Only intentional close can remove a pane from expected recovery.

231.4 Last Known Good Is Sacred

Recover from validated topology, not corrupted current state.

231.5 Every Pane Must Be Accounted For

Restored, skipped, manual, blocked or orphaned. Never silently missing.

231.6 Auto If Verified, Manual If Not

Manual exact recovery is better than unsafe external automation.

231.7 No External CMD Ever

Cursor terminal topology must restore inside Cursor or not auto-restore.

231.8 Verify Before Marking Restored

A terminal is not restored until cwd, conversation, heartbeat and registry match.

231.9 New Work Waits For Recovery

After crash-suspected startup, recover topology before starting unrelated work.

231.10 The Goal Is Returning to the Board

After crash, the Owner should return to the same operational board: same panes, same conversations, same tasks, same direction.

END OF PART XI.

Sí. Esta Parte XII debe tratar la RAM como infraestructura crítica de continuidad, igual que el registry de panes. Si Cursor/Claude/Node/Python se quedan sin memoria, no basta con “volver a abrir”: el sistema debe prevenir, aliviar, hacer checkpoint, degradar con seguridad y sobrevivir al OOM sin perder terminales, conversaciones, locks ni backlog. Lo añado sobre el baseline del Claude Power Pack ya cargado. 

