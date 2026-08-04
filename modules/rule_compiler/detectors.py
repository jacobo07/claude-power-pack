#!/usr/bin/env python3
"""Replay entry points: run a rule's REAL detector against a recorded incident.

`counterfactual.py` needs each claim to name an argv it can execute with the
preserved incident on stdin. This module is that argv, and nothing more. Each
subcommand is a thin carrier to the shipped mechanism -- it imports the live
detector and calls it. It never re-implements the check, because a probe that
reproduces the logic would keep passing after the real path broke, which is the
failure the harness exists to detect.

    echo "<incident>" | python -m modules.rule_compiler.detectors novelty

Prints FIRED / SILENT and exits 0. The verdict belongs to the harness; a
detector that raises is reported as neither, so a crash can never read as a
clean SILENT.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:            # runnable as a bare script too
    sys.path.insert(0, str(_PP_ROOT))

FIRED = "FIRED"
SILENT = "SILENT"
ERROR = "DETECTOR_ERROR"


def _novelty(stdin_text: str) -> tuple:
    """HR-NOVELTY-001 -- the 13-question novelty proof gate."""
    from modules.spec_gate.gate import check_novelty_gate
    r = check_novelty_gate(stdin_text)
    return (FIRED, str(r.matched)) if r.applies else (SILENT, "no signal")


def _stalled(stdin_text: str) -> tuple:
    """HR-STALLED-SESSION-ADVISORY-001 -- the loop-boundedness advisory.

    The incident is a pane record; the rule's whole point is that the advisory
    is VISIBLE and never a kill, so 'fired' means an advisory was produced.
    """
    from modules.cognitive_os.process_governor import PaneProc, loop_advisory
    rec = json.loads(stdin_text.lstrip("﻿"))
    # Only fields the live dataclass declares. An incident recorded against an
    # older shape must not crash the replay -- the harness would then read the
    # crash as "this rule does not cover its origin".
    fields = PaneProc.__dataclass_fields__
    unknown = sorted(set(rec) - set(fields))
    if unknown:
        raise ValueError(f"incident names fields PaneProc does not declare: {unknown}")
    adv = loop_advisory(PaneProc(**rec))
    if adv is None:
        return SILENT, "no advisory (fail-open silence)"
    return FIRED, f"{adv['level']}: {adv['message'][:120]}"


DETECTORS = {
    "novelty": _novelty,
    "stalled": _stalled,
}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] not in DETECTORS:
        print(f"usage: detectors <{'|'.join(sorted(DETECTORS))}>  (incident on stdin)")
        return 2
    try:
        text = sys.stdin.read()
    except (OSError, UnicodeError) as e:
        print(f"{ERROR}: could not read incident from stdin: {e}")
        return 0
    try:
        verdict, evidence = DETECTORS[args[0]](text)
    except Exception as e:  # noqa: BLE001 -- a crash must not read as SILENT
        print(f"{ERROR}: {type(e).__name__}: {e}")
        return 0
    print(f"{verdict}: {evidence}")
    return 0


__all__ = ["DETECTORS", "FIRED", "SILENT", "ERROR", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
