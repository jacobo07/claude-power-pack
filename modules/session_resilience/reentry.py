"""G6 runtime -- Reentry recorder: wires an ungraceful startup into G5 + G4.

The extension already RELAUNCHES panes on a cold start (restore_guard.js). This
module does the part the G6 dataset 6.7 names but that had no code: when startup
is classified ``ungraceful-shutdown`` (power_beacon.classify_startup), record the
recovery as a first-class event stream (G5) and produce a G4 acceptance verdict
on the reentry plan. It NEVER relaunches a pane itself -- that is the extension's
job; this observes and judges, so "G4 RECOVERED + G5 ungraceful event" (the G6
done-gate) becomes true and inspectable.

Honest scope of the headless verdict: a cold-start reentry governs the TERMINAL
board (which conversations come back in which cwd), not the editor surface (tabs/
scroll are the extension/host leg, Owner-run visual gate). So the verdict here is
capability-scoped to {windows, terminals, conversations}: every *live* pane in
pane_map is the reference; every live pane that is actually RESTORABLE (has a
session id, cwd and resume command) is the observed set. A live pane that cannot
be restored is a real miss -> PARTIAL/FAILED, never silently RECOVERED.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from . import epoch as epoch_mod
from . import power_beacon
from .acceptance import (
    FAILED,
    PARTIAL,
    RECOVERED,
    acceptance_gate,
    classify as g4_classify,
    score_recovery,
)
from .telemetry import RecoveryEventCollector

# A cold-start reentry can only govern the terminal board headlessly; editor
# dimensions are the host/extension leg (capability-aware acceptance, Dataset 04).
REENTRY_DIMENSIONS = frozenset({"windows", "terminals", "conversations"})

CAUSE = "ungraceful-shutdown"


def _now_iso(now: str | None) -> str:
    return now if now else datetime.now(timezone.utc).isoformat(timespec="seconds")


def live_panes(pane_map: dict) -> list[dict]:
    return [p for p in (pane_map.get("panes") or []) if p and p.get("live")]


def reference_panes(state_dir: Path | str, pane_map: dict) -> list[dict]:
    """The board as it stood BEFORE the interruption.

    Prefers the snapshot pinned by the open epoch -- the last topology recorded
    while the session was alive. Falls back to the live panes of the current
    pane_map only when no epoch pinned anything (no history yet): that fallback
    cannot witness a loss, and it is the pre-epoch behaviour, kept solely so a
    host with no snapshot history still produces a verdict rather than crashing.
    """
    pinned = epoch_mod.reference_path(state_dir)
    if pinned is not None:
        try:
            data = json.loads(pinned.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError):
            return live_panes(pane_map)
        return live_panes(data)
    return live_panes(pane_map)


def is_restorable(pane: dict) -> bool:
    """A pane the cold-start guard can actually relaunch: a session id, a cwd,
    and a resume command. Mirrors restore_guard.js's dedupe-by-sessionId intent
    without re-implementing its decision (which window to act in)."""
    return bool(pane.get("sessionId")) and bool(pane.get("cwd")) and bool(pane.get("resumeCmd"))


def _desc_from_panes(panes: list[dict]) -> dict:
    """A minimal canonical state-description (models.py shape) whose terminal
    board is these panes -- so G4's terminals/conversations extractors can score
    reference vs observed deterministically."""
    terminals = [
        {
            "pane_id": str(p.get("sessionId") or p.get("cwd")),
            "cwd": str(p.get("cwd")),
            "conversation_id": str(p.get("sessionId") or ""),
        }
        for p in panes
    ]
    return {
        "schema_version": 1,
        "captured_at": "reentry",
        "windows": [{
            "window_id": "reentry",
            "workspace_path": "reentry",
            "foreground": True,
            "terminals": terminals,
            "editor": {},
        }],
    }


def record_reentry(state_dir: Path | str, classification: dict, pane_map: dict,
                   now: str | None = None,
                   collector: RecoveryEventCollector | None = None) -> dict:
    """If ``classification`` is ungraceful-shutdown, emit the recovery event
    stream to G5 and return the G4 verdict on the reentry plan. Otherwise a
    no-op (returns the class with verdict=None). Fail-open is the caller's
    concern (the hub wraps this); here we surface real verdicts."""
    cls = classification.get("class")
    result = {"class": cls, "verdict": None, "recovered": None,
              "expected_panes": 0, "restorable_panes": 0, "missing": []}
    if cls != power_beacon.UNGRACEFUL:
        return result

    col = collector or RecoveryEventCollector(state_dir=Path(state_dir))
    ts = _now_iso(now)
    rid = "reentry-" + ts
    # The reference is the board we HAD, not the board that survived. Taking the
    # live panes of the post-crash pane_map (what this did before) asks "can we
    # relaunch what is left?" -- a question whose answer is yes even when most of
    # the board is gone. The pinned epoch reference asks the only question that
    # matters: can we get back what we had before the lights went out?
    #
    # This verdict judges the PLAN (every pre-crash pane has a relaunch path), not
    # the RESULT (they came back) -- reentry runs before the extension relaunches
    # anything, so scoring against what is live right now would fail a plan that has
    # not executed yet. tools/recovery_verdict.py judges the result later, against
    # the same pin.
    live = reference_panes(state_dir, pane_map)
    restorable = [p for p in live if is_restorable(p)]

    col.emit({"ts": ts, "type": "recovery_started", "recovery_id": rid,
              "cause": CAUSE, "expected_panes": len(live)})
    for p in restorable:
        col.emit({"ts": ts, "type": "pane_restored", "recovery_id": rid,
                  "conversation_id": p.get("sessionId"), "cwd": p.get("cwd"),
                  "repo": p.get("repo", "")})

    reference = _desc_from_panes(live)
    observed = _desc_from_panes(restorable)
    scorecard = score_recovery(reference, observed)
    verdict, missing = g4_classify(scorecard, host_capabilities=REENTRY_DIMENSIONS)
    gate = acceptance_gate(scorecard, host_capabilities=REENTRY_DIMENSIONS)

    col.emit({"ts": ts, "type": "acceptance_scored", "recovery_id": rid,
              "verdict": verdict, "missing_elements": missing})
    col.emit({"ts": ts, "type": "recovery_completed", "recovery_id": rid,
              "cause": CAUSE, "verdict": verdict, "missing_elements": missing,
              "duration_s": 0.0})

    result.update({
        "verdict": verdict,
        "recovered": verdict == RECOVERED,
        "allow_complete": gate.allow_complete,
        "expected_panes": len(live),
        "restorable_panes": len(restorable),
        "missing": missing,
        "recovery_id": rid,
    })
    return result


def _read_pane_map(state_dir: Path | str) -> dict:
    p = Path(state_dir) / "pane_map.json"
    if not p.is_file():
        return {"panes": []}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (ValueError, OSError):
        return {"panes": []}


def _main(argv=None) -> int:  # pragma: no cover - hub/manual entry point
    import argparse
    ap = argparse.ArgumentParser(description="G6 reentry recorder")
    ap.add_argument("--state-dir", default=str(Path.home() / ".claude" / "state"))
    ap.add_argument("--live-terminals", type=int,
                    default=int(os.environ.get("PP_LIVE_TERMS", "0")))
    a = ap.parse_args(argv)
    cls = power_beacon.classify_startup(a.state_dir, a.live_terminals)
    if cls["class"] != power_beacon.UNGRACEFUL:
        print(json.dumps({"class": cls["class"], "action": "none"}))
        return 0
    res = record_reentry(a.state_dir, cls, _read_pane_map(a.state_dir))
    print(json.dumps(res))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_main())
