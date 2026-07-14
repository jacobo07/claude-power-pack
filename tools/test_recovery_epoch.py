#!/usr/bin/env python3
"""V-gates for the Recovery Epoch (the pinned pre-interruption reference).

The load-bearing pair is V-EPOCH-BUG-REPRO / V-EPOCH-FIX. They run the SAME
verdict code over the SAME pane loss and differ only in which snapshot is chosen
as the reference:

  * newest snapshot (the behaviour before this change) -> RECOVERED. Four panes
    are gone and the gate passes, because the snapshotter already recorded the
    damage and the damage is being scored against itself.
  * the snapshot PINNED before the interruption          -> PARTIAL, four panes
    named.

A test that only asserted the fix would not prove the bug was real. Both poles
are asserted, so neither can pass vacuously.

Hermetic: everything is written under a temp state dir. Real pane RECORDS (repos,
cwds, session ids) are lifted from the live pane_map history when it exists, so
the fixture is shaped like production and not like the author's imagination; when
it does not exist, synthetic panes of the same shape are used and the run says so.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from modules.session_resilience import epoch, power_beacon  # noqa: E402
import tools.recovery_verdict as rv  # noqa: E402

PASSES: list[str] = []
FAILS: list[str] = []


def _ok(gate: str, evidence: str) -> None:
    PASSES.append(gate)
    print(f"  ok   {gate}: {evidence}")


def _fail(gate: str, diag: str) -> None:
    FAILS.append(gate)
    print(f"  FAIL {gate}: {diag}")


UTC = timezone.utc
T_REF = datetime(2026, 7, 13, 16, 27, tzinfo=UTC)      # last snapshot while alive
T_CRASH = datetime(2026, 7, 13, 16, 40, tzinfo=UTC)    # the lights go out
T_BOOT = datetime(2026, 7, 13, 17, 5, tzinfo=UTC)      # machine comes back
T_POST = datetime(2026, 7, 13, 17, 20, tzinfo=UTC)     # snapshotter records the damage
T_NOW = datetime(2026, 7, 13, 17, 25, tzinfo=UTC)


def real_panes(limit: int = 6) -> tuple[list[dict], str]:
    """Pane records from the live history -- real repos, cwds and session ids."""
    hist = Path.home() / ".claude" / "state" / "pane_map_history"
    if hist.is_dir():
        for f in sorted(hist.glob("pane_map_*.json"), reverse=True):
            try:
                data = json.loads(f.read_text(encoding="utf-8-sig"))
            except (ValueError, OSError):
                continue
            panes = [p for p in (data.get("panes") or []) if p.get("sessionId")]
            if len(panes) >= limit:
                return [dict(p) for p in panes[:limit]], f"real records from {f.name}"
    panes = [
        {"sessionId": f"0000000{i}-aaaa-bbbb-cccc-00000000000{i}",
         "repo": f"repo-{i % 3}", "cwd": f"C:/repos/repo-{i % 3}",
         "resumeCmd": "claude --resume", "tier": "OPEN-NOW"}
        for i in range(limit)
    ]
    return panes, "synthetic records (no live pane_map_history on this host)"


def write_snapshot(state_dir: Path, ts: datetime, panes: list[dict], live: int) -> Path:
    """A pane_map snapshot where the first ``live`` panes are alive."""
    payload = {"panes": [
        {**p, "live": i < live} for i, p in enumerate(panes)
    ]}
    hist = state_dir / "pane_map_history"
    hist.mkdir(parents=True, exist_ok=True)
    path = hist / f"pane_map_{ts.strftime('%Y%m%d_%H%M')}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_live_map(state_dir: Path, panes: list[dict], live: int) -> None:
    payload = {"panes": [{**p, "live": i < live} for i, p in enumerate(panes)]}
    (state_dir / "pane_map.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def point_rv_at(state_dir: Path) -> None:
    rv.STATE_DIR = state_dir
    rv.HISTORY_DIR = state_dir / "pane_map_history"
    rv.RECEIPTS_DIR = state_dir / "receipts"


def run_verdict() -> tuple[int, dict]:
    """rv.main --json, with stdout captured, so we assert on the real CLI path."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = rv.main(["--json", "--no-receipt"])
    out = buf.getvalue()
    start = out.find("{")
    payload = json.loads(out[start:]) if start >= 0 else {}
    return code, payload


def main() -> int:
    panes, provenance = real_panes(6)
    print(f"fixture: {provenance}")
    tmp = Path(tempfile.mkdtemp(prefix="pp_epoch_"))
    try:
        state = tmp / "state"
        state.mkdir(parents=True)
        point_rv_at(state)

        # --- The world before the crash: 6 panes alive, snapshotted. -----------
        pre = write_snapshot(state, T_REF, panes, live=6)
        # The session was alive and never closed gracefully.
        power_beacon.write_active_beacon(state, session_id="sid-live",
                                         snapshot_ref=pre.name,
                                         now=T_CRASH.isoformat())
        # The restore brought back 2 of 6. The snapshotter then recorded THAT.
        write_live_map(state, panes, live=2)
        post = write_snapshot(state, T_POST, panes, live=2)

        # --- Detection ---------------------------------------------------------
        det = epoch.detect_interruption(state, boot_time=T_BOOT, now=T_NOW)
        if det["interrupted"] and det["cause"] == epoch.CAUSE_UNGRACEFUL:
            _ok("V-EPOCH-DETECT-BOOT",
                "active beacon + machine booted after it -> interruption")
        else:
            _fail("V-EPOCH-DETECT-BOOT", f"expected interrupted, got {det}")

        # A new pane opened while others run must NOT read as a crash: the beacon
        # is active but the machine did not reboot and nothing measured zero.
        det_new = epoch.detect_interruption(state, live_terminal_count=None,
                                            boot_time=T_CRASH - timedelta(hours=3),
                                            now=T_NOW)
        if not det_new["interrupted"]:
            _ok("V-EPOCH-NO-SINGLE-SIGNAL",
                "active beacon alone (no reboot, count unmeasured) -> no epoch")
        else:
            _fail("V-EPOCH-NO-SINGLE-SIGNAL",
                  f"false positive on a normal new pane: {det_new}")

        det_cold = epoch.detect_interruption(state, live_terminal_count=0,
                                             boot_time=T_CRASH - timedelta(hours=3),
                                             now=T_NOW)
        if det_cold["interrupted"]:
            _ok("V-EPOCH-DETECT-COLDSTART",
                "active beacon + measured zero live terminals -> interruption (no reboot)")
        else:
            _fail("V-EPOCH-DETECT-COLDSTART", f"expected interrupted, got {det_cold}")

        power_beacon.write_graceful_exit(state, now=T_CRASH.isoformat())
        det_graceful = epoch.detect_interruption(state, boot_time=T_BOOT, now=T_NOW)
        if not det_graceful["interrupted"]:
            _ok("V-EPOCH-GRACEFUL-CLEAN", "graceful beacon -> no epoch even across a reboot")
        else:
            _fail("V-EPOCH-GRACEFUL-CLEAN", f"clean close read as a crash: {det_graceful}")
        power_beacon.write_active_beacon(state, session_id="sid-live",
                                         snapshot_ref=pre.name, now=T_CRASH.isoformat())

        # --- THE BUG: the newest snapshot passes a real loss -------------------
        code_bug, out_bug = run_verdict()   # no epoch open yet -> newest reference
        if out_bug.get("reference_source") == "newest" and out_bug.get("verdict") == "RECOVERED":
            _ok("V-EPOCH-BUG-REPRO",
                f"4 of 6 panes gone, scored against {out_bug['reference']} -> "
                f"RECOVERED (exit {code_bug}) -- the loss is invisible")
        else:
            _fail("V-EPOCH-BUG-REPRO",
                  f"expected a silent RECOVERED against the newest snapshot, got {out_bug}")

        # --- THE FIX: the pinned reference sees it -----------------------------
        ep = epoch.open_epoch(state, epoch.detect_interruption(
            state, boot_time=T_BOOT, now=T_NOW), now=T_NOW)
        if ep and ep["reference_file"] == pre.name:
            _ok("V-EPOCH-PIN-PRE",
                f"pinned {ep['reference_file']} (pre-interruption), not {post.name}")
        else:
            _fail("V-EPOCH-PIN-PRE", f"wrong pin: {ep}")

        code_fix, out_fix = run_verdict()
        missing_ok = out_fix.get("verdict") in ("PARTIAL", "FAILED")
        conv = (out_fix.get("dimensions") or {}).get("conversations", {})
        if missing_ok and code_fix == 3 and "2/6" in str(conv.get("summary", "")):
            _ok("V-EPOCH-FIX",
                f"same loss, pinned reference -> {out_fix['verdict']} (exit {code_fix}); "
                f"conversations {conv['summary']}")
        else:
            _fail("V-EPOCH-FIX",
                  f"the pinned reference failed to witness the loss: {out_fix} exit={code_fix}")

        # --- The pin must not re-pin as panes trickle back ---------------------
        write_snapshot(state, T_POST + timedelta(minutes=20), panes, live=3)
        ep2 = epoch.open_epoch(state, epoch.detect_interruption(
            state, boot_time=T_BOOT, now=T_NOW), now=T_NOW)
        if ep2 and ep2["reference_file"] == pre.name:
            _ok("V-EPOCH-IDEMPOTENT",
                "re-running on the same interruption keeps the original pin "
                "(a re-pin would select the damage)")
        else:
            _fail("V-EPOCH-IDEMPOTENT", f"the pin moved: {ep2}")

        # --- A shortfall stays open; only a real recovery closes it ------------
        cur = epoch.read_epoch(state)
        if cur and cur.get("status") == epoch.OPEN and cur.get("verdict") in ("PARTIAL", "FAILED"):
            _ok("V-EPOCH-STAYS-OPEN",
                f"verdict {cur['verdict']} recorded and the epoch stays open")
        else:
            _fail("V-EPOCH-STAYS-OPEN", f"a shortfall was closed or not recorded: {cur}")

        write_live_map(state, panes, live=6)          # every pane really comes back
        code_done, out_done = run_verdict()
        closed = epoch.read_epoch(state)
        if (out_done.get("verdict") == "RECOVERED" and code_done == 0
                and closed and closed.get("status") == epoch.CLOSED):
            _ok("V-EPOCH-CLOSE-ON-RECOVERED",
                "all 6 panes back -> RECOVERED against the SAME pin, epoch closed")
        else:
            _fail("V-EPOCH-CLOSE-ON-RECOVERED",
                  f"a true recovery did not close the epoch: {out_done} {closed}")

        # --- No reference -> HELD, never a silent pass -------------------------
        state2 = tmp / "state2"
        (state2 / "pane_map_history").mkdir(parents=True)
        point_rv_at(state2)
        write_live_map(state2, panes, live=2)
        power_beacon.write_active_beacon(state2, now=T_CRASH.isoformat())
        epoch.open_epoch(state2, epoch.detect_interruption(
            state2, boot_time=T_BOOT, now=T_NOW), now=T_NOW)
        code_held, _ = run_verdict()
        if code_held == 2:
            _ok("V-EPOCH-HELD-NO-REFERENCE",
                "interruption with no pre-crash snapshot -> HELD (exit 2), not RECOVERED")
        else:
            _fail("V-EPOCH-HELD-NO-REFERENCE",
                  f"expected HELD exit 2, got exit {code_held}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = len(PASSES) + len(FAILS)
    print(f"\nEPOCH_PASS={len(PASSES)}/{total}  threshold={total}/{total}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
