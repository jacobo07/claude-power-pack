# ctx-rent-obs tranche 1: STATUS (plane: GEX44, clone mission/ctx-rent-obs)

All findings below were observed on GEX44. `tools/cpp_fsck.py` reads this host's `~/.claude/state`, so its live findings describe
GEX44, not the laptop; it was used here only for the tests and the stale_resumption check on repo files.

| unit | state | done-gate (plan section 6) |
|---|---|---|
| W1 TAKEOVER.json + CLOSURE.md | DONE (d6f3fa18) | 12 rows A-L; sha256 8a19463321ff20d31328db4b3574382b7b85c08c86981d71ff56de1f0c5b0588. Rows I, J cite af7ec647 / 44396331, which are NOT objects in this clone: UNVERIFIED on this plane |
| W1 RESUMPTION seal + STALE banner | DONE (07d32082, e863190d) | see gate below |
| W1 econ_plane approval uuid | DONE (958cea47) | red first: `FAIL V-ECON-RAISE-APPROVAL-UUID ... exit 2`; then PASS (source `...:approval:25a5410c-...`). `test_econ_containment.py` ECON_PASS=58/59; the 1 FAIL is V-ECON-ADMISSION-STANDALONE (this host's settings.json has no standalone entry), pre-existing and GEX44-plane |
| W1 cpp_fsck transferred-NEXT | DONE (c3eb72ce, 60965597) | red first `FAIL V-FSCK-F4-TRANSFERRED-NEXT flagged=[]`; then FSCK_PASS=18/18. A second fix after the live file missed slice L at a sentence end |
| W1 ledger moves | NOT DONE here, laptop plane | see LEDGER_TODO |
| W2 B1 | DONE with limits (9efbd87e) | N=3 on GEX44: call-1 67,568 / 67,561 / 67,561. PATH `claude` 2.1.113 was refused by the API (`b1/attempt0-...jsonl`); probes used the already-installed `~/.local/bin/claude` 2.1.310 via CPP_CLAUDE_EXE, no install or settings change. Census JSON of slice B: laptop-plane, pending. B is NOT re-typed from N=1 (different plane) |
| W3 C1 | DONE: REFUTED (78f7c666 then 66201429) | contract commit precedes verdict commit; contract unedited (`git diff 78f7c666 HEAD -- contracts/C1.json` empty). 2 matched pairs, haiku, `--plugin-dir mods/ccr-probe`: subagent first call 46,658 -> 10,823, r = 76.8%, answer OK in both arms. Outside the frozen band [62%, 72%] around the claimed 67%. Direction holds; the number does not transfer (plane difference). Both pairs were bit-identical, so N=2 gives no variance information |
| W4 CI drill | NOT NEEDED, existing | `tools/test_floor_regression_gate.py` already drives injected additions to exit 1: `V-FLOOR-TRACER-E2E ... seeded+1024=1(RISE memory_global universal universal_1k)`, `V-FLOOR-POSITIVE-UNIVERSAL ... rc=1`. Run: `FLOOR_PASS=71/71 threshold=71/71 skipped=0` |

## W1 done-gate result
- ctx-rent-a2: `cpp_fsck` stale_resumption shows no finding for it: PASS. Before the seal the same check flagged it
  (NEXT_NAMES_TRANSFERRED_OBLIGATION, C-K), so the detector fired on the real file.
- econ-succession: the plan expected a FINDING there; **not met.** No TAKEOVER.json sits beside that file (its rows I and J live in
  ctx-rent-a2's), and its anchor 4e9953a7 is an ancestor of HEAD, so only the STALE banner marks it. The check cannot see it until its owner writes a
  TAKEOVER.json or re-anchors. Not extended here (out of section 6).
- goal-status programme == settled + open: **not checkable here.** The goals are not declared on this host (programme null, settled 0).

## goal-status (this host, plane GEX44; the laptop ledger holds the real figures)
`ctx-rent-obs`: programme null, cap null, settled 0, used 0, binding null.  `ctx-rent-a2`: same, all null/0.
Spend of this run is therefore unbooked anywhere (UNKNOWN).

## LEDGER moves: DONE on the laptop plane 2026-10-25 (Owner choice "a")
1. ctx-rent-a2: 36d35fab booked 75,443,513 by `goal-settle` without `--measured` (transcript minus prebind). The
   `since_iso` above was local time against UTC transcript timestamps (would have under-booked ~26.6M) and was not used.
2. ctx-rent-a2 programme set to settled + open = 94,966,147 by the Owner (`goal-programme --owner`); nothing released,
   over-run 34,966,147 (CLOSURE.md, 7d2b2992).
3. ctx-rent-obs: this GEX44 run booked 8,874,921, measured on GEX44 with `session_tree_tokens`, one settle per session:
   worker af2877d3 7,651,518 (equals its modelUsage); B1 probes 6d548cf6 / 928488da / f836e015 = 202,702 (19019039, the
   refused attempt, measured 0 and was not booked); C1 runs 2101c6e3 / cf0d162d / d50d0b66 / f09df71a / f84b2ad9 =
   1,020,701 including subagents. Settled 8,874,921 against the 7,000,000 ceiling: overdraft 1,874,921, ceiling not raised.

## Other notes
- Turn budget: stopped before 45 turns; tranche 1 complete except the laptop-plane items. Tranche 2 needs a new Owner approval.
- Goal binding (First step 1) skipped per the GEX44 brief.
- `.pp-capabilities` untracked file in the clone is not mine; left alone.
