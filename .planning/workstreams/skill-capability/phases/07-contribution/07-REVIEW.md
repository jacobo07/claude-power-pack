---
phase: 07-contribution
reviewed: 2026-10-03T00:00:00Z
depth: deep
diff_base: 21df84c9
files_reviewed: 4
files_reviewed_list:
  - tools/test_contribution_verdict.py
  - vault/programs/skill-capability/evidence/E-contribution.md
  - vault/programs/skill-capability/ledger.json
  - vault/programs/skill-capability/owner-bundle.md
findings:
  critical: 1
  warning: 4
  info: 4
  total: 9
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** deep
**Files Reviewed:** 4 (diff 21df84c9..HEAD, worktree sc-run, host gex44)
**Status:** issues_found

## Summary

Baseline on gex44, all foreground:
- `python3 tools/test_contribution_verdict.py`: `verdict: NOT_SEPARABLE`, `CT_PASS=13/13`, 23 drills, rc 0, 0.36 s.
- `python3 tools/test_skill_capability_program.py --pillar E`: `CEP_PILLAR_E=PASS`, rc 0.
- `git show HEAD:vault/programs/skill-capability/evidence/E-contribution.md | sha256sum` = `6875cdb4...e6ba3`, equal
  to the state.E pin.

Independent recomputation (`/tmp/e_review/fisher.py`, factorial-form hypergeometric with `fractions`, a different
code path from `math.comb`): all 8 FISHER_PINS reproduce exactly; the all-allocation floor within 10 sessions is 3/4 at
(4,5),(4,6),(5,4),(6,4); the equal floors are none for k=1..3, 1 for k=4 and 4/5 for k=5; the equal k needed for 1/2 is
10. The arithmetic is right. On the committed rows the verdict is honest: authoritative effect 0 and stored effect
1/2 are both below 3/4. The regrade join overrides the stored grade. Absent/empty grades and invalid rows are
UNMEASURED, and no "0/0" is printed as 0. Partial git failures yield INCONCLUSIVE on the clauses that need git (but
see WR-04).

The defects are in what the closure tells the Owner beyond the committed rows. The frozen `D-CARD.arm_c` "2/2 PASS" is
dismissed as unable to move the verdict, yet under the gate's own rule it flips E to SEPARABLE (CR-01). The
"necessary" session figure ignores the gate's own all-allocation rule: 20 is quoted where 15 suffices (WR-01). Two
robustness gaps break the gate on plausible inputs: a regrade append by the owning workstream (WR-02), and
stored-null control grades, which crash it (WR-03).

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: "these rows could not change the verdict" is false under the gate's own verdict rule; the frozen C-fixed 2/2 PASS flips E to SEPARABLE

**File:** `tools/test_contribution_verdict.py:1159-1160` (render), `vault/programs/skill-capability/evidence/E-contribution.md:128`,
`vault/programs/skill-capability/owner-bundle.md:16` ([E] line, "at n=2 they cannot move the verdict, p=1/3")

**Issue:** The verdict rule (`separation_verdict`, line 600-601) compares the largest committed EFFECT with the
budget's separation FLOOR (3/4); it never uses the p of the committed n=2 table. The render then dismisses the frozen
`D-CARD.arm_c` = "2/2 PASS (123c96cc)" (also the audit line 21, "C card, fixed, deny mode | 2 | 2/2 PASS") with a
p-value argument:

```python
L.append(f"  - fisher_two_sided(2, 2, 0, 2) = {frac(fisher_two_sided(2, 2, 0, 2))}: even the largest possible "
         f"n=2 effect cannot separate, so these rows could not change the verdict.")
```

A 2/2 vs 0/2 table has effect 1 (100 points), which is >= the floor 3/4, so the gate's own rule returns SEPARABLE.
Reproduced in a temp script (`/tmp/e_review/drill_cfixed.py`): the 8 pinned rows with arm C set to the frozen
"2/2 PASS" give `FAIL V-CT-SEPARATION SEPARABLE: the budget could separate an effect of this size (1 >= 3/4)`,
`V-CT-GRADES-AGREE ok (both SEPARABLE)`, `verdict SEPARABLE`, and `needed_k(1) = 4` (8 sessions, inside the cap of 10).

So the one figure in the program's own frozen denominators that suggests a large effect is exactly the figure that,
per D-01, would change E's disposition from RESEARCH_INSUFFICIENT_EVIDENCE to "the budget can separate; record an [E]
line and let the Owner decide a run". The evidence file and the [E] line instead tell the Owner it "cannot move the
verdict", and the recommendation "(b) keep E at RESEARCH_INSUFFICIENT_EVIDENCE, unless a stronger effect is expected"
omits that the frozen ledger already records a 100-point C-fixed effect. "p=1/3" is about whether the existing 2+2
rows are significant, which nobody claims; the question pillar E answers is whether the budget can separate.

Why the guards miss it: no clause or drill evaluates the cited-but-unrowed figures through `separation_verdict`; the
sentence is static prose with one computed number inside it, and V-CT-EVIDENCE-CURRENT only proves the file equals a
re-render of the same prose.

**Fix:** derive the dismissal through the verdict rule instead of asserting it, and say the true result:

```python
cf_effect = Fraction(1)  # 2/2 vs N0 0/2, from frozen D-CARD.arm_c
cf_v = separation_verdict(cf_effect, b["floor"])
L.append(f"  - if those rows exist (2/2 PASS vs {CONTROL_ARM} 0/2, effect {frac(cf_effect)}), the verdict rule gives "
         f"{cf_v}: the budget could separate an effect of this size (needed equal k = {needed_k(cf_effect)} per arm)")
```

and add a drill (`c-fixed-2of2-pass` -> V-CT-SEPARATION FAIL, verdict SEPARABLE). Rewrite the [E] line: the C-fixed
arm's frozen 2/2 is a 100-point effect the budget CAN separate at 4 vs 4 (8 sessions); the Owner question is whether to
run C-fixed vs N0 inside the cap, not only whether to raise it. Re-render, re-pin state.E's sha256 in the same commit.

## Warnings

### WR-01: "needs at least 10 per arm (20 sessions)" overstates the necessary condition; 6 vs 9 (15 sessions) separates a 1/2 effect

**File:** `tools/test_contribution_verdict.py:193-202` (`needed_k`, equal allocations only), `:1174-1177` (render),
`vault/programs/skill-capability/evidence/E-contribution.md:135`, `owner-bundle.md:16`

**Issue:** The docstring (lines 31-35) says a claim must hold for the most favourable design, so the floor is taken
over ALL allocations. `needed_k` breaks that rule: it searches equal k only. The [E] line then generalises the
equal-k answer into "A separating benchmark for the stored-grade effect needs at least 10 per arm (20 sessions, which
is a necessary condition ...)". It is not necessary: 3/6 vs 0/9 has effect exactly 1/2 and two-sided p = 4/91
(0.0440), recomputed independently with factorial-form fractions (`/tmp/e_review/fisher.py`), and the gate's own
`min_separable(6, 9)` gives floor 1/2. The smallest total that separates a 1/2 effect is 15 (6+9 or 9+6). The Owner is
being asked whether to raise the cap, and the number offered (20) is 5 sessions too high.

**Fix:** compute the all-allocation minimum beside the equal one and quote that one as the necessary condition:

```python
def needed_total(effect, cap=2 * NEEDED_K_MAX):
    if effect is None or effect <= 0:
        return None
    for tot in range(2, cap + 1):
        hits = [(n1, tot - n1) for n1 in range(1, tot)
                if (ms := min_separable(n1, tot - n1)) is not None and ms[0] <= effect]
        if hits:
            return tot, hits
    return None
```

Render "smallest total 15 (6,9)/(9,6); equal allocation 10 per arm (20)". Add a pin drill (`needed_total(1/2) == 15`),
fix the [E] line, re-render, and re-pin state.E.

### WR-02: an appended regrade row outside the pinned set turns the gate INCONCLUSIVE/FAIL; the row pin does not cover the regrade join

**File:** `tools/test_contribution_verdict.py:1216-1227` (`default_inputs`), `:388-397` (`authoritative`), `:735-738`
(`clause_rows_pinned`)

**Issue:** The docstring says the P3 jsonl is append-only and owned by another workstream, so only the pinned run_ids
are used. That is done for the rows (`pinned_split`) but not for the regrade rows: `default_inputs` passes the whole
working-tree regrade file. If the owning workstream appends one run and its reflog-aware regrade row, the same thing
713b02a7 did for N0/R/P, `authoritative` refuses with "regrade run_id 'D-cwst-C-r3' is absent from the rows", because
the new run was filtered out of `rows`. V-CT-SOURCES, V-CT-SEPARATION and V-CT-GRADES-AGREE go INCONCLUSIVE, and
`clause_rows_pinned` FAILs with "regrade rows differ from the blob at 713b02a7". Reproduced in
`/tmp/e_review/drill_append.py`. An append to the rows alone is handled ("1 rows outside the pinned set", ok). The
regrade append is not, so a legitimate append by the owner workstream would turn `--final` red on E. That append is
the most likely next one, because the [E] line asks the laptop to commit the C-fixed rows.

**Fix:** restrict the regrade rows to the pinned run_id set before the join, and compare only that subset with the
blob:

```python
ids = {r["run_id"] for r in st["info"]["rows_blob"]}
reg_in = [g for g in (reg or []) if isinstance(g, dict) and g.get("run_id") in ids]
reg_out = [g for g in (reg or []) if g not in reg_in]
```

Pass `reg_in` to `evaluate_core` and to `clause_rows_pinned`, and list `reg_out` under "outside the pinned set". Add a
drill that appends one row and its regrade row and expects all clauses ok.

### WR-03: stored control grades absent while the regrade grades them -> ZeroDivisionError traceback, not INCONCLUSIVE

**File:** `tools/test_contribution_verdict.py:1015,1019` (render), `:1278,1283,1304` (`derived_json`), `:1237-1241`
(`_render_or_none` catches only ValueError/KeyError/TypeError), `:442-443` (`rate`)

**Issue:** `clause_grades_agree` correctly guards `stored[CONTROL_ARM]["n"] == 0` (line 625), but `render` and
`derived_json` call `max_effect(stored)` with no guard. `pairs` -> `rate(ctl)` -> `Fraction(0, 0)` raises
ZeroDivisionError, which `_render_or_none` does not catch. Scenario: the N0 runs carry a stored `grade: null` (graded
only by the later reflog-aware regrade, the case the join exists for). Reproduced in `/tmp/e_review/drill_zero.py`:
evaluate_core gives V-CT-GRADES-AGREE INCONCLUSIVE, then `render raised ZeroDivisionError Fraction(0, 0)` and
`derived_json raised ZeroDivisionError`. In the default mode `default_results` calls `_render_or_none`, so the gate
dies with a traceback (rc 1, no `verdict:` line, no `CT_PASS=`). It does not print INCONCLUSIVE, and it does not exit 2.

**Fix:** make `max_effect` return None when the control is unmeasured, and render "UNMEASURED" for it:

```python
def max_effect(counts):
    if not counts or counts.get(CONTROL_ARM, {"n": 0})["n"] == 0:
        return None
    ...
```

Also catch `ArithmeticError` in `_render_or_none`. Add a drill: N0 stored grade null + regrade present -> GRADES-AGREE
INCONCLUSIVE, the render refused with a reason, and the gate still prints `verdict: INCONCLUSIVE`.

### WR-04: a git failure prints `FAIL V-CT-DRILLS`, against the module contract "a git failure is INCONCLUSIVE"

**File:** `tools/test_contribution_verdict.py:1244-1246` (`run_drills`), `:1266-1270`

**Issue:** When any pin or budget source is unreadable, `run_drills` returns `[("sources", ..., False)]`, and
`default_results` turns that into `FAIL V-CT-DRILLS a drill did not behave as required`. Reproduced with a `git` shim
on PATH that fails only `git log` (`/tmp/e_review/fakebin/git`): AUTH-COMMIT, AUTH-GRADER, ROWS-PINNED and
EVIDENCE-CURRENT read INCONCLUSIVE, V-CT-DRILLS reads FAIL, and the result is `verdict: INCONCLUSIVE CT_PASS=8/13`. The
verdict line is right. The FAIL line is wrong: it tells the reader the drills misbehaved when they never ran. This is
the same pattern as 06-REVIEW WR-02, which phase 6 fixed in its own gate. Also, in this state the verdict clauses run
on every working-tree row unpinned (`default_inputs` line 1222-1223), and they print `ok`.

**Fix:** have `run_drills` return a status, and emit `("V-CT-DRILLS", "INCONCLUSIVE", "drills not run: <why>")` when
sources refused. Consider marking the verdict clauses INCONCLUSIVE when the pin is unreadable, instead of judging
unpinned rows.

## Info

### IN-01: the session regexes read conditionals, quotes and "N of M" phrasings; a misread biases toward NOT_SEPARABLE

**File:** `tools/test_contribution_verdict.py:106-109`, `:489-504`

**Issue:** The patterns have no left boundary and no context, and the figure is attributed to the phase of the FILE,
not of the statement. Probed in-process: "2 of 10 fresh sessions were consumed" reads 10; "If this phase consumed 3
fresh sessions, the cap is exceeded" reads 3; a phase-5 file quoting "Phase 2 recorded: 4 fresh sessions were consumed"
counts 4 for phase 5. Within one phase, two plan SUMMARYs that each state the same per-plan figure collapse to one
(set semantics), so that case undercounts. In the current corpus all five matches (02-02:47, B:3, B:52, C:84, F:50)
are true statements of 0, and the fourth regex (`this phase consumed`) reads F:50 correctly. So nothing is misread
today. A misread that over-counts shrinks the budget and raises the floor, which makes NOT_SEPARABLE easier to
reach, so the direction of error favours the closing verdict.
**Fix:** anchor the patterns with `(?<![\w/])(\d+)` and reject a match preceded by `of `, `if ` or `would `, or require
the statement on its own bullet/sentence. Add a drill with one conditional sentence and one "N of M" sentence.

### IN-02: V-CT-BOUND's "floors non-increasing" check cannot fail on real input

**File:** `tools/test_contribution_verdict.py:180,185-190`, drill `bound-floors-fall` at `:866-870`

**Issue:** `floors[bb]` is the minimum over a subset of the same `allocs` dict (`key[0]+key[1] <= bb`), so it is
non-increasing by construction. The drill injects a fake `floors` dict, so it proves the comparator and not the
property. The evidence file calls the property "checked". That is true, but the check is a tautology rather than
evidence.
**Fix:** label it "by construction (subset minimum)", or recompute each budget's floor independently from
`min_separable` and compare.

### IN-03: "most favourable design" excludes extending the committed arms; the verdict survives

**File:** `tools/test_contribution_verdict.py:31-35` (docstring claim), `:168-182`

**Issue:** The design space is fresh allocations only. It does not include topping up the committed N0 0/2 and P 0/2
rows with new sessions of the same protocol. Recomputed independently: with 2+2 committed rows plus up to 10 new
sessions, the floor is 3/5 (60 points, at 5 vs 7). That is lower than 3/4 but still above the stored effect 1/2, so
the NOT_SEPARABLE verdict on the committed rows stands. The claim is narrower than the docstring states.
**Fix:** state the design space explicitly ("fresh allocations; topping up the committed arms gives floor 3/5,
also above 1/2"), or include the pooled designs in the bound.

### IN-04: state.E `reason` and the [E] line are typed prose; nothing re-derives their figures

**File:** `vault/programs/skill-capability/ledger.json` state.E.reason (547cbf76), `owner-bundle.md:16`

**Issue:** Every figure was checked against the gate's derivation and currently matches: N0/R/P/C 0/2, stored P 1/2,
0 and 50 points, cap 10, consumed 0, remaining 10, floor 3/4 (75), 4/5 (80) at 5 vs 5, 0 of 8 consumed, 20
sessions, p=1/3. But `--pillar E` pins only the evidence sha256, and V-CT-EVIDENCE-CURRENT does not read the ledger or
the bundle. So the CR-01 and WR-01 corrections (the "cannot move the verdict" claim, 20 -> 15) need hand edits in two
places, and those edits can drift.
**Fix:** have the gate emit the `[E]` line and a reason skeleton (`--json` already carries the figures), and add a
clause that the committed [E] line equals the emitted one.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
