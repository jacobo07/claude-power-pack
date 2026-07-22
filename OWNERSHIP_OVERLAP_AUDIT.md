# Ownership & Overlap Audit — Phase -1 (CGF proposal)

> Constitutional Governance Fabric (CGF) proposal: "Trasladar gobernanza desde prompts hacia
> infraestructura permanente de Claude Power Pack." This audit is the mandatory blocking gate
> before any line of the CGF is built. Verdict below: **the large majority of the proposal
> already exists under different names.** Objective must shift from creation to
> consolidation/wiring, per the repo's own `PR-DUPLICATE-TO-ADVANTAGE-001` and
> `T-IIC-CIVILIZATION-DUPLICATION-001`.

## Evidence inspected

- `CLAUDE.md` (root, project instructions) — ~20 sealed HR-* Hard Rules, all citing real incidents.
- `SKILLBANK.md` — found **stale**: lists 14 modules; real `modules/` count is ~70 (see below).
- One Explore-agent inventory pass (very-thorough breadth) across `modules/`, `vault/`,
  `governance/`, `hooks/hook-dispatcher.js`, `vault/liveness/reachability_registry.json`.
- Spot-verified independently (not taken on the agent's word alone, per HR-PREMISE-001):
  - `modules/duplicate_to_advantage/d2a_engine.py` — **exists**.
  - `modules/hard_rules/residual.py` — **exists**.
  - `hooks/hook-dispatcher.js` — **exists**; grepped directly — confirms
    `secret_firewall_gate.js` (line 201) and `d2a_gate.js` (line 250) are registered;
    **no match** for `cascade_prevention` in the same file (confirms the agent's UNWIRED claim).
  - `modules/secret_firewall/*.py` — **exists** (detector/redactor/allowlist/reporter).
  - `vault/liveness/reachability_registry.json` — **exists**.
- Checked `vault/plans/CCF_*.md` (acronym-collision risk: CCF vs. CGF) directly — read in full.
  **Ruled out**: CCF = "Creative Contract Fabric," an unrelated brand/image-generation pipeline
  spec. No prior CGF design exists under a confusing name. This is the one lead that could have
  made the whole audit moot; it did not.

## Repo module inventory (real count vs. SKILLBANK's stale 14)

~70 directories under `modules/`, including (not exhaustive): `akos_knowledge`, `ads`,
`agent-governance`, `arch-decision`, `backlog_autopilot`, `backup`, `cascade_prevention`, `cdio`,
`cognitive_os`, `code-review` (hyphen) **and** `code_review` (underscore — see naming-collision
finding), `contract_fabric`, `cost_collapse`, `craif`, `daif`, `dataset_first`, `decision_review`,
`done_gate`, `duplicate_to_advantage`, `error_prevention`, `fable_distillation`,
`frontier_intelligence`, `governance-overlay`, `graphify`, `hard_rules`, `karimo-harness`,
`liveness`, `one_shot`, `output_contracts`, `owner_queue`, `parallel_mesh`, `recall_roi`,
`refcheck`, `rollback`, `rule_compiler`, `sdd_os`, `secret_firewall`, `session_resilience`,
`setup_os`, `skill_router`, `sleepless_qa`, `spec_gate`, `sqi`, `uqf`, `zero-crash`, etc.

**Opportunistic finding (not requested, logged per Opportunity Discovery, not auto-fixed):**
`modules/code-review/` and `modules/code_review/` are two different directories differing only
by hyphen vs. underscore — a real drift risk for anyone routing by name. Flagging for the
Owner; not touched in this audit (out of Phase -1 scope, and a repo-wide rename is its own
blast-radius decision).

## Sealed/protected surfaces (CGF must not touch or duplicate)

- `CLAUDE.md` HR-001…HR-STALLED-SESSION-ADVISORY-001 block — sealed, canonical archive
  `vault/hard_rules/HARD_RULES.md`.
- Liveness Standard (CLAUDE.md, sealed 2026-07-13) — any new module must register in
  `vault/liveness/reachability_registry.json` or be wired; `python modules/liveness/reachability.py`
  is the existing done-gate.
- `modules/hard_rules/residual.py` — sealed doctrine: **Hard Rules cannot conflict, they can only
  jointly shrink the legal-move set.** Directly contradicts the CGF's proposed "Gate Conflict
  Resolution Gate" premise that conflicts need computing. A CGF conflict-resolution mechanism must
  reconcile with this, not re-derive a different model.
- `T-IIC-ORGCHART-IS-NOT-MECHANISM-001` — "naming a layer 'Supreme Court'/'Senate'/'Immune
  System'/'Digital Twin' adds zero mechanism; a dataset ships only if it names an engine, a gate,
  and an evaluator." Applies verbatim to a "Constitutional Governance Fabric" pitch: the name
  itself proves nothing; each of the ~35 named gates must independently justify existing.
- `PR-DUPLICATE-TO-ADVANTAGE-001`, `NON_DUPLICATION_LEDGER.md` + `SYSTEM_REGISTRY.md` — "no IAS
  dataset may re-govern any row above at its own level." The CGF is exactly this kind of
  cross-cutting registry proposal and is bound by the same law.
- DRK-07 (`vault/knowledge_base/decision_review/drk_07_governance_evolution_authority.md`) —
  sealed "propose-never-apply" self-evolution constitution; invariant "no self-mutation is
  autonomous." The CGF's "Governance Evolution Engine" would duplicate this near-verbatim.

## Mechanism-by-mechanism verdict (Groups A–I)

Legend: **REUSE** = exists, use as-is · **EXTEND** = exists, needs a scoped addition ·
**INTEGRATE** = exists in pieces across modules, needs a connecting layer · **CONSOLIDATE** =
2+ existing near-duplicates, pick one · **NEW** = confirmed gap · **WIRING GAP** = mechanism
exists in code but has no live hook/command invoking it (the Liveness Standard's own failure
mode, recurring here at scale).

| Group | Gate | Verdict | Evidence |
|---|---|---|---|
| A | Prompt Minimalism | **NEW (narrow)** | `prompt_pattern_optimizer.py` + `prompt_defense_baseline.py` cover adjacent ground, neither gates a single outgoing sub-agent prompt's size before send |
| A | Delegation | **EXTEND** | `skill_router/intent_classifier.py` (WIRED) + `pp_agents/proactive_dispatcher.py` (WIRED) route delegation; neither validates "should this have gone to a sub-agent" after the fact |
| B | Architectural Consistency | **REUSE, WIRING GAP** | `modules/arch-decision/` exists; `arch_check`/`test_closed_loop`/`test_v_block` listed in `known_orphans` |
| B | Ownership | **REUSE** | `decision_review/decision_kernel.py` + `SYSTEM_REGISTRY.md`/`NON_DUPLICATION_LEDGER.md` are exactly this |
| B | Blast Radius | **REUSE** | DRK-02 (doc) + `decision_kernel.py` DBR computation + `contract_fabric/side_effect_ledger.py` scope ladder |
| B | Duplicate-to-Advantage | **REUSE, WIRED** — strongest exact overlap in the whole proposal | `duplicate_to_advantage/d2a_engine.py` + `hooks/d2a_gate.js` confirmed registered in `hook-dispatcher.js` |
| C | Production Reality Gate++ | **REUSE, partially WIRED** | `sqi/repo_reality_scanner.py` + `output_contracts/validator.py` (Stop-chain WIRED); `cascade_prevention` confirmed **not** in dispatcher |
| C | Evidence-First | **REUSE** | SQI-00 "Reality Supremacy hierarchy" + `uqf/principles/proof_triad.py` |
| C | Requirement Reality | **REUSE** | `spec_gate/gate.py` (HR-SPEC-001), command-invoked |
| C | Documentation Truth | **REUSE** | `modules/refcheck/linter.py` + `ads/doc_updater.py` (Stop-chain WIRED) |
| D | Contract Connectivity | **REUSE** | DAIF-04 + `contract_fabric/side_effect_ledger.py` |
| D | Integration Completeness | **REUSE, exact name match** | `tools/verify_integration_wiring.py` |
| D | Completion Integrity | **REUSE, exact name match** | `modules/done_gate/artifact_done_gate.py` |
| D | Scope Integrity | **REUSE, exact name match** | `modules/one_shot/lock.py` (HR-ONESHOT-002) |
| E | Technical Debt | **REUSE** | DRK-05 + `recall_roi/recall_roi.py` (live-generated `RETIREMENT_CANDIDATES.md`) |
| E | Simplicity | **INTEGRATE (thin)** | folded into DRK-07 bias calibration; no standalone module |
| E | Determinism | **REUSE** | SQI-03 + repo-wide hermetic-×3 test convention |
| E | Dead Surface | **REUSE, exact name match — this repo's own flagship finding** | `modules/liveness/` + `reachability_registry.json` |
| E | Configuration Reality | **REUSE** | `modules/setup_os/drift_detector.py` |
| E | Invariant Preservation | **REUSE, exact name match** | `modules/sqi/baseline_guardian.py` (SQI-02, sealed `T-SQI-RATIO-GATE-REWARDS-DELETION-001`) |
| F | Failure Completeness | **REUSE (early-stage)** | `modules/craif/` Phase 1, SQI-07 taxonomy referenced |
| F | Regression | **REUSE** — duplicates Invariant Preservation above | `sqi/baseline_guardian.py` + `weakening_detectors.py` |
| F | Test Reality | **REUSE, exact name match, measured on this repo** | SQI-02: "Test File Reach 3.0%, Orphaned 97" |
| F | Migration Safety | **REUSE, WIRING GAP** | `modules/rollback/` + `modules/backup/` mostly in `known_orphans` |
| F | Security Boundary | **REUSE, WIRED, confirmed independently** | `modules/secret_firewall/` + `hooks/secret_firewall_gate.js` registered in PreToolUse-Edit chain |
| G | Resource Economics | **REUSE** | `cost_collapse/router.py` (HR-COST-*), doctrine-applied not hook-wired |
| G | Context Hygiene | **REUSE, largely WIRING GAP** | `cognitive_os/context.py`/`gc.py` in `known_orphans`; HR-CASCADE-005 logic in unwired `cascade_prevention` |
| G | Observability | **REUSE** | `cognitive_os/co_12_telemetry.py`, `monitoring/`, `graphify/` (Stop-chain WIRED via `session_writeback.py`) |
| G | Human Override | **REUSE, exact match** | `modules/owner_queue/owner_queue.py` + DRK-07 §VII.3 override protocol |
| H | Gate Conflict Resolution | **REUSE — and structurally different from the CGF's premise** | `modules/hard_rules/residual.py`: "no precedence to compute" |
| H | Gate Burden | **INTEGRATE (doc-only)** | DRK-07 §VII.5 review-cost metric; no standalone scorer |
| H | False Positive | **REUSE, exact match, actively maintained** | `governance/KNOWN_FALSE_POSITIVES.md` + `uqf/principles/false_positives_catalog.py` |
| H | Gate Bypass Integrity | **INTEGRATE (convention-level)** | distributed across every HR rule's EXCEPCIÓN clause + DRK-07 `owner_override` struct |
| I | Compounding Value | **REUSE, WIRED (conditional)** | `frontier_intelligence/corpus_roi.py` + `fable_distillation/fd_07_flywheel.py` |
| I | Reuse | **REUSE, exact match** | `modules/recall_roi/` + `duplicate_to_advantage/` |
| I | Knowledge Capture | **CONSOLIDATE — 3 overlapping surfaces** | `fable_distillation/`, `akos_knowledge/`, sibling `compound-learnings` skill |
| I | Future/Opportunity Discovery | **REUSE for known-gap half; NEW for IAS-C2 "Opportunity Cost" sibling** | `frontier_intelligence/unknown_unknown_generator.py`; `NON_DUPLICATION_LEDGER.md` already verdicted IAS-C2 `BUILD`, not yet built |
| — | Governance Evolution Engine | **REUSE — would duplicate DRK-07 near-verbatim** | `decision_review/` DRK-07 propose-never-apply constitution, `frontier_intelligence/evolution_engine.py`, CEPS bridge (WIRED), `learning-sentinel.js` (WIRED) |
| — | Precedence Architecture | **INTEGRATE — 3 existing precedent-shaped mechanisms to compose, not override** | `hard_rules/residual.py` (no-precedence-needed), DRK-07 §VII.9 invariant ordering, SQI-00 Reality Supremacy hierarchy |

## Aggregate reading

Of ~37 mechanisms audited: **0 are genuinely NEW at full scope** (only 2 narrow sub-pieces —
Prompt Minimalism proper, and the IAS-C2 Opportunity Cost dataset — are confirmed gaps). The
rest are REUSE, EXTEND, INTEGRATE, or CONSOLIDATE. A material fraction of the REUSE items carry
a **WIRING GAP**: the mechanism exists and imports cleanly but has no live hook/command pointing
at it (`arch-decision`, `cascade_prevention`, `cognitive_os/context+gc`, `rollback`/`backup`
partially) — this is the repo's own previously-diagnosed disease (Liveness Standard, sealed
2026-07-13) recurring at the exact scale the CGF proposal would otherwise re-diagnose from
scratch.

## Recommended objective shift (per the CGF proposal's own instructions: "cambiar objetivo hacia consolidacion, fortalecimiento, conectividad, enforcement y evolucion — no creacion duplicativa")

1. **Wire, don't build**: register `arch-decision`, `cascade_prevention`, `cognitive_os/context`+`gc`,
   `rollback`/`backup` into the Liveness registry as `LIBRARY`/`SCHEDULED`, or actually wire the
   already-built `cascade_prevention` HR-CASCADE-001…005 logic into `hook-dispatcher.js` — it is
   the single largest live gap (5 sealed Hard Rules whose enforcement code is unwired).
2. **Consolidate**: pick one owner among `fable_distillation` / `akos_knowledge` / `compound-learnings`
   for Knowledge Capture; resolve the `code-review` vs `code_review` naming collision.
3. **Build only the 2 confirmed gaps**: a true pre-send Prompt Minimalism check, and the
   already-verdicted-but-unbuilt IAS-C2 "Opportunity Cost" dataset.
4. **Do not build**: a new Governance Evolution Engine (duplicates DRK-07), a new Gate Conflict
   Resolution mechanism (contradicts sealed `hard_rules/residual.py` doctrine), a new
   Duplicate-to-Advantage Gate (is the exact existing D2A gate), a new Dead Surface Gate (is the
   exact existing Liveness Standard), a new Security Boundary Gate (is the exact existing,
   independently-verified secret firewall).
5. Any precedence architecture must explicitly cite and compose `hard_rules/residual.py` +
   DRK-07 §VII.9 + SQI-00, not re-derive a fourth incompatible ordering.

---

## STOP #1 — awaiting Owner approval

Phase -1 is complete. Per the CGF proposal's own protocol, this is a **blocking** checkpoint —
no Phase 2 (full inline plan, gate design, code) proceeds without explicit Owner sign-off on the
verdicts above. Specifically, approve or redirect on:

- Is the "0 new mechanisms at full scope, ~35 REUSE/EXTEND/INTEGRATE/CONSOLIDATE" reading
  accepted, or is there a mechanism above you believe is mis-verdicted?
- Do you want the recommended objective shift (wire the 5 unwired `cascade_prevention` Hard
  Rules + consolidate Knowledge Capture + build only the 2 confirmed gaps), or something else?
- Should the `code-review`/`code_review` naming collision and the SKILLBANK.md staleness
  (14 listed vs. ~70 real) be filed as separate follow-up items, or folded into this same effort?
