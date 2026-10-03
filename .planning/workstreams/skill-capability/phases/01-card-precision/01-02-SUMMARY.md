---
phase: 01-card-precision
plan: 02
subsystem: hooks/doctrine-card
tags: [doctrine-card, git-exit-128, root-cause, hermetic-tests, empty-tree]
requires: ["01-01"]
provides:
  - "classifyGitError(stderr) and ledger field git_error (enum only) on every numeric non-zero git exit of the commit card"
  - "first commit of a repo judged against the empty tree (ledger field base: empty-tree) instead of ending as a git-128 unknown"
  - "capsule-guard test hermetic (private DOCTRINE_CARDS_STATE_DIR) plus a discovered-population sweep with floor and drill"
  - "pillar A gate tools/test_card_precision.py SCA_PASS=36/36 on gex44"
affects: [hooks/doctrine_cards.js, hooks/capsule_mutation_guard.js]
tech-stack:
  added: []
  patterns: ["stderr class enum in the ledger, never raw stderr", "population discovered by an independent marker, floor + drill", "real git stderr captured in the gate and classified by the card's own function through node"]
key-files:
  created: []
  modified:
    - hooks/doctrine_cards.js
    - hooks/tests/test-doctrine-cards.js
    - hooks/tests/test-capsule-mutation-guard.js
    - hooks/capsule_mutation_guard.js
    - tools/test_card_precision.py
decisions:
  - "Classifier also names the `usage: git diff --no-index` banner as not_a_repo: git 2.43 exits 129 (not 128) outside a repo and `diff --cached` prints no 'not a git repository' text"
  - "Dubious ownership is reported NOT-REPRODUCED on gex44 (the git test seam yields exit 129 with no dubious text), never as reproduced"
  - "capsule_mutation_guard.js unwrapCall uses path.win32.basename (separate commit, pre-existing POSIX-only defect that kept the capsule suite at 17/18)"
requirements: [SC-A]
metrics:
  duration: "about 8 min wall clock (start 16:39Z, SUMMARY write 16:47Z host clock)"
  completed: 2026-10-03
status: complete
actuals:
  tokens: 7000    # approx chars/4 over the authored diff (334 inserted lines, no fixtures); estimated, not counted exactly
  tasks: 3
  commits: 4      # MEASURED: git rev-list --count 0eb6f08f..HEAD at SUMMARY write (excludes this SUMMARY's own commit)
plan_head_before: 0eb6f08f70a51486982a14391437861c01939e95
---

# Phase 1 Plan 02: Git exit 128 root cause Summary

The commit card now records the stderr class of every git failure (`git_error`), judges the first commit of a repo against the empty tree, and the capsule-guard test that wrote the 3 `abcd1234` rows into the live ledger writes into its own temp dir.

## Observed gate output (host kobicraft-gex44, git 2.43.0, node 18, python3)

`python3 tools/test_card_precision.py` -> rc 0, `SCA_PASS=36/36` (was 27/27 after plan 01-01). Verbatim:

```
ok   V-SCA-128-ROWS-SPLIT: 6 = abcd1234 x3 (index) + fce2689e x3 (only-paths)
ok   V-SCA-128-CANNOT-CHDIR-abcd1234: denied=False decision=unknown reason='git exit 128' basis=index git_error=cannot_chdir
INFO git=git version 2.43.0 host=kobicraft-gex44
ok   V-SCA-128-NOT-A-REPO: index: decision=unknown reason='git exit 129' basis=index git_error=not_a_repo | pathspec: decision=unknown reason='git exit 129' basis=only-paths git_error=not_a_repo (observed on this git: outside a repo `git diff` exits 129 via --no-index, not 128)
ok   V-SCA-128-OUTSIDE-REPO: decision=unknown reason='git exit 128' basis=only-paths git_error=outside_repo
ok   V-SCA-128-UNBORN-HEAD-CLASSIFIED: real git rc=128 stderr="fatal: bad revision 'HEAD'" -> unborn_head
ok   V-SCA-UNBORN-HEAD-JUDGED: denied=True decision=deny-card reason=None basis=only-paths git_error=None base=empty-tree
NOT-REPRODUCED V-SCA-128-DUBIOUS-OWNERSHIP host=kobicraft-gex44: decision=unknown reason='git exit 129' basis=index git_error=not_a_repo (git test seam GIT_TEST_ASSUME_DIFFERENT_OWNER did not produce the dubious-ownership stderr here)
INFO fce2689e: pack tool_calls=97 first_start=2026-10-03T08:41:10.845Z last_start=2026-10-03T15:09:37.415Z rows=['2026-10-03T14:12:55.252Z', '2026-10-03T14:13:41.324Z', '2026-10-03T14:16:04.817Z'] calls_in_120s_before_row=0,0,0 (the exact command is not in the pack and cannot be reproduced from it)
D-CARD unknown_git_exit_128=6: abcd1234 x3 -> cannot_chdir (reproduced; capsule-guard e2e ran the card without a private state dir); fce2689e x3 -> cause not recoverable from the pack (rows carry no stderr; calls_in_window=0,0,0); classes now recorded per row: git_error
ok   V-SCA-NODE-CAPSULE-GUARD: rc=0 last='CMG_PASS=18/18  threshold=18/18' (run without --e2e: ...)
ok   V-SCA-STATE-DIR-SWEEP: population=['test-capsule-mutation-guard.js', 'test-doctrine-cards.js'] without_private_state_dir=[] floor=2
ok   V-SCA-STATE-DIR-DRILL: stripped copy flagged=['test-capsule-mutation-guard.js'] (population ['test-capsule-mutation-guard.js']); unmodified copy flagged=[]
SCA_PASS=36/36
```

Node suites at the end: `DOCTRINE_CARDS_PASS=34/34` (was 30/30), `DDC_PASS=15/15`, `CMG_PASS=18/18  threshold=18/18`. All plan-01-01 checks still `ok`.

## Exact stderr git 2.43 printed on gex44, per class

| class | command shape (card's own args) | rc | stderr (first line) |
|---|---|---|---|
| cannot_chdir | `git -C C:\proj diff --cached` | 128 | `fatal: cannot change to 'C:\proj': No such file or directory` |
| not_a_repo | `diff HEAD -- f` in an empty dir (GIT_CEILING_DIRECTORIES set) | **129** | `warning: Not a git repository. Use --no-index to compare two paths outside a working tree` then the `usage: git diff --no-index` banner |
| not_a_repo | `diff --cached` in an empty dir | **129** | `error: unknown option `cached'` then the `usage: git diff --no-index` banner (no "not a git repository" text at all) |
| unborn_head | `diff HEAD -- f` in a repo with no commit | 128 | `fatal: bad revision 'HEAD'` |
| outside_repo | `diff HEAD -- <abs path of another dir>` in a repo with a commit | 128 | `fatal: <path>: '<path>' is outside repository at '<repo>'` |
| dubious_ownership | `GIT_TEST_ASSUME_DIFFERENT_OWNER=1`, `diff --cached` | **129** | the no-index usage banner; no text containing "dubious" |

(`rev-parse --show-toplevel` in the empty dir does print `fatal: not a git repository (or any of the parent directories): .git` with 128, but the card's diff is what fails first.)

## Task log

### Task 1 (tracer) - commit 71cd35e0
- `classifyGitError` (pure, exported), `git_error` on rows with a numeric non-zero status only (timeout/ENOENT rows keep their code and get none), header sentence, gate `run_card(..., extra_env=)` (state dir always wins), `V-SCA-128-ROWS-SPLIT`, `V-SCA-128-CANNOT-CHDIR-abcd1234`.
- The abcd1234 shape reproduces exactly on gex44 with the capsule e2e payload: `git exit 128`, basis index, `cannot_chdir`.
- Tracer gate: the plan's `<verify>` re-run before expanding: rc 0, `SCA_PASS=29/29`. `grep -c git_error hooks/doctrine_cards.js` = 3; `grep -n "stderr:" hooks/doctrine_cards.js` printed nothing.

### Task 2 (tdd) - commit 9db76722
- Red observation, run before the fallback existed (node block 12 against the Task 1 card): `FAIL V-DC-UNBORN-HEAD: denied=false decision=unknown base=undefined reason=git exit 128 git_error=unborn_head`, `DOCTRINE_CARDS_PASS=33/34`. V-DC-GIT-CLASSES passed already (the classifier existed from Task 1).
- Green after the fallback: `PASS V-DC-UNBORN-HEAD: denied=true decision=deny-card base=empty-tree`, `DOCTRINE_CARDS_PASS=34/34`.
- Fallback: on a numeric non-zero exit with args[1] `HEAD` and class `unborn_head`, one bounded `hash-object -t tree --stdin` (stdin `''`, no /dev/null), then the diff re-run with HEAD replaced by that oid; row gets `base: empty-tree`. `spawnGit(full, input)` stays the single spawn site. If either spawn fails the original failure row is written unchanged.
- Gate: `V-SCA-128-NOT-A-REPO`, `-OUTSIDE-REPO`, `-UNBORN-HEAD-CLASSIFIED` (real stderr captured by the gate, classified by the card's function through `node -e`), `V-SCA-UNBORN-HEAD-JUDGED`, `V-SCA-128-DUBIOUS-OWNERSHIP` (NOT-REPRODUCED line), `INFO fce2689e`, the single `D-CARD unknown_git_exit_128=6:` line (printed only if all 128 checks passed).

### Task 3 - commits eadc0fd5 (platform fix, see deviations) and 4ed37f5d
- `DOCTRINE_CARDS_STATE_DIR: path.join(TMP, 'doctrine-cards')` in the capsule test's `ENV`; `git diff --stat` for that file: 1 file, 2 insertions, 1 deletion.
- `V-SCA-NODE-CAPSULE-GUARD` (without --e2e; the dispatcher's `../skills/claude-power-pack/hooks/doctrine_cards.js` does not exist on this host or in this repo, checked with `ls`), `V-SCA-STATE-DIR-SWEEP` (population measured by `grep -lE` and again by the gate: exactly 2 members), `V-SCA-STATE-DIR-DRILL` (stripped copy flagged, unmodified copy not flagged).
- Plan-time population of five files that mention the card or a dispatcher shrinks to two once the commit-literal marker is required (test-wrapper-selfheal.js, test-scratchpad-fast-path.js, test-destructive-doctrine-card.js carry no commit command). Re-measured, not trusted.

## What is and is not reproduced

- abcd1234 x3: reproduced as `cannot_chdir` from the capsule e2e payload; cause fixed (private state dir). The e2e section itself cannot run on gex44 (card path of the dispatcher), so the "no longer writes the live ledger" claim rests on ENV carrying the dir and the sweep/drill, not on an observed e2e run here.
- fce2689e x3: cause not recoverable from the pack (rows carry no stderr; 0 pack tool_calls in the 120 s before each row, matching the orchestrator's read of none between 14:10 and 14:17Z). Future rows carry the class. The unborn-HEAD case, one of the possible causes (basis only-paths is `diff HEAD -- paths`), is now fixed rather than named.
- dubious_ownership: not reproduced on gex44 (test seam gives 129, no dubious text). The classifier handles the documented git text (`V-DC-GIT-DUBIOUS-TEXT`, a synthetic string, labelled as such) but no real git output produced it here. Aperture worth knowing: on 2.43 a dubious-ownership repo under `git diff` appears to degrade to the non-repo path, so the card would likely record `not_a_repo` for it.
- `not_a_repo` and the seam-induced case exit **129**, not 128, on this git. The plan assumed 128; expectation adjusted to the observation (the gate asserts the class and prints the observed status).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] classifier missed `diff --cached` outside a repo**
- **Found during:** Task 1 probing (real git, before writing the classifier into the card).
- **Issue:** the plan's regex list classifies by "not a git repository", but git 2.43 `diff --cached` outside a repo prints only `unknown option cached` plus the no-index usage banner, exit 129, so the index basis would have been `other`.
- **Fix:** added `usage: git diff --no-index` -> `not_a_repo` after the explicit text check. Order otherwise as in the plan.
- **Files modified:** hooks/doctrine_cards.js
- **Commit:** 71cd35e0

**2. [Rule 3 - Blocking] capsule suite failed 17/18 on gex44 before and without this plan's change**
- **Found during:** Task 3 first gate run (`V-SCA-NODE-CAPSULE-GUARD` FAIL, `CMG_PASS=17/18`).
- **Issue:** `V-CMG-JUDGE` case `& 'C:\Program Files\Git\cmd\git.exe' -C 'C:\w' log --oneline -3` judged not-allowed. `unwrapCall` used the host `path.basename`, which on POSIX leaves a Windows path whole. Confirmed pre-existing by running `git show HEAD:` of the test (before my edit) copied into hooks/tests/: same `17/18`, then deleted the copy.
- **Fix:** one token, `path.win32.basename` (identical on Windows, handles both separators). Own commit so it reverts independently. It is outside the plan's `files_modified`; taken as Rule 3 because the plan's own check and the SC-A closure gate need a green capsule suite. Flag for review: this is a live enforcement hook on the laptop.
- **Files modified:** hooks/capsule_mutation_guard.js
- **Commit:** eadc0fd5

### Plan-directed host adaptations (not behavioral deviations)
- Pre-commit HEAD assertion: branch `mission/skill-capability-run` in a worktree is outside the `agent-*` allow-list; the orchestrator resolved isolation to `none` and directed work here. Commits pathspec-scoped, `git log -1 --format=%s` matched after each.
- `GIT_TEST_ASSUME_DIFFERENT_OWNER`: honoured as the plan's NOT-REPRODUCED branch.

## Known Stubs

None.

## Threat Flags

None new. T-01-06 held (only the enum is stored; `grep -n "stderr:" hooks/doctrine_cards.js` empty; node `V-DC-GIT-ERROR-NO-RAW-STDERR`). T-01-07 mitigated (private dir + sweep + drill). T-01-08/09: the fallback adds one bounded `hash-object` (no `-w`) and one diff, only on the unborn-HEAD failure.

## Self-Check: PASSED

All 5 modified source files and this SUMMARY present on disk (`ls -l`); commits 71cd35e0, 9db76722, eadc0fd5, 4ed37f5d present in `git log --oneline -5`.
