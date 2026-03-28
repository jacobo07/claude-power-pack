# Phases 11-15: Validation and Governance (DEEP+)

## Phase 11 -- VALIDATE
- Run all quality gates: typecheck, lint, build, test, schema.
- Zero errors required on all gates. Warnings reviewed, not ignored.
- Document any gate that was skipped and why.

## Phase 12 -- SECURITY
- Scan for: exposed secrets, SQL injection, XSS, CSRF, open redirects, auth bypasses.
- Verify auth on all protected routes. Verify authorization (not just authentication).
- Check dependencies for known vulnerabilities if tooling available.

## Phase 13 -- PERFORMANCE
- Identify N+1 queries, missing indexes, unbounded loops, large payloads.
- Verify pagination on list endpoints. Verify rate limiting on public endpoints.
- Check bundle size impact for frontend changes.

## Phase 14 -- DOCUMENTATION
- Update inline comments for non-obvious logic.
- Update API docs if endpoints changed. Update README if setup changed.
- Do not create docs unless requested -- but do update existing ones.

## Phase 15 -- GOVERNANCE
- Verify compliance with project CLAUDE.md rules.
- Verify compliance with domain overlay rules.
- Run project-specific validation pipelines (linters, validators, custom gates).

## Constitution Rules 16-20

16. **Verify Before Claiming Done** -- Run all applicable quality gates. "It compiles" is not done.
17. **No Silent Failures** -- Every catch block must log, report, or re-throw. Empty catches are bugs.
18. **Proportional Response** -- Simple question = simple answer. Do not over-engineer.
19. **Respect Existing Architecture** -- Do not restructure unless explicitly requested.
20. **Document Deviations** -- If you deviate from the plan, document what, why, and impact.
