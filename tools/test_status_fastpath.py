#!/usr/bin/env python3
"""V-SFP gates for tools/status_fastpath.py + hooks/status-fastpath.js (ctx-same-pane S4).

Both poles of the matcher, kill switch, fail-open, deadline, a real projection over a temp state dir and a
temp git repo, and the node -> python -> JSON boundary the host actually crosses.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.mkdtemp(prefix="sfp-"))
STATE = TMP / "state"
REPO = TMP / "repo"
os.environ["CPP_STATUS_STATE_DIR"] = str(STATE)
sys.path.insert(0, str(ROOT / "tools"))
import status_fastpath as sfp  # noqa: E402

GIT = sfp.GIT
NODE = os.environ.get("CPP_NODE") or r"C:\Program Files\nodejs\node.exe"
passes = fails = 0


def _ok(gate, ev):
    global passes
    passes += 1
    print(f"PASS {gate}: {ev}")


def _fail(gate, ev):
    global fails
    fails += 1
    print(f"FAIL {gate}: {ev}")


def check(gate, cond, ev):
    (_ok if cond else _fail)(gate, ev)


def setup():
    # Arrange: a git repo with one commit and a mission whose cwd is that repo.
    STATE.mkdir(parents=True)
    REPO.mkdir()
    for args in (["init", "-q"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run([GIT, "-C", str(REPO), *args], check=True)
    (REPO / "a.txt").write_text("a", encoding="utf-8")
    subprocess.run([GIT, "-C", str(REPO), "add", "a.txt"], check=True)
    subprocess.run([GIT, "-C", str(REPO), "commit", "-q", "-m", "first commit"], check=True)
    (STATE / "gsd-mission-m-test0001.json").write_text(json.dumps(
        {"mission_id": "m-test0001", "state": "RUNNING", "epoch": 2, "cwd": str(REPO), "updated_at": 1}),
        encoding="utf-8")
    (STATE / "gsd-mission-m-other.json").write_text(json.dumps(
        {"mission_id": "m-other", "state": "RUNNING", "epoch": 1, "cwd": str(TMP), "updated_at": 2}),
        encoding="utf-8")


def main() -> int:
    setup()
    admitted = ["estado", "Estado", "¿Cómo va?", "como va", "cómo vamos?", "status", "Status.",
                "how's it going?", "How is it going", "progreso"]
    refused = ["", "cómo va el deploy? arregla el hook", "estado del bug 12", "status of the hook and fix it",
               "como va? y luego haz el commit", "approve", "1", "continua", "estado: lanza S5"]
    bad_in = [p for p in admitted if not sfp.is_status(p)]
    check("V-SFP-MATCH-STATUS", not bad_in, f"{len(admitted)} status prompts admitted; missed {bad_in}")
    bad_out = [p for p in refused if sfp.is_status(p)]
    check("V-SFP-MATCH-MIXED-REFUSED", not bad_out, f"{len(refused)} other prompts pass through; leaked {bad_out}")

    ev = {"session_id": "no-such-session", "cwd": str(REPO), "prompt": "¿cómo va?"}
    out = sfp.decide(ev)
    reason = (out or {}).get("reason", "")
    sha = subprocess.run([GIT, "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout[:8]
    check("V-SFP-PROJECTION", out is not None and out["decision"] == "block" and "m-test0001" in reason
          and f"@ {sha}" in reason and "dirty tracked 0" in reason and "m-other" not in reason,
          reason.replace("\n", " | ")[:300])
    check("V-SFP-NON-STATUS-NONE", sfp.decide({**ev, "prompt": "arregla el hook"}) is None,
          "a non-status prompt returns None")

    os.environ["CPP_STATUS_FASTPATH"] = "off"
    check("V-SFP-KILL-SWITCH", sfp.decide(ev) is None, "CPP_STATUS_FASTPATH=off returns None")
    del os.environ["CPP_STATUS_FASTPATH"]

    check("V-SFP-DEADLINE", sfp.decide(ev, now=lambda: -10.0) is None,
          "a projection past its deadline returns None (pass-through)")
    real_git = sfp.GIT
    sfp.GIT = str(TMP / "no-git.exe")
    check("V-SFP-FAIL-OPEN", sfp.decide(ev) is None, "a failing source returns None, never raises")
    sfp.GIT = real_git

    # Boundary: the node shim the host runs, with the real python behind it.
    env = {**os.environ, "CPP_STATUS_STATE_DIR": str(STATE)}
    shim = str(ROOT / "hooks" / "status-fastpath.js")
    r = subprocess.run([NODE, shim], input=json.dumps(ev), capture_output=True, text=True, encoding="utf-8",
                       env=env, timeout=20)
    try:
        parsed = json.loads(r.stdout)
    except ValueError:
        parsed = {}
    check("V-SFP-BOUNDARY-BLOCK", r.returncode == 0 and parsed.get("decision") == "block"
          and "m-test0001" in parsed.get("reason", ""), f"rc {r.returncode} stdout {r.stdout[:120]!r}")
    r2 = subprocess.run([NODE, shim], input=json.dumps({**ev, "prompt": "haz el commit"}), capture_output=True,
                        text=True, encoding="utf-8", env=env, timeout=20)
    check("V-SFP-BOUNDARY-PASS", r2.returncode == 0 and r2.stdout.strip() == "",
          f"rc {r2.returncode} stdout {r2.stdout[:80]!r}")
    r3 = subprocess.run([NODE, shim], input="not json", capture_output=True, text=True, encoding="utf-8",
                        env=env, timeout=20)
    check("V-SFP-BOUNDARY-GARBAGE", r3.returncode == 0 and r3.stdout.strip() == "",
          f"malformed stdin passes through: rc {r3.returncode}")

    print(f"SFP_PASS={passes}/{passes + fails}  threshold={passes + fails}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
