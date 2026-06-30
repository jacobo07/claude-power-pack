#!/usr/bin/env python3
"""prelaunch.py -- W6 core: one process that runs W1/W4/W5/W2 and emits JSON.

The orchestrator (kclaude.ps1) calls this ONCE before launching claude, instead
of spawning python four times (4x interpreter startup would blow the <2s
overhead budget). Each feature runs in its own thread with an INDIVIDUAL timeout
(W1=1.0s, W4=0.5s, W5=0.5s, W2=1.0s) and they run CONCURRENTLY, so wall-time is
the longest single timeout (~1s), not the sum. A feature that overruns or raises
is abandoned and the others still complete -- fail-open, never blocks the launch.

Cognitive OS:
  CO-08 (gate)       -- the hard hot-session-cap verdict for a NEW pane; the only
                        field the orchestrator may act on to BLOCK (rung-3).
  CO-00 (resume_gate)-- the effective-context advisory for the RESUME target; an
                        honest rung-2 warning (a block on resume is counter-
                        productive -- a session must be opened to be /compact-ed).
Both fail-open: an errored/timed-out gate yields a benign proceed/no-advice.

Output (stdout, one JSON object):
  {
    "advisories": [...], "coord": {...}, "resume": {...}, "known_sids": [...],
    "gate":        {"verdict":"proceed"|"refuse","reasons":[...],"satisfy":[...],
                    "hot_count":int,"same_repo_count":int,"cap":int},
    "resume_gate": {"band":str,"advise":bool,"message":str|null}
  }
"""
from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FTimeout
from pathlib import Path

_PP_ROOT = Path(__file__).resolve().parents[2]
if str(_PP_ROOT) not in sys.path:
    sys.path.insert(0, str(_PP_ROOT))

_GATE_PROCEED = {"verdict": "proceed", "reasons": [], "satisfy": [],
                 "hot_count": 0, "same_repo_count": 0, "cap": 0}
_RESUME_GATE_NONE = {"band": "UNKNOWN", "advise": False, "message": None}


def _res(fut, timeout, default):
    """Collect a pre-submitted future; default on timeout/exception."""
    try:
        return fut.result(timeout=timeout)
    except (FTimeout, Exception):  # noqa: BLE001
        return default


def _w1(cwd):
    from modules.wrapper.turn_counter import check
    return check(cwd)


def _w4(cwd):
    from modules.wrapper.repo_coordinator import coordinate, parallel_burn
    d = coordinate(cwd)
    pb = parallel_burn(cwd)   # D2: same-repo parallel large-prompt burn pattern
    return {"active": d.active, "warning": d.warning,
            "default_resume": d.default_resume, "source": d.source,
            "candidates": [c.get("session_id") for c in (d.candidates or [])],
            "burn_warning": pb.warning, "burn_panes": pb.panes}


def _w5(cwd, description):
    from modules.wrapper.cost_gate import cost_gate
    g = cost_gate(cwd, description=description)
    return g.lines


def _w2(cwd):
    from modules.wrapper.auto_resumer import get_resume
    r = get_resume(cwd)
    return {"resume_arg": r.resume_arg, "session_id": r.session_id,
            "source": r.source}


def _known_sids(cwd):
    """sids already on this cwd before launch (for W3 new-sid detection)."""
    from modules.wrapper.auto_resumer import list_candidates
    return [c["session_id"] for c in list_candidates(cwd)]


def _gate(cwd):
    """CO-08 hard hot-session cap verdict for a NEW pane on this cwd. The only
    field the orchestrator may act on to block; fail-open to proceed."""
    from modules.cognitive_os.scheduler import admit
    v = admit(cwd, is_new=True)
    return {"verdict": v.verdict, "reasons": v.reasons, "satisfy": v.satisfy,
            "hot_count": v.hot_count, "same_repo_count": v.same_repo_count,
            "cap": v.cap}


def _resume_gate(cwd, resume):
    """CO-00 effective-context advisory for the RESUME target (rung-2). Fast:
    one bridge read + one stat. Fail-open -> no advice."""
    sid = (resume or {}).get("session_id")
    if not sid:
        return dict(_RESUME_GATE_NONE)
    try:
        from modules.cognitive_os.context import resume_advisory
        a = resume_advisory(sid, cwd)
        return {"band": a.band, "advise": a.advise, "message": a.message}
    except Exception:  # noqa: BLE001 -- fail-open
        return dict(_RESUME_GATE_NONE)


def run(cwd, description=None):
    """All features run CONCURRENTLY (independent disk reads) so wall-time is
    the longest single timeout (~1s), not their sum -- keeps launch overhead
    under 2s while honoring each feature's individual timeout."""
    ex = ThreadPoolExecutor(max_workers=6)
    try:
        f_w1 = ex.submit(_w1, cwd)
        f_w4 = ex.submit(_w4, cwd)
        f_w5 = ex.submit(_w5, cwd, description)
        f_w2 = ex.submit(_w2, cwd)
        f_known = ex.submit(_known_sids, cwd)
        f_gate = ex.submit(_gate, cwd)
        w1 = _res(f_w1, 1.0, None)
        coord = _res(f_w4, 1.0, {"active": False, "warning": None,
                                 "default_resume": None, "source": "timeout",
                                 "burn_warning": None})
        w5 = _res(f_w5, 1.0, [])
        resume = _res(f_w2, 1.0, {"resume_arg": None, "session_id": None,
                                  "source": "timeout"})
        known = _res(f_known, 0.5, [])
        gate = _res(f_gate, 1.0, dict(_GATE_PROCEED))
    finally:
        ex.shutdown(wait=False)  # never block on a hung feature thread
    # CO-00 resume advisory: depends on the resolved resume target, so computed
    # after collection (fast: bridge read + stat). Fail-open inside _resume_gate.
    resume_gate = _resume_gate(cwd, resume)
    burn = (coord or {}).get("burn_warning")
    advisories = ([w1] if w1 else []) + list(w5 or []) + ([burn] if burn else [])
    return {"advisories": advisories, "coord": coord, "resume": resume,
            "known_sids": known, "gate": gate, "resume_gate": resume_gate}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--cwd", default=None)
    ap.add_argument("--description", default=None)
    args = ap.parse_args(argv)
    try:
        out = run(args.cwd or os.getcwd(), args.description)
    except Exception:  # noqa: BLE001 -- absolute fail-open
        out = {"advisories": [], "coord": {"active": False, "warning": None,
               "default_resume": None, "source": "error"},
               "resume": {"resume_arg": None, "session_id": None,
                          "source": "error"}, "known_sids": [],
               "gate": dict(_GATE_PROCEED), "resume_gate": dict(_RESUME_GATE_NONE)}
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stdout.flush()
    os._exit(0)  # bounded exit: never block process teardown on a stray thread


if __name__ == "__main__":
    main()
