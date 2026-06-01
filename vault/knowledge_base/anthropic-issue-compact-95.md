# [Bug] /compact freezes at ~95% progress indefinitely on Windows + Cursor

**Ready-to-file issue body for github.com/anthropics/claude-code.**
The Power Pack ships an Owner-triggered escape (`/compact-rescue`,
BL-COMPACT-001) but the canonical fix has to land upstream in
`claude.exe`. This file is the issue body the Owner can paste.

---

## Environment

- **Claude Code version:** (run `claude --version` before filing)
- **OS:** Windows 11 Pro 10.0.26200
- **Terminal:** Cursor (embedded PowerShell)
- **Active model:** Claude Opus 4.7 (1M context); seen in same
  configuration on Sonnet 4.6.

## Behaviour

Running `/compact` causes Claude Code to freeze with the progress
indicator stuck at approximately **95%**. The `claude.exe`
process stays alive (high working-set, low CPU). The `.jsonl`
transcript file stops receiving new turns. Input keystrokes are
ignored. The only recovery is to force-kill `claude.exe`.

## Steps to reproduce

1. Run a Claude Code session in Cursor on Windows long enough
   to accumulate a moderately large transcript (`claude.exe`
   working-set >= 200MB; observed reliably at >= 350MB).
2. Type `/compact` at the prompt.
3. Progress indicator climbs and stops at ~95%.
4. Indicator does not advance further; no new `.jsonl` lines
   appear in `~/.claude/projects/<encoded-cwd>/<sid>.jsonl`.

## Expected behaviour

`/compact` completes (indicator reaches 100%), the transcript is
replaced with the compacted summary, and the prompt returns.

## Observed behaviour

Indicator frozen at ~95% indefinitely (verified up to 30 min
before Owner force-killed). No further `.jsonl` writes. CPU
drops to <2%. Working-set stays where it was (no GC visible).

## Empirical data from a Power Pack instrumentation run

Captured while drafting BL-COMPACT-001:

- 40 `claude.exe` processes alive across sessions on the same
  host. Top-3 working-set: 451MB / 373MB / 352MB. Hang
  frequency correlates with working-set (larger transcript =
  higher hang probability).
- Auto-compact SendKeys daemon log: 15 successful
  Enter-dispatches / 2 TTL-only exits. The hang is **after** the
  Enter, not before; the daemon is not the source.
- The `.jsonl` is intact pre-compact (append-only writes
  preserve every prior turn). On force-kill + `--resume`, the
  session loads the pre-compact transcript without loss.

This points to the hang being in the post-API local render path
inside `claude.exe`: rebuild of the context window with the
summary, write of the new compacted `.jsonl`, reload of the
prompt cache, or final TTY draw. Not the network -- the API
response has clearly arrived (progress would not be at 95%
otherwise).

## Workaround currently shipped

`/compact-rescue` (BL-COMPACT-001) -- an Owner-triggered
PowerShell script that:

1. Finds the highest-RSS `claude.exe` on the host.
2. Verifies the session looks genuinely stuck via a `.jsonl`
   recency guard (idle >= 120s by default).
3. Captures the `sessionId` from the `.jsonl` header.
4. Force-kills `claude.exe`.
5. Signals `kclaude.bat` (the Power Pack launcher wrapper) to
   `--resume` in the same Cursor pane.

The workaround restores the session to its pre-compact state.
The in-flight compact summary is lost; the rest of the
transcript is preserved.

## Reach of the workaround

- It does NOT fix the underlying hang -- the bug is in
  `claude.exe` and the Power Pack cannot patch a vendored
  binary.
- It does give the Owner a clean escape (kill + resume) in
  <30 seconds when the hang is hit.
- Source: `tools/compact_rescue.ps1`,
  `commands/compact-rescue.md`,
  `vault/knowledge_base/compact-95-hang-repro.md` (Power Pack
  repo).

## What would help diagnose upstream

- A `claude.exe` build with verbose tracing of the post-API
  compact pipeline (context rebuild, `.jsonl` write, prompt-cache
  reload, TTY render) so we can identify which sub-step is
  blocking when the indicator sits at 95%.
- Confirmation of whether large summaries (long transcripts)
  hit a fixed-size buffer or a single-threaded operation that
  saturates on big inputs.

## Honest scope

Filed as a Windows + Cursor report. The Power Pack has not
reproduced this on Linux or macOS yet; the bug may or may not
be host-specific. If you have repro on other platforms, please
add a comment with your environment string.

---

**Issue body ends here.** Owner: copy from the line below the
"---" near the top of this file (just below the H1) through the
last paragraph above this footer, paste into a fresh issue at
github.com/anthropics/claude-code/issues. Include the output of
`claude --version` in the Environment block before filing.
