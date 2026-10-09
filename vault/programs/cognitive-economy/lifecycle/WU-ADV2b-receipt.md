# WU-ADV2b receipt
Status: DONE
- tools/gsd_mission.py: parse_plan, receipt_complete, goal_headroom, apply_approval, advance_unit, advance_pass; supervise wrapped, CPP_SWEEP_ADVANCE=off disables (default on).
- tools/test_advance.py: 11 PASS / 0 FAIL, incl. V-LIFE-ADV-ARMS-NEXT, -ONCE, -NOT-LISTED, -NO-AUTHORITY, -STUB-RECEIPT-NO-ARM.
- Predecessor hit breaker before commit; salvaged and committed by successor. Mutant drills not re-run by successor.
- WU-INST3: no packet in lifecycle dir -> WAITING_FOR_PACKET (not armed).
