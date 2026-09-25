---
covers: [gex44-mission-plane, mission-renewal, mission-disk-floor, gsd-mission-linux]
tier: T3
status: SPEC (nothing below is implemented unless marked LIVE)
owner_decisions: 2026-09-25
---

# GEX44 mission plane

## Problem (measured 2026-09-25)

Ralph missions run as `claude --bg` workers on the Owner's Windows laptop, supervised by a
Windows scheduled task. On that host: 1.1 GB free of 32 GB RAM with 50 Claude processes, so a
Phase-6 drill parked for hours on a local 3000 MB floor; two missions halted on their 24 h
budget while blocked; nothing re-arms a halted mission. GEX44 (Linux, 20 cores, 49 GB RAM
available, Claude Code 2.1.113 authenticated, Power Pack + gsd-core installed) is idle capacity.

## Owner decisions

1. Missions that do not need Windows move to GEX44: **KME first (pilot), then LuckyArena and
   CavEX**. **Orca X (Electron/Windows) and KobiiSports (Windows Wii toolchain) stay local.**
2. A budget halt must not end a mission that still has work: renew it, bounded.
3. Low disk on GEX44 triggers an **audit of `~/kobicraft` (1,280 GB)**, reported to the Owner.

## Scope

**A. Renewal (both planes).** When the supervisor halts a mission for `budget` only, and GSD
reports `OK` (work remains), it arms a successor mission copying cwd, resume command,
workstream, work_dir, add_dirs, permission mode and ALL directives; records `renewed_from`,
`lineage_id`, `renewal` n. Cap: 3 renewals per lineage, then a real HALT naming the cap.
Never renews: a mission halted by hand, COMPLETED, GSD `UNAVAILABLE`/`NO_PHASES`, or a halt
whose reason is not budget. Ledger event `mission_renewed`.

**B. GEX44 plane.**
- Power Pack on GEX44 becomes a git clone of `jacobo07/claude-power-pack`, synced by a
  fast-forward-only pull before each sweep; a non-fast-forward refuses the sweep and logs it.
- `gsd_mission.py` Linux paths: process argv from `/proc/<pid>/cmdline`, stop by process
  group, git from PATH. No Windows branch changes behaviour.
- Supervisor: systemd user timer, 5 min, `OnUnitInactiveSec`, `TimeoutStartSec=15min`.
- Each project runs from its own clone under `~/missions/<project>/`, on a mission branch
  `mission/<id>` pushed to origin after every committed step. Local panes pull; nobody edits
  the GEX44 checkout by hand. One writer per checkout.

**C. Disk floor.** Before any launch or relay, measure free space on `/`. Below **30 GB**:
hold the relay (ledger `relay_held reason=disk`) and run a READ-ONLY audit of `~/kobicraft`
(du tree to depth 3, largest files, oldest-untouched dirs, duplicate-size groups). Write it to
`~/.claude/state/disk-audit-<ts>.md` and surface it. **The plane deletes nothing** — reclaiming
space is an Owner decision per item (destructive-state-authorization).

## Out of scope

Moving Orca X or KobiiSports; any automatic deletion; running local and GEX44 workers on the
same mission; changing worker permission mode (stays `auto`, never bypass).

## Acceptance

- A: synthetic budget-halted mission with GSD `OK` renews once with directives intact; a
  hand-halted one does not; the 4th renewal halts with the cap reason; GSD `UNAVAILABLE` holds.
  Mutation: removing the cap check turns the cap gate red.
- B: on GEX44, `gsd_mission.py status` runs from the git clone; a pilot KME mission launches,
  relays at its wall at least once, and pushes a commit to `mission/<id>`.
- C: with the floor forced above free space, the relay is held and an audit file exists with
  no filesystem write outside `~/.claude/state/`. Control: floor below free space launches.

## Rollback / kill switches

`CPP_MISSION_RENEW=off` disables A. `systemctl --user disable --now pp-mission-sweep.timer`
stops B. Removing a project's clone ends it there; its branch stays on origin.

## Open risks

- Both hosts share one Claude subscription: GEX44 workers spend the same usage.
- `/` was 97% full and shrank 2 GB during one measurement: some GEX44 writer is active.
- Claude Code 2.1.113 on GEX44 may lag the local build; `--bg` behaviour must be re-measured
  there before the pilot, not assumed from W0 (measured on Windows).
