# Restore uses LIVE+RESUMABLE (all tiers), not LIVE-only — 2026-07-06

Sealed as an addendum to the pane-map restore line (SCS C78 add-v3 / C79).

## Owner premise (partially corrected)
Request: "restore ALL sessions from the pane_map, not just the 11 the agent
detected as LIVE; do NOT regenerate — regeneration loses sessions (e.g.
InfinityOps 6 LIVE)."

## What is actually true
- **The accurate goal is met by restoring all tiers.** `restore_panes.ps1`
  without `-LiveOnly` already restores every LIVE **and** RESUMABLE pane in the
  map — 49 sessions across 6 repos, InfinityOps (7) included. LIVE-only (11) was
  the under-restore; all-tiers is the fix. No code change needed — drop the flag.
- **Regeneration does NOT lose recent sessions.** RESUMABLE keeps every session
  whose transcript was touched within OldHours (48h). The fresh map had all 49.
  "InfinityOps 6 LIVE" in the Owner's memory was the OLD map's **mtime-forged
  false-LIVE** (fixed by the internal-timestamp classifier, T-PANE-MAP-FALSE-
  LIVE-MTIME-001); those 7 InfinityOps sessions are now correctly tagged
  `[recent]` but are STILL restored under all-tiers.
- **Genuine aging-out is by design, not a bug.** Sessions with no transcript in
  the last 48h (e.g. moneymaker-skill, CursorProjects from a days-old map) drop
  out of the regenerated map. Restoring 8-day-old sessions is rarely the intent,
  and they were not "open at crash". If truly wanted, raise `OldHours` or resume
  their transcripts directly — a deliberate choice, not an auto-restore default.

## T-RESTORE-ALL-TIERS-NOT-LIVE-ONLY-001 (supersedes the literal request T-RESTORE-USE-EXISTING-PANE-MAP-001)
Post-crash restore drives from the pane_map's LIVE **and** RESUMABLE tiers (all
sessions with a transcript in the window), not LIVE-only. "Don't regenerate" is
NOT the lesson — regeneration is what makes LIVE accurate; the correct lesson is
restore-all-tiers. The map is complete for the last 48h; anything older aged out
by design and is an explicit, not automatic, restore.

## Safety note (RAM)
49 `folderOpen` auto-tasks means one window-open can spawn all its panes (TUA-X
= 22 `claude.exe`). Given the documented claude.exe OOM history (~25 GB), all 49
were ARMED but `task.allowAutomaticTasks` was set back to `off` so they do not
mass-spawn. Restore heavy repos in waves.
