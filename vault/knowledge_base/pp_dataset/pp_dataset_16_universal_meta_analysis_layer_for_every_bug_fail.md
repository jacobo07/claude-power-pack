# PP Dataset Part XVI -- Universal Meta-Analysis Layer for Every Bug, Failure, Error, Drift, Regression and Execution Mismatch Across All Code-Producing Projects

**Source:** PP_DATASET_20260531T122242Z (2).md @ 330e261
**Source sha256:** 40ef5bde1bea2031
**Source line range:** 21719-23108 (1390 lines)
**Part number:** 16 (roman XVI)
**Ingested by:** tools/dataset_v2_ingest.py (Sprint 1 / M2 completeness recovery -- Parts XI-XXIII were absent from v1).

---

# CLAUDE POWER PACK -- EXTENSION DATASET PART XVI
# Universal Meta-Analysis Layer for Every Bug, Failure, Error, Drift, Regression and Execution Mismatch Across All Code-Producing Projects

## 325. UNIVERSAL META-ANALYSIS LAYER

### 325.1 Propósito

Claude Power Pack debe integrar una capa universal de meta-análisis para absolutamente cualquier bug, fallo, error, drift, regresión, mismatch, output débil, desviación de scope, error de ejecución, error de interpretación, problema de realidad productiva o incumplimiento de contrato que aparezca en cualquier proyecto del stack del Owner.

Esto aplica a:
- Claude Power Pack.
- KobiiCraft.
- MundiCraft.
- KobiMapEngine.
- KobiiSports.
- InfinityOps.
- CommonWealth Ops / TUAX.
- Pipelines de contenido.
- Automatizaciones n8n.
- Plugins.
- Frontends.
- Backends.
- CLIs.
- Agentes.
- Workflows.
- Cualquier repo que produzca cualquier ápice de código.

El meta-análisis no debe depender del dominio.
Debe ser project-agnostic, stack-wide y reusable.

### 325.2 Principio central

Every failure must improve the system.

Un bug no se considera completamente tratado hasta que el sistema haya respondido:

1. Qué ocurrió.
2. Por qué ocurrió.
3. Qué patrón revela.
4. Qué parte del proceso permitió que ocurriera.
5. Qué prevención debe añadirse.
6. Si debe convertirse en Hard Rule, Process Rule o Trap.
7. Si debe modificar el estándar de completitud futuro.
8. Si debe generar backlog.
9. Si debe generar test.
10. Si debe actualizar UKDL.
11. Si debe afectar a todos los proyectos o solo al repo actual.

### 325.3 Nombre canónico

Canonical Name:
Universal Meta-Analysis Layer

Abreviatura:
UMAL

Función:
Capturar, analizar y convertir cada bug/fallo/error/drift en mejora sistémica reutilizable.

---

## 326. BOILERPLATE AS ROUTER, NOT LIBRARY

### 326.1 Problema

El boilerplate del Owner ya es largo. Añadir más texto lo hace menos efectivo.

Claude Code puede empezar a ignorar partes por saturación de contexto.

La solución correcta:
El boilerplate debe ser router, no biblioteca.

La lógica completa debe vivir en archivos canónicos que Claude Code lee al inicio de sesión.

### 326.2 Regla

El prompt del Owner no debe contener toda la doctrina.
Debe apuntar a la doctrina.

El boilerplate solo debe activar:
- UKDL,
- Hard Rules,
- Process Rules,
- Traps,
- Production Reality Gate,
- Contract of Reality,
- meta-análisis,
- standard-of-completeness update,
- plan/execution mode routing.

### 326.3 Boilerplate compacto recomendado

Texto router:

```text
Mándame el siguiente prompt para plan mode con máximo ROI y todos los micro-commits que hagan falta antes de declarar como terminado. Que lo que añadamos se vuelva estándar de completitud para futuras features. Plan inline en chat para aprobar con un clic, no plan-file standalone, aunque también se respalda en plan-file. Distingue si el ROI exige plan mode, execution mode o ultra-plan mode. Itera con C:\Users\User\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt. Aplica UKDL tres niveles: Hard Rules, Process Rules y Traps. Production Reality Gate obligatorio en cada done-gate. Meta-análisis de patrones al cierre de cada bug, fallo, error, drift, regresión o sesión. Todo según ~/.claude/CLAUDE.md y knowledge-vault/UKDL/universal-knowledge.md. Contrato de Realidad activo: cero botones vacíos, placeholders, 401s, desconexiones frontend-CLI, claims sin evidencia o done falso. Kernel vMAX-NULL-ERROR. AGENT TEAMS Mode, autónomo, desatendido. Sin código en el prompt: Claude Code decide implementación.

326.4 Hard Rule candidata

HR-BOILERPLATE-ROUTER-001: Owner boilerplates must act as routers to canonical doctrine files, not as long duplicated libraries. If doctrine grows, move it to canonical files and keep prompt compact.


---

327. THREE-LEVEL UKDL META-ANALYSIS MODEL

327.1 Propósito

Cada error debe clasificarse en tres niveles de UKDL:

1. Hard Rules.


2. Process Rules.


3. Traps.



327.2 Level 1 -- Hard Rules

Hard Rules son bloqueadores.

Se usan cuando repetir el fallo sería grave.

Ejemplos:

secreto filtrado,

deploy sin verificación,

done falso,

registry corrupto,

reanudar conversación equivocada,

modificar settings global sin backup,

Production Reality Gate fallido,

401 ignorado,

botón vacío,

frontend desconectado de CLI,

placeholder enviado como feature real.


Una Hard Rule debe tener:

trigger observable,

stop condition,

required action,

evidence requirement,

false-positive guard,

scope,

test.


327.3 Level 2 -- Process Rules

Process Rules son mejoras del flujo.

No siempre bloquean, pero cambian cómo se trabaja.

Ejemplos:

antes de full test, mirar resource pressure,

antes de plan, decidir plan/execution/ultra-plan,

después de bug, generar meta-analysis record,

después de drift, actualizar standard of completeness,

tras output débil, mejorar Output Contract,

si una feature añade nuevo estándar, incluirlo en futuras features.


Una Process Rule debe tener:

cuándo aplica,

cómo cambia el proceso,

qué output añade,

qué checklist modifica,

si aplica local o globalmente.


327.4 Level 3 -- Traps

Traps son trampas recurrentes.

No siempre bloquean ni cambian proceso, pero alertan.

Ejemplos:

Claude Code tiende a dar done prematuro,

tendencia a crear plan-file en vez de plan inline,

confundir plan mode con execution mode,

asumir que un botón funciona porque existe visualmente,

validar frontend sin probar CLI/backend,

creer que compilar equivale a funcionar,

repetir full repo scans,

guardar demasiado texto en boilerplate,

convertir meta-análisis en ruido.


Una Trap debe tener:

pattern,

why dangerous,

early signal,

prevention nudge,

escalation threshold.


327.5 Hard Rule candidata

HR-UKDL-3LEVEL-001: Every significant bug, failure, error, drift or regression must be classified into Hard Rule, Process Rule, Trap, or explicitly rejected with reason.


---

328. UNIVERSAL FAILURE EVENT

328.1 Propósito

Crear un evento universal para cualquier fallo.

Canonical Name: Universal Failure Event

Abreviatura: UFE

328.2 UFE Schema

UNIVERSAL_FAILURE_EVENT event_id: timestamp: project: repo_path: source: source_type: failure_type: severity: detected_by: task_id: pane_id: conversation_id: user_intent: expected_behavior: actual_behavior: production_reality_impact: contract_of_reality_violation: root_cause_hypothesis: evidence: affected_files: affected_systems: cascade_risk: secret_risk: cost_risk: resource_risk: one_shot_risk: drift_type: was_preventable: prevented_by_existing_rule: rule_missing: meta_analysis_required: status:

328.3 Failure Types

bug

runtime_error

compile_error

test_failure

lint_failure

type_error

integration_failure

deploy_failure

frontend_backend_disconnect

CLI_frontend_disconnect

401_auth_failure

empty_button

placeholder_behavior

fake_done

missing_validation

scope_drift

naming_drift

context_drift

prompt_drift

output_drift

cost_drift

resource_drift

secret_risk

recovery_failure

pane_collision

registry_failure

crash

OOM

stale_context

wrong_assumption

weak_backlog

weak_plan

weak_handoff

incomplete_feature

standard_violation


328.4 Rule

Every failure enters the same funnel. No project gets custom excuses.


---

329. UNIVERSAL META-ANALYSIS RECORD

329.1 Propósito

Después de cada UFE relevante, generar meta-análisis.

329.2 Schema

UNIVERSAL_META_ANALYSIS_RECORD analysis_id: linked_failure_event: project: repo_path: failure_summary: surface_symptom: root_cause: deeper_pattern: process_gap: standard_gap: validation_gap: reality_gap: context_gap: tooling_gap: human_instruction_gap: agent_behavior_gap: cascade_path: why_existing_rules_failed: new_rule_needed: rule_level: hard_rule_candidate: process_rule_candidate: trap_candidate: test_candidate: backlog_candidate: standard_update_candidate: applies_to: local_project: all_code_projects: specific_stack_layer: future_features: evidence: confidence: false_positive_risk: owner_review_required: status:

329.3 Meta-analysis Questions

Every meta-analysis must answer:

1. Was this a one-off or a pattern?


2. Did the agent misunderstand the task?


3. Did the process allow a false done?


4. Did validation check the real thing?


5. Did the feature work in production reality?


6. Did a placeholder pass as implementation?


7. Did a UI element exist but not function?


8. Did frontend and CLI/backend disconnect?


9. Did auth return 401 and get ignored?


10. Did a plan become execution incorrectly?


11. Did execution happen when ultra-plan was needed?


12. Did context become too bloated?


13. Did boilerplate become too long?


14. Did the agent ignore canonical doctrine?


15. Should future features inherit a new done-gate?




---

330. PRODUCTION REALITY GATE

330.1 Propósito

Cada done-gate debe comprobar realidad productiva, no solo existencia de código.

El Owner lo ha definido claramente: Contrato de Realidad activo:

cero botones vacíos,

cero placeholders,

cero 401s ignorados,

cero desconexiones frontend-CLI,

cero claims sin evidencia,

cero done falso.


330.2 Production Reality Gate Checks

Para cualquier feature:

Does it compile?

Does it run?

Is it connected to real backend/CLI/workflow?

Are buttons/actions wired?

Are placeholders removed or explicitly marked?

Are auth paths valid?

Are 401/403 handled?

Does UI action trigger actual function?

Does CLI command execute real path?

Does output match user intent?

Is there evidence?

Is there no fake success state?

Are errors visible and handled?

Does done mean usable?


330.3 PRG Result

PRODUCTION_REALITY_GATE feature: status: pass | fail | partial | not_applicable checks: compile: runtime: integration: auth: UI_actions: CLI_actions: placeholders: evidence: error_handling: user_value: violations: done_allowed: next_required_action:

330.4 Hard Rule candidata

HR-PRG-001: No feature may be declared done until Production Reality Gate passes or the output explicitly states partial completion with remaining reality gaps.


---

331. STANDARD OF COMPLETENESS UPDATER

331.1 Propósito

El Owner quiere que “lo que añadamos se vuelva estándar de completitud para futuras features”.

Eso debe formalizarse.

Cada vez que una feature añade una nueva exigencia de calidad, esa exigencia debe evaluarse para convertirse en estándar futuro.

331.2 Standard Update Candidate

STANDARD_UPDATE_CANDIDATE candidate_id: source_task: source_failure: new_standard: why_it_matters: applies_to: future_features: all_projects: specific_project: specific_layer: done_gate_change: test_change: prompt_change: hard_rule_change: process_rule_change: owner_review_required: status:

331.3 Examples

If Secret Firewall is added: Future features must declare secret handling.

If CPC-OS adds topology recovery: Future restart/recovery features must account for terminal topology.

If RAM Watchdog is added: Future heavy tasks must check memory pressure.

If Production Reality Gate catches empty button: Future UI features must prove button actions are wired.

If CLI disconnect found: Future UI/CLI integrations must include end-to-end test.

331.4 Hard Rule candidata

HR-STANDARD-001: When a task introduces a new quality gate or prevention mechanism, PP must evaluate whether it becomes a future Standard of Completeness.


---

332. PLAN MODE / EXECUTION MODE / ULTRA-PLAN MODE ROUTER

332.1 Propósito

El boilerplate debe exigir que Claude Code distinga el modo de mayor ROI.

No siempre plan mode. No siempre execution mode. No siempre ultra-plan.

332.2 Modes

PLAN MODE: Usar cuando la tarea requiere aprobación, arquitectura o riesgo medio.

EXECUTION MODE: Usar cuando el siguiente paso es obvio, bajo riesgo y validable.

ULTRA-PLAN MODE: Usar cuando hay riesgo alto, múltiples sistemas, posible cascade, secrets, recovery, deploy, registry, production, auth, recursos o unknowns críticos.

332.3 Mode Decision

MODE_DECISION requested_by_owner: recommended_mode: why: risk: unknowns: execution_allowed: approval_required: plan_inline_required: plan_file_backup_required: micro_commits_required: next_step:

332.4 Hard Rule candidata

HR-MODE-ROUTER-001: Before responding to complex implementation requests, PP must decide whether maximum ROI requires plan mode, execution mode or ultra-plan mode.


---

333. INLINE PLAN FIRST, PLAN-FILE BACKUP SECOND

333.1 Propósito

El Owner quiere plan inline en chat para aprobar con un clic, no plan-file standalone, aunque respaldado en plan-file.

333.2 Rule

For plan mode:

primary plan must be inline in chat,

plan-file is backup,

no hiding important decisions only in file,

no forcing Owner to open separate file to approve.


333.3 Plan Contract

INLINE_PLAN_CONTRACT goal: mode: risk: phases: micro_commits: validation: done_gates: production_reality_gate: rollback: owner_approval_needed: plan_file_backup_path:

333.4 Hard Rule candidata

HR-INLINE-PLAN-001: Plan mode must produce an inline approval-ready plan in chat. Plan-file may back it up but must not replace it.


---

334. MICRO-COMMIT COMPLETION STANDARD

334.1 Propósito

El Owner quiere “todos los micro commits que hagan falta antes de declarar terminado”.

334.2 Micro-Commit Rule

Large changes must be split into micro-commits where each commit has:

single purpose,

passing tests or explicit reason,

secret scan,

rollback clarity,

no unrelated changes,

evidence.


334.3 Micro-Commit Plan

MICRO_COMMIT_PLAN feature: commits:

commit_id_planned: purpose: files: validation: risk: rollback: done_gate: final_integration_gate:


334.4 Hard Rule candidata

HR-MICROCOMMIT-001: Complex feature work must be split into micro-commits with validation and rollback boundaries before declaring done.


---

335. SESSION-CLOSE META-ANALYSIS GATE

335.1 Propósito

El meta-análisis debe ejecutarse al cierre de sesión y también al cierre de fallos relevantes.

335.2 When to Run

Run meta-analysis when:

SessionEnd,

Stop after bug fix,

test failure resolved,

deploy failure,

secret incident,

drift detected,

fake done caught,

output contract violation,

PRG failure,

recovery failure,

resource incident,

cost firebreak,

Owner correction,

repeated confusion,

scope drift.


335.3 Session Close Output

SESSION_CLOSE_META_ANALYSIS session_id: project: completed: failures_detected: drifts_detected: bugs_fixed: bugs_unfixed: patterns: hard_rule_candidates: process_rule_candidates: trap_candidates: standard_update_candidates: backlog_items: tests_needed: next_session_risks: safe_handoff: status:

335.4 Hard Rule candidata

HR-SESSION-META-001: Every significant session must close with meta-analysis of bugs, failures, drift, false done, process gaps and standards learned.


---

336. STACK-WIDE ERROR CAPTURE

336.1 Propósito

Inicialmente con Claude Power Pack activa. Después, idealmente, también cuando PP no esté activo.

336.2 Presence Modes

PP-ACTIVE: Full hooks, commands, agents, CEPS, UKDL, Hard Rules.

PP-PARTIAL: Some hooks/commands active, but not full system.

PP-PASSIVE: Project writes compatible logs/events, PP later ingests.

PP-OFFLINE: Errors captured by lightweight local format and imported later.

336.3 Universal Error Inbox

Ubicación sugerida:

~/.claude/pp_runtime/universal_error_inbox/events.jsonl

Project-local fallback:

<repo>/.claude-power-pack/error_inbox/events.jsonl

336.4 Universal Error Inbox Rule

Any stack component may write a sanitized UFE to the inbox.

Later, PP ingests and runs meta-analysis.

336.5 Hard Rule candidata

HR-UFE-INBOX-001: All code-producing projects should emit sanitized Universal Failure Events for bugs, errors, drift, regressions and false done, even if full Power Pack is not active.


---

337. META-ANALYSIS SOURCE ROUTERS

337.1 Sources

UMAL should ingest from:

test results,

build output,

lint output,

type checker output,

runtime logs,

frontend errors,

backend errors,

CLI errors,

401/403 auth errors,

empty button detectors,

placeholder scanners,

deploy logs,

browser console logs,

user corrections,

Claude Code failed tasks,

git diffs,

verify probes,

CEPS events,

NEVER_AGAIN,

UKDL,

Resource incidents,

CPC recovery incidents,

RAM/OOM autopsies,

output contract violations,

backlog stale items.


337.2 Router Contract

META_ANALYSIS_SOURCE_ROUTER source: event_detected: normalized_to_UFE: secret_scan: severity: requires_meta_analysis: destination: status:

337.3 Rule

Everything becomes UFE first, then meta-analysis.


---

338. CONTRACT OF REALITY VIOLATION TYPES

338.1 Purpose

Explicitly encode the Owner’s reality contract.

338.2 Violation Types

REALITY-001: Empty button.

REALITY-002: Placeholder presented as real feature.

REALITY-003: 401/403 ignored.

REALITY-004: Frontend action not connected to backend/CLI.

REALITY-005: CLI command exists but does nothing meaningful.

REALITY-006: Success toast without real success.

REALITY-007: Test passes but product path broken.

REALITY-008: Compile passes but runtime broken.

REALITY-009: Mock data presented as production data.

REALITY-010: Done claimed without user-visible proof.

REALITY-011: Agent says “implemented” but file only scaffolded.

REALITY-012: Button calls stub.

REALITY-013: Workflow node disconnected.

REALITY-014: API key missing but UI hides failure.

REALITY-015: Error swallowed silently.

338.3 Hard Rule candidata

HR-REALITY-001: Reality Contract violations must be treated as bugs, not polish issues.


---

339. META-ANALYSIS TO BACKLOG PIPELINE

339.1 Propósito

Cada meta-análisis debe producir acción.

Possible outputs:

no action needed,

backlog item,

hard rule,

process rule,

trap,

test,

standard update,

prompt compiler update,

documentation update,

tool/hook improvement.


339.2 Pipeline

1. UFE created.


2. Meta-analysis generated.


3. Rule level classified.


4. Backlog candidate generated.


5. Standard update evaluated.


6. Test candidate generated.


7. Owner review if high-impact.


8. Registry updated.


9. Future done-gates modified.



339.3 Backlog Item

META_BACKLOG_ITEM source_analysis: title: why_now: failure_prevented: applies_to: priority: done_criteria: validation: standard_impact: owner_approval_required:

339.4 Hard Rule candidata

HR-META-BACKLOG-001: Meta-analysis without action routing is incomplete. Every meta-analysis must produce an action, rejection reason or owner-review item.


---

340. META-ANALYSIS TO PROMPT COMPILER PIPELINE

340.1 Propósito

Los aprendizajes deben mejorar futuros prompts.

If failure caused by prompt ambiguity:

update prompt compiler.


If failure caused by missing PRG:

add PRG clause.


If failure caused by no inline plan:

add inline plan clause.


If failure caused by no mode decision:

add mode router clause.


340.2 Prompt Patch Candidate

PROMPT_PATCH_CANDIDATE source_failure: prompt_gap: new_clause: applies_to: risk: expected_prevention: status:

340.3 Rule

Repeated prompt-induced failures must update prompt compiler doctrine.


---

341. META-ANALYSIS TO TEST PIPELINE

341.1 Propósito

Cada patrón de bug serio debería generar test.

341.2 Test Candidate

TEST_CANDIDATE source_failure: bug_pattern: test_type: target_layer: expected_failure_before: expected_pass_after: fixture_needed: secret_safe: priority:

341.3 Examples

Empty button:

UI action wiring test.


401 ignored:

auth failure visible handling test.


CLI/frontend disconnect:

end-to-end command trigger test.


Placeholder:

placeholder scanner test.


Fake done:

output contract test.


Registry corruption:

recovery test.


OOM crash:

topology preservation test.


341.4 Rule

If a bug can recur and can be tested, create test candidate.


---

342. META-ANALYSIS TO STANDARD UPDATE PIPELINE

342.1 Propósito

Cada error que revela un estándar faltante debe modificar future done-gates.

342.2 Standard Registry

Ubicación sugerida:

~/.claude/pp_runtime/standards/completeness_standards.json

Project-local:

<repo>/.claude-power-pack/completeness_standards.json

342.3 Completeness Standard

COMPLETENESS_STANDARD standard_id: title: description: applies_to: trigger: required_evidence: done_gate: source_failure: created_at: status: owner_reviewed:

342.4 Rule

Future features must load relevant completeness standards before declaring done.


---

343. META-ANALYSIS DOES NOT MEAN VERBOSE OUTPUT

343.1 Problema

Meta-analysis can become noise.

343.2 Rule

Store full meta-analysis in canonical files. Show compact summary to Owner.

343.3 Owner Summary Format

META_ANALYSIS_SUMMARY pattern_found: rule_update: standard_update: backlog_created: next_prevention:

343.4 Hard Rule candidata

HR-META-NOISE-001: Meta-analysis should be stored structurally and summarized compactly. Do not bloat every final response with full doctrine.


---

344. UNIVERSAL META-ANALYSIS FILES

344.1 Canonical Files

Suggested locations:

knowledge-vault/UKDL/universal-knowledge.md
knowledge-vault/UKDL/hard-rules.md
knowledge-vault/UKDL/process-rules.md
knowledge-vault/UKDL/traps.md
knowledge-vault/UKDL/meta-analysis-log.jsonl
knowledge-vault/UKDL/completeness-standards.md
knowledge-vault/UKDL/reality-contract.md

Runtime:

~/.claude/pp_runtime/universal_error_inbox/events.jsonl
~/.claude/pp_runtime/meta_analysis/records.jsonl
~/.claude/pp_runtime/meta_analysis/standard_updates.jsonl
~/.claude/pp_runtime/meta_analysis/prompt_patches.jsonl

344.2 Rule

Canonical doctrine lives in files. Prompt only routes to it.


---

345. AGENT TEAMS MODE INTEGRATION

345.1 Propósito

AGENT TEAMS Mode debe usar meta-analysis.

Roles sugeridos:

Bug Root Cause Agent.

Production Reality Gate Agent.

Standard Completeness Agent.

Hard Rule Classifier Agent.

Trap Detector Agent.

Backlog Router Agent.

Test Candidate Agent.

Secret Safety Agent.

Cost/Cascade Agent.


345.2 Agent Team Output

AGENT_TEAM_META_ANALYSIS root_cause: reality_gate: rule_classification: standard_update: test_candidate: backlog: risk: final_recommendation:

345.3 Rule

Agent teams should not create verbose debate. They should produce compact structured conclusion.


---

346. UNIVERSALITY ACROSS ALL CODE PROJECTS

346.1 Propósito

Esto no es para un vertical.

Aplica a todo proyecto con código.

346.2 Project-Agnostic Rules

Every code project can fail through:

broken reality,

missing validation,

bad prompt,

bad plan,

weak execution,

hidden placeholder,

disconnected integration,

auth failure,

poor recovery,

resource crash,

secret leak,

drift,

false done.


Therefore every code project must share:

UFE schema,

meta-analysis schema,

PRG,

Standard Updater,

UKDL 3-level classification,

session-close meta-analysis,

prompt compiler patches.


346.3 Project-Specific Overrides

Projects may add extra rules, but cannot remove universal rules.

Examples:

Minecraft plugin adds Paper/TPS checks.

Web app adds button/API checks.

CLI adds command execution checks.

n8n adds node connectivity checks.

Agent workflow adds tool-call reality checks.


346.4 Hard Rule candidata

HR-UNIVERSAL-CODE-001: All code-producing projects must use universal failure/meta-analysis contracts, with project-specific extensions only adding stricter gates.


---

347. INITIAL IMPLEMENTATION WITH POWER PACK ACTIVE

347.1 Phase A -- PP Active Only

Implement first inside PP active environment:

SessionEnd meta-analysis hook.

UFE event capture.

meta-analysis record writer.

3-level UKDL classifier.

Production Reality Gate schema.

Standard Update Candidate schema.

compact owner summary.


347.2 Phase B -- Cross-Project PP Active

Enable for all repos where PP is loaded:

project-local UFE inbox,

universal inbox,

project-specific tags,

backlog routing.


347.3 Phase C -- PP Partial

Allow projects to emit UFE files even if full hooks not active.

347.4 Phase D -- PP Offline Import

Allow later import:

logs,

test failures,

user notes,

Claude transcripts,

CI failures,

error files.


347.5 Rule

Start with PP active. Design schema so PP inactive projects can join later.


---

348. CLAUDE CODE PROMPT FOR PART XVI IMPLEMENTATION

PROMPT:

Act as the implementation engineer for Claude Power Pack Universal Meta-Analysis Layer.

MISSION: Implement a project-agnostic meta-analysis system that captures every bug, failure, error, drift, regression, false done, Production Reality Gate violation, output mismatch and process failure across all code-producing projects.

SOURCE OF TRUTH: Use the repo on disk. Reuse existing UKDL, NEVER_AGAIN, CEPS, Hard Rules, session hooks, output contracts and backlog systems if present.

CORE DOCTRINE: The Owner boilerplate is a router, not a library. Full logic must live in canonical files read by Claude Code at session start.

NON-NEGOTIABLES:

Do not bloat the Owner boilerplate.

Do not store raw secrets in events, analysis, logs, UKDL, prompts or standards.

Do not convert every minor issue into a Hard Rule.

Do not skip Production Reality Gate for features.

Do not declare done when buttons, CLI, frontend/backend, auth, workflow or runtime reality is unverified.

Do not create verbose meta-analysis in final response; store structured record and show compact summary.

Do not make this domain-specific. It must apply to all code-producing projects.


IMPLEMENT FIRST:

1. Universal Failure Event schema.


2. Universal Meta-Analysis Record schema.


3. UKDL 3-level classifier: Hard Rules, Process Rules, Traps.


4. Production Reality Gate record.


5. Standard Update Candidate record.


6. Session-close meta-analysis hook in advisory mode.


7. Compact summary output.


8. Tests for fake done, placeholder, empty button, 401 ignored, frontend-CLI disconnect and prompt drift classification.



ACCEPTANCE:

Every significant failure can be normalized into UFE.

UFE can become meta-analysis record.

Meta-analysis classifies Hard Rule / Process Rule / Trap / reject.

PRG violation is treated as bug.

Standard update candidate can be produced.

Final output remains compact.

No raw secrets stored.

Tests pass.


FINAL RECEIPT: Return files changed, tests added, tests run, event schema status, classifier status, PRG status, standards update status, secret safety status, remaining risks and next phase.


---

349. HARD RULE SET FOR PART XVI

HR-META-001

Every significant bug, failure, error, drift, regression, false done or reality violation must generate or update a Universal Failure Event.

HR-META-002

Every Universal Failure Event must be classified into Hard Rule, Process Rule, Trap, backlog item, test candidate, standard update or rejected with reason.

HR-META-003

Production Reality Gate violations are bugs, not polish issues.

HR-META-004

Owner boilerplate must remain compact and route to canonical doctrine files.

HR-META-005

Session-close meta-analysis must be compact in chat and structured in storage.

HR-META-006

No raw secrets may be stored in meta-analysis, UKDL, events, standards, prompt patches or logs.

HR-META-007

If a new quality requirement is discovered, evaluate whether it becomes future Standard of Completeness.

HR-META-008

Plan mode must produce inline approval-ready plan; plan-file is backup, not replacement.

HR-META-009

Mode router must decide plan mode, execution mode or ultra-plan mode based on ROI and risk.

HR-META-010

All code-producing projects inherit universal meta-analysis contracts unless stricter project-specific rules apply.


---

350. PART XVI CANONICAL PRINCIPLES

350.1 Boilerplate Routes, Doctrine Lives Elsewhere

The prompt stays compact. The system files hold the full logic.

350.2 Every Failure Must Teach

Bugs that do not improve the system are wasted pain.

350.3 Reality Beats Compilation

Compiling is not done. Running is not done. Real user-visible behavior is done.

350.4 Meta-Analysis Must Produce Action

Rule, test, backlog, standard, trap, prompt patch or explicit rejection.

350.5 Not Every Bug Is a Hard Rule

Hard Rules block. Process Rules guide. Traps warn.

350.6 Standards Must Compound

When a better done-gate is discovered, future features inherit it.

350.7 Compact Output, Structured Memory

Do not spam the Owner. Store full analysis structurally.

350.8 Universal First, Project-Specific Second

All code projects share the same failure/meta-analysis backbone.

350.9 False Done Is a Critical Pattern

Done without Production Reality Gate is not done.

350.10 The Stack Must Become Harder To Break Every Time It Breaks

Every bug, failure, error or drift should make the entire execution stack more resilient.

END OF PART XVI.

Sí. La Parte XVII debe subir de meta-análisis reactivo a inmunidad predictiva del stack: que el sistema no solo aprenda después del bug, sino que detecte patrones antes de que se conviertan en fallos. Lo conecto al dataset base del Claude Power Pack, que ya tiene UKDL, CEPS, NEVER_AGAIN, Hard Rules, hooks y proactive agents como cimientos. 

