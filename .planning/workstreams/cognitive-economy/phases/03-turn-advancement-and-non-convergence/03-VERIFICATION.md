---
phase: 03-turn-advancement-and-non-convergence
status: passed
score: 4/4
verified: 2026-10-03
---

# Phase 3 Verification

Re-verified by epoch 4 from a fresh process: `python tools/test_cognitive_economy_program.py --pillar H` ->
`CEP_PILLAR_H=PASS` (re-runs `gates/gate_turns.py`), `--pillar J` -> `CEP_PILLAR_J=PASS`, `--final` ->
`CEP_VERDICT=PASS failures=0`.

| # | Success criterion | Result | Evidence |
|---|---|---|---|
| 1 | Campaign script over usage_index + root_progress (imported, never edited) joined to git classifies D-W7 turns into seven classes with written rules; turns per commit / green test per root; UNSETTLED separate | PASS | `measure/turns.py`; `evidence/H-J-turn-advancement.md` (rules, per-root table, unsettled 51.97 % kept apart) |
| 2 | >= 30 hand-labelled turns with agreement; shuffled-label negative control | PASS | 40 labels, agreement 0.875 vs shuffled 0.45 (`H-J-turn-advancement.md:63-64`) |
| 3 | H closes only via a gate re-running the classifier on a frozen sample with an output hash; J by its frozen rule from H | PASS | `gates/gate_turns.py` labels_sha256 match, red under `--perturb-order`; J 3.51 % >= 3 % -> handoff |
| 4 | Any optimization H suggests judged by the 3 % rule: handoff or rejected with the number | PASS | J detector proposal in `handoffs/J.md` (3.51 %); no edit of `tools/gsd_mission.py` |
