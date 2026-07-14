"""Recovery Epoch -- the pinned pre-interruption reference.

The arbiter (acceptance.py) is sound; both of its callers were feeding it a
reference derived from state read AFTER the interruption. `reentry` scored the
panes that came back against the restorable subset of those same panes;
`recovery_verdict` took the NEWEST pane_map snapshot, and the 5-minute
snapshotter keeps running after a bad restore. In both cases the reference
shrinks to fit the damage, so the gate compares damage against damage and
passes. A gate whose denominator is re-derived from the current state cannot
witness a loss.

An epoch is the missing boundary. When startup crosses an interruption, we PIN
the last pane_map snapshot taken while the session was still alive and freeze it
in `recovery_epoch.json`. That pin is a pointer to an immutable historical file,
written durably, and it never advances while the epoch is open -- so the
reference cannot heal itself into the damage.

`power_beacon.write_active_beacon` already declared a `snapshot_ref` field that
no producer ever filled. That starved field is the pin; this module is its
producer and its consumers' single source of truth.

Detection obeys the two-signal rule (ACV stale-marker lesson) -- one signal is
never enough:
  * an ACTIVE beacon (the session never closed gracefully) AND
  * the machine booted after that beacon was written  -- reboot / OOM-reboot
    OR a MEASURED zero live-terminal count            -- app-level kill, no reboot

A signal we cannot measure is never assumed. No boot time and no measured
terminal count -> no epoch (silence beats a false positive). No pre-interruption
snapshot -> the epoch opens with reference=None, and the verdict is HELD, never
a silent RECOVERED.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import power_beacon

SCHEMA_VERSION = 1
EPOCH_FILENAME = "recovery_epoch.json"
HISTORY_DIRNAME = "pane_map_history"
STAMP_FMT = "%Y%m%d_%H%M"

OPEN = "open"
CLOSED = "closed"

CAUSE_UNGRACEFUL = "ungraceful-shutdown"


# --- time helpers -----------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        dt = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def system_boot_time(now: datetime | None = None) -> datetime | None:
    """When the OS last booted, or None when this host cannot tell us.

    Stdlib only (psutil is not a PP dependency). Windows: GetTickCount64 gives
    milliseconds since boot. Linux: /proc/uptime. Anything else -> None, and the
    caller falls back to the measured-terminal-count signal rather than guessing.
    """
    now = now or _utcnow()
    try:
        if sys.platform == "win32":
            import ctypes

            ms = ctypes.windll.kernel32.GetTickCount64()  # type: ignore[attr-defined]
            return now - timedelta(milliseconds=float(ms))
        uptime_file = Path("/proc/uptime")
        if uptime_file.is_file():
            secs = float(uptime_file.read_text().split()[0])
            return now - timedelta(seconds=secs)
    except (OSError, ValueError, AttributeError, OverflowError):
        return None
    return None


# --- the pinned reference ---------------------------------------------------

def _history_dir(state_dir: Path | str) -> Path:
    return Path(state_dir) / HISTORY_DIRNAME


def snapshot_ts(name: str) -> datetime | None:
    """pane_map_YYYYMMDD_HHMM.json -> its UTC timestamp (the writer stamps UTC)."""
    stem = Path(name).stem
    if not stem.startswith("pane_map_"):
        return None
    try:
        return datetime.strptime(stem[len("pane_map_"):], STAMP_FMT).replace(
            tzinfo=timezone.utc)
    except ValueError:
        return None


def last_snapshot_before(state_dir: Path | str,
                         before: datetime | None = None) -> tuple[str | None, datetime | None]:
    """The newest topology snapshot taken at or before ``before`` -- i.e. the last
    one recorded while the session was still alive. Returns (filename, ts).

    Snapshots stamp to the minute, so a snapshot in the SAME minute as the
    interruption is accepted (<=): it was written before the machine died, and
    excluding it would discard the closest true reference we have.
    """
    hist = _history_dir(state_dir)
    if not hist.is_dir():
        return None, None
    best_name, best_ts = None, None
    for f in hist.glob("pane_map_*.json"):
        ts = snapshot_ts(f.name)
        if ts is None:
            continue
        if before is not None and ts > before:
            continue
        if best_ts is None or ts > best_ts:
            best_name, best_ts = f.name, ts
    return best_name, best_ts


def newest_snapshot(state_dir: Path | str) -> str | None:
    """The freshest snapshot -- what an ACTIVE beacon pins while the session lives."""
    name, _ = last_snapshot_before(state_dir, None)
    return name


def reference_path(state_dir: Path | str, epoch: dict | None = None) -> Path | None:
    """Absolute path of the OPEN epoch's pinned reference, or None."""
    ep = epoch if epoch is not None else read_epoch(state_dir)
    if not ep or ep.get("status") != OPEN:
        return None
    ref = ep.get("reference_file")
    if not ref:
        return None
    p = _history_dir(state_dir) / str(ref)
    return p if p.is_file() else None


# --- detection --------------------------------------------------------------

def detect_interruption(state_dir: Path | str,
                        live_terminal_count: int | None = None,
                        boot_time: datetime | None = None,
                        now: datetime | None = None) -> dict:
    """Did startup cross an interruption? Pure: reads the beacon, writes nothing.

    ``live_terminal_count=None`` means UNMEASURED -- it is never treated as zero.
    Defaulting it to 0 would classify every new pane opened alongside live ones as
    a crash, which is exactly the kind of single-signal false positive the
    two-signal rule exists to prevent.
    """
    now = now or _utcnow()
    beacon = power_beacon.classify_startup(state_dir, 0, now=now.isoformat()).get("beacon")
    out: dict = {"interrupted": False, "cause": None, "signals": [],
                 "interrupted_at": None, "beacon": beacon}
    if not beacon:
        out["signals"].append("no prior beacon on disk (first run)")
        return out
    if beacon.get("kind") == power_beacon.KIND_GRACEFUL:
        out["signals"].append("last exit beacon was graceful (clean close)")
        return out

    b_ts = parse_iso(beacon.get("ts"))
    out["interrupted_at"] = beacon.get("ts")
    signals = ["prior beacon kind=active (session never closed gracefully)"]

    boot = boot_time if boot_time is not None else system_boot_time(now)
    if boot is not None and b_ts is not None and boot > b_ts:
        signals.append(
            f"machine booted at {boot.isoformat(timespec='seconds')}, after that "
            f"beacon was written -- the session did not survive")
        out.update({"interrupted": True, "cause": CAUSE_UNGRACEFUL,
                    "signals": signals, "boot_time": boot.isoformat()})
        return out

    if live_terminal_count == 0:
        signals.append("measured zero live terminals at startup (true cold start)")
        out.update({"interrupted": True, "cause": CAUSE_UNGRACEFUL, "signals": signals})
        return out

    signals.append(
        "no second signal: the machine did not boot after the beacon and the live "
        "terminal count is not zero (or was not measured) -- not an interruption")
    out["signals"] = signals
    return out


# --- the epoch record -------------------------------------------------------

def _epoch_path(state_dir: Path | str) -> Path:
    return Path(state_dir) / EPOCH_FILENAME


def read_epoch(state_dir: Path | str) -> dict | None:
    p = _epoch_path(state_dir)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return None


def open_epoch(state_dir: Path | str, detection: dict,
               now: datetime | None = None) -> dict | None:
    """Pin the pre-interruption reference. Idempotent by ``interrupted_at``.

    N panes start at once after a reboot, so this runs N times concurrently. The
    key is the beacon timestamp: an epoch already open for the same interruption
    is returned UNCHANGED and is never re-pinned -- re-pinning after the panes
    have come back would select a post-crash snapshot and reintroduce the very
    denominator shrink this module exists to stop.
    """
    if not detection.get("interrupted"):
        return None
    now = now or _utcnow()
    key = detection.get("interrupted_at")

    existing = read_epoch(state_dir)
    if existing and existing.get("interrupted_at") == key:
        return existing  # same interruption -> the pin stands, judged or not

    beacon = detection.get("beacon") or {}
    b_ts = parse_iso(key)

    # The beacon's own pin wins when present (it was chosen while the session was
    # alive). Older beacons predate the producer and carry no snapshot_ref -- fall
    # back to selecting by time, which is what the pin encodes anyway.
    ref_name = beacon.get("snapshot_ref")
    ref_ts = snapshot_ts(ref_name) if ref_name else None
    if ref_name and not (_history_dir(state_dir) / str(ref_name)).is_file():
        ref_name, ref_ts = None, None  # pinned file pruned by retention
    if not ref_name:
        ref_name, ref_ts = last_snapshot_before(state_dir, b_ts)

    rec = {
        "schema_version": SCHEMA_VERSION,
        "status": OPEN,
        "cause": detection.get("cause"),
        "opened_at": now.isoformat(timespec="seconds"),
        "interrupted_at": key,
        "signals": detection.get("signals", []),
        "boot_time": detection.get("boot_time"),
        "reference_file": ref_name,
        "reference_ts": ref_ts.isoformat() if ref_ts else None,
        # How stale the reference is relative to the interruption. A large gap is
        # not a failure, but it IS reported: the verdict is only as good as the
        # last topology we recorded before the lights went out.
        "reference_lag_s": (
            int((b_ts - ref_ts).total_seconds()) if (b_ts and ref_ts) else None),
        "session_id": beacon.get("session_id"),
        "verdict": None,
        "missing": [],
        "judged_at": None,
    }
    power_beacon.durable_write_json(_epoch_path(state_dir), rec)
    return rec


def record_verdict(state_dir: Path | str, verdict: str, missing: list[str] | None = None,
                   now: datetime | None = None) -> dict | None:
    """Attach a verdict to the open epoch. RECOVERED closes it; anything else keeps
    it OPEN so the shortfall keeps surfacing until it is really recovered or the
    Owner dismisses it. An unjudged loss that stops being mentioned is a loss that
    was silently accepted -- the exact failure this whole effort exists to end."""
    ep = read_epoch(state_dir)
    if not ep or ep.get("status") != OPEN:
        return None
    now = now or _utcnow()
    ep["verdict"] = verdict
    ep["missing"] = list(missing or [])
    ep["judged_at"] = now.isoformat(timespec="seconds")
    if verdict == "RECOVERED":
        ep["status"] = CLOSED
        ep["closed_reason"] = "recovered"
    power_beacon.durable_write_json(_epoch_path(state_dir), ep)
    return ep


def dismiss(state_dir: Path | str, reason: str = "owner-dismissed",
            now: datetime | None = None) -> dict | None:
    """Owner closes an epoch he does not intend to recover (panes he no longer
    wants). Explicit and recorded -- never automatic."""
    ep = read_epoch(state_dir)
    if not ep or ep.get("status") != OPEN:
        return None
    ep["status"] = CLOSED
    ep["closed_reason"] = reason
    ep["closed_at"] = (now or _utcnow()).isoformat(timespec="seconds")
    power_beacon.durable_write_json(_epoch_path(state_dir), ep)
    return ep


def _main(argv=None) -> int:  # pragma: no cover - CLI for the hub / manual use
    import argparse
    ap = argparse.ArgumentParser(description="Recovery epoch (pinned reference)")
    ap.add_argument("--state-dir", default=str(Path.home() / ".claude" / "state"))
    ap.add_argument("--detect", action="store_true", help="classify startup (no writes)")
    ap.add_argument("--open", action="store_true", help="detect and pin an epoch")
    ap.add_argument("--show", action="store_true", help="print the current epoch")
    ap.add_argument("--dismiss", action="store_true", help="close the open epoch")
    ap.add_argument("--live-terminals", type=int,
                    default=(int(os.environ["PP_LIVE_TERMS"])
                             if os.environ.get("PP_LIVE_TERMS", "").isdigit() else None))
    a = ap.parse_args(argv)

    if a.dismiss:
        print(json.dumps(dismiss(a.state_dir) or {"epoch": None}, ensure_ascii=False))
        return 0
    if a.show:
        print(json.dumps(read_epoch(a.state_dir) or {"epoch": None}, ensure_ascii=False, indent=2))
        return 0
    det = detect_interruption(a.state_dir, a.live_terminals)
    if a.open:
        ep = open_epoch(a.state_dir, det)
        print(json.dumps(ep or {"interrupted": False, "signals": det["signals"]},
                         ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(det, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
