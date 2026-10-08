---
id: PLAN-CAA-WAKE-AMENDMENT-R
covers: [caa-wake-w1-recovery, caa-wake-reservation-reconcile, caa-wake-salvage, caa-wake-tranche-2, caa-dependency-predicate, caa-continuation]
status: AWAITING OWNER APPROVAL (one reply)
source: unbound control pane 3bd3b9be, main checkout cwd, absolute paths and git -C only (never cd into pp-caa-wake)
extends: vault/plans/event-driven-wake-caa-2026-10-08.md (APPROVED); reuses ce-a3 Amendment C, ce-a3b-r R2/R5, ce-lifecycle-v2 WU-1/1B/1H/4
---

# caa-wake Amendment R: recover W1 without Owner mechanics, then finish wake and CAA

The approval surface is the inline Master Plan in the chat. This file is its durable copy.

## 1. Reality delta (measured 2026-10-08 ~15:30Z)
- ce/caa-wake HEAD 480f0241. Dirty: tools/wake_check.py (+7/-2), untracked tools/mission_wait.py (619 lines),
  4 docs stubs, .pp-capabilities, W1-notes.md (F1-F6, D1-D2). No test file, no W1 commit, no receipt.
- W1 mission m-0fdcdcadd6f5: BLOCKED, epoch 1, pid 38012 dead. Host reason: the worker asked for "a new goal id
  caa-wake-b ~1.5M". Envelope token_estimate 5,381,919, src **auto**: the packet's lease (1.3M + 0.3M) was never
  turned into an envelope. cost_mark 3,390,276.
- Goal caa-wake: cap 5,000,000; used 4,955,858 = settled 3,634,920 + open 1,320,938.
  - Settled: W1 worker 12820fd5 3,193,295; pane 41f83b39 441,625 (bound by cwd since 10:51:25Z; last renew at 11:02Z).
  - Open: a **lease** of 1,111,090 on pane 41f83b39 (transcript still written at 17:02 local, so it is not
    proven dead), plus a **final** hold of 209,848 on the dead worker.
  - Holds turn LEAKED after 6 h, and LEAKED still counts. Nothing ever releases them.
- CAA dependency: the approved predicate is ALREADY TRUE (`ce/a3:.../a3/U2-RECEIPT.md` exists, exit 0). That
  receipt is "CLOSED SUPERSEDED (not a success receipt)". If it were registered as written, the wait would wake
  CAA on a non-success.
- Existing owners found:
  - out-of-band control: ce-a3 Amendment C;
  - fault capsule: ce-a3b-r R5 `mission_capsule.fault_capsule`;
  - hold reconcile: ce-a3b-r R2 `goal-reconcile`, proven on ce-a3 (open 1.93M -> 0);
  - per-session autopsy: R5 `goal-autopsy`;
  - prospective binding: ce-lifecycle-v2 WU-1B, b62f9019, done but not live;
  - HALTED/succession continuation and the one-call arm recipe: lifecycle WU-1H, which is Amendment C's WU-1C;
  - executable-authority admission and coordinator sub-cap: lifecycle WU-4;
  - certified guard installer: a3b-r R3.

## 2. Decisions
R1 Reconcile caa-wake with R2 goal-reconcile, run from this unbound pane.
   - Settle the dead worker at its measured total and close its final hold.
   - Settle pane 41f83b39 at its bound total and release its lease (Owner-approved: it left the root at 11:02Z).
   - Record before and after.
R2 Salvage W1 as SALVAGE_PENDING_VERIFICATION, following the e71f3a0b precedent.
   - Commit the dirty work as a patch plus a requirement map. Make no product commit until proof exists.
   - Classify each of the 6 packet requirements as VALID / PARTIAL / INVALID / UNKNOWN by deterministic checks.
R3 Recompile the rest of W1 by semantic closure:
   - W1R-0: deterministic, 0 model.
   - W1R-1: V-WAIT tests to green, plus a checkpoint commit. Lease 0.55M + 0.10M.
   - W1R-2: the 5 mutants, the gen2 waiting port, the receipt, and the W2 arm. Lease 0.25M + 0.05M.
   - Every arm is `arm --no-launch` + `envelope --token-estimate <lease+reserve>` + `admit`. Never src=auto.
R4 Tranche 2 is ledger goal `caa-wake-t2`, under the same semantic goal and program. The cap is the Owner's
   approved amount, declared with `--source` citing this approval. Children: W2 0.6M, W3 0.1M,
   W4 (CAA T3 residual) 1.8M, W5 0.6M. Each unit is leased on its own. Unused authority is returned.
R5 Replace the CAA predicate. CAA's real need from U2 was the goal-binding resolver, which is lifecycle WU-1. The new
   predicate is a SUCCESS receipt for lifecycle WU-1 on ce/lifecycle-v2 (content match, not just existence) AND the
   live guard at the installed hash. Invalidators: the CAA plan is COMPLETED or SUPERSEDED, or caa-wake-t2 is exhausted.
R6 DO_NOT_DUPLICATE: fault capsule, reconcile, binding, HALTED succession, executable-authority admission and the
   installer. caa-wake consumes them. mission_wait's owner_authority wait plus its `next: arm` is offered to lifecycle
   as its open debt ("deterministic approval consumer"). Merge it there; do not build it twice.
R7 caa-wake chains its own units through mission_wait receipt waits once W2 is live (self-hosting): the sweep, not a
   worker or a pane, arms the next unit.

## 3. Done-gate (caa-wake's own scope)
- V-WAIT-* green, 5 mutants red, W1 commit and receipt.
- Sweep stage live by hash; canaries for absent, appears, pre-satisfied, restart, duplicate, stale, NO_WORK and DENIED.
- CAA wait registered machine-readably and zero-hot; CAA woken by the sweep with no pane.
- CAA Reality Delta and Proof of Non-Work run. T3 done or proven no-work; T2/T4/T5 closed MERGED/SUPERSEDED against
  their owners with gate evidence.
- CAA's done-gate rebased from goal ce-a3 (closed) to caa-wake/caa-wake-t2.
- KV/UKDL/CBR entries for the failures that are confirmed and not duplicates.
- Items owned elsewhere (WU-1H succession, WU-4 authority admission, R3 install) are tracked as DEPENDENCY waits,
  not rebuilt.
