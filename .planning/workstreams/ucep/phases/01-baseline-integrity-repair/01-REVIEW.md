---
phase: 01-baseline-integrity-repair
reviewed: 2026-10-03T00:00:00Z
depth: standard
files_reviewed: 10
files_reviewed_list:
  - .gitattributes
  - modules/tower/baselines.py
  - modules/tower/donegate.py
  - modules/tower/ratchet.py
  - tools/family_baseline.py
  - tools/test_baseline_generations.py
  - tools/test_tower_donegate.py
  - tools/test_tower_ratchet.py
  - tools/test_ucep_baseline_integrity.py
  - tools/test_ucep_donegate_exits.py
findings:
  critical: 0
  warning: 7
  info: 3
  total: 10
status: partially_fixed
fixed: 2026-10-03
fix_summary: "WR-02..07 and IN-01 fixed (RED then GREEN), IN-03 scan list fixed; WR-01 residual deferred to Phase 3, IN-02 and the IN-03 reason mapping deferred"
---

# Phase 1: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** standard (diff 07f04424..HEAD, 10 files, plus the callees needed to judge them: `modules/tower/checks.py`, `modules/gsd_x/heartbeat.py`, `modules/gsd_x/cli.py`, `tools/test_family_injection.py`, `tools/test_tower_inheritance.py`, and the real `wii_homebrew/B1.json`)
**Files Reviewed:** 10
**Status:** partially_fixed (see "Fix Report" at the end)

## Summary

No BLOCKER. The phase does what ROADMAP S1-S5 say at module level, and the three focus questions that could have been blockers came out clean:

- **`test:` on a hook path.** `checks.py` contains no execution facility (only `os.path.isfile` for `test:`), `donegate.py` is the only caller of `ck.evaluate` in `modules/tower`, and `donegate.judge` has no production caller. No `test:` check can be executed on any hook path today. The H6 remap (`donegate.py:169`) is correct and `V-UCEP-H6-NOT-EXECUTED` has a working positive control.
- **N/A cap arithmetic.** `(30 * n) // 100` over active entries, counting only valid-token claims on active ids, is correct (10 entries -> 3, 15 -> 4, 17 -> 5). Duplicate or unknown ids can only over-count, which fails closed. Vocabulary parsing (`partition(":")`, exact head match, case-sensitive) is correct.
- **Ratchet `diff` kinds.** WHY/ORIGIN/CLASS/SCOPE are all compared with `_squash`, absent equals absent, and `REANCHORED` is the kind `reanchor` records, so recorded moves are accepted and unrecorded ones are regressions.

What remains are robustness gaps in the same escape-route family the phase set out to close (a chain that reads ok when history is missing, an "authority" that is a self-typed word, a done-gate that ignores the chain verdict it computes), one latent absence-read-as-health in the new discovery gates, and the open heartbeat-hermeticity item, which I could identify statically (WR-07).

Verification note: I read all ten files and their callees. I did not re-run the suites: in this tool environment Bash lacked a usable HOME for Python, so the probe runs for WR-07 failed before reaching the suites. WR-07 therefore rests on static tracing, stated as such.

## Warnings

### WR-01: `AUTHORITIES = ("Owner",)` is a self-attested word; the stated residual understates it

**File:** `modules/tower/ratchet.py:67-86` (allowlist), `modules/tower/ratchet.py:149-154` (`_recorded`), `tools/family_baseline.py:153-185` (CLI)
**Issue:** H1's fix turns "any non-empty string" into "any string whose first token is `Owner`". The comment at 67-70 says the residual is "whoever can edit THIS file controls the allowlist". That is not the real residual. The caller of `revert` / `promote` / `reanchor` (the API, or `family_baseline.py revert|reanchor --authority ...`) supplies the authority string itself, so any agent or script that types `--authority Owner` passes. Nobody edits `ratchet.py` to do that. The first-token rule also admits `Owner; acting alone`, `Owner (not asked)`, `Owner, via bot`. Concrete instance already in the tree: the two real generations were written by an executor agent with `Owner (UCEP-01, plan of record ...)` (EVIDENCE A1). The allowlist raises the cost of a typo, not of a forgery, so `V-UCEP-H1-*` proves "x" is refused and cannot prove an agent without the Owner's say-so is refused.
**Fix:** Either (a) state the real residual in the code comment, the module docstring and EVIDENCE section 7 ("authority is a self-declared token; the root of trust is code review of the generation commit"), or (b) bind it to something the caller cannot type: for the CLI, require an Owner-set environment variable or a typed confirmation that an unattended agent does not hold; for the API, make `authority` come from a capability object the caller must be handed. Option (a) is the minimum; do not leave the "allowlist" reading as a control it is not.

**Fix:** cc61c551 option (a): the `AUTHORITIES` comment in `ratchet.py` now states the real residual (self-declared token; root of trust is repo history plus the Owner reviewing generation commits); no behavioural change.
**Deferred:** binding authority to something a caller cannot type (admission records / capability object) to Phase 3 (ROADMAP Phase 3 item 3).

### WR-02: `verify_chain` reads ok when the root of the chain is missing (delete B0 instead of nulling the anchor)

**File:** `modules/tower/ratchet.py:175-191` (loop at 181)
**Issue:** H3b was closed by flagging a child with no `parent_sha256`, but only for pairs from `zip(generations, generations[1:])`. The first listed generation is never checked for being the origin (`generation == 0`, `parent is None`), and a missing predecessor is not a failure.
Snippet:
```python
for prev, cur in zip(rep.generations, rep.generations[1:]):
    ...
    if not anchor: rep.unanchored.append(cur)
```
Scenario: take family F with `B0.json` (strong) and `B1.json` (anchored). Delete `B0.json` and hollow `B1.json` (keep `"parent": 0`, any `parent_sha256`). `generations(F)` is `[1]`, `zip` yields no pairs, `ChainReport.ok` is True, `bl.latest(F)` returns the hollowed B1, and `donegate.judge` / `family_block` judge and inject it. This is the same attack H3b describes (hollow both, remove what pins the parent), done by deleting the parent rather than nulling the anchor; it is cheaper, and it is not covered by `V-UCEP-H3B`. Why existing guards fail: `unanchored` and `tampered` are only computed per consecutive pair; `_GEN` listing silently skips what is absent. A deleted middle generation is incidentally caught as TAMPERED (the child's anchor no longer matches the new neighbour), so only a missing prefix escapes. Severity is WARNING rather than BLOCKER because the accepted trust root is repo history, where a deleted `B0.json` is as visible as a recomputed hash; but it is the cheapest hole in the class this phase closes.
**Fix:**
```python
gens = rep.generations
if gens and gens[0] != 0:
    rep.regressions.append({"generation": gens[0], "id": "*", "kind": "MISSING_ROOT"})
for prev, cur in zip(gens, gens[1:]):
    if cur != prev + 1:
        rep.regressions.append({"generation": cur, "id": "*", "kind": "GAP"})
    if docs[cur].get("parent") != prev: ...  # also flag a parent field that disagrees
```
and add a `V-UCEP-H3B-DELETE-B0` attack gate with a control.

**Fix:** 8ddb5b0b `verify_chain` now flags MISSING_ROOT / GAP / PARENT_MISMATCH (id `*`). RED: V-UCEP-H3B-DELETE-B0, -GAP, -PARENT-FIELD failed on unfixed code (rc=1, 34/37; attack returned ok=True); GREEN 37/37 rc=0 with V-UCEP-H3B-ROOT-CONTROL; real chains still ok.

### WR-03: `donegate.judge` computes `chain_ok` and then ignores it in `would_block`

**File:** `modules/tower/donegate.py:185-187`
**Issue:** `"chain_ok": rt.verify_chain(family, root).ok` is in the report, but `would_block` is `any(x["verdict"] in (VIOLATED, UNJUDGED) ...)` only. A family whose chain is TAMPERED, UNANCHORED or carries unrecorded WITHDRAWN/WEAKENED regressions, with every remaining entry passing, reports `would_block: False`. All the H1/H2/H3b hardening is therefore invisible at the done-gate exit. This was not introduced by this phase, but the phase's S2 and S3 work hardens the chain verdict and the exit in the same change set and leaves them unconnected. It is report-only today (no caller until Phase 6), which is why this is a WARNING; when Phase 6 wires enforcement off `would_block` the chain hardening will not bite.
**Fix:** Include the chain: `would_block = chain_ok is False or any(...)`, expose `would_block_on_chain`, and add one gate: a TAMPERED fixture whose entries all PASS must report `would_block True`, with a clean-chain control reporting False.

**Fix:** a3b35fd6 `would_block = chain not ok OR any VIOLATED/UNJUDGED`; `would_block_on_chain` exposed. RED: V-UCEP-WR03-CHAIN-BLOCKS failed (chain_ok False, all entries pass, would_block False; rc=1, 13/15); GREEN 15/15 rc=0 with V-UCEP-WR03-CLEAN-CHAIN-CONTROL; test_tower_donegate 10/10.

### WR-04: an N/A claim skips evaluation of the entry's check, so a failing evaluable check is hidden (up to the cap)

**File:** `modules/tower/donegate.py:151-167` (the `if ident in na:` branch never calls `ck.evaluate`)
**Issue:** For an entry in `not_applicable` with a valid token and within cap, the check is not evaluated at all. An entry whose `file:`/`regex:` check would be FAIL (VIOLATED) is reported NOT_APPLICABLE, `would_block` can be False, and the report never records that the declared-N/A entry was in fact violated. The vocabulary is closed, but a token such as `no-money` cannot be verified against the entry, so the 30% cap is the only bound, and it still lets 30% of a family's violations disappear into a non-blocking verdict. `V-UCEP-H5-WITHIN-CAP-CONTROL` uses entries whose checks PASS, so it cannot see this.
**Fix:** Evaluate the check for every active entry, including N/A ones, and surface the result: keep `NOT_APPLICABLE` as the verdict but add `na_masked_violation: True` (and a `counts["na_over_failing_check"]`) when `r.outcome == FAIL`, and let `would_block` be True for it. Add a gate where an N/A-claimed entry has a failing `file:` check.

**Fix:** b1732af7 the check is now evaluated for every honoured N/A; a FAIL keeps verdict NOT_APPLICABLE but sets row `na_masked_violation`, report `na_masked_violations`, `counts.na_over_failing_check` and `would_block_on_masked_na`. RED: V-UCEP-WR04-NA-MASKS-FAILING-CHECK failed (violated=0, nothing flagged; rc=1, 15/17); GREEN 17/17 rc=0 with V-UCEP-WR04-NA-OVER-PASSING-CONTROL.
**Deviation from the suggested fix (deliberate):** `would_block` is NOT set True for a masked N/A. Reading the code and `test_tower_donegate.py` V-TDG-VERDICT-KINDS, a legitimate N/A is typically a `glob:`/`file:` check for a surface that does not exist (that test's `web-mobile` over `glob:tests/mobile_*.py` is exactly this and must stay honoured). Blocking on it would defeat the closed-vocabulary N/A mechanism; the failure is instead named at row, count, list and flag level so the Phase 6 enforcer can decide with the information in hand.

### WR-05: `discover_subjects` can silently return fewer subjects; the floor is frozen at today's population

**File:** `modules/tower/baselines.py:132` (`os.walk(base)`), consumers `tools/test_tower_ratchet.py` (`V-TRAT-REAL-CHAINS`) and `tools/test_baseline_generations.py` (`V-BGEN-REAL-B0-CITATIONS-HOLD`)
**Issue:** `os.walk` defaults to `onerror=None` and `followlinks=False`. A subdirectory that cannot be listed (permission, a transient lock on Windows) is skipped without a word, and a symlinked subject directory (a Linux or CI checkout, `core.symlinks=true`) is listed in `dirnames` but never descended. Either way the subject is not in the result and nothing says so. The only defence is the floor (`>= 4` subjects, `>= 60` active entries), which equals the current population: losing any of today's four subjects is caught, but the Phase 4 `archetype/<ID>` subjects this function exists for are above the floor and a dropped one is invisible, which is exactly "absence read as health". Positive control only proves a planted subject is found when the walk works.
**Fix:** `os.walk(base, onerror=_raise)` where `_raise(e)` re-raises, so an unreadable directory is loud. Replace the static floor with a cross-check against an independent enumerator: every id from `modules.tower.families.load_families()` must be in `discover_subjects()`, and (when git is available) the discovered count must equal the distinct parent directories of `git ls-files vault/tower/baselines/**/B*.json`.

**Fix:** 6c6835f6 `baselines.discover_report()` walks with `onerror` and records unreadable/symlinked dirs; `discover_subjects()` raises `SubjectDiscoveryError` rather than return a short list. New `tools/baseline_population.py` cross-checks the walk against the family registry, the git index (one-directional: every tracked subject must be discovered; untracked new ones are allowed), a glob and a raw-JSON active-entry count; the three real-tree gates fail on any unreadable dir or disagreement, and the 4/60 floor is kept only as a lower bound (it equals today's count by coincidence: 4 families == 4 subjects, 62 entries). RED: V-UCEP-DISCOVER-UNREADABLE/-SYMLINK failed (faulted dir gave `listed=['a']`, no signal; rc=1, 37/40); GREEN 40/40 rc=0, with V-UCEP-DISCOVER-CROSSCHECK-CONTROL proving the cross-check fires on a dropped and an invented subject. On this host the git route ran (unavailable routes: none).

### WR-06: `real` in `V-BGEN-REAL-B0-CITATIONS-HOLD` is keyed by entry id alone, so duplicate ids across discovered subjects mask a broken citation

**File:** `tools/test_baseline_generations.py:206` (`real[e["id"]] = bl.verify_origin(e)`)
**Issue:** The change replaced a four-family tuple with `discover_subjects()`, whose point is nested subjects such as `archetype/<ID>`. Entry ids were unique across the four families only by naming convention (`<family>-...`). Nested archetype subjects derived from shared rules will not necessarily keep that convention. With a shared id the later subject overwrites the earlier verdict, so a broken or QUOTE_MISSING entry in one subject is replaced by a VERIFIED one from another, `broken` stays empty, and `len(real) >= 60` counts distinct ids rather than entries. Latent today (62 distinct ids), but introduced by the generalisation.
**Fix:** Key by `(subject, id)`: `real[(fam, e["id"])] = ...`, and `moved`/`broken` listings use the pair. Floor on `len(real)` then counts real entries.

**Fix:** 099a6579 verdicts come from `_citation_verdicts()`, keyed `(subject, id)`; the real gate also requires `len(real)` to equal the raw-JSON active-entry count. RED: V-BGEN-REAL-KEY-NOT-MASKED (two subjects sharing an id, one with a missing origin file) failed on the id-keyed logic (population=1, broken={}; rc=1, 16/18); GREEN 18/18 rc=0 with V-BGEN-REAL-KEY-CONTROL.

### WR-07: the heartbeat write under the real HOME comes from `test_tower_inheritance.py` and `test_family_injection.py` (resolves EVIDENCE open item; both outside the 10-file scope)

**File:** `tools/test_tower_inheritance.py:137-141` (and no HOME redirect anywhere in the file); `tools/test_family_injection.py:31, 81, 156`; root cause `modules/gsd_x/heartbeat.py:31`
**Issue:** `heartbeat._STATE` is computed once at import: `Path(os.environ.get("CLAUDE_STATE_DIR") or (Path.home() / ".claude" / "state"))`. `cli.main()` (cli.py:201/206) calls `heartbeat.record`, which writes `gsd-x-heartbeat.json` there, fail-open.
- `test_tower_inheritance.py::_c2` calls `cli.main()` in-process (lines 137-141). The file never sets HOME/USERPROFILE (a grep for HOME/USERPROFILE finds nothing); it only monkeypatches `tc._state_dir` and `cli._tower_dir`, which do not cover the heartbeat. So the real `~/.claude/state/gsd-x-heartbeat.json` is read-modify-written.
- `test_family_injection.py` claims at lines 10-11 that heartbeats never touch the real `~/.claude`, but it imports `modules.gsd_x.cli` at top level (line 31, which imports `heartbeat`) before `main()` swaps HOME (line 81), so `_STATE` is already bound to the real home; `run_main` (line 156) calls `cli.main()` in-process and writes there. Its subprocess runs use `env` with the temp HOME and are fine.
- This matches the EVIDENCE control run: with the outer HOME on a temp dir, the import-time binding lands the file there regardless of the inner swap.
Effect: every run of these suites on a live machine increments the production heartbeat counters (`judgements`, `by_tier`, `recent`), polluting the signal `informative_rate()` exists to report. It is also why a before/after listing of `~/.claude/state` cannot be clean. Static identification only; not re-run here.
**Fix:** In both test files set `os.environ["CLAUDE_STATE_DIR"]` to a temp dir before importing `modules.gsd_x.cli` (or monkeypatch `heartbeat.HEARTBEAT` / `heartbeat._STATE` after import and restore it), and add a gate that the real heartbeat's mtime/size is unchanged across the run. Better, make `heartbeat` resolve its path at call time (`def _path(): ...`) so a HOME swap is honoured, the same call-time rule `discover_subjects` follows.

**Fix:** 1ba16a61 `heartbeat.py` now resolves its path per call (`heartbeat_path()`: `CLAUDE_STATE_DIR` first, else `<home>/.claude/state` -- the old formula, so the live hook is unchanged for the real home; `heartbeat.HEARTBEAT` stays resolvable via module `__getattr__`; no longer raises at import with no home). Both suites pin `CLAUDE_STATE_DIR` to a temp dir (restored in `finally`) and gain `V-TINH-HEARTBEAT-HERMETIC` / `V-FINJ-HEARTBEAT-HERMETIC`; new `tools/test_gsd_x_heartbeat_path.py` (7 gates) proves call-time resolution (env and HOME swap), identical live layout, and fail-open. RED on the unfixed module: heartbeat_path 0/7, inheritance 16/17, family_injection 23/24 (all rc=1). Real `~/.claude/state` bracket around both suites: before fix the heartbeat moved (size 3550 -> 3552, mtime changed); after fix unchanged (3594 -> 3594, identical mtime). GREEN 7/7, 17/17, 24/24.
**Deviation (deliberate):** the in-suite gates assert the heartbeat LANDED in the temp state dir rather than that the real file's mtime is unchanged. Measured 2026-10-03: with NO suite running, the real `gsd-x-heartbeat.json` changed twice in a 60 s idle window (live UserPromptSubmit hooks of other sessions write it), so an mtime/size gate on the real file is racy and the before/after bracket above is CONFOUNDED, not proof by itself. The decisive evidence is the redirect: RED gates show the temp state dir stayed empty (the heartbeat went elsewhere) before the fix, GREEN shows it holding the judgements after. Final gate-run bracket (all 13 suites): heartbeat 3616 -> 3612 bytes, but per-suite brackets show only `test_family_baselines` (which has no gsd_x/heartbeat/subprocess reference) coincided with a change, i.e. ambient writers, not these suites.

## Info

### IN-01: `test_ucep_donegate_exits.py` prints a self-satisfying threshold and does not restore HOME

**File:** `tools/test_ucep_donegate_exits.py:132` and `:292-293`
**Issue:** `threshold=%d/%d` is printed as `_PASS + _FAIL` over itself, so deleting a gate (or a gate that never runs) still prints `N/N`; only the exit code, driven by `_FAIL == 0`, carries the verdict. `test_ucep_baseline_integrity.py` hard-codes `33/33` but its exit is also `_FAIL == 0`, so it does not enforce the count either. Also `os.environ.update(HOME=home, USERPROFILE=home)` is never restored (the sibling file restores in `finally`), so a runner that imports `main` leaks the temp HOME.
**Fix:** `return 0 if _FAIL == 0 and _PASS == EXPECTED else 1` with a literal `EXPECTED` in both files; save and restore HOME/USERPROFILE in `finally`.

**Fix:** 66556c06 literal `EXPECTED` (17 and 40) in both files, exit 0 only when `_FAIL == 0 and _PASS == EXPECTED`; `test_ucep_donegate_exits.py` restores HOME/USERPROFILE in `finally`. RED: with `EXPECTED` raised by one both suites exit 1 although every gate passes (before, they exited 0); GREEN 17/17 and 40/40, rc=0.

### IN-02: `V-UCEP-REAL-REANCHORED` will go red on the next legitimate generation, and depends on trees outside the repo

**File:** `tools/test_ucep_baseline_integrity.py:606` (`gens == [0, 1]`), `:602-603` (every active entry `== VERIFIED`)
**Issue:** The gate pins `generations == [0, 1]` for both families and requires every active entry VERIFIED. Any later promote, revert or reanchor (for instance the 14 MOVED citations the EVIDENCE leaves open) turns it red although nothing regressed; and the VERIFIED check reads the PP main checkout and `...\Wii Projects\CavEX\...` absolute paths (EVIDENCE A3), so it cannot pass on another machine or CI. The same out-of-repo dependency already existed in `V-BGEN-REAL-B0-CITATIONS-HOLD`, so this extends it rather than creating it.
**Fix:** Assert `gens[:2] == [0, 1]` and that B1's `changes` keys equal the 9 ids; keep the F0 sha check; move the VERIFIED-on-disk assertion to the citations gate only, with a declared status for hosts lacking those trees (INCONCLUSIVE, not PASS).

**Deferred:** not a one-line fix (needs a declared INCONCLUSIVE status path and a restructure of `V-UCEP-REAL-REANCHORED`), outside the fix scope for this pass. Revisit before the first legitimate B2 on `persistent_state` / `wii_homebrew` (the next `reanchor` of the 14 MOVED citations will turn the gate red by design), or when the suite is first run off this host.

### IN-03: the no-exec scan covers two files; the unjudged reason `other` lumps three instrument failures

**File:** `tools/test_ucep_donegate_exits.py:210` (scan list), `modules/tower/donegate.py:73-74`
**Issue:** `V-UCEP-NO-EXEC-IMPORTS` scans `checks.py` and `donegate.py`, but `judge` also runs `ratchet.verify_chain`, `baselines`, `select` and `checks` helpers; an exec facility added to `ratchet.py` or `select.py` is outside the static scan (the dynamic marker would still catch a `test:` execution, which is the part that matters). Separately `_REASON_FROM_OUTCOME` maps only PROSE/EMPTY/UNREADABLE; MALFORMED, REFUSED_PATH and ERROR all become `unjudged_reason: "other"`, so a `test:` path that escapes the repo root (REFUSED_PATH) is indistinguishable from an evaluator crash in the report.
**Fix:** Add `ratchet.py`, `baselines.py`, `select.py` to the scan list; map `REFUSED_PATH -> "refused-path"`, `MALFORMED -> "malformed"`, `ERROR -> "evaluator-error"`.

**Fix (scan-list half):** 66556c06 `V-UCEP-NO-EXEC-IMPORTS` now scans `checks.py`, `donegate.py`, `ratchet.py`, `baselines.py`, `select.py` (passes: none contains an exec facility).
**Deferred (reason-mapping half):** `MALFORMED` / `REFUSED_PATH` / `ERROR` still map to `unjudged_reason: "other"`; changing the report vocabulary needs its own gate and is not a one-line fix. Do it with the first consumer that must tell a refused path from an evaluator crash (Phase 6).

## Fix Report (iteration 1, 2026-10-03)

Fixes applied on `ucep/mission` by gsd-code-fixer, one commit per finding, RED (fails on the unfixed code) then GREEN:

| Finding | Commit | Outcome |
|---|---|---|
| WR-01 | cc61c551 | comment states the real residual; behaviour unchanged; control deferred to Phase 3 |
| WR-02 | 8ddb5b0b | fixed: MISSING_ROOT / GAP / PARENT_MISMATCH |
| WR-03 | a3b35fd6 | fixed: `would_block` includes the chain |
| WR-04 | b1732af7 | fixed (visibility): masked N/A reported; `would_block` deliberately unchanged |
| WR-05 | 6c6835f6 | fixed: unreadable/symlinked dirs loud; cross-checked against independent enumerators |
| WR-06 | 099a6579 | fixed: keyed `(subject, id)` |
| WR-07 | 1ba16a61 | fixed: heartbeat path resolved per call; suites hermetic |
| IN-01 | 66556c06 | fixed |
| IN-03 | 66556c06 | scan list fixed; reason mapping deferred |
| IN-02 | -- | deferred |

### Deferred

- **WR-01 (Phase 3, admission records, ROADMAP Phase 3 item 3):** the authority is a self-declared token that any caller of `revert`/`promote`/`reanchor` can type; the allowlist raises the cost of a typo, not of a forgery. The root of trust today is repo history plus the Owner reviewing the commit that adds a generation. Binding authority to a record the caller cannot type is Phase 3 work; no signing or crypto was invented here.
- **WR-04 (decision, not a gap):** a masked N/A is surfaced, not blocked; Phase 6's enforcer can read `would_block_on_masked_na`.
- **IN-02:** see above.
- **IN-03 reason mapping:** see above.

### Phase gate (post-fix, Windows, python 3.12, real HOME)

| Suite | Result line | rc |
|---|---|---|
| test_baseline_generations | BASELINE_GENERATIONS_PASS=18/18 | 0 |
| test_tower_ratchet | TOWER_RATCHET_PASS=21/21 | 0 |
| test_tower_donegate | TOWER_DONEGATE_PASS=10/10 | 0 |
| test_family_baselines | FAMILY_BASELINES_PASS=20/20 | 0 |
| test_ucep_baseline_integrity | UCEP_BASELINE_INTEGRITY_PASS=40/40 | 0 |
| test_ucep_donegate_exits | UCEP_DONEGATE_EXITS_PASS=17/17 | 0 |
| test_tower_select | TOWER_SELECT_PASS=15/15 | 0 |
| test_tower_checks | TOWER_CHECKS_PASS=23/23 | 0 |
| test_tower_capsule | TOWER_CAPSULE_PASS=16/16 | 0 |
| test_tower_inheritance | TOWER_INHERITANCE_PASS=17/17 | 0 |
| test_family_injection | FINJ_PASS=24/24 | 0 |
| test_tower_o4 | TOWER_O4_PASS=7/7 | 0 |
| test_gsd_x_heartbeat_path (new) | GSD_X_HEARTBEAT_PATH_PASS=7/7 | 0 |

Also `tools/test_gsd_x.py` rc=0 (heartbeat reload gates) under an isolated `CLAUDE_STATE_DIR`. Verification ran in the isolated worktree `...\.claude\worktrees\ucep` (branch `ucep/mission`), against the real HOME for the two heartbeat suites; the four B0 files and `web_surface`/`persistent_state`/`wii_homebrew` B1 were not touched.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
