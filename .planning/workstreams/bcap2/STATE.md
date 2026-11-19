# STATE: bcap2

status: ARMING 2026-11-19 on GEX44 (Owner "continua esa mision de absorcion hasta terminarlo todo"; vehicle BCAP-2 GEX44)
current_phase: 3 (phases 1-2 PARTIALLY_PROVEN)
authority: 120M processed tokens + 3 x 40M top-ups (only with commits outside .planning/ since the last grant)
base: laptop feature/knowledge-acquisition committed HEAD at arm (the commit that adds this file)

## Phase log
(empty — the worker appends one section per phase: gate, measured numbers, spend, 5-line meta-analysis)

### Phase 1 CPP-DBG-001: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_dbg.py` exit 0, 37 PASS / 0 FAIL (20 adversarial fixtures + real bug 96b6f09a red->green). Liveness offenders 56->56.
spend: ~3.4M processed tokens (`mission_spend session-tree`, transcript ea6857df, incl. context re-reads); ceiling 14M.
meta-analysis:
1. The backlog assumed a CRAIF causal engine; the code says diagnosis is not CRAIF's role. Scanning first avoided building on a false premise.
2. Built a record verifier (extend CRAIF), not an engine; honest cost: nothing yet emits records live (R2).
3. Upstream skill was never fetched (R1); do it read-only before closing.
4. Hook-blocked `git stash drop` taught: use a WIP commit, not stash, for baselines in this shared repo.
5. Next: Phase 2 TDD shares fix.* fields with this verifier; wire done_gate there (R4).

### Phase 2 CPP-TDD-001: PARTIALLY_PROVEN
gate: `BCAP2_TDD_PYTHON=<venv py> python3 tools/test_bcap2_tdd.py` exit 0, 65 PASS / 0 FAIL (14 backlog fixtures + variants, real test_gaps mutation poles, routing, real slice 96b6f09a, CLI). Phase 1 gate 37/0. Liveness offenders 56->56.
spend: ~2.4M processed tokens this session (`mission_spend session-tree`, def2ee92, main only); ceiling 12M.
meta-analysis:
1. P07's file-presence check was the whole premise gap; keeping it as HEURISTIC_ONLY beside an evidence classifier avoided replacing a live registry entry.
2. No new verdict enum: stage facts map to strength_ladder keys, and the honest ceiling is ADVERSARIALLY-VERIFIED because TDD evidence supplies no production facts.
3. The mutator was reused unchanged; running it for real needed pytest+pytest-cov, absent on GEX44, so the gate fails loudly without BCAP2_TDD_PYTHON instead of skipping.
4. Nothing emits records live (R1) and done_gate/intent-verify do not consume them (R2): the card is a pointer; same weakness as Phase 1.
5. Next: Phase 3 AGSK (no dependency). Owed read-only upstream fetches (DBG R1, TDD R3) batch into one network step.
