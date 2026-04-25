# Sovereign Adapter Plan (MC-ABS series)

**Owner:** kobig · **Started:** 2026-04-25 · **Status:** MC-ABS-0 in flight

## Goal

Let the Power Pack route work through high-value third-party skills (Archon, claude-mem, Moonshot Kimi 2.6, shanraisshan's `claude-code-best-practice`) **without modifying their source**, **without violating their licenses**, and **without shipping skeletons that fake integration**.

Pattern: Composition over modification. Each adapter is a thin wrapper in `lib/adapters/<name>.js` that:

1. Validates the upstream is actually installed and reachable.
2. Translates Power-Pack inputs to the upstream's CLI / API shape.
3. Filters the upstream's output through Power-Pack quality gates (Reality Contract, OVO chaos checks).
4. Surfaces a single error mode when the upstream is absent, so the rest of the pack degrades cleanly.

## Micro-commit ladder

Each row is one atomic commit. Status is the verifiable state right now, not aspiration.

| ID | Title | Files | Status | Blocker |
|----|-------|-------|--------|---------|
| MC-ABS-0 | Compliance foundation | `vendor/NOTICE.md`, `vendor/README.md`, `lib/license_gate.js`, `tests/license_gate.test.js`, installer hooks | **IN FLIGHT this session** | none |
| MC-ABS-1 | Archon adapter + `/archon-run` | `lib/adapters/archon.js`, `commands/archon-run.md`, tests | **BLOCKED** | Need Archon repo URL + actual license file + one verified sample CLI invocation. The "1,500 parallel steps" claim in the v9900 prompt is unverified; treat as marketing until measured. |
| MC-ABS-2 | Kimi 2.6 (Moonshot) routing | `lib/adapters/moonshot.js`, router patch | **BLOCKED** | Need Moonshot API key, endpoint, model ID, and a scope decision: which Power-Pack skills route through K2.6 vs. stay on Anthropic? Wholesale routing breaks prompt-cache discipline and changes cost surface for every command in `commands/`. |
| MC-ABS-3 | shanraisshan design quality layer | `lib/adapters/best-practice.js`, design-token import | **BLOCKED** | Need repo URL, license, and the actual Aurelia/Halcyon token files. v9900 references tokens that aren't in this repo or any cited external location. |
| MC-ABS-4 | claude-mem sync to global vault | `lib/adapters/claude-mem.js`, sync wire to VPS vault | **BLOCKED — and prerequisite blocked too** | Per `MEMORY.md` (handoff 2026-04-25) and commit `6af098e`, claude-mem is installed but its background worker has been dead 46 days. Building a sync adapter on a dead worker = scaffold illusion. The ingestion roadmap (`vault/ingestion/ROADMAP.md`) needs to revive the worker before this adapter can be honestly built. |

## What MC-ABS-0 buys

- A repo-wide policy file that says "we wrap, we don't fork."
- A working detector that reads any path's license and tells the human (or installer) what they're about to integrate.
- An installer pre-flight that surfaces license obligations *before* a vendor copy goes wide.
- Foundation for MC-ABS-1..4: every future adapter calls `license_gate` against its upstream as part of its install path. No license info = no adapter.

## What MC-ABS-0 does NOT do

- Does not block installation. Detection is advisory, not enforcement. Owner-side decision.
- Does not auto-vendor anything. `vendor/` stays empty until an adapter explicitly populates it.
- Does not gate AGPL specifically — that's a *policy* decision the human makes when they see the advisory text. The gate just classifies and reports.

## Unblock checklist for MC-ABS-1 (Archon)

Before the next session attempts MC-ABS-1, Owner provides one of:

- [ ] **Path A:** GitHub URL of Archon + confirmation of license + one CLI invocation that produces visible output on Owner's machine (paste the output).
- [ ] **Path B:** Different first adapter target with the same proof bundle (URL + license + sample run).
- [ ] **Path C:** Explicit decision to defer the entire MC-ABS series and fall back to native Power-Pack skills only.

No proof bundle = MC-ABS-1 stays blocked. The Reality Contract does not allow "Coming Soon" adapters.

## OVO integration

When MC-ABS-1+ ships, each adapter goes through the standard OVO cycle:

1. Council verdict (5 advisors, `modules/governance-overlay/council.md`).
2. Chaos test (`modules/oracle/`) against the wrapped output.
3. Heartbeat / cascade-graph entry in `vault/audits/`.

That's the second quality layer the v9900 prompt requested; it already exists in this repo and adapters reuse it rather than re-implementing.
