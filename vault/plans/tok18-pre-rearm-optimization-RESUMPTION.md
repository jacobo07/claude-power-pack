# RESUMPTION -- TOK-18 Gen2.1 Economic Kill-Shot (Owner decision 2026-10-05)

**Owner of the work:** Cognitive Economy generation 2 (`vault/programs/cognitive-economy/gen2/`, card `MISSION.md`,
state `ledger.json`). Add Gen2.1 there; build no new programme. The 124M U1-U11 plan is SUPERSEDED; keep it as provenance only.
Stage 0 is SEALED: `gen2/evidence/stage0/README.md` (numbers, hashes, scripts). Do not redo it.

## Owner decision (2026-10-05, binding)
- **Scope now (no live model experiments before 2026-10-11T18:00Z):**
  P0 park/renewal guard -> A0 zero-model floor attribution -> B deterministic call-elimination ceiling ->
  budget-unit reconciliation -> minimal economic readout. Then STOP and report.
- **No A1 probes now.** After the reset, run an ADAPTIVE A1 only if A0 leaves a decision-relevant ambiguity
  (repeated baseline for noise, minimal envelope, split only still-ambiguous blocks, stop when VoI ~ 0).
  Rules/instructions belong to gen2 W3/E1 (resident-rule ablation); skill/agent listings belong to the
  skill-capability gen2 owner: hand them evidence, do not re-experiment.
- **Budget, processed tokens, counted from the anchor below:** target 6-10M, warn 10M, HARD CAP 15M.
  Report both incremental spend and total campaign spend (Stage 0 = 19.2M sunk, incl. 7.84M owner-map agent).
- **Agents: default 0.** Spawn only for an independent uncertainty whose value clearly exceeds its cost.
- **Do not productise yet:** replay stays a reproducible analysis artifact (exact KSR control 273,912,110);
  the bottom-up budget rule is followed procedurally, not built. Only the rearm/park guard is built now (small, red/green test).
- **Canary naming:** InfinityOps / odr-device-trust Phase 4 (`C:\Users\User\Apps\io-device-trust`, branch
  feat/odr-device-trust, HEAD b01fb3ac, 52 dirty paths not ours). Not TUA-X. No mutation there in Gen2.1.
  Its future canary is compiled from paid semantic state (D-01..D-04, 04-RESEARCH, 04-UI-SPEC) into Work Packets,
  not planner->researcher->plans. Canary stop rule is progress-adjusted, ceiling well below the old ~70M.
- **Priority order:** P0 park guard; P1 hard/soft floor residual (A0); P2 meta-work calls that can disappear
  (planner/researcher/verifier); P3 compile Phase 4 into Work Packets OFFLINE (zero-model where possible);
  P4 compare marginal ROI of floor reduction vs meta-work elimination; P5 build only winners (later, own authorization).
- **New metrics:** Resident Prefix Tax and Meta-Work Tax (planning/research/review/verify/status/handoff share of processed).
- Never rearm KME/KSR; never unblock m-a128e03c7419, m-608c8d8d761f; never re-enable PP-ReconFactory-Rearm-20261011.

## Spend anchor
Pane 87601e81 = 19,196,694 processed at 2026-10-05T11:13:02Z (script `gen2/evidence/stage0/self_spend.py`).
A successor pane counts its own session from zero; Gen2.1 spend = successor total (+ this pane after the anchor).

## Facts to verify, not trust
- Mission m-608c8d8d761f (InfinityOps) BLOCKED, worker dfc0acda pid 24976 not running, heartbeat 2026-10-04T23:46Z.
- "A BLOCKED mission can renew itself into the old architecture" comes from an Owner-relayed scan: reproduce the path
  in `modules/gsd_x` / `tools/gsd_mission*` before writing the guard.
- Floor split 35K tools / 45K instructions / 13K agents / 12K skills / 9K hooks and role split planner 14.6M /
  researcher 8.9M / verifier 7.4M / executor 1.6M are UNVERIFIED (not on disk). A0 measures them from transcripts.
- gen2 `ledger.json` `budget_tokens` has no unit field; prose labels it processed; derivation of 40/78/150M not on disk.

## Done since the anchor (pane tua-x-96, session 242ae047 -- verify, do not redo)
- **P0 DONE, c25622e8.** Path reproduced: `plan_next` halts a BLOCKED mission on budget and `renewal_refusal` renews a
  budget halt (m-4df3ebcb89ff -> m-608c8d8d761f was exactly that). Guard = `gsd_mission.py hold|release` (owner_hold;
  plan_next none, renewal refused), spec `vault/specs/mission-owner-hold.md`, `tools/test_gsd_mission_owner_hold.py`
  12/12 + 2-mutant drill, test_gsd_mission 220/220. APPLIED to m-608c8d8d761f; on the live record at budget time
  (created+24h+60s): plan none, renewal refused; unheld control: halt, renews. Release is Owner-only.
- **A0 InfinityOps DONE, 85adcbcf** (`gen2/evidence/stage0/infinityops/`): the floor split and role split in "Facts to
  verify" are now MEASURED (main floor 129k, soft ~80k; planner 14.6M/run, researcher 8.9M, verifier 7.4M, executor
  1.6M total). Corrections: prompt_snapshot is a host record, not context; hook success text IS context (~7-13%).
  This pane's spend was not separately metered (long interactive session; count it as UNKNOWN, not zero).

## Next 3 actions
1. A0 for KSR + KME: the same zero-model floor/role split (reuse `infinityops/io_*.py`, which take a worker list).
2. B pass 1: exact-match mechanical calls; extend to pass 2 only if pass 1 lands near the 10% threshold.
3. Units fix (ledger budget_tokens unit field) + minimal economic readout with Resident Prefix Tax and Meta-Work Tax; STOP and report.
