# Handoff [D] -- context lifetime / dead context -> economic rollover trigger owner

Pillar: [D] context lifetime / dead context. Terminal: MERGED_INTO_EXISTING_OWNER.

Owners (frozen): `vault/specs/economic-rollover-trigger.md` (the live trigger), `modules/cognitive_os/gc.py`.

## Result handed over (measurement: `vault/programs/cognitive-economy/evidence/D-E-context-lifetime.md`)

- In D-W7 the economic trigger asked 5 times; 3 asks became claimed crossings. Rehydration paid 0.0475 % of D-W7;
  carried context avoided <= 0.2346 %; net **[-0.05 %, +0.19 %]**, an interval, because the counterfactual
  (compaction at the wall, or the session ending) was not measured.
- 124 of the window's 127 interactive crossings came through the 45 % wall route (`route=self` and transport
  routes), not the economic one. Median context at crossing 458 k -> 128 k after.
- The KSR dead-carriage upper bound (<= 6.34 %, on KSR's own denominator) is NOT reclaimed by the trigger as
  observed. The remainder stays an upper bound, not a saving.

## For the owner (suggested measurement, the owner decides)

The spec's Production Reality asks for "`tier: econ` candidates with `would_rollover` true, followed by
`rollover_kclear_asked route=economic` rows". Measured: 39 econ candidates with `would_rollover: true` in
`rollover-ledger.jsonl`, against 5 economic asks in `gsd-autorun-ledger.jsonl`. The gap between verdicts and
asks is worth reading before tuning `CPP_ROLLOVER_ECON_PCT`: a verdict only becomes an ask on a later Stop at the
same HEAD (Behaviour 3), so commits landing in between will drop verdicts. To measure a realized saving instead
of an interval, a crossing needs its counterfactual: compare each economic successor against the predecessor's
own compaction cost at the wall.

## What the owner keeps

The trigger, its thresholds, `tools/rollover.py`, the watchdog and `modules/cognitive_os/gc.py`. The campaign
edited none of them.
