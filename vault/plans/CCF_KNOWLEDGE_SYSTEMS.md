# CCF Knowledge Systems — Phase 4

> Feeds from CCF runs into the existing PP knowledge vault. Reuse verdict throughout: `graphify`
> (location/navigation), `fable_distillation` (delta distillation), `akos_knowledge` own the
> generic knowledge-consumption chain (Phase -1) — CCF does not build a parallel vault, it
> produces typed feed events that the existing chain ingests.

## Feeds emitted by every sealed CCF run

| Feed | Trigger | Payload | Consumed by |
|---|---|---|---|
| `creative_failures` | Any Trademark Scanner BLOCK, any objective-check FAIL, any `ProviderError` | `{failure_id, component, concept_id, evidence, human_resolution?}` | `pp-never-again` (NEVER_AGAIN injection), Failure Corpus (below) |
| `provider_benchmarks` | Every Model Adapter call | `{provider, model_id, resolution, quality, cost, latency_ms, verdict}` | `pp-tco-advisor` (cost routing), Provider Benchmark Corpus |
| `prompt_evolution` | Every Prompt Compiler invocation across re-runs of the same concept | `{concept_id, prompt_version, avoid_list_version, diff_from_previous}` | Decision Corpus (tracks how `avoid_list.semantic` grows after each caught collision) |
| `quality_evolution` | Every Trademark Scanner run against a corpus version bump (`cpp creative audit`) | `{corpus_version, verdict_deltas[]}` | Trademark Risk Corpus (below) — this is the direct measure of whether the scanner is actually getting better, not just busier |
| `human_preferences` | Every `cpp creative select` | `{concept_id, rejected_concepts[], selection_reasoning?}` | Decision Corpus, and — longer-term — a training signal for whether the Prompt Compiler's concept diversity is well-calibrated |

Every feed event carries `provenance` (which project/run), `timestamp`, and `confidence` per the
CCF-wide convention (mirrors DAIF's own epistemic-marking discipline) — no feed event is accepted
into the vault without these three fields.

## Institutional datasets derived from CCF

### Failure Corpus (seeded in `INSTITUTIONAL_EXTRACTION.md` §B)
- **First entry, mandatory:** CCF-F01, the Trademark Collision Failure — the founding failure
  that justified building component #7 at all. Every subsequent `creative_failures` feed event
  of category `trademark_collision` links back to this founding entry as its origin case, so the
  corpus shows lineage (this specific failure → this specific gate) rather than an undifferentiated
  bag of incidents.
- Ongoing entries: CCF-F02 (empty-shell PDF), CCF-F03 (provider lock-in), CCF-F04 (unbounded
  serial cost), plus any new failure class a real run surfaces that Phase 0/1 didn't anticipate.
- **Growth rule:** a failure is added to this corpus only once, at first observation; every
  subsequent occurrence increments that entry's `recurrence_count`, it does not create a
  duplicate entry — mirrors the PP's existing recurring-error discipline (`pp-error-analyst`,
  CEPS 3+-recurrence promotion path).

### Decision Corpus (seeded in `INSTITUTIONAL_EXTRACTION.md` §C)
- First 5 entries carried forward verbatim from Phase 1 (provider choice, build-script-over-
  dependency, one-call-no-auto-regenerate, SVG-symbol-recolor, manual-vectorization-deferred).
- Ongoing entries accrue from `prompt_evolution` and `human_preferences` feeds: every time a
  human's `selection_reasoning` reveals a criterion the Creative Contract Engine's mood-axis
  extraction didn't capture, that's a decision-corpus candidate for improving component #1, not
  just a one-off preference.

### Trademark Risk Corpus (NEW — justified directly by the founding failure)
- **Why this is a new, dedicated corpus and not folded into the generic Failure Corpus:** the
  Trademark Scanner (#7) is explicitly the one component in the whole CCF that ships with known,
  declared-incomplete coverage (per `CCF_ARCHITECTURE.md` §7's honest-scope note). A dedicated
  corpus is how that gap gets tracked and closed over time rather than staying permanently
  incomplete: every `quality_evolution` feed event and every human-caught collision the narrow
  first-pass check *missed* becomes a corpus entry that either (a) grows the shape-category
  checklist, or (b) becomes a candidate reference-mark entry for the eventual corpus-backed
  similarity model.
- **Schema:** `{case_id, concept_description, detected_by (scanner|human), nearest_known_mark,
  verdict_at_time, corpus_version_at_time, resolution}`.
- **Done criterion for this corpus (not for CCF as a whole):** it is never "finished" — its
  purpose is a standing, growing record; the relevant health metric is recurrence rate of
  human-caught-but-scanner-missed collisions trending down release over release, not a count
  reaching zero.

## Non-goals (explicitly deferred, per Phase -1/Phase 1 ROI ranking)

No dedicated corpus is built yet for: vectorization-step outcomes (component out of v1 scope),
provider-fallback events (no second provider exists yet to benchmark against), or parallelization
throughput (no fan-out implementation exists yet to measure). Building a corpus for a capability
that doesn't exist yet would be exactly the kind of unwired, orphaned module the PP's Liveness
Standard flags — these corpora get created when their producing capability ships, not before.
