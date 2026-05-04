# Power Pack Core — Always Loaded

## PART A0 — ASSIMILATION SCAN

**PATH RULE**: `./` and `$PWD` only. Zero hardcoded absolute paths or project-specific names.

Before any reasoning:
1. **Workspace**: `ls -la ./`
2. **Manifest** (read first 1-2 found): `PROJECT.md` > `CLAUDE.md` > `GLOBAL_PRAXIS.md` > `package.json` > `pyproject.toml` > `Cargo.toml` > `go.mod` > `Makefile` > `CMakeLists.txt` > `pom.xml` > `build.gradle` > `README.md`
2.5. **KG**: if `_knowledge_graph/INDEX.md` exists, Read it. Use `[[wikilinks]]` instead of grep. Max 10 nodes/task.
2.6. **Vault**: if `~/.claude/vault/INDEX.md` exists, Read it. Max 5 pages/task. Routing: `parts/sleepy/governance-vault.md`.
2.7. **Sovereign Rigor**: read `parts/sovereign-rigor-amendment.md` (~50 lines). 5 rules SRA-1..5. Rejected regressions in `vault/audits/sovereign_objection.md`.
3. **Extract** PROJECT/STACK/DOMAIN/CONVENTIONS from manifest. Domain map:
   | Signal | Domain | Overlay |
   |---|---|---|
   | `*.py`, `pyproject.toml` | python | `overlays/python.md` |
   | `*.ts`/`*.tsx`, `package.json` | typescript | `overlays/typescript.md` |
   | `plugin.yml` + Paper API | minecraft | `overlays/minecraft.md` |
   | `mix.exs`, `*.ex` | elixir | `overlays/elixir.md` |
   | `*.c`/`*.h` + devkitPro/libogc | wii-homebrew | `wii-dev-best-practices` skill |
   | sitemap, SEO content | seo | `overlays/seo.md` |
   | PRD/roadmap/sprints | product | `overlays/product.md` |
   | other | general | none |
4. **Run Context** (mental, not printed): WORKSPACE/STACK/DOMAIN/OVERLAY.
5. **No manifests** → ask user before assuming.

All subsequent phases operate on this context. Never re-derive.

## PART A — EXECUTION DEPTH

**OBSERVE → PLAN → EXECUTE → VERIFY → HARDEN.** Read before edit. Define acceptance criteria before code. Atomic commits. Run tests + build before "done". Defensive coding + security check.

### Quality Gates (never skip)
Tests pass · Build succeeds · No hardcoded secrets · Files read before edit · User-facing change verified · Decisions logged.

### Hard Rules
Never invent unverified data · Never assume file/class/endpoint exists · Never present approximations as implementations · Never report completion without observable verification · Placeholders (TODO/TBD/FIXME) are deployment blockers · Commented-out wiring = NOT DELIVERED · Every external call: finite timeout, retry > 0, error handler · Do what was asked, nothing more.

### Zero-Issue Delivery (Kill-Switch)
"done"/"complete"/"ready"/"fixed" require: compile + tests + E2E verified. "Should work" is NOT evidence.

## PART B — INTENT ROUTING

3+ independent tasks in one prompt → REJECT, propose micro-prompts.

**Blast Radius**: HIGH (3+ files, core/auth/payment, architecture) → Plan Mode. LOW (single file, read-only, isolated) → execute.

**Tier Classification**:
| Tier | Type | Budget |
|---|---|---|
| 1 | Trivial lookup | <500 tok |
| 2 | Targeted fix | 500-1500 |
| 3 | Feature build | 1500-4000 |
| 4 | Architecture | 4000+ |
| 5 | Production risk | full |

## PART D — DELIVERY STANDARDS

Read before edit. Test after change. Every file created needs a consumer in same session. File exists ≠ works (observable output required). No secrets in code, no .env committed. Every external call: try/catch + timeout + fallback. Token cost ∝ problem complexity. No placeholder content.

## PART E — ERROR PATTERNS

- E1: **Selection Scope Confusion** — never mix candidates from different layers
- E2: **Scaffolding vs Identity Lock** — declare temporary scaffolding explicitly
- E3: **Layer Flattening** — enumerate layers, one decision per layer
- E4: **WordPress REST** — content.raw, never content.rendered
- E5: **Empty Template Waste** — never leave placeholder content
- E6: **Memory Index Bloat** — indexes are pure pointers, no inline content
- E7: **Derivable Content** — don't store what code can tell you
- E8: **Feedback Fragmentation** — one topic = one file
- E9: **Monolithic Skill Loading** — tiered loading, router pattern
- E10: **Elixir-First** — new systems scoring ≥2 fragility criteria → Elixir/OTP default. Score ≥4 BLOCKING (requires LDR + override). Flag fragile-lang systems (Node workers, Python daemons, bash orchestrators) for migration on first encounter.
- E11: **Hardcoded Path Injection** — global skills/shared modules: ZERO absolute paths (`C:/`, `/home/`, `/c/`). Use `./`, `$PWD`, env vars.

## PART R — BASH TRANSPORT SENTINEL

When Bash returns literal `[Tool result missing due to internal error]`: subprocess **completed**, harness lost transport.

**Recover**: trust `<task-notification>` side-channel (real status + exit code, independent of stdout). Read output file directly via `Read` tool — bypasses broken Bash. Never re-run side-effecting commands (push/write/schedule already happened). Don't loop — error-loop hook blocks 3-in-60s; switch transport or change command shape.

Origin: TUA-X X.13.1.7.5 hang 2026-04-28; promoted to universal patch X.13.1.8 / Baseline 115.0 R3.

## PART Q — THE LEASH

No `grep -r` / `find /` across full codebases without permission. >3 files in one turn = STOP and ask. >500 line files = read only relevant sections. **E11 enforcement**: absolute path in global skills/shared modules = STOP. **Austerity (Token Shield)**: before Explore agents or bulk-reads, check `./_audit_cache/source_map.json` (when present). Use `python tools/audit_cache.py --project . --summary <path>` for unchanged files. Semantic tags at `./_audit_cache/semantic_tags.json`.
