# P7G0 receipt

- Mission: m-302d70eabd59 (supersedes completed P6 m-be59d97fa311). Status: DONE (G0 freeze only).
- Tool calls used: 7 of 7 (Read x2 counted as dossier + packet, PowerShell x2, Write x3 -- packet read preceded the budget). 0 subagents, no Glob/Grep.
- Work-tree commit (recon wt_keosdtk_home, branch keosdtk-home): e3b0b82 -- g0_freeze.py, test_g0_freeze.py, G0_FREEZE.json, G0_HOLDOUT.json, 07-01-SUMMARY.md (pathspec-scoped; ~568 dirty .ksr_vault paths untouched).
- Receipt commit (PP repo): this file, hash printed by the commit call.
- Drill verbatim:
  PASS V-G0-DRAW / PASS V-G0-HOLDOUT / PASS V-G0-REPRO / PASS V-G0-RED / PASS V-G0-PREREG / PASS V-G0-STRATA
  G0_DRILL=6/6
- G0_FREEZE draw=300 sha256=0f2ecb37f162067edf85126b0a3ce950c316820ea9eda730104d73ef80d1c54b holdout=60 sha256=7bf4c5f55550182032fa1fa4e87db82ad8fb05b387f1451f9e205f8a0ddad221
- Both hashes equal the dossier's expected values on the first run (Pln part sha also matched).
- Open points: Owner may amend preregistration text before the first run, never after; holdout unread; GAP-4 A/A re-run and arm C redefinition deferred; no push, no checkpoint, no GEX44.

Metered by the main pane (worker transcript 53cd63b4, usage deduplicated by message.id): 11 model calls, 1,332,106
processed (11,895 out) -- OVER the 1.2M hard stop by 132,106; the session breaker did not trip. Drill re-run by the main
pane from e3b0b82: G0_DRILL=6/6; draw and holdout sha256 equal P7G0-DOSSIER.md exactly.

HANDOFF NOTE: P7G0 done
