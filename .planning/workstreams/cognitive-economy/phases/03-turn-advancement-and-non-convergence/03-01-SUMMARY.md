---
phase: 03-turn-advancement-and-non-convergence
plan: 01
status: complete
commits: [8f7b6caf, f25799a7, 4b59dc5e]
requirements: [CE-H, CE-J]
---

# Plan 03-01 Summary

- `measure/turns.py` classifies all 75,969 D-W7 calls (population == D-W7 calls) into the seven classes or
  UNSETTLED by written rules; advancing 12.53 %, bookkeeping 12.93 %, recovery 5.80 %, unsettled 51.97 % of D-W7
  weighted. `tools/root_progress.py` imported in-process, never edited.
- Controls: 40 blind hand labels, agreement 0.875 against a shuffled-label negative control of 0.45.
- H: `gates/gate_turns.py` re-runs the classifier on the frozen 3,000-row sample and checks the labels sha256;
  red under `--perturb-order`. IMPLEMENTED_AND_VERIFIED.
- J: decided from H by its frozen rule -- HUMAN-rooted recovery + repeat + non_convergent = 3.51 % >= 3 %, so a
  detector proposal goes to `tools/gsd_mission.py`'s owner (`handoffs/J.md`), with the audit G5 finding (Ralph
  no_progress fingerprints the whole work dir). DEFERRED_STRONGER_OWNER.
- Epoch 2 fix: a repo whose `git log` fails or times out labels its edits `edit_unknown` (UNSETTLED), not
  `edit_uncommitted`.
- SUMMARY written by epoch 4 (2026-10-03): the phase closed in the ledger in epoch 2/3 without this GSD artifact.
  Content is taken from `03-EVIDENCE.md` and `evidence/H-J-turn-advancement.md`; verifier re-run in epoch 4.
