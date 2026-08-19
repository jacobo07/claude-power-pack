---
title: D2A family wiring — join the automatic trigger to the expansion menu
date: 2026-08-19
tier: T2
status: APPROVED — Owner "2 con 1 dentro, go ahead" (2026-08-19)
covers: [d2a, d2a_engine, duplicate_to_advantage, d2a_gate, family_path, family_sizing,
         expansion, expansion_option, stop1, stop_1, sibling_systems, decomposition,
         d2a_family_command]
origin: Owner question 2026-08-19 "por que D2A no hace brainstorming automatico de nuevos
        sistemas hermanos cuando hay duplicados?"
supersedes_scope_note: vault/plans/d2a-expansion-2026-08-03.md §6 ("No new hook ...
        a UserPromptSubmit/Stop trigger is a separate, Owner-gated follow-up") — this
        IS that follow-up, now Owner-gated and approved.
---

# Spec — D2A family wiring

## 1. Problem, measured at source

The expansion machinery exists, is tested, and is unreachable from the only automatic
surface. Verified by direct read on 2026-08-19, not recalled:

| Fact | Evidence |
|---|---|
| the brainstorm exists | `d2a_engine.py:1292 compute_expansion()`, `:1392 build_stop1_menu()`, `:1428 render_stop1_menu()`; option **D** = "N genuinely-new adjacent systems" |
| it is reachable on two paths only | `:1134` inside `render_family()`, and `:1536` the `--family-file` CLI |
| the automatic surface takes the other path | `hooks/d2a_gate.js:146` → `execFileSync(python, [ENGINE, '--stdin', '--json'])` — the single-proposal path, which never enters `render_family()` |
| the hook knows and says so | its advisory prints `2. python ... --family-file <f>.json` as an instruction for a **human** to run |

Two working halves, no joint. The gate can say *a duplicate is here*; the thing that
converts a duplicate into sibling proposals sits behind a CLI nobody automatically calls.

Observed consequence, 2026-08-18: on a 25-system brief the gate fired, returned
`UNDETERMINED` at 45% capped coverage, named the instrument — and stopped. The family
analysis that found 22 of 25 already owned was done by hand.

## 2. What is NOT the problem, stated so it is not "fixed"

The harvest is deliberately **not** free-form invention. `d2a-expansion-2026-08-03.md`
§3.1 harvests the ≥6 already-scored candidates from each folded item's `portfolio`;
§6 forbids a new gap-discovery engine. That constraint is correct and is preserved
here: free-form generation of sibling systems is what `HR-NOVELTY-001` exists to stop,
and this estate's base rate — fifteen consecutive mega-corpus proposals measured
majority-owned — predicts free generation would mostly produce more duplicates.

**This spec changes reachability, not generation.**

## 3. Design

### 3.1 `/d2a-family` — the command (Owner option 1)

A live surface that takes a decomposed family and runs the family path end to end:
write `[{name, description}, ...]` to a scratchpad JSON, invoke
`d2a_engine.py --family-file <f> --repo-evidence`, present FOLD/MERGE/KEEP/DEFER plus
the STOP #1 menu. Reachability seeds from `commands/*.md`, so the file is what makes
`build_stop1_menu()` reachable at all.

### 3.2 The hook emits a decomposition REQUEST (Owner option 2)

`buildDeferAdvisory` currently ends in prose steps. It gains a structured, machine-
followable `DECOMPOSITION REQUEST` block naming `/d2a-family` explicitly, so the agent
performs the decomposition **in the same turn** and then runs the family path.

New: the **duplicate** branch (`buildAdvisory`) gets the same directive appended when
the brief is multi-system. A confirmed single-proposal duplicate verdict on a 25-system
brief is under-resolved in exactly the way the deferred branch already warns about, and
today it says nothing about the family path at all.

### 3.3 `isMultiSystemBrief(prompt)`

One exported predicate: `length > MEGA_LEN && countMatches(ARCH_NOUN_G) >= 6`. Reuses
the existing constants; adds no new tunable. It is deliberately *weaker* than
`isCreationProposal`'s mega branch (no `CREATE_VERB` count), because by the time it is
consulted the prompt has already passed that gate — re-testing the verb would be a
second, stricter filter applied to an already-filtered input.

### 3.4 Honest enforcement level

Level-2, unchanged. The hook cannot run the family path itself: it must not spawn a
long analysis inside a `UserPromptSubmit` frame, and decomposing free prose into
`{name, description}` records is a judgement operation, not a keyword one. **That is
the real reason this was never automated, and it is not closed by this spec** — what
closes is the gap between *the gate knows* and *the agent is told precisely what to
run*, with a command that makes running it one invocation instead of hand-authored JSON.

## 4. Files

| File | Change |
|---|---|
| `commands/d2a-family.md` | new — the live surface; makes the family path reachable |
| `hooks/d2a_gate.js` | `isMultiSystemBrief()`; `DECOMPOSITION REQUEST` block in `buildDeferAdvisory`; family directive appended to `buildAdvisory` on a multi-system brief |
| `tools/test_duplicate_to_advantage.py` | 4 new V-gates |

`d2a_engine.py` is **not touched**. The rollback story of the 2026-08-03 plan stays
intact, and no caller of `run()` / `run_family()` / `detect_duplicate()` changes.

## 5. Acceptance criteria (done-gate)

| Gate | Assertion |
|---|---|
| `V-D2A-FAMILY-COMMAND` | `commands/d2a-family.md` exists and names the exact `--family-file` invocation that reaches `build_stop1_menu` |
| `V-D2A-ADVISORY-DECOMPOSITION` | the deferred advisory carries `DECOMPOSITION REQUEST` and `/d2a-family` |
| `V-D2A-DUPLICATE-ROUTES-FAMILY` | a multi-system **duplicate** advisory also routes to the family path; a short one does **not** (no noise on ordinary proposals) |
| `V-D2A-FAMILY-REACHABLE` | the command's invocation string matches the engine's real CLI flag, asserted against `d2a_engine.py` source — so the instruction cannot rot into a flag that no longer exists |

Suite: `python tools/test_duplicate_to_advantage.py` → zero failures, hermetic ×3.
Umbrella: no new failing row.

## 6. Out of scope (stated, not silently dropped)

- **No automatic decomposition.** The agent decomposes; the hook requests it. Claiming
  otherwise would be a level-3 claim on a level-2 mechanism.
- **No new discovery engine.** §2 above.
- **No engine change.** Including no `--family-file -` stdin mode; a scratchpad file is
  auditable and keeps the engine's surface frozen.
