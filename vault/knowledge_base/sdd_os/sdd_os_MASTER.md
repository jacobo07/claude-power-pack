# SDD-OS -- Master Index

**Source:** Dataset SDD-OS 1.txt
**Source sha256:** a6c8f6bcd83a8230
**Source total lines:** 3774
**Ingested by:** tools/sdd_os_ingest.py (Sprint 2 / M4).

Spec-Driven Development OS. Core law: **Spec First. Execution Second. Validation Always.** Defines FOUR task tiers (0-3); Tier >= 2 requires a PRD before execution.

## Parts

| File | PARTE | Lines | Bytes |
|---|---|---|---|
| [sdd_os_01_universal_spec_governance_layer.md](sdd_os_01_universal_spec_governance_layer.md) | I | 613 | 15284 |
| [sdd_os_02_contracts_invariants_proof_driven_executio.md](sdd_os_02_contracts_invariants_proof_driven_executio.md) | II | 614 | 7907 |
| [sdd_os_03_specification_compiler_executable_engineer.md](sdd_os_03_specification_compiler_executable_engineer.md) | III | 936 | 9115 |
| [sdd_os_04_requirements_truth_system_rts_anti_halluci.md](sdd_os_04_requirements_truth_system_rts_anti_halluci.md) | IV | 842 | 8450 |
| [sdd_os_05_decision_os_engineering_governance_layer.md](sdd_os_05_decision_os_engineering_governance_layer.md) | V | 769 | 7454 |
| **total** | | | **48210** |

## Downstream wiring

- `modules/spec_gate/gate.py::classify_tier()` -- free-text -> Tier 0-3.
- `commands/prd-tier{0,1,2,3}.md` -- per-tier PRD templates.
- `modules/skill_router/intent_classifier.py` -- `spec` domain extended with SDD-OS trigger keywords.
- `modules/output_contracts` -- per-tier OQS floors (Tier0 60 / Tier1 70 / Tier2 80 / Tier3 90).

