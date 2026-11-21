# BCAP-2 Phase 1 — CPP-DBG-001 REUSE / EXTEND / CONNECT / DECLINE ledger

Reality Scan at 73c7f32c (2026-11-19, GEX44). Verdict: **PARTIALLY_PROVEN** (not CLOSED, see residuals).

| Owner | Finding (observed) | Decision |
|---|---|---|
| `modules/craif/` | Code is the liveness repair transaction only; `candidate.py` states "diagnosis is explicitly not CRAIF's role". `BOUNDARY_CONTRACT.md` nevertheless names CRAIF owner of causal candidates, evidence, closure. **The backlog's premise (a CRAIF causal engine exists) is false in code.** | EXTEND: `modules/craif/diagnosis.py`, a verifier of an investigation *record* (DBG-C01..C08). Not an engine, not a ledger. |
| `modules/osr/` | Aligns executions, first divergence; hands off to CRAIF. | REUSE as-is; record field `divergence` consumes its position; never a cause (fixture 5). |
| `skills/instrument-before-claim` | Doctrine for negative controls / red-capable instruments. | REUSE; C02 negative-control + exact-oracle checks encode it. |
| `skills/agent-introspection-debugging` | Agent self-failure only. | DECLINE as owner; unchanged. |
| `modules/skill_router` + `tools/jit_skill_loader.py` | Intent→latent card routing, spec/frontend only. | EXTEND: `diagnose` domain + one synthetic card (pointer only, never always-on). |
| `modules/done_gate`, test-gaps, mutation | Completion authority / regression. | CONNECT by record fields (`fix.mutation_detects`, `original_path_rerun`); wiring into done_gate deferred to Phase 2 (shared seam). |
| Separate `diagnosing-bugs` skill / Debugging OS | — | DECLINE (backlog forbids). |
| Upstream skills.sh mattpocock/diagnosing-bugs | **Not fetched** this session: no pinned commit, no licence recorded. Concepts implemented from the backlog's own six-phase summary only. | RESIDUAL R1 (no code or text copied). |

## Evidence (exit-0, GEX44)
- `python3 tools/test_bcap2_dbg.py` → `BCAP2_DBG_PASS: 37 PASS, 0 FAIL`: positive control, all 20 adversarial fixtures rejected with their named code, honest NOT_REPRODUCED/UNMEASURED states, flake maths (1% → 299 clean runs), 5 routing cases both ways.
- Real bug (criterion 3): 96b6f09a S177M `<path>@<sha>` hold read as a path. Parent commit returns the whole string (exact wrong output, not a crash), fix returns the path, plain-path control identical at both. Run through `git archive` into a temp dir.
- Existing suites unchanged: test_sleepy_skills 9/9, test_spec_driven 15/15, test_craif 15/15, test_sdd_os exit 0.
- Liveness: 504→505 modules, REACHABLE 336→337, gate offenders 56→56 (standing debt, no new orphan).

## Residuals (why not CLOSED, plan law 4)
- R1 CLOSED: pin + licence + read recorded in `dbg/MATTPOCOCK_READ.md` (mattpocock/skills @ abeeaf95, MIT); campaign B Phase 1 confirmed no further upstream row is open.
- R2 verifier judges a record; nothing yet *produces* records during a live debug. No hook writes one; criteria 5, 6, 8, 11 are enforced on records, not observed in a live investigation.
- R3 criterion 12 (matched benchmark vs baseline) and 14 (fresh session diagnoses unaided) unmeasured; need paid/live model runs.
- R4 not wired into `done_gate` / CEPS promotion (Phase 2 seam); fixture 19 only refuses at the record level.
- R5 ledger row not moved to ACTIVATED; routing proven by classifier calls, not a live UserPromptSubmit session.
