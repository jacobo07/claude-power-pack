# Generation S12 — Proven-Route Fan-out + Positive-Control Unlock (PROPOSAL, awaiting Owner "y")

Prepared 2026-11-04 by the coordinator (session 95e69b3d) after S11H closed. Nothing has been written to gen3 or t1,
and no money has been spent. The mission has been redirected to the S12 prompt, but it is still held: retarget
does not launch it.

## Where S11H left the programme (measured on GEX44, 2026-11-04)
- Frontier: **1100/1797 unique** = CERTIFIED_C 1086 + CERTIFIED_CXX 14, overlap 0 (t1 `2091cdad`,
  `evidence/frontier/counters.json`, FRONTIER_CHECK OK). S11H R4 certified 5 more under cert-cxx@2. The H2 guard
  checked that none of the 5 is in H2 (0/5) without anyone reading the manifest (fix `ae3da98d`).
- Proven object-model route: in the 6 known CXX functions, the vptr-offset registry and the this-call receiver were
  necessary 6/6, and both are graded PROVEN_IN_SCOPE. Callee-prototype propagation was necessary 4/6 (SUPPORTED).
  Slot signature was necessary 0/6 (do not build on it). Source: `s11h/h3_genome.json`, `h2x*.json`.
- Strategy rules exist that send each kind of residual to the right route: SR-REG-VCALL vs SR-REG-ONLY, and
  SR-FUNCPTR (`s11h/s_strategy.json`).
- Census: 2342 functions carry 10149 virtual-call sites (`s11/om_census.json`). The r12 class has 139 members. Only
  14 functions are certified CXX.
- Open debts:
  - R3 never ran on the 4 NOT_A_THIS_CALL refusals.
  - OM-PR1 is still 2/3: fn_80222480 stops at 98.90 because of mwcc register colouring. Its residual is unique,
    and it is FAN_OUT_REAL (9/31 near-misses are REG_ONLY).
  - H2 is sealed, unread and unspent (manifest `922f214e`).
- The method cannot be frozen and H2 cannot be spent while OM-PR1 is 2/3. Owner D1 still applies: no waiver and no
  control swap.

## Goal
1. Turn the proven route into frontier: fan it out over the uncertified dev pool.
2. Try once, on a bounded budget, to close the positive control. That is the only thing standing between the
   programme and its first legitimate held-out evidence.

## Units (one micro-commit each, evidence under `t1 evidence/ascension/s12/`)
- **S12-0 Reality.**
  - Recompute the frontier: expect 1100.
  - Check the open leases and the model spend actually settled since S10 (remaining ~$140, minus whatever S11
    settled).
  - Build the dev pool = the uncertified functions whose virtual-call sites match the registry/this-call motif,
    minus the certified ones, minus old H. H2 is excluded **by the guard only**: a membership check by hash, never
    by reading, listing or aggregating the manifest.
  - Output `s12/reality.json` and `s12/dev_pool.json`, with the count measured, not estimated.
- **F1 Fan-out.**
  - Apply the S11H route, selected per function by `search_plan`'s strategy rules, in batches of 25 over the dev
    pool.
  - Certify through `cert_cxx.certify` with the H2 guard ON.
  - Negative Search Memory is consulted before every search, and each new negative is written back.
  - **K1:** the first 2 batches certify 0 → stop F1 and record the residual class.
- **R3.** Probe the 4 NOT_A_THIS_CALL refusals under SR-FUNCPTR. Each ends as CERTIFIED, a new strategy rule, or a
  typed negative.
- **RC Register colouring (bounded).**
  - Build a deterministic model of mwcc allocation order from the 9 REG_ONLY near-misses, plus the R1 natural
    experiments in the certified corpus (DECL_ADD/DECL_DROP were the only classes that closed anything).
  - Move fn_80222480 from 98.90 to exact under the unchanged truth contract.
  - Cap 8M tokens.
  - **K2:** no movement above 98.90 after the model's top 3 predictions → one donor-route attempt: a certified
    function with the same live-range shape gives the declaration order. If that fails too → park, with a receipt.
- **FREEZE + H2, only if OM-PR1 reaches 3/3.**
  - The worker freezes the method (hash pinned), checks the positive control 3/3 against the frozen hash, and
    checkpoints "ready for sealed H2".
  - **The coordinator, not the worker**, runs the `heldout_release.py` preflight and then the sealed run, once.
  - If OM-PR1 stays at 2/3, H2 stays sealed and unspent. That is a valid outcome, not a failure.
- **Close.** Write `s12/closeout.md` (frontier delta, K1/K2 outcomes, meta-analysis), then CHECKPOINT_COMPLETE with
  `--residual`.

## Stop rule
| F1 new certificates | fn_80222480 | Result |
|---|---|---|
| < 3 | not closed | METHOD_PIVOT_REQUIRED, and the coordinator recommends **closing the programme** at the measured frontier |
| ≥ 3 | not closed | S12 counts as frontier-positive; H2 stays sealed; the next generation is the Owner's choice |
| any | exact | the freeze and the sealed H2 run become possible |

## Budget
- **Tokens:**
  - Mission m-fc7047a29f01 is retargeted: same gen3 cwd, workstream and authority lineage.
  - Authority: the remaining 19.8M is topped up to **50M**, with 1 × 15M contingency top-up. Estimate low 25M /
    central 40M / high 60M.
  - Split: F1 25M, RC 8M (moratorium), R3 3M, rest + close 4M.
- **Model USD:** $0 central. Ceiling **$15**, through the A4 spend lease, only in a unit whose receipt explains why
  deterministic search failed. The H2 sealed run is deterministic: $0.
- **Limits:** 16 cycles, 36 h. No push. Truth contract unchanged. The OM-PR1 control set stays frozen.

## Never
- Never read, list, run or aggregate H2 outside the coordinator's sealed release.
- Never waive or swap a positive control.
- Never count a function twice (the C and CXX columns stay separate).
- Never edit the Power Pack from the worker.

## Mechanics (coordinator)
- Done (prepare): S12 prompt written to `/tmp/s12_command.txt` on GEX44; `retarget` applied to m-fc7047a29f01.
- On "y":
  1. Write the "Generation S12" section into gen3 `ASCENSION-PLAN.md`.
  2. `mission_topup.py budget` to 50M.
  3. Run `checkpoint --clear` on m-fc7047a29f01. The sweep then launches it.
- m-a9d8915ae366 (recon general) is done (PR #13 merged, `abc63bb9`). Close it as COMPLETE, so it is not
  relaunched.
