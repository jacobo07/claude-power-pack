---
status: testing
phase: 06-consume-owners-and-close
source: [06-VERIFICATION.md]
started: 2026-10-04T23:00:00Z
updated: 2026-10-04T23:00:00Z
---

## Current Test

number: 1
name: "Owner and external [J] [M] [N] items (owner bundle rows 29, 30 and 31)"
expected: |
  After CE lands D, E, I (J) and Q, N, O, M (M) on a commit reachable from this branch, `python3 tools/ic_r2_evidence.py
  --pillar J --commit HEAD` (and M) prints owner_ledger rows; they are pasted with the owner and handoff evidence and
  `python3 tools/test_incremental_cognition_program.py --pillar J` (and M) passes. The Owner decides the PROMOTE-PROPOSED
  candidates of reviews/ukdl.md and reviews/cbr.md, records each promotion with its commit, re-pins ledger
  reviews.<key>.sha256 and runs `python3 tools/test_ic_closeout.py`. IC-J, IC-M and IC-N close only through these.
awaiting: user response

## Tests

### 1. Owner and external [J] [M] [N] items (exact commands in vault/programs/incremental-cognition/owner-bundle.md, Phase 6 section)
expected: ICP_PILLAR_J=PASS and ICP_PILLAR_M=PASS after CE lands its terminals on this line of history; every PROMOTE-PROPOSED candidate carries the Owner's decision and test_ic_closeout.py stays green
result: [pending]

### 2. Owner judgement of the Phase 6 review-fix decisions WR-01..WR-09
expected: Owner accepts (or amends) the policy decisions in 06-REVIEW.md: a junk or unknown owner terminal is OPEN, never a pasteable row (WR-01); exit 2 = could not run vs exit 1 = not ready (WR-02); the real-HEAD tracer derives its expectation from an independent read of the owner ledger (WR-03); a directory is not a file at HEAD (WR-04); delta evidence refs and domain-candidate targets must be canonical repo paths (WR-05, WR-06); V-ICR2-READ-ONLY is INCONCLUSIVE when only foreign untracked paths moved (WR-07); a measured line in JM-blocked.md is re-derived by the printer (WR-08); a missing control commit makes V-ICN-LEDGER-DELTAS INCONCLUSIVE, never a quiet PASS (WR-09)
result: [pending]

### 3. Judgment-tier prohibitions (verifier verdicts non-authoritative)
expected: Owner confirms the IC-J, IC-M and IC-N prohibitions held: no state.<P>, handoff, IC-* tick or mark-complete; JM-blocked.md and the bundle never read as if J or M closed; the program plan's note about CE's branch quoted as laptop-side, not as a measurement here; no candidate evidence unread, no KME-G smoke figure stated as KME-L, no upper bound stated as a saving; evidence/N.md never worded as if a pillar closed (evidence in 06-VERIFICATION.md)
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
