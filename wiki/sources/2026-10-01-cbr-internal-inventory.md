---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-cbr-internal-inventory]
raw: raw/2026-10-01-cbr-internal-inventory.md
kind: note
origin: read-only audit subagent, 2026-10-01, ~67 tool calls; repo @ 298975d
---

# CBR internal inventory (audit, 2026-10-01)

A subagent's read-only audit of the Constitutive Baseline Ratchet (`modules/tower`, `vault/tower`,
the delivery path in `modules/gsd_x/cli.py`), with file:line evidence in 13 sections. Feeds
[[cbr-gap-analysis]] and [[constitutive-baseline-ratchet]].

## What I re-verified myself

- Delivery is live: real session ids in `consumption.jsonl` (35 family rows, 20 sessions) and
  `hook-dispatcher.js:552` → `gsd_x_tier.js`.
- `cli.py:143-145` promises a done-gate; grep finds no caller of `donegate` or `ratchet.promote`
  outside tests and my probe. `family_baseline.py` has no `promote` command.
- Only B0 exists. 0 of 60 checks are runnable; reproduced with `wiki/tools/cbr_probe.py`.
- `tools/test_baseline_generations.py` 15/16, with 9 QUOTE_MISSING origins: re-run.

## Corrected

- The audit says all 47 capsules carry the identical lesson set. Measured: 43 of 47 share one set
  of 6 lessons, and the other 4 differ by one lesson. The conclusion (near-global, not per repo)
  stands; the figure was wrong.

## Taken from the audit without re-checking

- Tower suites: capsule 16/16, checks 23/23, donegate 10/10, inheritance 16/16, o4 7/7, ratchet
  21/21, select 15/15; family_baselines 20/20, family_injection 23/23.
- Liveness run: `tower/donegate` and `tower/ratchet` ORPHAN.
- O0 numbers (36 pairs, 540 verdicts, 470 UNJUDGED), the deposit ledger (3,914 rows, 94%
  landed-commit, `portability_proven` 0), and 58% UNKNOWN capsule offers.
- Doctrine-only items: A/B/C/D gate, Lift arithmetic, Propagation Set, Resident Kernel, Project
  Mission Genome.
