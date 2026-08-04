---
title: D2A+ — Expansion Option at STOP #1
date: 2026-08-03
status: APPROVED (Owner "y", 2026-08-03) — executing
tier: SDD-OS T2 (module + persisted config + multi-file + user-behaviour change)
covers:
  - d2a
  - d2a_engine
  - duplicate_to_advantage
  - stop1
  - stop_1
  - expansion
  - expansion_option
  - option_d
  - family_sizing
  - overlap_threshold
originating_rule: PR-D2A-EXPANSION-001
---

# D2A+ — Expansion Option at STOP #1

## 1. Problem

When a family-sizing audit measures N% of a proposed corpus as already owned, the
Owner is offered only two real shapes: build the residue, or archive. The space the
overlap freed is never converted into anything.

Measured instance (`vault/audits/apir/CPP_APIR_DATASET_ARCHITECTURE_PLAN.md:35`):
CPP-APIR came back ~80 % owned across 25 proposed datasets. The four options offered
were A execution-first (build the residue), B residue + thin doctrine tier, C defer,
D accept the 80 % duplication as a deliberate override. None of the four proposes
*new, non-duplicating* capability to occupy the ~20 vacated slots.

`vault/audits/ccfl_pdpf/STOP_1_VERDICT.md:104` shows the same shape at 35 proposed /
≈85 % owned.

## 2. Reality scan (premises verified before design)

Three premises in the originating prompt were falsified by direct read:

| Premise | Reality |
|---|---|
| "the STOP #1 menu is generated in `d2a_engine.py`" | It is not in any code. `d2a_engine.py:995 render_family()` emits FOLD/MERGE/KEEP/DEFER only. Menus are hand-written prose, authored fresh per audit, with per-audit option semantics |
| "validate each candidate against the existing 13-question Novelty Gate" | `modules/spec_gate/gate.py:271 check_novelty_gate()` is keyword-triggered and returns 13 *questions* plus `applies: bool`. It issues no verdict. Most candidates return `applies=False`, which is *not* a pass |
| "reuse the existing Empirical Gap Discovery framework" | `vault/plans/gap-discovery-2026-07-30.md` is a hand-run methodology (3 of 16 spaces swept by Glob/Grep). No executable framework exists |

Consequence: a code-only change would be an orphan (no audit would emit it), and a
doctrine-only change would be agent-memory-dependent — the exact failure shape that
plan's own GAP-1 documents. The fix lands in code AND doctrine AND a V-gate.

## 3. Design

### 3.1 Candidate source — already generated, never brainstormed

Every FOLDed / MERGEd item already carries a full `D2AVerdict` whose `portfolio` holds
>= 6 scored candidates (>= 3 vertical DEEPEN/HARDEN/AUTOMATE/DETERMINIZE, >= 3
horizontal CONNECT), each with 16 numeric dimensions, a ratio, and an anti-inflation
ledger. Those are adjacent capabilities derived from a real measured parent.

Option D therefore HARVESTS those portfolios, dedupes across items, filters, and ranks.
No new discovery system is built. This satisfies the constraint that expansion be
repository evidence, not free-form brainstorm.

### 3.2 Arithmetic

```
expansion_slots = proposed_count - recommended_count - len(defer)
overlap_pct     = round(100 * expansion_slots / proposed_count)
applies         = overlap_pct > expansion_threshold_pct     (strictly greater)
```

`defer` is subtracted because a DEFER is *unknown*, not *owned* — counting it as freed
space would over-claim. `expansion_slots` therefore equals folded + merged-away only.

`overlap_pct` is item-based, matching how the audits already report duplication
("≈83 %", "≈85 %").

### 3.3 Filters, in order

1. **Dedupe** by normalized `(operation, name)` key across all harvested portfolios.
2. **Self-duplication** — each candidate's own text is run back through
   `detect_duplicate()`. Rejected when it scores >= 50 % against a parent that is
   neither the family it reinforces nor the family it connects to. Reinforcing its own
   parent is the point; re-owning a third family is not.
3. **Novelty disposition** — `check_novelty_gate()` on each survivor.
   `applies=True` -> candidate is marked `NEEDS_NOVELTY_PROOF` and ships WITH all 13
   questions attached; it is never auto-admitted. `applies=False` -> `NOT_TRIGGERED`,
   which is explicitly NOT an exemption; filter 2 is the real gate.
4. **Rank** by ratio desc, then name. Take top `expansion_slots`.

Harvest is capped at `expansion_slots * expansion_candidate_multiplier` before
filtering, so the filters have surplus to cut from.

### 3.4 No padding

If fewer candidates survive than `expansion_slots`, the plan reports `n_requested` vs
`n_survived` and the shortfall is stated in the menu text. Padding to hit N is
forbidden (no-silent-caps doctrine).

### 3.5 The menu

overlap > threshold:

```
A. Execution-first  -- build only the genuine residue
B. Archive          -- build nothing
C. Hybrid           -- residue + expansion, to the original proposed count
D. Expansion        -- N genuinely-new adjacent systems, N = expansion_slots
E. Pause            -- Owner reviews first
```

overlap <= threshold: **A, B, E only.** C and D are both expansion-dependent (C is
"residue + expansion"), so emitting C without expansion machinery would reproduce the
hollow offer this work exists to remove.

## 4. Files

| File | Change |
|---|---|
| `vault/config/d2a.json` | new — `expansion_threshold_pct` (50), `expansion_candidate_multiplier` (2) |
| `modules/duplicate_to_advantage/d2a_engine.py` | `ExpansionCandidate`, `ExpansionPlan`, `Stop1Menu`, `load_config()`, `compute_expansion()`, `build_stop1_menu()`, `render_stop1_menu()`; menu appended to `render_family()` and to `--family-file --json` |
| `modules/duplicate_to_advantage/__init__.py` | export the new names |
| `tools/test_duplicate_to_advantage.py` | 5 new V-gates |
| `vault/knowledge_base/duplicate_to_advantage/D2A_INDEX.md` | the mandatory 5-option STOP #1 contract (INDEX only — the doctrine Parts are guarded at >2500 words each by `V-D2A-DEPTH`) |
| `vault/knowledge_base/ukdl-universal.md` | `PR-D2A-EXPANSION-001`, `T-D2A-RESIDUE-ONLY-001` |

## 5. Acceptance criteria (done-gate)

| Gate | Assertion |
|---|---|
| `V-D2A-EXPANSION-OFFERED` | overlap > threshold -> option D present, `n_requested == expansion_slots`, >= 1 surviving candidate |
| `V-D2A-EXPANSION-SILENT` | overlap <= threshold -> option D absent from the rendered menu |
| `V-D2A-EXPANSION-CONFIG` | threshold raised via config -> the same family stops offering D (proves not hardcoded) |
| `V-D2A-EXPANSION-NO-SELF-DUPLICATE` | no surviving candidate scores >= 50 % against a foreign parent |
| `V-D2A-EXPANSION-NOVELTY-CHECKED` | every candidate carries a novelty disposition; every `NEEDS_NOVELTY_PROOF` carries all 13 questions |

Suite gate: `python tools/test_duplicate_to_advantage.py` -> `D2A_PASS=n/n`, zero
failures, hermetic (3 consecutive runs byte-identical).

Repo gate: `REMOTE_DELTA 0 0` after a pathspec-scoped commit.

## 6. Out of scope (stated, not silently dropped)

- **No new hook.** Code + doctrine + V-gate does not mechanically force a future audit
  to emit the generated menu. That ceiling is the same class as this repo's GAP-1
  (`check_novelty_gate` correct in isolation, unreachable in practice). A
  `UserPromptSubmit`/Stop trigger is a separate, Owner-gated follow-up.
- **No new gap-discovery engine.** Option D is bounded by adjacency to the overlap's
  parents. It will not invent territory outside what the measured parents make
  adjacent, and it will not pad to N.
- **Existing audit documents are not rewritten.** APIR and CCFL-PDPF keep their
  historical menus; the contract applies to the next STOP #1 forward.

## 7. Rollback

Single-commit revert. The engine additions are purely additive (new functions + new
dataclasses); `run()`, `run_family()` and `detect_duplicate()` signatures and return
types are unchanged, so a revert cannot strand a caller.
