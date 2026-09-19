"""V-TWOPANE-* gates for the live two-pane exactness drill (Phase 1).

Three exit codes, not two:

  0  every gate passed
  1  a gate FAILED -- a verdict about the subject
  2  HARNESS-FAILED -- the evidence file, or a transcript it names, is missing or
     unreadable, so this run judged nothing. A verifier that could not judge its
     subject must never present as a verdict about that subject, and a run that
     skipped its subject must not read like a clean one.

Evidence comes from a real drill run (`tools/two_pane_drill.py`), never from a
fixture: the whole point of the phase is that the extension, the daemon and the
transcripts are the real ones.

Usage:  python tools/test_two_pane_exactness.py --runid <runid>
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNS = Path(os.environ.get("TEMP", "/tmp")) / "pp-two-pane-drill"

passes = fails = 0


def _ok(gate: str, evidence: str) -> None:
    global passes
    passes += 1
    print(f"PASS {gate}: {evidence}")


def _fail(gate: str, evidence: str) -> None:
    global fails
    fails += 1
    print(f"FAIL {gate}: {evidence}")


def _harness(why: str) -> int:
    print(f"HARNESS-FAILED: {why}")
    return 2


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runid", required=True)
    args = ap.parse_args(argv)

    manifest = RUNS / args.runid / "manifest.json"
    if not manifest.is_file():
        return _harness(f"no drill evidence at {manifest} -- run tools/two_pane_drill.py first")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return _harness(f"{manifest} unreadable: {exc.__class__.__name__}: {exc}")

    pane = (data.get("panes") or {}).get("A")
    if not pane:
        return _harness("pane A was never armed")
    for key in ("transcript", "nonce", "t0"):
        if key not in pane:
            return _harness(f"pane A has no {key} -- it was armed but never fired")
    transcript = Path(pane["transcript"])
    if not transcript.is_file():
        return _harness(f"pane A's transcript is gone: {transcript}")

    lr = _load("gsd_long_run")
    # The real three-part rule, imported rather than reimplemented: a second copy
    # would agree with the first on the day it was written and not afterwards.
    got = lr.user_issued_command_since(transcript, pane["nonce"], pane["t0"])
    if got:
        _ok("V-TWOPANE-A-RECEIVED",
            f"{pane['nonce']} appears in {transcript.name} after t0={pane['t0']}")
    else:
        _fail("V-TWOPANE-A-RECEIVED",
              f"{pane['nonce']} absent from {transcript.name} after t0={pane['t0']}")

    total = passes + fails
    print(f"TWOPANE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
