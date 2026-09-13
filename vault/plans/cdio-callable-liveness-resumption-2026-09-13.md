---
title: CDIO hard-filter reachability repair + the callable-liveness rung — what is proven and what is still open
date: 2026-09-13
tier: T2
status: FIVE COMMITS LANDED, VERIFIED. Open items are named below and none is blocking.
covers: [cdio, cdio_scorer, design_gate, review_gate, experience_contract, callable_reach,
         liveness, callable_liveness, gate_honesty, anti_slop, font_stack, reduced_motion]
---

# Resumption — CDIO reachability and gate honesty

Not `RESUMPTION_FILE.md`: that file is a 56-day-old ACTIVE-TASK ROUTER for the DAIF and
Crawl OS builds, it carries an explicit "do not delete" instruction, and it was already
dirty with an earlier session's uncommitted work. Overwriting it would have destroyed
state this session does not own.

## Identity

Repo `C:\Users\User\.claude\skills\claude-power-pack`, branch
`feature/knowledge-acquisition`. Session HEAD at start `87d5a38`; at end `e118d31`.

## The thesis, in one line

CDIO's problem was never its standards — it was that almost nothing automatic ever ran
them, and both the documentation and a 44/44 green suite said otherwise.

## Exact state — SEALED

Five commits, oldest first. Each is independently revertible and each carries its drill.

| commit | what |
|---|---|
| `4cb7a23` | the reduced-motion floor was conditioned on a contract *existing* |
| `76b23cc` | a comma defeated the anti-slop font check; SKIP claimed done |
| `45fe269` | the hard filters had no production caller; run them, report-only |
| `50a3e20` | third liveness rung — an exported function is not a called function |
| `e118d31` | say which path enforces and which reports; distil the session |
| `d09ab49` | repairs from the adversarial pass, **including a regression I caused** |

**Coherence anchor.** All five suites green:

```
python tools/test_cdio.py                  # 8/8
python tools/test_design_gate.py           # 12/12
python tools/test_experience_contract.py   # 19/19
python tools/test_cdicf_scope.py           # 10/10
python tools/test_callable_reach.py        # 6/6
python -m modules.liveness.callable_reach  # exit 0, 1369 frozen, no new, no stale
```

If `callable_reach` reports NEW debt, that is the ratchet working: wire the callable or
delete it. Never edit `vault/liveness/callable_inventory.json` to make a red run green.

## Active decisions (Owner-approved this session, do not reopen without reason)

1. **Report-only on the automatic path.** `review_gate(..., enforce_hard_filters=False)`
   from `design_gate.py`. Filters are seen, appear in the reason, withhold `is_done`, and
   cannot BLOCK. Enforcing mode remains the default for direct/agent callers.
2. **Honest claim + wire what is derivable** for the 16 prose-only checks. The honesty
   half landed; the wiring half is open (see below).
3. **PP-wide frozen inventory** for the callable ratchet, not CDIO-only and not a hard
   gate.

## Open — nothing here is blocking, each is named so it cannot be lost

1. **UKDL router pointer, OWED.** The distillation is at
   `vault/knowledge_base/callable-liveness-and-gate-honesty.md`. The one-line pointer into
   `vault/knowledge_base/ukdl-universal.md` was NOT added because that file carries another
   session's uncommitted work. Add it once their edits land.
2. **`hooks/cdio_visual_advisory.js` tells the agent a SKIP'd document "clears the
   anti-slop floor"** (`adviseReview`, reached for any non-BLOCK verdict including SKIP).
   That is the D1 defect surviving in the hook. NOT fixed here: that file holds 68 lines of
   uncommitted work from an earlier session, and committing it would package their changes.
   Fix once the tree is clean.
3. **D2 — `REVISE` is structurally unreachable on the automatic path.** Measured: the only
   non-critical deductions available are two majors, so the floor is 84 ≥ 80 (APPROVE), and
   any critical forces BLOCK. A DESIGN.md with several contradictory `experience:` fields
   collapses to ONE major and is APPROVED. The fix (one verdict per coherence problem)
   changes score COMPOSITION, which this codebase repeatedly and correctly calls a
   regression rather than a gate — so it is an Owner decision, not an autonomous change.
4. **D3 — `score_review([])` returns 100/APPROVE**, and `review_gate([], declared={...},
   observed={"unrelated": True})` returns `is_done=True`/CONFORMING. Zero evidence reads as
   a clean bill. Same reason as D2: fixing it changes a sealed core contract. Needs an
   abstain state kept away from the neutral one.
5. **Wire the derivable mechanical checks** (contrast pairs, spacing scale, type levels are
   derivable from DESIGN.md tokens; tap-target and the CDIO-07 behavioural floors are not,
   without a render path).
6. **No rendered surface is ever observed automatically.** Everything automatic reads
   declarations, and the automatic path always passes `observed_experience=None`, so it
   **cannot** detect the rendered reduced-motion breach `4cb7a23` repaired. That repair is
   reachable only from the agent path. Do not claim the WCAG floors are enforced in
   production.
7. **No transitive reachability in `callable_reach`.** There are no roots and no call
   graph: references are unioned across every non-test Python file, so two dead modules can
   certify each other, and a call inside a function nobody invokes counts like one on a
   live path. Named in the module docstring under the three EXCUSING cases. Closing it
   means a real call graph from declared roots — a different, much larger instrument.
8. **Nothing runs the callable ratchet automatically.** It is a CLI plus a `/liveness`
   entry. No hook, no CI, no Stop-chain. It is therefore subject to the exact defect it
   detects, one level up: a gate nobody invokes.
9. **The hook boundary is untested.** Every gate calls `design_gate()` in-process. Nothing
   spawns the real subprocess, parses its stdout, or asserts the hook turns a BLOCK into a
   `permissionDecision: deny`. The report-only findings are likewise never shown to reach
   an actionable consumer.
10. **`V-DESIGN-HARD-FILTERS-REACHED` does not require the experience filter.** It reads
    `exp` and prints it but never asserts it, so removing automatic experience-filter
    participation would leave that gate green.
11. **"Dependency resolved" means declared in `package.json`**, not installed, resolvable
    or usable. The negative control only adds a declaration.

## Next three concrete actions

1. Take the Owner decision on **D2/D3** — both change score composition, which this
   codebase correctly treats as a regression risk rather than a free fix.
2. Close **(9)**: one test that spawns `design_gate.py` as the hook does and asserts the
   deny path, since that is the only boundary the product actually uses.
3. Add the UKDL router pointer once `ukdl-universal.md` is clean, and decide whether the
   callable ratchet earns a Stop-chain hook (8).

## Start instruction

Run the six commands under **Coherence anchor**. If all green, the sealed work is intact
and you may start at *Next concrete actions*. Do not re-derive the reachability finding —
it is measured, fixed, and drilled. Do not run
`python modules/liveness/reachability.py --baseline`: the remaining 20 module-level
offenders are another session's in-flight `knowledge_acquisition` work.
