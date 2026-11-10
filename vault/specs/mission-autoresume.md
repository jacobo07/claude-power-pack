---
status: SPECIFIED 2026-11-10 (Owner: "añade un sistema global de claude power pack que reanude las misiones cuando se paren por 5 minutos")
tier: T2
covers: [mission-autoresume, stopped-mission-resume, halted-mission-five-minutes, renewal-auto-envelope]
owner: tools/mission_autoresume.py, called from tools/gsd_mission.py supervise() (the existing 5-minute sweep)
---

# A mission that stops for 5 minutes resumes on its own when it may, and the Owner hears when it may not

## Incident (measured 2026-11-10, GEX44, Ascension S23 m-f27c61b9e75c)
HALTED 09:42:09Z on "iterations 12 >= max 12" with 0 of 9 phases ticked. The halt-time renewal was refused
("lineage budget exhausted: 43,474,533 of 23,232,149"), but 23.2M was the AUTO envelope, not the Owner's 160M. The
refusal went only to the sweep row, so nothing was ledgered and nobody was told. The mission sat idle for 3 h 46 min
until the coordinator renewed it by hand (m-3f44ac4c922c).

## Change (one more pass of the existing sweep; no new loop, timer or daemon)
`autoresume_pass(now)` runs after `advance_pass` in `supervise()` (never in a dry run). It looks at every HALTED
mission whose last `mission_halted` row is at least `DELAY_S` (300 s) and at most `MAX_AGE_S` (24 h) old, and that has
no successor yet (no mission with `renewed_from` = it). It decides once per halt (ledger key = halt seq):

**Resumes** only a halt whose cause is a mechanism of the plane, not an Owner ceiling:
- the reason carries `budget: iterations N >= max N` (iteration cap), alone or with "owner dead" / "turn ended";
- and every existing renewal guard still passes (`_renewal_why_not`: GSD says work remains, renewal cap 3 per
  lineage, launched at least once, tree moved, goal not owned by another mission, Owner authority left);
- with one correction: when the record's envelope is AUTO (`token_estimate_src == "auto"`) and the Owner gave an
  authority, the lineage budget is re-derived as authority minus the closeout reserve. An envelope the Owner or an
  operator set is never raised.
- The successor carries the remainder of the wall (`max_hours` minus the time already used), never a fresh one.
  Less than 15 min left = not resumed.
- Ledger `autoresume_renewed` (successor id) on the halted mission. The ordinary launch path starts it on the next pass.

**Never resumes** (Owner classes; these are notified instead): an Owner hold or close, Owner authority or wall
exhausted ("older than N h"), a worker BLOCKED on a human, no_progress / stagnation, launches never acknowledged,
GSD not answering "work remains", the renewal cap reached, anything unrecognised.
For each of these: ledger `autoresume_refused` (reason) once and `mission_remedies.notify_incident` with key
`autoresume:<seq>` (delivered once, failed channel retried at most 3 times).

Exception (field dry run 2026-11-10): when the refusal is `singleflight:` (another LIVE mission already carries the
goal, e.g. m-9444639a3c78 superseded by m-ea861dcb4d2e) the work is not stopped: `autoresume_refused notified=False`,
no notice on any pass.

Kill switch `CPP_MISSION_AUTORESUME=off` (also obeys `CPP_MISSION_RENEW=off`). Never raises: an error is ledgered
`autoresume_error` and the sweep continues.

Out of scope: raising any Owner ceiling, re-opening a mission the Owner closed or held, halts older than 24 h (the 93
historical halts on GEX44 stay as they are), changing the halt-time renewal itself (backlog
`2026-11-10_renewal-blocked-by-auto-envelope.md` items 1 and 3).

## Acceptance (tools/test_mission_autoresume.py)
- V-MAR-ITER-RESUMES: iteration-cap halt 6 min ago, GSD OK, auto envelope 23M < spend 43M, authority 160M -> one
  successor; lineage budget = 160M - reserve; max_hours = remainder; ledger `autoresume_renewed`.
- V-MAR-TOO-SOON (negative): same halt 2 min ago -> nothing.
- V-MAR-TOO-OLD (negative): 25 h ago -> nothing, no notification.
- V-MAR-ONCE: a second pass -> no second successor (successor exists).
- V-MAR-WALL (negative): "budget: older than 72 h" -> no successor, `autoresume_refused`, one notify.
- V-MAR-OWNER-HOLD (negative): iteration halt with an owner_hold -> no successor, notified.
- V-MAR-OWNER-ENVELOPE (negative): iteration halt, envelope NOT auto and exhausted -> no successor, notified.
- V-MAR-GSD-DONE (negative): GSD ALL_COMPLETE -> no successor.
- V-MAR-WALL-SPENT (negative): iteration halt with < 15 min wall left -> no successor, notified.
- V-MAR-OFF: kill switch -> nothing at all.
- V-MAR-SUPERSEDED: singleflight refusal -> no successor, no notice on any pass.
- V-MAR-V2-NO-CAPSULE / V-MAR-V2-CAPSULE (review 2026-11-10 HIGH): a capsule-v2 mission renews only with the capsule
  key its halt handed on (`continuity.capsule_key`), never the record's own (predecessor, possibly retired) key.
- V-MAR-TRANSIENT (review LOW): "GSD answered UNAVAILABLE" / "goal check failed" ledger nothing and are re-decided
  on the next pass until MAX_AGE_S.
- V-MAR-WIRED: `supervise()` calls the pass (a real supervise over the temp state renews the fixture).
- Field (GEX44): dry run lists the decision for every HALTED mission of the last 24 h before the deploy.

## Rollback
`CPP_MISSION_AUTORESUME=off` in the sweep's environment, or revert the commit. No state of its own beyond ledger rows.
