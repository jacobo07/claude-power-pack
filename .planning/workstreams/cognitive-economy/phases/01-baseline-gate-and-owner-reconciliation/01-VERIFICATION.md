---
phase: 01-baseline-gate-and-owner-reconciliation
status: passed
score: 4/4
verified: 2026-10-03
---

# Phase 1 Verification

| # | Success criterion | Result | Evidence |
|---|---|---|---|
| 1 | gate_baseline.py re-runs usage_index for anchor + D-W7, exact / 0.5 %, exit 0/1, driven red once | PASS | green rc 0, red rc 1 (2 perturbed lines failed), tolerance control rc 0 -- `evidence/A-prg.md` |
| 2 | I, N, O, Q owners verified by reading/running; handoffs name pillar, owner, what owner keeps; O carries G1-G4 | PASS | `handoffs/I.md`, `N.md`, `O.md` (git_state.py:124-142, G1-G4), `Q.md` |
| 3 | `--pillar A/I/N/O/Q` each PASS | PASS | fresh-process verifier output in 01-EVIDENCE.md |
| 4 | PRG for A: gate run from a fresh process, stdout pasted | PASS | `evidence/A-prg.md`, cited by the ledger with sha256 |

Goal-backward check: pillar A is IMPLEMENTED_AND_VERIFIED through a gate the done-gate will re-run (L5), and
I/N/O/Q are closed by handoffs that landed after the freeze (verifier L4 `handoff_landed`), not by assertion.
