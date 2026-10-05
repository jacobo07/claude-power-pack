---
phase: 02-e1-runner-with-the-stopping-contract-as-tested-code
plan: 01
requirements: [E1-RUNNER]
status: complete (uncommitted; the orchestrator commits after review)
files_created:
  - vault/programs/cognitive-economy/e1/e1_contract.py
  - vault/programs/cognitive-economy/e1/e1_runner.py
  - vault/programs/cognitive-economy/e1/test_e1_runner.py
---

# 02-01 Summary: E1 runner single counted-run path, proven end to end with a fake CLI

## What was built

- `e1_contract.py`: a pure module (no I/O, subprocess, files or clock). It holds the constants (MODEL, CAP 17M,
  PC_DELTA 15k, HARM_WINDOW 8, HARM_LOSSES 4, MAX_ATTEMPTS 2, MAX_TASKS 11, ARMS, decision and condition strings),
  `ContractError`, `run_id`, `run_valid`, `task_pass` and `run_spend`. The module docstring documents the run
  record and run_start record field contract. A missing key counts as its failing value.
- `e1_runner.py`: the I/O layer, a POSIX port of the p3_runner judgement path. It contains `load_bank`
  (spec_from_file_location as `e1_bank_validate`), `packet_rules`, `excludes` (13 absolute paths, refuses
  !=13 or non-rules paths), `child_env`, `session_cmd`, `session` (subprocess.run looked up at call time),
  `find_transcript` (by sid, else by the normalised run-tree dir with an mtime floor; ambiguity returns None),
  `metrics` (via `tis_observed._calls_in`; MEASURED / NO_CALLS / UNMEASURED), `grade` (maps TimeoutExpired to
  rc "timeout"), `tree_snapshot` / `snapshot_diff`, `append_record` (append + fsync) and `one_run`. The ordered
  steps live in `_steps`, so an early stop still reaches the verdict lines. `__main__` prints the docstring and
  exits 2.
- `test_e1_runner.py`: a stdlib harness with 17 gates. The Popen guard is installed before any import. It
  includes a FakeCli (writes REF/NAIVE plus a two-call transcript), a `good_run(**over)` helper with dotted
  metrics keys, exact-name gate selection (the two no-model gates always run; an unknown name exits 1) and red
  drills inside V-E1-VALID and V-E1-SPEND. Each drill runs a mutant that must be rejected by the same predicate.

## Verify output (`python3 vault/programs/cognitive-economy/e1/test_e1_runner.py`, exit 0)

```
PASS V-E1-NO-MODEL blocked: blocked exec of /home/kobii/.local/bin/claude
PASS V-E1-TRACER-REF bad=[] valid=True reasons=[] task_pass=True first=25003 total=50308 out=100 spend=50308 pre=E1J_PASS=0/8 control=0/4 judgement=0/4 grade=E1J_PASS=8/8 control=4/4 judgement=4/4 scrub=['rules/common/code-review.md', 'rules/python/testing.md'] tree_files=4306 err=None
PASS V-E1-TRACER-NAIVE bad=[] valid=True reasons=[] grade=E1J_PASS=4/8 control=4/4 judgement=0/4 failing=['anchor_without_previous_price', 'anchor_differs_from_previous', 'guarantee_without_policy', 'delivery_bullet_without_fact'] err=None
PASS V-E1-VALID good=(True, []) faults=[['bank file in run tree'], ['run tree listing empty'], ['precondition not red'], ['precondition not red'], ['session transcript UNMEASURED'], ['entrypoint cli'], ['model claude-opus-5-5 absent from transcript'], ['grade did not run']] ...
PASS V-E1-TASK-PASS got=[True, False, False, False]
PASS V-E1-SPEND got=(700000, 0, 0, None) mutant(unknown->0)=(700000, 0, 0, 0) rejected=True
PASS V-E1-RUN-ID J-x-B-a2=True refused=[('C', 1), ('A', 3), ('A', 0)]
PASS V-E1-ARGV A_exact=True B_exact=True C_refused=True argv0=/home/kobii/.local/bin/claude
PASS V-E1-EXCLUDES real13=True refused={'twelve': True, 'hooks': True} first=/home/kobii/.claude/rules/technical-failure-to-product-state.md
PASS V-E1-ENV stripped=True kept_PATH_HOME=True
PASS V-E1-SESSION-PARSE {'ok': ('sid-1', 0, True), 'garbage': ('', 0, True), 'timeout': ('', 'timeout', True), 'missing': ('', 'exec-error', False)}
PASS V-E1-TRANSCRIPT {... 'two': (None, 'ambiguous: 2 transcripts for run tree'), 'old': (None, 'no transcript for run tree'), 'no_dir': (None, 'no transcript for run tree')}
PASS V-E1-METRICS synthetic=NO_CALLS/0 two=MEASURED calls=2 25003/50308/100 missing=UNMEASURED
PASS V-E1-GRADE-TIMEOUT grade={'rc': 'timeout', 'summary': 'grade timeout', ...} reasons=['grade did not run']
PASS V-E1-LEAK-ABORT leak: reasons=['bank file in run tree', 'precondition not red'] spend=0 exec=0 start=0 | empty: reasons=['run tree listing empty', 'precondition not red'] exec=0 start=0 err=None/None
PASS V-E1-PRECONDITION-GREEN reasons=['precondition not red', 'session transcript absent', ...] exec=0 start=0 err=None
PASS V-E1-NO-MODEL-END blocked=1 with -p=1: [['/home/kobii/.local/bin/claude', '-p', 'guard probe']]
E1_PASS=17/17  threshold=17/17
```

Acceptance checks after the run:
- `git worktree list | grep -c e1test` printed 0.
- The `~/.claude/projects` listing and the `/home/kobii/e1-runs` listing were identical before and after the
  test (diff empty).
- `git status --porcelain -- vault/programs/cognitive-economy/e1` showed only the 3 new files.
- `validate_bank.py freeze-check` printed `FREEZE-CHECK OK d68871742a`.
- Gate selection: `test_e1_runner.py V-E1-SPEND` printed `E1_PASS=3/3` (with the two no-model gates), and
  `V-E1-SPENDX` exited 1 as an unknown gate.
- No `claude` process was started. The only blocked argv is the positive control.

## Deviations from Plan

1. **[Rule 1 - Bug] Early stops skipped the verdict lines.** Found during Task 1. A `return` inside
   `try/finally` would have skipped `valid` / `task_pass` / `spend`. Fix: the ordered steps moved into
   `_steps(...)`, and `one_run` calls it inside try/finally, then computes the verdicts. Files: e1_runner.py.
   Verified by V-E1-LEAK-ABORT and V-E1-PRECONDITION-GREEN (valid False with reasons, spend 0).
2. **[Note, corrected 2026-10-05 after the 02-01 review (F1 HIGH)] The plan says the bank's `jgrade` does not
   catch TimeoutExpired, but it does.** The frozen `jgrade` catches its own 300 s timeout and returns
   `{"rc": 124, "total": 0, "fails": ["grade timed out after 300 s"], "summary": "grade timeout"}`; it never
   raises. This note first said "no code change was needed" and that `run_valid` refuses that shape ("grade did
   not run"). That was wrong: counting it invalid would rerun a solution that never returns and could turn an
   arm-B fail into a pass on attempt 2 (a false RELOCATION_CANDIDATE). Fixed under VALIDITY READINGS (a): the
   bank's rc 124 / "grade timeout" result counts as "grade ran" (valid run, task_pass False), via
   `e1_contract.grade_timed_out`. V-E1-GRADE-TIMEOUT now drives the real returned shape (valid True,
   task_pass False) and still covers a raising jgrade (rc "timeout", invalid "grade did not run"). The bank
   was not touched.
3. **[Discretion] run_valid's wording for absent fields.** When the metrics dict is absent the reason reads
   "session transcript absent", and an absent precondition_rc counts as "precondition not red". This follows
   the plan's rule that a missing key fails.
4. **[Discretion] ModelCallBlocked subclasses Exception, not OSError.** With OSError, `session()` would record a
   blocked call as an ordinary "exec-error" and hide it.

**Total deviations:** 1 auto-fixed bug, 1 plan-premise note, 2 discretion choices. **Impact:** none on scope.
Bank bytes are unchanged (freeze-check OK).
