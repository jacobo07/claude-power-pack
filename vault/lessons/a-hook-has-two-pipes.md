# A hook has two pipes, and only one of them was guarded

**Sealed** 2026-09-16 · Branch `feature/knowledge-acquisition` · IC-009
**Sister of** `timeout-without-tree-reaping-is-the-engine.md` (the same mechanism, one
layer out) and the 2026-06-01 async-wrapper trap in `ukdl-universal.md` (the same
mechanism, seen from the parent's side).

## User-visible symptom

The UI sat on `running PreToolUse hooks ... 6/8 ... 40m 44s`. The Owner reports this
cross-repo as a dead screen that only ESC recovers.

## Proximal mechanism (bfb40a1, prior session — CONFIRMED)

`fs.readFileSync(0, "utf-8")` on a stdin pipe that never closed. It blocks the event loop,
so the in-process watchdog was never scheduled, and the harness's 5 s budget killed the
shell WRAPPER while a timeout kills the direct child only — leaving the node process alive
holding the inherited stdout pipe.

    pid=47776  age_min=36.5  cpu_sec=0  parent_alive=False
    pid=3900   age_min=36.5  cpu_sec=0  parent_alive=False

Zero CPU over 36 minutes is the discriminator: it rules out a runaway regex and proves the
processes never executed one line of hook logic.

## Proven root cause (this session)

**The proximal mechanism was real and incomplete.** During the reality scan,
`session-file-guard.js` — the hook bfb40a1 fixed, hash-identical to its repo copy — was
found parked at 11.4 minutes, zero CPU, dead parent. Beside it, `first-time-project.js`,
which **reads no stdin at all**, parked with the same signature.

A hook has two pipes. On Windows Node's stdout-to-a-pipe is SYNCHRONOUS, so once the OS
buffer fills with no reader, `process.stdout.write` blocks the event loop exactly the way
`readFileSync(0)` did. Measured, and the two numbers disagree because the buffer belongs to
whoever CREATED the pipe:

    .NET RedirectStandardOutput   4096 B passes    8192 B BLOCKS
    libuv spawn                  65536 B passes  262144 B BLOCKS

The blocked child logged its `start` marker and never logged the marker on the line after
its write — parked INSIDE the write, not at exit.

The class therefore has four members, not one: a synchronous read; a shared helper whose
timer resolved but left its listener attached; an async listener with no timer at all; and
a write over the pipe buffer. Only the first was visible to the detector.

## Contributing conditions

- Two shared runtimes (`hook-utils.readStdin`, `hook-runtime.readStdinJson`) each carried
  the resolved-is-not-exited defect, so one file explained four to six parked hooks.
- `hook-runtime.runHook` never called `process.exit` at all, relying on the loop to drain.
- `hook-utils.js` was not in the repo, so no commit could record a fix to it.
- `learning-sentinel.js` emitted 148,740 B of `additionalContext`, over both buffers.

## The control that failed, and why prior defences missed it

The ratchet from 5ccbe78 was correct and structurally blind: it asked *does this file call
`readFileSync(0)`*, which is a question about one PRIMITIVE, while the defect is a PROPERTY
— can this process die when its producer never closes the pipe. Six further parked hooks
contained no banned call, so the gate reported a clean estate over them.

It was also gameable: the stale-entry clause forced deleting a name once fixed, but nothing
forced fixing before deleting. The ratchet could be turned by editing a dict.

## Repair

All ten of the frozen population migrated to a bounded-async template; both shared runtimes
hardened (detach, pause, `error` handler, non-unref'd hard-exit backstop, explicit exit);
three unbounded listeners bounded; `learning-sentinel` capped at the smaller measured buffer
with the deferred rules emitted as a named pointer list. `KNOWN_OFFENDERS` reached empty.

## Verification

- `V-STDIN-ALL-EXIT` drives all 36 harness-spawned scripts against an unclosed stdin: 36/36
  exit. Red branch driven with a thread-blocking mutant containing no banned call → 5/6,
  only that clause red, restored SHA-256 identical.
- `V-EMIT-BUDGET`: every emission under 4096 B; `learning-sentinel` 148,740 → 1,191 B.
- `V-MIRROR-*`: 18 dual-resident hook files pinned, 5 pre-existing divergences frozen.
- `HOOK_SELFTESTS` 41/41, inconclusive 1 (a budget test that correctly judged nothing on a
  starved host).
- Post-migration orphan census: 1 parked process, and it is `config.js`, not a hook.

## Recurrence guard

`tools/test_hook_stdin_liveness.py` (7 gates) and `tools/test_hook_mirror_identity.py`
(5 gates). The liveness gate is scoped to the property, derives the claimed-fixed set
rather than curating it, and reads process CPU to separate parked from slow.

## Mistakes made while building this — kept on purpose

1. **A probe that could not tell "never ran" from "ran fine."** A spawn failure fires
   `error`, not `exit`, and my first pipe probe read that as an exit — reporting 8192 B as
   EXITED in 232 ms and nearly filing a platform disagreement. Fixed with a marker file the
   child cannot forge, plus a clause asserting every ladder child actually executed.
2. **A locale bug that inverted six verdicts.** `Get-Process` printed `0,109`; `float()`
   raised; my `except ValueError: return False` labelled every PARKED hook BUSY. The final
   gate reads CPU through a syscall instead.
3. **A mutant that proved nothing.** `setInterval` does not hang a hook, because
   `process.exit()` is unconditional. The gate was right and the mutant was wrong — and the
   correction became the most useful finding in the session: what strands a process is never
   REACHING an exit call.
4. **Two false statements from broken instruments.** `NUL` is not a valid PowerShell
   `RedirectStandardInput`, so a process that never started was reported "STILL RUNNING";
   and verifying an emission by piping from PowerShell into node prepended a BOM, so the
   hook saw `{}` and the fix read as having deleted everything.
5. **A claim I had to withdraw.** I asserted that parked hooks were starving the host. Free
   memory read 109 MB then 1185 MB seconds later and node went 21 → 8 unaided: that is
   churn, not accumulation, and the measurement did not support the claim.

## Universal lesson

**Scope a guard to the property, not to the primitive; and prove the process dies, not that
its predicate returned.** A detector named after one call can only ever find that call, and
a promise settling is a fact about the caller while exiting is a fact about the process.
Every instrument failure above is the same shape as the bug it was chasing: something that
did not happen and something that succeeded left identical evidence.
