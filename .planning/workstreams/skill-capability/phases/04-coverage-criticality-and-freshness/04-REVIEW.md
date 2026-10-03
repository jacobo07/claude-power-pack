---
phase: 04-coverage-criticality-and-freshness
reviewed: 2026-10-03T00:00:00Z
depth: deep
files_reviewed: 6
files_reviewed_list:
  - tools/router_freshness_gate.py
  - tools/skill_coverage.py
  - tools/skill_mirror_drift.py
  - tools/test_router_freshness_gate.py
  - tools/test_skill_coverage.py
  - tools/test_skill_drift.py
findings:
  critical: 1
  warning: 8
  info: 4
  total: 13
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** deep (cross-file: `verify_global_mirrors` primitives, `skill_invocations.installed_names`, `hooks/hook-dispatcher.js` CHAIN_MAP)
**Files Reviewed:** 6 (diff 2dd5ab6c..HEAD aa0336bf, worktree sc-run, host gex44)
**Status:** issues_found

## Summary

Run on gex44 with `timeout 600`: `test_skill_coverage.py` 15/15, `test_skill_drift.py` 13/13,
`test_router_freshness_gate.py` 10/11 (rc=1, V-RFG-CLEAN FAIL, classified in WR-01).
`tools/skill_invocations.py` did not change in phase 4. It is not in the diff stat, and commits 1ad9ee71 and 8313c340
touch only `skill_coverage.py`, `test_skill_coverage.py` and evidence files. `installed_names` was read as a callee.

Security: no shell interpolation (every subprocess call takes an argv list), `--host` is validated by
`^[a-z0-9-]+$` before it builds a path, and a raw `--ref` / `repo_commit` reaches only `rev-parse --verify` before it
is replaced by the resolved sha. I found no injection or traversal that a non-repo actor can reach.

The main defect is one verdict that reads PASS when nothing was measured (CR-01). Most of the rest are measurements
that can quietly leave out part of their subject (WR-03, WR-06, WR-07, WR-08) and drills that cannot go red (WR-02).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: An absent or wrong live root reads PASS (every row ABSENT_LIVE, zero compared)

**File:** `tools/router_freshness_gate.py:198-209`; `tools/skill_mirror_drift.py:473`, `:478`
**Snippet:**
```python
bad = [r for r in rep["rows"] if r["status"] in ("DRIFT", "INCONCLUSIVE")]
...
return ("FAIL" if bad else "PASS"), lines
```
**Scenario (reproduced on gex44):**
`skill_drift_check(repo, Path('/nonexistent/skills'))` returns
`('PASS', ['24 repo skills vs /nonexistent/skills: IDENTICAL 0, DRIFT 0, INCONCLUSIVE 0, ABSENT_LIVE 24 ...'])`.
`skill_mirror_drift.py --live --live-root /nonexistent` exits 0, and so does `--live-root /etc`. The same happens by
default on any host with no `~/.claude/skills` (a CI box, a fresh clone, an install that put skills elsewhere), and
whenever `live_skills_root()` points to the wrong directory.
**Why guards fail:** ABSENT_LIVE is deliberately left out of `bad` ("not every repo skill is meant to be installed").
No clause checks that at least one pair was compared, or that the live root exists. So "compared nothing" and
"compared everything, all identical" print the same verdict. The UNMEASURED branch at line 184 only covers a checkout
with no skills. It never covers a live side with nothing on it. No V-RFG or V-SKD clause drives this pole.
**Fix:** treat a missing live root, and zero rows that are IDENTICAL or DRIFT, as UNMEASURED rather than PASS, in
both the router line and `--live` / `--json`:
```python
if not Path(root).is_dir():
    return "UNMEASURED", [f"live root {smd._tilde(root)} absent; nothing compared, not a pass"]
compared = c["IDENTICAL"] + c["DRIFT"]
if not bad and compared == 0:
    return "UNMEASURED", [head + "; zero pairs compared, not a pass"]
```
In `skill_mirror_drift.main`, exit with a distinct code (or print `UNMEASURED` and exit 1) when `compared == 0`. Add a
V-RFG-SKILL-DRIFT-NO-LIVE clause (Scenario with no `<tmp>/.claude/skills`) that fails on the current code.

## Warnings

### WR-01: V-RFG-CLEAN: the failure predates phase 4, but phase 4 added a second, host-coupled cause

**File:** `tools/test_router_freshness_gate.py:93-97`, `tools/router_freshness_gate.py:245-251`
**Classification:** phase 4 did not cause the original FAIL. `gate.run()` prints `V-ROUTER-LINKS FAIL router absent`,
because `router_path()` derives `/home/kobii/projects/-home-kobii-missions-skill-capability/memory/MEMORY.md`
(`REPO_ROOT.parents[1]` is `/home/kobii` on this non-install layout), and that file does not exist. The
`if not router.exists(): ... return 1` path is unchanged context in the diff. Phase 4 adds an independent second cause
on the same run: `V-ROUTER-SKILL-DRIFT FAIL ... android-reverse-engineering: DRIFT missing_live=['scripts/check-deps.ps1',
'scripts/decompile.ps1', 'scripts/find-api-calls.ps1', 'scripts/install-dep.ps1']` (the gex44 live copy has only the
`.sh` siblings). That is real drift, correctly reported. But V-RFG-CLEAN now reads the host's real `~/.claude/skills`.
Restoring the router would leave it red on gex44, and on any host its result depends on live-tree state the test does
not control.
**Fix:** keep V-RFG-CLEAN about the router: call the store/link/budget checks directly, or give `run()` a
`live_root` parameter and pass a hermetic identical-copy root from the test. Leave the host's real drift to
`skill_mirror_drift.py --live`, which is already documented as the host red pole. Record in the SUMMARY that the
original CLEAN FAIL is the router-path layout issue (pre-existing), not phase 4.

### WR-02: The CRLF drills over JSON records cannot go red

**File:** `tools/test_skill_drift.py:689-710` (V-SKD-CARD-SOURCE-CRLF), `:541-542` (V-SKD-RECORD-DRILL CRLF control);
`tools/test_skill_coverage.py:431-450` (V-SKC-RECORDING-CRLF)
**Scenario (mutant driven on gex44):** with `smd.lf_bytes = lambda b: b` (normalization removed),
`c_card_source_crlf()` returns `ok` and `c_record_drill()` returns `ok`. With `sc.read_lf` replaced by a raw
decode, `c_recording_crlf()` returns `ok`. JSON treats `\r` as insignificant whitespace, and these records hold no
multi-line strings. So a CRLF re-encoding of a JSON file parses the same with or without `lf_bytes`. The clauses claim
to prove the "blocker 1" CRLF handling, but they would pass if that handling were deleted.
**Fix:** move the CRLF pole to where CR changes the result. Re-encode the hashed content (a committed card or source
blob with CRLF in a temp repo, which must stay CURRENT through `_norm_sha`, and a control using raw `sha256` that must
go SOURCE_CHANGED). For the rendered `.md` evidence, the existing V-SKD/V-SKC-EVIDENCE-DRILL already covers it. Or drop
the JSON CRLF claims from the clause text.

### WR-03: A symlinked live subdirectory is invisible, so a live copy with extra content reads IDENTICAL

**File:** `tools/skill_mirror_drift.py:155-172`
**Scenario (reproduced):** the committed `skills/a/SKILL.md` matches `live/a/SKILL.md`, and `live/a/extra -> /some/dir`
holds `evil.py`. The result is `[('a', 'IDENTICAL', [])]`. `os.walk(followlinks=False)` puts the symlinked directory
in `dirs`, the loop moves it into `kept`, and it is never descended. It is also never recorded as an entry, so neither
`extra_live` nor `excluded` shows it. The docstring says symlinked directories "are not descended". It does not say
they are left out of the comparison altogether.
**Fix:** record a symlinked directory as a file entry hashed by its link text, as is already done for symlinked files:
```python
for d in dirs:
    p = Path(root) / d
    if p.is_symlink():
        rel = p.relative_to(base).as_posix()
        data = os.readlink(p).encode("utf-8", "surrogateescape")
        files[rel] = vgm._norm_sha(data); raw[rel] = hashlib.sha256(data).hexdigest()
    elif d == "__pycache__": excluded += 1
    else: kept.append(d)
```
Add a V-SKD-POLE-DRIFT mutant "extra symlinked dir" that expects `extra_live`.

### WR-04: The card record, H recordings and both evidence files are read from the working tree, not committed blobs

**File:** `tools/skill_mirror_drift.py:335-341` (`load_card_record`), `:253-260` (`card_pairs` reads dispatcher and
hook text from disk through `sc.discover_cards`); `tools/test_skill_drift.py:150-158`, `:309`;
`tools/test_skill_coverage.py:69-70`, `:251`; `tools/skill_coverage.py` (every repo read)
**Scenario:** in this shared checkout a session runs `--record-cards`. That writes
`card_source_digests.json` in the working tree, and nothing is committed. `--cards` and V-SKD-CARD-SOURCE-CURRENT now
read CURRENT, but the committed record that the ledger's prg pins is still stale. The same holds for an uncommitted
`--measure-live` (H-live / D-live json) followed by `--write-evidence`: V-SKD-RECORD-REPRODUCES and
V-SKC/V-SKD-EVIDENCE-CURRENT pass on files that exist only in the working tree. Only the H comparator's repo side was
moved to committed blobs. The record and the evidence it is judged against were not.
**Fix:** read `CARD_RECORD_REL`, `H-live-*.json`, `D-live-*.json` and the two evidence `.md` files through
`vgm.batch_blobs(repo, "HEAD", [...])`, discovering the recordings with `tracked_at`. Derive `card_pairs` from the
committed dispatcher and hook blobs at the same ref as the digests, so discovery and hashing share one plane. If the
working-tree copy differs from HEAD, report INCONCLUSIVE ("uncommitted record").

### WR-05: Most git failures in the card check are labelled UNTRACKED / DRIFT instead of INCONCLUSIVE

**File:** `tools/skill_mirror_drift.py:289`
**Snippet:** `if out and all(r.get("status") == "UNTRACKED" and "git-batch-error" in r.get("reason", "") for r in out):`
**Scenario:** `vgm.batch_blobs` reports a failed `cat-file --batch` as `git-batch-rc<N>` (non-zero exit),
`git-batch-truncated` or `git-batch-badheader`. Only `git-batch-error:` (an OSError or timeout) matches here. So a
`cat-file` that exits 128 after `rev-parse` succeeded turns every pair into `UNTRACKED`. `card_verdict` then says
`DRIFT`, and the operator is pointed at re-deriving cards when the real cause is a git failure. The gate still exits 1,
but the label is wrong, against the "git failure -> INCONCLUSIVE" rule.
**Fix:** match every batch-failure reason that `batch_blobs` emits:
`reason.split(":")[-1].startswith(("git-batch-error", "git-batch-rc", "git-batch-truncated", "git-batch-badheader"))`,
or have `batch_blobs` failures return one sentinel. Add a drill that monkeypatches `vgm.batch_blobs` to return
`git-batch-rc128` and expects INCONCLUSIVE.

### WR-06: `ls-tree` output is not `-z`, so non-ASCII tracked paths silently drop out of the repo side

**File:** `tools/skill_mirror_drift.py:111-121` (through `vgm.tracked_at`), `:134` (dead guard)
**Scenario (reproduced):** with the default `core.quotePath`, `ls-tree` prints `"skills/a/r\303\251f.md"`. The
leading quote fails `p.startswith("skills/a/")`, so the tracked file is never in the repo file list. A byte-identical
live copy then reads `('a', 'DRIFT', extra_live=['réf.md'])` (false DRIFT). A skill whose directory name is non-ASCII
is left out of the population entirely, with no row. The `if r.startswith('"')` guard in `repo_side` can never fire,
because quoted paths are filtered out before they reach it. Measured exposure today: 0 quoted paths under `skills/` at
HEAD.
**Fix:** add a local `tracked_at` that runs `ls-tree -r -z --name-only` (or `-c core.quotePath=false`) and splits on
`\0`. Remove the dead guard, or point it at any quoted path in the raw output and return INCONCLUSIVE.

### WR-07: Registrations written as `script: './x.js'` are invisible to the coverage sweep, and nothing counts the gap

**File:** `tools/skill_coverage.py:61` (`SCRIPT` matches only `../skills/claude-power-pack/...`),
`tools/test_skill_coverage.py:216-230` (V-SKC-REGISTRATIONS)
**Scenario:** CHAIN_MAP registers 76 `script:` entries. Many PreToolUse ones use the `./` form:
`./quality-skill-gate.js`, `./jobs-woz-gatekeeper.js`, `./readonly-prompts-guard.js`, `./quality-gate.js` (all present
in repo `hooks/`, several emit `permissionDecision` / `deny`). The parser skips them silently. A deny card registered
in that form (`./x.js` resolves to the same `hooks/x.js` the parser reads) would classify as `none`. Its card-vs-source
pair would also never be discovered, so H would not watch it. Checked today: none of the `./` PreToolUse hooks has a
`` `<name>` skill `` token, so no current row is wrong. V-SKC-REGISTRATIONS only checks that the parsed entries exist.
It never compares them with an independent count of `script:` lines, so a parser that misses half the registrations
still reads `ok`.
**Fix:** map `./<f>` to `hooks/<f>` in `registered_hooks`. In V-SKC-REGISTRATIONS, count every `script:` line inside
CHAIN_MAP (an independent marker) and FAIL if any is neither parsed nor on a named exclusion list (for example
`tests/fixtures/*`).

### WR-08: The live plane counts 24 directories without SKILL.md as skills, so the two planes use different definitions

**File:** `tools/skill_coverage.py:277`
**Scenario:** `dirs = sorted(p.name for p in entries if p.is_dir() and p.name in installed)`. `installed_names()`
includes every directory, so the gex44 recording lists `vault`, `synced`, `custom skills`, `bmad`, `wii-dev-skills`
and 19 others (`counts.dirs_without_skill_md = 24`). Each one gets a coverage and criticality class in
`D-coverage.md` (`none` / `low`), and the plane is reported as "gex44 185" skills. The repo plane requires
`SKILL.md`. So the `none` and `low` totals on the live plane are inflated by 24 entries that are not skills, and the
`>= REPO_FLOOR` check can be met by directories that are not skills.
**Fix:** use the repo definition on both planes: `p.is_dir() and (p / "SKILL.md").is_file() and p.name in installed`.
Keep `dirs_without_skill_md` as a reported count, re-record gex44, and re-render. If the containers (`bmad`,
`wii-dev-skills`) hold nested skills, discover those explicitly rather than classifying the container.

## Info

### IN-01: V-SKC-CLASS-TOTAL is a tautology
**File:** `tools/test_skill_coverage.py:233-245`. `classify_plane` emits one row per name, and every coverage or
criticality value comes from a closed set of literals, so no input can make this clause fail. Either drive it with a
mutant (a row with an invented class) or fold it into V-SKC-POSITIVE-CONTROL.

### IN-02: `--compare` does not report rows that disappeared, and raises on malformed recordings
**File:** `tools/skill_mirror_drift.py:451-464`. `moved` iterates only over the new rows, so a skill present in the
recording but gone from the repo is not reported as MOVED. `rec.get` on a JSON list (and `old[...]["status"]` on a row
without `status`) raises a traceback. Add `set(old) - {r["skill"] for r in rep["rows"]}` to `moved`, and catch
`AttributeError`/`KeyError` as INCONCLUSIVE.

### IN-03: The router's git-failure branch has no clause
**File:** `tools/test_router_freshness_gate.py`. `PATH=/nonexistent` gives
`('FAIL', ['INCONCLUSIVE: git not found ...'])` (checked by hand on gex44), but no V-RFG clause pins it. Add one that
monkeypatches `smd.vgm._git_exe`, as V-SKD-GIT-FAILURE does.

### IN-04: Small robustness and accuracy nits
`tools/test_skill_drift.py:302-304`: the `evidence_current` docstring says it returns `(ok, diagnostic)`, but it
returns a bool. `tools/test_skill_coverage.py:318`: indexing `["destructive-state-authorization"]` raises KeyError
(a traceback, not a FAIL line) if a recording lacks that skill. Use `.get` and add the failure to `bad`.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
