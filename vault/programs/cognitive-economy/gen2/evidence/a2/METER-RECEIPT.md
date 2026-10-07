# METER-RECEIPT -- infallible program meter (packet METER-PACKET.md, 2026-10-07)

## Confirmed facts (appended as they were confirmed)
- M1/M2/M4 implemented in `measure/attribute.py`: `find_session_files` (every dir under projects root + subagents), session
  totals separate from attribution (`session_totals`, `total_processed`, `unattributed_*`), torn-line counts, `--until`.
- M1/M4 implemented in `gen2/evidence/stage0/self_spend.py` (kept exec-compatible with `tools/tranche_driver.spend`:
  first `sid="..."` and first `^d=` line unchanged in shape). Missing transcript prints `UNKNOWN`, exit 2 as a script.
  Also fixed: a record with neither message.id nor requestId used to collapse into ONE key (`None`); now each counts.
- M3: `attribute.py --session SID` runs this counter AND self_spend.py as a separate process; AGREE only on equal
  calls+processed; DISAGREE/UNKNOWN carry no number; torn lines -> INCOMPLETE (lower bound). Exit 0/1/2/3.
- M5: `--host SID=HOST`; no local transcript -> UNKNOWN naming the host; a local transcript wins.
- M6 already enforced by `cep_gen2._receipt_extras` (boundary_calls < metered_calls fails); now also pinned against a
  meter-derived count (16) in the new gate.
- `python tools/test_ce_meter_truth.py` -> CE_METER_PASS=30/30; `python tools/test_ce_attribute.py` -> CE_ATTRIBUTE_PASS=15/15.
- Golden (cut-off 2026-10-07T18:00Z, both counters AGREE, 0 torn lines): 489481fa-3018-4082-98a4-95ce316cd24d = 10,695,300 / 61;
  886d7bb9-086d-4c66-a2db-a4043e2221de = 18,733,339 / 77 (>= 16,916,777 / 71 pinned by the packet; the session kept
  spending between the packet's reading and the 18:00Z cut-off).
