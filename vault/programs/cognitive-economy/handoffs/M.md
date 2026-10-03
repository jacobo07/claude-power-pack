# Handoff [M] -- model / processor allocation -> cognitive control plane owner

Pillar: [M] model / processor allocation. Terminal: DEFERRED_STRONGER_OWNER.

Owners (frozen): `vault/plans/cognitive-control-plane-2026-10-02.md` (C4 owns model policy), `modules/cost_collapse/`.

Frozen rule: "CCP C4 owns model policy; any routing experiment spends quota and needs Owner".

## Decision

The campaign ran no routing experiment and changed no model policy: an experiment spends quota, and the mission's
spend authorization covers its own measurement work only. Model choice belongs to CCP C4 and `modules/cost_collapse/`.

## Facts the campaign measured that the owner can use (all on D-W7 weighted)

- Turn taxonomy (`evidence/H-J-turn-advancement.md`): bookkeeping 12.93 %, coordination 9.38 %, recovery 5.80 %,
  proof 6.13 % (whole-turn weights). These are the classes a routing policy would consider moving to a cheaper model;
  their whole-turn weight is dominated by the carried prefix, which a model switch does not shrink, so any routing
  saving has to be measured on output and fresh input, not on these totals.
- Verification's own cost (`evidence/F-G-P-C-carriage.md`) is 0.50 %: routing test runs is not material.

## What the owner keeps

Model policy, `modules/cost_collapse/`, routing experiments and their quota. Nothing edited by the campaign.
