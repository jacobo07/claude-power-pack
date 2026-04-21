# Claude Power Pack — Roadmap to 100% Capability

Living document. Tracks work toward the 100% capability score from the OVO audit (`vault/audits/ovo_2026-04-21T20-57-37Z_A.md`). Each row names a Δ% target, a concrete deliverable, a blocker (if any), and an owner/estimate.

**Current verified score:** 77.2% projected after MC-OVO-21..24 soak (from 65.2% baseline).

## Closed in MC-OVO-30..34 cycle (this session)

| Item | Δ% | Commit | Evidence |
|---|---:|---|---|
| Apple ecosystem overlay (macOS + iOS + Swift) | +2-3 | `48f73c9` | `modules/executionos-lite/overlays/apple-ecosystem.md` 55 lines, pattern-match with android-native.md |
| Rust overlay (first of 8 language overlays — template) | +1 | (this commit) | `modules/executionos-lite/overlays/rust.md` |
| Roadmap doc (honest scope tracking) | +1 meta | (this commit) | this file |

## Deferred — explicit blockers + estimates

### MC-OVO-30 (Language skills / overlays — 7 of 8 remaining)

| Language | Form | Effort | Blocker |
|---|---|---|---|
| Go | overlay (`overlays/go.md`) | ~30 min | none — pure authoring, next session |
| Swift native | overlay (`overlays/swift-native.md`) | ~45 min | needs Apple-ecosystem overlay cross-links — can now build |
| Kotlin JVM | overlay (`overlays/kotlin.md`) | ~45 min | none — next session |
| Ruby | overlay (`overlays/ruby.md`) | ~30 min | none — next session |
| PHP | overlay (`overlays/php.md`) | ~30 min | none — next session |
| SQL | overlay (`overlays/sql.md`) | ~30 min | dialect split (Postgres/MySQL/SQLite/MSSQL) needs Owner pick first |
| Elixir code-idioms | overlay (`overlays/elixir.md` EXTENSION) | ~20 min | file exists with high-level rules; extend with code patterns next session |

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
| QEMU embedded dumper | 1 day | **SOFT BLOCKER: `apt install qemu-system*` on VPS (verified NOT installed as of 2026-04-21).** Needs sudo + ~400MB disk. Owner-approved provisioning required. |

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

## What 100% requires that Power Pack alone can't deliver

A few items of the original "100% baseline" depend on infrastructure outside this repo:

- **Xcode CI runner** (for full iOS empirical gate) — needs a macOS host, cannot be on Linux VPS. ~$80/mo for a basic GitHub Actions macOS runner or equivalent.
- **Unity / Unreal licenses** — commercial, Owner decision.
- **macOS dev workstation** — for local Apple dev; not infra Power Pack can "ship."

These are infrastructure decisions, not code. The pack can document the gates and the fastlane config (MC-OVO-33 did this) but cannot execute them from a Linux VPS.
