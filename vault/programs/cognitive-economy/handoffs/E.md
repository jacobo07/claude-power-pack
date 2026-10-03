# Handoff [E] -- fresh-epoch economics -> epoch rotation owner

Pillar: [E] fresh-epoch economics. Terminal: MERGED_INTO_EXISTING_OWNER.

Owners (frozen): `vault/specs/parent-context-epoch-rotation.md`, `vault/specs/interactive-context-rollover.md`.

## Result handed over (measurement: `vault/programs/cognitive-economy/evidence/D-E-context-lifetime.md`)

- Census (`python tools/gsd_epoch.py census`, all-time): 613 fresh worker sessions, 61 CONTEXT_ROTATION,
  437 TURN_CONTINUATION, 50 same-session continuations, rotation triggers wall 39 / economic_ceiling 11.
- D-W7 mission rotations: 52 (49 measured). Rehydration 0.9063 % of D-W7; carried context avoided <= 3.3177 %;
  net **[-0.91 %, +2.41 %]**.
- Ceiling for ANY threshold change: rotating earlier is worth <= 2.7839 % of D-W7 (net of the cheapest measured
  rehydration, so an upper bound); rotating later is worth <= 0.9063 %. Both are below the frozen 3 % materiality,
  so **no threshold change is proposed**. The current wall/economic thresholds stay as the owner set them.
- Interactive rollover (the second owner spec): 127 crossings in the window, median 458 k -> 128 k context, 2.13 %
  rehydration. Handed over as data; the same counterfactual caveat applies (see [D]).

## Note for the owner

48 of the 540 epochs started in D-W7 have no transcript under `~/.claude/projects`. 45 name a session that made
0 indexed calls in the window, and 3 have no session at all, so they sit outside the denominator. They are mostly
1-turn TURN_CONTINUATION epochs of `m-0353288ab95c` and `m-2dd5f3aeb143`: launches recorded as acknowledged that
produced no model call here. Worth a look if the census is ever used as a cost denominator.

## What the owner keeps

Rotation causes, thresholds, `tools/gsd_epoch.py`, `tools/gsd_mission.py`, `tools/rollover.py`. Nothing edited.
