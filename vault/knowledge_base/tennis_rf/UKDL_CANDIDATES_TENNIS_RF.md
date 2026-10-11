---
title: UKDL candidates -- Tennis RF programme (hard rules, process rules, traps) + CBR baseline classification
date: 2026-10-12
status: CANDIDATES. ukdl-universal.md (1.3 MB, sealed, CEPS-fed) is NOT edited here; the convention in this vault
  (UKDL_CANDIDATES_*.md siblings) is that a candidate file carries the entry and the Owner or a second occurrence merges it.
evidence: vault/programs/tennis-rf/*-receipt.md, ROOT-CAUSE-C2B.md, KNOWLEDGE.md
ownership sweep: TRF_KNOWLEDGE_PROMOTION.md "Dedup record" (0 hits for the class names)
---

# A. Candidates WITH a receipt (promotion-ready)

## HR-CAND-SHARED-PRECONDITION-GATES-THE-FANOUT-AT-SEND
Any job that fans N units out over one capped resource must be refused, before spend, if a precondition common to all N
is false. A check that lives only in the judge detects after the effect. Receipt: ROOT-CAUSE-C2B.md; SEND_CERT_DRILL 10/10;
test_fanout_preconditions 29/29. Irreversible cost: 1 of 4 Phase-7 jobs plus a worker session.

## PR-CAND-ONE-SHARED-CAUSE-IS-ONE-FAILURE
N units sharing a verdict cause are counted as one failure keyed by job, never as N class-"environment" misses.
Receipt: ROOT-CAUSE-C2B.md P3, WU-W1-receipt.md (custody miss classes).

## PR-CAND-LINT-BEFORE-COMPILE
Inputs that cannot compile by construction are rejected by a zero-cost lint before the paid compile. Receipt:
WU-W1-receipt.md (5/5 mutants RED), WU-W2-receipt.md (lint inside the certificate).

## PR-CAND-ORACLE-IS-A-PREREQUISITE-UNIT
A packet whose measurement needs an oracle names the oracle's build as a prior unit, or the verdicts are UNJUDGED and the
unit's headline number is UNKNOWN. Receipt: WU-W3b/W5a/W5b receipts (0 verdicts); W10a-b built the oracle.

## PR-CAND-SIZE-BUDGETS-FROM-THE-ADMISSION-ESTIMATOR
Run the admission estimator before writing a budget table. Receipt: K2, routes resized PP 5983db9d.

## T-CAND-DEFAULT-ORACLE-GIVES-DIFF-NOT-ERROR
A parameterised judge that silently falls back to the first game's binary reports DIFF for a correct object. Every profile
needs a positive control and a "wrong-profile" mutant. Receipt: WU-W10b-receipt.md (mutant -> DIFF 2/2 RED).

## T-CAND-FRESH-WORKTREE-CRLF-VS-LF-SNAPSHOT
A snapshot hook that hashes worktree bytes fails on autocrlf checkouts. Receipt: WU-W1-receipt.md (.gitattributes fix).

## T-CAND-REFUSED-ARM-DEADLOCKS-THE-CHAIN
See KNOWLEDGE.md K3 (HALT the never-launched record, re-arm). Prevention candidate belongs to gsdx_chain, not TRF.

# B. NOT promoted (unproven candidates; this programme produced no evidence)
- Cost per function is intrinsic to the function (FUNCTION_COST_INTRINSICNESS_FALLACY): no verified function exists.
- Marginal cognition per family member falls or is flat (FLAT_MARGINAL_COGNITION): sequence curve not run.
- Repeated raw binary page faults waste tokens (REPEATED_RAW_BINARY_PAGE_FAULT): sample of 3 reads.
- Haiku/tooling routing holdouts: skipped, they need a verdict oracle (W5b receipt).
- Compiled-learning discount on families: UNPROVEN (W8: family discount 96 % singletons, curve not measured).

# C. CBR (baseline) classification
Rule: a mechanism becomes baseline only if it is wired (the send path or the producer calls it) AND tested.

| Mechanism | Wired where | Tested | Decision |
|---|---|---|---|
| W1 CAPSULE_NOT_CURRENT send guard | stage.send, exit 16 before job creation | test_fanout_preconditions 29/29 | PROMOTE (baseline) |
| W1 source lint | candidate.build_units + certificate | 24-29 gates, 5/5 mutants RED | PROMOTE |
| W1 custody miss classes + head/tail stderr | candidate.py / runner | same suite | PROMOTE |
| W2 readiness certificate | stage.send (exit 17 NOT_READY:<check>) | SEND_CERT_DRILL 10/10 | PROMOTE; caveat: RED-first order not recorded, live PINS path exercised only as a refusal |
| W2 runner trim_objdiff_report in candidate mode | runner_lib.py:1472 | covered by C2c-fix lineage, no new test here | PROMOTE with the pre-existing caveat |
| W10a capsule profile (resort/tennis) | capsule_build/candidate/reproduce/pack_inputs | TENNIS_PROFILE_DRILL 11/11, Resort suites unchanged | PROMOTE |
| W10b Tennis judge + own F root (cap 4) | candidate.oracle2, stage.py third live root | TENNIS_JUDGE_DRILL 18/18 | PROMOTE for judge control; NOT_PROVEN with a real compiled Tennis object |
| W10c A/A job 1 (ksrmb-20261011-223128) | JOBS.md row 1: judged 3/3 MATCH | no W10c receipt exists | NOT promoted as a verified rate: unit ended PARTIAL (m-6bb7a56d3392); evidence is a JOBS.md row only |
| W6 causal ledger (ledger.py) | PP evidence script, not called by any producer | 5/5 | NOT baseline: not wired, role rules are regex |
| W7 family clustering | PP evidence script | deterministic re-run, red controls | NOT baseline: not wired, no transfer proof |
| Cascade record schema (records.jsonl) | not called by a producer | none | NOT baseline: only 12 W5a rows, all UNJUDGED |
| REA | REJECT (REA-DISPOSITION.md) | n/a | no promotion; D27 certification path |
