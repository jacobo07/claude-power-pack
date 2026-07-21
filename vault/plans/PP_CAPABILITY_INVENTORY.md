# PP Capability Inventory — Creative Compilation Framework (CCF) Reuse Audit

> Phase -1 output (blocking, per Owner's CCF ULTRA-PLAN spec). Read 2026-07-21 against the
> live repo (`git log` HEAD `da0b3ae`), not the fictional apparatus in CLAUDE.md prose.
> Method: `Glob`/`Grep`/`Read` over `modules/`, `vault/knowledge_base/`, `agents/` — cross-checked
> against `vault/knowledge_base/cpp_ias/NON_DUPLICATION_LEDGER.md` and `.../SYSTEM_REGISTRY.md`,
> which already run this exact audit at the whole-estate level (sealed 2026-07-12).

## Headline finding

The repo already carries **70+ modules** and **~524k words** of sealed institutional
specification (`SYSTEM_REGISTRY.md` inventory) whose own governing law is:
*"No [new layer] may re-govern any row above at its own level... A dataset that cannot name
a distinct ensemble-level object is REJECTED."* Applying that law to CCF: **most of the CCF
Core Architecture in the prompt (Phase 2) is not new — it is a rename of machinery that already
exists one level up.** Building it as specified would violate the repo's own Non-Duplication
Ledger the same way a 15th entry in that ledger would.

| CCF Core component (as specified) | Existing owner | Verdict |
|---|---|---|
| Creative Contract Engine | `vault/knowledge_base/d2a_fabric` (DAIF-04 Institutional Contract Fabric — "typed, evidence-grounded, authority-aware, resumable representations" of any cognitive work the PP produces) | **REUSE/EXTEND** — instantiate a Creative Contract as a DAIF contract type, don't reinvent the fabric |
| Creative Pipeline Runtime (orchestration, retries, budget) | `cognitive_os` (CO-00–12: routing, budget, session economy) + `parallel_mesh` (PM-01–05: cross-agent coordination) | **REUSE** |
| Agent Harness Framework (role/jurisdiction/budget/handoff contracts) | `agents/*.md` (12 live agents already use exactly this contract shape — see `oneshot-architect-auditor.md`: name/description/tools/role/output_contract) | **REUSE the pattern** — new agents are new `.md` files, not a new framework |
| Creative Provenance Engine (pixel → prompt → model → approval) | DAIF-21 (Reality Synchronization & Semantic Change) + `enforcement/done_gate` (`artifact_done_gate.py` already does hash/kind/status/verdict on artifacts) | **EXTEND** |
| Creative Manifest System / Creative Versioning / Regression | `done_gate` + `session_resilience` (checkpoint/rollback) + `replay_harness.py` (diff-based regression already exists generically) | **EXTEND** |
| Creative Intent Compiler (brief → structured spec) | `modules/karimo-harness/prd_parser.py` (deterministic, sha256-reproducible PRD→BLUEPRINT parser — same shape: NL brief → structured, evaluable spec) | **EXTEND** — a Creative brief is a PRD variant |
| Creative Evaluation Engine (objective vs. subjective gates, 6-lens review) | `vault/knowledge_base/cdio` + `cdio-reviewer` agent (already does exactly objective-vs-subjective, 6-lens, score-gated visual review — currently scoped to UI, not generation) | **EXTEND** — teach CDIO a "generated-asset" lens, don't build a parallel evaluator |
| QA Fabric / per-stage gates | `enforcement` (rule_compiler, done_gate, sweep_enforcer) | **REUSE** |
| Evidence Ingestion (web/reference sources, provenance) | `vault/knowledge_base/crawl_os` (CrawlOS — evidence ingestion + provenance, confirmed present) | **REUSE** |
| Knowledge Systems / institutional writeback | `graphify` (GK-00–12, knowledge location) + `fable_distillation` (FD, delta distillation) + `akos_knowledge` | **REUSE** |
| CLI namespace pattern (`cpp creative <verb>`) | existing `commands/*.md` + `cpp-*` slash-command family | **REUSE the pattern** |

## What is genuinely NEW (no existing owner found)

1. **Generation Provider Adapter Layer** — PP has zero abstraction today for image-generation
   providers (OpenAI `gpt-image-1`, Midjourney, Flux, Ideogram). `atomic_branding.py` is the
   closest neighbor but is explicitly deterministic/template-based (no network, no LLM) — it
   solves a different problem (Tailwind/motion tokens from a brand string) than "call an
   external image model and manage its capability/cost/failure contract." **Verdict: NEW.**
2. **Brand-domain pipeline stages** — concept brainstorm → per-concept image-gen prompt
   construction → multi-image generation → PDF brand-kit compilation → PNG→SVG vectorization →
   vector-editing handoff. No PP module owns this sequence. **Verdict: NEW**, but scoped as a
   *specialization* riding on the REUSE/EXTEND rows above, not a parallel stack.
3. **Design-token overlap note:** `design-md` (Google DESIGN.md wrapper) and `atomic_branding.py`
   already own *web design-token* generation (Tailwind/DTCG/motion). A Brand Identity Compiler
   that also emits a design-token layer for the brand should **call these**, not re-derive a
   token system.

## Consequence for Phase 1+ scope

Phase 2's 15-subsystem "CCF Core Architecture" should be rewritten as: a thin **Creative
domain profile** that (a) registers new DAIF contract/provenance types, (b) adds a Creative
Intent Compiler as a `prd_parser` variant, (c) adds an image-generation Provider Adapter Layer
(genuinely new), (d) adds domain-specific pipeline stages + evaluators, (e) wires into
`cognitive_os`/`parallel_mesh`/`done_gate`/`graphify` rather than re-implementing their jobs.
This is a **far smaller build** than the original 15-subsystem spec — most of it is composition,
not construction — which is the D2A-mandated outcome, not a scope cut for its own sake.
