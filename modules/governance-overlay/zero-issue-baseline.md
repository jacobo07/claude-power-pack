# Zero-Issue Delivery Baseline

> Loaded for STANDARD, DEEP, and FORENSIC tiers. ~250 tokens. The universal minimum standard for ALL software delivery.

## Principle

**If a system compiles but isn't complete, functional, and issue-free — it's a failure. Deliver nothing.**

"Complete" means: every defined route/endpoint responds, every UI screen renders, every data flow persists, every integration connects. Not "code exists" — **code works.**

## Cascade Verification Gates (run in order, stop on first failure)

### Gate 1: Static Analysis (per stack)
| Stack | Command | Pass |
|-------|---------|------|
| TypeScript | `npx tsc --noEmit` | 0 errors |
| Python | `mypy --strict` or `python -m py_compile` | 0 errors |
| Elixir | `mix compile --warnings-as-errors` | 0 errors, 0 warnings |
| Rust | `cargo check` | 0 errors |
| Go | `go vet ./...` | 0 errors |
| Java | `mvn compile` | 0 errors |

### Gate 2: Build
| Stack | Command | Pass |
|-------|---------|------|
| Next.js | `npx next build` | All routes generated |
| Expo | `npx expo export` | Passes |
| Phoenix | `mix compile` | Passes |
| Python | `pip install -e .` or equivalent | Passes |
| Docker | `docker build .` | Image created |

### Gate 3: Scaffold Audit (0 CRITICAL violations)
Scan all modified files for:
- Commented-out module wiring / supervision children
- `:infinity` / `Infinity` timeouts
- `raise "not implemented"` / `TODO` / `FIXME` placeholders
- Empty `catch` / `rescue` blocks
- Zero-retry external calls
- Unimported files (created but never consumed)
- Hardcoded absolute paths in global skills/shared modules (E11 — `C:/Users/`, `/home/`, `/c/Users/`)

### Gate 4: Tests (if test suite exists)
- `npm test` / `pytest` / `mix test` → all pass
- If no test suite: flag as risk, do not block, but note "0 tests — risk"

### Gate 5: End-to-End Functional Verification
**This is the gate that was missing.** "Compiles + builds" is necessary but NOT sufficient.

For web apps:
- Start the dev server → confirm it boots without errors
- Hit the main route → confirm HTTP 200 with expected content
- Hit each API endpoint → confirm data returns from DB
- If multi-stack (e.g., Phoenix + Next.js): BOTH must pass independently

For libraries:
- Import the module → confirm no runtime errors
- Call the primary public function → confirm expected output

For CLI tools:
- Run `--help` → confirm output
- Run the primary command → confirm expected behavior

For backend services:
- Boot the server → confirm listening
- Hit health endpoint → confirm 200
- Hit primary endpoint → confirm data flow

**If end-to-end verification cannot be performed** (no server access, no test environment): document exactly what was verified and what wasn't. Never claim "done" for unverified functionality.

## Multi-Stack Projects

When a project has multiple stacks (e.g., Phoenix API + Next.js frontend + Supabase DB):

1. Run Gates 1-4 for EACH stack independently
2. Run Gate 5 for the integrated system
3. ALL stacks must pass ALL gates. One stack failing = entire project fails.

## Kill-Switch Words

The words **"done", "complete", "ready", "fixed", "listo", "passing", "working"** require:
1. Evidence from running Gates 1-5
2. Output pasted or summarized (not "should work")
3. Any gate failure acknowledged and fixed before the word is used

## Escalation

| Consecutive failures | Action |
|---------------------|--------|
| 1 | Block delivery. Fix the issue. Re-run gates. |
| 2 | Block delivery. Log the pattern. Consider different approach. |
| 3 | Create `BLOCKED_DELIVERY.md`. Stop all work. Ask user for direction. |

## Completeness Definition

A system is "complete" when ALL of the following are true:
- [ ] Every route/endpoint defined in the codebase returns a response (not 404/500)
- [ ] Every UI screen renders without console errors
- [ ] Every form/input submits and the result persists
- [ ] Every integration (DB, API, auth) connects and returns data
- [ ] Every async operation has error handling and timeout
- [ ] No placeholder text or TODO markers in user-visible UI
- [ ] Mobile responsive (if web) — tested at 375px minimum

A system that compiles but fails any of the above is **NOT complete** and must NOT be delivered.
