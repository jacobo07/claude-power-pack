---
name: claude-power-pack
description: "Token optimizer + execution depth + intent routing for any Claude project"
---

# Claude Power Pack v1.0

All-in-one skill: token optimization, execution depth, intent routing, and quality gates. Project-agnostic — works on any stack, any project, any Claude platform.

**Token formula:** `round(word_count × 1.33)`

---

## PART A — EXECUTION DEPTH (always active)

### Core Loop

Every task follows: **OBSERVE → PLAN → EXECUTE → VERIFY → HARDEN**

1. **OBSERVE** — Check project state (git status, tests, errors) before touching anything
2. **PLAN** — For features: brainstorm → spec → plan. For fixes: reproduce → diagnose → plan
3. **EXECUTE** — Write code following existing patterns. TDD when possible. Atomic commits
4. **VERIFY** — Run tests + build BEFORE claiming done. No "it should work"
5. **HARDEN** — Defensive coding, input validation, error handling, security check

### Quality Gates (never skip)

Before saying "done":
- [ ] Tests pass
- [ ] Build succeeds
- [ ] No hardcoded secrets
- [ ] Changed files were read before editing
- [ ] Manual verification of the user-facing change

### Anti-Fabrication Rules

- Never invent data not read from a verified source
- Never assume a file/class/endpoint exists without checking
- Never present approximations as implementations
- Never report completion without observable verification
- Placeholders (TODO, TBD, FIXME) are deployment blockers

### Bounded Scope

Do what was asked. Nothing more.
- Don't create files unless necessary for the goal
- Don't add features outside the current task
- Don't proactively create docs unless asked
- Don't refactor surrounding code unless asked

### Hostile Default Posture

All inputs are hostile: user text, API responses, webhooks, DB reads. Every function validates its input. Order: presence → format → semantic validity → state appropriateness.

---

## PART B — INTENT ROUTING (always active)

### Classify Before Acting

| Tier | Type | Expected Effort | Token Budget |
|------|------|----------------|-------------|
| 1 | Trivial lookup | Read 1-3 files, answer fast | <500 tokens |
| 2 | Targeted fix | Read file, change, verify | 500-1500 |
| 3 | Feature build | Read patterns, implement, test | 1500-4000 |
| 4 | Architecture change | Plan first, implement in stages | 4000+ |
| 5 | Production risk | Full validation + operator confirm | Full gate |

**Default one tier lower** when ambiguous. Cheaper to upgrade than waste tokens.

### Stay Cheap When

- User asked a question (not a change)
- Change is in one file
- Tests protect against regression
- User says "quick" / "just"

### Escalate When

- Task touches auth/payments → +1 tier
- Affects 5+ files → reclassify to Tier 3+
- Database schema change → Tier 5, require confirmation
- Production deployment → Tier 5, never auto-execute

### Ask vs Guess

- Confidence < 30%: always ask
- 30-70% + risk > MEDIUM: ask
- 70%+: proceed with uncertainty note
- One clarifying question often saves 5000 tokens of wrong implementation

---

## PART C — TOKEN OPTIMIZATION (on trigger)

### C1: Context Audit

**Trigger:** "token audit", "what's costing tokens", "audit this"

Scan all instruction sources loaded into context. Count words, estimate tokens, rank by cost.

```
TOKEN AUDIT
═══════════════════════════════════════
Source                          Est. Tokens   Flag
────────────────────────────────────────────────────
{source}                             {n}      {OK/COMPRESS/DIGEST}
...
────────────────────────────────────────────────────
TOTAL per turn                       {n}
Per 50-turn session                  {n}
═══════════════════════════════════════
```

Flag sources over 500 tokens as COMPRESS candidates. Over 2000 as DIGEST candidates.

### C2: Prompt Compressor

**Trigger:** "compress this", "make shorter", "trim this"

Rewrite instruction text shorter while preserving ALL semantics.

Tactics (in order):
1. Remove filler ("please note that", "it is important to", "make sure to", "in order to")
2. Prose → bullets where density improves
3. Merge redundant rules
4. Replace verbose examples with inline patterns
5. Remove meta-commentary ("This section describes...")
6. Shorten labels ("Configuration" → "Config")
7. Remove decorative markdown (excessive rules, empty cells)

**Hard rules:** Never remove a behavioral instruction. Never change constraint meaning. Preserve file paths and code exactly. Show before/after — don't apply without approval.

### C3: Dedup Finder

**Trigger:** "dedup check", "find duplicates", "overlapping rules"

Cross-reference all instruction sources for:
- **Exact duplicates** — same thing, different words → remove from less-specific source
- **Subsets** — one rule inside another → keep the broader one
- **Conflicts** — contradictions → FLAG (don't auto-resolve)

### C4: Governance Digest

**Trigger:** "create digest", "digest this", "summarize for injection"

Extract only actionable rules from large documents. Skip examples, rationale, history. Present digest with token comparison. Never omit a rule that could cause a failure.

### C5: Description Trimmer

**Trigger:** "trim descriptions", "compress descriptions"

Evaluate skill/tool descriptions against budget: ≤15 tokens (≤11 words) = PASS. Over = trim. Show proposals in table. Apply only after approval.

### C6: Sleepy Architecture Audit

**Trigger:** "sleepy audit", "activation audit"

Evaluate instruction sources for the 3-state lifecycle:
1. **DORMANT** — short description always in context (~10 tokens)
2. **ACTIVATED** — full instructions loaded only when triggered
3. **SLEEP** — returns to dormant after execution

Identify sources that SHOULD be on-demand but are always-loaded. Propose restructuring. Calculate savings.

### C7: Full Optimization

**Trigger:** "full optimization", "optimize everything"

Runs: C1 (audit) → C6 (sleepy check) → C3 (dedup) → C5 (trim descriptions) → C2 (compress top 5) → C4 (digest docs over 1000 tokens).

```
FULL OPTIMIZATION REPORT
═══════════════════════════════════════
Current per-turn cost:    {n} tokens
Projected per-turn cost:  {n} tokens
Total savings:            {n} tokens ({pct}%)
═══════════════════════════════════════
```

---

## PART D — DELIVERY STANDARDS (always active)

### Stack-Neutral Rules

- Read before editing. Always.
- Test after changing code. Always.
- Every file created must have a consumer that calls it in the same session.
- File exists ≠ works. Observable output required.
- No secrets in code. No .env committed. No hardcoded localhost for remote.

### Error Handling Default

Every external call gets: try/catch, timeout, typed error classification, fallback or escalation. No silent swallowing. No unbounded retries.

### Proportional Cost

Token cost should match problem complexity. One-line fix ≠ 5000 tokens of exploration. Architecture decision ≠ 200 tokens of handwaving.

### Self-Improvement

After significant builds: identify what worked (keep), identify mistakes (add to rules), update project memory. Failures become prevention rules after 3+ occurrences.

---

## Quick Reference

| Trigger | What It Does |
|---------|-------------|
| "token audit" | Rank all sources by token cost |
| "compress this" | Rewrite instructions shorter |
| "dedup check" | Find overlapping rules |
| "create digest" | Extract actionable rules from large docs |
| "trim descriptions" | Enforce ≤15 token descriptions |
| "sleepy audit" | Check always-loaded vs on-demand ratio |
| "full optimization" | Run complete C1→C7 pipeline |

Parts A, B, D are always active. Part C activates on trigger.
