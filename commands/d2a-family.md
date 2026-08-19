---
description: Size a whole proposed family at once — FOLD/MERGE/KEEP/DEFER per system plus the STOP #1 menu, including the expansion option that proposes genuinely-new adjacent systems for the slots the overlap freed.
---

# /d2a-family

The single-proposal path scores an entire multi-system brief as **one bag of words**, so
it cannot resolve ownership per system — it returns one capped verdict for twenty-five
different questions. This command runs the *family* path, which scores each proposed
system separately against sealed parents and against its own siblings, then emits the
STOP #1 menu.

This file is also what makes `build_stop1_menu()` reachable. Reachability seeds from
`commands/*.md`; without this command the expansion machinery is live code behind a CLI
nothing invokes (`vault/specs/d2a-family-wiring.md` §1).

## Run it

Decompose the brief into one record per proposed system, write the list, run the engine:

```
[
  {"name": "UISC", "description": "universal intent and specification compiler ..."},
  {"name": "UASE", "description": "architecture synthesis engine ..."}
]
```

```
python modules/duplicate_to_advantage/d2a_engine.py --family-file <f>.json --repo-evidence
python modules/duplicate_to_advantage/d2a_engine.py --family-file <f>.json --repo-evidence --json
```

Write `<f>.json` to the session scratchpad, not into the repo. `--repo-evidence`
corroborates the expansion space with deterministic repo signals (registry gaps + the
Liveness Ledger); it is off by default so the family path stays hermetic.

**Decomposition is yours, not the engine's.** One record per *proposed system*, each
description in the brief's own words. Merging two proposed systems into one record hides
a duplicate; splitting one into two manufactures a family that was never proposed.

## What comes back

| Disposition | Meaning |
|---|---|
| **FOLD** | already owned by a sealed parent — extend it, do not build |
| **MERGE** | several proposed systems collapse into one dataset |
| **KEEP** | genuinely new: no sealed parent, no sibling overlap |
| **DEFER** | a parent's vocabulary matched but precision was too low to name it — **UNKNOWN, not new** |

`DEFER` is the row that matters most and the easiest to misread. It is kept distinct
from `KEEP` on purpose so a plausibility-capped candidate is never reported as
genuinely new.

Then the STOP #1 menu:

```
A. Execution-first  -- build only the genuine residue
B. Archive          -- build nothing
C. Hybrid           -- residue + expansion, to the original proposed count
D. Expansion        -- N genuinely-new adjacent systems, N = expansion_slots
E. Pause            -- Owner reviews first
```

**C and D appear only when item-based overlap is strictly above
`expansion_threshold_pct`** (50 by default, `vault/config/d2a.json`). Below it the menu
is A/B/E — offering expansion without expansion machinery is the hollow offer this whole
mechanism exists to remove.

## What option D is, and what it is not

D **harvests** the candidates already scored in each folded item's portfolio — verticals
(DEEPEN / HARDEN / AUTOMATE / DETERMINIZE) and horizontals (CONNECT) — then dedupes,
rejects any candidate that scores ≥50% against a *foreign* parent, attaches a novelty
disposition, and ranks. It is bounded by adjacency to measured parents.

It is **not** free-form brainstorming, deliberately. Inventing sibling systems from
nothing is what `HR-NOVELTY-001` exists to stop, and this estate's base rate — fifteen
consecutive mega-corpus proposals measured majority- or fully-owned — says free
generation would mostly produce more duplicates.

If fewer candidates survive the filters than there are slots, the plan reports
`n_requested` vs `n_survived` and states the shortfall. **Padding to hit N is
forbidden.**

## Before acting on the result

- `vault/audits/apir/NON_DUPLICATION_LEDGER.md` — a DO-NOT-BUILD row reopens only on
  measured evidence, never on a new name.
- `HR-NOVELTY-001` — the 13-question proof against a **discovered** sweep before any new
  institutional system is admitted. A candidate marked `NEEDS_NOVELTY_PROOF` ships with
  all thirteen attached and is never auto-admitted.
- A `NOT_TRIGGERED` novelty disposition is **not** an exemption; the self-duplication
  filter is the real gate.
