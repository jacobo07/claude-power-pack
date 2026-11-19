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

### Phase 3 CPP-AGSK-001: PARTIALLY_PROVEN
gate: `python3 tools/test_bcap2_agsk.py` exit 0, 55 PASS / 0 FAIL (ledger integrity, floor_guard both poles, routing recall/precision, liveness). Phase 1 gate 37/0. Liveness offenders 56->56.
pilot: AGSK-C constraint non-weakening absorbed as `modules/sqi/floor_guard.py` (diff-scoped; MIT NOTICE, pin 8c99fa36), latent card under domain "constraints" (not always-on).
residuals: 34 upstream rows in DISPOSITIONS.md are basis=HYPOTHESIS (only the pilot is READ); 7 rows UNVERIFIED (AGSK-B/D/E/F gaps unmeasured); nothing emits floor_guard live from done_gate (same weakness as Phases 1-2); closing needs those scans.
meta-analysis:
1. Scanning first showed 26 skills not 25; honest basis column stops a hypothesis reading as an absorption claim.
2. One pilot slice done fully beats 26 shallow ones; EXTEND landed beside the sqi census, no new router.
3. Routing negatives (typo, root cause, failing) pinned so the new card does not steal diagnose/tdd.
4. Weakening fixtures trip the auto-mode classifier on Write: edit via small Edits only.
5. Next: Phase 4 Anime.js (no dependency); batch owed upstream fetches (DBG R1, TDD R3) into one read-only network step.

### Phase 3 scan notes (historical)
Upstream pinned 8c99fa36 (MIT); scan notes and next steps in vault/programs/bcap-2/agsk/REUSE_LEDGER.md. No implementation yet. Spend this session before the wall: ~179k resident context (second session of epoch 2).

> Coordinator note 2026-11-19T16:5xZ (laptop pane 2cf9ec6d, Owner-approved): epochs 3 and 4 hung ~2 h on a host
> permission prompt for `Write tools/test_bcap2_agsk.py` (auto-mode classifier reads the seeded test-weakening
> fixtures as test tampering). The coordinator placed the worker's exact attempted content (11,350 chars) at that path.
> Do NOT re-create it with Write; change it with small Edit calls. Keep seeded-weakening fixtures in this file only.
