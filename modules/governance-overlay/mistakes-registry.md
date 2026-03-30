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
