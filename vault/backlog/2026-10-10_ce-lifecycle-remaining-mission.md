# Backlog: rest of the ce-a3 / lifecycle control-plane mission (2026-10-10)

Origin: Owner, 2026-10-10: "put the rest of the mission in the backlog of claude power pack". The mission is the out-of-band
lifecycle control plane from ce-a3 Amendments C and D (`Apps\pp-ce-a3` 4f1fe9ae, 3aa002af). It now runs as lineage
**ce-lifecycle-v3** (plan `Apps\pp-ce-lifecycle-v3\vault\plans\ce-lifecycle-v3-work-unit-economics-plan-2026-10-09.md`,
Owner option A). ce-lifecycle-v2 is RETIRED (incident `ce-lifecycle-v2-incident-coordinator-bind-2026-10-09.md`).

## State measured 2026-10-10 (no unit of this program is running)
- Goal `ce-lifecycle-v3`: cap 14,000,000, used 9,079,339, open 0, remaining 4,920,661
  (`python tools/mission_spend.py goal-status --goal ce-lifecycle-v3`).
- Live in this checkout: L1 prospective goal binding + halt-continues (3f9b57cc). Also live, according to the v3 install
  receipts: L3 econ (37a5f3c0), L4 (ed566db0) and L5 sweep advance stage (f3c0f8a0). The v3 branch head is e2fa4e42
  (2026-10-09 22:17).
- Done on the v3 branch: WU-1H (halt continues), WU-S5d (steward settles every terminal worker), WU-ADV2b (an approval
  record arms the next listed unit from the sweep).
- Resolved: stray m-d84de9dd1edb is under an Owner hold, "Never release".

| # | Task | P | Effort | Impact | Status | What is left / how it closes |
|---|---|---|---|---|---|---|
| 1 | **A hold does not stop a LIVE worker** (WU-TRIP, L6) | 0 | M | Critical | PENDING | Still leaking now. `gsd_mission.py status` shows RUNNING under cost-breaker holds: m-cd548e5d2ada 368M vs a 40M estimate, m-6f7451aefe40 175M vs 87.5M, m-80016a4bb9f2, m-9bee7894f20f, m-e6ea9c26d377. Fix: when a LIVE worker is held, checkpoint it, write a failure record, then end the process. Also spend without durable progress → reforecast. Packet: `WU-TRIP.md`. Canary: a held LIVE worker stops after its checkpoint. |
| 2 | **GOAL_STATE substring regex is still live** | 1 | S | High | PENDING | `hooks/session_budget_guard.js:208` still matches `goal-budget` as a substring and denies reading `vault/specs/goal-budget-admission.md`. The fix is R1b (ce/a3b-r d0d0eb2b), which Amendment D section 5 already authorizes installing. Install it with the same zero-model stage merge as L3-L5. Canary: the spec read passes and a protected write is still denied. |
| 3 | **WU-ADV2a is PARTIAL** (consume-once approval_id + goal-aware admit_route) | 1 | M | High | PARTIAL (3cf67a07) | Read its receipt and finish what it lists. Route admission printed `remaining=None` before this unit; prove it now reads goal remaining. |
| 4 | **WU-1C roots, then WU-1D closes WU-1** (L3/L4 in the old plan) | 1 | M | Medium | PACKETS EXIST | `WU-1C.md` and `WU-1D.md` are in the v3 worktree. `WU-1C2` is SUPERSEDED: never arm it. Arm through the advance stage (approval record), not from a pane. |
| 5 | **v3 economics S2-S4** (exe resolver + PATH-loss canary, floor+growth estimator with three-miss DEGRADED, predictive lease edge + closeout reserve) | 1 | L | High | UNVERIFIED | `WU-S2/S3/S4` left `.partial.json`/`.residual.md` files (untracked), so they ran, but no receipt was checked for this list. Confirm each receipt says DONE before arming more chain units: without the edge, units keep ending at the breaker (WU-ADV2b 987,645 > 960,000). |
| 6 | **WU-INST as a formal installer** (L5 of Amendment D) | 2 | M | Medium | PARTLY DONE | Installs ran as ad-hoc "zero-model stage merge" scripts (L3/L4/L5 receipts). Make it one tool: staged 3-way merge into the live checkout, commit by index (`git apply --cached`; the live tree carries foreign E4a edits), suites run there, sha receipt, drift check, rollback. Installing a guard change outside Amendment D's named set needs one hash-bound Owner YES. |
| 7 | **WU-FLOOR = A3 U3** (fresh focus floor) | 2 | M | Medium | PACKET EXISTS | Measure first (Proof of Non-Work). E1/TOK-18 may already cover it, which would make it MERGED or NO_WORK. Ceiling 1.0M. |
| 8 | **WU-GEX = A3 U4** (GEX44 binding) | 3 | S | Low | PACKET EXISTS | Proof of Need first: does any laptop goal run a GEX44 worker? If not, NO_WORK. Ceiling 0.8M. |
| 9 | **WU-CLOSE = A3 U5 + a3b-r R6/R7** | 2 | M | High | PACKET EXISTS | UNKNOWN spend fails closed at `gsd_mission.admit_route` and `loop_budget.admit_subagent`. Then canaries, KV/UKDL/CBR, CI wiring, and the ctx-rent S2 handoff. |
| 10 | **v3 knowledge (S7)** | 2 | S | Medium | PENDING | Record the incident and the traps in UKDL: coordinator cwd bind; R4 retroactive attribution x3 (6.86M, 32.58M); linear estimator vs quadratic cost. CBR only after the canaries pass live. |
| 11 | **v3 worktree hygiene** | 2 | S | Low | PENDING | 22 untracked `.partial.json`/`.residual.md` files plus `vault/specs/salvage/`. `RESUMPTION_FILE.md` (modified) still calls S5d uncommitted, but it is 4caca0e9. `lifecycle/RESUMPTION.md` was last written 2026-10-09 12:15. Rewrite one resume file from this list, then commit or discard the rest by pathspec. |
| 12 | **Close v2 for good** | 3 | S | Low | OWNER DECISION | v2 still has 104,498 of halt authority. Lowering its cap to used is the Owner's call (incident file, section Repair). |

## Master done-gate (Amendment D section 6 + v3 plan; none passed as a whole yet)
- Packetless arm → no process.
- Success without a receipt → RECOVERY_PENDING plus a record.
- A held DEAD worker settles; a held LIVE worker stops after its checkpoint (#1).
- An extension keeps cumulative spend and creates no new goal id.
- The live guard hash equals the approved hash, the spec read passes and the protected write is denied (#2).
- One successor is armed by the sweep with no pane.
- The PATH-loss canary, the three-miss DEGRADED canary and the edge-before-breaker replay of WU-1H3 pass (#5).
- A3: U2 SUPERSEDED, and U3/U4/U5 each DONE, NO_WORK or MERGED with evidence (#7-#9).
- The UNKNOWN 296,437 from the ce-a3 autopsy stays UNKNOWN.

## Recommended order
#1 (it is still leaking) → #2 → #5 + #3 (so later units stop ending at the breaker) → #4 → #9 → #7/#8 → #6, #10, #11.
Budget: the v3 plan forecast the chain at ~5.5M against 4.92M remaining. A unit that does not fit writes
WAITING_FOR_AUTHORITY with an EAC; never open a new goal id as a budget reset.

## Rules for whoever picks this up
- Never `cd` / `Set-Location` into a goal root. Use `git -C` and absolute paths. That bind cost 32.8M on 2026-10-09.
- Re-read the target worktree's `git log` right before writing a packet. Announce ownership by message, never by
  editing another pane's packet.
- Arm with `--no-launch` → `envelope` → `admit`. A bare `arm` launches without a packet.
