# Handoff [J] -- non-convergence detection -> mission supervisor owner

Pillar: [J] non-convergence detection. Terminal: DEFERRED_STRONGER_OWNER.

Owner (frozen): `tools/gsd_mission.py`.

## Result handed over (measurement: `vault/programs/cognitive-economy/evidence/H-J-turn-advancement.md`)

- Frozen rule: "non-advancing turns of interactive roots >= 3 % of D-W7 earns a detector proposal". Pre-registered
  input: HUMAN-rooted recovery + repeat + non_convergent turns, weighted. Measured: **3.51 %** of D-W7
  (recovery 3.10, non_convergent 0.31, repeat 0.10). The rule fires.
- All roots: recovery 5.80 %, repeat 0.78 %, non_convergent 0.48 % = 7.06 %; non-HUMAN roots (missions,
  continuations, others) ~3.55 %.
- Classifier agreement with blind labels 87.5 % (shuffled control 45 %); no disagreement touches these three classes.

## Detector proposal (the owner decides whether and how)

1. **Scope the progress fingerprint to the mission's own work (audit G5).** `progress_fingerprint`
   (`tools/gsd_mission.py:1649-1671`) hashes HEAD, whole-tree porcelain and the diff of the work dir. In a shared
   checkout any peer's churn changes it, so the no_progress halt (`:1553-1563`) cannot fire for a stalled mission.
   Candidate inputs that a peer cannot move: commits whose author/committer session is the mission's, or the
   mission's own branch tip when it runs in its own worktree.
2. **Count recovery, not only tree change.** 88 % of the measured non-convergent share is recovery (a turn reacting
   to an errored tool result). A detector that sees N consecutive recovery turns without an intervening edit or
   green test is what the data supports; a repeat-only detector would cover 0.41 of 3.51 points.
3. The share that fires the rule is HUMAN-rooted, which this owner does not supervise. If the owner adopts (2) for
   missions, the interactive half needs a different host (a Stop-chain advisory, for instance), owned elsewhere.

## What the owner keeps

`tools/gsd_mission.py`, the no_progress rule, `NO_PROGRESS_EPOCHS`, and the decision whether to build any of the
above. Nothing edited by the campaign.
