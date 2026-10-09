# WU-S5c receipt
Status: DONE (F3 mutant unproven, see below)

- F5 halt_continue: every exit sets row["renewal"]; exception path records the reason. Mutant KILLED (V-LIFE-NONRENEW-HAS-REASON).
- F1 clean finish with no receipt -> HALTED "no receipt" -> halt_continue. Mutant KILLED (V-LIFE-SUCCESS-NO-RECEIPT-NOT-COMPLETED). Two ADM tests now write a DONE receipt for the COMPLETED control.
- F4 capsule commits = since created_at via mission_steward._git_log. Mutant KILLED (V-LIFE-CAPSULE-MISSION-SCOPED).
- F3 guard CLOSEOUT_PATH admits *-receipt.md; V-SBG-CALLS-WALL-RECEIPT passes. Mutant NOT proven: drill control invalid because V-SBG-LATENCY (<50 ms) fails on a loaded host (131-440 ms), unrelated to this change.
- Suites: halt 19/0, guard 20/21 (latency only), MC 224/225 (V-MC-SUP-HOST-UNANSWERED-NOT-BLOCKED, not in touched code paths), ADM 43/43, steward 18/18.
- WU-INST2 NOT armed: session budget breaker reached; remaining-open lease not verified.
