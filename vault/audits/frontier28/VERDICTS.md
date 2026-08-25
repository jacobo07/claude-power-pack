---
title: Frontier-28 — D2A verdicts for the 28 hypotheses
date: 2026-08-25
status: PHASE 3 COMPLETE — all 28 classified
cutoff: bc81ca76cd8ef9ea78982c99016a03e979a91570
mandate: brief §10 (verdict set) · §13 (cross-hypothesis dedupe) · §21 (owner minimisation) · §58 (no metric gaming)
---

# Verdicts

## Correction first: two claims of mine were wrong

**1. "Both predictors are starved."** Committed in `3a3e78c`. It is false.
The claim traced to a module comment measured **2026-08-06** reporting 9 events. Measured
today, `vault/ceps/events.jsonl` holds **69 events across 9 distinct categories and 10
days**, four categories repeating, most recent written *today*. Both subagents read the
self-report; neither read the store. `predictive.substrate_quality()` now returns
**`SUBSTRATE_OK`** with three learned pairs: `regression→tooling`, `tooling→env`,
`tooling→regression`.

**A module's statement about its own data is a measurement with a timestamp, not a fact.**
It ages exactly like any other cached value, and it ages invisibly because it reads as
documentation.

**2. EED is not `DOCUMENTED`.** `modules/cognitive_load/load.py` measures the cost of
assembling enough context to change a unit — public-symbol surface, dependency width,
declared entry points. That is a real complexity metric with an executable surface.
Corrected to `PARTIALLY_MATERIALIZED`; the missing part is any *trend* over time or
complexity-per-unit-**capability**, which is what the hypothesis actually asks for.

## The sharpest finding: two broken halves of one capability

FPO and AFP are the same capability — predict a failure from precursor signatures in
`vault/ceps/events.jsonl` — implemented twice, and neither delivers, for **different and
individually invisible reasons**.

| | FPO (`cascade_prevention/predictive.py`) | AFP (`pp_agents/signals/cascade.py`) |
|---|---|---|
| Dispatched automatically? | **No** — registered at `SURFACE_DETECTORS["session"]`, no caller supplies that key | **Yes** — every prompt, via `jit_skill_loader` from three hooks |
| Substrate | `SUBSTRATE_OK`, 3 learned pairs | same store |
| Fires on real input? | would — never asked | **No** |

AFP's failure is at the **interface**. `_build_cascade_map()` keys on
`f"{category}:{subsystem}"` — learned keys are `regression:bash:cat`, `tooling:bash:cd`,
`regression:bash:cd`. `evaluate()` then tests `src_key.lower() in haystack`, where the
dispatcher passes **raw error message text** (`proactive_dispatcher.py:127`). Proven both
ways: the store's own most recent error text
(`"[Tool result missing due to internal error]"`) returns `None`; the synthetic composite
key fires. A composite assembled from two structured CEPS fields will never appear
verbatim inside an error string.

So the estate holds a predictor with a healthy substrate that nothing calls, and a
predictor that is called constantly and cannot match. Three distinct silent-failure modes
across two modules — **never dispatched**, **type-mismatched at the boundary**, and the
one I wrongly assumed, **starved** — and only the third would have been visible to any
existing instrument.

**Verdict: MERGE.** Not a new system, not even new logic. FPO's substrate analysis is
correct and its pairs are real; AFP's dispatch path is correct and already automatic.
One working capability exists across two files; it has never been assembled.

## Production evidence — the merge fired on a real prompt

Observed 2026-08-25, roughly an hour after the fix landed. The `UserPromptSubmit`
advisory on the Owner's next turn carried:

> `[Woz] [pp-cascade-guard] 'regression:bash:cd' has historically preceded: tooling:bash:cd.`

The whole chain, verified against live state rather than inferred: a real CEPS event
`regression:bash:cd` was recorded at `14:50:20Z` (store grew 69 → 72) → the 30-minute
window admitted it → `_recent_error_context()` returned the structured key →
`cascade.evaluate()` matched on `category:subsystem` → the dispatcher put it in
`additionalContext`. At commit time the honest claim was "capability installed,
compounding effect not yet proven" (§78). It is now proven: **AFP/FPO moves from
`ENFORCED` to `PRODUCTION_PROVEN`**, on an observed fire, not an assertion.

**And the counterweight, which matters more than the win.** The event's recorded
`root_cause` is **`"0 failed"`** — a *test-success* line, classified as a `regression`.
The prediction mechanism is correct and the key match is sound, because matching uses
`category:subsystem` and never the text. But the producer feeding it is recording benign
output as errors, so some fraction of these advisories will be built on non-events.

Turning the signal on has therefore made a **second, older defect visible for the first
time**: while every consumer returned `None`, nothing could reveal that the store's
contents were unreliable. Data quality was untestable precisely because nothing read the
data. This is a new finding of this mission, not a regression introduced by it, and it
belongs to whoever owns `hooks/bug-hunter-ceps-bridge.js` — recorded here, not silently
carried, and it does not alter the rung, which rests on the mechanism firing correctly on
a genuinely recorded event.

## The 28

| # | Hypothesis | Rung | Verdict | Owner / action |
|---|---|---|---|---|
| 1 | SCIF | ENFORCED ⚠ | **DONE (this mission)** | `duplicate_to_advantage/provenance.py`, shipped `ca8e885` |
| 2 | EIAA | PARTIAL | **EXTEND** | `graphify/global_store.py` — read `origins` back to discount echoes |
| 3 | OECL | PROVEN | **OWNED** | `daif/two_arm_trial.py`; scope narrow (tokens only), stated |
| 4 | BSC | PARTIAL | **CONNECT** | 4 modules already declare their blind spots — generate a view, do not add a registry |
| 5 | NMIE | DOCUMENTED | **EXTEND** | CEPS producer exists and is dispatcher-registered; add near-miss capture, do not build an archive |
| 6 | FPO | MATERIALIZED | **MERGE** → with 26 | dispatch it |
| 7 | IRBE | DOCUMENTED | **CREATE** (gated) | genuinely absent; `HR-NOVELTY-001` proof required |
| 8 | CCCE | MATERIALIZED | **OWNED** | `mutation_ratchet.py` + `run_sqi.py` |
| 9 | CIG | MATERIALIZED | **OWNED** | `decision_review/decision_kernel.py` |
| 10 | IBRS | MATERIALIZED | **OWNED** | `decision_kernel` + `architecture_horizon` |
| 11 | BPCC | PARTIAL | **EXTEND** | `rollback/` owns revocation; canary half absent |
| 12 | FLSA | DOCUMENTED | **DEFER** | no observed instance of the failure it prevents |
| 13 | CSO | DOCUMENTED | **CREATE** (gated) | confirmed absent; `cognitive_os` does eviction, not sufficiency |
| 14 | TND | ENFORCED | **OWNED** | `spec_gate.check_novelty_gate` via `jit_skill_loader` |
| 15 | DEC | PARTIAL | **EXTEND** | `decision_review` records decisions; erasure semantic missing |
| 16 | SREE | PARTIAL | **EXTEND** | `deep-research` annotates overlap; nothing is skipped |
| 17 | EED | PARTIAL ▲ | **EXTEND** | `cognitive_load/load.py` — add trend, not a new meter |
| 18 | ACD | ENFORCED | **OWNED** | `hooks/d2a_gate.js` |
| 19 | CLAO | PROVEN ± | **EXTEND** | `liveness/reachability.py` — dispatch-awareness (see below) |
| 20 | CCV | PARTIAL | **DEFER** | closest owner self-declares SPEC, not a running system |
| 21 | ADW | PARTIAL | **EXTEND** | `architecture_horizon` links consumers; nothing watches for drift |
| 22 | CHF | PARTIAL | **DEFER** | needs upstream version/EOL feeds that do not exist here |
| 23 | KRR | ENFORCED | **CONNECT** | consumer auto-fires; **producer is manual** — automate the rebuild |
| 24 | ERDR | MATERIALIZED | **CONNECT** | `verify_global_mirrors.py` works; reachable only by hand |
| 25 | HEC | PARTIAL | **EXTEND** | `alert_escalation` cuts frequency, not decision size |
| 26 | AFP | ENFORCED | **MERGE** → with 6 | interface mismatch |
| 27 | IRRL | PROVEN | **OWNED** | `fd_04_contrast.py` + `FRONTIER_RESIDUAL_MAP.md` |
| 28 | ICRA | PROVEN | **OWNED** | `sqi/weakening_detectors.py` |

### Distribution

| Verdict | Count |
|---|---:|
| **OWNED / REFERENCE** | 8 |
| **EXTEND** | 9 |
| **CONNECT** | 3 |
| **MERGE** | 1 (covering 2 hypotheses) |
| **DEFER** | 3 |
| **CREATE** | **2** — IRBE, CSO, both gated on `HR-NOVELTY-001` |
| DONE this mission | 1 |

**CREATE: 2 of 27 = 7.4%.** Below this estate's historical band (IAS 9%, RE Baseline 25%,
DAIF 36%). Recorded as measured, not steered — §58 forbids aiming at a distribution, and
that prohibition binds in both directions.

## Cross-hypothesis dedupe (§13)

The 28 do not survive as 28.

- **FPO + AFP → one capability**, two broken halves (above).
- **CLAO's extension *is* the instrument the BSC/FLSA findings demand.** Dispatch-awareness
  in `reachability.py` is what would have caught FPO automatically. One extension, three
  hypotheses served.
- **IBRS ⊂ CIG.** Both live in `decision_kernel.py`; blast radius is the input to
  amplification governance, not a separate owner.
- **EIAA and BSC are the same shape** — a claim capped by what its evidence can support.
  EIAA caps on ancestry, BSC on visibility.
- **KRR and ERDR are one pattern**: an automatic consumer with a manual producer (KRR), and
  a correct comparator nothing calls (ERDR). Same `CONNECT`.

Fourteen of twenty-seven are real code that no automatic surface invokes. **That is one
problem wearing fourteen names**, and it is the mission's actual subject.

## What will not be built, and why

- **No new autonomy OS.** HIC-OAR owns avoidable human intervention.
- **No dispatch-coverage system.** `reachability.py:78-85` already holds that reasoning,
  sealed 2026-07-22 for the hook layer — carry it down, do not re-found it.
- **No blindspot registry.** Four modules already declare theirs in code; a generated view
  beats a parallel registry (§61).
- **No near-miss archive.** The event store, its producer and two consumers already exist.
- **FLSA, CCV, CHF deferred** — each would be built against an unobserved failure, an
  owner that self-declares non-running, or data feeds that do not exist.

## Phase 5 order and status

1. **MERGE FPO + AFP** — **DONE** (`44a8f7f`), and **PRODUCTION_PROVEN** (`39c2e00`):
   observed firing on a real prompt within the hour. A regression I introduced here — the
   no-input fast path — was caught by the `benchmarks-ok` gate and fixed in `064d29b`.
2. **EXTEND liveness with dispatch-awareness** — **DONE** (`904dd21`, wired `9a3dd22`).
   `modules/liveness/dispatch.py`; 5 of 7 `SURFACE_DETECTORS` keys never supplied. Now
   reported per-session through the Stop delta, not only inside a test row.
3. **CONNECT KRR's producer** — **DONE** (`9a3dd22`). `audit_cache.py --refresh` plus
   `session_delta.refresh_audit_cache`; 3016 ms → 92 ms after persisting the stem map.
4. **Remaining, in order:** EIAA (read `origins` back to discount echoes) · DEC (cache a
   verdict as a default so a repeat decision stops being a decision) · SREE (skip, do not
   annotate) · HEC (compress the ask, not the frequency) · ADW · EED · BPCC · CLAO ·
   CCV — then the two gated CREATEs (**IRBE**, **CSO**) once each passes the
   `HR-NOVELTY-001` 13-question proof against a discovered sweep.

### Umbrella state, recorded rather than waved off

The full `verify_spp` run exits 1 on 7 rows. Each was checked against my changed-file set,
which contains **zero** files under `hooks/` or any global path:

| Row | Cause | Mine? |
|---|---|---|
| `benchmarks-ok` | `proactive_dispatch_ms` 103 > 30 — cold lazy-import of ~14 signal modules (94.5 ms cold / 69.2 ms warm; `cascade.evaluate` = 0.003 ms). Was 43 ms at S0, already 91 ms in the 2026-06-03 audit. | **the 123→103 part was** — fixed in `064d29b`; the residue is not |
| `hooks-registration` | marker-set mismatch including `output_contract_stop`, which a **concurrent pane** has modified and not committed | no |
| `mirror-parity` | canonical↔live drift in 5 files (`hook-dispatcher.js`, `lazarus-stub-recover.js`, …) | no |
| `dataset-build` | **passes standalone**; fails only under parallel execution | no |
| `drift-report` | `PAIRS is empty/missing` (config) | no |
| `paths+secrets` | pre-existing 129-entry allowlist across 50 files | no |
| `restart-and-lag` | environment/timing gate | no |

`mirror-parity` is the ERDR finding made concrete: the comparator works, nothing invokes it
automatically, so drift accumulates until someone runs it by hand. None of these are
dismissed — they are attributed, and the ones that are mine are fixed.
