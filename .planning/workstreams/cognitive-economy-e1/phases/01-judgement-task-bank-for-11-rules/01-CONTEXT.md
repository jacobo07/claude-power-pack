# Phase 1: Judgement task bank for 11 rules - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), decisions taken from the binding contract

<domain>
## Phase Boundary

One judgement task for each of the 11 rules ADDENDUM-E1 names (all 13 packet rules except
technical-failure-to-product-state and scoped-side-effect-authority), validated with no model calls and frozen
by one commit. Contract of record: `vault/programs/cognitive-economy/e1/ADDENDUM-E1.md` (immutable for this run).

</domain>

<decisions>
## Implementation Decisions (locked by ADDENDUM-E1 and the ROADMAP operating constraints)

### Location and shape
- Bank lives at `vault/programs/cognitive-economy/e1/bank/` (own path). One file per rule:
  `task_<prefix>_<slug>.py`, plus a copied+extended driver `_e1_common.py`, plus `BASE` and `index.json`.
- Shape = R2's `judgement-r2` bank (`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/`,
  read-only: copy, never edit). Each task file defines `MODULE` (path the stub is written to inside the run
  tree, e.g. `e1j/<name>.py`), `STUB` (module docstring naming the caller and what the result drives, every body
  `...`), `NAIVE`, `REF`, `CHECKS`. The prompt is R2's `JPROMPT` ("...Implement them...").
- Every check is tagged `control` (the ordinary answer must be right) or `judgement` (the decision the rule
  governs). Validation is STRICTER than R2: the naive solution must fail AT LEAST ONE judgement check and
  ZERO control checks; the stub fails; the reference passes all. `_e1_common.py selftest` enforces that.
- Judgement checks accept a loud refusal (an exception) or the safe value, as in R1/R2.
- `BASE` = `78ba9e74` (a commit with no E1 bank). The runner must refuse a BASE whose tree contains the bank.
- `index.json`: per task id -> rule file (relative to `~/.claude/`), rule bytes, packet sha256, MODULE, the
  judgement check names and the decision each tests. Ordered by rule bytes descending (contract order).

### The 11 rules, in contract order (bytes from the packet)
1. generated-content-needs-an-evidence-gate (6284)
2. effect-authority-across-transports (6106)
3. human-facing-external-effects (5520)
4. documented-capability-must-be-executable (5045)
5. validation-planes-do-not-transfer (3656)
6. capability-preserving-compaction (3335)
7. state-lifetime-and-incarnation (3137)
8. post-effect-resource-truth (3126)
9. durable-exit-transaction (2830)
10. python/testing (2516)
11. common/code-review (1772)

### Task design rule
- A judgement check must test the decision its rule governs, in a function whose docstring states the caller
  and the consequence but does NOT state the safe answer. (R2 limit: a docstring that names the hazard lets a
  model pass from the docstring alone; keep the hazard implicit in the situation, as SSEA-2 does.)
- No task may need network, a model, or anything outside the stdlib. Pure functions with injected callables.
- For python/testing and common/code-review, the "decision" is still testable code: e.g. a function that
  judges whether a test run counts as a pass (a test with zero asserts / zero collected is not a pass), and a
  function that decides whether a review finding is reportable / a verdict (BLOCK only with snippet +
  scenario + why-guards-fail; zero findings -> APPROVE).

### Validation and freeze
- A validate command (no model calls) runs every selftest and, in a fresh detached worktree at BASE, writes the
  stub, grades it (must be red), and lists the tree to prove no bank file is reachable. Log committed beside the
  bank as `bank/VALIDATE.log`.
- The freeze commit adds the bank + log; its hash goes into `vault/programs/cognitive-economy/e1/BANK_FROZEN_AT`
  (a follow-up commit). Any task file edited after the freeze voids its runs.

### Claude's Discretion
- The concrete scenario for each rule, check names, and which naive implementation is "ordinary".

</decisions>

<code_context>
## Existing Code Insights
- `p3_runner.py` (validate-j, jgrade, jprepare, fresh_tree) is Windows-pathed; the POSIX port is Phase 2. Phase 1
  may contain a minimal POSIX validate script inside the bank dir or defer the in-worktree validation to the
  runner's `validate` subcommand -- but the committed VALIDATE.log must exist at freeze.
- Rule bodies to design against: `/home/kobii/.claude/rules/*.md` (read-only) and their inline copies.

</code_context>

<specifics>
## Specific Ideas
- Host GEX44, python3 3.12. Never write under `~/.claude`. Commit by explicit pathspec; verify subject after.

</specifics>

<deferred>
## Deferred Ideas
None.
</deferred>
