# Gen2.1 Economic Kill-Shot -- readout (2026-10-05, STOPPED at the spend cap)

Unit: processed tokens (input + cache_write + cache_read + output, deduped by message id). All analysis zero-model.

## Spend (Owner cap: warn 10M, hard 15M from anchor 19,196,694 @ 11:13:02Z)
- Pane 87601e81 after anchor: 6,096,405 (21 calls). Pane tua-x-96 / 242ae047 after anchor: 8,435,275 (20 calls, `stage0/tua_spend.py`).
- **Gen2.1 incremental ~14.5M** (+ this commit). Total campaign incl. sunk Stage 0: ~33.7M. STOP: no further work without the Owner.

## A0 floor (main workers; `stage0/{ksr,kme}_a0.txt` via `stage0/a0_run.py` reusing `infinityops/io_*.py` unchanged)
| workload | floor mean | instructions | agent list | skill list | hooks (SessionStart+UPS) | other | soft sum | hard remainder (system prompt + tool schemas) |
|---|---|---|---|---|---|---|---|---|
| InfinityOps | 129k | ~45k | ~13k | ~12k | ~8.6k | ~4k | ~80k | ~40-49k |
| KSR | 121k | ~45k | ~9k | ~12k | ~8k | ~5k | ~79k | ~42k |
| KME | 138k | ~54k | ~18k | ~5k | ~8k | ~5k | ~90k | ~48k |
Instrument corrections: `io_attachments.py` divides per-worker lines by a hard-coded 8 (rescaled by 8/n above);
`io_context_rent.py` as committed still counts `prompt_snapshot` (KSR attribution 107.4%); KME tok/char calibration
broken on 2 of 3 workers (0.029) -> KME rent-class shares LOW confidence, floors (from usage) solid.
Split of the hard remainder into host vs account connectors: UNKNOWN (the only question left for an adaptive A1 after the reset).
- **Resident Prefix Tax** (floor rent / main context): InfinityOps 44%, KSR 44.9%, KME 49.2%; ~62-65% of the floor is CPP-controllable.
- In-run hook success text is context: ~11% (KSR, 21.9M) and ~13% (KME, 14.2M) of main context excluding prompt_snapshot; 7-13% on InfinityOps by regression.

## B call-elimination ceiling (`stage0/b_pass1.py`, pass 2 = quoted-path git fix, `b_pass2.txt`)
CLEAR (all tool uses mechanical): InfinityOps 4.0% calls / 3.3% processed, KSR 6.7% / 5.6%, KME 3.6% / 2.9%.
+ test invocations 0.5-2.0%. Below the 10% bar in all three -> **Model-Call Admission: do not build.**

## Meta-Work Tax (planner/researcher/verifier/checker/reviewer subagents / processed)
InfinityOps ~32% (planner 43.9M, researcher 35.8M, verifier 22.1M; executor 1.6M). KSR ~22% (planner 37.1M/5 runs) + 4.8% general-purpose.
KME ~1% (planning inline). Per plan: KME 11.9M vs KSR 24-28M vs InfinityOps 17.8-25.5M (suggestive, confounded by task type).

## Units
gen2 `ledger.json` budget now typed `processed`; `tools/cep_gen2.py` refuses an untyped or non-processed budget
(mutants untyped-budget, weighted-budget killed; selftest 12/12). Live ledger: unit failure cleared; 8 open W-units remain (pre-existing).

## Economics (central; old-architecture remaining: KSR ~430M, KME ~89M, InfinityOps P4 ~70M)
Levers, multiplicative: hook-text silence ~-8% (CPP, universal, cheapest) x soft-floor -20k ~-8% (instructions = E1/W3,
listings = skill-capability owner) x meta-work halved -11..-16% (GSD workloads) x bounded workers ~-20%. Central ~-42% (low -20%, high -60%).
- D dominant build: hook-output silence 2-5M; compiled Work Packets (planner/researcher elimination) 6-15M; capsule-v2 connect 2-5M; listings/instructions via their owners. **Low 6 / central 15 / high 30M.**
- First canary InfinityOps odr-device-trust Phase 4, compiled from paid state into 3 seam packets (~30 calls x ~140k each) + compile + one review on the founder-authority seam: **low 9 / central 16 / high 28M**; progress-adjusted stop, ceiling 35M (half the old 70M).
- Direct savings central ~238M (KSR ~180M, KME ~28M, InfinityOps ~30M); low ~100M.
- Gross return central ~5.8x on Gen2.1 + D + canary (~41M); ~4.0x including sunk Stage 0. Low case ~1.1x -> stage gates stay.
- Sensitivity: each 10k removed from every floor ~ 0.76B processed/week at the gen-1 D-W7 call count (75,969 calls). Not a saving.

## Recommendation (Owner decides)
1. Next build = hook success-text silence (measure estate-wide rent first; guards must still block) -- smallest cost, universal reach.
2. Then compiled Work Packets proven on the InfinityOps Phase 4 canary (after 2026-10-11T18:00Z).
3. Hand listings evidence to skill-capability gen2 and instructions evidence to E1/W3; do not rebuild them here.
4. Reject Model-Call Admission (ceiling 3-6%).