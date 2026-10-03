---
phase: 04-cognitive-cost-regression-gate
plan: 03
subsystem: floor-regression-gate
tags: [pillar-K, IC-K, measurement-sources, probe, real-gex44-floor, plane-gex44-reference, mutation-drill, window-pin]
requires: ["04-01", "04-02"]
provides:
  - "tools/floor_regression_gate.py: newest_transcript, session_transcript, resolve_source, resolve_probe_exe, probe_transcript, PROBE_PROMPT, first_call_tokens, load_lfp, probe_view, stamp_source, precheck_write, source_line, probe_line; flags --project-dir, --session, --probe, --cwd; SOURCE and PROBE output lines; provenance.source, provenance.probe, probe_view (in --json provenance), probe_error; env CPP_CLAUDE_EXE, CPP_FLOOR_PROBE_RESULTS, CPP_FLOOR_GATE_TEST, CPP_FLOOR_GATE_TEST_ROOT"
  - "tools/test_floor_regression_gate.py: 19 new V-FLOOR-* gates (sources, probe, real GEX44), stub executables, test fence, --real-session, drill M12-M13"
  - "vault/programs/incremental-cognition/floor/reference-gex44.json: plane gex44 reference written from the mission worker session 34f03871 (test and smoke input only)"
affects: ["04-04"]
tech-stack:
  added: []
  patterns: ["the owner's probe module is imported and its globals rebound inside try/finally, so listing_floor_probe.py keeps zero diff", "a test fence that only restricts: set, no executable outside the scratch root can ever be spawned; unset, production is unchanged", "every probe failure is a typed UNMEASURABLE (class name only), never a traceback and never exit 0", "a real-transcript gate SKIPs (never PASSes) when its transcript is absent, and is paired with a control that can go red"]
key-files:
  created: [vault/programs/incremental-cognition/floor/reference-gex44.json]
  modified: [tools/floor_regression_gate.py, tools/test_floor_regression_gate.py]
decisions:
  - "R2-W1 item 3 APPLIED: the committed reference-gex44.json carries provenance.window_sha256 dc6d23b90cac05e665ca0eb7b9b4c57ce440a4e0bb8f9f4e8c45d91c5885fd63 and window_rows 34 (computed by window_digest, 04-01); gate V-FLOOR-REAL-REFERENCE-PINNED re-reads transcript 34f03871 from disk, recomputes both with the same function and compares them to the committed reference; it prints SKIP (UNMEASURABLE: not on this host), never PASS, when the transcript is absent, and fails when the reference is missing or its pin does not match"
  - "reference_exists / refused_path are now checked BEFORE a source is resolved (precheck_write), so a doomed --write-reference --probe never spends a session"
  - "JSON stays at 12 keys: source and probe_view travel inside provenance"
  - "the process-wide test fence is set at test-module import; cli_env re-forces it after the caller's env, so no caller can switch it off"
status: complete
commits: 3
plan_head_before: 15f70abea8745d4e7113530dc6422a93af9bf344
actuals:
  tokens: 13400
  tasks: 3
  commits: 3
metrics:
  completed: 2026-10-04
requirements: [IC-K]
requirements-completed: []
---

# Phase 4 Plan 03: measurement sources, `--probe`, and the real GEX44 floor (pillar K) Summary

The gate now measures from four mutually exclusive sources (`--transcript`, `--project-dir`, `--session`, `--probe`), and on the real GEX44 floor it is green on today's interactive session, red on the appended mission prompt and red on a seeded +1,024-char universal rise in a real transcript, naming layer and scope each time. `--probe` reuses the owner's `listing_floor_probe.main` unchanged and is proven only through stub executables (no real `claude` session was started by any test or command). **IC-K is addressed, not satisfied** (the frozen-rule reference is the laptop one, plan 04-04); ledger `state.K` still prints `{}` and IC-K is not ticked.

**Code commits:** `f065ac8e` (Task 1 tracer: `--project-dir`, `--session`), `17228d2f` (Task 2: `--probe`, fence, probe_view, M12-M13), `09bb9142` (Task 3: real GEX44 gates, plane-gex44 reference). Task 1 and 2 commits touch only the two tool files; Task 3 touches `tools/test_floor_regression_gate.py` and the new reference.

## Observed results

- `python3 tools/test_floor_regression_gate.py` -> `FLOOR_PASS=59/59  threshold=59/59  skipped=0  inconclusive=0`, exit 0, 3.6 s (`timeout 60` exits 0). On GEX44 none of the real gates SKIP: `PASS V-FLOOR-REAL-GEX44`, `PASS V-FLOOR-REAL-A7-NO-CALL`, `PASS V-FLOOR-REAL-APPENDED-PROMPT`, `PASS V-FLOOR-SEEDED-REAL`, `PASS V-FLOOR-REF-GEX44-GREEN`, `PASS V-FLOOR-REAL-REFERENCE-PINNED`; all nine probe gates PASS (`V-FLOOR-PROBE-STUB`, `-BAD-EXIT`, `-NOT-EXECUTABLE`, `-TIMEOUT`, `-NO-EXE`, `-FENCE`, `-REFUSALS`, `-VIEW`, `V-FLOOR-NO-REAL-SESSION`).
- `python3 tools/test_floor_regression_gate.py --drill` -> `PASS DRILL-CONTROL unmutated run: 49/49 gates green (skipped 0)`, 13 `KILLED` lines (M1-M11 as before; M12 `newest_transcript` returns the oldest, killed by V-FLOOR-PROJECT-DIR-NEWEST; M13 `first_call_tokens` accepts a `<synthetic>` row, killed by V-FLOOR-NO-MODEL-CALL), `PASS DRILL-CLEAN-AFTER-MUTANTS 49/49`, `PASS DRILL-RESTORE gate file sha256 775574882200de2e before == after`, `DRILL killed=13/13`.
- `python3 tools/test_floor_regression_gate.py --real-session 607795c4-aa30-4fb8-886c-5b1e24a7a991` -> `PASS V-FLOOR-SEEDED-REAL ... FLOOR_PASS=59/59` (the laptop's seeded positive control path works through `lfp.transcript`).
- `python3 tools/test_incremental_cognition_program.py --selftest` -> `CEP_SELFTEST=PASS`, `ICP_SELFTEST=PASS`; `vault/programs/incremental-cognition/ledger.json` `state.K` is `{}`.
- Owner file untouched: `git diff --stat -- wiki/tools/listing_floor_probe.py wiki/tools/listing_floor_probe.results.jsonl` prints nothing; `git log -1 --format=%h -- wiki/tools/listing_floor_probe.py` prints `4d1cfb83`; the tracked results file sha256 is pinned unchanged inside V-FLOOR-PROBE-STUB.
- `grep -c 'PROBE_PROMPT = "Reply with the single word OK."' tools/floor_regression_gate.py` -> `1`; `grep -c 'subprocess.SubprocessError' tools/floor_regression_gate.py` -> `2`.

## RED outputs (recorded before each build)

- Task 1 (`FLOOR_PASS=40/44`): `FAIL V-FLOOR-SOURCES-E2E JSONDecodeError: Expecting value: line 1 column 1 (char 0)` (argparse rejected the new flags, exit 2), `FAIL V-FLOOR-PROJECT-DIR-NEWEST AttributeError: module 'floor_regression_gate' has no attribute 'newest_transcript'`, `FAIL V-FLOOR-SESSION-UNKNOWN rc=2 last=''`, `FAIL V-FLOOR-SESSION-ID-REFUSED '../x': rc=2 last=''; 'a/b': rc=2 last=''; ...` (all eight ids, exit 2 from argparse with no reason line).
- Task 2 (`FLOOR_PASS=46/53`): the seven red gates all stopped at argparse: `FAIL V-FLOOR-PROBE-STUB write rc=2 ... error: one of the arguments --transcript --project-dir --session is required`, `-PROBE-BAD-EXIT rc=2 last=''`, `-PROBE-NOT-EXECUTABLE`, `-PROBE-TIMEOUT timeout: rc=2 last=''; ... probe_error class not named`, `-PROBE-NO-EXE unset exe: rc=2 last=''`, `-PROBE-FENCE AttributeError: ... no attribute 'resolve_probe_exe'`, `-PROBE-REFUSALS missing cwd: rc=2 last=''`. V-FLOOR-PROBE-VIEW and V-FLOOR-NO-REAL-SESSION passed before the build (probe_view and first_call_tokens were added with Task 1's measure edit; the no-real-session guard is test-side).
- Task 3 (`FLOOR_PASS=57/59`): `FAIL V-FLOOR-REF-GEX44-GREEN the committed reference is missing: .../reference-gex44.json` and `FAIL V-FLOOR-REAL-REFERENCE-PINNED the committed reference is missing`. The four other real gates (REAL-GEX44, REAL-A7-NO-CALL, REAL-APPENDED-PROMPT, SEEDED-REAL) were green on first run: 04-01/04-02 already carry the classification, so the numbers match the planning measurements exactly (not a defect: these gates need no new gate code; they are what the plan asks to pin on real data). The pinned gate's red branch was also driven by hand against a scratch reference with a zeroed digest: `False 'window_sha256 re-read dc6d23b90cac != committed 000000000000; window_rows re-read 34 != committed 33'`.

## Real GEX44 smoke (foreground, read only)

Commands run from the worktree, transcripts REAL_A = interactive `607795c4`, REAL_B = mission worker `34f03871`, with `/tmp/ic-p4-03-*` outputs:

1. `--write-reference vault/programs/incremental-cognition/floor/reference-gex44.json --transcript <REAL_B>` -> exit 0:
```
SOURCE transcript name=34f03871-4d33-4b7d-a52e-ec674b20a223.jsonl
FLOOR reference written path=vault/programs/incremental-cognition/floor/reference-gex44.json total_chars=207245 tokens=109021 window_sha256=dc6d23b90cac window_rows=34
FLOOR verdict=REFERENCE_WRITTEN exit=0 reason=written
```
2. Green direction, `--check --reference reference-gex44.json --transcript <REAL_A>` (`/tmp/ic-p4-03-gex44-check.txt`, ends `exit=0`):
```
SOURCE transcript name=607795c4-aa30-4fb8-886c-5b1e24a7a991.jsonl
FLOOR total_chars ref=207245 now=202803 delta=-4442
WINDOW ref_sha256=dc6d23b90cac now_sha256=d5e2920263a0 ref_rows=34 now_rows=34 same=no
LAYER other:session_context scope=harness ref=1180 now=1121 delta=-59
LAYER system_prompt scope=unattributed ref=13830 now=9447 delta=-4383
SCOPE universal=+0 project=+0 harness=-59 unattributed=-4383
SKILLS ref_chars=30000 now_chars=30000 ref_entries=294 now_entries=294 ref_skill_count=294 now_skill_count=294
TOKENS status=not_comparable ref=109021 now=107351 delta=na
FLOOR verdict=WITHIN_BOUND exit=0 reason=within_bound
exit=0
```
(One difference from the planning expectation: the worker's `session_context` is also 59 chars larger than the interactive session's, a harness-scope fall; it is not a rise and does not change the verdict.)
3. Reverse direction, a scratch reference from REAL_A (`/tmp/ic-p4-03-ref-a.json`) checked against REAL_B (`/tmp/ic-p4-03-reverse.txt`, ends `exit=1`):
```
SOURCE transcript name=34f03871-4d33-4b7d-a52e-ec674b20a223.jsonl
FLOOR total_chars ref=202803 now=207245 delta=+4442
WINDOW ref_sha256=d5e2920263a0 now_sha256=dc6d23b90cac ref_rows=34 now_rows=34 same=no
LAYER other:session_context scope=harness ref=1121 now=1180 delta=+59
LAYER system_prompt scope=unattributed ref=9447 now=13830 delta=+4383
RISE system_prompt scope=unattributed delta=+4383 unit=chars rules=universal_1k
SCOPE universal=+0 project=+0 harness=+59 unattributed=+4383
SKILLS ref_chars=30000 now_chars=30000 ref_entries=294 now_entries=294 ref_skill_count=294 now_skill_count=294
TOKENS status=not_comparable ref=107351 now=109021 delta=na
FLOOR verdict=MATERIAL_RISE exit=1 reason=material_rise
exit=1
```
`grep -c '^RISE system_prompt scope=unattributed delta=+4383' /tmp/ic-p4-03-reverse.txt` -> `1`.
4. Default reference on GEX44, `--check --transcript <REAL_A>` -> `UNMEASURABLE reference_missing: no such reference file`, `FLOOR verdict=UNMEASURABLE exit=2 reason=reference_missing` (the frozen-rule reference is laptop-plane and absent here).
5. Snapshot: `stat -c '%n %s %Y'` of REAL_A and REAL_A7 before and after the whole smoke and the full test run: `diff /tmp/ic-p4-03-snap.before /tmp/ic-p4-03-snap.after` printed nothing (REAL_B excluded, it is a live session).

Committed reference acceptance output: `python3 -c ...` printed `gex44 34f03871-4d33-4b7d-a52e-ec674b20a223 109021 []`. Top-level keys (no content-bearing key; sizes only):
`['caveats', 'components', 'excluded', 'explanations', 'layers', 'provenance', 'schema', 'skill_listing', 'tokens', 'total_chars']`. Provenance carries `plane: gex44`, `source: transcript`, `install_commit 339ccaa91ee040e81e6171ea27e855b1f108aed0`, `window_sha256`, `window_rows 34`. `git show --stat HEAD` lists only `tools/test_floor_regression_gate.py` and the reference.

## R2-W1 item 3 (orchestrator requirement): APPLIED

The committed `reference-gex44.json` provenance carries `window_sha256` and `window_rows` from `window_digest` (04-01). Gate `V-FLOOR-REAL-REFERENCE-PINNED` re-reads `34f03871` from disk with `read_window` + `window_digest`, compares both values to the committed reference, asserts the reference identity (plane gex44, session 34f03871, `explanations == []`), has a positive control (the other real window, REAL_A, must NOT match the pin) and a cross-check that `measure()` and `window_digest` agree. When REAL_B is absent it prints `SKIP UNMEASURABLE: not on this host: ...` (never PASS); when the reference file itself is missing it FAILs. It PASSes on GEX44 (see the 59/59 line above).

## Deviations from Plan

### Auto-fixed / decided

**1. [Plan staging] probe_view and first_call_tokens landed in the Task 1 commit** - the plan places `first_call_tokens` and `probe_view` in Task 2, but `measure()` was already being edited for `--session` (Task 1) and `load_lfp()` is shared by `--session` and `--probe`; shipping them once avoided editing the same function in two commits. V-FLOOR-PROBE-VIEW therefore did not show a RED in Task 2 (recorded above).

**2. [Rule 2 - cost safety] `precheck_write`** - `reference_exists` and `refused_path` are now checked before the source is resolved, so `--write-reference ... --probe` on an existing target fails before it can spend a session (the plan's order would spawn first). Pinned by the existing V-FLOOR-WRITE-SAFETY (still green).

**3. [Plan interpretation] `--json` carries `source` and `probe_view` under `provenance`** - the 12-key document (V-FLOOR-JSON) is unchanged; `provenance.source` and `provenance.probe_view` hold them; `probe_error` is on the in-process result and in the `UNMEASURABLE probe_failed: <ExceptionClass>` text line.

**4. [Plan interpretation] extra refusals** - `--cwd` without `--probe` is `exit 2 cwd_without_probe`; `CPP_CLAUDE_EXE` naming a non-file is `claude_exe_not_found`; a fence with no `CPP_FLOOR_GATE_TEST_ROOT` refuses (fail closed). `load_lfp` falls back to the PYTHONPATH `wiki/tools` so a `--gate-path` copy outside the checkout can still import the owner module.

**5. [Plan interpretation] drill control and SKIPs** - the real-transcript gates SKIP on a host without the files, so the drill's control now requires `len(green) + skipped == len(DRILL_GATES)` (skips are reported on the control lines) instead of every gate being green; on GEX44 it reads `49/49 (skipped 0)`. The gates that spawn real subprocesses (SOURCES-E2E, PROBE-STUB, -BAD-EXIT, -NOT-EXECUTABLE, NO-REAL-SESSION, REAL-A7-NO-CALL, REAL-APPENDED-PROMPT, SEEDED-REAL, REF-GEX44-GREEN) are excluded from the drill's control like the tracer, since a monkeypatch cannot reach them; the in-process ones (all other probe gates, REAL-GEX44, REAL-REFERENCE-PINNED) are in it.

**6. [Real data] layer sums, not single rows** - V-FLOOR-REAL-GEX44 asserts the plan's planning numbers as per-layer sums across scopes (for example agent listing 27,062 = 24,417 universal + 2,645 unattributed after 04-02's attribution), which is what the planning measurements were.

**7. [tooling] session-file-guard false positive** - my first smoke command contained an `rm -f` of a `/tmp` file next to real transcript paths and the PreToolUse guard blocked it before anything ran; re-ran without the `rm` (the target did not exist). No session file was touched.

**8. [Trailer]** commits end with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (the session's attribution reminder, the same choice 04-01 and 04-02 recorded) rather than the dispatch's Opus 5.5 line.

## Known Stubs

None. The only stubs are the test-only stub executables the plan requires (`claude-stub`, `claude-bad`, `claude-nosid`, `claude-noexec`), written under the scratch root by the test and never committed.

## Threat Flags

None beyond the plan's register. T-04-03-01: no test or verification command started a real `claude` session (the fence is on process-wide in the test module; V-FLOOR-NO-REAL-SESSION proves the guard raises without a stub). T-04-03-04: transcripts opened read-only; the stat snapshot diff is empty. T-04-03-05: the reference says `plane: gex44`, the default reference stays absent (`reference_missing`). T-04-03-07: reference top-level keys listed above; `probe_error` carries the exception class only.

## Self-Check: PASSED

- `tools/floor_regression_gate.py`, `tools/test_floor_regression_gate.py`, `vault/programs/incremental-cognition/floor/reference-gex44.json` exist; commits `f065ac8e`, `17228d2f`, `09bb9142` are on `mission/incremental-cognition-run`; `git rev-list --count 15f70abea8745d4e7113530dc6422a93af9bf344..HEAD` = 3 before this SUMMARY commit.
- `FLOOR_PASS=59/59 skipped=0` and `DRILL killed=13/13` observed after the last code commit.
