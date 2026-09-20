---
status: issues_found
phase: 01-two-pane-exactness-drill
depth: standard
files_reviewed: 17
files_reviewed_list:
  - tools/two_pane_drill.py
  - tools/test_two_pane_exactness.py
  - tools/gsd_long_run.py
  - tools/gsd_long_run.py.pre-phase-advance
  - tools/continuation_transport.py
  - extension/src/extension.js
  - hooks/gsd_stop_continuation.js
  - tools/gsd_autorun_marker.py
  - modules/zero-crash/hooks/context-watchdog.py
  - hooks/hook-dispatcher.js
  - modules/gsd_x/mission/__init__.py
  - modules/gsd_x/mission/closure.py
  - modules/gsd_x/mission/obligation.py
  - modules/gsd_x/mission/store.py
  - tools/test_rearm_reachability.py
  - tools/test_transport_cold_start.py
  - tools/test_gsd_stop_continuation.js
date: 2026-09-20
findings:
  critical: 1
  warning: 3
  info: 1
  total: 5
---

# Phase 01 Code Review — two-pane-exactness-drill

**Reviewed:** 2026-09-20
**Depth:** standard
**Files Reviewed:** 17 (of 103 in scope; see coverage note at the end)
**Status:** issues_found

## Scope caveat

The diff base (`396477dbab9afdf0e860a422d3b08e8d449ce4ed`) is the parent of the
commit that first created the phase directory, not a commit scoped to phase 1's
own work. As a result the reviewed file set spans several unrelated efforts
committed in the same window:

- **In-phase (phase 1's own deliverables):** `tools/two_pane_drill.py`,
  `tools/test_two_pane_exactness.py`, `tools/gsd_long_run.py`,
  `tools/continuation_transport.py`, `extension/src/extension.js`,
  `hooks/gsd_stop_continuation.js`, `tools/gsd_autorun_marker.py`,
  `modules/zero-crash/hooks/context-watchdog.py`, `hooks/hook-dispatcher.js`,
  and their matching `tools/test_*.py` / `.js` gates.
- **Adjacent, NOT phase 1 (same commit window):** `modules/gsd_x/**`,
  `tools/gsd_x_*.py`, `tools/bench_gsd_x_reconstruction.py`,
  `skills/android-reverse-engineering/**`, `skills/mobile-game-wii-port/**`,
  and their `tools/test_android_re.py` / `tools/test_mobile_game_wii_port.py`
  gates.

Findings below are labelled `[in-phase]` or `[adjacent]` accordingly. Effort
was weighted toward the in-phase surface per the review brief; the adjacent
surface (android-reverse-engineering, mobile-game-wii-port, most of
`modules/gsd_x`) was only spot-checked (pattern sweeps for injection/eval/
hardcoded-secret shapes, plus a read of the mission core files) and found no
issues meeting the Proof Triad bar.

## Summary

The in-phase surface (the two-pane exactness drill, the `/cpp-gsd-long`
self-checking tools, the exact-target continuation transport, and the
hook-dispatcher chain wiring) is unusually rigorous: nearly every function
carries a comment naming the specific production incident it was written to
close, most state files use an atomic tmp-then-rename write, and several
files ship their own adversarial unit gates (`V-*` naming) with paired
positive/negative controls. Most candidate issues raised during this review
dissolved on closer reading of that surrounding context.

One finding is a genuine BLOCKER: a fully-written, carefully-guarded function
(`phase_boundary_owed`) that documents the exact 14-hour production stall it
exists to fix, and is never called from anywhere in the codebase — the fix
described in its own docstring is not live. Three further issues are lower-
severity robustness gaps in the drill tooling and the sweep's idle-time
computation.

## Critical Issues

### CR-01: `phase_boundary_owed` is fully implemented, documented against a real 14-hour production incident, and never called `[in-phase]`

**File:** `tools/gsd_long_run.py:955-1012` (function definition); no call site
exists anywhere in the reviewed tree.

**Issue:** `phase_boundary_owed()` is an elaborate, carefully-guarded function
(opt-in per marker, refuses on a trailing `?`, refuses when `gsd_status` is not
`OK`, refuses when a flag is already waiting, requires 40 minutes idle) whose
own docstring documents the exact incident it was built to fix: session
`fa6961b6` sat `stalled` six times over fourteen hours because
`/cpp-gsd-long`'s `sweep()` only knows how to resume across a *context*
(compaction) boundary, not a *phase* boundary. The function was written,
including a new marker field `advance_on_phase_boundary` that callers are
supposed to opt into.

Grep across the whole repository (`Grep pattern="phase_boundary_owed"`) turns up
exactly two hits: the definition in `tools/gsd_long_run.py` and an identical
copy in the stray backup file `tools/gsd_long_run.py.pre-phase-advance`. It is
not called from `sweep()` (verified by reading `sweep()` end-to-end,
`gsd_long_run.py:1015-1125` — the loop only branches on `reap_decision`,
`gsd_status`/`ALL_COMPLETE`, and `resumable = tail == cmd or
tail.startswith("/compact")`), not called from `report()`/`status()`, and not
referenced by `advance_on_phase_boundary` anywhere else in the codebase
(`Grep pattern="advance_on_phase_boundary"` matches only the function's own
body). `tools/test_gsd_long_run.py` has zero references to either symbol
(confirmed via grep, not just a read).

**Failure scenario:** Exactly the one in the docstring recurs unchanged: a
`/gsd-autonomous` run finishes a phase and ends its turn on prose (not a
`/compact` line, not the resume command, not a question). `sweep()`'s
`resumable` check is false, so the run falls into the `stalled` bookkeeping
branch at `gsd_long_run.py:1099-1104` forever — it will log `stalled` events
indefinitely and never advance, even though `phase_boundary_owed` was written
specifically to detect and repair this exact shape and even though a marker
could be opted in via `advance_on_phase_boundary: true`. Nothing in the current
code path ever sets or reads that field, so no marker can ever opt in.

**Why guards fail:** There is no test exercising the call site because there is
no call site to exercise — `test_gsd_long_run.py` cannot catch a wiring gap by
unit-testing the orphaned function's pure logic in isolation (which it does not
even do). This is the "documented capability nobody executes" failure mode:
the prose (docstring) describes a fix; the runtime behavior of `sweep()` is
unchanged from before the fix was written.

**Fix:** Wire a call into `sweep()`'s idle-handling branch, e.g. after the
existing `resumable` check fails and before falling through to `stalled`:

```python
if not resumable:
    boundary = phase_boundary_owed(m, st, tail, cmd, waiting, idle_s)
    if boundary["ok"]:
        actions.append({"session_id": sid, "action": "phase_advanced",
                        "reason": boundary["reason"]})
        if not dry_run:
            gate = resume_gate(m)
            if not gate["halt"]:
                mk = _marker_module()
                if mk is not None:
                    mk.bump_cycles(sid)
                route = _recover_via_transport(sid, cwd, str(transcript), cmd, cmd, mtime)
                ledger_append(sid, "phase_advanced", route=route)
        continue
```

and delete (or clearly mark historical-only) `tools/gsd_long_run.py.pre-phase-advance`
so a reader does not mistake it for a second live copy.

## Warnings

### WR-01: `fire()`'s daemon subprocess has no timeout handling — an unhandled `TimeoutExpired` crashes the drill mid-run `[in-phase]`

**File:** `tools/two_pane_drill.py:466-477`

```python
proc = subprocess.run(
    ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
     "-File", str(DAEMON)],
    env=drill_env(runid), capture_output=True, text=True, timeout=timeout, check=False)
```

**Issue:** `fire()` is invoked with the same `--timeout` value used for the
`arm()` polling wait (default 300s). If the daemon PowerShell script hangs
(e.g. blocking on a busy pane — "a busy pane is not a failure" per the
`arm()` docstring, treated elsewhere as recoverable, not exceptional),
`subprocess.run(..., timeout=timeout)` raises `subprocess.TimeoutExpired`.
There is no `try/except` around this call, so the whole `fire` invocation
crashes with an unhandled traceback instead of printing a `FAIL fire/<pane>:
...` line, unlike every other failure path in this file (`probe`, `arm`,
`observe` all print `FAIL ...` and return `1`).

**Concrete failure mode:** `manifest.json` has already been written at
`write_manifest(runid, data)` (line 463) *before* the subprocess call, with
`info["t0"]` and `info["expect_line"]` set. If the subprocess then times out
and raises, the process exits via an uncaught exception (stack trace to
stderr) instead of a clean `FAIL`, breaking the file's own stated three-exit-
code discipline ("a verifier that could not judge its subject must never
present as a verdict" — the sibling `test_two_pane_exactness.py` implements
this discipline explicitly; `two_pane_drill.py fire` does not).

**Why existing guards don't catch this:** No test in `test_two_pane_exactness.py`
drives `fire()` at all — it only unit-tests `_carries_nonce`, `_owning_window`,
and runs the real-drill-evidence gates against a `manifest.json` that assumes
`fire` already completed. Nothing exercises the daemon-timeout path.

**Fix:**
```python
try:
    proc = subprocess.run([...], env=drill_env(runid), capture_output=True,
                          text=True, timeout=timeout, check=False)
except subprocess.TimeoutExpired:
    print(f"FAIL fire/{pane}: daemon did not exit within {timeout:.0f}s")
    return 1
```

### WR-02: `two_pane_drill.py` reads and writes `manifest.json` non-atomically `[in-phase]`

**File:** `tools/two_pane_drill.py:83-86` (`write_manifest`)

```python
def write_manifest(runid: str, data: dict) -> None:
    p = manifest_path(runid)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

**Issue:** Unlike the sibling module `gsd_long_run.py`, which consistently
writes state files via a `tmp = path.with_suffix(".tmp"); tmp.write_text(...);
tmp.replace(path)` pattern (`write_thresholds`, `capture_endpoint`,
`write_job`), `two_pane_drill.py`'s `write_manifest` writes `manifest.json`
directly with `write_text`. The drill's own usage pattern is separate
`arm`/`fire`/`observe` invocations against the same `manifest.json` (arm now,
fire later once a human has watched a pane, observe after that) — if the
process is interrupted mid-write on any of those (Ctrl-C, host OOM), the file
is left truncated.

**Concrete failure mode:** every subsequent call — `read_manifest` inside
`two_pane_drill.py` itself, and `test_two_pane_exactness.py`'s `main()` when
given `--runid` — calls `json.loads()` on the file with no `try/except`
around this specific read path in `two_pane_drill.py` (only
`test_two_pane_exactness.py`'s harness-failure branch guards its own read),
so a corrupted manifest crashes the next `arm`/`fire`/`observe` call with an
unhandled `json.JSONDecodeError` instead of a clean `FAIL`.

**Why existing guards don't catch this:** no test simulates an interrupted
write, and the atomic-write pattern is already known and applied one file
away in `gsd_long_run.py` (imported here as `lr`), so this looks like an
inconsistency rather than a considered decision.

**Fix:** mirror the sibling module's tmp-then-replace pattern:
```python
def write_manifest(runid: str, data: dict) -> None:
    p = manifest_path(runid)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(p)
```

### WR-03: `sweep()`'s 20-minute stall/recovery gate uses raw transcript mtime instead of the conversation-clock-aware `session_idle_seconds()` that a sibling check in the same function already uses to avoid exactly this defect `[in-phase]`

**File:** `tools/gsd_long_run.py:1028-1033` (compare with `session_idle_seconds`,
`gsd_long_run.py:763-804`, and its caller `reap_decision`, `gsd_long_run.py:870-891`)

```python
for path, m in _markers():
    sid = m["session_id"]
    cmd = m.get("resume_command") or ""
    cwd = m.get("cwd") or ""
    transcript = find_transcript(sid)
    idle_s = (now - transcript.stat().st_mtime) if transcript else None
    ...
    decision = reap_decision(sid, transcript)   # uses session_idle_seconds() internally
    if decision["reap"]:
        ...
        continue
    ...
    if idle_s < STALL_MINUTES * 60:             # uses the RAW mtime computed above
        continue
```

**Issue:** `session_idle_seconds()`'s own docstring documents a measured
defect: transcript files receive host metadata rows (`custom-title`,
`cost-state`) that update the file's mtime without being real conversation
activity, and on 9 armed markers measured 2026-09-19 "the file clock ran up
to 19.0 h behind the conversation clock" (i.e., `now - mtime` reads as
*more recent* / less idle than the session's true last spoken content). This
was fixed for the 48-hour reap decision by adding `session_idle_seconds()`
and routing `reap_decision()` through it. The `idle_s` used a few lines above
for the 20-minute (`STALL_MINUTES`) recovery-eligibility gate is the
unfixed raw computation, `now - transcript.stat().st_mtime`, and is not
routed through `session_idle_seconds()`.

**Concrete failure mode:** a `/gsd-autonomous` run that has genuinely gone
silent (no new assistant turn) for well over 20 minutes, but whose transcript
file keeps receiving metadata-only mtime bumps from the host in the meantime,
never satisfies `idle_s >= STALL_MINUTES * 60`, so the sweep's `continue`
at `gsd_long_run.py:1063` skips it every pass — the `resumable`/`stalled`/
recovery logic below (including the one working recovery path,
`owed_line`/`_recover_via_transport`) is never reached for that session. This
is the identical failure shape the docstring for `session_idle_seconds`
describes (a stale session reading as recently active), applied to the
tighter and more consequential of the two thresholds in the same function.

**Why existing guards don't catch this:** `test_gsd_long_run.py` was not
opened in this pass to confirm test coverage of the discrepancy directly, but
the fix for the identical defect exists in the same file for the 48-hour path
(`reap_decision`), which is strong circumstantial evidence this is an
oversight in propagating the fix rather than a considered choice — the two
call sites are eleven lines apart in the same function.

**Fix:** route the stall-detection idle time through the same helper as the
reap decision:
```python
idle_s, idle_clock = session_idle_seconds(transcript) if transcript else (None, "none")
```
and use `idle_s` from that call for the `STALL_MINUTES` comparison as well,
recording `idle_clock` in the `stalled`/`recovered` ledger rows the way
`reap_decision` already records its own `clock` field.

## Info

### IN-01: `mission/store.py::load()` raises an unhandled `AttributeError` (rather than the intended `RuntimeError`) if the store file is a syntactically-valid JSON value that is not an object `[adjacent]`

**File:** `modules/gsd_x/mission/store.py:30-40`

```python
def load(root: Path) -> list[Obligation]:
    p = store_path(root)
    if not p.is_file():
        return []
    try:
        raw = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"obligation store at {p} is unreadable: {exc}") from exc
    return [Obligation.from_dict(d) for d in raw.get("obligations", [])]
```

**Issue:** if `.gsd-x/obligations.json` contains valid JSON whose top-level
value is not a dict (e.g. `[]`, `null`, or a bare string — any of which a
hand-edited or partially-written file could contain), `json.loads` succeeds
and the `except` clause is not triggered, but `raw.get(...)` then raises
`AttributeError: 'list' object has no attribute 'get'` (or similar), which
propagates uncaught past the function's documented contract ("a store that
cannot be read is not an empty store... raises RuntimeError"). The module's
own comment states the intended behavior (fail loudly with a `RuntimeError`
naming the problem) but the guard only covers the JSON-parsing failure mode,
not the wrong-top-level-type one.

**Why guards fail:** `save()` always writes `{"version": 1, "obligations":
[...]}`, so this path is only reachable via a hand-edited or corrupted store,
not through this module's own write path — which is why it is Info rather
than Warning: low likelihood, and the failure is still loud (an unhandled
exception) rather than silent, just not the specific, named `RuntimeError`
the code intends to raise.

**Fix:**
```python
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"obligation store at {p} is unreadable: {exc}") from exc
    if not isinstance(raw, dict):
        raise RuntimeError(f"obligation store at {p} is not a JSON object: {type(raw).__name__}")
    return [Obligation.from_dict(d) for d in raw.get("obligations", [])]
```

## Coverage note

Given the 40-tool-call investigation budget and the instruction to prioritise
the highest-signal files, this pass gave full standard-depth review to the
9 in-phase files named in the brief plus their most load-bearing test gates
(`test_two_pane_exactness.py`, `test_rearm_reachability.py`,
`test_transport_cold_start.py`, `test_gsd_stop_continuation.js`), and to the
core `modules/gsd_x/mission/*` files as a sample of the adjacent surface. The
remaining ~86 files in scope (most of `modules/gsd_x`, all of
`skills/android-reverse-engineering`, all of `skills/mobile-game-wii-port`,
the remaining `tools/test_gsd_x*.py` / `test_android_re.py` /
`test_mobile_game_wii_port.py` gates, and the documentation/spec files) were
not individually read at standard depth; a targeted grep sweep for injection/
`eval`/hardcoded-secret patterns across the android-reverse-engineering and
mobile-game-wii-port trees found no matches. This should be read as a
partial, priority-weighted pass rather than exhaustive coverage of the full
103-file list.

---

_Reviewed: 2026-09-20_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
