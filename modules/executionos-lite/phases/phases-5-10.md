# Phases 5-10: Implementation (STANDARD+)

## Phase 5 -- PLAN
- Break work into ordered tasks. Each task: one concern, one commit.
- Identify dependencies between tasks. Parallelize where safe.
- Estimate files touched per task.

## Phase 6 -- SCAFFOLD
- Create file structure, stubs, types, interfaces.
- No logic yet -- just the skeleton that passes type checks.
- Commit scaffold if project uses incremental commits.

## Phase 7 -- IMPLEMENT
- Write code task by task, in plan order.
- Follow domain overlay rules for the active stack.
- After each task: verify it works in isolation before moving on.

## Phase 8 -- INTEGRATE
- Wire new code into existing call chains.
- Verify imports, exports, registrations, route bindings.
- Run build/typecheck. Fix all errors before proceeding.

## Phase 9 -- TEST
- Write or update tests covering new behavior.
- Run test suite. All tests must pass (new and existing).
- If no test infra exists, flag as risk, do not skip.

## Phase 10 -- REVIEW
- Re-read all changed files. Check for: dead code, missing error handling, hardcoded values, security gaps.
- Verify every new file has at least one consumer.
- Verify every new function is called somewhere.

## Constitution Rules 6-15

6. **Wire Everything** -- Every file created must be imported/called somewhere. Orphan files are bugs.
7. **Save Triggers** -- Any state change must have an explicit save/persist call in the completion path.
8. **Error Boundaries** -- Every external call (API, DB, file I/O) must have error handling.
9. **No Hardcoded Secrets** -- Credentials, keys, tokens go in env/config, never in source.
10. **Type Safety** -- Use the type system. No `any`, no untyped catches, no implicit conversions.
11. **Minimal Diff** -- Change only what is needed. Do not refactor adjacent code unless requested.
12. **Existing Patterns** -- Use utilities and patterns already in the codebase. Do not reinvent.
13. **Build Must Pass** -- Code must compile/build without errors before declaring any task complete.
14. **Test Must Pass** -- All tests (new + existing) must pass before declaring any task complete.
15. **One Concern Per Commit** -- Each commit addresses one logical change. No mega-commits.
