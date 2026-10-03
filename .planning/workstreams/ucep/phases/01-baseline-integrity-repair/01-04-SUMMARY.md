---
phase: 01-baseline-integrity-repair
plan: 04
subsystem: tower-baselines
tags: [ucep, tower, ratchet, reanchor, provenance, baselines]
requires: ["01-01", "01-03"]
provides:
  - "ratchet.plan_reanchor / reanchor: one REANCHORED generation per call, all-or-nothing, refuses changed/empty quote, relative or worktree path, no-op, unknown/reverted id, non-allowlisted authority"
  - "family_baseline.py reanchor <family> --map <json> --reason R --authority A [--dry-run]"
  - "persistent_state/B1.json (8 ids) and wii_homebrew/B1.json (1 id): the 9 QUOTE_MISSING citations re-anchored to skills/<skill>/SKILL.md"
affects: [01-05]
key-files:
  created:
    - .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-reanchor-map.json
    - vault/tower/baselines/persistent_state/B1.json
    - vault/tower/baselines/wii_homebrew/B1.json
  modified: [modules/tower/ratchet.py, tools/family_baseline.py, tools/test_ucep_baseline_integrity.py]
decisions:
  - "Origins re-anchored to the PP main checkout skills/<skill>/SKILL.md (read-only); the home fallback was not needed"
  - "reanchor stores the OLD quote verbatim and refuses a changed or empty quote: a provenance move cannot launder a changed rule text"
  - "Assumption A1 (for 01-05 EVIDENCE): the Owner-approved plan of record vault/plans/ucep-naked-verb-2026-10-02.md is the Owner's authority for these re-anchorings"
metrics:
  completed: 2026-10-03
status: complete
commits: 4
plan_head_before: eabac68ebd49aeac32fd2b5e4f752011e7fe1346
requirements: [UCEP-01]
actuals:
  tokens: 16258   # chars/4 over `git diff BASE HEAD` (65032 chars; ~half is the two generated B1 files)
  tasks: 2
  commits: 4      # MEASURED: git rev-list --count BASE..HEAD at SUMMARY write (the SUMMARY commit itself comes after)
---

# Phase 1 Plan 4: ratchet.reanchor and the 9 rotted citations Summary

`ratchet.reanchor` now exists and refuses every laundering and rot path it was designed against, and the 9 entries whose `~/.claude/rules/*.md` citations became pointer stubs
are VERIFIED at their skill origins through two recorded generations (`persistent_state/B1.json`, `wii_homebrew/B1.json`). `V-BGEN-REAL-B0-CITATIONS-HOLD` passes at
population 62; no B0 and no web_surface B1 byte changed.

Commits (measured, `git rev-list --count eabac68e..HEAD` = 4): `e39d67c1` (Task 1 API + CLI), `694f5a24` (Task 1 data), `d5fd2ae4` (Task 2 refusal rules), `994fe560` (Task 2 data).
Status: COMPLETE. Production Reality: OBSERVED (real commands and exit codes in this worktree; harness on synthetic temp roots; the real tree judged by V-UCEP-REAL-REANCHORED and the regression suites).
Assumption A1 (RESEARCH, stated for 01-05 EVIDENCE as an Owner-reviewable assumption): the Owner's approved plan of record is the Owner's authority for this re-anchoring, so the real writes carry
`Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)`. Both writes are append-only and supersedable by a later reanchor/revert.

Environment: PowerShell tool disabled; commands via Bash with absolute `git.exe` / Python 3.12 and the `# bash-safe` marker. Root verified before each commit:
`C:/Users/User/.claude/skills/claude-power-pack/.claude/worktrees/ucep`, `ucep/mission`. BASE (persisted ledger `gsd-plan-head-before-01-04`) = `eabac68ebd49aeac32fd2b5e4f752011e7fe1346`.
Subject scope `(01-04)` per the orchestrator (the plan text said `ucep-01`).

Dirty-path SET before the plan (orchestrator-owned only): ` M .planning/workstreams/ucep/STATE.md`, `?? .gsd/`, `?? .planning/workstreams/ucep/milestone.lock`, `?? .planning/workstreams/ucep/state.json`.

sha256 before (B0s and web_surface B1; must be identical after):

```
1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407  kobiicraft_mode/B0.json
bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64  persistent_state/B0.json
98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7  web_surface/B0.json
2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1  web_surface/B1.json
2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd  wii_homebrew/B0.json
```

Precondition for Task 1 held: `git ls-files --eol -- vault/tower/baselines` showed `w/lf` on all 5 files; `rt.is_authorized` exists.

## Task 1 (tracer): reanchor end to end on ONE real entry

RED (3 new gates added first, HEAD `eabac68e`, ratchet.py unchanged), rc=1:

```
  FAIL V-UCEP-REANCHOR-ONE-GENERATION         generations=[0] error=AttributeError: ratchet.reanchor does not exist
  FAIL V-UCEP-REANCHOR-REFUSES-QUOTE-MISSING  refusal=None other='AttributeError: ratchet.reanchor does not exist' generations=[0]
  FAIL V-UCEP-REANCHOR-CLI                    dry rc=2 gens=[0]; real rc=2 gens=[0]; bad rc=2 gens=[0]; ...
UCEP_BASELINE_INTEGRITY_PASS=14/17  threshold=17/17
```

GREEN after `ratchet.plan_reanchor`/`reanchor` and `family_baseline.py reanchor` (rc=0): `UCEP_BASELINE_INTEGRITY_PASS=17/17  threshold=17/17`.
Commit `e39d67c1` feat(01-04): ratchet.reanchor moves an entry's provenance in one recorded generation (3 files).

Real map (temporary script under the job tmp dir, not committed). `bl.active_entries(fam)` with `verify_origin == QUOTE_MISSING` equalled EXACTLY the 9 ids of the plan.
Root chosen per family: **main checkout** (`C:\Users\User\.claude\skills\claude-power-pack\skills\<skill>\SKILL.md`, read-only) for BOTH families; the home fallback was not needed.
Every id VERIFIED at the main-checkout candidate; all lines equal the plan's table, no differences:

| family | id | skill | line | verdict |
|---|---|---|---|---|
| persistent_state | persistent_state-destructive-op-authorizes-exact-state-seen | destructive-state-authorization | 13 | VERIFIED |
| persistent_state | persistent_state-destructive-identity-falsification-test | destructive-state-authorization | 26 | VERIFIED |
| persistent_state | persistent_state-absence-of-identity-refuses | destructive-state-authorization | 42 | VERIFIED |
| persistent_state | persistent_state-precondition-window-must-be-closed | destructive-state-authorization | 82 | VERIFIED |
| persistent_state | persistent_state-batch-reauthorize-per-item | destructive-state-authorization | 109 | VERIFIED |
| persistent_state | persistent_state-monetary-qualifiers-travel-with-amount | monetary-quantity-integrity | 15 | VERIFIED |
| persistent_state | persistent_state-monetary-conflicting-qualifiers-refuse | monetary-quantity-integrity | 26 | VERIFIED |
| persistent_state | persistent_state-monetary-no-conversion-without-authorized-source | monetary-quantity-integrity | 37 | VERIFIED |
| wii_homebrew | wii_homebrew-claim-must-name-observing-plane | develop-here-prove-there | 14 | VERIFIED |

Map: `01-reanchor-map.json` (2 families, 9 ids, UTF-8, LF).

Dry-run (CLI, real tree, rc=0 both): wii_homebrew 1 planned line, persistent_state 8 planned lines, every one ending `VERIFIED`, e.g.
`wii_homebrew-claim-must-name-observing-plane: C:\Users\User\.claude\rules\develop-here-prove-there.md:9 -> C:\Users\User\.claude\skills\claude-power-pack\skills\develop-here-prove-there\SKILL.md:14 VERIFIED`.

Real write (wii_homebrew only), authority `Owner (UCEP-01, plan of record vault/plans/ucep-naked-verb-2026-10-02.md)`:

```
reanchored wii_homebrew-claim-must-name-observing-plane -> ...\vault\tower\baselines\wii_homebrew\B1.json   (rc=0)
wii_homebrew chain: OK (generations [0, 1])                                                                   (verify rc=0)
generations [0, 1]
parent_sha256 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd
changes keys ['wii_homebrew-claim-must-name-observing-plane']  kind REANCHORED, authority Owner (UCEP-01, ...)
verify_origin VERIFIED ...skills\develop-here-prove-there\SKILL.md 14
```

B1 has 0 CRLF byte pairs; `git ls-files --eol` -> `i/lf w/lf attr/text eol=lf`. All 4 B0s and web_surface B1 sha256 unchanged (same five values as above).
Commit `694f5a24` data(01-04): re-anchor wii_homebrew claim-must-name-observing-plane to its skill (B1) (map + wii_homebrew/B1.json only).

## Task 2: refusal matrix (RED then GREEN), then the 8 persistent_state entries

RED (11 gates added first, HEAD `694f5a24`, `ratchet.py` as committed in Task 1), rc=1:

```
  FAIL V-UCEP-REANCHOR-REFUSES-CHANGED-QUOTE  refusal=None other=None generations=[0, 1] (want [0])
  FAIL V-UCEP-REANCHOR-REFUSES-RELATIVE-PATH  refusal=None other=None generations=[0, 1]
  FAIL V-UCEP-REANCHOR-REFUSES-WORKTREE-PATH  refusal=None other=None generations=[0, 1]; control refusal=None other=None
  FAIL V-UCEP-REANCHOR-REFUSES-NOOP           refusal=None other=None generations=[0, 1] (want [0])
  FAIL V-UCEP-REAL-REANCHORED                 persistent_state: gens=[0] kinds_ok=False broken=[...8 ids]
UCEP_BASELINE_INTEGRITY_PASS=23/28  threshold=28/28
```

REFUSES-EMPTY-QUOTE already PASSED in RED: an empty quote falls to the weak-vocabulary fallback, which returned WEAK for the synthetic fixture (the plan anticipated this). The explicit rule now refuses it
by name instead of by luck. Every other new refusal gate (MOVED, BAD-AUTHORITY, UNKNOWN-ID, REVERTED-ID, ALL-OR-NOTHING) was already satisfied by Task 1's verify-only core plus `_need`/`_active`.

After the rules (no-quote, changed quote, non-absolute path, `/.claude/worktrees/` path, no-op; old quote stored verbatim): `27/28`, only `V-UCEP-REAL-REANCHORED` red (persistent_state unwritten).
Commit `d5fd2ae4` fix(01-04): reanchor refuses changed/empty quotes, relative or worktree paths, no-ops (ratchet.py + harness).

Real write (persistent_state, same authority as Task 1), dry-run re-run after the rules (rc=0, 8 planned lines, all VERIFIED; printed lines truncated to 60 chars by my `cut`, full lines in Task 1 above):

```
reanchored persistent_state-absence-of-identity-refuses, ...-batch-reauthorize-per-item, ...-destructive-identity-falsification-test,
  ...-destructive-op-authorizes-exact-state-seen, ...-monetary-conflicting-qualifiers-refuse, ...-monetary-no-conversion-without-authorized-source,
  ...-monetary-qualifiers-travel-with-amount, ...-precondition-window-must-be-closed -> ...\vault\tower\baselines\persistent_state\B1.json   (rc=0)
persistent_state chain: OK (generations [0, 1])      (verify rc=0)
wii_homebrew chain: OK (generations [0, 1])          (verify rc=0)
generations [0, 1]; parent_sha256 bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64
changes: 8, kinds ['REANCHORED']; unverified active entries: []; CRLF byte pairs in B1: 0
```

Commit `994fe560` data(01-04): re-anchor 8 persistent_state entries from rule stubs to their skills (B1). `git show --stat HEAD` lists only `vault/tower/baselines/persistent_state/B1.json`.

## Regression sweep (after both writes; every run rc=0)

```
UCEP_BASELINE_INTEGRITY_PASS=28/28
BASELINE_GENERATIONS_PASS=16/16     (V-BGEN-REAL-B0-CITATIONS-HOLD: "62 stored entries hold (14 moved: ...)")
TOWER_RATCHET_PASS=21/21
FINJ_PASS=23/23
TOWER_SELECT_PASS=15/15
FAMILY_BASELINES_PASS=20/20
TOWER_DONEGATE_PASS=10/10
TOWER_INHERITANCE_PASS=16/16
```

Dirty-path SET bracketing the sweep: identical before and after (`DIRTY SET UNCHANGED`); it held only the orchestrator-owned paths plus this plan's own uncommitted `01-04-SUMMARY.md` / `persistent_state/B1.json`.
sha256 AFTER (identical to BEFORE, all five): kobiicraft_mode/B0 `1a501441...2407`, persistent_state/B0 `bcb20d37...dc64`, web_surface/B0 `98e8d33f...d2d7`, web_surface/B1 `2e54ac45...d8e1`, wii_homebrew/B0 `2603cf39...c1bd`.
`git diff --name-status eabac68e..HEAD -- vault/tower/baselines`: `A persistent_state/B1.json`, `A wii_homebrew/B1.json` only. No file added under `modules/`.

## Deviations from Plan

- **[Scope] Commit subject scope** `(01-04)` instead of the plan's `ucep-01`, per the orchestrator (as in 01-03).
- **[Rule 3 - environment]** PowerShell tool unavailable; every command ran through Bash with absolute exe paths and the `# bash-safe` guard marker, Python invoked directly. No behavioural effect.
- **[Observation, out of scope]** `V-BGEN-REAL-B0-CITATIONS-HOLD` reports 14 entries as MOVED (e.g. `kobiicraft_mode-async-io`, `-golden-run-e2e`, `-gui-state-via-pdc`). The gate tolerates MOVED
  (quote present, line shifted); they predate this plan and belong to no family this plan touches. Not re-anchored (plan bound: the 9 QUOTE_MISSING only); candidate for 01-05 or a later phase.
- No auto-fix deviations; no quote was gone from the skills, so the revert fallback was not exercised on real data.

## Known Stubs

None. The temporary map-building script lives under the job tmp dir and is not committed; its output (`01-reanchor-map.json`) is the committed input record.

## Threat Flags

None beyond the plan's threat model (T-01-14..18 mitigated by the same-quote, path and all-or-nothing rules and their gates; T-01-16 accepted as assumption A1).

## Self-Check: PASSED

Files present: `modules/tower/ratchet.py`, `tools/family_baseline.py`, `tools/test_ucep_baseline_integrity.py`, `01-reanchor-map.json`, `persistent_state/B1.json`, `wii_homebrew/B1.json`.
Commits present: `e39d67c1`, `694f5a24`, `d5fd2ae4`, `994fe560`. Orchestrator-owned STATE.md / ROADMAP.md / `.gsd/` / `milestone.lock` / `state.json` were not staged or edited.
