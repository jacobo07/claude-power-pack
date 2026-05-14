# PART D — KOBIIDISTILLEROS MOTHER PROMPT (Sleepy)

Lazy-loaded by `/cpp-distill`. Defines the verbatim 19-section contract, the per-section required blocks, the tier-end markers, and the materialization rules for the in-session distillation driver.

**Status (2026-05-14):** Sections 1-6 are inferred from `Dataset KobiiDistillerOS 1.txt` (verbatim wording, single source of truth). Sections 7-19 carry the gap marker `<<AWAITING OWNER VERBATIM — Q1.a>>` until the Owner pastes the canonical Mother Prompt body. `run.py` will refuse to materialize gap-marked sections.

---

## CONTRACT

For every `/cpp-distill` invocation, the driver MUST emit 19 markdown files at `<output_root>/Tier_<T>/Seccion_<N>.md` matching the schema at `tools/distiller/schema.json`. Each section file MUST contain, in order:

1. A heading: `## <N>. <SECTION_TITLE>` — title sourced from `schema.json#section_titles[<N>]` (verbatim, accents preserved).
2. A body paragraph (no fixed length) distilling the ingestor chunks relevant to the section's theme. No filler. No empty-button references. No `Coming Soon`.
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
- After Sección 19: `-- FIN DE TIER 3 --` followed by `-- FIN DE DATASET v1.0 --`

The `🧨 KILL-SWITCH` marker appears once, in the section that handles abort conditions (Owner-defined; currently expected in the Tier 3 governance band).

---

## SECCIÓN 1 — INGESTOR ATÓMICO (IRE STAGE 1-2)

The ingestor is the entry gate. It accepts raw inputs and emits chunked, redacted, size-capped sidecars for the distillation driver. Three input modalities are in scope:

1. **Texto masivo** — automatic segmentation of files > 1 MB to avoid token-context collapse. The Atomic Ingestor in `tools/distiller/ingest.py` enforces a 1 MB hard cap with `--force` override.
2. **Transcripción de audio/vídeo** — Whisper-class integration for 40-minute gameplay → distillable text. Out of scope for v1; reserved for a separate `/ultra` cycle.
3. **Vision-to-Data** — extraction of architectural metadata from images (stadium DNA v2). Out of scope for v1; reserved.

Pre-LLM gates the ingestor enforces unconditionally: placeholder rejection, secret redaction, header-or-block chunking. See `schema.json#ingestor_limits` and `schema.json#redaction_patterns`.

## SECCIÓN 2 — EL MOTOR DE DESTILACIÓN (EL CEREBRO)

The engine applies the **Filtro de Exposición Operativa Extrema**. Every chunk runs through two dual functions before being committed to the output:

- **Avoid-Loss.** Blocks ideas that generate technical debt, "airport design", or irreversibility risk. Asks: *what kill-switch does this proposal require, and is the cost of reversing it ever paid?*
- **Chase-Gain.** Identifies snowball-effect opportunities and rapid-scaling vectors. Asks: *what compounds if this lands cleanly, and over what time horizon?*

A chunk that passes Avoid-Loss but fails Chase-Gain is preserved as defensive scaffolding. A chunk that passes Chase-Gain but fails Avoid-Loss is parked in a *deferred* bucket and surfaced only when its risk profile can be neutralized. Chunks that pass both are committed to the section being distilled.

## SECCIÓN 3 — MATERIALIZACIÓN (IRE STAGE 7)

The output is not a summary. It is **Materia Ejecutable**. Acceptable materialization targets:

- `.java` for KobiMapEngine extensions.
- `.json` DNA files for stadium / map topology.
- `.md` files in the Knowledge Vault.

`/cpp-distill` materializes only the third — markdown into the vault. Java/JSON materializers are downstream consumers that read the Tier_N markdown.

## SECCIÓN 4 — PROTOCOLO ANTI-MEDIOCRIDAD (CONTRATO DE REALIDAD)

KobiiDistillerOS is forbidden from generating:

- **Placeholders** — `Coming Soon`, `TODO`, `Añadir más tarde`, `<TU_URL_REAL>`, `raise NotImplementedError`. The validator surfaces these as exit code 2; the ingestor rejects them pre-LLM.
- **Botones vacíos** — every UI affordance referenced in distilled output must be wired to a real function. References to unbacked buttons trigger a section rewrite.
- **Logging frío** — corporate / generic / cynical tone. The voice must remain "Refugio Humano" with nostalgic anchoring. The Hawkins filter (>200 consciousness) is the qualitative gate.

A section that violates any of the three is rejected and re-iterated using the universal iteration protocol at `C:\Users\kobig\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-visual.txt`.

## SECCIÓN 5 — KERNEL vMAX-NULL-ERROR

The kernel monitors its own runtime. If hallucination rate or context drift exceeds **2 %**, the system enters **Freeze de Memoria** — distillation halts, no further chunks are committed, and the operator is notified. The threshold is non-negotiable; tuning it requires a separate `/ultra` cycle and an updated UKDL entry.

**Vacunas (Vaccine Synthesis).** Every corrected error lands as a UKDL entry — symptom, root cause, fix, vaccine. The system is contractually unable to repeat the same error twice; if it does, the vaccine entry was malformed and itself becomes an audit incident.

## SECCIÓN 6 — DISEÑO DE SOBERANÍA (MÓVIL & PC)

The vault must be accessible from mobile (Flutter / Streamlit) and PC (Claude Code / Terminal). Cross-server sync is mandatory. Three vault surface guarantees:

- **Visualización de ROI** — every processed dataset surfaces an ROI card (Temporal, Económico, Riesgo). The card is generated from the section ROI blocks.
- **Nivel de Conciencia (Filtro Hawkins)** — auto-evaluation of >200 consciousness. Content scoring cynical or purely transactional is rejected at the surface, not just at the validator.
- **Sovereign read path** — even offline, the vault is browsable; sync is opportunistic, not a hard dependency.

---

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

If the same anti-pattern projects across multiple project domains (e.g. plugin → daemon → frontend), note the cross-domain echo explicitly. Reject filter: entries whose vaccine is "be more careful" or "review more thoroughly" do not survive — only operationalizable vaccines count.

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

## SECCIÓN 14 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

## SECCIÓN 15 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

## SECCIÓN 16 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

## SECCIÓN 17 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

## SECCIÓN 18 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

## SECCIÓN 19 — <<AWAITING OWNER VERBATIM — Q1.a>>

(see Sección 7 binding rule.)

---

## ANCILLARY MARKERS (verbatim from dataset)

- `## 4. CONEXIÓN CON UNIVERSAL KNOWLEDGE DISTILLATION LAYER (UKDL)` — cross-project destilación transversal + IP defendibility tagging.
- `## 5. REGLAS DE EJECUCIÓN PARA LA IA` — hard rules (ROI temporal threshold, secret-handling via `/etc/` + 600 perms, Bedrock-agnostic export discipline).
- `## 🧮 CALCULADORA DE ROI DEL DATASET (PRE-SOFTWARE)` — dataset-level ROI card, distinct from per-section cards.
- `## 🧨 KILL-SWITCH CANÓNICO` — incinerate code, return to "Refugio" simplicity if airport-style complexity creeps in.

The driver may surface these as appendix sections in `READY.md` without counting them against the 19 mandatory sections.

---

## RETURN-TO-DORMANT

After `/cpp-distill` completes (validator exit 0), this part returns to dormant state. Re-loading happens automatically on the next `/cpp-distill` invocation.
