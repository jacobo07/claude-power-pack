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

### Anti-Drift Rules

- Product descriptions must preserve all defining features — never collapse multi-layered products into single frames
- If a project has a source-of-truth doc, read it BEFORE writing any summary
- If a project has forbidden semantic tokens, never use them (even in comments)
- Semantic drift (losing core product meaning in a summary) is a defect, not a wording issue
- After fixing drift: patch governance + install prevention rule + add linter check

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

### Deployment Safety

- Always delete old artifacts before uploading new ones
- Validate runtime dependencies in the actual execution environment before shipping
- Auth mode must be explicit and validated on startup — no hidden OAuth assumptions
- No emit-only systems: if something sends messages, it must also receive and process replies
- Startup health checks: validate critical imports and auth before serving users, not after first failure

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

---

## PART E — COMMUNITY ERROR PATTERNS (auto-fed by KobiiClaw)

Generalized prevention rules discovered through real project errors. Domain-agnostic — apply to any stack.

### E1: Selection Scope Confusion

When choosing between candidates (features, approaches, tools, architectures), NEVER mix candidates from different layers. If the user defines a selection pool, score ONLY within that pool. Existing/baseline options may inform technical strategy but must NOT appear as candidates in the selection.

**Pattern:** User asks "which of MY custom X should I build first?" Agent includes existing/stock X in the candidate list and recommends one of those instead.
**Root cause:** Conflating "technically easiest" with "what was actually asked."
**Fix:** Before scoring, explicitly list the candidate pool. Verify every candidate belongs to the defined scope. Separate: (A) candidate selection from (B) technical implementation strategy. The winner comes from A. The how-to-build comes from B.

### E2: Scaffolding vs Identity Lock

When using existing infrastructure as temporary scaffolding, ALWAYS declare it as temporary. Never let scaffolding choices drift into permanent identity. Evaluate the final result against the TARGET identity, not the scaffold's convenience.

**Pattern:** Agent hooks into existing system X as "temporary scaffold," then all subsequent work optimizes for X's constraints instead of the actual goal.
**Root cause:** Path dependency — early convenience choices become implicit permanent constraints.
**Fix:** Label every scaffolding decision with: (1) what it scaffolds, (2) when it gets replaced, (3) what the final evaluation criteria are (which must NOT reference the scaffold).

### E3: Layer Flattening

When a task has multiple distinct layers (selection, implementation, evaluation, identity), NEVER collapse them into one decision. Each layer has its own logic, its own candidates, its own constraints.

**Pattern:** Agent merges "what to build" with "how to build it" into a single recommendation, causing the easiest-to-build option to win over the strategically correct one.
**Root cause:** Optimization for single-dimension efficiency instead of multi-layer correctness.
**Fix:** Before making recommendations, enumerate the layers. Make one decision per layer. Cross-reference between layers only AFTER each layer has its own answer.

### E4: WordPress REST API — Raw vs Rendered Content Destruction

When modifying WordPress pages/posts via the REST API, ALWAYS use `content.raw` (Gutenberg block markup), NEVER `content.rendered` (processed HTML). Pushing rendered HTML back destroys all block editor structure irreversibly.

**Pattern:** Agent reads page content via REST API, gets `content.rendered` (processed HTML without `<!-- wp:block -->` comments), modifies it, POSTs it back. WordPress saves flat HTML as a single Classic block — hero images disappear, columns collapse, service cards lose text/buttons, the entire page layout breaks.
**Root cause:** The WP REST API returns two content formats: `raw` (with Gutenberg block comments) and `rendered` (processed HTML). Default `GET` returns rendered. Agent uses rendered for round-trip modifications without realizing it strips block structure.
**Fix:**
1. To READ raw content: `GET /wp-json/wp/v2/pages/{id}?context=edit` → use `response.content.raw`
2. To READ revision raw: `GET /wp-json/wp/v2/pages/{id}/revisions/{rev}?context=edit` → use `content.raw`
3. To MODIFY content: read raw first, modify within block structure, POST raw back
4. To APPEND (schema, FAQ sections): read raw, append to raw, POST raw
5. For meta-only changes (Yoast title/description): send ONLY the `meta` field, do NOT include `content`
6. NEVER restore from `content.rendered` — it destroys block editor layout permanently

**Severity:** CRITICAL — caused 27 pages to lose their entire visual design on a production site. Required rollback to pre-change revisions using raw content from `context=edit`.
