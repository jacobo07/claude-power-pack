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

## VPS Hand-off — MC-OVO-32-F / 31-Q / 34-V runtime validation

Three gates from this cycle require a Linux host with QEMU and AF_UNIX support. Sandbox policy blocks SSH + sudo from the agent, so Owner runs the bundle:

```bash
# On VPS 204.168.166.63 (KobiiClaw), in the claude-power-pack working tree:
git pull
bash tools/vps_validation_handoff.sh 2>&1 | tee /tmp/mc_ovo_vps_$(date +%Y%m%dT%H%M%SZ).log
```

Expected output (per gate):
- `MC-OVO-32-F`: `scaffold_fastapi.py` ALL GATES PASS (pip → pytest → uvicorn /health 200)
- `MC-OVO-31-Q`: `scaffold_qemu_dumper.py` ALL GATES PASS (pip → pytest with AF_UNIX mock QMP → qemu-system-x86_64 --version → CLI --help)
- `MC-OVO-34-V`: `PARITY host=<vps> py=3.x platform=linux tool_sha=4e53d4167f35 tests=8 status=PASS`

The `tool_sha=4e53d4167f35` match between Windows and Linux proves mistake-hook ingestion byte-parity. Paste the log back so we can archive it to `vault/audits/vps_validation_<ts>.log` and close the hand-off.

Failure playbook: the script exits with a distinct code per gate (1/2/3/4) so a truncated log still identifies which gate broke. Environment failures (4) point at provisioning; gate failures (1–3) point at scaffolder/test code that must be iterated locally.

## What 100% requires that Power Pack alone can't deliver

A few items of the original "100% baseline" depend on infrastructure outside this repo:

- **Xcode CI runner** (for full iOS empirical gate) — needs a macOS host, cannot be on Linux VPS. ~$80/mo for a basic GitHub Actions macOS runner or equivalent.
- **Unity / Unreal licenses** — commercial, Owner decision.
- **macOS dev workstation** — for local Apple dev; not infra Power Pack can "ship."

These are infrastructure decisions, not code. The pack can document the gates and the fastlane config (MC-OVO-33 did this) but cannot execute them from a Linux VPS.
