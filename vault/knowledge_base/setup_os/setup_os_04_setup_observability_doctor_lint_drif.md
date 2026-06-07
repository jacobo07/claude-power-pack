# CPP Setup OS -- PART 4: Setup Observability, Doctor/Lint, Drift, Recovery, Command Center

**Source:** Dataset CPP Setup 1.txt
**Source sha256:** 34f94e576fa32e19
**Source line range:** 8345-10934 (2590 lines)
**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).

---

125. PROPÓSITO DE LA PARTE IV

La Parte I definió la superioridad estratégica de PP Setup OS frente al plugin oficial.

La Parte II convirtió setup en transacciones, registry, rollback, manifest y workspace pack.

La Parte III añadió Setup Oracle, policy engine, shadow mode, advisory mode, permisos de autonomía y decisión inteligente.

La Parte IV añade la siguiente capa:

PP Setup OS debe poder observarse, medirse, compararse, diagnosticarse y mejorarse a sí mismo.

No basta con recomendar o instalar bien.

El sistema debe saber:

si está funcionando;

si el setup realmente mejora el repo;

si las automatizaciones añadidas generan valor;

si hay ruido;

si hay riesgo acumulado;

si está superando al plugin oficial;

si una automatización debe degradarse, desactivarse o reemplazarse;

si el repo está más preparado que antes;

si el Owner tiene menos carga mental;

si futuras sesiones serán más baratas, seguras y fiables.


La innovación central de esta parte es convertir PP Setup OS en un sistema medible.

Canonical Rule:

What cannot be measured cannot be trusted as setup improvement.


---

126. SETUP OBSERVABILITY LAYER

126.1 Nombre canónico

Setup Observability Layer

Abreviatura:

SOL-OBS

126.2 Propósito

Crear visibilidad interna sobre el estado, calidad, riesgo, coste y utilidad del setup.

126.3 Qué debe observar

setup readiness score;

setup sovereignty score;

secret readiness score;

validation readiness score;

rollback readiness score;

automation maturity;

active automation count;

blocked automation count;

noisy automation count;

stale automation count;

owner-side pending actions;

setup transactions completed;

failed-safe transactions;

rollbacks executed;

shadow-mode signals;

advisory usefulness;

command safety;

hook health;

MCP permission risk;

context pack freshness;

work queue health;

demo readiness trend;

revenue readiness trend.


126.4 Setup Observability Snapshot

SETUP_OBSERVABILITY_SNAPSHOT

snapshot_id

project

timestamp

setup_readiness_score

setup_sovereignty_score

secret_readiness_score

validation_readiness_score

rollback_readiness_score

active_automations

blocked_automations

stale_automations

noisy_automations

unresolved_p0_risks

pending_owner_side_actions

last_transaction_status

last_verify_status

next_best_action

trend


126.5 Regla

PP Setup OS must not rely on vibes. It must expose operational state.


---

127. SETUP HEALTH DASHBOARD MODEL

127.1 Propósito

Definir un dashboard lógico de salud del setup.

No necesariamente visual al principio.

Debe poder representarse como reporte, tabla, manifest o summary.

127.2 Health dimensions

Safety Health

Validation Health

Rollback Health

Automation Health

Registry Health

Policy Health

Context Health

Cost Health

Demo Health

Revenue Health

Owner Burden Health

Crash Recovery Health


127.3 Health bands

CRITICAL

Setup puede causar daño o romper Claude Code.

WEAK

Setup útil pero incompleto o frágil.

OPERATIONAL

Setup seguro para uso normal.

STRONG

Setup con buena gobernanza, rollback, validación y bajo ruido.

SOVEREIGN

Setup altamente medible, recuperable, eficiente y autónomo.

127.4 Health Report

SETUP_HEALTH_REPORT

project

health_band

strongest_dimension

weakest_dimension

p0_blockers

p1_improvements

stale_items

unsafe_items

overbuilt_items

missing_foundational_items

recommended_next_action


127.5 Regla

The weakest health dimension should guide the next setup task.


---

128. OFFICIAL PLUGIN BENCHMARK SUPREMACY

128.1 Propósito

PP Setup OS debe poder demostrar objetivamente que supera al plugin oficial.

No basta con decir que es mejor.

Debe compararse por dimensiones.

128.2 Benchmark dimensions

category detection;

repo profiling depth;

recommendation grounding;

risk classification;

secret safety;

install mode clarity;

validation planning;

rollback planning;

owner-side governance;

setup readiness scoring;

work queue generation;

demo readiness;

revenue readiness;

cost governance;

autonomy governance;

crash recovery;

observability.


128.3 Benchmark Result

OFFICIAL_PLUGIN_BENCHMARK_RESULT

project

official_style_output_possible

pp_setup_os_output

categories_matched

additional_governance_added

risks_detected

rollback_added

validation_added

blocked_unsafe_recommendations

next_best_action_added

supremacy_score


128.4 Supremacy Score

0-30:

Not better. Merely different.

31-60:

Better recommendations, weak governance.

61-80:

Clearly superior setup advisor.

81-95:

Superior governed setup system.

96-100:

Order-of-magnitude superior Setup OS.

128.5 Regla

PP Setup OS should preserve official-plugin usefulness while adding governance, not replace clarity with complexity.


---

129. SETUP IMPROVEMENT DELTA

129.1 Propósito

Cada ejecución debe medir qué mejoró.

129.2 Delta fields

SETUP_IMPROVEMENT_DELTA

before_state

after_state

readiness_delta

secret_safety_delta

validation_delta

rollback_delta

automation_maturity_delta

owner_burden_delta

cost_delta

risk_delta

demo_readiness_delta

revenue_readiness_delta

evidence


129.3 Ejemplos de delta válido

“Secret readiness improved because diff scanner and redaction policy were added.”

“Rollback readiness improved because local setup actions now have rollback recipes.”

“Owner burden decreased because best-next-action and owner-side commands were separated.”

“Automation maturity improved because hooks moved from idea to shadow mode.”


129.4 Regla

A setup task without delta should not be counted as meaningful progress.


---

130. SETUP DOCTOR MODE

130.1 Nombre canónico

Setup Doctor Mode

130.2 Propósito

Permitir que PP Setup OS diagnostique problemas del propio setup.

Activación conceptual:

setup está roto;

hooks fallan;

commands no aparecen;

agent genera ruido;

MCP no conecta;

manifest está stale;

registry contradice realidad;

rollback falta;

Owner no sabe qué hacer;

Claude Code startup se vuelve lento;

secret scanner bloquea demasiado;

output se vuelve demasiado largo.


130.3 Doctor Diagnosis

SETUP_DOCTOR_DIAGNOSIS

symptom

affected_area

likely_root_cause

evidence_needed

safe_checks

dangerous_checks_to_avoid

repair_options

recommended_fix

rollback_needed

owner_side_required

validation_after_fix


130.4 Doctor rules

Doctor Mode is read-only first.

Doctor Mode must not repair before diagnosis.

Doctor Mode must not touch global config directly.

Doctor Mode must prefer safe local checks.

Doctor Mode must separate symptoms from root cause.

Doctor Mode must generate a repair plan before mutation.

130.5 Regla

A setup system needs a doctor before it needs more features.


---

131. SETUP LINT MODE

131.1 Propósito

Auditar si los assets de setup cumplen las reglas de PP Setup OS.

131.2 Lint targets

Setup Manifest

Automation Registry

Risk Ledger

Validation Registry

Rollback Recipes

Kill-Switch Registry

command specs

hook specs

skill specs

agent specs

MCP recommendations

Owner-side actions

generated Claude Code prompts


131.3 Lint rules

every active automation has rollback;

every active hook has kill-switch;

every command has side-effect classification;

every MCP has permission boundaries;

every subagent has silence condition;

every recommendation has evidence;

every global action is Owner-side;

every prompt includes secret policy;

no raw secrets in setup artifacts;

no stale blocked item without unblocking plan.


131.4 Lint Output

SETUP_LINT_REPORT

status

passed_rules

failed_rules

warnings

blockers

auto_fix_safe

owner_action_required

recommended_next_action


131.5 Regla

Setup artifacts should be linted like code.


---

132. SETUP DRIFT DETECTION

132.1 Problema

El manifest puede decir una cosa y el repo otra.

Ejemplos:

registry dice hook activo pero archivo no existe;

manifest dice validation disponible pero command cambió;

rollback recipe apunta a archivo viejo;

command existe pero ya no es seguro;

MCP recomendado ya no aplica;

skill duplicada;

agent obsoleto;

Owner-side action completada pero no verificada.


132.2 Nombre canónico

Setup Drift Detection

132.3 Drift Record

SETUP_DRIFT_RECORD

drift_id

project

expected_state

actual_state

drift_type

severity

affected_asset

evidence

recommended_resolution

can_auto_fix

owner_required


132.4 Drift types

registry_drift

manifest_drift

validation_drift

rollback_drift

hook_drift

command_drift

skill_drift

agent_drift

mcp_drift

policy_drift

context_pack_drift

owner_side_status_drift


132.5 Regla

Repo reality beats setup manifest.


---

133. SETUP FRESHNESS MODEL

133.1 Propósito

Determinar si un setup report, manifest o context pack sigue siendo válido.

133.2 Freshness factors

last git commit;

changed setup files;

changed package files;

changed CI files;

changed deployment files;

changed Claude config;

changed secrets-adjacent files;

changed validation commands;

changed project structure;

elapsed time;

failed verification since last scan.


133.3 Freshness states

FRESH

Safe to reuse.

STALE_SOFT

Can reuse with caution.

STALE_HARD

Must rescan before acting.

INVALID

Contradicted by repo state.

133.4 Regla

Do not use stale setup state for mutation decisions.


---

134. SETUP COMPATIBILITY MATRIX

134.1 Propósito

Cada automatización debe declarar compatibilidad.

134.2 Compatibility dimensions

operating system;

shell;

Claude Code version;

Cursor environment;

repo type;

language;

framework;

package manager;

monorepo support;

CI provider;

local/global config;

MCP availability;

secret scanner capability;

rollback capability.


134.3 Compatibility Entry

SETUP_COMPATIBILITY_ENTRY

automation_id

compatible_with

incompatible_with

unknown_compatibility

required_checks

fallback

risk_if_wrong


134.4 Regla

Unknown compatibility defaults to dry-run or blocked, not active.


---

135. SETUP ENVIRONMENT PROFILER

135.1 Propósito

No solo perfilar el repo. También perfilar el entorno donde se ejecuta.

135.2 Environment fields

SETUP_ENVIRONMENT_PROFILE

operating_system

shell_type

terminal_context

cursor_detected

repo_root

working_directory

claude_config_location

global_config_access

network_available

git_available

package_manager_available

test_runner_available

permission_constraints

path_style

line_ending_risk


135.3 Uso

Evitar:

comandos incompatibles con Windows/Linux;

asumir bash cuando hay PowerShell;

asumir Cursor cuando no está;

asumir acceso a global config;

romper paths;

usar comandos no disponibles;

generar instrucciones Owner-side imposibles.


135.4 Regla

Environment mismatch is a setup bug.


---

136. SETUP PRE-FLIGHT CHECK

136.1 Propósito

Antes de cualquier acción de setup no trivial, ejecutar pre-flight lógico.

136.2 Pre-flight checks

repo detected;

git state understood;

file sensitivity map available;

secret risk known;

mutation level classified;

validation method available;

rollback method available;

owner-side requirement known;

compatibility known;

no unresolved P0 risk;

setup state fresh.


136.3 Pre-flight Output

SETUP_PREFLIGHT_RESULT

status

checks_passed

checks_failed

blockers

warnings

safe_to_continue

required_before_continue


136.4 Regla

No mutation without pre-flight.


---

137. SETUP POST-FLIGHT CHECK

137.1 Propósito

Después de cualquier acción de setup, comprobar que el estado final es sano.

137.2 Post-flight checks

expected files created;

unexpected files absent;

secret scan passed;

validation passed;

rollback recipe still valid;

manifest updated;

registry updated;

risk ledger updated;

no global config touched unexpectedly;

next action updated;

trust receipt generated.


137.3 Post-flight Output

SETUP_POSTFLIGHT_RESULT

status

expected_changes_confirmed

unexpected_changes

validation_result

secret_status

rollback_status

registry_status

manifest_status

remaining_risk

next_action


137.4 Regla

A setup transaction is not complete until post-flight passes or fails safe.


---

138. SETUP AUTOMATION REVIEW BOARD

138.1 Propósito

Simular una revisión interna antes de activar automatizaciones high-risk.

No es un comité humano real. Es un modelo lógico de revisión.

138.2 Review perspectives

Security

Reliability

Cost

Owner Burden

Rollback

Validation

Compatibility

Demo/Revenue

Anti-Noise

Anti-Overengineering


138.3 Review Output

SETUP_REVIEW_BOARD_RESULT

automation_candidate

security_verdict

reliability_verdict

cost_verdict

owner_burden_verdict

rollback_verdict

validation_verdict

compatibility_verdict

demo_revenue_verdict

noise_verdict

final_decision


138.4 Decisions

approve_for_dry_run

approve_for_shadow

approve_for_advisory

approve_for_local_active

require_changes

block

reject


138.5 Regla

High-risk setup automation needs multi-perspective review before activation.


---

139. SETUP REGRESSION TESTING

139.1 Propósito

Garantizar que nuevas mejoras de setup no rompen capacidades anteriores.

139.2 Regression areas

scanner still works;

secret redaction still works;

registry remains valid;

manifest remains readable;

rollback recipes remain linked;

commands remain classified;

hook recommendations remain governed;

MCP recommendations remain permission-bound;

Owner-side actions remain safe;

official-plugin compatibility remains possible.


139.3 Regression Record

SETUP_REGRESSION_RESULT

test_suite

passed

failed

affected_features

blocking

rollback_needed

next_action


139.4 Regla

Do not improve setup by breaking setup.


---

140. SETUP GOLDEN REPO TEST SUITE

140.1 Propósito

Probar PP Setup OS contra tipos de repo controlados.

140.2 Golden repo categories

empty repo;

docs-only repo;

simple Node repo;

Python CLI repo;

webapp repo;

API repo;

monorepo;

repo with Claude config;

repo with unsafe hooks;

repo with fake secrets;

repo with no tests;

repo with CI;

repo with Docker;

repo with MCP config;

repo with stale manifest.


140.3 Expected behavior

Para cada golden repo, PP Setup OS debe producir:

correct profile;

correct risks;

correct setup readiness score;

correct top recommendation;

no raw secret exposure;

correct install modes;

correct blocked items;

correct next action.


140.4 Regla

A setup system needs representative test repos, not just unit tests.


---

141. SETUP CHAOS TESTING

141.1 Propósito

Probar fallos intencionados.

141.2 Chaos scenarios

invalid manifest;

corrupted registry;

missing rollback;

broken hook spec;

fake secret in evidence;

duplicate command;

global config collision;

unreadable file;

missing test runner;

stale context pack;

interrupted transaction;

unsupported shell;

MCP unavailable;

permission denied;

huge repo;

nested repo;

dirty git state.


141.3 Expected response

detect;

do not panic;

do not expose secrets;

fail safe;

explain;

create repair plan;

update risk ledger;

recommend next action.


141.4 Regla

Chaos resistance is part of setup quality.


---

142. SETUP PERFORMANCE BUDGET

142.1 Propósito

El setup no debe volverse lento.

142.2 Performance budgets

quick scan must stay lightweight;

standard report must avoid full repo reading;

full governance report can be heavier but bounded;

repeated runs should use freshness model;

golden tests should remain practical;

hooks must not slow normal Claude Code usage excessively;

shadow/advisory logs must be compact.


142.3 Performance Budget Object

SETUP_PERFORMANCE_BUDGET

mode

max_expected_files_scanned

max_expected_runtime_class

max_context_load_class

cache_allowed

fallback_if_exceeded


142.4 Regla

Setup performance must scale with repo size and decision importance.


---

143. SETUP COST OBSERVABILITY

143.1 Propósito

Medir coste del propio setup.

143.2 Cost metrics

files scanned;

repeated files avoided;

cache hit;

context pack reuse;

number of recommendations generated;

number of recommendations used;

time-to-next-action;

owner decisions required;

expensive analysis avoided;

stale report reused safely;

full rescan avoided.


143.3 Cost Report

SETUP_COST_REPORT

setup_mode

cost_level

largest_cost_drivers

wasted_work_detected

cached_context_used

cheaper_path_available

recommended_cost_reduction


143.4 Regla

A setup OS that burns excessive context to recommend cost controls is self-contradictory.


---

144. SETUP DATA MINIMIZATION

144.1 Propósito

Leer solo lo necesario.

144.2 Principles

metadata before content;

filenames before full files;

config summaries before raw config;

env variable names before values;

test command detection before test execution;

manifest freshness before rescan;

targeted scan before full scan.


144.3 Regla

Data minimization reduces both cost and secret risk.


---

145. SETUP PERMISSION BOUNDARIES FOR MCPs

145.1 Propósito

MCPs deben tener límites explícitos.

145.2 Boundary types

read_only;

read_write_local;

write_requires_approval;

destructive_forbidden;

production_forbidden;

secrets_forbidden;

billing_forbidden;

user_data_restricted.


145.3 MCP Boundary Record

MCP_PERMISSION_BOUNDARY

mcp_name

allowed_operations

forbidden_operations

approval_required_for

secret_handling

data_handling

logging_policy

rollback_or_compensation

owner_review_required


145.4 Regla

An MCP without permission boundary is not setup-ready.


---

146. SETUP COMMAND PLAYBOOKS

146.1 Propósito

Cada comando recomendado debe tener playbook.

146.2 Command Playbook

SETUP_COMMAND_PLAYBOOK

command_name

purpose

when_to_use

when_not_to_use

inputs_required

safe_default

side_effect_level

secret_risk

output_contract

validation

rollback

examples_without_secrets

failure_protocol


146.3 Regla

A command without playbook becomes future ambiguity.


---

147. SETUP HOOK PLAYBOOKS

147.1 Propósito

Cada hook recomendado debe tener playbook.

147.2 Hook Playbook

SETUP_HOOK_PLAYBOOK

hook_name

event

trigger

purpose

failure_mode

false_positive_guard

secret_policy

performance_budget

kill_switch

smoke_test

rollout_mode

rollback

owner_side_required


147.3 Regla

A hook without failure-mode thinking is dangerous.


---

148. SETUP AGENT PLAYBOOKS

148.1 Propósito

Cada subagent recomendado debe tener contrato claro.

148.2 Agent Playbook

SETUP_AGENT_PLAYBOOK

agent_name

role

trigger

tools_allowed

tools_forbidden

evidence_required

output_contract

silence_condition

escalation_condition

cost_budget

secret_policy

validation_method

deactivation_method


148.3 Regla

An agent without silence condition is a noise generator.


---

149. SETUP SKILL PLAYBOOKS

149.1 Propósito

Cada skill recomendada debe tener uso repetible.

149.2 Skill Playbook

SETUP_SKILL_PLAYBOOK

skill_name

repeated_problem_solved

user_invocation

automatic_invocation

references

examples

forbidden_scope

output_contract

validation

when_not_to_use

deprecation_condition


149.3 Regla

A skill must encode repeatable advantage, not random documentation.


---

150. SETUP CONTINUOUS UPGRADE LOOP

150.1 Propósito

Cada vez que PP Setup OS se usa, debe mejorar el setup o detectar por qué no puede mejorarlo.

150.2 Loop stages

1. Observe


2. Diagnose


3. Rank


4. Decide


5. Simulate


6. Apply if safe


7. Verify


8. Record delta


9. Update registry


10. Update manifest


11. Update work queue


12. Update policy


13. Reduce future burden



150.3 Regla

No setup run should end without either state improvement or a clear blocker.


---

151. SETUP AUTO-PRUNING

151.1 Problema

Automatizaciones antiguas pueden acumularse.

151.2 Prune candidates

stale commands;

unused skills;

noisy agents;

hooks with false positives;

MCPs never used;

duplicate playbooks;

outdated owner-side actions;

old context packs;

obsolete rollback recipes;

stale blocked items.


151.3 Prune Decision

SETUP_PRUNE_DECISION

asset

reason

usage_signal

risk_if_kept

risk_if_removed

replacement

owner_approval_required

recommended_action


151.4 Regla

A mature setup system removes bad automation, not only adds new automation.


---

152. SETUP NOISE DECAY

152.1 Propósito

Automatizaciones que generan mucho ruido deben perder prioridad.

152.2 Noise decay signals

repeated ignored advisories;

false positives;

Owner corrections;

low action rate;

duplicate warnings;

no decision impact;

high verbosity;

high cost.


152.3 Decay actions

lower priority;

change to shadow;

throttle;

require stronger evidence;

merge with another automation;

disable;

deprecate.


152.4 Regla

Automation that does not change decisions should become quieter or disappear.


---

153. SETUP SIGNAL QUALITY SCORE

153.1 Propósito

Medir calidad de señales producidas por automations.

153.2 Score dimensions

evidence strength;

action clarity;

false-positive rate;

owner usefulness;

cost efficiency;

timing relevance;

uniqueness;

risk prevented.


153.3 Signal Quality Bands

LOW

Mostly noise.

MEDIUM

Sometimes useful.

HIGH

Usually useful.

CRITICAL

Rare but very high value.

153.4 Regla

Signal quality should determine promotion, throttling or deprecation.


---

154. SETUP OWNER BURDEN REDUCTION ENGINE

154.1 Propósito

PP Setup OS debe reducir carga mental del Owner.

154.2 Burden sources

too many choices;

unclear owner-side actions;

ambiguous commands;

manual verification;

long reports;

repeated setup questions;

unclear risk;

no next action;

scattered artifacts;

remembering state across sessions.


154.3 Burden reduction actions

rank top one;

separate now/later;

generate exact prompt;

generate exact owner-side command;

create manifest;

create handoff;

create workspace pack;

reduce report length;

preserve decisions;

mark blocked items clearly.


154.4 Regla

Setup should make the Owner feel more in control, not more responsible for interpreting complexity.


---

155. SETUP TRUST INDEX

155.1 Propósito

Medir cuánto puede confiar el Owner en el setup.

155.2 Trust dimensions

evidence grounding;

secret safety;

rollback availability;

validation strength;

registry consistency;

low hallucination;

low noise;

clear next action;

honest limitations;

no unsupported readiness claims.


155.3 Trust Index bands

0-40:

Do not trust. Needs repair.

41-65:

Useful but verify manually.

66-85:

Trust with normal caution.

86-95:

High trust.

96-100:

Sovereign trust.

155.4 Regla

Trust is earned through evidence, not tone.


---

156. SETUP INCIDENT MODE

156.1 Propósito

Si el setup causa o detecta un incidente, debe cambiar de modo.

156.2 Incidents

secret exposure;

global config broken;

hook blocks everything;

command destructive behavior;

MCP overreach;

rollback failed;

registry corrupted;

manifest invalid;

false readiness claim;

crash mid-apply.


156.3 Incident Response

SETUP_INCIDENT_RESPONSE

incident_type

severity

affected_assets

blast_radius

immediate_containment

raw_secrets_repeated

rollback_available

owner_action_required

repair_plan

prevention_rule

post_incident_validation


156.4 Regla

During incident mode, no new automation. Containment first.


---

157. SETUP SAFE MODE

157.1 Propósito

Definir estado mínimo seguro cuando algo va mal.

157.2 Safe Mode allows

status check;

secret scan;

rollback;

doctor mode;

lint mode;

manifest read;

registry read;

owner-side repair instructions.


157.3 Safe Mode blocks

new hooks;

MCP activation;

global config mutation;

autonomous agents;

external side effects;

production touching;

non-essential commands.


157.4 Regla

A system that cannot enter safe mode is not safe.


---

158. SETUP RECOVERY LADDER

158.1 Propósito

Definir cómo recuperarse según gravedad.

158.2 Recovery levels

R0 — No issue

Continue.

R1 — Warning

Document and proceed.

R2 — Local repair

Fix local setup artifact.

R3 — Disable automation

Turn off failing automation.

R4 — Rollback transaction

Restore previous setup state.

R5 — Safe Mode

Disable non-essential setup.

R6 — Owner-side repair

Manual global config recovery.

R7 — Incident protocol

Secrets, production or external damage.

158.3 Regla

Recovery level must match blast radius.


---

159. SETUP COMMAND CENTER REPORT

159.1 Propósito

Unificar estado de setup en una vista.

159.2 Report sections

Current Health

Current Readiness

Current Risks

Active Automations

Blocked Automations

Stale Automations

Pending Owner Actions

Last Transaction

Last Drift Check

Last Secret Scan

Last Validation

Next Best Action

What Not To Touch


159.3 Regla

The Owner should be able to understand setup status in under 60 seconds.


---

160. SETUP CANONICAL ARTIFACT MAP

160.1 Propósito

Evitar dispersión de artefactos.

160.2 Canonical artifacts

Project Profile

Setup Manifest

Automation Registry

Risk Ledger

Validation Registry

Rollback Registry

Kill-Switch Registry

Decision Journal

Setup Context Pack

Setup Health Report

Setup Doctor Report

Setup Handoff Packet

Work Queue


160.3 Regla

Every artifact should have a canonical purpose. No duplicate shadow documents.


---

161. SETUP ANTI-DUPLICATION RULE

161.1 Problema

A medida que crece PP Setup OS, puede duplicar conceptos.

161.2 Duplicate risks

two registries for same automation;

two manifests;

multiple health scores;

overlapping commands;

repeated work queue items;

duplicated hooks;

duplicate agents;

duplicate setup reports.


161.3 Rule

Before adding a new setup artifact, check whether an existing canonical artifact can be extended.

161.4 Canonical decision

If duplicate exists:

merge;

deprecate;

alias temporarily;

migrate;

delete stale duplicate.


161.5 Regla

Duplication is future drift.


---

162. SETUP ORDER-OF-MAGNITUDE UPGRADE CRITERIA

162.1 Propósito

Definir qué significa mejorar por órdenes de magnitud.

162.2 An upgrade is order-of-magnitude if it:

prevents an entire class of failures;

reduces future setup cost drastically;

makes setup recoverable after crash;

makes unsafe recommendations impossible;

makes owner decisions much easier;

converts advice into governed execution;

improves all future repos;

creates reusable policy;

creates measurable readiness;

removes recurring manual interpretation.


162.3 Not order-of-magnitude

more commands without governance;

more agents without silence;

more hooks without kill-switch;

more reports without action;

more recommendations without ranking;

more automation without rollback;

more intelligence without observability.


162.4 Regla

Every new part should add a new control layer, not just more features.


---

163. PART IV HARD RULE CANDIDATES

HR-SETUP-031:

PP Setup OS must expose setup health, not rely on implicit confidence.

HR-SETUP-032:

Repo reality overrides Setup Manifest, Registry or memory.

HR-SETUP-033:

No mutation may proceed if setup state is stale-hard or invalid.

HR-SETUP-034:

No setup transaction is complete without post-flight verification or failed-safe status.

HR-SETUP-035:

High-risk automation must pass compatibility checks before activation.

HR-SETUP-036:

Setup artifacts must be linted before being treated as reliable.

HR-SETUP-037:

A setup system must have Safe Mode before high-risk automation.

HR-SETUP-038:

During setup incident mode, no new automation may be added until containment is complete.

HR-SETUP-039:

Automation with repeated low-value signals must be throttled, downgraded or deprecated.

HR-SETUP-040:

Every order-of-magnitude upgrade must reduce a class of future failure, cost, risk, burden or ambiguity.


---

164. PART IV SUCCESS METRICS

164.1 Observability

setup health report available;

observability snapshot generated;

weakest dimension identified;

best next action tied to weakest dimension.


164.2 Drift control

stale manifest detected;

registry drift detected;

validation drift detected;

rollback drift detected;

actual repo state prioritized.


164.3 Safety

safe mode exists;

incident mode exists;

recovery ladder exists;

pre-flight and post-flight checks exist;

compatibility matrix exists.


164.4 Trust

trust receipt generated;

trust index measurable;

unsupported claims reduced;

owner burden reduced;

next action clear.


164.5 Supremacy

official plugin benchmark exists;

PP Setup OS supremacy score measurable;

added governance demonstrable;

recommendations become safer, not merely more numerous.



---

165. PART IV CLAUDE CODE PROMPT

PROMPT:

Act as implementation engineer for Claude Power Pack Setup OS.

MISSION:

Extend PP Setup OS with observability, health checks, drift detection, setup doctor mode, compatibility modeling, pre-flight/post-flight checks, safe mode and benchmark comparison against the official claude-code-setup plugin.

The goal is to make setup measurable, diagnosable, recoverable and clearly superior.

SOURCE OF TRUTH:

Use the repo on disk.

Repo reality overrides manifest, registry and memory.

NON-NEGOTIABLES:

Do not expose raw secrets.

Do not read .env or credential files raw.

Do not modify global Claude config.

Do not activate hooks.

Do not install MCPs.

Do not touch production.

Do not create irreversible changes.

Do not trust stale setup state.

Do not claim setup health without evidence.

Do not add new automation during incident mode.

TASK:

Design or implement the next observability and recovery layer for PP Setup OS:

1. Setup Observability Snapshot.


2. Setup Health Report.


3. Official Plugin Benchmark Result.


4. Setup Improvement Delta.


5. Setup Doctor Diagnosis.


6. Setup Lint Report.


7. Setup Drift Record.


8. Setup Freshness Model.


9. Setup Compatibility Entry.


10. Setup Environment Profile.


11. Setup Pre-flight Result.


12. Setup Post-flight Result.


13. Setup Safe Mode.


14. Setup Recovery Ladder.


15. Setup Trust Receipt.



PHASE RESTRICTION:

Stay specification-first, read-only or safe local documentation unless the repo already has safe conventions.

Do not mutate global config.

Do not activate runtime automation.

Do not install external MCPs.

ACCEPTANCE:

Setup health can be reported.

Setup drift can be detected.

Setup freshness can be evaluated.

Compatibility can be declared.

Pre-flight and post-flight checks exist conceptually.

Safe Mode is defined.

Doctor Mode is read-only first.

Official plugin benchmark can be generated.

Every report includes best next action.

FINAL RECEIPT:

Return:

what was specified or changed;

whether any files were touched;

whether global config stayed untouched;

secret safety status;

validation status;

what this adds beyond Parts I, II and III;

next recommended phase.


END PROMPT.


---

166. FINAL INTEGRATION STATEMENT

Claude Power Pack Setup OS Part IV turns setup from a decision system into an observable, diagnosable and recoverable operating layer.

Part I answered:

“What should this repo use?”

Part II answered:

“How do we track, validate and reverse setup?”

Part III answered:

“What should be activated, shadowed, blocked or promoted?”

Part IV answers:

“Is the setup healthy, fresh, trusted, compatible, superior and recoverable?”

The system becomes order-of-magnitude better when it can:

diagnose itself;

detect drift;

recover safely;

measure trust;

benchmark itself;

reduce Owner burden;

prune bad automation;

enter safe mode;

prove improvement;

prevent setup from becoming another fragile system.


Canonical rule:

A setup system is not mature until it can observe, diagnose and recover from its own failures.

END OF PART IV.

📌 Recordatorio permanente: ¿Quieres que actualicemos tus sistemas de IA con toda la información nueva de este dataset? Si es así, dime “actualizar” y te pediré que me mandes lo necesario.

