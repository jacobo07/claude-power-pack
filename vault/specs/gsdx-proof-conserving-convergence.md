---
status: APPROVED (Owner one-click, 2026-10-07, session 9de9bf3b) -- executing as Ralph mission, workstream gsdx-pcc
tier: T3 (new execution semantics for GSD X; cross-repo baseline)
covers: [gsdx-pcc, proof-conserving-convergence, causal-proof-binding, execution-frontier, verification-amortization, constitutive-baseline-ratchet, proof-certificate, minimal-sufficient-verification, impact-adapter-contract, mutant-farm, latency-observatory]
source: C:\Users\User\Downloads\Dataset GSD X Incremental Construction Runtime 1.md (2111 lines, 46 sections) -- design INPUT, not implementation truth
base: branch gsdx/pcc from feature/knowledge-acquisition@fbca24fc, worktree C:\Users\User\Apps\pp-gsdx-pcc
denominator: .planning/workstreams/gsdx-pcc/DENOMINATOR.md
---

# GSD X -- proof-conserving convergence

## Root function

GSD X minimizes TIME TO PROVEN CONVERGENCE. Quality is a constraint, never a variable:
semantic completeness, proof completeness, evidence strength, Production Reality, judge
independence, security and authority never decrease; UNKNOWN never becomes PASS; unmapped
impact never becomes "unaffected"; fresh-required evidence is never inherited; and no
optimization may hide a failure the incumbent full path detects. Wall-clock is the target;
compute/tokens are budgeted resources (posture ECONOMY | BALANCED | WALL_CLOCK, owned by
the goal budget, never authorising spend the existing policy forbids).

## Reality Scan (2026-10-07; P = read in source, O = observed by running)

1. P `goal/reconcile.decide` returns ONE Decision; WAIT on the first running epoch (reconcile.py:148); only `ungated[0]` is dispatched (:205).
2. P `goal/sweep.sweep_goal` applies one decision per pass (sweep.py:308-390).
3. P `goal/judge.judge` re-runs every SATISFIED gate serially; no VALIDATE path (judge.py:146-179).
4. P Binding is coarser than the dataset assumed: a clean `tree_id` is `HEAD^{tree}` of the WHOLE repository (git_state.py:129-133). Any commit anywhere stales every proof; the reconciler then re-runs them all (`_needs_a_gate_here`).
5. P `tools/change_impact.py` is Python-only (rglob *.py, :37-49), no adapter abstraction; its UNKNOWN is the vendored analyzer's `gaps[]` (exit 3) / UNJUDGED (exit 2).
6. P GK-13 (additive/widening/narrowing/replacing; direct/transitive/frontier) exists ONLY as `vault/knowledge_base/graphify/graphify_13_change_impact_compatibility.md` -- no code. Its classes and the "frontier is undetermined, never clean" rule are adopted here as the adapter contract's vocabulary.
7. P `tools/evidence_bundle.py` binds checks/reviews to sha256 artifact proofs + review ticket nonce; stale review detected by re-reading bytes; NO reusable certificate. Known hole (:140-141): A->B->A between ticket and read passes.
8. P `tools/mutation_probe.py` mutates the LIVE module for 8/10 ratchet pairs; `tools/mutation_drill.py` always works in an isolated temp copy with a control run. The farm builds on the drill's discipline, never the probe's live path.
9. P `modules/parallel_mesh` + `cognitive_os/scheduler` are advisory, fail-open, keyed on Claude pane sids; usable only as pure functions (`decide`, `CollisionDetector`) with synthetic ids.
10. P Constitutive Baseline Ratchet owner = `modules/tower/` (baselines, families, select, ratchet, donegate) + `tools/family_baseline.py`; effect path UserPromptSubmit -> gsd_x_tier.js -> `gsd_x/cli.family_block`. Families: kobiicraft_mode, persistent_state, web_surface, wii_homebrew. donegate is REPORT-ONLY by spec. GOAL WORKERS (`claude -p <brief>`, providers/claude.py:102-139) receive NO family baseline unless hooks fire in -p mode and the brief happens to match vocabulary -> a ratchet gap this mission closes.
11. P UCR-CIF, EDD/Semantic Reality Compiler and SSM/UCWSM/ContextImage have NO code owner on this branch (UCR-CIF "Verification Amortization" lives only in `vault/knowledge_base/ucr_cif/SOURCE_INVENTORY_FULL.json:30150-30169`). Not invented here: the frontier consumes obligations as they exist; brief.py is the ContextImage seam.
12. P UKDL canonical owner = `vault/knowledge_base/ukdl-universal.md` (ids `HR-`/`PR-`/`T-`). The prompt's `knowledge-vault/UKDL/universal-knowledge.md` does not exist.
13. O Baseline suites at fbca24fc: reconcile 22/22, judge 11/11, convergence 29/29, sweep 14/14, epoch 19/19, chaos 15/15, mutation_safety 8/8, **gate_provider 17/18 RED** (pre-existing, 3/3 runs).
14. P+O Root cause of 13: the gate supervisor's `subprocess.run(cmd)` (providers/gate.py:72) passes no std handles; on Windows the grandchild's output never reaches the log -> every gate verdict carries `observed: ''`. Scratch reproduction: 0 B; with explicit `stdout=sys.stdout, stderr=sys.stderr`: 11 B.
15. P Elixir pilot: Owner chose `C:\Users\User\Apps\io-chatgpt-plugin` (InfinityOps umbrella). Scout evidence places the historical "Phase 6" (W4b backlog file targets, MCP writer endpoints) in `C:\Users\User\Apps\io-ucg` (feat/universal-context-gateway, phases 01-09); no "image upload" was found there. Pilot runs on io-chatgpt-plugin; io-ucg is the historical-replay corpus. Neither tree is ever written: both are exercised only through fresh worktrees/copies.
16. O A live Ralph mission (m-9bee7894f20f) writes the main checkout -> this mission lives in its own worktree.
17. P Ecosystem denominator: sdd_os/scaffold.py (Python, Elixir/OTP, Rust, Go, Java Maven/Gradle, Kotlin, Node) + hook-runtime.js markers (composer.json, Gemfile). `auto-testing/detectors.py` knows only Java/Python/Node.

## Owner decisions (2026-10-07)

- D-O1 Arm `/cpp-gsd-long` in worktree `C:\Users\User\Apps\pp-gsdx-pcc`, branch `gsdx/pcc`.
- D-O2 Baseline promotion target: NEW tower family `software_construction` (universal software triggers), entries checked by this mission's V-gates through the existing ratchet/select/report-only donegate; ExecutionOS tier untouched.
- D-O3 Elixir pilot: io-chatgpt-plugin (see Reality 15).
- D-O4 Adapter authority ceiling: PROBATION. TRUSTED needs an explicit Owner go with the shadow report attached; the mission records PENDING_OWNER and continues.
- Budget: 12 cycles / 24 h per marker; re-arming the SAME mission after an honest budget halt is pre-authorised.

## Semantics (W1 ULTRA-PLAN resolves and amends this section; nothing below is final until the W1 audit)

### Proof states (on every obligation at a candidate)
FRESH (produced at this candidate) | INHERITED (certificate validated: claim, revision, gate pin, causal fingerprint, environment, policy all unchanged) | SUPERSEDED (a stronger proof explicitly replaced it) | STALE (a premise changed) | UNKNOWN (premises could not be established) -> FULL re-run. Only FRESH and INHERITED count toward closure; INHERITED always as an explicit `proof.inherited` event naming the certificate.

### Causal fingerprint
A certificate binds the content ids (git blob oids, eol-normalised as `git_state.blob_oid`) of its premise set: gate pin files + the obligation's declared/derived causal paths + adapter-derived dependency closure + toolchain/env fingerprint + proof-policy version. Premise set unknown -> the legacy whole-tree binding applies (no regression vs today). An adapter at SHADOW contributes nothing to inheritance.

### Freshness classes (extend gate_class)
DETERMINISTIC | COMPOSITIONAL | ENVIRONMENT_SENSITIVE | TEMPORAL | FRESH_REQUIRED. Legacy: unit -> DETERMINISTIC only when a causal premise set exists, else whole-tree; integration -> ENVIRONMENT_SENSITIVE; in_game/live and every REALITY obligation -> FRESH_REQUIRED, never inherited. Security/authorization/tenant/destructive/migration/upload claims are FRESH_REQUIRED by policy.

### Frontier
`compile_frontier(ctx) -> Frontier` is a pure projection over the GoalLog: expectation, execution (all justified actions with prerequisites, read/write sets, resource class, exclusivity), proof (what closure still needs), invalidation (what the last candidate staled), critical path (measured priors only; UNKNOWN duration allowed). `decide(ctx)` keeps its signature and returns the frontier's first action. WAIT only when the execution frontier is empty while epochs are in flight.

### Judge
VALIDATE an inherited certificate independently (re-derive the fingerprint at the judged tree, re-verify pins, policy, freshness class) or REPLAY. Independent REPLAYs run concurrently under a resource bound. Builder-cannot-judge, pin re-verification, worktree==tree and PASS/REFUSED/UNJUDGEABLE all stay.

### Shadow law
If the incumbent full path detects a failure the optimized path would have declared covered, the optimization path failed: regression fixture, adapter -> DEGRADED, certificate invalidation, UKDL candidate. Selective omission is never authorised above the adapter's maturity (ceiling PROBATION, D-O4).

## Done-gate (final)
`python tools/gsdx_pcc_done.py` exit 0 -- aggregates the named gates in ROADMAP "Final done-gate", requires every DENOMINATOR row dispositioned with evidence, and a clean worktree. Never weakened to finish.

## Rollback / kill switches
`GSDX_FRONTIER=off` -> decide() uses the legacy scalar path; `GSDX_PROOF_INHERITANCE=off` -> every proof re-runs (whole-tree binding); adapter state DISABLED by event. All new events are additive; old goal logs replay unchanged (W1 proves this).
</content>
</invoke>
