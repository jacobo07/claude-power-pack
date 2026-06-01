# PP Dataset -- Capabilities Extension (Output Amp + Cost + Fidelity + Secret FW)

**Source:** PP_DATASET_20260531T122242Z (1).md, lines 1218-2339
**Dataset part:** Part I
**Ingested:** 2026-06-01 (BL-DATASET-001 M0)
**Lines in this file:** 1122

---

*Todos los datos verificados empíricamente del repo en commit `330e261`.*
*Para regenerar: `python tools/_dataset_inventory.py` (siguiente).*
*Honest classifier blockers documentados; no advisory-taggear*
*ningún FAIL.*

# CLAUDE POWER PACK -- EXTENSION DATASET
# Output Amplification + Cost Collapse + Fidelity + Secret Firewall + Backlog Engine
# Dataset adicional para añadir al PP sin duplicar el dataset base

## 0. PROPÓSITO DE ESTA EXTENSIÓN

Este dataset define las extensiones que deben añadirse al Claude Power Pack para convertirlo en un sistema más fiable, más barato, más seguro y más útil cuando el Owner se queda sin ideas para avanzar un proyecto.

No sustituye el dataset base del Power Pack. Lo complementa.

El dataset base ya contiene:
- TIS/TCO para visibilidad de tokens y coste.
- CEPS para prevenir errores recurrentes.
- Hard Rules para convertir bugs críticos en reglas activas.
- JIT skill loading.
- Proactive agents.
- Monitoring.
- UQF/code review.
- Hooks globales.
- Gaps conocidos de verify_spp, paths+secrets, cache hit ratio, command discovery y cross-project learning.

Esta extensión añade lo que todavía no está suficientemente formalizado:

1. Output Amplification Layer.
2. Cost Collapse Layer.
3. Fidelity & One-Shot Reliability Layer.
4. Secret Firewall Layer para NO filtrar credenciales, API keys, tokens, passwords, cookies ni .env.
5. No-Idea Backlog Engine.
6. Project Momentum Engine.
7. Context Budget Contract.
8. Evidence-First Delivery Contract.
9. Anti-Overengineering Gate.
10. Owner Energy / Execution Leverage Mode.

---

## 1. PRINCIPIO CENTRAL

Claude Power Pack no debe limitarse a “ayudar a Claude Code”.

Debe actuar como un sistema operativo de ejecución que hace cuatro cosas antes de que el agente toque un proyecto:

1. Entender qué resultado exacto se busca.
2. Elegir el camino más barato para alcanzarlo.
3. Bloquear fugas de secretos antes de que ocurran.
4. Mantener el proyecto avanzando incluso cuando el Owner no tiene ideas.

La mejora real no es añadir más herramientas. La mejora real es crear gates que obliguen al agente a producir outputs:
- más útiles,
- más baratos,
- más verificables,
- más seguros,
- más orientados a avance real,
- menos propensos a romper el proyecto,
- menos propensos a desperdiciar tokens,
- menos propensos a exponer información sensible.

---

## 2. OUTPUT AMPLIFICATION LAYER

### 2.1 Problema

Claude Code puede ejecutar muchas acciones pero no siempre entrega un output final que sea directamente usable por el Owner.

Problemas típicos:
- Explica demasiado y entrega poco.
- Dice “he mejorado X” sin evidencias concretas.
- Genera cambios pero no deja checklist de validación.
- Termina una tarea sin decir qué queda desbloqueado.
- Entrega una solución técnicamente correcta pero estratégicamente débil.
- No distingue entre output informativo, output ejecutable y output vendible.
- No convierte aprendizaje en activos reutilizables.

### 2.2 Objetivo

Crear una capa llamada Output Amplification Layer que fuerce al agente a entregar cada tarea en formato de activo operativo.

Cada output debe clasificarse como uno de estos tipos:

1. Decision Output
   - Sirve para decidir.
   - Debe incluir opciones, tradeoffs, riesgos y recomendación.

2. Execution Output
   - Sirve para ejecutar.
   - Debe incluir pasos, archivos tocados, comandos, validaciones y rollback.

3. Asset Output
   - Sirve como activo reutilizable.
   - Debe incluir nombre canónico, ubicación sugerida, propósito y reglas de reutilización.

4. Debug Output
   - Sirve para resolver un fallo.
   - Debe incluir síntoma, causa raíz, fix, prevención y test.

5. Backlog Output
   - Sirve para crear siguientes tareas.
   - Debe incluir prioridad, impacto, esfuerzo, riesgo y criterio de done.

6. Governance Output
   - Sirve para endurecer el sistema.
   - Debe incluir regla, trigger, stop condition, evidence requirement y ubicación.

### 2.3 Regla de entrega

Ninguna tarea debe cerrarse con un simple “done”.

Toda tarea debe cerrar con:

- Qué se hizo.
- Qué evidencia lo prueba.
- Qué riesgo queda.
- Qué se desbloquea ahora.
- Qué debería hacerse después.
- Qué NO se hizo.
- Si hubo o no exposición de secretos.
- Si hubo o no cambios irreversibles.
- Si el output es reutilizable, dónde debe registrarse.

### 2.4 Output Quality Score

Crear un score interno de 0 a 100 llamado OQS.

Dimensiones:
- Clarity: el Owner entiende qué pasó.
- Actionability: se puede actuar sin reinterpretar.
- Evidence: hay pruebas reales, no claims.
- Reusability: se puede guardar como activo.
- Strategic value: acerca el proyecto a venta, estabilidad, ahorro o aprendizaje.
- Safety: no expone secretos ni rompe entornos.
- Cost efficiency: no usó más tokens/comandos de los necesarios.

Thresholds:
- OQS >= 85: output excelente.
- OQS 70-84: output aceptable.
- OQS 50-69: output débil; requiere mejora.
- OQS < 50: output no entregable.

Hard Rule candidata:
Before final response, if OQS < 70, do not report completion. Improve the final output or explicitly mark partial completion.

---

## 3. COST COLLAPSE LAYER

### 3.1 Problema

El dataset base ya detecta gasto de tokens, TIS/TCO y anomalías de cache. Pero falta una capa explícita de reducción agresiva de coste antes de ejecutar.

El problema no es solo saber cuánto costó una sesión. El problema es evitar desde el inicio rutas caras que podrían resolverse con herramientas determinísticas, archivos locales, grep, tests, índices o resúmenes compactos.

### 3.2 Objetivo

Crear una capa Cost Collapse Layer que reduzca el coste por tarea sin reducir la calidad.

Regla estratégica:
El agente debe usar el método más barato que preserve fidelidad suficiente.

Orden de preferencia:
1. Reglas locales / Hard Rules.
2. Índices locales.
3. grep/search determinístico.
4. tests existentes.
5. lectura parcial de archivos.
6. lectura completa de archivos.
7. razonamiento del modelo.
8. subagentes.
9. modelo caro.
10. investigación profunda larga.

### 3.3 Pre-Task Cost Contract

Antes de una tarea compleja, Claude Code debe generar internamente un contrato de coste:

- task_type
- expected_files_to_read
- expected_commands
- expected_model_calls
- expected_token_range
- cheap_path_available: yes/no
- expensive_path_justified: yes/no
- max_budget_soft
- max_budget_hard
- stop_condition

No debe pedir permiso cada vez. Debe usarlo como sistema interno de disciplina.

### 3.4 Token Waste Categories

Registrar cada desperdicio de tokens en categorías:

- unnecessary_full_file_read
- repeated_context_loading
- overlong_final_summary
- premature_agent_invocation
- duplicate_search
- stale_context_reprocessing
- unnecessary_deep_research
- no_index_used
- no_cache_used
- verbose_chain_without_artifact
- repeated_error_loop
- tool_retry_without_new_information

### 3.5 Cheap-First Rule

Hard Rule candidata:
Before using a high-cost model path, subagent, full repo scan, or long research flow, check whether a deterministic local path can answer the question. If yes, use the cheap path first.

### 3.6 Cost Autopsy

Al terminar una sesión larga, PP debe poder generar una autopsia:

- top 5 token drains
- top 5 repeated reads
- top 5 commands with low value
- prompts that caused scope explosion
- files repeatedly loaded
- moments where compact/handoff should have happened earlier
- suggested hard rules to prevent same cost pattern

### 3.7 Cost-to-Progress Ratio

Crear métrica:
Cost-to-Progress Ratio = estimated project progress / estimated cost

Una tarea barata con avance claro gana prioridad.
Una tarea cara sin avance directo se bloquea o se manda a backlog de investigación.

Categorías:
- Excellent: high progress / low cost.
- Acceptable: medium progress / low-medium cost.
- Risky: low progress / high cost.
- Blocked: unclear progress / high cost.

---

## 4. FIDELITY & ONE-SHOT RELIABILITY LAYER

### 4.1 Problema

El Owner quiere aumentar one-shot reliability. Eso no significa que Claude Code haga más cosas. Significa que las haga bien a la primera, con menos drift, menos malentendidos y menos retoques.

Fallos típicos:
- El agente interpreta mal el objetivo.
- Construye algo parecido pero no exacto.
- Omite restricciones.
- Genera código que importa pero no corre.
- Toca archivos fuera de scope.
- No verifica compatibilidad de versión.
- Hace refactor cuando se pidió fix.
- Cambia nombres canónicos.
- Entrega sin comprobar.
- Usa patrones incompatibles con el proyecto.

### 4.2 One-Shot Contract

Antes de ejecutar una tarea, PP debe compilar el prompt del Owner en un One-Shot Contract:

- User Objective
- Non-Negotiables
- Explicit Constraints
- Implied Constraints
- Forbidden Actions
- Files Allowed
- Files Forbidden
- Success Criteria
- Validation Commands
- Rollback Plan
- Ambiguity Register
- Assumptions Made
- Stop Conditions

Si faltan datos pero la tarea puede avanzar, el agente debe hacer la mejor aproximación segura y registrar assumptions. No debe bloquear por preguntas triviales.

### 4.3 Fidelity Lock

Crear una capa llamada Fidelity Lock.

Su función:
Mantener fidelidad al objetivo original aunque el agente encuentre oportunidades de mejora.

Reglas:
- No refactorizar si el objetivo era corregir un bug puntual.
- No ampliar scope sin razón.
- No cambiar arquitectura si bastaba un patch.
- No crear abstracciones nuevas si no resuelven un problema actual.
- No introducir dependencias sin justificación.
- No tocar naming canónico.
- No “mejorar” UX/estilo si no estaba pedido.
- No convertir una tarea de validación en una tarea de construcción.
- No sustituir el proyecto del Owner por la preferencia del modelo.

### 4.4 Assumption Ledger

Toda suposición debe registrarse internamente con:
- assumption
- confidence
- why needed
- risk if wrong
- mitigation

Si una suposición tiene alto riesgo, debe convertirse en stop condition.

### 4.5 Validation Ladder

Cada tarea debe validarse con la escalera más barata posible:

1. Static check.
2. Schema check.
3. Unit test.
4. Integration test.
5. Smoke test.
6. Manual evidence.
7. Runtime observation.
8. External verification.

No usar una validación cara si una barata ya descarta el fallo.

### 4.6 One-Shot Failure Log

Cada vez que una tarea requiera segundo intento, registrar:

- original instruction
- failed interpretation
- missing constraint
- failure type
- prevention rule
- whether prompt was ambiguous
- whether agent ignored explicit constraint
- whether tool output was misread
- whether context was stale

Después de 3 fallos similares, proponer Hard Rule.

---

## 5. SECRET FIREWALL LAYER

### 5.1 Problema crítico

El Power Pack debe impedir de forma agresiva que Claude Code filtre credenciales, API keys, tokens, passwords, cookies, private keys, .env, database URLs, OAuth secrets, webhook secrets, SSH keys o cualquier otro secreto.

Esto es más importante que velocidad, coste o comodidad.

La regla central:
Secrets must never leave the local machine, never be printed in final responses, never be committed, never be logged raw, never be copied into prompts, never be stored in evidence files, and never be sent to external tools.

### 5.2 Definición de secreto

Se considera secreto cualquier valor que permita acceso, autenticación, autorización, impersonation, billing, deployment, database access o control de infraestructura.

Incluye:
- API keys.
- Anthropic/OpenAI/Gemini keys.
- Stripe keys.
- Supabase service role keys.
- Database URLs.
- JWT secrets.
- OAuth client secrets.
- GitHub tokens.
- Telegram bot tokens.
- Discord webhooks.
- SMTP passwords.
- SSH private keys.
- Cloudflare tokens.
- AWS/GCP/Azure credentials.
- Railway/Render/Fly/Vercel tokens.
- WordPress application passwords.
- Cookies/session tokens.
- Bearer tokens.
- .env values.
- .npmrc tokens.
- .pypirc credentials.
- private.pem/id_rsa files.
- Any high-entropy string adjacent to words like key, token, secret, password, auth, bearer, credential.

### 5.3 Secret Zero-Trust Rule

Claude Code debe tratar cualquier archivo de configuración sensible como contaminado por defecto.

Archivos sensibles:
- .env
- .env.local
- .env.production
- .env.development
- .env.*
- config/secrets.*
- credentials.*
- service-account*.json
- firebase*.json
- .npmrc
- .pypirc
- id_rsa
- *.pem
- *.key
- docker-compose files with environment values
- GitHub Actions secrets references if expanded
- logs that may include authorization headers
- HTTP dumps
- database dumps

Regla:
Sensitive files may be inspected only in redacted mode. Raw values must not be displayed to the model unless the Owner explicitly requests local remediation and even then the output must redact values.

### 5.4 Secret Firewall Modes

Mode 1: Scan Mode
- Detects potential secrets.
- Does not print raw values.
- Reports file path, line number, secret type, confidence and redacted preview.

Mode 2: Redaction Mode
- Replaces raw secret with placeholder.
- Example: sk-...abcd becomes [REDACTED_OPENAI_KEY_LAST4_abcd].
- Never stores the full secret.

Mode 3: Block Mode
- Blocks write, commit, push, final output or evidence archive if raw secret is detected.

Mode 4: Quarantine Mode
- Moves contaminated evidence/log output to local quarantine.
- Does not commit.
- Does not summarize raw content.
- Emits safe remediation instructions.

### 5.5 Secret Detection Strategy

Use layered detection:

1. Known provider regex.
2. Generic key-value regex.
3. High-entropy detection.
4. Contextual proximity detection.
5. File path sensitivity.
6. Git diff detection.
7. Log/output stream detection.
8. Final response redaction.
9. Evidence archive redaction.
10. Clipboard/export redaction if supported.

Provider examples:
- OpenAI key patterns.
- Anthropic key patterns.
- Stripe live/test keys.
- GitHub ghp/gho/ghu/ghs tokens.
- Slack bot/webhook tokens.
- Telegram bot tokens.
- AWS access key IDs.
- Google service account private keys.
- Supabase JWT/service role strings.
- JWT three-part tokens.
- Bearer tokens.
- SSH private key blocks.

### 5.6 Secret Handling Rules

Hard Rule candidata:
Before writing, committing, pushing, archiving evidence, or producing final output, scan changed content and tool output for secrets. If any raw secret is detected, block the operation and redact.

Hard Rule candidata:
Never print full values from .env or credential files. If a value must be referenced, use provider/type + last 4 characters only.

Hard Rule candidata:
If a command may echo secrets, rewrite it to avoid printing environment values. Never run env, printenv, set, Get-ChildItem Env:, cat .env, type .env, or equivalent without redaction.

Hard Rule candidata:
If git diff contains a secret, do not commit. First remove secret, rotate if exposed, and add prevention rule.

Hard Rule candidata:
If a secret has already appeared in terminal output, treat it as potentially compromised and surface rotation guidance without repeating the secret.

### 5.7 Secret-Safe Evidence

Evidence files must never include raw secrets.

Allowed:
- [REDACTED_SECRET_TYPE]
- [REDACTED_LAST4_abcd]
- path + line + secret type
- hash of secret if local-only and non-reversible
- statement that scan found zero secrets

Forbidden:
- full key
- full token
- full DB URL
- full Authorization header
- full cookie
- full private key
- screenshots containing secrets
- logs containing secrets
- copied HTTP headers

### 5.8 Secret Canary Tests

Add test secrets that are fake but pattern-valid.

Test cases:
- fake OpenAI key in temp file
- fake Stripe key in git diff
- fake .env printed by command
- fake JWT in log
- fake private key block
- fake Supabase service_role JWT
- fake GitHub token in markdown evidence

Expected:
- detector catches them
- final output redacts them
- commit is blocked
- evidence archive is blocked or sanitized
- no raw value appears in logs

### 5.9 Secret Leak Incident Protocol

If a secret leak is detected:

1. Stop current execution.
2. Do not repeat the secret.
3. Identify secret type and location.
4. Mark exposure surface:
   - local only
   - model context
   - log file
   - git staged
   - git committed
   - git pushed
   - external service
5. Recommend rotation if beyond local-only.
6. Remove from file.
7. Add to .gitignore if needed.
8. Add placeholder/example file.
9. Add regression test.
10. Add NEVER_AGAIN entry.
11. Propose Hard Rule if new pattern.

### 5.10 Secret Firewall Priority

Secret Firewall overrides:
- cost optimization
- fail-open philosophy
- convenience
- speed
- final response polish
- automation
- deploy
- commit
- push
- evidence archive

For secrets, default must be fail-closed.

---

## 6. BACKLOG ENGINE WHEN OWNER HAS NO IDEAS

### 6.1 Problema

El Owner puede quedarse sin ideas para avanzar un proyecto. Esto crea fricción y pérdida de momentum.

El sistema no debe esperar a que el Owner tenga claridad perfecta.

PP debe poder mirar un proyecto y generar un backlog útil, priorizado y conectado al avance real.

### 6.2 No-Idea Mode

Crear comando o trigger:
“No tengo ideas”
“Qué hago ahora”
“Estoy bloqueado”
“Siguiente tarea”
“Dame backlog”
“Avanza este proyecto”
“Qué falta”
“Qué puedo mejorar”
“Qué haría un founder senior ahora”

Cuando se detecte, PP activa No-Idea Backlog Engine.

### 6.3 Backlog Sources

El backlog debe derivarse de fuentes reales:

- TODOs existentes.
- Failing tests.
- verify_spp failures.
- recent errors.
- CEPS events.
- NEVER_AGAIN log.
- stale docs.
- uncommitted changes.
- open gaps in dataset.
- missing tests.
- missing monitoring.
- missing README/onboarding.
- high-risk files.
- repeated manual operations.
- low-quality outputs.
- project-specific launch blockers.
- revenue blockers.
- demos that cannot be recorded.
- tasks that reduce future token cost.
- tasks that increase one-shot reliability.
- tasks that prevent secret leaks.
- tasks that create reusable assets.

### 6.4 Backlog Item Schema

Cada backlog item debe tener:

- ID
- Title
- Project
- Category
- Why it matters
- User value
- Business value
- Risk reduced
- Estimated effort
- Expected impact
- Files likely touched
- Validation method
- Done criteria
- Rollback risk
- Cost tier
- Recommended model
- Dependencies
- Priority score

### 6.5 Priority Formula

Priority Score =
(Revenue Impact x 3)
+ (Risk Reduction x 2)
+ (One-Shot Improvement x 2)
+ (Cost Reduction x 2)
+ (Launch Readiness x 3)
+ (Owner Time Saved x 2)
- (Implementation Risk x 2)
- (Token Cost x 1)
- (Scope Creep x 2)

### 6.6 Backlog Categories

1. Revenue / Sales Readiness
   - Anything that moves closer to selling, demoing, launching or monetizing.

2. Reliability
   - Tests, monitoring, rollback, validation, gates.

3. Cost Reduction
   - Cache, routing, token pruning, smaller context, deterministic indexes.

4. Secret Safety
   - Leak detection, redaction, .env hardening, precommit scanning.

5. One-Shot Reliability
   - Prompt contracts, validation ladders, assumption ledgers.

6. Output Quality
   - Better final reports, artifact generation, evidence packaging.

7. Developer Velocity
   - CLI helpers, scripts, docs, onboarding, project maps.

8. Knowledge Capture
   - Convert lessons into UKDL, Hard Rules, playbooks.

9. Demo / Proof
   - Recordable demos, screenshots, before/after evidence.

10. Strategic Assetization
   - Turn repeated workflows into reusable systems.

### 6.7 Next-Best-Action Output

When Owner has no ideas, PP must output exactly:

1. Best next task.
2. Why this task now.
3. What it unlocks.
4. Smallest safe first step.
5. Validation.
6. Stop condition.
7. Alternative if blocked.

No vague brainstorming.

### 6.8 Anti-Busywork Gate

The backlog engine must avoid fake productivity.

Blocked task types:
- polishing docs that nobody uses
- refactoring without measurable reliability gain
- adding features before core validation
- creating abstractions before repeated need
- researching when enough data exists
- aesthetic cleanup while launch blocker remains
- building dashboards without operational decision attached

Hard Rule candidata:
If backlog item does not improve revenue readiness, reliability, cost, safety, one-shot quality, or Owner time leverage, mark as low priority or reject.

---

## 7. PROJECT MOMENTUM ENGINE

### 7.1 Objetivo

Crear una capa que mantiene cada proyecto avanzando aunque el Owner esté cansado, ocupado o sin claridad.

La pregunta central:
“What action makes this project more sellable, more stable, more automated, or more demoable today?”

### 7.2 Momentum Modes

Mode A: 15-minute task
- ultra small
- low risk
- clear done
- useful when Owner has low energy

Mode B: 1-hour task
- meaningful improvement
- testable
- local scope

Mode C: Deep work task
- requires architecture
- high leverage
- should have One-Shot Contract

Mode D: Cleanup task
- removes friction
- reduces future cost
- only allowed if connected to measurable benefit

Mode E: Launch task
- directly improves demo, sales, onboarding or deployment

### 7.3 Daily Progress Rule

Every day, at least one task should make the project:
- closer to selling,
- closer to launch,
- safer to operate,
- cheaper to maintain,
- easier to demo,
- easier to continue tomorrow.

If none of those improves, the task was probably fake progress.

### 7.4 Momentum Ledger

PP should maintain a local ledger per project:

- date
- task completed
- category
- evidence
- impact
- next recommended task
- blocker removed
- time saved
- cost reduced
- risk reduced

This becomes the source for future backlog generation.

---

## 8. CONTEXT FIDELITY ENGINE

### 8.1 Problema

One-shot failures often happen because Claude Code receives too much irrelevant context or too little relevant context.

### 8.2 Context Pack

Before complex execution, PP should compile a Context Pack:

- current objective
- active project
- canonical names
- relevant files only
- forbidden files
- current branch
- recent commits
- open errors
- known hard rules
- relevant UKDL entries
- validation commands
- environment constraints
- secret risk classification

### 8.3 Context Pack Budget

The Context Pack must be compressed.

Rules:
- No full docs unless needed.
- Prefer indexes over raw files.
- Prefer excerpts over full file.
- Prefer current error over old background.
- Prefer constraints over narrative.
- Prefer commands over explanations.
- Prefer exact file paths over descriptions.
- Remove repeated user preferences unless task-relevant.

### 8.4 Stale Context Guard

Before acting on remembered facts, PP must check whether the repo state contradicts them.

If mismatch:
- use repo as source of truth
- note memory drift
- avoid overwriting current reality with old context

---

## 9. ANTI-OVERENGINEERING GATE

### 9.1 Problema

Claude Code may overbuild.

The Owner works on many systems. The danger is not lack of ideas. The danger is building too much before the next revenue/reliability proof.

### 9.2 Gate

Before creating a new module, daemon, agent, skill or workflow, ask internally:

- Is this solving a repeated problem?
- Has the problem occurred at least twice?
- Is there a cheaper checklist/manual version?
- Can this be a markdown SOP first?
- Does this reduce future cost or risk?
- Does this make the project closer to launch/sale/demo?
- Is there a validation plan?
- Will this increase maintenance burden?

If not, do not build. Put in backlog.

### 9.3 Minimum Viable Governance

Not every idea needs a full system.

Escalation ladder:
1. Note.
2. Checklist.
3. Hard Rule.
4. Script.
5. Hook.
6. Agent.
7. Daemon.
8. Full subsystem.

Build the lowest level that solves the actual problem.

---

## 10. PROMPT COMPILER FOR CLAUDE CODE

### 10.1 Objective

Add a prompt compiler that transforms Owner requests into Claude Code-ready execution prompts.

The compiler must produce:
- role
- objective
- context
- constraints
- allowed actions
- forbidden actions
- exact output contract
- validation
- stop conditions
- rollback
- secret handling
- cost discipline

### 10.2 Prompt Quality Gates

A prompt is weak if:
- success criteria are missing
- scope is unclear
- validation is missing
- secret handling is missing
- output format is vague
- no stop condition
- no “do not touch” list
- no rollback plan for risky changes
- no cost ceiling

PP should rewrite weak prompts into strong prompts before execution.

### 10.3 One-Shot Prompt Template

Every high-impact Claude Code prompt should include:

- Mission
- Current repo
- Source of truth
- Non-negotiables
- Do not modify
- Step order
- Required checks
- Secret firewall rules
- Evidence required
- Final answer format
- Failure protocol

---

## 11. SECURITY OUTPUT CONTRACT

### 11.1 Every final answer after repo work must include

- Secret scan status: passed/failed/not applicable.
- Files changed.
- Tests run.
- Evidence path.
- Risks.
- Next action.

If secrets were detected:
- Do not include the secret.
- State type and location only.
- Recommend rotation if needed.
- Block commit/deploy.

### 11.2 Final Response Redactor

Before final response, scan the response itself for secrets.

If secret appears:
- redact
- regenerate safe final
- log incident
- do not expose raw value

---

## 12. BACKLOG FOR IMPLEMENTING THIS EXTENSION

### P0 -- Security / Secrets

1. Build Secret Firewall detector.
2. Add final response redactor.
3. Add git diff secret scanner.
4. Add evidence archive secret scanner.
5. Add command-output redactor for env/log commands.
6. Add fake secret canary tests.
7. Add Hard Rules HR-SECRET-001 through HR-SECRET-007.
8. Add secret incident protocol to docs.
9. Add pre-commit block for raw secrets.
10. Add .env-safe inspection mode.

### P1 -- One-Shot Reliability

1. Build One-Shot Contract generator.
2. Build Fidelity Lock.
3. Build Assumption Ledger.
4. Build Validation Ladder selector.
5. Add one-shot failure log.
6. Add prompt compiler.
7. Add output contract checker.
8. Add OQS scoring.
9. Add no-silent-scope-expansion rule.
10. Add post-task evidence requirement.

### P2 -- Cost Collapse

1. Build pre-task cost contract.
2. Add cheap-first route selection.
3. Add token waste taxonomy.
4. Add cost autopsy.
5. Add repeated read detector.
6. Add model routing by risk and task type.
7. Add cache effectiveness audit.
8. Add cost-to-progress ratio.
9. Add expensive path justification gate.
10. Add session-start cost forecast.

### P3 -- No-Idea Backlog Engine

1. Build backlog generator from repo state.
2. Add priority scoring.
3. Add categories.
4. Add next-best-action mode.
5. Add anti-busywork gate.
6. Add momentum ledger.
7. Add 15-minute/1-hour/deep-work modes.
8. Add stale project detector.
9. Add launch-readiness backlog.
10. Add revenue-readiness backlog.

### P4 -- Project Momentum

1. Add daily progress ledger.
2. Add time-saved / risk-reduced metrics.
3. Add demo-readiness checks.
4. Add “what unlocks selling?” classifier.
5. Add owner-energy mode.
6. Add low-energy useful tasks.
7. Add deep-work task queue.
8. Add recurring blockers list.
9. Add project heatmap.
10. Add next action memory.

---

## 13. NEW HARD RULE CANDIDATES

### HR-SECRET-001
Before final output, scan the response for secrets. If any credential-like value is present, redact before responding.

### HR-SECRET-002
Before git commit or push, scan staged diff for secrets. If detected, block commit/push and require remediation.

### HR-SECRET-003
Never print raw .env values, private keys, tokens, database URLs, cookies or Authorization headers.

### HR-SECRET-004
Evidence files must not contain raw secrets. If tool output contains secrets, quarantine or redact before archiving.

### HR-SECRET-005
Do not run shell commands that dump environment variables unless output is redacted.

### HR-SECRET-006
If a secret has been exposed outside local-only context, recommend rotation without repeating the secret.

### HR-SECRET-007
Secret safety is fail-closed, even if other PP hooks are fail-open.

### HR-OUTPUT-001
Never mark a task complete without evidence, changed files summary, tests/validation status and remaining risks.

### HR-ONESHOT-001
Before multi-file modification, compile One-Shot Contract and obey scope lock.

### HR-COST-001
Before expensive model/subagent/full-repo path, attempt deterministic cheap path or document why impossible.

### HR-BACKLOG-001
When Owner has no next idea, generate next-best-action backlog from repo evidence, not generic brainstorming.

---

## 14. SUCCESS METRICS

### Secret Firewall
- 0 raw secrets in final responses.
- 0 raw secrets in evidence archive.
- 0 raw secrets committed.
- 100% fake secret canary detection.
- 100% redaction in logs shown to model.

### Cost Collapse
- Reduce repeated full-file reads by 50%.
- Increase cache hit ratio above 30%.
- Reduce long-session token waste by 30%.
- Add pre-task cost estimate to all complex tasks.
- Detect top 5 cost drains per session.

### One-Shot Reliability
- Fewer second-pass corrections.
- Fewer scope drift incidents.
- More tasks completed with validation on first attempt.
- All risky tasks have assumptions and stop conditions.
- All final outputs include evidence.

### Output Quality
- OQS average above 85.
- 100% final outputs classify what type of output was produced.
- 100% debug tasks include cause, fix, prevention and test.
- 100% backlog items include done criteria.

### Backlog Engine
- Owner can ask “what now?” and get useful task in one response.
- Backlog generated from real repo evidence.
- Every backlog item has priority score.
- Low-value busywork gets filtered.
- At least one recommended task always moves project closer to sale, launch, reliability, cost reduction or automation.

---

## 15. STRATEGIC CONCLUSION

The next evolution of Claude Power Pack should not be “more tools”.

It should be a tighter execution operating system.

The highest-leverage additions are:

1. Secret Firewall first.
   Because one leaked API key can cost more than every token optimization combined.

2. One-Shot Contract second.
   Because one correct execution is cheaper than three repair cycles.

3. Cost Collapse third.
   Because cheap deterministic checks should beat expensive reasoning whenever possible.

4. Output Amplification fourth.
   Because the Owner needs assets, decisions and validated progress, not vague summaries.

5. No-Idea Backlog Engine fifth.
   Because project momentum must not depend on the Owner always knowing the next move.

Canonical principle:
The Power Pack wins when Claude Code becomes cheaper, safer, more faithful, more autonomous and more directly useful per action.

END DATASET.
