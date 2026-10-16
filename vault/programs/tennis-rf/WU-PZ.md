# WU-PZ -- reprice the Tennis residual by class; next strategy or terminal verdict; record confirmed failures

Plan: `vault/plans/r2-failure-recompile-2026-10-16.md` (Owner "y" 2026-10-16). Hard cap 1.0M tokens. No searches over trees:
open the named files directly.

## Handles
- Pilot result: PP `vault\programs\tennis-rf\WU-PX-receipt.md` (+ `D\factory\priors.jsonl`, `D\factory\negative.jsonl`
  in `C:\Users\User\Apps\recon_work\wt_tennis_rf\tools\wros\binary\decomp`)
- Residual population: PP `vault\programs\tennis-rf\evidence\d28\d12\residuals_v1.jsonl`, `hypergraph.json`,
  `evidence\d28\d3\residuals.jsonl`; D12a/b/c receipts.
- Budget: `python tools\mission_spend.py programme-status --goal tennis-rf` (run in PP root).

## Steps
1. Class counts for the class 2-5 residual (near-match where signals exist / known family / semantic / architecture
   blocker / unknown). UNKNOWN stays its own class.
2. Per class: expected cost = population x PX's measured cost per MATCH for that class. A class with no measured close
   is UNPRICED, with the spend that produced 0 closes.
3. If a class is positive-EVC and fits the remaining programme capital: write `vault\programs\tennis-rf\NEXT.md`, a ready
   packet draft for it, with budget and stop-loss (the coordinator arms it after Owner capital review if needed).
   Otherwise write `vault\programs\tennis-rf\VERDICT.md`: what is closed (canonical MATCH count from the ledger), what each
   remaining class would cost, and why stopping is correct.
4. Knowledge entries, confirmed only (dedupe against `vault\knowledge_base\ukdl-universal.md` first):
   - coordinator spend off-ledger (19.25M + 7.06M; the settle cap)
   - worker died during host-wide tool starvation with no exit code captured (R2: every tool timed out, decomp tree only 155 files)
   - static chain end routed to an Owner question
   - a non-discriminative control (D12c wrong-width)
   - T1 left unmeasured by the held-out design
   - anything PX confirms

## Receipt `WU-PZ-receipt.md`
Class table, tranche costs, NEXT.md or VERDICT.md, entries written (ids), commits.
