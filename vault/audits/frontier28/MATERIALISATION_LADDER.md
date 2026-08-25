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

**Scale, measured, and stated at exactly the strength the evidence supports.**
`liveness_report.md` carries **242 LIVE verdicts, 228 of them (94%) import-edge verdicts**
whose reason begins "reached from". This does **not** show 228 modules never run. It shows
that 94% of the estate's positive liveness verdicts rest on a measurement that cannot
distinguish *executes* from *merely imported*. The `predictive` case proves the two can
diverge; how often they diverge is **UNKNOWN**, and unknown is the honest value — a number
would need the dispatch-surface analysis that does not exist. Owed to the instrument:
import reachability is a genuine *necessary* condition and `modules/liveness/` was built
for the "nothing reaches this" problem. The defect is in the reading, not the tool.

### The instrument this finding seems to demand already exists, one layer down

The obvious response to "reachability is not invocation" is to build something that
measures dispatched surfaces. Applying the mission's own rule to the mission's own idea
first: `modules/liveness/reachability.py:78-85` already contains the reasoning, sealed
2026-07-22.

> *"`hooks/*.js` by directory+extension alone is over-broad: a file merely sitting in
> hooks/ is not necessarily invoked by anything... Sealed 2026-07-22:
> hooks/cascade_check_bash.js was registered in NEITHER settings.json nor the dispatcher's
> chain map, yet every prior scan called it LIVE purely because it is a .js file living in
> hooks/."*

That is the same insight — presence in a location is not invocation — discovered
independently, hardened, and **bounded to the hook layer**. It was never carried down into
a module's *internal* dispatch table, where registration in a dict is likewise not
invocation. The file that hardened the reasoning is the same file whose report marks
`predictive` LIVE, because at the module layer it falls back to import edges.

**Verdict implication: EXTEND `modules/liveness/reachability.py`, not CREATE.** No new
owner, no new registry — carry an existing, sealed, correct idea one layer down to where
it was never applied. Recorded here so Phase 3 inherits the resolution rather than
re-deriving it, and so the CREATE that felt obvious is refused on evidence.

**Second-order note.** The estate also *knows* about its unwired surface and says so:
`vault/liveness/reachability_registry.json` declares 131 components, of which **62 are
self-declared `PLANNED`** (built, not wired) and 68 `LIBRARY`. That is honest, visible,
queued debt. The population this finding exposes is the opposite kind — components marked
**LIVE** that never dispatch. Visible debt has an owner and a queue; invisible debt reads
as health. That distinction, not the raw count, is what Phase 3 should act on.

## Placed: hypotheses 15-21

| # | Hypothesis | Rung | Owner | Engine said |
|---|---|---|---|---|
| 15 | DEC — decision erasure | **PARTIALLY_MATERIALIZED** | `modules/decision_review/decision_kernel.py` | DEFER, 45% |
| 16 | SREE — search extinction | **PARTIALLY_MATERIALIZED** | `modules/deep-research/deep_research.py` | "genuinely new", 27% |
| 17 | EED — entropy deflation | **DOCUMENTED** | NONE | "genuinely new", 28% |
| 18 | ACD — convergence detection | **ENFORCED** | `hooks/d2a_gate.js` + `d2a_engine.py` | "genuinely new", 25% |
| 19 | CLAO — capability adoption | **PRODUCTION_PROVEN** ± | `modules/liveness/reachability.py` | "genuinely new", 37% |
| 20 | CCV — compositional contracts | **PARTIALLY_MATERIALIZED** | `modules/contract_fabric/side_effect_ledger.py` | "genuinely new", 36% |
| 21 | ADW — assumption watchtower | **PARTIALLY_MATERIALIZED** | `modules/architecture_horizon/horizon.py` | "genuinely new", 16% |

### Evidence, briefly

- **DEC.** `decision_kernel.py:291-431` implements a real nine-stage sieve and writes an
  append-only `DecisionRecord`; `accountability.py:79-134` scores predictions against
  reality. But the **erasure** semantic is absent: precedent-collision flags a repeat
  decision and still routes it through all nine stages every time. Nothing caches a
  verdict as an auto-applied default. Recording a decision is not erasing it. The module
  also self-declares `PLANNED` in `reachability_registry.json:222-232`.
- **SREE.** `deep_research.py:1808-1821` matches new URLs against prior runs of the same
  prompt — and then **still fetches every one**, annotating overlap after the fact.
  Nothing is skipped, so no redundancy is actually extinguished.
- **EED.** `d2a_engine.py:23-25` ranks *new proposals* by compound value over complexity —
  per-proposal, forward-looking. Nothing measures complexity per unit capability across
  the estate, tracks owner count, or reports whether growth is reducing entropy.
  `code_reviewer.py`'s "complexity" is per-function cyclomatic, a different thing.
- **ACD.** `hooks/d2a_gate.js` fires on every prompt via `hook-dispatcher.js:267` and
  surfaces a duplicate verdict *before* building starts. **Corroborated by direct
  observation:** it fired on this mission's own opening prompt and named `KB-UCR-CIF` —
  which is how the contamination in §Phase 1 was found at all. Flagged as
  mission-observed rather than a durable log, so the rung stays `ENFORCED`.
- **CLAO — and the tension worth stating.** `reachability.py:46-56` computes
  REACHABLE / ORPHAN / UNKNOWN across hooks, commands, agents and settings, and
  `liveness_report.md` is a real dated artefact ("392 components, 242 LIVE, 150 non-LIVE")
  with concrete verdicts including `hook-dispatcher` itself flagged DRIFTED. That is a
  genuine `PRODUCTION_PROVEN` bar for the **orphan-detection** half.
  It coexists with the finding above: the same instrument **cannot** see a capability that
  is imported, registered, and never dispatched. Both hold. The rung reflects what it
  does; the blind spot belongs in MISSING, not in a downgrade. ± marks that split.
- **CCV.** `side_effect_ledger.py:78-95` reconciles one provider's declared vs observed
  effects; `capability_runtime/contract.py:9-17` validates a single capability's own
  contract. Neither checks **two capabilities composed** — A's output against B's expected
  input — which is the entire hypothesis. The closer of the two self-declares `PLANNED`
  and belongs to a corpus recorded as "SPEC, not a running system".
- **ADW.** `horizon.py:273-284` computes the transitive dependent closure of the real
  import graph — a working link from a unit to its consumers. `premise_verifier.py:109`
  checks premises exist before acting. Both are point-in-time and manually invoked;
  nothing watches for a previously-true assumption becoming false.

## Placed: hypotheses 22-28

| # | Hypothesis | Rung | Owner | Engine said |
|---|---|---|---|---|
| 22 | CHF — compatibility horizon | **PARTIALLY_MATERIALIZED** | `modules/dependency_sovereignty/sovereignty.py` | "genuinely new", 32% |
| 23 | KRR — knowledge revalidation | **ENFORCED** ▲ | `tools/audit_cache.py` + `~/.claude/hooks/gatekeeper-semantic.js` | "genuinely new", 38% |
| 24 | ERDR — external drift | **MATERIALIZED** | `tools/verify_global_mirrors.py`, `modules/mirror_discovery/` | "genuinely new", 45% |
| 25 | HEC — escalation compiler | **PARTIALLY_MATERIALIZED** | `modules/alert_escalation/policy.py` | **FOLD**, 80% owned by one_shot |
| 26 | AFP — autonomy failure predictor | **ENFORCED**, starved | `modules/pp_agents/signals/cascade.py` | "genuinely new", 15% |
| 27 | IRRL — independent replication | **PRODUCTION_PROVEN** | `modules/fable_distillation/fd_04_contrast.py` | "genuinely new", 41% |
| 28 | ICRA — compounding reality | **PRODUCTION_PROVEN** | `modules/sqi/weakening_detectors.py` | "genuinely new", 45% |

### Evidence, briefly

- **CHF.** `sovereignty.py:279-282` flags an unpinned dependency with no lockfile as
  `DO_NOT_USE` — real future-drift risk. But nothing reads upstream version, changelog or
  EOL data, so no actual horizon is forecast; `decision_kernel.py:46-48` only regex-matches
  the words "breaking change"/"deprecat" in decision text.
- **KRR ▲ — upgraded on evidence the subagent could not see.** The agent reported
  MATERIALIZED with no automatic caller, having correctly found no `gatekeeper-semantic.js`
  *in this repo*. It exists **globally**: `~/.claude/hooks/gatekeeper-semantic.js:108`
  recomputes a file's SHA-256 on PreToolUse Read and compares it against
  `_audit_cache/source_map.json`, surfacing staleness automatically. So the **consumer is
  enforced**; the **producer is not** — line 15 states the cache is written by
  `python tools/audit_cache.py --build`, by hand. Targeted revalidation fires on every
  Read against a map refreshed only when someone remembers.
  **Second finding, arguably larger:** that hook is **live-only, with no canonical copy in
  the PP repo**. The repo-scoped liveness scan therefore cannot see one of the estate's
  genuinely enforced surfaces — the same blind-spot family again, now inverted: not a dead
  thing reported live, but a live thing invisible to the instrument.
- **ERDR.** `verify_global_mirrors.py:275-281` SHA-256-compares the live `~/.claude/` tree
  against the git-committed blob and reports real `[DRIFT]` / `[MISSING]`;
  `mirror_discovery/discovery.py:130-160` supplies PAIRED / LIVE_ONLY / REPO_ONLY sets.
  Reachable only through `verify_spp.py`, itself invoked from human-typed commands.
- **HEC — and a refutation of the engine's one confident verdict.** The engine's sole FOLD
  claimed one_shot owns 80% of HEC. Read directly, `one_shot/escalation.py:9-14` is a
  three-line fail-count ladder (2 fails → Opus, 3 → STOP). It decides *when* to involve a
  human and contains no question-framing logic whatsoever. The engine's only non-"new"
  verdict in 28 is also wrong. What does exist —
  `alert_escalation/policy.py:48-50`, ENFORCED via
  `hooks/background-verifier.js` → `background_verifier_run.py:85` — collapses repeated
  findings into one standing row. That reduces notification **frequency**, not the size of
  the decision put to a human. The documented "high-leverage question compiler"
  (`fd_02`) has no module; only fd_00, fd_04 and fd_07 exist as code.
- **AFP.** Genuinely wired: `pp_agents/signals/cascade.py:98-124` builds a co-occurrence
  map and returns a proactive advisory *before* the successor error, dispatched
  automatically through `jit_skill_loader.py:1260` from three hooks. **But starved by the
  same store that starves FPO** — 9 events, 2 distinct timestamps, every category
  occurring exactly once, which the companion module states makes its guard "permanently
  unsatisfiable on this store". Wired, functional, and almost certainly returning `None`
  in practice.
- **IRRL.** `vault/fd04/FRONTIER_RESIDUAL_MAP.md:11-19` records three deposited claims
  re-posed cold to `claude -p` on a *different model*, in a fresh subprocess, hooks
  disabled, outside the repo — `REPRODUCED 6/6` — and the outcome changed real routing:
  "All three capability classes above are retired from frontier billing. They route to
  Sonnet." A genuinely independent evidence path, not a re-read of the same artefact.
- **ICRA.** `weakening_detectors.py:1` targets exactly the failure ICRA names — "the file
  is present, the case is collected, the case passes, and the protection is gone."
  `vault/audits/sqi_report_2026-08-06.md:8-23` is a real dated run: 149 files, 3,277
  assertions, "11 verifying NOTHING", offenders named. Manual invocation.

## Final distribution — 27 pre-existing hypotheses

`SCIF` is excluded: its ENFORCED rung was earned by code this mission committed today.

| Rung | Count | Hypotheses |
|---|---:|---|
| `DOCUMENTED` (genuinely absent) | **5** | NMIE · IRBE · FLSA · CSO · EED |
| `PARTIALLY_MATERIALIZED` | **9** | EIAA · BSC · BPCC · DEC · SREE · CCV · ADW · CHF · HEC |
| `MATERIALIZED` | **5** | FPO · CCCE · CIG · IBRS · ERDR |
| `ENFORCED` | **4** | TND · ACD · AFP · KRR |
| `PRODUCTION_PROVEN` | **4** | OECL · CLAO · IRRL · ICRA |

**Five of twenty-seven are genuinely absent.** The engine called twenty-one of
twenty-eight "genuinely new," and its single non-new verdict is the one refuted above.

**Fourteen of twenty-seven — over half — are real code that no automatic surface invokes.**
That is the estate's actual deficit, and it is not a shortage of capability. Adding a
twenty-ninth system would not touch it.

## A prediction of mine, falsified

The approved plan named **IRBE, CSO and OECL** as the strongest CREATE candidates.
IRBE and CSO hold. **OECL is the single highest-rung capability found so far** — the only
`PRODUCTION_PROVEN` row in 14. The lexical sweep scored it 113 hits and I read that as
near-absence; it was a vocabulary miss, the exact failure mode this audit was built to
catch, reproduced by me after naming it. Recorded rather than quietly corrected, per §58.

## Open

Hypotheses 15-28 in flight. No verdict is issued until all 28 are placed.
