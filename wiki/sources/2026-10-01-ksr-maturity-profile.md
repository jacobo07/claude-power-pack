---
type: source
created: 2026-10-01
updated: 2026-10-01
sources: [2026-10-01-ksr-maturity-profile]
raw: raw/2026-10-01-ksr-maturity-profile.md
kind: note
origin: read-only profiling subagent, 2026-10-01, ~38 file reads; KSR repo @ 14f7840 (did not read KobiiCraft)
---

# KobiiSports Resort: traits and maturity profile (2026-10-01)

Target side of the maturity-transfer pilot ([[maturity-transfer]]). KSR = a Kamek C++ module
injected into retail Wii Sports Resort PAL, shipped as a patched WBFS. Uses the shared taxonomy
(L1 works · L2 survives failure · L3 operable · L4 evolvable · L5 product · LG governed).

## Traits

- PRESENT: persistent user state (NAND save), content-heavy, build artifact, external integrations,
  constrained target, UI surface, modding a binary. New traits: reverse-engineered subject and
  scarce shared hardware (GEX44 boot quota, one physical Wii).
- PARTIAL: concurrent users (LAN code never seen running), remote deploy (GEX44 is a test host;
  players get a hand-carried disc), AI pipeline (dev side only), economy (local coins), playable
  (hub unreachable on silicon).
- ABSENT: live service, localized.

## Shape

41 capabilities: 28 LIVE, 9 BUILT-UNPROVEN, 4 DOC-ONLY.
- **LG governed** is the strongest: 7/7 LIVE, 111 rules, 10 ADRs, 88 lessons.
- **L5 product** has zero LIVE entries.
- **Weakest:** product CI and automated playtest (none; full headless playthrough judged
  not viable, ADR-002); release/rollback (`pipelines/release`, `rollback` empty); infra operability
  (dispatcher reported RUNNING while INACTIVE).
- *Interpretation (agent's):* rules tend to arrive after incidents rather than gates before them.

## What I re-verified myself

**G17, player-save integrity: confirmed in source.**
- Load accepts the file only if `rd >= 32`, magic matches and version is 1..10
  (`tools/caddie/src/main.cpp:1443-1445`).
- Anything else takes `memset(sd, 0, …)` with no log line on that branch (`:1498-1500`).
- `WriteKobiiSave` then opens the same file, seeks to 0 and overwrites it in place, with no
  checksum, temp file or backup (`:1555-1565`).
- Consequence: one torn write, or one downgrade after a version bump, silently resets a player's
  coins and rank, and the next save makes it permanent. A CRC32 already exists in
  `kobii_klog.cpp:327-331` and is not used by the save.

## Taken without re-checking

The other 23 gaps (G01-G24) with their backlog citations, the capability statuses, and the counts
per level. In particular: no devkitPPC on any reachable host (KSR-B-031), and the 2026-10-01 Owner
STOP of all four missions (KSR-B-060..072).
