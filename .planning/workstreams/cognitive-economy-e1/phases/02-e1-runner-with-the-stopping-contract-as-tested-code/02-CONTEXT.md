# Phase 2: E1 runner with the stopping contract as tested code - Context

**Gathered:** 2026-10-05
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss), decisions taken from the binding contract

<domain>
## Phase Boundary

`vault/programs/cognitive-economy/e1/e1_runner.py`: a POSIX port of the P3 runner's judgement path
(`.planning/workstreams/cognitive-resource-os/phases/06-p3-ablation/p3_runner.py`: fresh_tree, jprepare, jgrade,
session, metrics, judge) driving the frozen Phase 1 bank, with ADDENDUM-E1's stopping contract as code, and a
no-model test that drives every stop branch red and green.

</domain>

<decisions>
## Implementation Decisions (locked by ADDENDUM-E1 + ROADMAP)

### Host constants
- CLAUDE = `/home/kobii/.local/bin/claude` (2.1.289). Refuse `/usr/local/bin/claude` or any other path; record
  `claude --version` in every record. MODEL = `claude-opus-5-5`. GIT = `git` (POSIX). PY = `sys.executable`.
- RUNS dir outside the repo: `/home/kobii/e1-runs/<run_id>` (fresh detached worktree at the BASE in
  `bank/BASE`; refuse a BASE whose tree contains the bank).
- Arm B = `--settings {"claudeMdExcludes": [13 absolute paths under /home/kobii/.claude/rules]}` -- all 13 packet
  rules, including technical-failure and scoped-side-effect (group exclusion, as gate 1 measured).
- Session command as P3: `-p <JPROMPT>`, `--output-format json`, `--max-turns 40`, `--permission-mode acceptEdits`,
  `--allowedTools Read,Edit,Write,Grep,Glob,Bash`, timeout 1500 s, env stripped of CLAUDECODE*/CLAUDE_CODE_*.
- Metrics from the transcript via `tools/tis_observed._calls_in` (read-only import): first_call_context,
  total_context, output_tokens, calls, entrypoint (must be `sdk-cli`), models.

### Stopping contract as code (each clause a pure function, unit tested)
1. Order: tasks in descending rule bytes (from `bank/index.json`); arm order alternates task by task
   (task 0: A then B, task 1: B then A, ...).
2. One pair per task, no replicates; max 11 pairs = 22 counted runs.
3. Validity: precondition red AND session ran (transcript MEASURED, entrypoint sdk-cli) AND grade ran (a
   `P3J_PASS=`-style line printed). An invalid run is rerun once; a second invalid run -> that task is
   "no information" (the other arm of the pair is not needed further).
4. Decision per rule, final when its pair is valid: A pass + B pass -> RELOCATION_CANDIDATE; A pass + B fail ->
   STAYS; A fail -> NO_INFORMATION (stays); B pass where A fails -> reported, never used. Tokens never tie-break.
5. Harm stop: B loses (A pass, B fail) in >= 4 of the first 8 VALID pairs -> STOP `HARM_STOP`, all 13 stay.
6. Spend stop: summed counted `total_context` of all counted runs (valid and invalid alike: they were spent)
   reaches 17,000,000 -> STOP `SPEND_STOP`; checked before starting every run (a run that would start at or above
   the cap does not start). Undecided rules stay resident.
7. Positive control on the FIRST valid pair: B first_call_context must be <= A first_call_context - 15,000, else
   STOP `POSITIVE_CONTROL_STOP`.
8. Pin check before the first counted run: the 13 LF sha256 pins (from the packet
   `vault/programs/cognitive-economy/post-reset-packet.json`) -- any mismatch refuses to start.
9. Bank check: every bank task file's blob equals its blob at the commit in `e1/BANK_FROZEN_AT`; else refuse.
- Every terminal state writes a final record naming the stop condition (`ALL_DECIDED`, `HARM_STOP`,
  `SPEND_STOP`, `POSITIVE_CONTROL_STOP`, `NO_INFORMATION` per task, ...).
- Results: `vault/programs/cognitive-economy/e1/results.jsonl` (append-only); resumable (skip pairs already
  decided). Commit after every pair by explicit pathspec (the runner itself may commit, or the Phase 3 driver --
  either way one commit per pair; verify `git log -1 --format=%s`).

### Test
- `vault/programs/cognitive-economy/e1/test_e1_runner.py`: fake session + fake grader injected (no model call,
  no git worktree needed for contract tests); drives each stop branch both ways (fires / does not fire), the
  rerun-once rule, alternation, order, positive control, spend cap boundary (just below / at), pin mismatch
  refusal, bank-drift refusal. V-E1-* gate names, `E1_PASS=n/m` summary line, exit 0 only when all pass.

### Claude's Discretion
- Module structure, whether `run` and `contract` are split into two files.

</decisions>

<deferred>
## Deferred Ideas
None.
</deferred>
