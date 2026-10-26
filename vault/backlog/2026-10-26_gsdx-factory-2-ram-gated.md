# GSDX factory-2: work gated on free RAM (Owner, 2026-10-26: "añade todo esto al backlog ... en cuanto se tenga RAM")

**Activation criterion:** free physical RAM >= 3000 MB on the laptop (the `top-level-worker` launch floor). Check:
`(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1024`. Last measured: 1262 MB, 27 `claude` processes at
~8 GB working set (2026-10-26 ~08:00). Only recycling a process frees it; `/clear` and `/compact` do not.

**State at parking:** goal `gsdx-factory-2`, chain `vault/programs/gsdx-factory-2/chain.json`, envelope 36M, used
18,216,234. U1 closed (DONE, 0 solved, negative recorded; certified stays 519/1797). PP branch
`feature/knowledge-acquisition` at 2457f5b2 (local, unpushed). GEX44 `~/missions/t1-campaign` `t1/campaign` at 281b9881
(unpushed).

## Items, in order

1. **U2 launch (automatic).** Mission `m-a90380bd764f` is PREPARED; the 5-minute `PP-GsdLongRun-Sweep` retries it and
   refuses with `REFUSE_LOW_MEMORY` until the floor is met. No action needed beyond freeing RAM. Verify with
   `python tools/gsd_mission.py status` (state leaves PREPARED) and the sweep log.
2. **Review the U2 receipt** once `C:\Users\User\Apps\pp-gsdx-factory-2\vault\programs\gsdx-factory-2\WU-U2-receipt.md`
   lands: operator or recorded negative for CLASS_INTERRUPT COUNT_DIFFERS (cohort 45, medoid `fn_801BCA38`), suites
   (NEXT 24, CP1 16, FR1 15), certified before -> after, the follow-up `next` packet. Confirm the chain booked its spend.
3. **Compile U3** from the follow-up `next` packet (packet + route + chain unit, receipt inside the linked worktree, route
   sized from the admission floor: calls x ~120K x 1.2 <= target). Then the same RAM gate applies to its launch.
4. **E0** (plan row): Gen1 vs Gen2 comparison + Knowledge Vault/UKDL + CBR. Plan:
   `vault/plans/gsdx-factory-2-gen2-econ-plan-20261025.md`.

## Debts to run in the same window (suites are flaky under 3000 MB, so do them with RAM)

5. **BLOCKED worker with no receipt never reaches HALTED** (break 11 remainder; `tools/gsd_mission.py`
   `surface_blocked`). f83e256b only closes the case where the receipt is DONE. Needs a red gate + mutant like
   V-OH-BLOCKED-UNIT-RECEIPT-DONE-COMPLETES.
6. **`test_s5_reconcile` hang**: reproduce with a bounded timeout and enough RAM before diagnosing the code.
7. **exact_push not wired**: about 25 local PP commits unpushed (newest 2457f5b2); repo stays PUBLIC, the push scan
   blocks secrets only (Owner policy). GEX44 `t1/campaign` commits are unpushed too (Owner pushes via `! ssh`).
8. **Coordinator inline spend unmeasured** (U1 closeout done inline in pane fc4dce34) and **subagent envelope coverage
   UNKNOWN**: measure before E0 so the comparison is honest.

Related: memory `feedback_chain_unit_stop_must_continue_unattended.md` (breaks 11, 13, 14), unrelated RAM-gated mission
`m-255addec2cfc` (art-commerce, needs >8 GB and an Owner merge/deploy decision; not part of this item).
