# WU-1H2 -- apply the WU-1H design (second epoch of L1; the first spent its envelope reading)

Plan: as WU-1H.md (Amendment D L1, Owner "y", pp-ce-a3 3aa002af). Goal ce-lifecycle-v2. cwd = this worktree.
Start from vault/plans/ce-lifecycle-WU-1H-progress-2026-10-08.md: it holds the verified line numbers, the design
(steps 1-6) and the test/mutant plan. Do NOT re-survey tools/gsd_mission.py: read only the exact line ranges the note
cites (~559, ~861, ~1582, ~2161, ~2780-2796) and tools/test_gsd_mission_admission.py 252-324 for the fixture pattern.
Scope = WU-1H.md steps 1-9 + addendum A and C. Addendum B is settled: record "second format, mission-level" in the receipt.

Budget (measured: WU-1H epoch 1 = 31 turns, 692K, 0 code): hard cap 18 model calls. Write each helper in ONE Edit,
the test file in ONE Write, run all four suites in ONE PowerShell call that logs to _logs/wu1h2/. Past ~50K context:
commit what is green, update WU-1H-receipt.md, end with HANDOFF NOTE.

Steps:
1. Apply design steps 1-3 of the progress note (helpers, call sites incl. the "slim worker failed" legacy branch,
   launch_prompt capsule prefix). Kill switch CPP_HALT_CONTINUE=off.
2. tools/test_halt_continues.py: V-LIFE-HALT-CONTINUES, -ONCE, -NO-AUTHORITY, -KILL, -DEAD-NO-RESULT,
   -SUCCESS-NO-RECEIPT; mutants via tools/mutation_drill.py (drop receipt check; drop singleflight; provider success
   counts as receipt) must each go red.
3. Atomic arm (addendum C): `gsd_mission.py arm-chain` = arm --no-launch + envelope + admit; hold with the reason on
   any failure; never launches without a packet. One gate V-LIFE-ARMCHAIN-ATOMIC + admitted control.
4. Four suites. Commit by pathspec (-F msgfile; verify git log -1). Commit the progress note too.
5. Replace the stub WU-1H-receipt.md (<= 40 lines): gates, mutants, commits, calls, deploy recipe as hashes for
   WU-INST (no deploy). Commit.
6. Arm WU-ADV with arm-chain (or the 3-step recipe) if remaining - open >= 1,100,000 per `mission_spend.py
   goal-status --goal ce-lifecycle-v2`: --parallel-unit lc-WU-ADV, --wu-packet <abs WU-ADV.md>, --token-estimate
   800000, --route <abs route-WU-ADV.json>. Else WAITING_FOR_AUTHORITY in the receipt.
   NEVER write "needs a fresh pane" or "/kclear": if you cannot finish, commit, update the receipt and end with
   HANDOFF NOTE -- the coordinator or the sweep continues from the receipt.

End your final message with: HANDOFF NOTE: WU-1H done
