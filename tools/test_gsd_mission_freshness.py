#!/usr/bin/env python
"""V-MF-* gates for tools/gsd_mission_freshness.py and its arming point in gsd_autorun_marker.

Synthetic fixtures only: a drill pinned to one real repo's roadmap decays the day that repo
seeds a new milestone.

Run: python tools/test_gsd_mission_freshness.py
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gsd_mission_freshness as mf  # noqa: E402
import gsd_autorun_marker as mk  # noqa: E402

passes = 0
fails = 0


def _ok(gate, msg):
    global passes
    passes += 1
    print(f"[PASS] {gate}: {msg}")


def _fail(gate, msg):
    global fails
    fails += 1
    print(f"[FAIL] {gate}: {msg}")


STALE_STATE = "---\nmilestone: v2.0\nmilestone_name: code-injection-custom-sports\nstatus: in_progress\n---\n# State\nSports Batch 3, (+) tab UI hub complete.\n"
STALE_ROADMAP = "# Roadmap v2.0\n## Phase 2: (+) tab hub\n## Phase 7: Sports Batch 3 - seamless transitions\n"
FRESH_STATE = "---\nmilestone: v3.0\nmilestone_name: page2-native-gameselect\nstatus: planning\n---\n"
FRESH_ROADMAP = "# Roadmap v3.0\n## Phase 9: Page 2 semantic seam (FIX-2 ARM)\n## Phase 10: gameSelect identity ADR\n"
MISSION = "page2,gameselect,seam,fix2"


def project(tmp: Path, name: str, state: str | None, roadmap: str | None, bom=False) -> Path:
    root = tmp / name
    (root / ".planning").mkdir(parents=True)
    enc = "utf-8-sig" if bom else "utf-8"
    if state is not None:
        (root / ".planning" / "STATE.md").write_text(state, encoding=enc)
    if roadmap is not None:
        (root / ".planning" / "ROADMAP.md").write_text(roadmap, encoding=enc)
    return root


def cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = mk.main(argv)
    return rc, out.getvalue(), err.getvalue()


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        mk.STATE_DIR = tmp / "state"          # never touch the real ~/.claude/state
        stale = project(tmp, "stale", STALE_STATE, STALE_ROADMAP)
        fresh = project(tmp, "fresh", FRESH_STATE, FRESH_ROADMAP)

        # Arrange/Act/Assert per gate
        v = mf.check(stale, MISSION)
        if v.outcome == mf.STALE and not v.armable and v.matched == [] and "v2.0" in v.active_milestone:
            _ok("V-MF-STALE", f"old roadmap vs new mission -> STALE ({v.active_milestone})")
        else:
            _fail("V-MF-STALE", f"{v}")

        v = mf.check(fresh, MISSION)
        if v.outcome == mf.FRESH and v.armable and set(v.matched) == {"page2", "gameselect", "seam", "fix2"}:
            _ok("V-MF-FRESH", f"matched {v.matched}")
        else:
            _fail("V-MF-FRESH", f"{v}")

        # 'seamless' in the stale roadmap must not satisfy 'seam'
        v = mf.check(stale, "seam")
        if v.outcome == mf.STALE:
            _ok("V-MF-TOKEN-NOT-SUBSTRING", "'seamless' does not match term 'seam'")
        else:
            _fail("V-MF-TOKEN-NOT-SUBSTRING", f"{v}")

        # The shape that escaped on a real repo: a stale roadmap sharing ONE generic noun with
        # the mission. "Any intersection" called it FRESH; a majority rule must not.
        generic = project(tmp, "generic", STALE_STATE, STALE_ROADMAP + "Each sport has a slot.\n")
        v = mf.check(generic, MISSION + ",slot")
        if v.outcome == mf.STALE and v.matched == ["slot"]:
            _ok("V-MF-GENERIC-COLLISION", "1/5 shared generic term -> still STALE")
        else:
            _fail("V-MF-GENERIC-COLLISION", f"{v}")

        v = mf.check(fresh, ["Page 2", "game-select", "FIX-2"])
        if v.outcome == mf.FRESH and len(v.matched) == 3:
            _ok("V-MF-FORMS", "'Page 2' / 'game-select' / 'FIX-2' normalise and match")
        else:
            _fail("V-MF-FORMS", f"{v}")

        for gate, raw in (("V-MF-UNDECLARED-EMPTY", ""), ("V-MF-UNDECLARED-PUNCT", " , -- ,")):
            v = mf.check(fresh, raw)
            if v.outcome == mf.UNDECLARED and not v.armable:
                _ok(gate, f"{raw!r} -> UNDECLARED")
            else:
                _fail(gate, f"{v}")

        noroad = project(tmp, "noroad", FRESH_STATE, None)
        v = mf.check(noroad, MISSION)
        if v.outcome == mf.UNREADABLE and "ROADMAP.md" in v.reason:
            _ok("V-MF-UNREADABLE", v.reason)
        else:
            _fail("V-MF-UNREADABLE", f"{v}")

        bom = project(tmp, "bom", FRESH_STATE, FRESH_ROADMAP, bom=True)
        v = mf.check(bom, MISSION)
        if v.outcome == mf.FRESH and "v3.0" in v.active_milestone:
            _ok("V-MF-BOM", "BOM-prefixed files read; frontmatter still parsed")
        else:
            _fail("V-MF-BOM", f"{v}")

        # --- the arming point ---
        sid = "mf-test-session"
        rc, out, err = cli(["--write", "--session", sid, "--command", "/gsd-autonomous",
                            "--cwd", str(stale), "--mission", MISSION])
        if rc == 2 and "STALE" in err and mk.read_marker(sid) is None:
            _ok("V-MF-ARM-REFUSES-STALE", "CLI refused, no marker written")
        else:
            _fail("V-MF-ARM-REFUSES-STALE", f"rc={rc} err={err!r} marker={mk.read_marker(sid)}")

        rc, out, err = cli(["--write", "--session", sid, "--command", "/gsd-autonomous",
                            "--cwd", str(fresh)])
        if rc == 2 and "UNDECLARED" in err and mk.read_marker(sid) is None:
            _ok("V-MF-ARM-REFUSES-UNDECLARED", "CLI without --mission refused")
        else:
            _fail("V-MF-ARM-REFUSES-UNDECLARED", f"rc={rc} err={err!r}")

        rc, out, err = cli(["--write", "--session", sid, "--command", "/gsd-autonomous",
                            "--cwd", str(fresh), "--mission", MISSION])
        data = mk.read_marker(sid) or {}
        if rc == 0 and data.get("mission", {}).get("active_milestone", "").startswith("v3.0"):
            _ok("V-MF-ARM-FRESH", f"marker written with mission {data['mission']['matched']}")
        else:
            _fail("V-MF-ARM-FRESH", f"rc={rc} err={err!r} data={json.dumps(data)}")
        mk.clear_marker(sid)

        # standalone CLI exit codes
        out = io.StringIO()
        with redirect_stdout(out):
            rc_s = mf.main(["--project", str(stale), "--mission", MISSION])
            rc_f = mf.main(["--project", str(fresh), "--mission", MISSION])
        if (rc_s, rc_f) == (2, 0):
            _ok("V-MF-CLI-EXIT", "stale -> 2, fresh -> 0")
        else:
            _fail("V-MF-CLI-EXIT", f"stale={rc_s} fresh={rc_f}")

    print(f"MISSION_FRESHNESS_PASS={passes}/{passes + fails}  threshold=13/13")
    return 0 if fails == 0 and passes == 13 else 1


if __name__ == "__main__":
    sys.exit(main())
