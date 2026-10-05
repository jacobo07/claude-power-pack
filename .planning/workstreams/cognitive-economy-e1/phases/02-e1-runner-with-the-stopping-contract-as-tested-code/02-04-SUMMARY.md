---
phase: 02-e1-runner-with-the-stopping-contract-as-tested-code
plan: 04
requirements: [E1-RUNNER]
status: complete (uncommitted; the orchestrator commits after review)
files_modified:
  - vault/programs/cognitive-economy/e1/e1_runner.py
  - vault/programs/cognitive-economy/e1/test_e1_runner.py
---

# 02-04 Summary: the durable campaign loop, commit per pair, `plan` and `run`

## What was built

- `e1_runner.py` additions:
  - `drive(order, *, results, run_fn, check_fn, reconcile_fn, commit_fn=None, max_pairs=None, r2_rules, out)`.
    This is the only campaign loop. Each iteration reads results.jsonl and calls `e1_contract.replay`. It
    appends a `pair` record (plus `at`) for every newly terminal task and commits it. Then it acts on
    `next_action`:
    - HALTED: returns and appends nothing.
    - RECONCILE: appends `reconcile_fn(start)` and continues.
    - STOP: appends the `stop` record, commits it, and returns `EXIT[cond]`.
    - RUN: first applies the `max_pairs` pause (exit 4, no record). Then `check_fn()` runs before every run. A
      problem appends a `refusal` record, commits it, and exits 1. Otherwise drive calls `run_fn` and appends
      the run record.

    A ContractError from read or replay gives `E1-RUN REFUSED` (exit 1) and appends nothing. A commit_fn
    exception gives `COMMIT_FAILED` (exit 1); the record stays on disk and is not appended again on resume. The
    loop is bounded at `4*11*2+10` iterations, and going past the bound raises ContractError.
  - `reconcile(bank, start, *, projects)`: builds the run record for an orphan `run_start`:
    - `error` is "runner interrupted: run_start without a run record".
    - Metrics come from the run tree without a session id.
    - bank_access is recorded as evidence.
    - `drop_tree` is called only when the wt exists. Its exception is recorded as `drop_error`, and
      `worktree_removed` is False.
    - valid, task_pass and spend come from e1_contract.
  - `commit_results(repo, paths, subject, body="")`:
    - Runs `git add -- paths`, then `git commit -q -F - -- paths` with the message on stdin.
    - The message is the subject, an optional body, and `COAUTHOR`.
    - It checks `git log -1 --format=%s` and raises RuntimeError on a mismatch, leaving the commit as is.
    - Returns the HEAD hash.
    - No push, amend, reset, force or `--no-verify`.
  - `git(..., input=)`.
  - `EXIT`, `LOOP_BOUND`, `COAUTHOR`, `INTERRUPTED`.
  - `cmd_plan`:
    - Prints one TASK line per task, then SPENT, then NEXT.
    - Writes nothing.
    - A missing bank or any exception prints `PLAN REFUSED` (exit 1).
  - `cmd_run`: has no `--bank`. It runs preflight first, and any REFUSED prints the CHECK lines and
    `E1-RUN REFUSED n` (exit 1). Otherwise it binds these closures:
    - `run_fn`: one_run, with arm A getting `[]` excludes and arm B getting all 13.
    - `check_fn`: per_run_checks.
    - `reconcile_fn`.
    - `commit_fn`: commit_results on results.jsonl, or None with `--no-commit`.
  - `main` dispatches plan, preflight and run. Usage is exit 2. The module docstring lists the three usage
    lines and the exit codes.
- `test_e1_runner.py`: 15 new gates, all placed before V-E1-NO-MODEL-END:
  - 10 loop gates: `V-E1-LOOP-*`.
  - 5 commit and CLI gates: COMMIT, COMMIT-SUBJECTS, CLI-PLAN, CLI-RUN-REFUSES and CLI-USAGE.
  - A `Loop` recorder helper that records run_fn calls, check_fn calls, the check/run event order, commit
    subjects and spent before each run.

## Verify output

Task 1 verify (`... V-E1-LOOP-ALL-DECIDED ... V-E1-LOOP-COMMIT-FAIL`) ended `E1_PASS=12/12`, exit 0. Evidence:
```
PASS V-E1-LOOP-ALL-DECIDED rc=(0,'ALL_DECIDED') kinds={run:22, pair:11, stop:1} last=stop/ALL_DECIDED reloc=11 r2=[R2_CARRIED x2] commits=12 checks=22 check_before_every_run=True
PASS V-E1-LOOP-HARM all_loss=(3,'HARM_STOP')/8r/4p stays=13/13 control_3_losses=(0,'ALL_DECIDED')/22r losses_in_window=3
PASS V-E1-LOOP-SPEND million=SPEND_STOP/17r 17th_starts_at=(16000000, 1000000) spent=17000000 over=0 | 16x1M+999999=SPEND_STOP/17r spent=16999999 over=0 max_seen=1000000 18th_withheld | reactive-gate-mutant=18r/over=999998
PASS V-E1-LOOP-POSCTL delta14999=POSITIVE_CONTROL_STOP/2r used=False pc_ok=False | delta15000=ALL_DECIDED/22r used=True pc_ok=True
PASS V-E1-LOOP-NOINFO pair0=NO_INFORMATION reason='arm A invalid twice' t0_B_called=False calls=[(gceg,A,1),(gceg,A,2),(eaat,B,1)]
PASS V-E1-LOOP-RESUME first=(4,'PAUSED') pair=1 stop=0 | resume first_call=[(eaat,B,1)] t0_rerun=False end=ALL_DECIDED prefix=True
PASS V-E1-LOOP-HALTED rc=(3,'HARM_STOP') unchanged=True
PASS V-E1-LOOP-REFUSAL rc=(1,'REFUSED') runs=2 refusal before J-eaat_session_launch-B-a1, committed | resume first=(eaat,B,1) end=ALL_DECIDED
PASS V-E1-LOOP-RECONCILE with_transcript: valid=False spend=50308 dropped=1 next=(gceg,A,2) end=ALL_DECIDED | no_transcript: spend=None end=(3,'SPEND_UNMEASURED') runs=0
PASS V-E1-LOOP-COMMIT-FAIL rc=(1,'COMMIT_FAILED') last=pair/gceg | resume end=ALL_DECIDED t0_pair_records=1 first_commit='data(e1): pair 2 J-eaat_session_launch RELOCATION_CANDIDATE'
```
Full suite: exit 0, `E1_PASS=64/64  threshold=64/64`. The Task 2 gates:
```
PASS V-E1-COMMIT files=['results.jsonl'] still_staged=['other.txt'] subject_ok=True coauthor_ok=True | hook-rewrite: raised=True left_as_is='data(e1): rewritten'
PASS V-E1-COMMIT-SUBJECTS all_pass=12/12 all_loss=5/5 refusal=2/2 forbidden=[]
PASS V-E1-CLI-PLAN rc=0 tasks=11 first=[J-gceg_product_page, arms=A,B] last=J-cr_review_verdict next='NEXT RUN J-gceg_product_page A 1' | empty_bank=1 PLAN REFUSED | one_pair next='NEXT RUN J-eaat_session_launch B 1'
PASS V-E1-CLI-RUN-REFUSES rc=1 last='E1-RUN REFUSED 2' results_exists=False new_blocked=[]
PASS V-E1-CLI-USAGE '(none)'=2 'bogus'=2 'run --max-pairs x'=2 'plan --bogus'=2 'run --max-pairs 0'=2 usage_names_all=True checks_reached=[]
PASS V-E1-NO-MODEL-END blocked=1 with -p=0 version-probes=1 other=[]
```
The plan's Task 2 `<verify>` chain exited 0, and the real-bank `plan` ends `NEXT RUN J-gceg_product_page A 1` with
the 11 ids in contract order. `preflight` printed nine OK CHECK lines and `PREFLIGHT OK` (pins 13/13, cli
2.1.289, base 78ba9e7414, 17 files match d68871742a). `validate_bank.py freeze-check` printed `FREEZE-CHECK OK
d68871742a`. `ls results.jsonl` failed (no such file). `git worktree list` showed no e1-runs path, and
/home/kobii/e1-runs holds 0 entries. `e1_runner.py` with no argument exits 2.

## Red drills (throwaway in-process source mutations; nothing shipped, nothing written)

Each mutation turned the named gates red:
- drive with no per-run check: LOOP-ALL-DECIDED and LOOP-REFUSAL.
- No pair records: LOOP-ALL-DECIDED and LOOP-RESUME.
- commit_results without the subject check: COMMIT.
- commit without pathspec (other.txt swept in): COMMIT.
- max_pairs ignored: LOOP-RESUME.

The predictive spend gate's reactive mutant is shipped inside V-E1-LOOP-SPEND (18 runs, 999,998 over the cap).

## Deviations from Plan

1. **[Count] 64/64, not 60/60.** 02-03 ended at 49, while the plan assumed 45. 49 + 10 + 5 = 64.
2. **[Discretion] After a stop record, drive appends no pair records.** The plan's per-iteration pair step comes
   before `next_action`. On a stopped file it is skipped, so HALTED leaves the file byte-identical, which is what
   "after a stop, never another write" requires.
3. **[Fix needed by the plan's own text] cmd_run passes `excl=[]` for arm A.** The plan says
   `one_run(..., excl=excl)`. But `check_arm_excludes` (02-01 review reading (c)) refuses arm A with 13
   excludes, so every arm-A run would have raised before launch.
4. **[Additions to gates, all stricter]**
   - V-E1-LOOP-ALL-DECIDED also asserts the event order is exactly check, run x 22, so per_run_checks runs
     before every run (orchestrator requirement).
   - V-E1-COMMIT also drives the subject-mismatch red branch: a commit-msg hook rewrites the subject,
     commit_results raises naming both, and the commit is left as is.
   - V-E1-LOOP-SPEND carries a reactive-gate red drill.
   - V-E1-CLI-USAGE adds `--max-pairs 0` and swaps in a preflight/drive that must not be reached, so a usage bug
     can never fall through into a real run.
   - V-E1-CLI-RUN-REFUSES likewise replaces drive with a must-not-be-reached function. The refusal comes from
     the real preflight (bank_drift and freeze_check REFUSED on the absent BANK_FROZEN_AT).
5. **[Discretion] cmd_plan refuses on any exception or SystemExit, not only ContractError or SystemExit.**
   Example: a packet read error prints `PLAN REFUSED <ExcType>: <msg>` instead of a traceback.
6. **[Discretion] reconcile records a drop_tree exception as `drop_error`** and keeps the fixed `error` string,
   because the record must name the interruption.

Not touched: the bank, BANK_FROZEN_AT, the packet, STATE/ROADMAP, vault/progress.md and ~/.claude (scratch
only, under /home/kobii/.claude/jobs/68d51544/tmp/). No `git add`/`commit` in the real repo. commit_results ran
only in temp git repos. `run` was never invoked from a shell. The only real claude exec was `--version` via
preflight. `git status` shows `.planning/.../STATE.md` as modified, but this executor did not write it.

## Review fixes (02-04 review)

Review: pp-code-reviewer over the 02-04 campaign loop, verdict WARNING (F1 HIGH, F2 MEDIUM, F3 LOW). All three
fixed in `e1_runner.py` (plus the run_start field list in the `e1_contract.py` docstring), each with a V-E1 gate
that was driven red by a temporary break and restored byte-identically (sha256 checked).

- **F1 HIGH: a killed runner left the claude child spending.** `session()` now launches through `_launch`:
  `subprocess.Popen(start_new_session=True)` with a preexec that sets `prctl(PR_SET_PDEATHSIG, SIGKILL)` through
  ctypes and exits at once if the runner already died before the prctl. The 1500 s timeout is unchanged and kills
  the whole process group, as does any exception raised while waiting. The run_start record is now written by an
  `on_spawn(pid, start)` callback: after the process exists and before the wait, with `session_pid` and
  `session_pid_start` (`/proc/<pid>/stat` starttime, so a reused pid does not match). `reconcile()` raises
  `SessionAlive("session still alive pid N")` while that pid with that start time is alive, or while the pid is
  listed and its recorded start time is unknown. It measures nothing and drops nothing. `drive` turns any reconcile
  exception into REFUSED (exit 1) and appends nothing. An injected `exec_fn` and an exec error record `(None, None)`,
  which keeps the existing [run_start, run] shape. A crash between the spawn and the run_start fsync leaves no
  record; the child is SIGKILLed by the pdeathsig within that window, and the next start re-creates the tree.
  Gates: V-E1-SESSION-PDEATHSIG (a parent process running the real `session()` with a fake CLI is SIGKILLed: the
  pid was in run_start while the child ran, and the child is dead within 5 s), V-E1-SESSION-TIMEOUT-GROUP (timeout
  2 s: the child and its grandchild are both dead, rc "timeout"), V-E1-RUNSTART-PID (the production `one_run` path
  with no exec_fn: the fake child reads results.jsonl and finds its own pid in run_start), V-E1-RECONCILE-ALIVE
  (live pid and unknown start time are REFUSED with no record, drop or run; a reused pid and a dead pid reconcile
  spend=50308 as before).
- **F2 MEDIUM: a lost stop commit was never retried.** `drive(..., dirty_fn=)`: at the start and on HALTED, a
  dirty results.jsonl is committed (`data(e1): recommit results left uncommitted` /
  `data(e1): stop <cond> (recommit)`). If that commit fails, or the status cannot be read, the drive ends
  COMMIT_FAILED. `cmd_run` wires `results_dirty(REPO, results)` (`git status --porcelain -- results.jsonl`). Gate:
  V-E1-LOOP-STOP-RECOMMIT runs in temp git repos with the real `commit_results`. It covers a crash after the stop
  append and a failing stop commit: on resume the stop record is committed and the status is clean. A third drive
  makes no commit. It also checks the HALTED branch on its own, a commit failure, and an unreadable status.
- **F3 LOW: append onto a torn tail.** `torn_tail(path)`. `append_record` raises ContractError "torn tail" when
  the file is non-empty and does not end in `\n`, and writes nothing. `drive` checks it before every iteration, so
  it refuses before any run. Gate: V-E1-TORN-TAIL (refused with the bytes unchanged, drive REFUSED with no run;
  absent, empty and newline-terminated files still append).

Drills (`drills_0204.py` in the job scratch dir). Each break made its gate FAIL and was restored byte-identically
(e1_runner.py sha256 f443e8fd...):
D1 no prctl -> PDEATHSIG red; D2 `proc.kill()` instead of `killpg` -> TIMEOUT-GROUP red; D3 on_spawn after the
wait -> RUNSTART-PID and PDEATHSIG red; D4 reconcile ignores the pid -> RECONCILE-ALIVE red; D5 no recommit ->
LOOP-STOP-RECOMMIT red; D6 torn_tail always None -> TORN-TAIL red.

The review's drivers, rerun against the live code (`*_v2.py`):
d1: runner SIGKILLed after 2 calls, reconciled spend 200000 == the true transcript spend 200000, and the fake
session never finished. A session still alive is REFUSED (records stay [run_start], no run), and after it exits
the reconciled spend is 800000 == true. d2: P1-P6 all resume to ALL_DECIDED with no duplicate run, and the stop is
committed with a clean status (P5 and P6 previously ended at "pair 11"). d3: (a) and (b) both REFUSED with no run.

Suite: `E1_PASS=77/77` (71 + 6). Real host: `preflight` PREFLIGHT OK, exit 0; `plan` ends
`NEXT RUN J-gceg_product_page A 1`; `freeze-check` FREEZE-CHECK OK d68871742a. No results.jsonl and no git state
change in the real repo.
