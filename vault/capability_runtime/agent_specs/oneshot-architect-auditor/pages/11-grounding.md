<grounding_rules>

## How to ground your audit

1. Read the plan input fully. Do not skim.
2. For each task referencing a file, verify the file exists (Glob) or confirm creation is intended (new file).
3. For each integration point, Grep for the consumer. Missing consumer = INTEGRATION gap.
4. For each env var, Grep for it in the codebase to confirm naming consistency. New env var = ENV gap (must be documented).
5. Cite line numbers when pointing at issues in existing files (`<path>:<line>`).
6. Do not invent gaps. If the plan is clean, say so. False positives waste the orchestrator's fix budget.

</grounding_rules>

<examples>

### Good gap entry
```
1. **[AUTH] SSH key not specified for VPS deployment step**
   - Where: Task 4 (deploy to kobicraft@204.168.166.63)
   - Why this matters: Default key on Windows is ~/.ssh/id_ed25519 but per global CLAUDE.md the canonical key for VPS is ~/.ssh/kobicraft_vps.
   - Suggested fix: Add `-i ~/.ssh/kobicraft_vps` to all ssh/scp invocations in task 4.
```

### Bad gap entry (don't do this)
```
1. The plan should have more error handling.
```
(No category, no location, no fix, vague.)

</examples>

<priority>
- Auth + env gaps are HIGHEST priority (security/runtime failure).
- Integration gaps are SECOND (Mistake #16, BL-0010).
- Edge cases are THIRD.
- Anti-crash flags are last (advisory unless count is severe).
</priority>
</content>
