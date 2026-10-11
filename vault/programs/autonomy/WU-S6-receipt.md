# S6 receipt
Status: DONE

Commit: see `git log -1 -- tools/test_unit_proof_reuse.py` (S6: proof reuse / NO_WORK / tier / unit receipt).

- PROVEN: admit_route derives the default proof `unit:<packet stem>` over the packet when the route has none, and records `tier` (A4 tier_for) on the admission. A re-admit of an unchanged PROVEN unit returns NO_WORK (not launchable); arm_chain completes it with no worker (test G4, G7).
- PROVEN: supervise, at the done-check DONE, calls `emit_unit_receipt`: appends the A5 receipt to `vault/config/unit-receipts.jsonl` and records the claim PROVEN. Unmeasurable spend is skipped, never zero (G2, G3).
- PROVEN: `work_proof.populate_from_receipts` fills the ledger only from `Status: DONE` receipts with a packet beside them; idempotent (G6).
- PROVEN: a fresh-project canary (route with no proof/work_class, no prompt mention) inherits all of it (G1-G5, tools/test_unit_proof_reuse.py, 12/12).
- PROVEN: mutation drill (default proof disabled) turns G4, G4b, G7 red (9 pass / 3 fail).
- PROVEN: test_work_proof 13/13, admission 43/43, chain 11/11, envelope 67/67.
- NOT_PROVEN: test_halt_continues and test_advance were still running when this was written; not observed.
- NOT_PROVEN: the ledger is not yet populated for historic units (run `populate_from_receipts` on vault/programs/autonomy once); A4 tier is recorded but does not yet change the launched profile (SLIM needs slim-critical-settings.json).

Next unit must know: ledger and receipts paths honour CPP_CLAIM_LEDGER / CPP_UNIT_RECEIPTS. A unit whose packet is byte-identical to one already DONE is now NO_WORK; edit the packet to force a re-run.
