---
phase: 06-compile-out-lineage
reviewed: 2026-10-03T00:00:00Z
depth: deep
diff_base: df391c07
files_reviewed: 8
files_reviewed_list:
  - tools/card_lineage.py
  - tools/test_card_lineage.py
  - hooks/doctrine_cards.js
  - hooks/destructive_doctrine_card.js
  - vault/programs/skill-capability/evidence/G-lineage.md
  - vault/programs/skill-capability/evidence/H-drift.md
  - vault/programs/skill-capability/card_source_digests.json
  - vault/programs/skill-capability/ledger.json
findings:
  critical: 1
  warning: 4
  info: 3
  total: 8
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-10-03
**Depth:** deep (cross-file: `skill_mirror_drift` git/blob/record primitives, `skill_coverage.CARD_TOKEN/registered_hooks/discover_cards`, `verify_global_mirrors.batch_blobs`, the dispatcher CHAIN_MAP)
**Files Reviewed:** 8 (diff df391c07..d95c4cac, worktree sc-run, host gex44)
**Status:** issues_found

## Summary

Baseline on gex44, all foreground:
- `python3 tools/card_lineage.py`: `CARD_LINEAGE PASS population=2 head=d95c4cac`, rc 0.
- `python3 tools/test_card_lineage.py`: `CLG_PASS=30/30`, rc 0, 4.9 s.
- `node hooks/tests/test-doctrine-cards.js` 37/37, `node hooks/tests/test-destructive-doctrine-card.js` 15/15,
  `python3 tools/test_card_precision.py` 36/36, `python3 tools/test_skill_drift.py` 16/16, and `node --check` on both
  hooks: all green.
- The ledger pins match the committed LF blobs: G-lineage.md `f852af7f`, card_source_digests.json `985aa980`
  (state.G and state.H), H-drift.md `2e8cdccc`.
- Neither hook is installed on gex44's `~/.claude/hooks/`, so this host has no live copy that could drift.

What holds up: every byte compared comes from git blobs at the resolved commit, and nothing reads the working tree
(WORKTREE-ONLY drill, plus a code read). CRLF is normalised before regexes and digests. Subprocess calls are argv lists.
The trailer `source` is `\S+` and cannot inject a newline into the `cat-file --batch` payload. `diff-tree` takes the path
after `--`. The trailer `commit` must be 40 hex and is re-resolved. A blob read failure during discovery gives
INCONCLUSIVE. The trailers are `//` comment lines after the last statement, so they cannot change hook behaviour. Every
trailer forgery I tried (wrong sha, wrong commit, a commit that does not touch the source, a non-ancestor, the digest of
another file) is caught by at least one clause.

The defects are in what one trailer binds and in which registrations are seen. A card naming a second skill passes after
that skill changes and only H is re-recorded (CR-01), which is the exact bypass G exists to close. A subdirectory card
registered with the dispatcher's `./` shape escapes both sweeps (WR-01). After discovery, git failures read FAIL rather
than INCONCLUSIVE (WR-02). `--trailer-for` can emit a merge commit that its own COMMIT-TOUCHES rejects (WR-03). The
TRAILER clause's load-bearing proof measures the population rather than the clause (WR-04). None of these changes the
current 2-card PASS, because both live cards name exactly one skill and sit at top level. Every scenario was reproduced
in temp git repos under /tmp (scripts in /tmp/clg-review/). The worktree was not modified apart from this file.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: a card that names a second skill passes G after that skill changes and only H is re-recorded

**File:** `tools/card_lineage.py:207-211` (c_skill), `tools/card_lineage.py:95-105` (parse_trailer allows one marker per card)
**Issue:** The population and pillar H both treat EVERY CARD_TOKEN in a card file as a compiled-from source
(`skill_mirror_drift.committed_card_pairs` -> one H pair per `<name>` skill token). G allows exactly one trailer per
card, and SKILL only checks that the trailer's skill is *one of* the names:

```python
names = set(sc.CARD_TOKEN.findall(member["text"]))
if trailer["skill"] in names:
    return _out(PASS, trailer["skill"])
```

No clause requires every named skill to carry lineage. So a card with a second skill token is bound to its first skill
only, and for the second one G collapses back to H's weakness, which G exists to close: "H can be re-recorded without
anybody re-reading the skill" (card_lineage.py:10-12).
**Scenario (reproduced, temp git repo built by `test_card_lineage.Fixture`, /tmp/clg-review/repro.py R1):** add
`skills/third-skill/SKILL.md`, then add `// see also the \`third-skill\` skill for the companion rule` to
hooks/doctrine_cards.js above the lineage block. Commit and re-record H; H now holds 3 pairs, including
(doctrine_cards.js, third-skill). Then change third-skill's SKILL.md and commit:
`FAIL ['H-RECORD-CURRENT']`. Run `record_cards`, commit, and do NOT touch the card: **`PASS []`**. The source
skill changed, nobody re-derived the card, and the gate is green. A "see also the `x` skill" pointer is an
ordinary edit to a card body. The ledger's core claim ("a source skill change fails SOURCE-CURRENT even after pillar
H's record is re-recorded") is false for any multi-skill card.
**Why guards fail:** TRAILER-DUPLICATE makes a second trailer UNMEASURED, so a card cannot carry two lineages. SKILL
checks membership, not coverage. H-RECORD-CURRENT is cleared by the re-record. The drill table has no row where a card
names two skills.
**Fix:** bind lineage per named skill. Either allow one marker line per CARD_TOKEN skill (a duplicate *skill* is
UNMEASURED, and distinct skills are each judged by the six clauses), or at minimum add a coverage FAIL:
```python
missing = sorted(names - {trailer["skill"]})
if missing:
    return _out(FAIL, f"card names skill(s) with no lineage trailer: {missing}")
```
Add a drill MULTI-SKILL-RERECORDED, declared `FAIL {CW:SKILL}` (or the new clause), next to SOURCE-CHANGED-RERECORDED.

## Warnings

### WR-01: DISPATCHER-COVERED cannot see the `./<subdir>/x.js` registration variant, so a subdirectory card escapes both sweeps

**File:** `tools/card_lineage.py:72` (`CARD_FILE_RE = hooks/[^/]+\.js`), `tools/card_lineage.py:165-176` and docstring
`:37-38` ("a registered card outside the sweep cannot escape it"), via `tools/skill_coverage.py:62` (`SCRIPT` matches only
`'../skills/claude-power-pack/<rel>'`)
**Issue:** CHAIN_MAP has two registration shapes. One is `script: '../skills/claude-power-pack/hooks/x.js'` (43
entries). The other is `script: './x.js'` / `'./tests/fixtures/x.js'`, relative to the dispatcher's own directory (33
entries, 6 of them in a subdirectory: `hooks/hook-dispatcher.js:589-609`). `sc.registered_hooks` only knows the first
shape, so `committed_card_pairs`, and with it DISPATCHER-COVERED, never sees a `./` registration. The population only
looks at top-level `hooks/*.js`. A card that lives in a hooks subdirectory (`hooks/_shared/`, `hooks/lib/`) and is
registered with the `./` shape is therefore in neither set. DISPATCHER-COVERED's stated guarantee covers only one of the
two shapes.
**Scenario (reproduced, repro.py R2):** copy doctrine_cards.js to `hooks/_shared/sub_card.js` (deny + CARD_TOKEN), defuse
its marker line, and register `{ exe: NODE_EXE, script: './_shared/sub_card.js' }` next to the CW line in a PreToolUse
chain. Commit: `registered_hooks` lists no sub_card, the population is still the 2 old cards, and the verdict is **`PASS []`**,
for a registered, unlineaged deny card.
**Fix:** in `c_dispatcher_covered`, also parse `script: './<rel>'` and map it to `hooks/<rel>` before comparing. Better,
widen the population candidates to every tracked `hooks/**/*.js` outside `hooks/tests/` and `hooks/_tests/`, so that
discovery does not depend on the registration shape at all. Add a drill DISPATCHER-UNCOVERED-DOTSLASH. If the `./` shape
is deliberately out of scope, change the docstring/evidence sentence to name the one shape it covers.

### WR-02: a git failure inside a clause yields verdict FAIL, indistinguishable from real drift

**File:** `tools/card_lineage.py:339-341` (verdict fold), together with the per-clause git paths `:180-182`, `:240-248`,
`:252-258`, `:280-281`, `:168`
**Issue:** INCONCLUSIVE is returned only for failures before or during discovery (`:311-322`). After that, every git failure
(a merge-base timeout, a cat-file error on the record, a `committed_card_pairs` git failure, a batch error in
COMMIT-DIGEST) becomes a clause UNMEASURED, and the fold `PASS if all PASS else FAIL` turns it into verdict **FAIL**. The
CLI line then reads `CARD_LINEAGE FAIL`, and V-CLG-LIVE-CLEAN (`test_card_lineage.py` c_live_clean) maps a non-INCONCLUSIVE
verdict to `FAIL`, not `INCONC`. An operator or the CE verifier sees "drift: re-derive the card" when git simply did not
answer. That is the "git failure -> INCONCLUSIVE" property the evidence asserts in its Method section. It is never a
false PASS, so this is not a blocker. V-CLG-GIT-FAILURE only drives the first git call (resolve_commit), so the test
cannot see this.
**Scenario (reproduced, repro.py R3):** patch `smd.git_run` to fail only for `merge-base` ("timed out after 30 seconds") on
the CLEAN fixture: `verdict FAIL`, fail set `{DS:COMMIT-ANCESTOR, CW:COMMIT-ANCESTOR}`, last line
`CARD_LINEAGE FAIL population=2`.
**Fix:** tag clause outcomes that came from a git failure (for example `_out(UNMEASURED, ..., git=True)`, set where
`smd.is_git_failure`, a `git ... failed:` reason or the `rc=128` class is seen). Make the verdict INCONCLUSIVE when no clause
is FAIL and at least one UNMEASURED clause is git-tagged. Add a V-CLG-GIT-FAILURE-MIDJUDGE drill that fails a single git
subcommand.

Second shape of the same fold: a shallow clone, or any clone that lacks the trailer commit, makes
`resolve_commit(trailer["commit"])` fail (`:240-242`). COMMIT-ANCESTOR, COMMIT-TOUCHES and COMMIT-DIGEST go UNMEASURED,
and the verdict reads FAIL. Missing history is not drift either.

### WR-03: `--trailer-for` emits a merge commit that COMMIT-TOUCHES then rejects, so a card cannot be re-derived

**File:** `tools/card_lineage.py:142-147` (trailer_for: `git log -1 --format=%H <sha> -- <source>`) vs `tools/card_lineage.py:255-262`
(c_commit_touches: `git diff-tree --no-commit-id --name-only -r --root <commit> -- <source>`)
**Issue:** The generator and the judge use two different definitions of "the commit that changed the source". `git log`
with path limiting returns a merge commit when the merge differs from every parent, for example a conflict resolved
inside SKILL.md. Without `-m`/`-c`/`--cc`, `git diff-tree` on a merge commit prints nothing, so COMMIT-TOUCHES FAILs on the
exact line the tool printed. No other commit carries the merged blob, so COMMIT-DIGEST would refuse any hand-picked
alternative. The card stays red until somebody makes an unrelated commit to the SKILL.md, which turns the documented
re-derivation procedure (G-lineage.md "Re-derivation") into a livelock.
**Scenario (reproduced, /tmp/clg-review/merge.py):** in the fixture, edit CW's SKILL.md on `side` and on the main branch,
merge, and resolve the conflict in SKILL.md. `trailer_for` returns `commit=348036e7...`, which is the merge (2 parents).
Paste it, commit, and re-record H: `FAIL ['hooks/doctrine_cards.js:COMMIT-TOUCHES']` with the reason
`348036e7 did not change skills/concurrent-writers-shared-tree/SKILL.md`.
**Fix:** give both sides one definition. Make COMMIT-TOUCHES ask the same question as the generator:
`git log -1 --format=%H <commit> -- <source>` must equal `<commit>`. Or add `-m` to the diff-tree argv, so that a merge
which changes the path against a parent counts. Add a MERGE-REDERIVED drill declared PASS.

### WR-04: the TRAILER clause is not load-bearing, and its "forced PASS" proof measures the population instead

**File:** `tools/card_lineage.py:329-334` (judge), `tools/test_card_lineage.py:~690-711` (V-CLG-EVERY-CLAUSE TRAILER branch);
ledger state.G reason ("forcing each of the 10 clauses to PASS flips its drill FAIL to PASS")
**Issue:** `judge` makes the other six clauses UNMEASURED when `clauses["TRAILER"]["outcome"] != PASS or trailer is None`.
`trailer` comes from a separate `parse_trailer` call (`:328`), so the `trailer is None` guard alone already keeps the card
red, and c_trailer's outcome never changes a verdict. The gate does not force TRAILER PASS. It narrows the population
to marker-carrying members, so the flip it records proves that the CARD_TOKEN branch of `population()` is load-bearing,
not the TRAILER clause. G-lineage.md says this honestly ("the population was narrowed"). The ledger reason claims a
forced PASS for all 10 clauses.
**Scenario (reproduced, /tmp/clg-review/trailer_forced.py):** set `cl.CLAUSES["TRAILER"] = _forced` and judge the
UNLINEAGED-CARD, TRAILER-ABSENT and TRAILER-UNPARSEABLE drills: each is still `FAIL`, with 6 failing clauses. Replacing
c_trailer with an always-PASS stub would leave 30/30 green.
**Fix:** either drop the `trailer is None` half of the guard, so that the six clauses depend on TRAILER's outcome (then a
forced TRAILER PASS crashes into `trailer=None`, which needs handling), or keep the defence in depth and correct the
ledger reason to "9 clauses forced PASS; TRAILER is redundant with the parse guard and the population narrowing is proven
instead". Do not claim a flip that was never driven.

## Info

### IN-01: "the trailer is the last line" is documented but not enforced

**File:** `tools/card_lineage.py:12, 91-92`; G-lineage.md Method ("the last line of each card is one comment line")
**Issue:** `_marker_lines` accepts a marker line anywhere in the file, and CARD-EDIT-UNRECORDED shows a line after the
trailer passing every per-card clause. The rule exists only as prose.
**Fix:** either require `marks[0] == lines[-1]` (after dropping the trailing empty line) and FAIL/UNMEASURED otherwise,
or drop "last line" from the docstring and the evidence.

### IN-02: SOURCE-CURRENT and the COMMIT-* clauses judge `trailer["source"]`, not the canonical path

**File:** `tools/card_lineage.py:222, 256, 269`
**Issue:** When SOURCE-PATH fails, the other clauses still run against the foreign path the trailer names. The
SOURCE-PATH drill shows the effect: SOURCE-CURRENT, COMMIT-TOUCHES and COMMIT-DIGEST all PASS against DS's SKILL.md
for the CW card. The verdict is still FAIL, but the per-clause report says the CW lineage is current when it was never
checked against CW's source.
**Fix:** use `_source_rel(trailer["skill"])` in those three clauses, or make them UNMEASURED "source path wrong" when
SOURCE-PATH is not PASS.

### IN-03: the ledger reason mixes the 30-clause gate with mutant figures from the 28-clause version

**File:** `vault/programs/skill-capability/ledger.json` state.G reason
**Issue:** The reason says "gated by tools/test_card_lineage.py (30/30 clauses)" and, in the same sentence, cites mutants
that "turned 5 checks red (23/28)" and "(27/28)". Those figures come from 06-02 Task 2, when the gate had 28 clauses
(06-02-SUMMARY.md:99,105). They are sourced honestly, but the reason does not say which version they were measured on, so
a reader cannot reconcile 28 with 30.
**Fix:** add "(measured on the 28-clause gate, 06-02 Task 2)" or re-run both mutants against the 30-clause gate.

---

_Reviewed: 2026-10-03_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
