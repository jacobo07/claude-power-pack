# Cold-Boot Evidence -- Compact 95% Hang Recovery

**Date:** 2026-06-01T09:50:00Z
**Build:** BL-COMPACT-001 (Owner-approved plan inline, executed M0-M7)
**Result:** STRICT PASS (7/7 V-gates + verify_spp probe row + commit ladder green)

## Empirical timeline

| Step | Tool | Outcome |
|---|---|---|
| Preflight | `git fetch origin` + `git log -3` | clean on `main`, HEAD=82b94ab, no behind/ahead |
| PASO 0 diag | Owner clarification | hang specifically at 95% (post-API local, not network) |
| PASO 0 diag | grep vault for prior precedent | NONE -- first cycle to seal this bug |
| PASO 0 diag | `Get-Process claude` headcount | 40 alive procs, top-3 RSS = 451/373/352 MB |
| PASO 0 diag | daemon log `~/.claude/cache/auto-compact.log` | 15 OK / 2 TTL-only -- daemon not source |
| **Architecture decision** | Owner-approved plan inline | rescue Owner-triggered, never auto-kill; detector alert-only opt-in |
| M0 | `vault/knowledge_base/compact-95-hang-repro.md` (4 KB) | committed `de33020` |
| M1 | `tools/compact_rescue.ps1` (6919 B, ASCII) | DryRun PASS (captured THIS session's sid, no kill) -- committed `21f5804` |
| M2 | `commands/compact-rescue.md` (3709 B) | file present, format matches `pre-compact.md` pattern -- committed `642705b` |
| M3 | `tools/compact_hang_detector.py` (7758 B) | `--check` returns "OK: no compact hang detected" cleanly -- committed `ca6a2b2` |
| M4 | `vault/knowledge_base/ukdl-universal.md` (+78 lines) | PR-COMPACT-001 + T-COMPACT-001 markers present -- committed `5d5949f` |
| M5 | `tools/test_compact_rescue.py` (5 KB, 7 V-gates) | 7/7 PASS -- committed `7b572e2` |
| M6 | `tools/verify_spp.py` (+1 row) + apex v13 + Anthropic issue | `--row compact-resilience` STRICT PASS 1/1 in 5.31s -- committed `75f3cd8` |
| M7 | `vault/test-results/cold_boot_COMPACT_*.md` (this file) | cold-boot run: 7/7 PASS + verify_spp 1/1 PASS in 4.17s |

## V-gate detail (test_compact_rescue.py final run)

```
================================================================
COMPACT RESCUE TEST -- BL-COMPACT-001
================================================================
  PASS  V-COMPACT-RESCUE-EXISTS    (6919 bytes)
  PASS  V-COMPACT-CMD-EXISTS       (3709 bytes)
  PASS  V-COMPACT-DETECTOR-EXISTS  (7758 bytes)
  PASS  V-COMPACT-DRYRUN           (rc=0, log_advanced=True, json_well_formed=True)
  PASS  V-COMPACT-GUARD-ACTIVE     (rc=1 expected 1, abort_msg_present=True)
  PASS  V-COMPACT-UKDL-PR          (PR+T+BL markers present)
  PASS  V-BASELINE-INTACT          (modules.pp_agents.signals.health: OK; proactive_core: OK)

RESULT: 7 PASS / 0 FAIL (7 total)
```

## verify_spp probe row

```
[OK  ] compact-resilience     rc=0     4.17s
  total elapsed: 4.17s
  STRICT PASS -- 1 of 1 rows OK
```

## DryRun real evidence (M1 done-gate)

The rescue script captured THIS very session's UUID during M1
dry-run verification (confirming the sessionId extraction path
works against a live `.jsonl` header):

```json
{
    "timestamp":  "2026-06-01T09:43:22.7882072Z",
    "target_pid":  26936,
    "rss_mb":  416.2,
    "session_id":  "d15b2df3-74c9-4b17-866f-c529885d8c24",
    "cwd":  "C:\\Users\\User\\.claude\\skills\\claude-power-pack",
    "rescue_reason":  "compact_95_hang",
    "idle_seconds":  2,
    "jsonl_newest":  "C:\\Users\\User\\.claude\\projects\\C--Users-User--claude-skills-claude-power-pack\\d15b2df3-74c9-4b17-866f-c529885d8c24.jsonl"
}
```

## Guard active evidence

With default `IdleThresholdSeconds=120`, the rescue MUST abort
on an active session. Verified empirically:

```
[ABORT] Session looks active -- .jsonl written 2s ago.
        Wait 118s more, or override with:
        powershell -File tools\compact_rescue.ps1 -IdleThresholdSeconds 0
```

This is the protect-active-session contract working as designed.
The `V-COMPACT-GUARD-ACTIVE` gate codifies this as a regression
catcher: any future change that weakens the guard will fail the
gate.

## Owner activation (one-shot, post-push)

```powershell
# Mirror the slash command to the global ~/.claude/commands dir
# so /compact-rescue is invocable from any session:
Copy-Item `
  "$env:USERPROFILE\.claude\skills\claude-power-pack\commands\compact-rescue.md" `
  "$env:USERPROFILE\.claude\commands\compact-rescue.md"

# (Optional) Install the alert-only detector as a scheduled task
# checking every 60 seconds. NEVER kills -- only alerts.
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" --install

# Verify install:
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" --status
# Expected: "Detector task: Ready" (or similar non-empty state).

# To uninstall the detector later:
python "$env:USERPROFILE\.claude\skills\claude-power-pack\tools\compact_hang_detector.py" --uninstall
```

## Commit ladder (scoped, NO git add -A)

```
de33020  docs(compact): compact-95-hang-repro empirical doc
21f5804  feat(compact): compact_rescue.ps1 Owner-triggered rescue
642705b  feat(compact): /compact-rescue slash command
ca6a2b2  feat(compact): compact_hang_detector.py alert-only watchdog
5d5949f  docs(ukdl): PR-COMPACT-001 + T-COMPACT-001 compact hang governance
7b572e2  test(compact): 7/7 V-COMPACT-* rescue gates
75f3cd8  feat(compact): verify_spp probe + apex v13 + Anthropic issue body
<M7>     docs(compact): cold-boot evidence COMPACT_2026-06-01
```

Sibling-pane commit `6c21169 perf(session-start)` landed
between M1 and M2 from a parallel Claude Code pane. Pathspec
scoping protected each Mx commit from sibling contamination --
verified per-commit with `git show --stat`: every Mx commit
touches exactly its scoped file(s).

## Non-regression note

This work touched only the files listed above. No mutation to
`~/.claude/settings.json`, `~/.claude/commands/`, or
`~/.claude/hooks/`. The Owner-side mirror step
(`Copy-Item commands/compact-rescue.md $env:USERPROFILE\.claude\commands\`)
is documented but not auto-executed -- consistent with
"auto-mode denies self-modification" doctrine
(`memory/feedback_automode_denies_self_modification.md`).

verify_spp baseline pre-existing STRICT FAILs are NOT
regressions caused by this work; they pre-date BL-COMPACT-001
and are documented in the existing umbrella output.

## Reach (honest)

The rescue does NOT fix the underlying `claude.exe` hang. It
gives the Owner a clean escape in <30 seconds. The actual fix
must land upstream in `claude.exe`. The Anthropic issue body
is drafted at
`vault/knowledge_base/anthropic-issue-compact-95.md` -- Owner
files it when ready.
