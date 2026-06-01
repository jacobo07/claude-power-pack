# Cold-Boot Evidence -- Compact 1-Click Helper

**Date:** 2026-06-01T12:40:00Z
**Build:** BL-COMPACT-001 follow-up (apex-v13-compatible helper)
**Owner choice:** "Mantengo apex v13 + agrego helper Owner"
**Result:** STRICT PASS (10/10 V-gates + verify_spp probe row green)

## Owner-decision context

When the BL-COMPACT-001 follow-up plan proposed `--auto-rescue-after 90s`,
plan-time audit flagged a direct contradiction with apex v13
(sealed 10 minutes earlier in the same session): "NEVER auto-kill,
Owner-trigger only" was the canonical doctrine the new plan
violated. Three doctrinal options were presented:

1. Reverse apex v13 (auto-rescue OK)
2. Keep apex v13 + add low-friction Owner helper  <-- chosen
3. Execute plan literally, document contradictions in parallel

The Owner chose option 2. This work implements that choice.

## What changed

The change is purely additive and opt-in. The legacy passive
(OK-only popup) detector flow is unchanged and remains the
default. A new `--interactive` opt-in flag swaps the popup for a
`YesNoCancel` MessageBox:

- **Yes** -> spawn `tools/compact_rescue.ps1 -IdleThresholdSeconds 0`
  (guard-bypassed because the detector already confirmed `.jsonl`
  idle >= 5 min AND the Owner explicitly authorised by clicking).
- **No** -> write `~/.claude/state/compact_snooze_until.txt`
  with epoch + 60 s; subsequent `check_once()` returns early
  while snoozed.
- **Cancel / popup timeout** (300 s) -> no action.

The kill still requires explicit Owner consent at the moment
the alert fires. No-click paths (`--auto-rescue-after N`,
scheduled auto-kill) remain forbidden by apex v13.

## Empirical timeline

| Step | Tool | Outcome |
|---|---|---|
| Pre-execute | Plan-time architectural audit | flagged contradiction; surfaced 3 options to Owner |
| Owner decision | AskUserQuestion | "Mantengo apex v13 + agrego helper Owner" |
| M1 | `tools/compact_hang_detector.py` rewrite | argparse adopted, interactive mode added, magic-number cleanup per Jobs hook -- committed `38b51ce` |
| M2 | `tools/test_compact_rescue.py` +3 V-gates | 10/10 PASS -- committed `a57e46d` |
| M3 | apex v13 + UKDL PR-COMPACT-001a | doctrinal compatibility doc -- committed `1d2528c` |
| M4 | `vault/test-results/cold_boot_COMPACT_HELPER_*.md` | this file; final test run 10/10 + verify_spp probe STRICT PASS in 9.20s |

## V-gate detail (final cold-run)

```
COMPACT RESCUE TEST -- BL-COMPACT-001
================================================================
  PASS  V-COMPACT-RESCUE-EXISTS       (6919 bytes)
  PASS  V-COMPACT-CMD-EXISTS          (3709 bytes)
  PASS  V-COMPACT-DETECTOR-EXISTS     (14964 bytes)
  PASS  V-COMPACT-DRYRUN              (rc=0, log_advanced=True, json_well_formed=True)
  PASS  V-COMPACT-GUARD-ACTIVE        (rc=1 expected 1, abort_msg_present=True)
  PASS  V-COMPACT-UKDL-PR             (PR+T+BL markers present)
  PASS  V-COMPACT-INTERACTIVE-FLAG    (rc=0, OK_in_stdout=True)
  PASS  V-COMPACT-SNOOZE-CLEAR        (rc=0, existed=True, gone_after=True)
  PASS  V-COMPACT-DASH-COMPAT         (rc=0, OK_present=True)
  PASS  V-BASELINE-INTACT             (modules.pp_agents.signals.health: OK; proactive_core: OK)

RESULT: 10 PASS / 0 FAIL (10 total)
```

## verify_spp probe row

```
[OK  ] compact-resilience     rc=0     9.20s
  total elapsed: 9.20s
  STRICT PASS -- 1 of 1 rows OK
```

## Owner activation (one-shot)

```powershell
# Mirror the slash command to the global commands dir:
Copy-Item `
  "$env:USERPROFILE\.claude\skills\claude-power-pack\commands\compact-rescue.md" `
  "$env:USERPROFILE\.claude\commands\compact-rescue.md"

# Install the detector in INTERACTIVE mode (1-click rescue):
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" `
  install --interactive

# Or in legacy PASSIVE mode (OK-only popup, manual /compact-rescue afterward):
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" `
  install

# Verify state:
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" `
  status

# To uninstall:
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" `
  uninstall
```

## Doctrinal note (recorded for future builders)

The temptation to add `--auto-rescue-after N` recurs every time
a hang is hit. The empirical rejection lives in
`knowledge_vault/core/apex-completion-standard.md` axis v13 under
"Why Owner-trigger, never auto-kill":

- The hang signal is heuristic; matches a long-thinking Owner
  with a large transcript as readily as a stuck session.
- The cost of a false-positive kill is the entire current turn
  (worst-case mid-Edit). The cost of a false-negative is bounded
  by Owner patience. Asymmetric -- favour the conservative path.
- State-tracking ("90 consecutive seconds of heuristic stable")
  does NOT eliminate the false-positive surface; it just delays
  detection of false-positives.

The 1-click MessageBox is the minimum-friction Owner-decision
path. Anything cheaper (auto, scheduled, timer) crosses into
auto-kill territory that v13 forbids.

## Commit ladder (scoped, NO git add -A)

```
38b51ce  feat(compact): interactive 1-click helper for hang detector
a57e46d  test(compact): 3 new V-gates for interactive helper (10/10)
1d2528c  docs(compact): interactive helper sanctioned under apex v13
<M4>     docs(compact): cold-boot evidence COMPACT_HELPER_2026-06-01
```

## Non-regression note

This work touched only the files listed above (`detector.py`,
`test_compact_rescue.py`, `apex-completion-standard.md`,
`ukdl-universal.md`, this evidence doc). No mutation to
`~/.claude/settings.json`, `~/.claude/commands/`, or
`~/.claude/hooks/`. The Owner-side install step is documented
above, not auto-executed.
