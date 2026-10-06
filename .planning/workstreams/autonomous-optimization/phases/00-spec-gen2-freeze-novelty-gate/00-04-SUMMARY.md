---
phase: 00-spec-gen2-freeze-novelty-gate
plan: 04
subsystem: ic-gen2-ledger
tags: [ic-gen2, champion, opp-001, g2-champ, g2-opp, audit, secret-firewall, sha256-pins]
requires: [00-02, 00-03]
provides:
  - "gen2/evidence/champion/: five byte copies (Run 5 / Run 6 summaries, both r4-population logs, the Run 6 runner) with sha256 pins"
  - "gen2 ledger frozen.champion (run5 reconstructed, run6 runner-script, ratios_derived) and opportunities[OPP-001] (priced, outside frozen)"
  - "tools/ic_gen2.py: g2_champ(), g2_opp(), frozen_sha256(), expected_final_failures(), roadmap_phase_map(), audit(), main('audit')"
  - "wrapper --generation 2 --audit routing"
affects: [00-05]
tech-stack:
  added: []
  patterns: ["evidence re-derived through the resolver on every run (copy, pin, re-parse)", "injectable tracked/selftest_fn so an audit mutant is hermetic and cannot recurse into the selftest", "mutants written first and observed SURVIVING an empty rule before the rule exists"]
key-files:
  created:
    - vault/programs/incremental-cognition/gen2/evidence/champion/run5-summary.txt
    - vault/programs/incremental-cognition/gen2/evidence/champion/run5-r4-population.log
    - vault/programs/incremental-cognition/gen2/evidence/champion/run6-summary.txt
    - vault/programs/incremental-cognition/gen2/evidence/champion/run6-r4-population.log
    - vault/programs/incremental-cognition/gen2/evidence/champion/gex44_ic_rows.sh
  modified:
    - vault/programs/incremental-cognition/gen2/ledger.json
    - tools/ic_gen2.py
    - tools/test_incremental_cognition_program.py
key-decisions:
  - "G2-CHAMP compares run6's command with the runner's own run_step line by argv equality (shlex), $ROOT/$PF expanded from the runner's assignments and the interpreter taken from `python3 \"$@\"`, so quoting in the ledger command is free and a dropped flag is caught"
  - "Side lifecycle states are terminal for forward steps (only another side state may follow one); the plan said a side state may follow any state and was silent after"
  - "A7 treats FROZEN_AT present with no freeze-audit.md as FAIL (an unaudited freeze); the plan only specified the both-exist and FROZEN_AT-absent cases"
  - "g2_champ and g2_opp take the resolver (res) as second argument, not a root, so the selftest can serve altered evidence text"
requirements-completed: [AO-02]
duration: ~40 min (estimated; start time was not recorded)
completed: 2026-10-06
status: complete
commits: 3
plan_head_before: 4affefdad13f1b0fca8368678b019b80a72c4a01
actuals:
  tokens: 10990
  tasks: 3
  commits: 3
---

# Phase 0 Plan 04: Champion freeze, OPP-001 and the audit gate Summary

**The Run 5 / Run 6 champion numbers are frozen in the IC-gen2 ledger with pinned byte copies of their evidence and re-parsed on every run by G2-CHAMP; OPP-001 is the first opportunity row (priced, nothing realized) guarded by G2-OPP; and `--generation 2 --audit` (A1-A7) prints `ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d8...` pre-freeze. Plane: gex44. The ledger is still a DRAFT: FROZEN_AT is plan 00-05's.**

## Performance

- Tasks: 3 of 3 complete (task 1 tracer, tasks 2 and 3 auto/tdd); 3 task commits, the SUMMARY commit follows this file
- Files: 5 created, 3 modified; `git diff --shortstat 4affefda HEAD` before this file: 8 files changed, 937 insertions(+), 6 deletions(-)
- `actuals.tokens` is chars/4 over the code and ledger diff only (43961 chars); the five evidence copies are excluded

## Accomplishments

- Evidence copied with `cp --preserve=timestamps`; sha256 of the copies: run5-summary `a91bcbd4...`, run6-summary `75e10e10...`, runner `151338ea...` (the three pinned by the plan, all matched before copying), run5 log `6fbbb679...`, run6 log `725d2ab4...` (the plan gave no pin for this one; measured at copy time, size 1336 B as planned). Secret firewall `scan_file` on every copy: `is_critical` False, `no secrets detected` for all five.
- `frozen.champion`: run5 (unscoped, 869 s, 101.53 GB, exit 3, drifted, 10 locator scans, command `reconstructed` with a provenance note naming both sources and the overwritten runner) and run6 (scoped, 24 s, 2.83 GB, exit 0, exact, nine steps from the summary including `r4-d-w7` exit 3, command `runner-script`, `runner_line` 36); `ratios_derived` wall 36.2, read_GB 35.9 (recomputed: 869/24 = 36.2, 101.53/2.83 = 35.9).
- G2-CHAMP re-derives every scalar, the START line (head, started, project_filter, corpus_root), the population log fields, run6 `steps` and the runner argv from the copies, plus both sha pins, the evidence directory, the provenance tags and `ratios_derived`.
- OPP-001 row with all 25 keys, status priced, history [observed, priced], `realized_dividend` null, evidence = the OPP-001 file (sha256 pinned) plus fix commits `ea8c51f6`, `62152c0b`, `21bafb5d` (the three in the evidence file's front matter; the docs commit `14e7518a` is not a fix). Cost fields carry the evidence file's measured numbers and commands.
- G2-OPP: id format and uniqueness, status vocabulary, one-position forward steps, history starts `observed` and ends at status, realized only for certified/promoted/retired with value, unit, denominator and an existing measurement, predicted needs value and unit and may not say "realized", file evidence re-hashed, commit evidence reachable from HEAD.
- Audit A1-A7 over the real ledger (output below). `frozen_sha256` canonical form per plan; `roadmap_phase_map` read M[4,6] O[1] P[2,6] Q[3] R[5,6] from the live ROADMAP, equal to every pillar's `roadmap_phases`.

## Task Commits

| Task | Commit | Subject |
|---|---|---|
| 1 (tracer) | 598c30c3 | feat(00-04): IC-gen2 champion Run 5 / Run 6 frozen with pinned evidence + G2-CHAMP |
| 2 (tdd) | 96d98522 | feat(00-04): OPP-001 opportunity row + G2-OPP lifecycle and dividend rules |
| 3 (tdd) | 81279478 | feat(00-04): IC-gen2 --audit mode (A1-A7) gating the pre-registration freeze |

Tracer gate: after task 1, `--generation 2 --status` (violations empty), `--generation 2 --selftest` (PASS, `V-IC2-MUT-run5-provenance-verbatim killed by G2-CHAMP` present) and the five-file secret scan (5, []) all passed before task 2 started. Tracer verified end-to-end, expanding.

## Verification Observed (plane: gex44, HEAD 81279478, each in a fresh process)

- `--generation 2 --status` -> `{"open": ["M", "O", "P", "Q", "R"], "closed": [], "violations": []}`, exit 0.
- `--generation 2 --selftest` -> `ICP_GEN2_SELFTEST=PASS`, exit 0; 11 lines `killed by G2-CHAMP`, 14 `killed by G2-OPP`, 12 `killed by A<n>`, no SURVIVED or FAIL line; controls `V-IC2-OPP-CERTIFIED-ACCEPTED`, `V-IC2-AUDIT-CLEAN`, `V-IC2-AUDIT-FROZEN-RECORD-ACCEPTED`, `V-IC2-AUDIT-EXPECTED-SET` all ok.
- `--generation 2 --audit` exit 0:
  ```
  A1 ok status problems empty (CE L1-L9/X under the gen2 binding + G2 rules)
  A2 ok gen2 selftest passes
  A3 ok final-mode failure set equals the expected open-programme set (10 lines, pre-freeze)
  A4 ok roadmap_phases equal the ROADMAP checklist: M[4, 6], O[1], P[2, 6], Q[3], R[5, 6]
  A5 ok 10 frozen owner paths tracked
  A6 ok 79 gen2-authored frozen strings carry no deferral word and no placeholder
  A7 ok (not frozen yet)
  ICP_GEN2_AUDIT=PASS frozen_sha256=a8ac15d894a72c74eb71901b3081c7a6a20a0ee2d9da085a270dd015a204d39e
  ```
  No A-rule failed on the real ledger, so no ledger fix was needed for the audit. Note: the sha is of `frozen` as of HEAD 81279478; plan 00-05 must re-run the audit after any further `frozen` edit.
- `--selftest` (wrapper) -> `CEP_SELFTEST=PASS`, `ICP_GEN2_SELFTEST=PASS`, `ICP_SELFTEST=PASS`, exit 0.
- `--generation 2 --final` -> exactly 10 FAIL lines (L2 not frozen, L3 for M/O/P/Q/R, four L8) and `ICP_GEN2_VERDICT=FAIL failures=10`. Pre-freeze red, reported verbatim, not a pass.
- Acceptance one-liners: champion assertion `ok`; opportunities assertion `ok` and `'opportunities' not in frozen`; `sha256sum` of the three pinned copies equals the planned values; `test ! -e gen2/FROZEN_AT` true.
- `git diff --quiet 3f48f2e3 HEAD -- vault/programs/incremental-cognition/ledger.json vault/programs/incremental-cognition/FROZEN_AT tools/test_cognitive_economy_program.py tools/test_skill_capability_program.py .planning/STATE.md tools/gsd_mission.py` exit 0.
- `git rev-list --count 4affefda..HEAD` = 3 before this file.

## TDD record

- Task 2 RED (committed nowhere): 14 `opp-*` mutants against `g2_opp` returning `[]` all printed `SURVIVED (expected a G2-OPP line, got [])`, `ICP_GEN2_SELFTEST=FAIL`; the certified-row control passed (an empty rule accepts it). After the rule, 14 of 14 killed.
- Task 3 RED: with `ic_gen2.audit_rules` monkeypatched to return all-pass, the selftest printed 12 `SURVIVED` lines (A1, A2, A3 x2, A4 x2, A5, A6 x3, A7 x2) and the three controls passed; with the real rules 12 of 12 killed.
- Task 1 is a tracer (no TDD flag); its mutants were killed on the first green run, behind the clean control `V-IC2-CLEAN`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Mutant names briefly lost their `champ-` disambiguation**
- **Found during:** Task 1 (renaming mutants to the plan's names with `sed 's/mut("champ-/mut("/'`)
- **Issue:** the sed also stripped the prefix from `champ-missing` and `champ-evidence-outside-dir`, which would have read as unrelated labels.
- **Fix:** renamed them `champion-missing` and `champion-evidence-outside-dir`; the plan's seven names are exactly as planned.
- **Files modified:** tools/ic_gen2.py
- **Commit:** 598c30c3 (fixed before the commit)

### Other departures (additions, not failures)

- **More mutants than the plan lists:** G2-CHAMP 11 (plan 7), G2-OPP 14 (plan 10), audit 12 (plan 6), because each extra rule I added (ratios, command argv, directory, key set, side-state order, A2, A1, A7 missing record) needs a mutant under the "every rule has a mutant" criterion. Acceptance counts are lower bounds ("at least ten", "six").
- **A7 missing-record case and side-state rule** are design choices recorded in `key-decisions`; they refuse more than the plan text and can only matter at the freeze, so plan 00-05 should read them before writing its record.
- **Signature:** `g2_champ(led, res)` / `g2_opp(led, res)` take the resolver, not a root.
- The scratch scripts `/tmp/ic00_04_champ.py` and `/tmp/ic00_04_opp.py` produced the ledger edits outside the repo (the host guard refuses heredocs); the ledger itself is the artifact and G2-CHAMP/G2-OPP re-derive it, so the scripts are not needed later.

**Total deviations:** 1 auto-fixed (Rule 3, caught before commit) plus the additions above. **Impact:** none on outcomes; stricter than the plan in three places, all documented.

## Authentication Gates

None.

## Known Stubs

None. `opportunities[0].realized_dividend` is null by design (priced, not certified), `next_transition` names the canary that would change that; the live GEX44 install's effect stays UNMEASURED until its normal fast-forward sync.

## Threat Flags

None. No new endpoint or auth path. T-00-17: all five copies scanned, no CRITICAL hit, files hold counts and project directory names only. T-00-18/19/20/21: each has mutants (flipped sha, altered summary text, run5 provenance `runner-script`, realized-while-priced and predicted-says-realized, pillar O phases `[2]`, TBD, later).

## Issues Encountered

- The plan's `<action>` for G2-CHAMP says the run6 `command` must "occur in" the runner line expansion; I used argv equality instead (see key-decisions), which also lets the ledger quote `'KobiiCraft-Core-Files|kme-wt-arena2'` as a shell would.
- Inherited reds are unchanged and reported verbatim: IC gen1 `--final` L3/L8 lines (not re-run here; no gen1 file was touched, diff check above) and the ten pre-freeze gen2 `--final` lines.
- `PP-install` and gen1 suites other than the IC wrapper `--selftest` were not re-run: nothing in this plan touches them.

## Next Phase Readiness

Plan 00-05 can run `--generation 2 --audit` (currently PASS with the sha above), write `freeze-audit.md` containing exactly one `ICP_GEN2_AUDIT=PASS frozen_sha256=<hex>` line, commit it with the ledger as commit A, then write `FROZEN_AT` alone as commit B. After B, A7 compares the recorded sha with the live one; A3 then expects the final set without L2 (9 lines). Anything in `frozen` edited after the audit record changes the sha and fails A7.

## Self-Check

- Created files present: the five evidence copies (sha256sum run above), `tools/ic_gen2.py`, `vault/programs/incremental-cognition/gen2/ledger.json`.
- Commits `598c30c3`, `96d98522`, `81279478` are on `mission/autonomous-optimization-gen2`; subjects verified with `git log`.
- All task acceptance criteria and the plan-level verification commands were re-run after the last commit (see Verification Observed).

## Self-Check: PASSED
