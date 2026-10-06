# TOK-18 gen2 tranche learnings (WU4, receipts only; no transcripts read)
Sources: WU1-receipt.md, WU2-receipt.md, orchestrator-verified facts. Fix commit for WU1 red test: b67f5d8f.

## Incidents
1. Planning overrun. Symptom: planning pane c77978f6 spent 5,856,325 processed / 33 calls, ~98% of the 6M tranche (4th overrun). Cause: one pane re-sends ~170-190k context per call; its 0.9M estimate for 13 decision calls was really 2.51M. Evidence: orchestrator measurement. Fix: derive call allowance from budget / measured prefix (rule below).
2. Contradictory packet limits. Symptom: WU1 spent ~1.5M against a 0.6M cap. Cause: packet gave 0.6M AND 25 calls; at 97-125k per call 0.6M is ~5 calls. Evidence: WU1 receipt Spend. Fix: packet states allowance = budget / measured per-call prefix, never an independent call count.
3. Floor rent moved, not removed. Symptom: fresh workers start at 96,716 (WU1) and 95,548 (WU2) tokens. Cause: host+CPP prefix (~96k) is paid by every fresh worker; isolation removed transcript rent only. Evidence: both receipts. Fix: size packets for ~5 calls per 0.6M or shrink the floor (separate unit).
4. Red test committed. Symptom: test_floor_regression_gate 60/61, V-FLOOR-JSON key set differs. Cause: new JSON key cwd_admitted added without updating the contract test. Evidence: WU1 receipt Tests. Fix: b67f5d8f (61/61).
5. Non-discriminating drill. Symptom: WU1 red-pole mutant also exit 1. Cause: unmutated check was already exit 1 (organic MATERIAL_RISE), so the control sat on the red pole. Evidence: WU1 receipt. Fix: discriminate via V-FLOOR-ADMIT-CWD (exit 2 without flag, 0 with).
6. Non-comparable floor row. Symptom: floor +37,683 chars (188147 -> 225830) vs reference. Cause: biggest row memory_project +34,478 compares two different projects (reference recorded at probe cwd) after --admit-cwd. Evidence: WU1 receipt. Fix: per-cwd reference or explanation (Owner).
7. Same-file parallel Edits. 6 parallel Edits on one file, 5 blocked by anti-thrash, 5 calls burned. Fix: one scripted multi-edit.
8. BOM in commit subject. PS 5.1 Set-Content -Encoding utf8 for -F file gave U+FEFF subject. Fix: WriteAllText no-BOM, amend (e95407e6).

## Production reality (WU2)
PP-Vault-Summarize (wscript hidden_launch -> vault_summarize.py --check, 02:00 daily) carries wake_check. Last result 1 at 2026-10-06 02:00 predates the change: UNVERIFIED until 2026-10-07 02:00. Nothing consumes WAKE_FLAG.json. Gate exits 1 organically, so the task would wake nightly until re-baselined.

## Canary result
| worker | initial context | calls | processed | page faults | quality defects |
|---|---|---|---|---|---|
| WU1 floor gate | 96,716 | 24 | 1,498,007 (cap 0.6M, ~2.5x) | 0 | red test (V-FLOOR-JSON), non-discriminating drill, wiring not done |
| WU2 wake check | 95,548 | 5 | not recorded in receipt | few partial (vault_summarize, grep of 2 files) | none; gate 60/61 not re-run; prod UNVERIFIED |
| WU4 learnings | 96,459 | 3 | ~0.3M est (3 x ~100k) | 0 | none known |
| planning pane | n/a | 33 | 5,856,325 | n/a | estimate 2.8x low |

## Rules derived
- Call allowance = budget / measured per-call prefix, stated in the packet.
- A JSON contract key change ships with its contract test in the same commit.
- A mutation drill needs its control on the opposite pole to the mutant.
- Compare floors like-for-like (same project/cwd) or label the row non-comparable.

## Conversation-dependency debt
WU1 packet lacked test helper names, vault_summarize.py location, realistic call budget. WU2 packet lacked live task registration location, PP_WAKE_* override names, flag consumer contract. WU2 processed total absent from receipt.