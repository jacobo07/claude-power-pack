---
status: testing
phase: 02-persistent-failures-and-remote-integrity
source: [02-VERIFICATION.md]
started: 2026-10-03T19:30:24Z
updated: 2026-10-03T19:30:24Z
---

## Current Test

number: 1
name: "[C] PRG on the laptop: a7 mission provider_held until /login, then provider_released and one relay"
expected: |
  Ledger rows saved to vault/programs/incremental-cognition/evidence/C-prg.md; only then ledger state.C and IC-C.
awaiting: user response

## Tests

### 1. [C] PRG on the laptop (owner-bundle [C] line, exact commands there)
expected: a7's mission shows provider_held (class auth, quarantine, no launch) until the re-login, then provider_released and one relay; rows saved as evidence/C-prg.md
result: [pending]

### 2. [B] a7 re-login, Owner decision on install-local changes (a7 1 modified file, a5 1024), env deploy --apply for a7 and a5
expected: post-deploy preflight on a7 shows no pp_install_stale / hooks_broken / auth_expired; saved as evidence/B-prg.md
result: [pending]

### 3. WR-04 / WR-06 / WR-07 operator-facing semantics (02-REVIEW-FIX.md, flagged "requires human verification")
expected: Owner agrees with: lapsed token + unknown refresh expiry = unknown (park kept); status/clear on a renewal successor act on the inherited hold; breaker-less park releases only on usable-login evidence
result: [pending]

### 4. WR-08 merge strategy for PP_COMMIT_FLOOR=60e7947d (only on mission/incremental-cognition-run)
expected: merge preserves 60e7947d (no squash/rebase) or re-points the floor in the same merge
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
