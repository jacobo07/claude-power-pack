"""V-HPKT-* gates: item 12's consumer -- `gsd_mission.py handoff --packet` -> successor card.

All state is private (mission state, packets, the source tree). Drives:
  attach    a COMPLETE packet is attached to the hand-off and the successor's card carries its
            REFERENCE (never the bytes), inside the card cap
  verify    the command the card prints is executed as printed: OK, then STALE after an edit
  stale     a card rendered after the source moved says STALE and does not present the packet
  partial   a spec whose anchor is missing attaches nothing and says why
  clear     a later hand-off without --packet carries no packet from the earlier one
  kill      CPP_SOURCE_PACKET_CARD=off renders no packet block
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="hpkt-"))
os.environ["GSD_LONG_RUN_STATE_DIR"] = str(TMP / "state")
os.environ["GSD_LONG_RUN_SESSIONS_DIR"] = str(TMP / "sessions")
os.environ["CPP_SOURCE_PACKET_DIR"] = str(TMP / "packets")
os.environ["CPP_RESOURCE_ADMISSION"] = "off"  # RAM floor reads host memory; covered by test_a5_u6
for d in ("state", "sessions", "packets", "proj/src"):
    (TMP / d).mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gsd_mission as gm  # noqa: E402

PROJ = TMP / "proj"
SRC = PROJ / "src" / "mod.py"
SRC.write_text("".join(f"# filler {i}\n" for i in range(40)) + "def f(x):\n    return x + 1\n", encoding="utf-8")
NOW = 1_800_000_000.0
passes = fails = 0


def check(gate, cond, ev=""):
    global passes, fails
    if cond:
        passes += 1
        print(f"PASS {gate}: {ev}")
    else:
        fails += 1
        print(f"FAIL {gate}: {ev}")


class R:
    def __init__(self, out, rc=0):
        self.stdout, self.stderr, self.returncode = out, "", rc


def runner(tag, name):
    # The host's launch line must name "<mission>-e<epoch>", or the launch is refused as unbound.
    return lambda argv, cwd: R(f"backgrounded · {tag} · {name}\n  claude agents  list sessions")


def running_mission(mid: str, sid_prefix: str) -> str:
    gm.create(str(PROJ), "/gsd-autonomous", mission_id=mid, now=NOW)
    gm.launch_worker(mid, expect_epoch=0, expect_state=gm.PREPARED, reason="t",
                     runner=runner(sid_prefix, f"{mid}-e1"), now=NOW)
    sid = f"{sid_prefix}-aaaa-bbbb"
    gm.ack_session(sid, pid=77, proc_start="5", now=NOW + 5)
    return sid


def main() -> int:
    sid = running_mission("m-hpkt", "1a2b3c4d")
    check("V-HPKT-SETUP", gm.load("m-hpkt")["state"] == gm.RUNNING, "mission RUNNING with an owner")

    ref, why = gm.handoff_packet(sid, ["src/mod.py::return x + 1"])
    check("V-HPKT-ATTACH", ref is not None and ref["verdict"] == "COMPLETE", f"{why or ref['sha256'][:12]}")
    # While `sid` still owns the mission, so each refusal is for its OWN reason, not "no mission".
    bad, why = gm.handoff_packet(sid, ["src/mod.py::no such anchor anywhere"])
    check("V-HPKT-PARTIAL-REFUSED", bad is None and "PARTIAL" in why, why)
    bad, why = gm.handoff_packet(sid, ["src/mod.py"])
    check("V-HPKT-BAD-SPEC", bad is None and "unreadable packet spec" in why, why)
    rec = gm.request_handoff(sid, "continue at f()", now=NOW + 60, packet=ref)
    check("V-HPKT-RECORDED", rec["state"] == gm.HANDOFF and (rec.get("packet") or {}).get("sha256") == ref["sha256"])

    gm.launch_worker("m-hpkt", expect_epoch=1, expect_state=gm.HANDOFF, reason="relay",
                     runner=runner("2b3c4d5e", "m-hpkt-e2"), now=NOW + 70, note=rec["note"], packet=rec["packet"])
    card = gm.load("m-hpkt")["card"]
    check("V-HPKT-CARD-REFERENCE", "SOURCE PACKET (COMPLETE" in card and ref["path"] in card,
          "the successor card names the packet")
    body = Path(ref["path"]).read_text(encoding="utf-8")
    check("V-HPKT-NOT-INLINED", "return x + 1" in body and "return x + 1" not in card,
          "the evidence is in the packet file, not the card")
    check("V-HPKT-CARD-CAP", len(card.encode("utf-8")) <= gm.CARD_MAX_BYTES and "[card truncated at cap]" not in card,
          f"{len(card.encode('utf-8'))} bytes")

    # The command the card prints must run exactly as printed (a documented capability is executable).
    m = re.search(r"Check it first: (.+)$", card, re.M)
    cmd = shlex.split(m.group(1), posix=False) if m else []
    cmd = [c.strip('"') for c in cmd]
    if cmd and cmd[0] == "python":
        cmd[0] = sys.executable
    ok = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ)) if cmd else None
    check("V-HPKT-VERIFY-OK", ok is not None and ok.returncode == 0 and ok.stdout.startswith("OK"),
          (ok.stdout.strip() if ok else "no command on the card"))

    SRC.write_text(SRC.read_text(encoding="utf-8").replace("x + 1", "x + 2"), encoding="utf-8")
    stale = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ)) if cmd else None
    check("V-HPKT-VERIFY-STALE", stale is not None and stale.returncode == 3 and "STALE" in stale.stdout,
          (stale.stdout.strip() if stale else ""))
    stale_card = gm.render_card({**gm.load("m-hpkt"), "packet": ref})
    check("V-HPKT-STALE-CARD", "is STALE" in stale_card and "SOURCE PACKET (COMPLETE" not in stale_card,
          "a moved source is announced, never presented")
    SRC.write_text(SRC.read_text(encoding="utf-8").replace("x + 2", "x + 1"), encoding="utf-8")

    os.environ["CPP_SOURCE_PACKET_CARD"] = "off"
    try:
        killed = gm.render_card({**gm.load("m-hpkt"), "packet": ref})
    finally:
        os.environ.pop("CPP_SOURCE_PACKET_CARD", None)
    check("V-HPKT-KILL-SWITCH", "SOURCE PACKET" not in killed)
    check("V-HPKT-KILL-CONTROL", "SOURCE PACKET (COMPLETE" in gm.render_card({**gm.load("m-hpkt"), "packet": ref}),
          "the same render with the switch unset carries it")

    sid2 = running_mission("m-hpkt2", "3c4d5e6f")

    # Red team R1: a worker that moved into a worktree mid-epoch must get ITS bytes, not the stale
    # main checkout's. effective_workdir is what the transcript says; patched where handoff_packet looks.
    wt = TMP / "wt"
    (wt / "src").mkdir(parents=True)
    (wt / "src" / "mod.py").write_text(SRC.read_text(encoding="utf-8").replace("x + 1", "x + 99"), encoding="utf-8")
    real_ew = gm.effective_workdir
    gm.effective_workdir = lambda s, c, w=None: str(wt)
    try:
        wref, why = gm.handoff_packet(sid2, ["src/mod.py::return x + 99"])
    finally:
        gm.effective_workdir = real_ew
    wbody = Path(wref["path"]).read_text(encoding="utf-8") if wref else ""
    check("V-HPKT-LIVE-WORKDIR", wref is not None and wref["root"] == str(wt) and "x + 99" in wbody,
          why or f"packet rooted at the worktree the worker is in: {wref and wref['root']}")
    ref2, _ = gm.handoff_packet(sid2, ["src/mod.py:41-42"])
    gm.request_handoff(sid2, "first", now=NOW + 60, packet=ref2)
    r2 = gm.load("m-hpkt2")
    gm.launch_worker("m-hpkt2", expect_epoch=1, expect_state=gm.HANDOFF, reason="relay",
                     runner=runner("4d5e6f70", "m-hpkt2-e2"), now=NOW + 70, note="first", packet=r2["packet"])
    gm.ack_session("4d5e6f70-aaaa-bbbb", pid=78, proc_start="6", now=NOW + 80)
    rec2 = gm.request_handoff("4d5e6f70-aaaa-bbbb", "second, no packet", now=NOW + 90)
    check("V-HPKT-CLEARED", rec2.get("packet") is None, "a hand-off without --packet inherits none")
    print(f"HPKT_PASS={passes}/{passes + fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
