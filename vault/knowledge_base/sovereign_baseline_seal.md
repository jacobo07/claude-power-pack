# Sovereign Baseline Seal — BL-0068

**Sealed:** 2026-05-16
**Hash-chain parent:** BL-0063 (ULTRA ONESHOT 7-phase, CLI capacitation, 2026-05-04)
**Workstream:** KPP-KARIMO CORE FUSION & OPENSESESH ABSORPTION → GLOBAL KARIMO FUSION & SOVEREIGN BASELINE SEALING
**Protocol:** /ultra plan, all 7 phases executed in order (no skip).

## Declaration

The Sovereign Baseline operates at the intersection of **Context
Engineering (KARIMO)** ∩ **Forensic Recovery (Lazarus v3)**. This is the
Apex Standard for all future holding projects.

## Materialized this seal

| Deliverable | Artifact | Verification |
|---|---|---|
| PRD auto-ingestion | `modules/karimo-harness/prd_parser.py` (+ `schema.json`, fixture) | `test_karimo.py` G1–G3 Exit 0; deterministic sha256 round-trip |
| Explicit PRD path | `commands/cpp-prd-parse.md` | functional, no registration needed |
| 150-tool design index | `tools/design_index.py` + `design_tools_dataset.json` (10 real systems × 15 patterns) | 6 real queries → ≥3 hits each, <0.51 ms (gate <250 ms) |
| Design retrieval | `commands/cpp-design.md` | BM25 OR-terms, punctuation-injection safe |
| Atomic branding | `tools/atomic_branding.py` + `test_atomic_branding.py` | tiktoken-measured, `node --check` valid, deterministic |
| Jobs/Woz hybrid gate | in `atomic_branding.py` | threshold 2,500 tiktoken/component; Jobs WARN / Woz VETO |
| Global coupling | `~/.claude/CLAUDE.md` Sovereign Baseline section | physical `git diff` (Q6 gate #4) |

## Q&A lock (ONESHOT Phase 2)

- Q1 Hybrid: baked canonical dataset + opt-in `refresh_sources.json` (network-immune).
- Q2 Both: `PRD_BASELINE.json` source of truth + on-demand `<prd-constraints>` hook injection.
- Q3 Extended `tailwind.config.js` + sibling `motion-tokens.ts`.
- Q4 Jobs/Woz hybrid, 2,500 tokens/component (tiktoken cl100k_base; ceil(len/4) fallback).
- Q5 Both: `UserPromptSubmit` keyword hook + explicit `/cpp-prd-parse`.
- Q6 4-gate DONE: test_karimo Exit 0 · /cpp-design <250 ms ≥3 · PRD↔baseline parity · CLAUDE.md git diff.

## Audit (ONESHOT Phase 4–5)

`oneshot-architect-auditor` returned 11 gaps (3 BLOCKER, 6 MAJOR, 2 MINOR);
all folded into the executed plan (FTS5 isolation, fresh-clone safety,
real dataset provenance, hookSpecificOutput schema, measurable token gate,
pure-blueprint invariant, atomic writes, WAL).

## Owner-gated residue — CLOSED 2026-05-16

Both items were explicitly Owner-authorized by name in a follow-up
`/ultra plan` run and executed under the full 7-phase protocol
(audit: 11 gaps, 4 BLOCKER, all fixed pre-execution):

1. **`~/.claude/settings.json`** — ✅ CLOSED. `prd-keyword-sentinel.js`
   registered as the 3rd `UserPromptSubmit` entry under Q3a safety
   (timestamped backup `settings.json.bak-1778924478`, structural
   post-write assertion: array len exactly 3 + exactly 1 sentinel ref,
   discrete auto-rollback). Standalone-verified (exit 0, real
   `hookSpecificOutput`); live in-pipeline fire is cold-load-bound
   (next `/restart`) — stated honestly, not overclaimed. Mirror:
   `harness_mirror_settings.md`. Commit `23876f0`.
2. **`~/.claude/commands/ultra.md`** — ✅ CLOSED. Additive advisory
   Phase-1 KARIMO pre-pass applied to repo mirror + live, verified
   byte-identical (465 chars); Phase-2 mandatory-stop semantics
   asserted unchanged. Effective next `/ultra` (cold-load). Commit
   `e5c0571`.

Key takeaway: the auto-mode classifier gates self-modification on
*specific per-action authorization*, not a blanket autonomy mandate —
explicit by-name Owner authorization passed where the general mandate
was denied. The toolchain functioned without these the whole time;
they are convenience couplings now landed.
