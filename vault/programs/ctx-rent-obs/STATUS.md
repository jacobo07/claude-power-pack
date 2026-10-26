# ctx-rent-obs tranche 1: STATUS (plane: GEX44, clone mission/ctx-rent-obs)

All findings below were observed on GEX44. `tools/cpp_fsck.py` reads this host's `~/.claude/state`, so its live findings describe
GEX44, not the laptop; it was used here only for the tests and the stale_resumption check on repo files.

| unit | state | done-gate (plan section 6) |
|---|---|---|
| W1 TAKEOVER.json + CLOSURE.md | DONE (d6f3fa18) | 12 rows A-L; sha256 8a19463321ff20d31328db4b3574382b7b85c08c86981d71ff56de1f0c5b0588. Rows I, J cite af7ec647 / 44396331, which are NOT objects in this clone: UNVERIFIED on this plane |
| W1 RESUMPTION seal + STALE banner | DONE (07d32082, e863190d) | see gate below |
| W1 econ_plane approval uuid | DONE (958cea47) | red first: `FAIL V-ECON-RAISE-APPROVAL-UUID ... exit 2`; then PASS (source `...:approval:25a5410c-...`). `test_econ_containment.py` ECON_PASS=58/59; the 1 FAIL is V-ECON-ADMISSION-STANDALONE (this host's settings.json has no standalone entry), pre-existing and GEX44-plane |
| W1 cpp_fsck transferred-NEXT | DONE (c3eb72ce, 60965597) | red first `FAIL V-FSCK-F4-TRANSFERRED-NEXT flagged=[]`; then FSCK_PASS=18/18. A second fix after the live file missed slice L at a sentence end |
| W1 ledger moves | DONE on the laptop plane (08a441b7) | see LEDGER moves below |
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

## Tranche 2 (laptop plane, 2026-10-25; plan e26dd9f4; capital packet f651f202, approval 05863e30)
| unit | state | evidence |
|---|---|---|
| W5a worker boot census | DONE (fe149cdf selection, 066a6e92) | `B2.md`: background 102,244-105,796, slim-t2 18,285-20,218 |
| W5b C2 | SKIPPED by the saturation rule | no attributable boot source above 10K (B2) |
| W6 estate rent | DONE (7c4d9be7) | `ESTATE.md`: week 9.18B processed, top-level 92.5%, floor rent 48.1% |
| W7 receipt | this section | |

**Overrun, stop-loss crossed.** W5a and W6 ran inline in this coordinator pane (~150-190K per call) instead of a fresh
worker, on the reasoning that both are deterministic. The pane cost was the overrun: since the first tranche-2 turn
(2026-10-25T19:51:59Z, UTC cut) `session_tokens` = **8,839,459** over 60 calls (5,470,937 since the approval alone),
against 4,000,000 approved. Booked: `goal-settle --goal ctx-rent-obs --session e9fc375e-... --measured 8839459`.
Goal now: programme 12,874,921, settled 17,714,380, **overdraft 4,839,459**. Covered 2026-10-26 by the Owner (`goal-programme --owner --value 17714380`): programme ==
settled == 17,714,380, open 0, executable 0. The goal is closed with no spendable remainder. Work stopped at
the crossing; nothing else ran. The ctx-rent-obs follow-ups earlier in this session (items 2-5, before 19:51:59Z)
are measured as part of the same transcript and not booked anywhere.

Next lever (from ESTATE): the top-level boot floor, ~356M/week per 10K removed. Not started; needs its own plan and
capital, run by a fresh worker, never inline in a long pane.

## Other notes
- Hook pass-through of the approval uuid (`hooks/econ_admission.js` `doRaiseGoal`/`doRaise` do not send `--approval-uuid`):
  Owner decision 2026-10-25 (a): NOT wired on this branch. The approving entry is not yet in the transcript when
  UserPromptSubmit runs, and econ-succession S3/S2 (branch `oc1-econ-succession`, af7ec647) rewrites this path with durable
  pre-model approval receipts. It closes when that programme integrates S3; a separate fix here would duplicate and conflict.
- Turn budget: stopped before 45 turns; tranche 1 complete except the laptop-plane items. Tranche 2 needs a new Owner approval.
- Goal binding (First step 1) skipped per the GEX44 brief.
- `.pp-capabilities` untracked file in the clone is not mine; left alone.

## Tranche 3 (laptop plane, 2026-10-26; plan e4d889a8): STOPPED after W8 on the per-unit stop-loss
- **Capital approval not verified by this pane.** The pane was launched with the plan's section 6 prompt; the t3 packet
  approval (`approve ctx-rent-obs only`) was not visible in this repo and the pane did not check the ledger. The Owner
  should confirm it exists before any booking.
- **W8 done** (4564caa3 selection first, b4466a8b data): `B3.md`, N=8 selected, 7 valid (e3375b9a floor UNKNOWN), 4 repos,
  mean measured floor 110,190, named sources 55,393 (ESTIMATE), UNATTRIBUTED 54,797 (49.7%).
- **Metered** with `mission_spend.session_tokens` on this transcript right after W8 (UTC 2026-10-26): **2,801,368
  tokens over 27 calls**, against a W8 P80 of 0.9M. That is 3.1x P80, over the plan's 2x stop-loss (1.8M).
- **Stopped.** W9, W10, W11 not run. The remaining 1.2M under the 4.0M ceiling is under W9's P50 (1.6M).
- Cause: the per-call floor in this pane was ~104K (the PP repo's own boot), so 27 calls cost ~2.8M before any probe.
  W8 carried about 8 tool-result reads of ~20K each and a failed Bash call; the plan's 0.6M P50 assumed ~6 calls.
- Not booked: no `goal-settle` was run. W11 booking needs the Owner's decision on the 2.8M.
