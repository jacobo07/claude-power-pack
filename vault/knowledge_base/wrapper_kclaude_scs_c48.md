# SCS C48 -- kclaude wrapper (W1-W7 complete)

**Sealed:** 2026-06-23. Domain: launch wrapper / session continuity / TCO.
**Lineage:** consumes SCS C53 (TCO ground truth) for W5; reuses the W2
transcript-on-disk anchor (UKDL T-WRAPPER-TRANSCRIPT-ANCHOR-001) for W3/W4.

## Standard

`kclaude` wraps `claude` with fail-open pre-launch intelligence and absorbs the
old kclaude.bat /restart loop. Invariants:

1. **Fail-open absolute.** Every feature (W1-W5) returns silence/None on any
   error; `prelaunch.py` defaults every field; `kclaude.ps1` runs with
   `$ErrorActionPreference='Continue'`. claude ALWAYS launches.
2. **One pre-launch process.** W1+W4+W5+W2 run in a single `prelaunch.py`
   invocation, CONCURRENTLY, each with an individual timeout (W1=1.0s, W4=0.5s,
   W5=0.5s, W2=1.0s). Wall-time = the longest single timeout (~1s), never the
   sum -> measured launch overhead ~1.6s < 2s.
3. **W2 auto-resume happy path.** With no concurrent active pane,
   `cd <repo> ; kclaude` resumes that repo's latest transcript session with NO
   prompt. Anchor = transcript .jsonl on disk only (a pane_map sid whose .jsonl
   is gone is never resumed).
4. **W4 coordinator guard.** A second pane on a cwd with an active (<2h)
   session -> warning + default S (resume). `n` -> new session; numeric -> pick.
5. **W3 fast naming.** A NEW session is named from session_snapshot.json (the
   FAST source, seconds) -- NOT the transcript (~1-2 min lag) and NOT
   build_pane_map (disk-truth, needs the transcript). Writes a durable
   `wrapper_session_names.json` + a marked fast-path block in pane_map.md that
   bridges until build_pane_map regenerates.
6. **W5 cost gate = context, not money.** Claude Max => $0 marginal/token. Daily
   burn is read ONLY from transcripts via `token_ground_truth.today_output_tokens`
   (SCS C53; UKDL T-WRAPPER-W5-SOURCE-001) -- never budget_monitor (programmatic
   credits) or TIS (injection). Best-effort within its timeout; silent if it
   cannot compute in time (never a fake number).
7. **/restart preserved.** kclaude.ps1 absorbs the MC-LAZ-26 resume loop: on a
   restart flag it relaunches `--resume <sid>` (lazarus SID file) else
   `--continue`, in the same terminal. The old kclaude.bat is backed up
   (`.superseded`), never deleted.

## Done evidence (2026-06-23)

- modules/wrapper/: turn_counter (W1), auto_resumer (W2, +list_candidates),
  session_namer (W3), repo_coordinator (W4), cost_gate (W5), prelaunch (W6 core).
- tools/kclaude.ps1 (W6 orchestrator + /restart loop), tools/install_wrapper.ps1
  (W7); installed to ~/.claude/bin, USER PATH prepended; `where kclaude` ->
  `~/.claude/bin/kclaude.cmd`; `kclaude -h` prints usage.
- tools/test_wrapper.py -- 15/15 x3 hermetic (W1-W5 + fail-open).
- Overhead measured ~1.6s < 2s (prelaunch on a real cwd with transcripts).

## What this did NOT change

- build_pane_map.ps1 untouched (disk-truth regenerator; W3 bridges, never fights).
- budget_monitor / TIS untouched (wrong source for W5; documented).
- old ~/.claude/kclaude.bat preserved as a .superseded backup in ~/.claude/bin.

## Addendum v2 (2026-07-01) -- startup < 3s + silent single-session + /restart via kclaude

Invariant #2 (one pre-launch process, ~1.6s) proved too slow in practice: W5
cost_gate scans the whole transcript corpus (17-27s), the 1s timeout silently
dropped its advisory, and under GIL/cold-cache the blank reached ~15s. Three
fixes (T-KCLAUDE-STARTUP-BLANK-001, T-W4-DIALOG-SINGLE-SESSION-001,
HR-RESTART-VIA-KCLAUDE-001):

1. **Fast/advisories split.** `prelaunch.py --mode fast` runs ONLY the
   launch-critical bundle (W2 resume + W4 coordinate + CO-08 gate + CO-00
   advisory). The slow bundle (W1 turn + W5 cost + parallel_burn) runs detached
   via `--mode advisories`, writing `~/.claude/cache/kclaude_advisories.json`
   that the next launch prints instantly. Measured time-to-launch 333ms (<3s).
2. **Silent single-session (supersedes invariant #4's always-prompt).** One
   active session -> auto-resume, no dialog. Only multiple active sessions show
   a numbered list (3s timed default to most recent). `-n/--new` forces a fresh
   session; explicit `--resume/--continue` honored verbatim.
3. **/restart via kclaude.** The restart loop re-runs the fast CO gates so
   CO-00/CO-08 are active post-restart; restart-claude.ps1's clipboard targets
   the live bin/kclaude.ps1 (fail-open to bare claude).

**Live copy:** the Cursor kClaude profile runs `~/.claude/bin/kclaude.ps1` (byte
mirror of `tools/kclaude.ps1`). Every kclaude.ps1 edit MUST be mirrored to bin;
prelaunch.py is read live from the skills path (no mirror).

**Evidence:** tools/test_wrapper.py 21/21 x3 hermetic; tools/test_restart_and_lag.py
17/17 x3; tools/test_cognitive_os_build.py 68/68 (no regression on prelaunch.run).
