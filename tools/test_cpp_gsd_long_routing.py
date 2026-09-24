#!/usr/bin/env python
"""V-ROUTE-* gates: /cpp-gsd-long routes to a Ralph mission whatever the request says.

Owner decision 2026-09-24: "autocompact" / "compact" in a request means "keep going past the
context wall", which on this estate is a FRESH session (gsd_mission.py arm), never a
compaction. Three surfaces carry that decision, and each is judged here:

  1. the v2 arming CLI (gsd_autorun_marker.py --write) refuses without --legacy-compact and
     names the Ralph command in its refusal;
  2. the command text routes first, in its description and in a Routing section above
     both paths;
  3. the LIVE copy the harness loads (~/.claude/commands/cpp-gsd-long.md) is the repo copy.
     Measured 2026-09-24: the live copy was the 2026-09-19 v2-only text, so every
     /cpp-gsd-long compacted while the repo said Ralph was the default. Read-only check.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="gsd-route-test-")
os.environ["GSD_AUTORUN_MARKER_DIR"] = TMP  # a marker written by mistake lands here, never live
TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import gsd_autorun_marker as mk  # noqa: E402

passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate} {ev}")
    else:
        fails += 1
        print(f"FAIL {gate} {ev}")


def cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = mk.main(argv)
    return rc, out.getvalue(), err.getvalue()


def main() -> int:
    # --- 1. the v2 CLI refuses by default, whatever the command text says -----------------
    for tag, command in (("PLAIN", "/gsd-autonomous"), ("AUTOCOMPACT-WORDING", "/gsd-autonomous autocompact")):
        rc, out, err = cli(["--write", "--session", "route-test-0000", "--command", command,
                            "--cwd", TMP, "--mission", "alpha,beta,gamma"])
        check(f"V-ROUTE-CLI-REFUSES-{tag}",
              rc == 2 and "Ralph mission" in err and "gsd_mission.py" in err and " arm " in err,
              f"rc={rc} err={err[:160]!r}")
    check("V-ROUTE-CLI-REFUSAL-WRITES-NOTHING", not list(Path(TMP).glob("gsd-autorun-*.json")),
          str(list(Path(TMP).glob("*"))))
    # control: the opt-in gets PAST this gate (it may still be refused later, for its own reasons)
    rc, out, err = cli(["--write", "--session", "route-test-0001", "--command", "/gsd-autonomous",
                        "--cwd", TMP, "--mission", "alpha,beta,gamma", "--legacy-compact"])
    check("V-ROUTE-CLI-LEGACY-OPT-IN-PASSES-GATE", "Ralph mission" not in err, f"rc={rc} err={err[:160]!r}")

    # --- 2. the command text routes first -------------------------------------------------
    doc = (REPO / "commands" / "cpp-gsd-long.md").read_text(encoding="utf-8")
    front = doc.split("---", 2)[1] if doc.startswith("---") else ""
    desc = next((l for l in front.splitlines() if l.startswith("description:")), "")
    check("V-ROUTE-DESCRIPTION-SAYS-RALPH", "Ralph" in desc and "autocompact" in desc
          and "survives context compactions" not in desc, desc[:120])
    i_route, i_ralph, i_legacy = (doc.find("## Routing"), doc.find("## Default: Ralph"),
                                  doc.find("## Legacy (v2)"))
    check("V-ROUTE-ROUTING-SECTION-FIRST", 0 <= i_route < i_ralph < i_legacy,
          f"routing={i_route} ralph={i_ralph} legacy={i_legacy}")
    check("V-ROUTE-LEGACY-NEEDS-OWNER-PHRASE", '"legacy compact"' in doc and "--legacy-compact" in doc)

    # --- 3. the live copy is the repo copy ------------------------------------------------
    live = Path.home() / ".claude" / "commands" / "cpp-gsd-long.md"
    check("V-ROUTE-LIVE-COMMAND-IS-REPO-COMMAND",
          live.is_file() and live.read_bytes() == (REPO / "commands" / "cpp-gsd-long.md").read_bytes(),
          f"live={live} exists={live.is_file()} -- sync with Copy-Item if red")

    print(f"ROUTE_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
