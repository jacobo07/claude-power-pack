# WU-S5d receipt
Status: DONE (code by worker m-3bf354f42adc, HALTED at 695K vs stop 620K; proof + commit by coordinator)

- D1: steward R1 now selects terminal missions (COMPLETED/HALTED/BLOCKED) with a wu_packet, and resolves the goal by
  its cwd binding when the record has none. V-STEWARD-SETTLES-COMPLETED (850000 -> 0) and V-STEWARD-SETTLE-ONCE pass.
- D2: a PARTIAL / IN PROGRESS / stub status in a receipt's title line now reads as no receipt.
  V-LIFE-RECEIPT-STATUS-IN-TITLE passes, with its DONE-in-title control.
- Suites (coordinator re-run, scratchpad s5d/):
  - STEWARD 20/20, HALT 21/0, ADM 43/43, ADVANCE 4/0;
  - MC 224/225: the FAIL is pre-existing.
- Mutants: NOT proven this unit (the worker stopped at the breaker before the drill). Open debt.
- Not renewed: the authority left (~614K) was below its 620K token estimate. That is the correct refusal, not a fault.
