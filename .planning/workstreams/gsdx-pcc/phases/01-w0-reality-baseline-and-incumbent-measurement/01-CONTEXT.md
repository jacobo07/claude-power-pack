# Phase 1: W0 Reality, baseline and incumbent measurement - Context

**Gathered:** 2026-10-07
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Every API the spec names is premise-verified, R01 is fixed red-first, and the incumbent full path is
measured so every later speedup has an honest baseline. (ROADMAP Phase 1; DENOMINATOR row R01.)

</domain>

<decisions>
## Implementation Decisions

### Locked by the spec / roadmap (not discretionary)
- R01 root cause is already characterised (spec Reality 14): `providers/gate.py:72` `subprocess.run(cmd)` passes
  no std handles; on Windows the grandchild's output never reaches the log, so every gate verdict carries
  `observed: ''`. Fix must land RED-first (drive the failing gate_provider case red, then green), be mutation-drilled
  through `tools/mutation_drill.py` (isolated copy + control, never `mutation_probe` live mode), and get a UKDL
  T-entry in `vault/knowledge_base/ukdl-universal.md`.
- Baseline suite counts at fbca24fc (spec Reality 13): reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14,
  epoch 19/19, chaos 15/15, mutation_safety 8/8, gate_provider 17/18 RED. Done = gate_provider 18/18.
- Premise verification (HR-PREMISE-001) covers: evidence_bundle, mutation_drill, change_impact, parallel_mesh pure
  fns (`decide`, `CollisionDetector`), tower (baselines/families/select/ratchet/donegate) + `tools/family_baseline.py`.
  Record real signatures with file:line.
- Incumbent measurement: per-suite wall time of every `tools/test_gsd_x_goal_*.py`, judge replay time, one real
  goal's sweep->judge timeline. Anything unmeasurable is recorded UNKNOWN, never estimated.
- Phase output: `EVIDENCE.md` in this phase dir (commands, exit codes, observed output, Production Reality verdict,
  denominator rows moved, UKDL entries written). DENOMINATOR R01 row updated with evidence.
- Operating constraints in ROADMAP.md apply verbatim (worktree-only writes, PowerShell for git/python, absolute git
  path, hermetic tests, one msgfile per commit, never push, liveness exit 0 at phase end).

### Claude's Discretion
How the incumbent timeline is captured (existing GoalLog vs a hermetic fixture goal), as long as the source is named.

</decisions>

<code_context>
## Existing Code Insights

Spec of record: `vault/specs/gsdx-proof-conserving-convergence.md` (Reality Scan items 1-17 carry file:line anchors).
Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

Scratch reproduction of R01 (spec Reality 14): 0 B captured with bare `subprocess.run(cmd)`; 11 B with explicit
`stdout=sys.stdout, stderr=sys.stderr`.

</specifics>

<deferred>
## Deferred Ideas

None — everything else belongs to phases 2-10.

</deferred>
