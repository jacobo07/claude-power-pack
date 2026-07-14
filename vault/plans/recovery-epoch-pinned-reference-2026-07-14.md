# Recovery Epoch — pin the reference at the interruption boundary

- date: 2026-07-14
- mode: EXECUTION (not Ultra Plan — no architectural fork; the parent module already named the field)
- parent extended: `modules/session_resilience/` (G4 acceptance, G5 telemetry, G6 beacon/reentry)
- new subsystems: 0

## Finding (evidence, not inference)

The recovery arbiter (`session_resilience/acceptance.py`) is sound. Both of its
callers feed it a reference derived from state read AFTER the interruption:

- `reentry.record_reentry` sets `reference = live panes now` and
  `observed = the restorable subset of those same panes`. After a reboot the dead
  panes are already `live:false`, so the reference has already shrunk to whatever
  survived. It scores RECOVERED while panes are gone.
- `recovery_verdict.latest_reference()` takes the NEWEST `pane_map_history`
  snapshot. The 5-minute snapshotter keeps running after a bad restore, so within
  ~20 minutes the reference BECOMES the damage.

Measured on this host 2026-07-14: the arbiter returned `RECOVERED — 8/8 windows,
13/13 conversations` while the snapshot history shows a peak of 21 live panes.

Neither `classify_startup` nor `record_reentry` is called by any hook — the
interruption boundary is never detected (Liveness Standard: orphan modules).

Root cause: **there is no pinned pre-interruption reference.** A gate whose
denominator is re-derived from the current state cannot witness a loss.

## Change

`power_beacon.write_active_beacon` already declares a `snapshot_ref` field that
no producer ever fills. That starved field IS the pin.

1. `modules/session_resilience/epoch.py` — detect the interruption at a boundary
   (active beacon + OS boot crossing, or active beacon + measured zero live
   terminals: the two-signal rule), and durably pin the last pane_map snapshot
   taken BEFORE the interruption. Idempotent by `interrupted_at`. Immutable
   until judged.
2. Fill `snapshot_ref` on every active beacon write (after the epoch is opened,
   so the new beacon never overwrites the evidence of the crash it recovers from).
3. Redirect both consumers to the pinned reference. No reference ⇒ HELD, never a
   silent RECOVERED.
4. Wire the boundary into the SessionStart hub; surface the verdict.
5. Done-gate `tools/test_recovery_epoch.py` replays a REAL interruption from the
   96 snapshots on disk: current code says RECOVERED on a genuine pane loss
   (proves the bug); the pinned reference says PARTIAL and names the missing
   panes (proves the fix).
6. UKDL L1/L2/L3 + liveness `--baseline`.

## Scope guard

Editor tabs/order/focus/scroll stay OUT of the denominator — the pane_map source
cannot witness them. Reported as not-witnessed, never assumed passing.
