---
phase: 08-owner-reconciliation-and-creation-governance
plan: 01
status: complete
subsystem: skill-capability pillar J (creation governance)
tags: [creation-governance, pillar-J, gate, skill-frontmatter]
requires: [tools/skill_coverage.py, tools/skill_mirror_drift.py, modules/skill_router/skill_index.py]
provides: [tools/skill_creation_gate.py, tools/test_skill_creation_gate.py]
affects: [08-02 (declares the 24 repo skills with declaration_lines/insert_declaration, renders evidence/J-creation-gate.md), 08-04 (ledger J gate argv)]
tech-stack:
  added: []
  patterns: [discovered population from committed blobs, CLAUSES dict with forced-PASS flips, render excludes its own currency clause]
key-files:
  created: [tools/skill_creation_gate.py, tools/test_skill_creation_gate.py]
  modified: []
decisions:
  - "Forced-PASS flips of any clause except EVIDENCE-CURRENT re-render the evidence in a clone under the forced clause, because the render records every other clause outcome"
  - "Added drill FLOOR-ONE (population 1) so FLOOR also has a singleton flip; every one of the 7 clauses is proven load-bearing"
  - "Coverage blobs are read in two batch calls (dispatcher first, then hooks/tools/SKILL.md), since the registered hook set is only known from the dispatcher text"
metrics:
  duration: 433s
  completed: 2026-10-04
plan_head_before: 419c00a274d2a89dffe1a5ac37442adb34ce590f
actuals:
  tokens: 12500
  tasks: 2
  commits: 8
---

# Phase 8 Plan 01: J creation gate Summary

A 7-clause gate, `tools/skill_creation_gate.py`, judged on committed blobs. It refuses a `skills/<name>/` directory
whose SKILL.md does not declare `metadata.opportunity_detector` (a path, or `none` plus a reason). It checks each
declaration against pillar D's coverage class from `skill_coverage`. A two-skill tracer and 17 drills prove both
poles with exact fail sets.

## Commits

| Task | Commit | Files |
|---|---|---|
| 1 + 2 (one commit, as the plan prescribes) | b989cb75 `feat(08-01): pillar J creation gate refusing undeclared skill directories` | tools/skill_creation_gate.py, tools/test_skill_creation_gate.py |

`commits: 8` is the ledger instrument (`git rev-list --count 419c00a2..HEAD` at SUMMARY time). The range also holds 7
`fix(07)` commits from the concurrent phase-7 fixer in this worktree (5f6cedd3, cd580268, 1b52cb57, 4efeae98,
4ca66182, e1e08403, 318de225). This plan's own commits are b989cb75 and the SUMMARY commit.

## Gate outputs (verbatim)

- Task 1 verify: `[PASS] V-SCG-TRACER refused=FAIL fail_set={EVIDENCE-CURRENT,agent-architecture-audit:COVERAGE-AGREES,agent-architecture-audit:DECLARED,agent-architecture-audit:FORM,agent-architecture-audit:TARGET} admitted=PASS fail_set={}`
  and `python3 tools/skill_creation_gate.py | tail -1` -> `SKILL_CREATION FAIL population=24`. `git ls-files 'skills/*/SKILL.md' > /tmp/08-01-skills.txt; echo "rc=$?"` -> `rc=0`, 24 lines.
- Task 2 verify: `timeout 600 python3 tools/test_skill_creation_gate.py` -> `rc=1`. There is 1 `[FAIL]` line, V-SCG-LIVE, as the plan expects. `SCG_PASS=31/32`.
- Suite wall time on gex44: 4.2 s to 5.1 s across runs (`# wall=4.2s` on the post-commit run; `/usr/bin/time` wall=4.79s).
- Discovered at run time: `CWST=concurrent-writers-shared-tree (hooks/doctrine_cards.js) DSA=destructive-state-authorization (hooks/destructive_doctrine_card.js) S=agent-architecture-audit adapters=['tools/skill_opportunity_signals.py']`.

## Drill table (expected = observed for every row)

| Drill | Expected fail set (outcome) | Observed | Forced-PASS flip |
|---|---|---|---|
| BASELINE | {} PASS | {} PASS | - |
| UNDECLARED-S | S:DECLARED=FAIL, S:FORM/TARGET/COVERAGE-AGREES=UNMEASURED | same | - |
| DUPLICATE-CWST | CWST:DECLARED=FAIL | same | DECLARED -> PASS, restored |
| DOTSLASH-CWST (`./hooks/doctrine_cards.js`) | CWST:FORM=FAIL | same | FORM -> PASS, restored |
| TOPLEVEL-S (keys not under metadata) | S:FORM=FAIL | same | FORM -> PASS, restored |
| NONE-NO-REASON-S | S:TARGET=FAIL | same | TARGET -> PASS, restored |
| UNTRACKED-PATH-S (on disk, never committed) | S:TARGET=FAIL, S:COVERAGE-AGREES=FAIL | same | - |
| DSA-DECLARES-CARD | DSA:COVERAGE-AGREES=FAIL | same | COVERAGE-AGREES -> PASS, restored |
| CWST-DECLARES-NONE | CWST:COVERAGE-AGREES=FAIL | same | COVERAGE-AGREES -> PASS, restored |
| README-ONLY-DIR (X=scg-readme-only) | X:DECLARED=FAIL, X:FORM/TARGET/COVERAGE-AGREES=UNMEASURED | same | - |
| ALL-SKILLS-REMOVED | FLOOR=UNMEASURED, POSITIVE-CONTROL=UNMEASURED | same | - |
| CWST-REMOVED | POSITIVE-CONTROL=FAIL | same | POSITIVE-CONTROL -> PASS, restored |
| FLOOR-ONE (added) | FLOOR=FAIL | same | FLOOR -> PASS, restored |
| REASON-EDIT-UNRENDERED | EVIDENCE-CURRENT=FAIL | same | EVIDENCE-CURRENT -> PASS, restored |
| EVIDENCE-REMOVED | EVIDENCE-CURRENT=UNMEASURED | same | EVIDENCE-CURRENT -> PASS, restored |
| CRLF-S (CRLF committed blob) | {} PASS | {} PASS | - |
| WORKTREE-ONLY-S (declaration removed from the working file only) | {} PASS | {} PASS | - |

Other lines:
- `[PASS] V-SCG-EVERY-CLAUSE flipped={COVERAGE-AGREES,DECLARED,EVIDENCE-CURRENT,FLOOR,FORM,POSITIVE-CONTROL,TARGET} missing={}`
- `[PASS] V-SCG-NO-SELF-ENROL gate files enrolled=[] offending=[]; control enrols ['concurrent-writers-shared-tree']` (DJ-06)
- `[PASS] V-SCG-GIT-MISSING rc=1 last='SKILL_CREATION INCONCLUSIVE population=0 reason=HEAD not resolvable: git not found: git executable not found on PATH or known Windows locations'; control rc=0 last='SKILL_CREATION PASS population=24'`

## V-SCG-LIVE fail set (this checkout, HEAD b989cb75)

`verdict=FAIL population=24 fail_set_size=97`. The set is exactly `<skill>:DECLARED, <skill>:FORM, <skill>:TARGET,
<skill>:COVERAGE-AGREES` for each of the 24 skills in /tmp/08-01-skills.txt, plus `EVIDENCE-CURRENT` (UNMEASURED,
evidence not committed). A script checked equality against that file: `exact live fail set: True 97`. 08-02 turns
this line PASS.

## Acceptance criteria

- `grep -cE '"(concurrent-writers-shared-tree|destructive-state-authorization)"' tools/skill_creation_gate.py` -> 0.
- Non-comment counts in the gate: `sc.coverage(` 1, `smd.is_git_failure(` 2, `smd.tracked_paths(` 1,
  `sc.discover_cards(` 1, `sc.opportunity_adapters(` 1. `git-batch-*` tokens in the gate: only `git-batch-empty`
  and `git-batch-missing`.
- `python3 tools/skill_creation_gate.py --suggest` printed 24 blocks. `git status --porcelain -- skills` printed 0
  lines afterwards, so the command only prints.
- `python3 modules/liveness/reachability.py --json` still reports 64 offenders, the plan-time baseline. Neither new
  file is a row or an offender.

## For 08-02

- `scg.declaration_lines(skill, klass, evidence)` builds the lines. `scg.insert_declaration(text, lines)` appends
  them at the end of the frontmatter and keeps CRLF. It refuses a text that already has a `metadata:` key or a
  declaration. Take the classes from `scg.judge(repo)["skills"]` (`class`, `evidence`).
- Evidence: `python3 tools/skill_creation_gate.py --render > vault/programs/skill-capability/evidence/J-creation-gate.md`,
  run after the SKILL.md declarations are committed, then commit it (record/render -> commit -> gate).
- CWST's suggested declaration is `hooks/doctrine_cards.js`. DSA's is `none`, with a reason that names
  `hooks/destructive_doctrine_card.js`. The other 22 are `none`, with the none-class reason.

## Deviations from Plan

### Auto-fixed issues

**1. [Rule 1 - Bug] Forced-PASS flips could not turn the verdict PASS**
- **Found during:** Task 2, first suite run (6 flips FAIL, verdict stayed FAIL).
- **Issue:** render() records every clause outcome except EVIDENCE-CURRENT. Forcing any other clause PASS changes
  what the render should say, so EVIDENCE-CURRENT went red and the flip only proved EVIDENCE-CURRENT.
- **Fix:** the flip clones the drill repo and re-renders and commits the evidence under the forced clause, then
  judges the clone (record/render -> commit -> gate). EVIDENCE-CURRENT's own flips run on the drill repo unchanged,
  because re-rendering would repair what the drill broke. The restore check judges the original drill repo.
- **Commit:** b989cb75.

**2. [Rule 1 - Bug] Commit helper after `git rm`**
- `git add -A -- <removed path>` fails with "pathspec did not match". After a `git rm` the helper now commits without
  `add`. Commit b989cb75.

**3. [Rule 2 - Missing coverage] Drill FLOOR-ONE added**
- The plan's drill list had no singleton for FLOOR, so FLOOR had no forced-PASS flip. FLOOR-ONE keeps only CWST
  (population 1, so FLOOR fails and POSITIVE-CONTROL passes), and now all 7 clauses flip.

**4. Two blob batch calls, not one**
- The registered hook set is only known after reading the dispatcher. So the dispatcher is read in one batch call,
  and hooks, tools/*.py and SKILL.md in a second. The evidence file gets its own call, so `git-batch-missing` maps
  to UNMEASURED. Every read is still a committed blob at the resolved commit.

**5. Repo root appended to sys.path, not inserted first**
- This lets `from modules.skill_router.skill_index import _FM_RE` resolve without the repo root shadowing an installed
  module. Before choosing the import, I measured it at 0.027 s with only stdlib modules loaded.

### Notes (unattended choices)
- The worktree branch is `mission/skill-capability-run`, not `agent-*`. I committed there because the orchestrator
  told me to. Both new files were committed with an explicit pathspec, and `git log -1 --format=%s` matched the
  subject. Phase-7 fixer files, docs/* stubs and vault/progress.md were not touched.
- I did not update STATE.md, ROADMAP.md or REQUIREMENTS.md. The orchestrator owns them.

## Known Stubs

None.

## Threat Flags

None. The gate is read-only (git reads and temp directories only) and adds no endpoint or write path.

## Self-Check: PASSED

- FOUND: tools/skill_creation_gate.py, tools/test_skill_creation_gate.py (committed in b989cb75).
- FOUND: commit b989cb75 in `git log`.
