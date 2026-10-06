---
status: APPROVED (Owner "Aprobar todo", 2026-10-07, laptop session 08cb0d86) -- executing; see Execution log
covers: [edd-canary, edd-economics, compiled-execution, planner-extinction, deterministic-dossier, model-boundary-budget, edd-reforecast]
extends: vault/specs/orca-p4-compiled-execution-canary.md
---

# EDD (m-ee81e1595007) as a compiled-execution canary

## Verified reality (2026-10-06T21:56Z, GEX44, `edd-stage/edd_autopsy.py`, deterministic)
- RUNNING epoch 1, owner 19305de8 (pid 1933658 alive), token_estimate None, no hold; limits 40 cycles / 72 h only.
- 123 calls, 28,522,749 processed in 14.4 min (21:42:07-21:56:30). Main (Opus) 30 calls 5.22M, idle since
  21:44:31 waiting on ONE child: gsd-phase-researcher (Sonnet) 93 calls 23.30M, context 77k -> 372k.
- Product so far: commit 0372b5f5 (auto CONTEXT.md, discuss skipped) + untracked 01-RESEARCH.md. 0 obligations closed.
- GEX44 live daf90d00: `envelope` (token-estimate, model, autocompact, wu-packet, continue-max-tokens), `hold`/`release`.
  Breaker and hold PARK, never kill: a running turn keeps spending until `claude stop`.

## Autopsy (tool-shape classification; 123 calls)
| class | calls | processed | share |
|---|---|---|---|
| EVIDENCE_ACQUISITION (grep/sed/read, one per call) | 93 | 21.65M | 76% |
| STATE_READ (gsd-tools queries, git) | 15 | 2.82M | 10% |
| TEST_OR_BENCH_CONTROL | 5 | 1.67M | 6% |
| MUTATION (planning files) | 6 | 1.61M | 6% |
| CONTROL_LOOP + SPAWN + NARRATIVE | 4 | 0.77M | 3% |
Semantic decisions: <= 3 calls (CONTEXT write, researcher spawn, one narrative). Cost driver is context-residency
rent: the child re-sends a growing context (mean ~250k) for each single grep, so cost grows ~quadratically in calls.
Main floor 99k at call 0; main context grew 131k -> 224k by reading two GSD workflow documents into itself.
Grammar ahead for Phase 1: researcher (scan) -> planner (Orca: 121 calls/spawn) -> executor (scans again to write
the matrix). The same repository archaeology is paid three times.

## Challenger for the canary slice = EDD Phase 1 (reality scan + ownership matrix + spec)
- WU-1a ZERO MODEL: `tools/gsd_dossier.py` composes existing owners (import/caller graph of modules/gsd_x,
  `modules/liveness/reachability.py`, graphify query, D2A NON_DUPLICATION_LEDGER, dataset concept extraction) into
  a <= 40k-token dossier + raw refs on disk; salvages 01-RESEARCH.md as an input.
- WU-1b one fresh Sonnet worker via `envelope --wu-packet` (no parent transcript): writes OWNERSHIP_MATRIX.md and
  vault/specs/edd.md. Boundary budget <= 25 calls, ceiling 120k; reasons AMBIGUITY / NOVELTY (13Q on NEW rows) /
  PAGE. A context miss pages a file range; it never guesses.
- WU-1c ZERO MODEL proof: `tools/edd_canary_gate.py` (written first, seen red).
- Review only if NEW rows exist: one Sonnet reviewer on those rows, <= 8 calls.
- Hypothesis to falsify: Phase 1 at 3-8M vs champion grammar (researcher alone already 23.3M and still running).

## Envelope (this tranche only)
Canary attempt token_estimate 8M, trip ratio 1.5 (hold at 12M); tranche cap 25M including dossier build, review,
KV/UKDL/CBR and reserve. Over -> hold, never silent. Phases 2-7 are NOT funded until the canary reforecast exists.
Phase 2+ direction (unfunded): benchmark/holdout/mutation execution as deterministic runners (reuse
tools/mutation_drill.py); models only design fixtures and interpret contradicting results.

## Master Done-Gate
`python tools/edd_canary_gate.py` exits 0 only if: mission token_estimate is non-null and no unbounded worker runs;
every dataset concept has a matrix row with resolving file:line for producer and consumer; spec has `covers:`;
NEW rows carry the 13Q proof; the packet receipt (tokens, calls, reason codes) exists and metered canary spend
<= 12M; forecast-vs-actual and a Phase 2-7 reforecast from EDD evidence exist; KV/UKDL/CBR entries named in the
receipt exist; reachability exit 0 for new tools.

## Execution log
- 22:00:16Z stop: `gsd_mission hold` + `claude stop 19305de8` (pid gone in 1 s). Frozen spend of m-ee81e1595007:
  32,062,568 processed / 132 calls (main Opus 30 calls 5.22M; researcher Sonnet 102 calls 26.84M, ctx to 407k).
  9 researcher calls (+3.5M) landed between the plan (28.5M) and the stop.
- GEX44 `mission/edd-run` 89dac301: `tools/gsd_dossier.py` (81 concepts, 31 modules, 67 KB dossier in 6 s, zero
  model), `tools/edd_canary_gate.py` (red 1/13 before execution; G9 rewritten because reachability.py scans
  modules/ only and could never see tools/ -- a vacuous pass), WU-1 packet. dc20be77: partial RESEARCH.md salvaged.
- Canary record m-99b4cc7104f9: `arm --no-launch --supersedes m-ee81e1595007` (old -> HALTED), hold, envelope
  token_estimate 6M (trip 12M at default ratio 2.0, stall 3M), model sonnet, autocompact 120k, wu_packet WU-1
  (sha256 761051cb), max 3 cycles / 6 h, release. Launch is the agora sweep's.- Attempt 1 m-99b4cc7104f9 BLOCKED 22:13Z: autocompact 120k < measured floor 95.7k + dossier (3 compactions, 0.49M,
  compaction cost UNKNOWN). My error: window guessed, not derived from the floor (UC-18). Superseded.
- Attempt 2 m-51b4175db047 (autocompact 250k): matrix 81 rows + vault/specs/edd.md + receipt for 3,310,496 metered
  (work session 16 calls 2.60M; 2 continuation epochs 0.71M = 21.5% tax, UC-19). HALTED at max-cycles 3.
- Done-gate superseded note: the "reachability exit 0" clause above was replaced by G9 produced -> named -> read.
- RESULT 2026-10-06T22:5xZ: `python3 tools/edd_canary_gate.py` -> EDD_CANARY_GATE=13/13 at GEX44 mission/edd-run
  9640aecf; gate_ukdl_candidates PASS (19). Sampled quality 6/8 (C-15 wrong owner, C-54 wrong status), 28 rows
  UNKNOWN -> Phase 1 NOT done; repair packet WU-1R unfunded. Reforecast remaining EDD ~36M/~95M/~215M (canary/
  REFORECAST.md). Orchestrating Opus pane 08cb0d86 cost 17.41M / 56 calls since 21:52Z (UC-20): tranche ~21.2M
  measured of 25M cap; stopped there.