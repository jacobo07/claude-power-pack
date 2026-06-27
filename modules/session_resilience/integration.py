"""Session Resilience OS -- integration entry points (Sprint 6, I1/I2).

Callable, fail-open compositions of the family that a SessionStart hub and the
RAM guard invoke. Per HR-001 (auto-mode must not self-register global ~/.claude
hooks), this module ships the ENTRY POINTS + their tests; wiring them into the
live session_start_hub / ram_guard is an Owner-side registration step documented
in the SCS C56 seal. Every entry point is fail-open: a failure here must NEVER
block session start or a RAM advisory.

  on_session_start  (I1) -- snapshot current state (G3); if a crash is suspected,
                            score the live state against the last good version
                            (G4) and log the recovery lifecycle (G5).
  on_ram_threshold  (I2) -- force a snapshot (G3), validate it reconstructs and
                            scores clean (G4), log it (G5); retry once on failure,
                            then return an honest "not validated" advisory.
"""
from __future__ import annotations

from pathlib import Path

from . import acceptance as G4
from . import snapshot_versioning as G3
from . import telemetry as G5


def on_session_start(
    state_dir: Path | str,
    current_description: dict,
    crash_suspected: bool = False,
    ts: str | None = None,
) -> dict:
    """I1: snapshot the current state; on crash suspicion, detect the recovery gap
    by scoring the live state against the last good version. Fail-open."""
    try:
        store = G3.SessionVersionStore(state_dir)
        col = G5.RecoveryEventCollector(state_dir)
        vid = store.record(current_description, reason="session_start", ts=ts)
        if not crash_suspected:
            return {"snapshot": vid, "recovery": None, "fail_open": False}

        cat = store.catalog()
        if len(cat) < 2:
            return {"snapshot": vid, "recovery": {"verdict": None,
                    "reason": "no prior version to recover"}, "fail_open": False}
        target_id = cat[-2].version_id  # the pre-crash version
        target = store.reconstruct(target_id)
        col.emit({"ts": ts, "type": "crash_detected", "recovery_id": vid})
        col.emit({"ts": ts, "type": "recovery_started", "recovery_id": vid,
                  "target": target_id})
        sc = G4.score_recovery(target, current_description)
        gate = G4.acceptance_gate(sc)
        col.emit({"ts": ts, "type": "acceptance_scored", "recovery_id": vid,
                  "verdict": gate.verdict, "missing_elements": gate.missing_elements})
        col.emit({"ts": ts, "type": "recovery_completed", "recovery_id": vid,
                  "verdict": gate.verdict, "duration_s": 0.0,
                  "missing_elements": gate.missing_elements})
        return {"snapshot": vid, "recovery": {
            "target": target_id, "verdict": gate.verdict,
            "allow_complete": gate.allow_complete,
            "missing_elements": gate.missing_elements}, "fail_open": False}
    except Exception as exc:  # noqa: BLE001 -- fail-open: never block session start
        return {"fail_open": True, "error": str(exc)}


def on_ram_threshold(
    state_dir: Path | str,
    current_description: dict,
    ts: str | None = None,
    retries: int = 1,
) -> dict:
    """I2: force a snapshot before a memory-pressure advisory, validate it via G4
    (reconstructs + scores clean), log it. Retry once, then honest fallback."""
    last_err = ""
    for _ in range(retries + 1):
        try:
            store = G3.SessionVersionStore(state_dir)
            col = G5.RecoveryEventCollector(state_dir)
            vid = store.record(current_description, reason="ram_threshold", ts=ts)
            recon = store.reconstruct(vid)  # integrity: must reconstruct exactly
            gate = G4.acceptance_gate(G4.score_recovery(current_description, recon))
            if gate.verdict == G4.RECOVERED:
                col.emit({"ts": ts, "type": "version_selected", "recovery_id": vid,
                          "verdict": gate.verdict})
                return {"snapshot": vid, "valid": True,
                        "advisory": "snapshot seguro guardado", "fail_open": False}
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            continue
    return {"valid": False, "advisory": "snapshot no validado -- proceder con cautela",
            "fail_open": True, "error": last_err}
