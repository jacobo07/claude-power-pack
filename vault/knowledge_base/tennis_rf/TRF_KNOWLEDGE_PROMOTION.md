---
title: Tennis RF programme -- knowledge promotion (KV + FIOS entries), deduplicated
date: 2026-10-12
status: PROMOTED where a receipt exists; the rest listed as NOT promoted
source: vault/programs/tennis-rf/KNOWLEDGE.md (12 entries) + receipts W1-W8, W10a-b
---

# Dedup record (done before writing)
- `grep` over `vault/knowledge_base/**` for FANOUT_BEFORE_READINESS, EXPERIMENT_CANNOT_MEASURE, SOURCE_UNCOMPILABLE,
  INTRINSICNESS, FLAT_MARGINAL, REPEATED_RAW: 0 hits.
- `python -m modules.gsd_x.recall --query "fan-out readiness certificate"`: 2 hits, both are the TRF/CPX plans themselves
  (plans/tennis-rf-optimization-MASTER-PLAN-2026-10-11.md s4, plans/cpx-control-plane-extinction-cp50-2026-10-11.md s1).
  No prior KV entry. All entries below are new.

# Failure classes CONFIRMED (each cites its receipt)

## FANOUT_BEFORE_READINESS
Spending a shared, quota-capped resource on N units before any one precondition shared by all N is checked.
- Case: CP50 C2b, 1 GEX44 job (1 of 4 Phase-7 jobs) carried 50 units; no CURRENT_CAPSULE existed, so the judge could not
  accept a PASS receipt (549/549 files verified). Receipt: programs/tennis-rf/ROOT-CAUSE-C2B.md, WU-W1-receipt.md.
- Fix: `stage.send` refuses CAPSULE_NOT_CURRENT (exit 16) and NOT_READY:<check> (exit 17) before any spend.
  Proof: SEND_CERT_DRILL 10/10 (WU-W2-receipt.md), test_fanout_preconditions 29/29 (WU-W1-receipt.md).
- Prevention: the check that can refuse a whole fan-out runs at send time, not at judge time.

## DIAGNOSTIC_LABEL_COLLAPSE
One verdict copied onto every unit under a generic class ("environment"), so a single shared cause reads as N independent
noise events.
- Case: candidate.py copied the job verdict to 50 units as miss_class "environment". Receipt: ROOT-CAUSE-C2B.md P3.
- Fix: custody verdicts get their own classes (custody_no_current, custody_capsule_mismatch, custody_invalid); stderr kept
  as 2 KB head + 2 KB tail. Proof: test_fanout_preconditions 29/29.
- Detector: if N units share one miss_class, group by job before counting.

## EXPERIMENT_CANNOT_MEASURE_ITS_TARGET
An experiment whose design contains no step that can produce the quantity it exists to measure.
- Case 1: C2b job had no model step, so it could not give tokens per function (K1).
- Case 2: Tennis W5a step 3 needed a Tennis oracle that did not exist; every verdict UNJUDGED, per-verified cost UNKNOWN
  (K5, WU-W3b-receipt.md, WU-W5b-receipt.md: 0 verified, 0 model-free closures).
- Prevention: a packet that needs an oracle lists the oracle as a prerequisite unit. Plan W10a-c was inserted for that.

## SOURCE_UNCOMPILABLE_BY_CONSTRUCTION
Inputs built so that no compile can succeed, discovered only after the compile spend.
- Case: 50/50 C2b units rc=1 (raw m2c `?` types, CXX built with `-lang c`). ROOT-CAUSE-C2B.md P2.
- Fix: zero-compile `source_lint.py` wired into `candidate.build_units` and into the W2 certificate (per-unit lint).
  Proof: WU-W1-receipt.md (5/5 mutants RED), WU-W2-receipt.md replay (UNRESOLVED_TYPE named).

## PLAN_TARGET_BELOW_MEASURED_PHYSICS (K2)
A plan priced work units at one call's cost; the admission estimator (declared calls x 2.4 growth) priced 25 calls at
4.22M vs a 2.5M target and refused. Prevention: run `route_admission.py admit` before writing a budget table.
Proof: K2; routes resized PP 5983db9d.

## SHARED_POINTER_COLLISION (K-W10b)
One shared CURRENT_CAPSULE pointer would have made Tennis and Resort/cp50-c2 jobs fight over it and share one cap.
Fix: own F root as a third live root, own cap {1: 4}. Proof: TENNIS_JUDGE_DRILL 18/18 (WU-W10b-receipt.md).

## SILENT_WRONG_DEFAULT_ORACLE (K-W10b)
`match.py`/`candidate` judged Tennis against the Resort DOL: result is DIFF, not an error. Fix: profile-selected DOL/L0;
default path unchanged. Proof: control m1, mutation "Tennis judge reads Resort DOL" -> DIFF 2/2 RED.

## Small traps (each one wasted a launch or a call)
- m2c_producer `asm_root` appends "asm" itself: pass `.../out`. First launches in the foreground (K-W7).
- Donor count: "179" was 167 exact + 12 loose-only; count the class the claim names (K-W7).
- Refused arm-chain with no GSD workstream deadlocks the chain: repair = HALT the never-launched record, re-arm (K3).
- `.ksr_vault` hook hashes worktree bytes against LF snapshots; `core.autocrlf=true` fresh worktrees fail. Fix:
  `.gitattributes .ksr_vault/** text eol=lf` (WU-W1-receipt.md).

# NOT promoted (named in the packet; the evidence is absent)
- FUNCTION_COST_INTRINSICNESS_FALLACY: W6 shows 41.6 % floor rent and 0 % SEMANTIC, but 0 functions were verified, so cost
  per function cannot be separated from session topology. Hypothesis only.
- FLAT_MARGINAL_COGNITION: the same-family sequence curve was never run (WU-W5b-receipt.md: UNKNOWN). Not measured.
- REPEATED_RAW_BINARY_PAGE_FAULT: W6 sample is 2 reads + 1 re-read (1/3). Too small. Not measured.

# FIOS entries (frontier-intelligence layer: capital lessons)
1. Programme spend to first verified function: 13,086,143 processed tokens over 321 calls (18 worker sessions, W1-W5b),
   0 verified functions, SEMANTIC share 0 % (WU-W6-receipt.md). Lesson: the first R&D tokens bought tooling and
   measurement; price them as CAPEX, not per-function cost.
2. Context duplication factor 14.06 (processed/new); 27.0 % tax, 49.9 % exploration, 22.5 % work (W6). A worker that
   explores costs more than a worker that does; hand it the file list.
3. Tennis is ~70 % novel (1,255 families / 1,797 fns, novelty density 0.698) and 9.3 % deterministic-eligible (167)
   (WU-W7-receipt.md): the Resort cascade saves little on Tennis.
