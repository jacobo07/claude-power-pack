# [L] Compile-out of compound steps 7+8 -- PRG

Frozen rule: steps 7+8 owned by a NEW campaign module (never `tools/compound_unattended.py`, never
`hook-dispatcher.js`) with mutex, backup, atomic rename and rollback, proven by its own gate against a TEMP copy of
the state and real learning files; the live apply and the call-site switch are Owner items (audit G6).

## What was built

- `vault/programs/cognitive-economy/compound/steps78.py` -- `finalize(state, project, marker)`: mkdir mutex
  `<state>.lock` (stale after 30 s, gives up after 5 s with nothing written), byte backup `<state>.bak`, MERGE of the
  project entry (`{**old, last_run_iso, directive_count: 0}`), sibling tmp + fsync + `os.replace`, marker unlink;
  any unlink failure other than ENOENT restores the backup bytes (rollback); the mutex is always released.
- JSON keys stay case-sensitive. The live state holds one pair of project ids that differ only by case
  (`C--Users-...KobiiCraft-Core-Files` / `c--Users-...`); PowerShell `ConvertFrom-Json` refuses that file outright
  ("claves ... duplicadas", observed 2026-10-03 in this run). Python keeps both; the gate targets that pair.
- `vault/programs/cognitive-economy/gates/gate_compound78.py` -- the gate.

## Gate run (fresh process, worktree `cognitive-economy/autonomous-run`)

command: `python vault/programs/cognitive-economy/gates/gate_compound78.py`

```
  real inputs: 224 learning files, marker 357 bytes
  learning files newer than the advanced cursor (would be re-gathered): 0
  ok   advance
  ok   no_marker
  ok   rollback
  ok   busy
  ok   stale
  ok   live_intact
  target project 'C--Users-User-Desktop-Cursor-Projects-Minecraft-Projects-KobiiCraft-Workspace-KobiiCraft-Core-Files'; case-variant id pairs in live state: 1
GATE_COMPOUND78=PASS failures=0
```

Red drill: `--break-rollback` (the restore write becomes a no-op) -> `FAIL rollback`, `GATE_COMPOUND78=FAIL
failures=1`, exit 1. `live_intact` held in both runs: the live state's sha256 was identical before and after.

## Not part of this terminal (Owner bundle, `[L]`)

Applying `finalize` to the live `~/.claude/state/compound-learnings.json` and switching the call site (the
`/cpp-compound` command body and `tools/compound_unattended.py`) to call it.

## Product Delta / Intelligence Delta

- Product: the step that stalls `/cpp-compound` is now a tested function instead of six prose instructions.
- Intelligence: any PowerShell-side reader of the state file fails on the case-variant key pair (observed in this
  run). An earlier session recorded the same pair as a reason the loop sticks at steps 7+8 (project memory
  `project_compound_loop_sticks_at_steps_7_and_8.md`); its share of the 14x "STUCK" counter was not measured here.

Displacement: not applicable until the Owner switches the call site. Saving: none claimed (unknown).
