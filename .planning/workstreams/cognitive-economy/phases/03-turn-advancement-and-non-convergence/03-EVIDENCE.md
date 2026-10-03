# Phase 3 Evidence: Turn advancement and non-convergence

Full measurement: `vault/programs/cognitive-economy/evidence/H-J-turn-advancement.md`. Handoff: `handoffs/J.md`.

| Pillar | Terminal | Key number (D-W7) |
|---|---|---|
| H | IMPLEMENTED_AND_VERIFIED | 75,969 / 75,969 calls classified; advancing 12.53 %, bookkeeping 12.93 %, recovery 5.80 %, unsettled 51.97 %; gate PASS, red under `--perturb-order` |
| J | DEFERRED_STRONGER_OWNER | HUMAN-rooted recovery+repeat+non_convergent 3.51 % >= 3 % -> detector proposal to `tools/gsd_mission.py` |

Verifier: `CEP_PILLAR_H=PASS`, `CEP_PILLAR_J=PASS`.

Controls: population == D-W7 calls (75,969); blind labels 40, agreement 0.875 vs shuffled 0.45; G5 verified at
`tools/gsd_mission.py:1649-1671`.

## Product Delta

- A re-runnable, zero-model-call turn taxonomy for any window of the usage index (`measure/turns.py`), with a hash
  gate, a blind-label sheet generator and a scorer.
- `tools/gsd_mission.py`'s owner holds a measured proposal instead of an audit note.

## Intelligence Delta

- Half of all weighted spend (51.97 %) is exploration/execution whose value is not observable from transcripts plus
  git; that is the honest ceiling of what a turn taxonomy can judge.
- Recovery (a turn after an errored tool result) is the largest non-advancing class, 5.80 % of D-W7; repeat and
  uncommitted churn together are 1.26 %. Non-convergence here is mostly error handling, not looping.
- Median 27.6 turns per commit and 45.7 per green test across the 40 costliest roots.
- Measurement trap found and fixed before it shipped: `root_progress._commits` has a 60 s timeout and ignores the
  exit code, so a large repo (orca, 9,841 refs) returned an empty history and every edit there would have been
  counted as non-convergent. Here a failed log is UNSETTLED and is reported per repo (0 in this run).
