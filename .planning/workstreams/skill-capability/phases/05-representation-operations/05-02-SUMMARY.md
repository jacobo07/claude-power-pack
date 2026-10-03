---
phase: 05-representation-operations
plan: 02
subsystem: skill-capability / pillar F
status: complete
tags: [representation-operations, gate, drills, pillar-F, prg]
requires: [05-01 (tools/skill_dedup_sweep.py, evidence/F-sweep-gex44.json, sweep half of the gate)]
provides: [vault/programs/skill-capability/f-operations.json, tools/test_skill_representation.py (operations half + evidence render), vault/programs/skill-capability/evidence/F-representation.md]
affects: [05-03 (ledger closure cites f-operations.json as `file` and F-representation.md as `prg`)]
tech-stack:
  added: []
  patterns: [references-not-figures ledger entries, exact-red-set drills, real-data drills, subprocess poles, rendered evidence with dirty-source guard]
key-files:
  created:
    - vault/programs/skill-capability/f-operations.json
    - vault/programs/skill-capability/evidence/F-representation.md
  modified:
    - tools/test_skill_representation.py
decisions:
  - "D-01 terminal stays IMPLEMENTED_AND_VERIFIED. The four reasons are rendered in F-representation.md, and AUTHORIZATION_BOUND is rejected there with its reason."
  - "Committed-blob posture (05-01): V-FO-FILE reads f-operations.json at HEAD, so an uncommitted copy is INCONCLUSIVE and an absent one is FAIL. V-FR-EVIDENCE-CURRENT is INCONCLUSIVE while a render source is dirty, FAIL when the file differs from the render, and INCONCLUSIVE when it is uncommitted."
  - "The D-LISTING plane set is (\"laptop\",) for recall-window hosts and (\"repo\", \"laptop\") for sweep members. A laptop window that records another host string is refused (fail closed) until someone edits the set on purpose."
metrics:
  duration: ~10 min
  completed: 2026-10-03
estimate:
  tokens: 80000
  tasks: 3
actuals:
  tokens: 15600
  tasks: 3
  commits: 1
plan_head_before: 46f90ca54de28821f87c3c65fa779ee2dfa1c232
---

# Phase 5 Plan 02: F operation ledger, refusal gate with drills, rendered evidence Summary

The frozen F rule now refuses executably. Each applied representation operation is an entry in a committed ledger, and it carries only references: a D-LISTING probe row named by label and session id, plus committed recall windows. The gate derives every figure from those references and refuses each kind of violation through its own clause. Gex44 applies zero operations, and 21 drills show that every clause can still fail.

## Tasks

| # | Task | Commit |
|---|---|---|
| 1 | Tracer: operations file, V-FO-OP/BEFORE/AFTER, V-FO-FILE/ENTRIES, `--operations` entrance | e4947f62 (single plan commit) |
| 2 | V-FO-PAIR/RECALL/HELPED/RECALL-HELD/DEDUP-SWEEP/PLANE, V-FO-NOISE-SOURCED, 21 drills, subprocess poles | e4947f62 |
| 3 | `render_evidence`, `--write-evidence`, V-FR-EVIDENCE-CURRENT, F-representation.md | e4947f62 |

`git show --stat e4947f62` lists exactly the three plan files. The subject matches `git log -1 --format=%s`.

## Tracer gate (Task 1, before expanding)

- `--operations /tmp/f-ops-badop.json` (op `rename`, real K4 rows): rc 1, with `FAIL V-FO-ENTRIES 1 of 1 entries refused` / `entry #0 ('rename', 'drill-skill'): V-FO-OP FAIL: op 'rename' not in [...]`.
- `--operations vault/programs/skill-capability/f-operations.json`: rc 0, `ok V-FO-ENTRIES 0 operations applied (n=0, host gex44 per f-operations.json note)`.
- Default run before the commit: `INCONCLUSIVE V-FO-FILE ... exists on disk, but not in 'HEAD'`, exit 1. This is the intended refusal (see deviation 1).

## Drill table (V-FO-DRILLS, all hold)

| drill | expected | observed |
|---|---|---|
| POSITIVE-CONTROL | (none) | passes all clauses |
| POSITIVE-CONTROL-DEDUP | (none) | passes all clauses |
| OP-OUTSIDE | V-FO-OP | killed by V-FO-OP |
| MISSING-AFTER | V-FO-AFTER | killed by V-FO-AFTER |
| WRONG-DENOM | V-FO-BEFORE | killed by V-FO-BEFORE |
| ZERO-TOKENS | V-FO-BEFORE | killed by V-FO-BEFORE |
| SESSION-MISMATCH | V-FO-AFTER | killed by V-FO-AFTER |
| AMBIGUOUS-LABEL | V-FO-BEFORE | killed by V-FO-BEFORE |
| ORDER | V-FO-PAIR | killed by V-FO-PAIR |
| MISSING-RECALL | V-FO-RECALL | killed by V-FO-RECALL |
| RECALL-NULL | V-FO-RECALL | killed by V-FO-RECALL |
| RECALL-N0 | V-FO-RECALL | killed by V-FO-RECALL |
| RECALL-WRONG-CAP | V-FO-RECALL | killed by V-FO-RECALL |
| RECALL-WRONG-HOST | V-FO-RECALL | killed by V-FO-RECALL |
| NOT-HELPED | V-FO-HELPED | killed by V-FO-HELPED |
| NOISE-ABSENT | V-FO-HELPED | killed by V-FO-HELPED |
| RECALL-DROP | V-FO-RECALL-HELD | killed by V-FO-RECALL-HELD |
| DEDUP-NOT-IN-SWEEP | V-FO-DEDUP-SWEEP | killed by V-FO-DEDUP-SWEEP |
| DEDUP-NOT-MEMBER | V-FO-DEDUP-SWEEP | killed by V-FO-DEDUP-SWEEP |
| DEDUP-GEX44-REAL | V-FO-PLANE | killed by V-FO-PLANE (`member on plane gex44: D-LISTING measures the laptop listing`) |
| K4-REAL | V-FO-HELPED | killed by V-FO-HELPED (`after startup_tokens 89844 + noise 1500 >= before 87739 (noise: vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 12)`) |

## Broken-clause run (V-FO-HELPED forced to always ok, then reverted)

```
broken: exit 1
  FAIL V-FO-DRILLS 21 drills (2 positive controls)
      FAIL V-FO-DRILL-NOT-HELPED expected ['V-FO-HELPED'], red clauses []
      FAIL V-FO-DRILL-NOISE-ABSENT expected ['V-FO-HELPED'], red clauses []
      FAIL V-FO-DRILL-K4-REAL expected ['V-FO-HELPED'], red clauses []
SR_PASS=11/14          (pre-commit; V-FO-FILE / V-FO-ENTRIES INCONCLUSIVE uncommitted)
reverted: ok V-FO-DRILLS, SR_PASS=12/14 (same two pre-commit INCONCLUSIVEs)
```

## Final gate output (after commit e4947f62)

```
$ python3 tools/test_skill_representation.py          # exit 0
  ok   V-FD-RECORDINGS ... V-FD-TAMPER-DRILLS        (9 sweep clauses, unchanged from 05-01)
  ok   V-FO-FILE vault/programs/skill-capability/f-operations.json schema skill-capability/f-operations/1, rule = frozen F rule, 0 entries (committed blob at HEAD)
  ok   V-FO-ENTRIES 0 operations applied (n=0, host gex44 per f-operations.json note)
  ok   V-FO-NOISE-SOURCED noise 1500 tokens from vault/lessons/2026-10-03-capped-listing-and-card-aperture.md line 12
  ok   V-FO-DRILLS 21 drills (2 positive controls)
  ok   V-FO-SUBPROCESS-POLES red pole (K4 rows, recall deleted) rc=1 names FAIL V-FO-ENTRIES + V-FO-RECALL; green pole (vault/programs/skill-capability/f-operations.json) rc=0
  ok   V-FR-EVIDENCE-CURRENT vault/programs/skill-capability/evidence/F-representation.md (committed) equals the render of committed inputs (line endings normalized)
SR_PASS=15/15
```

CE `_check_evidence('F', prg F-representation.md)` printed `[]`.

## Acceptance evidence

- `f-operations.json`: `skill-capability/f-operations/1 0`.
- F-representation.md: 4 `command:` lines. It contains `D-LISTING` (14 lines), `D-SESSIONS` (1), `host: gex44` (1 line plus the operations line) and `host: laptop` (2).
- `--write-evidence` run twice gave the same sha256 both times (`0fd9185e…` on the first render; the final file was re-rendered after the docstring and clause-text edits, and it is pinned by V-FR-EVIDENCE-CURRENT).
- Appending one character to the evidence gave `FAIL V-FR-EVIDENCE-CURRENT ... differs from a fresh render`, exit 1, SR_PASS=14/15. Restoring it gave exit 0, 15/15.
- Moving f-operations.json to /tmp gave `FAIL V-FO-FILE ... absent: absent is not zero operations`, exit 1, SR_PASS=11/15 (V-FO-SUBPROCESS-POLES and V-FR-EVIDENCE-CURRENT also went red). Moving it back gave exit 0, 15/15. The working tree is clean for those paths.
- `grep -c 'float(' tools/test_skill_representation.py` = 0.
- Nothing under `~/.claude` or `wiki/` was written. There were no package installs.

## Program gates (foreground, timeout 1900)

```
A rc=0 CEP_PILLAR_A=PASS
B rc=0 CEP_PILLAR_B=PASS
C rc=0 CEP_PILLAR_C=PASS
D rc=0 CEP_PILLAR_D=PASS
H rc=0 CEP_PILLAR_H=PASS
```

## Deviations from Plan

1. **[Posture, 05-01 precedent] Single commit, committed-blob reads.** The plan wants one commit holding exactly the three files, and the gate reads the operations file and the evidence as committed blobs. So before that commit, the Task 1 and Task 3 `<verify>` lines (`default run exits 0`) cannot pass: V-FO-FILE / V-FO-ENTRIES / V-FR-EVIDENCE-CURRENT read INCONCLUSIVE as uncommitted. Before the commit I verified everything else, and both entrance poles across real processes. After the commit the default run exits 0.
2. **[Plan-check info fix] 21 drills, not 20.** The RECALL-WRONG-HOST drill added by 05-PLAN-CHECK info 3 makes 19 killed drills plus 2 positive controls. The acceptance line "20 lines: 18 killed + 2 controls" predates that fix.
3. **[Rule 2] V-FO-SUBPROCESS-POLES red pole uses the real K4 rows (with recall deleted), not the fabricated positive control.** The child process reads only the committed probe rows. The fabricated control's labels are not in those rows, so V-FO-BEFORE / V-FO-AFTER would also go red and hide whether the entrance resolves real rows. With K4 rows, the red set in the child is V-FO-RECALL plus V-FO-HELPED, and stdout names `FAIL V-FO-ENTRIES` and `V-FO-RECALL` as required.
4. **[Rule 2] V-FO-FILE also checks `rule` against the frozen F rule verbatim, and checks that `note` is present.** Otherwise a ledger stating a different rule would pass.
5. **Noise and probe rows are read through committed-blob checks** (`smd.committed_bytes`) before `lfv.bounds_parse` / `lfv.load_rows`, for the same posture as deviation 1. The key_link patterns `lfv.load_rows` / `lfv.bounds_parse` are kept.
6. **V-FR-EVIDENCE-CURRENT checks dirty sources** (f-operations.json, probe rows, lessons, `F-sweep-*.json`). This follows test_skill_coverage's phase-4 posture. The ledger is excluded because only its frozen section is read, and CE pins that.
7. **The recall-window host check uses the literal `laptop`.** The committed C-window-G.json records `host: kobicraft-gex44` (the node name). If the laptop's `--measure-live` writes a hostname string instead of `laptop`, its windows are refused until LISTING_HOSTS is edited on purpose. This fails closed, and it is recorded here so 05-03 / the owner bundle can say so.
8. **Worktree branch `mission/skill-capability-run` is not in the `agent-*` namespace** that the executor's worktree allow-list expects. The orchestrator assigned this worktree and branch explicitly, and 05-01 committed on the same branch. The branch is not protected (`git.base-branch --is-protected` = false).

## Known Stubs

None. `operations: []` is not a stub: no operation is measured to help on gex44 (D-01), and V-FO-ENTRIES reports `n=0` explicitly.

## Threat Flags

None. The new subprocess runs only this file's `--operations` mode, with `sys.executable` and a 120 s timeout. That mode never spawns a subprocess or runs drills.

## Self-Check: PASSED

- FOUND vault/programs/skill-capability/f-operations.json, vault/programs/skill-capability/evidence/F-representation.md, tools/test_skill_representation.py
- FOUND commit e4947f62 (`git rev-list --count 46f90ca5..HEAD` = 1)
