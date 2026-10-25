---
phase: 08-s9-knowledge-vault-ukdl-cbr-red-team-master-done-gate
plan: 01
subsystem: knowledge-vault
tags: [fc-12, incidents, ukdl, cbr, s8-predicate, s9_kv_check]
requires:
  - phase: 07-s7-historical-replay-champion-challenger
    provides: 07-PIN.json pinned ledger prefix; S5/S6/S7 suites run here for evidence
provides:
  - tools/s9_kv_check.py with check_incidents, check_ukdl, check_spec_predicate and a 28-case selftest
  - eight FC-12 incident files whose every citation was executed in this phase
  - dated UKDL section with 3 promoted laws and an Evaluated, not promoted list
  - S8 activation predicate with its measured value at the 07 pin
affects: [08-02, 08-03]
tech-stack:
  added: []
  patterns: [citations are executed, not read; every negative control shown to fire; absent evidence is exit 2]
key-files:
  created:
    - tools/s9_kv_check.py
    - vault/incidents/2026-10-24-flow-compression-phase-seal-without-frontmatter.md
    - vault/incidents/2026-10-24-flow-compression-fixture-from-memory-of-reader.md
    - vault/incidents/2026-10-24-flow-compression-control-never-shown-to-fire.md
    - vault/incidents/2026-10-24-flow-compression-class-regex-over-match.md
    - vault/incidents/2026-10-24-flow-compression-execution-plane-mismatch.md
    - vault/incidents/2026-10-25-flow-compression-plan-premise-not-in-code.md
    - vault/incidents/2026-10-25-flow-compression-figure-without-basis.md
    - vault/incidents/2026-10-25-flow-compression-harness-state-leak.md
  modified:
    - vault/knowledge_base/ukdl-universal.md
    - vault/specs/flow-compression.md
key-decisions:
  - "Three laws promoted (seal agrees with scheduler, inferred figure prints basis, drill needs a no-op control); the other five candidates linked to existing IDs, not duplicated"
  - "CBR recorded UNMEASURED: the static-check proof held, but no tower family fits mission orchestration and adding one changes prompt routing"
  - "S8 stays DORMANT: predicate FALSE at the 07 pin (55 mission_blocked rows, 0 with independent_work=true)"
duration: not measured (no wall-clock bracket kept across the context compaction)
completed: 2026-10-25
status: complete
commits: 3
plan_head_before: 4a7a0cdb48fae7caddc59b6461b0a5aead252894
actuals:
  tokens: 20000
  tasks: 3
  commits: 3
---

# Phase 8 Plan 01: Incidents, UKDL promotions, CBR proof and S8 predicate Summary

Eight FC-12 incident files whose gate, commit and init-progress citations are executed by a new checker (`tools/s9_kv_check.py`), three new UKDL laws promoted after a recorded grep, a CBR fresh-inheritance proof that held but is reported UNMEASURED, and the S8 work-stealing predicate recorded as FALSE at the 07 pin.

`commits: 3` was measured with `git rev-list --count` from the persisted ledger (`4a7a0cdb..HEAD`) before this SUMMARY's own commit, which makes four.

## Commits

| Task | Commit | What |
|---|---|---|
| 1 (tracer) | `a18e6a46` | `s9_kv_check` incident checker and the phase-seal incident |
| 2 | `b4cb82da` | seven further FC-12 incident files |
| 3 | `d705026e` | UKDL section, S8 predicate, `ukdl` and `spec` checks, selftest 28/28 |

## Bullet-to-class table

| # | Source group (phases 5 to 7, STATE.md and the plan's bullet list) | Class | Incident file |
|---|---|---|---|
| 1 | phases 1-4 sealed by hand, invisible to `init.progress` | PHASE SEAL WITHOUT GSD FRONTMATTER | `2026-10-24-flow-compression-phase-seal-without-frontmatter.md` |
| 2 | fixtures written from memory of the reader (4 cases) | FIXTURE FROM MEMORY OF THE READER | `2026-10-24-flow-compression-fixture-from-memory-of-reader.md` |
| 3 | controls and gates green because they could not go red (3 cases) | CONTROL NEVER SHOWN TO FIRE | `2026-10-24-flow-compression-control-never-shown-to-fire.md` |
| 4 | S6 class patterns typed on a word stem (4 defects) | CLASS REGEX OVER-MATCH | `2026-10-24-flow-compression-class-regex-over-match.md` |
| 5 | directive, mission card and harness name three execution planes | EXECUTION PLANE MISMATCH | `2026-10-24-flow-compression-execution-plane-mismatch.md` |
| 6 | plan named switches, events and counts the code did not hold (6 corrections) | PLAN PREMISE NOT IN CODE | `2026-10-25-flow-compression-plan-premise-not-in-code.md` |
| 7 | carried, subset and unobserved figures read as measured (4 figures) | FIGURE WITHOUT BASIS | `2026-10-25-flow-compression-figure-without-basis.md` |
| 8 | S7 harness state outlived its run (3 leaks) | HARNESS STATE LEAK | `2026-10-25-flow-compression-harness-state-leak.md` |

## UKDL grep log

Greps run with `grep -c -i -E` against the UKDL as it stood at the base (`git show 4a7a0cdb:vault/knowledge_base/ukdl-universal.md`) and against `vault/hard_rules/HARD_RULES.md`. They were re-run after the context compaction to record the counts; the hits were read before promoting. Earlier ID lookups with `grep -c -F` are listed last.

| Term | UKDL hits | HARD_RULES hits | Reading |
|---|---|---|---|
| `init\.progress` | 0 | 0 | law (a) new |
| `phase_complete` | 0 | 0 | law (a) new |
| `scheduler agrees` | 0 | 0 | law (a) new |
| `negative control` | 6 | 0 | covers law (b) |
| `fixture.*reader` | 0 | 0 | (b) narrow angle only; sub-case of the covering laws |
| `shown to fire` | 0 | 0 | (b) |
| `REGEX-STEM` | 1 | 0 | `T-REGEX-STEM-MATCHES-NOUN-001` covers law (c) |
| `over-match` | 0 | 0 | (c) |
| `no-op` | 13 | 0 | all 13 read (lines 1444-9634): hook and migration no-ops, one "no-op fix"; none is a drill control |
| `mutation drill` | 2 | 0 | `T-DRILL-VERDICT-WITHOUT-CONTROL-001` covers the clean-copy baseline only |
| `carried.unchanged` | 0 | 0 | law (e) new |
| `unobserved` | 2 | 0 | read (lines 7547, 10525): layout and tail-window cases; not about printed figures |
| `basis` | 2 | 0 | read (lines 4995, 17702): a dataset phrase and a monetary basis; not about printed figures |
| `inferred` | 3 | 0 | read (lines 1237, 6275, 6942; line 1237 is a watcher-log row): rules not inferred per session, report a fact do not guess; no law on labelling a printed figure's basis |
| `no-op drill` / `noop drill` (separate grep) | 0 | not run | law (d) new |
| `PR-SEAL|T-DRILL-NO-OP|PR-FIGURE-CARRIES|T-FIXTURE-FROM-MEMORY|T-CONTROL-NEVER` | 0 | not run | the new IDs are unique |
| `HR-PREMISE-001` | not run | 2 | covers candidate (f), the plan-premise class |

Decisions:

- (a) seal closed when the scheduler agrees: promoted as `PR-SEAL-IS-CLOSED-WHEN-THE-SCHEDULER-AGREES-001`, plus an unregistered `HR-CANDIDATE-SEAL-ASSERTS-THE-READERS-COUNT`.
- (b) fixture from memory of the reader: not promoted; linked to `T-NON-DISCRIMINATING-CONTROL-001`, `PR-SYNTHETIC-CONTROL-ASSERTS-CONSTRUCTION-001`, `T-OBSERVABLE-NOT-DISCRIMINATING-001`, `PR-CONTROL-PERTURBS-THE-SIGNAL-001`.
- (c) class regex over-match: not promoted; linked to `T-REGEX-STEM-MATCHES-NOUN-001` and `T-ZERO-MATCH-READS-AS-EMPTY-INPUT-001`.
- (d) drill needs a no-op control: promoted narrowly as `T-DRILL-WITHOUT-A-NOOP-CONTROL-001`, with links to `T-DRILL-VERDICT-WITHOUT-CONTROL-001`, `T-GREEN-SUITE-LIVE-MUTANT-001`, `T-A-CRASH-UNDER-A-MUTANT-COUNTED-AS-A-KILL-001`.
- (e) inferred figure prints its basis: promoted as `PR-INFERRED-FIGURE-PRINTS-ITS-BASIS-001`, distinguished from `PR-FIXTURE-IS-ORACLE-POPULATION-001`.
- Plan premise, harness state leak, execution plane: not promoted (covered, one-harness specific, and a recorded decision with no gate, respectively).

## CBR fresh-inheritance proof

Entry: `regex:<phase-7 VERIFICATION path>::<frontmatter status pattern>` (law (a), the strongest lesson a static check can express).

Commands (scripts in `/tmp`, outside the repo; temp root from `mktemp -d`):

```
python3 -I /tmp/s9-cbr-write.py <tmp>/gen <repo>        # modules.tower.baselines.write_generation into the temp root
python3 -I /tmp/s9-cbr-eval.py  <tmp>/gen <repo> <tmp>/mut   # separate process; modules.tower.checks.evaluate
```

Measured output:

```
WROTE /tmp/s9-cbr-9M2B1K/gen/flow_seal_proof/B0.json
LOADED generation=0 entries=1
REAL FC-SEAL-VERIFICATION-HAS-STATUS PASS pattern found
MUTATED FC-SEAL-VERIFICATION-HAS-STATUS FAIL pattern absent
CBR_PROOF HOLDS
```

The mutated tree is a copy of the phase-7 VERIFICATION with its frontmatter removed. Outcome: the proof holds mechanically. CBR is still reported UNMEASURED and not registered: none of the five families (game_mod_fidelity, kobiicraft_mode, persistent_state, web_surface, wii_homebrew) has triggers that fit mission orchestration, and adding a family changes prompt routing, which this mission does not change. Nothing was written under `vault/tower/` (scope diff below).

## Suite counts (run in this phase, foreground, `CPP_RESOURCE_ADMISSION=off`)

| Suite | Result | Evidence file |
|---|---|---|
| `tools/test_s5_reconcile.py` | `S5_PASS=44/44` | `/tmp/s9-evidence/test_s5_reconcile.out` |
| `tools/test_s6_blockers.py` | `S6_PASS=72/72` | `/tmp/s9-evidence/test_s6_blockers.out` |
| `tools/test_s7_replay.py` | `S7_PASS=164/164` | `/tmp/s9-evidence/test_s7_replay.out` |

## S8 recount

`/tmp/s9-recount.py` (and `check_spec_predicate`) read the pinned prefix through `flow_replay.load_pin` and `read_prefix` (which refuses unless the bytes hash to the pin):

```
rows 6339 torn 0 pin_rows 6339 sha b47ff018fb44766fb9e2add7b9e23276c18dc6c2ec84cb88d4709c82d95e2743
mission_blocked 55
independent_work_true 0
independent_work_keys_present 0
```

55 and 0, as 07-VERIFICATION measured. The key `independent_work` is absent from all 55 rows, so the predicate is FALSE because nothing recorded it, not because 55 rows were each measured false; the spec line says so. S8 stays DORMANT.

## Verification results

| Check | Result |
|---|---|
| `python3 tools/s9_kv_check.py --selftest` | `SELFTEST_PASS=28/28`, exit 0 |
| `incidents --glob 'vault/incidents/*flow-compression*.md' --evidence /tmp/s9-evidence --expect 8` | `INCIDENTS files=8 findings=0 exit=0` |
| `ukdl --path vault/knowledge_base/ukdl-universal.md --section 'Flow-compression S9 promotions (2026-10-25)'` | `findings=0 exit=0` |
| `spec --spec vault/specs/flow-compression.md --pin .../07-PIN.json` | `findings=0 exit=0` |
| `blocker_compiler.py decisions --cwd . --workstream flow-compression` | `measured: true`, `items: []`, exit 0 |
| `git diff --name-only 4a7a0cdb..HEAD` | 10 paths, all in the plan's `files_modified` |
| same diff restricted to `vault/tower`, `vault/hard_rules`, `gsd-core` | empty |
| OWNER_QUEUE sha256 prefix | `2c03045bfb579004`, unchanged |
| `gsd-tools query frontmatter.validate ... --schema plan` | `valid: true`, nothing missing |
| push | none |

## Deviations from Plan

**1. [Rule 1 - Bug] A dangling UKDL link caught by the new checker**
- **Found during:** Task 3, selftest. The UKDL control case failed with `LINK_UNRESOLVED`.
- **Issue:** I had linked `PR-PARSE-DECLARE-CARDINALITY-001` under Evaluated, not promoted. It is only mentioned in prose inside the `T-ZERO-MATCH-READS-AS-EMPTY-INPUT-001` entry; it has no entry of its own in the file or in HARD_RULES.md.
- **Fix:** linked `T-ZERO-MATCH-READS-AS-EMPTY-INPUT-001`, which is defined. The selftest then went 28/28.
- **Files modified:** `vault/knowledge_base/ukdl-universal.md`. **Commit:** `d705026e`.
- **Left alone (out of scope):** the base UKDL entry at line 83 still cites an ID that has no entry. Pre-existing; logged here, not repaired.

**2. [Plan wording] Verification 4 names base `dd334b92`; the dispatch base is `4a7a0cdb`**
- The scope diff was run against `4a7a0cdb`, the base the orchestrator specified and the ledger recorded.

**3. [Rule 3 - Blocking] First temp-root command refused**
- A hook refused an `rm -rf` of a scratch path that did not exist yet. Nothing was deleted; the proof used a fresh `mktemp -d` directory instead. The scratch directories remain in `/tmp`.

**4. Three promotions, not five.** Candidates (b) and (c) were covered at equal or greater strength and are linked, as D-07 requires.

## Known Stubs

None. The checker's `UNMEASURED` and `INCONCLUSIVE` paths are real outcomes with their own exit code, not placeholders.

## Threat Flags

None. No new network surface, auth path or trust-boundary file access; the checker reads repo files and the pinned ledger read-only.

## Open items for 08-02 and 08-03

- The incident open-debt entries (W1 summed mission-hours is 94 percent unobserved; W4 FC-06 zero is partly vacuous; no arm-time plane check; pre-commit branch assertion assumes `agent-*`) are recorded, not repaired.
- 08-03 imports `check_incidents`, `check_ukdl` and `check_spec_predicate` from `tools/s9_kv_check.py`.
- `.pp-capabilities` was already untracked at the start of this run and is not part of this plan.

## Self-Check: PASSED

- Created files present: `tools/s9_kv_check.py`, eight incident files (8 matched by `ls vault/incidents | grep -c flow-compression`), both edited vault files.
- Commits resolve: `a18e6a46`, `b4cb82da`, `d705026e` (`git cat-file -e`).
- Working tree: only the pre-existing untracked `.pp-capabilities`.
