# SDD-OS -- Spec-Driven Development OS (SCS C39)

## SCS C39 -- SDD-OS-by-default: classify the tier, gate the spec, scale the OQS (sealed 2026-06-07, BL-SDD-OS-001)

**Standard.** Every task is classified into an SDD-OS tier *before*
execution. Rigor scales with tier; the highest tier requires a full
spec and is blocked without one. Universal: the classifier and gates are
free-text + stdlib, so they work in any repo.

**Source of truth correction (premise check).** The `Dataset SDD-OS 1.txt`
defines **FOUR tiers (0-3)**, not five. The plan assumed a "Tier 4
(System/Arch)"; the dataset's **Tier 3 (Strategic / Platform Task)**
already absorbs new-OS / universal-framework / cross-repo / spec-driven
work. Built to the source, not the assumption.

| Tier | SDD-OS name | spec_gate size | OQS floor | Spec required |
|---|---|---|---|---|
| 0 | Micro Task | S | 60 | no (inline mini-spec) |
| 1 | Standard Task | M | 70 | brief spec |
| 2 | Feature / System | L | 80 | **full PRD + Arch Spec** |
| 3 | Strategic / Platform | XL | 90 | **full spec set + governance + kill switch** |

**What shipped (all verified, `tools/test_sdd_os.py` 10/10 x 3 hermetic):**
- `modules/spec_gate/gate.py::classify_tier()` -- free-text -> Tier 0-3
  + size (0->S,1->M,2->L,3->XL) + requires_spec/requires_prd (tier>=2).
  PRD-trigger keywords (system/os/framework/pipeline/universal/cross-repo
  ...) force >= Tier 2 (dataset PARTE I sec. 4).
- `commands/prd-tier{0,1,2,3}.md` -- per-tier PRD templates (mini-spec ->
  full strategic spec set).
- `modules/skill_router/intent_classifier.py` -- the EXISTING `spec`
  domain extended with SDD-OS vocabulary (NOT a duplicate `prd` domain).
  A PRD/spec prompt -> domain `spec`, should_wakeup True.
- `modules/output_contracts` -- `is_done_for_tier()` + `tier_floor()` +
  `TIER_OQS_FLOOR`. Per-tier floors layered OVER the global
  `OQS_DONE_THRESHOLD` (70), which is unchanged so HR-OUTPUT-003 holds.
- `vault/knowledge_base/sdd_os/` -- 5 PARTE files + MASTER (the dataset
  is richer than the plan's 6 thematic files: PARTEs II-V add
  Contracts/Proof, Spec-Compiler, Requirements-Truth, Decision-OS).

**Method (carries the prior lessons forward).** C28 (read the real
source before coding -- spec_gate did NOT classify; it received a size,
so M5 was a build, not an extension). C30 (extend the chokepoint -- the
`spec` intent domain already existed; extended it, didn't fork). No
classified FAILs at the gate (the incidental `secret_rotation_advisor`
nested-`__pycache__` leak was fixed at root, not waved off).

Cross-ref C28 (read source first / plan-is-a-hypothesis), C30 (extend
the chokepoint), C31 (spec-driven for L/XL -- SDD-OS is its generalization),
C37/C38 (recent dedicated-file SCS seals).

Sealed BL-SDD-OS-001 2026-06-07.
