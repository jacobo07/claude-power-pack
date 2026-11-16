# HANDOFF (interim, campaign 1 PARTIALLY PROVEN: phases 1-2 of 6 done)

Branch `mission/ascension-run` in `~/missions/ascension/.claude/worktrees/ascension`. Nothing pushed. Commits: 03c95cee (P1), dc154a52 (parked label), 695b0032 (P2).

## Owner summary
- Phase 1: 620 raw records -> 471 obligation identities, discovered not curated; an independent census caught a real omission (nested RESUMPTION files) and it is fixed. Real tree has 0 true duplicates (collapse proven on fixtures).
- Phase 2: reconciliation 372/471 (0.79); operational 0/373, because no execution evidence exists yet. `gsd_mission status` now shows held missions as `PARKED:*` in `display_state` (RED->GREEN).
- Seeds: Taste Skill REFERENCED_ELSEWHERE, ASTRYX NOT_OBSERVED, Design Index referenced in code. All three are laptop steps 1-2 in LAPTOP_STEPS.md. They are UNKNOWN, not available.

## Engineering handoff
- Re-run gates: `python3 tools/test_asc_inventory.py`, `python3 tools/test_asc_ledger.py`, `python3 tools/test_gsd_mission_parked_label.py` (all exit 0).
- Artifacts: vault/programs/ascension/phase1/obligation_inventory.json, phase2/reconciliation_ledger.json (regenerate with `python3 -m modules.backlog_autopilot.{inventory,ledger} --verify --out ...`).
- Ledger caveats: ACTIVATED is STATIC wiring only; license UNKNOWN on every row; CLAIM_REJECTED recall is low on real data (1).
- Phase 3 toolchain facts (probed): system python3 has NO playwright. A Chromium binary exists at /home/kobii/.cache/ms-playwright/chromium-1223/chrome-linux64/chrome . Use it directly (`--headless=new --no-sandbox --dump-dom|--screenshot`) with an in-page self-check script for the interaction check. Execution evidence for the ledger goes to vault/programs/ascension/phase2/execution_evidence.json as {OBL-id: {exit:0, cmd:...}}; Phase 3 should produce the first entries.
- Phase 3 owners to reuse: modules/capability_runtime/applicability.py (evaluate, compile_stack), modules/cdio/{scorer,componentry_catalog,motion_patterns,legal_surface}.py, design-md experience contract. Spend not yet measured (tools/mission_spend.py needs a session id).
- Next: Phase 3 (web vertical slice, 12 mandatory cases, one done_gate command), then 4, 5, 6. Pending liveness: run `python modules/liveness/reachability.py` in Phase 6 for inventory.py and ledger.py (both are CLI/library modules under backlog_autopilot, likely need a LIBRARY declaration).
