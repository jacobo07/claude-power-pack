---
covers: [experiment-admission, premise-ledger, instrument-qualification, matched-control, discriminating-observable, precondition-breaker, instrument-breaker, failure-taxonomy, perception-authority, p25-p38-replay, tb-p39-canary]
status: APPROVED 2026-10-17 (Owner "y" on the inline master plan, pane 88ca6ab1; defaults accepted: 30M hard tranche with re-forecast at 20M, canary = one gate-admitted P39, push branch at done-gate only)
tier: SDD T3 (new cross-repo standard layered on existing owners)
---

# Experiment Admission: causal contract before mutation

## Problem
Expensive experiments (GEX44 Dolphin slots, multi-million-token workers) ran before the owner, preconditions,
instrument, control and observable were established. Canonical incident: Two Builders P25-P38
(`vault/plans/planning-economics-m2-incident-20261016.md`; TB `docs/PREREG_P*`, `docs/RESULT_P*`).
Measured worker spend for P25-P31b is 26.9M processed. That excludes pane rent and the P32-P38 coordinator cost, which W1 measures.

## Existing owners (reality scan 2026-10-17; extend, never duplicate)
- `tools/planning_gate.py` `decide()` via `gsd_mission arm --work-unit`: planning-mode admission (capsules, invalidators, closed obligations).
- TB `tools/prereg_lint.py` `lint()`: 5 structural checks. NOT enforced: `tb_local.cmd_run` never calls it; p32-p38_run.sh skipped it.
  `probe_keys` reads only the PROBES dict literal (misses post-dict `PROBES[...] =`).
- `modules/gsd_x/goal/evidence.py`: hypothesis ledger, refuses to reopen a rejected hypothesis without a new ref. `mission/obligation.py` has STALE.
- `modules/gsd_x/goal/epoch.py` `info_key` / `HYPOTHESES` / `RetryWithoutNewInformation`: live in `reconcile.py`; keyed on goal epochs.
- `modules/done_gate/strength_ladder.py`: three-valued evidence (absent = UNDETERMINED), `EVIDENCE_CLASSES`.
- `modules/capability_runtime/applicability.py`: BLOCKED_BY_UNRESOLVED_OWNER / BLOCKED_BY_MISSING_EVIDENCE.
- `modules/tower/ratchet.py` (CBR) `promote`.
- UKDL `T-OBSERVABLE-NOT-DISCRIMINATING-001` (SHADOW), `T-NON-DISCRIMINATING-CONTROL-001`, `T-EMPTY-READER-INDISTINGUISHABLE-FROM-ABSENT-VALUE-001`.
- No failure taxonomy beyond CEPS's 9 code-error categories. "EDD" here means the compiled-execution canary; do not reuse the acronym.

## Contracts
1. **Premise ledger** (extend `evidence.py`): states PROVEN / UNPROVEN / FALSIFIED / STALE / NA. Each premise carries an evidence ref,
   an invalidation condition and `depends_on`. Stale propagation walks only the affected closure. A FALSIFIED premise is
   not citable without new evidence.
2. **`experiment_admission`** (one new pure, domain-free module; no current owner can host scientific validity without
   mixing it into planning mode). Verdicts are ADMIT / DOWNGRADE / REFUSE / NOT_REQUIRED, applied in proportion to cost.
   Checks:
   - owner + premise evidence for the mutated resource;
   - instrument qualification receipt: the same configuration has seen a positive case. Without it, an empty output is never negative;
   - control: matched dimensions, declared differences and why they do not matter;
   - observable: evidence ref that the baseline cannot produce it;
   - decision change: at least 2 outcomes mapping to different next actions;
   - novelty: causal delta against prior failed runs of the same shape (extends `epoch.info_key`).
   Its vocabularies:
   - **Fault taxonomy:** PREMISE, OWNERSHIP, CONTRACT, INSTRUMENT, CONTROL, OBSERVABLE, PERCEPTION, ROUTING.
   - **Verdict authority:** a model visual verdict is a CANDIDATE. Evidence lineage is tracked; two judgments from the same frame are not independent.
3. **Breakers.**
   - Repeated precondition discovery: the threshold comes from cumulative slot and token cost. It escalates `planning_gate` to
     BOUNDED_PLAN (contract reconstruction from known successful instances) until the contract closes.
   - Repeated instrument failure: no identical retry without a causal delta.
4. **Enforcement (compile, don't instruct).**
   - `prereg_lint` calls admission and writes a CLEAN receipt bound to the disc sha256.
   - `tb_local.cmd_run` refuses without that receipt.
   - Decisive env (`TB_DOLPHIN_LOG`) comes from the capsule run template.
   - `probe_keys` reads post-dict assignments.
   - The capsule sha is refreshed.
5. **Proportionality**: a deterministic local edit with a proven owner returns NOT_REQUIRED.

## Acceptance (master done-gate)
- **Replay** over the P25-P38 corpus:
  - P25 is refused (baseline-satisfiable observable);
  - the P26/P27 PASS is downgraded (perception candidate, shared lineage);
  - P31b is refused (identical instrument retry, env not compiled);
  - P31c ranks as high premise leverage;
  - the P32-P38 breaker fires at a stated point.
  Savings are graded MEASURED / LOWER-BOUND / PLAUSIBLE / UNKNOWN.
- **Canary**: successful-spawn archaeology (MosEisley_B level3, MosEisley_D level2, EndorBattle_C) produces a contract table, which derives P39.
  P39 runs through lint, then admission, then `tb_local` on one slot. A bad variant is refused before any slot is spent.
- **Cross-domain**: two non-game cases from repo history, plus a trivial-edit negative control (NOT_REQUIRED).
- **Mutation**: 8 drills go red (owner requirement removed, UNPROVEN promoted, control matching off, baseline PASS allowed,
  instrument check off, third identical retry allowed, breaker suppressed, candidate promoted to PASS).
- **Fresh worker**: reads premise state from the store, not the transcript.
- **Knowledge**:
  - UKDL HR (instrument liveness), PR (control by causal equivalence), PR (repeated preconditions = incomplete contract),
    Trap (identical instrument retry); the SHADOW observable trap is promoted;
  - Knowledge Vault incident; Construction Return;
  - CBR scoped to game-RE experiments until the cross-domain cases pass.
- **Red team**: `oneshot-architect-auditor`, using the 17 attack questions of the mission prompt; any material finding reopens its gate.

## Budget
Tranche 30M HARD (processed, deduped; re-forecast at 20M, economic recompile at 1.3x central).

| Work | Low | Central | High |
|---|---|---|---|
| W0 scan (done) | 0.6 | 0.8 | 1.0 |
| W1 corpus | 1.0 | 1.5 | 2.5 |
| W2a ledger | 1.0 | 1.8 | 3.0 |
| W2b admission | 2.0 | 3.5 | 6.0 |
| W2c breakers | 1.0 | 1.5 | 2.5 |
| W2d enforcement | 0.8 | 1.2 | 2.0 |
| W3 replay | 1.0 | 1.5 | 2.5 |
| W4 archaeology + canary | 2.0 | 3.0 | 5.0 |
| W5 cross-domain | 1.5 | 2.5 | 4.0 |
| W6 mutation | 0.8 | 1.2 | 2.0 |
| W7 knowledge | 0.8 | 1.2 | 2.0 |
| W8 red team | 1.5 | 2.0 | 3.5 |
| Overhead | 1.0 | 1.5 | 2.5 |
| Contingency | 1.0 | 4.0 | 6.0 |
| **Total** | **16** | **27** | **45** |

## Rollback / kill switch
- `CPP_EXPERIMENT_ADMISSION=off`: admission returns NOT_REQUIRED with a ledgered reason. Enforcement in `tb_local` becomes advisory.
- Every change is on branch `feature/experiment-admission`; revert = drop the branch.
