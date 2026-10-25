# Unit U2 — W3 review debt in gsd_mission.py (MEDIUM-1, LOW-1, LOW-3)

Repo: C:\Users\User\.claude\skills\claude-power-pack (a git worktree on its own branch; the path is rewritten below).
Use PowerShell; git is `& 'C:\Program Files\Git\cmd\git.exe'` (not on PATH). Python is
`C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`.

## Background
pp-code-reviewer on 08a441b7..a378414b (Tranche A W3, merged b664f978) left three findings in this unit's scope:
- MEDIUM-1: `gain_samples` (MARGINAL_GAIN_LOW input, `tools/gsd_mission.py` ~5797 `_gain_sample`, persisted via the
  `gain_samples=` kwarg of the launch helper ~1290/1377, passed at ~5960) is persisted only through `launch_worker`.
  On same-session continue, readmit or capsule rotation the samples are lost, so MARGINAL_GAIN_LOW is blind on the
  dominant relay path.
- LOW-1: a `relay_held` ledger row is appended on every pass while a mission stays held (~5786 / ~5804). The cwd hold
  already has a change-guard (see ~5666: "52 identical relay_held in 4.7 h"); the gain hold needs the same.
- LOW-3: `tools/test_w3_marginal_gain.py` check `V-W3C-MUTATION-RED` (~line 71) never reruns the gates on the
  mutant; it only proves the judge function changes.

## Task
1. Read the code around the lines above (Grep first; read only what you need). Confirm each finding is real today, or
   record it as NOT REPRODUCED with the evidence, and skip it.
2. MEDIUM-1: make `gain_samples` survive every path that rewrites the mission record after a relay (continue,
   readmit, capsule rotation), with the smallest change; prefer one shared persistence point over three copies.
   Test: a red-then-green check in `tools/test_w3_marginal_gain.py` that drives at least one non-launch_worker path
   and asserts the samples are still present afterwards (fails on the old code: show it).
3. LOW-1: append `relay_held` for the gain hold only when its reason/samples changed since the last row (same
   pattern as the cwd hold). Test: two identical held passes -> one row; a changed sample -> a second row.
4. LOW-3: make `V-W3C-MUTATION-RED` run the real gate path on the mutant (not only the judge), and still restore.
5. Never edit any hook, CLAUDE.md, agent catalog or MEMORY.md. Touch only gsd_mission.py and the test file(s).

## Done
- `python tools/test_w3_marginal_gain.py`, `python tools/test_w3_live_spend_card.py`,
  `python tools/test_w3_stage_authority.py` exit 0.
- Commit with a pathspec (only files you changed): `git commit -m "<msg>" -- <files>`.
- Receipt `vault/programs/factory-tranche-b/U2-receipt.md`: per finding REPRODUCED/NOT REPRODUCED with evidence, what
  you changed, the red output on old code, test output lines, and `COMMITS: <hash>` reachable from HEAD.
