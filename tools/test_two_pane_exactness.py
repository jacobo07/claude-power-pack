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


def gates_unit(drill, lr) -> None:
    """Rules the drill's identity rests on, driven without a live subject.

    These exist because every one of them was wrong once, on this host, in a
    way no fixture would have surfaced (2026-09-19).
    """
    import json as _json
    import os as _os
    import tempfile as _tempfile
    import time as _time

    nonce = "DRILL-A-unitgate"
    tmp = Path(_tempfile.mkdtemp(prefix="twopane-unit-"))

    def transcript(rows) -> Path:
        p = tmp / f"t{len(list(tmp.glob('*.jsonl')))}.jsonl"
        p.write_text("\n".join(_json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        return p

    # NOW, not a fixed date. A stale timestamp is excluded by the TIME bound, so
    # the text predicate is never reached and the gate below passes for a reason
    # other than the one it names -- measured 2026-09-19, a mutation that made
    # `observe` count a mere mention survived exactly that way.
    now_iso = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())
    typed = transcript([{"type": "user", "timestamp": now_iso,
                         "message": {"role": "user", "content":
                                     f"Reply with a single line beginning {nonce} and nothing else."}}])
    echoed = transcript([{"type": "user", "toolUseResult": {"stdout": nonce},
                          "timestamp": "2026-09-19T10:00:00Z",
                          "message": {"role": "user", "content":
                                      [{"type": "tool_result", "content": nonce}]}}])
    # The case only the toolUseResult guard catches: a tool result whose content
    # is a PLAIN STRING is shaped exactly like a typed prompt. Without this
    # fixture the guard is redundant with the block-shape check and a mutation
    # removing it survives -- measured 2026-09-19, it did.
    echoed_str = transcript([{"type": "user", "toolUseResult": {"stdout": nonce},
                              "timestamp": "2026-09-19T10:00:00Z",
                              "message": {"role": "user", "content": nonce}}])
    if not drill._carries_nonce(echoed_str, nonce):
        _ok("V-TWOPANE-NONCE-IGNORES-STRING-TOOL-RESULT",
            "a tool result whose content is a plain string is still not a keystroke")
    else:
        _fail("V-TWOPANE-NONCE-IGNORES-STRING-TOOL-RESULT",
              "a string-bodied tool result counted as a typed row")

    # A tool result IS a type="user" row. Counting by type reads an echo as an
    # event -- measured: a control built that way reported a keystroke into the
    # Owner's live pane that never happened.
    if drill._carries_nonce(typed, nonce) and not drill._carries_nonce(echoed, nonce):
        _ok("V-TWOPANE-NONCE-IGNORES-TOOL-RESULT", "typed row counts, tool_result does not")
    else:
        _fail("V-TWOPANE-NONCE-IGNORES-TOOL-RESULT",
              f"typed={drill._carries_nonce(typed, nonce)} echoed={drill._carries_nonce(echoed, nonce)}")

    # arm's predicate must stay WEAKER than observe's: the operator's own prompt
    # CONTAINS the nonce, so if observe used the same test the drill would pass
    # on its own setup.
    since = _time.time() - 3600
    prompt_only = lr.user_issued_command_since(typed, nonce, since)
    delivered = transcript([{"type": "user",
                             "timestamp": _time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                         _time.gmtime(_time.time())),
                             "message": {"role": "user", "content": nonce}}])
    real = lr.user_issued_command_since(delivered, nonce, since)
    if (not prompt_only) and real:
        _ok("V-TWOPANE-OBSERVE-IGNORES-THE-SETUP-PROMPT",
            "a prompt that merely mentions the nonce is not a delivery; a line that IS it, is")
    else:
        _fail("V-TWOPANE-OBSERVE-IGNORES-THE-SETUP-PROMPT",
              f"prompt_counted={prompt_only} delivered_counted={real}")

    # Addressability: a subject no window's terminal can reach must fail BEFORE
    # fire spends its timeout discovering it. Positive control first, or a
    # sweep that finds nothing reads exactly like a clean verdict.
    mine = drill._owning_window(_os.getpid())
    system_pid = drill._owning_window(4)          # the System process: no terminal, ever
    if mine is not None and system_pid is None:
        _ok("V-TWOPANE-ADDRESSABILITY-DISCRIMINATES",
            f"this process is owned by {mine['registry']} (terminal {mine['pid']}); pid 4 is not")
    else:
        _fail("V-TWOPANE-ADDRESSABILITY-DISCRIMINATES",
              f"self={mine} system={system_pid} -- the check cannot tell the two apart")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runid", default="",
                    help="a real drill run's id; omit to run only the unit gates")
    args = ap.parse_args(argv)

    drill = _load("two_pane_drill")
    lr = sys.modules.get("gsd_long_run") or _load("gsd_long_run")
    gates_unit(drill, lr)

    if not args.runid:
        total = passes + fails
        print(f"TWOPANE_PASS={passes}/{total}  threshold={total}/{total}  (unit gates only, "
              f"no live drill evidence was judged)")
        return 0 if fails == 0 else 1

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

    # The real three-part rule, imported rather than reimplemented: a second copy
    # would agree with the first on the day it was written and not afterwards.
    got = lr.user_issued_command_since(transcript, pane["nonce"], pane["t0"])
    if got:
        _ok("V-TWOPANE-A-RECEIVED",
            f"{pane['nonce']} appears in {transcript.name} after t0={pane['t0']}")
    else:
        _fail("V-TWOPANE-A-RECEIVED",
              f"{pane['nonce']} absent from {transcript.name} after t0={pane['t0']}")

    # Exactness is a claim about TWO panes. "A received it" alone is delivery.
    b = (data.get("panes") or {}).get("B")
    if not b:
        return _harness("no pane B recorded -- the run cannot speak about exactness, "
                        "only about delivery")
    b_transcript = Path(b["transcript"])
    if not b_transcript.is_file():
        return _harness(f"pane B's transcript is gone: {b_transcript}")
    b_got = lr.user_issued_command_since(b_transcript, b["nonce"], b["t0"])
    if not b_got:
        _ok("V-TWOPANE-B-UNTOUCHED",
            f"{b['nonce']} never appears in {b_transcript.name} after t0={b['t0']} "
            f"({b.get('role', 'second pane')})")
    else:
        _fail("V-TWOPANE-B-UNTOUCHED",
              f"{b['nonce']} reached {b_transcript.name} -- the line went to a pane that "
              "did not own the request")

    total = passes + fails
    print(f"TWOPANE_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
