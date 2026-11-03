---
status: APPROVED 2026-11-03 (Owner, session b7234aad: "añade una politica para que sea automatico universalmente en todo lo que la claude power pack este instalado y haya cpp-gsd-long")
covers: [gsd-x-universal, arm-preflight, gsd-milestone-required, capsule-v2-continuity, cpp-gsd-long, packet-unit-gsd]
owner: tools/gsd_mission.py arm_preflight
---

# GSD X universal: every armed mission runs on an open GSD milestone

## Problem (measured 2026-11-02/03, ttb lane B)
`arm_preflight` judged GSD only for `/gsd-` resume commands and WARNED for packet units on a NO_PHASES roadmap
("the packet is the work", gsdx-pcc P52a/b). But the capsule-v2 rollover seals from GSD (`init.manager`) or an open
obligation; with neither, the seal is refused and the mission sits BLOCKED forever (`CAPSULE_SEAL_REFUSED`, "No ROADMAP.md
found"). Three ttb missions died that way at their first context wall: m-6b8ea8f2f7c4, m-8e9e07e378fd, m-a87c05c57195
(~1.2M spent with no code on one of them; each restart was manual).

## Decision
1. `arm_preflight` asks GSD for EVERY arm, whatever the resume command. NO_PHASES or ALL_COMPLETE refuses the arm, packet or
   not, naming the remedy: create the milestone first (`/gsd-new-milestone`, or `.planning/ROADMAP.md` + `STATE.md` whose
   phases are the packet's phases), then arm. UNAVAILABLE stays `unmeasured` (never a refusal, never a pass).
2. Opt-out is explicit and recorded: env `CPP_GSD_X_OPTOUT="<reason>"` turns the refusal into a `warn` carrying the reason.
   An empty reason is no opt-out. `CPP_ARM_PREFLIGHT=off` still disables the whole preflight (existing kill switch).
3. Automatic in the CODE, not an Owner chore (Owner 2026-11-03: "si no tiene el milestone, debe crearse autónomamente,
   no esperar a que yo lo abra"): `arm` (when it launches) and `arm_chain` call `tools/gsd_milestone_scaffold.ensure`
   BEFORE the preflight. On NO_PHASES/ALL_COMPLETE it writes `.planning/ROADMAP.md` + `STATE.md` + `PROJECT.md` with the
   packet's phases (Q/P/W-labels, "Phase N", numbered lines; one fallback phase when none), re-asks the real GSD, keeps
   the files only on `OK`, otherwise restores the previous files. Prior files are moved to
   `.planning/milestones/auto-archived-<stamp>/`, never deleted. Kill switch `CPP_GSD_X_AUTOSCAFFOLD=off`.
4. Measured absence: gsd-tools EXITS 1 with "No ROADMAP.md found" / "No STATE.md found" on a repo with no milestone,
   which `gsd_status` reports as UNAVAILABLE. `gsd_milestone_scaffold.absent_roadmap` reads that as NO_PHASES in both the
   scaffold and the preflight (without it, decision 1 never fired on the commonest case -- found 2026-11-03 by the
   scaffold suite's real-GSD precondition).

## Acceptance
- `tools/test_arm_preflight.py`: V-PRE-GSDX-PACKET-NO-PHASES-REFUSES, V-PRE-GSDX-NON-GSD-ROUTE-REFUSES (both poles: OK passes),
  V-PRE-GSDX-OPTOUT-WARNS (reason recorded), V-PRE-GSDX-EMPTY-OPTOUT-REFUSES, existing gates updated where they encoded the
  P52a/b warn; arm_chain on NO_PHASES with a packet now refuses unarmed. Whole suite green.
- Live: ttb arm with its new milestone passes the gsd_status check (`ok`).

## Never
- Never read UNAVAILABLE as NO_PHASES (a host too loaded to answer must not block every arm).
- Never auto-write a roadmap from inside `arm_preflight` (read-only and idempotent stays true); the agent scaffolds, the gate judges.

## Rollback
Restore the `if resume_command.lstrip().startswith("/gsd-")` branch and the packet warn in `arm_preflight`, revert the test
edits and the cpp-gsd-long paragraph. Nothing else consumes the opt-out variable.
