---
title: Doctrine Law-ID Registry
tier: governance
purpose: Canonical home for named doctrine laws (DNA-NNNN IDs). Distinct from the rigor-measurement axis `highest_dna` tracked in tools/baseline_ledger.py.
---

# Doctrine Law-ID Registry

> **Note on terminology.** `DNA-NNNN` serves two independent purposes:
>
> - **As a law-ID** (this file): a named doctrine policy. Immutable once assigned.
> - **As a measurement** (`tools/baseline_ledger.py` axis `highest_dna`): the rigor level a project has reached. Monotonically elevating.
>
> A project can reference law-IDs (e.g. "must comply with DNA-400") while simultaneously tracking a rigor measurement (`kobiicraft: highest_dna = DNA-400000`). The two never collide because one is a name, the other a number.

## Registered Laws

| Law-ID | Title | Summary | Canonical Reference |
|--------|-------|---------|---------------------|
| `DNA-400` | Supremacía Empírica | Complex logic (>20 LOC, cross-module, state machine, concurrency, protocol handler) requires sandbox execution or synthetic-test evidence from the current session before delivery. Model reasoning alone is a vector of error — cite a `sleepless_qa` verdict.json or captured stdout/exit-code. | `modules/governance-overlay/core.md:21`, `modules/executionos-lite/sovereign-feature-template.md`, Mistake #51 |
| `DNA-2500` | Visual Sovereignty Standard | Visual output (UI, render, shader, asset, animation) must pass the 3-gate SUPREMACY cascade: game-feel-codex cites, adversarial-longevity exploit tree, voice-spec-lock recognition test. Missing any cite = REJECT. | `knowledge/iteration-prompts/visual-v1.md:16` |
| `DNA-25000` | Global Singularity Baseline | Any engineering advance in one sub-project auto-elevates the ecosystem's Global Baseline. Code that has not passed the Omni-Council (`modules/governance-overlay/council.md`) is forbidden from merge. Translator Hook (`~/.claude/hooks/baseline-translator.js`) fires on every UserPromptSubmit and bumps the per-axis `global_max` in `tools/baseline_ledger.py` when evidence is attached. | User directive, session 2026-04-19. Enforced by `baseline-translator.js` + Council verdict in `pre-output.md` Section 13. |

## Relationship to the Baseline Ledger

The ledger at `~/.claude/vault/global_baseline_ledger.json` tracks the **current rigor value** each project has reached on four axes:

- `k_qa` (prompt protocol version, e.g. `v310.0`)
- `k_router` (router framework version, e.g. `v2.0`)
- `engineering_baseline` (internal rigor tier, e.g. `v41.0`)
- `highest_dna` (current DNA measurement, e.g. `DNA-400000`)

When a project elevates its `highest_dna` measurement, that is a **value change**, not a new law. This registry is consulted only when introducing a **new named law** (e.g. adding `DNA-30000 Threat-Model Mandate` would warrant a row here).

## Process: Adding a New Law

1. Assign the next available DNA-NNNN ID (avoid collision with existing measurements on any project — check `python tools/baseline_ledger.py --max`).
2. Append a row to the table above.
3. Cite the enforcement surface: which overlay file (`modules/governance-overlay/*.md`), which gate (pre-task / during-task / pre-output / post-output), which Mistake-registry entry if applicable.
4. If enforcement requires code, pair the law with a concrete check in the overlay; a law without enforcement is documentation, not doctrine.
