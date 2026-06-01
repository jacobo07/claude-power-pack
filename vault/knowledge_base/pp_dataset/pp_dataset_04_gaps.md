# PP Dataset -- Cascade Prevention Engine

**Source:** PP_DATASET_20260531T122242Z (1).md, lines 3890-5296
**Dataset part:** Part III
**Ingested:** 2026-06-01 (BL-DATASET-001 M0)
**Lines in this file:** 1407

---


# CLAUDE POWER PACK -- EXTENSION DATASET PART III
# Cascade Bug Prevention + Output Fidelity + Cost Control + Secret Safety + Backlog Continuity

## 37. BUG CASCADE PREVENTION ENGINE

### 37.1 Propósito

El Claude Power Pack debe añadir una capa explícita para prevenir bugs en cascada.

Un bug en cascada ocurre cuando un error pequeño no se queda aislado, sino que genera una cadena de fallos posteriores:
- un mal prompt provoca una mala interpretación,
- la mala interpretación toca archivos incorrectos,
- los archivos incorrectos rompen tests,
- los tests rotos fuerzan fixes improvisados,
- los fixes improvisados generan deuda,
- la deuda entra en el learning system,
- el agente aprende mal,
- el mismo patrón se repite en otro proyecto.

La prevención de bugs en cascada debe convertirse en una capacidad central del Power Pack, no solo en una función de CEPS.

### 37.2 Principio central

Every bug has a blast radius.

El agente no debe limitarse a arreglar el síntoma. Debe identificar:
- origen,
- expansión,
- superficies contaminadas,
- sistemas afectados,
- prevención futura,
- hard rule candidata,
- coste causado,
- impacto en one-shot reliability,
- riesgo de repetición cross-project.

### 37.3 Nombre canónico

Canonical Name:
Cascade Bug Prevention Engine

Abreviatura:
CBPE

Función:
Detectar, contener y prevenir bugs que generan errores secundarios en código, contexto, coste, secretos, outputs, backlog, aprendizaje o despliegue.

---

## 38. CASCADE BUG MODEL

### 38.1 Estructura de una cascada

Toda cascada tiene 7 partes:

1. Root Trigger
   El evento inicial.

2. First Failure
   El primer fallo observable.

3. Propagation Path
   Cómo se expande.

4. Secondary Failures
   Fallos derivados.

5. Contaminated Surfaces
   Lugares donde el fallo deja residuos.

6. Blast Radius
   Alcance del daño.

7. Prevention Rule
   Regla que impide que vuelva a pasar.

### 38.2 Cascade Record Schema

CASCADE_RECORD
id:
timestamp:
project:
root_trigger:
first_failure:
propagation_path:
secondary_failures:
contaminated_surfaces:
blast_radius:
severity:
cost_impact:
secret_risk:
one_shot_impact:
output_quality_impact:
affected_files:
affected_tools:
affected_logs:
affected_learning_systems:
containment_action:
fix_action:
prevention_rule:
hard_rule_candidate:
validation_required:
status:

### 38.3 Severidad de cascada

C0 -- No cascade
El fallo está aislado.

C1 -- Local cascade
Afecta una función, archivo o test.

C2 -- Repo cascade
Afecta varias partes del repo.

C3 -- Workflow cascade
Afecta comandos, CI, deploy, scripts o generación de artefactos.

C4 -- Cross-system cascade
Afecta aprendizaje, hooks, agents, hard rules, otro proyecto o contexto futuro.

C5 -- Security cascade
Implica secretos, credenciales, tokens, .env, logs contaminados o exposición externa.

C6 -- Production cascade
Afecta deploy, usuarios, servicios activos, datos reales o infraestructura.

### 38.4 Regla de prioridad

Si una cascada incluye secretos, producción o aprendizaje contaminado, debe elevarse automáticamente a prioridad máxima.

---

## 39. CASCADE TYPES

### 39.1 Secret Leak Cascade

Cadena típica:
.env leído en raw → terminal output contiene key → evidence archive guarda output → final response resume key → learning system registra lesson contaminada → futuro agente puede recuperar secreto.

Prevención:
- redacted reads only,
- post-tool scanner,
- evidence sanitizer,
- final response scanner,
- no raw secrets in learning systems,
- incident protocol.

Hard Rule candidata:
If secret-like content appears in any tool output, stop and sanitize before continuing. Never allow contaminated output into evidence, memory, final response or commit.

### 39.2 Cost Explosion Cascade

Cadena típica:
prompt ambiguo → full repo scan → múltiples full-file reads → subagent innecesario → resumen largo → contexto lleno → compact tardío → segunda sesión necesaria.

Prevención:
- pre-task cost contract,
- context pack,
- cheap-first path,
- repeated read detector,
- cost-to-progress ratio,
- context budget ceiling.

Hard Rule candidata:
If the same file or dataset is read repeatedly without new information gain, stop and create a compressed context artifact before continuing.

### 39.3 Scope Drift Cascade

Cadena típica:
bug puntual → agente decide refactorizar → cambia arquitectura → rompe tests → arregla tests con workarounds → crea deuda → output dice “done” sin evidenciar equivalencia.

Prevención:
- Fidelity Lock,
- allowed files list,
- forbidden actions,
- no refactor unless requested,
- one-shot contract,
- validation ladder.

Hard Rule candidata:
A bug fix must not become a refactor unless the root cause proves refactor is required and the Owner’s constraints allow it.

### 39.4 Test Pollution Cascade

Cadena típica:
test usa fake critical bug → fake bug entra en NEVER_AGAIN → fake bug se convierte en Hard Rule → regla inútil contamina CLAUDE.md → futuras sesiones leen ruido como doctrina.

Prevención:
- test mode isolation,
- fake/test tag enforcement,
- no test artifacts in production learning,
- quarantine learning writes from test runs.

Hard Rule candidata:
Test artifacts must never auto-promote into production hard rules, UKDL doctrine, or persistent Owner-facing learning without explicit test tag and quarantine.

### 39.5 Learning Contamination Cascade

Cadena típica:
agente malinterpreta fallo → registra lesson incorrecta → CEPS la usa como patrón → Hard Rule se crea con trigger falso → futuras ejecuciones se bloquean por una regla mala.

Prevención:
- evidence requirement before learning,
- root-cause confidence field,
- learning review gate,
- reversible hard rule install,
- stale rule audit.

Hard Rule candidata:
No lesson may become a Hard Rule unless it includes observable trigger, reproducible evidence, and actionable stop condition.

### 39.6 Deployment Cascade

Cadena típica:
deploy sin verify → config incompatible → service down → rollback incompleto → logs contienen secretos → monitor solo ve TCP up → Owner cree que está sano pero está degraded.

Prevención:
- pre-deploy verify,
- post-deploy smoke,
- health check depth,
- rollback proof,
- secret-safe logs,
- production readiness contract.

Hard Rule candidata:
No deploy is complete until post-deploy health, rollback availability, and secret-safe evidence are verified.

### 39.7 Context Stale Cascade

Cadena típica:
agente recuerda estructura vieja → edita archivo movido → crea duplicado → docs y código divergen → future command usa ruta antigua → bug reaparece.

Prevención:
- repo truth before memory,
- file existence validation,
- stale context guard,
- canonical path registry,
- context pack refresh.

Hard Rule candidata:
Before acting on remembered repo structure, verify current file paths on disk.

### 39.8 Naming Drift Cascade

Cadena típica:
agente renombra concepto → otro módulo usa alias → docs usan tercer nombre → commands no encuentran entidad → backlog crea duplicados → Owner pierde claridad.

Prevención:
- canonical entity registry,
- no aliases,
- naming lint,
- rename approval,
- project glossary.

Hard Rule candidata:
Do not introduce new names for existing canonical entities. Resolve to canonical name before creating files, agents, commands or docs.

### 39.9 Output Drift Cascade

Cadena típica:
final output exagera avance → Owner confía → próxima tarea se basa en claim falso → Claude Code ejecuta sobre premisa falsa → proyecto se desvía.

Prevención:
- verification-or-no-claim,
- evidence strength labels,
- partial completion honesty,
- output contract registry.

Hard Rule candidata:
Do not state that a task is complete, tested, safe, deployed, production-ready, or secret-free without matching evidence.

### 39.10 Backlog Cascade

Cadena típica:
backlog genérico → Owner ejecuta tarea de baja prioridad → se pierde tiempo → proyecto no avanza a venta/demo/fiabilidad → se acumulan tareas bonitas pero inútiles.

Prevención:
- backlog from repo evidence,
- priority scoring,
- anti-busywork gate,
- revenue/demo/reliability filters,
- next-best-action output.

Hard Rule candidata:
Backlog items must be tied to evidence, risk reduction, revenue readiness, demo readiness, cost reduction, one-shot improvement or safety. Otherwise reject.

---

## 40. CASCADE CONTAINMENT PROTOCOL

### 40.1 Objetivo

Cuando se detecta una cascada, el agente debe dejar de expandir el daño.

### 40.2 Stop Conditions

Activar containment si:
- aparece un secreto,
- se toca archivo fuera de scope,
- un fix genera nuevos tests fallidos,
- el agente necesita tercer intento,
- se repite el mismo comando sin avance,
- se detecta contexto contradictorio,
- se rompe un contrato de output,
- el coste crece sin progreso,
- un log/evidence queda contaminado,
- una lesson se basa en una suposición débil.

### 40.3 Containment Steps

1. Freeze current scope.
2. Stop non-essential tool calls.
3. Identify root trigger.
4. Identify contaminated surfaces.
5. Prevent further writes.
6. Preserve safe evidence.
7. Redact any sensitive output.
8. Choose smallest safe correction.
9. Validate correction.
10. Register cascade record.
11. Propose prevention rule.
12. Update backlog if unresolved.

### 40.4 Cascade Containment Output

CASCADE_CONTAINMENT_REPORT
status:
root_trigger:
first_failure:
spread_detected:
contaminated_surfaces:
actions_stopped:
safe_evidence:
fix_applied:
validation:
remaining_risk:
hard_rule_candidate:
backlog_item_created:

---

## 41. PRE-EXECUTION CASCADE RISK CHECK

### 41.1 Objetivo

Antes de ejecutar una tarea, PP debe estimar riesgo de cascada.

### 41.2 Cascade Risk Factors

- touches secrets
- touches deploy config
- touches global config
- touches hooks
- touches learning systems
- touches hard rules
- touches generated files
- touches multiple projects
- touches canonical naming
- uses broad refactor
- uses full repo scan
- requires external API
- modifies CI/CD
- modifies auth
- modifies database schema
- modifies production command
- has vague prompt
- lacks validation
- lacks rollback
- previous similar task failed

### 41.3 Cascade Risk Score

Score 0-100.

0-20:
Low risk.

21-40:
Moderate risk. Require validation.

41-60:
High risk. Require One-Shot Contract and rollback.

61-80:
Critical risk. Require containment plan and secret scan.

81-100:
No autonomous execution. Needs explicit constrained plan or human approval.

### 41.4 Rule

High cascade risk tasks must not be executed as open-ended tasks.

---

## 42. BUG CASCADE PREVENTION FOR SECRETS

### 42.1 Core insight

Secret leaks are the most dangerous bug cascades because they propagate silently into:
- logs,
- model context,
- evidence,
- commits,
- screenshots,
- learning systems,
- backups,
- final responses,
- third-party tools.

### 42.2 Secret Cascade Surfaces

Scan these surfaces:

- terminal stdout
- terminal stderr
- shell history
- generated markdown
- evidence files
- cold boot evidence
- test fixtures
- screenshots
- JSON logs
- CEPS events
- NEVER_AGAIN entries
- UKDL rows
- Hard Rule candidates
- commit diffs
- staged files
- final response
- backlog items
- prompt compiler outputs

### 42.3 Secret Cascade Prevention Rule

A secret is not “handled” when removed from the source file.

It is handled only when all contaminated surfaces are clean or quarantined.

### 42.4 Secret Blast Radius Levels

SB0:
No secret detected.

SB1:
Secret only exists in local source file, not displayed.

SB2:
Secret appeared in terminal output.

SB3:
Secret appeared in generated artifact or evidence.

SB4:
Secret was staged or committed.

SB5:
Secret was pushed or sent externally.

SB6:
Secret entered model context, public logs, CI logs or third-party system.

### 42.5 Required Action by Secret Blast Radius

SB1:
Redact and keep local.

SB2:
Clear/avoid reusing output, rotate if sensitive.

SB3:
Quarantine artifact, regenerate sanitized evidence.

SB4:
Remove from git history or rotate immediately.

SB5:
Rotate immediately, revoke old credential, audit access.

SB6:
Treat as compromised, rotate, audit, document incident without raw value.

---

## 43. BUG CASCADE PREVENTION FOR COST

### 43.1 Core insight

Cost bugs are not only expensive. They also reduce quality because context becomes bloated and the agent gets less precise.

### 43.2 Cost Cascade Patterns

Pattern A:
Repeated file reads without summarization.

Pattern B:
Large dataset loaded for a small question.

Pattern C:
Subagent invoked before deterministic search.

Pattern D:
Long final summaries repeated in every turn.

Pattern E:
No context pack, so each task reloads history.

Pattern F:
No command discovery, so the agent reinvents command behavior.

Pattern G:
No backlog snapshot, so project is rescanned repeatedly.

### 43.3 Cost Cascade Stop Conditions

Stop if:
- same file read 3 times in one session,
- context exceeds threshold without handoff,
- output grows but artifact count stays zero,
- tool calls repeat same query,
- full repo scan returns no action,
- model route is expensive but task is simple,
- no validation has run after many calls.

### 43.4 Cost Cascade Fix

When detected:
1. Summarize relevant context into compact artifact.
2. Stop repeated reads.
3. Use index.
4. Use cheaper model route.
5. Create reusable project snapshot.
6. Add cost autopsy entry.
7. Add backlog task to eliminate repeated cost source.

---

## 44. BUG CASCADE PREVENTION FOR ONE-SHOT RELIABILITY

### 44.1 Core insight

One-shot failures often cascade from small ambiguity.

A missing constraint at the beginning becomes:
- wrong implementation,
- wrong files,
- wrong tests,
- wrong output,
- second attempt,
- higher cost,
- lower trust.

### 44.2 One-Shot Cascade Causes

- unclear objective
- missing forbidden actions
- missing allowed files
- missing validation
- missing rollback
- stale context
- overbroad prompt
- no output contract
- no secret policy
- no done criteria
- ambiguous canonical names

### 44.3 One-Shot Cascade Prevention

Before execution:
- compile One-Shot Contract,
- identify ambiguities,
- resolve high-risk assumptions,
- lock scope,
- select validation ladder,
- choose output contract,
- set stop conditions.

During execution:
- compare actions against scope,
- block scope expansion,
- detect repeated failures,
- detect validation mismatch.

After execution:
- record one-shot outcome,
- log failure cause if any,
- update prompt compiler rules.

### 44.4 One-Shot Failure Categories

- misunderstood objective
- wrong file
- wrong abstraction
- overengineering
- under-validation
- secret risk missed
- cost route wrong
- stale context
- naming drift
- output claim unsupported

---

## 45. BUG CASCADE PREVENTION FOR OUTPUT QUALITY

### 45.1 Core insight

Bad outputs create bad next actions.

If final response is vague, the Owner may make the next decision based on incomplete or false information.

### 45.2 Output Cascade Patterns

Pattern A:
Says “done” without evidence.

Pattern B:
Mentions tests but not command.

Pattern C:
Ignores risks.

Pattern D:
Does not mention files changed.

Pattern E:
Does not say what remains blocked.

Pattern F:
Does not create next action.

Pattern G:
Claims no secrets without scan.

Pattern H:
Does not distinguish partial completion from full completion.

### 45.3 Output Cascade Prevention

Every output should include:
- status,
- evidence,
- files changed,
- validation,
- secret scan,
- risks,
- next action,
- whether done criteria were met.

### 45.4 Output Cascade Rule

A weak final output is a bug because it contaminates the Owner’s next decision.

---

## 46. BUG CASCADE PREVENTION FOR BACKLOG

### 46.1 Core insight

A bad backlog can waste more time than a code bug.

If the system recommends low-leverage tasks, the Owner spends hours advancing the wrong thing.

### 46.2 Backlog Cascade Causes

- no evidence source,
- no priority formula,
- no revenue/demo/reliability filter,
- no effort estimate,
- no done criteria,
- no validation,
- too many tasks,
- no top one recommendation,
- generic suggestions,
- tasks detached from current blockers.

### 46.3 Backlog Cascade Prevention

Every generated backlog must:
- rank tasks,
- justify why now,
- include evidence source,
- include done criteria,
- include validation,
- reject busywork,
- identify smallest next action.

### 46.4 Backlog Health Metrics

- % backlog items with evidence
- % backlog items with done criteria
- % backlog items tied to launch/revenue/reliability/safety/cost
- number of stale items
- number of repeated items
- number of vague items
- number of blocked items
- number of completed high-impact items

---

## 47. CASCADE-AWARE HARD RULE PIPELINE

### 47.1 Objetivo

No todas las Hard Rules deben salir de bugs aislados. Algunas deben salir de cascadas.

Un bug aislado enseña una regla local.
Una cascada enseña una regla sistémica.

### 47.2 Cascade-to-HardRule Criteria

Proponer Hard Rule si:
- cascada alcanzó C3 o superior,
- secret risk fue S3 o superior,
- mismo root trigger ocurrió 2 veces,
- una cascada costó más de cierto umbral de tokens,
- output falso causó siguiente tarea incorrecta,
- test pollution contaminó learning,
- deployment cascade afectó producción,
- scope drift rompió tests,
- stale context creó archivos duplicados.

### 47.3 Hard Rule Format

HARD_RULE_CANDIDATE
id:
source_cascade_id:
title:
trigger:
stop_condition:
required_action:
evidence_required:
scope:
examples:
false_positive_guard:
test_required:
owner_review_required:

### 47.4 False Positive Guard

Cada hard rule contra cascadas debe incluir cuándo NO aplicar.

Ejemplo:
No bloquear lectura de config pública solo porque contiene la palabra token si el valor es un placeholder en .env.example.

---

## 48. CASCADE-AWARE CEPS EXPANSION

### 48.1 Objetivo

CEPS debe evolucionar de “event logger” a “cascade prevention system”.

### 48.2 Nuevos campos CEPS

Añadir a CEPS events:

- root_trigger
- cascade_depth
- propagation_path
- affected_surfaces
- secret_blast_radius
- cost_blast_radius
- learning_contaminated
- output_contaminated
- backlog_contaminated
- containment_success
- hard_rule_candidate_id

### 48.3 Cascade Depth

Depth 0:
Single isolated event.

Depth 1:
One secondary failure.

Depth 2:
Multiple secondary failures.

Depth 3:
Workflow affected.

Depth 4:
Learning or governance affected.

Depth 5:
Cross-project or secret/production affected.

### 48.4 CEPS Cascade Query

PP should be able to answer:
- What root triggers cause the most cascades?
- Which files create the biggest blast radius?
- Which task types produce the most cascade risk?
- Which commands often precede cascade?
- Which hard rules reduced cascades?
- Which projects have unresolved cascade patterns?

---

## 49. CASCADE-AWARE BACKLOG GENERATION

### 49.1 Objetivo

Backlog should prioritize tasks that reduce cascade risk.

### 49.2 Cascade Reduction Backlog Items

Examples:
- Add secret scanner before evidence archive.
- Add output contract validator.
- Add stale context guard.
- Add test artifact quarantine.
- Add repeated read detector.
- Add pre-deploy verification.
- Add rollback smoke test.
- Add file sensitivity map.
- Add prompt compiler for high-risk tasks.
- Add learning redaction.

### 49.3 Priority Boost

A backlog item gets priority boost if it:
- prevents C4+ cascades,
- prevents secret leaks,
- prevents repeated cost explosions,
- prevents false “done” claims,
- prevents cross-project contamination,
- prevents bad hard rules,
- prevents production deploy failures.

### 49.4 Cascade ROI

Cascade ROI =
probability of recurrence x blast radius x prevention strength / implementation effort

High Cascade ROI tasks should outrank cosmetic improvements.

---

## 50. CASCADE-AWARE PROMPT COMPILER

### 50.1 Objetivo

The prompt compiler should not only make prompts clearer. It should make them cascade-resistant.

### 50.2 Required Prompt Fields for Cascade Resistance

- objective
- exact scope
- allowed files
- forbidden files
- forbidden actions
- secret handling
- cost ceiling
- validation ladder
- rollback plan
- output contract
- stop conditions
- cascade risks
- containment protocol

### 50.3 Anti-Cascade Prompt Clause

Every high-risk Claude Code prompt should include:

“Do not expand scope. If the task reveals a broader architectural issue, stop after documenting it and create a backlog item instead of refactoring beyond scope.”

### 50.4 Secret Anti-Cascade Prompt Clause

Every prompt involving config, deployment, logs, auth, APIs, .env or integrations should include:

“Do not print, store, summarize, commit, or expose raw secrets. Use redacted previews only. If a secret appears in output, stop and trigger incident protocol.”

### 50.5 Cost Anti-Cascade Prompt Clause

Every broad audit prompt should include:

“Use deterministic local search and indexes before reading large files. Stop repeated reads. Summarize reusable context into a compact artifact if needed.”

---

## 51. CASCADE-AWARE VALIDATION LADDER

### 51.1 Problema

Validation itself can cause cascades if it runs unsafe commands, exposes secrets, mutates production or creates noisy artifacts.

### 51.2 Validation Risk Classes

V0:
Static reasoning only.

V1:
Read-only local checks.

V2:
Local tests.

V3:
Integration tests with fake data.

V4:
External service calls.

V5:
Production-touching validation.

V6:
Secret-adjacent validation.

### 51.3 Validation Rule

Choose the lowest validation level that proves the claim.

Do not use production-touching validation when local smoke test is enough.

### 51.4 Validation Safety

Before validation:
- check secret risk,
- check mutation risk,
- check production risk,
- check cost risk,
- check artifact contamination risk.

After validation:
- scan output,
- sanitize evidence,
- record exact command,
- avoid raw logs if secrets possible.

---

## 52. CASCADE-AWARE EVIDENCE SYSTEM

### 52.1 Problema

Evidence is useful, but contaminated evidence becomes a liability.

### 52.2 Evidence Contamination Types

- secret contamination,
- stale claim contamination,
- test artifact contamination,
- excessive log contamination,
- irrelevant context contamination,
- wrong project contamination,
- generated file contamination,
- production data contamination.

### 52.3 Evidence Hygiene Rules

- store only necessary evidence,
- redact secrets,
- label test artifacts,
- include command and result,
- avoid huge logs,
- include timestamp,
- include project,
- include scope,
- include validation level,
- include limitations.

### 52.4 Evidence Record Schema

EVIDENCE_RECORD
id:
timestamp:
project:
task:
validation_level:
command:
result:
raw_output_stored:
secrets_scanned:
redaction_applied:
limitations:
linked_execution_packet:
linked_cascade_record:
safe_to_commit:

---

## 53. CASCADE-AWARE LEARNING SYSTEM

### 53.1 Problema

Learning systems can amplify mistakes.

If a bad lesson enters UKDL, NEVER_AGAIN, CEPS or Hard Rules, future sessions may behave worse.

### 53.2 Learning Confidence Levels

LC0:
Unverified observation.

LC1:
Likely pattern.

LC2:
Reproduced once.

LC3:
Reproduced multiple times.

LC4:
Validated with tests.

LC5:
Validated across projects.

Only LC3+ should be considered for hard rules unless severity is critical.

### 53.3 Learning Safety Fields

Every lesson should include:
- source evidence,
- confidence,
- false-positive risk,
- scope,
- affected project,
- whether secret-redacted,
- whether test artifact,
- whether production incident,
- whether hard rule candidate.

### 53.4 Learning Quarantine

Quarantine lessons if:
- source is test artifact,
- evidence is missing,
- secret redaction uncertain,
- root cause uncertain,
- output was generated during failed task,
- project context was stale,
- lesson contradicts existing hard rule.

### 53.5 Rule

Never let unverified learning become active governance.

---

## 54. CASCADE-AWARE PROJECT SNAPSHOT

### 54.1 Objetivo

Project snapshots should include cascade risk state.

### 54.2 Additional Snapshot Fields

- open_cascade_records
- highest_cascade_severity
- unresolved_secret_risks
- unresolved_cost_cascades
- unresolved_scope_drift_events
- contaminated_evidence_count
- quarantined_lessons_count
- repeated_root_triggers
- top_cascade_prevention_task
- cascade_risk_trend

### 54.3 Use in “What Now?”

When Owner asks what to do next, PP should prioritize unresolved cascade risks before cosmetic backlog.

---

## 55. CASCADE COMMANDS TO ADD

### 55.1 /cascade-scan

Purpose:
Scan current project for possible cascade risks.

Output:
- root triggers
- vulnerable files
- risky commands
- unresolved learning contamination
- secret cascade surfaces
- top prevention tasks

### 55.2 /cascade-autopsy

Purpose:
Analyze a recent failure and map propagation.

Output:
- root cause
- propagation path
- blast radius
- containment quality
- prevention rule
- backlog item

### 55.3 /cascade-prevent

Purpose:
Generate hardening backlog to prevent future cascades.

Output:
- P0 cascade prevention tasks
- hard rule candidates
- tests to add
- hooks to add
- evidence hygiene fixes

### 55.4 /cascade-clean

Purpose:
Find and clean contaminated evidence, logs, lessons or artifacts.

Output:
- contaminated surfaces
- safe cleanup plan
- files requiring redaction
- rotation needed yes/no
- learning entries to quarantine

### 55.5 /cascade-hardrule

Purpose:
Convert a validated cascade into a Hard Rule.

Output:
- trigger
- stop condition
- required action
- evidence
- false-positive guard
- test requirement

---

## 56. CASCADE BUG PREVENTION BACKLOG

### P0 -- Secret Cascade Prevention

1. Add pre-tool secret risk classifier.
2. Add post-tool output secret scanner.
3. Add evidence sanitizer.
4. Add final response redactor.
5. Add learning redactor.
6. Add git diff secret scanner.
7. Add dangerous command registry.
8. Add secret blast radius classifier.
9. Add secret incident protocol.
10. Add fake secret canary tests.

### P1 -- Scope and One-Shot Cascade Prevention

1. Add One-Shot Contract.
2. Add Fidelity Lock.
3. Add allowed/forbidden file enforcement.
4. Add no-refactor-without-trigger rule.
5. Add assumption ledger.
6. Add ambiguity-to-stop-condition escalation.
7. Add validation ladder selector.
8. Add one-shot failure log.
9. Add output contract validator.
10. Add scope drift detector.

### P2 -- Cost Cascade Prevention

1. Add repeated read detector.
2. Add context pack generator.
3. Add cheap-first enforcement.
4. Add cost autopsy.
5. Add route escalation/de-escalation.
6. Add token waste taxonomy.
7. Add large dataset load warning.
8. Add compact artifact creation.
9. Add command discovery to avoid reinventing flows.
10. Add cost-to-progress metric.

### P3 -- Learning Cascade Prevention

1. Add learning confidence levels.
2. Add test artifact quarantine.
3. Add redacted learning writes.
4. Add hard rule false-positive guard.
5. Add stale learning audit.
6. Add learning contradiction detector.
7. Add cross-project learning scope tags.
8. Add cascade-to-hardrule workflow.
9. Add quarantine review command.
10. Add lesson evidence requirement.

### P4 -- Backlog and Output Cascade Prevention

1. Add backlog evidence requirement.
2. Add anti-busywork gate.
3. Add next-best-action contract.
4. Add output quality score.
5. Add evidence strength label.
6. Add partial completion marker.
7. Add demo/revenue readiness prioritizer.
8. Add project snapshot cascade fields.
9. Add backlog stale item detector.
10. Add final execution receipt.

---

## 57. BUG CASCADE TESTING STRATEGY

### 57.1 Test Philosophy

Cascade prevention must be tested with synthetic chains, not only isolated unit tests.

### 57.2 Required Test Scenarios

Test 1:
Fake .env secret appears in command output.
Expected:
- output redacted,
- evidence blocked or sanitized,
- learning write redacted,
- final response safe.

Test 2:
Bug fix attempts to edit forbidden file.
Expected:
- scope drift blocked,
- backlog item created for broader issue.

Test 3:
Test artifact critical bug tries to enter Hard Rules.
Expected:
- quarantined,
- no production hard rule installed.

Test 4:
Same file read repeatedly.
Expected:
- repeated read warning,
- context pack suggested.

Test 5:
Deploy attempted with failing verify.
Expected:
- deploy blocked,
- cascade risk report generated.

Test 6:
Final response claims tests passed without command.
Expected:
- output contract violation.

Test 7:
Backlog item generated without evidence.
Expected:
- rejected or marked speculative.

Test 8:
Stale remembered path conflicts with repo.
Expected:
- repo truth wins,
- stale context logged.

Test 9:
Secret in generated markdown.
Expected:
- markdown sanitized before write.

Test 10:
Learning entry contains token-like value.
Expected:
- learning redactor replaces value.

### 57.3 Cascade Test Success Metric

A cascade test passes only if:
- initial bug detected,
- propagation stopped,
- contaminated surfaces identified,
- safe output generated,
- prevention rule proposed,
- no raw secret exposed,
- no false “done” claim.

---

## 58. CASCADE PREVENTION METRICS

### 58.1 Core Metrics

- cascade_events_per_week
- average_cascade_depth
- max_blast_radius
- containment_success_rate
- repeated_root_trigger_count
- secret_cascade_count
- cost_cascade_count
- scope_drift_count
- learning_contamination_count
- output_contract_violation_count
- backlog_quality_violation_count

### 58.2 Target Metrics

Target S+++:
- 0 secret cascades escaping final response.
- 0 raw secrets in evidence.
- 0 test artifacts promoted to production hard rules.
- 90% cascade containment success.
- 50% reduction in repeated root triggers.
- 30% reduction in repeated read cost cascades.
- 100% high-risk tasks with One-Shot Contract.
- 100% completion claims with evidence.

### 58.3 Cascade Dashboard

Future dashboard should show:
- active cascades,
- resolved cascades,
- top root triggers,
- top risky files,
- top risky commands,
- unresolved P0 cascade tasks,
- prevented cascades,
- hard rules created from cascades.

---

## 59. CASCADE PREVENTION PRINCIPLES

### 59.1 Fix the Chain, Not Just the Link

Do not only fix the immediate error. Find how it spread.

### 59.2 Containment Before Optimization

When a cascade starts, stop the spread before improving anything.

### 59.3 Secrets Are Radioactive

If a secret appears anywhere, assume every downstream artifact may be contaminated until scanned.

### 59.4 Cost Cascades Are Quality Bugs

Excessive token use is not just financial waste. It degrades reasoning precision.

### 59.5 Weak Outputs Cause Future Bugs

A vague final answer can be the root cause of the next bad task.

### 59.6 Learning Must Be Clean

Never store contaminated or unverified lessons in permanent governance.

### 59.7 Backlog Can Drift Too

A bad backlog is a strategic cascade because it pushes the Owner toward low-leverage work.

### 59.8 Scope Is a Safety Boundary

Most cascades become worse when the agent expands scope without permission.

### 59.9 Evidence Must Be Safe

Evidence that leaks secrets or preserves false claims is worse than no evidence.

### 59.10 Every Cascade Should Leave a Gate Behind

A resolved cascade should produce at least one of:
- hard rule,
- test,
- scanner,
- backlog item,
- output contract,
- prompt compiler clause,
- validation step,
- command guard.

---

## 60. FINAL INTEGRATION STATEMENT

Claude Power Pack should evolve from:
“a set of skills, hooks and governance tools”

into:
“a cascade-resistant execution operating system for Claude Code.”

The next level is not more raw automation.

The next level is controlled automation that:
- protects secrets,
- prevents cascades,
- reduces cost,
- preserves fidelity,
- improves one-shot success,
- produces stronger outputs,
- creates useful backlog when the Owner has no ideas,
- converts every failure into a preventive gate,
- avoids contaminating long-term learning,
- keeps projects moving toward launch, sale, reliability, safety and autonomy.

Canonical rule:
A bug is not fully fixed until its cascade path is understood and blocked.

END OF PART III.
