---
status: testing
phase: 04-cognitive-cost-regression-gate
source: [04-VERIFICATION.md]
started: 2026-10-04T00:01:20Z
updated: 2026-10-04T00:01:20Z
---

## Current Test

number: 1
name: "Laptop [K] item: reference floor + one real PRG --check (owner bundle [K])"
expected: |
  The fixed tool files land on the laptop (tree state ef336ec7), the fixture suite is green there, floor/reference.json is written
  (option A probe or option B --session), the seeded --real-session control goes red/green as stated, and one real --check PRG is
  saved as evidence/K-prg.md. Only then K takes IMPLEMENTED_AND_VERIFIED and IC-K is ticked.
awaiting: user response

## Tests

### 1. Laptop [K] item (exact commands in vault/programs/incremental-cognition/owner-bundle.md, Phase 4 section)
expected: reference.json committed, K-prg.md recorded, `test_incremental_cognition_program.py --pillar K` passes
result: [pending]

### 2. Owner judgement of the review-fix policies WR-01 / WR-02 / WR-03
expected: Owner accepts (or amends) layer_absent -> exit 2, uncorrelated hook element -> unattributed, and uncompared tokens axis -> exit 2 unless --chars-only. Consequence to weigh: ordinary sessions reach only WITHIN_BOUND_CHARS_ONLY; plain WITHIN_BOUND needs a same-prompt probe session.
result: [pending]

### 3. Judgment-tier prohibitions (verifier verdicts non-authoritative)
expected: Owner confirms the three IC-K prohibitions in 04-0N-PLAN must_haves held (verifier judged all held; evidence in 04-VERIFICATION.md)
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
