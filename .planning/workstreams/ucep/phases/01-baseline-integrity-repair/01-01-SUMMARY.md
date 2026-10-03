---
phase: 01-baseline-integrity-repair
plan: 01
subsystem: tower-baselines
tags: [ucep, tower, baselines, ratchet, gitattributes, red-harness]
requires: []
provides:
  - "vault/tower/baselines/** pinned text eol=lf; generation_sha256 hashes committed bytes in this worktree"
  - "tools/test_ucep_baseline_integrity.py: 12-gate RED instrument for ratchet attacks H1/H2/H3b"
affects: [01-03, 01-04, 01-05]
tech-stack:
  added: []
  patterns: ["attack gate paired with a control on a B0-only temp copy", "RED run recorded on unchanged code before the fix"]
key-files:
  created: [tools/test_ucep_baseline_integrity.py]
  modified: [.gitattributes]
decisions:
  - "Fix CRLF anchoring with a .gitattributes pin plus on-disk normalisation (not a code-level hash change); content hashes stay equal to the committed blobs"
  - "Re-stat the 5 normalised baseline paths with git update-index (metadata only) so status is clean without staging content"
metrics:
  duration: "about 25 minutes"
  completed: 2026-10-03
status: complete
commits: 2
plan_head_before: 07f04424919933fcbcf20e3896441f204e072219
requirements: [UCEP-01]
actuals:
  tokens: 3089    # chars/4: 11811 bytes test file + 547 bytes added to .gitattributes
  tasks: 2
  commits: 2
---

# Phase 1 Plan 1: LF-pin baseline generations and RED ratchet harness Summary

LF pin on `vault/tower/baselines/**` takes `test_tower_ratchet.py` from 20/21 to 21/21 with all five generation hashes equal to
their committed blobs, and a 12-gate harness shows (RED, unchanged ratchet) that all seven H1/H2/H3b attacks currently pass as
`ok=True` while the five controls hold: `UCEP_BASELINE_INTEGRITY_PASS=5/12`.

Commits (measured with `git rev-list --count 07f0442..HEAD` from the persisted ledger): `2f904f62` (Task 1), `acc61048` (Task 2).

Status: COMPLETE. Production Reality: OBSERVED (real commands, real exit codes, in this worktree; the harness runs against
a B0-only temp copy, so the real second generation is judged only by `test_tower_ratchet.py` V-TRAT-REAL-CHAINS).

## Environment notes

- PowerShell tool is DISABLED in this executor session. All commands ran through the Bash tool using the
  absolute `C:\Program Files\Git\cmd\git.exe` (autocrlf-aware build, not the Bash-PATH `/usr/bin/git`) and the
  absolute Python 3.12 interpreter, with the `# bash-safe` marker for the bridge guard. Python was run directly,
  never under `timeout`.
- Pinned root verified: `C:/Users/User/.claude/skills/claude-power-pack/.claude/worktrees/ucep`, branch `ucep/mission`.

## Task 1 (tracer): LF-pin baseline generations

### BASE and dirty-path SET (before)

BASE = `07f04424919933fcbcf20e3896441f204e072219`

Sorted `git status --porcelain` BEFORE (orchestrator-owned tracking files only, nothing under tower baselines):

```
 M .planning/workstreams/ucep/STATE.md
?? .gsd/
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/state.json
```

`git status --porcelain -- vault/tower/baselines` = empty. `git ls-files --eol -- vault/tower/baselines` BEFORE:

```
i/lf    w/crlf  attr/                 	vault/tower/baselines/kobiicraft_mode/B0.json
i/lf    w/crlf  attr/                 	vault/tower/baselines/persistent_state/B0.json
i/lf    w/crlf  attr/                 	vault/tower/baselines/web_surface/B0.json
i/lf    w/crlf  attr/                 	vault/tower/baselines/web_surface/B1.json
i/lf    w/crlf  attr/                 	vault/tower/baselines/wii_homebrew/B0.json
```

### BEFORE sha256 table (D-06; temp script under the jobs tmp dir, outside the repo, never committed; exit 0)

| file | blob (git show HEAD:) | raw disk (CRLF) | disk with CRLF->LF | blob == plan table | LF == blob |
|---|---|---|---|---|---|
| kobiicraft_mode/B0.json | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | c2ebd2567006784ea5510f376586a02ad8b9d5402d49e9396e131097fd5fe7af | 1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407 | True | True |
| persistent_state/B0.json | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | 62757541f34812961681eff73aae0538cb5dfaaa6ab79105347587ea5b5d60eb | bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64 | True | True |
| web_surface/B0.json | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | c5e9c67e861f255de5580992c19f09de24b6f1aa9031ddefa0aecbb6634d9d9e | 98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7 | True | True |
| web_surface/B1.json | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | 883d7918fc4c7b980020e53e3fc8b93f807aa920ec2e8a531f188d6b236f84f6 | 2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1 | True | True |
| wii_homebrew/B0.json | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | 1a73b1e83d0b054109fdf525ead742ec499a577adf5969852bcc743155bf7e30 | 2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd | True | True |

Precondition satisfied: no blob hash differs from the plan table and every LF-normalised disk hash equals its blob hash, so
normalising destroys no state.

### Actions and observed results

1. `.gitattributes`: appended a dated comment block (precedent wording of :22-27) and exactly one rule
   `vault/tower/baselines/** text eol=lf` (count in file = 1). File stays uniformly CRLF on disk (autocrlf), no mixed endings.
2. Guarded normalisation (temp script `ucep0101_norm.py normalise`, exit 0): all 5 files rewritten CRLF->LF in binary mode,
   each only after its LF-normalised hash was proven equal to its blob hash. No `git checkout --` used.
3. Index stat cache: `git status` kept listing the 5 files as ` M` even though their content equals HEAD
   (`git hash-object` == index oid == HEAD oid for all 5; `git diff --stat` empty). Cause: the index entry still
   recorded the CRLF file size, and git short-circuits a size mismatch as "modified" without comparing content;
   `update-index --refresh` therefore printed "needs update" and changed nothing. Fixed with
   `git update-index -- <the 5 paths>` (re-stat only). Verified afterwards: `git status --porcelain -- vault/tower/baselines`
   empty and `git diff --cached --stat -- vault/tower/baselines` empty (no staged content change).
4. Verification (plan `<verify>` commands):
   - `python tools/test_tower_ratchet.py`: exit 0, `PASS V-TRAT-REAL-CHAINS  4 real families verified clean`,
     last line `TOWER_RATCHET_PASS=21/21  threshold=21/21` (was 20/21 at HEAD per RESEARCH F1). Zero `FAIL` lines.
   - `git ls-files --eol -- vault/tower/baselines`: 5 lines, `crlf=0`, `attr/text eol=lf` x5 (exit 0 criterion):

     ```
     i/lf    w/lf    attr/text eol=lf      	vault/tower/baselines/kobiicraft_mode/B0.json
     i/lf    w/lf    attr/text eol=lf      	vault/tower/baselines/persistent_state/B0.json
     i/lf    w/lf    attr/text eol=lf      	vault/tower/baselines/web_surface/B0.json
     i/lf    w/lf    attr/text eol=lf      	vault/tower/baselines/web_surface/B1.json
     i/lf    w/lf    attr/text eol=lf      	vault/tower/baselines/wii_homebrew/B0.json
     ```

### AFTER sha256 (on-disk, `sha256sum`; equals the F0 blob column for all 5 -> D-06 immutability held)

```
1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407  kobiicraft_mode/B0.json
bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64  persistent_state/B0.json
98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7  web_surface/B0.json
2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1  web_surface/B1.json
2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd  wii_homebrew/B0.json
```

B0 and web_surface B1 content is unchanged; only the on-disk line endings differ from before (raw CRLF hashes in the BEFORE table).

### Commit

`2f904f62` `fix(ucep-01): pin tower baseline generations to LF so parent anchors hash committed bytes`
(pathspec `-- .gitattributes`; `git show --stat HEAD` lists only `.gitattributes`, 8 insertions; subject verified; no deletions).

### Dirty-path SET after Task 1

```
 M .planning/workstreams/ucep/STATE.md
?? .gsd/
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-01-SUMMARY.md
?? .planning/workstreams/ucep/state.json
```

Same as BEFORE plus this SUMMARY; `.gitattributes` is committed; no baseline path dirty.

## Task 2: RED harness `tools/test_ucep_baseline_integrity.py`

### What was built

12 gates (7 attacks + 5 controls) on a B0-ONLY temp copy of the real web_surface family (`shutil.copyfile` of `B0.json`
only; the real second generation is never read or copied, so the probe trap F3 cannot recur). All writes under
`tempfile.mkdtemp(prefix="ucep_bi_")`, removed in `finally`; HOME/USERPROFILE are pointed at a temp dir for the run
(hermetic HOME pattern of `tools/test_family_injection.py:79-84`) and restored afterwards. Diff kinds are string
literals and report fields are read with defaults, so the unchanged `ratchet.py` imports cleanly and the RED run fails
on predicates, not on crashes.

| gate | role | asserts (the fixed behaviour) |
|---|---|---|
| V-UCEP-H1-RAW | attack | withdrawal recorded with authority `x` -> `ok is False` |
| V-UCEP-H1-RAW-CONTROL | control | same withdrawal, reason + authority `Owner` -> ok |
| V-UCEP-H1-API | attack | `revert` and `promote` with authority `x` both raise `RatchetRefusal`, generations stay `[0]` |
| V-UCEP-H1-API-CONTROL | control | `revert` with `Owner (approved by ...)` -> generations `[0, 1]`, chain ok |
| V-UCEP-H2-WHY / -ORIGIN / -CLASS / -SCOPE | attacks | unrecorded edit -> not ok and `(id0, WHY_CHANGED / REANCHORED / CLASS_CHANGED / SCOPE_CHANGED)` regression |
| V-UCEP-H2-CONTROL | control | all four edits recorded (kind list + reason + `Owner`) -> ok |
| V-UCEP-H3B | attack | hollowed chain, B1 anchor removed -> not ok and `unanchored == [1]` |
| V-UCEP-H3B-CONTROL-TAMPER | control | same hollowing, anchor intact -> `tampered == [1]`, not ok (existing detection must stay) |
| V-UCEP-CLEAN-CONTROL | control | anchored B1 identical to B0 -> ok, no regressions, none unanchored |

### RED run (unfixed ratchet.py)

Run against the UNCHANGED `modules/tower/ratchet.py` (`git diff --quiet HEAD -- modules/tower/ratchet.py` rc=0).
Run twice: first with the file uncommitted (HEAD `2f904f62591057ca1bcd154e9907ad19d4933127`), then again from the
committed harness at HEAD `acc61048d320cfe3e764a90efd4499dfda5722e6`. Both runs are identical on stdout.
Command: `python tools/test_ucep_baseline_integrity.py` (run directly, no `timeout`). Result: `rc=1`.

Verbatim stdout (HEAD acc61048d320cfe3e764a90efd4499dfda5722e6, rc=1):

```
V-UCEP baseline integrity gates (B0-only copy of web_surface)
  FAIL V-UCEP-H1-RAW                          H1 attack accepted: {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [], 'ok': True}
  PASS V-UCEP-H1-RAW-CONTROL                  the same withdrawal with reason + authority 'Owner' is clean
  FAIL V-UCEP-H1-API                          H1 API attack accepted: revert refused=False promote refused=False generations=[0, 1, 2] (written: ['B1', 'B2']) missing_keys=[]
  PASS V-UCEP-H1-API-CONTROL                  revert with authority 'Owner (...)' writes B1 and the chain is ok
  FAIL V-UCEP-H2-WHY                          H2 attack accepted (want WHY_CHANGED): {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [], 'ok': True}
  FAIL V-UCEP-H2-ORIGIN                       H2 attack accepted (want REANCHORED): {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [], 'ok': True}
  FAIL V-UCEP-H2-CLASS                        H2 attack accepted (want CLASS_CHANGED): {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [], 'ok': True}
  FAIL V-UCEP-H2-SCOPE                        H2 attack accepted (want SCOPE_CHANGED): {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [], 'ok': True}
  PASS V-UCEP-H2-CONTROL                      the same four edits recorded with reason + authority are clean
  FAIL V-UCEP-H3B                             H3b attack accepted: {'family': 'web_surface', 'generations': [0, 1], 'regressions': [], 'tampered': [], 'unanchored': [1], 'ok': True}
  PASS V-UCEP-H3B-CONTROL-TAMPER              the same hollowing with the anchor intact reads TAMPERED at B1
  PASS V-UCEP-CLEAN-CONTROL                   an anchored B1 identical to B0 is clean; absent scope is not churn

UCEP_BASELINE_INTEGRITY_PASS=5/12  threshold=12/12
```

Plan `<verify>` predicate evaluated: `rc == 1`, FAIL lines = 7 (exactly V-UCEP-H1-RAW, H1-API, H2-WHY, H2-ORIGIN,
H2-CLASS, H2-SCOPE, H3B), `PASS V-UCEP-...CONTROL` lines = 5, line `UCEP_BASELINE_INTEGRITY_PASS=5/12` present -> VERIFY PASS.
Instrument reading: every attack returned `'ok': True` (or a successful write for H1-API) on the old code, so the holes are
real and the harness is not vacuous; every control held. A later green on this file is therefore evidence.
`git ls-files -- tools/test_ucep_baseline_integrity.py` lists it after the commit. The only `B1.json` mentions in the source
are the temp-root hand-edit loop in the H3b helper, never a path under `bl.BASELINES_DIR`.

### Commit

`acc61048` `test(ucep-01): RED harness for ratchet attacks H1/H2/H3b on a B0-only copy`
(`git add` of the single path, then `git commit -F <msgfile> -- tools/test_ucep_baseline_integrity.py`; 1 file, 279 insertions;
subject verified; no deletions).

## Plan-level verification

Run at HEAD `acc61048d320cfe3e764a90efd4499dfda5722e6`, each bracketed by the sorted dirty-path SET:

| command | exit | result |
|---|---|---|
| `python tools/test_tower_ratchet.py` | 0 | `TOWER_RATCHET_PASS=21/21  threshold=21/21` (V-TRAT-REAL-CHAINS PASS) |
| `python tools/test_tower_donegate.py` | 0 | `TOWER_DONEGATE_PASS=10/10  threshold=10/10` |
| `python tools/test_baseline_generations.py` | 1 | `BASELINE_GENERATIONS_PASS=15/16  threshold=16/16`; the only FAIL is `V-BGEN-REAL-B0-CITATIONS-HOLD` (the 9 QUOTE_MISSING entries, population=62), which plan 01-04 fixes - expected, not a regression of this plan |
| `python tools/test_ucep_baseline_integrity.py` | 1 | `UCEP_BASELINE_INTEGRITY_PASS=5/12` (intentional RED) |

Dirty-path SET before and after the whole run: identical (`dirty set identical`); final set is

```
 M .planning/workstreams/ucep/STATE.md
?? .gsd/
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-01-SUMMARY.md
?? .planning/workstreams/ucep/state.json
```

i.e. the BEFORE set (orchestrator-owned tracking files) plus this SUMMARY; the committed paths are `.gitattributes` and the new
test file. `git status --porcelain -- vault/tower/baselines` empty. On-disk sha256 of the 5 generation files re-checked after
Task 2 and equal to the F0 blob column. `modules/tower/ratchet.py` untouched. No write to the production ledger (HOME was
temp for the harness, which only writes under its temp root).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Index stat cache kept the normalised baselines "modified"**
- **Found during:** Task 1 step (e)
- **Issue:** After the CRLF->LF rewrite, `git status --porcelain -- vault/tower/baselines` listed all 5 files as ` M` although
  their content equals HEAD (`hash-object` == index oid == HEAD oid; `git diff --stat` empty). The index entry still recorded the
  CRLF file size; git treats a size mismatch as modified without comparing content, and `update-index --refresh` cannot clear it.
  The plan's acceptance criterion requires empty status.
- **Fix:** `git update-index -- <the 5 baseline paths>` (re-stat only, explicit paths). Verified `git status` empty and
  `git diff --cached --stat -- vault/tower/baselines` empty, so no content was staged and none is in any commit.
- **Files modified:** none (index metadata only)
- **Commit:** n/a (no tracked content change)

### Environment deviation (not a plan change)

PowerShell tool is disabled in this session; the plan's PowerShell verify commands were run through the Bash tool with
equivalent commands (absolute `git.exe` and `python.exe`; `sha256sum` instead of `Get-FileHash`; `grep -c` instead of
`Select-String`). Same predicates, same thresholds.

Otherwise: plan executed as written.

## Authentication gates

None.

## Known Stubs

None. Nothing in the harness or the attribute rule is deferred, hard-coded as a filler value, or left unwired for this
plan's scope.

## Threat Flags

None. No new network endpoint, auth path, file access beyond temp roots, or schema change at a trust boundary.
Threat register: T-01-01 mitigated (pin + normalisation verified by `ls-files --eol` and hash equality), T-01-02 mitigated
(rewrite only after LF hash == blob hash and clean status; B0 and web_surface B1 sha256 unchanged), T-01-03 mitigated (B0-only
copy, RED run recorded with HEAD, every attack paired with a control), T-01-04 mitigated (all writes under temp roots; dirty set
and baseline sha unchanged after the run).

## Self-Check

Files exist:
- FOUND: `.gitattributes` (rule line count 1)
- FOUND: `tools/test_ucep_baseline_integrity.py`
- FOUND: `.planning/workstreams/ucep/phases/01-baseline-integrity-repair/01-01-SUMMARY.md`

Commits exist (`git log --oneline` in the pinned worktree):
- FOUND: `2f904f62` fix(ucep-01): pin tower baseline generations to LF so parent anchors hash committed bytes
- FOUND: `acc61048` test(ucep-01): RED harness for ratchet attacks H1/H2/H3b on a B0-only copy

## Self-Check: PASSED

## Next

01-03 closes H1/H2/H3b in `modules/tower/ratchet.py` and flips the 7 attack gates of this harness; 01-04 adds
`ratchet.reanchor` and writes `persistent_state/B1.json` and `wii_homebrew/B1.json`, which is what takes
`test_baseline_generations.py` to 16/16. The LF pin from this plan is the precondition for those generation writes
(the new B1 anchors hash LF bytes).

