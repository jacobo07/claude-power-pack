---
phase: 01-baseline-integrity-repair
plan: 03
subsystem: tower-baselines
tags: [ucep, tower, ratchet, allowlist, anchors, provenance]
requires: ["01-01"]
provides:
  - "ChainReport.ok False for an unanchored child; family_baseline verify prints UNANCHORED and exits 1 (H3b)"
  - "ratchet.diff reports WHY_CHANGED, REANCHORED, CLASS_CHANGED, SCOPE_CHANGED (H2)"
  - "ratchet.AUTHORITIES + is_authorized; revert/promote refuse an unlisted authority; _recorded counts only allowlisted ones (H1)"
affects: [01-04, 01-05]
key-files:
  modified: [modules/tower/ratchet.py, tools/family_baseline.py, tools/test_ucep_baseline_integrity.py]
decisions:
  - "Authority allowlist is a code constant AUTHORITIES = ('Owner',), first-token, case-sensitive match; no minimum reason length"
  - "REANCHORED is the origin-change diff kind (the name 01-04's reanchor will record); verify_chain/diff never call verify_origin"
metrics:
  completed: 2026-10-03
status: complete
commits: 3
plan_head_before: 0131552e96b22b331577df0549f15538d4ef2556
requirements: [UCEP-01]
actuals:
  tokens: 3500    # chars/4 over `git diff BASE HEAD` (13999 chars)
  tasks: 3
  commits: 3
---

# Phase 1 Plan 3: Ratchet H1/H2/H3b closure Summary

The ratchet can no longer be talked past: an unanchored child, an unrecorded rewrite of why/origin/class/scope, and a change
recorded under an arbitrary authority string are all refused, and `tools/test_ucep_baseline_integrity.py` goes from RED 5/12 to
`UCEP_BASELINE_INTEGRITY_PASS=14/14` with every control still green.

Commits (measured, `git rev-list --count 0131552e..HEAD` = 3): `1b087de0` (Task 1), `c06e28ed` (Task 2), `630b993c` (Task 3).
Status: COMPLETE. Production Reality: OBSERVED (real commands and exit codes in this worktree; harness on B0-only temp copies,
real families judged by `test_tower_ratchet.py` V-TRAT-REAL-CHAINS).

Environment: PowerShell tool disabled; all commands via Bash with absolute `git.exe` / Python 3.12 and the `# bash-safe` marker,
Python run directly. Root verified each commit: `C:/Users/User/.claude/skills/claude-power-pack/.claude/worktrees/ucep`, `ucep/mission`.
BASE (persisted ledger `gsd-plan-head-before-01-03`) = `0131552e96b22b331577df0549f15538d4ef2556`.

Dirty-path SET before the plan (orchestrator-owned only):

```
 M .planning/workstreams/ucep/STATE.md
?? .gsd/
?? .planning/workstreams/ucep/milestone.lock
?? .planning/workstreams/ucep/state.json
```

sha256 before (B0s and web_surface B1; must be identical after):

```
1a50144150bf7134c966fd832a368a18958a363a7fb8cfc9bbe8ea481a0a2407  kobiicraft_mode/B0.json
bcb20d37f568a8873710990e4e43351010e882ac6fcd0f38b1e387a1d674dc64  persistent_state/B0.json
98e8d33fef37ae75732cd92694d4ef20bd68ce8649c3239f6dfd8d16a5eea2d7  web_surface/B0.json
2e54ac452ac256703fb5a3d9b8252ed30a903ab3d64f651c16174727ee5cd8e1  web_surface/B1.json
2603cf39889cb421c9fd31968b706d68a79aa7f14539173a4eb669761a4bc1bd  wii_homebrew/B0.json
```

Subject scope is `(01-03)` per the orchestrator (the plan text said `ucep-01`).

## Task 1 (tracer): H3b closed end to end

Pre-fix run (new gate added first, ratchet.py / family_baseline.py unchanged per `git diff --quiet HEAD` rc=0), harness rc=1:

```
  FAIL V-UCEP-CLI-UNANCHORED  unanchored rc=0 out='web_surface chain: OK (generations [0, 1])\n'; anchored rc=0 out='web_surface chain: OK (generations [0, 1])\n'
UCEP_BASELINE_INTEGRITY_PASS=5/13  threshold=13/13
```

(V-UCEP-H3B was already FAIL there: the 7 original attack gates + the new CLI gate = 5 PASS of 13.)

Changes: `ChainReport.ok` = `not regressions and not tampered and not unanchored`; module docstring anchor paragraph updated;
`family_baseline.py verify` prints `UNANCHORED B%d: no parent_sha256, so its parent's bytes are not pinned` and the regression line now
reads `(no allowlisted reason+authority on record)`. Harness: `V-UCEP-CLI-UNANCHORED` drives `fb.main(["verify", fam])` with
`bl.BASELINES_DIR` monkeypatched to a temp root (restored in `finally`), unanchored chain -> rc 1 + `UNANCHORED B1`, anchored control -> rc 0.

Post-fix:

```
harness rc=1  FAIL set = {H1-RAW, H1-API, H2-WHY, H2-ORIGIN, H2-CLASS, H2-SCOPE}   UCEP_BASELINE_INTEGRITY_PASS=7/13
test_tower_ratchet.py   rc=0  TOWER_RATCHET_PASS=21/21
test_tower_donegate.py  rc=0  TOWER_DONEGATE_PASS=10/10
grep -c 'not self.unanchored' ratchet.py = 1 ; grep -c 'UNANCHORED B%d' family_baseline.py = 1
```

V-UCEP-H3B PASS and V-UCEP-CLI-UNANCHORED PASS; exactly the expected 7/13.

Commit: `1b087de0` `fix(01-03): an unanchored child generation fails the chain (H3b)` (pathspec: ratchet.py, family_baseline.py,
test_ucep_baseline_integrity.py; 3 files, +45/-5; subject verified; no deletions).

## Task 2: H2 closed (diff covers why, origin, class, propagation_scope)

Pre-fix reading: the 7/13 run of Task 1 (the four V-UCEP-H2-* attacks FAIL with `'ok': True`, control PASS).

Changes in `modules/tower/ratchet.py`: constants `WHY_CHANGED`, `CLASS_CHANGED`, `SCOPE_CHANGED`, `REANCHORED` (4 matches of
`^(...) = `); `_origin_key(origin)` -> `(squash(file), str(line), squash(quote))`, `("","","")` for a non-dict; `diff` appends, in
order and after the check/requirement comparisons of a present, non-reverted entry: WHY_CHANGED, REANCHORED, CLASS_CHANGED,
SCOPE_CHANGED (absent equals absent, so today's generations produce no churn); docstring kind table extended.

Post-fix:

```
harness rc=1  FAIL set = {H1-RAW, H1-API}   UCEP_BASELINE_INTEGRITY_PASS=11/13   (5 PASS V-UCEP-H2-* lines: 4 attacks + control)
test_tower_ratchet.py rc=0  TOWER_RATCHET_PASS=21/21   (V-TRAT-REAL-CHAINS PASS: the real families stay clean, no BLOCKED note needed)
AST region check (verify_chain + diff FunctionDefs, comments ignored): functions_seen=['diff','verify_chain'] verify_origin_uses=[]  rc=0
```

`verify_origin` is not referenced in `verify_chain` or `diff` (the only textual mention is in a comment). Task 2 step 6 BLOCKED
contingency did not trigger: no real-family regression, no generation file touched.

Commit: `c06e28ed` `fix(01-03): ratchet diff covers why, origin, class and propagation_scope (H2)` (ratchet.py only, +28; subject verified).

## Task 3: H1 closed (allowlisted authority in `_need` and `_recorded`)

Pre-fix run (new gate `V-UCEP-ALLOWLIST` added first, ratchet.py unchanged since `c06e28ed`, `git diff --quiet HEAD` rc=0), harness rc=1:

```
  FAIL V-UCEP-H1-RAW      FAIL V-UCEP-H1-API
  FAIL V-UCEP-ALLOWLIST   is_authorized=False wrongly refused=['Owner', "Owner (approved 'both', 2026-10-01)", 'Owner: plan of record'] ... real "Owner (approved 'both', 2026-10-01)" ok=False
UCEP_BASELINE_INTEGRITY_PASS=11/14  threshold=14/14
```

Changes in `modules/tower/ratchet.py`: `import re`; `AUTHORITIES = ("Owner",)`; `is_authorized(authority)` (str only; strip; first token via
`re.split(r"[\s:(,;]", s, maxsplit=1)[0]`; case-sensitive; empty/non-str -> False); `_need` keeps both non-empty checks and raises
`RatchetRefusal("authority %r is not on the allowlist ...")` for an unlisted one (NO minimum reason length: `reason="new"` and CLI
`--reason gone` still work); `_recorded` requires `is_authorized(rec.get("authority"))`; module docstring says "allowlisted `authority`
(AUTHORITIES)". `tools/family_baseline.py`: usage shows `--authority Owner[ (context)]`, docstring mentions the allowlist and UNANCHORED.
Harness: `V-UCEP-ALLOWLIST` (accepts `Owner`, `Owner (approved 'both', 2026-10-01)`, `Owner: plan of record`; refuses `x`, `""`, `"   "`,
`None`, `owner`, `Ownerx`, `Owner's cat`, `Bot Owner`; control = the real web_surface B1 `promoted_by`, read only), threshold 14/14,
docstring updated for the one read of the real B1.

### D-07 allowlist choice and residual risk

Code constant, not a data file: tests stay hermetic via `root=`, and a data file would be writable by the same party that writes
generations. First-token match so the real `promoted_by` form `Owner (approved 'both', 2026-10-01)` passes while look-alikes
(`Ownerx`, `owner`, `Bot Owner`, `Owner's cat`) do not. Residual (T-01-13, accepted): whoever can edit `ratchet.py`, or who recomputes
`parent_sha256` after hollowing, controls the outcome; a file-level ratchet cannot stop that and repo history is the root of trust
(stated in the code comment above `AUTHORITIES`).

Post-fix (bracketed by the sorted dirty-path SET, identical before and after; `diff` of the two sets empty):

```
UCEP_BASELINE_INTEGRITY_PASS=14/14  threshold=14/14        rc=0
TOWER_RATCHET_PASS=21/21            rc=0
TOWER_DONEGATE_PASS=10/10           rc=0
TOWER_INHERITANCE_PASS=16/16        rc=0
TOWER_CAPSULE_PASS=16/16            rc=0
TOWER_SELECT_PASS=15/15             rc=0
FAMILY_BASELINES_PASS=20/20         rc=0
BASELINE_GENERATIONS_PASS=15/16     rc=1   (only FAIL: V-BGEN-REAL-B0-CITATIONS-HOLD, fixed by 01-04, as expected)
AST check (verify_chain/diff contain no verify_origin): rc=0
```

Acceptance greps: `AUTHORITIES = ("Owner",)` 1 match, `def is_authorized` 1 match. Signatures of `diff`, `verify_chain`, `revert`, `promote`
unchanged (`^def (verify_chain|revert|promote|diff)\(` lines identical to the original parameter lists). No file added under `modules/`.

Commit: `630b993c` `fix(01-03): ratchet authority comes from an allowlist (H1)` (3 files, +66/-12; subject verified; no deletions).

## Plan-level verification

- Harness progression: 01-01 RED `5/12` -> (new CLI gate, unchanged code) `5/13` -> T1 `7/13` -> T2 `11/13` -> (new allowlist gate) `11/14` -> T3 `14/14`.
- `TOWER_RATCHET_PASS=21/21` after every task (real chains clean under the stricter diff and `ok`).
- B0 and web_surface B1 generation files byte-immutable: sha256 after equals sha256 before for all 5 (table at top); `git status --porcelain -- vault/tower/baselines` empty.
- Dirty-path SET at the end: the BEFORE set plus this SUMMARY (all three code commits landed; STATE.md / `.gsd/` / `milestone.lock` / `state.json` never staged).
- Hermetic: the harness points HOME/USERPROFILE at a temp dir and writes only under `tempfile.mkdtemp`; no production ledger row.

## Deviations from Plan

None to the code. Notes:

1. Commit subject scope is `(01-03)` per the orchestrator instruction, not the `ucep-01` written in the plan.
2. Harness threshold constants were raised in step (13, then 14) as gates were added, so `threshold=N/N` always equals the file total.
3. The harness docstring sentence "never reads the real second generation" was narrowed: only the `V-UCEP-ALLOWLIST` control reads the real B1 `promoted_by` (read only, as the plan prescribes).
4. Environment: PowerShell disabled in this session; plan verify commands run through Bash with absolute `git.exe`/`python.exe` and equivalent predicates.
5. No BLOCKED item: Task 2 step 6 did not trigger (real chains stayed clean).

## Authentication gates

None.

## Known Stubs

None.

## Threat Flags

None new. T-01-10 (authority forgery) mitigated by allowlist + V-UCEP-H1-RAW/H1-API/ALLOWLIST; T-01-11 (provenance laundering)
mitigated by the four new diff kinds + V-UCEP-H2-* with a recorded-rewrite control; T-01-12 (hollow and drop anchor) mitigated by
`ok` requiring `not unanchored` + V-UCEP-H3B/CLI-UNANCHORED; T-01-13 accepted (see D-07 residual).

## Self-Check: PASSED

- FOUND: `modules/tower/ratchet.py`, `tools/family_baseline.py`, `tools/test_ucep_baseline_integrity.py`
- FOUND commits: `1b087de0`, `c06e28ed`, `630b993c` (`git log --oneline BASE..HEAD` lists exactly these 3)
- Harness `14/14` rc=0 observed after the last commit's content (committed tree == working tree for the 3 files).
