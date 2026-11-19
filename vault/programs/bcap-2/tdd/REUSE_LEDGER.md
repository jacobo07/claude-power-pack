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

## Phase 2 outcome (PARTIALLY_PROVEN) — 2026-11-19

Built: `classify_slice` + `mutation_outcome` in `modules/uqf/principles/tdd_workflow.py` (P07 heuristic kept, now labelled `HEURISTIC_ONLY`);
stage facts map to `strength_ladder` keys (`assertions_observed`, `failure_branch_driven`, `regression_case_pinned`, `integration_boundary_exercised`);
TDD evidence alone caps at ADVERSARIALLY-VERIFIED (it supplies no production facts). Mutation = existing `tools/test_gaps.py`, driven for real (KILLED / SURVIVED / base-red UNMEASURABLE).
Routing: `tdd` intent domain + one latent card (`python3 -m modules.uqf.principles.tdd_workflow <record.json>`, also the first real caller of P07 and a verdict-coded CLI).
Gate: `BCAP2_TDD_PYTHON=<py with pytest,pytest-cov,coverage> python3 tools/test_bcap2_tdd.py` -> 65 PASS / 0 FAIL (14 backlog fixtures + variants, routing both poles, real slice 96b6f09a through git archive). Without that env the mutation poles fail loudly (55/1), never silently pass. Negative-control drill: disabling the post-hoc check turned F02 and CLI red; file restored byte-identical. Phase 1 gate still 37/0. Liveness offenders 56 -> 56.

Residuals (why not PROVEN):
- R1 Nothing emits `classify_slice` records live: no hook/executor captures RED runs; the card is a pointer, so C2 provenance is only as good as the record's author (done-gate items 3, 10 not proven live).
- R2 Not wired into `intent-verify` / done_gate callers (item 5, 10); ladder mapping is a library call.
- R3 Upstream mattpocock/skills/tdd never fetched (no pin/licence) — read-only fetch still owed. `verification-loop`, `auto-test`, `intent-verify` scanned only by name.
- R4 Mutation is Python/pytest only; other languages are an explicit ceiling (`MUTATION_UNSUPPORTED_LANGUAGE`).
- R5 No A/B benchmark, no runtime-cost measurement, no UKDL promotion (items 9, 11, 12).
- R6 `/usr/bin/python3` on GEX44 lacks pytest; the gate needs a venv (made in the job tmp dir, not committed).
