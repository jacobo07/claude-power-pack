# PP Dataset -- Execution OS + Secret-Safe Tools

**Source:** PP_DATASET_20260531T122242Z (1).md, lines 2340-3889
**Dataset part:** Part II
**Ingested:** 2026-06-01 (BL-DATASET-001 M0)
**Lines in this file:** 1550

---


# CLAUDE POWER PACK -- EXTENSION DATASET PART II
# Execution OS, Secret-Safe Automation, Backlog Generation, Output Fidelity and Cost Governance

## 16. EXECUTION OPERATING SYSTEM LAYER

### 16.1 Problema

El Claude Power Pack ya tiene múltiples piezas potentes: hooks, skills, agents, TIS/TCO, CEPS, Hard Rules, OSA y UQF. Pero todavía puede comportarse como una colección de herramientas separadas en vez de como un sistema operativo de ejecución unificado.

El riesgo:
- Cada herramienta optimiza una parte.
- El agente puede usar una skill sin respetar coste.
- El agente puede hacer un review sin conectar con backlog.
- El agente puede detectar un bug sin convertirlo en regla.
- El agente puede ahorrar tokens pero perder fidelidad.
- El agente puede entregar una respuesta bonita pero no avanzar el proyecto.

La extensión necesaria es una capa superior que gobierne todas las demás.

### 16.2 Nombre canónico

Canonical Name:
Claude Power Pack Execution OS

Abreviatura:
PP-EOS

Propósito:
Convertir cada interacción de Claude Code en una unidad controlada de ejecución con objetivo, coste, seguridad, evidencia, output y siguiente paso.

### 16.3 Loop central

Todo ciclo debe pasar por este loop:

1. Intent Intake
2. Scope Lock
3. Secret Risk Classification
4. Cost Route Selection
5. Context Pack Assembly
6. Execution Plan
7. Safe Tool Execution
8. Validation Ladder
9. Evidence Packaging
10. Output Amplification
11. Backlog Update
12. Learning Capture
13. Hard Rule Candidate Detection

Nada debería ejecutarse “suelto”.

### 16.4 Execution Packet

Crear un objeto lógico llamado Execution Packet.

Campos:

- execution_id
- timestamp
- project
- owner_prompt
- interpreted_intent
- task_type
- scope
- allowed_files
- forbidden_files
- secret_risk_level
- cost_budget
- model_route
- context_pack_id
- validation_plan
- expected_output_type
- rollback_plan
- done_criteria
- evidence_required
- backlog_update_required
- learning_capture_required

Este Execution Packet no tiene que mostrarse siempre al Owner. Debe existir internamente para evitar drift.

### 16.5 Task Type Taxonomy

Cada petición debe clasificarse como:

- debug
- implement
- review
- refactor
- research
- architecture
- backlog
- governance
- secret_scan
- cost_audit
- prompt_compile
- deploy
- test
- documentation
- demo_readiness
- revenue_readiness
- onboarding
- cleanup
- migration
- monitoring
- rollback

La clasificación determina:
- qué skills se activan,
- qué modelo se usa,
- qué validación mínima se exige,
- qué nivel de secret scanning aplica,
- qué output final se espera.

---

## 17. SECRET-SAFE TOOL EXECUTION LAYER

### 17.1 Problema

La protección de secretos no puede vivir solo al final del flujo. Para ser real, debe envolver cada herramienta, comando, lectura, diff, commit, log y respuesta.

Un secreto puede filtrarse en:
- terminal output,
- logs,
- evidence files,
- screenshots,
- copied prompts,
- commit diffs,
- generated markdown,
- issue reports,
- CI output,
- debugging dumps,
- final answers,
- external subagent context.

### 17.2 Principio

Secret safety must be pre-tool, post-tool and pre-output.

No basta con escanear antes de commit. Hay que escanear:
- antes de leer,
- antes de ejecutar,
- después de ejecutar,
- antes de escribir,
- antes de archivar,
- antes de responder,
- antes de push/deploy.

### 17.3 Secret Risk Levels

Cada tarea debe clasificarse en nivel de riesgo:

#### S0 -- No Secret Risk
Tareas puramente conceptuales o sobre archivos públicos.

Ejemplos:
- README público.
- Documentación sin credenciales.
- Arquitectura abstracta.
- Backlog.

#### S1 -- Low Secret Risk
Puede tocar configuración pero no credenciales.

Ejemplos:
- package.json
- pyproject.toml
- non-sensitive config
- CI template without secrets

#### S2 -- Medium Secret Risk
Puede estar cerca de secretos.

Ejemplos:
- docker-compose
- deployment docs
- environment examples
- integration configs
- webhook docs

#### S3 -- High Secret Risk
Puede contener secretos reales.

Ejemplos:
- .env
- logs
- credentials files
- service accounts
- private keys
- deployment outputs
- database URLs

#### S4 -- Critical Secret Risk
Secreto ya detectado o exposición probable.

Ejemplos:
- git diff contiene token
- terminal output contiene key
- evidence archive contaminado
- secret committed
- secret pushed
- production credential visible

### 17.4 Allowed Behavior by Risk

S0:
- normal execution.

S1:
- lightweight scan before final.

S2:
- scan reads/writes/diffs.

S3:
- redacted reads only.
- no raw output.
- no final quote.
- no evidence raw archive.

S4:
- stop execution.
- redact.
- quarantine.
- incident protocol.
- rotation guidance.

### 17.5 Dangerous Commands Registry

PP debe tener un registro de comandos peligrosos por riesgo de secreto.

Comandos bloqueados o redirigidos a redaction mode:

Unix:
- env
- printenv
- cat .env
- grep -r KEY
- grep -r SECRET
- grep -r TOKEN
- docker inspect
- kubectl describe secret
- kubectl get secret -o yaml
- heroku config
- railway variables
- vercel env pull
- fly secrets list
- aws configure list
- git diff --cached sin scanner posterior

Windows PowerShell:
- Get-ChildItem Env:
- gci env:
- type .env
- Get-Content .env
- Get-Content *.pem
- Get-Content *secret*
- Select-String -Pattern "key|token|secret|password" sin redaction
- docker inspect
- git diff sin scanner posterior

Regla:
Si el objetivo legítimo requiere ejecutar algo parecido, debe envolverse en redaction mode.

### 17.6 Secret-Safe Command Rewrite

Ejemplos de transformación:

No permitido:
cat .env

Permitido:
scan .env and report variable names only, with values redacted.

No permitido:
printenv

Permitido:
list environment variable names only, no values.

No permitido:
git diff

Permitido:
git diff piped through secret scanner before display.

No permitido:
docker inspect container

Permitido:
docker inspect with fields allowlist and redaction on Env.

### 17.7 Secret Allowlist

Algunos archivos pueden contener palabras como key/token sin ser secretos.

Ejemplos:
- documentation explaining API keys.
- fake test fixtures.
- placeholder strings.
- .env.example with dummy values.

Pero allowlist nunca debe aceptar valores reales.

Allowlist fields:
- file_path
- reason
- allowed_patterns
- forbidden_patterns
- expiry
- reviewer

### 17.8 Secret Scanner Output Format

Formato permitido:

SECRET_SCAN_RESULT
status: PASS | FAIL | WARNING
risk_level: S0-S4
files_scanned:
findings:
  - file:
    line:
    type:
    confidence:
    redacted_preview:
    action_required:
raw_values_exposed: false
commit_allowed: true/false
evidence_allowed: true/false

Nunca incluir valor completo.

---

## 18. OUTPUT CONTRACT REGISTRY

### 18.1 Problema

El agente puede entregar outputs inconsistentes según el tipo de tarea.

Para mejorar fidelidad y one-shot, PP necesita un registro de contratos de salida.

### 18.2 Contratos por tipo

#### Debug Contract

Debe incluir:

- Symptom
- Reproduction path
- Root cause
- Fix applied
- Files changed
- Validation run
- Regression risk
- Prevention rule
- Secret scan status
- Next action

#### Implementation Contract

Debe incluir:

- Feature built
- Scope respected
- Files changed
- Design decisions
- Tests run
- Known limitations
- Rollback plan
- Secret scan status
- Backlog updates

#### Review Contract

Debe incluir:

- Findings by severity
- Evidence
- False-positive checks
- Recommended fixes
- No-finding statement if clean
- Secret exposure check

#### Architecture Contract

Debe incluir:

- Current problem
- Proposed structure
- Alternatives rejected
- Tradeoffs
- Migration path
- Validation strategy
- Cost impact
- Maintenance impact
- Security impact

#### Backlog Contract

Debe incluir:

- Top 1 next action
- Top 5 backlog items
- Priority score
- Why now
- Done criteria
- Cost tier
- Risk tier
- Expected unlock

#### Cost Audit Contract

Debe incluir:

- Total token/cost estimate
- Biggest drains
- Waste categories
- Repeated reads
- Expensive decisions
- Recommended savings
- Future hard rules

#### Secret Incident Contract

Debe include:

- Secret type
- Exposure surface
- Location
- Whether raw value was repeated: no
- Rotation needed: yes/no
- Files to clean
- Preventive rule
- Tests to add

### 18.3 No-Completion Without Contract

Hard Rule candidata:
A task cannot be marked complete unless its final response satisfies the output contract for its task type.

---

## 19. PROJECT AUTOPILOT BACKLOG SYSTEM

### 19.1 Objetivo

Cuando el Owner no sabe qué hacer, PP debe actuar como un strategic execution scout.

No debe generar ideas genéricas. Debe mirar el proyecto y encontrar el siguiente movimiento con mayor ROI.

### 19.2 Backlog Generation Inputs

Fuentes internas:

- failing tests
- open TODOs
- warnings
- verify failures
- git status
- recent commits
- stale branches
- stale docs
- missing README
- missing env example
- missing tests
- missing monitoring
- missing onboarding
- missing deployment guide
- missing rollback
- repeated bugs
- manual repeated tasks
- unresolved NEVER_AGAIN entries
- uninstalled hard rules
- unregistered hooks
- unreviewed generated code
- unvalidated workflows
- files with high churn
- files with high complexity
- paths with secret risk
- large files read repeatedly
- commands frequently failing
- project-specific launch blockers

Fuentes estratégicas:

- what makes it sellable
- what makes it demoable
- what makes it safer
- what makes it cheaper
- what makes it more autonomous
- what reduces Owner manual work
- what increases one-shot reliability
- what creates reusable IP
- what converts knowledge into system

### 19.3 Backlog Modes

#### Mode: Launch Readiness

Find tasks that make project ready to launch.

Examples:
- add smoke test
- fix demo blocker
- create deployment checklist
- add rollback
- document setup
- remove secret risk
- verify production config

#### Mode: Revenue Readiness

Find tasks that make project easier to sell.

Examples:
- demo script
- proof page
- before/after evidence
- ROI calculator
- onboarding flow
- case study extraction
- pitch-ready architecture diagram

#### Mode: Reliability Readiness

Find tasks that prevent failure.

Examples:
- tests
- monitors
- health checks
- fail-closed gates
- regression detectors
- rollback paths

#### Mode: Cost Readiness

Find tasks that reduce future Claude/API/computation cost.

Examples:
- cache
- local index
- precomputed context pack
- smaller prompts
- deterministic scanners
- summarized docs
- model routing

#### Mode: Security Readiness

Find tasks that prevent secret leaks.

Examples:
- secret scanner
- .env.example
- gitignore
- redaction wrappers
- pre-commit scanner
- incident docs
- fake secret canary tests

#### Mode: Knowledge Readiness

Find tasks that preserve learning.

Examples:
- convert bug to Hard Rule
- update UKDL
- create KB entry
- create troubleshooting playbook
- add prevention rule
- create project map

### 19.4 Backlog Output Ranking

Priority labels:

P0:
Must do now. Blocks safety, launch, secrets, deploy, or core reliability.

P1:
High leverage. Strongly improves one-shot, cost, reliability or revenue readiness.

P2:
Useful soon. Improves maintainability or reduces friction.

P3:
Nice-to-have. Do only after P0-P2.

Rejected:
Fake progress, unclear ROI, too much scope, no validation.

### 19.5 Backlog Item Example Schema

BACKLOG_ITEM
id:
project:
title:
category:
priority:
why_now:
evidence_source:
impact:
effort:
risk:
cost_tier:
secret_risk:
one_shot_gain:
revenue_gain:
owner_time_saved:
files_likely_touched:
validation:
done_criteria:
rollback:
dependencies:
recommended_prompt_for_claude_code:

### 19.6 Backlog Anti-Hallucination Rule

The backlog engine must not invent repo facts.

Allowed:
- “Detected from file/test/log.”
- “Inferred from missing standard artifact.”
- “Recommended based on project type.”

Not allowed:
- pretending a file exists without checking.
- pretending a test failed without evidence.
- pretending a feature exists.
- inventing business status.
- inventing production metrics.

---

## 20. CLAUDE CODE PROMPT GENERATOR EXTENSION

### 20.1 Problema

The Owner often needs prompts for Claude Code. Bad prompts cause:
- scope drift,
- bad code,
- missing validation,
- expensive execution,
- secret leaks,
- one-shot failure.

PP should generate Claude Code prompts that are strict enough to execute safely.

### 20.2 Prompt Compiler Modes

#### Mode A: Build Prompt

For implementing something.

Must include:
- repo path
- task
- source of truth
- files allowed
- files forbidden
- no secrets rule
- tests
- final output contract

#### Mode B: Debug Prompt

For fixing a bug.

Must include:
- symptom
- reproduction
- constraints
- root-cause-first rule
- no broad refactor
- validation
- prevention rule

#### Mode C: Audit Prompt

For reviewing.

Must include:
- severity table
- evidence required
- false positive check
- no code changes unless asked
- output contract

#### Mode D: Backlog Prompt

For generating next tasks.

Must include:
- inspect repo evidence
- score backlog
- reject busywork
- output top 1 + top 5

#### Mode E: Security Prompt

For scanning secret risk.

Must include:
- redaction only
- no raw secret output
- incident protocol
- commit block if found

#### Mode F: Cost Audit Prompt

For reducing Claude/code cost.

Must include:
- identify repeated work
- propose deterministic replacements
- estimate savings
- add rules

### 20.3 Prompt Compiler Hard Rules

- Never ask Claude Code to print .env values.
- Never ask Claude Code to paste secrets.
- Never ask Claude Code to make broad changes without allowed files.
- Never ask Claude Code to “improve everything.”
- Never ask Claude Code to skip tests.
- Never ask Claude Code to commit without secret scan.
- Never ask Claude Code to use full repo context if a smaller context pack works.
- Never ask Claude Code to refactor unless refactor is the task.

---

## 21. COST-AWARE MODEL ROUTING EXTENSION

### 21.1 Objective

PP should decide not only which skill to activate, but also what model or execution depth is justified.

### 21.2 Routing Factors

- task complexity
- risk level
- number of files
- secret risk
- need for reasoning
- need for code generation
- need for verification
- context size
- project importance
- reversibility
- previous failures
- cost budget

### 21.3 Model Route Classes

#### Route 0 -- Deterministic Only
Use scripts, grep, tests, scanners.
No expensive reasoning.

#### Route 1 -- Cheap Reasoning
Use smaller model or short context.
For simple backlog, summaries, small edits.

#### Route 2 -- Standard Execution
Use normal Claude Code path.
For typical implementation/debug.

#### Route 3 -- High Fidelity
Use stronger reasoning.
For architecture, hard bugs, multi-file changes.

#### Route 4 -- Critical Governance
Use maximum care.
For secrets, deploy, production, irreversible changes.

### 21.4 Route Escalation

Escalate only if:
- deterministic path fails,
- validation fails,
- ambiguity is high risk,
- previous attempt failed,
- production risk is high,
- security risk is high.

### 21.5 Route De-escalation

De-escalate if:
- task is docs-only,
- no code changes,
- no production risk,
- no secrets,
- clear known pattern,
- existing script can solve it.

---

## 22. KNOWLEDGE RETRIEVAL OVER RAW CONTEXT

### 22.1 Problema

Large context wastes tokens and reduces precision.

PP should retrieve the right knowledge, not load everything.

### 22.2 Knowledge Index Types

Create indexes for:

- Hard Rules
- UKDL entries
- NEVER_AGAIN lessons
- CEPS events
- project docs
- commands
- skills
- validation commands
- known bugs
- known file ownership
- secret-sensitive paths
- architecture decisions
- backlog items

### 22.3 Retrieval Contract

For every task, retrieve only:

- top 3 relevant Hard Rules
- top 3 relevant UKDL entries
- top 3 project constraints
- top 3 validation commands
- top 3 risk warnings

If more needed, escalate.

### 22.4 Context Diet Rule

Hard Rule candidata:
Do not load full historical datasets into execution context when a retrieval index can provide the relevant constraints.

---

## 23. SECRET-SAFE KNOWLEDGE CAPTURE

### 23.1 Problema

Learning systems can accidentally preserve secrets forever.

If a secret appears in a bug, CEPS event, session lesson, screenshot, terminal log or evidence file, the learning system may turn a temporary exposure into a permanent leak.

### 23.2 Rule

Learning capture must be redacted by default.

Before writing to:
- UKDL
- NEVER_AGAIN
- session_lessons
- CEPS events
- hard rules
- evidence archive
- cold boot files
- backlog
- markdown docs

Run secret redaction.

### 23.3 Safe Lesson Format

Instead of:
“The Stripe key sk_live_xxx caused...”

Use:
“A live Stripe API key was exposed in [file] at [line]. Raw value redacted. Rotation recommended.”

### 23.4 Secret Memory Prohibition

Hard Rule candidata:
Never store raw secrets in long-term learning systems. Secret-related lessons must preserve pattern, not value.

---

## 24. PROJECT STATE SNAPSHOT

### 24.1 Objective

PP should maintain a lightweight snapshot of each project so that it can generate useful backlog and context without rescanning everything.

### 24.2 Snapshot Fields

PROJECT_STATE_SNAPSHOT
project:
repo_path:
branch:
last_commit:
last_scan:
test_status:
verify_status:
secret_scan_status:
open_backlog_count:
p0_count:
recent_errors:
recent_files_changed:
known_launch_blockers:
known_security_blockers:
known_cost_blockers:
known_one_shot_blockers:
next_recommended_action:
last_owner_intent:
last_successful_task:
last_failed_task:

### 24.3 Snapshot Update Triggers

Update snapshot after:
- task completion
- failed validation
- secret finding
- test run
- commit
- deploy
- rollback
- backlog generation
- hard rule installation
- project audit

### 24.4 Snapshot Use

When Owner asks “what now?”, PP should consult snapshot first, then repo evidence.

---

## 25. OWNER ENERGY MODE

### 25.1 Problema

The best next action depends on Owner energy.

If Owner has low energy, recommending a 6-hour architecture refactor is useless.

### 25.2 Energy Modes

#### Low Energy
Recommend:
- 15-minute task
- review only
- backlog grooming
- one small test
- one doc fix with direct impact
- one secret scan
- one validation command

#### Medium Energy
Recommend:
- 1-hour implementation
- focused bug fix
- small automation
- context pack creation
- demo-readiness improvement

#### High Energy
Recommend:
- deep architecture
- multi-file implementation
- agent design
- hard bug
- launch/deploy preparation

### 25.3 Rule

If energy unknown, default to medium and offer a small first step.

### 25.4 Anti-Burn Principle

PP should not romanticize grinding.

The system should increase output without requiring the Owner to sleep less or manually hold context.

---

## 26. DEMO-READINESS ENGINE

### 26.1 Problema

Many projects become technically impressive but hard to demo.

A project that cannot be demoed is harder to sell, fund, validate or explain.

### 26.2 Demo Readiness Checklist

- Can it run from clean setup?
- Is there a single command or clear flow?
- Is there sample data?
- Are secrets excluded?
- Is there a demo script?
- Is there a before/after?
- Is there visual evidence?
- Is there a failure-safe path?
- Is there a short explanation?
- Is there proof of value?
- Can the Owner record a clip today?

### 26.3 Demo Blocker Categories

- setup blocker
- visual blocker
- data blocker
- auth blocker
- performance blocker
- UX blocker
- explanation blocker
- reliability blocker
- secret risk blocker

### 26.4 Backlog Priority

Demo blockers should rank high when:
- project is close to presentation,
- Owner needs to show progress,
- sales/funding depends on proof,
- content creation depends on recordable clips.

---

## 27. REVENUE-READINESS ENGINE

### 27.1 Objective

PP should identify tasks that move a project closer to money.

This does not mean always building sales pages. It means finding the technical or operational bottleneck blocking monetization.

### 27.2 Revenue Readiness Questions

- Can someone understand the value in 30 seconds?
- Can someone see proof?
- Can someone try it?
- Can someone buy it?
- Can someone onboard?
- Can the Owner explain ROI?
- Can the system operate without fragile manual work?
- Can the demo survive scrutiny?
- Is there a clear target user?
- Is there a clear transformation?

### 27.3 Revenue Backlog Categories

- proof asset
- demo asset
- onboarding asset
- pricing support
- ROI calculator
- case study extraction
- reliability hardening
- deployment readiness
- user journey cleanup
- sales narrative
- lead magnet
- internal ops automation

### 27.4 Rule

If two tasks have similar technical value, prioritize the one that makes the project easier to sell, demo or validate.

---

## 28. VERIFICATION-OR-NO-CLAIM RULE

### 28.1 Problema

Agents often say things are fixed without evidence.

### 28.2 Rule

No claim without evidence.

Allowed:
- “Tests passed: command X.”
- “Static scan found no secrets.”
- “File Y changed at section Z.”
- “Could not verify because...”
- “Partial completion.”

Forbidden:
- “Should work.”
- “Likely fixed.”
- “Everything is good.”
- “Production ready” without deploy/runtime evidence.
- “No secrets” without scan.
- “Validated” without command/output.

### 28.3 Evidence Strength Levels

E0:
No evidence. Claim not allowed.

E1:
Static reasoning.

E2:
File inspection.

E3:
Static tool/linter.

E4:
Unit test.

E5:
Integration/smoke test.

E6:
Runtime proof.

E7:
Production/real-user proof.

### 28.4 Final Output Requirement

Every final report should label evidence strength.

---

## 29. CASCADE PREVENTION EXPANSION

### 29.1 Problema

A bug rarely stays isolated. One bad assumption creates multiple failures.

PP already has CEPS and cascade guard, but it can be expanded.

### 29.2 Cascade Types

- Secret leak cascade
- Cost explosion cascade
- Scope drift cascade
- Test failure cascade
- Deployment cascade
- Context stale cascade
- Naming drift cascade
- Prompt ambiguity cascade
- Tool output misread cascade
- Cross-project contamination cascade

### 29.3 Cascade Trigger Examples

Secret leak cascade:
.env printed → terminal log contaminated → evidence archive contaminated → final response repeats secret.

Cost explosion cascade:
full repo scan → repeated file reads → subagent invoked → long summary → no artifact.

Scope drift cascade:
small bug fix → refactor → tests break → more fixes → original task incomplete.

Prompt ambiguity cascade:
unclear task → wrong assumption → wrong files touched → validation irrelevant.

### 29.4 Cascade Response

When cascade detected:
1. Stop expansion.
2. Identify root trigger.
3. Freeze current scope.
4. Validate current damage.
5. Propose smallest safe correction.
6. Add CEPS event.
7. Add Hard Rule candidate if repeated.

---

## 30. FILE SENSITIVITY MAP

### 30.1 Objective

PP should maintain a map of file sensitivity by project.

### 30.2 Sensitivity Classes

PUBLIC:
Safe docs, README, examples.

INTERNAL:
Architecture, backlog, implementation docs.

CODE:
Source files.

CONFIG:
Configuration without secrets.

SECRET_ADJACENT:
Could contain secret references.

SECRET_BEARING:
May contain real secrets.

GENERATED:
Build artifacts, logs, reports.

EVIDENCE:
Test results, screenshots, audit logs.

### 30.3 Handling by Class

PUBLIC:
Normal.

INTERNAL:
Normal but avoid unnecessary exposure.

CODE:
Run UQF/code review.

CONFIG:
Scan before output/commit.

SECRET_ADJACENT:
Redacted inspection.

SECRET_BEARING:
Fail-closed.

GENERATED:
Check for accidental secret echo.

EVIDENCE:
Must be sanitized before storage.

### 30.4 Use Cases

- Prevent reading secret files raw.
- Prevent committing contaminated logs.
- Prioritize scanning high-risk files.
- Avoid wasting tokens on generated artifacts.
- Build safer context packs.

---

## 31. COMMAND DISCOVERY EXTENSION

### 31.1 Problema

The dataset base notes that slash commands exist but are not auto-discovered by intent.

This reduces leverage because the Owner must remember command names.

### 31.2 Solution

Add Command Discovery Layer.

When Owner intent matches a command, PP should suggest or route to:
- /code-review
- /audit-all
- /deploy
- /rollback
- /auto-test
- /distill
- /compound
- /resume
- /pre-compact
- /speckit tasks
- /arch-decision
- /cpp-deep-research

### 31.3 Command Metadata Schema

COMMAND_REGISTRY_ENTRY
name:
description:
intent_patterns:
risk_level:
secret_risk:
cost_tier:
requires_confirmation:
validation_output:
related_skills:
forbidden_contexts:

### 31.4 Rule

If a command already solves the Owner’s intent, prefer command route over ad-hoc reasoning.

---

## 32. SKILL SELECTION QUALITY GATE

### 32.1 Problema

Auto-activating too many skills creates noise and cost.

Activating too few reduces quality.

### 32.2 Skill Activation Score

Score based on:
- intent match
- file type match
- project match
- risk match
- past usefulness
- cost impact
- redundancy with other skills
- whether skill has validation path

### 32.3 Max Skills Rule

Default:
- maximum 3 skills per task.

Exception:
- architecture/deep audit can use more if justified.

### 32.4 Redundant Skill Block

If two skills provide overlapping guidance, choose the more project-specific one.

Example:
For KobiiCraft Java plugin bug:
prefer kobiicraft-debug + java-architect over generic debugging-wizard unless needed.

---

## 33. HUMAN-READABLE EXECUTION RECEIPT

### 33.1 Objective

At the end of meaningful work, Owner should receive a short receipt that allows trust without reading all logs.

### 33.2 Receipt Format

EXECUTION_RECEIPT
task:
status:
files_changed:
commands_run:
tests:
secret_scan:
evidence:
risks:
next_best_action:

### 33.3 Receipt Rules

- No raw secrets.
- No huge logs.
- No fake confidence.
- No “done” without validation.
- If partial, say partial.

---

## 34. FUTURE COMMANDS TO ADD

### 34.1 /what-now

Purpose:
Generate next-best-action backlog from project state.

Output:
- best next task
- why now
- evidence
- done criteria
- prompt for Claude Code

### 34.2 /secret-scan

Purpose:
Scan current repo or changed files for secrets.

Output:
- redacted findings
- commit allowed yes/no
- rotation required yes/no

### 34.3 /cost-autopsy

Purpose:
Analyze latest session/token waste.

Output:
- drains
- waste categories
- savings recommendations
- hard rule candidates

### 34.4 /one-shot-compile

Purpose:
Convert vague Owner task into strict Claude Code prompt.

Output:
- execution prompt
- constraints
- validation
- secret rules
- stop conditions

### 34.5 /demo-ready

Purpose:
Check if project can be demoed or recorded.

Output:
- blockers
- proof gaps
- shortest path to demo

### 34.6 /revenue-ready

Purpose:
Check if project is closer to monetization.

Output:
- sales blockers
- proof assets needed
- onboarding gaps
- next revenue task

### 34.7 /context-pack

Purpose:
Create minimal task-specific context pack.

Output:
- relevant files
- relevant rules
- validation commands
- forbidden files
- secret risks

### 34.8 /output-score

Purpose:
Score final output quality.

Output:
- OQS
- missing fields
- improvement suggestions

---

## 35. IMPLEMENTATION PRIORITY FOR PP

### 35.1 P0

1. Secret Firewall detector.
2. Pre-output redactor.
3. Git diff secret scanner.
4. Evidence sanitizer.
5. Dangerous command guard.
6. Fake secret canary tests.
7. HR-SECRET rules.

Reason:
A single leaked credential is catastrophic.

### 35.2 P1

1. One-Shot Contract.
2. Output Contract Registry.
3. Execution Receipt.
4. Fidelity Lock.
5. Verification-or-No-Claim Rule.

Reason:
Improves trust and one-shot reliability immediately.

### 35.3 P2

1. /what-now command.
2. Project State Snapshot.
3. Backlog scoring.
4. Demo-readiness engine.
5. Revenue-readiness engine.

Reason:
Keeps projects moving when Owner lacks ideas.

### 35.4 P3

1. Cost Collapse Layer.
2. Cost autopsy.
3. Repeated read detector.
4. Model route classes.
5. Context Pack budget.

Reason:
Reduces long-term operating cost.

### 35.5 P4

1. Command discovery.
2. Skill selection scoring.
3. Knowledge retrieval indexes.
4. Cascade prevention expansion.
5. File sensitivity map.

Reason:
Improves system intelligence and reduces manual orchestration.

---

## 36. FINAL CANONICAL PRINCIPLES

### 36.1 Secret Safety Over Everything

If secret safety conflicts with cost, speed, convenience, evidence or automation, secret safety wins.

### 36.2 Evidence Over Confidence

The agent must not sound certain when it has not verified.

### 36.3 Cheap Path Before Expensive Path

Deterministic local checks beat expensive reasoning when they answer the question.

### 36.4 Scope Fidelity Over Cleverness

Do exactly what the Owner asked unless a safety issue requires stopping.

### 36.5 Backlog From Reality, Not Imagination

Next tasks must come from repo evidence, project state or explicit strategic goal.

### 36.6 Output Must Become an Asset

A good output should leave behind a decision, rule, test, backlog item, prompt, evidence file or reusable system.

### 36.7 One-Shot Means Fewer Repair Cycles

The system should optimize for correct first execution, not impressive recovery.

### 36.8 No Raw Secrets in Long-Term Memory

Learning systems preserve patterns, not credentials.

### 36.9 Momentum Is a Feature

A project should always have a next action that moves it closer to sale, launch, reliability, safety, automation or lower cost.

### 36.10 The Power Pack Is an Execution Governor

Claude Power Pack is not just a skill pack. It is the governance layer that makes Claude Code safer, cheaper, more faithful and more useful.

END OF PART II.
