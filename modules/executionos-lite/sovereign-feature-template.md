# Sovereign Feature Template (Ley DNA-400)

> Use this template for any DEEP+ feature brief. All four bracketed sections are MANDATORY. A brief missing any section is rejected at the pre-task gate.

## [CONTEXT]

- **Problem:** <what real constraint or user-visible gap prompted this?>
- **Why now:** <deadline, incident, compounding risk — the forcing function>
- **Target outcome:** <observable, measurable — "X endpoint returns Y under load Z" not "improve performance">
- **Out of scope:** <what this feature does NOT change — prevents scope creep>

## [PRE_FLIGHT_TEST]

A test/script written and executed BEFORE implementation begins. Its initial failure defines the goal; its eventual pass defines completion.

- **Location:** `<repo>/tests/sanity/<feature_name>.{sh,py,mjs}`
- **What it exercises:** <the minimum input→process→output path that must work>
- **Success criterion:** exit code 0 AND <specific observable: file contents, HTTP status, log line, verdict.json key>
- **Failure mode before implementation:** <what exit code / stderr the test produces today — this is the baseline>

If you cannot write a pre-flight test, the feature is not well-enough specified to build. Stop and refine `[CONTEXT]`.

## [VALIDATION_GATE]

Empirical evidence required before emitting a completion claim. At least ONE must be cited in the delivery message:

- [ ] `sleepless_qa` verdict: `~/.claude/sleepless-qa/runs/<run-id>/verdict.json` with `status=PASS` produced in this session
- [ ] Pre-flight test transitioned from FAIL → PASS; stdout/exit-code captured and pasted in delivery
- [ ] For destructive or remote-only logic: deferred verification with explicit owner step documented

Pure model reasoning ("this should work because…") is explicitly rejected as evidence (see Mistake #51).

**Additional gates that apply automatically:**
- Tier-appropriate mistake scan from `governance-overlay/pre-output.md`
- Zero-issue gate (`zero-crash/hooks/zero-crash-gate.js`)
- Language Fragility Gate if new backend/infra code (score >=4 = Elixir default or LDR)

## [DNA_UPDATE]

What this feature teaches the system. Exactly one of:

- **New law / amendment:** "Added Ley X (summary)" — append to relevant governance file
- **New mistake recorded:** "Registered Mistake #N (summary)" — append to `mistakes-registry.md`
- **Golden pattern:** tag reusable pattern with `#GOLDEN_PATTERN` via `memory-engine/append_memory.py --tag GOLDEN_PATTERN`
- **None — pure maintenance:** explicitly stated. Maintenance features don't always teach; forcing a fake lesson is worse than no lesson.

---

## Template Usage

1. Copy this file structure into the feature's plan document (`~/.claude/plans/<name>.md` or `.planning/...`).
2. Fill every bracketed section before writing code.
3. Run the `[PRE_FLIGHT_TEST]` once to capture baseline failure.
4. Implement until the test passes.
5. Run the `[VALIDATION_GATE]` checks and paste evidence into the delivery.
6. Execute the `[DNA_UPDATE]` write.
