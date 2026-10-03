#!/usr/bin/env python3
"""Economic rollover evaluation -- spec vault/specs/economic-rollover-trigger.md.

rollover.py's shadow judges a session once, at the 40 % snapshot, without the session's start
head, so its work-boundary test needs a clean tracked tree -- which a shared tree never has
(2026-10-02: 110 of 126 decisions "worth it, but not at a work boundary"). This evaluates the
same capsule and the same break-even policy with the start head the watchdog recorded, so a
commit made since the session began is a boundary, and writes the decision where the watchdog
reads it: <state>/decisions/<session>.json, stamped with the head it judged.

The policy (decide, at_boundary, completeness, safe_to_forget) stays in rollover.py; this file
only supplies the missing argument and the hand-off. Spawned detached by context-watchdog.py
(pythonw, no console). Never raises out of main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve().parent


def _rollover():
    if "rollover" in sys.modules:
        return sys.modules["rollover"]
    spec = importlib.util.spec_from_file_location("rollover", _HERE / "rollover.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rollover"] = mod
    spec.loader.exec_module(mod)
    return mod


def decision_path(session_id: str, state_dir: Optional[Path] = None) -> Path:
    ro = _rollover()
    return Path(state_dir or ro.STATE_DIR) / "decisions" / f"{session_id}.json"


def evaluate(session_id: str, cwd: str, transcript: Optional[str], used_pct: Optional[float],
             start_head: Optional[str], state_dir: Optional[Path] = None) -> dict:
    """Judge this session now, with its start head; record the row and the decision file."""
    ro = _rollover()
    cap = ro.compile_capsule(session_id, cwd, transcript)
    receipt = ro.seal(cap, state_dir)
    comp = ro.completeness(cap)
    stf = ro.safe_to_forget(receipt, comp)
    usage = cap["usage"]
    boot = len(ro.bootstrap(cap))
    ratio = (ro.price_ratio(usage.get("model", "")) if usage.get("state") == "OK"
             else ro._unknown("no usage"))
    ev, reh = ro.horizon_evidence(state_dir)
    dec = ro.decide(usage, boot, ro.at_boundary(cap["repo"], start_head), used_pct, ratio,
                    horizon=ev, rehydration=reh)
    head = (cap.get("repo") or {}).get("head")
    row = {"session_id": session_id, "cwd": cwd, "tier": "econ", "mode": "economic",
           "start_head": start_head, "head": head, "decision": dec, "capsule": receipt,
           "completeness": comp, "safe_to_forget": stf["verdict"], "refusals": stf["reasons"],
           "obligations": len(cap.get("obligations") or []), "bootstrap_chars": boot}
    ro.ledger("shadow_candidate", state_dir, **row)
    out = {"session_id": session_id, "head": head, "start_head": start_head,
           "ts": time.time(), "decision": dec}
    p = decision_path(session_id, state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    ro._atomic_write(p, json.dumps(out).encode("utf-8"))
    if dec.get("economics") == ro.UNKNOWN:      # the horizon was NEEDED and missing/expired, not merely absent
        out["prior_refresh"] = refresh_prior(state_dir)    # after the decision is on disk: never delays it
    return out


def refresh_prior(state_dir: Optional[Path] = None) -> str:
    """THE refresher of the horizon prior (audit ccp-s16-1 G4): run here, detached, when a decision
    found it missing or expired. One builder at a time (non-blocking lock; a busy lock means another
    evaluation is already building); the build reads the usage index and transcripts (~3 min)."""
    ro = _rollover()
    base = Path(state_dir or ro.STATE_DIR)
    fd = None
    try:
        base.mkdir(parents=True, exist_ok=True)
        fd = os.open(base / "horizon-prior.lock", os.O_RDWR | os.O_CREAT)
        if not ro._lock_try(fd):
            return "busy"
        sys.path.insert(0, str(_HERE))
        import rollover_replay
        rollover_replay.write_prior(base)
        return "written"
    except Exception as exc:  # detached: report in the row, never crash
        return f"failed: {type(exc).__name__}: {exc}"[:200]
    finally:
        if fd is not None:
            os.close(fd)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--session", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--transcript")
    ap.add_argument("--used-pct", type=float)
    ap.add_argument("--start-head", required=True)
    a = ap.parse_args(argv)
    try:
        out = evaluate(a.session, a.cwd, a.transcript, a.used_pct, a.start_head)
    except Exception as exc:  # detached: report, never crash a console that does not exist
        print(f"rollover_econ: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"head": out["head"], "decision": out["decision"]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
