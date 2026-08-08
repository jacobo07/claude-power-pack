---
title: Ledger discovery — coverage by construction for cumulative ledgers
date: 2026-08-08
tier: T2
status: APPROVED — Owner selected "construir el descubrimiento de ledgers" (2026-08-08)
covers: [liveness, liveness_ledger, ledger_discovery, coverage_by_construction, discovered_registry]
audit: vault/plans/egcc-expansion-2026-08-07.md
---

# Spec — discovered ledgers

## Problem, measured

`modules/liveness/liveness_ledger.py` states the doctrine in its own docstring —
*"an undeclared component is not audited and not missed, so absence of a probe
reads as health"* — and applies it to modules: `_discovered_registry()` delegates
to `reachability.discovered_rows()`, auto-enrolling every module.

The ledger probes were left behind. They are still the hand-written rows, so
only two cumulative ledgers are watched:

| cumulative ledger | rows | watched |
|---|---|---|
| `vault/decision_registry/records.jsonl` | 1 | yes |
| `vault/dataset_first/necessity_ledger.jsonl` | 1 | yes |
| `vault/done_gate/receipts.jsonl` | 1 | **no** |
| `vault/ias/c2_opportunity_cost_ledger.jsonl` | 1 | **no** |
| `vault/anti_fragility/hacks.jsonl` | 1 | **no** |

The three unwatched are not scored UNKNOWN. They are absent from the
denominator, and absence reads as health — the defect this file names.

## The hard part: a ledger is not a log

`vault/` holds 954 `.jsonl` files. Counting thin ones naively returns 328,
because per-session telemetry (`jit_usage_<uuid>`, `rtk_<uuid>`,
`budget-<ts>`) holds one or two rows **by design** — one file per session. A
criterion that calls those starved would drown the five real findings in noise.

Both halves of the separation are measured from disk, never listed:

1. **Directory gate.** A directory holding more than `MAX_JSONL_IN_LEDGER_DIR`
   `.jsonl` files is a per-event store, not a ledger home. Measured separation:
   the largest ledger home (`vault/audits`) holds about 5; the smallest
   per-event store (`vault/research`) holds 52. Any threshold in 7..51
   separates them; **8** is chosen near the low end so a growing ledger home
   reports as a store rather than silently keeping members.
2. **Family gate.** Within a kept directory, stems are normalised by masking
   uuid, hex and timestamp runs. A family with `MIN_FAMILY_FOR_SERIES` (3) or
   more members is a per-session series. One file is a ledger; two may be
   coincidence; three of one shape is a series.

## Scope

1. `_discovered_ledgers(repo_root)` — emits registry rows in the **same shape**
   as the hand-written ones. Appended in `default_registry()` beside
   `_discovered_registry()`.
2. `_probe_ledger_rows` + its dispatch branch. `file-mtime` is the wrong probe
   here: it judges freshness, so a one-row ledger touched today reads LIVE. The
   new probe counts non-blank rows AND checks freshness.
3. Exclusions are returned and reported with counts and reasons.

## Non-negotiable constraints

| # | Constraint | Defect avoided |
|---|---|---|
| 1 | No ledger path is ever written down; the set is walked off disk | A registry enrolled by hand measures memory (`PR-COVERAGE-BY-CONSTRUCTION-001`) — the exact defect being repaired |
| 2 | Exclusions reported with counts and reasons, never silent | Silent truncation reads as "covered everything" (`no-silent-caps`) |
| 3 | Verdicts of the 358 pre-existing rows must be **byte-identical** | A change that silently re-scores history is a regression wearing a feature's clothes; the reference is pinned BEFORE the edit, never re-derived after (`feedback_reference_derived_from_post_state`) |
| 4 | A 1-row ledger is reported with its count, and is **not** a new failure verdict | A rare-event ledger legitimately holds one row. Distinguishing that from starvation needs the writer, which this does not open |
| 5 | 0 rows and a missing file are distinct verdicts | An instrument that collapses "empty" into "absent" cannot say which it found |
| 6 | Named ids and integers, never a ratio | A ratio is satisfied by shrinking its denominator (`feedback_never_gate_on_a_ratio`) |
| 7 | Fail-open per row and for the whole discovery | The existing module fails open; a discovery step that raises would take the whole audit down with it |
| 8 | Thresholds stated once, as named constants, with the measured gap that justifies them | A magic number nobody can re-derive is a decision with no author |

## Acceptance criteria

| Gate | Asserts |
|---|---|
| `V-LD-DISCOVERED` | A ledger written into a temp vault appears; removed, it disappears |
| `V-LD-SERIES-EXCLUDED` | 3 same-shape uuid files are excluded as a series, and the exclusion is reported |
| `V-LD-STORE-EXCLUDED` | A directory over the jsonl threshold is excluded as a store, and reported |
| `V-LD-LEDGER-KEPT` | A lone `records.jsonl` in its own directory is kept |
| `V-LD-EMPTY-VS-MISSING` | 0 rows and no file yield different verdicts |
| `V-LD-ROWS-IN-EVIDENCE` | The row count appears in the evidence string in both the live and the silent case |
| `V-LD-NO-RATIO` | No float and no ratio-like key in the emitted rows |
| `V-LD-EXISTING-UNCHANGED` | All 358 pinned verdicts identical, compared against the pre-change snapshot |
| `V-LD-LIVE-FINDS-THE-THREE` | On the real repo, `done_gate/receipts`, `ias c2` and `anti_fragility/hacks` are enrolled |
| `V-LD-FAIL-OPEN` | An unreadable tree returns rows rather than raising |
| `V-LD-HERMETIC` | Three consecutive runs byte-identical |

## Done-gate

Eleven gates pass, three identical runs, `reachability.py` offenders not
increased, `test_egcc_c1.py` and `test_egcc_residue.py` unchanged,
pathspec-scoped commit, `REMOTE_DELTA = 0 0`.

## Out of scope

Deciding whether any given thin ledger is starved or merely rare. That requires
opening each writer, and enrolling the subject is the prerequisite, not the
conclusion.
