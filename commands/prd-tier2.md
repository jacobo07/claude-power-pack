---
name: prd-tier2
description: Render the SDD-OS Tier 2 (Feature / System Task) full PRD + Architecture Spec. For new relevant functionality or changes impacting architecture, data, UX, security, workflows or integrations (new agent, workflow, module, persistence, pipeline, API integration, CLI/plugin change). Full PRD (Problem/Objective/Non-objectives/Users/FR/NFR/AC) + Architecture Spec + Roadmap + Validation Contract. Tier >= 2 requires a PRD before execution. Source. SDD-OS PARTE I sec. 3, 5, 6.
---

# /prd-tier2 -- Feature / System PRD + Architecture Spec

Tier 2 = new capability or architecture/data/UX/security/workflow/
integration impact. **Execution without a PRD is prohibited** (SDD-OS
PARTE I sec. 4). Fill and get the plan approved before coding.

```
## Tier 2 PRD
### 1. Problem
- Current pain: <...>
- Risk of not solving it: <...>
- Errors it prevents: <...>

### 2. Objective (observable)
- <e.g. "Every Tier 2+ task generates a PRD + Architecture Spec + AC
  before execution is permitted." -- never "improve the system">

### 3. Non-objectives
- <what is explicitly NOT in scope -- prevents scope creep>

### 4. Users / actors
- <human user · Claude Code · Power Pack · target repo · CI/CD · agents>

### 5. Functional requirements (each verifiable)
- FR-001: <...>
- FR-002: <...>

### 6. Non-functional requirements (if applicable)
- NFR-001: <security / robustness / speed / cost / compatibility /
  reversibility / observability / cross-repo portability>

### 7. Acceptance criteria (done = all pass)
- AC-001: <...>
- AC-002: <...>

## Architecture Spec
- Components affected: <...>
- Contracts (inputs/outputs/invariants): <...>
- Failure modes anticipated: <...>
- Rollback / fallback: <...>

## Roadmap (verifiable steps)
- Step 1: <...>  (done-gate: <...>)
- Step 2: <...>  (done-gate: <...>)

## Validation contract
- Happy path: <...>
- Error cases: <...>
- Regression check: <...>
- Proof of real behavior (not just "compiles"): <...>
```

## Done-gate (Tier 2)
- Spec, Architecture Spec and AC exist and were approved.
- Implementation follows the spec; no scope creep; no broken contracts.
- Validation demonstrates real behavior, not just compilation.
- OQS for this surface meets the Tier 2 floor (>= 80).
