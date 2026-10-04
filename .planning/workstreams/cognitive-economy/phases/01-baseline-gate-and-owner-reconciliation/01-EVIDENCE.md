# Phase 1 Evidence: Baseline gate and owner reconciliation

Commit: `21671d6c` on `cognitive-economy/autonomous-run` (worktree `.claude/worktrees/cognitive-economy`).

## Pillar results

| Pillar | Terminal | Proof |
|---|---|---|
| A | IMPLEMENTED_AND_VERIFIED | `gates/gate_baseline.py` green rc 0, red drill rc 1, tolerance control rc 0 (`evidence/A-prg.md`) |
| I | MERGED_INTO_EXISTING_OWNER | brief.py 20/20 (V-BRIEF-*), gsd_mission.py 213/213 (`handoffs/I.md`) |
| N | MERGED_INTO_EXISTING_OWNER | both sweeps registered, rc 0 at 16:10/16:11, heartbeats complete (`handoffs/N.md`) |
| O | MERGED_INTO_EXISTING_OWNER | spine live; G1-G4 tree-pin finding handed over with file:line (`handoffs/O.md`) |
| Q | MERGED_INTO_EXISTING_OWNER | `state.<P>.capital` contract (`handoffs/Q.md`) |

## Verifier output (fresh processes, after commit 21671d6c)

command: `python tools/test_cognitive_economy_program.py --pillar <P>`

```
CEP_PILLAR_A=PASS
CEP_PILLAR_I=PASS
CEP_PILLAR_N=PASS
CEP_PILLAR_O=PASS
CEP_PILLAR_Q=PASS
```

`--status`: closed A I N O Q, open 15, violations [].

## Red drill (success criterion 1)

`gate_baseline.py --perturb anchor.calls=23926 --perturb D-W7.cache_read=21000000000` -> rc 1,
`GATE_BASELINE=FAIL failures=2`, each perturbed line FAIL and every untouched line ok. Full output in
`vault/programs/cognitive-economy/evidence/A-prg.md`.

## Product Delta

- A re-runnable baseline gate now exists: any later "the economy improved" claim can be checked against a frozen
  before-snapshot that the gate proves still reproduces (it did, at 0.0000 % drift).
- `ledger_write.py`: one writer for `state.<P>` that computes the sha256 pins, so no pin is typed by hand.

## Intelligence Delta

- The usage index reproduces a closed past window byte-exactly across runs (anchor and D-W7, all six raw fields),
  so the frozen denominators are a stable instrument and not a moving target.
- The five "already owned" pillars needed zero new code: the cost of closing them was verification, not
  construction. The capability already existed for all four of I, N, O, Q.
- Running the mission in its own worktree (forced by the harness) is the audit's own G2(a)/G5 fix; the plan's
  rejection of a worktree (s10) was about a different mission's cwd-alignment hold.
