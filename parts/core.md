# Power Pack Core — Always Loaded

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

### E6-E10 (Memory + Language)
- E6: Memory Index Bloat — indexes must be pure pointers, no inline content
- E7: Derivable Content — don't store what code can tell you
- E8: Feedback Fragmentation — one topic = one file
- E9: Monolithic Skill Loading — tiered loading, router pattern
- E10: Elixir-First — For new systems scoring >=2 on fragility criteria (concurrent, fault-tolerant, real-time, daemon, stateful, distributed), Elixir/OTP is the DEFAULT language. Score >=4 is BLOCKING — non-Elixir requires explicit LDR + user override. Fragile-language systems (Node.js workers, Python daemons, bash orchestrators) scoring 4+ MUST be flagged for Elixir migration on first encounter.

## PART Q — THE LEASH

- No `grep -r` or `find /` across entire codebases without permission
- >3 files in a single turn = STOP and ask user
- >500 line files = read only relevant sections
