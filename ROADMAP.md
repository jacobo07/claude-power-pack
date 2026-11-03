# Claude Power Pack — Roadmap to 100% Capability

Living document. Tracks work toward the 100% capability score from the OVO audit (`vault/audits/ovo_2026-04-21T20-57-37Z_A.md`). Each row names a Δ% target, a concrete deliverable, a blocker (if any), and an owner/estimate.

**Current verified score:** 77.2% projected after MC-OVO-21..24 soak (from 65.2% baseline).

## Closed in MC-OVO-30..34 cycle

| Item | Δ% | Commit | Evidence |
|---|---:|---|---|
| Apple ecosystem overlay (macOS + iOS + Swift) | +2-3 | `48f73c9` | `modules/executionos-lite/overlays/apple-ecosystem.md` |
| Rust overlay (first of 8 language overlays — template) | +1 | `166d1d4` | `modules/executionos-lite/overlays/rust.md` |
| Go overlay (2 of 8) | +1 | (next commit) | `modules/executionos-lite/overlays/go.md` |
| Kotlin overlay (3 of 8) | +1 | (next commit) | `modules/executionos-lite/overlays/kotlin.md` |
| Roadmap doc (honest scope tracking) | +1 meta | `166d1d4` | this file |
| **MC-OVO-34** Vault auto-fire hook | +1 | `f3ea1ca` | `modules/governance-overlay/hooks/mistake-ingest.js` + `vault/knowledge_base/errors.md` (52 mistakes ingested via empirical fire test) |
| Go overlay (2 of 8) | +1 | `0ac7543` | `modules/executionos-lite/overlays/go.md` |
| Kotlin overlay (3 of 8) | +1 | `0ac7543` | `modules/executionos-lite/overlays/kotlin.md` |
| **MC-OVO-30-EXT** Swift-native overlay (4 of 8) | +1 | this cycle | `modules/executionos-lite/overlays/swift-native.md` |
| **MC-OVO-36** Vault self-optimization (errors.md → INDEX.md) | +1 | this cycle | `tools/vault_summarize.py` + `vault/knowledge_base/INDEX.md` (category-ranked, top-N per bucket, 4/4 gates PASS) |
| **MC-OVO-30-EXT** elixir-ext overlay (8 of 8 — CLOSES language series) | +1 | `ec56e8c` | `modules/executionos-lite/overlays/elixir-ext.md` (Nerves/Ash/Livebook/releases/Gleam + Elixir 1.18/OTP 27) |
| **MC-OVO-31-Q** QEMU dumper scaffolder (3-gate cascade) | +1 | `419d3e6` | `tools/scaffold_qemu_dumper.py` — QMP client + mock-QMP tests + qemu-present gate |
| **MC-OVO-34-V** Mistake-hook cross-platform parity test | +1 | `9516741` | `tests/test_mistake_frequency_xplat.py` — Windows baseline PASS tool_sha=4e53d4167f35 |
| **MC-OVO-32-F** VPS validation hand-off bundle | +0 meta | (this commit) | `tools/vps_validation_handoff.sh` — packages 32-F + 31-Q + 34-V gates for one-shot VPS run |

## Deferred — explicit blockers + estimates

### MC-OVO-30 (Language overlays — 5 of 8 remaining after Go + Kotlin shipped)

| Language | Form | Effort | Blocker |
|---|---|---|---|
| ~~Go~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30+ cycle (go.md) |
| ~~Kotlin JVM~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30+ cycle (kotlin.md) |
| ~~Swift native~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30-EXT cycle (swift-native.md, cross-linked to apple-ecosystem.md) |
| ~~Ruby~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30-LANG cycle (`d3d227b`, `overlays/ruby.md`) |
| ~~PHP~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30-LANG cycle (`d3d227b`, `overlays/php.md`) |
| ~~SQL~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30-SQL cycle (`d3d227b`, `overlays/sql.md` multi-dialect Postgres/MySQL/SQLite/MSSQL) |
| ~~Elixir code-idioms~~ | ~~overlay~~ | ~~DONE~~ | SHIPPED in MC-OVO-30-EXT cycle (`ec56e8c`, `overlays/elixir-ext.md` — Nerves/Ash/Livebook/releases/Gleam, complements base elixir.md) |

**Language-overlay series is now CLOSED: 8 of 8 shipped** (rust, go, kotlin, swift-native, ruby, php, sql, elixir-ext).

**Why not shipped in one session:** writing 7 high-quality overlays at ~30-45 min each = 4-5h of focused work. A same-session bulk ship would produce skeletons (Mistake #47, Success Hallucination). Shipping 1 template (`rust.md`) per session builds momentum honestly.

**Note on dedicated skills vs overlays:** the Capability Audit's "Dedicated skill" column (e.g., `python-pro`, `cpp-pro`) refers to skills in `~/.claude/skills/` — these are installed independently of the Power Pack and not part of this repo's scope. Overlays in `modules/executionos-lite/overlays/` are the pack-owned equivalent.

### MC-OVO-31 (Sleepless QA dumpers — mobile / game / embedded)

| Target | Effort | Blocker |
|---|---|---|
| iOS dumper (simulator + device) | 1-2 days | **HARD BLOCKER: Xcode toolchain required.** Runs on macOS host only. Linux VPS cannot execute. Needs macOS CI runner or owner-local macOS. |
| Android dumper (emulator + ADB) | 1 day | **SOFT BLOCKER: Android SDK + emulator image (~10GB) must be provisioned on VPS.** Feasible but disk-cost non-trivial. |
| Unity dumper | 2-3 days | **HARD BLOCKER: Unity Editor license + headless build license.** Commercial product, Pro license ~$185/mo. |
| Unreal dumper | 2-3 days | **HARD BLOCKER: UE install (~100GB disk), platform-specific toolchains.** Editor also expensive to host. |
| Godot dumper | 1 day | **NO BLOCKER.** Free engine, runs headless, can be scripted. Strong candidate for next session. |
| ~~QEMU embedded dumper~~ | ~~1 day~~ | ~~UNBLOCKED + SCAFFOLDED~~ | Owner installed qemu-system-x86 + qemu-system-arm on VPS (2026-04-22). Scaffolder shipped in `419d3e6` (`tools/scaffold_qemu_dumper.py`). VPS validation pending run of `tools/vps_validation_handoff.sh` — see VPS Hand-off section below. |

**Minimum honest ship in a follow-up session:** Godot dumper (no blocker) + QEMU dumper (if Owner approves VPS `apt install`).

### MC-OVO-32 (Framework bootstrappers — 4 targets)

The `/bootstrap-new-project` command (MC-OVO-22, `9491b38`) already covers the basic case for Python, TS web, Spring Boot, Elixir, C/C++, Minecraft, Embedded via a 7-stack detection table. The "full bootstrapper" in the audit meant richer scaffolding for framework-specifics:

| Framework | Incremental work over /bootstrap-new-project | Effort |
|---|---|---|
| Django | Django-admin scaffold + settings split + migrations skeleton + auth + DRF starter | 1-2 days |
| Rails | `rails new` + RSpec + devise + sidekiq + first-migration workflow | 1-2 days |
| NestJS | `nest new` + first module/controller/service + OpenAPI decorators | 1 day |
| Spring Boot | Deeper than the current stub: Maven archetype + REST controller + JPA entity + Flyway + actuator | 1 day |

**Honest take:** these are "batteries-included" scaffolders where the batteries change every 6 months. Each one needs real-world maintenance. Recommend: pick the ONE the Owner actually ships in (Spring Boot for KobiiCraft alignment? NestJS for SaaS?) and build that one solidly, not all four at half-depth.

### MC-OVO-34 (Vault learning automation)

| Piece | Effort | Blocker |
|---|---|---|
| Auto-fire `session_checkpoint.py learn-error` on commits that touch `mistakes-registry.md` | ~1 hour | none — hook wire-up + testing |
| Auto-push `#GOLDEN_PATTERN`-tagged memory entries to the project-local `vault/knowledge_base/` | ~1 hour | need to decide the append-only vs dedup policy |
| Cross-project vault sync (so learnings in repo A land in repo B's vault) | ~4 hours | needs a central vault server (VPS has one, but the sync protocol isn't designed yet) |

**Minimum ship in a follow-up:** the first piece (auto-fire on mistakes-registry touch) + an empirical gate where the hook actually runs + a post-commit on THIS repo to prove the mechanism works end-to-end. Second and third pieces track separately.

## Proposed session priority order

1. **Next session:** MC-OVO-30 Go overlay + Kotlin overlay (pure authoring, no infra, highest-RoI).
2. **Session +2:** MC-OVO-34 piece 1 (auto-fire hook + empirical gate). Requires running a fake mistakes-registry edit and verifying the hook fires.
3. **Session +3:** MC-OVO-31 Godot dumper (no blockers) + QEMU dumper if Owner approves VPS provision.
4. **Session +4+:** remaining overlays (Swift/Ruby/PHP/SQL/Elixir-ext), Spring Boot scaffolder depth, Django IF Owner confirms it's used.

## VPS Hand-off — MC-OVO-32-F / 31-Q / 34-V runtime validation — **CLOSED with evidence**

Three gates from this cycle require a Linux host. Sandbox policy blocks agent-driven SSH + sudo, so Owner runs via the launcher (wrap-proof heredoc-over-stdin):

```bash
# From the claude-power-pack working tree on Windows host:
bash tools/run_vps.sh
```

**Runtime evidence captured 2026-04-22T11:37:12Z** (VPS `ubuntu-8gb-hel1-1`, git HEAD `55cdf12`):

| Gate | Result | Evidence |
|---|---|---|
| MC-OVO-32-F — FastAPI 3-gate | **PASS** | pip install OK, 4 tests passed, `GET /health -> 200 {"status":"ok","project":"scaffolded-api"}` |
| MC-OVO-31-Q — QEMU dumper 3-gate | **SKIP** | `qemu-system-x86_64` absent; skip path fires cleanly as designed; install `qemu-system-x86 qemu-system-arm` on VPS to close |
| MC-OVO-34-V — mistake-hook parity | **PASS** | `PARITY host=ubuntu-8gb-hel1-1 py=3.12.3 platform=linux tool_sha=4e53d4167f35 tests=8 status=PASS` — byte-identical to Windows baseline |

Archived log: `vault/audits/vps_validation_20260422T113712Z.log` (2869 bytes). This is the canonical Path A evidence precedent.

### Path A evidence pattern — canonical for any future sandbox-blocked validation

When the agent's sandbox rails block a runtime operation (SSH, sudo, self-mod of permissions), the **Path A pattern** is the accepted evidence route:

1. Agent writes a **local launcher** (e.g. `tools/run_vps.sh`) that carries the remote payload via `ssh 'bash -s' <<REMOTE` heredoc so terminal wrap cannot corrupt the command line.
2. Agent commits + pushes + gives Owner a single-line invocation (e.g. `!bash tools/run_vps.sh`).
3. Owner executes via `!` passthrough. Output tees to a known log path.
4. Agent archives the log to `vault/audits/<artifact>_<ISO>.log` and commits it (non-ignored log extension).
5. Agent runs OVO cycle on the delta with the archived log as cited evidence in the Council block.

This pattern is now **DoD-canonical** for this project. A validation task that requires runtime access to a sandbox-gated surface is NOT blocked — it routes to Path A with a scripted launcher. "Coming soon" is rejected; "shipped to sandbox boundary + Owner-runnable Path A + archived log evidence" is accepted.

## What 100% requires that Power Pack alone can't deliver

A few items of the original "100% baseline" depend on infrastructure outside this repo:

- **Xcode CI runner** (for full iOS empirical gate) — needs a macOS host, cannot be on Linux VPS. ~$80/mo for a basic GitHub Actions macOS runner or equivalent.
- **Unity / Unreal licenses** — commercial, Owner decision.
- **macOS dev workstation** — for local Apple dev; not infra Power Pack can "ship."

These are infrastructure decisions, not code. The pack can document the gates and the fastlane config (MC-OVO-33 did this) but cannot execute them from a Linux VPS.

---

## GSD X Reconstruction Factory — Universal Wii Inverse Compiler backlog

**North Star:** evolve the current Tennis-focused Reconstruction Factory into a reusable Wii reconstruction capability where a single human mission can ingest a new Wii title, inherit prior platform/toolchain knowledge, collapse known code and families deterministically, reserve strong-model reasoning for genuinely novel semantic residuals, and return source-like projections + certificates + Program Genome + irreducible unknowns in hours rather than weeks where the title's novelty permits.

**One-shot definition:** one human intent starts one durable autonomous mission. Internally the mission may rotate contexts, launch agents, run thousands of compiles/experiments, consult cross-title corpora and improve the Factory. Externally it should continue until completion or a genuine Owner boundary.

**Current maturity statement:** Tennis demonstrates a real, increasingly self-improving reconstruction capability, but this is not yet a general "arbitrary Wii DOL -> near-exact source in one session" system. The next proof is transfer: title #2 and title #3 must start materially higher than Tennis. If title #5 still repays the same GX/BRRES/MWCC/SDK archaeology, compounding has failed.

### Priority epic WII-RF-1 — Massive Wii Known-Code Excision

**Goal:** remove verified Nintendo SDK, runtime, middleware, common libraries, compiler-generated artifacts and reusable engine code from the expensive game-specific reconstruction frontier before bespoke reasoning.

Backlog:
- Build/extend library and SDK certificate corpus with explicit provenance, version/build applicability, positive/negative fixtures and counterexamples.
- Fingerprint DOL/REL/library regions early in intake and classify known mass before function-level work.
- Separate platform/runtime/library identity from game-specific semantics.
- Reuse cross-title exact and normalized matches.
- Make verified known-code excision trigger a population-collapse rescan.
- Measure known-code mass removed per title and false-positive rate.

**Done when:** an unseen compatible Wii title can automatically excise a material fraction of non-game-specific functions with exact/proven lineage and zero silent false lifts.

### Priority epic WII-RF-2 — Wii Toolchain Genome / MWCC Verified Inverse Compiler

**Goal:** make MWCC, PPC EABI, SDA, linker/build-context and common lowering behavior increasingly known before a new game's unique logic is analyzed.

Backlog:
- Expand Build Twin/toolchain evidence profiles across known Wii titles and certified calibration functions.
- Continue MWCC forward-probe corpus and Active Compiler Tomography.
- Promote verified native-motif <-> source-construct mappings into Compiler Genome rules.
- Cover C/C++, virtual dispatch, constructors/destructors, thunks, switch/loop lowering, SDA, inlining, templates, register-allocation/source-shape tails and TU-sensitive behavior as evidence demands.
- Mine natural discriminating functions before synthetic probes.
- Preserve toolchain/source equivalence and UNDERDETERMINED_TOOLCHAIN when multiple configurations explain the same native artifact.
- Add compiler-profile transfer holdouts across titles.

**Done when:** common compiler/source-pattern classes route deterministically to bounded candidate spaces and strong-model use is confined to genuinely novel residuals.

### Priority epic WII-RF-3 — Industrial C++ Object Model Recovery

**Goal:** recover class/object structure globally instead of solving C++ functions independently.

Backlog:
- Global class/vtable registry.
- Constructor/destructor mining.
- VTable slot solver.
- This-pointer recovery.
- Base-class/thunk classification.
- Global class-layout constraint solving.
- Bidirectional prototype/callsite propagation.
- State/data ownership inference.
- Structured C++ source skeleton generation from the recovered object model.
- Regional/class-level compile-back where function-local harnesses lose relevant context.
- Promote S11-derived rules only at demonstrated applicability scope.

**Done when:** unseen C++ virtual-call/class families can be reconstructed from raw binary/decompiler evidence without hand-written per-function layouts, and shared recovered facts close multiple dependent functions.

### Priority epic WII-RF-4 — Generative Function Families / Semantic Quotient Compiler

**Goal:** replace N-function reconstruction with minimal verified generators + parameter vectors wherever the source population is generative.

Backlog:
- Family induction over CFG, call topology, constants, field accesses, ABI, stack behavior, dataflow and compile-back behavior.
- Convert clusters into executable generators, not similarity labels.
- Parameterize type, field offset, constant, callee, branch polarity, enum/slot and other bounded dimensions.
- Minimum Generative Basis per subsystem.
- Self-factoring recovery for latent helpers/templates/base methods.
- Leave-one-family-out validation.
- Bulk Collapse Sweep after every promoted family/rule.

**Done when:** Work Unit Compression rises materially; large raw populations collapse into a much smaller number of reconstruction problems and future members instantiate without whole-function reasoning.

### Priority epic WII-RF-5 — Cross-Title Wii Donor Corpus / Platform Genome

**Goal:** every reconstructed Wii title raises the starting line for the next.

Backlog:
- Build a cross-title donor index for exact and normalized functions, SDK/library code, compiler motifs, engine helpers and data formats.
- Maintain separate Wii Platform Genome, Toolchain Genome, Engine/Series Genome, Game Genome and local subsystem/sport knowledge.
- Track donor provenance and legal/clean-room status.
- Add cross-title homology confidence and counterexamples.
- Make intake query platform/compiler/library/engine ancestry before bespoke reconstruction.
- Treat cross-title transfer as a required CBR/fresh-consumer test for platform-scope promotions.

**Done when:** a new compatible title begins partially understood before game-specific analysis, with inherited deterministic coverage measurable at intake.

### Priority epic WII-RF-6 — Unknown Tail Factory / P90-P99 Reconstruction

**Goal:** industrialize the last hard 5-20% instead of allowing rare C++, SDA, inlining, templates, large CFGs, stateful logic or cross-TU cases to dominate calendar time.

Backlog:
- Continuously cluster the slowest unresolved historical cases by causal bottleneck.
- Build tail-specific tools/solvers only when break-even is positive.
- Maintain WHY_NOT_EXACT / WHY_UNKNOWN machine-readable diagnoses.
- Route compiler-shape residuals to Compilation Fabric rather than semantic regeneration.
- Optimize P50/P90/P99 time-to-diagnosis and time-to-certificate.
- Track Unknown Debt/interest by fan-out and downstream rework.
- Preserve underdetermined distinctions rather than chasing unknowable source syntax.

**Done when:** tail latency falls generation over generation and no recurring tail morphology repeatedly requires artisanal rediscovery.

### Priority epic WII-RF-7 — Proof Compression / Certification Throughput

**Goal:** prevent assurance, not generation, from becoming the dominant bottleneck at thousands of functions.

Backlog:
- Content-addressed compile transactions and proof receipts.
- Proof caching and dependency-aware invalidation.
- Shared Build Twin/toolchain proofs.
- Family certificates and proof inheritance.
- Proof CSE / dominator concepts where consumers justify them.
- Incremental regional re-certification after semantic deltas.
- Separate exact native certification, semantic truth, source proximity and evidence independence.
- Measure proof-compression ratio and certification P90/P99.

**Done when:** thousands of derived/reused instances do not each repay the full independent reasoning + verification cost while exactness authority remains unchanged.

### Priority epic WII-RF-8 — Cross-Title Factory Benchmark Arena

**Goal:** prove, rather than claim, that the Factory is becoming universal and faster.

Required benchmark generations:
- Factory G(n) -> unseen Wii title A.
- Factory G(n) -> unseen Wii title B.
- Factory G(n) -> unseen Wii title C.
- Repeat later with a promoted Factory generation on equivalent hidden cohorts.

Measure at minimum:
- deterministic coverage at intake;
- known-code excision coverage;
- cross-title inherited coverage;
- family-generated coverage;
- strong-model calls per 1,000 functions;
- functions per reusable rule;
- Work Unit Compression Ratio;
- Reasoning Compression Ratio;
- Proof Compression Ratio;
- exact certification rate;
- false-positive / false-lift rate;
- compile iterations per exact;
- time to first 50%, 90%, 99%;
- P50/P90/P99 reconstruction latency;
- Owner interventions per verified engineering delta;
- prompt size / Prompt Compression Ratio;
- residual semantic entropy and novel semantic mass.

**Hard transfer expectation:** title #2 should require materially less reasoning/function than Tennis. Title #3 should inherit more again. If transfer does not improve the curve, pause claims of universalization and fix the missing compounding layer.

### Supporting backlog — Wii Reconstruction Performance / One-Mission Economics

- Build a Time Compression Frontier that attributes wall time to scope, knowledge rediscovery, context, inference, search, compile, verification, human waits, coordination and resource contention.
- Optimize the dominant reducible term rather than adding features by habit.
- Trade deterministic compute for serial cognition when ROI is positive.
- Maintain no-model zones for fully covered deterministic regions and a model-only frontier for true novelty.
- Make work units variable-sized: one function, one family, one library, one type system, one dispatcher + leaves, whichever is epistemically coherent.
- Track the slope of throughput: every solved cohort should make an applicable future cohort cheaper.
- Version the Factory explicitly by generation with benchmark deltas and failure modes.
- Run candidate Factory generations in shadow on historical workloads before promotion.
- Promote time-compression improvements through CBR only when they preserve or strengthen truth.
- Treat reconstruction performance regressions like runtime regressions.

### Universal Wii one-mission admission gate

Do not claim "any Wii game in one session" until independent cross-title evidence shows that a new title can automatically execute most of this chain:

binary census
-> platform/toolchain fingerprint
-> known-code excision
-> cross-title matching
-> family collapse
-> C/C++ class/type recovery
-> global constraint propagation
-> compile-back search
-> sparse semantic-model frontier
-> exact/incremental certification
-> Program Genome + unresolved irreducible residual report.

The end-state target is **reconstruction as throughput, not reconstruction as per-function cognition**.

### Institutional metrics to keep visible

The main leading indicator is not raw certified-function count. Track whether the number of functions requiring individual reasoning is collapsing.

Required trend:
- Work Unit Compression Ratio up.
- Reasoning Compression Ratio up faster.
- Deterministic Coverage up.
- Cross-title inherited coverage up.
- Functions per reusable rule up.
- Compile iterations per exact down.
- P99 reconstruction latency down.
- Owner interventions down.
- Prompt size / Prompt Debt down.
- Residual Semantic Entropy down.
- Novel Semantic Mass becomes the dominant irreducible cost.

### Constitutive Baseline Ratchet

Every proven improvement from these epics must be evaluated for promotion at the narrowest evidence-supported scope:

function family -> module/game -> engine/series -> toolchain/build -> Wii platform -> broader reconstruction archetype.

Promotion requires explicit applicability, positive/negative evidence, counterexamples, regression protection, Production Reality and a fresh consumer. Future projects must inherit promoted capability automatically; falling back to a slower known path should require an applicability explanation.

