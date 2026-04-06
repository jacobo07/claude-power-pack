# Governance Overlay — During-Task Verification

> Loaded for DEEP and FORENSIC tiers. ~200 tokens. Checked after EACH file created or modified.
> Inherits workspace context from PART A0 Assimilation Scan. All file references use `./` relative paths.

## Per-File Checks

After creating or modifying each file, verify:

### Wiring Check (Mistakes #1, #2, #6)
- **New file** → grep codebase for at least one import/require of this file
- **New export** → verify at least one call site exists
- **If no consumer found** → STOP and wire it before continuing to the next file
- A file without a consumer is not "done" — it's dead code

### Integration Check (Mistakes #4, #5, #7)
- **New event/listener** → verify the corresponding emit/dispatch call exists
- **New config getter** → verify something reads the value
- **Replacement/upgrade** → verify ALL old call sites have been updated (not just the first one found)
- Use `grep -r "old_function_name"` to find remaining references

### Data Flow Check (Mistakes #3, #15)
- **New state/data** → verify save/persist exists in the completion path
- **New counter/metric** → verify it tracks REAL state, not just the initial value
- A counter initialized to `items.length` that never updates is Mistake #15

### Pattern Check (Mistakes #8, #9, E11)
- **Changed geometry/layout constants** → verify dependent ratios are still correct
- **About to build a utility** → grep first — does this utility already exist?
- **Using deprecated API** → check for the modern equivalent
- **Any path string in skill/global code** → must be `./` or `$PWD`. Absolute paths = E11 violation

### API Endpoint Security Checks (Per-Endpoint, Mistakes #25, #26)
When modifying any API endpoint in a FastAPI/Express/Phoenix project:
1. **Authentication:** Verify `Depends(get_current_user)` or equivalent auth dependency is present
2. **Rate limiting:** Verify rate limit decorator exists for write endpoints (POST/PUT/DELETE)
3. **Query parameter types:** Verify enum parameters use proper Enum types, not raw strings
4. **Tenant scoping:** If model has `org_id`, verify query filters by `user.org_id`
5. **Error handling:** Verify no bare `except Exception:` — always narrow the catch or log the error

If any check fails: fix before proceeding. Do NOT defer to "later fix".

### Language Robustness Check (when implementing in non-Elixir with fragility score >=2)
When implementing a backend service, daemon, or CLI tool in a non-Elixir language:
- **Every `try/catch` block** → verify it has explicit error recovery (retry, fallback, escalation), not just logging (Mistake #25)
- **Every HTTP client call** → verify timeout + retry + circuit breaker pattern (exponential backoff, max retries) (Mistake #25)
- **Every long-running process** → verify SIGTERM/SIGINT handler + graceful shutdown + connection draining (Mistake #25)
- **Every shared state** → verify isolation mechanism: per-request context, locks, actors, or immutable design (Mistake #25)
- **Every background job** → verify queue depth limits + dead letter handling + job timeout (Mistake #25)
If any of these are missing, flag as Mistake #25 (Fragile Language for Critical Systems) and require implementation before proceeding.

### Async Safety Check (Mistake #34)
When writing Python code that bridges sync and async contexts:
- **Any `asyncio.run()` call** → verify it is ONLY inside `if __name__ == "__main__":`. If found in library/utility code, BLOCK and rewrite using the dual-path pattern (try `get_running_loop` → `create_task` / except → `threading.Thread`)
- **Any sync wrapper around async functions** → verify it handles both "already in event loop" and "no event loop" cases
- **Any module imported by FastAPI/aiohttp/async framework** → grep for `asyncio.run(` — must return 0 results

### Database Access Mode Check (Mistake #35)
When writing code that opens file-based databases (DuckDB, SQLite):
- **Every `connect()` call** → verify explicit access mode parameter (`read_only=True` for readers)
- **Multiple consumers of same DB file** → verify only ONE process is the designated writer
- **Connection constructors** → verify they accept `read_only: bool` parameter and pass it through

### Agent Governance Checks (when building agent systems)
When modifying code detected as an agent system (see pre-task Section 7):
- **New agent loop** → verify kill switch present: `max_iterations` + `circuit_breaker` + `cost_limit` (Mistake #27)
- **New tool registration** → verify tool is in `allowed_tools` policy; dangerous tools (`shell_exec`, `delete_*`) need explicit justification (Mistake #28)
- **New agent-to-agent call** → verify trust boundary declaration: identity verification + trust score check (Mistake #29)
- **New agent memory write** → verify no secrets (API keys, tokens, credentials) stored in agent state
- **Framework adapter** → verify AGT adapter configured for detected framework, or manual policy enforcement in place
- **Multi-step workflow** → verify saga/rollback exists for partial failure recovery (Mistake #33)
