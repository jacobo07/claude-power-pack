---
status: testing
phase: 05-offline-replay-and-owner-bundle
source: [05-VERIFICATION.md]
started: 2026-10-04T03:00:00Z
updated: 2026-10-04T03:00:00Z
---

## Current Test

number: 1
name: "Laptop [L] items: KME-L ranking run + the Owner's live-quota decision (owner bundle rows 10 and 11)"
expected: |
  After the Laptop code sync and the Phase 3 population proof, `kme_replay.py rank --denominator KME-L` is run on the laptop and
  its printed L-KME-L file is committed (population exact, all three candidates measured or UNMEASURED with named reasons),
  and the Owner's decision on live champion / challenger sessions is recorded in their own words as evidence/L-owner-decision.md.
  IC-L closes only through these; until then it stays unticked.
awaiting: user response

## Tests

### 1. Laptop [L] items (exact commands in vault/programs/incremental-cognition/owner-bundle.md, Phase 5 section)
expected: L-KME-L-<date>.md committed with terminal_evidence true, and evidence/L-owner-decision.md written by the Owner naming [L]; `test_incremental_cognition_program.py --pillar L` then reaches a terminal disposition
result: [pending]

### 2. Owner judgement of the Phase 5 review-fix decisions CR-01 / WR-01..04 / WR-06 / IN-01
expected: Owner accepts (or amends) the R4 identity rule (the bundle under any spelling, a byte copy, or a mission-written file never counts as an owner_decision; exemption only by the literal L-owner-decision*.md name), the R3-L cross-check of front matter against the json block, terminal only at rollover growth 100000, retries and rereads keyed per thread, and dense ranks for equal figures (05-REVIEW-FIX.md marks them requires human verification)
result: [pending]

### 3. Judgment-tier prohibitions (verifier verdicts non-authoritative)
expected: Owner confirms the IC-L prohibitions held: no number for an UNMEASURED candidate, no figure presented as a saving, no ledger / IC-L / claude-session / ~/.claude write, smoke never presented as KME-L, no Owner decision invented, no laptop run claimed (evidence in 05-VERIFICATION.md, Prohibitions table)
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
