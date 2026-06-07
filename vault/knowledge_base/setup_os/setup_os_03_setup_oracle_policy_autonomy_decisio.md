# CPP Setup OS -- PART 3: Setup Oracle, Policy, Autonomy, Decision Journal, Value Density

**Source:** Dataset CPP Setup 1.txt
**Source sha256:** 34f94e576fa32e19
**Source line range:** 6023-8344 (2322 lines)
**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).

---

86. PROPÓSITO DE LA PARTE III

La Parte I convirtió PP Setup OS en una versión superior del plugin oficial claude-code-setup.

La Parte II convirtió las recomendaciones en transacciones, registry, rollback, kill-switches, manifest y workspace pack.

La Parte III añade la capa siguiente:

PP Setup OS debe poder decidir con criterio propio qué nivel de setup corresponde a cada repo, cuándo una automatización está madura para activarse, cuándo debe quedarse en shadow mode, cuándo una acción debe bloquearse y cuándo un repo todavía no merece más automatización.

La innovación principal de esta parte es crear un sistema de decisión:

No solo “qué instalar”.

Sino:

qué instalar primero;

qué no instalar todavía;

qué necesita sandbox;

qué requiere Owner-side action;

qué debe vivir en advisory mode;

qué puede pasar a local active;

qué está prohibido;

qué debe convertirse en backlog;

qué debe convertirse en policy;

qué debe convertirse en hard rule;

qué debe ser eliminado porque genera ruido.



---

87. SETUP ORACLE LAYER

87.1 Nombre canónico

Canonical Name:

Setup Oracle Layer

Abreviatura:

SOL

87.2 Propósito

Setup Oracle Layer es la capa que decide la siguiente acción correcta de setup usando:

Project Profile;

Setup Manifest;

Automation Registry;

Risk Ledger;

Validation Registry;

Rollback Recipes;

Kill-Switch Registry;

Automation Dependency Graph;

File Sensitivity Map;

Owner goal;

maturity state;

current blockers.


87.3 Pregunta central

“What is the safest highest-leverage next setup move for this repo?”

87.4 Output

SETUP_ORACLE_DECISION

decision_id

project

current_state

target_state

recommended_action

action_type

why_this_now

why_not_other_actions

blocked_actions

required_prerequisites

safety_level

expected_state_delta

validation_required

rollback_required

owner_required

risk_if_ignored

next_after_completion


87.5 Regla

PP Setup OS should never output a flat list when a decision is needed.

It must identify the best next setup move.


---

88. SETUP POLICY ENGINE

88.1 Problema

Sin policy engine, cada repo puede recibir recomendaciones inconsistentes.

Un repo con secretos, deploy, CI y MCPs externos no puede tratarse igual que un repo de documentación local.

88.2 Nombre canónico

Setup Policy Engine

88.3 Propósito

Aplicar reglas de setup según:

tipo de repo;

riesgo de secretos;

madurez;

validación existente;

rollback existente;

urgencia de demo;

urgencia de revenue;

nivel de autonomía deseado;

tipo de automatización.


88.4 Policy Decision Object

SETUP_POLICY_DECISION

policy_id

policy_name

applies_to

trigger

allowed_actions

blocked_actions

required_gates

required_evidence

exception_conditions

false_positive_guard

owner_override_allowed

status


88.5 Policy Categories

Secret Safety Policy

Global Config Policy

Hook Activation Policy

MCP Permission Policy

Subagent Autonomy Policy

Slash Command Side-Effect Policy

Evidence Storage Policy

Rollback Policy

Validation Policy

Cost Policy

Demo Readiness Policy

Revenue Readiness Policy

Crash Recovery Policy


88.6 Regla

A recommendation that violates policy cannot be P0/P1 unless the recommendation is to fix the policy blocker itself.


---

89. SETUP SANDBOX SIMULATION

89.1 Problema

Dry-run dice qué cambiaría.

Pero algunas automatizaciones necesitan probarse en entorno simulado antes de tocar el repo real.

89.2 Nombre canónico

Setup Sandbox Simulation

89.3 Propósito

Permitir que PP Setup OS pruebe automatizaciones en un entorno seguro, sin afectar el repo real.

89.4 Usos

probar hooks;

probar command specs;

probar redaction;

probar rollback;

probar setup manifest generation;

probar registry updates;

probar fake secret detection;

probar collision detection;

probar bad config recovery;

probar output contract enforcement.


89.5 Sandbox Simulation Record

SETUP_SANDBOX_SIMULATION

simulation_id

project

candidate_automation

simulated_files

simulated_config

simulated_inputs

expected_behavior

actual_behavior

secrets_exposed

rollback_tested

failure_mode_tested

passed

blockers_found

next_action


89.6 Regla

Hooks, redactors, installers, rollback systems and global config generators should pass sandbox simulation before active use.


---

90. SHADOW MODE GOVERNANCE

90.1 Problema

Algunas automatizaciones son útiles pero peligrosas si bloquean acciones demasiado pronto.

Ejemplo:

secret scanner con falsos positivos;

cost firebreak demasiado agresivo;

hook que bloquea comandos legítimos;

output validator que interrumpe demasiado;

subagent que genera ruido;

MCP advisor que recomienda demasiado.


90.2 Nombre canónico

Shadow Mode Governance

90.3 Propósito

Ejecutar automatizaciones observando, pero sin bloquear.

90.4 Shadow Record

SHADOW_MODE_RECORD

automation_id

project

trigger_seen

action_it_would_have_taken

actual_action_taken

false_positive_possible

owner_value

noise_level

cost

recommendation

promote_or_adjust


90.5 Promotion criteria

Una automatización puede pasar de shadow a advisory si:

detectó eventos reales;

no expuso secretos;

no generó ruido excesivo;

sus recomendaciones cambiaron una decisión;

tiene rollback;

tiene kill-switch;

tiene validation.


90.6 Regla

High-risk automation should prove itself in shadow mode before becoming active.


---

91. ADVISORY MODE GOVERNANCE

91.1 Propósito

Después de shadow mode, una automatización puede aconsejar, pero no actuar.

91.2 Advisory Output Contract

ADVISORY_OUTPUT

automation_id

trigger

evidence

recommendation

risk_if_ignored

action_required

owner_decision_needed

cost_of_action

confidence

false_positive_guard


91.3 Reglas

No advisory without evidence.

No repeated advisory without new information.

No advisory if action is unclear.

No advisory if cost of reading advisory exceeds value.

No advisory may include raw secrets.

91.4 Promotion criteria

Una automatización puede pasar de advisory a active solo si:

sus advisories fueron útiles;

no generó noise;

Owner no tuvo que corregirla repetidamente;

tiene pruebas;

tiene rollback;

tiene kill-switch;

tiene scope cerrado.



---

92. AUTONOMY PERMISSION SYSTEM

92.1 Problema

No todas las automatizaciones pueden tener el mismo nivel de autonomía.

92.2 Nombre canónico

Autonomy Permission System

92.3 Niveles

P0 — Observe Only

Puede escanear y reportar.

P1 — Recommend

Puede sugerir, no modificar.

P2 — Draft

Puede crear planes, prompts o specs.

P3 — Dry-Run

Puede simular cambios.

P4 — Local Safe Apply

Puede aplicar cambios locales reversibles.

P5 — Local Active Guard

Puede bloquear o modificar acciones locales bajo reglas estrictas.

P6 — Owner-Side Global

Puede generar acciones globales para el Owner, no ejecutarlas directamente.

P7 — External Approval-Gated

Puede interactuar con herramientas externas solo con aprobación.

P8 — Production Protocol

Solo bajo protocolo explícito.

P9 — Forbidden

No permitido.

92.4 Permission fields

AUTONOMY_PERMISSION

automation_id

current_permission_level

max_allowed_level

reason

required_gates_for_next_level

owner_override_allowed

expiration

review_required


92.5 Regla

Secret risk, global config risk, production risk and external side effects lower autonomy automatically.


---

93. SETUP PERMISSION ESCALATION

93.1 Propósito

Automatizaciones deben poder ganar permisos con evidencia.

93.2 Escalation requirements

Para pasar de P1 a P2:

output contract exists.


Para pasar de P2 a P3:

dry-run plan exists.


Para pasar de P3 a P4:

rollback exists;

validation exists;

file sensitivity checked.


Para pasar de P4 a P5:

kill-switch exists;

false-positive rate acceptable;

shadow/advisory history clean.


Para pasar a P6:

Owner-side protocol exists.


Para pasar a P7:

permission boundaries exist.


Para pasar a P8:

production protocol exists.


93.3 Regla

Autonomy is earned, not assumed.


---

94. SETUP BLOCKER CLASSIFICATION

94.1 Propósito

Cuando algo no puede instalarse, el sistema debe explicar exactamente por qué.

94.2 Blocker types

BLOCKED_SECRET_RISK

BLOCKED_NO_VALIDATION

BLOCKED_NO_ROLLBACK

BLOCKED_NO_KILL_SWITCH

BLOCKED_GLOBAL_CONFIG

BLOCKED_EXTERNAL_PERMISSION

BLOCKED_COLLISION

BLOCKED_DEPENDENCY

BLOCKED_LOW_READINESS

BLOCKED_NO_OWNER_GOAL

BLOCKED_SPECULATIVE

BLOCKED_HIGH_COST

BLOCKED_UNCLEAR_VALUE

BLOCKED_BUSYWORK


94.3 Blocker Record

SETUP_BLOCKER

blocker_id

affected_candidate

blocker_type

evidence

severity

fix_required

smallest_unblocking_step

owner_required

can_defer

status


94.4 Regla

Blocked is not failure.

Blocked is safe governance.


---

95. SETUP UNBLOCKING ENGINE

95.1 Propósito

No basta con bloquear. El sistema debe decir cómo desbloquear.

95.2 Unblocking Output

UNBLOCKING_PLAN

blocker

target_candidate

smallest_safe_step

required_artifact

validation

rollback

owner_action

estimated_effort

priority

prompt_for_claude_code


95.3 Ejemplos

Si está bloqueado por no tener rollback:

crear rollback recipe.

Si está bloqueado por secret risk:

ejecutar secret scan y sanitizer.

Si está bloqueado por global config:

generar Owner-side plan.

Si está bloqueado por collision:

crear collision resolution.

Si está bloqueado por validation gap:

crear validation registry entry.

95.4 Regla

Every P0/P1 blocked candidate must produce an unblocking plan.


---

96. SETUP DECISION JOURNAL

96.1 Problema

Las decisiones de setup pueden parecer obvias en el momento, pero perderse después.

96.2 Nombre canónico

Setup Decision Journal

96.3 Propósito

Registrar por qué se decidió instalar, bloquear, diferir, rechazar o degradar una automatización.

96.4 Entry

SETUP_DECISION_JOURNAL_ENTRY

decision_id

timestamp

project

candidate

decision

reasoning

evidence

rejected_alternatives

risk_accepted

risk_rejected

owner_input

future_review_date


96.5 Decisiones posibles

install_now

dry_run_first

shadow_first

advisory_only

owner_side_only

defer

reject

replace_existing

deprecate_existing

require_more_evidence


96.6 Regla

Important setup decisions should be explainable later.


---

97. SETUP CHANGE BUDGET

97.1 Problema

Meter demasiados cambios de setup a la vez puede romper el repo o confundir al Owner.

97.2 Nombre canónico

Setup Change Budget

97.3 Propósito

Limitar cuántas mutaciones de setup pueden ocurrir en una transacción.

97.4 Budget fields

SETUP_CHANGE_BUDGET

max_files_changed

max_hooks_added

max_commands_added

max_skills_added

max_agents_added

max_mcp_changes

max_global_changes

max_risk_score

max_cost_level

max_owner_actions


97.5 Defaults

Phase 0:

0 mutations.

Phase 1:

security artifacts only.

Phase 2:

dry-run artifacts only.

Phase 3:

small local changes only.

Phase 4:

Owner-side global only.

Phase 5:

continuous improvement with strict budget.

97.6 Regla

If setup change budget is exceeded, split into smaller transactions.


---

98. SETUP BATCHING STRATEGY

98.1 Propósito

Agrupar recomendaciones sin crear riesgo.

98.2 Batch types

SAFETY_BATCH

Secret scanner, redaction, diff hygiene.

VALIDATION_BATCH

Validation registry, smoke tests, verify command.

ROLLBACK_BATCH

Rollback recipes, backup strategy, kill-switch.

CONTEXT_BATCH

Workspace pack, context pack, manifest.

AUTOMATION_BATCH

Hooks, skills, commands, agents.

EXTERNAL_BATCH

MCP, external integrations, provider configs.

98.3 Regla

Batches must be ordered:

Safety → Validation → Rollback → Context → Automation → External.

Never reverse this order without explicit reason.


---

99. SETUP NOISE CONTROL

99.1 Problema

Un setup poderoso puede generar demasiado ruido.

99.2 Noise sources

too many recommendations;

too many advisories;

repeated warnings;

low-value hooks;

verbose reports;

agents speaking too often;

commands with overlapping purpose;

registry bloat;

backlog duplication.


99.3 Noise Score

SETUP_NOISE_SCORE

recommendation_count

repeated_warning_count

low_value_advisories

duplicate_candidates

owner_decision_load

report_length_vs_actionability


99.4 Regla

If noise increases faster than actionable value, simplify.


---

100. SETUP ACTIONABILITY SCORE

100.1 Propósito

Medir si el output sirve para actuar.

100.2 Score dimensions

clear next action;

evidence source;

done criteria;

validation;

rollback;

owner-side clarity;

low ambiguity;

no generic advice;

priority clarity;

blocked items separated.


100.3 Thresholds

0-50:

Not actionable.

51-70:

Needs refinement.

71-85:

Actionable.

86-100:

High leverage.

100.4 Regla

A setup report with no actionable next step is incomplete.


---

101. SETUP MINIMUM VIABLE AUTOMATION

101.1 Problema

No toda idea requiere hook, agent o MCP.

101.2 Escalation ladder

1. Note


2. Checklist


3. Prompt template


4. Command


5. Skill


6. Hook


7. Subagent


8. MCP


9. Daemon


10. Production workflow



101.3 Regla

Use the lowest automation level that solves the repeated problem.

101.4 Examples

If Owner forgets a process:

start with checklist.

If Claude Code repeatedly misunderstands task:

create prompt template or skill.

If unsafe command repeats:

create hook.

If external data is needed often:

consider MCP.

If continuous monitoring is needed:

consider daemon.

101.5 Rule

Over-automation is setup debt.


---

102. SETUP VALUE DENSITY FILTER

102.1 Propósito

Distinguir automatizaciones de alto valor frente a ornamentales.

102.2 Value Density

Value Density = state improvement / setup complexity

High value:

prevents secrets;

enables validation;

prevents broken global config;

reduces repeated costs;

improves one-shot reliability;

creates rollback;

improves demo/revenue readiness.


Low value:

aesthetic organization;

duplicate commands;

generic agents;

hooks without clear trigger;

MCPs with unclear need;

skills for one-off tasks.


102.3 Regla

Low value density items should be rejected or deferred.


---

103. SETUP SOVEREIGNTY SCORE

103.1 Propósito

Medir cuánto puede operar un repo con Claude Code sin depender de memoria humana.

103.2 Dimensions

manifest exists;

profile exists;

validation registry exists;

rollback recipes exist;

command registry exists;

automation registry exists;

file sensitivity map exists;

context pack exists;

owner-side actions documented;

next action exists;

crash recovery exists;

setup handoff exists.


103.3 Score bands

0-30:

Human-memory dependent.

31-60:

Partially structured.

61-80:

Operationally structured.

81-95:

Strong Claude Code readiness.

96-100:

Sovereign setup state.

103.4 Regla

A repo with low sovereignty should receive structure before automation.


---

104. SETUP COMPOUNDING LOOP

104.1 Propósito

Cada ejecución de PP Setup OS debe mejorar las siguientes.

104.2 Loop

1. Scan repo.


2. Generate profile.


3. Recommend.


4. Register.


5. Validate.


6. Apply safely if allowed.


7. Capture decision.


8. Update manifest.


9. Update work queue.


10. Update policy if pattern repeats.


11. Update hard rule if risk repeats.


12. Update context pack.


13. Reduce future scan cost.



104.3 Regla

If a setup run does not make future setup easier, it is weak.


---

105. SETUP LEARNING WITHOUT OVERFITTING

105.1 Problema

Aprender demasiado de un repo puede crear reglas malas para otros.

105.2 Learning classes

LOCAL_LESSON

Aplica solo a este repo.

POLICY_CANDIDATE

Podría aplicar a una clase de repos.

GLOBAL_RULE_CANDIDATE

Podría aplicar a todos los repos.

ANTI_PATTERN

Debe evitarse en general.

105.3 Promotion rules

Local lesson can become policy candidate if repeated across similar repos.

Policy candidate can become global rule only with false-positive guard.

Global rule must have exception conditions.

105.4 Regla

Do not globalize from one repo too quickly.


---

106. SETUP ANTI-FRAGILITY TESTS

106.1 Propósito

PP Setup OS debe mejorar cuando encuentra fallos.

106.2 Failure tests

Test cases should simulate:

invalid settings;

broken hook;

missing rollback;

fake secret in output;

global config collision;

MCP permission overreach;

command with dangerous side effect;

duplicate skill;

noisy subagent;

crash mid-transaction;

validation missing;

Owner-side action incomplete.


106.3 Expected behavior

detect;

block;

explain;

create unblocking plan;

preserve safe state;

avoid raw secret exposure;

add backlog item;

update risk ledger.


106.4 Regla

A setup system is not mature until it has been tested against failure modes.


---

107. SETUP SAFETY CASE

107.1 Propósito

Para cada automation batch, PP Setup OS debe poder justificar que es seguro.

107.2 Safety Case

SETUP_SAFETY_CASE

batch_id

claim

evidence

assumptions

risks

mitigations

validation

rollback

residual_risk

owner_decision_needed


107.3 Example claim

“Local setup commands are safe to add because they do not touch global config, do not read secrets, have no external side effects, and can be removed by deleting project-local files.”

107.4 Regla

No high-risk setup batch without Safety Case.


---

108. SETUP TRUST RECEIPT

108.1 Propósito

El Owner necesita confiar sin leer todo.

108.2 Trust Receipt

SETUP_TRUST_RECEIPT

status

what_changed

what_did_not_change

global_config_status

secret_status

validation_status

rollback_status

active_automations

blocked_automations

next_best_action

risk_remaining


108.3 Regla

Every meaningful setup run must end with trust receipt.


---

109. SETUP GOVERNANCE FOR GENERATED PROMPTS

109.1 Problema

PP Setup OS generará prompts para Claude Code.

Esos prompts también pueden ser inseguros.

109.2 Prompt governance

Every generated prompt must include:

mission;

source of truth;

allowed actions;

forbidden actions;

secret policy;

mutation level;

validation;

rollback;

output contract;

stop conditions.


109.3 Prompt Risk Levels

PROMPT_SAFE_READ_ONLY

Only scan/report.

PROMPT_LOCAL_SAFE

Can create local reversible artifacts.

PROMPT_GLOBAL_OWNER_SIDE

Only generate Owner instructions.

PROMPT_EXTERNAL_APPROVAL

External actions need approval.

PROMPT_FORBIDDEN

Would expose secrets or cause unsafe mutation.

109.4 Regla

A generated prompt is an automation surface. Govern it.


---

110. SETUP EVIDENCE BOUNDARY

110.1 Propósito

Determinar qué evidencia se guarda y cuál no.

110.2 Evidence allowed

summarized test results;

command names;

pass/fail;

redacted findings;

file paths;

line numbers without raw secrets;

setup decisions;

validation status;

rollback status.


110.3 Evidence forbidden

raw .env;

raw tokens;

raw private keys;

full logs with secrets;

screenshots with credentials;

raw HTTP headers;

raw database URLs;

raw cookies.


110.4 Regla

Evidence is useful only if it is safe.


---

111. SETUP TIME-TO-VALUE METRIC

111.1 Propósito

Medir cuánto tarda el setup en generar valor real.

111.2 Time-to-Value events

first profile generated;

first P0 risk detected;

first safe recommendation generated;

first validation registry created;

first rollback recipe created;

first local automation installed;

first blocked unsafe action prevented;

first next-best-action executed.


111.3 Regla

PP Setup OS should optimize for fast safe value, not huge initial setup.


---

112. SETUP BURDEN INDEX

112.1 Propósito

Medir si el setup está cargando demasiado al Owner.

112.2 Burden factors

number of decisions required;

number of owner-side actions;

number of blocked items;

complexity of report;

number of commands to run;

ambiguity;

manual verification burden.


112.3 Rule

Reduce Owner burden by:

ranking;

batching;

explaining;

generating exact Owner-side actions;

separating now/later;

rejecting busywork.


112.4 Regla

A setup system that requires too much human interpretation is failing.


---

113. SETUP DEFAULT PATHS

113.1 Propósito

Definir caminos por defecto según estado del repo.

113.2 If no Claude config exists

Default path:

Profile → Manifest → Validation Registry → Secret Safety → Commands → Skills → Hooks.

113.3 If Claude config exists but no rollback

Default path:

Inventory → Registry → Rollback Recipes → Verify → Improve.

113.4 If hooks exist but no kill-switch

Default path:

Hook Audit → Kill-Switch Registry → Smoke Tests → Risk Ledger.

113.5 If MCPs exist

Default path:

Permission Audit → Secret Risk → Allowed/Forbidden Actions → Owner Review.

113.6 If repo has secrets risk

Default path:

Secret Firewall → Env Hygiene → Evidence Sanitizer → Diff Scanner → Continue.

113.7 If repo has no tests

Default path:

Validation Registry → Smoke Test → Setup Readiness Update.

113.8 Regla

PP Setup OS should choose path based on repo state, not generic checklist order.


---

114. SETUP REJECTION ENGINE

114.1 Propósito

PP Setup OS must be able to say no.

114.2 Reject if

no evidence;

low value density;

high maintenance burden;

no validation;

no rollback;

high secret risk;

duplicates existing automation;

creates noise;

unclear Owner value;

speculative;

requires global mutation too early;

requires external side effects too early;

violates current phase.


114.3 Rejection Record

SETUP_REJECTION

candidate

reason

evidence

reconsider_if

alternative_lower_risk_action

status


114.4 Regla

Rejecting bad automation is progress.


---

115. SETUP UPGRADE LADDER

115.1 Propósito

Mejorar un repo por niveles.

115.2 Levels

L0 — Unprepared

No profile, no config, no validation.

L1 — Profiled

Repo understood.

L2 — Safe

Secrets and risky files classified.

L3 — Validatable

Known validation commands exist.

L4 — Reversible

Rollback recipes exist.

L5 — Locally Automated

Safe local commands/skills exist.

L6 — Guarded

Hooks exist with kill-switches.

L7 — Assisted

Subagents/advisories exist.

L8 — Integrated

MCPs governed.

L9 — Operational

Workspace pack, manifest, registry, work queue active.

L10 — Sovereign

Crash recovery, setup oracle, continuous improvement, low Owner burden.

115.3 Regla

Do not jump levels without satisfying lower-level safety gates.


---

116. SETUP FOR DIFFERENT OWNER ENERGY STATES

116.1 Propósito

El setup debe adaptarse al estado mental/energético del Owner.

116.2 Modes

LOW_ENERGY_SETUP

Output:

one action;

minimal risk;

exact prompt;

no overload.


MEDIUM_ENERGY_SETUP

Output:

top 3 actions;

dry-run plan;

one validation task.


HIGH_ENERGY_SETUP

Output:

full governance report;

phased roadmap;

implementation prompt.


116.3 Regla

If energy unknown, default to medium and prioritize the smallest action that unlocks safety or validation.


---

117. SETUP FOR URGENT DEMO

117.1 Propósito

Si hay demo cercana, setup debe priorizar demostrabilidad.

117.2 Demo urgent path

identify run command;

identify smoke test;

identify sample data;

avoid secrets;

create demo script;

create failure fallback;

avoid big architecture changes;

generate recording checklist;

validate visible flow.


117.3 Regla

Before a demo, do not install risky automation unless it directly prevents demo failure.


---

118. SETUP FOR FUNDING / INVESTOR CONTEXT

118.1 Propósito

Si un proyecto se va a enseñar a inversor, PP Setup OS debe priorizar credibilidad.

118.2 Investor-readiness setup checks

can explain system in 2 minutes;

has proof flow;

has reliability story;

has safety story;

has operational maturity;

has demo path;

has next milestones;

no obvious secret/security negligence;

no fragile setup story.


118.3 Relevant automations

demo-ready;

revenue-ready;

validation registry;

trust receipt;

setup manifest;

progress proof;

rollback documentation;

architecture summary.


118.4 Regla

For investor context, trust artifacts outrank internal cleverness.


---

119. SETUP PROGRESS PROOF

119.1 Propósito

Cada parte del setup debe demostrar avance.

119.2 Proof types

risk reduced;

validation added;

rollback added;

secret safety improved;

automation registered;

collision resolved;

Owner burden reduced;

demo readiness improved;

revenue readiness improved;

cost reduced;

crash recovery improved.


119.3 Progress Proof Entry

SETUP_PROGRESS_PROOF

proof_id

before_state

after_state

evidence

risk_reduced

time_saved

next_unlock


119.4 Regla

Setup work should be measured by state change, not number of files created.


---

120. FINAL PART III PRINCIPLES

120.1 The Oracle Chooses, The Registry Remembers

Decision logic and state memory must be separate.

120.2 Shadow Before Power

Dangerous automation should observe before it acts.

120.3 Permissions Must Be Earned

Autonomy rises only through evidence.

120.4 Blocked Is Safe

A blocked recommendation prevents damage.

120.5 Unblocking Is Mandatory

A blocked P0/P1 item must include the smallest safe unblock path.

120.6 Low-Value Automation Is Debt

More automation is not automatically better.

120.7 Setup Must Fit Owner Energy

The best next action must be executable by the Owner’s current state.

120.8 Investor/Demo Context Changes Priority

Visible proof can outrank internal elegance.

120.9 Safety Gates Create Speed

Safe setup reduces future hesitation and repair cycles.

120.10 Setup Must Compound

Every run should make the next run cheaper, safer or clearer.


---

121. PART III HARD RULE CANDIDATES

HR-SETUP-021:

High-risk automation must pass shadow mode before active blocking or mutation.

HR-SETUP-022:

Every automation must have an explicit autonomy permission level.

HR-SETUP-023:

Secret risk, global config risk, production risk and external side effects automatically lower autonomy.

HR-SETUP-024:

Every blocked P0/P1 setup candidate must include an unblocking plan.

HR-SETUP-025:

No setup output is complete without a best next action.

HR-SETUP-026:

No setup batch may exceed its change budget; split oversized batches.

HR-SETUP-027:

No setup recommendation may skip the minimum viable automation ladder.

HR-SETUP-028:

A setup prompt generated for Claude Code must include secret policy, mutation level, validation, rollback and stop conditions.

HR-SETUP-029:

No automation should be promoted from advisory to active without evidence of useful advisories and acceptable noise.

HR-SETUP-030:

If a repo has low setup sovereignty, prioritize structure before automation.


---

122. PART III SUCCESS METRICS

122.1 Oracle quality

100% setup reports include best next action.

100% best next actions explain why now.

100% blocked actions explain why not now.


122.2 Permission quality

100% automations have permission level.

100% permission escalations list required gates.

0 high-risk automations become active directly.


122.3 Noise quality

repeated advisories reduced;

duplicate recommendations reduced;

top recommendations are actionable;

blocked items separated clearly.


122.4 Safety quality

shadow mode used for high-risk hooks;

active automations have kill-switches;

external actions approval-gated;

global config owner-side only.


122.5 Compounding quality

each run updates manifest, registry, decision journal or work queue;

future scans become cheaper;

context packs reduce repeated reading;

setup sovereignty score increases over time.



---

123. PART III CLAUDE CODE PROMPT

PROMPT:

Act as implementation engineer for Claude Power Pack Setup OS.

MISSION:

Extend PP Setup OS with decision governance, setup oracle logic, policy evaluation, shadow/advisory modes and autonomy permission modeling.

The goal is to prevent unsafe automation activation and ensure every setup action is ranked, blocked, deferred or promoted with evidence.

SOURCE OF TRUTH:

Use the repo on disk.

If repo state contradicts previous assumptions, use repo state.

NON-NEGOTIABLES:

Do not expose raw secrets.

Do not read .env or credential files raw.

Do not modify global Claude config.

Do not activate hooks.

Do not install MCPs.

Do not touch production.

Do not create irreversible changes.

Do not promote automation to active without validation, rollback and kill-switch.

Do not generate generic recommendations.

Do not skip best-next-action.

TASK:

Design or implement the next governance layer for PP Setup OS:

1. Setup Oracle Decision model.


2. Setup Policy Decision model.


3. Shadow Mode governance.


4. Advisory Mode governance.


5. Autonomy Permission model.


6. Blocker classification.


7. Unblocking plan model.


8. Decision Journal.


9. Change Budget.


10. Minimum Viable Automation ladder.


11. Setup Sovereignty Score.


12. Setup Upgrade Ladder.



PHASE RESTRICTION:

Stay specification-first or read-only unless safe local conventions already exist.

Do not activate runtime automation.

Do not mutate global config.

Do not install external MCPs.

ACCEPTANCE:

Every recommendation can be assigned an autonomy level.

Every high-risk automation can be blocked, shadowed or advisory-only.

Every blocker has an unblocking path.

Every setup decision is explainable.

Every generated Claude Code prompt includes policy, validation, rollback and stop conditions.

Every report includes best next action.

FINAL RECEIPT:

Return:

what was specified or changed;

whether any files were touched;

whether global config stayed untouched;

secret safety status;

validation status;

what this adds beyond Parts I and II;

next recommended phase.


END PROMPT.


---

124. FINAL INTEGRATION STATEMENT

Claude Power Pack Setup OS Part III turns setup from a planning system into a decision system.

Part I answered:

“What should this repo use?”

Part II answered:

“How do we track, validate and reverse setup?”

Part III answers:

“What is safe to activate, what must stay in shadow, what is blocked, what deserves autonomy, and what is the best next move?”

The system becomes stronger when it can say:

install this;

simulate this;

shadow this;

advise only;

block this;

reject this;

do this later;

do this now;

do not automate this yet.


Canonical rule:

The best setup system is not the one that installs the most. It is the one that activates only what the repo is mature enough to safely use.

END OF PART III.

📌 Recordatorio permanente: ¿Quieres que actualicemos tus sistemas de IA con toda la información nueva de este dataset? Si es así, dime “actualizar” y te pediré que me mandes lo necesario.

CLAUDE POWER PACK SETUP OS — EXTENSION DATASET PART IV

Setup Observability + Benchmark Supremacy + Compatibility Matrix + Doctor Mode + Upgrade Intelligence

