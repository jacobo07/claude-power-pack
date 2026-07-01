# kClaude: New Session on Launch + Startup < 3s -- 2026-07-01

Status: **Shipped + verified** (behavioral test 4/4, mirrored to bin)
Mode: EXECUTION · Follows fec5c3a (startup) + 0b55d6a (Cursor profile)

## Two bugs (Owner-confirmed)

- **BUG A:** kClaude lands in the last session instead of opening a NEW one.
- **BUG B:** takes > 3s to load.

## Design clarification (Owner)

- kClaude (terminal button) -> ALWAYS a new session, like the native Claude
  button. Gates (CO-00/CO-08) apply but NEVER auto-resume.
- "Last session" -> resume (Cursor native + lazarus, already routed to smart).
- Explicit `kclaude --resume <sid>` -> resume, only when asked.

## PASO -1 diagnosis (primary source: ~/.claude/bin/kclaude.ps1)

- **bin/kclaude.ps1 is NOT stale** -- hash-identical to tools/kclaude.ps1 (11909
  B) and HAS F1 fast mode (`--mode fast`, `Get-FastDecision`). So BUG B is not a
  stale bin.
- **BUG A root cause:** the fec5c3a F2 `coord.active` / `resume.resume_arg`
  auto-resume branches fire on a bare terminal launch.
- **BUG B is downstream of BUG A:** auto-resuming loads the whole transcript ->
  >3s. A new session loads nothing. The wrapper itself is 333ms (verified).
- **Nuance:** removing F2 exposes the CO-08 rung-3 block, which prompts "resume
  instead?" -> would re-create BUG A. The Owner's "gates active but never
  auto-resume" resolves it -> CO-08 becomes advisory.

## Fix (tools/kclaude.ps1 -> mirrored to bin)

- Decision collapsed: `if ($explicitResume) { resume } else { NEW }`. Removed the
  coord.active/multiple/resume_arg auto-resume branches + the dead Read-HostTimed
  helper. `-n/--new` kept as a no-op (new is now the default).
- CO-08: advisory on a bare launch -- warns (hot count vs cap) then PROCEEDS with
  the new session. No Read-Host, no exit 9, no force-resume.
- /restart loop UNCHANGED (F3 intact): still `$launch = @('--resume', $sid)`.
- Re-mirrored tools/kclaude.ps1 -> ~/.claude/bin/kclaude.ps1 (in sync, 9240 B).

## Verification (observed)

- **Behavioral (tools/test_kclaude_launch.ps1, stubs claude, runs in pp-root
  which HAS resumable sessions):**
  - bare launch -> `claude` (no args) = NEW session.
  - `--resume fake-sid-abc` -> `claude --resume fake-sid-abc`.
  - restart loop resumes SID; CO-08 advisory (no Read-Host). **4/4 x3.**
- test_wrapper.py **24/24 x3** (+V-LAUNCH-NEW-ON-BARE, V-LAUNCH-RESUME-EXPLICIT,
  V-RESTART-STILL-RESUMES).
- test_restart_and_lag.py **17/17** (F3 not broken).
- Parse OK, ASCII-only, bin mirror in sync.

## BUG B resolution

New session = no `claude --resume` = no transcript load. Startup returns to the
verified 333ms wrapper overhead (~= native Claude + <1s). BUG B was a symptom of
BUG A; no separate fix. (bin was already current with fast mode.)

## Seal

- UKDL T-KCLAUDE-LAUNCH-CONTEXT-001 + SCS C48 addendum v3.
- Profile kClaude already exists + sorts correctly (0b55d6a); no settings edit.

## Owner visual gate

Reload Cursor, click kClaude -> a NEW claude session (not the prior one), prompt
< 3s. /restart -> resumes the same session. "Last session" -> resumes with CO.
