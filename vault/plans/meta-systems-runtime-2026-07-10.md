# Universal Meta-Systems Runtime — Architecture Decision (STOP #1 backup)

Date: 2026-07-10 · Pane: CLAUDE-POWER-PACK · Base: `c4720cf` · Corpus: `45dd1f9`
Status: **DONE 2026-07-10 — Option C deflated shipped. runtime/ (parser+noun_map+executor+loop+CLI); test_meta_systems_runtime.py 7/7 ×3 hermetic; corpus SHA 45dd1f9 intact; SCS C86 sealed.**

## FASE -1 — Reality Scan (findings, evidence-backed)

### 1. Do the meta-systems already have execution hooks?

**No. The corpus is pure doctrine — zero execution hooks, zero runnable code.**
But it is *not* unstructured prose. Every dataset carries a uniform contract layer:

| Structure | Where | Observed |
|---|---|---|
| Named operations `OP(args) → output` | PART V — Interfaces & Contracts | **38** across 7 datasets (5–6 each) |
| `*Guarantee:*` clause per op | PART V | **38** (1:1 with ops) |
| `*Never:*` clause per op | PART V | **27** — **OPTIONAL**, 11 ops have none |
| Registries + Pipelines (`a → b → c`) | PART VI | all 7 |
| Lifecycle state machine + hard gates (`GV-N`) | PART VII | all 7 |
| Frozen/semantic contract ("must never drift") | PART V tail | all 7 |

The corpus is **machine-parseable doctrine**. That single fact decides the architecture.

### 2. What exists in the PP that can be reused

- `modules/parallel_mesh/pm_03_bus.py` — **API verified**: `Finding`, `FindingsBus`,
  `stage_finding(repo, sid, topic, claim, ...)`, `publish_session_findings(repo, findings, *, sid)`,
  `load_context_digest(repo, ...)`. Real and importable.
- `modules/duplicate_to_advantage/d2a_engine.py` — **the precedent shape**: deterministic,
  fail-open, propose-never-build, `run(Proposal) -> D2AVerdict` + `render()` + `main(argv)`.
  The runtime should be the same shape.
- `modules/universal-meta-systems/corpus-reference.md` — 3-step corpus discovery, already written.
- `modules/one_shot/`, `modules/spec_gate/` — contract/gate idioms to mirror.

**NOT verified (do not design against them yet):** CO-12 telemetry and GK-08 writeback public
APIs were not read. Per HR-PREMISE-001 they must be verified before any call is written.

### 3. What is genuinely new

Exactly one thing: **a corpus contract parser** (PART V/VI/VII → structured ops, pipelines, gates).
Everything else is thin composition over it.

## RUNTIME ARCHITECTURE DECISION

**Recommendation: OPTION C (interpreter), with A folded into it and B rejected.**

- **B (7 runners) — REJECT.** "Each runner knows its meta-system's logic" *is* reimplementation.
  It duplicates 38 operations that already exist as doctrine, and it rots: any corpus edit
  silently desyncs 7 Python files. It violates the rule the Owner set
  (`expose-not-reimplement`) at the level of its core premise.
- **A (generic applier) — FOLDS INTO C.** A generic runtime that does *not* read the corpus has
  nothing to apply; that is precisely the "abstracción vacía" risk. Once A reads the corpus, A *is* C.
- **C (interpreter) — ADOPT.** Parse the corpus contract layer, apply the noun-map, emit an
  execution plan. The logic stays in the corpus; the runtime holds none of it. The stated
  complexity risk is bounded because the parse target is a uniform 3-section schema, not free prose.

### Anti-inflation pass (applying the D2A discipline to this proposal)

Proposed: 4 engines (R-CORE, R-NOUN-MAP, R-LOOP, R-AUDIT) over 5 sprints. Deflated:

| Proposed | Verdict | Why |
|---|---|---|
| Corpus contract parser | **NEW** | Genuinely new; the only real engine |
| R-NOUN-MAP registry | **NEW (small)** | Load/validate/fallback of one JSON file |
| R-CORE Executor | **THIN** | parser + noun-map → plan |
| R-LOOP | **THIN** | executor × 7 in corpus loop order + stop conditions |
| R-AUDIT | **NOT NEW — it is MS-6** | Auditing a repo for gaps *is* the Absence Engine applied to the repo. Run the interpreter with `MS-6` and the repo as target. Writing a separate audit engine re-implements MS-6 in Python — the exact banned move. |

Net: **2 new units + 3 thin drivers**, not 4 engines. R-AUDIT collapsing into MS-6 is the
recursion the corpus promises (`SELF_INTERROGATE`), and it is free.

### Three corrections to the proposed plan

1. **Noun-map auto-derivation from `CLAUDE.md` cannot be deterministic-semantic.** Mapping
   `"operator" → "<repo concept>"` from prose requires meaning. A regex that pretends to do this
   is theater. Correct design: derive *candidate* nouns (frequency-ranked domain terms), **PROPOSE**
   them for Owner confirmation, and fail-open to the generic noun-map with a visible warning.
   Propose-never-build, same as D2A.
2. **Test fixtures must use synthetic noun-maps, never real repo names.** The proposed done-gates
   name three live repos. Depending on them is non-hermetic (they can change) and imports domain
   vocabulary into a module whose whole contract is universality. `V-EXECUTOR-DOMAIN-SPECIFIC`
   must prove *two different synthetic noun-maps → two different plans* in a tmp dir.
3. **Parser must treat `Never:` as optional** (11 of 38 ops lack it) and must never write to the corpus.

### Honest ceiling of "domain-specific actions"

The interpreter emits a **noun-substituted, gate-checked execution plan**: per operation, the
substituted signature + guarantee + (optional) never-clause + the PART VII gates that must hold.
Deterministic, reproducible, zero LLM. Its specificity is exactly as rich as the noun-map — no
richer. It will not invent repo actions the noun-map does not license. Stating this now so
"acciones específicas, no vagas" is judged against what the design can actually deliver.

## Constraints carried forward

Corpus read-only (`45dd1f9`) · interpreter never reimplements · noun-map is the single point of
variability · STOP #1 before any implementation · never `git add -A`.
