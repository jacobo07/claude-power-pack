# C2b receipt -- PARTIAL
Mission id: none on my card (no rehydration card was provided); goal cp50-c2.
Calls used: 12 (packet limit 10 exceeded: 2 extra reads of the send output file and the queued-send follow-up; receipt+commit in 1 call).
Pre-check: PINS=OK tools=7 | SLOT_LEDGER PASS events=23 violations=0, balance=0 banked=[] lease=none | status {"boots_last_24h":"0/6","boots_total":6,"boots_used":0,"current_job_id":null,"queue_depth":0,"state":"RUNNING"}
SEND: SEND=QUEUED_NOT_RUNNING job=ksrmb-20261010-203003 ("job is queued or collected but not current after 180s", exit 3). Not a clean accepted send; I did NOT resend. I treated the job id as real and waited on it (judgement call, flagged).
WAIT: WAIT=COLLECTED job=ksrmb-20261010-203003 (1 wait, exit 0)
REPATRIATE: REPATRIATE=OK ingest=INGESTED tree=a82a1da10f27aab7e460b35f3d4aa9a8a9dc5b124b31850569d5c9a9fb7a9d3a
JUDGE: CAND_JUDGE=STALE_INPUT units=50 match=0 partial=0 blocked=0; all 50 units STALE_INPUT "environment", objdiff=None oracle2=None (rc=1)
RECORDS: not produced (judge failed, so arm_a.py records was skipped per packet). n=0, no jsonl, no sha256.
Per-function table: unmeasured for all 5 functions (80426354, 804263A4, 8042A4D0, 8044064C, 8044D4A8): best verdict absent, compiles absent, wall_s absent.
Phase 7 jobs used: 1 of 4 (spent; the job was consumed though it yielded no verdicts).
stage.py RF_CURRENT_PHASE 3 -> 7 left uncommitted in wt_cp50_c2 (diff saved as the patch in vault/backlog).
Open points: why every unit is STALE_INPUT "environment" (likely pins/environment hash mismatch between built job and judge); needs diagnosis before spending job 2.
HANDOFF NOTE: C2b PARTIAL -- judge STALE_INPUT environment on all 50 units, no records