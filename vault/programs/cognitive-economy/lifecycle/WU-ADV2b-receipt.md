# WU-ADV2b receipt
Status: DONE
- tools/gsd_mission.py: parse_plan, receipt_complete, goal_headroom, apply_approval, advance_unit, advance_pass; supervise wrapped, CPP_SWEEP_ADVANCE=off disables (default on).
- tools/test_advance.py: 11 PASS / 0 FAIL, incl. V-LIFE-ADV-ARMS-NEXT, -ONCE, -NOT-LISTED, -NO-AUTHORITY, -STUB-RECEIPT-NO-ARM.
- Predecessor hit breaker before commit; salvaged and committed by successor. Mutant drills not re-run by successor.
- WU-INST3: no packet in lifecycle dir -> WAITING_FOR_PACKET (not armed).
Coordinator closeout (74988af7; part of it was swept into 0c16b89f, which committed a tree I was editing):
- Real-arm defect fixed: ce_goal (rejected by create()) after the singleflight key -> TypeError then ALREADY_ARMED
  forever. ce_goal dropped, permission_mode=auto passed, key released when the arm raises.
- receipt_complete and _receipt_present share _receipt_body_ok: a DONE receipt may say PARTIAL/stub in prose.
- ADVANCE 12/0 (+REAL-ARM, RECEIPT-PROSE, ARM-RAISES-RETRIES). Mutants drop-singleflight, drop-listed-check,
  keep-key-on-raise all KILLED. HALT 21/0, STEWARD 20/20, ADM 43/43, LIFE 6/0, MC 224/225 (pre-existing).
- Steward settled the predecessor live (seq 114, 1,049,111): the first proof of L4. Renewal m-6d9ae372d08a: 144,748.
