# E1 closeout (post-E1 Phase 1)

Driver `e1_closeout.py`, one call, 0 model calls. Receipt contract: `tools/cep_gen2.py` check_receipt (B1, 42a984fb).

| step | commit | result |
|---|---|---|
| D1 | a051c761 | gen1 state.B savings: 8,477/call, upper_bound |
| D2 | e7fbf548 | 12.5k (= 12,515) and 10.8k superseded |
| D3 | b95fe289 | calibration -32.3% vs forecast; net byte est 9,422 |
| D4 | 9375fbad | pointer tax 9,232 B, ESTIMATED 3,093-4,038 tok/call |
| D5 | cf290946 | cleanup-survival test 4/4 (red pole real) |
| D6 | 861e2799 | payback PAID_BACK: 8,784 of 1,083 calls (laptop main, lower bound) |
| D7 | 1b93539b | receipt; gen2 W3 closed |

Correction: 17b3188a's "41,353 B" is wrong; the moved originals are 37,353 B (backup dir), so the plan's 10.8k / 22% were derived from a typo.
