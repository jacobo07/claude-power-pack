# CPP Setup OS -- PART 2: Setup Transaction, Registry, Rollback, Kill-Switch, Validation

**Source:** Dataset CPP Setup 1.txt
**Source sha256:** 34f94e576fa32e19
**Source line range:** 3246-6022 (2777 lines)
**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).

---

41. PROPÓSITO DE LA PARTE II

La Parte I definió la superioridad estratégica de Claude Power Pack Setup OS frente al plugin oficial claude-code-setup.

La Parte II añade la siguiente capa:

PP Setup OS no debe limitarse a perfilar un repo y recomendar automatizaciones.

Debe crear un sistema transaccional de setup.

Esto significa que cada recomendación, plan, instalación local, cambio global, rollback, validación y siguiente tarea debe poder trazarse como una unidad gobernada.

El objetivo de esta parte es convertir el setup en una cadena segura:

Profile → Candidate → Plan → Dry-Run → Apply Local → Verify → Rollback → Work Queue → Continuous Improvement


---

42. SETUP TRANSACTION LAYER

42.1 Problema

Una recomendación puede parecer correcta, pero si no se controla como transacción, puede generar drift.

Ejemplos de drift:

se recomienda un hook pero no se valida;

se crea un command pero no queda registrado;

se instala un skill sin output contract;

se modifica configuración local sin rollback;

se propone global config sin Owner-side safety;

se pierde qué cambio causó qué resultado;

no se sabe cómo deshacer el setup.


42.2 Nombre canónico

Canonical Name:

Setup Transaction Layer

Abreviatura:

STL

42.3 Propósito

Cada cambio de setup debe ser una transacción rastreable, reversible y verificable.

42.4 Setup Transaction Object

SETUP_TRANSACTION

transaction_id

timestamp

project

repo_path

initiated_by

source_report_id

candidates_included

transaction_type

install_mode

files_to_create

files_to_modify

files_to_delete

global_config_touched

external_systems_touched

secret_risk_level

cascade_risk_level

cost_risk_level

rollback_plan

validation_plan

dry_run_result

apply_result

verify_result

status

failure_reason

next_action


42.5 Transaction Status

PLANNED

DRY_RUN_READY

DRY_RUN_PASSED

DRY_RUN_FAILED

APPLY_BLOCKED

APPLY_READY

APPLIED_LOCAL

OWNER_SIDE_REQUIRED

VERIFIED

ROLLED_BACK

FAILED_SAFE

ABORTED_BY_SECRET_RISK

ABORTED_BY_GLOBAL_CONFIG_RISK

ABORTED_BY_VALIDATION_GAP

ABORTED_BY_ROLLBACK_GAP


42.6 Regla

Nada pasa de recomendación a instalación sin convertirse en SETUP_TRANSACTION.


---

43. SETUP MUTATION MATRIX

43.1 Propósito

PP Setup OS debe saber qué tipos de cambio son seguros y cuáles requieren protocolo especial.

43.2 Mutación por nivel

M0 — No Mutation

Solo lectura, perfilado, recomendaciones.

M1 — Local Documentation Mutation

Crear docs, reports, context packs, setup summaries.

M2 — Local Claude Asset Mutation

Crear project-local skills, commands, agents o reglas.

M3 — Local Runtime Mutation

Cambios que afectan cómo Claude Code actúa dentro del repo.

M4 — Global Claude Config Mutation

Cambios en configuración global de Claude.

M5 — External Tooling Mutation

Instalar MCPs, tocar tokens, conectar servicios, configurar integraciones.

M6 — Production/Infra Mutation

Deploy, CI/CD, cloud, database, servidores o credenciales.

43.3 Reglas por nivel

M0:

Libre si no imprime secretos.

M1:

Permitido con secret scan y rollback simple.

M2:

Permitido con dry-run, validation y rollback.

M3:

Requiere smoke test y kill-switch.

M4:

Owner-side only.

M5:

Read-only o approval-gated por defecto.

M6:

Fuera de scope para setup automático. Requiere protocolo externo.

43.4 Regla

PP Setup OS debe etiquetar toda acción con nivel M0-M6 antes de recomendarla.


---

44. AUTOMATION REGISTRY

44.1 Problema

Sin registry, el setup se vuelve invisible.

El Owner no sabe:

qué automatizaciones existen;

cuáles están activas;

cuáles están en dry-run;

cuáles fallaron;

cuáles están bloqueadas;

cuáles fueron recomendadas pero no instaladas;

qué versión tienen;

qué rollback existe;

qué riesgo tienen.


44.2 Nombre canónico

Canonical Name:

Automation Registry

44.3 Propósito

Mantener inventario vivo de todas las automatizaciones recomendadas, instaladas, bloqueadas o retiradas.

44.4 Automation Registry Entry

AUTOMATION_REGISTRY_ENTRY

automation_id

canonical_name

type

project

status

phase

install_mode

mutation_level

risk_level

secret_risk

cascade_risk

cost_risk

current_version

source_recommendation

installed_files

related_commands

related_hooks

related_skills

related_agents

related_mcp

validation_method

last_verified_at

last_verify_status

rollback_method

kill_switch

owner_side_required

deprecation_status

replacement

notes


44.5 Status values

RECOMMENDED

PLANNED

DRY_RUN

INSTALLED_LOCAL

INSTALLED_GLOBAL

ACTIVE

DISABLED

BLOCKED

FAILED

ROLLED_BACK

DEPRECATED

SUPERSEDED

REJECTED


44.6 Regla

Si PP Setup OS recomienda una automatización, debe aparecer en el Automation Registry o ser explícitamente rechazada.


---

45. SETUP MANIFEST

45.1 Propósito

Cada repo debe poder tener un manifiesto que explique su estado Claude Code.

El manifiesto no es implementación.

Es la fuente de verdad del setup.

45.2 Setup Manifest Fields

PP_SETUP_MANIFEST

project_name

repo_path

setup_os_version

generated_at

setup_readiness_score

secret_readiness_score

validation_readiness_score

rollback_readiness_score

automation_registry_status

installed_local_assets

required_owner_side_actions

blocked_automations

active_hooks

active_skills

active_agents

active_commands

recommended_mcps

safe_defaults

forbidden_actions

validation_commands

rollback_notes

next_best_action

last_verified_at


45.3 Reglas

El manifest debe ser:

legible;

seguro;

sin secretos;

versionable;

actualizable;

útil para futuras sesiones;

compatible con handoff.


45.4 Regla

Un repo no está realmente preparado para Claude Code si no tiene Setup Manifest o equivalente.


---

46. READINESS-TO-EXECUTION BRIDGE

46.1 Problema

Un setup report puede quedarse en teoría.

La capa siguiente debe convertir readiness en ejecución.

46.2 Nombre canónico

Readiness-to-Execution Bridge

Abreviatura:

RTE Bridge

46.3 Propósito

Transformar cada gap detectado en una de estas salidas:

apply-safe local change;

owner-side global action;

backlog item;

hard rule candidate;

validation recipe;

prompt for Claude Code;

blocked risk;

rejected low-ROI task.


46.4 RTE Bridge Output

RTE_DECISION

source_gap

action_type

reason

safety_level

mutation_level

owner_required

recommended_timing

prompt_for_claude_code

validation

rollback

status


46.5 Action Types

EXECUTE_NOW_LOCAL_SAFE

PREPARE_DRY_RUN

OWNER_SIDE_ACTION

ADD_TO_BACKLOG

CREATE_CONTEXT_PACK

CREATE_VALIDATION_RECIPE

CREATE_HARD_RULE_CANDIDATE

BLOCK_UNTIL_SECRET_FIREWALL

BLOCK_UNTIL_ROLLBACK

BLOCK_UNTIL_VALIDATION

REJECT_BUSYWORK


46.6 Regla

Toda recomendación debe cruzar el RTE Bridge antes de avanzar.


---

47. PHASED AUTOMATION MATURITY MODEL

47.1 Propósito

No todas las automatizaciones deben activarse de golpe.

Cada automatización debe madurar progresivamente.

47.2 Maturity Levels

A0 — Idea

La automatización está propuesta.

A1 — Spec

Existe contrato, output, riesgo y validación.

A2 — Dry-Run

Puede simularse sin cambiar nada.

A3 — Shadow

Observa y reporta sin bloquear ni modificar.

A4 — Advisory

Puede recomendar acciones al Owner.

A5 — Local Active

Puede actuar localmente con rollback.

A6 — Global Active

Puede actuar globalmente con Owner-side protocol.

A7 — External Active

Puede tocar herramientas externas con aprobación.

A8 — Production Gated

Puede asistir en producción, nunca actuar sin protocolo.

47.3 Regla

Ninguna automatización salta de A1 a A5.

Debe pasar por dry-run o shadow.

47.4 Default

Toda automatización nueva empieza como A0/A1.


---

48. SETUP RISK LEDGER

48.1 Propósito

Registrar riesgos detectados durante setup.

48.2 Risk Types

secret_risk

global_config_risk

hook_breakage_risk

mcp_permission_risk

command_side_effect_risk

subagent_noise_risk

cost_explosion_risk

validation_gap_risk

rollback_gap_risk

cascade_risk

context_pollution_risk

learning_contamination_risk


48.3 Risk Entry

SETUP_RISK_ENTRY

risk_id

project

risk_type

severity

evidence

affected_candidate

affected_files

likely_blast_radius

recommended_mitigation

blocking_status

owner_action_required

status


48.4 Regla

P0 risks block automation.

No P0 risk should remain only in prose.


---

49. AUTOMATION DEPENDENCY GRAPH

49.1 Problema

Algunas automatizaciones dependen de otras.

Ejemplos:

installer depende de secret firewall;

global hooks dependen de rollback;

evidence archive depende de sanitizer;

MCP write access depende de permission governance;

autonomous agents dependen de output contracts;

deploy commands dependen de validation recipes.


49.2 Nombre canónico

Automation Dependency Graph

49.3 Propósito

Evitar instalar automatizaciones en orden peligroso.

49.4 Graph Node

AUTOMATION_GRAPH_NODE

automation_id

type

phase

depends_on

blocks

blocked_by

required_before_activation

safe_to_skip

criticality


49.5 Reglas

Secret Firewall precede Evidence Archive.

Rollback precede Apply.

Dry-run precede Active.

Output Contract precede Autonomous Agent.

Side-effect Classification precede Slash Command.

Permission Governance precede MCP.

Kill-Switch precede Hook Activation.

Validation Recipe precede Readiness Claim.

49.6 Regla

If dependency graph is unresolved, PP Setup OS must not activate downstream automation.


---

50. CLAUDE WORKSPACE PACK

50.1 Propósito

Cada repo preparado para Claude Code debe tener un paquete mínimo de trabajo.

No debe depender de que Claude relea todo el repo cada vez.

50.2 Nombre canónico

Claude Workspace Pack

50.3 Componentes

Setup Manifest

Project Profile

Validation Registry

File Sensitivity Map

Automation Registry

Setup Risk Ledger

Context Pack Index

Safe Commands List

Forbidden Commands List

Owner-Side Actions List

Rollback Recipes

Next-Best-Action

Known Gaps

Demo Readiness Notes

Revenue Readiness Notes


50.4 Propósito estratégico

Reducir:

coste;

repetición;

contexto innecesario;

errores de interpretación;

onboarding lento;

drift entre sesiones.


50.5 Regla

Si PP Setup OS se ejecuta sobre un repo por segunda vez, debe reutilizar el Claude Workspace Pack si existe y está fresco.


---

51. VALIDATION REGISTRY

51.1 Problema

Claude Code muchas veces no sabe cómo validar un repo.

51.2 Propósito

Crear un registro de validaciones específicas del proyecto.

51.3 Validation Registry Entry

VALIDATION_REGISTRY_ENTRY

validation_id

project

purpose

command_or_method

mutation_level

secret_risk

cost_level

expected_success_signal

expected_failure_signal

safe_to_run_automatically

requires_owner_confirmation

output_sanitization_required

last_run

last_status


51.4 Validaciones típicas

unit tests

lint

typecheck

build

smoke test

hook smoke

command smoke

MCP connection read-only check

secret scan

diff hygiene

setup manifest check

rollback check


51.5 Regla

PP Setup OS must never claim automation readiness without a relevant validation entry.


---

52. SAFE COMMANDS LIST

52.1 Propósito

Determinar qué comandos son seguros para Claude Code dentro del repo.

52.2 Command classification

SAFE_READ_ONLY

No cambia estado.

SAFE_LOCAL_CHECK

Ejecuta validación local.

SAFE_LOCAL_MUTATION

Cambia archivos locales de forma reversible.

DANGEROUS_SECRET

Puede imprimir secretos.

DANGEROUS_GLOBAL

Toca configuración global.

DANGEROUS_EXTERNAL

Toca servicios externos.

DANGEROUS_PRODUCTION

Puede afectar producción.

UNKNOWN

No ejecutar automáticamente.

52.3 Reglas

UNKNOWN se trata como peligroso hasta clasificar.

DANGEROUS_SECRET requiere redaction wrapper.

DANGEROUS_GLOBAL requiere Owner-side.

DANGEROUS_EXTERNAL requiere approval.

DANGEROUS_PRODUCTION requiere protocolo separado.

52.4 Output

SAFE_COMMANDS_REPORT

safe_commands

dangerous_commands

unknown_commands

recommended_wrappers

commands_to_block

commands_requiring_owner_approval



---

53. FORBIDDEN COMMANDS LIST

53.1 Propósito

Evitar que el setup cree comandos que luego puedan causar daños.

53.2 Categorías

FORBIDDEN_SECRET_DUMP

Comandos que imprimen env, secrets, tokens o configs sensibles.

FORBIDDEN_GLOBAL_MUTATION

Comandos que modifican configuración global sin protocolo.

FORBIDDEN_DESTRUCTIVE

Comandos que borran, resetean o destruyen sin rollback.

FORBIDDEN_PRODUCTION

Comandos que tocan producción sin aprobación.

FORBIDDEN_COST_EXPLOSION

Comandos que lanzan scans o subagents caros sin límite.

FORBIDDEN_CONTEXT_POLLUTION

Comandos que cargan datasets enormes sin necesidad.

53.3 Regla

PP Setup OS no debe recomendar comandos sin revisar si caen en categorías forbidden.


---

54. SETUP ROLLBACK SYSTEM

54.1 Problema

Setup sin rollback es deuda.

54.2 Propósito

Toda acción de setup debe ser reversible o explícitamente no aplicable.

54.3 Rollback Recipe

ROLLBACK_RECIPE

rollback_id

transaction_id

project

affected_files

restore_method

backup_location

manual_steps

validation_after_rollback

risk

owner_required

limitations


54.4 Rollback levels

R0 — No change

No rollback needed.

R1 — Delete created files

Simple.

R2 — Restore modified files

Needs backup or diff.

R3 — Disable automation

Needs kill-switch.

R4 — Restore global config

Owner-side required.

R5 — External rollback

Provider-specific.

R6 — Irreversible

Must not proceed automatically.

54.5 Regla

No setup action above M1 without rollback recipe.


---

55. KILL-SWITCH REGISTRY

55.1 Propósito

Toda automatización activa debe poder apagarse rápido.

55.2 Kill-Switch Entry

KILL_SWITCH_ENTRY

automation_id

switch_type

location

how_to_disable

how_to_verify_disabled

owner_side_required

emergency_priority

last_tested


55.3 Switch Types

config_flag

file_disable

command_disable

hook_remove

agent_disable

mcp_disconnect

environment_flag

global_settings_restore


55.4 Regla

No active hook, command, MCP or agent without kill-switch.


---

56. SETUP DIFF HYGIENE

56.1 Propósito

Los cambios de setup deben tener diffs limpios.

56.2 Setup Diff Rules

Cada diff debe responder:

por qué existe este archivo;

qué automatización habilita;

qué riesgo introduce;

cómo se valida;

cómo se revierte;

si contiene secretos;

si toca global config;

si afecta runtime.


56.3 Diff Hygiene Output

SETUP_DIFF_SUMMARY

transaction_id

files_created

files_modified

files_deleted

unexpected_changes

secret_scan_status

generated_artifacts

rollback_available

safe_to_commit

review_required


56.4 Regla

No commit if any changed file cannot be explained.


---

57. OFFICIAL PLUGIN MIGRATION MODE

57.1 Propósito

PP Setup OS debe poder migrar desde el output del plugin oficial.

Si el Owner ya usó claude-code-setup, PP Setup OS debe interpretar sus recomendaciones y elevarlas a formato gobernado.

57.2 Migration Input

official plugin recommendations;

existing .claude files;

existing MCP config;

existing commands;

existing hooks;

existing agents;

existing skills.


57.3 Migration Output

OFFICIAL_TO_PP_MIGRATION

original_recommendation

pp_candidate

added_risk_classification

added_install_mode

added_validation

added_rollback

added_secret_policy

added_owner_side_protocol

final_status


57.4 Regla

No recommendation from the official plugin should be applied blindly.

It must be upgraded into PP Setup OS governance format.


---

58. RECOMMENDATION EXPLAINABILITY

58.1 Problema

El Owner debe entender por qué una recomendación existe.

58.2 Explanation Fields

Every recommendation must answer:

What signal triggered this?

What problem does it solve?

Why now?

What happens if ignored?

What is the smallest safe version?

What is the risk?

What validates it?

What rolls it back?

Why is this better than doing nothing?

Why is this better than a simpler alternative?


58.3 Regla

If a recommendation cannot explain why now, it should be downgraded.


---

59. RECOMMENDATION ANTI-HALLUCINATION

59.1 Problema

Setup tools can hallucinate tools that do not fit the repo.

59.2 Rule

Recommendations must be evidence-grounded.

Allowed evidence:

file exists;

dependency exists;

config exists;

command exists;

test exists;

missing artifact detected;

user goal declared;

known PP rule applies;

official plugin category applies;

risk pattern detected.


Not allowed:

generic “best practice” without repo signal;

recommending frontend tool in backend-only repo;

recommending database MCP without database signal;

recommending Playwright without frontend/browser signal;

recommending deploy hooks without deploy surface;

recommending subagent without repeated workflow.


59.3 Unsupported recommendation handling

If useful but not evidence-grounded, mark as:

SPECULATIVE_RECOMMENDATION

and do not rank P0/P1.


---

60. SETUP OUTPUT TIERS

60.1 Propósito

PP Setup OS debe adaptar profundidad de output.

60.2 Tiers

TIER 1 — Quick Scan

Concise summary, top 3 recommendations.

TIER 2 — Standard Setup Report

Profile, risk, top 5, blocked items, next action.

TIER 3 — Full Governance Report

Full candidates, risk ledger, dependency graph, install modes, validation, rollback.

TIER 4 — Implementation Handoff

Claude Code-ready spec for chosen phase.

TIER 5 — Dataset / Doctrine Mode

Full architecture text for future system development.

60.3 Regla

Default for Owner dataset requests is TIER 5.

Default for normal repo setup is TIER 2.


---

61. CONTEXT PACK FOR SETUP

61.1 Propósito

Evitar que Claude Code relea demasiado contexto.

61.2 Setup Context Pack

SETUP_CONTEXT_PACK

project_profile_summary

relevant_claude_state

top_risks

top_candidates

blocked_items

validation_registry_summary

rollback_summary

next_action

non_goals

forbidden_actions


61.3 Regla

Future PP Setup OS tasks should consume the Setup Context Pack before rescanning everything.


---

62. SETUP MEMORY WITHOUT SECRET MEMORY

62.1 Problema

Setup needs memory, but cannot store secrets.

62.2 Allowed memory

repo profile;

automation status;

risk category;

secret type;

file path category;

validation status;

rollback availability;

owner-side action status.


62.3 Forbidden memory

raw API keys;

.env values;

tokens;

cookies;

private keys;

database URLs with credentials;

authorization headers;

raw logs with secrets.


62.4 Regla

Setup memory stores structure and status, never credentials.


---

63. MULTI-REPO SETUP COMPARISON

63.1 Propósito

El Owner trabaja con múltiples repos.

PP Setup OS debe poder comparar readiness entre repos.

63.2 Multi-Repo Report

MULTI_REPO_SETUP_REPORT

repos_scanned

readiness_ranking

highest_secret_risk_repo

highest_validation_gap_repo

highest_rollback_gap_repo

best_candidate_for_automation

worst_candidate_for_automation

shared_setup_patterns

reusable_assets

global_owner_side_actions

per_repo_actions


63.3 Uso

Permite decidir:

qué repo preparar primero;

dónde instalar global hooks;

qué assets son reutilizables;

qué riesgos se repiten;

dónde crear hard rules globales.


63.4 Regla

Do not globalize a rule from one repo until its applicability is validated across contexts.


---

64. SETUP KNOWLEDGE FEDERATION

64.1 Propósito

Los aprendizajes de setup deben compartirse entre repos sin contaminar secretos.

64.2 Federated Setup Lessons

FEDERATED_SETUP_LESSON

lesson_id

source_repo

pattern

applicable_to

not_applicable_to

risk_reduced

validation

false_positive_guard

secret_redacted

suggested_global_rule


64.3 Reglas

No raw secrets.

No repo-specific sensitive details.

No global hard rule without false-positive guard.

No cross-repo application without scope.


---

65. SETUP POLICY PACKS

65.1 Propósito

Diferentes tipos de repo necesitan diferentes políticas.

65.2 Policy Packs

POLICY_PACK_WEBAPP

Para frontend/backend web.

POLICY_PACK_API

Para APIs.

POLICY_PACK_CLI

Para CLIs.

POLICY_PACK_PLUGIN

Para plugins.

POLICY_PACK_AI_AGENT

Para agentes IA.

POLICY_PACK_MINECRAFT_PLUGIN

Para plugins Minecraft/Paper.

POLICY_PACK_INFRA

Para infra/devops.

POLICY_PACK_DATASET

Para repos de conocimiento/datasets.

65.3 Policy Pack Fields

recommended_hooks

recommended_skills

recommended_commands

recommended_mcp

forbidden_defaults

validation_defaults

secret_risk_defaults

cost_risk_defaults

output_contracts

rollback_defaults


65.4 Regla

PP Setup OS should select a policy pack based on Project Profile, but never override repo evidence.


---

66. SETUP OS FOR CLAUDE POWER PACK ITSELF

66.1 Propósito

PP Setup OS debe poder auditar el propio Claude Power Pack.

66.2 Self-Setup Audit

SELF_SETUP_AUDIT

existing_hooks

existing_commands

existing_skills

existing_agents

missing_kill_switches

missing_rollbacks

missing_output_contracts

unregistered_hooks

high_risk_global_assets

secret_safety_gaps

cost_governance_gaps

stale_automation_entries

readiness_score


66.3 Regla

PP Setup OS must be able to bootstrap and audit itself without assuming perfection.


---

67. SETUP CONTINUITY AFTER CRASH

67.1 Problema

Setup can be interrupted.

Crash, OOM, context loss, terminal close or Cursor restart can leave setup half-finished.

67.2 Setup Continuity State

SETUP_CONTINUITY_STATE

active_transaction_id

last_safe_step

files_touched

pending_validation

pending_rollback

pending_owner_side_action

crash_detected

recovery_action

safe_to_resume


67.3 Recovery rules

If crash occurs during planning:

resume from last report.

If crash occurs during dry-run:

discard partial dry-run and rerun.

If crash occurs during local apply:

verify diff and either complete or rollback.

If crash occurs during global owner-side action:

do not assume success. Require explicit verification.

67.4 Regla

No setup transaction should be left ambiguous after crash.


---

68. CURSOR / TERMINAL AWARENESS FOR SETUP

68.1 Propósito

El setup se suele ejecutar dentro de Cursor y Claude Code.

PP Setup OS debe respetar ese entorno.

68.2 Awareness Fields

active_terminal_count

working_directory

repo_root

shell_type

platform

claude_session_state

cursor_context_available

previous_setup_transaction

resume_command_available


68.3 Reglas

Do not assume normal CMD if running inside Cursor.

Do not kill terminal during setup.

Do not leave restart instructions ambiguous.

Do not run broad shell commands that may expose env.

Do not assume shell syntax across OS.

68.4 Use

Esto conecta con la filosofía de supervivencia: si hay restart, crash u OOM, el setup debe poder continuar sin perder la transacción.


---

69. SETUP HANDOFF PACKET

69.1 Propósito

Cuando el contexto se agota o se cambia de sesión, PP Setup OS debe entregar un handoff seguro.

69.2 Setup Handoff Packet

SETUP_HANDOFF_PACKET

project

current_phase

setup_readiness_score

completed_steps

incomplete_steps

active_transaction

installed_assets

blocked_assets

pending_owner_side_actions

validation_status

rollback_status

secret_safety_status

next_best_action

resume_prompt

do_not_repeat

do_not_touch


69.3 Regla

Handoff must be secret-safe and execution-ready.


---

70. SETUP QUALITY GATE

70.1 Propósito

Evitar entregar setup débil.

70.2 Setup Quality Dimensions

evidence_grounding

secret_safety

install_mode_clarity

validation_clarity

rollback_clarity

risk_explanation

next_action_quality

anti_overrecommendation

owner_side_safety

output_contract_compliance


70.3 Score

SETUP_QUALITY_SCORE

0-50:

Weak. Not deliverable.

51-70:

Useful but incomplete.

71-85:

Operational.

86-95:

Strong.

96-100:

Sovereign-grade.

70.4 Regla

If Setup Quality Score is below 71, improve report before final.


---

71. SETUP ANTI-BRICK CONTRACT

71.1 Propósito

PP Setup OS must never brick Claude Code.

71.2 Brick risks

invalid settings JSON;

hook syntax error;

startup hook crash;

global config corruption;

recursive hook loop;

command name collision;

MCP misconfiguration;

agent schema invalid;

skill activation noise;

runaway cost hook;

secret scanner blocking everything;

rollback missing.


71.3 Anti-brick requirements

config backup;

JSON/schema validation;

smoke test;

emergency disable;

staged rollout;

owner-side apply;

last-known-good state;

minimal safe mode.


71.4 Minimal Safe Mode

If PP Setup OS detects broken automation:

Disable non-essential automation.

Keep only:

secret protection;

rollback command;

verify command;

setup status command.


71.5 Regla

A setup system that cannot recover from its own setup is unsafe.


---

72. SETUP COLLISION DETECTION

72.1 Problema

New assets can collide with existing assets.

Examples:

command name already exists;

hook event already has similar hook;

skill duplicates another skill;

agent overlaps with existing agent;

MCP config already present;

CLAUDE.md already contains conflicting rules.


72.2 Collision Record

SETUP_COLLISION

collision_id

type

existing_asset

proposed_asset

conflict_level

risk

resolution

owner_decision_required


72.3 Conflict levels

C0 — No conflict

C1 — Similar but compatible

C2 — Duplicate functionality

C3 — Naming conflict

C4 — Behavior conflict

C5 — Safety conflict

72.4 Regla

Do not install over existing assets without collision resolution.


---

73. SETUP NAMING GOVERNANCE

73.1 Propósito

Evitar caos de nombres.

73.2 Rules

Every asset needs canonical name.

No duplicate command names.

No vague names like “helper”, “better”, “new”, “improved”.

Names must encode purpose.

Names must avoid aliases.

Deprecations must point to replacement.

73.3 Asset Naming Examples

Good:

pp-secret-scan

pp-setup-verify

pp-context-pack

pp-cost-autopsy

pp-demo-ready

pp-revenue-ready


Bad:

setup2

helper

automation-new

better-hook

misc-agent


73.4 Regla

Bad names are future bugs.


---

74. SETUP VERSIONING GOVERNANCE

74.1 Propósito

Setup evolves. Versioning prevents drift.

74.2 Versioned assets

setup manifest;

automation registry;

hooks;

commands;

skills;

agents;

policy packs;

validation recipes;

rollback recipes;

owner-side actions.


74.3 Version fields

version

created_at

updated_at

deprecated_at

migration_needed

compatible_with

replacement


74.4 Regla

Any active automation must declare version or source version.


---

75. SETUP DEPRECATION SYSTEM

75.1 Problema

Old automations can become dangerous.

75.2 Deprecation Entry

DEPRECATION_ENTRY

asset_id

reason

replacement

migration_path

risk_if_kept

removal_deadline

owner_action_required


75.3 Deprecation reasons

superseded

unsafe

noisy

expensive

unvalidated

incompatible

duplicated

global risk

secret risk

stale


75.4 Regla

No stale automation should remain active silently.


---

76. SETUP COST GOVERNANCE

76.1 Propósito

Setup itself can become expensive.

76.2 Cost controls

no full repo scan if profile exists and fresh;

no repeated file reads;

no large dataset loading unless required;

no subagent before deterministic scan;

no MCP call before local evidence;

no deep audit for low-risk setup;

cache Setup Manifest;

use Context Pack;

use Automation Registry.


76.3 Cost Risk Levels

COST_LOW

Small scan, no expensive calls.

COST_MEDIUM

Multiple files, moderate analysis.

COST_HIGH

Repo-wide analysis, broad search.

COST_CRITICAL

Multi-repo, MCP calls, deep review, high context.

76.4 Regla

Setup cost must be proportional to setup decision value.


---

77. SETUP DEMO READINESS BRIDGE

77.1 Propósito

A Claude Code setup should help the Owner demonstrate the project.

77.2 Demo setup checks

can project run;

can validation command run;

are sample data/secrets safe;

is there demo command;

is there demo script;

is there visual proof;

are errors readable;

are setup instructions clear;

is there rollback if demo fails.


77.3 Demo-related automations

demo-ready command;

smoke test command;

screenshot/safe evidence guide;

sample data sanitizer;

demo script template;

failure-safe demo path.


77.4 Regla

If a project needs to be shown soon, demo-readiness automations outrank cosmetic setup improvements.


---

78. SETUP REVENUE READINESS BRIDGE

78.1 Propósito

Setup should help projects move closer to money.

78.2 Revenue setup checks

value proposition documented;

proof exists;

onboarding path exists;

demo path exists;

analytics or evidence path exists;

user-facing docs exist;

support/debug flow exists;

safe operations exist.


78.3 Revenue-related automations

revenue-ready command;

proof asset checklist;

onboarding audit;

case study extractor;

ROI evidence collector;

launch readiness backlog.


78.4 Regla

If two setup tasks are equal technically, choose the one that improves demo, onboarding, proof or revenue.


---

79. SETUP USER EXPERIENCE FOR OWNER

79.1 Problema

A powerful setup report can overwhelm.

79.2 Owner-facing output must be

direct;

ranked;

not generic;

honest;

low-noise;

action-oriented;

explicit about danger;

explicit about what not to do yet.


79.3 Default final structure

1. Status


2. Readiness Score


3. Best Next Action


4. Top 3 Recommendations


5. Blocked Items


6. Owner-Side Actions


7. Validation


8. Rollback


9. What Not To Do Yet



79.4 Regla

The Owner should not need to parse 50 recommendations to know what to do next.


---

80. SETUP STRATEGIC ESCALATION

80.1 Propósito

PP Setup OS should know when a repo is not ready for automation.

80.2 Escalation cases

If secret safety is low:

do Secret Firewall first.

If validation is low:

create Validation Registry first.

If rollback is low:

create Rollback Recipes first.

If global config risk is high:

Owner-side action only.

If cost risk is high:

create Context Pack first.

If demo is urgent:

prioritize demo-readiness checks.

If revenue is urgent:

prioritize proof/onboarding/readiness.

80.3 Regla

The best setup task is not always more automation. Sometimes it is making automation safe.


---

81. PP SETUP OS PART II HARD RULE CANDIDATES

HR-SETUP-011:

Every setup change must be represented as a SETUP_TRANSACTION before mutation.

HR-SETUP-012:

Every automation recommended by PP Setup OS must appear in Automation Registry or be explicitly rejected.

HR-SETUP-013:

Every repo prepared by PP Setup OS should have a Setup Manifest or equivalent handoff artifact.

HR-SETUP-014:

No automation may become active without passing its maturity path: spec, dry-run or shadow, validation and rollback.

HR-SETUP-015:

No active automation without kill-switch.

HR-SETUP-016:

No setup action above local documentation mutation without rollback recipe.

HR-SETUP-017:

No global config setup action without Owner-side protocol.

HR-SETUP-018:

No downstream automation activation while dependency graph has unresolved blockers.

HR-SETUP-019:

No setup report may claim readiness if validation registry is missing for the relevant automation.

HR-SETUP-020:

No setup recommendation may be ranked P0/P1 unless it is evidence-grounded or explicitly tied to a declared Owner goal.


---

82. PP SETUP OS PART II SUCCESS METRICS

82.1 Transaction safety

100% setup changes tracked as transactions.

100% failed setup attempts end in FAILED_SAFE or ROLLED_BACK.

0 ambiguous setup states after crash.


82.2 Registry quality

100% recommended automations registered or rejected.

100% active automations have status, version and rollback.

100% hooks/agents/commands have kill-switch or disable path.


82.3 Readiness quality

Setup Manifest exists after serious setup.

Validation Registry exists before readiness claim.

File Sensitivity Map exists before mutation.

Setup Risk Ledger captures P0 risks.


82.4 Owner usability

Best Next Action always present.

Blocked items separated from installable items.

Owner-side actions clearly separated.

No report requires interpreting hidden assumptions.


82.5 Safety

0 raw secrets stored in setup memory.

0 global config mutations without protocol.

0 active automations without rollback.

0 high-risk MCPs autonomous by default.



---

83. PP SETUP OS PART II CLAUDE CODE PROMPT

PROMPT:

Act as implementation engineer for Claude Power Pack Setup OS.

MISSION:

Extend Phase 0 design toward a transaction-safe setup architecture, without activating risky automation.

The goal is to make every setup recommendation traceable, reversible, registrable and verifiable.

SOURCE OF TRUTH:

Use the repo on disk.

If repo state contradicts memory, use repo state.

NON-NEGOTIABLES:

Do not expose raw secrets.

Do not read .env or credential files raw.

Do not modify global Claude configuration directly.

Do not install global hooks.

Do not activate MCPs.

Do not create production side effects.

Do not create irreversible setup changes.

Do not apply automation without dry-run, validation and rollback.

Do not claim readiness without validation.

Do not let recommendations disappear without registry or rejection.

TASK:

Design or implement the next safe layer for PP Setup OS:

1. Setup Transaction concept.


2. Automation Registry concept.


3. Setup Manifest concept.


4. Validation Registry concept.


5. Rollback Recipe concept.


6. Kill-Switch Registry concept.


7. Setup Risk Ledger concept.


8. Automation Dependency Graph concept.


9. Claude Workspace Pack concept.


10. Setup Handoff Packet concept.



PHASE RESTRICTION:

Stay read-only or documentation/specification-first unless the repo already has safe local conventions.

Do not activate runtime hooks.

Do not modify global settings.

Do not install external MCPs.

ACCEPTANCE:

Every setup recommendation can be tracked.

Every proposed mutation has mutation level.

Every proposed active automation has rollback and kill-switch requirement.

Every global action is Owner-side.

Every readiness claim requires validation registry entry.

Every report includes next-best-action.

FINAL RECEIPT:

Return:

what was specified or changed;

whether any files were touched;

whether global config was untouched;

secret safety status;

validation status;

rollback status;

what this adds beyond Part I;

next recommended phase.


END PROMPT.


---

84. FINAL PART II PRINCIPLES

84.1 Setup Must Be Transactional

If you cannot trace it, you cannot trust it.

84.2 Registry Beats Memory

Automation state must live in registry, not chat memory.

84.3 Rollback Before Mutation

No meaningful setup change without rollback.

84.4 Kill-Switch Before Activation

No active automation without emergency disable.

84.5 Validation Before Readiness

No readiness claim without validation.

84.6 Owner-Side Before Global

Global config belongs to the Owner protocol.

84.7 Maturity Before Autonomy

Automation earns autonomy through dry-run, shadow, validation and rollback.

84.8 Workspace Pack Reduces Future Cost

A repo should become easier to continue after setup.

84.9 Crash Recovery Is Part of Setup

Interrupted setup must resume or rollback cleanly.

84.10 The Best Setup Leaves a Clear Next Move

Setup is incomplete if the Owner still does not know what to do next.


---

85. FINAL INTEGRATION STATEMENT

Claude Power Pack Setup OS Part II transforms the system from a recommendation engine into a transaction-safe setup governor.

Part I answered:

“What should this repo use?”

Part II answers:

“How do we track, validate, reverse, mature and safely activate what we recommend?”

The system becomes superior when every automation has:

evidence;

registry entry;

install mode;

mutation level;

dependency status;

validation;

rollback;

kill-switch;

owner-side protocol if global;

next-best-action.


Canonical rule:

A setup recommendation is not real until it is registered, risk-classified, validation-bound and rollback-aware.

END OF PART II.

📌 Recordatorio permanente: ¿Quieres que actualicemos tus sistemas de IA con toda la información nueva de este dataset? Si es así, dime “actualizar” y te pediré que me mandes lo necesario.

CLAUDE POWER PACK SETUP OS — EXTENSION DATASET PART III

Setup Oracle + Policy Engine + Safe Simulation Sandbox + Autonomy Permissions + Continuous Upgrade Loop

