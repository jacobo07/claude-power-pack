#!/usr/bin/env python
"""V-CTRUTH-* -- a compaction is claimed only when the transcript shows one.

Spec: vault/specs/exact-target-continuation.md (C1).

INCIDENT (2026-09-18, session 8178f7d0). The watchdog told the model
"COMPACTION LANDED" at 14:16:53 UTC. The last compaction boundary in that
transcript was 2026-09-17 13:19; the marker was armed at 20:45 that day. The
session had merely been restarted, and a resumed session reads ~17% context.
The predicate was "context below the rearm floor + marker + no flags", which a
restart satisfies. These gates hold the replacement predicate: a transcript row
`type=system, subtype=compact_boundary` newer than the cycle reference.

Hermetic: synthetic session ids, a throwaway ledger dir, transcripts under a
temp dir, the trigger/daemon calls replaced by recorders (Stop B must never
drop a real flag from a test).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

os.environ["GSD_LONG_RUN_STATE_DIR"] = tempfile.mkdtemp(prefix="ctruth-state-")

ROOT = Path(__file__).resolve().parents[1]
WATCHDOG = ROOT / "modules" / "zero-crash" / "hooks" / "context-watchdog.py"
TOOLS = ROOT / "tools"
TMP = Path(tempfile.mkdtemp(prefix="ctruth-tx-"))

# What the reading MEANS, pinned absolutely: the incident's own figure.
RESTARTED_SESSION_PCT = 17.0

passes = 0
fails = 0


def check(gate: str, cond: bool, ev: str) -> None:
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def iso(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(epoch)) + ".000Z"


def boundary(epoch: float) -> dict:
    """Shape copied from a real row (8178f7d0 line 9018), trimmed."""
    return {"parentUuid": None, "type": "system", "subtype": "compact_boundary",
            "content": "Conversation compacted", "level": "info",
            "compactMetadata": {"trigger": "auto", "preTokens": 739212, "postTokens": 22131},
            "uuid": str(uuid.uuid4()), "timestamp": iso(epoch)}


def quoted(epoch: float) -> dict:
    """An assistant turn QUOTING a boundary row -- this very estate does that."""
    text = 'the row reads {"type":"system","subtype":"compact_boundary"} here'
    return {"type": "assistant", "timestamp": iso(epoch),
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def write_tx(session: str, rows) -> Path:
    t = TMP / f"{session}.jsonl"
    lines = [{"type": "system", "cwd": str(ROOT)}] + list(rows)
    t.write_text("\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
    return t


def sid() -> str:
    return f"ctruth-{uuid.uuid4().hex[:12]}"


lr = load(TOOLS / "gsd_long_run.py", "gsd_long_run")
mk = load(TOOLS / "gsd_autorun_marker.py", "gsd_autorun_marker")
wd = load(WATCHDOG, "ctxwd_ctruth")

_calls: list = []
wd._write_trigger_flag = lambda *a, **k: _calls.append(("flag", k)) or "flag"
wd._spawn_daemon = lambda *a, **k: _calls.append(("spawn", k)) or True


def stamp(s: str) -> None:
    (Path(tempfile.gettempdir()) / wd.ORCH_THROTTLE_FLAG.format(session_id=s)).write_text(
        str(time.time()), encoding="utf-8")


def run(s: str, tp) -> dict:
    os.environ["_TEST_CONTEXT_PCT"] = str(RESTARTED_SESSION_PCT)
    try:
        return wd.run({"session_id": s, "cwd": str(ROOT), "transcript_path": str(tp or "")}) or {}
    finally:
        os.environ.pop("_TEST_CONTEXT_PCT", None)


def events(s: str) -> list[dict]:
    return lr.ledger_events(s)


def names(s: str) -> list[str]:
    return [e["event"] for e in events(s)]


def cleanup(s: str) -> None:
    for f in (wd.RESUME_ARMED_FLAG, wd.RESUME_DONE_FLAG, wd.RESUME_CONFIRMED_FLAG,
              wd.ADVISORY_FLAG, wd.SNAPSHOT_FLAG):
        wd._clear_flag(s, f)
    mk.clear_marker(s)


def armed(s: str) -> bool:
    return wd._flag_exists(s, wd.RESUME_ARMED_FLAG)


# ------------------------------------------------------------------ observer unit
def gates_observer() -> None:
    now = time.time()
    tp = write_tx(sid(), [boundary(now - 7200), quoted(now + 60), boundary(now - 60)])
    obs = lr.compaction_observed(tp, now - 3600)
    check("V-CTRUTH-OBS-PICKS-LATEST-REAL",
          obs.get("state") == "observed" and obs.get("boundary_ts") == iso(now - 60),
          f"{obs}")
    obs = lr.compaction_observed(tp, now)
    check("V-CTRUTH-OBS-OLDER-IS-UNOBSERVED", obs.get("state") == "unobserved", f"{obs}")
    obs = lr.compaction_observed(TMP / "no-such.jsonl", 0.0)
    check("V-CTRUTH-OBS-MISSING-IS-UNREADABLE", obs.get("state") == "unreadable", f"{obs}")
    tp2 = write_tx(sid(), [quoted(now + 60)])
    obs = lr.compaction_observed(tp2, 0.0)
    check("V-CTRUTH-OBS-QUOTE-IS-NOT-BOUNDARY", obs.get("state") == "unobserved", f"{obs}")


# ------------------------------------------------------------------ watchdog
def gates_watchdog() -> None:
    # The incident, exactly: armed AFTER the last boundary, context low.
    s = sid(); stamp(s)
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        tp = write_tx(s, [boundary(time.time() - 7 * 3600)])
        before = len(_calls)
        out = run(s, tp)
        check("V-CTRUTH-INCIDENT-NO-LANDED",
              out.get("decision") != "block" and not armed(s) and len(_calls) == before,
              f"decision={out.get('decision')!r} armed={armed(s)} "
              f"reason={str(out.get('reason', ''))[:70]!r}")
        check("V-CTRUTH-INCIDENT-LEDGERED",
              "compaction_unobserved" in names(s) and "resume_requested" not in names(s),
              f"events={names(s)}")
        run(s, tp)
        check("V-CTRUTH-UNOBSERVED-LEDGERED-ONCE",
              names(s).count("compaction_unobserved") == 1, f"events={names(s)}")
    finally:
        cleanup(s)

    # No transcript at all: nothing can be observed, nothing is claimed.
    s = sid(); stamp(s)
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        out = run(s, "")
        check("V-CTRUTH-NO-TRANSCRIPT-NO-LANDED",
              out.get("decision") != "block" and not armed(s), f"decision={out.get('decision')!r}")
    finally:
        cleanup(s)

    # Quoted text is not a compaction.
    s = sid(); stamp(s)
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        out = run(s, write_tx(s, [quoted(time.time() + 5)]))
        check("V-CTRUTH-QUOTE-NO-LANDED",
              out.get("decision") != "block" and not armed(s), f"decision={out.get('decision')!r}")
    finally:
        cleanup(s)

    # Positive control + one resume per boundary.
    s = sid(); stamp(s)
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        b1 = time.time() + 2
        tp = write_tx(s, [boundary(b1)])
        out = run(s, tp)
        req = [e for e in events(s) if e["event"] == "resume_requested"]
        check("V-CTRUTH-OBSERVED-FIRES",
              out.get("decision") == "block" and armed(s) and "/d1-continue" in out.get("reason", ""),
              f"decision={out.get('decision')!r} armed={armed(s)}")
        check("V-CTRUTH-REQUEST-CARRIES-BOUNDARY",
              len(req) == 1 and req[0].get("boundary_ts") == iso(b1),
              f"requested={req}")
        # Tier 2 of the NEXT cycle clears both flags; same boundary must not license again.
        wd._clear_flag(s, wd.RESUME_ARMED_FLAG)
        wd._clear_flag(s, wd.RESUME_DONE_FLAG)
        out = run(s, tp)
        check("V-CTRUTH-ONE-RESUME-PER-BOUNDARY",
              out.get("decision") != "block" and names(s).count("resume_requested") == 1,
              f"decision={out.get('decision')!r} events={names(s)}")
        tp = write_tx(s, [boundary(b1), boundary(b1 + 3)])
        out = run(s, tp)
        check("V-CTRUTH-NEW-BOUNDARY-LICENSES-AGAIN",
              out.get("decision") == "block" and names(s).count("resume_requested") == 2,
              f"decision={out.get('decision')!r} events={names(s)}")
    finally:
        cleanup(s)

    # Observer unloadable -> fail CLOSED (a resume is an effect).
    s = sid(); stamp(s)
    real = wd._load_tool
    try:
        mk.write_marker(s, "/d1-continue", cwd=str(ROOT))
        tp = write_tx(s, [boundary(time.time() + 2)])
        wd._load_tool = lambda name: None if name == "gsd_long_run" else real(name)
        out = run(s, tp)
        check("V-CTRUTH-NO-OBSERVER-FAILS-CLOSED",
              out.get("decision") != "block" and not armed(s), f"decision={out.get('decision')!r}")
    finally:
        wd._load_tool = real
        cleanup(s)

    # No marker: the branch stays inert even with a fresh boundary.
    s = sid(); stamp(s)
    try:
        out = run(s, write_tx(s, [boundary(time.time() + 2)]))
        check("V-CTRUTH-NO-MARKER-INERT", not out and not armed(s), f"out={out!r}")
    finally:
        cleanup(s)


def main() -> int:
    print("V-CTRUTH -- compaction truth before any resume")
    if not hasattr(lr, "compaction_observed"):
        print("FAIL V-CTRUTH-OBSERVER-EXISTS: gsd_long_run.compaction_observed is missing")
        gates_watchdog()
        total = passes + fails + 1
        print(f"CTRUTH_PASS={passes}/{total}  threshold={total}/{total}")
        return 1
    gates_observer()
    gates_watchdog()
    total = passes + fails
    print(f"CTRUTH_PASS={passes}/{total}  threshold={total}/{total}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
