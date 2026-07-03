# First-Load Trim Proposal — Owner-side (2026-07-03)

**Status:** PROPOSAL ONLY. The agent does NOT apply any of this — HR-001 forbids
editing `~/.claude/CLAUDE.md` and the JIT hook config autonomously. Owner
reviews, decides, applies.

**Basis:** the only surviving lever from the corpus audit (`548d062`,
`vault/plans/token-optimization-audit-2026-07-03.md`) — first-load system prompt
mean **~57k input tokens**. All estimates below are **measured**, not invented.

**Honest framing first.** Owner is on Claude Max (flat rate) and lifetime cache
ratio is 96.3%, so the *marginal $ cost* of first-load is ≈0. The real benefit
of trimming is **context-window headroom** (less static crowding → more room for
actual work before `/compact`) plus the small fraction that is genuine
cache-creation cost each time the content changes. ROI is **modest by design** —
this is the audit's least-bad lever, not a windfall.

---

## Where the ~57k first-load actually goes (measured)

| Component | Measured size | Loaded |
|---|---|---|
| Global `~/.claude/CLAUDE.md` | 39,226 ch ≈ **9,800 tok** | every session (cache-creation turn 1, cache-read after) |
| JIT active-spec injection (`jit_skill_loader.py`) | up to `SPEC_CAP_BYTES` 24,000 B ≈ **6,000 tok**; observed **13,396 B ≈ 3,349 tok** (`rollback-skill.md`) | **every prompt** (not just turn 1) |
| Skills registry + tool defs + MEMORY.md + system prompt | remainder (~38k tok) | harness-owned, not trimmable here |

---

## Proposal A — CLAUDE.md trim (~1,500 tok, ~15% of the file)

### A.0 — DO NOT TOUCH (hard constraint, cited)

Per the sealed HARD RULE (`memory/reference_claude_md_40k_char_warning`): **never
relocate the Bash-Bridge, Parallel-Subagent, or Anti-Waiting rules.** These are
the two largest sections and they stay inline verbatim:

- `Parallel Subagent Limit on Windows (MANDATORY)` — 2,511 tok — **KEEP**
- `Windows Bash Bridge Reliability (MANDATORY)` — 2,309 tok — **KEEP**
- `Background Process Hygiene (MANDATORY)` — 404 tok — **KEEP** (reaper doctrine)
- `Critical Rules (Inlined)` / `Anti-Antipattern Protocol` — **KEEP** (always-active)

These 4 blocks (~5,600 tok, ~57% of the file) are load-bearing kill-switches. No
trim touches them.

### A.1 — Compress to on-demand pointers (candidates)

These sections are mostly **pointers to other systems** already documented in the
vault. Each can shrink to a one-line reference the agent expands only when the
task needs it. Measured sizes:

| Section | Current tok | Proposed | Saved |
|---|---|---|---|
| Sovereign Baseline (Apex Standard) | 442 | ~60 (1-line → `knowledge_vault/`) | ~380 |
| Sovereign Standard (Mandatory Baseline) | 416 | ~60 | ~356 |
| Sovereign RTK Baseline | 304 | ~50 | ~254 |
| Knowledge Vault Protocol | 206 | ~50 (→ `INDEX.md`) | ~156 |
| ULTRA / ONESHOT Protocol | 181 | ~40 (→ `commands/ultra.md`) | ~141 |
| Small pointer blocks (ExecutionOS, Governance Overlay, USAP, Global Alignment Ledger, First-Time Setup, KobiiAI, CARL, Vault Index) | ~380 combined | ~120 | ~260 |
| **Total** | **~1,929** | **~380** | **~1,547 tok** |

Net: CLAUDE.md ≈ 9,800 → ~8,250 tok. Also buys **~6,000 chars** of headroom
below the 40k firewall (currently at 39,226 — dangerously close; this trim alone
removes the firewall-breach risk that `claude_md_firewall.js` guards).

**What NOT to over-trim:** keep enough of each pointer that the agent knows the
system EXISTS and where to load it. A bare filename with no hook = the agent
forgets the capability. One sentence + path is the floor.

## Proposal B — JIT active-spec injection (HIGHEST recurring ROI)

### The finding

`jit_skill_loader.py::_active_spec()` (lines ~602–672) selects the spec by
**most-recently-modified mtime**, NOT by relevance to the prompt:

```
latest = max(candidates, key=lambda p: p.stat().st_mtime)
```

Consequence (observed THIS session): a power-pack session whose task is a **token
audit** gets `vault/specs/rollback-skill.md` (13,396 B ≈ **3,349 tok**) injected
into **every prompt** — because it was the last spec touched, not because it is
relevant. Unlike the one-time first-load, this **recurs per turn**: a 40-turn
session (the audit found **282 sessions over 40 turns**) carries ~3.3k tok × 40 ≈
**134k tok** of an unrelated spec across the session (cache absorbs most, but it
occupies live context every turn and re-creates cache whenever the spec file is
edited).

### Proposed adjustments (pick one; B.2 recommended)

- **B.1 — First-turn-only injection.** Inject the active spec only on the first
  usage turn of a session (dedupe like the skill-router `_skillrouter_carded`
  path already does), not every prompt. Est. saving: (N−1)×3.3k tok/session of
  live-context occupancy on long sessions. Lowest-risk; spec still available.
- **B.2 — Relevance gate (recommended).** Before injecting, require a keyword
  overlap between the prompt and the spec's title/first-paragraph (reuse the
  existing regex-token approach). No overlap → skip. Kills the "unrelated
  rollback spec in a token-audit session" case entirely. Est. saving: full
  3.3k tok/prompt on off-topic sessions.
- **B.3 — Lower `SPEC_CAP_BYTES`** from 24,000 → 12,000 B. Blunt; caps worst
  case but still injects irrelevant specs. Least preferred (B.2 dominates it).

`DISCOVERY_TOK` (80) and the 40 KB `BUDGET_BYTES` breaker are already tight —
**no change proposed** to those.

---

## Owner install steps (manual — agent does not apply)

**Proposal A (CLAUDE.md trim):**
1. Back up: `Copy-Item ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-trim-20260703.bak`
2. Edit `~/.claude/CLAUDE.md`: replace each A.1 section body with a one-line
   pointer (keep A.0 sections verbatim).
3. Verify under firewall: `(Get-Content ~/.claude/CLAUDE.md -Raw).Length` < 40000.
4. `/restart` (CLAUDE.md loads at session start).

**Proposal B (JIT spec — B.2 relevance gate):**
1. Back up: `Copy-Item tools/jit_skill_loader.py tools/jit_skill_loader.py.bak`
2. In `_active_spec()`, after computing `latest`, gate the return on a
   prompt↔spec keyword overlap (pass `prompt` into the function from `run()`).
3. `python tools/verify_rtk_fusion.py` is unrelated; instead re-run any JIT test
   under `tools/` if present, then `/restart`.

## How to measure the result (before → after)

1. **Baseline now:** `python tools/token_corpus_audit.py --report vault/plans/first-load-baseline-20260703.md` — note `A1 mean_first_load`.
2. Apply A and/or B, `/restart`, run 3–5 normal sessions.
3. **Re-measure:** re-run the audit; compare `A1 mean_first_load` and the JIT
   telemetry (`vault/telemetry/jit_usage_*.jsonl` output_tokens per prompt).
4. **Success gate:** first-load drops by the A.1 estimate (~1.5k tok) AND the
   JIT per-prompt injection drops to ~0 on off-topic sessions (B.2). No loss of
   any capability the agent relied on (watch for "agent forgot system X").

## What this proposal deliberately does NOT claim

- No claim of large $ savings (flat rate + 96% cache → marginal ≈0).
- No output-quality trade (A trims pointers, not doctrine; B skips irrelevant
  specs the session never used).
- No touch to the protected kill-switch sections or the 40 KB breaker.
