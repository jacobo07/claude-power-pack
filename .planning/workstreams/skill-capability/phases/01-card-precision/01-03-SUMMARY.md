---
phase: 01-card-precision
plan: 03
subsystem: program-ledger
tags: [ledger, pillar-closure, evidence, pillar-A]
requires: ["01-01", "01-02"]
provides:
  - "ledger state.A = IMPLEMENTED_AND_VERIFIED with gate + prg evidence (sha256 of LF bytes); frozen object unchanged"
  - "vault/programs/skill-capability/evidence/A-card-precision.md (prg evidence)"
  - "vault/programs/skill-capability/owner-bundle.md with two [A] laptop-plane lines"
affects: [vault/programs/skill-capability/ledger.json]
key-files:
  created:
    - vault/programs/skill-capability/evidence/A-card-precision.md
    - vault/programs/skill-capability/owner-bundle.md
  modified:
    - vault/programs/skill-capability/ledger.json
decisions:
  - "ledger.json written by textual replacement of the single `state.A` line, so the diff is exactly one line and the hand layout of the file is kept; the frozen dump was asserted equal before and after and equal to the FROZEN_AT copy"
  - "Savings: one upper_bound entry (5 turns, displacement unknown, denominator D-CARD); no realized figure"
requirements: [SC-A]
metrics:
  duration: "about 15 min wall clock (gate re-run 16:50Z host clock)"
  completed: 2026-10-03
status: complete
actuals:
  tokens: 4500    # approx chars/4 over the authored files (evidence file about 16k chars incl. verbatim gate output, ledger line, owner bundle)
  tasks: 2
  commits: 2      # MEASURED: git rev-list --count a60f34e74e0b7252f9b6f372b1eedc2ac78ef844..HEAD at SUMMARY write (excludes this SUMMARY's own commit)
plan_head_before: a60f34e74e0b7252f9b6f372b1eedc2ac78ef844
---

# Phase 1 Plan 03: Pillar A ledger closure Summary

Pillar A is closed in the program ledger as IMPLEMENTED_AND_VERIFIED: the verifier re-runs `tools/test_card_precision.py` on gex44 and prints `CEP_PILLAR_A=PASS`, with the prg evidence cited by LF sha256 and the saving recorded as an upper bound over D-CARD.

## Observed output (host kobicraft-gex44)

Gate, run once before writing the evidence file: `python3 tools/test_card_precision.py` -> rc 0, `SCA_PASS=36/36`, HEAD a60f34e7, 2026-10-03T16:50:13Z (full stdout is in the evidence file, verbatim).

`--pillar A`, pre-commit (after the ledger write, before any 01-03 commit), `timeout 1900 python3 tools/test_skill_capability_program.py --pillar A`:

```
CEP_PILLAR_A=PASS
```
rc=0.

`--pillar A`, post-commit (tree at 78ae723f, includes both 01-03 commits):

```
CEP_PILLAR_A=PASS
```
rc=0.

`--selftest` (`timeout 900 python3 tools/test_skill_capability_program.py --selftest`, rc 0), last two lines verbatim:

```
CEP_SELFTEST=PASS
SCP_SELFTEST=PASS
```

Plan baseline at plan time was `FAIL L3 A: no terminal disposition`, `CEP_PILLAR_A=FAIL`.

Acceptance checks observed: `git diff` of the ledger before commit changed exactly 1 line (the `state.A` line; numstat `1 1`); frozen dump equal to the FROZEN_AT copy (asserted in the writing script, and L2 passes inside `--pillar A`); evidence file greps: `mtime_source|placed|measured` = 21 lines, `gex44` = 12, `4615e1d1` = 5, `CEP_PILLAR_A` = 0; the reason string was checked against the L7 word list before writing.

## Task log

### Task 1 (tracer) - commit fad5a253
- Evidence file with: rule and aperture, D-CARD table (3a05f288 the single measured mtime, taken from the pack's recorded value; the other four placed inside writer windows identified from command text), the 6th deny 4615e1d1 beside D-CARD, the git-128 x6 section with the gate's verbatim lines, C8, the out-of-owner hook flag, the gate stdout verbatim with `command:`/host/date/HEAD, savings, commits.
- `state.A`: terminal IMPLEMENTED_AND_VERIFIED; evidence in order gate, prg, file (evidence pack, sha `dacfdf5a...0c05`), file (replay spec, LF sha), owner (`hooks/doctrine_cards.js`), commit 4e9cf4d4, commit 71cd35e0; one upper_bound saving.
- Tracer feedback gate: `--pillar A` printed PASS (rc 0) before the commit, so expansion to Task 2 was safe.

### Task 2 - commit 78ae723f
- `owner-bundle.md` created: 2-line header, then two `[A]` lines. Line 1 is the plan's laptop live-card sync (names `mission/skill-capability`, `hooks/doctrine_cards.js`, `host: laptop`, the expected `unknown_reasons` value, the 3 `abcd1234` rows). Line 2 is the orchestrator-added item: eadc0fd5 (`path.win32.basename` in `unwrapCall` of the live `hooks/capsule_mutation_guard.js`), Owner to accept or revert when syncing hooks.
- `--selftest` and the post-commit `--pillar A` recorded above.

## Honest limits recorded in the evidence file

- 4a7ee8bc: the writer is identified by window times only. The pack's truncated command shows `WriteAllText` of `spec_*.json`, not `ledger_write.py` literally.
- Four of five D-CARD replays use placed mtimes, not measured ones; only 3a05f288 is measured, and that measurement is the pack's laptop value, not re-measured on gex44.
- dubious-ownership 128: NOT-REPRODUCED on gex44 (git 2.43 seam yields exit 129 with the no-index banner).
- fce2689e x3: cause not recoverable from the pack; the unborn-HEAD fix is one possible cause, not an identified one.
- The capsule e2e section was not run on gex44 (dispatcher card path is the laptop layout), so the claim that it no longer writes the live ledger rests on the private state dir, the sweep and the drill.
- The 6th deny 4615e1d1 (rollover predecessor lines) stays denied and is not fixed.
- The saving is an upper bound only; no live-session measurement exists on gex44.

## Deviations from Plan

### Auto-fixed Issues

None in the sense of Rules 1-3 firing on this plan's own work. Two plan-directed adaptations:
- The ledger was written by a script doing a single-line textual replacement rather than `json.dump` of the whole object, because the file's hand layout (inline objects per pillar) would otherwise have been reformatted and the acceptance check requires only `state.A` lines to change. The script asserted `frozen` unchanged versus both the in-memory copy and `git show 217d72b5...:ledger.json`, and that every other pillar's state is unchanged.
- Task 2 committed `owner-bundle.md` alone first, so the SUMMARY could hold the post-commit `--pillar A` output; this SUMMARY is committed separately (docs commit, with STATE/ROADMAP).
- Orchestrator additions beyond the plan text: a second `[A]` owner-bundle line (the capsule guard hook) and the honest-limits entries above in the evidence file (the evidence file already carried the hook flag and the 4a7ee8bc / dubious-ownership / capsule-e2e notes at write time).

## Known Stubs

None.

## Threat Flags

None new. T-01-10 held (frozen asserted equal before and after, L2 passes); T-01-11 (prg cited by LF sha, gate output verbatim with command/host); T-01-12 (every runtime claim names gex44, laptop effect is an `[A]` line); T-01-13 (saving is upper_bound / unknown / D-CARD).

## Self-Check: PASSED

Files present: evidence/A-card-precision.md, owner-bundle.md, ledger.json (`ls vault/programs/skill-capability/` and `evidence/` observed). Commits fad5a253 and 78ae723f present in `git log`; `git log -1 --format=%s` matched the message subject after each.
