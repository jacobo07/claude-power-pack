# CCP §16.1 C6-C9 -- phase-4 adversarial audit

Auditor: oneshot-architect-auditor (phase 4, /ultra plan "CCP §16.1 C6-C9"), 2026-10-03.
Subject: `vault/plans/ccp-s16-longitudinal-economics-2026-10-03.md` §16.1 (lines 82-127).
Scope: read-only; findings appended as confirmed.

State observed during the audit: H0 had already landed (`1703e609`), and a W1 draft was sitting uncommitted in
`tools/rollover.py` (mtime 09:58:56, `ledger()` at 616-682). Execution ran alongside this audit, so W1 is judged on
that live draft.

## Gaps

### G1 HIGH -- D1: decide() must stay pure. The callers load the prior; decide does not (Q1)
- `test_rollover.py:169-171` V-ROLLOVER-BREAKEVEN calls `decide(u, 4000, True, 40.0, ratio)` with the DEFAULT
  horizon and expects `would_rollover` True (n* 18.2 <= 30). `rollover_replay.judge` calls `ask(rollover.HORIZON_CALLS)`,
  `ask(10**9)` and float horizons `v - c/growth` (`rollover_replay.py:302-324`).
- Suppose decide read the artifact whenever it got the default. The test sets `ro.STATE_DIR` to a temp dir, so there
  is no artifact there, the result is UNKNOWN, the decision is UNDETERMINED and the gate goes red. Replay passes 30
  explicitly, so it would stay on the int path. Its "shipped" column would then quietly change meaning: it would be
  the legacy constant, not what ships.
- Fix: decide accepts `horizon: int | float | dict(evidence)`. An int or float keeps today's semantics and is
  labelled ESTIMATE. A dict carries `{values, basis, rehydration}`. A new `load_prior(state_dir)` lives in
  rollover.py and is called by `observe` (rollover.py:711) and `rollover_econ.evaluate` (rollover_econ.py:55).
  When the artifact is absent, those callers pass `{basis: UNKNOWN}`. They never fall back to 30, which is what Q2
  decided.
- Tests to add:
  - an econ row with no artifact has `horizon_basis` UNKNOWN and `would_rollover` False;
  - with an artifact, the basis is MEASURED;
  - a drill where a caller omits the evidence must go red.
- Rename replay's "shipped" to "legacy-30" once D1 lands.

### G2 MEDIUM -- C/G cannot explode, and ROBUST_ROLLOVER is reachable but late (Q1 second half, Q2)
- decide returns at `growth < MIN_GROWTH_TOKENS` before any horizon is considered (rollover.py:527-528). So every
  horizon-judged state has G >= 150k, which bounds C/G at 1.86M/150k = 12.4 calls (p90 4.53M gives 30.2).
- The price ratio (w-r)/r is about 39. That is the fixture at test_rollover.py:167 (8.0/0.2), and it also matches
  the plan's golden n* = 25.6 at G ~ 210k. With fresh ~ 129k:
  - G = 150k: n* ~ 33.5, so the threshold n*+C/G ~ 46 calls;
  - G = 300k: n* ~ 16.8 + 6.2 = 23.
- So UNDETERMINED is NOT structurally guaranteed. Whether a state is decided depends on the prior's tail.
- Real data (plan C4 table) agrees. With +p50 rehydration, 14 boundaries were W (WOULD), against 29 with the prior
  alone. Golden's first robust boundary moves from call 96 to call 168, with 46 of its 214 calls left. That is
  coherent for a ROBUST predicate over C in [0, C_p50]. Robust on the C=0 side for CONTINUE, robust at C_p50 for
  ROLLOVER: this is the correct interval logic.
- Caveats:
  - (a) "robust" covers only C up to the p50 of an UPPER bound, not p90. The basis label must name it
    (`UPPER_BOUND_P50`).
  - (b) No real boundary was ever horizon-driven to CONTINUE (negative control PARTIAL). ROBUST_CONTINUE and
    UNDETERMINED both act as `would_rollover` False, so they are labels only. No claim of ROBUST_CONTINUE on real
    data is allowed.
  - (c) Expect fewer economic asks than today. That is accepted under Q2.

### G3 HIGH -- The prior artifact has an expiry and no refresher
- R1 writes the artifact with `expires`, but `prior --write` is a manual CLI and nothing schedules it.
- After expiry, every econ and shadow decision becomes UNKNOWN. The economic trigger then retires to the 45 % wall
  without telling anyone. That is a "documented capability that nobody executes".
- Fix, pick one and name it in the plan:
  - (a) `rollover_econ.evaluate`, which is already detached, refreshes an expired artifact before deciding;
  - (b) a scheduled task.
- In both cases a row reason "prior expired/absent" is counted, and P1 must show a receipt with basis MEASURED.
- The source is the usage_index sqlite (rollover_replay.py:278-286). The index's own freshness is a dependency:
  record `max(ts)` and treat a stale index as UNKNOWN.
- Declare the minor bias: a live global artifact cannot exclude the reader's own capsule chain, which replay does
  (rollover_replay.py:362).

### G4 HIGH -- W1: a dropped capsule_sealed row is reported, but nobody acts on the report
- The draft `ledger()` now returns bool (rollover.py:646). Both control-row writers ignore it:
  - `rollover.py:811-819`: seal still prints the verdict SAFE_TO_FORGET and exits 0;
  - `session_checkpoint.py:331-336`: prints "[capsule] SAFE_TO_FORGET -> ... /clear".
- After a dropped row, the gate answers NO_CAPSULE (rollover.py:454-456). The model has already been told to /clear,
  and the ASK flow stalls. It fails closed, so this is availability, not safety. But the message is false.
- Fix: both callers check the return. On False they print "[capsule] UNKNOWN -- receipt not recorded, seal again"
  and the CLI exits 3.
- Add a test: monkeypatch the lock to stay busy, then assert the message is not SAFE_TO_FORGET.

### G5 MEDIUM -- W1 lock: the local idiom is correct; three details need fixing (Q3)
- Lock helpers that already exist: `gsd_mission._Lock` (gsd_mission.py:137-186), `pp_eval.common.Lock`
  (modules/pp_eval/common.py:77-110) and `gsd_sweep_pass` (59-63). Importing gsd_mission into rollover.py would
  add a heavy dependency for 20 lines. A local copy is right, and that is what the draft does.
- The sidecar placement is correct and must stay:
  - `rollover-ledger.lock` and `ledger-failures/` sit in state/rollover. Nothing globs that level:
    `newest_capsule` globs `capsules/*.json` (676-678), decisions/ is its own subdir, and `walk_cache_guard` globs
    ~/.claude/state non-recursively.
  - Locking the LEDGER file itself would have been a bug. msvcrt locks are mandatory on Windows, so
    `sealed_receipt`'s read (rollover.py:425) would raise OSError, return None, and the gate would answer NO_CAPSULE.
- Details to fix:
  - (a) The docstring cites `gsd_mission.MissionLock`, which does not exist (the class is `_Lock`). It also cites
    `test_rollover_ledger_race` and "258/900", but that test is absent from tools/ at audit time. Land the test in
    the same commit, or fix the text. The number in the docstring must come from a committed run.
  - (b) `LEDGER_LOCK_TIMEOUT_S = 5.0`. The only FOREGROUND caller is the watchdog's gate subprocess, with
    `timeout=20` (context-watchdog.py:990-991), and it writes `reset_gate` after the verdict (rollover.py:798).
    Python startup on a starved host plus 5 s still fits, but a loss there is telemetry only. Recommend <= 2 s.
    Econ (1215-1238) and shadow (1087+) are detached pythonw, so no hook blocks on them.
  - (c) The never-raise behaviour is preserved for OSError. A non-serializable field raises TypeError outside the
    try, but that was already true before the draft.

### G6 MEDIUM -- S1 and D1 contradict the owner spec, so the spec must change in the same commits
- S1: `vault/specs/interactive-context-rollover.md:67-68` says "A dirty tree is recorded, not refused (it survives a
  reset on disk; peers' writes are dirty too)." The S1 commit must amend §4. The rationale to record: dirty edits in
  ANOTHER repo survive on disk, but no successor inherits them as an obligation, which is exactly the orphan-hunk
  incident.
- D1: §5 (lines 75-76) says "N* ... <= 20". The code says `HORIZON_CALLS = 30` (rollover.py:47). That drift already
  exists today. D1 must rewrite §5 with the evidence and basis rule.

### G7 MEDIUM -- S1: the narrowest predicate (Q4)
- Plan wording risk: a check that reads the dirty state of whole repos, or any refusal driven by the capsule repo's
  own dirt, would refuse almost every session in a tree with 769 dirty paths.
- Predicate:
  - Compute it in `compile_capsule` and seal it into the capsule as `custody`, so the evidence is part of the
    receipt.
  - Judge it in `completeness()` as a `missing` entry. `safe_to_forget(receipt, comp)` stays as it is.
  - Steps:
    - (1) Take the FULL `session_writes(tp)` list, not `[-15:]` (rollover.py:310, 328).
    - (2) Resolve each path's root with `git -C <parent> rev-parse --show-toplevel`, compared with `_pathkey`.
    - (3) Skip roots equal to the capsule repo root. That repo's dirty set is already recorded (spec §4).
    - (4) A path outside any repo is `uncovered`: a warning, not a refusal.
    - (5) Run one pathspec-limited `git -C <root> status --porcelain --untracked-files=all -- <paths>` per foreign
      root. Refuse iff it returns rows, and name the paths.
    - (6) A git failure or timeout is UNKNOWN, so it is missing and REFUSED, per the spec's "UNKNOWN counts as
      absent".
- Effects:
  - The pathspec hides peers' dirt on other paths.
  - The one remaining refusal on a peer's dirt is a peer editing the SAME file. Refusing there is correct, because
    custody is shared.
  - Case a4849588: cwd Orca-X, Edit on PP `tools/rollover.py`, foreign root PP, ` M` gives REFUSED.
- Known aperture to declare: files written through Bash/PowerShell (Set-Content, sed, redirects) are invisible to
  `session_writes` (rollover.py:146).
- Test: a fixture with two repos covering:
  - a foreign dirty path that the session wrote, which must be REFUSED;
  - foreign dirt the session never wrote, which must PASS (the control);
  - a non-repo path, which is a warning.

### G8 MEDIUM -- P1 cannot return the other answer in a short window
- Baseline from the plan: 6 fragments in 1,076 rows over ~5 days, about 0.56 % of rows.
- "Fragment count unchanged" over a few hours of real sessions is the EXPECTED reading even with no fix at all.
- P1 must state:
  - the window;
  - the expected count under the old shape (expectation >= 3 needs ~540 concurrent rows);
  - the `ledger-failures/` drop count beside it.
- Below that, the verdict is INCONCLUSIVE. Primary evidence for W1 stays the multi-process race gate with the
  old-shape control. If the control produces 0 fragments, that run is INCONCLUSIVE, not PASS.

### G9 MEDIUM -- Commit order (Q5)
- K1, R1, R2 and H0 are done or independent. H0 landed as `1703e609`.
- Keep W1 next. It is already in progress.
- SPLIT D1:
  - D1a: decide accepts evidence and stays pure, with tests and the three drills. Replay and test_rollover stay
    green.
  - D1b: `load_prior` is wired into observe and econ, the spec §5 rewrite (G6) lands, and the refresher (G3) lands.
    D1b depends on R1's artifact schema.
- S1 is independent of D1. It is safety and could go before D1b. It needs the spec §4 amendment (G6).
- W1, D1 and S1 all touch rollover.py. Commit them strictly one after another, each pathspec-scoped, and check the
  hunk headers before each commit: other panes are live, since the file changed during this audit.
- P1 comes after W1 and D1b. Nothing should be merged.

### G10 LOW -- False premises in the plan (Q6)
- Plan line 91 names `_last_seal` (rollover.py:422). It does not exist. The function is `sealed_receipt`
  (rollover.py:414-435). Line 422 is its path expression. The brief repeats the wrong name.
- Plan line 13 ("UNOWNED, untouched") is superseded by Q1/H0 and should carry a dated note.
- The F6 numbers (676-701, 748) come from a scratch reproducer that is not in the repo, and the W1 docstring cites
  a different figure (258/900). The committed race test must be the single source.
- Verified true:
  - `writes[-15:]` (rollover.py:328);
  - the dirty state is cwd-repo only (`repo_facts(cwd)`, rollover.py:109-122, called from compile_capsule);
  - econ writes `decisions/<sid>.json` (rollover_econ.py:64-66);
  - the watchdog asks on `would_rollover` True at head (context-watchdog.py:1282-1298);
  - the ledger is control state for the gate (rollover.py:453).

### G11 LOW -- Pre-existing: shadow and econ seals overwrite the capsule that /kclear sealed
- `observe` (rollover.py:707) and `rollover_econ.evaluate` (rollover_econ.py:48) call `seal()` on the same
  `capsules/<sid>.json` that /kclear seals.
- The gate hashes that file against the `capsule_sealed` receipt (rollover.py:465-467). `created` changes on every
  seal, so a shadow run that lands between /kclear and the gate gives REFUSED "capsule on disk is not the bytes that
  were sealed".
- Econ is suppressed once the ASK flag is set (watchdog 1263). Shadow is not.
- It fails closed. S1 adds git calls to compile_capsule, which widens the window.
- Recommendation: give shadow and econ seals their own path (e.g. `capsules/shadow/`). This is outside §16.1 scope,
  so log it as debt.

### G12 LOW -- W1 changes the line endings
- Text mode `"a"` on Windows wrote CRLF. The draft's `"ab"` writes LF.
- The readers (`sealed_receipt`, `rollover_replay.read_ledger`, test_rollover:240/248) parse each line with
  json.loads or count `\n`, so mixed endings are harmless.
- Note it in the commit message so a later byte-level reader does not misread it as a torn-row symptom.

## Verdict
EXECUTE-WITH-FIXES. Fold in G1, G3 and G4 before D1b and W1 are sealed; G6 and G7 go into S1; G8 into P1; G9 sets
the order.
