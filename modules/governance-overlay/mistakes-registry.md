# Governance Overlay — Mistakes Registry

> Reference document. Loaded only during FORENSIC tasks or when investigating a specific mistake.

## Mistake #1: Building Without Wiring
- **Detection:** `grep -r "import.*from.*<new_file>" .` returns 0 results
- **Example:** Created `lib/analytics.ts` with 5 exported functions. No file imports it. All functions are dead code.
- **Prevention:** After creating any file, grep for callers. No callers = not done.

## Mistake #2: Detail Without Integration
- **Detection:** New utility module exists but no screen/component calls it
- **Example:** Built a complete `formatCurrency()` utility. Never called it from the UI that displays prices.
- **Prevention:** Wire the utility into its consumer in the same session.

## Mistake #3: Data Without Save Triggers
- **Detection:** State is mutated but no `.save()`, `.update()`, or `.insert()` in the path
- **Example:** Updated user preferences in memory but never persisted to database.
- **Prevention:** Trace every data mutation to a persist call.

## Mistake #4: Events Without Sources
- **Detection:** `addEventListener` or `.on()` exists but no corresponding `.emit()` or `.dispatch()`
- **Example:** Registered a `userUpdated` event handler but nothing ever emits `userUpdated`.
- **Prevention:** For every listener, verify the emitter exists.

## Mistake #5: Config Without Consumers
- **Detection:** Config getter/constant exported but no code reads it
- **Example:** Added `MAX_RETRY_COUNT = 3` to config but the retry loop uses a hardcoded `5`.
- **Prevention:** Grep for every config key to verify it's consumed.

## Mistake #6: File Exists ≠ Works
- **Detection:** File exists on disk but produces no observable output when the app runs
- **Example:** Created a migration file but never ran it. Tables don't exist.
- **Prevention:** Every file needs a consumer AND observable output.

## Mistake #7: Upgrade Without Replacement
- **Detection:** New implementation exists alongside old one; old call sites not updated
- **Example:** Created `evaluateV2()` but all screens still call `evaluateV1()`.
- **Prevention:** Update every call site when replacing an implementation.

## Mistake #8: Constants Drift
- **Detection:** Changed a base constant but dependent ratios/calculations unchanged
- **Example:** Changed grid columns from 3 to 4 but card width still calculates `100% / 3`.
- **Prevention:** After changing any constant, grep for all references and verify math.

## Mistake #9: Deprecated Patterns
- **Detection:** Built a new utility when an existing one does the same thing
- **Example:** Wrote a custom `formatDate()` when the project already uses `dayjs`.
- **Prevention:** Search for existing implementations before creating new ones.

## Mistake #10: Report Gaps Instead of Fixing
- **Detection:** Comment says `// TODO: fix this` or output says "this needs to be addressed"
- **Example:** Found a broken import, noted it in the PR description, but didn't fix it.
- **Prevention:** Fix issues in the same pass. Don't defer what you can resolve now.

## Mistake #11: Remote != Localhost
- **Detection:** `localhost` or `127.0.0.1` hardcoded in code that runs on a server
- **Example:** API client configured with `http://localhost:3000` deployed to production.
- **Prevention:** Use environment variables for all connection strings.

## Mistake #12: Approximating Instead of Implementing
- **Detection:** Solution works for the demo case but fails on edge cases
- **Example:** Parsing dates with string splitting instead of using a date library.
- **Prevention:** Solve the actual hard problem. Don't approximate.

## Mistake #13: Assumptions Without Verification
- **Detection:** Edited a file without reading it first; called a function assuming its signature
- **Example:** Added a parameter to a function call that doesn't accept that parameter.
- **Prevention:** Read the file. Verify the API. Then make the change.

## Mistake #14: Analyzing Callee Without Caller
- **Detection:** Fixed a function's internals without checking who calls it and how
- **Example:** Changed a function's return type but the 3 callers all expect the old type.
- **Prevention:** Trace the full call chain UPWARD before modifying any function.

## Mistake #15: Static Display of Dynamic Data
- **Detection:** UI shows a counter that's set once and never updates
- **Example:** Dashboard shows "Total Users: 42" computed at page load but never re-queries.
- **Prevention:** Counters and metrics must track real-time state or be explicitly labeled as snapshots.

## Mistake #16: Scaffold Illusion (Compiles != Works)
- **Detection:** Module exists and compiles, but is commented out in the startup/wiring, has stub implementations, or is never called by the running system. Tests validate isolated units but never test integration. Claimed as "done" because `mix compile` / `tsc --noEmit` passes.
- **Example:** KairosDreamer module file didn't exist, its startup was commented out in application.ex, yet the commit message claimed "persistent memory via Ecto/SQLite3". Gateway was a pure function, never supervised as GenServer, yet claimed "Circuit Breaker". PermissionMatrix used naive string checks, yet claimed "Zero Trust". 16 tests passed but none tested the agentic loop end-to-end.
- **Root Causes:**
  1. Skeleton-first development: boilerplate compiles fast, gives false confidence
  2. "Next iteration" stubs: commenting out wiring with intent to enable later
  3. Happy-path-only security: blacklisting obvious cases, ignoring bypass vectors
  4. No error recovery by default: `:infinity` timeouts, zero retries, no malformed response handling
  5. Tests that validate existence, not behavior: testing what IS, not what's MISSING
- **Prevention (MANDATORY for every module):**
  1. **Wire-before-claim:** Every new module must be active in the supervision tree / startup path. Commented-out children = not done.
  2. **Adversarial security:** For every security check, ask "how would an attacker bypass this?" before claiming it works. Test at least 3 bypass vectors.
  3. **Defensive defaults:** Every external call needs a timeout (not `:infinity`), a retry count (not 0), and a malformed response handler.
  4. **Integration-before-unit:** Write at least 1 test that exercises the full path (user input → processing → output) before writing unit tests. A system where every unit passes but the integration fails is worse than untested.
  5. **Negative testing:** For every feature, write at least 1 test for "what happens when this fails?" not just "does this work when everything is perfect?"

## Mistake #17: Runtime != Compiles (OmniCapture Gate)
- **Detection:** All static verification passes but runtime telemetry shows errors
- **Example:** `tsc --noEmit` passes, `mix compile` passes, but the app crashes at runtime due to missing env vars, unreachable APIs, or schema mismatches.
- **Prevention:** At DEEP+ tier, query OmniCapture telemetry before claiming completion. At FORENSIC, BLOCK if CRITICAL/FATAL events exist.

## Mistake #18: Return Type Contract Mismatch
- **Detection:** Module A calls Module B and pattern-matches on return values that B never produces. `case B.check() do {:ok, _} -> ...` when B actually returns `{:pass, _}`.
- **Example:** Governance Plug expected `{:ok, _}` from RuntimeCheck but it returns `{:pass, _}`, `{:skip, _}`, `{:block, _}`. All RuntimeCheck results silently fell through to a catch-all `_ ->`.
- **Root Causes:**
  1. Writing the caller before reading the callee's source
  2. Assuming conventional return types without verification
  3. No tests that exercise the integration path between caller and callee
- **Prevention:**
  1. Before writing ANY `case Module.function() do`, READ the function's source to see its actual return types
  2. After wiring modules, write at least 1 test per return type branch
  3. Use `@spec` and `@type` to document contracts — compiler/Dialyzer catches mismatches

## Mistake #19: Dead Code Integration (System-Scale Wiring Gap)
- **Detection:** A subsystem (multiple modules) is "integrated" but no code path in the host system invokes any of its functions. `grep -rn "Subsystem." lib/ | grep -v "subsystem/"` returns 0 results.
- **Example:** 11 governance modules compiled into OSA. Zero lines outside `governance/` referenced them. A `Plug` module existed but no host code imported it. Removing all 11 files would not change runtime behavior.
- **Root Causes:**
  1. Building the subsystem in isolation without concurrent host-side integration
  2. "Plug architecture" assumed — creating an integration module but never calling it
  3. No integration test that exercises the host → subsystem → host round trip
- **Prevention:**
  1. After creating any integration module, grep for callers OUTSIDE the subsystem directory
  2. Write a test that starts the host application and verifies the subsystem hook fires
  3. Use the subsystem from the host in the same session — don't defer wiring to "next iteration"

## Mistake #20: Shell Escaping Corruption on Remote Deploy
- **Detection:** Code deployed via SSH heredoc or shell script has mangled special characters: `\\` becomes `\`, single quotes break enclosures, `$` variables get interpolated by the shell.
- **Example:** `~r/\\$/` (match trailing backslash) deployed via SSH heredoc became `~r/$/` (match end-of-line). PermissionMatrix silently stripped all `$` from commands, breaking command substitution detection.
- **Root Causes:**
  1. Using shell heredocs for code containing quotes, backslashes, or `$`
  2. Not verifying deployed code matches source after transfer
  3. Multiple layers of shell escaping (local shell → SSH → remote shell)
- **Prevention:**
  1. Use SCP/rsync for file transfer instead of heredoc injection
  2. After every remote deploy, read back the file and diff against source
  3. For Elixir/Python: write files locally, SCP to remote, compile on remote
  4. Never use shell heredoc for files containing regex, quotes, or interpolation characters

## Mistake #21: SQL Placeholder Portability
- **Detection:** `grep -rn 'cursor.execute.*".*?' | grep -v '_param'` returns results
- **Example:** Using hardcoded `?` in SQL queries instead of database-agnostic helpers.
- **Why:** SQLite uses `?`, PostgreSQL uses `%s`. Hardcoding one breaks the other.
- **Prevention:** Always use `_param()` helper from database.py. Before commit: `grep -rn 'cursor.execute.*".*?' | grep -v '_param'` should return 0.

## Mistake #22: Schema-Code Column Drift
- **Detection:** Code references table columns that don't exist in the CREATE TABLE schema.
- **Example:** Writing `INSERT INTO trades (signal_source, ...) VALUES (...)` when `signal_source` column doesn't exist in the `trades` CREATE TABLE definition.
- **Why:** Happens when orchestrator code is written before schema is finalized, or when schema changes aren't propagated.
- **Prevention:** After writing any INSERT/UPDATE SQL, verify every column exists in database.py. Use grep to confirm.

## Mistake #23: Empty Registry Module
- **Detection:** `__init__.py` is empty but other modules import functions from it.
- **Example:** `from backend.agents import AgentOrchestrator` when `backend/agents/__init__.py` is empty.
- **Why:** Planning to add later but forgetting. Causes ImportError at runtime.
- **Prevention:** If any module does `from X import func`, verify `func` exists in X BEFORE committing. Run import test.

## Mistake #24: Incomplete State Machine
- **Detection:** State machine defines transitions dict but missing handler functions for some transitions.
- **Example:** `VALID_TRANSITIONS = {"pending": ["running", "cancelled"], "running": ["completed", "failed"]}` but no function handles the `running -> failed` transition.
- **Why:** Easy to define states but forget to implement the transition logic.
- **Prevention:** For every entry in VALID_TRANSITIONS, verify a function handles that transition. Count transitions vs functions.
