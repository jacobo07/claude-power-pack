# PART D — KOBIIDISTILLEROS MOTHER PROMPT (Sleepy)

Lazy-loaded by `/cpp-distill`. Defines the verbatim **22-section contract** (v1.0 Sovereign Sealing), the per-section required blocks, the **Tandas & Partes** structural layer, the tier-end markers, and the materialization rules for the in-session distillation driver.

**Status (2026-05-14, v1.2 Sovereign Sealing):** All 22 canonical sections present. §1-6 realigned to Owner-ratified titles. §7-13 instruction-shape preserved from Phase A (commit `e2ebd59`). §14-22 new instruction-shape bodies. §22 fused (Inferencia Decisional Exógena & Conocimiento Negativo). Zero gap markers. Zero placeholders.

---

## CONTRACT

For every `/cpp-distill` invocation, the driver MUST emit 22 markdown files at `<output_root>/Tier_<T>/Seccion_<N>.md` matching the schema at `tools/distiller/schema.json` (v1.2.1). Each section file MUST contain, in order:

1. A heading: `## <N>. <SECTION_TITLE>` — title sourced from `schema.json#section_titles[<N>]` (verbatim, accents preserved).
2. **Tandas & Partes body** (mandatory per `schema.tandas_partes_spec`): three depth-tandas × three orthogonal partes per tanda. See the structural layer section below.
3. A `🧮 Calculadora de ROI` block with all five required fields:
   - `Tipo` — primary ROI dimension (Temporal / Patrimonial / Riesgo / Soberanía / Escalabilidad).
   - `ROI Temporal` — quantified multiplier (e.g. `50×–100×`).
   - `ROI Riesgo` — qualitative (Crítico / Alto / Moderado / Bajo).
   - `Escenario` — Conservador / Realista / Agresivo.
   - `Explicación` — 1-3 sentences linking the ROI to the section topic.
4. A `🏁 Cierre patrimonial` closing line — typically opens with **Acelera** / **Defiende** / **Consolida** / **Incinera** depending on the section's strategic vector.
5. A `🦅 Comentario del Oráculo` aside — 1-3 sentences in oracular voice; never corporate, never cynical.

After the final section of each tier, append the tier-end marker on its own line:
- After Sección 7: `-- FIN DE TIER 1 --`
- After Sección 13: `-- FIN DE TIER 2 --`
- After Sección 22: `-- FIN DE TIER 3 --` followed by `-- FIN DE DATASET v1.2 --`

The `🧨 KILL-SWITCH` canonical marker appears once, inside §16 (Antifragilidad).

---

## TANDAS & PARTES — STRUCTURAL LAYER (v1.0 Sovereign Sealing)

Every section body partitions into 3 depth-tandas × 3 orthogonal partes per tanda. This is the OUTPUT shape; the per-section instruction bodies below describe the THEME each tanda/parte fills.

**Depth-tandas (ascending depth):**

- `### Tanda T1 — Baseline (esenciales)` — minimum viable signal a reader at first contact needs to act today.
- `### Tanda T2 — Chase-Gain (ampliación)` — snowball-effect / rapid-scaling vectors built on top of T1.
- `### Tanda T3 — Síntesis & Ventaja Estructural` — compounding advantage and irreversible moat; the long-horizon shape.

**Partes (orthogonal slots inside each tanda):**

- `#### Parte I — Narrativa` — why this exists; the human-anchored story; Refugio-voice context.
- `#### Parte II — Estructura` — the shape, framework, schematic, or operational mechanic.
- `#### Parte III — ROI` — tiempo / dinero / riesgo of applying it; ties into the section ROI block.

The validator (`tools/distiller/validate.py`) enforces both marker regexes (`tanda_heading_regex`, `parte_heading_regex` from `schema.tandas_partes_spec`) per section file. A section missing any required tanda or parte fails exit 1.

The §2 native "POR TANDAS" semantic (quick-wins → structural → arquitectura) is absorbed by the depth-tanda axis: T1 = quick wins, T2 = structural, T3 = arquitectura. No conflict, no duplication.

---

## SECCIÓN 1 — RESUMEN GENERAL (ARQUITECTÓNICO)

Compress the dataset into a load-bearing architectural snapshot. The output is not an abstract — it is the map a new engineer or strategist would need to act in the first 30 minutes. The body must surface, across its three tandas:

- WHAT the dataset is about, in one sentence (no jargon, no qualifications).
- WHICH systems / projects / decisions it informs (cite Owner-known anchors when the dataset names them: KobiiCraft, LaptOps, KobiiSports Resort, Helsinki, MundiCraft, Andorra).
- WHAT THIS SECTION SELF-IS — the architectural spine readers should hold in mind throughout the remaining 21 sections.

Reject patterns: marketing language; table-of-contents prose; summaries that hide the spine. The Resumen General IS the spine.

## SECCIÓN 2 — IDEAS ACCIONABLES (POR TANDAS)

Surface actionable items the dataset endorses. The native "Tandas" semantic of this section maps directly onto the depth-tanda axis:

- T1 Baseline = quick wins (executable within 24h, single owner, reversible).
- T2 Chase-Gain = structural (1 week, 2-3 collaborators, partial reversibility).
- T3 Síntesis = arquitectura (1 month+, multi-system commit, irreversible by design).

Each idea entry inside a tanda: action verb (imperative), expected ROI dimension (tiempo / dinero / riesgo / soberanía / escalabilidad), prerequisite cost in tooling or attention. Reject patterns: ideas that need a meeting before they need a commit; ideas whose prerequisite cost is higher than the listed ROI; ideas phrased as "explore" or "consider".

## SECCIÓN 3 — FRAMEWORKS Y MODELOS MENTALES

Extract the cognitive frameworks the dataset deploys or implies. Each entry: name (or proposed name if implicit), one-line shape (`A maps to B via C`), domain of applicability (where it WORKS), and one boundary condition (where it BREAKS). Cap 5-9 frameworks per dataset.

Reject patterns: generic frameworks any business book would name (Porter / BCG / SWOT) unless the dataset uses them in a domain-shifted way; frameworks whose boundary condition is "use your judgement"; frameworks that lack an operational handle.

## SECCIÓN 4 — ESTRATEGIAS (SOPs + ÁRBOLES DE DECISIÓN)

Render the dataset's strategic moves as executable SOPs and decision trees. Each SOP: 5-12 steps maximum, every step has an observable success criterion. Each decision tree: `if A then B else C` chains where every leaf is a concrete action — never a deferral. Include the strategic intent (1 line) at the top of each SOP/tree so a reader can detect when the procedure applies to a NEW situation outside the dataset's home domain.

Reject patterns: SOPs that end with "iterate"; trees with leaves of "see specialist"; strategies whose first step is "align stakeholders".

## SECCIÓN 5 — PATRONES, LEYES OCULTAS Y PRINCIPIOS

Surface the structural patterns the dataset exhibits but does not name. Each entry: pattern name (coin one if needed), one-line statement, evidence in the source (file path / quote / page / timestamp), and a cross-domain echo (where the same pattern appears outside this dataset's home domain). These are the LAWS — what survives if the dataset's surface features are stripped away.

Reject patterns: aphorisms; principles that are restatements of well-known maxims (KISS, DRY, YAGNI) without domain-specific bite; patterns with only one evidence point.

## SECCIÓN 6 — SEÑALES SOCIALES Y JUEGOS DE PODER

Map the social, political, and power dynamics the dataset references or relies on. For each: actor (role, not name unless public), motivation (what they want, what they fear), lever (what makes them act), and observable signal (how an outside observer detects this dynamic firing). The Owner consumes this as situational intelligence — what coalitions matter, where gatekeepers sit, which signals precede a power shift.

Reject patterns: gossip; ad-hominem framing; signals that require insider access to detect; "everyone is rational and aligned" abstractions.

-- FIN DE TIER 1 --

## SECCIÓN 7 — CITAS CLAVE (DESTILADAS)

Extract verbatim quotations from the source whose **removal would degrade the dataset's strategic value**. Each citation: ≤ 2 lines, source-attributed (timestamp / page / speaker / line-number when known). Cap 5-12 citations per section. A citation only counts as DESTILADA if it compresses a **transferable principle**, not an anecdote.

Reject patterns:
- Bare aphorisms with no operational consequence.
- Quotes lifted out of context that lose meaning.
- Anything that paraphrases — verbatim only.

Each citation must be followed by a 1-line **interpretation** stating how the principle is operationalizable in the Owner's stack.

## SECCIÓN 8 — ERRORES, SESGOS Y ANTI-PATRONES

Catalog every failure mode the source surfaces — explicit mistakes, cognitive biases, and structural anti-patterns. For each entry emit:

- **Symptom** (1 sentence): what an observer sees when this fails.
- **Root cause** (1 sentence): the underlying mechanism, not the trigger.
- **Vaccine** (1 sentence): a concrete action — code-level, process-level, or architectural — that makes the failure mode unrepeatable.

If the same anti-pattern projects across multiple project domains (plugin → daemon → frontend), note the cross-domain echo explicitly. Reject filter: entries whose vaccine is "be more careful" or "review more thoroughly" do not survive — only operationalizable vaccines count.

## SECCIÓN 9 — AGENTES Y WORKFLOWS (CREACIÓN DIRECTA DESDE EL DATASET)

Convert the dataset's heuristics into deployable agent specs. Each agent entry:

- **Name** (kebab-case).
- **Role** (1 line): what decision it owns.
- **Trigger condition** (event, file path, or prompt pattern).
- **Primary tool / skill / module dependency.**
- **Exit condition** — the observable that proves the agent is done.
- **Hand-off contract** — what artifact / state it surrenders to the next agent.

Workflow chains: render as `A → B → C` with the predicate that fires each transition spelled out (`A→B when …`). Output is meant to drop directly into `~/.claude/agents/<name>.md` or a Power-Pack module skeleton — no rewriting required.

## SECCIÓN 10 — FUNCIONES NUEVAS PARA SAAS Y SISTEMAS IA EMPRESARIALES

For each strategic vector in the dataset, propose 1-3 new product features deployable as SaaS or enterprise AI. Each feature entry:

- **ICP** (Ideal Customer Profile, 1 line — who buys, why now).
- **Pain neutralized** (1 sentence, observable cost in the buyer's day).
- **MVP scope** — ≤ 2 weeks of build, named technologies, named integrations.
- **Moat created** — the structural reason a competitor can't replicate this in < 6 months.

Reject features whose moat collapses without continuous human curation, and features whose ICP is "everyone".

## SECCIÓN 11 — SERVICIOS NUEVOS Y OCÉANOS AZULES (APLICABLE A LOS PROYECTOS DEL USUARIO)

List blue-ocean services the dataset implies but does not name. Each entry:

- **Served niche** (specific demographic + jobs-to-be-done).
- **Why blue** — no entrenched competitor, named alternatives that miss this niche.
- **ROI tier** — Temporal / Patrimonial / Soberanía / Escalabilidad.
- **Risk profile** — Crítico / Alto / Moderado / Bajo.
- **Owner-project anchor** — explicit mapping to KobiiCraft / KobiiSports Resort / LaptOps / Helsinki Live-Feed or a named adjacent venture.

Reject filter: services that require licenses, permits, or jurisdictional permissions the Owner does not already hold.

## SECCIÓN 12 — SÍNTESIS PARA ENTRENAMIENTO PROFUNDO

Compress the dataset into a training-grade synthesis suitable as a fine-tuning seed or system-instruction prompt. Output three sub-layers:

1. **Canonical taxonomy** — terms + definitions extracted verbatim from the source. No paraphrase.
2. **Decision trees** — `if-then` chains the source endorses, rendered as readable nested bullets.
3. **Failure-mode dictionary** — cross-referenced to §8, indexed so any vaccine can be looked up by symptom.

Total under **1200 words** to fit a single context-injection window. If the source overruns that budget, prefer compression over completeness — strategic depth over surface breadth.

## SECCIÓN 13 — INTEGRACIÓN MULTI-SISTEMA (INFINITYOPS CORE)

Map how the dataset's outputs plug into the Owner's existing infrastructure: KobiiCraft (Paper plugins), KobiiSports Resort, LaptOps Hive, the Power Pack itself, the Knowledge Vault. For each integration target:

- **Data ingress format** — file extension, schema reference, transport (HTTP / WebSocket / direct file).
- **Data egress format** — what flows back out, who consumes it.
- **Governance gate** — who or what signs off (Owner manual? validator? Council of 5?).
- **Failure isolation boundary** — when this integration fails, which other systems must keep running.

Identify shared schema collisions the Owner must resolve **before** wiring this dataset into the InfinityOps spine. Flag any field that exists in two target systems with semantically different meanings.

-- FIN DE TIER 2 --

## SECCIÓN 14 — COGNITIVE MIRROR & ESPEJO DEL OWNER

Reflect the Owner's own cognitive shape back, surfaced from the dataset. Three reflections required, distributed across the three depth-tandas:

- **Identity anchors** — values, anchors (Refugio, MCPE, 2014, KobiiClaw), and commitments the dataset reinforces. Cite the dataset evidence for each anchor.
- **Blind spots** — patterns the Owner is drawn to that the dataset surfaces as risk-shaped or repeat-failure-shaped. Name the bait that makes the pattern attractive.
- **Leverage** — domains where the Owner's existing cognition compounds when applied to this dataset's content. Cite the dataset evidence that the compounding is real, not flattery.

The output is a mirror, not a compliment. If the dataset reveals a delusion the Owner holds, name it; if it reveals an underused strength, name that too.

Reject patterns: generic "know thyself" platitudes; flattery; reflections that don't tie back to one or more named anchors.

## SECCIÓN 15 — DECISION TRACEABILITY & ROI CAUSALITY LAYER

For every major decision the dataset references or implies, render the full causal chain: trigger event → decision → first-order consequence → second-order consequence → ROI realized (or sunk cost). Each decision entry: who decided, what alternatives existed, why this one was chosen, and what the measured outcome was (cite numbers if available).

The goal is to make every decision in the dataset re-auditable — a future Owner or auditor can reconstruct WHY. Each entry stores its own evidence (file paths, timestamps, witnesses) inline so the audit does not need to re-derive context.

Reject patterns: decisions framed as inevitable; consequences described without first-vs-second order separation; outcomes asserted without measurement; "we decided collectively" framings.

## SECCIÓN 16 — ANTIFRAGILIDAD & KILL-SWITCH UNIVERSAL

Surface the conditions under which each component of the dataset's recommendation BREAKS, and the kill-switch that incinerates the failed branch before contamination spreads. Each entry: component, failure mode, observable breakage signal, kill-switch action (specific command, file deletion, branch revert, or human escalation).

Embed the canonical 🧨 KILL-SWITCH marker once inside this section's T3 tanda — it is the marker the validator looks for to confirm the kill-switch contract is honored at the dataset level, not just per-component.

The system is contractually antifragile — every recommendation must come with its own abort condition. Reject patterns: "monitor and adjust"; switches whose execution requires the same actor who introduced the failure; switches that require Owner approval AND Owner is the failure mode.

## SECCIÓN 17 — PENSAMIENTO ARBORESCENTE (otros contextos y propósitos de negocio)

Project the dataset's content into adjacent business contexts beyond the obvious home domain. For each branch:

- **Target domain** (named industry / segment).
- **What carries over verbatim** — the principle or pattern that needs no translation.
- **What requires translation** — domain-specific vocabulary or constraint shifts.
- **What is rejected outright** — content that does not survive the move.

Three to five branches minimum. The goal is to harvest the dataset's TRANSFERABLE structure — what does this dataset teach about [adjacent domain X] even though it never mentions X?

Reject patterns: branches into trivially-similar domains; branches whose translation effort exceeds 50% of the original signal; branches whose only justification is "it's also a system".

## SECCIÓN 18 — ROI DEL DATASET (tiempo/dinero/riesgo) — CON FREEZE GATE

Render a dataset-level ROI card distinct from per-section ROI blocks: aggregated time saved, money saved or unlocked, risk neutralized, sovereignty / consciousness preserved. Numbers cite their provenance (which section, which evidence).

Then declare a FREEZE GATE: the condition under which acting on the dataset's recommendations would burn more value than it creates — for example, "freeze action if competing dataset Y arrives within 30 days" or "freeze action if Owner-project anchor X enters drawdown". The freeze gate is not pessimism — it is the dataset's own anti-overshoot condition. Without it, the dataset becomes a maximalist hammer.

Reject patterns: ROI numbers without provenance; freeze gates phrased as "if things change"; freeze gates that never fire.

## SECCIÓN 19 — PLAN DE ACCIÓN CON EL DATASET (operativo + ejecución)

Render a concrete execution plan that moves the dataset from on-disk-knowledge to in-production-effect. Three phases mapped to the three depth-tandas:

- **T1 — PREP** — what gets staged, who reviews, where artifacts land. Time-box: 1-3 days. Exit criterion: named artifact at named path.
- **T2 — DEPLOY** — the smallest reversible deployment, with verifications named. Time-box: 1-5 days. Exit criterion: observable signal in production (log line, dashboard tick, user action).
- **T3 — AMPLIFY** — the snowball steps that take a verified deployment to compounding scale. Time-box: 2-6 weeks. Exit criterion: measurable change in the leading indicator from §21.

Each phase: owner, time-box, exit criteria. Reject patterns: plans with phases longer than 2 weeks at T1/T2; plans whose exit criteria are "feels done"; plans without a named owner.

## SECCIÓN 20 — LOOPS DE CASHFLOW & CAPITAL PACIENTE

Map the dataset's recommended cashflow loops and patient-capital allocations. Each loop entry:

- **Input** — where money enters.
- **Output** — where money compounds.
- **Velocity** — how fast a unit cycles (per day / per week / per quarter).
- **Decay condition** — the signal that the loop has stopped compounding and capital should rotate out.

Patient-capital entries additionally specify: minimum holding period before ROI realization, and signals that justify holding through interim drawdown (so the Owner does not exit at the first dip).

The Owner consumes this as the FINANCIAL spine of the dataset — what compounds vs what is consumed. Reject patterns: loops without decay conditions; patient-capital recommendations without a defined exit signal; "set it and forget it" framings.

## SECCIÓN 21 — TELEMETRÍA ESTRATÉGICA DE CICLOS

Define the telemetry the Owner needs to detect whether the dataset's recommendations are landing or drifting. For each strategic vector surfaced in §2 (accionables) or §19 (plan de acción):

- **Leading indicator** — early, cheap-to-measure, available within the cycle.
- **Lagging indicator** — truthful, expensive-to-measure, available after the cycle closes.
- **Cadence** — per session / per week / per release / per quarter.
- **Actionable threshold** — the value at which the indicator stops being informative and becomes a trigger for a §16 kill-switch or §19 amplify-step.

Reject patterns: vanity metrics; indicators without thresholds; cadences slower than the underlying cycle; indicators whose measurement cost exceeds the decision value they unlock.

## SECCIÓN 22 — INFERENCIA DECISIONAL EXÓGENA & CONOCIMIENTO NEGATIVO (Outside-the-Box Time-Saver)

This is the fused outermost section — the Owner's escape hatch from the dataset's home domain. Two complementary harvests, distributed across the three depth-tandas:

- **Inferencia Exógena** — decisions inferred from adjacent domains that the dataset does NOT cover but COULD steal from. Each entry: adjacent domain, decision pattern transplanted, expected friction during transplant, and the time saved by NOT having to re-derive the pattern from scratch.
- **Conocimiento Negativo** — what the dataset tells you NOT to do. Each entry: anti-pattern, the bait that draws people into it, the cost of the trap (in hours / dollars / opportunity), and the early-warning signal that lets the Owner detect the trap BEFORE paying its cost.

The fusion is non-accidental: outside-the-box inference IS the harvest mechanism for inheriting other people's negative knowledge. Skip the failure ladder; inherit it. The Negative Knowledge Vault is the dataset's most defensible IP — knowing what to skip is a permanent compounding advantage and is harder for a competitor to replicate than knowing what to do.

Reject patterns: inferences that require expertise the Owner does not have; negative knowledge without an early-warning signal (it then cannot fire in time to save the cost); meta-commentary about how clever the cross-domain transfer is.

-- FIN DE TIER 3 --

-- FIN DE DATASET v1.2 --

---

## ANCILLARY MARKERS (verbatim from dataset)

- `## 4. CONEXIÓN CON UNIVERSAL KNOWLEDGE DISTILLATION LAYER (UKDL)` — cross-project destilación transversal + IP defendibility tagging.
- `## 5. REGLAS DE EJECUCIÓN PARA LA IA` — hard rules (ROI temporal threshold, secret-handling via `/etc/` + 600 perms, Bedrock-agnostic export discipline).
- `## 🧮 CALCULADORA DE ROI DEL DATASET (PRE-SOFTWARE)` — dataset-level ROI card, distinct from per-section cards (rendered inside §18).
- `## 🧨 KILL-SWITCH CANÓNICO` — incinerate code, return to "Refugio" simplicity if airport-style complexity creeps in (canonical marker lives inside §16 T3).

The driver may surface these as appendix sections in `READY.md` without counting them against the 22 mandatory sections.

---

## RETURN-TO-DORMANT

After `/cpp-distill` completes (validator exit 0), this part returns to dormant state. Re-loading happens automatically on the next `/cpp-distill` invocation.
