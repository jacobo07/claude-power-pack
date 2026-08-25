---
title: Frontier-28 — materialisation ladder for the 28 hypotheses
date: 2026-08-25
status: IN PROGRESS — 7 of 28 placed; hypotheses 1-7 and 15-28 in flight
cutoff: bc81ca76cd8ef9ea78982c99016a03e979a91570
mandate: brief §12 (documented vs materialised) · §8 (evidence hierarchy) · §52 (claim-evidence type system)
---

# Materialisation ladder

## Why a ladder and not a verdict

Both instruments used in reconnaissance asked a binary question — is this **new** or is it
**owned** — and the evidence refuses it. The dominant state in this estate is neither:
a capability described at length in a dataset, with no executable surface, or with one
that nothing invokes.

Rungs, lowest to highest: `DOCUMENTED` · `DECLARED` · `PARTIALLY_MATERIALIZED` ·
`MATERIALIZED` · `ENFORCED` · `PRODUCTION_PROVEN`.

**The rule that makes the measurement trustworthy:** any rung above `DOCUMENTED` may only
be evidenced from an executable surface (`modules/`, `tools/`, `hooks/`, `commands/`,
`tests/`, or a JSON registry that code actually loads). Prose establishes `DOCUMENTED` and
nothing more, however detailed. This also immunises the pass against both live
contamination sources — the concurrent session's 175 untracked files and the prior
mission's `ucr_cif` — because neither is executable.

## Placed so far (7 of 28)

| # | Hypothesis | Rung | Owner | Engine said |
|---|---|---|---|---|
| 8 | CCCE — causal contribution | **MATERIALIZED** | `tools/mutation_ratchet.py`, `modules/sqi/weakening_detectors.py`, `tools/run_sqi.py` | "genuinely new", 12% |
| 9 | CIG — amplification governance | **MATERIALIZED** | `modules/decision_review/decision_kernel.py` | "genuinely new", 37% |
| 10 | IBRS — blast radius | **MATERIALIZED** | `decision_kernel.compute_blast_radius`, `modules/architecture_horizon/horizon.py` | "genuinely new", 38% |
| 11 | BPCC — propagation + canary | **PARTIALLY_MATERIALIZED** | `modules/rollback/rollback.py` | "genuinely new", 26% |
| 12 | FLSA — loop interference | **DOCUMENTED** | NONE | "genuinely new", 19% |
| 13 | CSO — context sufficiency | **DOCUMENTED** | NONE | "genuinely new", 41% |
| 14 | TND — true novelty | **ENFORCED** | `modules/spec_gate/gate.py::check_novelty_gate` via `tools/jit_skill_loader.py` | "genuinely new", 12% |

### Evidence, briefly

- **CCCE.** `mutation_ratchet.py:79-112` breaks a real return value and checks which
  referencing tests still pass — a genuine injected-defect causal test, not
  post-hoc correlation. `run_sqi.py:488-503` composes it behind `--mutation-probe`.
  Manual invocation only; no hook or CI calls either, which is exactly why it stops
  short of ENFORCED.
- **CIG.** `decision_kernel.py:159-171` escalates review tier as blast magnitude rises;
  `:174-183` scales evidence burden with reversibility — "more evidence the more it
  propagates," implemented. Nothing invokes `review_decision()` automatically.
- **IBRS.** `decision_kernel.py:91-96` scores nine impact surfaces before routing;
  `horizon.py:20-25` computes the transitive dependent closure of the real import graph
  before a change lands. Both reachable only by manual command.
- **BPCC.** The **revocation** half is real and end-to-end: `rollback.py` selects a
  source, dispatches a runner, runs a post-restore healthcheck and only then writes a
  receipt (`:525-545`). The **canary / staged-propagation** half has zero executable
  surface anywhere, confirmed by an explicit negative admission in
  `modules/craif/__init__.py:6-8`: *"No snapshot, sandbox, canary, rollback, or real
  mutation happens in this phase."* A true partial, not a near-miss.
- **FLSA.** `fd_07_flywheel.py:39-42` caps one loop's own turn size so it cannot spin.
  That is self-throttling of a single flywheel, not detection of interference *between*
  loops. No comparator over multiple named loops exists.
- **CSO.** `modules/recall_roi/` measures whether an injected knowledge item was ever
  re-used — usage and eviction telemetry. It never correlates context volume against
  outcome correctness, which is the actual function. Different capability.
- **TND.** `jit_skill_loader.py:1488-1495` calls `check_novelty_gate(prompt)` on every
  qualifying prompt and injects `HR-NOVELTY-001` into `additionalContext`; the loader is
  wired into the live hook chain. Verified independently by direct read, not taken on
  report.

## Two findings that reshape the mission

**1. The engine's error is not noise — it is one-directional and total.**
Seven of seven rows above were called "genuinely new." Three are MATERIALIZED, one is
PARTIALLY, and one is **ENFORCED** — TND fires on every prompt, *including the prompt that
launched this audit*, and the engine scored it new at 12% coverage. An instrument that
declares novelty on low lexical coverage cannot distinguish "absent" from "phrased
differently," and every such confusion resolves toward building something that already
exists.

**2. The estate's characteristic failure is not building — it is wiring.**
`jit_skill_loader.py:1440` records how TND reached ENFORCED at all:

> *"HR-NOVELTY-001 / modules.spec_gate.gate.check_novelty_gate existed as a pure function
> with zero live callers — the fix built to stop the 6-audit mega-corpus-proposal pattern
> only fired if the agent remembered to check it manually."*

The gate designed to stop repeated mega-corpus proposals was itself inert until someone
noticed it had no callers. That is the same pathology the `liveness` module was built to
measure, and it is what the rung distribution above measures directly: **CCCE, CIG and
IBRS are all real, correct, and reachable only if a human remembers them.** The gap
between MATERIALIZED and ENFORCED is where this estate's capability actually leaks.

The implication for Phase 3 is concrete: for this class of hypothesis, the highest-leverage
verdict is unlikely to be CREATE. It is **MATERIALIZE** (write the missing executable half)
and **ENFORCE** (wire what already works to a surface that fires without being remembered).

## Placed: hypotheses 1-7

| # | Hypothesis | Rung | Owner | Engine said |
|---|---|---|---|---|
| 1 | SCIF — self-contamination immunity | **ENFORCED** ⚠ mission-generated | `modules/duplicate_to_advantage/provenance.py` | DEFER, 45% |
| 2 | EIAA — evidence independence | **PARTIALLY_MATERIALIZED** | `modules/graphify/global_store.py` | DEFER, 45% |
| 3 | OECL — observer effect | **PRODUCTION_PROVEN** | `modules/daif/two_arm_trial.py` | DEFER, 45% |
| 4 | BSC — blindspot surface | **PARTIALLY_MATERIALIZED** | 4 independent modules, no unified map | "genuinely new", 28% |
| 5 | NMIE — near-miss intelligence | **DOCUMENTED** | NONE | DEFER, 45% |
| 6 | FPO — failure precursor | **MATERIALIZED**, zero callers | `modules/cascade_prevention/predictive.py` | "genuinely new", 31% |
| 7 | IRBE — institutional bisection | **DOCUMENTED** | NONE | DEFER, 45% |

⚠ **SCIF's rung is disqualified as prior capability.** `provenance.py` was committed by
*this mission* today (`ca8e885`). It is reported for completeness and excluded from every
pre-existence claim — the audit may not cite its own output as evidence that something
already existed, which is the very rule that module implements.

### Evidence, briefly

- **EIAA.** `global_store.py:122-146` unions a claim's `origins` on merge and preserves
  differing summaries as `alt_summaries` rather than clobbering — real lineage capture.
  But nothing anywhere reads `origins` back to notice that N mentions share one ancestor
  and must therefore *not* raise confidence. Lineage is recorded; it is never used to
  discount an echo. That missing half is the whole point of the hypothesis.
- **OECL.** `two_arm_trial.py:416-426` measures the CLI's own token overhead under
  isolated vs unisolated instrumentation, and three recorded trials under `vault/trials/`
  carry real observed values — `session_overhead_tokens: 4895` against
  `arm_b_overhead_tokens: 73923`. The estate measured how much its own instrument
  perturbs the measurement, on real runs, and changed the isolation-flag design as a
  result (`T-DAIF-ISOLATION-LEAK-001`). Scope is narrow (token overhead, not timing or
  memory) and invocation is manual — `reachability_registry.json:194-197` classes it
  `PLANNED`.
  **Independence caveat, applied to my own evidence:** the three trial files carry
  *identical* figures. That is one measurement recorded three times, not three
  confirmations. The rung stands on the recorded run; the apparent multiplicity does not.
- **BSC.** The idiom is real and recurs independently in at least four modules:
  `horizon.py:46-53` (`UNMODELLED_STRESSORS`, naming what the audit cannot see),
  `sovereignty.py:65-73` (`UNREACHABLE_RUNGS`), `effect_harness.py:161-175` (rules for
  which "no probe exists here or can", reported separately from measured absence), and
  `weakening_detectors.py:499-502`, which caps a conclusion at "UNKNOWN, not zero
  survivors" when the baseline cannot discriminate. Each caps only its *own* local
  conclusion; no cross-cutting map exists that a new audit inherits. Note this is also an
  **architectural convergence** datum: four modules independently evolved the same shape.
- **NMIE.** Genuinely absent. `classify_sources.py:71-85` has a `near_misses()` function,
  but it measures how close a URL classifier came to firing a rule — not an operational
  near-miss. `pre_mortem.py:16-57` is a static regex risk list with no event capture and
  no learning loop. Nothing records "this almost failed" as a first-class record.
- **FPO.** Real and complete: `predictive.py` loads `vault/ceps/events.jsonl`, computes
  category co-occurrence in a time window, and returns graded verdicts including
  `SUBSTRATE_DEGENERATE` and `UNMEASURABLE`. **Zero callers** — a repo-wide grep finds
  only its own `__main__`; `hooks/cascade_check_bash.js:25` wires
  `cascade_prevention.engine.detect`, the present-state detector, never `predictive`.
  It is also **starved**: the module reports the live event store holds 9 events, all in
  distinct categories, so it could not emit a real `PREDICTED` verdict even if called.

  **Correction — the agent's "zero callers" is wrong, and the truth is worse.**
  `engine.py:131` *does* import `predict`, inside `_detect_session`, which *is* registered
  in `SURFACE_DETECTORS["session"]` and dispatched by `detect()`. The code is reachable.
  It simply never runs: the only automatic caller in the repo is
  `hooks/cascade_check_bash.js:28`, which calls `detect('bash', ...)`. A repo-wide sweep
  for `detect('<surface>')` finds `session` and `context` **only inside test files**,
  `deploy` in a manual health-report tool, and `edit` / `commit` / `task` with no callers
  at all. **Six of the seven registered detectors never fire in production.**
  Not an orphan — a registered handler for a surface nobody emits.
- **IRBE.** Genuinely absent, and the near-miss is instructive: its only textual hit was
  `vault/knowledge_base/ucr_cif/SOURCE_INVENTORY_FULL.json:3047`, the prior mission's own
  inventory. The agent correctly refused to count it. `rule_compiler/counterfactual.py`
  replays one rule against the incident that produced it — forward validation of a single
  rule, not backward bisection across a history of institutional changes.

## The finding that outranks the rest: reachability is not invocation

`vault/audits/liveness_report.md:209` classes
`module:cascade_prevention/predictive` as **LIVE**, with the reason
*"reached from modules/cascade_prevention/engine"*. That is true, and it is not the
question anyone cares about. The module is import-reachable from a live module and still
executes **never**, because the live module dispatches on a surface key
(`'session'`) that no production caller ever supplies.

The estate's own liveness instrument — built precisely because 156 modules once existed
that nothing reached — answers *"is this wired into the import graph?"*. The question that
determines whether a capability exists in practice is *"does anything actually call it with
arguments that reach this branch?"*. Between those two questions sit at least six working
detectors that have never run.

This is the mission's central mechanism restated one level up. The ladder was built to
separate `DOCUMENTED` from `MATERIALIZED`, on the theory that the estate's leak is prose
without code. The leak runs one rung higher too: **`MATERIALIZED` code, correctly
registered, that no live surface dispatches to.** An import edge is cheap to create and
looks identical to a call path in every static instrument.

Consequences to carry into Phase 3:

1. `ENFORCED` may not be granted on the existence of a caller. It requires a caller on an
   automatic surface **that supplies arguments reaching the capability**. Registration in
   a dispatch table is not invocation.
2. **CLAO's owner is weaker than it appears.** `modules/liveness/` answers the wiring
   question, not the consumption question, so it is a partial implementation of "is this
   capability actually consumed" — the exact hypothesis it looked like it owned.
3. This is a **discovered instance of the FLSA/BSC family**: a measurement that reports
   health for a component that cannot fire. It was found by hand, which means nothing
   currently detects it.

Recorded as `T-REACHABLE-BUT-NEVER-DISPATCHED-001` in the mission trap file.

## A prediction of mine, falsified

The approved plan named **IRBE, CSO and OECL** as the strongest CREATE candidates.
IRBE and CSO hold. **OECL is the single highest-rung capability found so far** — the only
`PRODUCTION_PROVEN` row in 14. The lexical sweep scored it 113 hits and I read that as
near-absence; it was a vocabulary miss, the exact failure mode this audit was built to
catch, reproduced by me after naming it. Recorded rather than quietly corrected, per §58.

## Open

Hypotheses 15-28 in flight. No verdict is issued until all 28 are placed.
