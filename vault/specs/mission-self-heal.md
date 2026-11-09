---
status: SPECIFIED 2026-11-09 (Owner AskUserQuestion "Plan" -> "Aprobar todo"; "Confianza" -> "Sí, solo en lista")
tier: T2
covers: [mission-self-heal, phantom-dirty-align, launch-preflight-trust, launch-preflight-mcp, liveness-incident-notify]
owner: tools/gsd_mission.py (align_cwd, launch_worker, _note_liveness_incident) · tools/mission_remedies.py
---

# A stalled mission repairs the causes it can prove safe, and tells the Owner about the rest within one sweep

## Incidents (measured, KobiiCraft survivalsmp-spawn on GEX44, 2026-11-08/09)
1. m-df9b41d13eb3: 3 launches refused "Workspace not trusted" -> HALTED "3 launches never acknowledged". 0 tokens spent.
2. m-9444639a3c78 epoch 1-3: host "open this session to continue setup". Cause: the clone's `.mcp.json` server `codex`
   points at a Windows `.exe`; its approval dialog blocked every headless start.
3. m-9444639a3c78 epoch 4 and 5: `launch_held_cwd behind_dirty`, 21 h and then 3 h 20 min. The only "dirty" path is a
   blob committed `-text` while `.gitattributes` says `text eol=lf`; git re-normalises it on every read, so
   `status --porcelain` is never empty and `merge --ff-only` was never tried. The path is not touched by the work.
In all three the sweep DETECTED the condition (`launch_failed`, SETUP_HOLD, `liveness_incident`) and nothing acted or
told anyone. Detection exists; repair and notification do not.

## Change (extends the sweep and the launch path; no second loop, no second daemon)
1. **Phantom-dirty alignment** (`align_cwd`). When the cwd is a behind ancestor and dirty, compute the dirty tracked
   paths. If (a) `git diff --quiet --ignore-cr-at-eol -- <paths>` is clean (the differences are line endings only) AND
   (b) `git diff --quiet <cwd_head> <work_dir_head> -- <paths>` is clean (the fast-forward does not touch them), run
   `merge --ff-only` and return `fast_forwarded` with `phantom=[paths]`. Any real content change keeps `behind_dirty`.
   Nothing can be lost: the paths are left exactly as they are.
2. **Launch preflight** (`mission_remedies.preflight(rec)`, called in `launch_worker` before the host launch):
   - **Trust**: if `hasTrustDialogAccepted` is not true for the exact cwd AND the cwd is under a root listed in the
     HOST-LOCAL file `~/.claude/state/mission-self-heal.json` `trust_roots` (missing file / empty list = never), set it.
     Merge-preserving atomic write of `$CLAUDE_CONFIG_DIR/.claude.json` (default `~/.claude.json`), read back, ledger
     `remedy_applied kind=trust`. Outside the roots: nothing written, ledger `remedy_refused kind=trust`.
   - **MCP**: for each `.mcp.json` server in the cwd not already in the project's enabled/disabled lists, if its
     `command` resolves neither as an existing path nor on PATH, add it to `disabledMcpjsonServers` (rejecting, the
     safe direction). A server that DOES resolve is never approved: ledger `remedy_refused kind=mcp` + notify.
   - Never raises; any error is ledgered `remedy_error` and the launch proceeds as today.
3. **Incident notification**: `_note_liveness_incident` (already once per condition key) also calls
   `mission_topup.notify` with mission id, cwd and the condition, and ledgers `incident_notified` with the channel
   result ("no channel configured" is recorded, never silent). Latency = one sweep pass (5 min).
4. Kill switch `CPP_MISSION_SELF_HEAL=off`: all three revert to today's behaviour.

Never in scope (Owner classes): approving a runnable MCP server, trusting a path outside `trust_roots`, authority or
budget, live/staging writes, deleting anything, committing in the mission's repo, re-arming a HALTED mission.

## Acceptance (tools/test_mission_self_heal.py)
- V-MSH-PHANTOM: repo with a `-text` CRLF blob under `text eol=lf`, cwd behind work_dir -> `fast_forwarded`, phantom
  path listed, cwd HEAD == work_dir HEAD, file bytes unchanged.
- V-MSH-REAL-DIRTY (negative): a real content edit on the same setup -> `behind_dirty`, HEAD unchanged, edit intact.
- V-MSH-PHANTOM-TOUCHED (negative): phantom path also changed between the heads -> `behind_dirty`.
- V-MSH-TRUST: cwd under a root -> flag true, every other key of `.claude.json` preserved byte-equal as JSON.
- V-MSH-TRUST-OUTSIDE (negative): cwd outside roots, and roots file absent -> file unchanged, `remedy_refused`.
- V-MSH-MCP: unresolvable command -> disabled; resolvable command -> untouched + refused row.
- V-MSH-NOTIFY: a new incident key -> exactly one notify call; same key again -> none.
- V-MSH-OFF: kill switch -> none of the above happens.
- Field (GEX44): remove the manual skip-worktree on the phantom file; the next relay fast-forwards on its own.

## Rollback
Kill switch, or revert the commit. The host-local roots file is the only state; deleting it disables trust repair.

## As built (2026-11-09) and review (pp-code-reviewer: APPROVE, 0 CRITICAL / 0 HIGH / 4 MEDIUM / 3 LOW, all fixed)
- M1 phantom set: `-c core.quotePath=false diff --name-only -z`, must EQUAL `status --porcelain -z` (staged changes
  included), index AND worktree checked, `--literal-pathspecs`, and every path must exist as a file. The test for M1
  caught a second cause: gsd_mission's git runner decodes with the locale (cp1252 turned `café.md` into `cafÃ©.md`),
  and a pathspec matching nothing makes `diff --quiet` exit 0. The existence check closes both.
- M2 `.claude.json` lost update: the write is abandoned and redone if the file's mtime/size moved before the replace.
- M3 only stdio servers with a literal `command` are candidates; URL servers and `${...}` commands are never rejected.
- M4 a failed/unconfigured channel is ledgered `incident_notify_failed` and retried on later passes, at most 3 times;
  `_note_liveness_incident` now calls the notifier on every pass while the condition holds (delivery dedups).
- L3 empty and filesystem-root entries in `trust_roots` are ignored.
- Gates: tools/test_mission_self_heal.py 18/18; test_gsd_mission 242/242, cwd_align 18/18, liveness_incident 7/7.
