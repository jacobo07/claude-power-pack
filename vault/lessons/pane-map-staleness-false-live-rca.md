# Pane Map Staleness + False-LIVE RCA (2026-07-06)

Sealed SCS C79. Origin: Cursor crash -> reopened to Cursor Agents home ->
`pane_map.md` was 8 days stale -> "lost panes with no fast recovery".

## Symptom
- `~/.claude/state/pane_map.md` header: `Generated 2026-06-28` (8 days old) on 2026-07-06.
- Owner reported many TUA-X LIVE panes missing from the map and needing urgent recovery.

## Root cause A -- staleness (T-PANE-MAP-STALENESS-ROOT-CAUSE-001)
`build_pane_map.ps1` was invoked ONLY by the Cursor extension
(`extension/src/extension.js`, `restore_guard.js`). There was NO scheduled task
and NO Stop/SessionStart hook regenerating it. `pp-snapshot-writer` (every 15 min)
writes `session_snapshot.json` only, not the pane_map. So whenever the extension
was not driving refreshes (crash, `.vsix` inactive) the map went stale
indefinitely. `schtasks /query | findstr pane` returned nothing -- the script was
built but the auto-update task was never registered.

## Root cause B -- false-LIVE by mtime (T-PANE-MAP-FALSE-LIVE-MTIME-001)
Regenerating produced 30 "LIVE" panes. The prompt itself expected ~11. Forensics:
- `session_snapshot.json` (authoritative open-tab registry) held only 2 tabs.
- 35 transcripts shared ONE file-mtime spike ~11 min ago (a batch sweep).
- Per-file INTERNAL last-message timestamp (content, not metadata) proved only
  1 pane was genuinely live (this session, internal age 0.1 min). The other 34
  had real last turns 14h-7d old (830 min .. 10106 min) while their file mtime
  was ~11 min. A metadata-only touch (heartbeat merger / backup / git / AV)
  forged mtime-based liveness.

`build_pane_map.ps1` classified `live` by file mtime:
`$isLive = $inSnap -or ($ageMin -le $LiveMinutes)`. The `$ageMin` clause is the
corruption vector: any en-masse mtime touch floods the map with false-LIVE.

## Fix
1. `build_pane_map.ps1` -- new `Get-LastInternalAgeMin` reads a bounded transcript
   tail, takes the NEWEST internal `"timestamp"` record, and liveness becomes
   `$isLive = $inSnap -or ($internalAgeMin -le $LiveMinutes)`. Immune to
   mtime-touch. Re-run: 30 LIVE -> 3 LIVE (truth).
2. `PP-PaneMapUpdate` scheduled task: `/sc minute /mo 5 /it` -- regenerates every
   5 min while logged on. Verified enabled + runnable. (Onlogon sibling needs
   elevation; the minute task covers post-logon within 5 min regardless.)
3. Cursor `settings.json` already correct: `workbench.startupEditor: none`,
   `window.restoreWindows: all`. The Agents-home-on-crash was ungraceful
   shutdown (power loss), NOT a config gap -- no edit needed.

## HR
HR-PANE-MAP-FRESHNESS-001 (canonical `vault/hard_rules/HARD_RULES.md`).

## SCS C79 -- PaneMap-Freshness-Active
build_pane_map.ps1 liveness classified by internal timestamp (not mtime);
PP-PaneMapUpdate task regenerates every 5 min; Cursor startupEditor:none
confirmed. Crash -> map fresh < 5 min, LIVE flag trustworthy.

## Restore doctrine (do NOT auto-mass-spawn)
Disk truth disproved "38 live panes to recover". Auto-opening 38 `claude --resume`
terminals on a mtime-forged signal would flood the workspace with stale sessions.
Restore is Owner-decided: reopen the genuinely-active pane(s) (recent INTERNAL
timestamp) + reopen workspace windows on request. Consistent with
HR-STALLED-SESSION-ADVISORY-001 (never act autonomously on a stale/ambiguous
session signal).
