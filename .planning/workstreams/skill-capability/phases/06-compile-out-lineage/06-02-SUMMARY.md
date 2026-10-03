---
phase: 06-compile-out-lineage
plan: 02
subsystem: skill-capability pillar G (compile-out lineage gate)
status: complete
tags: [lineage, gate, drills, pillar-G, evidence]
requires: [06-01 tools/card_lineage.py judge/fail_set/CLAUSES/population/trailer_for, lineage trailers on both cards]
provides: [tools/test_card_lineage.py (V-CLG-*, 30 clauses), vault/programs/skill-capability/evidence/G-lineage.md]
affects: [06-03 G closure (ledger G evidence, gate argv, G-lineage.md pin)]
tech-stack:
  added: []
  patterns: [temp-repo fixture seeded from HEAD blobs, exact fail-set drills, forced-pass load-bearing flips, committed-blob evidence currency]
key-files:
  created: [tools/test_card_lineage.py, vault/programs/skill-capability/evidence/G-lineage.md]
  modified: []
decisions:
  - "Fixture commits R/A/B/C built once per run and copytree'd per drill (DG-07); identity, autocrlf=false, gpgsign=false, empty hooksPath passed with -c AND written to the repo-local config"
  - "Added a per-drill UNMEASURED-outcome check for 8 drills, so a measured FAIL where the judge could not measure is not hidden by an equal fail set"
  - "Missing committed evidence is FAIL ('run --write-evidence and commit'); any other git failure reading it is INCONC"
metrics:
  duration: "~8 min wall (20:50:30Z - 20:58:30Z)"
  completed: 2026-10-03
plan_head_before: f5846eb3b9e7902846b6512fa5c4047744cac4a5
actuals:
  tokens: 14600   # chars/4 over the two created files (45616 + 12619 bytes)
  tasks: 3
  commits: 3
---

# Phase 6 Plan 02: pillar G lineage gate Summary

`tools/test_card_lineage.py` drives `tools/card_lineage.judge` from both sides. The live checkout and a clean temp
fixture both PASS. Each of 23 tamper drills reproduces its declared fail set exactly. Forcing any one of the 10
clauses to PASS turns its drill PASS, which shows each clause can change the verdict. The gate renders
`evidence/G-lineage.md` and compares it with the committed blob. Result: `CLG_PASS=30/30  threshold=30/30`, about
3.4 s on gex44.

## Commits

| # | sha | subject |
|---|-----|---------|
| 1 | a179624d | test(06-02): G -- lineage gate tracer, live and clean poles plus the core red drill |
| 2 | a057c82f | test(06-02): G -- all 23 lineage drills exact-set, git failure INCONCLUSIVE, every clause load-bearing |
| 3 | 3e60b990 | feat(06-02): G -- lineage gate driven from both poles, every clause load-bearing |

`git rev-list --count f5846eb3..HEAD` = 3. Every commit used a pathspec (`git commit -F <msgfile> -- <paths>`).
`git log -1 --format=%s` matched the message file each time.

## Full gate output (final, HEAD 3e60b990)

```
ok   V-CLG-LIVE-CLEAN HEAD judges PASS, population=2, fail set empty
ok   V-CLG-POSITIVE-CONTROL population=2 holds both known cards; trailer skills concurrent-writers-shared-tree, destructive-state-authorization equal discover_cards
ok   V-CLG-DRILL-CLEAN PASS {}
ok   V-CLG-DRILL-SOURCE-CHANGED-RERECORDED FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT}
ok   V-CLG-DRILL-SOURCE-CHANGED-RAW FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:SOURCE-CURRENT}
ok   V-CLG-DRILL-REDERIVED PASS {}
ok   V-CLG-DRILL-TRAILER-SHA-DIGIT FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:SOURCE-CURRENT}
ok   V-CLG-DRILL-TRAILER-ABSENT FAIL {ALL7(hooks/destructive_doctrine_card.js)}
ok   V-CLG-DRILL-TRAILER-DUPLICATE FAIL {ALL7(hooks/destructive_doctrine_card.js)}
ok   V-CLG-DRILL-TRAILER-UNPARSEABLE FAIL {ALL7(hooks/destructive_doctrine_card.js)}
ok   V-CLG-DRILL-SKILL-MISMATCH FAIL {hooks/doctrine_cards.js:SKILL}
ok   V-CLG-DRILL-SOURCE-PATH FAIL {hooks/doctrine_cards.js:SOURCE-PATH}
ok   V-CLG-DRILL-GHOST-SKILL FAIL {H-RECORD-CURRENT, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES, hooks/doctrine_cards.js:SOURCE-CURRENT}
ok   V-CLG-DRILL-COMMIT-UNKNOWN FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR, hooks/doctrine_cards.js:COMMIT-DIGEST, hooks/doctrine_cards.js:COMMIT-TOUCHES}
ok   V-CLG-DRILL-COMMIT-NOT-ANCESTOR FAIL {hooks/doctrine_cards.js:COMMIT-ANCESTOR}
ok   V-CLG-DRILL-COMMIT-NOT-TOUCHING FAIL {hooks/doctrine_cards.js:COMMIT-TOUCHES}
ok   V-CLG-DRILL-COMMIT-WRONG-DIGEST FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST}
ok   V-CLG-DRILL-FLOOR-ONE FAIL {FLOOR}
ok   V-CLG-DRILL-FLOOR-ZERO FAIL {DISPATCHER-COVERED, FLOOR, H-RECORD-CURRENT}
ok   V-CLG-DRILL-UNLINEAGED-CARD FAIL {ALL7(hooks/new_card.js)}
ok   V-CLG-DRILL-DISPATCHER-UNCOVERED FAIL {DISPATCHER-COVERED}
ok   V-CLG-DRILL-CARD-EDIT-UNRECORDED FAIL {H-RECORD-CURRENT}
ok   V-CLG-DRILL-RECORD-UNPARSEABLE FAIL {H-RECORD-CURRENT}
ok   V-CLG-DRILL-CRLF PASS {}
ok   V-CLG-DRILL-WORKTREE-ONLY PASS {}
ok   V-CLG-SUBPROCESS-RED red fixture rc=1 'CARD_LINEAGE FAIL population=2' naming hooks/doctrine_cards.js SOURCE-CURRENT=FAIL; clean fixture rc=0
ok   V-CLG-GIT-FAILURE git missing: live and fixture judge INCONCLUSIVE ('git not found'), no exception escaped; restored judge PASS
ok   V-CLG-EVERY-CLAUSE declared sets cover all 10 clauses; 10 forced passes flipped their drill FAIL->PASS and back on restore
ok   V-CLG-EVIDENCE-CURRENT committed vault/programs/skill-capability/evidence/G-lineage.md equals the render (after CRLF->LF)
ok   V-CLG-EVIDENCE-DRILL render accepted, CRLF copy accepted, one-character change refused
CLG_PASS=30/30  threshold=30/30
```
rc=0. In this summary the ALL7 rows are abbreviated. The tool prints all seven `<card>:<CLAUSE>` members, and the
rendered evidence lists them in full.

## Red checks run outside the gate (each /tmp copy was deleted afterwards)

- **Exact-set check (Task 1):** in a copy, SOURCE-CHANGED-RERECORDED declared `{}`. The copy printed
  `FAIL V-CLG-DRILL-SOURCE-CHANGED-RERECORDED declared FAIL {} | observed FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT}`
  and `CLG_PASS=6/7`, rc=1.
- **Mutant 1, COMMIT-DIGEST always PASS (Task 2):**
  ```
  FAIL V-CLG-DRILL-TRAILER-SHA-DIGIT declared FAIL {...:COMMIT-DIGEST, ...:SOURCE-CURRENT} | observed FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT}
  FAIL V-CLG-DRILL-GHOST-SKILL declared FAIL {H-RECORD-CURRENT, ...:COMMIT-DIGEST, ...:COMMIT-TOUCHES, ...:SOURCE-CURRENT} | observed (no COMMIT-DIGEST)
  FAIL V-CLG-DRILL-COMMIT-UNKNOWN declared FAIL {...:COMMIT-ANCESTOR, ...:COMMIT-DIGEST, ...:COMMIT-TOUCHES} | observed (no COMMIT-DIGEST)
  FAIL V-CLG-DRILL-COMMIT-WRONG-DIGEST declared FAIL {hooks/doctrine_cards.js:COMMIT-DIGEST} | observed PASS {}
  FAIL V-CLG-EVERY-CLAUSE COMMIT-DIGEST: drill COMMIT-WRONG-DIGEST itself is not ok
  CLG_PASS=23/28  threshold=28/28   rc=1
  ```
  The two drills the plan named (COMMIT-WRONG-DIGEST, TRAILER-SHA-DIGIT) both went red, and so did 3 more.
- **Mutant 2, SOURCE-CURRENT reads the working-tree source instead of HEAD (Task 2):**
  ```
  FAIL V-CLG-DRILL-WORKTREE-ONLY declared PASS {} | observed FAIL {hooks/doctrine_cards.js:SOURCE-CURRENT} | hooks/doctrine_cards.js:SOURCE-CURRENT: worktree mutant
  CLG_PASS=27/28  threshold=28/28   rc=1
  ```
- **Evidence-missing branch:** before commit 3, the gate printed `FAIL V-CLG-EVIDENCE-CURRENT ... not committed: run
  --write-evidence and commit` (`CLG_PASS=29/30`). After the commit it printed ok. This matches the order the caller
  gave: render, then commit, then run the gate.

## Timings (gex44, whole gate, DG-10 bound 60 s)

- Final (30 clauses): 3.36 s, 4.17 s, 3.36 s.
- After Task 2 (28 clauses): 3.48 s, 3.76 s, 3.43 s.
- The laptop runtime was not measured. It goes in the [G] owner-bundle note in 06-03.

## Evidence

- `vault/programs/skill-capability/evidence/G-lineage.md`, CE `lf_sha256` = `f852af7ff6214faf3169068b34bd1cf1419b5f691ff07c8689af50b8a3a713f0`
  (raw sha256 is the same, since the file has no CR).
- Two consecutive `--write-evidence` runs gave byte-identical files (same sha256). `grep -c '^command: '` = 5,
  `grep -c $'\r'` = 0, and `grep -cE 'gex44|/tmp/|kobicraft'` = 0.
- CE one-off: `ce._check_evidence("G", {"kind":"prg","ref":<G-lineage.md>,"sha256":<lf_sha256>}, ce.Resolver(),
  owners_G, denoms)` returned `[]`.

## Regression and the gate runs the caller asked for (foreground, at HEAD 3e60b990)

- `python3 tools/test_card_lineage.py`: `CLG_PASS=30/30  threshold=30/30`, rc=0
- `python3 tools/card_lineage.py`: `CARD_LINEAGE PASS population=2 head=3e60b990`, rc=0. All 14 per-card clauses
  and the 3 gate clauses are PASS.
- `python3 tools/test_skill_drift.py`: `SKD_PASS=16/16`, rc=0
- `python3 tools/test_skill_coverage.py`: `SKC_PASS=17/17`, rc=0, `ok V-SKC-EVIDENCE-CURRENT`
- `python3 tools/test_skill_capability_program.py --pillar X` (timeout 1900): A, B, C, D, F and H each printed
  `CEP_PILLAR_<X>=PASS` with rc=0.
- `git status --porcelain -- skills/ hooks/` was empty before and after every gate run, so the drills wrote only
  into temp dirs.

## Deviations from Plan

1. **[Rule 2 - correctness] UNMEASURED-outcome check.** `fail_set` collects every non-PASS clause, so on its own it
   cannot tell UNMEASURED from FAIL. The must_haves require absent, duplicate and unparseable trailers, a zero
   population, an unreadable record and a missing source to be UNMEASURED. `UNMEASURED_EXPECT` now asserts that for
   TRAILER-ABSENT, TRAILER-DUPLICATE, TRAILER-UNPARSEABLE, UNLINEAGED-CARD, FLOOR-ZERO (FLOOR and
   DISPATCHER-COVERED), RECORD-UNPARSEABLE, GHOST-SKILL (SOURCE-CURRENT) and COMMIT-UNKNOWN (its three commit
   clauses). A drill whose fail set matches but whose outcome class does not now prints FAIL. This adds to the
   declared sets and changes none of them.
2. **No change to any declared fail set.** All 23 rows matched the plan's derivation on the first run. No fixture
   or clause fix was needed.
3. **Commit granularity.** The plan commits only in Task 3. Following the executor's per-task protocol, Tasks 1
   and 2 were also committed (`test(06-02)`), and Task 3 used the plan's exact subject.
4. **Branch allow-list.** As in 06-01, the worktree branch is `mission/skill-capability-run`, not `agent-*`.
   `git.base-branch --is-protected` returned `false`, so the commits were made on it.

## Out of scope / deferred

- Gate argv and the ledger G evidence belong to 06-03. CE `gate_argv_problem` requires `argv[0] == "python"`, so
  the G gate argv there must be `["python", "tools/test_card_lineage.py"]`. G-lineage.md is pinned at
  `f852af7f...`. STATE.md, ROADMAP.md and ledger.json were not touched, as the caller asked.
- Liveness wiring of tools/test_card_lineage.py is part of 06-03's G closure.

## Known Stubs

None. A grep of the test file for TODO, FIXME and placeholder found nothing.

## Threat Flags

None. The gate writes only under its own TemporaryDirectory, plus G-lineage.md when run with `--write-evidence`.
T-06-06..09 are mitigated as the plan specifies: HEAD-blob seeds and unchanged skills/ and hooks/ status; exact
sets plus forced-pass flips; committed-blob currency with a one-character drill; and fixture identity, autocrlf,
gpgsign and hooksPath all pinned.

## Self-Check: PASSED

- tools/test_card_lineage.py and vault/programs/skill-capability/evidence/G-lineage.md exist and are committed
  (`git status --porcelain` on both is empty).
- a179624d, a057c82f and 3e60b990 are all present in `git log f5846eb3..HEAD`.
