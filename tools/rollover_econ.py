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
    dec = ro.decide(usage, boot, ro.at_boundary(cap["repo"], start_head), used_pct, ratio)
    head = (cap.get("repo") or {}).get("head")
    row = {"session_id": session_id, "cwd": cwd, "tier": "econ", "mode": "economic",
           "start_head": start_head, "head": head, "decision": dec, "capsule": receipt,
           "completeness": comp, "safe_to_forget": stf["verdict"], "refusals": stf["reasons"],
           "bootstrap_chars": boot}
    ro.ledger("shadow_candidate", state_dir, **row)
    out = {"session_id": session_id, "head": head, "start_head": start_head,
           "ts": time.time(), "decision": dec}
    p = decision_path(session_id, state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    ro._atomic_write(p, json.dumps(out).encode("utf-8"))
    return out


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
