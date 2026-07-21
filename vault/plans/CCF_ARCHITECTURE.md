# CCF Architecture — Phase 2

> Status: **SPECIFIED**, not **EXISTS** (per DAIF epistemic marking convention). Grounded in
> `PP_CAPABILITY_INVENTORY.md` (reuse verdicts) and `REVERSE_ENGINEERING_REPORT.md` +
> `INSTITUTIONAL_EXTRACTION.md` (real reference-implementation evidence). Where the reference
> repo's real shape beats the original abstract CCF spec, the real shape is adopted — noted
> per-component as "ADOPTED FROM REFERENCE."

## Component diagram (structured text)

```
Human brief
    |
    v
[1. Creative Contract Engine] ---(DAIF-04 contract type)---> Creative Specification
    |
    v
[2. Config-Driven Pipeline] --(expands spec into N concept configs)--> concept_config[1..N]
    |
    v (per concept, fan-out — parallel_mesh)
[3. Prompt Compiler] --(concept_config + Creative Spec)--> {prompt, avoid_list(semantic)}
    |
    v
[4. Model Adapter Layer] --(prompt, params)--> ImageArtifact | ProviderError
    |
    v
[7. Trademark Collision Scanner] --(ImageArtifact, concept_config)--> PASS | WARN | BLOCK
    |
    v (PASS or WARN+human-ack)
[5. Artifact Compiler] --(N ImageArtifacts)--> showcase.html -> showcase.pdf
    |
    v
[HUMAN: concept selection — human-irreducible, per Institutional Extraction §F]
    |
    v (chosen concept only)
[5. Artifact Compiler, Phase 2 mode] --(chosen ImageArtifact)--> brandkit.html -> brandkit.pdf
    |
    v
[6. Creative Evaluation Engine] --(all artifacts)--> objective_report + human_gate_queue
    |
    v (all objective PASS + human select recorded)
[8. Release Manager] --(artifacts + reports + provenance)--> Brand Package (SEALED)
```

## Components, in dependency order

### 1. Creative Contract Engine
- **Reuse verdict (Phase -1):** EXTEND — instantiates a Creative Contract as a new DAIF-04
  contract *type*, not a new contract fabric.
- **Input:** human brief (free text), optional reference assets/URLs (routed through CrawlOS for
  provenance-tracked ingestion — REUSE, not rebuilt).
- **Process:** ambiguity resolution is mandatory before proceeding — any brief field the compiler
  cannot confidently classify (tone, audience, constraint) is surfaced as a blocking question, not
  guessed. This is a genuine LLM-judgment step (see gap vs. `prd_parser` below).
- **Output:** an executable Creative Specification: `{brand_name, industry, audience, values[],
  constraints{must, must_not}, visual_references[], mood_axis{...}, deadline?}` — typed, stored as
  a DAIF contract instance, not a document.
- **Gap vs. reference repo:** the reference repo has no equivalent stage — `config.json` in the
  real system is hand-written by the human directly. The Creative Contract Engine is the layer
  that produces that `config.json`'s *content* from a natural-language brief. **Decision:** build
  this stage; the reference repo skipped it because its user was technical enough to hand-author
  config directly, which will not hold for a general-purpose CCF.
- **Gap vs. `prd_parser`:** `prd_parser.py` is explicitly regex/heuristic, **no LLM calls**
  (verified against its real source, `modules/karimo-harness/prd_parser.py`). Aesthetic/mood-axis
  extraction from a creative brief is not a deterministic-regex task the way "must/must_not/auth"
  constraint bucketing is. **Decision:** reuse `prd_parser`'s S1–S5 state-machine *shape*
  (tokenize → classify → extract → schema_map → emit) for the deterministic parts (deadline,
  hard constraints, must_not), but the mood/aesthetic axis extraction is a genuinely new,
  LLM-assisted sub-step layered on top — not a wholesale reuse.

### 2. Config-Driven Pipeline
- **ADOPTED FROM REFERENCE**, generalized. The reference repo's `config.json` shape
  (per-concept: font, colours, bg, wordmark, avoid, icon description; global: theme, accent,
  headFont, labels) is extended with one new required field: `icon_direction` (see Prompt
  Compiler) and is designed to be schema-versioned so future specializations (UI, Presentation)
  add their own concept-axis fields without touching the pipeline engine itself.
- **Input:** Creative Specification (from #1).
- **Output:** N `concept_config` entries, each fully self-contained (no cross-concept references),
  enabling independent parallel processing.
- **Reuse verdict:** REUSE `cognitive_os`/`parallel_mesh` for the fan-out execution — this
  component only defines the config *shape*, not a new orchestration engine.

### 3. Prompt Compiler
- **Input:** one `concept_config` + Creative Specification.
- **Output:** `{prompt: string, avoid_list: {named: string[], semantic: SemanticAvoidSpec[]}}`.
- **Fix for CCF-F01 (Trademark Collision Failure):** the reference repo's `avoid` field is
  named-entity-only (`avoid: ["Airbnb"]` style). The Prompt Compiler now ALSO emits a
  `semantic` avoid spec — a structured description of the icon *concept's shape category*
  (e.g. "continuous closed loop," "chat-bubble derivative," "two overlapping circles") extracted
  from the same icon description used to build the prompt. This is consumed by the Trademark
  Collision Scanner (#7), not checked by the Prompt Compiler itself — the compiler's job is to
  *produce* the structured signal, not to judge it.
- **Reuse verdict:** NEW — no existing PP module compiles image-generation prompts; closest
  neighbor (`atomic_branding.py`) is deterministic/template-only with no model call and no prompt
  text output, confirmed by reading its source in Phase -1.

### 4. Model Adapter Layer
- **Reuse verdict:** NEW (confirmed gap in Phase -1 — no image-generation provider abstraction
  exists anywhere in the PP).
- **Interface:** `generate(prompt: string, params: {resolution, quality, ...}) -> ImageArtifact |
  ProviderError`. `ImageArtifact = {bytes, format, resolution, provider, model_id, cost, latency_ms,
  request_id}` — every field the reference repo's live demo actually reported (7 calls, ~90s each,
  cost) becomes a first-class, logged field, not a verbal aside in a chat transcript.
- **Fallback gap (CCF-F03), EXPLICITLY NOT CLOSED in v1:** the reference repo has no fallback
  provider; the Model Adapter Layer's interface is *shaped* to support a second adapter
  (`generate()` is provider-agnostic), but **v1 ships with exactly one adapter (`gpt-image-2`)
  and no automatic fallback logic** — per Institutional Extraction §E ranking, this is lowest ROI
  until a real outage is observed. `ProviderError` propagates to the caller; the Release Manager
  (#8) simply fails the run rather than silently degrading.

### 5. Artifact Compiler
- **ADOPTED FROM REFERENCE, verbatim shape**, this is the single biggest "reuse the real thing,
  don't reinvent the abstract spec" decision in this architecture: `config/source →
  plain build script → HTML → headless-Chrome print-to-PDF`. No PDF library, no design-tool SDK.
  Runs in two modes: **showcase mode** (Phase 1 — N concepts, A4, 2×N/2 grid, disclaimer) and
  **brandkit mode** (Phase 2 — 1 concept, SVG `<symbol>` + CSS-variable recolor, multi-page).
- **Fix for CCF-F02 (empty-shell PDF footgun), MANDATORY:** before building any company/brand's
  PDF, the compiler verifies the expected `ImageArtifact` set for that entry actually exists on
  disk/in the artifact store. If not: **skip that entry and emit a structured warning**
  (`{entry_id, reason: "no_generated_images", skipped: true}`) into the run's evaluation report —
  never silently emit a near-empty PDF. This is the direct, named fix for the observed footgun.
- **Reuse verdict:** the *finisher* (headless-Chrome print-to-pdf, HTML assembly) has no existing
  PP owner and is adopted as-is from the reference shape; the *gating* (skip-if-missing) composes
  with `done_gate`'s existing artifact-verification pattern (`artifact_done_gate.py` already does
  hash/kind/status/verdict checks — this reuses that check *before* the build step fires, not
  after).

### 6. Creative Evaluation Engine
- **Reuse verdict:** EXTEND `cdio-reviewer` / CDIO methodology (objective-vs-subjective, 6-lens,
  score-gated) — currently scoped to UI surfaces; CCF teaches it a "generated-asset" lens rather
  than building a parallel scorer.
- **Objective checks** (from Institutional Extraction §D): wordmark spelling matches config;
  named `avoid` entries absent; resolution/format correct; PDF page count/size within expected
  bounds for images actually present (closes CCF-F02 at the evaluation layer too, belt-and-braces);
  Trademark Collision Scanner verdict is PASS or WARN-with-ack (never silently BLOCK-and-continue).
- **Subjective checks:** queued to the human_gate_queue — concept selection, recolor-variant
  legibility, typography-system coherence — never auto-resolved.

### 7. Trademark Collision Scanner (NEW — dedicated component, not a config field)
- **Why dedicated, not folded into the Prompt Compiler or Evaluation Engine:** the founding
  failure (CCF-F01) demonstrated that a text-level `avoid` field cannot catch a semantic/visual
  collision — this requires an actual comparison against a reference-mark corpus, which is a
  distinct capability (a similarity model + a maintained corpus of known marks) from prompt
  assembly or generic quality scoring.
- **Input:** the generated `ImageArtifact` + the `semantic` avoid spec from the Prompt Compiler
  (#3) + a maintained reference corpus of well-known marks (shape-level, not just name-level).
- **Output:** `{risk_score: float, verdict: PASS | WARN | BLOCK, justification: string,
  nearest_known_mark?: string}`.
- **Gate semantics:** BLOCK halts the pipeline for that concept before it ever reaches the
  showcase (Release Manager, #8, refuses release on any un-cleared BLOCK). WARN requires an
  explicit human acknowledgment recorded in the human_gate_queue before that concept can proceed
  to showcase inclusion — mirroring exactly how the reference repo's creator caught the Airbnb
  case manually, except now structurally required rather than incidental.
- **Honest scope note (epistemic marking: PROPOSED, not EXISTS):** a production-grade visual
  similarity scanner against a corpus of registered marks is a real ML/data engineering project,
  not a config flag. This architecture specifies the *contract* (input/output/gate semantics);
  it does not claim the scanner is built. The first shippable increment is the gate wiring itself
  (BLOCK/WARN semantics, human-ack queue) paired with a deliberately narrow first-pass check —
  the named-entity list plus a small, explicitly-scoped shape-category checklist derived directly
  from the Airbnb case (closed loops, chat-bubble derivatives, overlapping-circle marks). That
  narrow check is logged as partial coverage on every run, never presented as full trademark-
  database coverage; the corpus-backed similarity model is a tracked follow-on, not an assumed
  day-one capability.

### 8. Release Manager
- **Reuse verdict:** EXTEND `done_gate` + `session_resilience` (checkpoint/rollback) +
  `replay_harness.py` (diff-based regression, already generic) rather than new Manifest/
  Versioning/Regression subsystems, per Phase -1.
- **Release gate:** all objective Evaluation Engine checks PASS, human concept-selection is
  recorded, and no un-acknowledged Trademark Scanner BLOCK exists anywhere in the artifact set.
- **Output:** a Brand Package = every generated artifact + every compiled prompt + the evaluation
  report + the decision log (which concept was picked, by whom, when) + the provenance chain
  (DAIF-21 reality-sync record: brief → contract → concept configs → prompts → model calls →
  artifacts → human approvals → package). This is the CCF instance of DAIF's existing "typed,
  evidence-grounded, authority-aware, resumable representation" — not a new provenance engine.

## Specialization: Brand Identity Compiler

Inherits the full CCF Core (1–8) unmodified. Adds only:
- **Brand-specific config schema**: `{industry, values[], audience, competitor_avoid_list}` layered
  onto the generic Config-Driven Pipeline shape (#2).
- **Brand research stage**: a CrawlOS-backed (REUSE) evidence-ingestion pass over competitor
  marks and industry visual conventions, feeding both the Creative Contract Engine (#1, mood-axis
  grounding) and the Trademark Scanner's reference corpus (#7, competitor-specific entries).
- **Moodboard stage**: a showcase-mode Artifact Compiler run (#5) over *reference* assets rather
  than generated concepts — reuses the identical rendering path, different input set.
- **Brand guidelines output**: the existing brandkit-mode Artifact Compiler output *is* the
  guidelines document (6-page PDF structure observed in Phase 0) — no separate guidelines
  generator needed.
- Does **not** reimplement contract handling, prompt compilation, model adaptation, artifact
  building, evaluation, scanning, or release — all inherited.

## Future specializations (UI Compiler, Presentation Compiler, etc.)

Each new specialization needs exactly two new things: **(a)** a domain-specific config schema
extension (#2) and **(b)** domain-specific evaluators plugged into the Creative Evaluation Engine
(#6, new lens on the same CDIO-extended scorer). Everything else — Contract Engine, Model Adapter,
Artifact Compiler, Trademark Scanner (or its domain-appropriate collision-check analog, e.g.
component-library licensing for a UI Compiler), Release Manager — is inherited without
modification. This is the concrete test of Phase -1's reuse-first finding: if a new specialization
ever needs a *new* instance of #1/#4/#5/#8, that is a signal the CCF Core abstraction is wrong,
not that the specialization is unusual.

## Dependency graph (existing PP systems this composes with)

```
CCF Core
 ├─ 1. Creative Contract Engine ──depends on──> DAIF-04 (contract fabric), CrawlOS (evidence ingestion)
 ├─ 2. Config-Driven Pipeline   ──depends on──> cognitive_os (routing/budget), parallel_mesh (fan-out)
 ├─ 3. Prompt Compiler          ──depends on──> (none — new, leaf component)
 ├─ 4. Model Adapter Layer      ──depends on──> (none — new, leaf component)
 ├─ 5. Artifact Compiler        ──depends on──> done_gate (artifact_done_gate.py existence checks)
 ├─ 6. Creative Evaluation Eng. ──depends on──> cdio-reviewer / CDIO 6-lens methodology
 ├─ 7. Trademark Collision Scanner ──depends on──> (none — new; consumes #3's semantic avoid_list)
 └─ 8. Release Manager          ──depends on──> done_gate, session_resilience, replay_harness.py,
                                                  DAIF-21 (reality sync / provenance)
Agent execution (any component needing an LLM call) ──uses the pattern of──> agents/*.md (existing
  12-agent contract shape: name/description/tools/role/output_contract) — new agents (e.g. a
  "creative-contract-compiler" agent) are new .md files in that same directory, not a new
  Agent Harness Framework.
```

## Gaps vs. reference repo, with decisions

| Gap | Reference repo behavior | CCF decision |
|---|---|---|
| No brief→config compiler | Human hand-writes `config.json` | Build Creative Contract Engine (#1) — required for a general-purpose tool, not required for the creator's own single-user tool |
| No semantic trademark check | `avoid` is named-entity text only | Build Trademark Collision Scanner (#7) as a dedicated, honestly-scoped component (narrow first-pass check now, corpus-backed version as a tracked follow-on) |
| `to-pdf.mjs` rebuilds empty entries | No existence check | Mandatory existence-check fix specified in Artifact Compiler (#5) |
| No provider fallback | Single `gpt-image-2` call, fails hard on error | Interface shaped for multi-provider (#4), but **v1 ships single-provider by design** — documented as an open gap, not silently closed |
| No parallelization | Sequential, ~90s/call | `parallel_mesh` fan-out at the Config-Driven Pipeline layer (#2) — required for the "100+ brands" institutional framing, not required at reference-repo's single-brand scale |
| Manual PNG→SVG + Vectorpea step | Fully external, browser-driven, unscripted | **Deliberately out of CCF v1 scope** — Institutional Extraction §E ranks this ROI below the trademark/empty-PDF fixes; revisit once Core is proven |
