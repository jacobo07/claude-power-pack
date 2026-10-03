---
phase: 05-representation-operations
reviewed: 2026-10-03T00:00:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - tools/skill_dedup_sweep.py
  - tools/test_skill_representation.py
  - vault/programs/skill-capability/f-operations.json
  - vault/programs/skill-capability/evidence/F-sweep-gex44.json
  - vault/programs/skill-capability/evidence/F-representation.md
  - vault/programs/skill-capability/ledger.json (state.F, 03cd4730)
findings:
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** deep (cross-file: `skill_mirror_drift` git/blob primitives, `verify_global_mirrors.batch_blobs`,
`test_listing_floor_verdict.load_rows/frozen`, `wiki/tools/listing_floor_probe.analyse`, `test_skill_delivery.measure_live`)
**Files Reviewed:** 2 source files (commits ec706ab8, cfe4c377, e4947f62) plus the committed F artifacts and ledger state.F (03cd4730). Worktree sc-run, HEAD 42ee8abe, host gex44.
**Status:** issues_found

## Summary

Baseline on gex44:
- `timeout 600 python3 tools/test_skill_representation.py`: SR_PASS=15/15, rc 0 (0.28 s).
- `python3 tools/skill_dedup_sweep.py --compare vault/programs/skill-capability/evidence/F-sweep-gex44.json`:
  `MOVED gex44/claude-power-pack ['dir_digest', 'files'] (groups and drift_excluded unchanged)`, rc 1. This is known
  (05-01 deviation 2).
- The prg sha256 in state.F (`1ca8386f...`) equals the LF sha256 of the committed `F-representation.md`.

Mutant runs were done in a throwaway clone (`/tmp/sr-rev`). The worktree was not modified, apart from this file.

What holds up: every gate input goes through `smd.committed_bytes`. That check refuses a working-tree copy that is
missing or differs after LF normalization, so the working-tree reads in `probe_rows` (line 762) and `evidence_state`
(line 1163) cannot see uncommitted bytes. The recall check uses integer cross-multiplication. Absent, zero and non-int
figures in `_side` / `_recall` read as UNMEASURED and are refused. Subprocess calls take argv lists only. Window and
sweep references are confined to the evidence directory with no `..`, and they are resolved through
`git cat-file HEAD:<rel>`, so I found no path traversal through `--operations` content. `--recording`, `--operations`
and `--out` are operator-supplied paths, as intended.

The defects are in what the operation gate accepts as evidence. Recall windows are never ordered or deduplicated
(WR-02), and D-LISTING rows are never checked for their plane (WR-03). One gate claim passes for the wrong reason:
the subprocess red pole survives a mutant that waves through an absent recall (WR-01). The sweep groups unrelated
skills on an empty body (WR-04), and it labels a lower bound as an upper bound (WR-05). It also lets `--host repo`
overwrite the repo plane (WR-06). V-FO-RECALL can be satisfied only by fabricated windows (WR-07, known). Today there
are 0 applied operations, so none of these changes the current 15/15. Each one bites the first real laptop entry.

## Warnings

### WR-01: V-FO-SUBPROCESS-POLES red pole passes without the recall clause firing

**File:** `tools/test_skill_representation.py:1053-1055, 1070`
**Issue:** The red pole is the real K4 entry with `recall` deleted. The K4 rows are themselves refused by V-FO-HELPED
(89844 + 1500 >= 87739). That alone gives rc 1 and `FAIL V-FO-ENTRIES`. The only recall-specific test is the
substring `"V-FO-RECALL" in out_bad`. That substring is also matched by `V-FO-RECALL-HELD skipped: recall not ok`,
which `c_fo_entries` prints for any non-ok recall status, including a mutated `n/a`.
```python
red_ok = rc_bad == 1 and "FAIL V-FO-ENTRIES" in out_bad and "V-FO-RECALL" in out_bad
```
**Reproduced:** In the clone, `_recall` was changed to return `("n/a", "MUTANT: absent recall waved through", None)` for
a missing recall. Result: `V-FO-DRILL-MISSING-RECALL` FAIL, but `ok V-FO-SUBPROCESS-POLES ... names FAIL V-FO-ENTRIES +
V-FO-RECALL`. The subprocess output was only
`V-FO-HELPED FAIL: ...; V-FO-RECALL-HELD skipped: recall not ok`. The "driven red across a real process boundary on a
missing recall" claim in D01_REASONS #3 and in the ledger reason is therefore not shown by this clause.
**Fix:** Match the clause token exactly, and require the recall clause to be the reason:
```python
red_ok = (rc_bad == 1 and "FAIL V-FO-ENTRIES" in out_bad
          and re.search(r"(^|; |: )V-FO-RECALL FAIL: UNMEASURED: recall is absent", out_bad, re.M) is not None)
```
Better still, build the red pole from an entry that every other clause admits, so the recall clause is the only red
one. With the committed rows that is not possible, because no helped pair exists, so at least use the exact-token match.

### WR-02: V-FO-RECALL accepts one window twice, or windows in reverse time order

**File:** `tools/test_skill_representation.py:649-676` (`_recall`)
**Issue:** Before and after are required to be different paths (line 649), with the same capability and host. Their
content and time are never compared. A window document carries `start`/`end` (see `C-window-G.json`), but the gate
reads neither. So two things pass: (a) one measurement committed under two filenames, which is recall "held" by
construction, and (b) an "after" window measured before the "before" window. The frozen rule's recall check is then
met without any post-operation measurement.
**Reproduced** (in-process `check_entry` on `base_fixture`):
- `duplicate` (both windows 4/5, identical start/end): `ALL ok/n-a`.
- `after-window-older` (before 2026-10-05..06, after 2026-09-01..02): `ALL ok/n-a`.
**Fix:** In `_recall`, parse `start`/`end` as UTC epochs and refuse with UNMEASURED when they are absent or
unparseable. Then require `before.end <= after.start`, which also forbids identical windows. Optionally require that
the before window ends no later than the before probe row's `ts`, and that the after window starts no earlier than the
after row's `ts`. Add two drills, RECALL-DUPLICATE and RECALL-ORDER, each red by V-FO-RECALL only.

### WR-03: D-LISTING before/after rows are never checked for their plane

**File:** `tools/test_skill_representation.py:532-564` (`_side`), compare `1146-1155` (`_row_plane`) and `514`
**Issue:** The gate requires recall windows to come from the D-LISTING plane (`LISTING_HOSTS = ("laptop",)`). The
listing rows themselves are resolved only by label and session id. `_row_plane` exists, but it is called only by the
renderer. A probe row appended from gex44 or another host (cwd `/home/...`, `_row_plane` -> UNKNOWN) is accepted as a
D-LISTING measurement. The positive-control fixture rows (`_drill_row`, line 835) carry no `cwd` or `settings_file`,
so `_row_plane` gives UNKNOWN for them, and POSITIVE-CONTROL still passes. That green is direct evidence that
UNKNOWN-plane rows are admitted.
**Fix:** In `_side`, after the rc/result check:
```python
if _row_plane(r) not in LISTING_HOSTS:
    return "FAIL", f"UNMEASURED: {key} row #{i} plane {_row_plane(r)} is not the D-LISTING plane", None
```
Give `_drill_row` a `cwd` under `LAPTOP_PROFILE`, and add a ROW-PLANE drill (cwd `/home/x`) that is red by V-FO-BEFORE
only.

### WR-04: An empty or blank-only body puts unrelated skills into one dedup group

**File:** `tools/skill_dedup_sweep.py:102-107, 226-254`; grammar `modules/skill_router/skill_index.py:123`
**Issue:** `body_sha` hashes the text after `_FM_RE`. Its closing `---\s*\n` also eats trailing blank lines, so every
frontmatter-only SKILL.md has the same `body_sha` (sha256 of `b""`, `body_bytes` 0). The same holds for
frontmatter + blank lines. `groups()` has no floor and no exclusion, so these skills become one "dedup candidate"
group even when their descriptions and their other files differ. V-FO-DEDUP-SWEEP (line 679) then admits a dedup
operation that cites that group. On gex44 the smallest body is 95 bytes, so the committed recording is unaffected. The
laptop recording in the owner bundle is not yet measured.
**Reproduced:** live root with `pdf-tools` ("Extract tables from PDF files"), `slack-notify` ("Post a message to a Slack
channel") and `x` (frontmatter + `\n\n`), all without body text:
`groups() -> [(['pdf-tools', 'slack-notify', 'x'], 0)]`.
**Fix:** Do not form groups on an empty body. Either skip `body_bytes == 0` in `groups()`, or record them as a
separate `empty_body` list. Add a V-FD pole (two frontmatter-only skills -> 0 groups) and a mutant that drops the
guard. If whitespace-only bodies should also be excluded, compare on `body.strip()`.

### WR-05: `listing_chars_upper_bound` is smaller than the characters an entry removal frees

**File:** `tools/skill_dedup_sweep.py:292-299`; probe semantics `wiki/tools/listing_floor_probe.py:57-62`
**Issue:** The probe writes `described (N)` with `N = len(desc.strip())`, the description only. Removing a listing line
`- <name>: <desc>\n` frees `len(name) + 4 + N` characters (`- `, `: `, the newline). Summing `N` over the top-k
members therefore gives a lower bound on the line characters. It is labelled `listing_chars_upper_bound` in the
sweep's `--json`, in the gate's `--json`, in the rendered evidence, and in the owner-bundle wording "upper bound".
Today it renders `UNMEASURED`, because neither sleepy member is watched, so the defect is latent. The first watched
group will show a figure below the real line cost under an "upper bound" label.
**Reproduced:** a 2-name group, both `described (100)`: `listing_chars_upper_bound 100`; characters removed from the
listing text are 118.
**Fix:** Add `len(name) + 4` per counted member (`- `, `: `, `\n`), so the figure is a true per-line upper bound.
Alternatively rename it `description_chars` and drop "upper bound" from its label. Keep CAP_NOTE in both cases.

### WR-06: `--measure-live --host repo` overwrites the repo plane with the live plane and exits 0

**File:** `tools/skill_dedup_sweep.py:65, 320, 377`; gate `tools/test_skill_representation.py:130-138`
**Issue:** `HOST_RE` admits `repo`, so `planes = {"repo": rp, host: lp}` keeps only the live plane under the key
`repo`. The recording's `repo_commit` is still the repo plane's commit. The CLI prints `repo=161 repo=161/186` and
exits 0. The gate's V-FD-RECORDINGS also passes, because `set(planes) == {"repo", "repo"}`. Only V-FD-REPO-REPRODUCES
catches it, as `repo.commit differs`.
**Reproduced:** `--measure-live --host repo --out /tmp/sr-host-repo.json` gives rc 0, planes `['repo']`,
`root ~/.claude/skills`, 161 skills. `--recording` on it: V-FD-RECORDINGS ok, V-FD-POP-FLOOR ok, V-FD-GROUPS-REPRODUCE
ok (`repo/managing-sleepy-skills` ...), REPO-REPRODUCES FAIL.
**Fix:** Reject `host == "repo"` in `main` (exit 2) and in `c_recordings`, for example
`if rec["host"] == "repo": fail("host 'repo' collides with the repo plane label")`. Also assert in `build_recording`
that `host != "repo"`.

### WR-07: V-FO-RECALL's green branch can be reached only by fabricated windows (known, 05-02 deviation 7)

**File:** `tools/test_skill_representation.py:514, 672`; `tools/test_skill_delivery.py:628, 1137`
**Issue:** `test_skill_delivery.py --measure-live` records `host = socket.gethostname()`. The CLI call at line 1137 does
not pass `host`, and there is no `--host` flag. The gate admits only the literal `laptop`. Unless the laptop's hostname
is literally `laptop`, every real window is refused. The positive controls pass only because `_drill_window` types
`host="laptop"`. This fails closed and is documented in owner-bundle line 11. Still, the documented procedure for
applying an operation cannot be completed as written, and the green half of V-FO-RECALL has never seen a real input.
**Fix:** Add a `--host` flag to `test_skill_delivery.py --measure-live`, validated by `^[a-z0-9-]+$`, defaulting to
refusal rather than to `gethostname()`. Record the plane label in the window. Keep `LISTING_HOSTS` as plane labels.
Alternatively, map node names to planes in one committed table that both gates read.

## Info

### IN-01: Unreachable branch in `c_planes_apart`

**File:** `tools/test_skill_representation.py:253-254`
**Issue:** `len(names) == 1 and names <= drift` cannot be true, because line 250 already fails every group with
`len(names) < 2`. The "drift name as the only name of a group" refusal is therefore dead code, and no drill isolates it.
**Fix:** Delete it, or replace it with a check that is live: every `distinct_names == len(names) == len(g["names"])`.

### IN-02: `live_plane` / `repo_plane` can raise instead of returning INCONCLUSIVE

**File:** `tools/skill_dedup_sweep.py:186-190` (outside the try at 193); `tools/verify_global_mirrors.py:182` (via `repo_plane:150`)
**Issue:** (a) `md.is_file()` on a live skill directory with mode 000 raises `PermissionError` on Python 3.12 (EACCES
is not in pathlib's ignored errnos). Reproduced:
`RAISED PermissionError [Errno 13] Permission denied: .../locked/SKILL.md`. `--measure-live` and `--compare` then exit
with a traceback, not `INCONCLUSIVE ...`. (b) A tracked `skills/` path that is not valid UTF-8 decodes with
surrogateescape. `batch_blobs` then raises `UnicodeEncodeError` on `payload.encode("utf-8")`. `repo_plane`'s docstring
says it never raises, and inside the gate `run_clause` reports the error as `FAIL malformed recording` rather than
INCONCLUSIVE.
**Fix:** Move the `is_dir`/`is_file` probes inside the try, and catch `OSError`. In `repo_plane`, refuse names that do
not encode as UTF-8 (as `live_plane` already does) before calling `batch_blobs`.

### IN-03: The evidence documents a `--compare` command that exits 1 (known, 05-01 deviation 2)

**File:** `tools/test_skill_representation.py:1202`; `evidence/F-representation.md` "## Commands"
**Issue:** `command: python3 tools/skill_dedup_sweep.py --compare .../F-sweep-gex44.json` is listed with the
reproduction commands, but on gex44 it returns `MOVED gex44/claude-power-pack`, rc 1, minutes after a measure. The
owner bundle explains this. The rendered evidence does not.
**Fix:** In the render, append to that `command:` line: "exits 1 (MOVED) when a live skill's hook logs grew; groups
unchanged is the expected reading".

### IN-04: `discover()` discards the git failure reason

**File:** `tools/test_skill_representation.py:96-103`
**Issue:** `tracked, _ = smd.tracked_paths(repo, "HEAD")` drops the reason. When git is missing or times out, every
working-tree recording is reported as `uncommitted: ... exists only in the working tree (commit it)`, which is a false
diagnosis even though the status, INCONCLUSIVE, is right. With no working-tree file present, the result becomes
V-FD-RECORDINGS **FAIL** `no ... discovered` instead of INCONCLUSIVE.
**Fix:** If `tracked is None`, return one INCONCLUSIVE row carrying `why`, and make `default_run` map it to INCONCLUSIVE.

### IN-05: Entry-level INCONCLUSIVE and uncommitted windows are reported as FAIL

**File:** `tools/test_skill_representation.py:654-656, 776-777, 791-795`
**Issue:** `window_docs` drops a window that `committed_json` refuses as uncommitted. `_recall` then reports it as FAIL
`not a committed window document`. An unsourced-noise `V-FO-HELPED INCONCLUSIVE` is also folded into
`fail(...)` for V-FO-ENTRIES. Both are red, but they contradict the module docstring (line 26: "An uncommitted input is
INCONCLUSIVE, never judged"). They also point at the wrong fix: the entry is not malformed, its input is uncommitted.
**Fix:** Carry the `committed_json` reason into `docs` (for example as `{w: (None, why)}`). Have `c_fo_entries` raise
`inconclusive` when every red clause is INCONCLUSIVE or the cause is uncommitted.

### IN-06: No pole exercises the symlink, dangling-link or non-UTF-8 branches of `live_plane`

**File:** `tools/test_skill_representation.py:356-370` (POLES); `tools/skill_dedup_sweep.py:181-202`
**Issue:** The poles cover a file entry and a directory without SKILL.md. They do not cover the `symlinked` list, the
dangling symlink that goes to `non_dir`, or the non-UTF-8 refusal. Breaking any of those three would keep
V-FD-HASH-POLES green.
**Fix:** Add a DISCOVERY-LINKS pole (on POSIX): a directory symlink to a real skill (expect it in `names` and
`symlinked`), plus a dangling link (expect it in `non_dir`). On Windows, skip it with a named `n/a` rather than an ok.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
