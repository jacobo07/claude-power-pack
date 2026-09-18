---
covers: [cpp-gsd-long, gsd-long-run-v2, gsd-autorun-ledger, gsd-long-run-sweep, resume-validation]
date: 2026-09-18
tier: T2
extends: vault/specs/gsd-autonomous-autocompact.md, vault/specs/autocompact-per-session-flags.md
---

# /cpp-gsd-long v2 -- a resume loop that checks itself

Before v2 the loop was "press Enter and trust it". Measured on this host
(`~/.claude/hooks/auto-compact-daemon.log`): 68 Enters sent, 22 daemon exits
with a flag still waiting, 2 triggers discarded, and no record anywhere of
whether any resume actually resumed.

## Gaps closed

| # | gap | change |
|---|-----|--------|
| 1 | no outcome record | `~/.claude/state/gsd-autorun-ledger.jsonl`: armed, crossing, resume_requested, resume_dispatched, resume_confirmed, refused, halted, stalled, recovered, finished, reaped |
| 2 | a stalled run never recovers | `tools/gsd_long_run.py sweep` every 5 min (Task Scheduler, wscript, hidden): respawns the daemon for waiting flags; re-drops a flag when the transcript ends on the resume line and nothing is waiting; records stalls |
| 3 | Enter submits whatever the box holds | flags carry `transcript` + `expect_line` / `expect_prefix`; the daemon sends only when the last assistant message's last line matches; a flag still mismatched after 180 s becomes `auto-compact-refused-<sid>.flag` |
| 5 | e2e never proven | `gsd_long_run.py report --session <sid>` derives the verdict from the ledger: PROVEN needs >= 2 crossings each followed by a confirmed resume |
| 6 | wrong project | arming refuses unless the session's own cwd (first `cwd` in its transcript) equals `--cwd` |
| 7 | mission checked once | re-checked at every resume; STALE/UNREADABLE halts the run and clears the marker |
| 8 | GSD may see 0 phases | for `/gsd-autonomous`, arming asks `gsd-tools query init.manager`; refuses on 0 incomplete phases or when GSD cannot be asked |
| 9 | manual cleanup | sweep clears markers whose milestone is `all_complete` (finished) or whose transcript is gone / idle > 48 h (reaped), then restores the project config when no marker still uses it |
| 10 | stale text | tier-2 message names the per-session pending flag |
| 11 | no budget | marker `max_cycles` (12) / `max_hours` (24); exceeding either halts at the next resume |
| 12 | no RAM check | resume under 1500 MB free tells the agent to run `gsd_long_run.py wait-ram` (bounded) before emitting the line |
| 13 | backup inside config.json | backup moved to `~/.claude/state/gsd-long-run-backups/<sha1(project)>.json`; an embedded backup is migrated on apply/restore |

## Not done, deliberately

- **4 headless resume** (`claude -p --resume <sid>`): the interactive pane still
  owns that session; a second process appending to the same transcript is two
  writers on one log with no lock. Rejected until Claude Code offers a
  supported attach/submit channel.
- **5 live proof** is produced by the ledger on the next real run; it cannot be
  claimed from tests, which must never dispatch a real compaction.

## Outcomes are distinct

Refusal to arm (exit 2, `REFUSED: <reason>`), halt (run stopped by budget or
mission, marker cleared, ledger `halted`), refused dispatch (text mismatch,
ledger `refused`), stall (no transcript activity, ledger `stalled`). "Could
not ask GSD" is its own reason, never folded into "0 phases".

## Acceptance
`tools/test_gsd_long_run.py` (V-GSDLR-*), `tools/test_autocompact_per_session.py`,
`tools/test_gsd_autocompact.py` all green; mutation drills on budget halt,
mission halt, cwd refusal, phase refusal, expect-line validation.

## Rollback
Revert the commits; restore hooks from `~/.claude/hooks/_bak_autocompact_20260918/`;
`schtasks /delete /tn PP-GsdLongRun-Sweep /f`.
