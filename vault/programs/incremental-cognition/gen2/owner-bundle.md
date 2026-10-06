# IC-gen2 autonomous-optimization -- Owner bundle

One line per item that needs an Owner action. The mission never asks mid-run (ROADMAP operating constraints); it records the
action here and continues with other phases. An item stays open until the action lands, unless its line says
AUTHORIZATION_BOUND.

Run plane: GEX44 worktree `.claude/worktrees/ao-gen2` of `~/missions/autonomous-optimization`, branch
`mission/autonomous-optimization-gen2` (never pushed; fetch it back).

Pillar letters in this file belong to the IC-gen2 programme (autonomous-optimization); the same letters in the CE and IC
gen1 ledgers are different pillars.

| # | pillar | source | action | exact command | what closes when it lands |
|---|---|---|---|---|---|
| 1 | [P0] (IC-gen2) | OPP-001; D-OQ2 | On the laptop, where floor 5962571c exists, compute the floor's stable patch-id and send it back | `git show 5962571c840943ae0a3aa901efb08e69a04434da | git patch-id --stable` | the value lets a follow-up commit add a stored floor patch-id so a no -x pick is accepted on hosts without the floor object; status PLANNED, not built in Phase 0 |
