# Lateral-Thinking Skill + Cascade Error Prevention System (CEPS) — Plan v1

**Status**: FASE 0 (architecture) complete. Awaiting Owner `apruebo` for FASE 1+.
**Kernel baseline**: vMAX-NULL-ERROR with cascade effect — every feature lifts the floor for the next.
**Plan-mode origin**: Owner ULTRA PLAN MODE request 2026-05-25.
**Backup artifact only** — the primary plan lives in the chat. This file is the registry.

---

## Reality Contract (paraphrased — no literal trigger tokens per `feedback_plan_files_not_allowlisted.md`)

No "works in theory". Either works with empirical evidence or it does not work. No
step marked done without observable output. The skill must produce output that
empirically differs from the baseline, not text-that-describes-what-it-would-produce.
If LT yields generic output instead of real lateral thinking → not done. If CEPS logs
errors without preventing recurrence → not done. Stub-only sections marked with
completion-pending anchors or elided ellipses are non-shippable in this stream.
Iterate until the kernel baseline is satisfied.

---

## Objective

Two coupled components:

### Component 1 — Lateral-Thinking Skill
A PP skill that, when activated, makes Claude approach any problem from non-obvious
angles before converging on a solution. NOT a "think creatively" prompt — a structured
system with 5 forced frames:

1. **Reframing**: at least 3 opposite perspectives before solution
2. **Inversion**: what would guarantee failure? → invert
3. **Cross-domain analogy**: equivalent problem in a different domain, transfer the solution
4. **Constraint removal**: what if constraint X did not exist?
5. **First principles**: destroy given assumptions, rebuild from zero

### Component 2 — Cascade Error Prevention System (CEPS)
A system that converts every error / bug / drift / gap-between-asked-and-delivered into:
- (a) immediate record with classification (type, severity, context)
- (b) underlying-pattern extraction (root cause, not symptom)
- (c) forward propagation: in which future scenarios could this manifest? → preventive rules
- (d) automatic distribution: session_lessons.md + UKDL + project knowledge_vault
- (e) integration with Auto-Testing Gate: new patterns generate new tests

CEPS is not a log. It is a cumulative-immunity system. Each error makes the system
smarter for the next one.

---

## Architecture decisions (P1–P7)

### P1 — Skill format & JIT integration

**Decision**: Hybrid `.md` skill + JIT latent-card.

- Skill lives at `~/.claude/skills/lateral-thinking/SKILL.md` (Skill-tool invocable)
- JIT loader gets trigger family #10:
  - Regex: `(stuck|atascado|no idea|how should i|design problem|brainstorm|approach|alternativas|atrapado|complex problem|hard\b)` (case-insensitive)
  - Injects an 80-token discovery card pointing to the skill, never the full body
- Agent invokes Skill tool on demand if the card is relevant
- Matches BL-0068/0069 vendored-Apollo JIT doctrine

**Rationale**: discovery card = low context cost; full body on demand = pay only when
the problem genuinely requires it; reuses existing JIT architecture without rewriting it.

### P2 — Five-frames selection

**Decision**: Always-all-5 framed as checklist + agent rates each (1–5) and applies top 3
with depth.

Pre-rating heuristic by problem-domain:

| Domain | Default top 3 |
|---|---|
| algorithmic / math | first-principles, inversion, analogy |
| product / UX | reframing, constraint-removal, analogy |
| system design | first-principles, constraint-removal, inversion |
| debugging | inversion, first-principles, reframing |
| creative writing | reframing, constraint-removal, analogy |
| default | agent judgment based on prompt content |

The rating itself is data (feeds metric P7 over time).

**Rationale**: always-all-5 with depth = bloat. Pure-selective = risk of eliding the
frame that breaks the problem. Hybrid scales depth with problem difficulty and produces
telemetry.

### P3 — Module coupling

**Decision**: Independent modules with shared event bus.

- LT and CEPS do NOT couple
- Bus: `vault/ceps/events.jsonl` (append-only, atomic write)
- CEPS listens via Stop hook
- LT writes `lt_frame_applied` events with metadata (frame, score, problem-domain) that
  CEPS optionally correlates with later errors
- LT can fire without CEPS active
- CEPS can capture errors from non-LT sessions
- If LT activates without CEPS: LT works normally, no pattern telemetry; user can manually
  invoke CEPS using the bus event as input

**Rationale**: coupling = LT loses cases where the problem does not need CEPS.
Independence = each module testable in isolation, hook fanout limited.

### P4 — Error detection trigger

**Decision**: 3-layer mixed.

1. **Manual / HIGH-confidence**: slash command `/ceps-record-error <category> <description>`
2. **Verify-fail / HIGH-confidence**: `tools/verify_spp.py` STRICT-FAIL row auto-feeds CEPS
3. **Auto-detect / LOW-confidence draft**:
   - Stop hook scans last 5 turns for correction patterns:
     `no, actually`, `wrong`, `stop`, `revert`, tool DENY events, inversion-of-prior-claim regex
   - Emits to `vault/ceps/drafts/<ts>.json` with `confidence: low`
   - Drafts require `/ceps-confirm <draft-id>` to persist

**Rationale**: pure-manual loses signal; pure-auto generates noise; drafts layer avoids
spurious persistence while preserving real signal. Verify-fail leverages already-empirical
gates.

### P5 — Propagation model

**Decision**: Symbolic taxonomy + FTS5 sidecar (no LLM in propagation path).

Event schema:

```json
{
  "id": "ceps_<sha1[:16]>",
  "ts": "2026-05-25T00:00:00Z",
  "category": "regression|security|drift|scaffold|incomplete-shell|integration|spec-violation|tooling|env",
  "subsystem": "free-form tag (e.g., jit-loader, hook-fanout, ps-bash-bridge)",
  "pattern_signature": "sha256 of normalized root-cause description",
  "prevention_rule": "templated one-line rule",
  "affected_modules": ["..."],
  "evidence_path": "path or vault link",
  "confidence": "low|high"
}
```

- Index: FTS5 sidecar in `vault/ceps/patterns.db`, table `ceps_patterns_fts`
- Owns its own rowid space, NEVER touches `turns_fts` (BL-0068 apex doctrine)
- Propagation: JIT loader queries FTS5 with prompt keywords + subsystem hints →
  top-3 matching patterns inject single-line `[ceps-pattern] <prevention_rule>
  (cat=<X>, sig=<8 chars>)` into additionalContext
- Deterministic, <5ms, Reality-Contract clean

**Rationale**: embeddings = heavy infra, non-deterministic, noisy. Pure regex = loses
semantics. Symbolic taxonomy + FTS5 = pattern already used by Lazarus / Sovereign Vault
(same cache profile + can reuse `vault_search.py` binding).

### P6 — Auto-Testing Gate integration

**Decision**: SKIP-by-default stubs + 7-day stale-WARN gate.

- CEPS marks pattern `auto_test_eligible: true` only if
  `category ∈ {regression, security, drift}`
- Generates stub at `tests/ceps_generated/test_<sig[:12]>.py` with:
  - `@pytest.mark.skip(reason="ceps-stub-pending: <rule>")`
  - Assertion template with completion-pending anchor comments
- Auto-Testing Gate does NOT fail on SKIP (current 19/19 PASS preserved — verified in M14)
- New gate rule: stub older than 7 days → WARN (not FAIL) — forces resolution without
  breaking builds

**Rationale**: failing-by-default stubs would break the 19 tests immediately. SKIP =
visible but non-blocking. 7-day stale = pressure without asphyxiation.

### P7 — Empirical success metrics (declared BEFORE building)

**LT skill empirical pass-gate**:

- N=5 prompts, mixed-domain (1 algorithmic, 1 product/UX, 1 system-design, 1 debugging,
  1 creative)
- Same context, run with skill / without skill
- Owner blind-eval per pair on 3 axes (novelty, depth, actionability), 1–5 each (max 15
  pts per run, max 75 pts aggregate)
- Pass-gate: aggregate-with-skill ≥ aggregate-without-skill + **1.5 pts** (10% of 15-pt
  scale)
- <1.5 → iterate regex / frames up to 3 cycles; still <1.5 → KILL (Reality Contract)

**CEPS empirical pass-gate**:

- 10 errors: 7 real ones extracted from `vault/knowledge_base/session_lessons.md` history
  + 3 fresh synthetic patterns
- For each: present subsequent prompts that touch the error's category
- Measure: of 10 errors, how many trigger a relevant `[ceps-pattern]` injection?
- Pass-gate: **≥7/10 (70%)** relevant injections → PASS
- <7/10 → iterate taxonomy/regex up to 3 cycles; still <7/10 → KILL or pivot

---

## Collision map (M0c)

| Existing system | Potential collision | Mitigation |
|---|---|---|
| JIT loader (9 triggers) | Trigger 10 (LT) competes for 40 KB budget | Priority 5 (after graphql/apollo prio 0–3) — Apollo always wins in GraphQL repos |
| JIT vague-lint signal | Vague prompts often also "stuck" | LT trigger deactivates if `_detect_vague_prompt` already fired (mutex in run()) |
| arch_check piggyback | ≥2 design verbs triggers arch_check + LT | LT defers if `_arch_check_inject` already fired; arch_check carries LT nudge in its context |
| Intent-Lock | Different lifecycle phases (LT pre-impl, IL on tool exec) | None — verified in M5 |
| Auto-Testing Gate (19 tests) | New `tests/ceps_generated/` could be scanned | `@pytest.mark.skip` default + segregated path |
| Stop hooks (5 active) | CEPS adds hook → fanout cost (memory `hook-fanout-systemic-cost.md`) | Throttle ≥10 min between fires; future consolidation in hook-dispatcher.js (Zero-Command Comp E) |
| Sovereign Vault FTS5 | CEPS DB is sidecar to `vault_search.py` | Separate DB `vault/ceps/patterns.db`, own table `ceps_patterns_fts`, does NOT touch `turns_fts` (BL-0068) |
| `session_lessons.md` (cat>> corruption observed 2026-05-23) | CEPS distributes to session_lessons | Atomic write pattern mandatory (tempfile + os.replace); template in `tools/_append_lessons_override.py` |

---

## Micro-commit ladder

### FASE 0 — Architecture (plan mode, no code)

- [x] M0a: Answer P1–P7 with concrete decisions + rationale
- [x] M0b: Define empirical success metric for each component
- [x] M0c: Map potential collisions with existing PP modules
- [ ] M0d: Persist plan to `vault/plans/lateral-thinking-skill-plan.md` (this file)

**→ CHECKPOINT: present resolved plan. Wait for "apruebo" to proceed.**

### FASE 1 — Lateral Thinking Skill

- [ ] M1: `~/.claude/skills/lateral-thinking/SKILL.md` — frontmatter + 5 frames + heuristic + scoring rubric
- [ ] M2: `~/.claude/skills/lateral-thinking/references/` — 1 file per frame with cross-domain examples
- [ ] M3: Trigger family #10 in `tools/jit_skill_loader.py` — regex + 80-token discovery card + mutex with vague-lint + arch_check
- [ ] M4: Empirical pass-gate: `tools/test_lt_empirical.py` — 5 prompts with/without, side-by-side JSON, Owner scoring entry-point
- [ ] M5: Non-collision test: prompts touching Intent-Lock + Arch-Check verify LT does not double-fire
- [ ] M6: code-reviewer pre-commit → commit `feat(skill): lateral-thinking v1 — 5 frames, JIT-wired (LT_PASS=<delta>)`

### FASE 2 — Cascade Error Prevention System

- [ ] M7: Classification schema in `vault/ceps/schema.json` — enum categories, confidence types, contexts
- [ ] M8: Three triggers in `tools/ceps_recorder.py` — slash command, verify-fail hook, Stop-hook auto-detect with drafts gate
- [ ] M9: Root-cause extractor `tools/ceps_extractor.py` — normalize description, compute `pattern_signature`, generate `prevention_rule` from template per category
- [ ] M10: Forward propagation `tools/ceps_propagator.py` — query FTS5 with prompt+subsystem hints, return top-3 patterns matching as `[ceps-pattern]` lines
- [ ] M11: Distributor `tools/ceps_distributor.py` — atomic-write to 3 destinations: `vault/knowledge_base/session_lessons.md`, UKDL `vault/knowledge_base/ukdl-universal.md`, `vault/ceps/patterns.db`
- [ ] M12: Empirical closed-loop test: `tools/test_ceps_closed_loop.py` — 10 errors injected, ≥7/10 = PASS
- [ ] M13: code-reviewer pre-commit → commit `feat(ceps): cascade error prevention v1 — classify+propagate+distribute (CEPS_PASS=<X>/10)`

### FASE 3 — Auto-Testing Gate integration

- [ ] M14: Baseline check — confirm 19/19 PASS pre-change
- [ ] M15: Test generator `tools/ceps_test_gen.py` — pattern → stub at `tests/ceps_generated/test_<sig[:12]>.py` with `@pytest.mark.skip`. Gate amendment: 7-day stale stub → WARN
- [ ] M16: Full-cycle empirical: introduce real error → CEPS records → propagates → distributes → generates stub → re-run Gate → 19/19 PASS + 1 visible SKIP
- [ ] M17: code-reviewer pre-commit → commit `feat(ceps+atg): auto-test stub generation (CYCLE_PASS=true)`

### FASE 4 — Completion Standard

- [ ] M18: `knowledge_vault/core/skill-completion-standard.md` — checklist obligatory for any new PP skill:
  1. Empirical pass-gate defined pre-build
  2. Side-by-side comparison with/without skill
  3. No-collision verified vs existing modules
  4. Distribution integrated with CEPS
  5. Auto-test stub generated
  6. Atomic-write for all .md appends (post-2026-05-23 cat>> apex corruption)
  7. RTK proxy compatibility
- [ ] M19: Append "Skill Completion Axis" section to `apex-completion-standard.md` (atomic write)
- [ ] M20: code-reviewer pre-commit → commit `feat(standard): skill-completion-standard v1 — baseline raised post LT+CEPS`

---

## Iteration protocol (auto-applied on any M*)

1. If M* fails empirical pass-gate:
2. Auto-record with CEPS (eat-own-dog-food)
3. Iterate using `~\Downloads\Promptsss\Prompts pa iterar\Universal\iteracion-avanzada-universal.txt` (max 3 cycles per M*)
4. If cycle 3 fails → STOP, surface to Owner with evidence, await decision
5. Never declare M* done without empirical output proving the difference

---

## Post-approval execution mode

Agent Teams unattended. M1→M20 sequential. Automatic STOP on:
- (a) empirical pass-gate failure after 3 iterations
- (b) collision detected at runtime
- (c) architectural decision not covered in M0a

Final executive summary: M* status, M4 evidence (LT side-by-side), M12 evidence (CEPS
closed-loop), M16 evidence (full cycle), commit SHAs.

---

**Last updated**: 2026-05-25 (FASE 0 close; awaiting Owner approval for FASE 1+)
