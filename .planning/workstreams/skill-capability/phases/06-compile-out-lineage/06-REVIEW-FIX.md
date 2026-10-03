---
phase: 06-compile-out-lineage
fixed_at: 2026-10-03
review_path: .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-10-03 (appended per finding as each landed)
**Source review:** .planning/workstreams/skill-capability/phases/06-compile-out-lineage/06-REVIEW.md
**Iteration:** 1
**Where verification ran:** in the checkout `.claude/worktrees/sc-run` on host gex44, as the orchestrator asked (no
extra review-fix worktree was created). Every gate ran there, in the foreground, against committed blobs, and can be
reproduced from that tree.

## RED baseline (before any fix, reviewer repros in /tmp/clg-review, not committed)

- repro.py R1 (CR-01): multi-skill card, second skill changed, H re-recorded, card untouched: `PASS []`.
- repro.py R2 (WR-01): `hooks/_shared/sub_card.js` registered `./_shared/sub_card.js`: `registered_hooks` has no
  sub_card, population is the 2 old cards, verdict `PASS []`.
- repro.py R3 (WR-02): merge-base timeout on the CLEAN fixture: `FAIL {DS:COMMIT-ANCESTOR, CW:COMMIT-ANCESTOR}`, last
  line `CARD_LINEAGE FAIL population=2`.
- merge.py (WR-03): trailer_for returns the merge commit `248b91ce` (2 parents); after pasting it and re-recording H:
  `FAIL [hooks/doctrine_cards.js:COMMIT-TOUCHES]`.
- trailer_forced.py (WR-04): TRAILER forced PASS on UNLINEAGED-CARD, TRAILER-ABSENT, TRAILER-UNPARSEABLE: each still
  `FAIL` with 6 failing clauses (the forced clause changes no verdict).

## Fixed Issues

### CR-01: a card that names a second skill passes G after that skill changes and only H is re-recorded

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** e97ebef9
**Applied fix:** one `// COMPILED-FROM:` line per skill the card names (`parse_trailers`; a duplicate skill is
UNMEASURED). SKILL now requires the trailer skills to EQUAL the CARD_TOKEN set (a named skill with no trailer, or a
trailer for an unnamed skill, is FAIL). SOURCE-PATH, SOURCE-CURRENT and the three COMMIT-* clauses are judged per
trailer and folded FAIL > UNMEASURED > PASS. The two live cards name one skill each, so neither card changed and
`card_source_digests.json` / H-drift.md are untouched.
**RED -> GREEN:** new drills MULTI-SKILL-LINEAGED (declared PASS), MULTI-SKILL-RERECORDED (FAIL {CW:SOURCE-CURRENT}),
MULTI-SKILL-UNLINEAGED (FAIL {CW:SKILL}). Before the code change: 29/33, with MULTI-SKILL-UNLINEAGED judged `PASS {}`
(the bypass) and LINEAGED read as a duplicate. After: 33/33. The reviewer's repro.py R1 (no trailer added for
third-skill) now reads FAIL on CW:SKILL from the moment the card names the second skill, before that skill even
changes.

### WR-01: DISPATCHER-COVERED cannot see the `./<subdir>/x.js` registration variant

**Files modified:** `tools/skill_coverage.py`, `tools/skill_mirror_drift.py`, `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** 7e2c429f
**Applied fix:** `skill_coverage.registered_hooks(text, dotslash=False)` gains an opt-in `./<rel>` branch in the same
parser loop (mapped to `posixpath.normpath("hooks/" + rel)`), threaded through `discover_cards` and
`skill_mirror_drift.committed_card_pairs`. Defaults are unchanged, so pillar D's coverage class, its recorded WR-07
limit and pillar H's pair set do not move (D 17/17, H 16/16, D-coverage.md / H-drift.md untouched). G's
DISPATCHER-COVERED uses `committed_card_pairs(..., dotslash=True)`; the population is every tracked `hooks/**/*.js`
outside `hooks/tests/` and `hooks/_tests/` (live population still 2: the only other non-test subdirectory hook,
`hooks/_shared/hook-runtime.js`, names no skill).
**RED -> GREEN:** behavioural RED is the reviewer's repro.py R2 (`PASS []`, population 2). New drills
SUBDIR-CARD-DOTSLASH (declared FAIL ALL7(hooks/_shared/sub_card.js)) and DISPATCHER-UNCOVERED-DOTSLASH (FAIL
{DISPATCHER-COVERED}); DISPATCHER-UNCOVERED now copies the card to `hooks/tests/deep_card.js`, since `hooks/sub/` is
inside the sweep. Each half is load-bearing (measured by monkeypatch): the old top-level regex turns
SUBDIR-CARD-DOTSLASH into `FAIL {DISPATCHER-COVERED}` (exact set breaks), and ignoring `dotslash` turns
DISPATCHER-UNCOVERED-DOTSLASH into `PASS {}`. Gate 35/35.

### WR-02: a git failure inside a clause yields verdict FAIL, indistinguishable from real drift

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** 2c80f09a
**Applied fix:** clause outcomes carry `git: true` when git did not answer (`_git_reason`: git missing, a
`git <sub> failed:` OS error/timeout, any `smd.BATCH_FAILURES` reason, or a non-zero rc that is not an absence
answer such as "does not exist"). `fold_verdict`: any measured FAIL, or an UNMEASURED that is not git (no trailer,
missing source, zero population), is FAIL; when every non-PASS clause is git-tagged the verdict is INCONCLUSIVE and the
CLI tail names the clauses. A trailer commit that does not resolve is classified by `rev-parse --is-shallow-repository`:
in a shallow clone it is git-tagged UNMEASURED (missing history is not drift), in a complete history it cannot be an
ancestor, so COMMIT-ANCESTOR is a measured FAIL (COMMIT-UNKNOWN now asserts that via a new FAIL_EXPECT table).
**RED -> GREEN:** new V-CLG-GIT-FAILURE-MIDJUDGE (smd.git_run failing for one subcommand: merge-base timeout,
diff-tree rc=128, cat-file OS error; plus a red control where the merge-base stub on SOURCE-CHANGED-RERECORDED still
reads FAIL) and drill SHALLOW-CLONE (depth-1 `file://` clone of the clean fixture, declared INCONCLUSIVE). Before the
code: all three stubs read `FAIL`, SHALLOW-CLONE read `FAIL`, COMMIT-UNKNOWN's ancestor was UNMEASURED (33/37). After:
37/37; the reviewer's repro.py R3 now reads `CARD_LINEAGE INCONCLUSIVE ... reason=git did not answer in ...`.

### WR-03: `--trailer-for` emits a merge commit that COMMIT-TOUCHES then rejects

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** a9271418
**Applied fix:** one definition, `card_lineage.last_change(repo, rev, source)` (path-limited `git log -1 --format=%H`),
used by both `trailer_for` and COMMIT-TOUCHES; COMMIT-TOUCHES passes when `last_change(commit, source) == commit`,
otherwise FAIL naming the last commit that did change it. A merge that resolved the source counts, exactly as the
generator counts it.
**RED -> GREEN:** new drill MERGE-REDERIVED (CW's SKILL.md edited on two branches, conflict resolved inside the merge,
precondition asserts trailer_for names the 2-parent merge, declared PASS). Before: `FAIL {CW:COMMIT-TOUCHES}`
("did not change"), as in the reviewer's merge.py. After: PASS; merge.py itself now reads `PASS []`. Gate 38/38.
V-CLG-GIT-FAILURE-MIDJUDGE now stubs `log` for this clause instead of `diff-tree`.

### IN-01: "the trailer is the last line" is documented but not enforced

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** b7200f52
**Applied fix:** enforced (option a). `parse_trailers` returns the parsed trailers with the problem "not at end of
file" when a non-marker line follows the lineage block (one trailing newline is not a line); TRAILER is then a
measured FAIL. Both live cards end on their marker line, so they are unaffected.
**RED -> GREEN:** new drill TRAILER-NOT-LAST (comment appended after CW's trailer, H re-recorded). Before: `PASS {}`.
After this commit: FAIL (declared ALL7(CW) here; WR-04 below narrows it to {CW:TRAILER}). CARD-EDIT-UNRECORDED, which
reached H-RECORD-CURRENT by the same append, now edits the card body above the lineage block. Gate 39/39.

### WR-04: the TRAILER clause is not load-bearing, and its "forced PASS" proof measures the population instead

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md` (ledger reason in the final ledger commit below)
**Commit:** b163452f
**Applied fix:** made TRAILER load-bearing (option a). The `trailer is None` half of the guard is gone: the six depend
on TRAILER's outcome alone. UNMEASURED (absent / duplicate skill / unparseable) leaves them UNMEASURED; PASS or the
measured FAIL from IN-01 judges them on the parsed trailers; a forced PASS on a card without trailers judges an empty
list (SKILL is a measured FAIL, per-trailer clauses "no trailer"; no crash). TRAILER-NOT-LAST, where every trailer
parses and only the position fails, is TRAILER's singleton.
**RED -> GREEN:** before the judge change TRAILER-NOT-LAST read ALL7(CW), and the new defence-in-depth row (TRAILER
forced PASS on TRAILER-ABSENT) had SKILL UNMEASURED. After: V-CLG-EVERY-CLAUSE forces all 10 clauses and each singleton
flips FAIL -> PASS -> FAIL; the marker-only population is kept as a separately labelled row ("population CARD_TOKEN
branch"), not a TRAILER claim; TRAILER forced PASS on TRAILER-ABSENT stays FAIL on SKILL. The reviewer's
trailer_forced.py still reads FAIL on its three drills, which is now the stated defence in depth: an always-PASS
c_trailer would turn V-CLG-DRILL-TRAILER-NOT-LAST and V-CLG-EVERY-CLAUSE red. Gate 39/39.

### IN-02: SOURCE-CURRENT and the COMMIT-* clauses judge `trailer["source"]`, not the canonical path

**Files modified:** `tools/card_lineage.py`, `tools/test_card_lineage.py`, `vault/programs/skill-capability/evidence/G-lineage.md`
**Commit:** fbdbf0fc
**Applied fix:** SOURCE-CURRENT, COMMIT-TOUCHES and COMMIT-DIGEST judge `_source_rel(trailer["skill"])`; the
trailer's source string is judged by SOURCE-PATH only.
**RED -> GREEN:** SOURCE-PATH is redefined as a true singleton (only the path string is wrong,
`skills/<skill>/skill.md`, with CW's own digest and commit); the reviewer's foreign-path case becomes
SOURCE-PATH-FOREIGN, declared {CW:SOURCE-PATH, CW:SOURCE-CURRENT, CW:COMMIT-DIGEST}. Before the change SOURCE-PATH read
four clauses and SOURCE-PATH-FOREIGN read only {CW:SOURCE-PATH} (the content clauses PASSed against DS's file).
After: both exact, SOURCE-PATH's forced-PASS flip holds. Gate 40/40.

### IN-03: the ledger reason mixes the 30-clause gate with mutant figures from the 28-clause version

**Files modified:** `vault/programs/skill-capability/ledger.json` (state.G only)
**Commit:** 1f2227a0
**Applied fix:** re-measured both mutants on the current 40-clause gate instead of annotating the old figures. Each was
applied in place to `tools/card_lineage.py`, the gate run, and the file restored with `git checkout --` (the clean
tree was committed first; the restored gate read 40/40):
- COMMIT-DIGEST always PASS: `CLG_PASS=32/40` (8 red: DRILL-TRAILER-SHA-DIGIT, SOURCE-PATH-FOREIGN, GHOST-SKILL,
  COMMIT-UNKNOWN, SHALLOW-CLONE, COMMIT-WRONG-DIGEST, EVERY-CLAUSE, EVIDENCE-CURRENT).
- SOURCE-CURRENT reading the working tree: `CLG_PASS=37/40` (3 red: DRILL-WORKTREE-ONLY, DRILL-GHOST-SKILL,
  EVIDENCE-CURRENT).

The same commit holds the WR-04 part of the ledger: state.G's reason now says that each of the 10 clauses forced PASS
flips its own singleton (TRAILER via TRAILER-NOT-LAST), and it names the population narrowing as its own row instead
of a TRAILER flip. The other figures were also brought up to date (40/40 clauses, 32 drills, gate about 5.0 s).
**Ledger coupling:** only state.G's G-lineage.md pin moved, `f852af7f...` -> `abe493da57fd5599...` (sha256 of the
committed LF blob, last written at fbdbf0fc and unchanged at 1f2227a0). `card_source_digests.json` (`985aa980...`) and H-drift.md (`2e8cdccc...`) are
byte-unchanged, so state.H is untouched. `frozen` and every other ledger line are byte-identical; this was checked by
diffing each line except state.G's.

## Final verification (checkout sc-run, gex44, foreground, HEAD 1f2227a0)

- `python3 tools/test_card_lineage.py`: `CLG_PASS=40/40  threshold=40/40`
- `python3 tools/card_lineage.py`: `CARD_LINEAGE PASS population=2 head=1f2227a0`
- `python3 tools/test_skill_drift.py`: `SKD_PASS=16/16`
- `python3 tools/test_skill_coverage.py`: `SKC_PASS=17/17`
- `node --check` on both hooks: ok; `node hooks/tests/test-doctrine-cards.js`: `DOCTRINE_CARDS_PASS=37/37`;
  `node hooks/tests/test-destructive-doctrine-card.js`: `DDC_PASS=15/15`; `python3 tools/test_card_precision.py`:
  `SCA_PASS=36/36`
- `python3 tools/test_skill_capability_program.py --pillar X`: `CEP_PILLAR_X=PASS` for A, B, C, D, F, G, H
- `python3 tools/test_skill_capability_program.py --status`: `"violations": []`

No hook file changed (both live cards name exactly one skill and already end on their trailer), so neither card was
re-derived and pillar H's record did not move.

---

_Fixed: 2026-10-03_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
