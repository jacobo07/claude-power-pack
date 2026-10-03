---
phase: 05-representation-operations
fixed_at: 2026-10-03
review_path: .planning/workstreams/skill-capability/phases/05-representation-operations/05-REVIEW.md
iteration: 1
findings_in_scope: 13
fixed: 12
skipped: 0
no_change_needed: 1
status: all_fixed
---

# Phase 5: Code Review Fix Report

**Fixed at:** 2026-10-03
**Source review:** `.planning/workstreams/skill-capability/phases/05-representation-operations/05-REVIEW.md`
**Iteration:** 1

Worktree sc-run, branch mission/skill-capability-run, host gex44, python3 3.12.3. Edits and commits were made in
this checkout directly (no worktree, as instructed). Mutant runs used a throwaway clone at `/tmp/sr-fix`. Every
verification below ran in this checkout, not in the clone, except where a line says "clone".

**Summary:**
- Findings: 13 (WR-01..WR-07, IN-01..IN-06)
- Fixed: 12 (the 11 assigned, plus IN-03, whose review fix is evidence text only)
- No change needed: 1 (WR-07, known/structural: 05-02 deviation 7, owner bundle `[F]` line)
- Skipped: 0

Each fix was RED first (a drill, pole or mutant that showed the defect on the old code), then GREEN, and went in as its
own pathspec commit.

## Fixed Issues

### WR-01: V-FO-SUBPROCESS-POLES red pole passes without the recall clause firing

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`
**Commit:** 180bec69
**RED:** in the clone, a mutant made `_recall` return `n/a` for an absent recall. V-FO-DRILL-MISSING-RECALL went FAIL,
but the pole still printed `ok V-FO-SUBPROCESS-POLES ... names FAIL V-FO-ENTRIES + V-FO-RECALL`.
**GREEN:** the red pole now requires `RECALL_ABSENT_RE`, which is
`(^|; |: )V-FO-RECALL FAIL: UNMEASURED: recall is absent`. Under the same mutant the pole reads
`FAIL V-FO-SUBPROCESS-POLES ... lacks ...`. Without the mutant: SR_PASS=15/15. Evidence bytes unchanged.

### WR-02: V-FO-RECALL accepts one window twice, or windows in reverse time order

**Status:** fixed: requires human verification (logic: the window ordering rule)
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md`, `ledger.json` (state.F prg
sha `1ca8386f...` -> `c9f8b52c...`; reason "21 drills (19 refusals" -> "24 drills (22 refusals")
**Commit:** e5a41192
**RED:** the fixture windows were given start/end, and three drills were added: RECALL-DUPLICATE, RECALL-ORDER and
RECALL-UNTIMED. On the old `_recall` all three showed `expected ['V-FO-RECALL'], red clauses []`.
**GREEN:** `_recall` now parses `start`/`end` with `_utc_epoch` (a timezone is required). It returns UNMEASURED unless
start < end, and it requires before.end <= after.start. Each of the three drills is killed by V-FO-RECALL only, and
both positive controls stay green. The review's optional bound against the probe row `ts` was not added, because those
`ts` values carry no timezone.

### WR-03: D-LISTING before/after rows are never checked for their plane

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md`, `ledger.json` (prg sha
`c9f8b52c...` -> `47c1da99...`; "24 drills (22 refusals" -> "25 drills (23 refusals")
**Commit:** 656207d1
**RED:** `_drill_row` was given a `cwd` under LAPTOP_PROFILE, and a ROW-PLANE drill was added (after row with cwd
`/home/x`). On the old `_side` it showed `red clauses []`.
**GREEN:** `_side` now refuses a row whose `_row_plane` is not in LISTING_HOSTS (UNMEASURED). ROW-PLANE is killed by
V-FO-AFTER only. The real K4 rows derive to `laptop`, so K4-REAL is still killed by V-FO-HELPED only.

### WR-04: An empty or blank-only body puts unrelated skills into one dedup group

**Status:** fixed
**Files modified:** `tools/skill_dedup_sweep.py`, `tools/test_skill_representation.py`
**Commit:** 42a69797
**RED:** new pole V-FD-POLE-EMPTY-BODY with three skills: pdf-tools and slack-notify (frontmatter only) and x
(frontmatter + blank lines). On the old `groups()` it read `body_bytes=[0] groups=1`.
**GREEN:** `sweep.groupable(rec)` (body_bytes > 0) now gates group formation. drift_excluded is still computed for
those names. The pole reads `groups=0`, and the mutant V-FD-MUTANT-EMPTY-BODY-GROUPED (guard dropped) is killed by
EMPTY-BODY. `--recording` on F-sweep-gex44.json passes 7/7 (the smallest gex44 body is 95 bytes). METHOD["group"]
names the rule for future recordings. Residual: a body made only of spaces, with no trailing newline, is not eaten by
`_FM_RE` and still hashes as non-empty. Telling it apart from the records would need a schema change.

### WR-05: `listing_chars_upper_bound` is smaller than the characters an entry removal frees

**Status:** fixed: requires human verification (arithmetic of the bound)
**Files modified:** `tools/skill_dedup_sweep.py`, `tools/test_skill_representation.py`
**Commit:** 32be6105
**RED:** new pole V-FD-POLE-LISTING-LINE-BOUND builds the listing in memory (`- aa: <100 chars>`,
`- bbb: <100 chars>`). The old code read `listing_chars_upper_bound=100 chars freed per removal=[107, 108]`.
**GREEN:** each member now counts `len(name) + LINE_OVERHEAD (4) + N`, and the top k are summed. A new `chars_basis`
key states the line shape and that whitespace the probe strips is not counted. The pole gives 108, equal to the largest
figure freed. The gex44 figure still renders UNMEASURED, so the evidence bytes are unchanged.

### WR-06: `--measure-live --host repo` overwrites the repo plane with the live plane and exits 0

**Status:** fixed
**Files modified:** `tools/skill_dedup_sweep.py`, `tools/test_skill_representation.py`
**Commit:** 89133b7a
**RED:** new pole V-FD-POLE-HOST-REPO-REFUSED read `--measure-live --host repo rc=0 wrote=True; build_recording built;
V-FD-RECORDINGS ok`.
**GREEN:** `sweep.host_ok()` refuses `repo` in three places: `main` (exit 2, nothing written), `build_recording` and
`c_recordings`. The pole now reads `rc=2 wrote=False; build_recording refused; V-FD-RECORDINGS FAIL`. CLI check:
`--measure-live --host repo --out /tmp/sr-host-repo.json` gave rc=2 and wrote no file. Evidence unchanged.

### IN-01: Unreachable branch in `c_planes_apart`

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md`, `ledger.json` (prg sha
`47c1da99...` -> `45e71f65...`)
**Commit:** 951332c9
**RED:** new tamper drill DISTINCT-NAMES (distinct_names + 1) was red by V-FD-GROUPS-REPRODUCE only, while
V-FD-PLANES-APART stayed ok.
**GREEN:** the dead branch was replaced with a check that can fire: distinct_names == member names ==
len(names list) == len(set(names list)). DISTINCT-NAMES is now killed by both clauses. The evidence gained one
tamper-drill row.

### IN-02: `live_plane` / `repo_plane` can raise instead of returning INCONCLUSIVE

**Status:** fixed
**Files modified:** `tools/skill_dedup_sweep.py`, `tools/test_skill_representation.py`
**Commit:** 114950ab
**RED:** new pole V-FD-POLE-UNREADABLE-INCONCLUSIVE (a mode-000 live skill, plus a temp git repo with a tracked
`skills/bad\xff/SKILL.md`) read `RAISED PermissionError; ... RAISED UnicodeEncodeError`.
**GREEN:** the `is_dir`/`is_file` probes now sit inside the try that catches OSError. `repo_plane` refuses a name that
is not UTF-8 before it calls `batch_blobs`. Both cases read INCONCLUSIVE; the repo reason is
`tracked name 'bad\udcff' is not UTF-8`. `--recording` passes 7/7. If mode 000 does not deny the current user (root),
the pole marks the live half n/a and says so.

### IN-03: The evidence documents a `--compare` command that exits 1

**Status:** fixed (no behaviour change, evidence text only, as the review proposed)
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md`, `ledger.json` (prg sha
`5211851c...` -> `a2c0fc2b...`)
**Commit:** 1086fdc1
**Before:** the rendered evidence contained no caveat (`grep -c "exits 1"` gave 0).
**After:** a `note:` line now follows each `--compare` command. It says the command exits 1 (`MOVED ... (groups and
drift_excluded unchanged)`) once a live skill's own hooks append to its directory, that this is the expected reading,
and that on any other node the result is INCONCLUSIVE (host-bound). The note sits on its own line so the command line
can still be copied. Observed: `--compare` rc=1,
`MOVED gex44/claude-power-pack ['dir_digest', 'files'] (groups and drift_excluded unchanged)`.

### IN-04: `discover()` discards the git failure reason

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`
**Commit:** 0c7adb4b
**RED:** new pole V-FD-POLE-GIT-UNAVAILABLE patches `smd.tracked_paths` to fail. On the repo it gave the false
`uncommitted: ...` diagnosis. On an empty tree it gave V-FD-RECORDINGS FAIL "no ... discovered".
**GREEN:** `discover()` now returns one row, `(GIT_ROW, None, "INCONCLUSIVE: git cannot list the tracked paths at
HEAD: <why>")`. The recording loop of `default_run`, moved unchanged into `recordings_results`, maps that row to
INCONCLUSIVE and does not add the "gex44 not discovered" FAIL. Both cases now read INCONCLUSIVE with git's reason, and
the worst status is INCONCLUSIVE.

### IN-05: Entry-level INCONCLUSIVE and uncommitted windows are reported as FAIL

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md`, `ledger.json` (prg sha
`45e71f65...` -> `5211851c...`)
**Commit:** e9ec33e0
**RED:** new V-FO-ENTRIES-STATUS lines inside V-FO-DRILLS drive `window_docs` and `c_fo_entries` in-process. On the old
code, UNCOMMITTED-WINDOW and NOISE-UNSOURCED both read FAIL.
**GREEN:** a window that is present but uncommitted is now kept as `Unjudged(reason)`; an absent window stays FAIL.
`_recall` reads an `Unjudged` window as INCONCLUSIVE. `c_fo_entries` raises INCONCLUSIVE when every non-ok, non-skipped
clause is INCONCLUSIVE, and FAIL as soon as one clause is FAIL. The control UNCOMMITTED-AND-DROP stays FAIL. The
clause doc text for V-FO-RECALL and V-FO-ENTRIES was updated.

### IN-06: No pole exercises the symlink, dangling-link or non-UTF-8 branches of `live_plane`

**Status:** fixed
**Files modified:** `tools/test_skill_representation.py`
**Commit:** 988e2d29
**RED (clone):** three `live_plane` mutants: `symlinked` never appended; a dangling link falls through to
`no_skill_md`; the UTF-8 refusal removed. Each one left V-FD-HASH-POLES ok and SR_PASS=15/15.
**GREEN:** new pole V-FD-POLE-DISCOVERY-LINKS (POSIX; named n/a elsewhere). In the clone, each mutant now fails it.
Without the mutants: SR_PASS=15/15.

## No Change Needed

### WR-07: V-FO-RECALL's green branch can be reached only by fabricated windows

**File:** `tools/test_skill_representation.py:514`; `tools/test_skill_delivery.py:628, 1137`
**Reason:** known and structural (05-02 deviation 7; already an owner-bundle `[F]` line). The gate fails closed. The
review's fix (a `--host` flag on `test_skill_delivery.py --measure-live`, or a node-to-plane table) changes another
pillar's instrument, so it is not a cheap honest fix in this file, and no evidence-text fix was named. No change.
**Original issue:** `test_skill_delivery.py` records `socket.gethostname()`, while the gate admits only `laptop`. A real
laptop window is therefore refused unless the node is literally named `laptop`.

## Ledger coupling

Only the state.F line (104) of `vault/programs/skill-capability/ledger.json` changed: `git diff 1a224354 HEAD`
shows one hunk, `@@ -104 +104 @@`. Two things in it changed:
- the prg sha of `evidence/F-representation.md`: `1ca8386f...` -> `a2c0fc2ba6d70351e120bdee9d869c8c10620521f3728030142eff0114bf8ffc`;
- the drill count in the reason: "21 drills (19 refusals, 2 positive controls)" -> "25 drills (23 refusals, 2
  positive controls)".

`evidence/F-sweep-gex44.json` (`8b17edc5...`) and `f-operations.json` (`a19b06cf...`) did not change, and neither did
their pins. `frozen` and every other state entry are byte-identical.

## Verification (run in this checkout, sc-run, on gex44)

- `timeout 600 python3 tools/test_skill_representation.py`: SR_PASS=15/15, rc 0 (13 poles + 2 mutants, 7 tamper
  drills, 25 FO drills + 3 entry-status lines).
- `python3 tools/test_skill_representation.py --recording vault/programs/skill-capability/evidence/F-sweep-gex44.json`:
  SR_PASS=7/7.
- `python3 tools/test_skill_capability_program.py --pillar X` for A, B, C, D, F, H: CEP_PILLAR_A=PASS, B=PASS,
  C=PASS, D=PASS, F=PASS, H=PASS.
- `python3 tools/test_skill_capability_program.py --status`: closed [A, B, C, D, F, H], open [E, G, I, J, K, L, M, N],
  violations [].

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

## Verification gap closure

Source: `05-VERIFICATION.md` (gaps_found 17/18, HEAD 78ca9cac). Worktree sc-run, host gex44, python3 3.12.3. Edits and
commits in this checkout directly (no worktree). Every gate run below ran in this checkout. Each item was RED first on
the code as it was, then GREEN, and went in as its own pathspec commit.

### Gap 1 (WR-05): `listing_chars_upper_bound` is a true bound or UNMEASURED

**Status:** fixed: requires human verification (arithmetic of the bound)
**Files modified:** `tools/skill_dedup_sweep.py`, `tools/test_skill_representation.py`
**Commit:** 8a8ffb8d
**RED:** two new poles build a listing, run it through the probe's own `analyse` (`wiki/tools/listing_floor_probe.py`,
loaded from the tree, not edited) on a synthetic transcript, and require the bound to be UNMEASURED or >= the
characters the member's own entry frees. On the old code: `V-FD-POLE-LISTING-MULTILINE listing_chars_upper_bound=108
freed={'aa': 420, ...}` and `V-FD-POLE-LISTING-NAME-COLLISION listing_chars_upper_bound=49 freed={'code-review': 316,
...}` (the `- code-review:code-review: ...` line overwrote the skill's key), SR_PASS=14/15.
**GREEN:** a member counts only when the challenger row carries `watch_shape[name] = {lines, keys, chars}` with
lines 1, keys 1 and chars == len(name) + LINE_OVERHEAD (5) + N. Anything else is UNMEASURED with a `chars_why`.
`sweep.entry_shape(listing, name)` is the reference shape: it splits the way the probe does (`splitlines()`, `- `
lines, key before the first ':'). The frozen probe writes no `watch_shape`, so every figure from its rows now reads
UNMEASURED. Both poles check two cases: the probe's rows as written, and the same rows given the true shape. Both read
UNMEASURED (`entry spans 2 listing lines`, `2 listing lines parse to this name`). LISTING-LINE-BOUND is the positive
control: UNMEASURED without a shape, and 108 == the largest figure freed with one. `CHARS_BASIS` now says + 5.
Result: SR_PASS=15/15 (15 poles + 2 mutants). The gex44 group still renders UNMEASURED (its `chars_why`: both members
`not in watch set`), so the evidence bytes did not change.
**Real-listing check (gex44 transcript 88cfe52b, 30000 chars, 294 `- ` lines, 213 keys):** 121 keys pass the proof,
and for each of them the figure equals the entry's block length. agent-reach (4 lines, 845 chars), claude-api (3 lines,
1083) and code-review (2 keyed lines) are refused.
**Residual:** a continuation line of a description that itself starts with `- ` counts as an entry in the probe's
grammar, so the probe and `entry_shape` both end the block there. This is written in the `entry_shape` docstring.

### Gap 2 (WR-02 anchor): recall windows tied to the commit that applied the operation

**Status:** fixed: requires human verification (logic: the anchor rule)
**Files modified:** `tools/test_skill_representation.py`, `evidence/F-representation.md` (re-rendered), `ledger.json`
(state.F prg sha `a2c0fc2b...` -> `40141784e8fcf82a4049e4ad681a6e65c515f0d326f9ff85f835a3eb8c640303`, F line only)
**Commit:** 76d5cac5
**RED:** the fixture entry gained `applied_commit` (fabricated, resolved by the fixture at 2026-09-09T02:00:00+02:00,
between the windows), and three drills were added. On the old `_recall`, all three read
`expected ['V-FO-RECALL'], red clauses []` (SR_PASS=13/15):
- RECALL-BOTH-PRE-OP: both windows end before a commit at 2026-09-20.
- RECALL-BOTH-POST-OP: both windows start after a commit at 2026-08-20.
- MISSING-APPLIED-COMMIT: the field is deleted.
**GREEN:** `resolve_applied_commits(refs, repo)` asks git three questions for each 7-40 hex ref: is it a commit
(`rev-parse --verify`), is it an ancestor of HEAD (`merge-base --is-ancestor`), and what is its committer time
(`log -1 --format=%cI`, parsed timezone-aware). `operations_inputs` passes the result to `check_entry(..., commits)`.
`_recall` checks the anchor last and requires before.end <= commit time <= after.start. The outcomes:
- missing or malformed field, unknown commit, or a commit that is not an ancestor: UNMEASURED (FAIL);
- git unable to answer: INCONCLUSIVE.
Each of the three RED drills is now killed by V-FO-RECALL FAIL. Three more drills go through real git:
- APPLIED-COMMIT-REAL: the commit that added `f-operations.json`, with the windows one day either side of its real
  `%cI`. It passes every clause. This is a third positive control.
- APPLIED-COMMIT-UNRESOLVED: 40 zeros. FAIL.
- APPLIED-COMMIT-GIT-FAILURE: `git -C` on an absent directory. INCONCLUSIVE.
The two fabricated positive controls pass with the fabricated anchor. Drills now also pin the status of their red
clauses: FAIL, or INCONCLUSIVE for NOISE-ABSENT and APPLIED-COMMIT-GIT-FAILURE. The evidence drill table shows that
status.
**Mutants:** each of these was run on a copy and the copy deleted afterwards. Each turned V-FO-DRILLS red:
- time comparisons disabled: BOTH-PRE-OP and BOTH-POST-OP FAIL;
- a missing field defaulted to the drill commit: MISSING-APPLIED-COMMIT FAIL;
- unsourced noise flipped from INCONCLUSIVE to FAIL: NOISE-ABSENT and ENTRIES-STATUS-NOISE-UNSOURCED FAIL.
**Schema:** the entry schema text (gate docstring, `ENTRY_SCHEMA_LINES`, the V-FO-RECALL clause doc, all rendered into
the evidence) names `applied_commit`. `f-operations.json` holds 0 entries, and its `rule` is the frozen text verbatim,
so it was not changed (pin `a19b06cf...` unchanged). The schema id stays `/1` because no entry was ever written under
the old shape.
**Follow-up commit f349cbcb:** this adds the APPLIED-COMMIT-NOT-ANCESTOR drill. It builds a throwaway repository,
never this one, with HEAD detached on its first commit and a second commit on a side branch. The windows are placed
around the side commit's real committer time, so the only check that can refuse it is ancestry. The drill is killed
by V-FO-RECALL FAIL (`is not an ancestor of HEAD`). In a mutant without `merge-base --is-ancestor` it reads
`red clauses []`. Evidence re-rendered; prg sha `40141784...` ->
`7183cb5945f06530b936592f5674b9cd5a2e5e9692322da755ea72ed7baec1ba`, F line only. The gate now gives SR_PASS=15/15,
`V-FO-DRILLS 32 drills`.

### Gap 3: state.F reason states the counts the gate prints

**Status:** fixed
**Files modified:** `ledger.json` (state.F `reason` only)
**Commit:** 27867eb1
**RED:** a throwaway script, `/tmp/sc_reason_check.py`, not committed, compared two strings. One was the drill
clause of the reason. The other was the `V-FO-DRILLS` head of a gate run.
- The ledger said `25 drills (23 refusals, 2 positive controls)`.
- The gate printed `32 drills (3 positive controls, 27 refusals red by FAIL, 2 INCONCLUSIVE expectations) + 3
  entry-status lines (2 INCONCLUSIVE, 1 FAIL)`.
Result: MISMATCH. NOISE-ABSENT had always been an INCONCLUSIVE expectation, not a red refusal, and the old head never
printed the split at all.
**GREEN:** the reason now quotes the printed head verbatim, and the script reads MATCH. The reason also says what each
group does:
- each refusal is red by FAIL on its own clause;
- each INCONCLUSIVE expectation (unsourced noise, git unable to answer) reads INCONCLUSIVE on its own clause;
- each positive control (one of them on a real ancestor commit) passes every clause.
The operation-gate sentence now names the applied_commit anchor. These counts come from the drill tables that every
drill is checked against, so a green run prints observed counts.

## Ledger coupling (gap closure)

All four ledger edits are on line 104, the `"F":` line. `git diff 78ca9cac HEAD -- vault/programs/skill-capability/ledger.json`
has one hunk, `@@ -104 +104 @@`. A JSON comparison against the pre-edit file shows these parts identical:
- `frozen`;
- every other state entry;
- all F evidence entries except the prg sha.
The changes:
- prg sha of `evidence/F-representation.md`: `a2c0fc2b...` -> `40141784...` (76d5cac5) -> `7183cb5945f06530b936592f5674b9cd5a2e5e9692322da755ea72ed7baec1ba` (f349cbcb);
- the reason text (27867eb1).
`F-sweep-gex44.json` (`8b17edc5...`) and `f-operations.json` (`a19b06cf...`) did not change, and neither did their pins.
The owner bundle was not edited. No new Owner action results. The existing `[F]` laptop procedure (line 11) is
narrower now: the operation has to be committed between the two windows, and the entry has to name that commit as
`applied_commit`. An entry without it is refused with `applied_commit None is not the 7-40 hex commit that applied
the operation`.

## Verification (gap closure, run in this checkout, sc-run, on gex44, HEAD 27867eb1)

- `timeout 600 python3 tools/test_skill_representation.py`: SR_PASS=15/15, rc 0. The parts: V-FD 15 poles + 2 mutants
  and 7 tamper drills + clean control; V-FO 32 drills + 3 entry-status lines; subprocess poles ok; V-FR-EVIDENCE-CURRENT ok.
- `python3 tools/test_skill_representation.py --recording vault/programs/skill-capability/evidence/F-sweep-gex44.json`: SR_PASS=7/7.
- `timeout 1900 python3 tools/test_skill_capability_program.py --pillar X`: CEP_PILLAR_A=PASS, B=PASS, C=PASS,
  D=PASS, F=PASS, H=PASS.
- `python3 tools/test_skill_capability_program.py --status`: violations [], rc 0.

