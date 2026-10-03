---
phase: 02-listing-floor
plan: 02
subsystem: listing-floor
tags: [ledger, pillar-closure, owner-bundle, pillar-B]
requirements: [SC-B]
status: complete
commits: 1
plan_head_before: c95f58f06dc9d03fd5a6871ce20156b5993cb39b
actuals:
  tokens: 9000
  tasks: 2
  commits: 1
---

# Phase 2 Plan 02: Pillar B ledger closure Summary

**Pillar B is closed in the ledger as FALSIFIED_OR_REJECTED_BY_EVIDENCE on the generated D-LISTING measurement, with one upper-bound saving and one laptop-plane `[B]` Owner line for the plugin-paging gateway hypothesis.**

## Task 1 (tracer) and Task 2 -- commit cfdd8196

- A writer script (`/home/kobii/.claude/jobs/6be377dc/tmp/write_b.py`, outside the repo) composed `state.B` from
  `python3 tools/test_listing_floor_verdict.py --json` only, refused unless verdict == FALSIFIED, asserted the L7
  regex is clear, the `frozen` object unchanged and equal to the FROZEN_AT (217d72b5) copy, and every other pillar's
  state unchanged, then replaced exactly the one `"B":` line textually.
- Evidence: measurement (sha256 `941e7185e8bdd11838451673c233595d0d88c6e3b21d3f15866e6ac961d93dde` of
  `vault/programs/skill-capability/evidence/B-listing-floor.md`), owner `wiki/tools/listing_floor_probe.py`,
  commits 4d1cfb83 (K4), d9072185 (C6), 84a2d891 (02-01). No `gate` entry, no sha pin of the live jsonl.
- Saving: one entry, 9000 tokens, upper_bound, displacement unknown, denominator D-LISTING; note carries
  ~4000 per gateway read, C6 +11 chars, K4 +2105 startup tokens (noise +-1500, n=1 per arm) as measured, not saved.
- Acceptance one-offs: kinds `['commit', 'measurement', 'owner']`, 1 saving `upper_bound unknown D-LISTING`; 11
  figures of 3+ digits in reason/value/note all found in the --json object (C6 +11 is the difference of two
  --json values, `after - before`); L7 regex False; frozen equals FROZEN_AT copy True; ledger numstat `1 1`, only
  the `"B":` line changed.
- Owner bundle: exactly one `[B]` line appended (`[A]` lines still 2), contains `host: laptop`, `D-SESSIONS`,
  `upper bound`, `listing_floor_probe.py`, the ': ' split precondition, the new-labels note.
- `git show --stat HEAD` lists exactly ledger.json and owner-bundle.md.

## Verbatim result lines

- Pre-commit `--pillar B`: `CEP_PILLAR_B=PASS` (rc 0)
- Post-commit `--pillar B`: `CEP_PILLAR_B=PASS`
- Post-commit `--pillar A`: `CEP_PILLAR_A=PASS`
- Post-commit verdict script: `LF_PASS=11/11`
- `--selftest` last two lines: `CEP_SELFTEST=PASS` / `SCP_SELFTEST=PASS` (rc 0)

D-SESSIONS consumed this phase: 0 fresh sessions (listing family 8 of 12 remaining).

## Deviations from Plan

- **[Choice] one commit:** Task 1 (tracer) was verified (`--pillar B` PASS) and left uncommitted, then committed
  together with Task 2 as the plan's commit step prescribes, since both touch only the two plan files.
- The 02-01 commit cited as evidence is `84a2d891` (the commit that completed the verdict gate); the plan said
  "from its SUMMARY".
- Untracked `.gsd/` in the tree pre-existed and was left alone.

## Known Stubs

None.

## Threat Flags

None. Only a ledger entry and an Owner-bundle text line changed; no new network, auth or schema surface.

## Self-Check: PASSED

Commit cfdd8196 resolves; ledger and bundle changes present; pillar A/B and verdict gate green on the committed tree.
