# Handoff [I] -- one-shot work packet -> existing owners

Pillar: [I] one-shot work packet. Terminal: MERGED_INTO_EXISTING_OWNER (frozen rule: "exists (epoch brief +
Ralph card); no build").

Owners (frozen): `modules/gsd_x/goal/brief.py`, `tools/gsd_mission.py`.

## What was verified (2026-10-03, worktree `cognitive-economy/autonomous-run` at 8b62b6ce)

- `modules/gsd_x/goal/brief.py:48` `compile_brief(...)` builds the epoch packet from durable goal state only:
  Founder's verbatim intent, open obligations, undispositioned failures, boundaries; 16 KB cap that refuses
  rather than truncates (`BRIEF_MAX_BYTES`, line 35).
  Run: `python tools/test_gsd_x_goal_claude_providers.py` -> `GSDX_CLAUDE_PROVIDERS_PASS=20/20`, including
  V-BRIEF-VERBATIM-INTENT, V-BRIEF-OPEN-GAPS, V-BRIEF-FAILURES, V-BRIEF-BOUNDARIES, V-BRIEF-DETERMINISTIC.
- `tools/gsd_mission.py:882` `render_card(rec, git_facts, gsd_facts)` is the Ralph per-epoch card.
  Run: `python tools/test_gsd_mission.py` -> `MC_PASS=213/213`.
- This very campaign runs on that packet (mission `m-fdefb0fca0c0`, epoch 1 in this session).

## What the owner keeps

Everything: the brief format, the card, their size caps and tests. The campaign builds nothing for [I].

## Note for the owner (no action required)

The packet is only as fresh as the cwd it is rendered in; `tools/gsd_mission.py:1583` `align_cwd` already
guards that. This campaign worked in a dedicated worktree (audit G2(a)/G5 fix), so its successors depend on
that fast-forward path.
