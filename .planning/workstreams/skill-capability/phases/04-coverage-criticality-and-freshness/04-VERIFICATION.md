---
phase: 04-coverage-criticality-and-freshness
verified: 2026-10-03T19:26:45Z
status: passed
score: 4/4 roadmap success criteria + 4/4 plans (one must-have per plan driven red independently) verified (SC-D, SC-H)
covered_files:
  - .planning/workstreams/skill-capability/REQUIREMENTS.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-01-PLAN.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-01-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-02-PLAN.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-02-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-03-PLAN.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-03-SUMMARY.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-04-PLAN.md
  - .planning/workstreams/skill-capability/phases/04-coverage-criticality-and-freshness/04-04-SUMMARY.md
  - tools/router_freshness_gate.py
  - tools/skill_coverage.py
  - tools/skill_mirror_drift.py
  - tools/test_router_freshness_gate.py
  - tools/test_skill_coverage.py
  - tools/test_skill_drift.py
  - vault/programs/skill-capability/card_source_digests.json
  - vault/programs/skill-capability/evidence/D-coverage.md
  - vault/programs/skill-capability/evidence/D-live-gex44.json
  - vault/programs/skill-capability/evidence/H-drift.md
  - vault/programs/skill-capability/evidence/H-live-gex44.json
  - vault/programs/skill-capability/ledger.json
covered_digest: "v1:sha256:e480a6cc21bf9f3a021a54885e347e329c9033f6c97f39da0ed155efa32c0ce0"
behavior_unverified: 0
overrides_applied: 0
verifier: gsd-verifier subagent, host gex44, worktree sc-run, HEAD bec199a7
---

# Phase 4: Coverage, criticality and freshness - Verification

**Goal:** Every installed skill gets a coverage and criticality class (discovered, not curated); drift is gated.
**Requirements:** SC-D, SC-H. **Host:** gex44 (python3). **HEAD:** bec199a7. **Re-verification:** No.

## Roadmap success criteria

| # | Criterion | Command | Observed | Verdict |
|---|-----------|---------|----------|---------|
| 1 | Sweep with a population floor and a positive control | `python3 tools/test_skill_coverage.py` | rc=0, `SKC_PASS=17/17`. Fed an empty recording (`--recording {}`): `INCONCLUSIVE V-SKC-POPULATION plane emptyrec.json: missing fields [...]` and `INCONCLUSIVE V-SKC-CRITICALITY-RULE plane gex44 not available`, never "all none" | PASS |
| 2 | Drift gate red on a mutated mirror | `python3 tools/skill_mirror_drift.py --live --live-root <tmp>` (tmp = `git archive HEAD skills/*`) | identical copy rc=0, `IDENTICAL 24`; after appending one byte to `motion-promo/SKILL.md` rc=1, `DRIFT motion-promo changed=['SKILL.md']` | PASS |
| 3 | `--pillar D` PASS | `timeout 1900 python3 tools/test_skill_capability_program.py --pillar D` | `CEP_PILLAR_D=PASS`, rc=0 (re-runs the declared gate) | PASS |
| 4 | `--pillar H` PASS | `timeout 1900 python3 tools/test_skill_capability_program.py --pillar H` | `CEP_PILLAR_H=PASS`, rc=0 | PASS |

## Gates run (foreground, bounded)

| Gate | Result |
|------|--------|
| `python3 tools/test_skill_coverage.py` | rc=0, `SKC_PASS=17/17` |
| `python3 tools/test_skill_drift.py` | rc=0, `SKD_PASS=16/16` |
| `python3 tools/test_router_freshness_gate.py` | rc=1. Every V-RFG clause passes except `V-RFG-CLEAN` (see below). The new skill-drift clauses pass: GREEN, RED, UNMEASURED, NO-LIVE, GIT-FAILURE |
| `HOME=<empty dir>` runs of the D and H gates | `SKC_PASS=17/17`, `SKD_PASS=16/16`. Both gates read only committed files, so the laptop `--final` can re-run them |
| `--pillar A`, `--pillar B`, `--pillar C` | all `PASS` (earlier pillars did not regress) |
| `python3 tools/test_skill_invocations.py` (owner baseline) | `SKINV_PASS=11/12`. The only FAIL is `V-SKINV-REAL-TYPED: positive-control transcript not found`. It is laptop-only and was already failing in phase 3 |

### V-RFG-CLEAN red is honest. It is not a phase 4 defect

- **`router absent` was already there before phase 4.** I took `tools/router_freshness_gate.py` from `a98f883c^` (before the H wiring) and ran it from this checkout. It prints `V-ROUTER-LINKS FAIL router absent` too. `router_path()` builds `/home/kobii/projects/-home-kobii-missions-skill-capability/memory/MEMORY.md` from `root.parents[1]`. That is a laptop install layout, and this gex44 clone does not have it.
- **`V-ROUTER-SKILL-DRIFT FAIL` is real drift on this host.** `ls ~/.claude/skills/android-reverse-engineering/scripts/` shows only `.sh` files. The live copy is dated 2026-09-19. `git ls-tree HEAD` shows 4 `.ps1` files on top of those. Phase 4 did not edit gex44's `~/.claude`, by decision D-02. The finding goes to the Owner in the `[H]` bundle line.
- So the router gate now fails for two reasons, and both are named and true. The new check was placed before the early return for an absent router, so it is not hidden behind that return.

## Per-plan must-haves: can each gate return the other answer? (independent drills)

| Plan | Must-have | Drill I ran | Result |
|------|-----------|-------------|--------|
| 04-01 (D) | Positive control: CWST = opportunity_detector. A mutated dispatcher passed via `--dispatcher` exits 1 with `FAIL V-SKC-POSITIVE-CONTROL` | `grep -v "hooks/doctrine_cards.js'" hooks/hook-dispatcher.js > tmp`, then `--dispatcher tmp`. Control: an unmodified copy | mutant rc=1, `SKC_PASS=12/17`, `FAIL V-SKC-POSITIVE-CONTROL concurrent-writers-shared-tree: 'none' != 'opportunity_detector'`. Control `17/17` |
| 04-02 (H) | Repo side read from committed blobs. Both poles: IDENTICAL vs DRIFT | temp live root built from committed blobs, then one byte added. Plus the real `--live` on gex44 | 24 IDENTICAL rc=0. Then DRIFT rc=1. Real host: rc=1, `DRIFT android-reverse-engineering missing_live=[4 .ps1]`, counts 13/1/10/0 match `H-live-gex44.json` |
| 04-03 (H) | Card vs source: SOURCE_CHANGED after a committed source edit. Real record CURRENT at HEAD | real `--cards`. Then in a temp clone, commit an edit to `skills/destructive-state-authorization/SKILL.md` and run `--cards --repo .` | real: both pairs CURRENT, rc=0. Clone: `SOURCE_CHANGED destructive-state-authorization` rc=1, `test_skill_drift.py` `FAIL V-SKD-CARD-SOURCE-CURRENT` (14/16), `--pillar H` `CEP_PILLAR_H=FAIL` |
| 04-04 (D/H closure) | Pins are LF sha256. `--pillar D` PASS | temp clone: set state.D prg sha256 to all zeros, run `--pillar D`. Then restore | `FAIL L4 D: prg file ... D-coverage.md sha256 changed since it was cited`, `CEP_PILLAR_D=FAIL`. Restored: `PASS` |

The gate files also carry their own mutants, and they pass: V-SKD-RECORD-DRILL kills 9 mutants, one per check part, and V-SKC-DRILL-* covers four drills. The in-process mutants only add to the drills above. My drills do not depend on them.

## Ledger state

- `state.D`, `state.H` = `IMPLEMENTED_AND_VERIFIED`. Gate argvs are `["python","tools/test_skill_coverage.py"]` and `["python","tools/test_skill_drift.py"]`, and `savings: []`.
- **The evidence pins match the files.** I recomputed each with my own LF-normalized sha256, which equals `ce.lf_sha256`:
  - D: `D-coverage.md` matches `a23854ef…`, and `D-live-gex44.json` matches `442578e8…`.
  - H: `H-drift.md` matches `8d0ec054…`, `H-live-gex44.json` matches `43831a34…`, and `card_source_digests.json` matches `cdce7261…`.
  - All of the cited commits exist: D `1ad9ee71`, `8313c340`; H `97ded664`, `a94256e6`, `06dae4b0`, `a98f883c`.
- **Frozen object unchanged.** `frozen` at HEAD equals `frozen` at FROZEN_AT `217d72b5`. Result: True.
- **Phase 4 changed only D and H.** Comparing the ledger at `8b0137aa` (the last commit before phase 4) with HEAD: the only top-level key that changed is `state`, and inside it only `D` and `H`. A, B and C are byte-identical.
- **Owner bundle.** `vault/programs/skill-capability/owner-bundle.md` has one `[D]` line and two `[H]` lines, all `host: laptop`. They cover the laptop recording procedure, the fetch precondition for the `repo_commit` reproduction, the android drift finding, and the three new ways the router can go red.

## Discovered, not curated (SC-D)

- **Repo plane.** `skills/*/SKILL.md` gives 24, and `skill_coverage.py --json` gives 24 rows.
- **Live plane.** The recording `D-live-gex44.json` lists 161 skills. A fresh glob of `~/.claude/skills/*/SKILL.md` also gives 161. The symmetric difference is empty, so the recording is current.
- **Every skill is classified.** `D-coverage.md` has a full per-skill row table for gex44: 161 skills, each with coverage, criticality and the file that produced each class.
- **Classes come from code, not a typed list.** No literal skill list exists in `tools/skill_coverage.py`. The coverage classes are derived from the dispatcher plus the adapter at gate time, as drill 04-01 shows.
- **Stated limit (review WR-07).** The parser skips 33 `./<file>` registrations. 26 of them resolve, and none of those 26 is a deny card that names a skill. The other 7 have no file in this checkout. `D-coverage.md` line 12 says all of this. It is a disclosed limit, not a silent hole.

## Requirements coverage

| Req | Status | Evidence |
|-----|--------|----------|
| SC-D | SATISFIED | criterion 1, drill 04-01, `--pillar D` PASS |
| SC-H | SATISFIED | criteria 2 and 4, drills 04-02 and 04-03, router wiring reached (`V-ROUTER-SKILL-DRIFT` printed by the frozen owner) |

REQUIREMENTS.md still shows SC-D and SC-H as `Pending`, and the ROADMAP phase 4 plan boxes are still unchecked. Updating those is the orchestrator's bookkeeping. It is not a codebase gap.

## Anti-patterns

| File | Finding | Severity |
|------|---------|----------|
| the 6 phase 4 tool files | `grep -nE "TBD\|FIXME\|XXX"` finds nothing | none |
| `vault/programs/skill-capability/owner-bundle.md` line 8 (`[D]`) | Says "gex44 ... (185 skill dirs; ...)". The recording says `skill_dirs 161, entries 186`, and the ledger reason says 161. The figure is stale from plan time. The 9 high/none figure is correct | Info. The fix is one word in an Owner-facing line. No gate reads it |

## Laptop plane (not a phase gap)

Three items belong to the Owner bundle: the laptop D live recording, the laptop H `--live` run and its recording, and the decision on syncing gex44's live skills.

## Gaps

None. Status `passed`.

---
_Verified: 2026-10-03T19:26:45Z, gsd-verifier, host gex44_
