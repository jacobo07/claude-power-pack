# D28 Tennis Frontier Collapse -- common brief for every D-unit worker (2026-10-13)

Binding plan: PP `vault/plans/tennis-frontier-collapse-2026-10-12.md` (Owner "y and rearm the mission until you finish
all of this", 2026-10-13). Read sections 1, 3, 4 once; your packet names your phase. `PROGRAMME.md` still governs the
session loop (steps 1-5), paths, hard constraints and economic rules; where it names the old plan or "hard stop 55M",
this brief wins: goal `tennis-rf`, programme 90,000,000 (Owner capital 9ff2a9f9), automatic successor leases (8M
tranche, 1.5M kept; D28 Ph1b 3c98097b). Running out of programme is the Owner's boundary: never ask for capital,
never open a lease by hand, never change a cap.

Sealed before you: Ph0 (wt_tennis_rf six commits, tip 88d36ff), Ph1a 729f7387 (receipt status derives from the
ledger: `tools/receipt_judge.py`, `tools/claim_evidence.py`), Ph1b 3c98097b.

## Planes
- Laptop: light only (about 1.6 GB free). No heavy python here; nothing that loads the 1,797-function corpus.
- GEX44: all corpus work. M = `/home/kobii/missions/tennis-w11` (layout: `WU-P1P2-gex.md` "Layout"). P1P2 outputs:
  `M/out/p1p2/` (facts.jsonl, factor.json, blockers.json, hypotheses.json, knowledge_shock.json, receipt.md).
  W12 evidence: PP `vault/programs/tennis-rf/evidence/w12/`. Python `/opt/ksr-decomp/venv/bin/python`,
  `export KSR_DECOMP_TOOLS=/opt/ksr-decomp`, 20 cores. Your outputs: `M/out/d28/<phase>/` and code in
  `M/out/d28/tools/`. Copy every result you cite back into PP `vault/programs/tennis-rf/evidence/d28/<phase>/`
  (scp from the laptop) and commit it there, pathspec.
- Remote calls: write a no-BOM LF script to the scratchpad, run `cmd /c "ssh -o BatchMode=yes gex44 bash -s < <file>"`.
  Anything longer than ~2 min: `nohup ... </dev/null > log 2>&1 & disown` and poll the log in later calls (one
  bounded check per call, never a sleep loop). Never launch `claude` on GEX44 unless your packet says so.
- Stop-loss: GEX44 available < 16 GB or laptop free < 1 GB -> pause new work, receipt what is done. Kill nothing.

## Rules
- Deterministic first: a number comes from a script you ran (command in the receipt). A model judgement on a
  function needs a Proof of Model Necessity line. Abstain (`UNKNOWN` / `INCONCLUSIVE`) over guessing.
- Every grouping/index carries a red control (permutation must collapse it) or is INCONCLUSIVE.
- Never edit `M/out/p1p2/` or W7/W12 originals: copy, then change the copy.
- GEX44 compute jobs: JOBS.md. Approved 4, used 3. Only D6 may use job 4. Jobs 5-6 are NOT approved: a unit that
  needs them writes `Status: BLOCKED_HUMAN` naming the exact approval.
- Write outputs as they exist; stop new work at 85 % of your calls and split per PROGRAMME.md step 4.
- Receipt also gets a `## Plan delta` line: which plan MDG numbers this unit settled and their values.
