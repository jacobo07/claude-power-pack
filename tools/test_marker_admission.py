"""V-MADM-* gates: a file the sweep refuses to ADMIT is named, not swallowed.

Phase 4 delivered an instrument whose stated done-criterion is that "an empty
sweep is distinguishable from a sweep that judged nothing". It achieved that for
DECLINES -- `kept` names the clause holding each marker -- and missed it one
level below, for NON-ADMISSIONS. A `gsd-autorun-*.json` that never became a
marker produced no row, no log and no count.

Measured 2026-09-21 on the live estate: 8 files matched the sweep's own glob,
6 were reported on, and 2 (82-byte test residue with no `session_id`) were
dropped in silence. Nothing in the output could reveal that.

These gates pin the fix AND the floor. The floor matters independently: a glob
that silently stopped matching reads exactly like an estate with nothing to
judge, which is the failure `instrument-before-claim.md` calls a population
floor.

Hermetic: the state directory is redirected to a temp dir, every sweep runs
dry, and no real marker is touched.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"

TMP = Path(tempfile.mkdtemp(prefix="madm-"))
STATE, HOOKS, PROJECTS, SESSIONS = (TMP / n for n in ("state", "hooks", "projects", "sessions"))
for d in (STATE, HOOKS, PROJECTS, SESSIONS):
    d.mkdir(parents=True)
os.environ.update({"GSD_LONG_RUN_STATE_DIR": str(STATE), "GSD_LONG_RUN_HOOKS_DIR": str(HOOKS),
                   "GSD_LONG_RUN_PROJECTS_DIR": str(PROJECTS), "GSD_LONG_RUN_NO_SPAWN": "1",
                   "GSD_LONG_RUN_SESSIONS_DIR": str(SESSIONS)})

passes = fails = inconclusive = 0


def check(gate, cond, ev):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


def skip(gate, why):
    global inconclusive
    inconclusive += 1
    print(f"SKIP {gate}: INCONCLUSIVE -- {why}")


def load(path: Path, name: str):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lr = load(TOOLS / "gsd_long_run.py", "gsd_long_run_madm")
# Never shell out to gsd-tools from a unit gate.
lr.gsd_status = lambda project, timeout=45: {"outcome": "UNAVAILABLE", "reason": "stubbed"}


def clear():
    for p in STATE.glob("gsd-autorun-*.json"):
        p.unlink()


def write(name: str, body: str):
    (STATE / name).write_text(body, encoding="utf-8")


def good_marker(sid: str):
    # resume_command deliberately NOT /gsd-autonomous, so the sweep never asks
    # GSD about a project and this gate stays a unit test.
    write(f"gsd-autorun-{sid}.json", json.dumps({
        "session_id": sid, "resume_command": "/absw2-continue", "cwd": "", "cycles": 0}))


def rows(acts, kind):
    return [a for a in acts if a.get("action") == kind]


def only(acts, kind, field="reason"):
    return [a.get(field) for a in rows(acts, kind)]


# ------------------------------------------------------------------------ gates
def gate_no_session_id_is_named():
    """The exact shape found on the live estate: 82 bytes, no session_id."""
    clear()
    write("gsd-autorun-intent-ghost-deadbeef.json",
          json.dumps({"resume_command": "/gsd-autonomous", "post_compact_intent": "something"}))
    acts = lr.sweep(dry_run=True, explain=True)
    named = rows(acts, "not_a_marker")
    check("V-MADM-NO-SESSION-ID-IS-NAMED",
          len(named) == 1 and named[0]["reason"] == "no session_id"
          and named[0]["file"] == "gsd-autorun-intent-ghost-deadbeef.json",
          f"{named}")


def gate_unreadable_is_named():
    clear()
    write("gsd-autorun-broken.json", "{ this is not json")
    acts = lr.sweep(dry_run=True, explain=True)
    named = only(acts, "not_a_marker")
    check("V-MADM-UNREADABLE-IS-NAMED",
          len(named) == 1 and named[0].startswith("unreadable:"), f"{named}")


def gate_non_object_is_named():
    """A JSON array parses fine and is still not a marker. Before the fix this
    and a malformed file were the same silence."""
    clear()
    write("gsd-autorun-array.json", "[1, 2, 3]")
    acts = lr.sweep(dry_run=True, explain=True)
    named = only(acts, "not_a_marker")
    check("V-MADM-NON-OBJECT-IS-NAMED",
          len(named) == 1 and named[0] == "not an object: list", f"{named}")


def gate_scanned_floor():
    """The denominator. Without it, a glob that stopped matching reads like an
    estate with nothing to judge."""
    clear()
    good_marker("madm-aaaaaaaaaaaa")
    good_marker("madm-bbbbbbbbbbbb")
    write("gsd-autorun-ghost-1.json", json.dumps({"resume_command": "/x"}))
    write("gsd-autorun-ghost-2.json", "[]")
    acts = lr.sweep(dry_run=True, explain=True)
    s = rows(acts, "scanned")
    check("V-MADM-SCANNED-FLOOR",
          len(s) == 1 and s[0]["files"] == 4 and s[0]["admitted"] == 2 and s[0]["rejected"] == 2,
          f"{s}")


def gate_silent_by_default():
    """Opt-in, exactly like `kept`. A default sweep's output is unchanged, so
    nothing that parses it today sees a new row."""
    clear()
    good_marker("madm-cccccccccccc")
    write("gsd-autorun-ghost-3.json", json.dumps({"resume_command": "/x"}))
    acts = lr.sweep(dry_run=True)
    check("V-MADM-SILENT-BY-DEFAULT",
          not rows(acts, "not_a_marker") and not rows(acts, "scanned"),
          f"not_a_marker={len(rows(acts, 'not_a_marker'))} scanned={len(rows(acts, 'scanned'))}")


def gate_valid_marker_is_not_accused():
    """Green control. A detector that rejected everything would pass every gate
    above and be indistinguishable from one that works."""
    clear()
    good_marker("madm-dddddddddddd")
    admitted, rejected = lr._scan_markers()
    acts = lr.sweep(dry_run=True, explain=True)
    check("V-MADM-VALID-MARKER-IS-NOT-ACCUSED",
          len(admitted) == 1 and not rejected and not rows(acts, "not_a_marker"),
          f"admitted={len(admitted)} rejected={rejected}")


def gate_markers_signature_unchanged():
    """Three callers unpack (Path, dict). The scan grew underneath `_markers`;
    `_markers` itself must not have changed shape."""
    clear()
    good_marker("madm-eeeeeeeeeeee")
    write("gsd-autorun-ghost-4.json", json.dumps({"resume_command": "/x"}))
    got = lr._markers()
    ok = (len(got) == 1 and isinstance(got[0], tuple) and len(got[0]) == 2
          and isinstance(got[0][0], Path) and isinstance(got[0][1], dict)
          and got[0][1]["session_id"] == "madm-eeeeeeeeeeee")
    check("V-MADM-MARKERS-SIGNATURE-UNCHANGED", ok, f"{got}")


def main() -> int:
    if not hasattr(lr, "_scan_markers"):
        skip("V-MADM-SUBJECT-PRESENT", "gsd_long_run._scan_markers is absent")
        print(f"MADM_PASS={passes}/{passes + fails}  inconclusive={inconclusive}")
        return 2
    for g in (gate_no_session_id_is_named, gate_unreadable_is_named, gate_non_object_is_named,
              gate_scanned_floor, gate_silent_by_default, gate_valid_marker_is_not_accused,
              gate_markers_signature_unchanged):
        try:
            g()
        except Exception as exc:
            skip(g.__name__, f"{exc.__class__.__name__}: {exc}")
    total = passes + fails
    print(f"MADM_PASS={passes}/{total}  inconclusive={inconclusive}  threshold={total}/{total}")
    return 0 if fails == 0 and inconclusive == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
