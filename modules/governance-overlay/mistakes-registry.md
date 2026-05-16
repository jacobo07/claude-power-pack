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

## Mistake #25: Fragile Language for Critical Systems
- **Detection:** New backend system scores 4+ on fragility criteria but uses Node.js/Python without a Language Decision Record. `grep -r "express\|fastify\|flask\|fastapi" <new_project>/` in a system that needs supervision trees.
- **Example:** Built a multi-agent orchestrator with 8 concurrent LLM calls, retry logic, and state management in Node.js. No supervisor, no circuit breakers, no graceful shutdown. Single unhandled promise rejection kills all 8 agents.
- **Root Causes:**
  1. Defaulting to familiar language without evaluating requirements
  2. Assuming all backend languages are equivalent for all workloads
  3. Not scoring fragility criteria before choosing a stack
- **Prevention:**
  1. Run the 10-criterion fragility score BEFORE writing any code
  2. If score >= 4, Elixir is the default — override requires explicit LDR
  3. If non-Elixir chosen, manually implement ALL OTP equivalents listed in the LDR
  4. Post-task verification must confirm equivalents are present, not just listed

## Mistake #26: Building Critical Infrastructure Without Language Decision Record
- **Detection:** Project has background workers + fault tolerance needs + concurrent operations (scores >= 4 on fragility gate), but no `LDR_*.md` file in project docs/ or governance/ directory.
- **Example:** COEE SaaS built in Python/FastAPI with Celery workers, SMTP delivery, concurrent API calls, long-running campaign orchestration — scores 7/10 on fragility gate — but no LDR was created before development started.
- **Root Causes:**
  1. Fragility gate not yet implemented when project started
  2. Gate existed but was bypassed without documentation
  3. Team defaulted to "familiar" language without evaluation
- **Prevention:**
  1. Pre-task fragility gate (Section 5) MUST run on every new project
  2. Score >= 4 without LDR = BLOCKED (cannot write code until LDR filed)
  3. Retroactive LDR required for existing projects per Section 5e
  4. Register in Global Alignment Ledger if LDR was bypassed

---

## Agent Governance Mistakes (OWASP ASI Coverage)

## Mistake #27: Agent Without Kill Switch (OWASP ASI-10)
- **Detection:** Agent loop code has no `max_iterations`, no `circuit_breaker`, no `timeout`, no `cost_limit`. `grep -rn "while.*True\|for.*range.*999\|loop do" <agent-dir>` without nearby `max_iterations` or `break` condition.
- **Example:** LangChain agent with `while True` loop and no stop condition burns $200 in API calls before manual intervention.
- **Root Causes:**
  1. Prototyping without guardrails — "I'll add limits later"
  2. Framework defaults don't enforce iteration caps
  3. Cost accumulates silently (no per-iteration cost tracking)
- **Prevention:**
  1. Every agent loop MUST have: `max_iterations` cap, `total_cost_limit`, circuit breaker pattern
  2. Use AGT `AgentRuntime` kill switch or implement equivalent manual check
  3. Log cost-per-iteration and abort when budget threshold reached

## Mistake #28: Unbounded Tool Access (OWASP ASI-01: Unrestricted Agency)
- **Detection:** Agent has access to `shell_exec`, `file_write`, `network_raw`, or `delete_*` without explicit scope limits. `grep -rn "tools.*=.*\[" <agent-dir>` shows dangerous tools without corresponding `blocked_tools` or path restrictions.
- **Example:** CrewAI agent given `bash_tool` access with no path restrictions deletes project files via `rm -rf`.
- **Root Causes:**
  1. Giving agents "all tools" for convenience during development
  2. Not auditing transitive capabilities (tool A can invoke tool B)
  3. No separation between dev and production tool sets
- **Prevention:**
  1. Define `allowed_tools` AND `blocked_tools` explicitly. Default = deny all
  2. Use AGT `PolicyEngine` with `CapabilityModel` for enforcement
  3. Production tool sets must be a strict subset of development tool sets

## Mistake #29: Trust Without Verification (OWASP ASI-03: Insecure Agent-Agent Communication)
- **Detection:** Multi-agent system passes messages between agents without authentication, trust scoring, or input validation. `grep -rn "send_message\|delegate\|handoff" <agent-dir>` without nearby `verify\|authenticate\|trust`.
- **Example:** Rogue agent injects instructions into shared memory that other agents execute blindly, causing data exfiltration.
- **Root Causes:**
  1. Treating inter-agent communication like internal function calls
  2. No identity model for agents (all agents are equal)
  3. Shared memory without access control
- **Prevention:**
  1. Every agent-to-agent call must verify identity (Ed25519 or equivalent)
  2. Use AGT `AgentMesh` trust scores — minimum 700 for delegation
  3. Validate all incoming messages regardless of source agent's trust level

## Mistake #30: Privilege Escalation via Tool Chain (OWASP ASI-05)
- **Detection:** Agent in Ring 3 (restricted) can chain tools to achieve Ring 0 (admin) effects. Agent can't delete files directly but can run a shell command that deletes files, or can write a script that does privileged operations.
- **Example:** Agent with only `write_file` permission writes a bash script, then uses `execute_file` to run it with elevated privileges.
- **Root Causes:**
  1. Auditing tools individually instead of auditing tool chains
  2. File write + file execute = arbitrary code execution
  3. No transitive permission analysis
- **Prevention:**
  1. Audit tool chains for transitive privilege escalation
  2. Use AGT `runtime ring-audit` to detect escalation paths
  3. If agent can write AND execute: treat as having execution privileges in policy

## Mistake #31: SLO-Blind Agent Deployment (OWASP ASI-08)
- **Detection:** Agent system deployed to production without defined latency, error-rate, or cost SLOs. No monitoring dashboard, no alerting thresholds.
- **Example:** Production agent has 8-second p99 latency, no one notices until users complain. Error rate silently climbs to 15%.
- **Root Causes:**
  1. Treating agents as "fire and forget" background processes
  2. No observability infrastructure for agent systems
  3. SLOs defined for the API layer but not for the agent layer
- **Prevention:**
  1. Define SLOs BEFORE deployment: latency p99, error rate, cost per operation
  2. Use AGT `AgentSRE` for monitoring, circuit breakers, and error budgets
  3. Set up alerting: circuit breaker opens → page on-call

## Mistake #32: Unsigned Agent Plugin (OWASP ASI-04: Supply Chain Vulnerabilities)
- **Detection:** Third-party agent plugin/tool loaded without cryptographic signature verification. `pip install random-agent-tool` or `npm install sketchy-agent-plugin` without provenance check.
- **Example:** Installed a community LangChain tool that contains exfiltration code in `__init__.py`, sending agent context to external server.
- **Root Causes:**
  1. Treating agent plugins like regular library dependencies
  2. No supply chain verification process for agent tools
  3. Agent tools have higher blast radius than libraries (they execute with agent permissions)
- **Prevention:**
  1. Verify cryptographic signatures before installing any agent plugin
  2. Use AGT `Marketplace verify` command for signature validation
  3. Audit plugin source code — agent tools are code that runs with YOUR agent's permissions

## Mistake #33: Stateful Agent Without Saga (OWASP ASI-05: Improper Output Handling)
- **Detection:** Multi-step agent workflow with no rollback/compensation on partial failure. Agent performs steps A, B, C sequentially; if C fails, A and B side effects remain.
- **Example:** Agent books a flight (step A), reserves a hotel (step B), fails on car rental (step C). Orphaned flight and hotel bookings with no automatic cleanup.
- **Root Causes:**
  1. Treating agent workflows as atomic when they're actually distributed transactions
  2. No compensation logic for already-completed steps
  3. "Happy path" development — assuming all steps succeed
- **Prevention:**
  1. Use saga pattern: every step has a corresponding compensation/rollback action
  2. Use AGT `AgentRuntime` saga orchestration for automatic rollback
  3. Test partial failure scenarios explicitly — kill the agent mid-workflow and verify cleanup

---

## Runtime Environment Mistakes (LLM Cognitive Blind Spots)

## Mistake #34: Async/Sync Boundary Violation (asyncio.run Trap)
- **Detection:** `grep -rn "asyncio.run(" <project>/` in any file that is NOT a `__main__` entry point. Any `asyncio.run()` call in library code, utility modules, or code imported by async frameworks (FastAPI, aiohttp, Quart).
- **Example:** `telegram_notifier.py` used `asyncio.run(send_message())` in sync wrapper functions. When called from within FastAPI (which has its own running event loop), it crashes with `RuntimeError: This event loop is already running`. The entire API server dies.
- **Root Causes:**
  1. LLM treats `asyncio.run()` as the "simple" sync→async bridge without modeling the caller's runtime context
  2. Code works in isolation (`python script.py`) but fails when imported into an async framework
  3. No consideration of whether the function will be called from sync or async contexts
- **Prevention:**
  1. **NEVER** use `asyncio.run()` in library/utility code. Only permitted inside `if __name__ == "__main__":` guards
  2. For sync→async bridges, use the dual-path pattern:
     ```python
     def sync_wrapper(**kwargs):
         try:
             loop = asyncio.get_running_loop()
             loop.create_task(async_function(**kwargs))  # Inside async context
         except RuntimeError:
             import threading
             threading.Thread(target=lambda: asyncio.new_event_loop().run_until_complete(
                 async_function(**kwargs)), daemon=True).start()  # Outside async context
     ```
  3. Pre-deploy audit: `grep -rn "asyncio.run(" | grep -v "__main__"` must return 0 results

## Mistake #36: Hardcoded Path Injection in Global Skills
- **Detection:** `grep -rn "C:/Users\|/home/\|/c/Users" <skill-dir>/` returns results in instruction files (`.md`). Absolute paths in scripts targeting specific VPS hosts are exempt.
- **Example:** Global skill file references `C:/Users/kobig/Desktop/MyProject/src/main.py` instead of `./src/main.py`. Agent then fails when invoked in any other project or machine.
- **Root Causes:**
  1. Agent copies paths from exploration results directly into skill instructions
  2. Skill written while working on one project, never tested in another
  3. No enforcement gate for path relativity in shared code
- **Prevention:**
  1. **PATH RULE** (PART A0): `./` and `$PWD` ONLY in global skills and shared modules
  2. Before committing any `.md` instruction file: `grep -rn "C:/Users\|/home/\|/c/Users" <file>` must return 0
  3. VPS scripts with real host paths are exempt but must use variables (`$WORKSPACE`, `$REMOTE_DIR`) where possible
  4. Classified as error pattern E11 in `parts/core.md`

## Mistake #35: Single-Writer Database Assumption
- **Detection:** `grep -rn "duckdb.connect\|sqlite3.connect\|connect(" <project>/` shows database connections without explicit `read_only` parameter. Multiple processes/services access the same database file.
- **Example:** KobiiClaw daemon (writer) and FastAPI dashboard (reader) both open the same `.duckdb` file without access mode. When both are running, `IOException: Could not set lock on file` crashes whichever process connects second.
- **Root Causes:**
  1. LLM generates code for a single consumer without modeling the deployment topology (daemon + API + scripts all hitting the same file)
  2. File-based databases (DuckDB, SQLite) have single-writer semantics but this isn't enforced at connection time by default
  3. "It works in development" (single process) doesn't mean it works in production (multiple processes)
- **Prevention:**
  1. Every database connection constructor MUST accept and use an `access_mode` or `read_only` parameter
  2. Readers use `read_only=True`. Only ONE process is the designated writer
  3. If multiple writers are needed, use a database that supports it (PostgreSQL) or implement a write-through API
  4. Pre-deploy audit: map all processes that access each database file. If count > 1, verify access modes are explicit

---

## Cognitive Blind Spot Mistakes (Intent-Lock Protocol Coverage)

## Mistake #37: Silent Quality Degradation (Optimistic Fallback)
- **Detection:** Grep for dual-path code: `if (available) { fastPath() } else { slowPath() }` where the slow/fallback path has no WARNING-level log, no metric emission, and no user notification. The system "works" but at a fraction of intended capability.
- **Example (Java/Minecraft):** FAWE async EditSession (50ms for 384k blocks) silently falls back to BukkitRunnable tick loop (96 seconds) — server lags but doesn't crash, operators don't know FAWE isn't active. **Example (Python/ML):** GPU inference silently falls back to CPU — 100x slower, user sees "working" but responses take minutes. **Example (TypeScript/Web):** CDN cache miss silently falls back to origin fetch — TTFB spikes 10x. **Example (Elixir/OTP):** GenServer silently restarts and loses accumulated state — appears "resilient" but data is gone. **Example (Any stack):** Rate-limited API silently returns cached/stale data instead of failing.
- **Root Causes:**
  1. LLM treats fallbacks as "graceful degradation" without modeling the quality delta between primary and fallback paths
  2. Fallback path logged at INFO instead of WARNING — operators never notice
  3. No metrics/counters on fallback activation — silent production degradation for weeks
  4. "Works" conflated with "works correctly" — the system operates but at unacceptable performance
- **Prevention:**
  1. Every fallback path MUST log a WARNING (not INFO) explaining the degradation and its impact
  2. If fallback is >10x slower or loses data → ABORT with clear error, don't silently degrade
  3. Metrics: fallback activations must be observable (counter, structured log, alert threshold)
  4. Litmus test: "If this fallback runs in production for a week unnoticed, what's the damage?" If damage > trivial → the fallback needs an alert, not just a log line

## Mistake #38: Producer-Consumer Gap (Deferred Wiring That Never Completes)
- **Detection:** For every method that returns a `List<T>`, `Iterator<T>`, emits events, or writes a data file: grep for callers/readers. Zero callers = gap. Distinct from Mistake #1 (orphan file) because the PRODUCER works correctly; the gap is the missing CONSUMER.
- **Example (Java):** `MacroPrefabPlacer.getPendingPlacements()` returns placement instructions for 20 buildings — but no code ever calls it. The schematics are never pasted. **Example (Python):** Signal scorer writes `scored_signals.json` — no downstream reader processes it. **Example (TypeScript):** Redux action type `USER_PREFERENCES_UPDATED` dispatched — no reducer handles it, state never updates. **Example (Elixir):** GenServer casts a `:sync_data` message — no `handle_cast(:sync_data, _)` clause exists, message silently dropped. **Example (Any API):** Webhook endpoint registered at `/webhooks/payment` — no handler function processes incoming payloads.
- **Root Causes:**
  1. LLM builds the producer in one pass, plans to build the consumer "in the next iteration" — but the next iteration never comes or loses context
  2. The producer compiles and tests correctly in isolation, giving false confidence
  3. No gate that asks "who consumes this output?" before claiming the producer is done
- **Prevention:**
  1. When building a producer, the consumer MUST be wired in the SAME session
  2. If consumer is genuinely deferred → flag as `// CONSUMER_MISSING — <what should read this>` in code AND in session summary
  3. Pre-output gate: "For every new data output (return value, file, event, message), who reads it? If nobody → it's not done"
  4. Detection heuristic: any `get*()`, `fetch*()`, `load*()`, `emit()`, or file write without a corresponding call site is a candidate

## Mistake #39: Synchronous Default Trap (Blocking When Async Is Required)
- **Detection:** Grep for sync I/O or blocking calls in async/event-driven contexts: `readFileSync` in Express handlers, `requests.get` in FastAPI async endpoints, `GenServer.call(_, _, :infinity)`, `Thread.sleep` in event loops, `Bukkit.getScheduler().runTask` wrapping heavy computation. The code works in isolation but kills throughput in production.
- **Example (Java/Minecraft):** `block.setType()` called 200x per server tick on the main thread — each call triggers lighting update + chunk dirty flag. 384k blocks = 96 seconds of continuous lag. **Example (Python/FastAPI):** `requests.get(url)` in an `async def` endpoint — blocks the entire event loop, all concurrent requests stall. **Example (TypeScript/Node):** `fs.readFileSync()` in an Express handler — blocks the event loop for ALL requests during file read. **Example (Elixir):** `GenServer.call(pid, msg, :infinity)` — caller process hangs forever if target GenServer is stuck or slow. **Example (Any UI):** Heavy JSON parsing or image processing on the main/UI thread — app freezes, user sees "not responding".
- **Root Causes:**
  1. LLM defaults to the simplest API call without modeling the caller's runtime context (event loop, game tick, UI thread)
  2. Sync version works in unit tests and scripts — failure only manifests under concurrent load
  3. No pre-task declaration of concurrency model → LLM picks sync by default
  4. Framework provides both sync and async APIs — LLM chooses sync because it's fewer lines of code
- **Prevention:**
  1. **API Bounding (Intent-Lock Phase 1):** Before writing code, declare the concurrency model: "I will use X for async, Y for sync boundaries"
  2. Rule: If the runtime has an event loop, main thread, or tick system — ALL I/O and heavy computation goes off-thread. No exceptions.
  3. Fallback prohibition: If an async API exists for the operation, the sync API is PROHIBITED in that context
  4. Detection audit: `grep -rn "readFileSync\|requests\.get\|:infinity\|Thread\.sleep\|runBlocking" <async-context-dirs>/` must return 0 results

## Mistake #40: Type-Semantic Mismatch (Wrong Column in Filter)
- **Detection:** Supabase/SQL query uses a filter where the column's declared type doesn't match the value type. `grep -rn "\.gte\|\.lte\|\.eq\|\.gt\|\.lt" <project>/ | grep -v "test"` — for each, verify column type matches value type (UUID vs string, timestamp vs date, integer vs text).
- **Example:** `supabase.from('rep_metadata').select('*').gte('id', today)` — comparing UUID column `id` to a date string `'2026-04-07'`. Query silently returns wrong results because UUID string comparison is lexicographic, not temporal.
- **Root Causes:**
  1. LLM sees "filter by today" and grabs the first column without checking its type in the CREATE TABLE
  2. Supabase JS client doesn't validate column types at compile time — the query runs but returns garbage
  3. No test exercises the query with production-like data
- **Prevention:**
  1. Before writing ANY Supabase filter (`.eq`, `.gte`, `.lte`, `.in`), verify the column's declared type in the schema
  2. UUID columns: only filter with UUID strings. Timestamp columns: only filter with ISO datetime strings. Text columns: only filter with text
  3. Pre-commit audit: for each `.gte`/`.lte` call, the value type must match the column type in CREATE TABLE

## Mistake #41: Security Amnesia (Zero RLS on Fresh Schema)
- **Detection:** `grep -rn "CREATE TABLE" <migrations>/` count vs `grep -rn "ENABLE ROW LEVEL SECURITY" <migrations>/` count. If tables > RLS enables, security is missing.
- **Example:** 16 Supabase tables created across 3 migrations with zero `ENABLE ROW LEVEL SECURITY` or `CREATE POLICY` statements. The anon key (shipped in the client bundle) grants full read/write access to all data.
- **Root Causes:**
  1. LLM focuses on feature delivery and defers security to "hardening phase" that never happens
  2. Single-user assumption: "only one user, no need for RLS" — but the anon key is PUBLIC, anyone can query
  3. No governance gate that checks RLS count vs table count
- **Prevention:**
  1. Every `CREATE TABLE` in a Supabase migration MUST be followed by `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` and at least one `CREATE POLICY`
  2. Even single-user apps need RLS — the anon key is embedded in the client bundle
  3. Pre-commit audit: count tables vs RLS policies. If tables > policies, BLOCK the commit
  4. RPC functions that bypass RLS must be marked `SECURITY DEFINER` explicitly

## Mistake #42: Hardcode Drift (Inline Constants from DB State)
- **Detection:** `grep -rn "total_skills.*22\|skills_count.*22\|: 22," <project>/` or any inline number that represents a count derivable from the database.
- **Example:** `total_skills: 22` hardcoded in 5 locations across case-study.ts, model-readiness.ts, and framing functions. When a 23rd skill is added to the database, all 5 locations silently report wrong totals.
- **Root Causes:**
  1. LLM knows the current DB state at code-generation time and inlines it as a constant
  2. No test verifies the constant matches the DB count
  3. Constants feel "safe" because they compile — but they drift from source of truth silently
- **Prevention:**
  1. Never hardcode a value that derives from database state (counts, mappings, enums, configurations)
  2. Always query the source of truth. If performance is a concern, cache with a TTL — but the source must be the database
  3. Skill→group mappings, feature flags, category lists: all must come from DB, not inline Records
  4. Detection heuristic: any integer constant that matches a `SELECT COUNT(*)` from a table is a candidate for hardcode drift

## Mistake #43: The Quine Scanner Bug (Self-Referential Detection)
- **Detection:** A scaffold audit / linter / code scanner reports violations in its own source file — specifically in the lines where detection patterns are defined as string literals.
- **Example:** `zero-crash-gate.js` defines `{ regex: /:infinity\b/ }` to detect infinite timeouts. The scaffold audit scans `.js` files, finds the literal `:infinity` in line 82 of its own file, and reports it as a CRITICAL violation. This creates `BLOCKED_DELIVERY.md` with 6 failed fix attempts — because every fix attempt still contains the literal in the pattern definition.
- **Root Cause:** The scanner's pattern definitions are written as readable string literals in a language the scanner also covers. The observer cannot observe itself without interference (Heisenberg applied to linters).
- **Prevention:**
  1. Scanner pattern definitions must be **anti-quine encoded** — break string literals via concatenation so the source text doesn't contain the literal being detected
  2. Fix pattern: `new RegExp(':infin' + 'ity\\b')` — the source file no longer contains `:infinity` as a scannable token
  3. Same for string patterns in Python linters: `r"TO" + r"DO:?\s"` instead of `r"TODO:?\s"`
  4. Audit for this at pattern-creation time: any file that (a) defines regex/string patterns AND (b) is in a language the scanner covers is vulnerable
  5. Test: after adding any new scanner pattern, run the scanner against its own file and verify 0 self-detections

## Mistake #44: Dual-Loader Anti-Pattern (Double Context Injection)
- **Detection:** A hook injects file content via `additionalContext` AND also tells the agent to invoke a skill that loads overlapping content. Both paths fire → same concepts loaded twice → ~2000-5000 wasted tokens per session.
- **Example:** `session-init.js` loads `modules/executionos-lite/core.md` + `modules/governance-overlay/core.md` into context. Then a snippet says "Activate /claude-power-pack" which loads `parts/core.md` + `parts/execution.md` — overlapping governance and execution rules.
- **Root Cause:** Two content-delivery systems (hook injection + skill invocation) built independently, never reconciled. Each assumes it's the sole loader.
- **Prevention:**
  1. One loader per concern — if the hook injects content, it must NOT also ask the agent to invoke the skill (or vice versa)
  2. Hook message should say "content ALREADY loaded" to prevent agent from re-invoking
  3. Audit at integration time: grep for file paths in both hook code AND skill definitions; overlap = violation
  4. Token budget: measure hook injection size + skill load size; if both fire, sum exceeds tier budget

## Mistake #45: Hook Input Blindness (Classifying on Wrong Data)
- **Detection:** A PreToolUse hook classifies task complexity from `tool_input` fields, but the first tool call (usually Read/Glob) contains file paths, not user intent. Result: tier classification is almost always LIGHT regardless of actual task complexity.
- **Example:** User says "refactor the entire auth system" (DEEP tier). First tool call is `Read { file_path: "src/auth.ts" }`. Hook reads `tool_input.content` → empty. `tool_input.command` → empty. Classifies as LIGHT. Loads minimal governance.
- **Root Cause:** PreToolUse hooks receive the tool's parameters, not the user's original message. The hook assumes tool_input contains user intent.
- **Prevention:**
  1. Pull from ALL available data fields: `data.message`, `data.tool_input.description`, `data.tool_input.query` — not just content/command/prompt
  2. Default to STANDARD (not LIGHT) when no keywords match — LIGHT should be opt-in, not the fallback
  3. If the platform provides a SessionStart hook event, use that instead of PreToolUse for classification

## Mistake #46: Overblocking Access to Prevent Duplication
- **Detection:** A "do not re-invoke" or "already loaded" directive blocks a skill/module that contains UNIQUE content not available through the auto-loaded path. Test: diff the auto-loaded content vs the skill content. If the skill has rules/parts not present in the auto-load, the block is too broad.
- **Example:** Hook injects `modules/executionos-lite/core.md` (Constitution Core 5). Message says "Do NOT re-invoke /claude-power-pack". But the skill loads `parts/core.md` (PART A0 Assimilation Scan, E1-E11 Error Patterns, PART Q Leash) — content NOT in modules/. Those rules become inaccessible.
- **Root Cause:** Treating two content systems as fully overlapping when they are only partially overlapping. The anti-duplication fix was correct for the shared subset but overreached by blocking the unique subset.
- **Prevention:**
  1. Before adding "do not invoke" directives, diff the two content sources. Map shared vs unique content.
  2. Use targeted messaging: "Modules X, Y already loaded — skill available for parts Z, W (not in hook)."
  3. Never use blanket "do not invoke" — always specify WHAT is already loaded and WHAT remains available.

## Mistake #47: Success Hallucination (Ley 25 Enforcement)
- **Detection:** A feature touching runtime behavior (UI, gameplay, API, daemon, command handler) is marked "done", "fixed", "ready", or "complete" without a PASS ticket from the Sleepless QA Pipeline (`modules/sleepless_qa/`). The "evidence" cited is compilation success, type checks, or lint cleanliness.
- **Example:** A new `/kobii teleport` command is added. `mvn clean package` succeeds. `tsc --noEmit` is green. The plugin reloads without errors. Claim: "done". Reality: the command's permission check has a typo (`kobii.teleport.self` vs `kobii.teleport.slef`), so ops can use it, players cannot. No one tested it in-game. The bug ships.
- **Root Cause:** Compilers verify syntax, not behavior. Static verification does NOT prove runtime works (extends Mistake #17 — Runtime != Compiles). The author's optimism fills the empirical gap.
- **Prevention:**
  1. Before any "done" emission on runtime-behavior features, the Sleepless QA pipeline MUST have observed the behavior and emitted a PASS ticket for the current run_id.
  2. `tsc --noEmit` / `mvn compile` / `cargo check` passing is a PREREQUISITE, not a verdict.
  3. A feature with zero empirical evidence is a scaffold illusion (Mistake #16 variant) regardless of how clean the diff looks.
  4. Honest alternative when VPS/QA pipeline is unreachable: say "code written, statically valid, **empirical verification pending VPS**". Never collapse the two states into one claim.

## Mistake #48: Zero-Shot Execution (Ley 26 Enforcement)
- **Detection:** Code edits, script modifications, or non-trivial refactors begin without a pre-written Plan of Action (API Bounding + Never-Do Matrix + Atomic Micro-Commit Roadmap + Verification Section). No file in `./.planning/` or `~/.claude/plans/` references the current task.
- **Example:** Owner says "add a retry loop to the webhook sender". Agent immediately opens `webhook.py`, writes a retry loop using `time.sleep(2**attempt)`, ships. Reality: the webhook runs inside an asyncio event loop — sync sleep blocks the whole loop (Mistake #39). A 30-second plan would have caught it; zero-shot didn't.
- **Root Cause:** Familiarity bias. "I've written retry loops before, I don't need to plan this one." The cost of writing a plan (2 minutes) is always less than the cost of a wrong-pattern fix (20+ minutes to diagnose and unwind).
- **Exceptions (plan-free is ok):** Typo fixes, single-line bug fixes, doc/comment tweaks, renaming a local variable, deleting obviously dead code.
- **Prevention:**
  1. Any edit touching >1 file, new functionality, async/concurrent code, or production-risk paths MUST have a plan file approved before the first Write/Edit tool call.
  2. If the agent catches itself editing without a plan, HALT immediately, roll back pending edits if feasible, and enter PLAN MODE.
  3. Plans must include: Oracle (API Bounding), Never-Do Matrix (3+ prohibitions), Roadmap (atomic steps), Verification (what passes = done).

## Mistake #49: Untwinned Feature (Ley 27 Enforcement)
- **Detection:** A new endpoint, UI component, command handler, daemon entrypoint, or state machine transition is added WITHOUT a corresponding `.yml` action script for the Sleepless QA pipeline in the same commit. `git diff --name-only <commit>` shows the code file but no `.yml` twin under `action_scripts/` or the feature's test directory.
- **Example:** A new `/kobii crate` command is added in `CommandRegistry.java` with full business logic and permission checks. Commit shipped. Six weeks later, a refactor breaks the permission check. No QA coverage existed because no `.yml` twin was ever written. The regression ships to production.
- **Root Cause:** "I'll write the test later" is the oldest broken promise in software. Features ship, deadlines tighten, tests never get written. The twin mandate closes that loophole at the commit boundary.
- **Prevention:**
  1. Every new runtime-behavior feature ships with its `.yml` action script in the same commit. Pre-commit hook enforces this at Sprint+ tier.
  2. The `.yml` twin must exercise the feature's primary happy path and at least 1 adversarial case (permission denial, bad input, concurrent caller).
  3. Refactors that rename/relocate a feature must also update the twin's action steps in the same commit.
  4. Exception: pure internal refactors with no behavioral change (e.g., extracting a helper) are exempt, but must be labeled as such in the commit message.

## Mistake #50: Terminal Outsourcing (Ley 28 Enforcement)
- **Detection:** An agent with Bash/shell tool access concludes a work unit by asking the Owner to run commands and report the output, when the agent could have run those commands itself. Symptoms: "please run X and paste the result", "copy the following into your terminal", "I need you to verify this on your side".
- **Example:** Agent finishes building a self-test script. Instead of invoking Bash itself to run `python -m my_module heartbeat` and inspecting the output, it asks the Owner to execute the script and paste back the log. The Owner had to catch the autonomy failure and manually invoke an "Oroboros" correction protocol.
- **Root Cause:** Anxiety about running code with side effects, or defaulting to "helpful advisor" mode instead of "autonomous executor" mode. The agent conflates *caution about destructive operations* (correct) with *refusal to verify its own non-destructive output* (incorrect).
- **Prevention:**
  1. Before emitting any "please run" or "copy-paste this command" ask, check: is this command **non-destructive** AND **runnable with tools I have**? If yes → run it yourself.
  2. Legitimate exceptions (still must be stated explicitly): commands requiring Owner credentials the agent lacks (`gcloud auth login`), destructive ops on shared systems (prod DB `DROP`), commands with interactive prompts.
  3. For infrastructure scripts the agent just wrote: the default is **"I run it, I show the raw output, I interpret the output honestly"** — never "here's the command, tell me what happened".
  4. Even if the command might fail: running it and capturing the failure is MORE valuable than asking the Owner to run it and report success/failure. The agent sees the actual stack trace; the Owner's retelling is lossy.

## Mistake #51: Razonamiento Supuesto (Assumed Reasoning — Ley DNA-400)
- **Detection:** A non-trivial logic change (>20 LOC, cross-module call, state machine, protocol handler, concurrency primitive) is delivered without either (a) a Sleepless QA verdict artifact, or (b) a synthetic test run whose stdout/exit-code was captured in the same session. Model-reasoned correctness claims like "this should work because X implies Y" without an execution trace qualify.
- **Example:** Agent rewrites a retry loop to use exponential backoff with jitter. Reads the calling code, traces the happy path in its head, claims "verified". Never actually runs the loop against a failing endpoint. Ships. At runtime, the jitter multiplier overflows on the 10th retry because a `long` was silently promoted to `int` in a helper call. The model was "reasoning correctly" about a signature it got wrong.
- **Root Cause:** The model's internal world-model drifts from the running system in ways it cannot detect from source alone. Type coercion, library version skew, async scheduler quirks, OS-level edge cases, memory layout, timing — none are visible to pure reasoning. The only SSoT is empirical execution.
- **Prevention:**
  1. Ley DNA-400 (Supremacía Empírica): complex logic must be validated by sandbox execution or synthetic test before delivery. Model reasoning is a vector of error, not a proof.
  2. For any delivery emitting runtime-behavior code, the agent must cite either a `sleepless_qa` verdict.json or attach captured stdout/stderr from a standalone execution.
  3. Cited evidence must be from THIS session, not a recollection of prior runs ("I tested this yesterday" = not evidence).
  4. If sandbox execution is impossible (no runtime, hostile target, destructive side effects), phrase the delivery honestly: *"code reasoned statically; empirical verification deferred to [specific owner step]"* — never collapse reasoning and verification into a single claim.
  5. This mistake pairs with #47 (Success Hallucination). #47 catches claims without a pipeline verdict; #51 catches the earlier step — claims built on reasoning alone before any execution was attempted.

## Mistake #52: Auditor Bug Misattributed to Audited System
- **Detection:** An audit report flags the audited system as defective based on a failure mode caused by the auditor's own ad-hoc tooling, one-liner, or inline script. Symptoms: a recommendation to "fix X" where X is a file/component that works correctly when exercised via its canonical tool, and the "broken" signal came from an auditor-written script that had a bug.
- **Example:** The OVO capability audit (`vault/audits/ovo_2026-04-21T20-57-37Z_A.md`, §12 Recommendation #2) recommended fixing `mistake-frequency.json` because an inline `python -c "... sorted(d.items(), key=lambda x: -x[1]) ..."` one-liner raised `TypeError: bad operand type for unary -: 'str'`. The real cause: the one-liner sorted the whole top-level dict including non-entry keys (`schema`, `threshold`, `last_updated`) instead of scoping to `d["entries"]`. The official `tools/mistake_frequency.py --top 3` ran without error and returned correct output (`M16 count=4, M17 count=3`). The file and its parser were fine; the auditor's ad-hoc script was not. Recommendation #2 of the cited audit report is hereby **RETRACTED**.
- **Root Cause:** Audit velocity pressure leads to ad-hoc verification scripts. When those scripts error, the cognitive default is "the system is broken" rather than "my script is wrong." The error message + the target filename appearing in the same line creates false attribution.
- **Prevention:**
  1. Before declaring any audited component "broken," run its **canonical tool** (the one the system ships with) — not an inline one-liner. If the canonical tool works, the component is not broken.
  2. Inline one-liners during audits are fine for exploration, but findings promoted to report-level recommendations MUST be re-verified via canonical tooling in the same session.
  3. If no canonical tool exists, audit the scaffolding gap itself (Mistake #1 — Building Without Wiring: no consumer for the produced data) rather than attributing parse errors to the data file.
  4. When an audit report is revised for this reason, cite the original (incorrect) recommendation explicitly and mark it RETRACTED with the evidence of the canonical-tool run.
- **Related:** pairs with #17 (Static verification != runtime works) — the auditor's one-liner "compiled" as valid Python but did not exercise the real behavior.

## Mistake #53: Forensic Probe Skipped (RLP / AFHL / CGAR not consulted at FORENSIC tier)
- **Detection:** A FORENSIC-tier OVO audit emits a verdict (A or A+) without a `[FORENSIC_PROBES: ...]` provenance band in the Council block. Equivalent: `tools/forensic_probes.py` was not invoked, OR was invoked but its output was not surfaced to the Council reasoning. `grep -c "FORENSIC_PROBES" <council-text>` returns 0.
- **Example:** A Minecraft plugin delta touches `EconomyHandler.java`. Static OVO grades A on the basis of clean tests. The probes were not consulted. AFHL would have flagged that `EconomyHandler.java` is registered as an NMS-reflection hack whose upstream version (Paper 1.21.4) just exited the registered range (`[1.21.0, 1.21.4)`). RLP would have flagged that the last 10 TPS samples on the dev server show sustained degradation. The static verdict ships; the runtime fails.
- **Root Cause:** OVO's static phases (delta + mistake registry + Council) are agent-driven and complete in a single pass. The forensic probes require an additional tool invocation, and the agent — under context pressure — defaults to the path of least resistance and skips them. The failure mode is identical to Mistake #47 (Success Hallucination) but at the audit layer instead of the build layer: "static is clean, therefore runtime is clean" is the same fallacy whether stated by a developer or an auditor.
- **Prevention:**
  1. At FORENSIC tier, the OVO Phase B exit criterion includes a `[FORENSIC_PROBES: rlp=..., afhl=..., cgar=..., cap=...]` band. The verdict-record tool will reject a verdict A/A+ at FORENSIC tier without this band (future enforcement).
  2. `NOT_CONFIGURED` is a valid emission — it does not block A/A+, but it must be present in the Council block as evidence the probes were *consulted* (and the project simply hasn't opted in).
  3. The probes are advisory below FORENSIC tier — but if the delta touches paths the probes know about (registered hacks, declared cascade nodes), running them is recommended even at STANDARD/DEEP.
  4. See `modules/oracle/ovo-protocol.md § Phase B+` for the canonical invocation.
- **Related:** pairs with #47 (Success Hallucination) and #51 (Razonamiento Supuesto) — both are "claims without empirical evidence." #53 is the audit-layer version: the probes are the empirical evidence at the audit layer.
