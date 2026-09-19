# GSD X — resumption contract after wave N3

**Written 2026-09-19.** Self-contained: a fresh worker continues from this file with no
prior conversation.

## Identity

- Repo `C:\Users\User\.claude\skills\claude-power-pack`
- Canonical **development**: `feature/knowledge-acquisition`
- Canonical **release**: `main` — advanced to `06d88cd`, equal to `origin/main`
- Historical, **not deleted**: `gsd-x` (`a3411c9`), `integrate/gsd-x-landing` (`42dd006`) —
  both had zero commits unique to `main`

## What must NOT be re-litigated without new evidence

1. **There were never three competing GSD X realities.** Both legacy branches are ancestors
   of `main` with zero unique commits. Do not spend a wave "merging old GSD X branches".
2. **Dependency staleness cannot detect knowledge going stale by omission.** Measured: of
   the 12 surfaces the 21 path-naming claims were observed against, **zero** moved across
   the 27-commit delta, while the ledger was decisively stale. A coverage sweep scoped to
   claimed surfaces returns empty and rebuilds the defect inside its own detector. Coverage
   is scoped to the **complement**. This is measured, not argued.
3. **`claims.jsonl` is PROGRAM-level knowledge about GSD X.** It is not a mission database.
   Mission runtime state belongs to GSD's `.planning/`. Do not store mission unknowns here.
4. **Semantic name overlap does not prove contract equivalence.** Three equivalences were
   proposed and all three failed a contract audit: program `UNPROVEN` rows are not a
   reusable mission Unknown Queue; `NOT_BUILT_BY_DECISION` is not mission-level negative
   completeness; the five-state vocabulary is not reconstruction epistemics (`PREDICTED`,
   `INTERVENTION_CONFIRMED`, `UNDERDETERMINED`, `CONTAMINATED`, `UNOBSERVABLE` have no
   representation, and `UNPROVEN` collapses three different failure semantics into one).
5. **`main` is advanced by compare-and-swap** `update-ref <ref> <new> <old>`, never the
   single-argument form, and never from the dirty checkout.

## State

**N3 is CLOSED.** Ledger 69 → 86 claims, 30 pinned, coverage zero.

    dataset gate   10/10  exit 0        drill  10/10  exit 0  (both poles)
    GSDX suite     14/14  exit 0        reconciler  0 findings, exit 0

Production Reality boundary earned: **ACTUAL REPO EVIDENCE RECONCILED** — the producer ran
against the real 27-commit delta, no hash or message hardcoded in the predicate.

`continuation-proven-live` v1 is **untouched and preserved**. Phase 1 positive leg remains
`BLOCKED_BY_RESOURCE` (needs a live subject session in an extension-owned terminal above the
1500 MB floor); acceptance is still `PARTIAL`, 3 crossings / 1 confirmed resume, and PROVEN
still needs a second. Its criteria were not softened. Another pane is actively working it
(`e2acb69`, two-pane drill identity by nonce).

## Open, with exact next action

| item | state | next |
|---|---|---|
| `dormancy-reverted` mutation **SURVIVES** in `tools/test_gsd_x_mutation.py` (1/2) | pre-existing, unrelated to N3 — test and subject `modules/gsd_x/tier.py` byte-identical at `3e56322`, `fd87e39` and HEAD | write the test that catches reverting the dormancy fix, or classify the mutant as equivalent/unreachable with a traced producer argument |
| `EXTERNAL_GITHUB_ENFORCEMENT_PENDING` | `.github/` does not exist; nothing enforces gates at merge time | add a workflow running the four checks + branch protection on `main`; needs repo-admin authority |
| UKDL promotion of 5 rule candidates | `PROMOTION_PENDING_CONCURRENT_WRITER` | `vault/knowledge_base/ukdl-universal.md` held **1,061** uncommitted foreign rows; promote when that writer lands. Candidates are in `vault/lessons/knowledge-stale-by-omission.md` with intended levels |
| 56 of 86 claims unpinned | frozen inventory in `test_gsd_x_dataset.py`, shrink-only | backfill `depends_on` on further subsets; the ratchet fails on new debt and on stale entries |
| `depends_on` kinds `gate:` / `report:` | declared, **not implemented** — the reconciler processes `path:` only | implement or remove; an unenforced pin that looks enforced is this wave's own failure class |
| `GSDX-C08` (orca-exact re-entry) | still UNPROVEN, correctly | not credited by the terminal-inbox confirmation in `GSDX-C14` |

## Next highest-leverage work

The Mission Intelligence Spine's first vertical slice — sparse intent → Mission Contract
projection → **Derived Obligation with provenance** → proof requirement → GSD planning seam
→ evidence-governed transition → closure receipt. N3 was its precondition: building a
Mission Contract on a ledger 27 commits stale reproduces the defect one layer up.

Owners that must **not** be duplicated: GSD Core (lifecycle, plan-drift, capability
registry, worktree safety, state authority) · Capability Runtime (applicability) · Graphify
(typed edges — a regenerable cache under `~/.claude/state/graphify/`, which is why it cannot
own a committed ledger) · Done Gate + strength ladder + Production Reality · `gsd_long_run` +
context-watchdog + continuation transport (one door) · Oracle/OSR (instrument registry).
