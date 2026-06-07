---
name: prd-tier1
description: Render the SDD-OS Tier 1 (Standard Task) brief spec. For moderate functional changes with limited impact (add an option, improve a flow, simple endpoint, add a command, modify an existing integration, fix a bug with a clear cause). Brief Spec + Acceptance Criteria + Impact Map + Test Plan + Completion Gate. Source. SDD-OS PARTE I sec. 3 (Tier 1).
---

# /prd-tier1 -- Standard Task brief spec

Tier 1 = moderate functional change, limited impact. No full PRD, but a
brief spec is required before coding.

Fill and paste at the top of the working prompt:

```
## Tier 1 brief spec
### Brief
- Goal: <what this change must achieve, in observable terms>
- Non-goals: <what is explicitly out of scope>

### Acceptance criteria
- AC-001: <verifiable condition>
- AC-002: <verifiable condition>

### Impact map
- Files / modules touched: <list>
- Existing contracts touched: <callers, APIs, schemas -- or "none">
- Regression surface: <what could break>

### Test plan
- Happy path: <the case that proves the feature works>
- Edge / error case: <the failure case you will exercise>

### Completion gate
- Spec approved · implementation follows spec · happy + error case
  validated · no existing contract broken.
```

## Done-gate (Tier 1)
- Every AC observed to pass (not "should pass").
- The error case was actually exercised.
- No regression in the listed impact surface.
