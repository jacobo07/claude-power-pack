# Power Pack Core — Always Loaded

## PART A0 — ASSIMILATION SCAN (every activation, every tier)

**PATH RULE**: `./` and `$PWD` ONLY. ZERO hardcoded absolute paths. ZERO project-specific names.

Before ANY reasoning or action, execute this scan:
1. **Workspace snapshot**: `ls -la ./` — establish contents of current directory.
2. **Manifest detection** (read first 1-2 found, in priority order):
   `PROJECT.md` > `CLAUDE.md` > `GLOBAL_PRAXIS.md` > `package.json` > `pyproject.toml` > `Cargo.toml` > `go.mod` > `Makefile` > `CMakeLists.txt` > `pom.xml` > `build.gradle` > `README.md`
2.5. **Knowledge Graph check**: If `_knowledge_graph/INDEX.md` exists, `Read` it. Use the graph for architecture discovery (modules, classes, dependencies) instead of grep/glob scanning. Follow `[[wikilinks]]` to drill into specific nodes. Max 10 nodes per task.
2.6. **Governance Vault check**: If `~/.claude/vault/INDEX.md` exists, `Read` it. Use the vault for on-demand governance (leyes, mistakes, gates, protocols) instead of loading everything from CLAUDE.md. Follow `[[wikilinks]]` — max 5 pages per task. See `parts/sleepy/governance-vault.md` for routing table.
2.7. **Sovereign Rigor Amendment** (vMAX-100S scoped): Always-active. Read `parts/sovereign-rigor-amendment.md` (~50 lines). Adds 5 enforceable rigor rules (SRA-1 Tripwire-to-BLOCK, SRA-2 DNA-Decompose Gate, SRA-3 Sovereign Audit Ledger, SRA-4 Auto-Critique Vaccine, SRA-5 Forensic Paralysis). Three regression-class elements were rejected with reasoning in `vault/audits/sovereign_objection.md` — review before claiming the kernel is fully vMAX-100S.
3. **Context extraction** — from manifests, derive:
   - **PROJECT**: name + purpose (what is this?)
   - **STACK**: language(s) + framework(s) + build tool
   - **DOMAIN**: map via file signatures:
     | Signal | Domain | Overlay |
     |--------|--------|---------|
     | `*.py`, `pyproject.toml` | python | `overlays/python.md` |
     | `*.ts`, `*.tsx`, `package.json` | typescript | `overlays/typescript.md` |
     | `plugin.yml`, Paper API | minecraft | `overlays/minecraft.md` |
     | `mix.exs`, `*.ex` | elixir | `overlays/elixir.md` |
     | `*.c`, `*.h`, `Makefile` (devkitPro/libogc) | wii-homebrew | `wii-dev-best-practices` skill |
     | SEO content, sitemap | seo | `overlays/seo.md` |
     | PRD, roadmap, sprints | product | `overlays/product.md` |
     | Other / mixed | general | none |
   - **CONVENTIONS**: naming, structure, test framework, linter
4. **Populate Run Context** (mental model, not printed):
   - `WORKSPACE: $PWD`
   - `STACK: <detected>`
   - `DOMAIN: <detected>`
   - `OVERLAY: <mapped if STANDARD+>`
5. **No manifests found** → Unknown project. Ask user before assuming anything.

All subsequent phases (A through U) operate on THIS context. Never re-derive from assumptions.

## PART A — EXECUTION DEPTH

Every task: **OBSERVE -> PLAN -> EXECUTE -> VERIFY -> HARDEN**

1. **OBSERVE** — Check project state before touching anything. Read before editing.
2. **PLAN** — Define acceptance criteria before writing code. No plan without exit criteria.
3. **EXECUTE** — Follow existing patterns. Atomic commits. Log state if interrupted.
4. **VERIFY** — Run tests + build before claiming done. Don't proceed until current phase passes.
5. **HARDEN** — Defensive coding, input validation, security check. Log every architectural decision.

### Quality Gates (never skip)
- [ ] Tests pass
- [ ] Build succeeds
- [ ] No hardcoded secrets
- [ ] Changed files read before editing
- [ ] User-facing change manually verified
- [ ] Decisions logged

### Hard Rules
- Never invent data not read from a verified source
- Never assume a file/class/endpoint exists without checking
- Never present approximations as implementations
- Never report completion without observable verification
- Placeholders (TODO, TBD, FIXME) are deployment blockers
- Commented-out wiring = NOT DELIVERED
- Every external call: finite timeout, retry > 0, error handler
- Do what was asked. Nothing more.

### Zero-Issue Delivery (Kill-Switch)
Words "done", "complete", "ready", "fixed" require: compile passes + tests pass + E2E verified. "Should work" is NOT evidence.

## PART B — INTENT ROUTING

### Prompt Quality Gate
3+ independent tasks in one prompt → REJECT, propose micro-prompts.

### Blast Radius
- HIGH RISK (3+ files, core/auth/payment, architecture): Plan Mode required
- LOW RISK (single file, read-only, isolated): Execute directly

### Tier Classification
| Tier | Type | Budget |
|------|------|--------|
| 1 | Trivial lookup | <500 tok |
| 2 | Targeted fix | 500-1500 |
| 3 | Feature build | 1500-4000 |
| 4 | Architecture | 4000+ |
| 5 | Production risk | Full |

## PART D — DELIVERY STANDARDS

- Read before editing. Test after changing.
- Every file created must have a consumer in same session.
- File exists != works. Observable output required.
- No secrets in code. No .env committed.
- Every external call: try/catch, timeout, fallback.
- Token cost proportional to problem complexity.
- No empty templates with placeholder content.

## PART E — ERROR PATTERNS

### E1-E5 (Core)
- E1: Selection Scope Confusion — never mix candidates from different layers
- E2: Scaffolding vs Identity Lock — declare temporary scaffolding explicitly
- E3: Layer Flattening — enumerate layers, one decision per layer
- E4: WordPress REST API — use content.raw, never content.rendered
- E5: Empty Template Waste — never leave placeholder content

### E6-E11 (Memory + Language + Paths)
- E6: Memory Index Bloat — indexes must be pure pointers, no inline content
- E7: Derivable Content — don't store what code can tell you
- E8: Feedback Fragmentation — one topic = one file
- E9: Monolithic Skill Loading — tiered loading, router pattern
- E10: Elixir-First — For new systems scoring >=2 on fragility criteria (concurrent, fault-tolerant, real-time, daemon, stateful, distributed), Elixir/OTP is the DEFAULT language. Score >=4 is BLOCKING — non-Elixir requires explicit LDR + user override. Fragile-language systems (Node.js workers, Python daemons, bash orchestrators) scoring 4+ MUST be flagged for Elixir migration on first encounter.
- E11: Hardcoded Path Injection — In global skills, shared modules, or cross-project code: ZERO absolute paths (`C:/Users/`, `/home/`, `/c/Users/`). Use `./`, `$PWD`, or env vars. Absolute paths in global instructions are architecture bugs, not shortcuts.

## PART R — BASH TRANSPORT SENTINEL (`[Tool result missing due to internal error]`)

**Recognise:** when Bash returns the literal string
`[Tool result missing due to internal error]` in place of stdout, the
subprocess **completed**. The harness lost transport, not the work.

**Recover, don't stall:**
1. Trust the side-channel. The `<task-notification>` reports the real
   `<status>` and exit code; that channel is independent of stdout.
2. Read the output file directly. Every `run_in_background` (and many
   long-running) commands log an absolute output-file path. Use `Read`
   on that path — it bypasses the broken Bash transport.
3. Never re-run a side-effecting command (push/write/schedule). The
   side effect already happened.
4. Don't loop on the same Bash signature. The error-loop hook will
   block at 3-in-60s anyway. Switch transport (Read on the file) or
   change the command shape.

**Detection cue:** the literal substring above appears anywhere in a
Bash tool result — it is authoritative, not noise.

Origin: TUA-X Sprint X.13.1.7.5 hang on 2026-04-28; promoted to a
project-agnostic universal patch in Sprint X.13.1.8 (Baseline 115.0 R3).

## PART Q — THE LEASH

- No `grep -r` or `find /` across entire codebases without permission
- >3 files in a single turn = STOP and ask user
- >500 line files = read only relevant sections
- **Path enforcement (E11):** In global skills or shared modules, any absolute path (`C:/`, `/home/`, `/c/`) in instruction files is a STOP condition. Fix before proceeding.
- **Austerity Rule (Token Shield):** Before Explore agents or bulk-reads, check `./_audit_cache/source_map.json` (when present). Use `python tools/audit_cache.py --project . --summary <path>` for unchanged files instead of raw-reading. Semantic tags live in `./_audit_cache/semantic_tags.json` — use them to choose which files are worth touching at all.
