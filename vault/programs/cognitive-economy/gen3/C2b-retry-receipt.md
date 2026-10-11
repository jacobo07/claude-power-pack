# C2b-retry receipt (2026-10-11)
Mission id: not shown on any card in my context (goal cp50-c2). Calls used: 5 of 7 (the receipt call is the 5th).
Pre-check (verbatim): `PINS=OK tools=7 ...pins.json` | `SLOT_LEDGER PASS events=23 violations=0; balance=0 banked=[]; lease=none` | status `{"boots_last_24h":"0/6","boots_total":6,"boots_used":0,"current_job_id":null,"queue_depth":0,"state":"RUNNING"}`
SEND: `SEND=RUNNING job=ksrmb-20261011-094630` (exactly one send)
WAIT: `WAIT=COLLECTED job=ksrmb-20261011-094630`
REPATRIATE: `REPATRIATE=INVALID_CUSTODY ingest=None tree=49c9d46671ada1e8f637a3ae59ae924f785613f81a4c0612640254c438beac34`
  reason: run/MANIFEST.json missing
  reason: run/receipt.json missing; cannot check the expected identity
Judge: not run (the plan gates it on REPATRIATE=OK).
Records: not produced (n=0, no jsonl, no sha256). Ledger rows for this job: none printed.
Per-function table: absent; nothing measured. Compile failures by arm (m2c vs m2cvs): unmeasured.
Phase 7 jobs used: 2 of 4. This job is spent and the plan forbids a resend.
PP commit: see git log line in the final message.
Open points: the job is COLLECTED on GEX44 but the repatriated tree has no run/MANIFEST.json and no run/receipt.json. This resembles the known "runs do not come home" gap. The coordinator decides whether the job's own output can be recovered through the dispatcher's collect path (RULE-090 forbids ssh/scp). I did not investigate.
HANDOFF NOTE: C2b-retry PARTIAL -- REPATRIATE=INVALID_CUSTODY (run/MANIFEST.json and run/receipt.json missing) for job ksrmb-20261011-094630; no records