---
status: testing
phase: 03-kme-corpus-measurements
source: [03-VERIFICATION.md]
started: 2026-10-03T22:21:23Z
updated: 2026-10-03T22:21:23Z
---

## Current Test

number: 1
name: "KME-L laptop runs: owner bundle [D]..[I], population proof first"
expected: |
  The unfiltered population proof matches the frozen KME-L entry exactly; then each pillar's primary KME-L file (and D's CPP-D-W7 leg, E's second workload) is written; only then ledger state.D..I and IC-D..IC-I.
awaiting: user response

## Tests

### 1. KME-L laptop runs, owner bundle [D]..[I] (exact commands there; population proof first, unfiltered)
expected: population_match exact; one primary measurement file per pillar with terminal_evidence true; R3 accepts the cited files
result: [pending]

### 2. H prediction check
expected: if the KME-L H share also clears 3 % (KME-G smoke 7.3 %, driven by verifier subagents), the Owner decides the follow-up for H's predicted FALSIFIED_OR_REJECTED disposition
result: [pending]

### 3. D second workload
expected: the CPP-D-W7 leg on the laptop at coverage exactly 1 (D-GEX44-B001 is UNMEASURED and confirms nothing)
result: [pending]

### 4. Review coverage
expected: tools/test_kme_pillars.py (~2.7k lines) was only skimmed by 03-REVIEW; an Owner or a later review reads it in full
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
