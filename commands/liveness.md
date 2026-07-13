---
description: Is anything we shipped actually running? Audits every module for reachability from a live surface and reports LIVE / WIRED-BUT-SILENT / DRIFTED / ORPHANED.
---

# /liveness

The ecosystem verifies at CONSTRUCTION time (V-gates, hermetic runs, done-gates) and is
blind POST-SHIP. A V-gate proves code works *when invoked*; nothing proves anything
invokes it. `built != wired` is the recurring class: dispatcher drift, producers with no
consumer, orphan modules, the Copy-Item last mile.

Two commands, one question.

## The whole ledger

```
python modules/liveness/liveness_ledger.py
```

One row per module found on disk, plus the hand-declared components (hook dispatcher, the
PM-03 bus, the Stop-chain hooks). Declaring is not a prerequisite for being audited: a
module is audited because it EXISTS. That is the fix for the ledger's original defect --
a component nobody declared was not scored UNKNOWN, it was absent from the denominator
entirely, and absence read as health.

## The reachability gate

```
python modules/liveness/reachability.py            # report + gate (exit 1 on a new orphan)
python modules/liveness/reachability.py --json
python modules/liveness/reachability.py --baseline # freeze today's debt after wiring one
```

Exit 1 means a module exists, imports cleanly, probably passes its tests -- and **no live
surface reaches it**. Three ways to clear it, in order of preference:

1. **Wire it.** Give it a hook, a command, or a tool a real surface invokes. Then re-run
   `--baseline` so the standing debt shrinks by name.
2. **Declare it** in `vault/liveness/reachability_registry.json` with a class:
   `LIBRARY` (imported by siblings only), `SCHEDULED` (driven by a scheduled task),
   `DEPRECATED` (dead on purpose), or `PLANNED` (wiring pending -- must carry an
   OWNER_QUEUE row). Silence is not an exemption; a malformed class is not an exemption.
3. **Delete it.** An unreachable module that nobody will wire is debt with a maintenance
   bill.

The debt is enumerated BY NAME, never as a count or a ratio: a threshold is satisfied by
deleting a module and a ratio is satisfied by adding a reachable one. Only a named set
forces the number down for the right reason.

## Standard

Any NEW module that lands unreachable and undeclared fails the gate. That is the point:
the next dead subsystem should be caught the week it is built, not the month someone
finally goes looking.
