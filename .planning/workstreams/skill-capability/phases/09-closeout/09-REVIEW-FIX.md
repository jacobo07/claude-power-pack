---
phase: 09-closeout
fixed_at: 2026-10-04T00:38:59Z
review_path: .planning/workstreams/skill-capability/phases/09-closeout/09-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 6
skipped: 1
status: all_fixed
---

# Phase 09: Code Review Fix Report

**Fixed at:** 2026-10-04T00:38:59Z
**Source review:** .planning/workstreams/skill-capability/phases/09-closeout/09-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (CR-01, WR-01..04, IN-01, IN-02)
- Fixed: 6 (CR-01, WR-01, WR-02, WR-03, WR-04, IN-01)
- Skipped: 1 (IN-02, which has nothing to fix)
- Status is `all_fixed` because every finding that has a defect is fixed. IN-02 has none.

**Where verification ran.** Unit gates and final checks ran in the main worktree
`/home/kobii/missions/skill-capability/.claude/worktrees/sc-run`, on committed blobs. No nested worktree was
created, as the caller instructed. Every laptop-plane check ran in a throwaway clone under
`/home/kobii/.claude/jobs/06c5c0e4/tmp/p9fix/`. Those clones have a full `core.autocrlf=true` checkout and were
cloned from this branch's HEAD. state.N was written and `--final` was run only inside those clones, never in the
worktree. Nothing was pushed.

## Fixed Issues

### CR-01: On a core.autocrlf=true clone `--final` fails L5 J

**Files modified:** `tools/test_skill_creation_gate.py`
**Commit:** dbc76d19
**Applied fix:**
- `build_base` now goes through `skills_archive()`, which runs
  `git -c core.autocrlf=false -c core.eol=lf archive ...`, so its members are the committed blob bytes whatever the
  clone's config is.
- `undeclared()` now strips the declaration from a text whose line endings are all CRLF. It works on the LF form and
  hands the text back CRLF, the way `insert_declaration` does. Mixed and lone-CR texts are still left alone.
- New in-suite drill `V-SCG-AUTOCRLF-PLANE`. It clones this repo with `--shared --no-checkout` and sets
  `core.autocrlf=true`.
  - Positive control: a plain archive there is CRLF on 24/24 SKILL.md.
  - The pinned archive equals the checkout's archive and the HEAD blobs on 24/24.
  - Each CRLF text is stripped and re-declared, 24/24, and its result equals the LF insert.
- Red drive: both mutants turn the drill red.
  - "undeclared bails on CR" fails with the original `ValueError: frontmatter already has a metadata key`.
  - "archive unpinned" fails because the pinned archive matches HEAD on only 0/24.
- **CRLF sweep.** In a fresh `core.autocrlf=true` clone of dbc76d19, `--pillar A`..`--pillar M` all exited rc 0 with
  `CEP_PILLAR_<P>=PASS`. Every gate argv those pillars invoke (A `test_card_precision`, C `test_skill_delivery`,
  D `test_skill_coverage`, F `test_skill_representation`, G `test_card_lineage`, H `test_skill_drift`,
  J `test_skill_creation_gate`) was also run directly in that clone, and each exited rc 0. No other CRLF failure was
  found, so no other gate needed a fix.
- LAPTOP-CLOSEOUT step 9's expected text ("`SCP_VERDICT=PASS`; if R1 fails ...") is now accurate as written. The
  acceptance run below shows R1 as the only failure.

### WR-01: `--closeout` dropped the ledger invariant, so emptying `retained` passed

**Files modified:** `tools/test_skill_capability_prefinal.py`, `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md`
**Commit:** 0cabe6e0
**Applied fix:**
- `check_invariant(..., allow_state_n=False)`. A shared `_judge_invariant` runs `V-PF-LEDGER-INVARIANT` in both
  modes, and closeout mode relaxes only the state.N clause.
- The selftest fixture's `retained.keys` is now non-empty. There is a new green control (closeout with state.N
  written) and a red mutant, "closeout: retained emptied (WR-01)", which must name `'retained'`.
- LAPTOP-CLOSEOUT step 9 no longer offers re-declaring `retained` as a closeout remedy. It now says such a ledger
  turns `--closeout` red and needs its own reviewed change.
- Repro without any reset, `p9fix/repro_wr01_v2.sh` (autocrlf clone):
  - state.N only gives `PF_VERDICT=PASS`.
  - state.N plus `retained.settings.keys=[]` gives `FAIL V-PF-LEDGER-INVARIANT: ledger key 'retained' differs`, and
    the script exits 0.

### WR-02: The boundary-4 check could not be satisfied, and the push was never specified

**Files modified:** `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md`
**Commit:** 8371bc84
**Applied fix:**
- Section 1, laptop side:
  - Run `git rev-parse FETCH_HEAD` after the fetch and record the result as `<run-tip>`. A hash survives the later
    fetch in bundle item 6. The name `FETCH_HEAD` does not.
  - Foreign commits are defined against the push target. Immediately before pushing, run
    `git fetch <gex44-remote> mission/skill-capability`, then `git log --oneline HEAD --not <run-tip> FETCH_HEAD`. That
    log must list only this closeout's own commits: state.N, CLOSE.md and bundle-item commits.
  - A second, path-limited log (`-- . ":(exclude)vault/programs/skill-capability"`) is expected to be empty.
  - The push command is named: `git push <gex44-remote> HEAD:mission/skill-capability`, never forced. If it is
    refused as non-fast-forward, re-fetch and run both checks again.
- gex44 side: an ancestor check plus a log of the commits being pushed now run before the gex44 push. That push is
  stated exempt because it is a fast-forward of a branch that holds only the run's own commits.
- Step 11 repeats the check and the push. It also adds `git add` for CLOSE.md: a new file cannot be committed by
  pathspec alone.
- `p9fix/repro_wr02_v2.sh` exits 0. It builds a bare repo standing in for the gex44 one, then a laptop clone with
  autocrlf, then commits state.N and CLOSE.md.
  - The first log is exactly those two commits, and the second log is empty.
  - `git push --dry-run` is accepted.
  - A foreign peer commit to `hooks/doctrine_cards.js` is caught by both logs.
- The reviewer's original repro tests the removed `FETCH_HEAD..HEAD` command, so it still exits 1 by construction.

### WR-03: "on committed blobs" was overstated

**Files modified:** `tools/test_skill_capability_prefinal.py`, `vault/programs/skill-capability/LAPTOP-CLOSEOUT.md`
**Commit:** 85555abe
**Applied fix (widened, not narrowed):**
- `V-PF-COMMITTED` and `V-PF-DIRTY-SET-STABLE` now read `git status --porcelain --untracked-files=all` over the
  whole tree.
- They tolerate only an explicit `HOOK_STUB_PATHS` list: `vault/progress.md`, `.gsd/`, `docs/arch/`,
  `docs/changelog/`, `docs/constitution/` and `docs/prd/`. Every other dirty or untracked path, anywhere, makes the
  check INCONCLUSIVE.
- Selftest: one green (stubs only) and three red mutants (dirty hook, untracked skill file, a `docs/` path outside
  the list). Each mutant must name its path.
- LAPTOP-CLOSEOUT line 6 now says what "on committed blobs" measured.
- Ledger `deltas.product[13]` ("on committed blobs") was left unchanged. After the widening it describes what the
  re-recorded gex44 run measured. No ledger edit was needed.
- `p9fix/repro_wr03_v2.sh` exits 0: a clean tree with stubs gives `[]`, and both the dirty
  `hooks/doctrine_cards.js` and an untracked `skills/zz-new/SKILL.md` are seen.

### WR-04: 17 clauses had no red mutant of their own

**Files modified:** `tools/test_skill_capability_prefinal.py`
**Commit:** e875c052
**Applied fix:**
- `mutant(name, fn, expect=None)` counts a mutant as killed only when one of its problems contains `expect`, so the
  clause under test is the one that said no.
- There are 20 new per-clause mutants:
  - the record's host, date, command, PF_MODE, PF_TERMINAL, PF_OPEN and N-PASS lines;
  - COMMANDS without `CLOSE.md`, without `state.N` and without the run branch, each separately, plus a
    `tools/../x.py` argv refused by CE;
  - CBR predicted, empty surprise and a no-path evidence cell;
  - UKDL without Trap and without Source;
  - DECISIONS without Options;
  - STATUS closed short by one;
  - N-OPEN rc 2;
  - DELTAS pillar Z.
- Clause-deletion survey `p9fix/repro_wr04_v2.py` (the reviewer's script, pointed at a fresh clone and extended with
  3 deletions for the new WR-01 and WR-03 clauses): 20/20 deletions killed, control killed, 0 survivors, exit 0.

### IN-01: git failures outside `rep.judge` crashed instead of reading INCONCLUSIVE

**Files modified:** `tools/test_skill_capability_prefinal.py`
**Commit:** d9e17fb8
**Applied fix:**
- The ledger, closeout and bundle reads moved into the judged callables. `ok_detail` may now be a callable, which is
  evaluated inside `judge`.
- A ledger read failure marks L8, CBR and DELTAS INCONCLUSIVE.
- `path_exists` raises `GitUnavailable` when HEAD does not resolve, instead of answering "absent".
- `judge` turns a `RuntimeError` (for example from `frozen_at_commit`) into a FAIL row with its message, not a
  traceback.
- Selftest drills:
  - git raising everywhere gives 8 INCONCLUSIVE rows and no traceback;
  - path_exists with git returning rc 128 raises;
  - RuntimeError gives a FAIL row.
- Red drive: the old `path_exists` makes the selftest FAIL (69/70), and the old `judge` lets the RuntimeError
  escape.

### Re-record of the gex44 pre-final evidence (09-03 D-03)

**Files modified:** `vault/programs/skill-capability/evidence/pre-final-gex44.md`
**Commit:** b712f2c1
- `python3 tools/test_skill_capability_prefinal.py --write-evidence` was run at d9e17fb8 on kobicraft-gex44. It gave
  `PF_VERDICT=PASS` 16/16, with the whole-tree V-PF-COMMITTED. The untracked report file was moved out of the tree
  for the run and moved back after.
- No ledger key pins this record's sha (0 occurrences). state.N pins it only at laptop time, in step 5.

## Skipped Issues

### IN-02: UKDL / CBR / deltas spot-check

**File:** `vault/programs/skill-capability/reviews/ukdl.md`, `reviews/cbr.md`, `ledger.json` `deltas`
**Reason:** there is nothing to fix. The reviewer found no unbacked claim. The one exception it named, the
"committed blobs" wording, is WR-03 and is fixed there.
**Original issue:** none.

## Final checks (worktree, committed blobs, HEAD b712f2c1)

```
$ python3 tools/test_skill_capability_prefinal.py
  (every V-PF-* line ok, including V-PF-COMMITTED "whole working tree clean except the hook-written stubs")
PF_TERMINAL=A,B,C,D,E,F,G,H,I,J,K,L,M
PF_OPEN=N (expected: state.N and --final are laptop-only)
PF_PASS=16/16
PF_FAILED=-
PF_VERDICT=PASS
rc=0
$ python3 tools/test_skill_capability_prefinal.py --selftest | tail -2
PF_SELFTEST_GREENS=24
PF_SELFTEST=PASS kills=70/70
$ python3 tools/test_skill_creation_gate.py | tail -1
SCG_PASS=49/49
$ --pillar A..M: CEP_PILLAR_A..M=PASS, each rc=0
```

## Acceptance: CRLF-clone laptop simulation (`p9fix/sim_laptop_final.sh`, clone of b712f2c1, core.autocrlf=true)

```
step 1 no output                     ok
step 2 SCP_SELFTEST=PASS             ok
step 3 open [N], violations []       ok
step 4 PF_FAILED=V-PF-L8 only (L3 N) ok
steps 5-7 state.N written (CRLF working file) and committed
step 8 PF_PASS=10/10 PF_VERDICT=PASS ok
step 9 re-run of step 1: no output   ok
J gate on this plane: SCG_PASS=49/49 (V-SCG-AUTOCRLF-PLANE PASS)
--final rc=1 (24s):
CEP_VERDICT=PASS failures=0
  FAIL R1 /skillOverrides: declared retained but absent
  FAIL R1 /env/CLAUDE_DOCTRINE_CARDS: declared retained but absent
SCP_VERDICT=FAIL failures=2
failures other than R1: []
SIM_LAPTOP_FINAL bad=0 final_rc=1
```

Every pillar A..N passes inside CE (`CEP_VERDICT=PASS failures=0`). R1 fails on gex44 because gex44's
`~/.claude/settings.json` lacks the two declared retained keys. gex44 is not the laptop, so this is the expected
host-specific result and says nothing about the laptop's R1.

---

_Fixed: 2026-10-04T00:38:59Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
