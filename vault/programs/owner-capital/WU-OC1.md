# WU-OC1 -- econ-succession S1-S5 (goal econ-succession, existing 20M programme). Owner-approved; no Owner questions.
Master plan: vault/plans/owner-capital-ctx-rent-2026-10-11.md (section 3 order, section 6 stop-losses). Owner typed
`approve p80` 2026-10-11T12:01:24Z (uuid e2a5f2c6-abcf-423f-86a5-faff86bd957b, packet sha 9e7616c2...): capsules APPLIED,
ctx-rent-a2 programme 30M, econ-succession-a1 programme 10M. Do not touch those two goals in this WU.
0. Bind: write ~/.claude/state/goal-binding/<your sid>.json = {"goal":"econ-succession","since_ts":"<first transcript ts UTC>","source":"explicit","pid":0}.
   Read vault/programs/econ-succession/RESUMPTION_FILE.md, then plan vault/plans/econ-succession-2026-10-11.md sections 4-7 only.
   W0 already passed at 13:45 (capital_authority.py, econ_admission.js, owner_capital_capture.js clean; no live binding on the goal); re-check git status of those 3 files only.
1. S1 provenance spike (bounded 6 calls): which transcript/hook fields separate interactive Owner input from -p / --bg / worker prompts. Record the verdict in the plan.
2. S3 then S2, red tests first in tools/test_econ_succession.py (V-SUCC-*): durable receipts + approval-time expiry/drift + INVALIDATED row for fd25efd1; approve verb + receipt in econ_admission.js, owner_capital_capture.js merged into it (registered hook stays econ_admission).
3. S4 succession.py both transactions + crash replay (programme -> successor lease via ledger lease_open; L1 immutable). S5 dead-holder reservation reconciler (ctx-rent-a2 has 3 holds totalling 2,762,810 in sessions 262be369 / 47f3da08 / b8ff709c: reconcile them by evidence, never by guess).
4. Each step: tests green, pathspec commit on feature/knowledge-acquisition (no push; ~56 foreign dirty files exist -- never stage them), update the econ-succession RESUMPTION_FILE.
Stop-loss: a step over 3x its plan P50 row; an anti-self-escalation test that cannot be made red; a live writer on an owner file. Then write the receipt with Status: BLOCKED and the reason.
Common: no Monitor, no waiting call, no GSD commands, at most 1 subagent (pp-code-reviewer before commits touching 3+ files). Never edit tools/gsd_mission.py or settings.json. Model capital mutation stays denied: never call capital-apply or goal-declare yourself.
Done-check: test_econ_succession.py and test_capital_authority.py exit 0; S1-S5 commits listed.
Then arm the next unit in ONE PowerShell call: gsd_mission.py arm-chain --cwd <repo root> --command "/gsd-autonomous" --wu-packet vault/programs/owner-capital/WU-OC2.md --token-estimate 9M --route vault/programs/owner-capital/route-OC2.json --permission-mode auto --rollover-protocol capsule-v2
Receipt path: vault/programs/owner-capital/WU-OC1-receipt.md (line 1 '# WU-OC1 receipt', line 2 'Status: DONE' or BLOCKED; K7 row estimate vs actual processed tokens).
