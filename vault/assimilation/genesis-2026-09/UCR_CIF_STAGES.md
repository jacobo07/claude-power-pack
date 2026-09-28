# Assimilation — UCR-CIF stage per capability, UKDL candidates, Constitutive Baseline status

2026-09-28. Stages use the ladder OBSERVED → LOCAL SUCCESS → REPEATED SUCCESS → CROSS-CONTEXT →
CROSS-PROJECT → ADVERSARIAL → PRODUCTION REALITY → REGRESSION PROOF → TRANSFER PROOF → PROMOTED.
Nothing below is PROMOTED: the promotion authority (UCR-CIF construction) is unmerged, and this file
is the record a promoter reads, not a promotion. CLAUDE.md gained zero lines.

## Stage per capability (highest rung with evidence)

| capability | stage | evidence |
|---|---|---|
| test live-state isolation ratchet | REGRESSION PROOF | red measured before fix (4f27cff); 29 suites green; controls |
| routing metrics (item 29) | PRODUCTION REALITY | real ledger 448 attempts; `gsd_epoch certify` on S10 and a live mission |
| verified reuse (item 30) | LOCAL SUCCESS | 13/13 both poles; approval boundary driven; no real duplicate batch yet |
| paired experiments (item 31) | PRODUCTION REALITY | exp-002: registration committed first, 4 real successors, blinded grades |
| source packet by reference (item 12) | LOCAL SUCCESS | handoff path 14/14; no live mission has used `--packet` yet |
| task ledger seam (item 22) | LOCAL SUCCESS (owner unwired) | 10/10 + AST ratchet; Goal Spine has no live invoker |
| task adaptation (item 32) | LOCAL SUCCESS (owner unwired) | 7/7; contract.revise has no production caller |
| charter lab (item 33) | OBSERVED | seam note only |
| night research (item 34) | CROSS-CONTEXT | local 11/11 + VPS deploy, status on the real host; real pass pending the window |
| reviewer reply contract | LOCAL SUCCESS | installer 11/11 on a synthetic agent; real agent ABSENT (Owner step, HR-001) |
| T4–T7 (items 18–28) | PRODUCTION REALITY | live since 6fdd61a; real reviews found real false greens |

## UKDL candidates (not promoted)

| level | id | claim | evidence rung |
|---|---|---|---|
| HARD RULE | HR-TEST-LIVE-STATE-001 | a test never writes live operational state unless it is an explicit Production Reality test | CLASS 0 recurrence + ratchet (REGRESSION PROOF) |
| HARD RULE | HR-EMPTY-GATE-001 | a gate that executed no checks cannot approve | T5 evidence bundle; real reviews |
| HARD RULE | HR-UNKNOWN-SEVERITY-001 | an unrecognised finding severity is INCOMPLETE, never approval | 2faeeaf |
| HARD RULE | HR-REUSE-NO-APPROVAL-001 | reused evidence never transfers approval to a new target | V-REUSE-CANNOT-APPROVE (driven) |
| PROCESS RULE | PR-CONTRACT-STATES-CONSTRAINTS-001 | a constraint a worker is failed for must be in its contract | d71f615 |
| PROCESS RULE | PR-EVIDENCE-BY-REFERENCE-001 | payload larger than a bounded envelope is referenced by hash, never truncated | exp-002 dry run 28/32 |
| PROCESS RULE | PR-ARM-CARRIES-TREATMENT-001 | an experiment arm must be shown to carry its treatment before registration | exp-001 withdrawn |
| TRAP | T-IMPACT-BY-FILENAME-001 | filename similarity as change-impact evidence | 6fd3102 |
| TRAP | T-TEST-DEFAULT-STATE-PATH-001 | tests inheriting module-level production state paths | 4f27cff |
| TRAP | T-CURRENT-BYTES-ARE-NOT-REVIEWED-BYTES-001 | current file bytes as proof of what a reviewer read | 8f82e11 |
| TRAP | T-USER-TIMER-WITHOUT-LINGER-001 | an installed user timer on a host without linger never fires | VPS 2026-09-28 |

## Constitutive Baseline Ratchet status

| tier | properties |
|---|---|
| LOCAL BASELINE (enforced in this repo by a gate) | live-state isolation (test_state_isolation); fail-closed review intake; nonce-bound review; import-based change impact; canonical path identity; contract-stated bounds; preregistered experiments; evidence by reference |
| CPP-WIDE CANDIDATE | test/live-state isolation; empty gate cannot approve; unknown severity fails closed; reuse never approves |
| CROSS-PROJECT CANDIDATE | tests never touch live state; evidence by reference; arm-carries-treatment |
| PROMOTED BASELINE | none — the authority is unmerged; promotion is the Owner's (or UCR-CIF's) act |
