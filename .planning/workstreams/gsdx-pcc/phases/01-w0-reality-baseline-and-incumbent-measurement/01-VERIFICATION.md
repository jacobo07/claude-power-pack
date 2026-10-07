---
phase: 01-w0-reality-baseline-and-incumbent-measurement
workstream: gsdx-pcc
verified: 2026-10-07
status: passed
score: 20/20
roadmap_success_criteria: 3/3 verified
behavior_unverified: 0
overrides_applied: 0
re_verification: true
re_verified: 2026-10-07 (worker epoch 3; evidence: 01-verify-{vrb,vtl,gate-provider,git}.log committed at baf27b86)
covered_files:
  - .planning/workstreams/gsdx-pcc/ROADMAP.md
  - .planning/workstreams/gsdx-pcc/DENOMINATOR.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-01-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-02-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-03-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-04-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-05-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-06-PLAN.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-01-SUMMARY.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-02-SUMMARY.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-03-SUMMARY.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-04-SUMMARY.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-05-SUMMARY.md
  - .planning/workstreams/gsdx-pcc/phases/01-w0-reality-baseline-and-incumbent-measurement/01-06-SUMMARY.md
  - modules/gsd_x/goal/providers/gate.py
  - tools/gsdx_reality_baseline.py
  - tools/test_gsdx_reality_baseline.py
  - tools/gsdx_goal_timeline.py
  - tools/test_gsdx_goal_timeline.py
  - vault/liveness/reachability_registry.json
  - vault/knowledge_base/ukdl-universal.md
covered_digest: "v1:sha256:e3377648abe6a550f272b04db5913ba967e40d571819fb1a1c33affb661a69d0"
human_verification_resolved:
  - test: "Run `python tools/test_gsdx_reality_baseline.py` (17 V-RB gates at HEAD) and commit the output with EXIT=<n>"
    expected: "GSDX_REALITY_BASELINE_PASS=17/17  threshold=17/17, EXIT=0"
    why_human: "No committed log of the current 17-gate suite exists. 01-02-SUMMARY.md:42 reports 16/16 (before c75dc3cc); 17/17 appears only as prose in 01-05-SUMMARY.md:20 and 01-INCUMBENT.md:68. The verifier may not run python here."
  - test: "Run `python tools/test_gsdx_goal_timeline.py` and commit the output with EXIT=<n>"
    expected: "GSDX_GOAL_TIMELINE_PASS=8/8  threshold=8/8, EXIT=0"
    why_human: "Only SUMMARY prose (01-03-SUMMARY.md:42) claims 8/8; no committed log."
  - test: "git show --stat 58934936: confirm 01-r01-red.log is in the same commit as the gate.py fix, or committed before it"
    expected: "01-r01-red.log committed with or before 58934936"
    why_human: "01-01 truth 1 is a commit-ordering claim; not observable from file contents."
  - test: "git diff fbca24fc 96bdb8b1 -- vault/liveness/reachability_registry.json and git diff --numstat fbca24fc HEAD -- vault/knowledge_base/ukdl-universal.md"
    expected: "registry: only known_orphans changes; ukdl: additions only (deletions column 0)"
    why_human: "01-04 truth 4 and 01-01 truth 6 are diff-shape claims; not observable from file contents."
  - test: "Decide whether the mutation-suite UNKNOWN is acceptable for Phase 6 planning, or relaunch with CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1 (or free RAM) and run the in-copy mutation-suite command"
    expected: "Either an explicit Owner acceptance that Phase 6 measures its own incumbent first, or a measured row for test_gsd_x_goal_mutation.py"
    why_human: "Closing it needs a launch-environment change the mission is forbidden to make unattended (ROADMAP.md:33-38)."
---

# Phase 1: W0 Reality, baseline and incumbent measurement -- Verification Report

**Phase goal (ROADMAP.md:105-106):** Every API the spec names is premise-verified, R01 is fixed red-first, and the
incumbent full path is measured so every later speedup has an honest baseline.
**Done line (ROADMAP.md:51-52):** gate_provider 18/18; `EVIDENCE.md` with the incumbent table.
**Verified:** 2026-10-07. **Mode:** initial (no previous VERIFICATION.md). **Method:** Read/Grep/Glob only, judged
from committed logs (`EXIT=<n>` trailers) and source. No command was run by the verifier.

## Verdict

All three roadmap success criteria are VERIFIED from committed logs and source, and the Done line holds. Four plan-level
truths stay UNCERTAIN only because their evidence is a command output that no committed log carries, or a git-history
shape that file contents cannot show. None is FAILED. Status is `human_needed` because those must be run before the
phase is called passed. No BLOCKER was found.

**Re-verification (2026-10-07, worker epoch 3): status `passed`, 20/20.** The commands this report asked for were
run and committed at baf27b86:

| Log | Result | Row |
|---|---|---|
| `01-verify-vrb.log` | 17/17, EXIT=0 | P6 |
| `01-verify-vtl.log` | 8/8, EXIT=0 | P8 |
| `01-verify-gate-provider.log` | 18/18, EXIT=0 | - |
| `01-verify-git.log` | red log in 58934936; ukdl `24 0`; registry hunks only in `known_orphans` | P1, P4, P11 |

baf27b86 also fixed the self-sizing threshold warning by pinning the gate count at 17. The Owner settled item #5 on
2026-10-07 at 20:05: the mutation-suite timing stays UNKNOWN in Phase 1 and becomes Phase 6's entry obligation
(DENOMINATOR R11).

## Observable truths

| # | Truth | Status | Evidence (file:line) |
|---|---|---|---|
| SC1 | HR-PREMISE-001 premise check recorded for evidence_bundle, mutation_drill, change_impact, parallel_mesh pure fns, tower; real signatures cited file:line | VERIFIED | Real set `01-premises.log:1` `EXIT=0`. The verifier is silent on success (`modules/error_prevention/premise_verifier.py:115-120,157`). Control `01-premises-control.log:2,5` `[FAIL] decide in modules.parallel_mesh.pm_02_intent`, `EXIT=1`. Signatures with file:line are in `01-PREMISES.md:16-69`, and `01-EVIDENCE.md:88-100` summarises them. Spot-checked against source: `modules/cognitive_os/scheduler.py:94` decide, `modules/tower/ratchet.py:164` promote, `tools/mutation_drill.py:159` drill, `modules/gsd_x/goal/git_state.py:124` tree_id all match. Note: the full signature table is in PREMISES.md, linked from EVIDENCE.md, not inlined in it |
| SC2 | R01 driven red, fixed, mutation-drilled; gate_provider 18/18; UKDL T-entry | VERIFIED | RED `01-r01-red.log:7,20-21` (`observed: ''`, 17/18, EXIT=1). Fix in source at `modules/gsd_x/goal/providers/gate.py:77`: `subprocess.run(cmd,stdout=sys.stdout,stderr=sys.stderr)`. GREEN `01-r01-green.log:20-21`. Phase-end fresh run `01-phase-end-gate-provider.log:20-21` 18/18, EXIT=0. Drill `r01-drill.json:5-6` reverts exactly that line, and `01-r01-drill.log:3-4` shows `MUTANT KILLED`, EXIT=0. The drill's exit map gives KILLED=0 only when the control passed (CONTROL_INVALID=4, `tools/mutation_drill.py:205`). UKDL heading at `vault/knowledge_base/ukdl-universal.md:15295`, one occurrence |
| SC3 | Incumbent table in EVIDENCE.md: per-suite wall time, judge replay time, one real goal's sweep->judge timeline; UNKNOWN where unmeasurable | VERIFIED (UNKNOWN accepted, see below) | Table at `01-EVIDENCE.md:106-126`: 17 suites measured, 3 runs each. Raw rows in `01-incumbent-suites.jsonl` with 18 guard rows, 0 `"verdict": "CHANGED"`. Per-run logs in `incumbent-logs/`, e.g. `test_gsd_x_goal_long_run_provider-1.log:18`. The cold and min sums were re-added by hand and match: 154.096 and 146.680. Real-goal timeline: `01-timeline-g002.log:1-63` (6 judged gates, replay 2.9 s, EXIT=0). Current-engine fixture through the real CLI: `01-timeline-fixture.log:1-11` (converged, replay 0.4 s, judge CLI wall 1.558 s, EXIT=0). The mutation suite is UNKNOWN with its reason at `01-incumbent-suites.jsonl:71`, and the lower-bound label is at `01-EVIDENCE.md:135` |
| P1 | 01-01: RED captured before gate.py changed and lands in the same commit as the fix | VERIFIED (re-verified at baf27b86) | Log content is correct (`01-r01-red.log`). `01-verify-git.log`: `git show --stat 58934936` lists `01-r01-red.log` in the same commit as `modules/gsd_x/goal/providers/gate.py`, EXIT=0 |
| P2 | 01-01: no collateral in sweep / gate_class / cli / chaos | VERIFIED | `01-r01-collateral-pre.log:17,32,61,80` = `01-r01-collateral-post.log:17,32,61,80` (14/14, 11/11, 25/25, 15/15), all EXIT=0 |
| P3 | 01-01: stderr-only mutant observed and recorded as a blind spot | VERIFIED | `01-r01-drill-stderr.log:1,3` 18/18, EXIT=1 (SURVIVED); disclosed at `01-EVIDENCE.md:84` |
| P4 | 01-01: exactly one UKDL heading, additions-only diff | VERIFIED (re-verified at baf27b86) | One match at `ukdl-universal.md:15295`. `01-verify-git.log`: `git show --numstat 0c93c0e9 -- vault/knowledge_base/ukdl-universal.md` = `24 0` (additions only) |
| P5 | 01-02: `suites` is hermetic and serial, appends rows, refuses the live-mutating suite unless `--in-copy`, the guard exits 3 on change or UNKNOWN, `table` renders UNKNOWN rows | VERIFIED | `tools/gsdx_reality_baseline.py:121` (HOME/USERPROFILE/GSDX_GOALS_ROOT), `:294-298` (refusal rc 2), `:203-225` (in-copy clean git), `:346-358` (guard -> 3), `:252-253` (UNKNOWN rows), `:44` (heartbeat exclusion by name only) |
| P6 | 01-02: `tools/test_gsdx_reality_baseline.py` passes every gate (plan said 15; there are now 17) | VERIFIED (re-verified at baf27b86: `01-verify-vrb.log` GSDX_REALITY_BASELINE_PASS=17/17 threshold=17/17 EXIT=0; count pinned at 17 in baf27b86) | 17 `check("V-RB-...")` calls counted in `tools/test_gsdx_reality_baseline.py:87-276`. The two additions are GUARD-EXCLUDES-ONLY-NAMED at `:183` (with a control at `:181`) and IN-COPY-CLEAN-GIT at `:250`. Both are justified by measured confounds and both add coverage, so the deviation from 15 is acceptable. No committed log of a 17/17 run exists (human_verification #1) |
| P7 | 01-03: `recorded` reads a COPY through GoalLog.read(); replay null when seconds absent; corrupt or missing input refused with exit 2 | VERIFIED | `tools/gsdx_goal_timeline.py:124-129` (copytree then `GoalLog(...).read()`, GoalLogError -> 2), `:94-96` (replay None unless numeric). The g-002 cross-check matches the plan's expectation of 6 gates / 2.9 s (`01-timeline-g002.log:58-60`) |
| P8 | 01-03: `tools/test_gsdx_goal_timeline.py` 8/8 | VERIFIED (re-verified at baf27b86: `01-verify-vtl.log` GSDX_GOAL_TIMELINE_PASS=8/8 EXIT=0) | 8 gates in source (`tools/test_gsdx_goal_timeline.py:109-175`); no committed run log (human_verification #2) |
| P9 | 01-03: the fixture drives the real CLI to CONVERGED, hermetic | VERIFIED | `01-timeline-fixture.log:1` `converged True`, temp fixture root at `:10`, EXIT=0 |
| P10 | 01-04: liveness red captured before the freeze, frozen, re-run to 0 | VERIFIED | `01-liveness-before.md:3,77` (57 offenders, EXIT=1); `01-liveness-baseline.log:2` EXIT=0; `01-liveness-after.md:3,77` (0, EXIT=0) |
| P11 | 01-04: the freeze changes only known_orphans (prior orphans plus exactly the named offenders) | VERIFIED (re-verified at baf27b86: `01-verify-git.log` hunks @@-5 / @@-7,0 +8,51 / @@-11 +62,6 all inside the `known_orphans` array, which opens at line 2 and closes at `],`; re-read by worker epoch 3) | The registry holds the frozen names (`vault/liveness/reachability_registry.json:2,21,67`). Whether only that key changed needs a git diff (human_verification #4) |
| P12 | 01-04: DENOMINATOR R10 added OPEN, no row altered | VERIFIED (row present) | `DENOMINATOR.md:66` R10 OPEN, frozen at 96bdb8b1 |
| P13 | 01-05: every goal suite has a row or UNKNOWN; gate_provider = 18/18; baselines match; mutation suite in a copy or UNKNOWN; guard SAME; fixture `observed` non-empty | VERIFIED | `01-EVIDENCE.md:108-126`: 8 `= n/m` baselines and no DIFFERS. The mutation suite has an UNKNOWN row plus the rc 2 refusal row tagged `[in copy]`. 0 CHANGED guard rows. Fixture `observed ['2 passed']` at `01-timeline-fixture.log:3-6`; guard `01-guard-timeline.log:1-3` SAME, EXIT=0 |
| P14 | 01-06: phase-end fresh gate_provider 18/18 and liveness 0 | VERIFIED | `01-phase-end-gate-provider.log:20-21`; `01-phase-end-liveness.md:3,77` |
| P15 | 01-06: EVIDENCE.md has the full chain and verdicts that are never upgraded | VERIFIED (one wording overclaim, see anti-patterns) | `01-EVIDENCE.md:50-59` (incident -> root cause -> class -> fix -> regression -> guard -> UKDL), `:306-317` (verdicts: R01 POSIX UNJUDGED, mutation timing UNJUDGED, liveness OBSERVED, not PROVEN) |
| P16 | 01-06: R01 DONE only with every piece of evidence | VERIFIED | `DENOMINATOR.md:57`. Each cited artifact exists: 58934936 in the log at `01-EVIDENCE.md:32`, the 18/18 log, the KILLED log, the UKDL id, and EVIDENCE.md |
| P17 | 01-06: worktree clean after the final commit, nothing pushed | VERIFIED (clean) | The session-start git status snapshot for branch gsdx/pcc is clean. "Nothing pushed" was not independently checked |

**Score:** 20/20 VERIFIED, 0 UNCERTAIN, 0 FAILED. The roadmap contract is 3/3. (Initial pass 16/20; P1, P6, P8 and P11 were re-verified at baf27b86 from `01-verify-{vrb,vtl,gate-provider,git}.log`, all EXIT=0.)

### Decision on the mutation-suite UNKNOWN (SC3)

I accept it as an UNKNOWN within SC3's own wording, recorded where it could not be measured. My reasons:

1. **Every attempt is on disk.**
   - Run 1 hit an instrument gap, not an engine result: `incumbent-logs/test_gsd_x_goal_mutation-1.log:1` reads `INSTRUMENT_FAILED: git could not report the targets' state`.
   - That gap was fixed in-phase, with a new gate (`tools/test_gsdx_reality_baseline.py:232-252`).
   - Run 2 was killed by a host-level memory-pressure reaper.
2. **Closing it needs a forbidden step.** It takes a Claude Code launch-environment change (`CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1`), and the operating constraints forbid the mission from making that kind of change unattended (`ROADMAP.md:33-38`: never ask mid-run, record and continue).
3. **The result is not upgraded.** It is labelled UNJUDGED (`01-EVIDENCE.md:315`), the family wall sum is labelled a lower bound (`:135`), and no number was estimated.

**Caveat (WARNING, not a gap):** "unmeasurable" here means not measured on this host in this run. It does not mean it cannot be measured. Phase 6 (mutant farm) compares directly against this suite and has no incumbent timing for it (`01-INCUMBENT.md:71`). Phase 6 must not claim a mutation speedup until it has measured this incumbent itself. It goes to the Owner as human_verification #5.

### Decision on 17 V-RB gates versus the 15 planned

The deviation is acceptable and adds coverage:

- `V-RB-GUARD-EXCLUDES-ONLY-NAMED` comes from the 01-01 heartbeat confound (`01-EVIDENCE.md:297`). It carries its own control: a non-heartbeat write must still trip the guard (`tools/test_gsdx_reality_baseline.py:180-184`).
- `V-RB-IN-COPY-CLEAN-GIT` comes from the run-1 refusal.

The pass count for 17 is unverified (P6).

## Required artifacts

| Artifact | Exists | Substantive | Wired | Status |
|---|---|---|---|---|
| `modules/gsd_x/goal/providers/gate.py` (fix line) | yes | `:77` contains the planned string exactly | used by `dispatch` at `:131`, and the real CLI fixture shows `observed` populated | VERIFIED |
| `tools/gsdx_reality_baseline.py` | yes | fingerprint/suites/unknown/table, `def parse_summary` at `:51` | it produced `01-incumbent-suites.jsonl` and the table; no non-.planning caller | VERIFIED (orphan-by-design instrument, see warnings) |
| `tools/test_gsdx_reality_baseline.py` | yes | 17 gates, both poles | - | VERIFIED (run log missing) |
| `tools/gsdx_goal_timeline.py` | yes | `def timeline` at `:56`, recorded + fixture | it produced the 3 timeline JSON/log pairs | VERIFIED |
| `tools/test_gsdx_goal_timeline.py` | yes | 8 gates | - | VERIFIED (run log missing) |
| `01-EVIDENCE.md` | yes | contains "Production Reality" (`:306`) and the incumbent table | - | VERIFIED |
| `vault/liveness/reachability_registry.json` | yes | known_orphans frozen | read by reachability.py, which exits 0 | VERIFIED |
| `DENOMINATOR.md` R01 / R10 | yes | `:57` DONE with evidence; `:66` OPEN | - | VERIFIED |

## Key links

| From | To | Via | Status |
|---|---|---|---|
| supervisor (`gate.py:74-80`) | run log -> `harvest` `observed` (`gate.py:182-186`) | inherited std handles | WIRED: `01-r01-green.log:7`, `01-timeline-fixture.log:3-6` |
| `r01-drill.json` | `gate.py:77` | `tools/mutation_drill.py --spec` | WIRED: the `old` string equals the source line |
| `gsdx_reality_baseline.py suites` | `01-incumbent-suites.jsonl` -> `01-incumbent-suites-table.md` -> `01-EVIDENCE.md` | `_append` / `render_table` | WIRED: the EVIDENCE table rows equal the table rows |
| `gsdx_goal_timeline.py fixture` | `tools/gsd_x_goal.py` (real CLI) | subprocess | WIRED: `gsdx_goal_timeline.py:141`, and converged=True in the log |

## Behavioral spot-checks / probes

Step 7b was skipped by the verifier: there is no shell on this host. The orchestrator's committed logs stand in for spot-checks
(RED/GREEN/drill/phase-end/fixture, all with `EXIT=`). There are no `scripts/*/tests/probe-*.sh` probes for this phase.

## Requirements coverage

| Requirement | Plan | Status | Evidence |
|---|---|---|---|
| R01 | 01-01, 01-06 | SATISFIED | `DENOMINATOR.md:57` DONE; SC2 |
| R10 (added this phase) | 01-04 | OPEN by design, to Phase 10 | `DENOMINATOR.md:66` |

## Anti-patterns found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `tools/test_gsdx_reality_baseline.py` | 189-193 | The threshold is derived from the gates that ran (`threshold={total}/{total}`), and six gates sit behind `hasattr(rb, "LIVE_MUTATING")`. Removing that constant would print `11/11` and exit 0 while six gates vanish | WARNING | A self-sizing denominator: a later edit can shrink the suite to green. Fix: a fixed `EXPECTED = 17` and fail when `total != EXPECTED` |
| `tools/test_gsdx_reality_baseline.py` | 77 | The tool-absent branch prints a stale `0/16  threshold=16/16`; there are 17 gates | INFO | A cosmetic drift, and the same root cause as the row above |
| `tools/gsdx_reality_baseline.py`, `tools/gsdx_goal_timeline.py` | - | No caller outside their own tests and `.planning`. `reachability.py` scans `modules/` only (`01-phase-end-liveness.md:5`), so the liveness gate is blind to them | WARNING | Instruments the later phases (9, 10) need are not in any done-gate. Declare or wire them by Phase 9/10 |
| `01-EVIDENCE.md` | 300 | "17 suites + 2 mutation attempts ... all SAME" overclaims. The jsonl has 18 guard rows: the reaped run 2 never wrote one | WARNING | One measurement call has no closing guard. Mitigated by the later SAME timeline guard (`01-guard-timeline.log:1`) and an empty `git status -- modules tools` (`01-INCUMBENT.md:70`) |
| `01-EVIDENCE.md` | 126 | The table carries a "measured" mutation row (`1 run, 0.282 s, rc 2, none`) that is the refusal, not the suite | INFO | Labelled at `:125` and `01-INCUMBENT.md:68`. A reader of the table alone could misread it |

The debt-marker scan (the standard six-token regex from the verifier procedure) over the 5 code files changed in this
phase found 0 hits. The positive control, `^import ` on the same glob, matched 37 lines in all 5 files, so the scan
could see them.

## Commands the orchestrator must run

1. `python tools/test_gsdx_reality_baseline.py` and commit the output with `EXIT=`. Expect `GSDX_REALITY_BASELINE_PASS=17/17`.
2. `python tools/test_gsdx_goal_timeline.py` and commit the output with `EXIT=`. Expect `GSDX_GOAL_TIMELINE_PASS=8/8`.
3. `git -C <wt> show --stat 58934936` (is `01-r01-red.log` in it or earlier?) and `git -C <wt> log --oneline -- .planning/.../01-r01-red.log`.
4. `git -C <wt> diff fbca24fc 96bdb8b1 -- vault/liveness/reachability_registry.json` (only `known_orphans` may change).
5. `git -C <wt> diff --numstat fbca24fc HEAD -- vault/knowledge_base/ukdl-universal.md` (the deletions column must be 0).
6. `gsd_run query verification.fingerprint <phaseDir> <covered_files...>`, pasting the result into `covered_digest`.

If 1-5 come back as expected, the four UNCERTAIN rows become VERIFIED and the status may move to `passed`. The one
exception is the mutation-suite item (#5), which stays an Owner decision.

## Gaps summary

There are no blocking gaps. The phase goal is met: premises are verified with a failing control, R01 is fixed red-first
and drilled (revert KILLED), the fix is visible through the real CLI, and the incumbent is measured with one honestly
labelled UNKNOWN. What remains is evidence hygiene (two test-suite runs and three git-shape checks without committed
logs) and three warnings for later phases:

- the self-sizing threshold in the V-RB suite;
- the new instruments sit outside the liveness aperture;
- Phase 6 has no incumbent mutation-suite timing.

---
_Verified: 2026-10-07_
_Verifier: Claude (gsd-verifier), Read/Grep/Glob only_
