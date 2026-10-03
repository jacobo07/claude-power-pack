---
phase: 07-contribution
fixed_at: 2026-10-03T22:36:13Z
review_path: .planning/workstreams/skill-capability/phases/07-contribution/07-REVIEW.md
iteration: 1
findings_in_scope: 9
fixed: 9
skipped: 0
status: all_fixed
---

# Phase 7: Code Review Fix Report

**Fixed at:** 2026-10-03T22:36:13Z

**Source review:** .planning/workstreams/skill-capability/phases/07-contribution/07-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 9 (CR-01, WR-01..04, IN-01..04)
- Fixed: 9
- Skipped: 0
- Commits: 5f6cedd3, cd580268, 1b52cb57, 4efeae98, 4ca66182, e1e08403, 318de225, a930c332, 446dc93e, 7acd2feb
**Where verification ran:** worktree `sc-run` (`/home/kobii/missions/skill-capability/.claude/worktrees/sc-run`,
branch `mission/skill-capability-run`), host gex44, python3. No extra review-fix worktree was created: the
orchestrator pinned all work to this worktree.

## Fixed Issues (in the order applied; each entry was appended before the next finding started)

### CR-01: frozen C-fixed 2/2 PASS flips E to SEPARABLE under the gate's own rule -- fixed (5f6cedd3)

- RED before: `review-drills/drill_cfixed.py` -> `FAIL V-CT-SEPARATION SEPARABLE ... (1 >= 3/4)`, `verdict SEPARABLE`,
  `needed_k(1) 4`, while the evidence said "these rows could not change the verdict".
- Fix: `c_fixed_frozen()` judges the frozen `D-CARD.arm_c` figure through `separation_verdict` against the committed
  control and the budget floor; render and `--json` (`c_fixed_frozen`) use it. New in-gate drill `c-fixed-2of2-pass`
  (C rows set to PASS) -> `V-CT-SEPARATION FAIL verdict SEPARABLE (effect 1, needed equal k 4, frozen-figure
  judgement SEPARABLE)`. E-contribution.md re-rendered, state.E sha256 re-pinned (2faed836...), state.E.reason and
  the [E] line rewritten as the Owner question (a) about 8 sessions C-fixed vs N0 / (b) raise cap / (c) keep E.
- GREEN after commit: gate `CT_PASS=13/13` (24 drills), rc 0; `--pillar E` `CEP_PILLAR_E=PASS`.
- Status: fixed: requires human verification (it is a reasoning/logic finding; the figures are the gate's).

### WR-01: "needs at least 10 per arm (20 sessions)" overstated the necessary condition -- fixed (cd580268)

- RED before: `review-drills/mintotal.py` -> `15 [(6, 9, 1/2), (9, 6, 1/2)]`, exact 1/2 effect separable at total 15
  (3/6 vs 0/9), while evidence and [E] line said 20. Independent factorial-form check: `fisher(3,6,0,9) = 4/91`.
- Fix: `needed_total()` (all allocations, same most-favourable rule as the floor, bounded by 2 x needed_k) rendered
  beside the equal answer, carried in `--json` (`needed_total`, `c_fixed_frozen.needed_total`). `NEEDED_PINS` +
  drill `needed-total-pins`: 1/2 -> 15 at (6,9)/(9,6), equal 20; 1 -> 7 at (2,5)/(3,4)/(4,3)/(5,2), equal 8
  (my first pin for effect 1 listed only (3,4)/(4,3); the drill caught it, and `fisher(2,2,0,5) = 1/21` was confirmed
  independently before the pin was corrected). Red branch driven: replacing needed_total with the equal-only rule
  gives `WRONG 1/2: needed_total (20, [(10, 10)]) ...`.
- [E] line / state.E.reason: 15 (20 at equal allocation), option (b) "raise the cap to at least 15"; state.E sha256
  re-pinned (999e2cad...).
- GREEN after commit: `CT_PASS=13/13` (25 drills), rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed.

### WR-02: an appended regrade row outside the pinned set turned the gate INCONCLUSIVE/FAIL -- fixed (1b52cb57, 4efeae98)

- RED before: `review-drills/drill_append.py` -> `V-CT-SOURCES INCONCLUSIVE regrade run_id 'D-cwst-C-r3' is absent
  from the rows`, verdict INCONCLUSIVE, `ROWS-PINNED FAIL regrade rows differ from the blob at 713b02a7`.
- Fix: `pinned_regrade_split()` keeps only regrade rows whose run_id is in the pinned row set; the rest are listed as
  "outside the pinned set" (render line + ROWS-PINNED text) and never joined. ROWS-PINNED compares only the pinned
  subset with the blob and FAILs on an outside regrade row that names no row at all (keeps the old orphan safety).
  Drills `append-row-and-regrade` (all clauses ok) and `regrade-orphan-outside-pin` (ROWS-PINNED FAIL); red branch
  driven by undoing the split -> `append-row-and-regrade ... V-CT-SOURCES INCONCLUSIVE ... ROWS-PINNED FAIL`.
  E-contribution.md re-rendered (new "Regrade rows outside" line), state.E sha256 re-pinned (4cc7c20d...).
- Follow-up 4efeae98: the drill first asserted exactly 1 outside regrade row; an end-to-end append through
  `default_inputs` (load_rows patched in memory, no file written) showed the drill itself going red on an
  already-appended tree. Now relative to the standing outside count; the same scenario reports 0 drills WRONG.
- Note: in that end-to-end append scenario all verdict clauses and ROWS-PINNED stay ok, and V-CT-EVIDENCE-CURRENT
  goes red because the evidence lists the outside rows. That is the documented re-render signal, which existed
  before this fix for a rows-only append too; it is not hidden.
- GREEN after commit: `CT_PASS=13/13` (27 drills), rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed.

### WR-03: stored control grades absent while the regrade grades them -> ZeroDivisionError -- fixed (4ca66182)

- RED before: `review-drills/drill_zero.py` -> `render raised ZeroDivisionError Fraction(0, 0)`,
  `derived_json raised ZeroDivisionError Fraction(0, 0)`.
- Fix: `pairs()` gives no pair for an absent / 0-measured control, so `max_effect` is None; `render` refuses with
  "UNMEASURED: the stored grades leave N0 or every treatment arm with 0 measured rows ..."; `_render_or_none` also
  catches `ArithmeticError`; `--json` reports the effect as `UNMEASURED`. Drill `N0-stored-null-regraded`:
  GRADES-AGREE INCONCLUSIVE, verdict INCONCLUSIVE, render refused with that reason. Red branch driven: pairs without
  the guard -> `render refused: Fraction(0, 0)` and the drill reads WRONG.
- GREEN: drill_zero.py now prints `render ok` / `json ok` (no exception); end-to-end through `default_inputs` with
  N0 stored grades nulled in memory: `verdict: INCONCLUSIVE`, `EVIDENCE-CURRENT INCONCLUSIVE cannot render:
  UNMEASURED ...`, `--json` effects `{'authoritative': '0', 'stored': 'UNMEASURED'}`, no traceback. (In that
  scenario V-CT-DRILLS still read FAIL before WR-04; see WR-04.) Rendered evidence unchanged on the committed rows
  (no re-pin needed). Gate `CT_PASS=13/13` (28 drills) rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed.

### WR-04: a git failure printed `FAIL V-CT-DRILLS` -- fixed (e1e08403)

- RED before: `PATH=review-drills/fakebin:$PATH python3 tools/test_contribution_verdict.py` -> `FAIL V-CT-DRILLS a
  drill did not behave as required`, `verdict: INCONCLUSIVE`, `CT_PASS=8/13`, with SOURCES / SEPARATION /
  GRADES-AGREE / CONSUMPTION printing `ok` on unpinned rows.
- Fix: `run_drills` returns `(status, why, drills)`; a refusal prints `INCONCLUSIVE V-CT-DRILLS drills not run: <why>`
  (also under `--drills`). `default_inputs(git)` judges no row when the pins are unreadable, so the verdict clauses
  read INCONCLUSIVE with the pin error as reason (the reviewer's "consider" item, taken). New drill
  `git-log-fails-end-to-end` runs the whole default path with a failing `git log` and requires no FAIL line,
  INCONCLUSIVE verdict clauses and verdict INCONCLUSIVE; red branch driven by restoring the old refusal shape ->
  `V-CT-DRILLS FAIL, FAIL lines ['V-CT-DRILLS']`. A `nested` guard keeps the drill from re-entering the drills.
- GREEN: same fake-git run -> 0 `FAIL` lines, `INCONCLUSIVE V-CT-DRILLS drills not run: sources refused: pins
  unreadable (...)`, `verdict: INCONCLUSIVE`, `CT_PASS=4/13` (fewer ok lines than before because the verdict
  clauses no longer judge unpinned rows). Real git: `CT_PASS=13/13` (29 drills), rc 0, 0.75 s; `CEP_PILLAR_E=PASS`.
  Rendered evidence unchanged (no re-pin needed).
- Status: fixed.

### IN-01: the session regexes read conditionals and "N of M" phrasings -- fixed (318de225)

- RED before (in-process probe): `"2 of 10 fresh sessions were consumed."` -> {10}; `"If this phase consumed 3 fresh
  sessions, ..."` -> {3}; `"... if 5 fresh sessions were consumed ..."` -> {5}.
- Fix: every SESSION_RES pattern carries `(?<![\w/.])(?<!\bof )(?<!\bif )(?<!\bwould )`; pattern 3's number refuses
  a following decimal only (a first version refused a trailing "." and dropped the real `B-listing-floor.md:3`
  statement; caught by comparing the corpus match list before/after). The committed corpus still yields the same 5
  statements (02-02:47, B:3, B:52, C:84, F:50, all 0). Drill `sessions-conditional-and-n-of-m` -> all ok, remaining
  10; red branch with the old patterns -> SESSIONS/BOUND/SEPARATION/GRADES-AGREE INCONCLUSIVE.
- Not addressed (out of the bounded fix): the quoted-statement attribution case and the set-semantics undercount of
  two plan SUMMARYs stating the same per-plan figure; both remain as the review describes (nothing misread today).
- Status: fixed.

### IN-02: V-CT-BOUND's "floors non-increasing" check cannot fail on real input -- fixed (a930c332)

- Finding confirmed by reading: `floors[bb] = _floor_over(allocs, bb)` is a minimum over a subset of the same dict.
- Fix (the reviewer's first option, a label, not a new check): docstring, V-CT-BOUND text and the render now say
  "by construction (subset minimum)"; the docstring states that the `bound-floors-fall` drill proves only the
  comparator. E-contribution.md re-rendered, state.E sha256 re-pinned (172f7da1...).
- GREEN after commit: `CT_PASS=13/13` rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed (wording only; no red/green behaviour to drive).

### IN-03: "most favourable design" excluded topping up the committed arms -- fixed (446dc93e)

- Fix: the docstring now says the bound's design space is fresh allocations only. `topup_floor()` (derived from the
  committed counts) is rendered beside the bound and in `--json` as `topup`: floor 3/5 (60 points) at 5 vs 7, 5 vs 8,
  5 vs 9 and mirrored; against it the authoritative 0 and the stored 1/2 both give NOT_SEPARABLE. It does not move
  the verdict floor. Independent check: the reviewer's factorial-form `fisher.py` prints the same six allocations
  at 3/5; the `needed-total-pins` drill pins it. E-contribution.md re-rendered, state.E sha256 re-pinned (0aa33711...).
- GREEN after commit: `CT_PASS=13/13` rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed.

### IN-04: state.E reason and the [E] line were typed prose nothing re-derived -- fixed (7acd2feb)

- Fix: `owner_texts()` builds the owner-bundle [E] line and `state.E.reason` from the same figures as the evidence
  (effects, floors, topped-up floor, smallest totals, the frozen C-fixed judgement, consumption, pins). It refuses
  unless the verdict is NOT_SEPARABLE, because another verdict means state.E must be re-decided, not re-worded.
  New clause `V-CT-OWNER-TEXTS`: the committed [E] line (exactly one) and state.E.reason equal the emitted texts, in
  the working tree and at HEAD. `--owner-texts` prints them, `--json` carries `owner_texts`, and the drill
  `owner-line-one-digit-changed` must FAIL. The bundle line and the reason were rewritten from the emission. The
  reason now says "the derivation is host-independent" instead of naming gex44, so the clause also holds on the
  laptop. `terminal` is unchanged (RESEARCH_INSUFFICIENT_EVIDENCE); the gate's verdict on the committed rows is
  still NOT_SEPARABLE.
- RED observed before the commit: `FAIL V-CT-OWNER-TEXTS the [E] line of ... owner-bundle.md at HEAD differs from
  the emitted one`, `CT_PASS=13/14`. GREEN after the commit: `CT_PASS=14/14`, rc 0; `CEP_PILLAR_E=PASS`.
- Status: fixed.

## Owner texts now committed (emitted by `python3 tools/test_contribution_verdict.py --owner-texts`)

Figures from `--json`: effects authoritative 0 / stored 1/2; floor 3/4 at (4,5),(4,6),(5,4),(6,4), equal 4/5;
`needed_total.stored` = 15 at (6,9)/(9,6), `needed_k.stored` = 10; `c_fixed_frozen` = 2/2 vs 0/2, effect 1,
SEPARABLE, needed_k 4, needed_total 7, p_rows 1/3, committed_row false; `topup` = 3/5, both effects NOT_SEPARABLE;
budget cap 10, consumed 0, remaining 10.

The [E] line asks the Owner to choose: (a) about 8 fresh laptop sessions, C-fixed vs N0 at 4 per arm, inside the
cap; (b) raise the D-SESSIONS cap to at least 15; or (c) keep E at RESEARCH_INSUFFICIENT_EVIDENCE. The Owner has
not decided. This run spent no session.

## Final verification (main worktree `sc-run`, gex44, after the last commit 7acd2feb; gates read committed blobs)

`python3 tools/test_contribution_verdict.py` (verbatim, drill sub-lines included):

```
  ok   V-CT-SOURCES 8 rows, 6 joined to a regrade row; measured passes: N0 0 of 2, R 0 of 2, P 0 of 2, C 0 of 2
  ok   V-CT-FISHER-PINS 8 exact pins reproduced, each symmetric (e.g. 3/4 vs 0/5 = 1/21, 1/2 vs 0/2 = 1)
  ok   V-CT-SESSIONS stated: phase 2 0, phase 3 0, phase 5 0; not stated: phase 1, 4, 6; consumed_stated 0, remaining 10; this phase 0 (p3_runner.py lines 29, 32 are Windows paths)
  ok   V-CT-BOUND budget 10 sessions: all-allocation floor 3/4 (75 points) attained at (4,5),(4,6),(5,4),(6,4); equal k=5 floor 4/5; floors non-increasing in the budget over 2..10 (by construction: subset minimum)
  ok   V-CT-SEPARATION NOT_SEPARABLE: the largest committed effect 0 is below the smallest effect any allocation within 10 sessions can separate (3/4); R vs N0 0 (p=1), P vs N0 0 (p=1), C vs N0 0 (p=1)
  ok   V-CT-GRADES-AGREE both grade sources give NOT_SEPARABLE: authoritative effect 0, stored effect 1/2
  ok   V-CT-AUTH-COMMIT 713b02a7 added the regrade file; subject has '6/6 swallow', body names the reflog-aware grader
  ok   V-CT-AUTH-GRADER .planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_delivery.py at 713b02a7 carries FAIL-SWALLOW-REPAIRED (3 occurrences)
  ok   V-CT-AUTH-AUDIT vault/audits/cwst-representation-verdict-2026-10-03.md line 19: P r1 stored PASS regrades FAIL-SWALLOW-REPAIRED
  ok   V-CT-CONSUMPTION consumed in 0 of 8 measured rows (0 UNMEASURED); C invoked 0 of 2; N0 invoked 0 of 2; P invoked 0 of 2; R invoked 0 of 2
  ok   V-CT-ROWS-PINNED 8 rows equal the blob at 123c96cc (LF sha256 90f3e94810d6), 6 regrade rows equal the blob at 713b02a7 (LF sha256 07792b986281); both pins are ancestors of HEAD; 0 rows and 0 regrade rows outside the pinned set
  ok   V-CT-EVIDENCE-CURRENT working tree and HEAD both equal a fresh render (LF sha256 0aa337118856)
  ok   V-CT-OWNER-TEXTS the [E] line and state.E.reason equal the emitted texts in the working tree and at HEAD (LF sha256 34f5fd83e2fa / 1f0ee3b590d4)
  ok   V-CT-DRILLS 31 drills, clean case all ok, each mutant moved exactly its declared clauses
    (31 drill sub-lines, none marked WRONG; new: c-fixed-2of2-pass, N0-stored-null-regraded,
     sessions-conditional-and-n-of-m, owner-line-one-digit-changed, needed-total-pins, append-row-and-regrade,
     regrade-orphan-outside-pin, git-log-fails-end-to-end)
verdict: NOT_SEPARABLE
CT_PASS=14/14
rc=0
```

`python3 tools/test_skill_capability_program.py --pillar X`, X = A..H (verbatim):

```
CEP_PILLAR_A=PASS
rc=0
CEP_PILLAR_B=PASS
rc=0
CEP_PILLAR_C=PASS
rc=0
CEP_PILLAR_D=PASS
rc=0
CEP_PILLAR_E=PASS
rc=0
CEP_PILLAR_F=PASS
rc=0
CEP_PILLAR_G=PASS
rc=0
CEP_PILLAR_H=PASS
rc=0
```

Other checks:
- `git show HEAD:vault/programs/skill-capability/evidence/E-contribution.md | sha256sum` = `0aa33711...6886`,
  equal to the state.E pin. The ledger diff since cdd40074 is one line (state.E); `frozen` compares equal; terminal
  is RESEARCH_INSUFFICIENT_EVIDENCE.
- Fake git (`review-drills/fakebin` on PATH): 0 `FAIL` lines, `INCONCLUSIVE V-CT-DRILLS drills not run: ...`,
  `verdict: INCONCLUSIVE`, `CT_PASS=4/14`.
- Concurrent writer: another session committed `b989cb75` and `494a9723` (08-01, pillar J files only) between my
  commits in this worktree. `git show --stat` of all ten fix commits lists only `tools/test_contribution_verdict.py`,
  `E-contribution.md`, `ledger.json` and `owner-bundle.md`; their two commits touch none of these. The A..H runs
  above happened after both of their commits.
- Not committed by this agent: this file (the orchestrator commits it), `vault/progress.md` (hook artifact), and the
  untracked docs/{arch,changelog,constitution,prd}/* stubs.

---

_Fixed: see fixed_at_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
