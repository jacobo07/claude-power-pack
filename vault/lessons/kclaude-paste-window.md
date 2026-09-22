# The paste window of a new pane (T-KCLAUDE-PASTE-WINDOW-001)

**Symptom (Owner, 2026-09-22):** a prompt pasted from the clipboard into a NEW
Claude pane does not arrive. Asked: fix it globally, document the root cause,
make prompts pasteable as early as possible.

## Root cause

A Cursor pane starts `cmd /K kclaude.cmd -> powershell.exe -File kclaude.ps1 ->
claude.exe` (chain walked from the live process table, not taken from a doc).
**Until `claude.exe` is up there is no prompt box and no bracketed-paste mode**,
so a paste in that window reaches a console with no reader for it: it is lost,
or its newlines arrive as Enter keys. The paste window is therefore everything
that runs before `& claude`. Claude's own SessionStart chain (~4.7 s measured)
is *not* in the window: it delays submission, and the prompt box accepts a
paste while it runs (changelog: "Esc cancels a prompt waiting on a SessionStart
hook").

Two independent costs made the window long. Both measured, median of 3:

| cost | measured | owner |
|---|---|---|
| synchronous Python in `kclaude.ps1` before launch | prelaunch fast 1145 ms + hook-registry check 1081 ms | this repo -- **fixed** |
| Windows PowerShell 5.1 startup itself | `powershell -NoProfile -Command exit` **4183 ms** vs `cmd /c exit` 127 ms; + one Management and one Utility cmdlet **7352 ms** | the machine -- **needs an elevated one-time fix** |

The second one is the larger, and it is machine-wide. A fresh `powershell.exe`
loads native images (`*.ni.dll`) for `mscorlib`, `System` and `System.Core` --
so the instrument can see a native image -- but not for
`System.Management.Automation` or `Microsoft.PowerShell.ConsoleHost`, and
`ngen display System.Management.Automation` answers *"The specified assembly is
not installed"*. PowerShell's core is JIT-compiled on every start, which every
powershell.exe on this host pays: panes, hooks, scheduled tasks, agent tool
calls.

## What changed

1. **Bare pane runs no Python before `claude`** (`bin/kclaude.ps1`, mirrored at
   `tools/kclaude.ps1`). The fast prelaunch returned nothing launch-critical
   for a pane with no `--resume`/`--scope`: scope recall needs a sid, the resume
   gate keys on a `$resumeArg` a bare pane never has, the CO-08 warning never
   blocked anything. Resume and `--scope` panes keep it, because there it is
   load-bearing.
   - The CO-08 warning was **relocated**, not dropped: it rides the cached
     advisory bundle (`prelaunch.run_advisories` -> `_gate_advisory`), printed
     instantly at the next launch like W1/W5. Pinned by `V-CO08-IN-ADVISORY-CACHE`.
   - The namer's "sessions that existed before launch" list is read from the
     project's transcript directory in ~6 ms, **before** launch, so it cannot
     race the new session's transcript. Pinned by `V-PASTE-KNOWN-FROM-DISK`.
2. **Hook-registry check cached by content.** Its verdict is a pure function of
   four inputs: settings bytes, the dispatcher source it loads, the checker's
   own source, and whether each dispatcher target exists. A VALID verdict is
   reused only when all four match; any change re-judges live -- exactly the
   launch after a rewrite, the case the check exists for. INVALID/UNJUDGEABLE
   are never cached. The receipt records `cached`, so the generations ledger
   stays honest.
3. **`tools/ngen_powershell.ps1`** -- the elevated one-time fix for cost #2.
   Idempotent, reversible (`ngen uninstall`), measures itself before and after.

Measured, stub `claude`, alternated, median of 3, same host:
**old launcher 13 782 ms -> new 7 502 ms** to launch. The remainder is almost
entirely PowerShell startup and module autoload, which only NGEN addresses.

## The rule, and what holds it

**On a bare pane nothing synchronous runs before `& claude` except what the
launch itself consumes.** Informational work is detached or served from a
cache. A new blocking step justifies itself against the gate, not against its
own runtime in isolation -- each one was "only ~1 s" when it was added.

- `tools/test_kclaude_paste_window.py` (V-PASTE-*, 10/10) drives the real
  launcher with a stub `claude` and **counts** synchronous steps through the
  `KCLAUDE_TRACE_FILE` trace, rather than timing them: python's own startup
  measured 458-1422 ms across consecutive runs here. Isolated TEMP and state
  dir, so it never consumes another pane's restart flag or writes the Owner's
  caches. Mutation drill 4/4 killed (bare pane runs the decision again; cache
  never hits; cache reuses any verdict; cache ignores the key).
- `tools/test_wrapper.py` 25/25 -- including the fix to `V-ADVISORY-CACHE`, which
  had never stubbed `_gate` and so read the live host (23 hot sessions) once the
  gate joined the advisory bundle.

## Not proven

- The fate of bytes pasted inside the window (lost vs replayed as keystrokes)
  was reasoned from the absent reader, **not observed**: driving a paste into a
  fresh Cursor pane is outside what the agent can do from a tool call.
- ~~The NGEN effect is predicted from the missing native images, not yet
  measured.~~ **CLOSED BY MEASUREMENT, same session, 2026-09-22** -- see below.

## The NGEN fix, run and measured (2026-09-22, elevated)

The Owner ran `tools/ngen_powershell.ps1` as Administrator. Eleven assemblies
had no native image; all eleven installed `ok`; the after-probe found **zero**
remaining. The script measures itself **in the same batch**, which is the only
comparison an irreversible machine-wide change permits:

| `powershell -NoProfile -Command exit` | median | readings |
|---|---|---|
| before | 1962 ms | 1962 / 1867 / 2167 |
| after | **433 ms** | 869 / 433 / 320 |

**4.5x, and the prediction's magnitude was wrong.** The 4183 ms recorded higher
up in this file is a real reading of a starved host, not the machine's resting
cost -- the same-batch before figure is 1962 ms. So the honest claim is the
ratio, not the 4183 ms of saving the earlier number implied. The original
readings are left standing above: a historical measurement describes the run
that happened, and editing it to match today would fabricate a verification.

Bare-pane launcher after the fix, same harness as the gate (real launcher, stub
`claude`, private TEMP and state dir), **at 467 MB free**: readings
2133 / 1439 / 1498 / 2096 / 2425, **median 2096 ms**, against 7502 ms in the
previous session. That pair is **cross-load, not same-batch**, and is reported
as such -- it is the comparison that already cost this investigation one wrong
number (the "+3 s of module autoload" that a same-batch reading put at ~700 ms).
The trace also re-confirms both behaviours the commit claims: no synchronous
Python on a bare pane, and `sync:hook-registry` on the cold run only, absent on
the four that follow it.

## Instrument failures on the way

- `Assembly.Location` was the first probe for native images and reported every
  assembly JIT -- including `mscorlib`, which is impossible on a healthy .NET.
  It returns the IL path even when the native image is used, so it could only
  ever say one thing. Replaced by the process's loaded modules (`*.ni.dll`),
  with `mscorlib` as the positive control.
- The gate's stub-call counter read cmd's output as ASCII and died on
  `ECHO está desactivado.` (Spanish console code page). Now counts lines as bytes.
