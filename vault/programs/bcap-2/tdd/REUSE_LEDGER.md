# BCAP-2 Phase 2 — CPP-TDD-001 Reality Scan (SCAN ONLY, no implementation yet) — 2026-11-19, base e591f666

| Owner | Observed | Decision (proposed) |
|---|---|---|
| `modules/uqf/principles/tdd_workflow.py` (P07) | Presence heuristic only: any test path in the change set passes all sources (fixture 1 passes wrongly). Registered in `modules/uqf/principles/__init__.py:110`. No caller found outside the registry in modules/ or tools/. | EXTEND: keep the heuristic as its own weaker signal (label HEURISTIC_ONLY); add evidence-aware classification beside it. |
| `tools/test_gaps.py` | Verdicts SURVIVED / UNMEASURABLE / TIMEOUT already exist (lines 10, 163, 237). Python/pytest only. | REUSE as the mutation oracle (C5). Never write a second mutator. Add KILLED/ERROR/NOT_RUN mapping only if absent. |
| `modules/done_gate/strength_ladder.py` | 13-rung ladder, three-valued evidence (True/False/absent -> UNDETERMINED). Requirement keys include `assertions_observed`, `failure_branch_driven`, `regression_case_pinned`. | CONNECT: map RED_VERIFIED/GREEN_VERIFIED/BEHAVIOR_VERIFIED onto these keys. No new verdict enum (backlog C6). |
| `modules/craif/diagnosis.py` (Phase 1) | `fix.regression_seam`, `fix.mutation_detects`, `fix.original_path_rerun` already carry the shared regression seam. | CONNECT: the TDD evidence record feeds the same `fix.*` fields. |
| `skills/verification-loop`, `commands/auto-test.md`, `intent-verify` | Not yet read. | Scan next. |
| Upstream mattpocock/skills/tdd | Not fetched: no pin, no licence. | Do read-only fetch + record licence before any adaptation. |

## Next exact steps
1. Gate `tools/test_bcap2_tdd.py` with the 14 fixtures of the backlog as poles (fixture 1: one test file + several sources must NOT certify).
2. Add `classify_slice(record)` next to P07 (C1 APPLICABLE/CONDITIONAL/NOT_APPLICABLE/UNRESOLVED; C2 red-reason + revision-bound provenance; C4 oracle independence; C5 outcome vocabulary; C6 map to strength_ladder keys).
3. Route applicable coding prompts to a latent card (extend `diagnose`-style synthetic card in `modules/skill_router/skill_index.py`).
4. One real slice red->green via git archive, as in `tools/test_bcap2_dbg.py::test_real_bug`.
5. Liveness check, backlog Status + `deferred-backlog.md` row, STATE.md spend + 5-line analysis, commit.
