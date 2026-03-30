# Governance Overlay — Post-Output Learning

> Loaded for DEEP and FORENSIC tiers. ~100 tokens. Runs after task completion.

## Failure Capture

If any mistake from the 15-mistake registry was caught during this task:

1. **Log to failure patterns** — if `/governance/12_FAILURE_PATTERNS.md` exists in the project:
   ```
   ### [DATE] Mistake #N: [Short description]
   - **What happened:** [Brief description]
   - **How caught:** [Which check caught it — during-task, pre-output, quality gate]
   - **Prevention rule:** "Before [action], always [check]"
   ```

2. **Extract prevention rule** — distill into a one-line rule that prevents recurrence

3. **Project-specific mistakes** — if the mistake is NOT in the 15-mistake registry (it's unique to this project):
   - Add to `governance/domain/PROJECT_DOMAIN_RULES.md` as a new DR-NNN rule
   - Format: Rule, Rationale, Detection, Status: ACTIVE

## FORENSIC Tier Additional Logging

If task was classified as FORENSIC:
- Create incident trace in `/governance/17_CAUSAL_TRACE.md`
- Record the full causal chain: symptom → investigation → root cause → fix → verification
- Update `/governance/18_CONFIDENCE_LOG.md` with certainty level of the fix
- Flag if the fix is a workaround vs a root-cause resolution
