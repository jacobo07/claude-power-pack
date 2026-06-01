# PP Dataset -- Implementation Blueprint

**Source:** PP_DATASET_20260531T122242Z (1).md, lines 8396-10303
**Dataset part:** Part VII
**Ingested:** 2026-06-01 (BL-DATASET-001 M0)
**Lines in this file:** 1908

---

Continuación directa. La Parte VII baja todo esto a diseño de implementación sobre el PP actual, que ya tiene Hard Rules, CEPS, NEVER_AGAIN, hooks, TIS/TCO, skills y commands como base operativa. 

# CLAUDE POWER PACK -- EXTENSION DATASET PART VII
# Implementation Blueprint: Secret Firewall, Cascade Prevention, Cost Collapse, One-Shot Compiler, Backlog Autopilot

## 121. IMPLEMENTATION BLUEPRINT LAYER

### 121.1 Propósito

Esta parte convierte las extensiones anteriores en un blueprint implementable por Claude Code.

El objetivo no es añadir teoría, sino definir:
- módulos concretos,
- archivos sugeridos,
- comandos,
- hooks,
- tests,
- gates,
- schemas,
- criterios de aceptación,
- orden de implementación,
- hard rules candidatas,
- owner-side actions.

### 121.2 Principio

No extension is real until it has:
- module,
- command,
- test,
- verification probe,
- output contract,
- secret handling,
- cascade handling,
- cost handling,
- backlog integration,
- documentation,
- failure mode.

### 121.3 Implementation Rule

Toda nueva capacidad del PP debe pasar por:

1. Design
2. Minimal implementation
3. Tests
4. Secret scanner compatibility
5. verify probe
6. CEPS integration
7. NEVER_AGAIN learning path
8. Hard Rule candidate path
9. Command or hook exposure
10. Owner-facing documentation

---

## 122. PROPOSED MODULE MAP

### 122.1 Objetivo

Crear una estructura clara para que el Power Pack no siga creciendo como monolito.

### 122.2 Nuevos módulos sugeridos

```text
modules/
  secret_firewall/
    __init__.py
    detector.py
    redactor.py
    classifier.py
    command_guard.py
    diff_scanner.py
    evidence_sanitizer.py
    learning_sanitizer.py
    incident.py
    rotation.py
    fixtures.py

  cascade_prevention/
    __init__.py
    model.py
    detector.py
    premortem.py
    containment.py
    blast_radius.py
    root_cause_library.py
    ceps_bridge.py
    hardrule_bridge.py
    backlog_bridge.py

  output_contracts/
    __init__.py
    registry.py
    validator.py
    receipt.py
    evidence_levels.py
    output_score.py

  cost_collapse/
    __init__.py
    pretask_contract.py
    repeated_read_detector.py
    cost_firebreak.py
    route_selector.py
    autopsy.py
    context_pack_budget.py

  one_shot/
    __init__.py
    compiler.py
    fidelity_lock.py
    assumption_ledger.py
    scope_guard.py
    validation_ladder.py
    failure_log.py

  backlog_autopilot/
    __init__.py
    harvester.py
    scorer.py
    pruner.py
    next_best_action.py
    money_mode.py
    breakage_mode.py
    time_saving_mode.py
    demo_readiness.py
    revenue_readiness.py

  project_state/
    __init__.py
    snapshot.py
    freshness.py
    sensitivity_map.py
    handoff.py
    progress_proof.py

  execution_os/
    __init__.py
    packet.py
    safety_envelope.py
    autonomy_ladder.py
    checkpoint.py
    clean_failure.py

122.3 Regla de modularidad

Si una capacidad:

toca secretos,

escribe learning,

genera evidencia,

modifica backlog,

afecta coste,

puede bloquear ejecución,


entonces no debe vivir dentro de un único script gigante. Debe tener módulo propio y tests propios.


---

123. COMMAND MAP TO ADD

123.1 Propósito

Exponer las capacidades nuevas mediante comandos claros.

123.2 Nuevos slash commands sugeridos

/secret-scan
/secret-incident
/secret-rotate-guide
/cascade-scan
/cascade-autopsy
/cascade-prevent
/cost-autopsy
/cost-firebreak
/one-shot-compile
/output-score
/what-now
/backlog-harvest
/backlog-prune
/demo-ready
/revenue-ready
/context-pack
/project-snapshot
/progress-proof
/diff-hygiene
/handoff-safe

123.3 Command Requirements

Cada command debe declarar:

COMMAND_SPEC name: purpose: inputs: outputs: secret_risk: cost_risk: cascade_risk: requires_repo: requires_git: can_write: can_commit: owner_approval_required: validation: failure_mode:

123.4 Command Discovery Integration

El dataset base ya identifica que existen comandos globales pero falta auto-discovery por intent. Esta extensión debe conectar los nuevos comandos al futuro Command Discovery Layer para no depender de memoria manual del Owner.


---

124. HOOK MAP TO ADD

124.1 Propósito

No todo debe depender de comandos manuales. Algunas protecciones deben ejecutarse como hooks.

124.2 Hooks sugeridos

Hook 1: secret-pre-tool-guard

Event: PreToolUse

Aplica a:

Bash

Read

Write

Edit

MultiEdit


Función: Bloquear o redirigir acciones que puedan imprimir, leer o escribir secretos raw.

Hook 2: secret-post-tool-redactor

Event: PostToolUse

Función: Escanear stdout/stderr y tool result. Si detecta secreto, redacción/cuarentena.

Hook 3: diff-hygiene-pre-commit

Event: PreToolUse Bash

Trigger: git commit git push

Función: Escanear staged diff, generated files, evidence, logs y secretos antes de commit/push.

Hook 4: output-contract-stop-check

Event: Stop

Función: Revisar si el output final satisface contrato mínimo: evidence, secret status, risks, next action.

Hook 5: cost-firebreak-hook

Event: PostToolUse

Función: Detectar repeated reads, repeated failed commands, full repo scans y escalada de coste.

Hook 6: cascade-risk-pre-tool

Event: PreToolUse

Función: Detectar acciones con alto cascade risk: global config, deploy, secrets, learning systems, hard rules.

Hook 7: backlog-harvest-stop

Event: Stop

Función: Si se detectó riesgo no resuelto, crear backlog item sugerido.

124.3 Hook Rule

Los hooks de seguridad de secretos deben ser fail-closed.

Los hooks de coste y backlog pueden ser advisory/fail-open.

Los hooks de deploy, secret, commit y learning contamination deben bloquear cuando el riesgo sea crítico.


---

125. SECRET FIREWALL IMPLEMENTATION SPEC

125.1 Objetivo

Implementar la primera versión real del Secret Firewall.

125.2 Minimal Viable Secret Firewall

MVP debe incluir:

1. Provider regex detector.


2. Generic entropy detector.


3. Contextual key-value detector.


4. Redactor.


5. Diff scanner.


6. Evidence sanitizer.


7. Final response scanner.


8. Dangerous command guard.


9. Fake secret fixtures.


10. CLI command /secret-scan.



125.3 detector.py

Responsabilidad: Detectar secretos.

Funciones:

detect_secrets(text, source=None, mode="standard") -> SecretScanResult
detect_file(path, redacted=True) -> SecretScanResult
detect_diff(diff_text) -> SecretScanResult
detect_command_output(stdout, stderr) -> SecretScanResult

Tipos detectados:

OPENAI_KEY

ANTHROPIC_KEY

STRIPE_KEY

GITHUB_TOKEN

AWS_ACCESS_KEY

GOOGLE_PRIVATE_KEY

TELEGRAM_BOT_TOKEN

DISCORD_WEBHOOK

SUPABASE_JWT

DATABASE_URL

JWT

BEARER_TOKEN

COOKIE

PRIVATE_KEY_BLOCK

GENERIC_HIGH_ENTROPY_SECRET


125.4 redactor.py

Responsabilidad: Reemplazar secretos por placeholders seguros.

Formato: [REDACTED_SECRET_TYPE_LAST4_abcd]

Nunca:

base64,

reversible encryption,

hidden raw value,

full secret in metadata.


125.5 command_guard.py

Responsabilidad: Interceptar comandos peligrosos.

Debe detectar:

cat .env

type .env

Get-Content .env

printenv

env

Get-ChildItem Env:

docker inspect

kubectl get secret

git diff before scan

heroku config

vercel env pull

railway variables


Acciones:

block

rewrite suggestion

allow with redaction

require owner-side local action


125.6 diff_scanner.py

Responsabilidad: Escanear:

git diff

git diff --cached

untracked sensitive files

generated evidence files

logs

screenshots metadata if available


125.7 evidence_sanitizer.py

Responsabilidad: Garantizar que nada en vault/test-results/, reports, cold boot evidence, audit cache o generated docs contenga secretos raw.

125.8 incident.py

Responsabilidad: Clasificar blast radius y generar guía de respuesta.

No debe repetir el secreto.

125.9 Acceptance Criteria

SECRET_FIREWALL_MVP_PASS si:

fake OpenAI key detectada y redacted.

fake Stripe live key detectada y redacted.

fake GitHub token detectado en git diff.

fake .env dump bloqueado.

fake private key block bloqueado.

final response scanner redacts.

evidence sanitizer removes raw value.

learning sanitizer prevents raw value entering UKDL/NEVER_AGAIN.

no false raw value appears in test output.

all tests pass.



---

126. CASCADE PREVENTION IMPLEMENTATION SPEC

126.1 Objetivo

Convertir cascade prevention en módulo ejecutable.

126.2 MVP

MVP debe incluir:

1. CascadeRecord schema.


2. Root cause classifier.


3. Blast radius classifier.


4. Cascade pre-mortem generator.


5. Containment report.


6. CEPS bridge.


7. Hard Rule candidate bridge.


8. Backlog bridge.


9. CLI /cascade-autopsy.


10. Tests con cascadas sintéticas.



126.3 model.py

Define:

CascadeRecord
CascadeSeverity
BlastRadius
ContaminatedSurface
PropagationPath
ContainmentAction

126.4 detector.py

Detecta patrones como:

secret in output

repeated command failure

scope drift

test pollution

learning contamination

deploy without verify

stale context acting

output claim without evidence

repeated read cost cascade


126.5 premortem.py

Genera pre-mortem para tareas high-risk.

Debe devolver:

possible root failures

propagation paths

secret risk

cost risk

scope risk

containment plan

stop conditions


126.6 containment.py

Cuando detecta cascade:

freeze scope,

stop tool expansion,

identify contaminated surfaces,

choose smallest safe correction,

create report,

push CEPS event,

propose backlog item.


126.7 ceps_bridge.py

Amplía CEPS sin romper schema existente.

Si no se puede modificar CEPS todavía:

guardar cascade sidecar en vault/cascades/cascade_records.jsonl

enlazar con CEPS event ID.


126.8 hardrule_bridge.py

Convierte cascadas C3+ o secret cascades en hard rule candidates.

126.9 Acceptance Criteria

CASCADE_MVP_PASS si:

detecta secret leak cascade sintética.

detecta cost cascade sintética por repeated reads.

detecta scope drift cascade.

detecta test artifact pollution.

genera CascadeRecord.

genera containment report.

genera hard rule candidate.

genera backlog item.

no raw secrets en cascade record.

CEPS bridge escribe evento válido.



---

127. COST COLLAPSE IMPLEMENTATION SPEC

127.1 Objetivo

Reducir coste real de sesiones largas y evitar repetir trabajo.

127.2 MVP

1. Pre-task cost contract.


2. Repeated read detector.


3. Cost firebreak.


4. Cost autopsy.


5. Context pack budget.


6. Route selector.


7. CLI /cost-autopsy.


8. CLI /cost-firebreak.



127.3 repeated_read_detector.py

Detectar:

mismo archivo leído 3+ veces,

misma búsqueda repetida,

mismo comando fallido repetido,

full repo scan sin artifact posterior,

long output sin summary.


127.4 cost_firebreak.py

Si se activa:

summarize facts,

identify missing fact,

propose cheapest next action,

suggest context artifact,

optionally create backlog item.


127.5 route_selector.py

Rutas:

R0 deterministic R1 cheap reasoning R2 standard R3 high fidelity R4 critical governance

127.6 Cost Evidence

Cada cost autopsy debe incluir:

repeated reads,

expensive commands,

long outputs,

wasted loops,

suggested index,

suggested hard rule,

estimated future savings.


127.7 Acceptance Criteria

COST_COLLAPSE_MVP_PASS si:

detects repeated file reads,

detects repeated failed command,

suggests compact context artifact,

identifies expensive route,

outputs cost autopsy,

creates backlog item for repeated cost source,

no secrets in cost logs.



---

128. ONE-SHOT COMPILER IMPLEMENTATION SPEC

128.1 Objetivo

Crear /one-shot-compile para convertir instrucciones vagas en prompts ejecutables por Claude Code.

128.2 MVP

Inputs:

Owner request

project path optional

task type optional

risk level optional


Outputs:

Claude Code prompt

constraints

non-goals

allowed files

forbidden files

validation

secret rules

cost rules

stop conditions

output contract


128.3 compiler.py

Debe producir:

ONE_SHOT_PROMPT mission: repo: source_of_truth: scope: allowed_actions: forbidden_actions: secret_policy: cost_policy: validation: rollback: output_contract: stop_conditions: final_receipt_format:

128.4 fidelity_lock.py

Debe bloquear:

broad refactor,

naming drift,

dependency changes,

unrelated cleanup,

production deploy,

global config edit,

raw secret printing.


128.5 assumption_ledger.py

Debe marcar:

assumptions,

confidence,

risk if wrong,

verification needed.


128.6 Acceptance Criteria

ONE_SHOT_MVP_PASS si:

vague request becomes scoped prompt.

secret policy included.

stop conditions included.

validation included.

output contract included.

no raw secrets included.

broad scope is constrained.

high-risk assumptions are labeled.



---

129. BACKLOG AUTOPILOT IMPLEMENTATION SPEC

129.1 Objetivo

Crear sistema que responda “qué hago ahora” desde evidencia real.

129.2 MVP

1. Backlog harvester.


2. Priority scorer.


3. Next-best-action engine.


4. Backlog pruner.


5. Demo readiness mode.


6. Revenue readiness mode.


7. Breakage mode.


8. Time-saving mode.


9. CLI /what-now.


10. CLI /backlog-harvest.



129.3 harvester.py

Fuentes:

git status

failing tests

TODOs

verify failures

CEPS

NEVER_AGAIN

cascade records

secret findings

cost autopsy

stale docs

missing .env.example

missing tests

unregistered hooks

repeated manual commands


129.4 scorer.py

Priority Score:

priority =
  revenue_value * 3
+ demo_value * 3
+ reliability_gain * 3
+ secret_risk_reduction * 4
+ cascade_risk_reduction * 4
+ cost_reduction * 2
+ one_shot_gain * 2
+ owner_time_saved * 2
- effort * 1
- implementation_risk * 2
- scope_creep_risk * 3

129.5 next_best_action.py

Debe devolver:

NEXT_BEST_ACTION task: why_now: evidence: state_delta: smallest_first_step: done_criteria: validation: risk_if_ignored: prompt_for_claude_code:

129.6 pruner.py

Debe eliminar:

duplicates,

stale items,

vague items,

cosmetic-only tasks,

no-evidence tasks,

already solved tasks.


129.7 Acceptance Criteria

BACKLOG_AUTOPILOT_MVP_PASS si:

generates next best action from repo state.

rejects generic busywork.

includes done criteria.

includes validation.

includes evidence.

includes Claude Code prompt.

prioritizes secret/cascade risks above cosmetic work.

deduplicates repeated items.



---

130. OUTPUT CONTRACT IMPLEMENTATION SPEC

130.1 Objetivo

Garantizar que cada respuesta final de Claude Code sea confiable.

130.2 MVP

1. Output contract registry.


2. Output validator.


3. Execution receipt.


4. Evidence strength labels.


5. Output score.


6. Stop hook integration.



130.3 registry.py

Contratos:

debug

implementation

review

architecture

backlog

cost audit

secret incident

deploy

rollback

research

prompt compile


130.4 receipt.py

Formato:

EXECUTION_RECEIPT status: task: files_changed: commands_run: validation: secret_scan: cascade_risk: cost_notes: evidence: remaining_risks: next_action:

130.5 evidence_levels.py

E0 no evidence E1 reasoning E2 file inspection E3 static tool E4 unit test E5 integration test E6 runtime proof E7 production proof

130.6 output_score.py

Score dimensions:

answered request

evidence

actionability

safety

concision

next action

no unsupported claims

no raw secrets

output contract match


130.7 Acceptance Criteria

OUTPUT_CONTRACT_MVP_PASS si:

detects missing evidence.

detects unsupported “done”.

detects missing secret scan status.

detects missing next action.

detects task type mismatch.

generates execution receipt.

blocks or flags unsafe final output.



---

131. PROJECT STATE IMPLEMENTATION SPEC

131.1 Objetivo

Mantener snapshots para reducir coste y mejorar continuidad.

131.2 MVP

1. Project snapshot.


2. Sensitivity map.


3. Freshness tags.


4. Progress proof.


5. Safe handoff.



131.3 snapshot.py

PROJECT_STATE_SNAPSHOT:

project

repo_path

branch

last_commit

tests_status

verify_status

secret_scan_status

open_cascade_count

open_backlog_count

top_risks

next_best_action

last_successful_task

last_failed_task


131.4 sensitivity_map.py

Clasificar:

PUBLIC

INTERNAL

CODE

CONFIG

SECRET_ADJACENT

SECRET_BEARING

GENERATED

EVIDENCE


131.5 freshness.py

F0 current filesystem F1 current git F2 current test F3 recent session F4 old memory F5 assumption

131.6 handoff.py

HANDOFF_PACKET:

completed

not completed

files changed

validations

secret status

cascade status

next action

resume prompt


131.7 Acceptance Criteria

PROJECT_STATE_MVP_PASS si:

snapshot generated.

sensitivity map generated.

stale context labeled.

handoff contains no raw secrets.

next action included.

progress proof record generated.



---

132. VERIFICATION PROBES TO ADD

132.1 Objetivo

Cada nueva capability necesita verify probe.

132.2 Nuevos probes

tools/verify_secret_firewall.py
tools/verify_cascade_prevention.py
tools/verify_cost_collapse.py
tools/verify_one_shot_compiler.py
tools/verify_backlog_autopilot.py
tools/verify_output_contracts.py
tools/verify_project_state.py

132.3 verify_spp integration

Añadir rows futuras:

secret-firewall

cascade-prevention-v2

cost-collapse

one-shot-compiler

backlog-autopilot

output-contracts

project-state


132.4 Probe Output Standard

Cada probe debe emitir:

<PROBE_NAME>_PROBE = N/M

Ejemplo:

SECRET_FIREWALL_PROBE = 12/12

132.5 Rule

No module is complete until its verify probe can run independently.


---

133. TEST SUITES TO ADD

133.1 Unit tests

tests/test_secret_firewall.py
tests/test_secret_redactor.py
tests/test_secret_command_guard.py
tests/test_cascade_prevention.py
tests/test_cost_collapse.py
tests/test_one_shot_compiler.py
tests/test_backlog_autopilot.py
tests/test_output_contracts.py
tests/test_project_state.py

133.2 Integration tests

tests/integration/test_secret_to_evidence_pipeline.py
tests/integration/test_cascade_to_hardrule_pipeline.py
tests/integration/test_backlog_from_cascade_pipeline.py
tests/integration/test_cost_firebreak_pipeline.py
tests/integration/test_one_shot_to_output_contract_pipeline.py

133.3 Canary tests

Secret canaries:

fake OpenAI key

fake Anthropic key

fake Stripe key

fake GitHub token

fake private key

fake DB URL

fake JWT

fake Telegram token


Cascade canaries:

test artifact pollution

scope drift

repeated reads

unsupported done claim

stale context

secret in evidence


133.4 Rule

Tests must prove not only detection, but non-propagation.


---

134. OWNER-SIDE REGISTRATION PLAN

134.1 Problema

El dataset base ya documenta que ciertas acciones globales requieren Owner-side script por classifier policy.

134.2 Required Owner-side scripts

tools/register_secret_hooks.py
tools/register_cascade_hooks.py
tools/register_output_contract_hooks.py
tools/register_cost_hooks.py
tools/register_backlog_commands.py

134.3 Script requirements

Cada script debe:

support --dry-run,

backup settings.json,

be idempotent,

print markers,

avoid raw secrets,

validate JSON after write,

show rollback path.


134.4 Owner-side Output

OWNER_REGISTRATION_REPORT script: dry_run: changes_planned: backup_path: markers_added: validation: rollback: restart_required:


---

135. IMPLEMENTATION ORDER

135.1 Phase 0 -- Safety Baseline

Implementar primero:

1. secret detector


2. redactor


3. final response scanner


4. evidence sanitizer


5. diff scanner


6. fake secret tests



No avanzar a autonomía hasta esto.

135.2 Phase 1 -- Secret Firewall Hooks

1. dangerous command guard


2. pre-tool secret guard


3. post-tool redactor


4. git commit/push scanner


5. learning sanitizer



135.3 Phase 2 -- Output Contracts

1. execution receipt


2. output validator


3. evidence levels


4. unsupported claim detector


5. Stop hook advisory/blocker



135.4 Phase 3 -- Cascade Prevention

1. CascadeRecord


2. premortem


3. containment


4. CEPS bridge


5. hardrule bridge


6. backlog bridge



135.5 Phase 4 -- Cost Collapse

1. repeated read detector


2. cost firebreak


3. cost autopsy


4. context pack budget


5. route selector



135.6 Phase 5 -- One-Shot Compiler

1. prompt compiler


2. fidelity lock


3. assumption ledger


4. validation ladder


5. failure log



135.7 Phase 6 -- Backlog Autopilot

1. harvester


2. scorer


3. next-best-action


4. pruner


5. demo/revenue/breakage modes



135.8 Phase 7 -- Project State

1. snapshot


2. sensitivity map


3. freshness tags


4. progress proof


5. safe handoff




---

136. ACCEPTANCE GATES BY PHASE

136.1 Phase 0 Gate

Pass if:

no fake secret leaks in test output,

redactor works,

evidence sanitizer works,

final response scanner works,

diff scanner blocks fake secret.


136.2 Phase 1 Gate

Pass if:

dangerous commands blocked or rewritten,

hooks can run fail-closed for secrets,

learning sanitizer blocks raw secret,

commit scanner blocks raw secret.


136.3 Phase 2 Gate

Pass if:

unsupported done claims flagged,

missing evidence flagged,

missing secret status flagged,

execution receipt generated.


136.4 Phase 3 Gate

Pass if:

cascade record created,

containment report created,

CEPS bridge works,

hard rule candidate generated,

backlog item generated.


136.5 Phase 4 Gate

Pass if:

repeated read detected,

cost firebreak triggers,

autopsy generated,

cheaper route suggested.


136.6 Phase 5 Gate

Pass if:

vague prompt becomes scoped,

non-goals included,

stop conditions included,

validation included,

secret policy included.


136.7 Phase 6 Gate

Pass if:

/what-now returns evidence-backed task,

busywork rejected,

priority score computed,

prompt for Claude Code generated.


136.8 Phase 7 Gate

Pass if:

snapshot generated,

stale context marked,

handoff generated,

no secrets in handoff.



---

137. NEW HARD RULE SET: IMPLEMENTATION CANDIDATES

HR-SECRET-FW-001

All output paths must pass through redaction before being stored, shown, committed or used for learning.

HR-SECRET-FW-002

Commands that dump environment variables or credential files must be blocked or executed only through redaction mode.

HR-SECRET-FW-003

No evidence artifact may be written until secret scan passes or redaction is applied.

HR-CASCADE-IMPL-001

If a bug affects more than one surface, create CascadeRecord before marking fixed.

HR-CASCADE-IMPL-002

If a test artifact triggers production learning, quarantine it and block hard rule promotion.

HR-COST-IMPL-001

If the same file is read three times in one task, create or use a context artifact before reading again.

HR-OUTPUT-IMPL-001

Final output must not claim completion without matching evidence level.

HR-BACKLOG-IMPL-001

A backlog item without evidence, done criteria and validation must be rejected or rewritten.

HR-ONESHOT-IMPL-001

High-risk tasks require One-Shot Contract before multi-file edits.

HR-PROJECTSTATE-IMPL-001

Handoff packets must include secret status, validation status, next action and unresolved risks.


---

138. CLAUDE CODE MASTER PROMPT FOR IMPLEMENTING PART VII

138.1 Purpose

Este prompt debe usarse para Claude Code cuando se quiera implementar esta Parte VII.

138.2 Prompt

Act as the implementation engineer for the Claude Power Pack repository.

MISSION: Implement the next safe slice of the Claude Power Pack Extension Part VII.

SOURCE OF TRUTH: Use the current repository on disk as truth. Do not rely on memory if files differ.

NON-NEGOTIABLES:

Do not print, log, store, commit, or expose raw secrets.

Do not read .env or credential files raw.

Do not modify ~/.claude/settings.json directly unless using an Owner-side registration script with --dry-run, backup, idempotent merge and validation.

Do not refactor unrelated modules.

Do not introduce dependencies unless justified.

Do not mark complete without tests or explicit limitation.

Do not allow test artifacts to enter production learning or hard rules.

Do not create broad architecture rewrites.


TASK: Implement only the smallest safe vertical slice from the selected phase.

REQUIRED FLOW:

1. Inspect repo structure.


2. Identify existing modules to reuse.


3. Create or update only files needed for the selected slice.


4. Add tests first or alongside implementation.


5. Run targeted tests.


6. Run relevant verify probe if exists.


7. Run secret scan if implemented.


8. Produce execution receipt.



SECRET POLICY: All generated outputs, evidence, logs and test artifacts must be safe. Use fake secrets only in clearly marked fixtures. Never include real credentials.

OUTPUT CONTRACT: Return:

files changed,

tests run,

validation result,

secret safety status,

cascade risk status,

remaining risks,

next recommended slice.


STOP IF:

a command may expose secrets,

scope expands beyond selected slice,

global config edit is required without Owner-side script,

validation cannot be run,

repository state contradicts the plan,

implementation requires unrelated refactor.



---

139. PART VII SUCCESS DEFINITION

139.1 Success

Part VII is successful when the Power Pack has moved from conceptual extensions to implementable modules.

139.2 Minimum successful outcome

At minimum:

Secret Firewall has MVP spec.

Cascade Prevention has MVP spec.

Cost Collapse has MVP spec.

One-Shot Compiler has MVP spec.

Backlog Autopilot has MVP spec.

Output Contracts have MVP spec.

Project State has MVP spec.

verify probes are defined.

tests are defined.

implementation phases are ordered.

hard rule candidates are defined.

Claude Code implementation prompt exists.


139.3 Strategic success

The PP becomes capable of:

blocking credential leaks,

preventing bug cascades,

reducing token waste,

improving one-shot execution,

generating useful next tasks,

making outputs trustworthy,

preserving project state,

turning failures into rules/tests/backlog.



---

140. PART VII CANONICAL PRINCIPLES

140.1 Implementability Beats Elegance

A beautiful architecture without tests, commands and probes is not real.

140.2 Security First Slice

Secret Firewall must be implemented before deeper autonomy.

140.3 Every Module Needs a Probe

If verify_spp cannot see it, it will drift.

140.4 Every Probe Needs a Test

A probe without tests is a decorative check.

140.5 Every Test Must Avoid Real Secrets

Security tests use fake canaries, never real credentials.

140.6 Every Hook Needs Registration Safety

Global hook changes require Owner-side scripts, backups and dry-runs.

140.7 Every Cascade Needs a Record

If the bug spread, record the spread.

140.8 Every Cost Pattern Needs a Firebreak

If cost repeats, create a stop point or reusable artifact.

140.9 Every Backlog Item Needs Done Criteria

A backlog item without done criteria is not a task.

140.10 Every Final Output Needs a Receipt

The Owner should never need to guess what changed, what passed, what failed or what remains risky.

END OF PART VII.

Otra cosa que quiero que haga la Claude Powerpack es que cuando yo haga, por ejemplo, restart, el comando /restart, que en vez de matar la terminal, iniciar una nueva y pegar un comando, la cosa sería que el exit de cuando yo hago restart y va a restartear, guarde la conversación exacta donde estábamos y haga exit y que el exit lo mande al CMD, es decir, a la terminal en Cursor, ojo, en Cursor, importante, no puede ser en CMD normal, tiene que ser en el CMD de Cursor. Entonces, lo manda por defecto al CMD y en el CMD pone Cloud y Resume o lo que sea y el ID de la conversación exacta donde estábamos. Y otra cosa, cuando yo abro un paint nuevo, es decir, cuando yo abro una terminal nueva en un proyecto de Cursor o en donde sea o en un repo en donde sea, donde sea que esté la Claude Powerpack, quiero que cuando yo abra, se registre en un JSON el número de sesiones que tengo activadas ahora mismo. Es decir, tengo tres terminales abiertas, ¿no? Uno en la conversación número 1111, por ejemplo, otro en la conversación 2222, otro en la conversación 3333, ¿no? Y cada uno está haciendo una cosa distinta. dentro de un proyecto, cada uno está desarrollando su propia cosa. Que, por cierto, también sería bueno tener un backlog para que cada pane de cada terminal tenga cosas que hacer y no colisionen, es decir, que no estén trabajando dos pains en la misma cosa, sino que estén desarrollando el proyecto, que todos tengan un backlog, que se regenere cada vez que hacemos algo, que se ha añadido una idea. Entonces, cuando se guardan esas conversaciones que están abiertas o, por ejemplo, se cambian, porque si yo, por ejemplo, estoy en la conversación 2222 en la terminal número 2 y quiero pasar a la conversación 4444, que no tengo abierta, pero quiero cambiar a esa conversación en la misma terminal, entonces el router, el archivo JSON, cambia la conversación activa del pain 2 a la conversación 4444. y entonces ahí se guarda que cuando yo, por cualquier motivo, cierre Cursor, ya sea que se me apaga el ordenador, que se me, yo qué sé, que se me va la luz, que cierro Cursor porque se me crashea por un out of memory o lo que sea, cuando yo vuelva a abrir Cursor, se abran justo el número de terminales que tenía abierto, exactamente igual y exactamente en la conversación que dice el JSON, el JSON file. Entonces, esas dos cosas.

hay que reforzar esto muchísimo para que nada salga bugueado

Sí. Esto hay que añadirlo como Parte VIII y tratarlo como un sistema crítico, porque si se implementa mal te puede dejar panes duplicados, conversaciones perdidas, terminales trabajando en lo mismo, JSON corrupto o restores falsos.

El dataset base ya tiene piezas relacionadas como terminal-slot-recorder, Lazarus livesnap, restart-target-consumer, mark-live-session, SessionStart y SessionEnd, así que esto no debe construirse desde cero, sino como una capa superior de continuidad y routing sobre esos mecanismos existentes. 

