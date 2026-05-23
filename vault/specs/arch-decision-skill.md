# Spec: Architecture Decision Skill (Arch-Check)

Sealed: 2026-05-23.
Cross-references: `vault/specs/auto-testing-gate.md` (sister axis),
`vault/specs/deep-research-agent.md` (sister axis).

## 1. Purpose

Before the agent (or the Owner) commits to an architectural decision,
consult the local knowledge vault and surface relevant vetoes, prior
lessons, and sealed Standards that bear on the proposed direction. The
vault that is not consulted is the vault that does not exist; this
skill closes that gap.

## 2. Reality Contract

- A veto that does not surface when relevant = the skill does not work.
- A CLEAR verdict when a real collision exists = the skill lies.
- A timeout that blocks the response = the skill is a regression.

All three failure modes have observable empirical signatures
(`additionalContext` timestamps, `vault/decisions/` artifact presence,
`tools/arch_check_timings.json`). The DONE-gate is the V-block.

## 3. Architecture

### 3.1 Components

| # | File | Role |
|---|---|---|
| C1 | `modules/arch-decision/arch_check.py` | Fast-path verdict engine (STDIN -> COLLISION/WARNING/CLEAR + cited context). |
| C2 | `tools/jit_skill_loader.py` extension | Piggyback on existing UserPromptSubmit hook (no new hook fanout). |
| C3 | `commands/arch-decision.md` | Manual `/arch-decision "<desc>"` DEEP mode; generates ADR. |
| C4 | `vault/.arch-index/index.json` | Pre-built index (vetoes / lessons / standards) with weights. |
| C5 | `modules/arch-decision/build_index.py` | Rebuilds the index from 8 vault paths. |

### 3.2 Vault sources scanned (weighted)

1. `~/.claude/knowledge_vault/core/apex-completion-standard.md` (weight 1.0 — sealed Standards / Axes)
2. `~/.claude/projects/.../memory/feedback_*.md` discovered via `MEMORY.md` (weight 0.9 — vetoes-in-disguise)
3. `~/.claude/knowledge_vault/gex44_antipatterns/*.md` (weight 0.85 — named antipatterns)
4. `~/.claude/knowledge_vault/antipatterns/*.md` (weight 0.8)
5. `vault/knowledge_base/session_lessons.md` (weight 0.7 — session-specific lessons)
6. `~/.claude/knowledge_vault/governance/*.md` (weight 0.6 — heuristics + protocols)
7. `~/.claude/knowledge_vault/errors/*.md` (weight 0.5)
8. `vault/knowledge_base/ukdl-universal.md` (weight 1.0 — explicit cross-ref hub)

Total expected sources: 80-150 documents depending on per-host knowledge_vault density.

### 3.3 Verdict shapes

`COLLISION` — entity from prompt matches an entry whose first-paragraph
or filename declares a hard prohibition. Top three sources cited literal
in ≤200 words.

`WARNING` — Jaccard similarity ≥0.3 between prompt token-shingles and
indexed lesson/standard body-shingles, OR architectural-concept match
(prompt mentions a concept named in an apex sealed section). Top one
source cited.

`CLEAR` — no source above the relevance floor. Output is empty (no
context injected). Default if the index is empty or fails to load.

## 4. Per-mode latency budgets

| Mode | Budget | Behaviour on overshoot |
|---|---|---|
| `--fast` (default) | 3.0 s wall-clock total (load index + score + format). | Returns `CLEAR (timeout)` — fail-open, never blocks. |
| `--deep` (manual via `/arch-decision`) | 60 s total (allows LLM ADR generation). | If LLM step exceeds 60 s the ADR is written with sections marked `[partial]`. |

`--fast` mode never spawns LLM. Index search is pure Python (re +
collections.Counter + sklearn-free TF-IDF — small math, no heavy deps).

## 5. STDIN contract

Both `arch_check.py --fast` and `arch_check.py --deep` read the prompt
from STDIN (per `windows-argv-limit-stdin-fix.md` vaccine: claude.exe
argv limit on Windows prevents long-prompt CLI args).

Output: JSON on stdout (`{"verdict":"COLLISION"|"WARNING"|"CLEAR","context":"<= 200 words","sources":[...]}` for fast; ADR text for deep). Exit codes:
0 = success (any verdict), 1 = bad invocation, 2 = index missing or unreadable.

## 6. Threshold of activation

The JIT loader piggyback fires arch_check only when the user prompt
contains ≥2 design-verbs from `arch_check_vocab.json:verbs` (Spanish +
English coverage: diseña, diseñar, arquitectura, implementar, propón,
proponer, debería, deberíamos, elegir, escoger, build, design,
architecture, propose, should-i, which, choose, between, vs, plan,
strategy). The floor prevents firing on trivial prompts.

## 7. Output format (context injection)

```
ARCH-CHECK [<verdict>]
- <source 1 file>:<line range or section> -> <one-line summary>
- <source 2 ...>
- <source 3 ...>

Why this surfaced: <one sentence connecting prompt entities to sources>.

This is advisory. The agent decides what to weigh.
```

Maximum 200 words. Never paraphrases the source; quotes the literal
short phrase that triggered the match.

## 8. Failure modes (fail-open)

| Failure | Behaviour |
|---|---|
| Index file missing | CLEAR + log to `vault/.arch-index/log` once per session. Never blocks. |
| Timeout (>3 s fast) | CLEAR. Never blocks. |
| Subprocess crash | Hook continues. Never blocks. |
| Vocab file missing | Fallback to a 30-verb hardcoded list. CLEAR if no matches. |

## 9. Closed loop via UKDL

When `/arch-decision --deep` writes an ADR with Vault-conflicts != [],
a UKDL-AC-NN row is appended to `vault/knowledge_base/ukdl-universal.md`
referencing the ADR file. This is Owner-applied (the agent proposes the
row; Owner accepts via running the proposer). Closed-loop without
silent mutation, per Axis B of apex (Async-Audit: READ + PROPOSE only).

## 10. Mirror-Sync-Direction

This skill ships PP-only files plus one piggyback on
`tools/jit_skill_loader.py` (already in PP + loose). No new
`~/.claude/hooks/<file>.js` is added (Component 2 extends the existing
JIT loader, satisfying the hook-fanout-systemic-cost lesson). The
agent NEVER writes to `~/.claude/hooks/`; loose -> PP is the only
sync direction.

## 11. Recursion guard

The fast-path `arch_check.py` spawned from inside the JIT loader
sets `CLAUDEPP_ARCHCHECK_RUNNING=1` (env). If the loader detects this
env on entry, it short-circuits with CLEAR — prevents the LLM-side
ADR generation from re-triggering its own arch-check on recursive
prompts. Sister to `CLAUDEPP_DEEPRESEARCH_RUNNING`,
`CLAUDEPP_AUTOTEST_RUNNING`.

## 12. DONE-gate (binary, no classifications)

A PP install is Apex-complete on the Architecture Decision Axis iff:

1. `vault/specs/arch-decision-skill.md` (this file) and
   `vault/plans/arch-decision-skill-2026-05-23.md` exist.
2. `modules/arch-decision/build_index.py` runs `python build_index.py`
   exit 0; produces `vault/.arch-index/index.json` with `len(sources) >= 50`
   and `arch_check_vocab.json` with `len(verbs)+len(concepts) >= 30`.
3. `modules/arch-decision/arch_check.py --fast` exit 0 for the V-block
   prompts; V-COLLISION/V-COLLISION-2 produce COLLISION; V-WARNING /
   V-WARNING-2 produce WARNING; V-CLEAR produces CLEAR; V-TIMING shows
   p95 < 3.0 s over 10 runs.
4. `commands/arch-decision.md` registered (visible in available-skills
   list after `/restart`).
5. `tools/jit_skill_loader.py` integration tested empirically: synthetic
   prompt with ≥2 design verbs + 1 known veto entity returns context
   injected into `additionalContext`; prompt without verbs returns no
   injection.

Missing any of 1-5 = NOT Apex-complete on the Architecture Decision Axis.

## 13. Opt-out

`CLAUDEPP_ARCHCHECK_DISABLED=1` env var disables the JIT piggyback for
the current session. Honest opt-out; documented; never silent.

## 14. Cross-references

- `knowledge_vault/core/apex-completion-standard.md` (target axis)
- `vault/lessons/hook-fanout-systemic-cost.md` (why piggyback, not new hook)
- `vault/lessons/windows-argv-limit-stdin-fix.md` (STDIN vaccine)
- `vault/specs/auto-testing-gate.md` (sister axis architecture)
- `vault/specs/deep-research-agent.md` (sister axis architecture)
- `~/.claude/projects/.../memory/MEMORY.md` (source for vetoes index)

## 15. Future extensions (NOT in this cycle)

- Multi-language vocab (currently Spanish + English).
- Per-project vocab overrides via `<repo>/.arch-vocab.json`.
- Embedding-based semantic match (currently TF-IDF + Jaccard only).
- Automatic UKDL row write (currently Owner-applied; the propose-only
  posture is intentional per Axis B).

These are explicit scope cuts. Adding them later does not change the
DONE-gate above; the DONE-gate is what makes the axis complete TODAY.
