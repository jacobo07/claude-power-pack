# Backlog — Parallel Mesh deferred systems (2026-07-01)

Owner ruled at STOP #1 (Q-B): build the **5 NEW** datasets (PM-01…PM-05), defer the rest.
Recorded here so the deferral is honest and scheduled, not dropped (per the "no classified
FAILs at done-gate" doctrine).

## Deferred — reason per item

| System | Why deferred | Real home when built |
|---|---|---|
| **Cognitive Compiler** | EXTEND, near-COVERED. `one_shot/compiler.py` (`compile_contract`) + CO-03 route + `spec_gate.classify_tier` already compile objective→scope→budget→plan. Only worth a dataset if it *orchestrates* those into one pre-reasoning compile step beyond what exists. | EXTEND section on CO-03, or a thin PM-06+ that chains existing compilers. |
| **Deterministic Replacement Engine** | EXTEND, near-COVERED. CO-03's cascade already has a **"deterministic" rung** (Vault→asset→deterministic→Haiku→Sonnet→Opus). The genuinely-new part is a *tracking/promotion layer* (what has been determinisified, tokens saved). | EXTEND section on CO-03 + a CO-01 savings ledger row. |
| **Cross Project Learning Network** | EXTEND, borderline-NEW. Primitives exist but scattered: `vault/knowledge_base/` (global), `token-optimizer/cross_project_dedup.py` (rule dedup), `autoresearch/cross_signal_bus.py` (cross-project keywords), CEPS project→global promotion. The new value is a *unified local→global promotion protocol*. Defensible as a standalone **PM-06** later. | **PM-06** if pursued: unify the promotion protocol over the existing four primitives. |
| **Cognitive Portfolio Manager** | **COVERED by CO-01.** CO-01 *is* "Operating Economics & Cognitive Capital"; ROI Scoring is already folded into CO-01 (INDEX line 86). The one non-CO-01 mechanic — *cross-pane* budget arbitration — was kept and shipped in **PM-04**. No standalone dataset needed. | Not a dataset. Cross-pane mechanic lives in PM-04; the rest is CO-01. |

## Follow-up builds these datasets imply (EXECUTION mode, Owner-authorized)

1. **CO-08 `scheduler.py` recalibration** (from PM-02 §I.3, Owner Q-A = Recalibrate): relax
   `SAME_REPO_CAP` so a same-repo pane passing the PM-02 scope-check is admitted; undeclared panes
   keep the blunt cap. This is a *code* change to a sealed live module — its own tested + committed
   EXECUTION step, gated by the standard done-gates (`test_cognitive_os_build.py` must stay green).
2. **PM-01…PM-05 live implementation** — if/when the architecture is to become code (the C61→C62
   pattern): a `modules/parallel_mesh/` built in bounded anti-burn waves, each tested + committed +
   pushed, with a `tools/test_parallel_mesh_build.py` done-gate. Not in scope for this seal (this
   seal is the architecture only, mirroring SCS C61).

## Priority note

None of the deferred items is a P0. The CO-08 recalibration code change (follow-up #1) is the
highest-value next step because it is what makes the mesh's founding promise *enforced* rather than
*documented* — but it touches a sealed live module, so it is a deliberate, gated EXECUTION task, not
an auto-continue.
