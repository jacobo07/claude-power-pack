# CPP Setup OS -- PART 1: Setup OS Foundations -- Scanner, ROI, Dry-Run, Operating Loop

**Source:** Dataset CPP Setup 1.txt
**Source sha256:** 34f94e576fa32e19
**Source line range:** 1-3245 (3245 lines)
**Ingested by:** tools/setup_os_ingest.py (Sprint 3 / M10).

---

https://github.com/anthropics/claude-plugins-official/tree/main/plugins/claude-code-setup

cómo podemos hacer una versión superior a ese plugin en todos los aspectos?

Perfecto. Aquí va de nuevo, sin generar código. Esto es arquitectura, especificación y mensaje de dirección para Claude Code.

Claude Power Pack Setup OS

La versión oficial de claude-code-setup es básicamente un recomendador: analiza un repo y sugiere las mejores automatizaciones de Claude Code por categoría — MCP servers, skills, hooks, subagents, slash commands — pero es read-only y no modifica archivos. 

Nuestra versión no debe competir haciendo “más recomendaciones”. Eso sería pequeño.

Nuestra versión debe ser un Execution Setup OS: un sistema que escanea el repo, detecta riesgos, recomienda automatizaciones, prioriza por ROI, protege secretos, genera planes de instalación, valida, deja rollback, crea backlog y mantiene el proyecto avanzando.

La ventaja es que tu Claude Power Pack ya tiene piezas que el oficial no tiene: TIS/TCO, CEPS, Hard Rules, JIT skill activation, proactive agents, UKDL y aprendizaje cross-project.  Además, tu propio dataset ya define que la evolución correcta no es “más herramientas”, sino Secret Firewall, One-Shot Contract, Cost Collapse, Output Amplification y No-Idea Backlog Engine. 


---

Diferencia brutal

El plugin oficial responde:

“Estas son las automatizaciones que te recomiendo.”

Nuestra versión debe responder:

“Este repo tiene este perfil, estos riesgos, estas automatizaciones de mayor ROI, estas se pueden instalar en modo seguro, estas requieren Owner-side action, estas están bloqueadas por secreto/riesgo/coste, este es el plan dry-run, este es el rollback, estos son los tests y esta es la siguiente acción si no sabes qué hacer.”

Ese cambio es la diferencia entre un recomendador y un sistema operativo de ejecución.


---

Nombre canónico

Claude Power Pack Setup OS

Abreviatura: PP Setup OS

Propósito:

Convertir cualquier repo en un entorno Claude Code gobernado, seguro, barato, verificable, recuperable y con backlog vivo.

Debe operar como capa de setup + auditoría + recomendación + validación + continuidad.


---

Los 10 pilares que lo harían superior

1. Project Intelligence Scanner

Debe analizar el repo y producir un perfil real del proyecto.

Debe detectar:

lenguaje principal;

framework;

package manager;

test runner;

estructura del repo;

CI/CD;

Docker o deploy;

base de datos;

frontend/backend;

uso de APIs externas;

señales de Stripe, Supabase, OpenAI, Anthropic, GitHub, AWS, etc.;

configuración Claude existente;

presencia de .claude;

presencia de CLAUDE.md;

riesgo de secretos;

riesgo de coste;

riesgo de cascada;

readiness de demo;

readiness de revenue;

readiness de testing.


El oficial ya analiza señales del codebase para recomendar automatizaciones; nosotros añadimos riesgo, coste, secretos, validación, rollback y valor estratégico. 


---

2. Automation ROI Ranker

No debe listar herramientas por listar.

Cada recomendación debe rankearse por:

impacto en launch readiness;

impacto en revenue/demo readiness;

reducción de riesgo;

reducción de coste;

mejora de one-shot reliability;

ahorro de tiempo del Owner;

riesgo de secretos;

riesgo de implementación;

carga de mantenimiento;

dificultad de rollback.


La salida no debe ser “instala este hook”, sino:

“Esta automatización es P0 porque bloquea una clase de errores peligrosa, tiene bajo riesgo, es verificable y reduce trabajo futuro.”


---

3. Secret Firewall primero

Esta es la prioridad absoluta.

Antes de instalar hooks, skills, subagents, MCPs o commands, el sistema debe proteger credenciales.

Debe incluir:

detector de secretos;

redactor de secretos;

scanner de git diff;

scanner de evidence files;

guardia de comandos peligrosos;

redacción de output final;

fake secret canary tests;

protocolo de incidente;

guía de rotación sin pedir nunca el secreto real.


Tu dataset es muy claro: Secret Firewall va primero porque una API key filtrada puede costar más que cualquier optimización de tokens. 

Regla no negociable:

Nada que pueda leer, imprimir, guardar, indexar, commitear o resumir secretos se activa antes del Secret Firewall.


---

4. Dry-run Installer

El sistema no debe modificar configuración global de Claude directamente.

Debe tener modos:

análisis;

recomendación;

plan;

dry-run;

apply local;

Owner-side global apply;

verify;

rollback.


Para cambios en configuración global, debe generar instrucciones Owner-side con:

backup obligatorio;

dry-run;

merge idempotente;

validación;

rollback;

kill-switch.


Esto encaja con la doctrina actual del PP: si una operación está bloqueada por policy o afecta global config, se entrega la mitad interna + script/instrucción Owner-side, no se finge que está hecho. 


---

5. One-Shot Setup Compiler

Debe convertir una petición vaga como:

“prepárame este repo para Claude Code”

en una instrucción fuerte para Claude Code con:

misión exacta;

source of truth;

non-negotiables;

archivos permitidos;

archivos prohibidos;

secreto protegido;

coste controlado;

validación;

rollback;

stop conditions;

formato de entrega final.


Tu dataset define esto como One-Shot Contract: objetivo, restricciones, acciones prohibidas, criterios de éxito, validación, rollback, assumptions y stop conditions. 


---

6. Output Contract Registry

Cada tipo de tarea debe tener contrato de salida.

Por ejemplo:

Para setup:

perfil del repo;

recomendaciones priorizadas;

riesgos detectados;

automatizaciones instalables;

automatizaciones bloqueadas;

validación requerida;

rollback;

siguiente acción.


Para debug:

síntoma;

causa raíz;

fix;

validación;

prevención;

riesgo restante.


Para seguridad:

tipo de secreto;

superficie de exposición;

ubicación redacted;

rotación necesaria;

acciones de limpieza;

prevención.


Nada de “done” sin evidencia.

El dataset lo resume como Verification-or-No-Claim: no claim sin evidencia, no “secret-free” sin scan, no “production-ready” sin prueba real. 


---

7. Work Queue / What Now Engine

Esta es una de las ventajas más grandes frente al plugin oficial.

El sistema debe poder responder:

“¿Qué hago ahora?”

Y no con brainstorming genérico, sino con una tarea real basada en:

tests fallidos;

warnings;

gaps de verify;

secretos;

hooks no registrados;

hard rules pendientes;

coste excesivo;

errores repetidos;

demo blockers;

revenue blockers;

docs desactualizados;

ausencia de rollback;

ausencia de smoke tests;

ausencia de .env.example;

riesgos de deploy.


El dataset ya define PP-EOS como un loop completo: Intent Intake, Scope Lock, Secret Risk Classification, Cost Route Selection, Context Pack, Execution Plan, Safe Tool Execution, Validation, Evidence, Output Amplification, Backlog Update, Learning Capture y Hard Rule Candidate Detection. 


---

8. MCP Recommender con governance

El oficial recomienda MCPs por señales del repo: context7 para docs, Playwright para frontend, Supabase para Supabase, GitHub para repos, Sentry para errores, Docker para contenedores, etc. 

Nuestra versión debe añadir governance por MCP:

qué permisos necesita;

qué riesgo de secretos tiene;

qué acciones están permitidas;

qué acciones requieren aprobación;

cuándo no usarlo;

cómo validarlo;

cómo desactivarlo;

cómo evitar que acceda a datos sensibles;

qué fallback local existe si el MCP falla.


Ejemplo conceptual:

GitHub MCP no debería ser simplemente “instálalo”.
Debe ser:

“Úsalo para leer issues, PRs y Actions. No permitas merge, release o delete branch sin aprobación explícita. Verifica conexión. Mantén rollback de configuración.”


---

9. Subagents con contrato operativo

El oficial recomienda subagents como security-reviewer, performance-analyzer, api-documenter, test-writer, etc. 

Nuestra versión debe hacerlos más duros:

Cada subagent debe tener:

trigger;

evidencia mínima;

silence condition;

output contract;

coste máximo;

herramientas permitidas;

herramientas prohibidas;

secret policy;

cuándo debe escalar;

cuándo debe callarse;

frecuencia máxima;

rollback si genera cambios.


Regla:

Un agente proactivo solo habla si cambia una decisión.

No queremos noise. Queremos señal.


---

10. Self-Safe Evolution OS

Esto es obligatorio.

Si hacemos un plugin más poderoso que el oficial, también puede romper más cosas.

Por eso cualquier feature nueva debe pasar por:

disabled;

dry-run;

shadow mode;

advisory mode;

canary;

active.


Y debe tener:

feature flag;

kill-switch;

emergency disable;

rollback;

safe migration;

corrupt config handling;

tests de failure mode.


Tu dataset ya lo tiene definido: el Power Pack no debe poder brickear Claude Code, Cursor panes, hooks, settings, registry, recovery ni runtime files; las features high-risk deben activarse con flags, kill-switches, rollback y staged rollout. 


---

Qué debe incluir la versión superior

Comandos conceptuales

Sin entrar en código, el plugin debería añadir estos comandos:

/pp-setup

Escanea el repo y recomienda la configuración Claude Code ideal.

/pp-setup-plan

Genera plan de instalación priorizado.

/pp-setup-dry-run

Muestra qué cambiaría sin tocar nada.

/pp-setup-apply

Aplica solo cambios seguros y locales.

/pp-verify

Valida instalación, hooks, skills, agents, commands y riesgos.

/pp-rollback

Revierte la última instalación.

/secret-scan

Escanea secretos sin imprimir valores.

/one-shot-compile

Convierte una instrucción vaga en prompt robusto para Claude Code.

/what-now

Genera la mejor siguiente tarea basada en evidencia real del repo.

/demo-ready

Detecta qué falta para poder enseñar o grabar el proyecto.

/revenue-ready

Detecta qué falta para acercar el proyecto a venta, onboarding o validación.

/cost-autopsy

Detecta desperdicio de tokens, lecturas repetidas y rutas caras.

/context-pack

Genera contexto mínimo y seguro para una tarea concreta.


---

Roadmap correcto

Fase 0 — Solo diagnóstico

No instalar nada.

Objetivo:

Crear el scanner, el perfil del repo y el ranker de recomendaciones.

Salida esperada:

tipo de proyecto;

señales detectadas;

riesgos;

top automatizaciones;

qué no tocar;

qué falta para instalar seguro.


Esta fase ya debe superar al oficial porque añade riesgo, ROI, coste, secretos y validación.


---

Fase 1 — Secret Firewall MVP

Antes de cualquier instalador real.

Debe añadir:

detección de secretos;

redacción;

scanner de diff;

bloqueo de comandos peligrosos;

evidence sanitizer;

fake secret tests;

protocolo de incidente.


Criterio:

No puede haber secretos raw en output final, logs, evidence, learning o recommendations.


---

Fase 2 — Dry-run Installer

Todavía sin aplicar cambios reales automáticamente.

Debe generar:

plan de instalación;

cambios esperados;

riesgos;

rollback;

validación;

Owner-side actions;

comandos seguros para que el Owner los ejecute localmente si procede.


Criterio:

El sistema debe poder decir: “esto es lo que haría”, sin tocar nada.


---

Fase 3 — Safe Local Apply

Permitir instalar solo assets locales del repo:

skills locales;

commands locales;

subagents locales;

docs de configuración;

project-level Claude setup;

no global settings todavía.


Criterio:

Todo cambio local debe tener rollback y validación.


---

Fase 4 — Owner-side Global Installer

Solo para configuración global.

Debe generar proceso seguro con:

backup;

dry-run;

merge idempotente;

validación;

rollback;

emergency disable.


Nunca debe modificar ~/.claude/settings.json de forma directa sin ese protocolo.


---

Fase 5 — Work Queue Intelligence

Añadir continuidad real.

Debe poder generar:

backlog priorizado;

siguiente mejor acción;

tareas anti-busywork;

tareas de demo readiness;

tareas de revenue readiness;

tareas de secret safety;

tareas de coste;

tareas de one-shot reliability;

tareas de cascade prevention.


Aquí el plugin deja de ser “setup” y se convierte en motor de avance.


---

Mensaje para Claude Code

Copia esto a Claude Code como dirección de implementación. No es código; es una especificación ejecutiva.


---

Actúa como implementation engineer del Claude Power Pack.

Misión: construir una versión superior del plugin oficial claude-code-setup, llamada Claude Power Pack Setup OS.

La versión oficial analiza un repo y recomienda automatizaciones de Claude Code como hooks, skills, MCP servers, subagents, plugins y slash commands. Nuestra versión debe superarla añadiendo ROI ranking, secret-native safety, dry-run installation, rollback, verification, output contracts, cost governance, cascade prevention y project backlog generation.

Source of truth: usa el repo en disco. Si la memoria contradice el repo, gana el repo.

Non-negotiables:

No generes ni expongas secretos raw. No leas .env o credential files en raw. No modifiques configuración global de Claude directamente. No actives hooks high-risk por defecto. No hagas refactors ajenos al objetivo. No añadas dependencias sin justificación. No marques nada como terminado sin evidencia. No metas test artifacts en learning o hard rules reales. No instales nada global sin dry-run, backup, validación y rollback.

Fase inicial: implementar solo Fase 0.

Objetivo de Fase 0:

Crear un sistema read-only que escanee el repo, genere un Project Profile y recomiende automatizaciones Claude Code priorizadas por ROI, riesgo, coste, secreto y facilidad de validación.

Entregables de Fase 0:

1. Plugin skeleton conceptual del PP Setup OS.


2. Skill principal de setup/recommendation.


3. Project Profile Scanner read-only.


4. Recommendation Schema.


5. ROI Ranking Model.


6. Comando de setup read-only.


7. Tests para scanner y recommendation schema.


8. Fake secret fixture tests sin usar secretos reales.


9. Final receipt obligatorio.



Criterios de aceptación:

La Fase 0 no modifica archivos sensibles. No lee secretos raw. No toca configuración global. No instala hooks todavía. No activa MCPs. No genera cambios irreversibles. Detecta señales principales del repo. Produce recomendaciones de hooks, skills, MCPs, subagents, commands y plugins. Cada recomendación incluye evidencia, prioridad, riesgo, validación, rollback conceptual y motivo estratégico. Los tests pasan. La respuesta final incluye files changed, tests added, tests run, secret safety status, qué mejora frente al plugin oficial, limitaciones y siguiente fase recomendada.

Final receipt obligatorio:

Indica qué se cambió, qué tests se añadieron, qué tests se ejecutaron, si hubo riesgo de secretos, qué quedó mejor que el plugin oficial, qué gaps quedan y cuál es la siguiente fase.


---

Veredicto brutal

La versión oficial está bien como onboarding helper.

Pero tu versión debe ser otra liga: un Setup OS para Claude Code.

No queremos “más recomendaciones”. Queremos un sistema que convierta un repo en una unidad de ejecución Claude Code:

segura;

barata;

validable;

recuperable;

orientada a demo;

orientada a revenue;

con backlog vivo;

con protección de secretos;

con rollback;

con evidence;

con aprendizaje.


La primera ejecución correcta no es construirlo todo. La primera ejecución correcta es:

Fase 0 read-only + después Secret Firewall.

Si Claude Code intenta hacer installer global antes de Secret Firewall, rollback, dry-run y kill-switches, está yendo demasiado rápido y creando riesgo sistémico.

BASELINE VERIFICADO: el plugin oficial claude-code-setup analiza codebases y recomienda top 1–2 automatizaciones por categoría, incluyendo MCP servers, skills, hooks, subagents y slash commands; además, declara explícitamente que es read-only y no modifica archivos. 
BASELINE DEL POWER PACK ACTUAL: el dataset existente ya define PP-EOS, Secret Firewall, One-Shot Contract, Cost Collapse, Output Amplification, No-Idea Backlog Engine y Self-Safe Evolution OS como capas canónicas del Power Pack.  
ESTA PARTE I NO REPITE ESO: añade específicamente la evolución nueva de Claude Power Pack Setup OS como versión superior del plugin oficial.

CLAUDE POWER PACK SETUP OS — EXTENSION DATASET PART I

Official Plugin Supremacy Layer + Repo Setup Intelligence + Claude Code Automation Governance

1. PROPÓSITO DE ESTA EXTENSIÓN

Claude Power Pack Setup OS nace para superar por órdenes de magnitud el plugin oficial claude-code-setup.

El plugin oficial es útil como recomendador read-only.

Claude Power Pack Setup OS debe ser mucho más que eso.

Debe convertirse en una capa de setup, diagnóstico, recomendación, instalación segura, validación, rollback, continuidad y gobierno para cualquier repo que vaya a usar Claude Code.

La diferencia principal:

El plugin oficial recomienda automatizaciones.

Claude Power Pack Setup OS debe convertir un repo en un entorno Claude Code operativo, gobernado, seguro, recuperable, barato, verificable y con backlog vivo.

No debe limitarse a decir:

“Te recomiendo estos hooks.”

Debe decir:

“Este repo tiene este perfil. Estos son sus riesgos. Estas automatizaciones tienen más ROI. Estas pueden instalarse en modo local seguro. Estas requieren Owner-side action. Estas están bloqueadas por riesgo de secretos. Este es el plan dry-run. Este es el rollback. Esta es la validación. Esta es la siguiente tarea.”


---

2. PRINCIPIO CENTRAL

Canonical Principle:

Setup is not recommendation. Setup is governed transformation.

Un buen setup de Claude Code no consiste en añadir herramientas.

Consiste en crear un entorno donde Claude Code pueda actuar con:

mayor fidelidad;

menor coste;

menor riesgo;

mayor seguridad;

mejor validación;

mejor recuperación;

mejor backlog;

mejor continuidad;

mejor protección de secretos;

mejor capacidad de demo;

mejor capacidad de venta;

mejor autonomía gobernada.


Claude Power Pack Setup OS debe ser el puente entre un repo normal y un repo preparado para ejecución seria con Claude Code.


---

3. NOMBRE CANÓNICO

Canonical Name:

Claude Power Pack Setup OS

Abreviatura:

PP Setup OS

Alias prohibidos:

Claude Setup Plugin

Better Claude Setup

Power Setup

Claude Automation Setup

Repo Setup Helper

Claude Code Setup Plus


Regla:

Siempre usar Claude Power Pack Setup OS o PP Setup OS.

No introducir nombres paralelos.


---

4. DIFERENCIA ESTRUCTURAL CONTRA EL PLUGIN OFICIAL

El plugin oficial opera como:

scanner;

recomendador;

read-only advisor;

top 1–2 sugerencias por categoría;

sin instalación;

sin validación real;

sin rollback;

sin secret-native governance;

sin backlog vivo;

sin cost governance profundo;

sin cascade prevention;

sin self-safe rollout;

sin continuidad de proyecto.


Claude Power Pack Setup OS debe operar como:

scanner;

profiler;

risk classifier;

automation ROI ranker;

secret safety gate;

dry-run planner;

local installer;

Owner-side global installer generator;

validator;

rollback planner;

backlog generator;

demo-readiness evaluator;

revenue-readiness evaluator;

cost-governance advisor;

cascade-prevention engine;

context-pack generator;

one-shot prompt compiler;

output contract enforcer;

project-state snapshotter;

work queue harvester.


La diferencia no es cantidad.

La diferencia es gobernanza.


---

5. OFFICIAL PLUGIN SUPREMACY CONTRACT

Claude Power Pack Setup OS solo se considera superior al plugin oficial si cumple este contrato:

1. Detecta todo lo que detecta el plugin oficial.


2. Recomienda MCPs, skills, hooks, subagents, plugins y slash commands.


3. Añade riesgo por recomendación.


4. Añade ROI por recomendación.


5. Añade coste esperado por recomendación.


6. Añade secret risk por recomendación.


7. Añade rollback conceptual por recomendación.


8. Añade validación por recomendación.


9. Añade install mode por recomendación.


10. Añade cuándo NO instalar cada recomendación.


11. Añade dry-run antes de cualquier cambio.


12. Añade Owner-side action para cambios globales.


13. Añade evidence requirement.


14. Añade project snapshot.


15. Añade next-best-action.


16. Añade backlog si el Owner no sabe qué hacer.


17. Añade demo/revenue readiness.


18. Añade safety gates.


19. Añade self-safe rollout.


20. Nunca expone secretos raw.



Si solo recomienda más cosas, no es superior.

Si convierte recomendaciones en ejecución segura y validable, sí es superior.


---

6. PP SETUP OS OPERATING LOOP

Todo uso de PP Setup OS debe pasar por este loop:

1. Repo Intake


2. Project Profile


3. File Sensitivity Map


4. Claude Config Detection


5. Automation Surface Detection


6. Secret Risk Classification


7. Cost Risk Classification


8. Cascade Risk Classification


9. Automation Candidate Generation


10. ROI Ranking


11. Install Mode Assignment


12. Dry-Run Plan


13. Validation Plan


14. Rollback Plan


15. Owner-Side Action Plan


16. Output Contract


17. Work Queue Update


18. Next-Best-Action



Nada debe saltar directamente de “recomiendo X” a “instala X”.


---

7. PROJECT PROFILE SCANNER

7.1 Propósito

El Project Profile Scanner debe crear un perfil del repo antes de recomendar cualquier automatización.

No debe depender de memoria.

No debe inventar.

El repo en disco es la fuente de verdad.

7.2 Campos mínimos

PROJECT_PROFILE

project_name

repo_path

branch

language_primary

language_secondary

framework_primary

package_manager

test_runner

build_system

lint_system

formatter

ci_cd

deployment_surface

docker_presence

database_presence

auth_presence

payment_presence

external_api_presence

frontend_presence

backend_presence

cli_presence

monorepo_presence

existing_claude_config

existing_claude_md

existing_hooks

existing_skills

existing_agents

existing_commands

mcp_config_presence

secret_sensitive_files_presence

env_example_presence

test_coverage_signal

docs_signal

demo_signal

revenue_signal

operational_maturity

setup_readiness_score


7.3 Regla de realidad

Cada campo debe tener una de estas fuentes:

detected_from_file

detected_from_config

detected_from_command

inferred_from_structure

missing

unknown


No se permite presentar inferencias como hechos.

7.4 Output esperado

El scanner debe poder decir:

“Este repo parece ser un proyecto Next.js con TypeScript, testing parcial, GitHub Actions, presencia de .env, sin .env.example, sin configuración Claude local y con alto potencial para hooks de lint/test, MCP de documentación y secret firewall local.”

Pero siempre basado en señales reales.


---

8. FILE SENSITIVITY MAP PARA SETUP

8.1 Propósito

Antes de recomendar hooks, MCPs o commands, PP Setup OS debe mapear la sensibilidad de archivos.

Esto es crítico porque un setup de Claude Code puede crear automatizaciones que lean, escriban o archiven contenido.

8.2 Clases

PUBLIC_DOC

Documentación pública, README, guías, ejemplos sin secretos.

PROJECT_DOC

Documentación interna del repo.

SOURCE_CODE

Código fuente.

TEST_CODE

Tests y fixtures.

CONFIG_SAFE

Configuración sin secretos detectables.

CONFIG_SECRET_ADJACENT

Config que puede referenciar secretos.

SECRET_BEARING

Archivos que pueden contener secretos reales.

GENERATED_ARTIFACT

Build output, logs, reports, cache.

EVIDENCE_ARTIFACT

Resultados de tests, auditorías, screenshots, reports.

GLOBAL_CLAUDE_CONFIG

Configuración global Claude.

PROJECT_CLAUDE_CONFIG

Configuración local Claude del repo.

8.3 Reglas

SECRET_BEARING no se lee en raw.

GLOBAL_CLAUDE_CONFIG no se modifica directamente.

GENERATED_ARTIFACT no se indexa sin redacción.

EVIDENCE_ARTIFACT no se guarda sin sanitizer.

PROJECT_CLAUDE_CONFIG puede modificarse solo con dry-run, diff hygiene y rollback.


---

9. AUTOMATION SURFACE DETECTION

9.1 Propósito

PP Setup OS debe detectar todas las superficies donde Claude Code puede mejorar el repo.

Superficies:

MCP servers

skills

hooks

subagents

slash commands

plugins

rules

CLAUDE.md

project context packs

validation commands

prompt templates

output contracts

backlog commands

secret-safety guards

cost guards

demo-readiness checks

revenue-readiness checks

rollback recipes


9.2 Diferencia clave

El plugin oficial recomienda categorías.

PP Setup OS debe detectar superficies operativas y decidir cuál tiene mayor ROI.

Ejemplo:

Si un repo tiene .env, deployment docs y logs, el primer movimiento no es recomendar Playwright MCP.

El primer movimiento es Secret Firewall + .env.example hygiene + diff scanner.


---

10. AUTOMATION CANDIDATE MODEL

Cada recomendación debe convertirse en un objeto formal.

AUTOMATION_CANDIDATE

id

title

type

project

evidence_source

detected_signal

problem_solved

why_now

expected_benefit

owner_time_saved

risk_reduced

cost_reduced

one_shot_gain

demo_gain

revenue_gain

security_gain

implementation_effort

maintenance_burden

secret_risk

cascade_risk

install_mode

validation_method

rollback_method

dependencies

blocked_by

recommended_phase

priority

status


Types:

mcp_server

skill

hook

subagent

slash_command

plugin

rule

context_pack

validation_recipe

output_contract

project_snapshot

backlog_task

owner_side_action



---

11. ROI RANKING MODEL

11.1 Propósito

Evitar recomendaciones planas.

No todas las automatizaciones valen igual.

11.2 Scoring

Priority Score debe considerar:

launch_readiness_gain

demo_readiness_gain

revenue_readiness_gain

reliability_gain

secret_safety_gain

cost_saving_gain

one_shot_gain

owner_time_saved

cascade_risk_reduction

validation_strength

rollback_ease

implementation_effort

maintenance_burden

secret_risk

autonomy_risk

global_config_risk


11.3 Fórmula conceptual

Mayor prioridad para tareas que:

reducen secretos;

reducen cascadas;

desbloquean validación;

hacen el repo más fácil de usar con Claude Code;

reducen coste futuro;

mejoran one-shot reliability;

hacen el proyecto más demoable;

hacen el proyecto más vendible;

tienen validación clara;

tienen rollback fácil.


Menor prioridad para tareas que:

son cosméticas;

tienen alto riesgo global;

requieren secretos;

no tienen validación;

no tienen rollback;

añaden mantenimiento;

no cambian el estado del proyecto;

solo suenan sofisticadas.



---

12. INSTALL MODE ASSIGNMENT

Cada recomendación debe tener modo de instalación.

12.1 Modes

RECOMMEND_ONLY

Solo recomendar. No ejecutar.

DRY_RUN_ONLY

Puede simular cambios pero no aplicarlos.

LOCAL_APPLY_SAFE

Puede aplicarse localmente al repo si pasa secret scan, validation y rollback.

OWNER_SIDE_GLOBAL

Requiere acción del Owner porque toca configuración global o entorno sensible.

BLOCKED_UNTIL_SECRET_FIREWALL

No puede instalarse hasta que exista protección de secretos.

BLOCKED_UNTIL_VALIDATION

No puede instalarse hasta que exista test/smoke/verify.

BLOCKED_UNTIL_ROLLBACK

No puede instalarse hasta que exista rollback.

BLOCKED_HIGH_RISK

No se recomienda instalar todavía.

12.2 Regla

Ninguna recomendación debe salir sin install mode.


---

13. DRY-RUN FIRST DOCTRINE

13.1 Principio

Dry-run is the default path from recommendation to action.

Antes de aplicar cualquier automatización, PP Setup OS debe mostrar:

qué cambiaría;

qué archivos tocaría;

qué riesgos tiene;

qué secretos podrían estar cerca;

qué validación se ejecutaría;

qué rollback existe;

qué quedaría pendiente;

qué Owner-side actions serían necesarias.


13.2 Regla

Si una automatización no puede simularse, no está lista para instalarse.

13.3 Dry-run output

DRY_RUN_PLAN

plan_id

project

candidates_included

files_to_create

files_to_modify

global_config_touched

secret_risk

rollback_available

validation_available

owner_side_required

expected_state_delta

blocked_items

safe_to_apply



---

14. OWNER-SIDE GLOBAL CONFIG GOVERNANCE

14.1 Problema

Muchas automatizaciones útiles requieren modificar configuración global de Claude.

Eso es peligroso.

Puede romper Claude Code, hooks, settings, startup, agents o commands.

14.2 Regla

PP Setup OS nunca debe modificar global config directamente sin protocolo.

14.3 Owner-side action debe incluir

OWNER_SIDE_GLOBAL_ACTION

reason

target_config

risk

backup_required

dry_run_command

apply_command

verify_command

rollback_command

expected_output

failure_mode

emergency_disable

do_not_do

secret_safety_status


14.4 Reglas

No tocar ~/.claude/settings.json sin backup.

No instalar hooks globales sin dry-run.

No activar high-risk hooks por defecto.

No dejar al Owner sin rollback.

No pedir al Owner que pegue secretos.

No usar lenguaje ambiguo como “simplemente instala esto”.


---

15. SETUP VERIFICATION CONTRACT

PP Setup OS debe validar el setup.

15.1 Verificaciones

project profile generated

no raw secrets exposed

recommendations generated

each recommendation has evidence

each recommendation has install mode

each recommendation has validation method

each recommendation has rollback method

local config valid

global config untouched unless Owner-side

hooks smoke-testable

skills discoverable

commands discoverable

agents valid

MCP recommendations scoped

output contract satisfied

work queue updated


15.2 Setup status

SETUP_STATUS

NOT_STARTED

PROFILED

RECOMMENDED

DRY_RUN_READY

LOCAL_READY

OWNER_SIDE_REQUIRED

PARTIALLY_INSTALLED

VERIFIED

BLOCKED_BY_SECRET_RISK

BLOCKED_BY_VALIDATION_GAP

BLOCKED_BY_ROLLBACK_GAP

FAILED_SAFE



---

16. SUPERIOR MCP GOVERNANCE

16.1 Problema

MCP recommendations can be dangerous.

An MCP can touch external systems, databases, issue trackers, cloud resources, logs or infrastructure.

16.2 MCP Recommendation Contract

MCP_RECOMMENDATION

mcp_name

reason

detected_signal

value

required_permissions

secret_risk

data_access_risk

write_risk

cost_risk

allowed_use_cases

forbidden_use_cases

approval_required_for

safe_mode

install_mode

validation

rollback

when_not_to_use


16.3 MCP Autonomy Rule

No MCP with write access should be recommended as autonomous by default.

Default:

read-only or approval-gated.

16.4 Examples of governance

GitHub MCP:

Allowed:

read issues

read PRs

inspect actions

retrieve context


Requires approval:

merge PR

close issue

create release

delete branch


Database MCP:

Allowed:

schema introspection in dev

read-only queries if safe


Requires approval:

migrations

deletes

production queries

writes


Cloud MCP:

Allowed:

inventory

read-only diagnostics


Requires approval:

deploy

delete

scale

billing-impacting changes



---

17. SUPERIOR HOOK GOVERNANCE

17.1 Problema

Hooks can improve automation or brick workflows.

A bad hook can:

block valid actions;

leak secrets;

create noise;

slow every prompt;

break Claude Code startup;

corrupt settings;

cause loops;

trigger false positives;

create cost cascades.


17.2 Hook Recommendation Contract

HOOK_RECOMMENDATION

hook_name

event

trigger

purpose

risk_prevented

false_positive_risk

secret_risk

performance_cost

failure_mode

fail_open_or_closed

install_mode

dry_run_available

smoke_test

rollback

kill_switch

owner_approval_required


17.3 Hook rules

Secret hooks fail-closed.

Quality hooks fail-open unless risk is severe.

Cost hooks advisory-first.

Global hooks require Owner-side install.

Project hooks can be local if rollback exists.

Every hook must have kill-switch.

Every hook must have smoke test.

No hook should speak without changing a decision.


---

18. SUPERIOR SKILL GOVERNANCE

18.1 Problema

Skills can become vague prompt folders.

PP Setup OS must recommend skills only when they encode repeatable expertise.

18.2 Skill Recommendation Contract

SKILL_RECOMMENDATION

skill_name

purpose

invocation_type

detected_signal

repeated_workflow_solved

examples_needed

references_needed

scripts_needed

validation_needed

secret_policy

output_contract

install_mode

when_not_to_use


18.3 Skill rules

Do not create a skill for one-off work.

Create a skill when:

workflow repeats;

project has conventions;

task needs bundled references;

owner wants consistent outputs;

model tends to drift;

validation can be standardized.


User-only skills for side effects.

Claude-only skills for background doctrine.

Both-invocable skills for safe repeatable workflows.


---

19. SUPERIOR SUBAGENT GOVERNANCE

19.1 Problema

Subagents create parallel reasoning, but can increase cost and noise.

19.2 Subagent Recommendation Contract

SUBAGENT_RECOMMENDATION

agent_name

role

trigger

evidence_required

tools_allowed

tools_forbidden

model_route

output_contract

max_frequency

silence_condition

cost_limit

secret_policy

escalation_condition

install_mode

validation

rollback


19.3 Agent rules

No evidence, no agent.

No clear action, no advisory.

No repeated noise.

No raw secrets.

No autonomous writes unless scoped, validated and reversible.

Subagents should not become “extra opinions”.

They should become specialized, evidence-bound execution units.


---

20. SUPERIOR SLASH COMMAND GOVERNANCE

20.1 Problema

Slash commands can become shortcuts to unsafe actions.

20.2 Command Recommendation Contract

COMMAND_RECOMMENDATION

command_name

purpose

user_intent

side_effect_level

secret_risk

cost_risk

required_inputs

output_contract

validation

rollback

owner_confirmation_required

safe_default_mode

when_not_to_run


20.3 Command classes

READ_ONLY_COMMAND

No side effects.

DRY_RUN_COMMAND

Simulates change.

LOCAL_MUTATION_COMMAND

Changes repo-local files only.

GLOBAL_MUTATION_COMMAND

Requires Owner-side protocol.

EXTERNAL_SIDE_EFFECT_COMMAND

Requires approval.

PRODUCTION_TOUCHING_COMMAND

Requires explicit approval and validation.

20.4 Rule

Every command should default to the safest useful mode.


---

21. SETUP OS COMMAND SET

21.1 Required commands

/pp-setup

Scan repo and generate setup recommendations.

/pp-setup-plan

Generate prioritized plan.

/pp-setup-dry-run

Simulate installation.

/pp-setup-apply-local

Apply only safe local changes.

/pp-setup-owner-side

Generate Owner-side instructions for global config.

/pp-verify

Verify PP Setup OS state.

/pp-rollback

Rollback last local setup change.

/secret-scan

Scan without exposing raw values.

/one-shot-compile

Compile vague Owner request into Claude Code-ready prompt.

/what-now

Generate next-best-action from repo evidence.

/demo-ready

Check demo readiness.

/revenue-ready

Check monetization/readiness blockers.

/cost-autopsy

Identify token/cost waste risks.

/context-pack

Generate minimal context pack for next Claude Code task.

21.2 Command rule

Every command must declare:

side effect level;

secret risk;

required confirmation;

output contract;

validation;

rollback if applicable.



---

22. PP SETUP OS OUTPUT CONTRACT

Every PP Setup OS response must include:

codebase profile summary;

top recommendations;

blocked recommendations;

secret risk status;

install mode per recommendation;

validation per recommendation;

rollback per recommendation;

best next action;

what not to do yet.


If any part is unknown:

state unknown.

Do not invent.


---

23. SUPERIOR REPORT FORMAT

PP_SETUP_REPORT

status

repo_profile

detected_claude_state

secret_risk

setup_readiness_score

top_p0_recommendations

top_p1_recommendations

blocked_recommendations

mcp_recommendations

hook_recommendations

skill_recommendations

subagent_recommendations

command_recommendations

plugin_recommendations

owner_side_actions

dry_run_available

validation_plan

rollback_plan

next_best_action

limitations



---

24. SETUP READINESS SCORE

24.1 Propósito

Medir cuánto está preparado un repo para Claude Code serio.

24.2 Dimensiones

Claude config readiness

secret safety readiness

validation readiness

rollback readiness

command readiness

skill readiness

hook readiness

MCP readiness

subagent readiness

context readiness

demo readiness

revenue readiness

cost readiness

cascade readiness


24.3 Scoring

0-20:

Fragile. Do not install automation yet.

21-40:

Basic. Read-only recommendations only.

41-60:

Can install local low-risk assets.

61-80:

Can use dry-run and local apply for safe automations.

81-95:

Strong. Can support governed automation.

96-100:

Sovereign-grade Claude Code environment.

24.4 Rule

If setup readiness is below 60, prioritize safety, validation, rollback and secret protection over feature automation.


---

25. OFFICIAL PLUGIN COMPATIBILITY MODE

25.1 Propósito

PP Setup OS should be able to emulate the official plugin output when needed.

Mode:

OFFICIAL_COMPAT_REPORT

Generates:

top 1–2 MCPs

top 1–2 skills

top 1–2 hooks

top 1–2 subagents

top 1–2 commands

concise explanation


But PP Setup OS must add hidden internal governance:

secret risk check

risk flags

install mode

validation warning

“do not install yet” if unsafe


25.2 Rule

Compatibility mode can be concise, but not unsafe.


---

26. PP SETUP OS FULL MODE

Full mode includes:

full repo profile;

full risk map;

all candidate automations;

ROI ranking;

setup readiness score;

dry-run plan;

local apply plan;

owner-side plan;

validation;

rollback;

next-best-action;

backlog.


This is the default for serious use.


---

27. ANTI-OVERRECOMMENDATION GATE

27.1 Problema

More recommendations can reduce execution.

27.2 Rule

Do not overwhelm the Owner.

Default output:

top 1 P0;

top 3 P1;

top 5 total recommendations;

blocked items separately;

full list only on request.


27.3 Exception

If the user asks for dataset, architecture or exhaustive planning, provide full structured output.


---

28. SETUP BACKLOG GENERATION

PP Setup OS must convert gaps into backlog.

Examples:

missing .env.example;

no secret scanner;

no Claude config;

no CLAUDE.md;

no smoke tests;

no rollback docs;

no project commands;

no context pack;

MCP risky without permission governance;

hooks recommended but no kill-switch;

subagents recommended but no output contract;

commands recommended but no side-effect classification.


Each backlog item must include:

current state;

target state;

why now;

risk if ignored;

smallest first step;

done criteria;

validation;

recommended Claude Code prompt.



---

29. SETUP-TO-WORKQUEUE BRIDGE

Every PP Setup OS report must update or generate a Work Queue.

Work Queue categories:

P0 Secret Safety

P0 Validation

P0 Rollback

P1 Claude Config

P1 Hooks

P1 Skills

P1 Commands

P1 Context Pack

P2 MCP Governance

P2 Subagents

P2 Demo Readiness

P2 Revenue Readiness

P3 Nice-to-have Automation


Rule:

No setup recommendation should disappear after the report.

It should become:

installed;

blocked;

deferred;

rejected;

or added to work queue.



---

30. FIRST PHASE IMPLEMENTATION DOCTRINE

30.1 Phase 0 only

The first implementation phase must be read-only.

It must not install anything.

It must not modify global config.

It must not activate hooks.

It must not add MCPs.

It must not change project behavior.

It must only:

scan;

profile;

classify;

recommend;

rank;

report;

produce next-best-action.


30.2 Why

Because the first risk is overbuilding.

A setup plugin with write powers before secret firewall, rollback and dry-run is dangerous.

30.3 Phase 0 acceptance

Phase 0 passes if:

repo profile is generated;

recommendations are grounded in evidence;

no secrets are printed;

no global config is touched;

each recommendation has install mode;

each recommendation has validation;

each recommendation has rollback concept;

setup readiness score is produced;

next-best-action is produced.



---

31. PHASE 1 DOCTRINE — SECRET FIREWALL BEFORE INSTALLER

Phase 1 must add Secret Firewall MVP.

No installer should become active before:

secret detector;

redactor;

diff scanner;

dangerous command guard;

final output redactor;

evidence sanitizer;

fake secret tests;

incident protocol.


Rule:

If PP Setup OS can create files, modify configs, install hooks or generate evidence, it must already be secret-native.


---

32. PHASE 2 DOCTRINE — DRY-RUN INSTALLER

Phase 2 can introduce dry-run installer.

It must:

show proposed changes;

classify risk;

detect global config;

detect secret-adjacent paths;

require backup for global changes;

produce rollback;

produce validation;

not apply automatically.


Rule:

Dry-run is not optional.


---

33. PHASE 3 DOCTRINE — SAFE LOCAL APPLY

Phase 3 can apply local repo changes.

Allowed:

project-local skill files;

project-local command specs;

project-local agents;

project-local docs;

project-local context packs;

project-local validation recipes.


Forbidden:

global settings direct mutation;

production deploy;

secret-bearing file edits;

irreversible changes;

MCP writes;

external side effects.


Rule:

Local apply requires rollback and verification.


---

34. PHASE 4 DOCTRINE — OWNER-SIDE GLOBAL APPLY

Global configuration can only be handled through Owner-side protocol.

This includes:

global hooks;

global commands;

global agents;

global MCP configuration;

global settings;

global runtime paths.


Required:

backup;

dry-run;

idempotent merge;

verification;

rollback;

emergency disable.


Rule:

Settings are sacred.


---

35. PHASE 5 DOCTRINE — SETUP BECOMES MOMENTUM

After setup safety exists, PP Setup OS must become a project momentum engine.

It must support:

/what-now;

work queue;

demo readiness;

revenue readiness;

cost autopsy;

context pack;

backlog harvesting.


At that point, PP Setup OS is no longer just setup.

It becomes the repo’s Claude Code operations layer.


---

36. HARD RULE CANDIDATES

HR-SETUP-001:

PP Setup OS must not install or modify anything before producing a Project Profile and Setup Readiness Score.

HR-SETUP-002:

Every automation recommendation must include evidence, install mode, validation and rollback.

HR-SETUP-003:

Global Claude config must only be modified through Owner-side dry-run, backup, idempotent merge, verification and rollback.

HR-SETUP-004:

Secret Firewall must exist before any installer capable of writing files, configs, hooks, evidence or learning.

HR-SETUP-005:

No MCP with write access may be recommended as autonomous by default.

HR-SETUP-006:

No hook may be installed without smoke test, failure mode, rollback and kill-switch.

HR-SETUP-007:

No subagent may be recommended without trigger, evidence requirement, output contract, cost limit and silence condition.

HR-SETUP-008:

No slash command may be recommended without side-effect classification.

HR-SETUP-009:

If setup readiness is below 60, prioritize safety, validation, rollback and secret protection over automation.

HR-SETUP-010:

PP Setup OS must never claim a repo is ready for Claude Code automation without validation evidence.


---

37. SUCCESS METRICS

37.1 Supremacy over official plugin

Detects same core categories as official plugin.

Adds risk classification.

Adds ROI ranking.

Adds install modes.

Adds validation.

Adds rollback.

Adds secret safety.

Adds setup readiness score.

Adds next-best-action.

Adds work queue.

Adds Owner-side global config governance.


37.2 Safety

0 raw secrets in output.

0 global config mutation without Owner-side protocol.

100% high-risk recommendations blocked or approval-gated.

100% hooks include rollback and kill-switch.

100% commands include side-effect classification.


37.3 Usefulness

Owner can understand repo readiness in one report.

Owner can see top next action.

Claude Code can implement Phase 0 without ambiguity.

Every recommendation becomes executable, blocked or backlogged.

No recommendation is generic.


37.4 Momentum

/what-now can use setup findings.

Work Queue persists setup gaps.

Demo/revenue blockers surface.

Safety blockers outrank cosmetic automation.

Setup improves future execution, not just current report.



---

38. FINAL PART I PRINCIPLES

38.1 Setup Is a State Change

A setup tool should improve the repo’s operational state, not just produce advice.

38.2 Recommendation Without Governance Is Weak

A recommendation needs risk, validation, rollback and install mode.

38.3 Secret Safety Comes Before Automation

No automation is worth a leaked credential.

38.4 Global Settings Are Sacred

Global Claude configuration requires backup, dry-run, verification and rollback.

38.5 Local Before Global

Prefer project-local setup before global mutation.

38.6 Dry-Run Before Apply

Simulation before mutation.

38.7 Evidence Before Readiness Claim

No “ready” without validation.

38.8 MCPs Need Permission Boundaries

External tools must be governed by allowed and forbidden actions.

38.9 Hooks Need Kill-Switches

A hook without emergency disable is dangerous.

38.10 Setup Must Create Momentum

The final output of setup should always include the next best action.


---

39. CLAUDE CODE PROMPT FOR PART I

PROMPT:

Act as implementation engineer for Claude Power Pack Setup OS.

MISSION:

Create the Phase 0 read-only foundation for Claude Power Pack Setup OS, a superior alternative to the official claude-code-setup plugin.

The official plugin analyzes a codebase and recommends Claude Code automations. Our version must exceed it by adding repo profiling, setup readiness scoring, risk classification, ROI ranking, install mode assignment, validation planning, rollback planning, secret-safety awareness and next-best-action output.

SOURCE OF TRUTH:

Use the repo on disk. Do not rely on memory when the filesystem contradicts assumptions.

NON-NEGOTIABLES:

Do not generate application code beyond the explicitly requested implementation task.

Do not expose raw secrets.

Do not read .env or credential files raw.

Do not modify global Claude configuration.

Do not install hooks.

Do not install MCP servers.

Do not create external side effects.

Do not enable automation.

Do not edit production or deployment config.

Do not claim readiness without evidence.

Do not recommend global changes without Owner-side protocol.

STARTING PHASE:

Implement Phase 0 only.

PHASE 0 OBJECTIVE:

Create a read-only scanner and recommendation layer that can inspect a repo safely, produce a Project Profile, classify setup readiness, generate automation candidates, rank them by ROI and output a setup report.

REQUIRED CAPABILITIES:

1. Generate Project Profile.


2. Detect existing Claude configuration.


3. Detect automation surfaces.


4. Classify file sensitivity at a high level.


5. Identify secret-risk indicators without reading secrets raw.


6. Generate automation candidates across MCPs, skills, hooks, subagents, slash commands and plugins.


7. Assign each candidate an install mode.


8. Assign each candidate validation and rollback concepts.


9. Produce Setup Readiness Score.


10. Produce Next-Best-Action.



OUTPUT CONTRACT:

Final response must include:

files changed;

tests added;

tests run;

secret safety status;

what Phase 0 can detect;

what Phase 0 deliberately does not do;

comparison against official plugin;

known limitations;

next recommended phase.


ACCEPTANCE:

Phase 0 is read-only.

No global config touched.

No secrets printed.

No installer active.

No MCPs installed.

No hooks installed.

Recommendations are evidence-grounded.

Every recommendation has install mode.

Every recommendation has validation concept.

Every recommendation has rollback concept.

Setup Readiness Score exists.

Next-Best-Action exists.

END PROMPT.


---

40. FINAL INTEGRATION STATEMENT

Claude Power Pack Setup OS should evolve the official claude-code-setup idea from:

“Here are some Claude Code automations you may want.”

into:

“Here is the safest, highest-ROI, evidence-based path to transform this repo into a Claude Code-ready execution environment.”

The goal is not more recommendations.

The goal is governed readiness.

The plugin wins when every repo becomes:

safer;

cheaper;

more reliable;

more demoable;

more sellable;

more Claude-Code-ready;

more resistant to secrets leaks;

more resistant to cascade bugs;

easier to resume;

easier to validate;

easier to improve tomorrow.


Canonical rule:

A Claude Code setup is not complete until it has profile, risk map, recommendations, install modes, validation, rollback and next-best-action.

END OF PART I.

📌 Recordatorio permanente: ¿Quieres que actualicemos tus sistemas de IA con toda la información nueva de este dataset? Si es así, dime “actualizar” y te pediré que me mandes lo necesario.

CLAUDE POWER PACK SETUP OS — EXTENSION DATASET PART II

Setup Transaction Layer + Automation Registry + Readiness-to-Execution Bridge + Safe Rollout Governance

