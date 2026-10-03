---
phase: 04-coverage-criticality-and-freshness
plan: 01
subsystem: skill-capability pillar D
tags: [coverage, criticality, sweep, pillar-D, gate]
requires: []
provides:
  - tools/skill_coverage.py (discovered sweep, discover_cards(), --measure-live, --json)
  - tools/test_skill_coverage.py (pillar D gate, 15 V-SKC clauses)
  - evidence/D-live-gex44.json (raw facts, host gex44)
  - evidence/D-coverage.md (prg)
key-files:
  created:
    - tools/skill_coverage.py
    - tools/test_skill_coverage.py
    - vault/programs/skill-capability/evidence/D-live-gex44.json
    - vault/programs/skill-capability/evidence/D-coverage.md
decisions:
  - "Coverage and criticality are derived at gate time; the recording holds raw facts only"
status: complete
plan_head_before: 2dd5ab6ce2410b40a976d20dbc3f77875601991e
commits: 2
actuals:
  tokens: 28000
  tasks: 2
  commits: 2
---

# Phase 4 Plan 01: pillar D coverage + criticality Summary

Discovered sweep of every skill on the repo plane (24) and the recorded gex44 live plane (185), with coverage class
(opportunity_detector / card / none) derived from the dispatcher registrations and the adapter source, and criticality
(high / medium / low) from plane-labelled evidence. The gate drives two positive controls, four drills, synthetic paths,
CRLF copies and an empty-recording case.

## Commits (task commits; this SUMMARY is a third, docs commit)

- 1ad9ee71 feat(04-01): D -- coverage sweep tracer, classes derived from dispatcher registrations
- 8313c340 feat(04-01): D -- criticality rule, gex44 live recording, drills

`plan_head_before` 2dd5ab6c. `git rev-list --count 2dd5ab6c..HEAD` also counts the parallel plan 04-02 commits in the same
tree (a94256e6, 97ded664), so `commits: 2` is this plan's own commits, counted by pathspec, not the range.

## Gate

`python3 tools/test_skill_coverage.py` last line: `SKC_PASS=15/15`, exit 0. Clauses: V-SKC-POPULATION, REGISTRATIONS,
POSITIVE-CONTROL, CLASS-TOTAL, EVIDENCE-CURRENT, EVIDENCE-DRILL, CRLF-CONTROLS, CRITICALITY-RULE,
DRILL-DETECTOR-UNREGISTERED, DRILL-ADAPTER-REMOVED, DRILL-CARD-UNREGISTERED, DRILL-STUBS-REMOVED, SYNTHETIC-PATHS (a-d,
each with a control), RECORDING-CRLF, UNMEASURED-NOT-NONE.

## Measured counts per plane (planes are never summed)

| plane | skills | coverage | criticality |
|---|---|---|---|
| repo | 24 | opportunity_detector 1, card 1, none 22 | high 0, medium 4, low 20 |
| gex44 (live, recorded) | 185 | opportunity_detector 1, card 1, none 183 | high 11, medium 5, low 169 |

gex44 recording counts: entries 186, skill_dirs 185, dangling_symlinks 1, dirs_without_skill_md 24, commands_excluded 86;
evidence items: 10 rule_stub, 1 hard_rule, 1 activation. Heat-map membership (column only): repo 0 of 24, gex44 39 of 185.

High criticality with coverage none on gex44: 9 (plan predicted 8): develop-here-prove-there, evaluation-corpus-governance,
guard-event-reachability, instrument-before-claim, monetary-quantity-integrity, presence-is-not-residency,
real-context-reachability, recurring-work-cardinality (the 8 stubs) and claude-power-pack.

## Red run (subprocess, mutated dispatcher)

Copy of `hooks/hook-dispatcher.js` with the one `script: '../skills/claude-power-pack/hooks/doctrine_cards.js'` line removed:

    python3 tools/test_skill_coverage.py --dispatcher /tmp/disp_no_cards.js ; rc=1
      FAIL V-SKC-POSITIVE-CONTROL concurrent-writers-shared-tree: 'none' != 'opportunity_detector'
      FAIL V-SKC-EVIDENCE-CURRENT ... is not the current render (run --write-evidence)
      FAIL V-SKC-CRLF-CONTROLS ...  FAIL V-SKC-DRILL-DETECTOR-UNREGISTERED removed 0 ...  FAIL V-SKC-DRILL-ADAPTER-REMOVED ...
      SKC_PASS=10/15

## Other checks

- CE one-off (`ce._check_evidence("D", prg, ...)` with `ce.lf_sha256`): `[]` for the task 1 render and for the final render.
- Laptop-shape check: `D-coverage.md` with every LF turned into CRLF, passed to `evidence_current` against the render: `True`.
- `git diff --quiet 2dd5ab6c HEAD -- tools/skill_invocations.py` rc=0 (imported, not edited).
- Gate grep for `expanduser|subprocess|urllib` outside comments: 0. Library naming either control skill: 0.
  The evidence file has no CRLF; the recording holds no class words.

## Deviations from Plan

1. [Rule 3 - plumbing] The Task 1 commit already contains the full criticality rule and the `--measure-live` recorder in
   `tools/skill_coverage.py` (the plan staged those into Task 2). Behaviour is the same; only the commit split differs.
   The Task 1 gate exercised the repo plane only.
2. [Rule 1 - portability] A first version of V-SKC-RECORDING-CRLF used a backslash inside an f-string expression, a
   SyntaxError before Python 3.12; fixed before the Task 2 commit (the laptop interpreter version is unknown).
3. Observation, not a defect: claude-power-pack is `high` on gex44 because `~/.claude/CLAUDE.md` line 15 sits inside the
   `## HARD RULES -- ROUTER` section and carries the token `skills/claude-power-pack`. That is the stated rule applied to
   recorded evidence, so the high-and-none list is 9, not the 8 the plan predicted.
4. The gate's V-SKC-REGISTRATIONS line prints per-chain counts for all chains (43 registrations, 37 distinct scripts) and
   states 15 distinct PreToolUse scripts; only PreToolUse chains feed cards.

## Auth gates, stubs, threat flags

None. No stubs. T-04-01..03 mitigations are implemented as listed (recording holds names, `~/.claude/...` file labels,
line numbers and counts only; classes computed at gate time; empty or schema-mismatched recording is INCONCLUSIVE).

## Owner line for 04-04

`[D]` The laptop live plane is not recorded: run `python tools/skill_coverage.py --measure-live --host laptop` there, commit
`D-live-laptop.json`, re-run `python tools/test_skill_coverage.py --write-evidence`.

## Self-Check: PASSED
