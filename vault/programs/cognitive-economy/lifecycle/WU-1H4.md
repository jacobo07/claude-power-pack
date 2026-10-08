# WU-1H4 -- commit and receipt for WU-1H (fourth epoch of L1; NO code work left)

Plan: as WU-1H.md (Amendment D L1). Goal ce-lifecycle-v2. cwd = this worktree.
Verified by the coordinator at arm (2026-10-08 ~22:15): tools/test_halt_continues.py = HALT_CONTINUES_PASS=10 FAIL=0
(_logs/wu1h3/t3.log); the three mutants are KILLED (_logs/wu1h3/mut1..3.log: V-LIFE-HALT-RECEIPT-PRESENT,
V-LIFE-HALT-ONCE, V-LIFE-SUCCESS-NO-RECEIPT). Do NOT read source files, do NOT rerun the mutants.

Budget (WU-1H3: 10 calls ~645K): hard cap 7 model calls. One command per call.

Steps:
1. Four suites in ONE PowerShell call, each to _logs/wu1h4/<name>.log, then print only each summary line:
   tools/test_halt_continues.py, tools/test_gsd_mission.py, tools/test_process_lifecycle.py,
   tools/test_gsd_mission_admission.py. A failure that also fails on HEAD (git stash is forbidden: compare against the
   WU-1B receipt's numbers, MC 224/225 pre-existing) is pre-existing; a new one stops here with the receipt.
2. Commit by pathspec with -F msgfile (a NEW msg file): tools/gsd_mission.py, tools/test_halt_continues.py,
   vault/plans/ce-lifecycle-WU-1H2-progress-2026-10-08.md, vault/plans/ce-lifecycle-WU-1H3-progress-2026-10-08.md,
   vault/programs/cognitive-economy/lifecycle/WU-1H3.md, route-WU-1H3.json, WU-1H4.md, route-WU-1H4.json.
   Verify `git log -1 --format=%s`.
3. Replace WU-1H-receipt.md (<= 40 lines): gates 10/10, mutants 3/3 killed, suites, commit hash, epochs
   (1H 926K, 1H2 755K, 1H3 645K, 1H4), sha256 of tools/gsd_mission.py for WU-INST (no deploy, HR-001),
   addendum B "second format, mission-level". Commit it.
4. `mission_spend.py goal-status --goal ce-lifecycle-v2`; if remaining - open >= 1,100,000 run
   `python tools/gsd_mission.py arm-chain` FROM THIS WORKTREE with --parallel-unit lc-WU-ADV,
   --wu-packet <abs WU-ADV.md>, --token-estimate 800000, --route <abs route-WU-ADV.json>; else write
   WAITING_FOR_AUTHORITY in the receipt.

NEVER write "needs a fresh pane" or "/kclear". End your final message with: HANDOFF NOTE: WU-1H done
