---
phase: 00-spec-gen2-freeze-novelty-gate
reviewed: 2026-10-06T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - tools/gex44_env_preflight.py
  - tools/ic_gen2.py
  - tools/test_ao_p0.py
  - tools/test_gex44_env_preflight.py
  - tools/test_incremental_cognition_program.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 00: Code Review Report

**Reviewed:** 2026-10-06
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the diff since c0796c82 for the five files. The three focus areas:

- **pp_install floor (fail-open risk).** The abbreviated trailer and the different-40-hex trailer are correctly refused. Probed with real git: a 41-char superstring sha does not match, and the floor abbreviated to 8 chars does not match. The required-files check still runs on every accept path, and git failures map to UNMEASURABLE, never READY. One real hole remains: the trailer match is a substring match over the whole message, not a trailer-line match (WR-01).
- **ic_gen2 `bound()` leak risk.** `bound()` snapshots before the `try` and restores in `finally`. All seven CE globals (SELF_REL, LEDGER_REL, FROZEN_AT_REL, HANDOFF_DIR, PILLARS, REQS_REL, REQ_ROW) are exactly the gen-specific module globals CE defines. Nested use restores correctly. I found no leak.
- **Selftest mutants.** Each mutant must produce a line with its expected label prefix, and a clean control runs first. The preflight drill requires every named target to flip to False, and it restores the patched attribute in `finally`. I found no mutant that cannot fail. One gap in what is not mutated is noted in IN-04.

The defects found are an uncaught-exception path in the champion judge, a coupling of the generation-1 gates to generation 2, a directory-confinement bypass, and the trailer anchoring.

## Warnings

### WR-01: Cherry-pick trailer accepted anywhere in a commit message, not only as a trailer line

**File:** `tools/gex44_env_preflight.py:271`
**Issue:** `_has_pick_trailer` runs `git log -F --grep "(cherry picked from commit <floor>)"`. `-F` with `--grep` is a substring match over the full message. The docstring and the task claim an "exact trailer", but any commit whose prose merely quotes the string is accepted. I reproduced it with a throwaway repo. A commit with message `docs: prose only, not a pick: (cherry picked from commit <40a>) ok?` matched with the current command. An anchored pattern did not match it. A real trailer matched under both. A commit that talks about this floor in its body, for example one documenting this very check or a revert note, would turn a stale install into READY via `cherry_pick_trailer`. This is the one path that works with the floor object absent, so no other signal backstops it. It also weakens the claim in the `check_pp_install` docstring that the floor sha proves repo identity, because that now holds only for the ancestry path. `floor_by_pick` is reported as a finding, but a finding does not refuse.
**Fix:** Anchor to a whole line. Do not use `-F`. In the default BRE, `(`, `)` and the hex digits are literal, and `^` and `$` anchor per message line:
```python
rc, out, _ = sbx.run([git, "log", "--grep", f"^(cherry picked from commit {floor})$",
                      "--format=%H", "--max-count=1", "HEAD"], cwd=install)
```
Add a regression case to `make_pick_install` (`spoof=True` variant) with the floor's full 40-hex embedded mid-line in prose. Add it to M9's targets. The existing spoof only covers a different sha and an 8-char abbreviation, so an unanchored match still passes the suite today.

### WR-02: `g2_champ` raises on a malformed ledger instead of reporting a failure

**File:** `tools/ic_gen2.py:318-322`
**Issue:** The ratio recomputation guards `wall_s` with `isinstance` but not `read_GB`. The guard is `r6["wall_s"] and r6.get("read_GB")`, and the divide is `r5["read_GB"] / r6["read_GB"]`. I confirmed both crashes by calling `g2_champ` on a mutated copy of the real ledger. With `run5.read_GB` removed it raises `KeyError: 'read_GB'`. With `run5.read_GB = "101.5"` it raises `TypeError`. The scalar mismatch lines were already appended, but the exception discards them. Effects:
- `--generation 2 --status` never prints its JSON.
- `--final` prints no `ICP_GEN2_VERDICT` line.
- `--audit` prints no `ICP_GEN2_AUDIT` line.
- The process exits 1 with a traceback, not the documented 0/1/2 contract.
- In `selftest`, the same input raises out of `judge()` and crashes the whole selftest, so it cannot be reported as a killed mutant.

A done-gate that parses `ICP_GEN2_*` lines sees nothing. A downstream consumer cannot tell a judged failure from a crash. The same class of unguarded access exists in `audit_rules` (`sorted(p.get("roadmap_phases") or [])` at line 400 and `sorted({...p.get("owner")...})` at line 406 raise on mixed-type lists).
**Fix:**
```python
num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
if r5 and r6 and all(num(r5.get(k)) and num(r6.get(k)) and r6[k] for k in ("wall_s", "read_GB")):
    ...
```
Report a `G2-CHAMP ... is not a number` line otherwise. Add a mutant "run5-read-GB-removed" expecting `G2-CHAMP`. Optionally wrap `problems()` in `main` so an unexpected exception prints `ICP_GEN2_VERDICT=COULD_NOT_RUN` and returns 2.

### WR-03: Generation-1 `--final` and `--selftest` are now hard-coupled to ic_gen2 and the gen2 ledger; `--generation 1` is not honored

**File:** `tools/test_incremental_cognition_program.py:1349-1380` (also 1312-1328)
**Issue:** The comment at 1349 says `# lazy: generation 1 never loads it`, and `_generation` documents "Absent -> 1". The code does the opposite. Bare `--selftest` (1355) and bare `--final` (1370) import `ic_gen2` unguarded and fold its result into the gen1 exit code. `--generation 1 --final` takes the same path, because `gen == 1` falls through to `"--final" in argv`. Consequences:
- A checkout or copy that has the wrapper but not `tools/ic_gen2.py`, the gen2 ledger or `modules/sdd_os` gets `ModuleNotFoundError` from a gate that was self-contained before. The existing owner bundle (`vault/programs/incremental-cognition/owner-bundle.md:76-85`) checks out an explicit file list for the wrapper and then runs `--selftest`. That list does not include `ic_gen2.py`.
- `--final`'s exit code is now `0` only if gen2 final also passes. Gen2 is open by design until phase 7, so gen1 `--final` can never be judged on its own. A gen2 COULD_NOT_RUN (rc 2) overrides gen1's result.
- Gen1 `--final` prints gen2's `L3` and `L8` FAIL lines under gen1's output, so a reader and any log scraper see gen2 failures beside `ICP_VERDICT`. D-OQ3 says gen1 reporting is unchanged.

**Fix:** Make `--generation 1` mean gen1 only: handle `gen == 1` with `g_argv` (the `--generation` tokens stripped) and keep the old behavior byte for byte. Run the gen2 leak check (`check_binding`) as an addition that is skipped with a visible "gen2 not present" note when `ic_gen2` cannot be imported, and keep gen2's own verdict on `--generation 2`. Fix the comment at 1349 either way.

### WR-04: G2-CHAMP directory confinement is bypassable with `..`

**File:** `tools/ic_gen2.py:246`
**Issue:** `ref.startswith(CHAMP_DIR)` is a string-prefix check. `…/evidence/champion/../../owner-bundle.md` passes it. I confirmed this: the ref is accepted past the confinement check and only the later sha comparison complains. The rule exists so that champion evidence is only the byte-copied files in `evidence/champion/`. With a correctly pinned sha (`source_sha256 == sha256`, which the ledger author writes), a ref that resolves anywhere else in the repo, or to an absolute path through `Resolver._path`, satisfies the rule. The selftest mutant `champion-evidence-outside-dir` only tests a ref with no `champion/` prefix, so it never exercises this.
**Fix:**
```python
norm = posixpath.normpath(ref)
if not (isinstance(ref, str) and norm.startswith(CHAMP_DIR) and ".." not in ref.split("/")):
```
Add a mutant using `CHAMP_DIR + "../owner-bundle.md"` (with the sha computed from that file) expecting `G2-CHAMP`.

## Info

### IN-01: Literal invisible BOM character in source

**File:** `tools/ic_gen2.py:563`
**Issue:** `r.stdout.lstrip("<U+FEFF>")` embeds a raw U+FEFF in the string literal. It is invisible in review, triggers injection scanners, and is easy to lose in an editor round-trip, which would silently turn this into `lstrip("")`.
**Fix:** `r.stdout.lstrip("<U+FEFF>")`.

### IN-02: Temp directories are never removed

**File:** `tools/test_ao_p0.py:31, 190 (make_temp_repo), 387`
**Issue:** `_STATE_DIR`, every `make_temp_repo` directory (4 mutants) and the `aop0-novrepo-` repo are created with `mkdtemp` and never deleted, so each run leaks several directories under the system temp.
**Fix:** `atexit.register(shutil.rmtree, path, ignore_errors=True)` for each, or one `TemporaryDirectory` held at module level.

### IN-03: A trailing bare `--generation` silently selects generation 1

**File:** `tools/test_incremental_cognition_program.py:1312-1328`
**Issue:** With `--generation` as the last token and no value, the first branch is skipped (`i + 1 < len(argv)` is false). The token falls into `rest` and the default `gen = 1` is used. The caller gets a gen1 run, which is the wrong ledger, with no error.
**Fix:** If `a == "--generation"` and there is no next token, return `(None, rest)` so `main` prints the existing COULD_NOT_RUN usage error.

### IN-04: Test gaps around the new accept paths

**File:** `tools/test_gex44_env_preflight.py:431-445`
**Issue:**
- No case asserts that the ancestry path emits no `floor_by_pick` finding. `V-ENVPF-PP-READY-VIA-ANCESTRY` checks only `floor_via`, so a mutant that always appends the finding survives.
- No case covers a trailer for the right floor present while the required file is dropped with the floor object absent. `V-ENVPF-PP-PICK-REQUIRED-FILE` covers the floor-present variant only.
- Nothing covers the mid-line lookalike (see WR-01).

**Fix:** Add `expect_no_finding`, plus one `make_pick_install(floor_absent=True, drop_required=True)` case, plus the WR-01 case with a mutant that removes the anchor.

### IN-05: Evidence files keyed by basename in `g2_champ`

**File:** `tools/ic_gen2.py:257`
**Issue:** `texts[ref.rsplit("/", 1)[-1]]` keys by basename. Two evidence entries with the same basename silently overwrite each other, and the one later picked up as the summary, log or runner is the last one listed. `summ` is selected by `k.endswith("summary.txt")`, so `run5-summary.txt` and `xrun6-summary.txt` collide on the same predicate across runs. Also, `if "population" in r:` at line 290 makes the population check optional, so a ledger that drops the `population` key skips it with no failure line.
**Fix:** Key by the full `ref` and select by exact expected names. Treat a missing `population` as a failure.

---

_Reviewed: 2026-10-06_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
